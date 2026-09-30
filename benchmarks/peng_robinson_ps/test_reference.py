"""Frozen independent PS acceptance; never imports production thermodynamics."""
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

import reference as ref
from equilibrium import EntropyPT, TrialFailure
from solver import solve_ps, S_TOL, SCAN_POINTS

FROZEN = json.loads(ref.ARTIFACT.read_text())


class PositiveCases(unittest.TestCase):
    pass


def positive(case):
    def test(self):
        result=solve_ps(**case['input'])
        self.assertEqual(result['status'],'success')
        ref.compare_states(result['solution'],case['forward'])
        self.assertEqual(ref.compact(result),case['inverse'])
        self.assertLessEqual(abs(result['solution']['S_residual_J_mol_K']),S_TOL)
        d=result['diagnostics']
        self.assertEqual(d['scan_evaluations'],SCAN_POINTS)
        self.assertEqual(d['candidate_count'],1)
        self.assertEqual(d['failed_evaluations'],[])
        self.assertEqual(d['final_evaluations'],1)
        self.assertTrue(d['fresh_final'])
    return test


for c in FROZEN['cases']:
    setattr(PositiveCases,'test_'+c['case_id'].lower(),positive(c))


class NegativeCases(unittest.TestCase):
    pass


def negative(case):
    def test(self):
        if case['case_id']=='PURE_COEXISTENCE_GAP':
            result=solve_ps(**case['specification'])
            self.assertTrue(result['diagnostics']['gap_detected'])
            self.assertEqual(result['diagnostics']['candidate_count'],1)
            self.assertGreater(result['diagnostics']['final_bracket']['entropy_span_J_mol_K'],100.)
        else:
            result=ref.run_negative(case['overrides'],FROZEN['cases'][1]['input']['S_target'])
        self.assertEqual(result['status'],case['expected_status'])
        self.assertNotIn('solution',result)
        self.assertEqual(ref.compact(result),case['result'])
        for key in ('T_K','phases','beta','H_eq_J_mol','S_eq_J_mol_K'):
            self.assertNotIn(key,result)
    return test


for c in FROZEN['negative_cases']:
    setattr(NegativeCases,'test_'+c['case_id'].lower(),negative(c))


