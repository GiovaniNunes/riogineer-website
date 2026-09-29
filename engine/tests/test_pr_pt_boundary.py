"""M8.1 runtime restart, failure safety, precision isolation and frozen acceptance."""
from dataclasses import FrozenInstanceError, asdict, replace
import importlib.util
import json
from math import exp
from pathlib import Path
import unittest
from unittest.mock import patch

from riogineer_engine.pr_eos import PengRobinsonEOS, ThermodynamicError
from riogineer_engine.pr_flash import (AccuracyProfile, SolverSettings, flash_pt,
                                      stability_restart_seed)
from riogineer_engine.pr_stability import stability
from riogineer_engine.rachford_rice import RRResult, solve_rr

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('boundary_comparison', ROOT / 'benchmarks/peng_robinson_pt_boundary/compare_production.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)
REFERENCE = comparison.read_reference()
CENTER = next(c for c in REFERENCE['bubble_cases'] if c['case_id'] == 'BUBBLE_CENTER')['reference']


def run(record=CENTER, settings=SolverSettings()):
    state, bip = comparison.inputs(REFERENCE, record)
    return flash_pt(state, bip, settings)


def seed_inputs():
    state, bip = comparison.inputs(REFERENCE, CENTER)
    eos = PengRobinsonEOS(bip.component_ids, state.temperature_K, state.pressure_Pa_abs, bip)
    z = state.composition.molar_fractions
    return eos, z, stability(eos, z)


class BubbleMatrix(unittest.TestCase):
    pass


def bubble_test(case):
    def test(self):
        actual = comparison.evaluate(REFERENCE, case['reference'])
        checks = comparison.compare(REFERENCE, actual, case['reference'])
        self.assertTrue(all(c['passed'] for c in checks), checks)
        self.assertEqual(actual['diagnostics']['initialization']['restart_count'], int(case['needs_stability_restart']))
        if case['reference']['classification'] == 'single_liquid':
            self.assertEqual(set(actual['phases']), {'liquid'})
            self.assertIsNone(actual['final_K'])
            self.assertEqual(actual['beta'], 0.)
    return test


for case in REFERENCE['bubble_cases']:
    setattr(BubbleMatrix, 'test_'+case['case_id'].lower(), bubble_test(case))


class RestartSafety(unittest.TestCase):
    def assert_empty(self, result):
        self.assertFalse(result.status.startswith('success'))
        self.assertEqual(result.phases, ())
        self.assertIsNone(result.beta)
        self.assertEqual(result.final_K, ())

    def test_runtime_stability_mapping_and_orientation(self):
        result = run()
        init = result.diagnostics.initialization
        seed = init.restart_seed
        self.assertEqual(init.initial_rr.status, 'liquid_tendency')
        self.assertEqual(init.restart_rr.status, 'two_phase')
        self.assertEqual(init.restart_count, 1)
        self.assertGreater(seed.parent_pip, 1)
        self.assertLess(seed.trial_pip, 1)
        self.assertIn(seed.trial_composition, [t.composition for t in result.diagnostics.stability.trials])
        self.assertEqual(seed.stability_sum, exp(-seed.trial_tpd_RT))
        self.assertEqual(seed.K, tuple(seed.stability_sum*w/z for w,z in zip(seed.trial_composition, CENTER['z'])))
        self.assertNotEqual(seed.K, result.final_K)
        self.assertNotEqual(seed.K, init.initial_K)
        self.assertTrue(result.diagnostics.equilibrium_stability.stable)

    def test_changed_runtime_feed_changes_seed(self):
        first = run()
        changed = run(dict(CENTER, z=[.5001,.4999]))
        self.assertEqual(changed.status, 'success_two_phase')
        seed = changed.diagnostics.initialization.restart_seed
        self.assertIsNotNone(seed)
        self.assertNotEqual(seed.K, first.diagnostics.initialization.restart_seed.K)
        self.assertEqual(seed.K, tuple(seed.stability_sum*w/z for w,z in zip(seed.trial_composition, [.5001,.4999])))

    def test_no_restart_without_converged_stability(self):
        with patch('riogineer_engine.pr_flash.stability_restart_seed') as seed:
            r = run(settings=SolverSettings(stability_max_iterations=1))
        self.assert_empty(r)
        self.assertEqual(r.status, 'stability_not_converged')
        seed.assert_not_called()

    def test_seed_not_returned_as_equilibrium(self):
        r = run(settings=SolverSettings(flash_max_iterations=1))
        self.assert_empty(r)
        self.assertEqual(r.status, 'flash_not_converged')
        self.assertEqual(r.diagnostics.initialization.restart_count, 1)

    def test_restart_rr_failure_no_retry_loop(self):
        endpoint = RRResult('liquid_tendency', 0., -.1, True, 0)
        with patch('riogineer_engine.pr_flash.solve_rr', return_value=endpoint) as rr:
            r = run()
        self.assertEqual(rr.call_count, 2)
        self.assert_empty(r)
        self.assertEqual(r.diagnostics.initialization.restart_count, 1)
        self.assertEqual(r.diagnostics.initialization.restart_rr, endpoint)

    def test_initial_rr_nonconvergence_is_not_endpoint_restart(self):
        failed = RRResult('not_converged', None, .1, False, 200)
        with patch('riogineer_engine.pr_flash.solve_rr', return_value=failed) as rr:
            r = run()
        self.assertEqual(rr.call_count, 1)
        self.assertEqual(r.diagnostics.initialization.restart_count, 0)
        self.assert_empty(r)

    def test_later_rr_endpoint_does_not_trigger_second_restart(self):
        calls = []
        def controlled(z, k, limit):
            calls.append(k)
            return solve_rr(z,k,limit) if len(calls) <= 2 else RRResult('vapor_tendency',1.,.1,True,0)
        with patch('riogineer_engine.pr_flash.solve_rr', side_effect=controlled):
            r = run()
        self.assertEqual(len(calls), 3)
        self.assert_empty(r)
        self.assertEqual(r.diagnostics.initialization.restart_count, 1)

    def test_final_stability_remains_mandatory(self):
        def controlled(eos, z, limit, tangent=None):
            s = stability(eos,z,limit,tangent)
            return replace(s, stable=False) if tangent is not None else s
        with patch('riogineer_engine.pr_flash.stability', side_effect=controlled):
            r = run()
        self.assert_empty(r)
        self.assertEqual(r.status, 'flash_not_converged')

    def test_invalid_trial_rejected_before_rr_seed(self):
        eos,z,s = seed_inputs()
        candidate = min(s.trials, key=lambda t:t.tpd_RT)
        for w in ((float('nan'),.5), (0.,1.), (.2,.2), (.5,)):
            with self.subTest(w=w), self.assertRaises(ThermodynamicError):
                stability_restart_seed(eos,z,replace(s,trials=(replace(candidate,composition=w),)))

    def test_no_negative_stationary_trial_fails_explicitly(self):
        eos,z,s = seed_inputs()
        with self.assertRaisesRegex(ThermodynamicError, 'No converged vapor-like'):
            stability_restart_seed(eos,z,replace(s,trials=()))

    def test_opposite_orientation_not_guessed(self):
        eos,z,s = seed_inputs()
        with patch.object(PengRobinsonEOS, 'phase_identification', return_value=.5):
            with self.assertRaisesRegex(ThermodynamicError, 'liquid-like parent'):
                stability_restart_seed(eos,z,s)

    def test_multiple_candidates_select_strongest_deterministically(self):
        eos,z,s = seed_inputs()
        a = stability_restart_seed(eos,z,s)
        b = stability_restart_seed(eos,z,replace(s,trials=tuple(reversed(s.trials))))
        self.assertEqual(a,b)

    def test_zero_inventory_preserves_single_phase(self):
        for z in ([1.,0.], [0.,1.]):
            r = run(dict(CENTER,z=z))
            self.assertEqual(r.status, 'success_single_phase')
            self.assertEqual(r.diagnostics.initialization.restart_count, 0)
            self.assertEqual(r.phases[0].composition, tuple(z))
        eos,_,s = seed_inputs()
        with self.assertRaisesRegex(ThermodynamicError, 'positive binary'):
            stability_restart_seed(eos,(1.,0.),s)

    def test_json_diagnostics_are_finite(self):
        json.dumps(asdict(run()), allow_nan=False)


class Precision(unittest.TestCase):
    def test_immutable_standard_and_explicit_high(self):
        standard, high = SolverSettings(), SolverSettings.high_accuracy()
        self.assertEqual(standard.profile, AccuracyProfile.STANDARD)
        self.assertEqual(standard.fugacity_tolerance, 1e-11)
        self.assertEqual(high.profile, AccuracyProfile.HIGH_ACCURACY)
        self.assertEqual(high.fugacity_tolerance, 1e-12)
        for name in ('flash_max_iterations','rr_max_iterations','stability_max_iterations','material_tolerance'):
            self.assertEqual(getattr(standard,name), getattr(high,name))
        with self.assertRaises(FrozenInstanceError):
            high.fugacity_tolerance = 1e-10

    def test_conflicting_or_unqualified_controls_rejected(self):
        for settings in (SolverSettings(fugacity_tolerance=1e-12),
                         SolverSettings(profile=AccuracyProfile.HIGH_ACCURACY),
                         SolverSettings(profile='high_accuracy'),
                         replace(SolverSettings.high_accuracy(), fugacity_tolerance=1e-10)):
            self.assertEqual(run(settings=settings).status, 'invalid_input')

    def test_standard_high_standard_and_repeat(self):
        ref = REFERENCE['dew_reference']
        first = run(ref)
        high = run(ref,SolverSettings.high_accuracy())
        self.assertEqual(first,run(ref))
        self.assertEqual(high,run(ref,SolverSettings.high_accuracy()))
        self.assertEqual(first.diagnostics.iterations,59)
        self.assertEqual(first.beta,.9868744541552132)
        self.assertLessEqual(max(map(abs,high.diagnostics.fugacity_residual)),1e-12)
        self.assertGreater(high.diagnostics.iterations,first.diagnostics.iterations)
        self.assertLessEqual(high.diagnostics.iterations,100)

    def test_m10_high_accuracy_frozen_comparison(self):
        a = comparison.evaluate(REFERENCE, REFERENCE['dew_reference'], SolverSettings.high_accuracy(), True)
        checks = comparison.compare(REFERENCE,a,REFERENCE['dew_reference'],True)
        self.assertTrue(all(c['passed'] for c in checks),checks)

    def test_required_downstream_margin(self):
        evidence = comparison.local_dew_margin(REFERENCE)
        self.assertTrue(all(c['passed'] for c in evidence['comparisons']))
        self.assertGreaterEqual(evidence['minimum_margin_factor'], REFERENCE['recommendation']['minimum_required_margin_factor'])

    def test_reference_structure_and_integrity(self):
        self.assertEqual(tuple(c['case_id'] for c in REFERENCE['bubble_cases']), comparison.CASE_IDS)
        with patch.object(Path,'read_bytes',return_value=b'{"reference_id":"wrong"}'):
            with self.assertRaisesRegex(ValueError,'integrity mismatch'):
                comparison.read_reference()
