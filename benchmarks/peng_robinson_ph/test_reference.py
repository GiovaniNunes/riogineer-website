"""Independent numerical acceptance and explicit PH failure semantics."""
import inspect
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import reference as ref
from equilibrium import IndependentPT, TrialFailure
from solver import solve_ph

FROZEN=json.loads(ref.ARTIFACT.read_text())


class RoundTrips(unittest.TestCase):
    """Each positive case runs a fresh PH solve against the frozen oracle."""


def make_case(case):
    def test(self):
        i=case['input']
        result=solve_ph(i['P_Pa_abs'],i['z'],i['H_target_J_mol'],bounds=i['T_bounds_K'])
        self.assertEqual(result['status'],'success',result['message'])
        s=result['solution']
        ref.compare_states(s,case['forward'])
        ref.compare_states(s,case['inverse']['solution'])
        self.assertLessEqual(abs(s['H_residual_J_mol']),ref.H_TOL)
        for p in s['phases'].values():
            self.assertAlmostEqual(p['h_J_mol'],p['h_ig_J_mol']+p['h_res_J_mol'],places=8)
            self.assertAlmostEqual(p['s_J_mol_K'],p['s_ig_J_mol_K']+p['s_res_J_mol_K'],places=10)
        for b in result['diagnostics']['brackets']:
            self.assertLessEqual(b['F_low']*b['F_high'],0.)
        d=result['diagnostics']
        self.assertEqual(d['scan_evaluations'],128)
        self.assertEqual(d['total_evaluations'],d['scan_evaluations']+d['root_evaluations']+d['final_evaluations'])
    return test


for case in FROZEN['cases']:
    setattr(RoundTrips,'test_'+case['case_id'].lower(),make_case(case))


class FailureSemantics(unittest.TestCase):
    def run_failure(self,expected,**kw):
        inputs=dict(P=3e5,z=[.5,.5],H_target=-14232.339998531099)
        inputs.update(kw)
        r=solve_ph(**inputs)
        self.assertEqual(r['status'],expected,r['message'])
        self.assertNotIn('solution',r)
        return r

    def test_frozen_negative_cases(self):
        for case in FROZEN['negative_cases']:
            with self.subTest(case=case['case_id']):
                self.run_failure(case['expected_status'],**case['inputs'])

    def test_nonfinite_enthalpy(self):
        for H in [float('nan'),float('inf'),float('-inf'),None,True]:
            with self.subTest(H=H): self.run_failure('invalid_input',H_target=H)

    def test_invalid_pressure(self):
        for P in [-1.,0.,float('nan'),float('inf')]:
            with self.subTest(P=P): self.run_failure('invalid_input',P=P)

    def test_invalid_composition(self):
        for z in [[0.,0.],[-.1,1.1],[.5],[.5,float('nan')],[.5,.5,.1],None]:
            with self.subTest(z=z): self.run_failure('invalid_input',z=z)

    def test_invalid_bounds(self):
        for bounds in [[199.,500.],[200.,1001.],[300.,300.],[500.,200.],[float('nan'),500.],None]:
            with self.subTest(bounds=bounds): self.run_failure('temperature_domain_invalid',bounds=bounds)

    def test_unknown_component(self):
        self.run_failure('unsupported_component',component_ids=['methane','unknown'])

    def test_invalid_controls(self):
        for kw in [dict(grid_points=2),dict(xtol=0.),dict(maxiter=0),dict(method='newton')]:
            with self.subTest(kw=kw): self.run_failure('invalid_input',**kw)

    def test_pt_failure_leaves_hole(self):
        oracle=IndependentPT().evaluate
        def faulty(T,P,z):
            if 290<T<310: raise TrialFailure('pt','Controlled PT nonconvergence')
            return oracle(T,P,z)
        r=self.run_failure('pt_evaluation_failure',evaluator=faulty)
        failed=[r for r in r['diagnostics']['scan'] if r['status']!='success']
        self.assertTrue(failed)
        self.assertTrue(all('H_eq_J_mol' not in r and 'F_J_mol' not in r for r in failed))
        self.assertEqual(r['diagnostics']['root_evaluations'],0)

    def test_caloric_failure(self):
        def faulty(T,P,z): raise TrialFailure('caloric','Controlled caloric failure')
        self.run_failure('caloric_evaluation_failure',evaluator=faulty)

    def test_root_trial_failure(self):
        oracle=IndependentPT().evaluate
        def faulty(T,P,z):
            if abs(T-300)<.1: raise TrialFailure('pt','Failure inside valid endpoint bracket')
            return oracle(T,P,z)
        r=self.run_failure('pt_evaluation_failure',evaluator=faulty)
        self.assertGreater(r['diagnostics']['root_evaluations'],0)

    def test_final_reevaluation_failure(self):
        # Explicit instrumented seam proves the final PT call is fresh.
        seen={}; oracle=IndependentPT().evaluate
        def faulty(T,P,z):
            seen[T]=seen.get(T,0)+1
            if abs(T-300)<1e-7 and seen[T]>1:
                raise TrialFailure('caloric','Fresh final evaluation failure')
            return oracle(T,P,z)
        r=self.run_failure('caloric_evaluation_failure',evaluator=faulty)
        self.assertEqual(r['diagnostics']['final_evaluations'],1)

    def test_multiple_roots_no_arbitrary_selection(self):
        # Synthetic response tests solver policy, not thermodynamic qualification.
        def curve(T,P,z):
            H=(T-270.)*(T-330.)
            return dict(T_K=T,H_eq_J_mol=H,H_eq_direct_J_mol=H,
                        classification='synthetic',beta=0.,phases={})
        r=self.run_failure('multiple_ph_roots',H_target=0.,evaluator=curve)
        self.assertEqual(len(r['diagnostics']['roots']),2)
        self.assertEqual(r['diagnostics']['monotonicity'],'nonmonotonic')

    def test_exact_grid_root_freshly_checked(self):
        o=IndependentPT(); H=o.evaluate(300.,3e5,[.5,.5])['H_eq_J_mol']
        r=solve_ph(3e5,[.5,.5],H,grid_points=4)
        self.assertEqual(r['status'],'success')
        self.assertEqual(r['diagnostics']['root_evaluations'],0)
        self.assertEqual(r['diagnostics']['final_evaluations'],1)
        self.assertEqual(r['solution']['T_K'],300.)

    def test_discontinuous_pure_target_rejected(self):
        gap=FROZEN['pure_saturation_gap']
        r=self.run_failure('ph_nonconvergence',P=1000.,z=[0.,1.],H_target=gap['excluded_target_J_mol'])
        self.assertGreater(abs(r['diagnostics']['roots'][0]['residual_J_mol']),10000.)

    def test_coarse_temperature_convergence_not_sufficient(self):
        self.run_failure('ph_nonconvergence',xtol=1e-6)

    def test_cp_guard_before_evaluation(self):
        with self.assertRaises(TrialFailure) as cm: IndependentPT().evaluate(199.,3e5,[.5,.5])
        self.assertEqual(cm.exception.stage,'caloric')


