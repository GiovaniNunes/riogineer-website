"""Physical qualification assertions and clearly synthetic policy controls."""
import sys,unittest,math
from pathlib import Path
from dataclasses import replace,asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.pt_iteration_budget.common import *
from benchmarks.pt_iteration_budget.profile import Profile,inverse,guard
from benchmarks.pt_iteration_budget.harness import pt,endpoint,PROVENANCE,BIP,IDS,PROVIDER
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
        with self.assertRaises(PumpFailure):guard(r,spec,Profile(400),'PS')
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

class Evidence(unittest.TestCase):
    def test_all_independent_comparisons(self):
        raw=read(HERE/'candidate_ledger.json');self.assertEqual(raw['failed_comparisons'],195)
        l=read(HERE/'qualified_ledger.json');self.assertEqual(l['failed_comparisons'],0)
        for cap in ('200','400'):
            for group in ('PT','inverses','chains'):
                r=l['profile_counts'][cap][group];self.assertEqual(r['accepted'],r['total'])
    def test_reference_mapping_is_independent_and_preserves_values(self):
        audit=read(HERE/'phase_identity_reference.json');raw={r['case_id']:r['state'] for r in read(HERE/'reference.json')['PT']}
        self.assertFalse(audit['production_imported']);self.assertEqual(sum(r['swapped'] for r in audit['cases']),6)
        for r in audit['cases']:
            self.assertEqual(r['status'],'verified');before=raw[r['case_id']];after=r['state']
            self.assertEqual(sorted(map(hashed,before['phases'].values())),sorted(map(hashed,after['phases'].values())))
            for k in ('H_eq_J_mol','S_eq_J_mol_K'):self.assertEqual(before[k],after[k])
            for name,physical in r['mapping'].items():
                pip=r['phase_identity'][name]['PIP'];self.assertTrue(pip>1 if physical=='liquid' else pip<1)
    def test_legacy_payload_and_iteration_sequence(self):
        p=read(HERE/'production.json')
        for r in p['compatibility']:
            self.assertTrue(r['same_payload_and_diagnostics']);self.assertTrue(r['same_iteration_sequence'])
        for r in p['inverses']:
            if r['cap']==100:self.assertTrue(r['legacy_equal'])
    def test_scope_preserved(self):
        rows=read(HERE/'production.json')['application_scope']
        self.assertEqual(len(rows),32);self.assertTrue(all(r['admitted'] for r in rows[:30]));self.assertTrue(all(not r['admitted'] for r in rows[30:]))
    def test_complete_PS_fresh_profile_and_balances(self):
        for row in read(HERE/'production.json')['chains']:
            r=row['result']
            if r['status']!='accepted_prototype':
                self.assertEqual(row['cap'],100);self.assertEqual(r['stage'],'PS');self.assertNotIn('outlet',r);continue
            self.assertLessEqual(abs(r['energy']['pump_residual_W']),r['energy']['pump_allowance_W'])
            self.assertLessEqual(abs(r['energy']['integrated_residual_W']),r['energy']['integrated_allowance_W'])
            if r['identity']:self.assertEqual(r['diagnostics'],{});continue
            d=r['diagnostics']['PS']['diagnostics'];self.assertEqual(d['scan_count'],64);self.assertEqual(d['failures'],[]);self.assertEqual(d['candidate_count'],1)
            for k in ('PS','PH'):
                d=r['diagnostics'][k]['diagnostics'];self.assertEqual(d['fresh_final_count'],1);self.assertEqual(d['pt_settings']['flash_max_iterations'],row['cap'])
            self.assertFalse(r['production_support'])
if __name__=='__main__':unittest.main()
