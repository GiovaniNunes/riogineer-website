"""Strict adapters around the unchanged, snapshotted Bia recovery evaluator."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import uuid

from jsonschema import Draft202012Validator
from .streams import number_streams, unavailable_properties

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'engine/fixtures/treinamento-bia-110000'
MODEL = {'id': 'prescribed_component_recoveries', 'version': '1.0'}
LIMITATIONS = [
    'Prescribed component recoveries; no rigorous vapor-oil-water equilibrium or predicted separation efficiency.',
    'Assumed constant component heat capacities; no pressure or phase dependence, latent heat or dissolution.',
    'OIL is an outlet containing hydrocarbon and carried-over water, not an asserted single equilibrium phase.',
    'One feed and one separator only. No sizing, dynamics, additional equipment or recycle calculations.',
    'Balance checks verify bookkeeping within this development model, not physical accuracy.',
]
WARNING = {'code': 'DEVELOPMENT_MODEL', 'path': '/equipment/0/model', 'severity': 'warning',
           'message': 'Synthetic recovery and Cp assumptions. This is not a rigorous three-phase equilibrium calculation.'}


class Invalid(ValueError):
    def __init__(self, message, path='/', code='VALIDATION_FAILED'):
        super().__init__(message)
        self.payload = {'error': {'code': code, 'message': message, 'issues': [
            {'code': code, 'path': path, 'severity': 'error', 'message': message}]}}


def loads(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Invalid('Duplicate JSON key: ' + key, code='INVALID_JSON')
            result[key] = value
        return result
    def constant(value):
        raise Invalid('Nonfinite JSON value: ' + value, code='INVALID_JSON')
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError) as error:
        if isinstance(error, Invalid):
            raise
        raise Invalid('Invalid JSON document', code='INVALID_JSON') from error


def validate_schema(name, document):
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise Invalid('All numbers must be finite')
        if isinstance(value, dict):
            for item in value.values(): finite(item)
        if isinstance(value, list):
            for item in value: finite(item)
    finite(document)
    schema = json.loads((ROOT / f'contracts/v1/{name}.schema.json').read_text())
    error = next(Draft202012Validator(schema).iter_errors(document), None)
    if error:
        path = '/' + '/'.join(str(p) for p in error.absolute_path)
        raise Invalid(error.message, path)
    return document


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def implementation_hash():
    paths = sorted((ROOT / 'engine/riogineer_engine').glob('*.py')) + sorted((ROOT / 'contracts/v1').glob('*.json'))
    return digest({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


EVALUATOR_PATH = FIXTURE / 'recovery_model.py'
EVALUATOR_HASH = hashlib.sha256(EVALUATOR_PATH.read_bytes()).hexdigest()
manifest = json.loads((FIXTURE / 'manifest.json').read_text())
if EVALUATOR_HASH != next(f['sha256'] for f in manifest['files'] if f['file'] == 'recovery_model.py'):
    raise RuntimeError('The reference evaluator has changed; refuse to run unreviewed equations')
spec = importlib.util.spec_from_file_location('bia_reference_recovery', EVALUATOR_PATH)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def validate_parameters(components, feed, parameters):
    if len(set(components)) != len(components):
        raise Invalid('Component IDs must be unique', '/components')
    keys = set(components)
    for label, values in [('feed', feed['component_mass_flow_kg_h']),
                          ('recoveries', parameters['recovery_fractions']),
                          ('Cp', parameters['caloric_model']['cp_J_kg_K'])]:
        if set(values) != keys:
            raise Invalid(f'{label} component keys must exactly match the component basis')
    if sum(feed['component_mass_flow_kg_h'].values()) <= 0:
        raise Invalid('Feed must have positive total mass flow')
    if parameters['separator']['pressure_Pa_abs'] > feed['pressure_Pa_abs']:
        raise Invalid('Separator pressure cannot exceed feed pressure')
    for component, row in parameters['recovery_fractions'].items():
        if abs(sum(row.values()) - 1) >= 1e-12:
            raise Invalid(f'Recoveries for {component} must sum to one; values are not normalized')


def validate_requirements(requirements):
    validate_schema('requirements', requirements)
    r = requirements
    if r['schema_version'] in ('1.1', '1.2', '1.3', '1.4', '1.5'):
        from .network import build
        f = build(r)
        return {'requirements': deepcopy(r), 'validation': f['validation']}
    reserved = {'GAS_SINK', 'OIL_SINK', 'WATER_SINK'}
    ids = [r['feeds'][0]['id'], r['equipment'][0]['id']]
    if len(set(ids)) != 2 or reserved.intersection(ids):
        raise Invalid('Equipment/source IDs must be distinct and not reserved sink IDs')
    validate_parameters(r['components'], r['feeds'][0]['state'], r['equipment'][0]['parameters'])
    return {'requirements': deepcopy(r), 'validation': {'status': 'valid', 'messages': [deepcopy(WARNING)]}}


def port(name, direction):
    return {'id': name, 'direction': direction, 'kind': 'material'}


def build_flowsheet(requirements):
    if isinstance(requirements, dict) and requirements.get('schema_version') in ('1.1', '1.2', '1.3', '1.4', '1.5'):
        validate_schema('requirements', requirements)
        from .network import build
        return build(requirements)
    validated = validate_requirements(requirements)
    r = validated['requirements']
    unit = r['equipment'][0]
    source = r['feeds'][0]['id']
    f = dict(schema_version='1.1', kind='flowsheet', case_id=r['case_id'], profile=r['profile'],
             units=r['units'], requirements_sha256=digest(r), components=r['components'],
             boundaries=[{'id': source, 'type': 'source', 'ports': [port('outlet', 'out')]}] +
                 [{'id': name + '_SINK', 'type': 'sink', 'ports': [port('inlet', 'in')]} for name in ('GAS', 'OIL', 'WATER')],
             equipment=[{'id': unit['id'], 'type': unit['type'], 'model': unit['model'],
                         'ports': [port('inlet', 'in')] + [port(p, 'out') for p in ('gas', 'oil', 'water')],
                         'operating_parameters': unit['parameters']}],
             streams=[{'id': 'FEED', 'service': 'feed', 'specified_state': r['feeds'][0]['state']}] +
                 [{'id': p.upper(), 'service': p, 'specified_state': None} for p in ('gas', 'oil', 'water')],
             connections=[{'id': 'C-FEED', 'stream_id': 'FEED', 'source': {'owner_id': source, 'port_id': 'outlet'},
                           'target': {'owner_id': unit['id'], 'port_id': 'inlet'}}] +
                 [{'id': 'C-' + p.upper(), 'stream_id': p.upper(), 'source': {'owner_id': unit['id'], 'port_id': p},
                   'target': {'owner_id': p.upper() + '_SINK', 'port_id': 'inlet'}} for p in ('gas', 'oil', 'water')],
             solver={'method': 'single_pass'}, calculation={'status': 'not_run', 'input_sha256': None},
             validation=validated['validation'], presentation={'layout': 'wide'})
    number_streams(f['streams'], f['connections'], [source])
    validate_flowsheet(f)
    f['calculation']['input_sha256'] = semantic_hash(f)
    return f


def validate_flowsheet(f):
    if isinstance(f, dict) and f.get('schema_version') in ('1.2', '1.3', '1.4', '1.5', '1.6'):
        from .network import validate
        validate(f)
        return f
    validate_schema('flowsheet', f)
    nodes = f['boundaries'] + f['equipment']
    ids = [n['id'] for n in nodes]
    if len(set(ids)) != len(ids): raise Invalid('Duplicate node ID')
    sources = [n for n in f['boundaries'] if n['type'] == 'source']
    sinks = [n for n in f['boundaries'] if n['type'] == 'sink']
    if len(sources) != 1 or len(sinks) != 3: raise Invalid('Exactly one source and three sinks required')
    for node in nodes:
        expected = {'inlet': 'in', 'gas': 'out', 'oil': 'out', 'water': 'out'} if node['type'] == 'three_phase_separator' else ({'outlet': 'out'} if node['type'] == 'source' else {'inlet': 'in'})
        if len(node['ports']) != len(expected) or {p['id']: p['direction'] for p in node['ports']} != expected:
            raise Invalid('Invalid or duplicate equipment ports')
    streams = {s['id']: s for s in f['streams']}
    if len(streams) != 4 or {s['service'] for s in streams.values()} != {'feed', 'gas', 'oil', 'water'}:
        raise Invalid('Four unique feed/gas/oil/water streams required')
    if len({c['id'] for c in f['connections']}) != 4 or {c['stream_id'] for c in f['connections']} != set(streams):
        raise Invalid('Exactly one unique connection per stream required')
    if f['schema_version'] == '1.1':
        numbers = [s['engineering_number'] for s in f['streams']]
        if len(set(numbers)) != len(numbers): raise Invalid('Engineering stream numbers must be unique')
    unit = f['equipment'][0]
    used_sinks = set()
    for c in f['connections']:
        s = streams[c['stream_id']]
        if s['service'] == 'feed':
            if c['source'] != {'owner_id': sources[0]['id'], 'port_id': 'outlet'} or c['target'] != {'owner_id': unit['id'], 'port_id': 'inlet'} or s['specified_state'] is None:
                raise Invalid('Feed must connect the source outlet to separator inlet and specify its state')
        else:
            if c['source'] != {'owner_id': unit['id'], 'port_id': s['service']} or c['target']['port_id'] != 'inlet' or c['target']['owner_id'] not in {n['id'] for n in sinks} or s['specified_state'] is not None:
                raise Invalid('Products must connect matching separator ports to sinks, with no independent specified state')
            used_sinks.add(c['target']['owner_id'])
    if len(used_sinks) != 3: raise Invalid('Each product requires its own sink; shared ports and recycles are unsupported')
    feed = next(s for s in streams.values() if s['service'] == 'feed')['specified_state']
    validate_parameters(f['components'], feed, unit['operating_parameters'])
    return f


def semantic_hash(f):
    data = deepcopy(f)
    for key in ('presentation', 'calculation', 'validation'): data.pop(key, None)
    for key in ('equipment', 'boundaries', 'streams', 'connections'):
        data[key].sort(key=lambda n: n['id'])
    for node in data['equipment'] + data['boundaries']: node['ports'].sort(key=lambda p: p['id'])
    data['components'].sort()
    return digest({'flowsheet': data, 'engine': implementation_hash(), 'evaluator': EVALUATOR_HASH, 'model': MODEL})


def _calculate_process(f):
    if isinstance(f, dict) and f.get('schema_version') in ('1.2', '1.3', '1.4', '1.5', '1.6'):
        from .network import calculate as calculate_network
        return calculate_network(f)
    validate_flowsheet(f)
    p = f['equipment'][0]['operating_parameters']
    feed = next(s for s in f['streams'] if s['service'] == 'feed')['specified_state']
    try:
        result = reference.evaluate(feed, p['separator'], p['recovery_fractions'], p['caloric_model'])
        json.dumps(result, allow_nan=False)
    except (ValueError, ArithmeticError) as error:
        raise Invalid('Reference calculation failed: ' + str(error), code='CALCULATION_FAILED') from error
    if not result['checks_passed']:
        raise Invalid('Reference balance checks failed', code='CALCULATION_FAILED')
    streams = {s['id']: {**result['streams']['FEED' if s['service'] == 'feed' else s['service'].upper()],
                         'properties': unavailable_properties()} for s in f['streams']}
    total_residual = sum(result['component_mass_residual_kg_h'].values())
    total_tolerance = len(f['components']) * 1e-8
    output = dict(schema_version='1.1', kind='results', case_id=f['case_id'], run_id=str(uuid.uuid4()),
        input_sha256=semantic_hash(f), requirements_sha256=f['requirements_sha256'],
        engine={'version': '1.0.0', 'implementation_sha256': implementation_hash(), 'evaluator_sha256': EVALUATOR_HASH, 'model': MODEL},
        status='completed', units=f['units'], streams=streams,
        equipment=[{'id': f['equipment'][0]['id'], 'model': MODEL, 'separator_duty_W': result['separator_duty_W']}],
        balances={'mass': {'status': 'passed', 'component_residual_kg_h': result['component_mass_residual_kg_h'],
                          'total_residual_kg_h': total_residual, 'component_tolerance_kg_h': 1e-8, 'total_tolerance_kg_h': total_tolerance},
                  'energy': {'status': 'passed', 'residual_W': result['energy_residual_W'], 'tolerance_W': 1e-6,
                             'duty_W': result['separator_duty_W'], 'model': p['caloric_model']['type'],
                             'reference_temperature_K': p['caloric_model']['reference_temperature_K'], 'positive_duty': 'heat_into_separator'}},
        warnings=[deepcopy(WARNING)], limitations=LIMITATIONS,
        unavailable=[{'calculation': name, 'status': 'not calculated', 'reason': reason} for name, reason in [
            ('Rigorous three-phase equilibrium', 'No VLLE or aqueous equilibrium model is included.'),
            ('Vessel sizing and predicted separation efficiency', 'No geometry-based equipment model is included.'),
            ('Phase-dependent / latent-heat energy balance', 'Only the assumed constant-Cp caloric model is available.')]])
    validate_schema('results', output)
    return output


def calculate(f):
    from .thermodynamics import enrich_results
    output = _calculate_process(f)
    if output['schema_version'] == '1.7':
        return output
    try:
        enriched = enrich_results(output)
    except (ValueError, ArithmeticError) as error:
        raise Invalid('Molecular property calculation failed: ' + str(error), code='CALCULATION_FAILED') from error
    validate_schema('results', enriched)
    return enriched
