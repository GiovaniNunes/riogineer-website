"""Frozen PH state acceptance plus isolated bounded-solver failure controls."""
from dataclasses import replace
from math import fsum
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.peng_robinson_ph import compare_production as comparison
from riogineer_engine.pr_ph_flash import PHSpecification, PHSettings, flash_ph
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_eos import BinaryInteractions,MODEL
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolarComposition,StateSpecificationProvenance,ThermodynamicState

REFERENCE=comparison.read_reference()
IDS=('methane','n_hexane')
BIP=BinaryInteractions('explicit_zero@1.0',IDS,((0.,0.),(0.,0.)),REFERENCE['metadata']['BIP_provenance'])
PROVENANCE=StateSpecificationProvenance(MODEL,BIP.identifier)


def specification(case):
    i=case['input']
    return PHSpecification(i['P_Pa_abs'],i['H_target_J_mol'],MolarComposition(IDS,tuple(i['z'])),PROVENANCE)


class Matrix(unittest.TestCase):
    pass


def positive_test(case):
    def test(self):
        r=PengRobinsonProvider().flash_PH(specification(case),BIP)
        checks=comparison.compare(REFERENCE,case,r)
        self.assertTrue(all(c['passed'] for c in checks),checks)
        self.assertEqual(sum(t.stage=='scan' for t in r.diagnostics.trials),128)
        self.assertEqual(sum(t.stage=='final' for t in r.diagnostics.trials),1)
        self.assertEqual(r.diagnostics.pt_settings,SolverSettings.high_accuracy())
        self.assertEqual(len(r.diagnostics.brackets_K),1)
        self.assertEqual(r.caloric.equilibrium.overall_state.composition.component_ids,IDS)
        self.assertEqual(r.caloric.equilibrium.overall_state.composition.molar_fractions,tuple(case['input']['z']))
        H=fsum(p.fraction*c.h_total_J_mol for p,c in zip(r.caloric.equilibrium.phases,r.caloric.phases))
        self.assertEqual(H,r.caloric.aggregate.h_J_mol)
        self.assertEqual(r.caloric.equilibrium.overall_state.temperature_K,r.temperature_K)
    return test


for case in REFERENCE['cases']:
    setattr(Matrix,'test_'+case['case_id'].lower(),positive_test(case))


def negative_test(case):
    def test(self):
        i=case['inputs']
        r=comparison.evaluate(REFERENCE,i['P'],i['H_target'],i['z'],i.get('component_ids',IDS),i.get('bounds',(200.,500.)),i.get('maxiter',100))
        status='unsupported_component' if r.status=='unsupported_components' else r.status
        self.assertEqual(status,case['expected_status'])
        self.assertIsNone(r.caloric);self.assertIsNone(r.temperature_K);self.assertIsNone(r.enthalpy_residual_J_mol)
    return test


for case in REFERENCE['negative_cases']:
    setattr(Matrix,'test_'+case['case_id'].lower(),negative_test(case))


