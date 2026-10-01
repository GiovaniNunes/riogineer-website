"""Verify captured real-provider runs; full runner reproduction is a separate gate."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmarks.pump_energy.common import ROOT, REFERENCE, PRODUCTION, digest
from benchmarks.pump_energy.compare_production import compare
from benchmarks.pump_energy.scope import ledger, admissible
from riogineer_engine.thermodynamics import MolecularCompositionProvider
from riogineer_engine.components import component


class ProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = json.loads(REFERENCE.read_text())
        cls.prod = json.loads(PRODUCTION.read_text())
        cls.rows = {r['case_id']:r for r in cls.prod['cases']}

    def test_provenance_and_comparisons(self):
        self.assertEqual(self.prod['reference_sha256'], digest(REFERENCE))
        self.assertEqual(self.prod['comparison_source_sha256'], digest(ROOT/'benchmarks/pump_energy/compare_production.py'))
        for path, sha in self.prod['production_source_sha256'].items():
            self.assertEqual(digest(ROOT/path), sha)
        self.assertEqual(self.prod['failed_comparison_count'], 0)
        for r in self.rows.values():
            self.assertTrue(r['comparisons_passed'])

    def test_real_ps_holes_preserved(self):
        for name in ('BUBBLE_BELOW', 'BUBBLE_MINUS_01'):
            r = self.rows[name]['result']
            self.assertEqual((r['status'], r['stage'], r['reason']), ('production_failure', 'PS', 'property_evaluation_failed'))
            self.assertNotIn('outlet', r['states'])
            d = r['diagnostics']['PS']
            self.assertEqual(d['scan_count'], 64)
            self.assertEqual(d['candidate_count'], 1)
            self.assertEqual(d['fresh_final_count'], 0)
            self.assertEqual([t['temperature_K'] for t in d['failures']], [461.9047619047619, 466.6666666666667])
            self.assertTrue(all(t['underlying_status'] == 'flash_not_converged' for t in d['failures']))

    def test_standalone_ph_does_not_rescue_path(self):
        for name in ('BUBBLE_BELOW', 'BUBBLE_MINUS_01'):
            row = self.rows[name]
            d = row['standalone_PH_diagnostic']['diagnostics']
            self.assertEqual(d['scan_count'], 128)
            self.assertEqual(d['status'], 'success')
            self.assertEqual(d['candidate_count'], 1)
            self.assertEqual(d['fresh_final_count'], 1)
            self.assertLessEqual(abs(d['residual']), 1e-6)
            lo, hi = d['selected_bracket_K']
            self.assertTrue(all(not lo <= t['temperature_K'] <= hi for t in d['failures']))
            ref = next(c['result']['states']['outlet'] for c in self.ref['cases'] if c['case_id'] == name)
            actual = row['standalone_PH_diagnostic']['state']
            self.assertLessEqual(abs(actual['T_K']-ref['T_K']), 1e-7)
            self.assertLessEqual(abs(actual['H_eq_J_mol']-ref['H_eq_J_mol']), 1e-6+1e-11*abs(ref['H_eq_J_mol']))
            self.assertEqual(row['result']['status'], 'production_failure')

    def test_identity_scaling_and_conditioning(self):
        for row in self.rows.values():
            r = row['result']
            if 'metrics' not in r:
                continue
            m = r['metrics']
            a, b, c = [r['states'][key] for key in ('inlet', 'isentropic', 'outlet')]
            F = sum(m['component_in_mol_s'])
            budget = 64*sys.float_info.epsilon*max(1., abs(F*a['H_eq_J_mol']), abs(F*c['H_eq_J_mol']))
            self.assertLessEqual(abs(m['energy_identity_residual_W']), budget)
            self.assertEqual(m['component_mass_in_kg_s'], m['component_mass_out_kg_s'])
            self.assertLessEqual(abs(b['S_eq_J_mol_K']-a['S_eq_J_mol_K']), 1e-8)
            self.assertGreaterEqual(m['delta_s_J_mol_K'], -2e-8)
        base = self.rows['CANONICAL']['result']
        for name, scale in [('FLOW5', .05), ('FLOW200', 2.)]:
            r = self.rows[name]['result']
            self.assertEqual(r['states'], base['states'])
            self.assertAlmostEqual(r['metrics']['W_recovered_W'], scale*base['metrics']['W_recovered_W'], places=9)
        for name in ('IDENTITY_BINARY', 'IDENTITY_HEXANE'):
            r = self.rows[name]['result']
            self.assertEqual(r['diagnostics'], {})
            self.assertEqual(r['states']['inlet'], r['states']['outlet'])
            self.assertEqual(r['metrics']['W_recovered_W'], 0.)
        for name in ('DP_10.0', 'DP_0.1', 'DP_0.001'):
            r = self.rows[name]['result']
            self.assertEqual(r['status'], 'unresolved_work')
            self.assertIsNone(r['metrics']['reconstructed_efficiency'])

    def test_label_is_not_critical_guard(self):
        p = self.prod['pure_supercritical_label_probe']
        self.assertEqual(p['classification'], 'single_liquid')
        self.assertTrue(p['PT_diagnostics']['stability']['stable'])
        self.assertGreater(p['PT_diagnostics']['stability']['phase_identification_parameter'], 1.)

    def test_narrow_scope_is_enforceable(self):
        evidence = ledger()
        self.assertEqual(sum(r['admitted_to_proposed_scope'] for r in evidence['rows']), 13)
        for row in evidence['rows']:
            self.assertEqual(admissible(row['inputs'], evidence), row['admitted_to_proposed_scope'])
        base = evidence['rows'][0]['inputs']
        self.assertFalse(admissible(base | dict(T1=300.001), evidence))
        self.assertFalse(admissible(base | dict(z=[1., 0.]), evidence))

    def test_m7_mass_molar_reconstruction(self):
        for c in self.ref['cases']:
            i = c['inputs']
            rates = {name: i['flow']*3.6*z*component(name).molecular_weight
                     for name, z in zip(('methane', 'n_hexane'), i['z'])}
            state = dict(temperature_K=i['T1'], pressure_Pa_abs=i['P1'],
                mass_flow_kg_h=sum(rates.values()), component_mass_flow_kg_h=rates)
            p = MolecularCompositionProvider().enrich(state).composition
            self.assertAlmostEqual(p.molar_flow_kmol_h/3.6, i['flow'], places=10)
            for name, z in zip(('methane', 'n_hexane'), i['z']):
                self.assertAlmostEqual(p.molar_fractions[name], z, places=12)

    def test_comparator_detects_corruption(self):
        c = self.ref['cases'][0]
        result = deepcopy(self.rows[c['case_id']]['result'])
        result['states']['outlet']['H_eq_J_mol'] += 1.
        self.assertFalse(all(r['passed'] for r in compare(c['inputs'], c['result'], result)))


if __name__ == '__main__':
    unittest.main()
