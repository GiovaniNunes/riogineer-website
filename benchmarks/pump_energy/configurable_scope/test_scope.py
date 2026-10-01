"""Focused configurable-scope qualification and clearly synthetic guard tests."""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from benchmarks.pump_energy.configurable_scope.policy import ROOT,HERE,REFERENCE,PRODUCTION,inputs,state_guard,work_policy
from benchmarks.pump_energy.configurable_scope.runtime import admissibility
from benchmarks.pump_energy.common import digest


class ScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref=json.loads(REFERENCE.read_text());cls.prod=json.loads(PRODUCTION.read_text())
        cls.data=list(zip(cls.ref['cases'],cls.prod['cases']))
        cls.base=cls.data[0]

    def test_sources_and_prior_preserved(self):
        for doc in (self.ref,self.prod):
            for path,sha in doc['source_sha256'].items():self.assertEqual(digest(ROOT/path),sha)
        for path,sha in self.prod['production_source_sha256'].items():self.assertEqual(digest(ROOT/path),sha)
        self.assertEqual(digest(REFERENCE),self.prod['reference_sha256'])
        self.assertEqual(digest(ROOT/'benchmarks/pump_energy/liquid_pump_path_reference.json'),self.ref['prior_reference_sha256'])
        self.assertEqual(digest(ROOT/'benchmarks/pump_energy/production_comparison.json'),self.prod['prior_production_sha256'])
        self.assertFalse(self.ref['production_numerics_imported'])

    def test_coverage_and_all_comparisons(self):
        self.assertEqual(len(self.data),46)
        self.assertEqual(sum(r['group']=='holdout' for r,p in self.data),8)
        self.assertEqual(sum(r['group']=='corner' for r,p in self.data),16)
        self.assertEqual(self.prod['failed_comparisons'],0)
        self.assertEqual(sum(admissibility(r['inputs'],p['result'],p['witnesses'])['accepted'] for r,p in self.data),38)

    def test_off_grid_cases_use_actual_states(self):
        for r,p in self.data:
            if r['group']=='holdout':
                self.assertTrue(admissibility(r['inputs'],p['result'],p['witnesses'])['accepted'])
                self.assertEqual(p['result']['states']['inlet']['T_K'],r['inputs']['T1'])
                self.assertEqual(p['result']['states']['outlet']['P_Pa_abs'],r['inputs']['P2'])
                self.assertTrue(p['evidence_origin'].startswith('extension:'))

    def test_full_scans_and_no_holes(self):
        for r,p in self.data:
            for key,d in p['result']['diagnostics'].items():
                self.assertEqual(d['status'],'success');self.assertEqual(d['candidate_count'],1)
                self.assertEqual(d['scan_count'],64 if key=='PS' else 128)
                self.assertEqual(d['settings']['temperature_bounds_K'],[200.,500.])
                self.assertEqual(d['fresh_final_count'],1);self.assertEqual(d['failures'],[])
                self.assertLessEqual(abs(d['residual']),1e-8 if key=='PS' else 1e-6)

    def test_boundary_evidence_and_reserve(self):
        b=self.ref['boundary'];self.assertEqual(len(b['rows']),149)
        for row in b['rows']:
            self.assertEqual(row['status'],'available')
            self.assertEqual((row['lower_phase'],row['upper_phase'],row['witness_phase']),('vapor_liquid','single_liquid','single_liquid'))
            self.assertGreater(row['phase_composition_gap'],.4)
            self.assertGreater(row['Z_gap'],.3)
            self.assertLess(abs(row['derivative_Pa_K']),b['engineering_slope_allowance_Pa_K'])
        self.assertGreater(16e6-b['sampled_max_bubble_Pa']-25000-1000,2e6)
        eq=json.loads((HERE/'boundary_equations.json').read_text())
        self.assertEqual(eq['reference_sha256'],digest(REFERENCE))
        for row in eq['rows']:
            self.assertEqual(row['status'],'accepted')
            self.assertLessEqual(max(map(abs,row['fugacity_residual'])),2e-10)
            self.assertLessEqual(abs(row['library_pressure_difference_Pa']),1000.)

    def test_alternate_boundary_branch_retained(self):
        rows=json.loads((HERE/'boundary_refinement.json').read_text())['rows']
        alternate=[x for x in rows if 'original_inverse_T_K' in x]
        self.assertEqual(len(alternate),4)
        for x in alternate:
            self.assertGreater(x['original_inverse_T_K'],370.)
            self.assertLess(abs(x['local_branch_error_K']),1e-7)

    def test_small_work_and_residual_sensitivity(self):
        for r,p in self.data:
            policy=admissibility(r['inputs'],p['result'],p['witnesses'])
            if r['group']=='conditioning':
                dp=r['inputs']['P2']-r['inputs']['P1']
                self.assertEqual(policy['accepted'],dp>=10000.)
            if policy['accepted'] and r['inputs']['P2']!=r['inputs']['P1']:
                self.assertLessEqual(policy['work']['ratio'],1e-4)
                error=abs(p['result']['metrics']['delta_h_J_mol']-r['result']['metrics']['delta_h_J_mol'])
                self.assertLessEqual(error,policy['work']['budget_J_mol'])
        for r in self.ref['sensitivity']:
            for t in r['trials']:
                self.assertEqual(t['PS']['status'],'success');self.assertEqual(t['PH']['status'],'success')
                self.assertLessEqual(abs(t['ps_dh_J_mol']),370e-8)
                self.assertLessEqual(abs(t['ph_dh_J_mol']),1.01e-6)

    def test_flow_scaling_interval(self):
        for r,p in self.data:
            for f in p['flow_checks']:
                self.assertTrue(all(q['passed'] for q in f['checks']))
            if p['policy']['accepted']:
                # New unlisted flow value: scope has no flow allowlist or inverse dependency.
                i=r['inputs']|dict(flow=91.234)
                q=admissibility(i,p['result'],p['witnesses'])
                self.assertTrue(q['accepted'])
                self.assertAlmostEqual(q['W_recovered_W']/91.234,p['result']['metrics']['W_recovered_W']/100.,places=9)

    def test_identity_and_representation(self):
        for r,p in self.data:
            if r['group']=='identity':
                q=admissibility(r['inputs'],p['result'],p['witnesses'])
                self.assertTrue(q['accepted']);self.assertEqual(q['W_recovered_W'],0.)
                self.assertEqual(p['result']['diagnostics'],{})
                self.assertIsNone(q['work']['reconstructed_eta'])
                i=r['inputs']|dict(P2=math.nextafter(r['inputs']['P1'],math.inf))
                self.assertEqual(inputs(i),'positive_rise_below_floor')
        r,p=self.base;i=r['inputs']
        self.assertEqual(200.*1e5,20e6) # explicit bar-absolute -> Pa normalization
        self.assertIsNone(inputs(i|dict(P2=i['P1']+10000.)))
        self.assertEqual(inputs(i|dict(P2=math.nextafter(i['P1']+10000.,-math.inf))),'positive_rise_below_floor')

    def test_outside_range_and_invalid_inputs(self):
        r,p=self.base; i=r['inputs']
        for patch in [dict(T1=299.99),dict(T1=350.01),dict(P1=19e6),dict(P1=25.1e6),
            dict(P2=30.1e6),dict(P2=i['P1']-1),dict(eta=.59),dict(eta=1.01),
            dict(flow=4.99),dict(flow=200.01),dict(flow=0),dict(flow=float('nan')),
            dict(P2=float('inf')),dict(z=[.50001,.49999]),dict(z=[1.,0.]),
            dict(kij=[[0.,.01],[.01,0.]]),dict(component_ids=['methane','water'])]:
            with self.subTest(patch=patch):
                self.assertFalse(admissibility(i|patch,p['result'],p['witnesses'])['accepted'])
        self.assertFalse(admissibility({},p['result'],p['witnesses'])['accepted'])

    def test_synthetic_phase_and_guard_boundaries(self):
        r,p=self.base;s=deepcopy(p['result']['states']['inlet']);w=deepcopy(p['witnesses']['inlet'])
        for T,expected in [(300.,True),(370.,True),(math.nextafter(300.,-math.inf),False),(math.nextafter(370.,math.inf),False)]:
            a=s|dict(T_K=T);b=w|dict(T_K=T)
            self.assertEqual(state_guard(a,b) is None,expected)
        self.assertIsNotNone(state_guard(s|dict(P_Pa_abs=math.nextafter(20e6,-math.inf)),w))
        for phase in ('single_vapor','vapor_liquid'):
            self.assertIsNotNone(state_guard(s|dict(classification=phase),w))
        self.assertIsNotNone(state_guard(s,w|dict(P_Pa_abs=16e6+1)))
        # Actual prior supercritical methane counterexample, rejected by fixed recipe.
        old=json.loads((ROOT/'benchmarks/pump_energy/production_comparison.json').read_text())
        self.assertIsNotNone(state_guard(old['pure_supercritical_label_probe'],w))

    def test_synthetic_inverse_and_finite_failures(self):
        r,p=self.base
        for kind in ('PS_failure','ambiguous','no_final','wrong_bounds','nan_witness','phase_payload','entropy'):
            result=deepcopy(p['result']);w=deepcopy(p['witnesses'])
            if kind=='PS_failure':result['stage']='PS';result['status']='production_failure'
            elif kind=='ambiguous':result['diagnostics']['PS']['candidate_count']=2
            elif kind=='no_final':result['diagnostics']['PH']['fresh_final_count']=0
            elif kind=='wrong_bounds':result['diagnostics']['PS']['settings']['temperature_bounds_K']=[250.,400.]
            elif kind=='nan_witness':w['inlet']['H_eq_J_mol']=float('nan')
            elif kind=='phase_payload':result['states']['outlet']['phases']['liquid']['Z']=-1.
            elif kind=='entropy':result['states']['outlet']['S_eq_J_mol_K']-=1.
            self.assertFalse(admissibility(r['inputs'],result,w)['accepted'],kind)

    def test_runtime_conditioning_rejection_without_reference(self):
        r,p=self.base;s=deepcopy(p['result']['states'])
        h=s['inlet']['H_eq_J_mol'];s['isentropic']['H_eq_J_mol']=h+1e-8;s['outlet']['H_eq_J_mol']=h+2e-8
        self.assertEqual(work_policy(r['inputs'],s)['status'],'unresolved')


if __name__=='__main__':unittest.main()
