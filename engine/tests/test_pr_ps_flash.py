"""M13 external acceptance and isolated inversion safety; no reference generator imports."""
from dataclasses import replace
from math import fsum
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.peng_robinson_ps import compare_production as comparison
from riogineer_engine.pr_ps_flash import PSSpecification,PSSettings,flash_ps
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_eos import ThermodynamicError,MODEL
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolarComposition,StateSpecificationProvenance,ThermodynamicState

REFERENCE=comparison.read_reference()
BIP=comparison.BIP
PROVENANCE=comparison.PROVENANCE
IDS=comparison.IDS


class FrozenMatrix(unittest.TestCase):
    pass


def positive(case):
    def test(self):
        r=comparison.evaluate(case['input'])
        checks=comparison.compare(REFERENCE,case,r)
        self.assertTrue(all(x['passed'] for x in checks))
        c=r.caloric
        self.assertEqual(fsum(p.fraction*v.s_total_J_mol_K for p,v in zip(c.equilibrium.phases,c.phases)),c.aggregate.s_J_mol_K)
        self.assertEqual(fsum(p.fraction*v.h_total_J_mol for p,v in zip(c.equilibrium.phases,c.phases)),c.aggregate.h_J_mol)
        self.assertEqual(c.equilibrium.overall_state.temperature_K,r.temperature_K)
    return test


def negative(case):
    def test(self):
        r=comparison.negative(case)
        self.assertEqual(r.status,case['expected_status'])
        self.assertIsNone(r.caloric)
        self.assertIsNone(r.temperature_K)
        self.assertIsNone(r.entropy_residual_J_mol_K)
        if case['case_id']=='PURE_COEXISTENCE_GAP':
            self.assertTrue(r.diagnostics.gap_detected)
            self.assertGreater(r.diagnostics.final_entropy_span_J_mol_K,100.)
    return test


for case in REFERENCE['cases']:
    setattr(FrozenMatrix,'test_'+case['case_id'].lower(),positive(case))
