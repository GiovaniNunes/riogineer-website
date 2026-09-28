import copy
import unittest
from unittest.mock import patch

from riogineer_engine.core import ROOT, Invalid, loads, build_flowsheet, calculate, validate_requirements, validate_flowsheet, semantic_hash
from riogineer_engine.network import validate, COMPONENT_TOLERANCE
from riogineer_engine.network_models import MODELS, TEMPERATURE_TOLERANCE_K, PRESSURE_TOLERANCE_PA


def requirements():
    return loads((ROOT / 'contracts/examples/milestone-4-requirements.json').read_text())


def mixing_case():
    r = requirements()
    r['equipment'] = [r['equipment'][2]]
    r['feeds'] = [dict(id='SOURCE_A', state=copy.deepcopy(r['feeds'][0]['state'])),
                  dict(id='SOURCE_B', state=copy.deepcopy(r['feeds'][0]['state']))]
    r['sinks'] = [dict(id='OIL_SINK')]
    edges = [('A', 'SOURCE_A', 'outlet', 'MIX_1', 'inlet_a'),
             ('B', 'SOURCE_B', 'outlet', 'MIX_1', 'inlet_b'),
             ('OUT', 'MIX_1', 'outlet', 'OIL_SINK', 'inlet')]
    r['streams'] = [dict(id=s, service='oil') for s, *_ in edges]
    r['connections'] = [dict(id='C_' + s, stream_id=s, source=dict(owner_id=a, port_id=ap),
                             target=dict(owner_id=b, port_id=bp)) for s, a, ap, b, bp in edges]
    return r