class Controls(unittest.TestCase):
    def test_provider_advertises_standalone_ph_and_ps_extensions(self):
        p=PengRobinsonProvider()
        self.assertIn('flash_PH',p.capabilities)
        self.assertIn('flash_PS',p.capabilities)
        self.assertFalse({'PS_flash','water_PH','process_energy_balance'} & p.capabilities)
        self.assertEqual(SolverSettings().fugacity_tolerance,1e-11)

    @classmethod
    def setUpClass(cls):
        cls.provider=PengRobinsonProvider()
        cls.base=cls.provider.equilibrium_caloric_PT(ThermodynamicState(300.,300000.,MolarComposition(IDS,(.5,.5)),PROVENANCE),BIP,SolverSettings.high_accuracy())

    def fake(self,fn):
        def evaluate(state,bip,settings):
            self.assertEqual(settings,SolverSettings.high_accuracy())
            self.seen.append(state.temperature_K)
            return replace(self.base,aggregate=replace(self.base.aggregate,h_J_mol=fn(state.temperature_K)))
        return evaluate

    def solve(self,fn,target=0.,settings=PHSettings()):
        self.seen=[]
        s=PHSpecification(300000.,target,MolarComposition(IDS,(.5,.5)),PROVENANCE)
        return flash_ph(s,BIP,self.fake(fn),settings)

    def empty(self,r,status):
        self.assertEqual(r.status,status)
        self.assertIsNone(r.caloric);self.assertIsNone(r.temperature_K);self.assertIsNone(r.enthalpy_residual_J_mol)

    def test_fresh_final_and_explicit_high_accuracy_every_trial(self):
        r=self.solve(lambda T:T-301.234)
        self.assertEqual(r.status,'success')
        self.assertEqual(self.seen[-1],r.temperature_K)
        self.assertIn(self.seen[-1],self.seen[:-1])
        self.assertEqual(r.diagnostics.trials[-1].stage,'final')
        self.assertLessEqual(abs(r.enthalpy_residual_J_mol),1e-6)
        self.assertEqual(SolverSettings().fugacity_tolerance,1e-11)

    def test_multiple_candidates_fail_without_selecting_first(self):
        r=self.solve(lambda T:(T-250.)*(T-400.))
        self.empty(r,'multiple_ph_roots')
        self.assertEqual(len(r.diagnostics.brackets_K),2)
        self.assertIsNone(r.diagnostics.selected_bracket_K)

    def test_exact_scan_root_is_freshly_evaluated(self):
        r=self.solve(lambda T:T-200.)
        self.assertEqual(r.status,'success')
        self.assertEqual(r.temperature_K,200.)
        self.assertEqual(r.diagnostics.root_iterations,0)
        self.assertEqual(len(self.seen),129)

    def test_no_bracket(self):
        self.empty(self.solve(lambda T:T+1000.),'enthalpy_target_not_bracketed')

    def test_iteration_exhaustion(self):
        self.empty(self.solve(lambda T:T-301.234,settings=PHSettings(max_iterations=1)),'ph_nonconvergence')

    def test_discontinuous_gap_cannot_pass_temperature_only(self):
        r=self.solve(lambda T:-10. if T<301.234 else 10.)
        self.empty(r,'ph_nonconvergence')
        self.assertEqual(r.diagnostics.trials[-1].stage,'final')
        self.assertIn('residual failed',r.diagnostics.reason)

    def test_final_evaluation_failure_not_cached_success(self):
        self.seen=[];fn=self.fake(lambda T:T-200.)
        def changed(state,bip,settings):
            c=fn(state,bip,settings)
            return replace(c,aggregate=replace(c.aggregate,h_J_mol=1.)) if len(self.seen)>128 else c
        s=PHSpecification(300000.,0.,MolarComposition(IDS,(.5,.5)),PROVENANCE)
        r=flash_ph(s,BIP,changed)
        self.empty(r,'ph_nonconvergence')
        self.assertEqual(r.diagnostics.trials[-1].residual_J_mol,1.)

    def test_pt_failure_recorded_and_not_bridged(self):
        failed=replace(self.base.equilibrium,status='flash_not_converged',phases=(),beta=None,final_K=())
        c=CaloricResult('flash_not_converged',failed,message='controlled PT failure')
        with patch.object(PengRobinsonProvider,'equilibrium_caloric_PT',return_value=c) as call:
            r=self.provider.flash_PH(specification(REFERENCE['cases'][0]),BIP)
        self.empty(r,'pt_evaluation_failure')
        # A controlled failure does not prevent inspection of the remaining scan domain.
        bounds=r.diagnostics.settings.temperature_bounds_K
        count=r.diagnostics.settings.scan_points
        temperatures=[entry.args[0].temperature_K for entry in call.call_args_list]
        self.assertEqual(temperatures,[bounds[0]+(bounds[1]-bounds[0])*i/(count-1) for i in range(count)])
        self.assertTrue(all(t.stage=='scan' and t.status=='pt_evaluation_failure' for t in r.diagnostics.trials))
        self.assertEqual(r.diagnostics.brackets_K,())
        self.assertEqual(r.diagnostics.trials[0].underlying_status,'flash_not_converged')
        self.assertIsNone(r.diagnostics.trials[0].enthalpy_J_mol)

    def test_caloric_failure_recorded_without_enthalpy(self):
        c=CaloricResult('invalid_caloric_data',self.base.equilibrium,message='controlled caloric failure')
        with patch.object(PengRobinsonProvider,'equilibrium_caloric_PT',return_value=c):
            r=self.provider.flash_PH(specification(REFERENCE['cases'][0]),BIP)
        self.empty(r,'caloric_evaluation_failure')
        self.assertIsNone(r.diagnostics.trials[0].enthalpy_J_mol)

    def test_nonfinite_caloric_value(self):
        self.empty(self.solve(lambda T:float('nan')),'caloric_evaluation_failure')

    def test_invalid_input_and_controls(self):
        spec=specification(REFERENCE['cases'][0])
        for h in (float('nan'),float('inf')):
            self.empty(self.provider.flash_PH(replace(spec,enthalpy_J_mol=h),BIP),'invalid_input')
        for settings in (PHSettings(scan_points=2),PHSettings(max_iterations=0),PHSettings(enthalpy_tolerance_J_mol=1.),PHSettings(temperature_tolerance_K=1.)):
            self.empty(self.provider.flash_PH(spec,BIP,settings),'invalid_input')
        self.empty(self.provider.flash_PH(spec,BIP,PHSettings((300.,300.))),'temperature_domain_invalid')
        self.empty(self.provider.flash_PH(spec,BIP,PHSettings((200.,201.))),'enthalpy_target_not_bracketed')

    def test_invalid_caloric_domain_propagates(self):
        from riogineer_engine.pr_eos import ThermodynamicError
        with patch('riogineer_engine.pr_caloric.component_caloric',side_effect=ThermodynamicError('caloric_out_of_range','controlled Cp domain failure')):
            r=self.provider.flash_PH(specification(REFERENCE['cases'][0]),BIP)
        self.empty(r,'caloric_out_of_range')

    def test_pure_nhexane_gap(self):
        g=REFERENCE['pure_saturation_gap']
        r=comparison.evaluate(REFERENCE,g['P_Pa_abs'],g['excluded_target_J_mol'],[0.,1.])
        self.empty(r,g['inversion']['status'])

    def test_determinism_and_call_order(self):
        target=specification(REFERENCE['cases'][1])
        first=self.provider.flash_PH(target,BIP)
        for case in REFERENCE['cases'][:3]:
            self.provider.flash_PH(specification(case),BIP)
            self.assertEqual(self.provider.flash_PH(target,BIP),first)
        self.provider.flash_PH(replace(target,enthalpy_J_mol=float('nan')),BIP)
        self.assertEqual(self.provider.flash_PH(target,BIP),first)

    def test_no_benchmark_or_external_thermodynamic_imports(self):
        import ast
        source=(ROOT/'engine/riogineer_engine/pr_ph_flash.py').read_text()
        tree=ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                self.assertFalse(any(v in (node.module or '') for v in ('benchmark','scipy','thermo.','teqp')))
        self.assertNotIn('json',source)


if __name__=='__main__':unittest.main()
