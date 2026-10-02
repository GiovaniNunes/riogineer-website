"""Physical qualification assertions and clearly synthetic policy controls."""
import sys,unittest,math
from pathlib import Path
from dataclasses import replace,asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.m21_pt200.common import *
from benchmarks.m21_pt200.profile import Profile,inverse,guard
from benchmarks.m21_pt200.harness import pt,endpoint,PROVENANCE,BIP,IDS,PROVIDER
from riogineer_engine.pr_ps_flash import PSSpecification
from riogineer_engine.pr_ph_flash import PHSpecification
from riogineer_engine.thermodynamics import MolarComposition,ThermodynamicState
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pump_energy import inverse as legacy_guard,PumpFailure
from riogineer_engine.separator_liquid_state import Failure

class Policy(unittest.TestCase):
    def synthetic(self,cap,kind,mode):
        profile=Profile(cap);base=pt(300.,3e7,[.5,.5],profile);calls=[];seen={}
        spec=(PSSpecification if kind=='PS' else PHSpecification)(3e7,0.,MolarComposition(IDS,(.5,.5)),PROVENANCE)
        def evaluate(s,bip,settings):
            self.assertEqual(settings,profile.settings);t=s.temperature_K;calls.append(t);seen[t]=seen.get(t,0)+1
            eq=replace(base.equilibrium,overall_state=s)
            if mode=='wrong_profile':eq=replace(eq,provenance=replace(eq.provenance,settings=Profile(100).settings if cap!=100 else Profile(200).settings))
            if mode=='hole' and 460<t<470:return replace(base,status='flash_not_converged',equilibrium=replace(eq,status='flash_not_converged',phases=(),beta=None),aggregate=None,phases=())
            value=(t-250)*(t-400) if mode=='ambiguous' else (-1. if t<301.234 else 1.) if mode=='gap' else math.nan if mode=='nonfinite_property' else t-300.
            if mode=='fresh_failure' and seen[t]>1:value+=1.
            agg=replace(base.aggregate,**({'s_J_mol_K':value} if kind=='PS' else {'h_J_mol':value}))
            return replace(base,equilibrium=eq,aggregate=agg)
        return inverse(spec,BIP,profile,kind,evaluate),calls

    def test_ambiguity_preserved_all_profiles(self):
        for cap in CAPS:
            for kind,status,n in [('PS','ambiguous_ps_root',64),('PH','multiple_ph_roots',128)]:
                r,calls=self.synthetic(cap,kind,'ambiguous');self.assertEqual(r.status,status);self.assertIsNone(r.caloric);self.assertEqual(len(calls),n)
    def test_PS_holes_never_skipped(self):
        for cap in CAPS:
            r,calls=self.synthetic(cap,'PS','hole');self.assertEqual(r.status,'property_evaluation_failed');self.assertIsNone(r.caloric);self.assertEqual(len(calls),64)
    def test_residual_discontinuity_and_fresh_failure(self):
        for cap in CAPS:
            for kind in ('PS','PH'):
                for mode in ('gap','fresh_failure'):
                    r,_=self.synthetic(cap,kind,mode);self.assertNotEqual(r.status,'success');self.assertIsNone(r.caloric)
    def test_wrong_nested_profile_rejects(self):
        for cap in CAPS:
            for kind in ('PS','PH'):
                r,_=self.synthetic(cap,kind,'wrong_profile');self.assertNotEqual(r.status,'success');self.assertIsNone(r.caloric)
    def test_nonfinite_inputs_and_properties(self):
        for cap in CAPS:
            for kind in ('PS','PH'):
                spec=(PSSpecification if kind=='PS' else PHSpecification)(3e7,math.nan,MolarComposition(IDS,(.5,.5)),PROVENANCE)
                r=inverse(spec,BIP,Profile(cap),kind);self.assertNotEqual(r.status,'success');self.assertIsNone(r.caloric)
                r,_=self.synthetic(cap,kind,'nonfinite_property');self.assertNotEqual(r.status,'success');self.assertIsNone(r.caloric)
    def test_iteration_limit_real_PT_and_no_payload(self):
        s=ThermodynamicState(350.,3e5,MolarComposition(IDS,(.5,.5)),PROVENANCE)
        c=PROVIDER.equilibrium_caloric_PT(s,BIP,replace(SolverSettings.high_accuracy(),flash_max_iterations=1))
        self.assertEqual(c.status,'flash_not_converged');self.assertEqual(c.equilibrium.diagnostics.iterations,1)
        self.assertIsNone(c.aggregate);self.assertEqual(c.equilibrium.phases,());self.assertIsNone(c.equilibrium.beta)
    def test_additive_guard_and_legacy_rejection(self):
        profile=Profile(200);a=pt(300.,3e7,[.5,.5],profile)
        spec=PSSpecification(3e7,a.aggregate.s_J_mol_K,MolarComposition(IDS,(.5,.5)),PROVENANCE)
        r=inverse(spec,BIP,profile,'PS');self.assertEqual(guard(r,spec,profile,'PS')['numerical_profile'],profile.identifier)
        with self.assertRaises(PumpFailure):legacy_guard(r,spec,'PS')
        with self.assertRaises(PumpFailure):guard(r,spec,Profile(100),'PS')
        bad=replace(r,caloric=replace(r.caloric,equilibrium=replace(r.caloric.equilibrium,overall_state=replace(r.caloric.equilibrium.overall_state,pressure_Pa_abs=2e7))))
        with self.assertRaises(PumpFailure):guard(bad,spec,profile,'PS')
        bad=replace(r,entropy_residual_J_mol_K=1.)
        with self.assertRaises(PumpFailure):guard(bad,spec,profile,'PS')
    def test_phase_guard_remains_active(self):
        for cap in CAPS:
            with self.assertRaises(Failure):endpoint(350.,3e5,[.5,.5],Profile(cap))
            with self.assertRaises(Failure):endpoint(400.,1e3,[.5,.5],Profile(cap))
    def test_settings_immutable_and_no_automatic_fallback(self):
        from dataclasses import FrozenInstanceError
        p=Profile(200)
        with self.assertRaises(FrozenInstanceError):p.cap=400
        with self.assertRaises(ValueError):Profile(201)
        self.assertIsNone(p.record()['fallback']);self.assertEqual(SolverSettings.high_accuracy().flash_max_iterations,100)


