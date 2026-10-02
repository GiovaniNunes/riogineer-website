"""Read-only qualification checks; synthetic inverse tests are policy tests only."""
import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.configurable_separator_pump.common import read,matrix,TOLS
from benchmarks.configurable_separator_pump.prototype import solve

class PrototypePolicy(unittest.TestCase):
    def evaluator(self,fn):return lambda t:dict(S=fn(t),classification='single_liquid')
    def test_fresh_final(self):
        r=solve(self.evaluator(lambda t:t-231.628),0.,'S',64,1e-8)
        self.assertEqual(r['status'],'local_candidate');self.assertEqual(r['trials'][-1]['stage'],'fresh_final')
        self.assertFalse(r['global_uniqueness'])
    def test_hole_does_not_hide_incomplete_coverage(self):
        def q(t):
            if t>460:raise ValueError('unknown PT region')
            return dict(S=t-232,classification='single_liquid')
        r=solve(q,0.,'S',64,1e-8)
        self.assertEqual(r['status'],'local_candidate');self.assertEqual(r['coverage'],'incomplete')
    def test_hole_cannot_be_bridged(self):
        def q(t):
            if 225<t<240:raise ValueError('unknown at root')
            return dict(S=t-232,classification='single_liquid')
        r=solve(q,0.,'S',64,1e-8);self.assertEqual(r['status'],'unbracketed');self.assertNotIn('state',r)
    def test_competing_roots(self):
        r=solve(self.evaluator(lambda t:(t-231)*(t-330)),0.,'S',64,1e-8)
        self.assertEqual(r['status'],'ambiguous');self.assertNotIn('state',r)
    def test_discontinuity_and_nonfinite(self):
        r=solve(self.evaluator(lambda t:-1. if t<232 else 1.),0.,'S',64,1e-8)
        self.assertEqual(r['status'],'fresh_residual_failed')
        r=solve(self.evaluator(lambda t:math.nan),0.,'S',64,1e-8)
        self.assertEqual(r['status'],'unbracketed');self.assertEqual(r['coverage'],'incomplete')
    def test_hole_during_refinement(self):
        def q(t):
            if 231<t<232:raise ValueError('refinement hole')
            return dict(S=t-231.5,classification='single_liquid')
        r=solve(q,0.,'S',64,1e-8);self.assertEqual(r['status'],'root_evaluation_failed')

class FrozenEvidence(unittest.TestCase):
    def test_matrix_and_counts(self):
        _,rows=matrix();d=read('production.json');l=read('candidate_ledger.json')
        self.assertEqual(len(rows),64);self.assertEqual(len(d['cases']),64)
        self.assertEqual(sum(l['counts'].values()),64)
        self.assertEqual(sum(c['role']=='M20_anchor' for c in d['cases']),30)
        self.assertEqual(l['failed_comparisons'],0)
        self.assertEqual(l['prototype_failed_comparisons'],0)
        self.assertEqual(l['contract_negative_failures'],0)
    def test_scope_and_no_prototype_promotion(self):
        for c in read('production.json')['cases']:
            if c['role']=='M20_anchor':
                self.assertEqual(c['application']['status'],'admitted');self.assertEqual(c['disposition'],'accepted')
            if c['role']=='8MPa_challenge':
                self.assertEqual(c['disposition'],'unresolved');self.assertEqual(c['application']['status'],'rejected')
                self.assertEqual(c['production_numerics']['stage'],'PS')
                self.assertFalse(c['prototype']['production_qualified'])
                self.assertEqual(c['prototype']['PS']['coverage'],'incomplete')
                self.assertEqual(c['reference_target_PH_diagnostic']['diagnostics']['status'],'success')
    def test_sources_and_tolerances(self):
        r=read('reference.json');self.assertFalse(r['production_imported']);self.assertEqual(r['tolerances'],TOLS)
        for s in read('production.json')['source_checks'].values():self.assertTrue(s['passed'])
    def test_conservation_and_identity(self):
        for c in read('production.json')['cases']:
            if c['disposition']!='accepted':continue
            a=c['guarded_callable']['result'];self.assertTrue(c['integrated_energy']['passed'])
            s=a['inlet']['stream'];o=a['outlet']
            self.assertEqual(s['component_mass_flow_kg_h'],o['component_mass_flow_kg_h'])
            if a['identity']:self.assertEqual(s,o);self.assertEqual(a['fluid_power_W'],0.)
            else:self.assertLessEqual(a['work_ratio'],1e-4)
    def test_independent_local_and_iteration_evidence(self):
        p=read('phase_comparison.json');self.assertEqual(len(p['states']),115)
        self.assertEqual(p['failed_comparisons'],0)
        d=read('iteration_diagnostic.json');self.assertEqual(d['failed_comparisons'],0)
        for c in d['cases']:
            self.assertEqual(c['result']['coverage'],'sampled_complete')
            self.assertFalse(c['production_default_changed'])
            self.assertIsNotNone(c['default_PT_final_guard'])
    def test_prototype_preserves_upstream_energy(self):
        d=read('integration_checks.json')
        self.assertEqual(len(d['prototype_paths']),2)
        for r in d['prototype_paths']:self.assertTrue(r['passed'])
        self.assertEqual(d['sources']['PT_WARM']['reason'],'absent_liquid')
    def test_nonfinite_pump_specifications_reject(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
        from riogineer_engine.separator_liquid_state import representation,identity,Failure
        from riogineer_engine.separator_liquid_pump import run
        source=read('sources.json')['PH_FLASH']['result']
        for pressure,eta in ((math.nan,.8),(math.inf,.8),(2e6,math.nan),(2e6,math.inf)):
            with self.subTest(pressure=pressure,eta=eta),self.assertRaises(Failure):
                run(representation(source),source,identity(source),pressure,eta)
if __name__=='__main__':unittest.main()
