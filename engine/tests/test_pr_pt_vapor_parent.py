"""M8.2 frozen production acceptance and guarded orientation dispatch."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.peng_robinson_pt_vapor_parent import compare_production as comparison
from riogineer_engine.pr_eos import PengRobinsonEOS, ThermodynamicError
from riogineer_engine.pr_flash import SolverSettings, flash_pt, stability_restart_seed
from riogineer_engine.pr_stability import stability
from riogineer_engine.rachford_rice import RRResult

REFERENCE, CONTEXT=comparison.context()
TARGET=next(c['independent_equilibrium'] for c in REFERENCE['cases'] if c['original_failure'])


def run(record=TARGET,settings=SolverSettings()):
    state,bip=comparison.prior.inputs(CONTEXT,record)
    return flash_pt(state,bip,settings)


def seed_inputs():
    state,bip=comparison.prior.inputs(CONTEXT,TARGET)
    eos=PengRobinsonEOS(bip.component_ids,state.temperature_K,state.pressure_Pa_abs,bip)
    z=state.composition.molar_fractions
    return eos,z,stability(eos,z)


class FrozenMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=comparison.build()

    def test_profile_isolation_call_order_and_both_orientations(self):
        self.assertTrue(self.evidence['passed'])
        self.assertEqual(self.evidence['M8_1_bubble']['diagnostics']['initialization']['restart_seed']['orientation'],
                         'liquid_parent_vapor_trial')


def state_test(case):
    def test(self):
        rows=[r for r in self.evidence['rows'] if r['case_id']==case['case_id']]
        self.assertEqual(len(rows),2)
        for row in rows:
            p=row['production'];init=p['diagnostics']['initialization']
            self.assertTrue(all(c['passed'] for c in row['comparisons']))
            if case['original_failure']:
                self.assertEqual(init['initial_rr']['status'],'vapor_tendency')
                self.assertEqual(init['restart_count'],1)
                seed=init['restart_seed']
                self.assertLess(seed['parent_pip'],1)
                self.assertGreater(seed['trial_pip'],1)
                self.assertNotEqual(seed['K'],tuple(seed['stability_sum']*w/z for w,z in zip(seed['trial_composition'],TARGET['z'])))
                self.assertNotEqual(seed['K'],p['final_K'])
    return test


for i,c in enumerate(REFERENCE['cases']):
    setattr(FrozenMatrix,f'test_neighborhood_{i:02d}',state_test(c))


class RestartSafety(unittest.TestCase):
    def test_seed_construction_error_propagates_without_equilibrium(self):
        error=ThermodynamicError('rachford_rice_not_converged','Controlled seed construction failure')
        with patch('riogineer_engine.pr_flash.stability_restart_seed',side_effect=error) as seed:
            p=run()
        seed.assert_called_once()
        self.assertEqual(p.status,'rachford_rice_not_converged')
        self.assertEqual(p.diagnostics.message,'Controlled seed construction failure')
        self.assertEqual(p.phases,())
        self.assertIsNone(p.beta)
        self.assertEqual(p.final_K,())
        self.assertIsNone(p.classification)
        self.assertEqual(p.diagnostics.initialization.restart_count,1)

    def test_invalid_sum_rejected(self):
        eos,z,s=seed_inputs()
        for value in (float('nan'),float('inf'),0.,-1.):
            with self.subTest(value=value), patch('riogineer_engine.pr_flash.safe_exp',return_value=value):
                with self.assertRaises(ThermodynamicError):stability_restart_seed(eos,z,s)

    def test_invalid_trial_rejected(self):
        eos,z,s=seed_inputs();t=min(s.trials,key=lambda t:t.tpd_RT)
        for w in ((0.,1.),(float('nan'),.5),(.4,.4),(.5,)):
            with self.subTest(w=w),self.assertRaises(ThermodynamicError):
                stability_restart_seed(eos,z,replace(s,trials=(replace(t,composition=w),)))

    def test_ambiguous_or_same_phase_rejected(self):
        eos,z,s=seed_inputs()
        for value in (1.,float('nan'),.9,15.):
            with self.subTest(value=value),patch.object(PengRobinsonEOS,'phase_identification',return_value=value):
                with self.assertRaises(ThermodynamicError):stability_restart_seed(eos,z,s)

    def test_stable_or_unconverged_cannot_seed(self):
        eos,z,s=seed_inputs()
        for changed in (replace(s,stable=True),replace(s,converged=False)):
            with self.assertRaises(ThermodynamicError):stability_restart_seed(eos,z,changed)

    def test_pure_feed_retains_no_restart(self):
        for z in ([1.,0.],[0.,1.]):
            p=run(dict(TARGET,z=z))
            self.assertEqual(p.status,'success_single_phase')
            self.assertEqual(p.diagnostics.initialization.restart_count,0)

    def test_seed_failure_does_not_publish_phases(self):
        p=run(settings=SolverSettings(flash_max_iterations=1))
        self.assertEqual(p.status,'flash_not_converged')
        self.assertEqual(p.phases,())
        self.assertIsNone(p.beta)
        self.assertEqual(p.diagnostics.initialization.restart_count,1)

    def test_failed_restart_rr_is_bounded(self):
        endpoint=RRResult('vapor_tendency',1.,.1,True,0)
        with patch('riogineer_engine.pr_flash.solve_rr',return_value=endpoint) as rr:
            p=run()
        self.assertEqual(rr.call_count,2)
        self.assertEqual(p.status,'rachford_rice_not_converged')
        self.assertEqual(p.phases,())
        self.assertEqual(p.diagnostics.initialization.restart_count,1)

    def test_candidate_order_independent(self):
        eos,z,s=seed_inputs()
        self.assertEqual(stability_restart_seed(eos,z,s),
                         stability_restart_seed(eos,z,replace(s,trials=tuple(reversed(s.trials)))))


if __name__=='__main__':unittest.main()
