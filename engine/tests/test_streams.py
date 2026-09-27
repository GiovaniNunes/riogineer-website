import copy
import unittest

from riogineer_engine.core import ROOT, loads, build_flowsheet, calculate, validate_flowsheet, semantic_hash, Invalid
from riogineer_engine.streams import number_streams


def reference():
    return build_flowsheet(loads((ROOT / 'contracts/examples/requirements.json').read_text()))


class StreamIdentityTests(unittest.TestCase):
    def test_reference_numbers_and_layout_independence(self):
        f = reference()
        identity = {s['id']: s['engineering_number'] for s in f['streams']}
        self.assertEqual(identity, {'FEED': 1, 'GAS': 2, 'OIL': 3, 'WATER': 4})
        fingerprint = semantic_hash(f)
        f['presentation']['layout'] = 'compact'
        f['streams'].reverse(); f['connections'].reverse()
        number_streams(f['streams'], f['connections'], [f['boundaries'][0]['id']])
        self.assertEqual({s['id']: s['engineering_number'] for s in f['streams']}, identity)
        self.assertEqual(semantic_hash(f), fingerprint)
        for stream in f['streams']: del stream['engineering_number']
        number_streams(f['streams'], f['connections'], [f['boundaries'][0]['id']])
        self.assertEqual({s['id']: s['engineering_number'] for s in f['streams']}, identity)

    def test_calculation_preserves_original_numbered_streams_and_regeneration(self):
        f = reference()
        streams = f['streams']
        original_objects = list(streams)
        before = copy.deepcopy(f)
        for _ in range(2):
            result = calculate(f)
            self.assertIs(f['streams'], streams)
            self.assertEqual(f, before)
            for old, current in zip(original_objects, f['streams']):
                self.assertIs(current, old)
                self.assertEqual(result['streams'][current['id']]['temperature_K'], 313.15)
                self.assertEqual(result['streams'][current['id']]['pressure_Pa_abs'], 2000000)
        self.assertEqual(reference()['streams'], before['streams'])
        # Existing nonconsecutive numbers must survive too; calculation cannot assign numbers.
        for stream in streams: stream['engineering_number'] += 20
        assigned = copy.deepcopy(streams)
        calculate(f)
        self.assertEqual(streams, assigned)

    def test_duplicate_missing_invalid_numbers_rejected(self):
        for number in [1, 0, -1, 1.5, True, 9007199254740992]:
            with self.subTest(number=number):
                f = reference(); f['streams'][1]['engineering_number'] = number
                with self.assertRaises(Invalid): validate_flowsheet(f)
        f = reference(); del f['streams'][0]['engineering_number']
        with self.assertRaises(Invalid): validate_flowsheet(f)

    def test_numbering_helper_is_generic_and_preserves_assigned_numbers(self):
        # A data-structure test only: this does not enable another process model.
        streams = [{'id': n} for n in ['internal_b', 'out', 'in', 'internal_a']]
        edges = [('in', 'source', 'out', 'unit_a'), ('internal_a', 'unit_a', 'a', 'unit_b'),
                 ('internal_b', 'unit_a', 'b', 'unit_b'), ('out', 'unit_b', 'out', 'sink')]
        connections = [{'stream_id': s, 'source': {'owner_id': a, 'port_id': p},
                        'target': {'owner_id': b, 'port_id': 'in'}} for s, a, p, b in edges]
        number_streams(streams, list(reversed(connections)), ['source'])
        self.assertEqual({s['id']: s['engineering_number'] for s in streams}, {'in': 1, 'internal_a': 2, 'internal_b': 3, 'out': 4})
        streams.append({'id': 'later'})
        connections.append({'stream_id': 'later', 'source': {'owner_id': 'unit_a', 'port_id': '0'}, 'target': {'owner_id': 'sink2', 'port_id': 'in'}})
        number_streams(streams, connections, ['source'])
        self.assertEqual(streams[-1]['engineering_number'], 5)

    def test_result_association_uses_ids_and_properties_are_explicitly_unavailable(self):
        f = reference()
        mapping = {s['id']: 'STREAM_' + str(s['engineering_number']) for s in f['streams']}
        for s in f['streams']: s['id'] = mapping[s['id']]
        for c in f['connections']: c['stream_id'] = mapping[c['stream_id']]
        result = calculate(f)
        self.assertEqual(set(result['streams']), set(mapping.values()))
        self.assertEqual([result['streams'][mapping[s]]['mass_flow_kg_h'] for s in ['FEED', 'GAS', 'OIL', 'WATER']], [110000, 22000, 77550, 10450])
        for state in result['streams'].values():
            for quantity in state['properties'].values():
                self.assertIsNone(quantity['value'])
                self.assertEqual(quantity['status'], 'not_calculated')
                self.assertTrue(quantity['unit'])
        self.assertEqual(result['streams'][mapping['GAS']]['component_mass_flow_kg_h']['water'], 0)
        self.assertEqual(result['balances']['energy']['duty_W'], 0)

    def test_legacy_flowsheets_remain_valid_and_do_not_acquire_frontend_numbers(self):
        f = reference(); f['schema_version'] = '1.0'
        for s in f['streams']: del s['engineering_number']
        before = copy.deepcopy(f)
        validate_flowsheet(f)
        self.assertEqual(calculate(f)['streams']['FEED']['mass_flow_kg_h'], 110000)
        self.assertEqual(f, before)
