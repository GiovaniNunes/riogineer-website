"""Independent pre-M8.1 acceptance, never importing production thermodynamics."""
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import reference as ref
from study import Study, rr, rr_value

FROZEN=json.loads(ref.ARTIFACT.read_text())


class BubbleMatrix(unittest.TestCase):
    pass


def bubble_test(case):
    def test(self):
        expected=case['reference'];s=Study()
        actual=s.equilibrium(expected['T_K'],expected['P_Pa_abs'],expected['z'])
        checks=ref.compare(actual,expected,FROZEN['inherited_acceptance_tolerances']['PH'])
        self.assertTrue(all(r['passed'] for r in checks))
        self.assertLessEqual(max(abs(v) for v in actual['material_reconstruction_residual']),1e-10)
        if actual['classification']=='single_liquid':
            self.assertEqual(actual['beta'],0.)
            self.assertNotIn('vapor',actual['phases'])
            self.assertIsNone(actual['final_K'])
            self.assertIsNone(case['stability_seed_experiment'])
        else:
            self.assertGreater(actual['beta'],0.)
            self.assertLess(actual['beta'],1.)
            self.assertLess(max(abs(v) for v in actual['log_fugacity_residual']),1e-11)
            for i,k in enumerate(actual['final_K']):
                self.assertEqual(k,actual['phases']['vapor']['composition'][i]/actual['phases']['liquid']['composition'][i])
            for label in ['liquid','vapor']:
                for phi,lnphi in zip(actual['phases'][label]['phi'],actual['phases'][label]['ln_phi']):
                    self.assertAlmostEqual(math.log(phi),lnphi,places=13)
    return test


for case in FROZEN['bubble_cases']:
    setattr(BubbleMatrix,'test_'+case['case_id'].lower(),bubble_test(case))