class Selection(unittest.TestCase):
    def test_canonical_selection_conflicts_and_custom_settings(self):
        from riogineer_engine.numerical_profiles import PT200,NumericalProfile,resolve_pt_settings
        from dataclasses import FrozenInstanceError
        self.assertIs(resolve_pt_settings(NumericalProfile.PT200),PT200)
        self.assertIs(resolve_pt_settings(NumericalProfile.PT200.value),PT200)
        with self.assertRaises(FrozenInstanceError):PT200.flash_max_iterations=400
        raw=replace(SolverSettings.high_accuracy(),flash_max_iterations=200)
        self.assertIs(resolve_pt_settings(settings=raw),raw)
        self.assertFalse(hasattr(raw,'numerical_profile'))
        self.assertIs(resolve_pt_settings(NumericalProfile.PT200,raw),PT200)
        for invalid in ('pr_high_accuracy_pt400@1','unknown',400,False):
            with self.assertRaises(ValueError):resolve_pt_settings(invalid)
        for bad in (SolverSettings.high_accuracy(),replace(raw,flash_max_iterations=400),replace(PT200,flash_max_iterations=400),replace(PT200,numerical_profile='unknown')):
            with self.assertRaises(ValueError):resolve_pt_settings(NumericalProfile.PT200,bad)
        self.assertEqual(resolve_pt_settings(),SolverSettings())

    def test_provider_PT_and_caloric_profile_provenance(self):
        from riogineer_engine.numerical_profiles import PT200,NumericalProfile
        s=ThermodynamicState(466.6666666666667,8e6,MolarComposition(IDS,(.5,.5)),PROVENANCE)
        raw=PROVIDER.flash_PT(s,BIP,SolverSettings.high_accuracy())
        self.assertEqual(raw.status,'flash_not_converged');self.assertEqual(raw.diagnostics.iterations,100)
        named=PROVIDER.flash_PT(s,BIP,numerical_profile=NumericalProfile.PT200)
        self.assertEqual(named.status,'success_two_phase');self.assertEqual(named.diagnostics.iterations,152)
        self.assertEqual(named.provenance.settings,PT200)
        self.assertEqual(PROVIDER.identifier,'peng_robinson@1.0')
        for fn in (PROVIDER.flash_PT,PROVIDER.equilibrium_caloric_PT):
            with self.assertRaises(ValueError):fn(s,BIP,numerical_profile='pr_high_accuracy_pt400@1')
            with self.assertRaises(ValueError):fn(s,BIP,SolverSettings.high_accuracy(),numerical_profile=NumericalProfile.PT200)
        self.assertEqual(PROVIDER.equilibrium_caloric_PT(s,BIP,None).status,'invalid_input')
        # Raw PT historically raises for an explicit None; keep that API behavior.
        with self.assertRaises(AttributeError):PROVIDER.flash_PT(s,BIP,None)
        for fn in (PROVIDER.flash_PT,PROVIDER.equilibrium_caloric_PT):
            with self.assertRaises(ValueError):fn(s,BIP,None,numerical_profile=NumericalProfile.PT200)
        bad=replace(SolverSettings(),flash_max_iterations=0)
        self.assertEqual(PROVIDER.flash_PT(s,BIP,bad).status,'invalid_input')
        self.assertEqual(PROVIDER.equilibrium_caloric_PT(s,BIP,bad).status,'invalid_input')

    def test_real_provider_inverse_calls_and_final_settings(self):
        from benchmarks.m21_pt200.harness import solve
        from riogineer_engine.numerical_profiles import PT200
        base=pt(300.,3e7,[.5,.5],Profile(200))
        for kind in ('PS','PH'):
            spec=(PSSpecification if kind=='PS' else PHSpecification)(3e7,base.aggregate.s_J_mol_K if kind=='PS' else base.aggregate.h_J_mol,MolarComposition(IDS,(.5,.5)),PROVENANCE)
            r,rec=solve(spec,Profile(200),kind)
            self.assertEqual(r.status,'success');self.assertEqual(r.diagnostics.pt_settings,PT200)
            self.assertEqual(r.caloric.equilibrium.provenance.settings,PT200)
            self.assertEqual(len(rec['calls']),len(r.diagnostics.trials))
            self.assertTrue(all(c['pt_settings']==asdict(PT200) for c in rec['calls']))
            self.assertEqual(sum(t.stage=='scan' for t in r.diagnostics.trials),64 if kind=='PS' else 128)
            self.assertTrue(any(t.stage=='final' for t in r.diagnostics.trials))
            # Untouched numerical payload with forged final provenance is rejected.
            bad=replace(r,caloric=replace(r.caloric,equilibrium=replace(r.caloric.equilibrium,provenance=replace(r.caloric.equilibrium.provenance,settings=SolverSettings.high_accuracy()))))
            with self.assertRaises(PumpFailure):guard(bad,spec,Profile(200),kind)
            provider_fn=PROVIDER.flash_PS if kind=='PS' else PROVIDER.flash_PH
            with self.assertRaises(ValueError):provider_fn(spec,BIP,numerical_profile='unknown')

class ImplementationEvidence(unittest.TestCase):
    def test_frozen_comparisons_and_current_source_integrity(self):
        from benchmarks.m22_separator_pump.integrity import preservation,source_verify
        from benchmarks.m21_pt200.evidence import build
        preservation();source_verify()
        result=build();self.assertEqual(result['failed_checks'],0)
        self.assertEqual(result,read(HERE/'evidence.json'))
        self.assertEqual(result['peak_iterations'],199)
