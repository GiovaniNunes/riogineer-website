"""General PH interval qualification with controlled unavailable PT evaluations."""
from dataclasses import replace
import unittest
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.pr_eos import BinaryInteractions
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_ph_flash import PHSettings, PHSpecification, flash_ph
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolarComposition, StateSpecificationProvenance, ThermodynamicState


class Intervals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bip=BinaryInteractions('controlled_zero@1.0',('methane','n_hexane'),((0.,0.),(0.,0.)),'Explicit zero')
        cls.z=MolarComposition(cls.bip.component_ids,(.5,.5))
        cls.provenance=StateSpecificationProvenance('peng_robinson@1.0',cls.bip.identifier)
        cls.spec=PHSpecification(300000.,0.,cls.z,cls.provenance)
        cls.base=PengRobinsonProvider().equilibrium_caloric_PT(
            ThermodynamicState(300.,300000.,cls.z,cls.provenance),cls.bip,SolverSettings.high_accuracy())
        cls.failure=CaloricResult('flash_not_converged',replace(cls.base.equilibrium,
            status='flash_not_converged',phases=(),beta=None,final_K=()),message='controlled unavailable PT')

    def solve(self,fn,hole=lambda T:False,final_failure=False):
        seen=[]
        def evaluate(state,bip,settings):
            self.assertEqual(settings,SolverSettings.high_accuracy())
            T=state.temperature_K;seen.append(T)
            if hole(T) or (final_failure and len(seen)>7 and T==200.):return self.failure
            return replace(self.base,aggregate=replace(self.base.aggregate,h_J_mol=fn(T)))
        result=flash_ph(self.spec,self.bip,evaluate,PHSettings(scan_points=7))
        self.assertEqual(seen[:7],[200.,250.,300.,350.,400.,450.,500.])
        for trial in result.diagnostics.trials:
            if trial.status!='success':
                self.assertIsNone(trial.enthalpy_J_mol)
                self.assertIsNone(trial.classification)
                self.assertIsNone(trial.residual_J_mol)
        return result

    def empty(self,r,status):
        self.assertEqual(r.status,status)
        self.assertIsNone(r.caloric)
        self.assertIsNone(r.temperature_K)
        self.assertIsNone(r.enthalpy_residual_J_mol)

    def test_unique_root_before_unrelated_hole(self):
        r=self.solve(lambda T:T-275.,lambda T:T==400.)
        self.assertEqual(r.status,'success')
        self.assertEqual(r.temperature_K,275.)
        self.assertEqual(r.diagnostics.brackets_K,((250.,300.),))
        self.assertEqual(r.diagnostics.trials[-1].stage,'final')

    def test_unique_root_after_leading_and_consecutive_holes(self):
        r=self.solve(lambda T:T-425.,lambda T:T<=300. or T==500.)
        self.assertEqual(r.status,'success')
        self.assertEqual(r.temperature_K,425.)
        self.assertEqual(r.diagnostics.brackets_K,((400.,450.),))

    def test_bracket_cannot_cross_single_hole(self):
        r=self.solve(lambda T:T-350.,lambda T:T==350.)
        self.empty(r,'pt_evaluation_failure')
        self.assertEqual(r.diagnostics.brackets_K,())

    def test_bracket_cannot_cross_consecutive_holes(self):
        self.empty(self.solve(lambda T:T-375.,lambda T:300.<=T<=400.),'pt_evaluation_failure')

    def test_disconnected_roots_remain_ambiguous(self):
        r=self.solve(lambda T:(T-275.)*(T-425.),lambda T:T==350.)
        self.empty(r,'multiple_ph_roots')
        self.assertEqual(r.diagnostics.brackets_K,((250.,300.),(400.,450.)))
        self.assertIsNone(r.diagnostics.selected_bracket_K)

    def test_no_root_with_hole_preserves_failure_diagnostic(self):
        r=self.solve(lambda T:1.,lambda T:T==350.)
        self.empty(r,'pt_evaluation_failure')
        self.assertIn('flash_not_converged',r.diagnostics.reason)

    def test_no_root_without_hole_remains_unbracketed(self):
        self.empty(self.solve(lambda T:1.),'enthalpy_target_not_bracketed')

    def test_all_points_unavailable(self):
        r=self.solve(lambda T:1.,lambda T:True)
        self.empty(r,'pt_evaluation_failure')
        self.assertEqual(r.diagnostics.brackets_K,())

    def test_refinement_hole_fails_without_interpolation(self):
        r=self.solve(lambda T:T-275.,lambda T:T==275.)
        self.empty(r,'pt_evaluation_failure')
        self.assertEqual(r.diagnostics.trials[-1].stage,'root')

    def test_single_near_target_point_is_not_exact_root(self):
        self.empty(self.solve(lambda T:1e-8,lambda T:T!=350.),'pt_evaluation_failure')

    def test_exact_isolated_scan_root_preserves_fresh_final_rule(self):
        r=self.solve(lambda T:T-350.,lambda T:T!=350.)
        self.assertEqual(r.status,'success')
        self.assertEqual(r.diagnostics.brackets_K,((350.,350.),))
        self.assertEqual(r.diagnostics.trials[-1].stage,'final')

    def test_exact_roots_in_disconnected_intervals_remain_ambiguous(self):
        r=self.solve(lambda T:(T-250.)*(T-450.),lambda T:T==350.)
        self.empty(r,'multiple_ph_roots')
        self.assertEqual(len(r.diagnostics.brackets_K),2)

    def test_final_failure_cannot_reuse_scan_state(self):
        self.empty(self.solve(lambda T:T-200.,lambda T:T==400.,True),'pt_evaluation_failure')

    def test_discontinuity_still_fails_final_residual(self):
        self.empty(self.solve(lambda T:-1. if T<275. else 1.,lambda T:T==400.),'ph_nonconvergence')

    def test_programming_error_is_not_a_property_hole(self):
        def broken(*args,**kwargs):raise TypeError('controlled programming error')
        with self.assertRaises(TypeError):flash_ph(self.spec,self.bip,broken)

    def test_repeat_and_call_order(self):
        first=self.solve(lambda T:T-275.,lambda T:T==400.)
        self.solve(lambda T:(T-275.)*(T-425.),lambda T:T==350.)
        self.assertEqual(first,self.solve(lambda T:T-275.,lambda T:T==400.))


if __name__=='__main__':unittest.main()
