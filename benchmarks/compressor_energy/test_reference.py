"""Independent compressor acceptance; no production imports and no evidence writes."""
import ast
import copy
import json
from pathlib import Path
import unittest

try:
    from . import reference as ref
except ImportError:
    import reference as ref


class CompressorReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=ref.ARTIFACT.read_bytes()
        cls.frozen=json.loads(cls.before)
        cls.fresh=ref.build()
        cls.cases={c['case_id']:c for c in cls.fresh['cases']}
        cls.canonical=cls.cases['CANONICAL']

    def test_frozen_byte_reproduction(self):
        self.assertEqual(self.before.decode(),ref.encode(self.fresh))
        self.assertEqual(self.before,ref.ARTIFACT.read_bytes())

    def test_canonical_complete_sequence(self):
        r=self.canonical['result'];i=self.canonical['inputs']
        self.assertTrue(r['accepted_outlet'])
        self.assertGreater(r['H2_target_J_mol'],r['isentropic']['H_eq_J_mol'])
        self.assertGreater(r['isentropic']['H_eq_J_mol'],r['inlet']['H_eq_J_mol'])
        ref.audit(i,r)

    def test_fresh_inlet(self):
        i=self.canonical['inputs']
        self.assertEqual(ref.EntropyPT().evaluate(i['T1'],i['P1'],i['z']),self.canonical['result']['inlet'])

    def test_fresh_ps_and_ph_residuals(self):
        for c in self.fresh['cases']+self.fresh['thermodynamic_studies']:
            r=c['result'];i=c['inputs'];o=ref.EntropyPT()
            b=o.evaluate(r['isentropic']['T_K'],i['P2'],i['z'])
            d=o.evaluate(r['outlet']['T_K'],i['P2'],i['z'])
            self.assertLessEqual(abs(b['S_eq_J_mol_K']-r['inlet']['S_eq_J_mol_K']),1e-8)
            self.assertLessEqual(abs(d['H_eq_J_mol']-r['H2_target_J_mol']),1e-6)

    def test_all_energy_efficiency_and_conservation_checks(self):
        for c in self.fresh['cases']+self.fresh['thermodynamic_studies']:
            with self.subTest(case=c['case_id']):ref.audit(c['inputs'],c['result'])

    def test_efficiency_series(self):
        rows=sorted([self.canonical]+[c for c in self.fresh['cases'] if c['group']=='efficiency'],key=lambda c:c['inputs']['eta'])
        self.assertEqual([c['inputs']['eta'] for c in rows],[.6,.7,.75,.8,.85,.9,1.])
        for a,b in zip(rows,rows[1:]):
            self.assertEqual(a['result']['isentropic'],b['result']['isentropic'])
            for field in ['H2_target_J_mol','fluid_power_W']:
                self.assertGreater(a['result'][field],b['result'][field])
            self.assertGreater(a['result']['outlet']['T_K'],b['result']['outlet']['T_K'])

    def test_pressure_ratio_series(self):
        rows=sorted([self.canonical]+[c for c in self.fresh['cases'] if c['group']=='pressure'],key=lambda c:c['inputs']['P2'])
        self.assertEqual([c['inputs']['P2']/c['inputs']['P1'] for c in rows],[1.5,2.,3.,5.,8.])
        for a,b in zip(rows,rows[1:]):
            for field in ['delta_H_is_J_mol','delta_H_actual_J_mol','fluid_power_W']:
                self.assertGreater(b['result'][field],a['result'][field])

    def test_flow_scaling(self):
        base=self.canonical['result'];double=self.cases['FLOW_200.0']['result']
        for field in ['inlet','isentropic','outlet','H2_target_J_mol']:
            self.assertEqual(base[field],double[field])
        self.assertEqual(double['fluid_power_W'],2*base['fluid_power_W'])
        for c in self.fresh['flow_scaling']:self.assertLessEqual(c['absolute_error_W'],c['allowance_W'])

    def test_ideal_limit(self):
        c=self.cases['ETA_1.0'];r=c['result']
        self.assertEqual(r['H2_target_J_mol'],r['isentropic']['H_eq_J_mol'])
        self.assertLessEqual(abs(r['outlet']['T_K']-r['isentropic']['T_K']),1e-7)
        self.assertLessEqual(abs(r['outlet']['S_eq_J_mol_K']-r['inlet']['S_eq_J_mol_K']),2e-8)

    def test_entropy_generation(self):
        for c in self.fresh['cases']:
            if c['inputs']['eta']<1:self.assertGreater(c['result']['delta_S_actual_J_mol_K'],0)

    def test_phase_transparency_and_service_boundary(self):
        for c in self.fresh['cases']:
            for k in ['inlet','isentropic','outlet']:self.assertEqual(c['result'][k]['classification'],'single_vapor')
        c=self.fresh['thermodynamic_studies'][0]
        for k in ['inlet','isentropic','outlet']:
            self.assertEqual(c['result'][k]['classification'],'vapor_liquid')
            self.assertGreater(c['result'][k]['beta'],0)
            self.assertLess(c['result'][k]['beta'],1)
        self.assertEqual(c['inputs']['service'],'thermodynamic_only')
        i=dict(c['inputs']);i.pop('service')
        self.assertEqual(ref.calculate(**i)['status'],'compressor_state_invalid')

    def test_pure_component_vapor_cases(self):
        for name in ['PURE_METHANE','PURE_HEXANE']:
            self.assertTrue(self.cases[name]['result']['accepted_outlet'])

    def test_boundary_case(self):
        c=self.cases['BOUNDARY_VAPOR'];i=c['inputs'];o=ref.EntropyPT()
        dew=o.flash.flash(P=i['P1'],VF=1.,zs=i['z']).T
        self.assertAlmostEqual(i['T1']-dew,2.,places=10)
        self.assertEqual(c['result']['inlet']['classification'],'single_vapor')

    def test_scan_controls_and_single_candidates(self):
        for c in self.fresh['cases']:
            r=c['result']
            self.assertEqual(r['PS']['scan_count'],64)
            self.assertEqual(r['PH']['scan_count'],128)
            self.assertEqual(r['PS']['candidate_count'],1)
            self.assertEqual(r['PH']['candidate_count'],1)
            self.assertEqual(r['PH']['final_evaluations'],1)
            self.assertTrue(r['PS']['fresh_final'])

    def test_direct_equation_alternative_root_cross_checks(self):
        self.assertEqual(len(self.fresh['cross_method']),len(self.fresh['cases'])+1)
        for c in self.fresh['cross_method']:
            for check in c['checks']:self.assertLessEqual(check['absolute_error'],check['allowance'])

    def test_call_order_independence(self):
        self.assertEqual({c['after'] for c in self.fresh['call_order']},{'positive','low_efficiency','ideal','invalid','PS_failure','PH_failure'})
        self.assertTrue(all(c['byte_identical'] for c in self.fresh['call_order']))

    def test_gap_semantics(self):
        negatives={c['case_id']:c for c in self.fresh['negative_cases']}
        self.assertTrue(negatives['PS_GAP']['result']['solver_failure']['diagnostics']['gap_detected'])
        self.assertEqual(negatives['PS_GAP']['result']['solver_failure']['status'],'ps_nonconvergence')
        self.assertEqual(negatives['PH_GAP']['result']['solver_failure']['status'],'ph_nonconvergence')

    def test_ambiguity_and_property_hole_semantics(self):
        negatives={c['case_id']:c for c in self.fresh['negative_cases']}
        for name,status in [('PS_AMBIGUOUS','ambiguous_ps_root'),('PS_HOLE','property_evaluation_failed')]:
            self.assertEqual(negatives[name]['result']['solver_failure']['status'],status)

    def test_unbracketed_cases_are_not_synthetic(self):
        for c in self.fresh['negative_cases']:
            if c['case_id'].endswith('UNBRACKETED'):
                self.assertFalse(c['synthetic'])
                self.assertIn('target_not_bracketed',c['result']['solver_failure']['status'])

    def test_reconstruction_detects_corrupt_outlet(self):
        r=copy.deepcopy(self.canonical['result']);r['outlet']['H_eq_J_mol']+=.01
        with self.assertRaises(AssertionError):ref.audit(self.canonical['inputs'],r)

    def test_reconstruction_detects_corrupt_power(self):
        r=copy.deepcopy(self.canonical['result']);r['fluid_power_W']+=1.
        with self.assertRaises(AssertionError):ref.audit(self.canonical['inputs'],r)

    def test_reference_generation_has_no_production_imports(self):
        paths=[ref.HERE/'reference.py',ref.HERE/'solver.py']
        paths += [ref.ROOT/p for p in self.fresh['metadata']['source_sha256'] if p.endswith('.py')]
        for path in paths:
            tree=ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):self.assertNotIn('riogineer_engine',node.module or '')
                if isinstance(node,ast.Import):
                    for alias in node.names:self.assertNotIn('riogineer_engine',alias.name)

    def test_provenance_hashes(self):
        for name,sha in self.frozen['metadata']['source_sha256'].items():
            self.assertEqual(ref.digest(ref.ROOT/name),sha)


# One independently reported test per negative specification, including nonfinite
# variants. A subtest-only count must not obscure failure-matrix coverage.
def negative_test(spec):
    name,patch,status,stage=spec
    def test(self):
        result=ref.compact(ref.run_negative(patch))
        expected=next(c for c in self.frozen['negative_cases'] if c['case_id']==name)
        self.assertEqual(result,expected['result'])
        self.assertEqual(result['status'],status)
        self.assertEqual(result['failure_stage'],stage)
        self.assertFalse(result['accepted_outlet'])
        for key in ['inlet','isentropic','outlet','fluid_power_W','H2_target_J_mol']:
            self.assertNotIn(key,result)
    return test


for index,spec in enumerate(ref.negative_specs()):
    setattr(CompressorReferenceTests,'test_negative_'+str(index).zfill(2),negative_test(spec))

if __name__=='__main__':unittest.main()