class NetworkTests(unittest.TestCase):
    def test_version_dispatch_preserves_invalid_document_errors(self):
        for operation in [validate_requirements, build_flowsheet, validate_flowsheet, calculate]:
            for value in [None, [], 'invalid', 42]:
                with self.subTest(operation=operation.__name__, value=value):
                    with self.assertRaises(Invalid): operation(value)

    def test_reference_topology_and_numbers(self):
        r = requirements()
        self.assertEqual(validate_requirements(r)['requirements'], r)
        f = build_flowsheet(r)
        self.assertEqual({u['id']: u['type'] for u in f['equipment']},
                         {'SEP_1': 'three_phase_separator', 'SPLIT_1': 'splitter', 'MIX_1': 'mixer'})
        self.assertEqual({s['id']: s['engineering_number'] for s in f['streams']},
                         {'FEED': 1, 'GAS': 2, 'OIL': 3, 'WATER': 4, 'OIL_A': 5, 'OIL_B': 6, 'OIL_PRODUCT': 7})
        self.assertEqual(validate(f), ['SEP_1', 'SPLIT_1', 'MIX_1'])
        self.assertEqual(len(f['connections']), 7)
        validate_flowsheet(f)

    def test_reference_component_splits_merge_and_balances(self):
        result = calculate(build_flowsheet(requirements()))
        streams = result['streams']
        expected = {'FEED': (22000, 77000, 11000), 'GAS': (22000, 0, 0), 'WATER': (0, 0, 10450),
                    'OIL': (0, 77000, 550), 'OIL_A': (0, 46200, 330), 'OIL_B': (0, 30800, 220), 'OIL_PRODUCT': (0, 77000, 550)}
        for sid, values in expected.items():
            state = streams[sid]
            self.assertEqual(state['component_mass_flow_kg_h'], dict(zip(['methane', 'n_hexane', 'water'], values)))
            self.assertEqual(state['mass_flow_kg_h'], sum(values))
            self.assertEqual(state['component_mass_fractions'], {c: v / sum(values) for c, v in state['component_mass_flow_kg_h'].items()})
            self.assertEqual(state['temperature_K'], 313.15)
            self.assertEqual(state['pressure_Pa_abs'], 2000000)
            for prop in (state['properties'][key] for key in ('density', 'gas_volumetric_flow', 'oil_volumetric_flow', 'water_volumetric_flow')):
                self.assertIsNone(prop['value']); self.assertEqual(prop['status'], 'not_calculated')
        for sid in ['OIL_A', 'OIL_B', 'OIL_PRODUCT']:
            self.assertEqual(streams[sid]['component_mass_fractions'], streams['OIL']['component_mass_fractions'])
        for balance in [result['balances']['mass']] + [e['mass_balance'] for e in result['equipment']]:
            self.assertEqual(balance['status'], 'passed')
            self.assertEqual(balance['total_residual_kg_h'], 0)
            self.assertEqual(list(balance['component_residual_kg_h'].values()), [0, 0, 0])
            self.assertEqual(balance['component_tolerance_kg_h'], COMPONENT_TOLERANCE)
        self.assertEqual(result['balances']['energy']['residual_W'], 0)
        for e in result['equipment']:
            self.assertEqual(e['energy_residual_W'], 0); self.assertEqual(e['duty_W'], 0); self.assertEqual(e['work_W'], 0)

    def test_original_separator_and_nonzero_duty_unchanged(self):
        for temperature in [313.15, 333.15]:
            old = loads((ROOT / 'contracts/examples/requirements.json').read_text())
            r = requirements()
            for data in [old, r]: data['equipment'][0]['parameters']['separator']['temperature_K'] = temperature
            a = calculate(build_flowsheet(old)); b = calculate(build_flowsheet(r))
            for sid in ['FEED', 'GAS', 'OIL', 'WATER']:
                self.assertEqual(a['streams'][sid], b['streams'][sid])
            self.assertEqual(a['balances']['mass'], b['balances']['mass'])
            for key in ['residual_W', 'duty_W', 'reference_temperature_K']:
                self.assertEqual(a['balances']['energy'][key], b['balances']['energy'][key])
            self.assertEqual(b['streams']['OIL']['enthalpy_flow_W'], b['streams']['OIL_PRODUCT']['enthalpy_flow_W'])

    def test_order_layout_identity_and_repeated_calculation(self):
        r = requirements(); original = copy.deepcopy(r)
        f = build_flowsheet(r); before = copy.deepcopy(f); objects = list(f['streams'])
        a = calculate(f); b = calculate(f)
        self.assertEqual(a['streams'], b['streams']); self.assertEqual(f, before); self.assertEqual(r, original)
        for old, current in zip(objects, f['streams']): self.assertIs(old, current)
        for key in ['equipment', 'streams', 'connections', 'boundaries']: f[key].reverse()
        f['presentation']['layout'] = 'compact'
        self.assertEqual(semantic_hash(f), semantic_hash(before))
        self.assertEqual(calculate(f)['streams'], a['streams'])
        for key in ['equipment', 'streams', 'connections', 'feeds', 'sinks']: r[key].reverse()
        rebuilt = build_flowsheet(r)
        self.assertEqual({s['id']: s['engineering_number'] for s in rebuilt['streams']}, {s['id']: s['engineering_number'] for s in before['streams']})
        for stream in f['streams']: stream['engineering_number'] += 100
        numbers = copy.deepcopy(f['streams'])
        calculate(f)
        self.assertEqual(f['streams'], numbers)

    def test_schedule_uses_dependencies_not_tags_or_array_order(self):
        r = requirements(); mapping = {'SEP_1': 'Z', 'SPLIT_1': 'B', 'MIX_1': 'A'}
        for u in r['equipment']: u['id'] = mapping[u['id']]
        for c in r['connections']:
            for side in ['source', 'target']: c[side]['owner_id'] = mapping.get(c[side]['owner_id'], c[side]['owner_id'])
        r['equipment'].reverse()
        self.assertEqual(calculate(build_flowsheet(r))['execution']['equipment_order'], ['Z', 'B', 'A'])
        # A second graph with no separator demonstrates a generic registry/scheduler.
        self.assertEqual(calculate(build_flowsheet(mixing_case()))['execution']['equipment_order'], ['MIX_1'])

    def test_stream_identity_is_independent_of_service_names(self):
        r = requirements()
        mapping = {s['id']: 'S_' + str(i) for i, s in enumerate(r['streams'])}
        for stream in r['streams']:
            stream['id'] = mapping[stream['id']]
            stream['service'] = 'same_service'
        for c in r['connections']: c['stream_id'] = mapping[c['stream_id']]
        f = build_flowsheet(r)
        before = copy.deepcopy(f)
        result = calculate(f)
        self.assertEqual(set(result['streams']), set(mapping.values()))
        self.assertEqual(result['streams'][mapping['OIL_A']]['mass_flow_kg_h'], 46530)
        self.assertEqual(result['streams'][mapping['OIL_PRODUCT']]['mass_flow_kg_h'], 77550)
        self.assertEqual(f, before)

    def test_independent_ready_units_have_canonical_tie_breaking(self):
        r = mixing_case()
        r['equipment'].append(dict(r['equipment'][0], id='A_MIX'))
        r['sinks'].append(dict(id='OTHER_SINK'))
        for uid in ['SOURCE_C', 'SOURCE_D']:
            r['feeds'].append(dict(id=uid, state=copy.deepcopy(r['feeds'][0]['state'])))
        edges = [('C', 'SOURCE_C', 'outlet', 'A_MIX', 'inlet_a'),
                 ('D', 'SOURCE_D', 'outlet', 'A_MIX', 'inlet_b'),
                 ('OTHER', 'A_MIX', 'outlet', 'OTHER_SINK', 'inlet')]
        r['streams'] += [dict(id=s, service='oil') for s, *_ in edges]
        r['connections'] += [dict(id='C_' + s, stream_id=s, source=dict(owner_id=a, port_id=ap), target=dict(owner_id=b, port_id=bp)) for s, a, ap, b, bp in edges]
        expected = calculate(build_flowsheet(r))
        for key in ['equipment', 'feeds', 'sinks', 'connections', 'streams']: r[key].reverse()
        actual = calculate(build_flowsheet(r))
        self.assertEqual(actual['execution']['equipment_order'], ['A_MIX', 'MIX_1'])
        self.assertEqual(actual['streams'], expected['streams'])
        self.assertEqual(actual['balances'], expected['balances'])

    def test_bad_splits_rejected(self):
        for values in [(-.1, 1.1), (.5, .4), (.6, .5), (float('nan'), .4), (float('inf'), .4), (True, 0), (0, 0)]:
            with self.subTest(values=values):
                r = requirements(); r['equipment'][1]['parameters']['fractions'] = dict(zip(['outlet_a', 'outlet_b'], values))
                with self.assertRaises(Invalid): build_flowsheet(r)
        r = requirements(); r['equipment'][1]['parameters']['fractions'].pop('outlet_b')
        with self.assertRaises(Invalid): validate_requirements(r)

    def test_zero_branch_is_distinct_from_unavailable(self):
        r = requirements(); r['equipment'][1]['parameters']['fractions'].update(outlet_a=0, outlet_b=1)
        out = calculate(build_flowsheet(r))['streams']
        self.assertEqual(out['OIL_A']['mass_flow_kg_h'], 0)
        self.assertIsNone(out['OIL_A']['component_mass_fractions'])
        self.assertIsNone(out['OIL_A']['properties']['density']['value'])
        self.assertEqual(out['OIL_PRODUCT'], out['OIL'])

    def test_mixer_equal_conditions_and_unsupported_differences(self):
        r = mixing_case(); out = calculate(build_flowsheet(r))['streams']['OUT']
        self.assertEqual(out['mass_flow_kg_h'], 220000)
        self.assertEqual(out['temperature_K'], 313.15); self.assertEqual(out['pressure_Pa_abs'], 2000000)
        for field, tolerance in [('temperature_K', TEMPERATURE_TOLERANCE_K), ('pressure_Pa_abs', PRESSURE_TOLERANCE_PA)]:
            near = copy.deepcopy(r); near['feeds'][1]['state'][field] += tolerance / 2
            self.assertEqual(calculate(build_flowsheet(near))['streams']['OUT'][field], out[field])
            bad = copy.deepcopy(r); bad['feeds'][1]['state'][field] += 1
            with self.assertRaisesRegex(Invalid, 'Unsupported mixer inlet'): calculate(build_flowsheet(bad))

    def test_unknown_owners_ports_directions_and_occupied_ports(self):
        cases = [('owner_id', 'UNKNOWN', 'source', 'Unknown equipment'),
                 ('port_id', 'unknown', 'source', 'Unknown port'),
                 ('port_id', 'gas', 'target', 'direction')]
        for key, value, side, message in cases:
            f = build_flowsheet(requirements()); f['connections'][0][side][key] = value
            with self.assertRaisesRegex(Invalid, message): validate_flowsheet(f)
        f = build_flowsheet(requirements()); f['connections'][5]['target'] = copy.deepcopy(f['connections'][4]['target'])
        with self.assertRaisesRegex(Invalid, 'Duplicate occupation'): validate_flowsheet(f)
        f = build_flowsheet(requirements()); f['streams'].pop(); f['connections'].pop()
        with self.assertRaisesRegex(Invalid, 'Missing required'): validate_flowsheet(f)

    def test_duplicate_ids_numbers_and_missing_port_rejected(self):
        for collection in ['equipment', 'streams', 'connections']:
            f = build_flowsheet(requirements()); f[collection][1]['id'] = f[collection][0]['id']
            with self.assertRaises(Invalid): validate_flowsheet(f)
        f = build_flowsheet(requirements()); f['streams'][1]['engineering_number'] = 1
        with self.assertRaisesRegex(Invalid, 'numbers must be unique'): validate_flowsheet(f)
        f = build_flowsheet(requirements()); f['equipment'][1]['ports'].pop()
        with self.assertRaisesRegex(Invalid, 'required ports'): validate_flowsheet(f)

    def test_cycle_rejected_without_iteration(self):
        r = requirements()
        a, b = r['connections'][0], r['connections'][-1]
        a['source'], b['source'] = b['source'], a['source']
        with self.assertRaisesRegex(Invalid, 'Cycle detected.*recycle networks are not supported'): build_flowsheet(r)

    def test_component_and_caloric_basis_validation(self):
        r = requirements(); r['caloric_model']['cp_J_kg_K'].pop('water')
        with self.assertRaisesRegex(Invalid, 'component keys'): build_flowsheet(r)
        r = requirements(); r['equipment'][0]['parameters']['caloric_model']['reference_temperature_K'] = 280
        with self.assertRaisesRegex(Invalid, 'share the network caloric basis'): build_flowsheet(r)
        r = requirements(); r['equipment'][0]['parameters']['recovery_fractions']['water']['oil'] = .2
        with self.assertRaisesRegex(Invalid, 'recoveries must sum'): build_flowsheet(r)

    def test_invalid_calculated_balance_cannot_be_published(self):
        original = MODELS['splitter']['execute']
        def corrupt(*args):
            outgoing, duty = original(*args)
            outgoing['outlet_a']['component_mass_flow_kg_h']['water'] += 1
            return outgoing, duty
        with patch.dict(MODELS['splitter'], execute=corrupt):
            with self.assertRaisesRegex(Invalid, 'balance failed'): calculate(build_flowsheet(requirements()))

    def test_engineering_changes_invalidate_fingerprint(self):
        f = build_flowsheet(requirements()); old = semantic_hash(f)
        f['equipment'][1]['operating_parameters']['fractions'].update(outlet_a=.5, outlet_b=.5)
        self.assertNotEqual(semantic_hash(f), old)
        validate_flowsheet(f)
        self.assertEqual(calculate(f)['streams']['OIL_A']['mass_flow_kg_h'], 38775)

    def test_pressure_increase_and_unsupported_equipment_blocked(self):
        r = requirements(); r['equipment'][0]['parameters']['separator']['pressure_Pa_abs'] = 3000000
        with self.assertRaisesRegex(Invalid, 'cannot increase pressure'): calculate(build_flowsheet(r))
        r = requirements(); r['equipment'][1]['type'] = 'compressor'
        with self.assertRaises(Invalid): build_flowsheet(r)


if __name__ == '__main__': unittest.main()
