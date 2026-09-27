import copy
import hashlib
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from riogineer_engine.core import (ROOT, FIXTURE, Invalid, loads, validate_schema,
    validate_requirements, build_flowsheet, validate_flowsheet, calculate, semantic_hash)
from riogineer_engine.server import Handler


def requirements():
    return loads((ROOT / 'contracts/examples/requirements.json').read_text())


class EngineeringTests(unittest.TestCase):
    def test_reference_snapshots_are_byte_identical_to_manifest(self):
        for item in loads((FIXTURE / 'manifest.json').read_text())['files']:
            self.assertEqual(hashlib.sha256((FIXTURE / item['file']).read_bytes()).hexdigest(), item['sha256'])

    def test_all_stream_quantities_match_saved_bia_results(self):
        expected = loads((FIXTURE / 'separator_results.json').read_text())
        actual = calculate(build_flowsheet(requirements()))
        for name, stream in expected['streams'].items():
            for key, value in stream.items():
                if isinstance(value, dict):
                    for component, quantity in value.items():
                        self.assertAlmostEqual(actual['streams'][name][key][component], quantity, delta=1e-8)
                else:
                    self.assertAlmostEqual(actual['streams'][name][key], value, delta=1e-8)
        self.assertEqual(actual['balances']['mass']['component_residual_kg_h'], expected['component_mass_residual_kg_h'])
        self.assertAlmostEqual(actual['balances']['energy']['duty_W'], expected['separator_duty_W'], delta=1e-6)
        self.assertAlmostEqual(actual['balances']['energy']['residual_W'], expected['energy_residual_W'], delta=1e-6)

    def test_temperature_case_from_existing_teaching_reference(self):
        r = requirements(); r['equipment'][0]['parameters']['separator']['temperature_K'] = 333.15
        actual = calculate(build_flowsheet(r))
        self.assertAlmostEqual(actual['balances']['energy']['duty_W'], 1465444.444444444, delta=1e-6)
        self.assertEqual(actual['streams']['OIL']['mass_flow_kg_h'], 77550)

    def test_recovery_case_from_existing_teaching_reference(self):
        r = requirements(); r['equipment'][0]['parameters']['recovery_fractions']['water'].update(oil=.1, water=.9)
        actual = calculate(build_flowsheet(r))
        self.assertEqual(actual['streams']['OIL']['mass_flow_kg_h'], 78100)
        self.assertEqual(actual['streams']['WATER']['mass_flow_kg_h'], 9900)

    def test_absent_outlet_has_null_composition(self):
        r = requirements(); r['equipment'][0]['parameters']['recovery_fractions']['methane'].update(gas=0, oil=1)
        out = calculate(build_flowsheet(r))['streams']['GAS']
        self.assertEqual(out['mass_flow_kg_h'], 0)
        self.assertIsNone(out['component_mass_fractions'])

    def test_strict_requirements_rejections(self):
        mutations = [
            lambda r: r.update(schema_version='999'),
            lambda r: r.update(unexpected=True),
            lambda r: r['units'].update(pressure='bar'),
            lambda r: r['feeds'][0]['state'].update(temperature_K=True),
            lambda r: r['feeds'][0]['state'].update(temperature_K=float('nan')),
            lambda r: r['feeds'][0]['state'].update(temperature_K=0),
            lambda r: r['feeds'][0]['state'].update(component_mass_flow_kg_h={'methane': 0, 'n_hexane': 0, 'water': 0}),
            lambda r: r['components'].append('water'),
            lambda r: r['components'].append('unknown'),
            lambda r: r['equipment'].append(copy.deepcopy(r['equipment'][0])),
            lambda r: r['equipment'][0]['model'].update(id='three_phase_equilibrium'),
            lambda r: r['equipment'][0]['parameters']['separator'].update(pressure_Pa_abs=3e6),
            lambda r: r['equipment'][0]['parameters']['recovery_fractions']['water'].update(water=1),
            lambda r: r['equipment'][0]['parameters']['caloric_model']['cp_J_kg_K'].update(water=-1),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                r = requirements(); mutate(r)
                with self.assertRaises(Invalid): validate_requirements(r)

    def test_topology_rejections(self):
        mutations = [
            lambda f: f['equipment'][0]['ports'][0].update(id='feed'),
            lambda f: f['connections'][1]['source'].update(port_id='oil'),
            lambda f: f['connections'][1]['target'].update(owner_id='missing'),
            lambda f: f['connections'][1]['target'].update(owner_id='OIL_SINK'),
            lambda f: f['connections'][1].update(stream_id='FEED'),
            lambda f: f['connections'][1].update(id='C-FEED'),
            lambda f: f['streams'][1].update(specified_state=f['streams'][0]['specified_state']),
            lambda f: f['streams'][1].update(service='oil'),
            lambda f: f['boundaries'][1].update(type='source'),
            lambda f: f['solver'].update(method='recycle'),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                f = build_flowsheet(requirements()); mutate(f)
                with self.assertRaises(Invalid): calculate(f)

    def test_layout_and_status_are_not_numerical_identity(self):
        f = build_flowsheet(requirements()); before = semantic_hash(f)
        f['presentation']['layout'] = 'compact'; f['calculation']['status'] = 'stale'
        f['equipment'][0]['ports'].reverse(); f['connections'].reverse()
        self.assertEqual(before, semantic_hash(f))
        self.assertEqual(calculate(f)['input_sha256'], before)

    def test_numerical_and_topology_changes_invalidate_identity(self):
        f = build_flowsheet(requirements()); before = semantic_hash(f)
        f['equipment'][0]['operating_parameters']['separator']['temperature_K'] += 1
        self.assertNotEqual(before, semantic_hash(f))
        f = build_flowsheet(requirements())
        a, b = f['connections'][1:3]
        a['target'], b['target'] = b['target'], a['target']
        validate_flowsheet(f)
        self.assertNotEqual(before, semantic_hash(f))

    def test_case_and_equipment_ids_are_not_hardcoded(self):
        r = requirements(); r['case_id'] = 'NEW-CASE'; r['equipment'][0]['id'] = 'SEP-002'; r['feeds'][0]['id'] = 'SOURCE-2'
        f = build_flowsheet(r); result = calculate(f)
        self.assertEqual(result['equipment'][0]['id'], 'SEP-002')
        self.assertEqual(result['streams']['FEED']['mass_flow_kg_h'], 110000)

    def test_input_is_not_mutated_and_unavailable_is_explicit(self):
        f = build_flowsheet(requirements()); before = copy.deepcopy(f); result = calculate(f)
        self.assertEqual(before, f)
        for item in result['unavailable']:
            self.assertEqual(item['status'], 'not calculated'); self.assertTrue(item['reason'])
            self.assertNotIn('value', item)
        bad = copy.deepcopy(result); bad['unavailable'][0]['value'] = 0
        with self.assertRaises(Invalid): validate_schema('results', bad)

    def test_nonfinite_duplicate_json_and_overflow_rejected(self):
        for text in ['{"x":NaN}', '{"x":1,"x":2}']:
            with self.assertRaises(Invalid): loads(text)
        r = requirements(); r['feeds'][0]['state']['component_mass_flow_kg_h']['water'] = 1e308
        with self.assertRaises(Invalid): calculate(build_flowsheet(r))


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def request(self, path, body, content_type='application/json'):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        connection.request('POST', path, body, {'Content-Type': content_type})
        response = connection.getresponse(); result = (response.status, json.loads(response.read()))
        connection.close(); return result

    def test_http_pipeline(self):
        status, validated = self.request('/v1/validate-requirements', json.dumps(requirements()))
        self.assertEqual(status, 200); self.assertEqual(validated['validation']['status'], 'valid')
        status, f = self.request('/v1/build-flowsheet', json.dumps(validated['requirements']))
        self.assertEqual(status, 200)
        status, result = self.request('/v1/calculate', json.dumps(f))
        self.assertEqual(status, 200); self.assertEqual(result['streams']['FEED']['mass_flow_kg_h'], 110000)

    def test_http_errors(self):
        for path, body, mime, expected in [('/v1/unknown','{}','application/json',404),
             ('/v1/calculate','{}','text/plain',415),('/v1/calculate','{','application/json',422),
             ('/v1/calculate','{}','application/json',422),('/v1/calculate','x'*131073,'application/json',413)]:
            with self.subTest(status=expected):
                status, error = self.request(path,body,mime)
                self.assertEqual(status,expected); self.assertIn('issues',error['error'])


if __name__ == '__main__': unittest.main()
