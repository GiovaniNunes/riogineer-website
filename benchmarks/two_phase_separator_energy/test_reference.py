"""External-library-only M17 reference verification, independent of production."""
import json,math,unittest
from copy import deepcopy
from reference import ARTIFACT,build,encode,qualify,specifications,validate_spec,EntropyPT,solve_ph
from benchmarks.peng_robinson_ph.equilibrium import TrialFailure


class ReferenceTests(unittest.TestCase):
    def test_frozen_reproduction(self):self.assertEqual(ARTIFACT.read_text(),encode(build()))

    def test_negative_specifications(self):
        base=specifications()[0]['inputs']
        for k,v in [('mode','unknown'),('F',0),('F',-1),('F',float('inf')),('Pin',0),('Pout',4e7),('Pout',-1),('Tin',199),('Tout',501),('z',[.4,.4]),('z',[-.1,1.1]),('duty_W',0),('components',['water'])]:
            with self.subTest(k=k,v=v),self.assertRaises(ValueError):validate_spec(dict(base,**{k:v}))
        bad=dict(base,mode='adiabatic')
        with self.assertRaises(ValueError):validate_spec(bad)
        for k in base:
            bad=deepcopy(base);del bad[k]
            with self.assertRaises(ValueError):validate_spec(bad)

    def test_coverage_and_energy_signs(self):
        rows=json.loads(ARTIFACT.read_text())['cases']
        for mode in ('specified_temperature','adiabatic'):
            group=[r for r in rows if r['inputs']['mode']==mode]
            self.assertEqual({r['outlet']['classification'] for r in group},{'single_vapor','single_liquid','vapor_liquid'})
            self.assertTrue(any(r['inputs']['Pin']==r['inputs']['Pout'] for r in group))
            self.assertTrue(any(r['inputs']['Pin']>r['inputs']['Pout'] for r in group))
        self.assertTrue(any(r['duty_W']>0 for r in rows));self.assertTrue(any(r['duty_W']<0 for r in rows))
        self.assertTrue(any(r['inputs']['mode']=='adiabatic' and r['inlet']['classification']!=r['outlet']['classification'] for r in rows))

    def test_phase_inventory_and_absence(self):
        for r in json.loads(ARTIFACT.read_text())['cases']:
            for name,p in r['outputs'].items():
                self.assertAlmostEqual(p['mass_flow_kg_h'],sum(p['component_mass_flow_kg_h']))
                if p['molar_flow_mol_s']==0:
                    self.assertIsNone(p['composition']);self.assertIsNone(p['h_J_mol']);self.assertEqual(p['enthalpy_flow_W'],0)
                else:self.assertAlmostEqual(p['enthalpy_flow_W'],p['molar_flow_mol_s']*p['h_J_mol'])
            self.assertLessEqual(abs(r['energy_residual_W']),r['inputs']['F']*1e-6+1e-8)

    def test_independent_inverse_unbracketed_ambiguous_and_hole(self):
        def state(T,H):return dict(T_K=T,H_eq_J_mol=H,classification='synthetic',beta=1.,phases={})
        out=solve_ph(1e6,[.5,.5],0,evaluator=lambda T,P,z:state(T,1e6+T))
        self.assertEqual(out['status'],'enthalpy_target_not_bracketed')
        out=solve_ph(1e6,[.5,.5],0,evaluator=lambda T,P,z:state(T,(T-270)*(T-430)))
        self.assertEqual(out['status'],'multiple_ph_roots')
        def hole(T,P,z):
            if 290<T<310:raise TrialFailure('pt','controlled property hole')
            return state(T,T-300)
        out=solve_ph(1e6,[.5,.5],0,evaluator=hole)
        self.assertEqual(out['status'],'pt_evaluation_failure');self.assertNotIn('solution',out)

    def test_real_coexistence_gap(self):
        pt=EntropyPT();a=pt.evaluate(350.,1e7,[0.,1.]);out=solve_ph(1000.,[0.,1.],a['H_eq_J_mol'],evaluator=pt.evaluate)
        self.assertEqual(out['status'],'ph_nonconvergence');self.assertNotIn('solution',out)


if __name__=='__main__':unittest.main()
