"""Independent acceptance gates; no production imports or writes."""
import json
import math
import unittest

import reference as ref


class Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads(ref.FROZEN.read_text())
        cls.actual = ref.build()

    def test_deterministic_reproduction(self):
        self.assertEqual(self.actual, self.frozen)
        self.assertEqual(ref.build(), self.actual)

    def test_mathematical_vapor_mapping(self):
        self.assertEqual(ref.seed([.5,.5],[.1,.9],2.,'vapor_parent_liquid_trial'),
                         [2.5,.5/1.8])

    def test_mathematical_liquid_mapping(self):
        self.assertEqual(ref.seed([.5,.5],[.1,.9],2.,'liquid_parent_vapor_trial'),
                         [.4,3.6])

    def test_orientation(self):
        self.assertEqual(ref.orientation(.99,15.),'vapor_parent_liquid_trial')
        self.assertEqual(ref.orientation(15.,.99),'liquid_parent_vapor_trial')

    def test_ambiguous_orientation_rejected(self):
        for p,t in [(1.,15.),(.9,.8),(15.,16.),(float('nan'),15.)]:
            with self.subTest(p=p,t=t), self.assertRaises(ValueError):
                ref.orientation(p,t)

    def test_invalid_compositions_rejected(self):
        for z,w,S in [([0.,1.],[.1,.9],2.),([.5,.4],[.1,.9],2.),
                      ([.5,.5],[.1,.8],2.),([.5],[1.],2.),
                      ([.5,.5],[.1,.9],0.),([.5,.5],[.1,.9],float('inf')),
                      ([.5,.5],[float('nan'),.9],2.)]:
            with self.subTest(z=z,w=w,S=S), self.assertRaises(ValueError):
                ref.seed(z,w,S,'vapor_parent_liquid_trial')

    def test_invalid_orientation_rejected(self):
        with self.assertRaises(ValueError):
            ref.seed([.5,.5],[.1,.9],2.,'guessed')
        with self.assertRaises(ValueError):
            ref.restart_required(True,'guessed',{'physical_interior_root':False})

    def test_stability_required_even_when_wilson_has_no_root(self):
        self.assertFalse(ref.restart_required(False,'vapor_parent_liquid_trial',
                                             {'physical_interior_root':False}))

    def test_wilson_root_suppresses_restart(self):
        self.assertFalse(ref.restart_required(True,'vapor_parent_liquid_trial',
                                             {'physical_interior_root':True}))

    def test_four_original_states_match_unchanged_ph_scan(self):
        found=[c for c in self.actual['cases'] if c['original_failure']]
        self.assertEqual(len(found),4)
        for c,expected in zip(found,[.6973798823980142,.7601629763456957,
                                     .8503531817039216,.9878592504353508]):
            self.assertTrue(c['restart_required'])
            self.assertAlmostEqual(c['independent_equilibrium']['beta'],expected,14)

    def test_neighborhood_has_stable_and_wilson_controls(self):
        cases=self.actual['cases']
        self.assertEqual(sum(c['independent_equilibrium']['classification']=='single_vapor'
                             for c in cases),4)
        self.assertEqual(sum(c['stability']['Wilson_RR']['physical_interior_root']
                             for c in cases),2)

    def test_no_production_imports(self):
        import sys
        self.assertFalse(any(k.startswith('riogineer_engine') for k in sys.modules))


def case_test(index):
    def check(self):
        c=self.actual['cases'][index]; frozen=self.frozen['cases'][index]
        t=c['stability']; eq=c['independent_equilibrium']
        self.assertEqual(t['orientation'],'vapor_parent_liquid_trial')
        self.assertLess(t['parent_PIP'],1.)
        self.assertGreater(t['trial_PIP'],1.)
        self.assertAlmostEqual(t['tpd_RT'],-math.log(t['S']),11)
        self.assertLess(t['stationarity_error'],1e-11)
        self.assertAlmostEqual(t['library_sum'],t['S'],11)
        for zi,wi,Wi,k,direct,lib in zip(ref.Z,t['trial_composition'],t['unnormalized_W'],
                                        t['derived_K'],t['direct_fugacity_K'],
                                        t['library_trial_parent_ratios']):
            self.assertAlmostEqual(wi,Wi/t['S'],11)
            self.assertAlmostEqual(k/direct,1.,11)
            self.assertAlmostEqual(lib*k,1.,11)
            self.assertAlmostEqual(k*Wi/zi,1.,11)
        self.assertAlmostEqual(t['normalized_only_RR']['F1'],0.,14)
        self.assertAlmostEqual(t['derived_RR']['F1'],1.-t['S'],13)
        ref.compare(eq,frozen['independent_equilibrium'])
        if eq['classification']=='single_vapor':
            self.assertFalse(c['restart_required'])
            self.assertEqual(c['precision_experiments'],{})
            self.assertGreater(t['tpd_RT'],0.)
            self.assertNotIn('liquid',eq['phases'])
        else:
            self.assertLess(t['tpd_RT'],0.)
            self.assertGreater(t['derived_RR']['F0'],0.)
            self.assertLess(t['derived_RR']['F1'],0.)
            self.assertTrue(0 < t['derived_RR']['beta'] < 1)
            for name,tol in [('standard',1e-11),('high_accuracy',1e-12)]:
                run=c['precision_experiments'][name]
                ref.compare(run,eq)
                self.assertLessEqual(run['max_log_fugacity_residual'],tol)
                self.assertLessEqual(run['iterations'],100)
                for step in run['history']:
                    rr=ref.rr(ref.Z,step['K'])
                    self.assertTrue(rr['physical_interior_root'])
                    self.assertLessEqual(abs(rr['residual']),2e-14)
                self.assertNotEqual(run['history'][0]['K'],eq['final_K'])
            ref.compare(c['precision_experiments']['standard'],
                        c['precision_experiments']['high_accuracy'])
    return check


for i,T in enumerate(ref.TEMPERATURES):
    setattr(Qualification,f'test_state_{i:02d}_{str(T).replace(".","_")}',case_test(i))

if __name__ == '__main__':
    unittest.main()
