"""Benchmark-only qualification; does not alter production regression expectations."""
import copy
import json
import math
import unittest
from reference import ARTIFACT, CONSTANTS, R, Z, build, compare, dataset_check, validate


class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads(ARTIFACT.read_text())
        cls.fresh = build()

    def test_exact_dataset_and_full_frozen_reproduction(self):
        dataset_check()
        validate(self.saved)
        compare(self.saved,self.fresh)

    def test_exact_pr_coefficients_and_classical_mixing(self):
        pure=self.saved['pure_parameters']['components']
        for c,p in zip(CONSTANTS,pure):
            k=.37464+1.54226*c['omega']-.26992*c['omega']**2
            alpha=(1+k*(1-math.sqrt(300/c['Tc_K'])))**2
            self.assertAlmostEqual(k,p['kappa'],delta=1e-14)
            self.assertAlmostEqual(alpha,p['alpha'],delta=1e-14)
            self.assertAlmostEqual(.45724*R**2*c['Tc_K']**2/c['Pc_Pa_abs']*alpha,p['a_i_Pa_m6_mol2'],delta=1e-14)
            self.assertAlmostEqual(.07780*R*c['Tc_K']/c['Pc_Pa_abs'],p['b_i_m3_mol'],delta=1e-18)
        for key in ['homogeneous_mixture','mixture_at_x','mixture_at_y']:
            m=self.saved['cases'][1][key]; zs=m['composition']
            a=sum(zs[i]*zs[j]*math.sqrt(pure[i]['a_i_Pa_m6_mol2']*pure[j]['a_i_Pa_m6_mol2']) for i in range(2) for j in range(2))
            b=sum(zs[i]*pure[i]['b_i_m3_mol'] for i in range(2))
            self.assertAlmostEqual(a,m['a_mix_Pa_m6_mol2'],delta=1e-14)
            self.assertAlmostEqual(b,m['b_mix_m3_mol'],delta=1e-18)

    def test_distinct_stable_states_and_neighborhoods(self):
        a,b,c=self.saved['cases']
        self.assertTrue(a['stability']['homogeneous_feed_stable'])
        self.assertFalse(b['stability']['homogeneous_feed_stable'])
        self.assertTrue(c['stability']['homogeneous_feed_stable'])
        # C has three roots despite being stable vapor: root count is not stability.
        self.assertEqual(len(c['homogeneous_mixture']['physical_real_Z_roots']),3)
        for case,phase in zip([a,b,c],['L','VL','V']):
            self.assertEqual(len(case['neighborhood']),9)
            self.assertTrue(all(n['phase']==phase for n in case['neighborhood']))
        self.assertGreaterEqual(b['equilibrium_common_tangent_TPD']['refined_min_TPD_RT'],-1e-9)

    def test_equilibrium_material_fugacity_and_rachford_rice(self):
        b=self.saved['cases'][1]; beta=b['beta']; x=b['liquid']['composition']; y=b['vapor']['composition']
        self.assertAlmostEqual(sum(x),1,delta=1e-12); self.assertAlmostEqual(sum(y),1,delta=1e-12)
        for i in range(2):
            self.assertAlmostEqual((1-beta)*x[i]+beta*y[i],Z[i],delta=1e-12)
            self.assertAlmostEqual(x[i]*b['liquid']['phi'][i],y[i]*b['vapor']['phi'][i],delta=1e-12)
        residual=sum(Z[i]*(b['K'][i]-1)/(1+beta*(b['K'][i]-1)) for i in range(2))
        self.assertAlmostEqual(residual,0,delta=1e-12)

    def test_all_real_roots_and_library_selection(self):
        b=self.saved['cases'][1]
        for key in ['homogeneous_mixture','mixture_at_x','mixture_at_y']:
            m=b[key]; roots=m['physical_real_Z_roots']; self.assertEqual(roots,sorted(roots))
            self.assertTrue(all(r>m['B'] for r in roots))
            self.assertTrue(all(abs(v)<1e-12 for v in m['cubic_polynomial_residuals']))
        self.assertEqual(len(b['mixture_at_x']['physical_real_Z_roots']),3)
        self.assertEqual(b['liquid']['Z'],b['mixture_at_x']['smallest_real_root'])
        self.assertEqual(b['vapor']['Z'],b['mixture_at_y']['largest_real_root'])

    def test_artifact_rejects_corruption(self):
        mutations=[
            lambda d:d['components'][0].update(Tc_K=190.6),
            lambda d:d.update(z=[.4,.6]),
            lambda d:d['cases'][0].update(classification='vapor'),
            lambda d:d['cases'][1].update(beta=.1),
            lambda d:d['cases'][1]['liquid']['composition'].__setitem__(0,.4),
            lambda d:d['cases'][1]['liquid']['phi'].__setitem__(0,10.),
            lambda d:d['cases'][1]['K'].__setitem__(0,20.),
            lambda d:d['pure_parameters']['components'][0].update(alpha=float('nan')),
        ]
        for mutate in mutations:
            bad=copy.deepcopy(self.saved); mutate(bad)
            with self.assertRaises(AssertionError): validate(bad)

    def test_tightening_precision_below_acceptance_and_optional_bip(self):
        p=self.saved['cases'][1]['precision_study']
        self.assertLess(abs(p['beta_difference']),1e-10)
        self.assertLess(max(abs(v) for v in p['x_difference']+p['y_difference']),1e-10)
        self.assertNotEqual(self.saved['optional_nonzero_kij']['beta'],self.saved['cases'][1]['beta'])


if __name__=='__main__': unittest.main()
