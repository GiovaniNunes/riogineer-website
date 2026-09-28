"""EOS gate uses frozen independent data, never an oracle recalculated by production."""
import json
from pathlib import Path
import unittest
from riogineer_engine.pr_eos import BinaryInteractions, PengRobinsonEOS, pure_parameters, real_cubic_roots, ThermodynamicError

REFERENCE = json.loads((Path(__file__).resolve().parents[2]/'benchmarks/peng_robinson/methane_nhexane_pr_reference.json').read_text())
IDS = tuple(REFERENCE['component_order'])
BIP = BinaryInteractions('explicit_zero@1.0', IDS, ((0.,0.),(0.,0.)), 'Explicit mathematical qualification specification')


def eos(t=300., p=300000., ids=IDS, bip=BIP):
    return PengRobinsonEOS(ids, t, p, bip)


class EOSGate(unittest.TestCase):
    def close(self, actual, expected, quantity):
        tol = REFERENCE['acceptance_tolerances'][quantity]
        self.assertLessEqual(abs(actual-expected), tol['atol']+tol['rtol']*abs(expected), (quantity,actual,expected))

    def test_pure_parameters(self):
        for ref in REFERENCE['pure_parameters']['components']:
            p = pure_parameters(ref['id'], REFERENCE['pure_parameters']['T_K'])
            for attr,key in [('kappa','kappa'),('alpha','alpha'),('a','a_i_Pa_m6_mol2'),('b','b_i_m3_mol')]:
                self.close(getattr(p,attr),ref[key],key)

    def test_mixing_and_all_roots(self):
        for c in REFERENCE['cases']:
            e = eos(c['T_K'],c['P_Pa_abs'])
            for key in ('homogeneous_mixture','mixture_at_x','mixture_at_y'):
                if key not in c: continue
                ref = c[key]; m = e.mixture(ref['composition'])
                for attr,k,t in [('a','a_mix_Pa_m6_mol2','a_mix_Pa_m6_mol2'),('b','b_mix_m3_mol','b_mix_m3_mol'),('A','A','A_B'),('B','B','A_B')]:
                    self.close(getattr(m,attr),ref[k],t)
                self.assertEqual(len(m.roots),len(ref['physical_real_Z_roots']))
                for v,r in zip(m.roots,ref['physical_real_Z_roots']): self.close(v,r,'Z_roots')
                self.close(m.roots[0],ref['smallest_real_root'],'Z_roots')
                self.close(m.roots[-1],ref['largest_real_root'],'Z_roots')

    def test_fixed_composition_fugacity(self):
        from math import exp
        for c in REFERENCE['cases']:
            e=eos(c['T_K'],c['P_Pa_abs'])
            for label,index in [('liquid',0),('vapor',-1)]:
                if label not in c: continue
                ref=c[label]; m=e.mixture(ref['composition']); f=e.fugacity(m,m.roots[index])
                self.close(f.Z,ref['Z'],'Z_roots')
                for actual,expected,phi,phiref in zip(f.ln_phi,ref['ln_phi'],f.phi,ref['phi']):
                    self.close(actual,expected,'ln_phi')
                    tol=REFERENCE['acceptance_tolerances']['ln_phi']
                    self.assertLessEqual(abs(phi-phiref),phiref*(exp(tol['atol']+tol['rtol']*abs(expected))-1))

    def test_component_permutation(self):
        a=eos().mixture((.2,.8))
        reverse=BinaryInteractions('reverse',IDS[::-1],BIP.values,BIP.source)
        e=eos(ids=IDS[::-1],bip=reverse); b=e.mixture((.8,.2))
        self.close(a.a,b.a,'a_mix_Pa_m6_mol2')
        for x,y in zip(a.roots,b.roots): self.close(x,y,'Z_roots')
        f=eos().fugacity(a,a.roots[0]); g=e.fugacity(b,b.roots[0])
        for x,y in zip(f.ln_phi,g.ln_phi[::-1]): self.close(x,y,'ln_phi')

    def test_root_and_log_domain_guards(self):
        self.assertEqual(real_cubic_roots(0,0,0),(0.,))
        for a,b in zip(real_cubic_roots(-6,11,-6),(1,2,3)): self.assertAlmostEqual(a,b)
        self.assertAlmostEqual(real_cubic_roots(0,1,1)[0],-.6823278038280193)
        m=eos().mixture((.5,.5))
        with self.assertRaises(ThermodynamicError): eos().fugacity(m,m.B)

    def test_bip_validation_and_nonzero_sensitivity(self):
        for values in [((0,),(0,)),((0,0),),((1,0),(0,0)),((0,.1),(.2,0)),((0,float('nan')),(float('nan'),0))]:
            with self.assertRaises(ThermodynamicError): BinaryInteractions('bad',IDS,values,'test')
        b=BinaryInteractions('nonzero',IDS,((0,.02),(.02,0)),'explicit sensitivity')
        self.assertNotEqual(eos(bip=b).mixture((.5,.5)).a,eos().mixture((.5,.5)).a)

    def test_phase_identification_matches_independent_derivatives(self):
        for c in REFERENCE['cases']:
            e=eos(c['T_K'],c['P_Pa_abs']); m=e.mixture(c['z']); f=e.lowest_gibbs(m)
            self.assertAlmostEqual(e.phase_identification(m,f.Z),c['stability']['phase_identification_parameter'],delta=1e-10)
