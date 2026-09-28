import copy
import unittest
from unittest.mock import patch
from riogineer_engine.core import ROOT, loads, build_flowsheet, calculate, validate_requirements, Invalid, reference
from riogineer_engine.network_models import MODELS


def requirements():
    return loads((ROOT / 'contracts/examples/milestone-5-requirements.json').read_text())


class SequentialTests(unittest.TestCase):
    def test_reference_conservation_energy_and_properties(self):
        r = requirements()
        f = build_flowsheet(r)
        before = copy.deepcopy(f)
        o = calculate(f)
        self.assertEqual(f, before)
        self.assertEqual(o['execution']['equipment_order'], ['SEP_1', 'HEATER_1', 'SEP_2'])
        expected = {'FEED': (22000, 77000, 11000), 'GAS_1': (22000, 0, 0),
                    'OIL_1': (0, 77000, 550), 'WATER_1': (0, 0, 10450),
                    'HEATED_OIL': (0, 77000, 550), 'GAS_2': (0, 3850, 0),
                    'OIL_PRODUCT': (0, 73150, 55), 'WATER_2': (0, 0, 495)}
        for sid, values in expected.items():
            state = o['streams'][sid]
            self.assertEqual(state['component_mass_flow_kg_h'], dict(zip(r['components'], values)))
            self.assertEqual(state['mass_flow_kg_h'], sum(values))
            self.assertEqual(state['pressure_Pa_abs'], 2000000)
            self.assertEqual(state['temperature_K'], 313.15 if sid in list(expected)[:4] else 333.15)
            for c, rate in state['component_mass_flow_kg_h'].items():
                self.assertEqual(state['component_mass_fractions'][c], rate / sum(values))
            for prop in state['properties'].values():
                self.assertIsNone(prop['value'])
                self.assertEqual(prop['status'], 'not_calculated')
        duty = (77000 * 2200 + 550 * 4180) * 20 / 3600
        self.assertAlmostEqual(o['equipment'][1]['duty_W'], duty, places=6)
        self.assertAlmostEqual(o['streams']['HEATED_OIL']['enthalpy_flow_W'] - o['streams']['OIL_1']['enthalpy_flow_W'], duty, places=6)
        self.assertEqual(o['equipment'][0]['duty_W'], 0)
        self.assertLessEqual(abs(o['equipment'][2]['duty_W']), 1e-6)
        for e in o['equipment']:
            self.assertEqual(e['mass_balance']['total_residual_kg_h'], 0)
            self.assertEqual(set(e['mass_balance']['component_residual_kg_h'].values()), {0})
            self.assertLessEqual(abs(e['energy_residual_W']), 1e-6)
        self.assertEqual(o['balances']['mass']['total_residual_kg_h'], 0)
        self.assertEqual(set(o['balances']['mass']['component_residual_kg_h'].values()), {0})
        self.assertAlmostEqual(o['balances']['energy']['duty_W'], duty, places=6)
        self.assertLessEqual(abs(o['balances']['energy']['residual_W']), 1e-6)
        self.assertEqual(o['balances']['energy']['positive_duty'], 'heat_into_network')

    def test_actual_calculated_state_is_consumed_downstream(self):
        r = requirements()
        r['equipment'][1]['parameters']['outlet_temperature_K'] = 343.15
        r['feeds'][0]['state']['component_mass_flow_kg_h']['n_hexane'] = 80000
        original = reference.evaluate
        seen = []
        def spy(feed, *args):
            seen.append(copy.deepcopy(feed))
            return original(feed, *args)
        with patch.object(reference, 'evaluate', side_effect=spy):
            o = calculate(build_flowsheet(r))
        self.assertEqual(seen[1]['temperature_K'], 343.15)
        self.assertEqual(seen[1]['component_mass_flow_kg_h']['n_hexane'], 80000)
        for key, value in seen[1].items():
            self.assertEqual(value, o['streams']['HEATED_OIL'][key])
        self.assertEqual(o['streams']['GAS_2']['component_mass_flow_kg_h']['n_hexane'], 4000)
        self.assertAlmostEqual(o['equipment'][2]['duty_W'], -(80000 * 2200 + 550 * 4180) * 10 / 3600, places=6)

    def test_zero_temperature_change_has_calculated_zero_duty(self):
        r = requirements()
        r['equipment'][1]['parameters']['outlet_temperature_K'] = 313.15
        o = calculate(build_flowsheet(r))
        self.assertEqual(o['equipment'][1]['duty_W'], 0)
        self.assertEqual(o['streams']['OIL_1'], o['streams']['HEATED_OIL'])

    def test_heater_invalid_inputs(self):
        def temperature(r, value): r['equipment'][1]['parameters']['outlet_temperature_K'] = value
        changes = [lambda r: r['equipment'][1]['parameters'].pop('outlet_temperature_K'),
                   lambda r: r['equipment'][1]['parameters'].pop('caloric_model'),
                   lambda r: r.pop('caloric_model'),
                   lambda r: r['caloric_model']['cp_J_kg_K'].pop('water'),
                   lambda r: r['equipment'][1]['parameters']['caloric_model']['cp_J_kg_K'].update(water=1),
                   lambda r: r['connections'][4]['source'].update(port_id='invalid'),
                   lambda r: r['connections'][4]['target'].update(port_id='gas'),
                   lambda r: r['equipment'][2]['parameters']['recovery_fractions']['water'].update(oil=.2)]
        for value in [float('nan'), float('inf'), -1, 0]:
            changes.append(lambda r, v=value: temperature(r, v))
            changes.append(lambda r, v=value: r['caloric_model']['cp_J_kg_K'].update(water=v))
        for change in changes:
            with self.subTest(change=change):
                r = requirements(); change(r)
                with self.assertRaises(Invalid): validate_requirements(r)

    def test_ports_cycles_and_independent_states_remain_blocked(self):
        for mutate in [lambda f: f['equipment'][1]['ports'].pop(),
                       lambda f: f['connections'][4]['source'].update(owner_id='unknown'),
                       lambda f: f['streams'][4].update(specified_state=copy.deepcopy(f['streams'][0]['specified_state']))]:
            f = build_flowsheet(requirements()); mutate(f)
            with self.assertRaises(Invalid): calculate(f)
        r = requirements()
        # Swap destinations: source directly to sink, downstream oil back to SEP_1.
        r['connections'][0]['target'], r['connections'][6]['target'] = r['connections'][6]['target'], r['connections'][0]['target']
        with self.assertRaisesRegex(Invalid, 'Cycle'): build_flowsheet(r)

    def test_dependency_order_identity_and_regeneration(self):
        r = requirements(); f = build_flowsheet(r)
        numbers = {s['id']: s['engineering_number'] for s in f['streams']}
        self.assertEqual(numbers, dict(zip(['FEED','GAS_1','OIL_1','WATER_1','HEATED_OIL','GAS_2','OIL_PRODUCT','WATER_2'], range(1,9))))
        for key in ['equipment', 'streams', 'connections', 'sinks']: r[key].reverse()
        self.assertEqual({s['id']: s['engineering_number'] for s in build_flowsheet(r)['streams']}, numbers)
        renamed = {'SEP_1': 'Z_UPSTREAM', 'HEATER_1': 'M_HEATER', 'SEP_2': 'A_DOWNSTREAM'}
        for e in r['equipment']: e['id'] = renamed[e['id']]
        for c in r['connections']:
            for side in ['source','target']: c[side]['owner_id'] = renamed.get(c[side]['owner_id'], c[side]['owner_id'])
        self.assertEqual(calculate(build_flowsheet(r))['execution']['equipment_order'], ['Z_UPSTREAM','M_HEATER','A_DOWNSTREAM'])
        before = copy.deepcopy(f['streams'])
        for _ in range(2):
            f['presentation']['layout'] = 'compact'
            calculate(f)
            self.assertEqual(f['streams'], before)

    def test_bad_energy_adapter_cannot_publish(self):
        original = MODELS['heater']['execute']
        def bad(*args):
            outgoing, duty = original(*args)
            return outgoing, duty + 1
        with patch.dict(MODELS['heater'], execute=bad):
            with self.assertRaisesRegex(Invalid, 'energy'): calculate(build_flowsheet(requirements()))

    def test_cooling_is_not_a_heater_operating_mode(self):
        r = requirements()
        r['equipment'][1]['parameters']['outlet_temperature_K'] = 300
        with self.assertRaisesRegex(Invalid, 'cooling is not supported'): calculate(build_flowsheet(r))

    def test_old_contracts_do_not_accept_heater(self):
        r = requirements(); r['schema_version'] = '1.1'
        with self.assertRaises(Invalid): build_flowsheet(r)
        f = build_flowsheet(requirements()); f['schema_version'] = '1.2'
        with self.assertRaises(Invalid): calculate(f)
