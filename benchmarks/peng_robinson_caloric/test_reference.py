"""Independent caloric qualification; never imports production EOS/equipment."""
import copy
import json
import math
import unittest

import reference as ref
import equations as eq


class CaloricReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = ref.ARTIFACT.read_bytes()
        cls.saved = json.loads(cls.before)
        cls.fresh = ref.build()
        cls.b = next(c for c in cls.saved['cases'] if c['case_id'] == 'B')
        cls.phases = [p for c in cls.saved['cases'] for p in c['phases'].values()]
        cls.phases += cls.saved['pure_states'] + cls.saved['low_pressure_states']

    def test_frozen_reproduction(self):
        ref.compare(self.saved, self.fresh)
        self.assertEqual(self.before, ref.ARTIFACT.read_bytes())

    def test_component_constants(self):
        self.assertEqual(self.saved['components'], ref.M8['components'])
        self.assertEqual(ref.dataset_check(), self.saved['provenance']['component_source_sha256'])
        self.assertEqual(self.saved['formulation']['R_J_mol_K'], 8.31446261815324)
        self.assertEqual(self.saved['kij'], [[0., 0.], [0., 0.]])

    def test_cp_coefficients_and_integrals(self):
        models = ref.cp_models()
        for i, d in enumerate(ref.CP_DATA):
            for T in (280., 298.15, 300., 350., 400.):
                cp, h, s = eq.ideal_pure(T, d['coefficients'])
                ref.close(models[i](T), cp, 'Cp')
                ref.close(models[i].T_dependent_property_integral(eq.T_REF, T), h, 'h_ig')
                ref.close(models[i].T_dependent_property_integral_over_T(eq.T_REF, T), s, 's_ig')

    def test_cp_validity(self):
        for T in (200., 280., 400., 1000.):
            ref.require_cp_domain(T)
        for T in (199.999, 1000.001, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                ref.require_cp_domain(T)
        with self.assertRaises(ValueError):
            ref.require_cp_domain(300., reference=150.)

    def test_ideal_reference_and_mixing(self):
        for d in ref.CP_DATA:
            _, h, s = eq.ideal_pure(eq.T_REF, d['coefficients'])
            self.assertEqual((h, s), (0., 0.))
        mixed = eq.ideal(eq.T_REF, eq.P_REF, [.5, .5], ref.CP_DATA)
        self.assertAlmostEqual(mixed['s_ig_J_mol_K'], eq.R * math.log(2), places=13)
        pure = eq.ideal(eq.T_REF, eq.P_REF, [1., 0.], ref.CP_DATA)
        self.assertEqual(pure['s_ig_J_mol_K'], 0.)

    def test_ideal_pressure_and_composition(self):
        a = eq.ideal(350., 1e3, [.2, .8], ref.CP_DATA)
        b = eq.ideal(350., 1e6, [.2, .8], ref.CP_DATA)
        self.assertEqual(a['h_ig_J_mol'], b['h_ig_J_mol'])
        self.assertAlmostEqual(b['s_ig_J_mol_K']-a['s_ig_J_mol_K'], -eq.R*math.log(1000), places=12)
        expected = sum(z*eq.ideal_pure(350., d['coefficients'])[1] for z, d in zip([.2, .8], ref.CP_DATA))
        ref.close(a['h_ig_J_mol'], expected, 'h_ig')

    def test_analytic_alpha_and_mixture_derivatives(self):
        for p in self.phases:
            pure, a, da, b = eq.parameters(p['T_K'], p['composition'], ref.COMPONENTS, ref.KIJ)
            for direct, library in zip(pure, p['pure_parameters']):
                ref.close(direct['alpha'], library['alpha'], 'alpha')
                ref.close(direct['dalpha_dT_K_inv'], library['dalpha_dT_K_inv'], 'dalpha_dT')
            ref.close(a, p['a_mix_Pa_m6_mol2'], 'a')
            ref.close(da, p['da_mix_dT_Pa_m6_mol2_K'], 'da_dT')
            ref.close(b, p['b_mix_m3_mol'], 'b')

    def test_residual_enthalpy(self):
        for p in self.phases:
            h, _ = eq.departures(p['T_K'], p['P_Pa_abs'], p['Z'], p['a_mix_Pa_m6_mol2'], p['da_mix_dT_Pa_m6_mol2_K'], p['b_mix_m3_mol'])
            ref.close(h, p['h_res_J_mol'], 'h_res')

    def test_residual_entropy(self):
        for p in self.phases:
            _, s = eq.departures(p['T_K'], p['P_Pa_abs'], p['Z'], p['a_mix_Pa_m6_mol2'], p['da_mix_dT_Pa_m6_mol2_K'], p['b_mix_m3_mol'])
            ref.close(s, p['s_res_J_mol_K'], 's_res')

    def test_total_contributions(self):
        for p in self.phases:
            ref.close(p['h_total_J_mol'], p['h_ig_J_mol']+p['h_res_J_mol'], 'h_total')
            ref.close(p['s_total_J_mol_K'], p['s_ig_J_mol_K']+p['s_res_J_mol_K'], 's_total')

    def test_case_a_stable_liquid(self):
        a = self.saved['cases'][0]
        self.assertEqual(a['case_id'], 'A')
        self.assertEqual(a['classification'], 'L')
        self.assertEqual(list(a['phases']), ['liquid'])
        ref.close(a['phases']['liquid']['Z'], ref.M8['cases'][0]['liquid']['Z'], 'Z')

    def test_case_b_liquid_composition_and_root(self):
        p = self.b['phases']['liquid']
        self.assertEqual(p['composition'], ref.M8['cases'][1]['liquid']['composition'])
        ref.close(p['Z'], ref.M8['cases'][1]['liquid']['Z'], 'Z')
        self.assertLess(p['h_res_J_mol'], -30000.)

    def test_case_b_vapor_composition_and_root(self):
        p = self.b['phases']['vapor']
        self.assertEqual(p['composition'], ref.M8['cases'][1]['vapor']['composition'])
        ref.close(p['Z'], ref.M8['cases'][1]['vapor']['Z'], 'Z')
        self.assertNotEqual(p['Z'], self.b['phases']['liquid']['Z'])

    def test_case_b_overall_h(self):
        b = self.b
        expected = (1-b['beta'])*b['phases']['liquid']['h_total_J_mol']+b['beta']*b['phases']['vapor']['h_total_J_mol']
        ref.close(expected, b['overall_h_J_mol'], 'h_total')
        self.assertEqual(b['beta'], ref.M8['cases'][1]['beta'])

    def test_case_b_overall_s(self):
        b = self.b
        expected = (1-b['beta'])*b['phases']['liquid']['s_total_J_mol_K']+b['beta']*b['phases']['vapor']['s_total_J_mol_K']
        ref.close(expected, b['overall_s_J_mol_K'], 's_total')

    def test_case_c_stable_vapor(self):
        c = self.saved['cases'][2]
        self.assertEqual(c['case_id'], 'C')
        self.assertEqual(c['classification'], 'V')
        self.assertEqual(list(c['phases']), ['vapor'])
        ref.close(c['phases']['vapor']['Z'], ref.M8['cases'][2]['vapor']['Z'], 'Z')

    def test_pure_component_eos(self):
        self.assertEqual(len(self.saved['pure_states']), 12)
        for p in self.saved['pure_states']:
            ref.close(p['h_res_J_mol'], p['pure_EOS_h_res_J_mol'], 'h_res')
            ref.close(p['s_res_J_mol_K'], p['pure_EOS_s_res_J_mol_K'], 's_res')
            self.assertEqual(p['ideal_entropy_terms']['s_ig_mixing_J_mol_K'], 0.)

    def test_ideal_gas_limit(self):
        for i in (0, 4, 8):
            rows = self.saved['low_pressure_states'][i:i+4]
            for key in ('h_res_J_mol', 's_res_J_mol_K'):
                self.assertTrue(all(abs(a[key]) > abs(b[key]) for a, b in zip(rows, rows[1:])))
            self.assertLess(abs(rows[-1]['Z']-1), 1e-6)
            self.assertLess(abs(rows[-1]['h_res_J_mol']), .01)
            self.assertLess(abs(rows[-1]['s_res_J_mol_K']), 1e-4)

    def test_units_and_flows(self):
        self.assertEqual(ref.molar_to_mass(100., 20.), 5000.)
        self.assertEqual(ref.molar_enthalpy_flow(3.6, 100.), 100.)
        self.assertEqual(ref.mass_enthalpy_flow(72., 5000.), 100.)
        for mw in (0., -1., float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                ref.molar_to_mass(1., mw)
        phase_sum = 0.
        for name, p in self.b['phases'].items():
            F = 1000.*(self.b['beta'] if name == 'vapor' else 1-self.b['beta'])
            mass_flow = F*p['mixture_MW_kg_kmol']
            by_mass = ref.mass_enthalpy_flow(mass_flow, p['h_total_J_kg'])
            by_moles = ref.molar_enthalpy_flow(F, p['h_total_J_mol'])
            self.assertAlmostEqual(by_mass, by_moles, delta=1e-8)
            phase_sum += by_mass
        self.assertAlmostEqual(phase_sum, self.b['benchmark_equilibrium_enthalpy_flow_W'], delta=1e-8)

    def test_reference_shifts(self):
        proof = ref.reference_shift_checks(self.saved['cases'])
        self.assertLess(abs(proof['enthalpy_flow_difference_shift_error_W']), 1e-6)
        self.assertGreater(abs(proof['phase_difference_change_under_component_shifts_J_mol']), 1000.)
        # A common entropy shift cancels in phase differences; component-specific ones need not.
        l, v = [self.b['phases'][k]['s_total_J_mol_K'] for k in ('liquid', 'vapor')]
        self.assertAlmostEqual((v+17.)-(l+17.), v-l, places=12)

    def test_consistency_identities(self):
        for p in self.phases:
            self.assertLess(abs(p['consistency']['dHres_dT_minus_T_dSres_dT_J_mol_K']), 2e-5)
            ref.close(p['h_res_J_mol']-p['T_K']*p['s_res_J_mol_K'], p['consistency']['g_res_from_fugacity_J_mol'], 'h_res')

    def test_additional_temperature_and_neighborhoods(self):
        self.assertEqual({c['T_K'] for c in self.saved['cases']}, {280., 300., 350., 400.})
        for c in self.saved['cases']:
            self.assertEqual(len(c['classification_neighborhood']), 9)
            self.assertTrue(all(n['phase'] == c['classification'] for n in c['classification_neighborhood']))

    def test_corruption_rejected(self):
        for path, value in [(('cases', 1, 'phases', 'liquid', 'h_total_J_mol'), 123.),
                            (('components', 0, 'MW_kg_kmol'), 16.),
                            (('cp', 'components', 0, 'coefficients', 0), 4.),
                            (('cases', 0, 'phases', 'liquid', 's_total_J_mol_K'), float('nan'))]:
            wrong = copy.deepcopy(self.saved)
            target = wrong
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(AssertionError):
                ref.compare(wrong, self.fresh)


if __name__ == '__main__':
    unittest.main()
