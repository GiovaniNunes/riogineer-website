"""Independent Pre-M12 acceptance, including decimal energy arithmetic."""
from decimal import Decimal, localcontext
import inspect
import json
import sys
import unittest

from reference import ARTIFACT, build, specifications
from solver import mode_b


class EnergyQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads(ARTIFACT.read_text())
        cls.actual = build()
        cls.cases = {c['specification']['case_id']: c for c in cls.actual['cases']}

    def check_case(self, index):
        actual = self.actual['cases'][index]
        frozen = self.frozen['cases'][index]
        self.assertEqual(actual, frozen)
        a, b, spec = actual['mode_A'], actual['mode_B'], actual['specification']
        self.assertEqual(a['status'], 'success')
        self.assertEqual(b['status'], 'success')
        for result in (a, b):
            self.assertEqual(result['F_in_mol_s'], result['F_out_mol_s'])
            self.assertEqual(result['z_in'], result['z_out'])
            self.assertEqual(result['inlet']['z'], result['outlet']['z'])
        # Different arithmetic implementation: high precision from exact float inputs.
        with localcontext() as context:
            context.prec = 60
            flow = Decimal.from_float(spec['F'])
            hin = Decimal.from_float(a['inlet']['H_eq_J_mol'])
            hout = Decimal.from_float(a['outlet']['H_eq_J_mol'])
            delta = hout - hin
            q = flow * delta
            error = abs(q - Decimal.from_float(a['Q_W']))
            self.assertLessEqual(float(error), actual['forward_energy_allowance_W'])
            self.assertLessEqual(abs(float(delta) - a['delta_H_J_mol']),
                                 actual['forward_energy_allowance_W'] / spec['F'])
            self.assertEqual(q.compare(Decimal(0)), spec['expected_sign'])
        self.assertLessEqual(abs(b['R_H_J_mol']), 1e-6)
        self.assertLessEqual(abs(b['R_Q_W']), actual['inverse_energy_allowance_W'])
        self.assertLessEqual(actual['absolute_errors']['H_target_reconstruction_J_mol'],
                             actual['forward_energy_allowance_W'] / spec['F'])
        self.assertLessEqual(abs(b['outlet']['T_K'] - spec['Tout']), 1e-7)

    def test_byte_exact_frozen_reproduction(self):
        self.assertEqual(json.dumps(self.actual, indent=2, allow_nan=False) + '\n',
                         ARTIFACT.read_text())

    def test_zero_duty(self):
        case = self.cases['ZERO_DUTY']
        self.assertEqual(case['mode_A']['Q_W'], 0.)
        self.assertEqual(case['mode_A']['inlet'], case['mode_A']['outlet'])
        self.assertLessEqual(case['absolute_errors']['T'], 1e-7)

    def test_flow_scaling(self):
        first = self.cases['VAPOR_HEATING']['mode_A']
        second = self.cases['VAPOR_HEATING_DOUBLE_FLOW']['mode_A']
        for key in ('inlet', 'outlet', 'delta_H_J_mol'):
            self.assertEqual(first[key], second[key])
        self.assertEqual(2 * first['Q_W'], second['Q_W'])

    def test_reverse_heating_cooling(self):
        for heating, cooling in [('VAPOR_HEATING', 'VAPOR_COOLING'),
                                  ('LIQUID_HEATING', 'LIQUID_COOLING'),
                                  ('LIQUID_TO_TWO_PHASE', 'TWO_PHASE_TO_LIQUID'),
                                  ('TWO_PHASE_TO_VAPOR', 'VAPOR_TO_TWO_PHASE')]:
            a = self.cases[heating]['mode_A']
            b = self.cases[cooling]['mode_A']
            self.assertEqual(a['Q_W'], -b['Q_W'])
            self.assertGreater(a['Q_W'], 0.)
            self.assertLess(b['Q_W'], 0.)

    def test_all_phase_transitions(self):
        pairs = {(c['mode_A']['inlet']['classification'],
                  c['mode_A']['outlet']['classification'])
                 for c in self.actual['cases']}
        required = {('single_liquid', 'vapor_liquid'),
                    ('vapor_liquid', 'single_vapor'),
                    ('single_vapor', 'vapor_liquid'),
                    ('vapor_liquid', 'single_liquid'),
                    ('vapor_liquid', 'vapor_liquid')}
        self.assertTrue(required.issubset(pairs))

    def test_specified_pressure_change(self):
        c = self.cases['SPECIFIED_OUTLET_PRESSURE']
        self.assertEqual(c['mode_A']['inlet']['P_Pa_abs'], 6e6)
        self.assertEqual(c['mode_B']['outlet']['P_Pa_abs'], 3e6)

    def test_inverse_has_no_forward_temperature_input(self):
        self.assertNotIn('Tout', inspect.signature(mode_b).parameters)
        self.assertNotIn('riogineer_engine', sys.modules)
        self.assertFalse(any(k.startswith('riogineer_engine.') for k in sys.modules))


for index, specification in enumerate(specifications()):
    def positive(self, index=index):
        self.check_case(index)
    setattr(EnergyQualification, 'test_positive_' + specification['case_id'], positive)

# Fixed frozen negative inventory: failures cannot quietly disappear from regeneration.
for index, negative in enumerate(json.loads(ARTIFACT.read_text())['negative_cases']):
    def rejected(self, index=index):
        actual = self.actual['negative_cases'][index]
        self.assertEqual(actual, self.frozen['negative_cases'][index])
        self.assertEqual(actual['result']['status'], actual['specification']['expected_status'])
        self.assertNotIn('outlet', actual['result'])
    setattr(EnergyQualification, 'test_negative_' + negative['specification']['case_id'], rejected)


if __name__ == '__main__':
    unittest.main()
