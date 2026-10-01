"""Focused independent evidence/physics checks; regeneration is a separate gate."""
import ast
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmarks.pump_energy.common import ROOT, HERE, REFERENCE, TOLS, digest, validate


class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REFERENCE.read_text())
        cls.rows = {r['case_id']: r for r in cls.data['cases']}

    def test_complete_candidate_ledger(self):
        self.assertEqual(len(self.rows), 20)
        self.assertEqual(self.data['tolerances'], TOLS)
        self.assertEqual(sum(c['result']['status'] == 'accepted' for c in self.rows.values()), 15)
        self.assertEqual(sum(c['result']['status'] == 'unresolved_work' for c in self.rows.values()), 3)
        self.assertEqual(sum(c['result']['status'] == 'unsupported_phase' for c in self.rows.values()), 2)

    def test_independence_and_source_integrity(self):
        self.assertFalse(self.data['production_numerics_imported'])
        for file, expected in self.data['source_sha256'].items():
            self.assertEqual(digest(ROOT/file), expected, file)
        # Verify the executed helper chain imports no production numerical modules.
        for file in self.data['source_sha256']:
            if file.endswith('.py'):
                tree = ast.parse((ROOT/file).read_text())
                for n in ast.walk(tree):
                    if isinstance(n, ast.ImportFrom):
                        self.assertNotIn('riogineer_engine', n.module or '')
                    elif isinstance(n, ast.Import):
                        self.assertTrue(all('riogineer_engine' not in a.name for a in n.names))

    def test_data_and_units(self):
        self.assertEqual(self.data['kij'], [[0., 0.], [0., 0.]])
        self.assertEqual(self.data['convention']['PR_a'], .45724)
        self.assertEqual(self.data['convention']['PR_b'], .07780)
        self.assertEqual(self.data['units']['power'], 'W')
        self.assertEqual(self.data['dependencies']['thermo'], '0.6.0')

    def test_inverse_scans_and_fresh_residuals(self):
        for c in self.rows.values():
            r = c['result']
            for key, d in r['diagnostics'].items():
                self.assertEqual(d['status'], 'success')
                diag = d['diagnostics']
                self.assertEqual(diag['scan_evaluations'], 64 if key == 'PS' else 128)
                self.assertEqual(len(diag['brackets']), 1)
                self.assertEqual(diag['final_evaluations'], 1)
                self.assertEqual(diag['scan'][0]['T_K'], 200.)
                self.assertEqual(diag['scan'][-1]['T_K'], 500.)
                root = diag['roots'][0]
                residual = root['residual_J_mol_K' if key == 'PS' else 'residual_J_mol']
                self.assertLessEqual(abs(residual), TOLS[key+'_residual'])

    def test_material_and_energy_consistency(self):
        for c in self.rows.values():
            r, i = c['result'], c['inputs']
            if 'metrics' not in r:
                continue
            a, b, o = [r['states'][k] for k in ('inlet', 'isentropic', 'outlet')]
            m = r['metrics']
            for s in (a, b, o):
                self.assertEqual(s['classification'], 'single_liquid')
                self.assertEqual(s['z'], i['z'])
            self.assertEqual(m['component_in_mol_s'], m['component_out_mol_s'])
            self.assertEqual(m['mass_residual_kg_s'], 0.)
            self.assertAlmostEqual(sum(m['component_out_mol_s']), i['flow'], places=10)
            budget = 64*sys.float_info.epsilon*max(1., abs(i['flow']*a['H_eq_J_mol']), abs(i['flow']*o['H_eq_J_mol']))
            self.assertLessEqual(abs(m['energy_identity_residual_W']), budget)
            self.assertLessEqual(abs(m['target_recovered_residual_J_mol']), 1e-6)
            self.assertLessEqual(abs(b['S_eq_J_mol_K']-a['S_eq_J_mol_K']), 1e-8)
            self.assertGreaterEqual(o['S_eq_J_mol_K']-a['S_eq_J_mol_K'], -2e-8)

    def test_identity_and_ideal_efficiency(self):
        for name in ('IDENTITY_BINARY', 'IDENTITY_HEXANE'):
            r = self.rows[name]['result']
            self.assertEqual(r['diagnostics'], {})
            self.assertEqual(r['states']['inlet'], r['states']['outlet'])
            self.assertEqual(r['metrics']['W_recovered_W'], 0.)
            self.assertIsNone(r['metrics']['reconstructed_efficiency'])
        r = self.rows['ETA1']['result']
        self.assertLessEqual(abs(r['states']['isentropic']['T_K']-r['states']['outlet']['T_K']), 1e-7)
        self.assertLessEqual(abs(r['metrics']['delta_s_J_mol_K']), 2e-8)

    def test_flow_scaling(self):
        base = self.rows['CANONICAL']['result']
        for name, factor in [('FLOW5', .05), ('FLOW200', 2.)]:
            r = self.rows[name]['result']
            self.assertEqual(r['states'], base['states'])
            self.assertAlmostEqual(r['metrics']['W_recovered_W'], factor*base['metrics']['W_recovered_W'], places=9)

    def test_work_conditioning_and_cross_method(self):
        self.assertTrue(self.rows['DP_1000.0']['result']['metrics']['work_resolved'])
        for name in ('DP_10.0', 'DP_0.1', 'DP_0.001'):
            m = self.rows[name]['result']['metrics']
            self.assertFalse(m['work_resolved'])
            self.assertGreater(m['delta_h_J_mol'], 0.)
            self.assertIsNone(m['reconstructed_efficiency'])
        for row in self.data['cross_method']:
            self.assertEqual(row['PS']['status'], 'success')
            self.assertEqual(row['PH']['status'], 'success')
            self.assertLessEqual(abs(row['difference_from_primary_J_mol']), 2e-6)

    def test_boundary_and_supercritical_counterexample(self):
        binary, pure = self.data['boundary_probes']
        self.assertEqual(binary['probes'][2]['state']['classification'], 'single_liquid')
        self.assertEqual(binary['probes'][4]['state']['classification'], 'vapor_liquid')
        self.assertNotEqual(pure['probes'][2]['state']['classification'], pure['probes'][4]['state']['classification'])
        probe = self.data['pure_supercritical_label_probe']
        self.assertGreater(probe['state']['T_K'], probe['pure_Tc_K'])
        self.assertGreater(probe['state']['P_Pa_abs'], probe['pure_Pc_Pa_abs'])
        self.assertEqual(probe['state']['classification'], 'single_liquid')
        for row in self.data['endpoint_boundaries']:
            self.assertNotIn('unavailable', row)
            self.assertGreater(row['relative_pressure_margin'], 0.)
            self.assertEqual(row['probes'][1]['classification'], 'single_liquid')
            self.assertNotEqual(row['probes'][0]['classification'], 'single_liquid')

    def test_benchmark_input_guards(self):
        base = self.rows['CANONICAL']['inputs']
        examples = [('flow', 0., 'invalid_flow'), ('flow', float('nan'), 'invalid_flow'),
            ('P1', -1., 'invalid_pressure'), ('P2', 1e6, 'invalid_pressure'),
            ('P2', float('inf'), 'invalid_pressure'), ('eta', 0., 'invalid_efficiency'),
            ('eta', 1.01, 'invalid_efficiency'), ('T1', 199., 'temperature_domain_invalid'),
            ('T1', 501., 'temperature_domain_invalid'), ('z', [.4, .4], 'invalid_composition'),
            ('z', [-.1, 1.1], 'invalid_composition'),
            ('component_ids', ['methane', 'water'], 'unsupported_components'),
            ('kij', [[0., .1], [.1, 0.]], 'unsupported_bip')]
        for key, value, expected in examples:
            with self.subTest(key=key, value=value):
                self.assertEqual(validate(base | {key:value}), expected)


if __name__ == '__main__':
    unittest.main()