class Evidence(unittest.TestCase):
    def test_two_reproductions_match_frozen_bytes(self):
        expected=ref.ARTIFACT.read_text()
        self.assertEqual(ref.serialize(ref.build()),expected)
        self.assertEqual(ref.serialize(ref.build()),expected)

    def test_no_production_imports(self):
        self.assertFalse(any(k.startswith('riogineer_engine') for k in sys.modules))
        self.assertNotIn('T_reference',inspect.signature(solve_ph).parameters)

    def test_canonical_monotonic_unique(self):
        for c in FROZEN['cases'][:3]:
            d=c['inverse']['diagnostics']
            self.assertEqual(d['monotonicity'],'increasing')
            self.assertEqual(len(d['roots']),1)
            self.assertEqual(len(d['brackets']),1)

    def test_boundary_phase_change_inside_root_bracket(self):
        cases=[c for c in FROZEN['cases'] if c['case_id'] in ['PH_BUBBLE_ABOVE','PH_DEW_BELOW']]
        for c in cases:
            d=c['inverse']['diagnostics']; b=d['brackets'][0]
            phases={r['classification'] for r in d['scan'] if b['T_low']<=r['T_K']<=b['T_high']}
            self.assertEqual(len(phases),2)
            self.assertGreater(len({r['classification'] for r in d['root_trials']}),1)

    def test_continuity_refinement(self):
        for c in FROZEN['continuity']:
            spans=[r['enthalpy_span_J_mol'] for r in c['refinement']]
            self.assertTrue(all(a>b>0 for a,b in zip(spans,spans[1:])))
            self.assertLess(spans[-1],.1)

    def test_resolution_and_second_method(self):
        for c,s in zip(FROZEN['cases'][:3],FROZEN['sensitivity']):
            for r in s['alternatives'].values():
                self.assertEqual(r['status'],'success')
                ref.compare_states(r['solution'],c['forward'])

    def test_enthalpy_perturbations(self):
        for c,s in zip(FROZEN['cases'][:3],FROZEN['sensitivity']):
            Ts=[r['solution']['T_K'] for r in s['perturbations']]
            self.assertLess(Ts[0],c['forward']['T_K'])
            self.assertGreater(Ts[1],c['forward']['T_K'])

    def test_near_zero_absolute_residual(self):
        c=next(c for c in FROZEN['cases'] if c['case_id']=='PH_NEAR_ZERO_H')
        self.assertLess(abs(c['input']['H_target_J_mol']),1.)
        self.assertLessEqual(c['inverse']['solution']['H_absolute_residual_J_mol'],ref.H_TOL)

    def test_low_pressure_residual_not_forced_zero(self):
        p=FROZEN['cases'][2]['inverse']['solution']['phases']['vapor']
        self.assertLess(abs(p['Z']-1),.001)
        self.assertGreater(abs(p['h_res_J_mol']),0.)
        self.assertLess(abs(p['h_res_J_mol']),2.)

    def test_absent_phases_are_not_fabricated(self):
        for c in FROZEN['cases']:
            s=c['inverse']['solution']
            if s['classification']=='single_liquid':
                self.assertEqual(s['beta'],0.); self.assertNotIn('vapor',s['phases'])
            elif s['classification']=='single_vapor':
                self.assertEqual(s['beta'],1.); self.assertNotIn('liquid',s['phases'])


if __name__=='__main__': unittest.main()
