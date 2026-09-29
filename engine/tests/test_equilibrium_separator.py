"""M9 integration gates, with independent frozen M8 expected flow arithmetic."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
import unittest
from unittest.mock import patch
from riogineer_engine.core import ROOT, Invalid, build_flowsheet, calculate, semantic_hash, validate_requirements
from riogineer_engine.milestone9 import requirements
from riogineer_engine.components import component
from riogineer_engine.network_models import MODELS, state_from_rates
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.thermodynamics import Composition

REFERENCE = json.loads((ROOT/'benchmarks/peng_robinson/methane_nhexane_pr_reference.json').read_text())
IDS = ('methane', 'n_hexane')


class EquilibriumSeparatorTests(unittest.TestCase):
    def run_case(self, r=None):
        f = build_flowsheet(r or requirements())
        return f, calculate(f)

    def test_fixture_mass_basis_and_round_trip_against_independent_reference(self):
        r = requirements()
        self.assertEqual(r, json.loads((ROOT/'contracts/examples/milestone-9-requirements.json').read_text()))
        f, out = self.run_case(r)
        feed = out['streams']['HYDROCARBON_FEED']
        self.assertEqual(feed['component_mass_flow_kg_h'], {'methane': 8021.4, 'n_hexane': 43087.68})
        self.assertAlmostEqual(feed['mass_flow_kg_h'], 51109.08, delta=1e-10)
        self.assertEqual(feed['properties']['component_molar_flow']['value'], dict.fromkeys(IDS, 500))
        self.assertEqual(feed['properties']['molar_flow']['value'], 1000)
        self.assertEqual(feed['properties']['molar_composition']['value'], dict.fromkeys(IDS, .5))
        t = out['equipment'][0]['thermodynamics']
        b = REFERENCE['cases'][1]
        self.assertEqual((t['classification'], t['status']), ('vapor_liquid', 'success_two_phase'))
        self.assertAlmostEqual(t['beta'], b['beta'], delta=1e-9)
        self.assertGreater(t['iterations'], 0)
        self.assertLess(max(abs(v) for v in t['fugacity_residual'].values()), 1e-9)
        self.assertLess(abs(t['rachford_rice_residual']), 1e-10)
        self.assertLess(max(abs(v) for v in t['material_reconstruction_residual'].values()), 1e-10)
        self.assertAlmostEqual(t['vapor_molar_flow_kmol_h'] + t['liquid_molar_flow_kmol_h'], 1000, delta=1e-8)
        for phase, suffix in [('liquid', 'L'), ('vapor', 'V')]:
            self.assertAlmostEqual(t['Z_'+suffix], b[phase]['Z'], delta=1e-9)
        for i, c in enumerate(IDS):
            self.assertAlmostEqual(t['final_K'][c], b['K'][i], delta=1e-8)
        D = lambda v: Decimal(str(v))
        for phase, stream, vector, fraction in [('vapor', 'VAPOR_PRODUCT', 'y', D(b['beta'])), ('liquid', 'LIQUID_PRODUCT', 'x', 1-D(b['beta']))]:
            s = out['streams'][stream]
            expected_total_mass = Decimal(0)
            for i, c in enumerate(IDS):
                expected_n = Decimal(1000) * fraction * D(b[phase]['composition'][i])
                self.assertEqual(component(c).molecular_weight, REFERENCE['components'][i]['MW_kg_kmol'])
                expected_m = expected_n * D(component(c).molecular_weight)
                expected_total_mass += expected_m
                self.assertAlmostEqual(s['component_mass_flow_kg_h'][c], float(expected_m), delta=1e-8)
                self.assertAlmostEqual(s['properties']['component_molar_flow']['value'][c], float(expected_n), delta=1e-8)
                self.assertAlmostEqual(s['properties']['molar_composition']['value'][c], b[phase]['composition'][i], delta=1e-9)
                self.assertAlmostEqual(s['properties']['molar_composition']['value'][c], t[vector][c], delta=1e-12)
            self.assertAlmostEqual(s['mass_flow_kg_h'], float(expected_total_mass), delta=2e-8)
            self.assertAlmostEqual(s['properties']['molar_flow']['value']/1000, float(fraction), delta=1e-12)
        for s in out['streams'].values():
            self.assertEqual((s['temperature_K'], s['pressure_Pa_abs']), (300, 300000))
            self.assertIsNone(s['enthalpy_flow_W'])
            for key in ('density', 'gas_volumetric_flow', 'oil_volumetric_flow', 'water_volumetric_flow'):
                self.assertEqual(s['properties'][key]['status'], 'not_calculated')
                self.assertIsNone(s['properties'][key]['value'])
        self.assertEqual(out['balances']['energy']['status'], 'not_calculated')
        self.assertIsNone(out['equipment'][0]['duty_W'])
        self.assertIsNone(out['equipment'][0]['work_W'])
        self.assertEqual(out['equipment'][0]['material_streams'], dict(inlet='HYDROCARBON_FEED', vapor='VAPOR_PRODUCT', liquid='LIQUID_PRODUCT'))
        self.assertLess(abs(out['balances']['mass']['total_residual_kg_h']), 2e-8)
        for c in IDS:
            self.assertLess(abs(t['component_molar_residual_kmol_h'][c]), 1e-8)
            self.assertLess(abs(t['component_mass_residual_kg_h'][c]), 1e-8)

    def test_single_phases_keep_declared_zero_streams_without_fabricated_properties(self):
        for pressure, present, absent in [(30000000, 'liquid', 'vapor'), (1000, 'vapor', 'liquid')]:
            with self.subTest(pressure=pressure):
                f, out = self.run_case(requirements(pressure))
                t = out['equipment'][0]['thermodynamics']
                self.assertEqual(t['classification'], 'single_'+present)
                feed = out['streams']['HYDROCARBON_FEED']
                active = out['streams'][present.upper()+'_PRODUCT']
                zero = out['streams'][absent.upper()+'_PRODUCT']
                self.assertEqual(active, feed)
                self.assertEqual(zero['component_mass_flow_kg_h'], dict.fromkeys(IDS, 0))
                self.assertEqual(zero['mass_flow_kg_h'], 0)
                self.assertEqual(zero['properties']['component_molar_flow']['value'], dict.fromkeys(IDS, 0))
                self.assertEqual(zero['properties']['molar_flow']['value'], 0)
                for name in ('molar_composition', 'molecular_mass'):
                    self.assertEqual(zero['properties'][name]['status'], 'not_calculated')
                    self.assertIsNone(zero['properties'][name]['value'])
                self.assertIsNone(t['x' if absent == 'liquid' else 'y'])
                self.assertIsNone(t['Z_L' if absent == 'liquid' else 'Z_V'])
                self.assertIsNone(t['phi_L' if absent == 'liquid' else 'phi_V'])
                self.assertIsNone(t['final_K'])
                self.assertEqual(out['balances']['mass']['total_residual_kg_h'], 0)
                self.assertEqual(len(f['streams']), 3)

    def test_actual_mass_temperature_pressure_reach_provider(self):
        original = PengRobinsonProvider.flash_PT
        captured = []
        def capture(provider, state, bip):
            captured.append(state)
            return original(provider, state, bip)
        _, baseline = self.run_case()
        for field, value in [('temperature_K', 305), ('pressure_Pa_abs', 360000), ('component_mass_flow_kg_h', {'methane': 600*16.0428, 'n_hexane': 400*86.17536})]:
            r = requirements()
            r['feeds'][0]['state'][field] = value
            with patch.object(PengRobinsonProvider, 'flash_PT', capture):
                _, out = self.run_case(r)
            s = captured[-1]
            self.assertIsInstance(s.composition, Composition)
            self.assertEqual(s.temperature_K, r['feeds'][0]['state']['temperature_K'])
            self.assertEqual(s.pressure_Pa_abs, r['feeds'][0]['state']['pressure_Pa_abs'])
            self.assertEqual(dict(s.composition.component_mass_flow_kg_h), r['feeds'][0]['state']['component_mass_flow_kg_h'])
            self.assertAlmostEqual(s.composition.molar_fractions['methane'], .6 if isinstance(value, dict) else .5)
            self.assertNotEqual(out['equipment'][0]['thermodynamics']['beta'], baseline['equipment'][0]['thermodynamics']['beta'])
            self.assertEqual(out['equipment'][0]['thermodynamics']['classification'], 'vapor_liquid')
            self.assertEqual(out['balances']['mass']['status'], 'passed')

    def test_build_never_flashes_and_numbers_are_stable(self):
        with patch.object(PengRobinsonProvider, 'flash_PT', side_effect=AssertionError('PFD must not flash')):
            r = requirements()
            validate_requirements(r)
            f = build_flowsheet(r)
            for key in ('equipment', 'streams', 'connections', 'sinks', 'components'):
                r[key].reverse()
            reordered = build_flowsheet(r)
        numbers = lambda f: {s['id']: s['engineering_number'] for s in f['streams']}
        self.assertEqual(numbers(f), {'HYDROCARBON_FEED': 1, 'LIQUID_PRODUCT': 2, 'VAPOR_PRODUCT': 3})
        self.assertEqual(numbers(f), numbers(reordered))
        hashed = semantic_hash(f)
        for key in ('streams', 'connections', 'equipment', 'boundaries'):
            f[key].reverse()
        f['presentation']['layout'] = 'compact'
        self.assertEqual(semantic_hash(f), hashed)
        before = deepcopy(f)
        first, second = calculate(f), calculate(f)
        self.assertEqual(first['streams'], second['streams'])
        self.assertEqual(first['equipment'], second['equipment'])
        self.assertEqual(first['input_sha256'], semantic_hash(f))
        self.assertEqual(first['input_sha256'], second['input_sha256'])
        self.assertEqual(f, before)
        self.assertEqual(numbers(f), numbers(reordered))

    def test_invalid_specs_rejected_before_calculation(self):
        variants = []
        for field in ('temperature_K', 'pressure_Pa_abs'):
            r = requirements(); r['feeds'][0]['state'][field] = 0; variants.append(r)
        r = requirements(); r['feeds'][0]['state']['component_mass_flow_kg_h']['methane'] = -1; variants.append(r)
        r = requirements(); del r['equipment'][0]['parameters']['property_package']; variants.append(r)
        r = requirements(); r['equipment'][0]['parameters']['bip']['values'][0][1] = .1; variants.append(r)
        for c in ('water', 'unknown'):
            r = requirements(); r['components'].append(c); r['feeds'][0]['state']['component_mass_flow_kg_h'][c] = 1; variants.append(r)
        for r in variants:
            with self.assertRaises(Invalid): validate_requirements(r)
        f = build_flowsheet(requirements()); f['equipment'][0]['ports'].append(dict(id='water', direction='out', kind='material'))
        with self.assertRaises(Invalid): calculate(f)

    def test_water_and_unknown_direct_equipment_fail_before_provider(self):
        unit = build_flowsheet(requirements())['equipment'][0]
        for c in ('water', 'unknown'):
            feed = state_from_rates(dict(methane=8021.4, n_hexane=43087.68, **{c: 1}), 300, 300000, None)
            with patch.object(PengRobinsonProvider, 'flash_PT', side_effect=AssertionError('Must not execute')):
                with self.assertRaisesRegex(ValueError, 'methane/n_hexane|Unknown'):
                    MODELS[unit['type']]['execute'](unit, {'inlet': feed}, None)

    def test_nonconvergence_and_all_failure_statuses_abort_network(self):
        original = PengRobinsonProvider.flash_PT
        def fail(provider, state, bip):
            return original(provider, state, bip, SolverSettings(flash_max_iterations=1))
        f = build_flowsheet(requirements())
        with patch.object(PengRobinsonProvider, 'flash_PT', fail):
            with self.assertRaisesRegex(Invalid, 'SEP_PR_1: peng_robinson@1.0: PT flash flash_not_converged.*iterations=1'):
                calculate(f)
        for status in ('invalid_input', 'unsupported_components', 'stability_not_converged', 'rachford_rice_not_converged', 'numerical_domain_error'):
            def failed(provider, state, bip):
                return replace(original(provider, state, bip), status=status, classification=None, phases=(), beta=None)
            with patch.object(PengRobinsonProvider, 'flash_PT', failed):
                with self.assertRaisesRegex(Invalid, status): calculate(f)


if __name__ == '__main__':
    unittest.main()