class Qualification(unittest.TestCase):
    def test_boundary_bracket_without_fake_vapor_below(self):
        T=FROZEN['bubble_boundary']['T_K']
        cases=FROZEN['bubble_cases']
        self.assertTrue(all(c['reference']['classification']=='single_liquid' for c in cases if c['reference']['T_K']<T))
        self.assertTrue(all(c['reference']['classification']=='vapor_liquid' for c in cases if c['reference']['T_K']>T))
        saturation=FROZEN['bubble_boundary']
        self.assertEqual(saturation['liquid']['composition'],saturation['z'])
        for x,y,lp,vp in zip(saturation['z'],saturation['incipient_vapor']['composition'],
                             saturation['liquid']['ln_phi'],saturation['incipient_vapor']['ln_phi']):
            self.assertLess(abs(math.log(x)+lp-math.log(y)-vp),1e-9)

    def test_center_has_stability_split_but_no_Wilson_root(self):
        c=next(c for c in FROZEN['bubble_cases'] if c['case_id']=='BUBBLE_CENTER')
        self.assertTrue(c['needs_stability_restart'])
        self.assertFalse(c['independent_homogeneous_stable'])
        self.assertLess(c['stability_trial']['tpd_RT'],0)
        self.assertLess(c['Wilson_RR']['F0'],0)
        self.assertLess(c['Wilson_RR']['F1'],0)
        self.assertEqual(c['Wilson_RR']['status'],'liquid_tendency')
        self.assertAlmostEqual(c['reference']['beta'],.002099474006536296,places=14)

    def test_Wilson_region_systematic(self):
        region=FROZEN['Wilson_no_root_region']
        self.assertGreater(region['Wilson_F0_zero_T_K'],region['independent_bubble_T_K'])
        failures=[c for c in FROZEN['bubble_cases'] if c['needs_stability_restart']]
        self.assertEqual(len(failures),7)
        for c in failures:
            self.assertGreater(c['reference']['T_K'],region['independent_bubble_T_K'])
            self.assertLess(c['reference']['T_K'],region['Wilson_F0_zero_T_K'])

    def test_stationary_scaling_and_tpd_identity(self):
        for c in FROZEN['bubble_cases']:
            s=c['stability_trial'];z=c['reference']['z']
            self.assertAlmostEqual(s['tpd_RT'],-math.log(s['S']),places=11)
            self.assertLess(s['stationarity_error'],1e-11)
            for k,w,zi in zip(s['seed_K'],s['composition'],z):
                self.assertLess(abs(k-s['S']*w/zi),1e-11)
            self.assertLess(abs(s['normalized_only_F0']),1e-14)

    def test_unstable_stability_seed_has_physical_RR_root(self):
        for c in FROZEN['bubble_cases']:
            if c['independent_homogeneous_stable']: continue
            initial=c['stability_trial']['seed_RR']
            self.assertEqual(initial['status'],'two_phase')
            self.assertGreater(initial['beta'],0.)
            self.assertLess(initial['beta'],1.)
            # A seed is deliberately not frozen equilibrium K or beta.
            self.assertNotEqual(initial['beta'],c['reference']['beta'])

    def test_stability_seed_converges_independently(self):
        s=Study()
        for c in FROZEN['bubble_cases']:
            if c['independent_homogeneous_stable']: continue
            e=c['reference'];actual=s.successive_substitution(e['T_K'],e['P_Pa_abs'],e['z'],1e-12,c['stability_trial']['seed_K'])
            self.assertTrue(all(r['passed'] for r in ref.compare(actual,e,FROZEN['inherited_acceptance_tolerances']['PH'])))

    def test_RR_endpoint_semantics_not_forced_split(self):
        self.assertEqual(rr([.5,.5],[.8,.2])['status'],'liquid_tendency')
        self.assertEqual(rr([.5,.5],[2.,3.])['status'],'vapor_tendency')
        for K in [[1.,1.],[1.5,.5]]:
            self.assertFalse(rr([.5,.5],K)['physical_interior_root'])
        good=rr([.5,.5],[2.,.5])
        self.assertTrue(good['physical_interior_root'])
        self.assertLessEqual(abs(rr_value([.5,.5],[2.,.5],good['beta'])),2e-14)
        with self.assertRaises(ValueError):rr([.5,.5],[float('nan'),.5])

    def test_dew_frozen_PH_reference_unchanged_values(self):
        old=json.loads(ref.PH_PATH.read_text())
        expected=next(c for c in old['cases'] if c['case_id']=='PH_DEW_BELOW')['forward']
        self.assertEqual(expected['T_K'],FROZEN['dew_reference']['T_K'])
        self.assertTrue(all(c['passed'] for c in ref.compare(FROZEN['dew_reference'],expected,old['tolerances'])))

    def test_precision_study_meets_each_requested_fugacity_limit(self):
        for row in FROZEN['dew_precision_study']:
            s=row['fixed_T_result']
            self.assertLessEqual(s['max_log_fugacity_residual'],row['requested_log_fugacity_tolerance'])
            self.assertLessEqual(s['iterations'],100)
            self.assertLessEqual(max(abs(v) for v in s['material_reconstruction_residual']),1e-10)

    def test_precision_trend_and_cost(self):
        rows=FROZEN['dew_precision_study'];expected=FROZEN['dew_reference']
        errors=[abs(r['fixed_T_result']['H_eq_J_mol']-expected['H_eq_J_mol']) for r in rows]
        margins=[r['local_H_matching']['minimum_margin_factor'] for r in rows]
        self.assertTrue(all(a>b for a,b in zip(errors,errors[1:])))
        self.assertTrue(all(a<b for a,b in zip(margins,margins[1:])))
        self.assertEqual([r['fixed_T_result']['iterations'] for r in rows],[53,59,62,65,68,71])

    def test_recommendation_is_loosest_target_with_predeclared_margin(self):
        rec=FROZEN['recommendation'];rows=FROZEN['dew_precision_study']
        qualifying=[r for r in rows if r['local_H_matching']['max_allowance_fraction']<=ref.MAX_DOWNSTREAM_ALLOWANCE_FRACTION]
        self.assertEqual(rec['high_accuracy_log_fugacity_tolerance'],qualifying[0]['requested_log_fugacity_tolerance'])
        self.assertEqual(rec['high_accuracy_log_fugacity_tolerance'],1e-12)
        self.assertGreaterEqual(rec['observed_minimum_margin_factor'],5.)
        self.assertEqual(rec['standard_log_fugacity_tolerance'],1e-11)

    def test_standard_dew_downstream_miss_is_preserved(self):
        row=next(r for r in FROZEN['dew_precision_study'] if r['requested_log_fugacity_tolerance']==1e-11)
        self.assertFalse(row['local_H_matching']['all_passed'])
        failed=[r['quantity'] for r in row['local_H_matching']['comparisons'] if not r['passed']]
        self.assertIn('liquid.h_J_mol',failed)

    def test_recommended_local_H_match_has_margin_for_all_fields(self):
        row=next(r for r in FROZEN['dew_precision_study'] if r['requested_log_fugacity_tolerance']==1e-12)
        self.assertTrue(row['local_H_matching']['all_passed'])
        self.assertTrue(all(c['allowance_fraction']<=.2 for c in row['local_H_matching']['comparisons']))
        self.assertLessEqual(abs(row['local_H_matching']['H_residual_J_mol']),1e-6)

    def test_source_integrity(self):
        for path,digest in FROZEN['metadata']['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ref.ROOT/path).read_bytes()).hexdigest(),digest)
        old=json.loads(ref.PH_PATH.read_text())
        self.assertEqual(FROZEN['inherited_acceptance_tolerances']['PH'],old['tolerances'])

    def test_two_fresh_builds_equal_frozen_bytes(self):
        text=ref.ARTIFACT.read_text()
        self.assertEqual(ref.serialize(ref.build()),text)
        self.assertEqual(ref.serialize(ref.build()),text)

    def test_no_production_runtime_imports(self):
        self.assertFalse(any(k.startswith('riogineer_engine') for k in sys.modules))


if __name__=='__main__':unittest.main()