class StudyTests(unittest.TestCase):
    def test_clean_process_byte_reproduction_twice(self):
        before=ref.ARTIFACT.read_bytes()
        command=[sys.executable,'-B',str(Path(ref.__file__))]
        a=subprocess.run(command,check=True,capture_output=True).stdout
        b=subprocess.run(command,check=True,capture_output=True).stdout
        self.assertEqual(a,b)
        self.assertEqual(before,ref.ARTIFACT.read_bytes())

    def test_ideal_residual_and_equilibrium_entropy(self):
        oracle=EntropyPT()
        for c in FROZEN['cases']:
            s=oracle.evaluate(c['forward']['T_K'],c['input']['P'],c['input']['z'])
            weights={'liquid':1-s['beta'],'vapor':s['beta']}
            entropy=enthalpy=0.
            for k,p in s['phases'].items():
                self.assertAlmostEqual(p['s_J_mol_K'],p['s_ig_J_mol_K']+p['s_res_J_mol_K'],places=11)
                ref.close(p['s_J_mol_K'],p['direct_s_J_mol_K'],'s')
                ref.close(p['h_J_mol'],p['direct_h_J_mol'],'h')
                entropy+=weights[k]*p['s_J_mol_K']; enthalpy+=weights[k]*p['h_J_mol']
            ref.close(s['S_eq_J_mol_K'],entropy,'s')
            ref.close(s['H_eq_J_mol'],enthalpy,'h')

    def test_gibbs_and_fixed_composition_derivative_identities(self):
        oracle=EntropyPT()
        for c in FROZEN['cases']:
            for row in oracle.identities(c['inverse']['solution']).values():
                self.assertLess(abs(row['g_res_identity_error_J_mol']),1e-7)
                self.assertLess(abs(row['dHres_dT_minus_T_dSres_dT_J_mol_K']),2e-5)

    def test_density_candidates_recovery_and_complete_domain(self):
        for c,study in zip(FROZEN['cases'],FROZEN['scan_density']):
            for run in study['runs']:
                self.assertEqual(run['status'],'success')
                self.assertEqual(run['diagnostics']['candidate_count'],1)
                self.assertEqual(run['diagnostics']['successful_scan_evaluations'],run['grid_points'])
                self.assertEqual([p['T_K'] for p in run['diagnostics']['scan_endpoints']],[200.,500.])
                ref.compare_states(run['solution'],c['forward'])

    def test_target_perturbations(self):
        cases={c['case_id']:c for c in FROZEN['cases']}
        for p in FROZEN['target_perturbations']:
            c=cases[p['case_id']]; solution=p['result']['solution']
            self.assertGreater((solution['T_K']-c['forward']['T_K'])*p['delta_S_J_mol_K'],0.)
            self.assertEqual(p['result']['diagnostics']['candidate_count'],1)
            self.assertLessEqual(abs(solution['S_residual_J_mol_K']),S_TOL)

    def test_boundary_continuity_vs_pure_gap(self):
        for c in FROZEN['boundary_continuity']:
            spans=[r['entropy_span_J_mol_K'] for r in c['refinements']]
            self.assertTrue(all(0<b<a for a,b in zip(spans,spans[1:])))
            self.assertLess(spans[-1],2e-5)
        gaps=[r['entropy_span_J_mol_K'] for r in FROZEN['pure_gap']['refinements']]
        self.assertTrue(all(g>100 for g in gaps))

    def test_conditioning_positive_but_not_global_proof(self):
        self.assertGreater(FROZEN['minimum_matrix_slope_J_mol_K2'],.1)
        for c in FROZEN['scan_density']:
            for r in c['runs']:
                self.assertGreater(r['diagnostics']['minimum_scan_slope_J_mol_K2'],0.)

    def test_call_order_after_failure_and_phase_changes(self):
        oracle=EntropyPT()
        for c in reversed(FROZEN['cases']):
            self.assertNotEqual(solve_ps(3e5,[.5,.5],1e6,evaluator=oracle.evaluate)['status'],'success')
            self.assertEqual(ref.compact(solve_ps(**c['input'],evaluator=oracle.evaluate)),c['inverse'])

    def test_direct_equation_root_crosscheck(self):
        for c,r in zip(FROZEN['cases'],FROZEN['cross_method']):
            ref.compare_states(r['result']['solution'],c['forward'])

    def test_absent_phases_not_fabricated(self):
        for c in FROZEN['cases']:
            s=c['inverse']['solution']
            if s['classification']=='single_liquid':
                self.assertEqual(set(s['phases']),{'liquid'})
            if s['classification']=='single_vapor':
                self.assertEqual(set(s['phases']),{'vapor'})

    def test_hole_never_bridged(self):
        r=ref.run_negative({'synthetic':'hole','S_target':0.},0.)
        self.assertEqual(r['diagnostics']['brackets'],[])
        self.assertGreater(len(r['diagnostics']['failed_evaluations']),0)

    def test_nonfinite_and_invalid_controls(self):
        for kw in [dict(P=float('inf')),dict(S_target=float('nan')),dict(z=[float('nan'),0.]),
                   dict(grid_points=True),dict(maxiter=0),dict(xtol=0.)]:
            args=dict(P=3e5,z=[.5,.5],S_target=0.);args.update(kw)
            self.assertEqual(solve_ps(**args)['status'],'invalid_input')

    def test_final_state_is_fresh_not_scan_cache(self):
        count=0
        def evaluator(T,P,z):
            nonlocal count
            count+=1
            if count>64:
                raise TrialFailure('caloric','Synthetic final-evaluation failure')
            return dict(S_eq_J_mol_K=T-300,classification='synthetic')
        r=solve_ps(3e5,[.5,.5],0.,evaluator=evaluator)
        self.assertEqual(r['status'],'property_evaluation_failed')
        self.assertEqual(r['diagnostics']['final_evaluations'],1)
        self.assertNotIn('solution',r)

    def test_frozen_source_hashes(self):
        for path,digest in FROZEN['metadata']['source_sha256'].items():
            self.assertEqual(ref.hashlib.sha256((ref.ROOT/path).read_bytes()).hexdigest(),digest)


if __name__=='__main__':
    unittest.main()