for case in REFERENCE['negative_cases']:
    setattr(FrozenMatrix,'test_'+case['case_id'].lower(),negative(case))


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider=PengRobinsonProvider()
        cls.base=cls.provider.equilibrium_caloric_PT(ThermodynamicState(300.,3e5,MolarComposition(IDS,(.5,.5)),PROVENANCE),BIP,SolverSettings.high_accuracy())

    def setUp(self):
        self.calls=[]
        self.spec=PSSpecification(3e5,0.,MolarComposition(IDS,(.5,.5)),PROVENANCE)

    def fake(self,fn):
        def evaluator(state,bip,settings):
            self.assertEqual(settings,SolverSettings.high_accuracy())
            self.calls.append(state.temperature_K)
            return replace(self.base,aggregate=replace(self.base.aggregate,s_J_mol_K=fn(state.temperature_K)))
        return evaluator

    def solve(self,fn,settings=PSSettings()):
        return flash_ps(self.spec,BIP,self.fake(fn),settings)

    def empty(self,r,status):
        self.assertEqual(r.status,status)
        self.assertIsNone(r.caloric);self.assertIsNone(r.temperature_K);self.assertIsNone(r.entropy_residual_J_mol_K)

    def test_capabilities_only_ps_added(self):
        self.assertEqual(self.provider.capabilities,frozenset({'pr_eos','phase_stability','single_phase_PT','two_phase_PT_flash','phase_caloric_TP','equilibrium_caloric_PT','flash_PH','flash_PS'}))
        self.assertNotIn('water_PH',self.provider.capabilities)
        self.assertNotIn('process_energy_balance',self.provider.capabilities)
        self.assertEqual(SolverSettings().fugacity_tolerance,1e-11)

    def test_exact_scan_point_no_duplicate_and_fresh_final(self):
        r=self.solve(lambda T:T-300.)
        self.assertEqual(r.status,'success')
        self.assertEqual(r.diagnostics.brackets_K,((300.,300.),))
        self.assertEqual(r.diagnostics.root_iterations,0)
        self.assertEqual(len(self.calls),65)
        self.assertEqual(self.calls[-1],300.)
        self.assertEqual(r.diagnostics.trials[-1].stage,'final')

    def test_near_scan_point_not_duplicated(self):
        r=self.solve(lambda T:T-300.+1e-9)
        self.assertEqual(r.status,'success')
        self.assertEqual(len(r.diagnostics.brackets_K),1)
        self.assertIn(300.,r.diagnostics.near_exact_scan_temperatures_K)
        self.assertLessEqual(abs(r.entropy_residual_J_mol_K),1e-8)

    def test_exact_bisection_root_has_zero_final_span(self):
        r=self.solve(lambda T:T-350.)
        self.assertEqual(r.status,'success')
        self.assertEqual(r.diagnostics.final_bracket_K,(350.,350.))
        self.assertEqual(r.diagnostics.final_entropy_span_J_mol_K,0.)

    def test_near_endpoint_requires_fresh_final(self):
        r=self.solve(lambda T:T-200.+1e-9)
        self.assertEqual(r.status,'success')
        self.assertEqual(r.diagnostics.trials[-1].stage,'final')

    def test_bisection_does_not_use_enthalpy(self):
        r=self.solve(lambda T:T-301.234)
        self.assertEqual(r.status,'success')
        self.assertAlmostEqual(r.temperature_K,301.234,places=8)
        self.assertEqual(r.caloric.aggregate.h_J_mol,self.base.aggregate.h_J_mol)
        self.assertLessEqual(r.diagnostics.final_bracket_K[1]-r.diagnostics.final_bracket_K[0],1e-10)

    def test_complete_scan_before_ambiguity(self):
        r=self.solve(lambda T:(T-250.)*(T-400.))
        self.empty(r,'ambiguous_ps_root')
        self.assertEqual(len(self.calls),64)
        self.assertEqual(len(r.diagnostics.brackets_K),2)
        self.assertIsNone(r.diagnostics.selected_bracket_K)

    def test_hole_completes_scan_without_bridging(self):
        fn=self.fake(lambda T:T-300.)
        def hole(state,bip,settings):
            c=fn(state,bip,settings)
            return CaloricResult('flash_not_converged',None,message='controlled PT hole') if 290<state.temperature_K<310 else c
        r=flash_ps(self.spec,BIP,hole)
        self.empty(r,'property_evaluation_failed')
        self.assertEqual(len(self.calls),64)
        self.assertEqual(r.diagnostics.brackets_K,())
        self.assertTrue(any(t.status!='success' for t in r.diagnostics.trials))

    def test_caloric_failure_preserves_underlying_status(self):
        def fail(state,bip,settings):return CaloricResult('invalid_caloric_data',self.base.equilibrium,message='controlled caloric failure')
        r=flash_ps(self.spec,BIP,fail)
        self.empty(r,'property_evaluation_failed')
        self.assertEqual(len(r.diagnostics.trials),64)
        self.assertEqual(r.diagnostics.trials[0].underlying_status,'invalid_caloric_data')

    def test_raised_property_failure_is_controlled(self):
        def fail(state,bip,settings):raise ThermodynamicError('numerical_domain_error','controlled raised error')
        self.empty(flash_ps(self.spec,BIP,fail),'property_evaluation_failed')

    def test_profile_mismatch_rejected(self):
        bad=replace(self.base,equilibrium=replace(self.base.equilibrium,provenance=replace(self.base.equilibrium.provenance,settings=SolverSettings())))
        self.empty(flash_ps(self.spec,BIP,lambda *a,**kw:bad),'property_evaluation_failed')

    def test_nonfinite_entropy_rejected(self):
        self.empty(self.solve(lambda T:float('nan')),'property_evaluation_failed')

    def test_nonfinite_enthalpy_not_published(self):
        bad=replace(self.base,aggregate=replace(self.base.aggregate,h_J_mol=float('inf')))
        self.empty(flash_ps(self.spec,BIP,lambda *a,**kw:bad),'property_evaluation_failed')

    def test_root_iteration_limit(self):
        self.empty(self.solve(lambda T:T-301.234,PSSettings(max_iterations=1)),'ps_nonconvergence')

    def test_fresh_final_residual_failure(self):
        fn=self.fake(lambda T:T-300.)
        def changed(state,bip,settings):
            c=fn(state,bip,settings)
            return replace(c,aggregate=replace(c.aggregate,s_J_mol_K=1.)) if len(self.calls)>64 else c
        r=flash_ps(self.spec,BIP,changed)
        self.empty(r,'ps_nonconvergence')
        self.assertEqual(r.diagnostics.trials[-1].stage,'final')

    def test_fresh_final_property_failure(self):
        fn=self.fake(lambda T:T-300.)
        def changed(state,bip,settings):
            c=fn(state,bip,settings)
            return CaloricResult('invalid_caloric_data',None) if len(self.calls)>64 else c
        self.empty(flash_ps(self.spec,BIP,changed),'property_evaluation_failed')

    def test_discontinuity_not_temperature_only_success(self):
        r=self.solve(lambda T:-10. if T<301.234 else 10.)
        self.empty(r,'ps_nonconvergence')
        self.assertTrue(r.diagnostics.gap_detected)
        self.assertEqual(r.diagnostics.final_entropy_span_J_mol_K,20.)

    def test_no_bracket(self):
        self.empty(self.solve(lambda T:T+1000),'entropy_target_not_bracketed')

    def test_specification_and_provenance_validation(self):
        for s in [None,replace(self.spec,entropy_J_mol_K=True),replace(self.spec,entropy_J_mol_K=float('inf')),
                  replace(self.spec,pressure_Pa_abs=0.),replace(self.spec,composition=MolarComposition(IDS,(.4,.4))),
                  replace(self.spec,provenance=StateSpecificationProvenance('other',BIP.identifier))]:
            self.empty(self.provider.flash_PS(s,BIP),'invalid_input')
        self.empty(self.provider.flash_PS(self.spec,None),'unsupported_bip')

    def test_invalid_controls(self):
        for settings in [None,PSSettings(scan_points=True),PSSettings(scan_points=2),PSSettings(max_iterations=101),PSSettings(max_iterations=0),
                         PSSettings(entropy_tolerance_J_mol_K=1e-7),PSSettings(temperature_tolerance_K=1e-9)]:
            self.empty(self.provider.flash_PS(self.spec,BIP,settings),'invalid_input')
        self.empty(self.provider.flash_PS(self.spec,BIP,PSSettings(temperature_bounds_K=(300.,300.))),'temperature_domain_invalid')

    def test_internal_round_trip_separate_from_external_acceptance(self):
        for c in REFERENCE['cases'][:3]:
            i=c['input'];T=c['forward']['T_K']
            state=ThermodynamicState(T,i['P'],MolarComposition(IDS,tuple(i['z'])),PROVENANCE)
            forward=self.provider.equilibrium_caloric_PT(state,BIP,SolverSettings.high_accuracy())
            r=self.provider.flash_PS(PSSpecification(i['P'],forward.aggregate.s_J_mol_K,state.composition,PROVENANCE),BIP)
            self.assertEqual(r.status,'success')
            self.assertLessEqual(abs(r.temperature_K-T),REFERENCE['tolerances']['T']['atol'])

    def test_repeat_after_other_regimes_and_gap(self):
        c=REFERENCE['cases'][1];baseline=comparison.evaluate(c['input'])
        for prior in REFERENCE['cases'][:3]:
            comparison.evaluate(prior['input'])
            self.assertEqual(baseline,comparison.evaluate(c['input']))
        comparison.negative(REFERENCE['negative_cases'][-1])
        self.assertEqual(baseline,comparison.evaluate(c['input']))

    def test_offline_no_independent_runtime_dependencies(self):
        self.assertFalse(any(name.split('.')[0] in ('thermo','chemicals','scipy') for name in sys.modules))


if __name__=='__main__':unittest.main()
