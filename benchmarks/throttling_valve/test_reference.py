"""Independent valve qualification and property-hole acceptance boundaries."""
import json
import unittest
try:
    from . import reference as ref
    from .solver import calculate, EntropyPT, TrialFailure, solve_ph
except ImportError:
    import reference as ref
    from solver import calculate, EntropyPT, TrialFailure, solve_ph


class ValveQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=ref.build()
        cls.cases={c['case_id']:c for c in cls.data['cases']}

    def test_frozen_reference(self):
        self.assertEqual(ref.encode(self.data),ref.ARTIFACT.read_text())

    def test_canonical_flashes_inside_region(self):
        r=self.cases['CANONICAL']['result']
        self.assertEqual(r['inlet']['classification'],'single_liquid')
        self.assertEqual(r['outlet']['classification'],'vapor_liquid')
        self.assertGreater(r['outlet']['beta'],.1)
        self.assertLess(r['outlet']['beta'],.9)
        self.assertEqual(r['PH']['candidate_count'],1)
        self.assertEqual(r['PH']['final_evaluations'],1)
        self.assertEqual(r['final_endpoint_evaluations'],1)
        self.assertLess(abs(r['PH_residual_J_mol']),1e-6)

    def test_observed_heating_and_cooling(self):
        self.assertLess(self.cases['CANONICAL']['result']['delta_T_K'],0)
        self.assertGreater(self.cases['LIQUID_HEATING']['result']['delta_T_K'],0)
        self.assertLess(abs(self.cases['NEGLIGIBLE_DROP']['result']['delta_T_K']),1e-4)

    def test_flow_invariance(self):
        base=self.cases['CANONICAL']['result']
        for name in ['DOUBLE_FLOW','LOW_FLOW']:
            r=self.cases[name]['result']
            self.assertEqual(r['outlet'],base['outlet'])
            self.assertEqual(r['inlet'],base['inlet'])
            self.assertEqual(r['energy_residual_W'],base['energy_residual_W']*r['F_in_mol_s']/base['F_in_mol_s'])

    def test_pressure_series_is_not_forced_monotonic_temperature(self):
        self.assertGreater(self.cases['PRESSURE_MODERATE']['result']['delta_T_K'],0)
        self.assertLess(self.cases['PRESSURE_SUBSTANTIAL']['result']['delta_T_K'],0)

    def test_phase_material_enthalpy_reconstruction(self):
        for c in self.data['cases']+self.data['separate_studies']:
            r=c['result'];s=r['outlet'];b=s['beta'];weights={'liquid':1-b,'vapor':b}
            self.assertEqual(r['F_in_mol_s'],r['F_out_mol_s'])
            self.assertEqual(r['z_in'],r['z_out'])
            for j,z in enumerate(r['z_in']):
                self.assertAlmostEqual(sum(weights[k]*p['composition'][j] for k,p in s['phases'].items()),z,places=10)
            self.assertLess(abs(sum(weights[k]*p['h_J_mol'] for k,p in s['phases'].items())-s['H_eq_J_mol']),1e-6)
            self.assertGreaterEqual(r['delta_S_J_mol_K'],-1e-8)

    def test_pure_endpoints(self):
        for name in ['PURE_METHANE','PURE_HEXANE_VAPOR','PURE_HEXANE_LIQUID']:
            self.assertTrue(self.cases[name]['result']['accepted_outlet'])

    def test_two_phase_inlet_is_separate(self):
        c=next(c for c in self.data['separate_studies'] if c['case_id']=='TWO_PHASE_INLET')
        self.assertFalse(c['accepted_primary_scope'])
        self.assertEqual(c['result']['inlet']['classification'],'vapor_liquid')
        self.assertEqual(calculate(**c['inputs'])['status'],'inlet_service_scope')

    def test_exact_hole_remains_failure(self):
        with self.assertRaisesRegex(TrialFailure,'End of SS without convergence'):
            EntropyPT().evaluate(461.1764705882353,1e7,[.5,.5])

    def test_full_domain_is_not_silently_bridged(self):
        r=calculate(**ref.spec(Pout=1e7),controls=dict(grid_points=256))
        self.assertEqual(r['status'],'pt_evaluation_failure')
        self.assertFalse(r['accepted_outlet'])
        self.assertNotIn('outlet',r)

    def test_explicit_connected_interval(self):
        c=self.cases['PRESSURE_FLASH_ONSET']
        self.assertEqual(c['inputs']['qualified_interval'],[280.,350.])
        for check in self.data['property_hole_investigation']['connected_interval']:
            self.assertEqual(check['result']['PH']['candidate_count'],1)
            self.assertEqual(check['result']['PH']['monotonicity'],'increasing')
            self.assertLess(abs(check['state']['H_residual_J_mol']),1e-6)

    def test_invalid_intervals_rejected(self):
        for interval in [(199.,350.),(280.,501.),(350.,280.),(300.,300.),[280.],None]:
            r=calculate(**ref.spec(),qualified_interval=interval)
            self.assertEqual(r['status'],'temperature_domain_invalid')
            self.assertNotIn('outlet',r)

    def test_outside_declared_interval_cannot_be_published(self):
        pt=EntropyPT()
        target=pt.evaluate(300.,3e7,[.5,.5])['H_eq_J_mol']
        cached=solve_ph(1e7,[.5,.5],target,evaluator=pt.evaluate)
        self.assertEqual(cached['status'],'success')
        r=calculate(**ref.spec(Pout=1e7),qualified_interval=(310.,350.),
                    ph_solver=lambda *args,**kwargs:cached)
        self.assertEqual(r['status'],'final_acceptance_failed')
        self.assertFalse(r['accepted_outlet'])
        self.assertNotIn('outlet',r)

    def test_boundary_studies_bracket_phases(self):
        c={r['case_id']:r for r in self.data['separate_studies']}
        self.assertEqual(c['BUBBLE_BELOW']['result']['outlet']['classification'],'single_liquid')
        self.assertEqual(c['BUBBLE_ABOVE']['result']['outlet']['classification'],'vapor_liquid')
        self.assertEqual(c['DEW_BELOW']['result']['outlet']['classification'],'vapor_liquid')
        self.assertEqual(c['DEW_ABOVE']['result']['outlet']['classification'],'single_vapor')

    def test_call_order(self):
        self.assertEqual(len(self.data['call_order']),12)
        self.assertTrue(all(r['byte_identical'] for r in self.data['call_order']))

    def test_negative_atomicity_after_success(self):
        pt=EntropyPT()
        self.assertTrue(calculate(**ref.spec(),oracle=pt)['accepted_outlet'])
        for row in ref.negative_specs():
            r=ref.run_negative(row,oracle=pt)['result']
            self.assertFalse(r['accepted_outlet'])
            self.assertNotIn('outlet',r)
        self.assertEqual(ref.compact(calculate(**ref.spec(),oracle=pt)),self.cases['CANONICAL']['result'])


def negative_test(row):
    def test(self):
        r=ref.run_negative(row)['result']
        self.assertFalse(r['accepted_outlet'])
        self.assertEqual(r['status'],row['expected_status'])
        self.assertEqual(r['failure_stage'],row['expected_stage'])
    return test


for index,row in enumerate(ref.negative_specs()):
    setattr(ValveQualification,'test_negative_'+str(index)+'_'+row['case_id'].replace('-','_').replace('.','_'),negative_test(row))

if __name__=='__main__':unittest.main()
