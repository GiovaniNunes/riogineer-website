"""Validated acyclic execution over existing stable stream identities."""
from copy import deepcopy
import math
import uuid
from .network_models import MODELS, ports, state_from_rates, SPLIT_TOLERANCE, TEMPERATURE_TOLERANCE_K, PRESSURE_TOLERANCE_PA
from .streams import number_streams, unavailable_properties

MODEL = {'id': 'acyclic_component_conservation', 'version': '1.0'}
COMPONENT_TOLERANCE = 1e-8
ENERGY_TOLERANCE = 1e-6
LIMITATIONS = [
    'Prescribed separator recoveries and constant component Cp; no equilibrium or property prediction.',
    'Mixer supports equal inlet temperature and pressure only; no enthalpy-based temperature solution.',
    'Network energy accounting is limited to the shared constant-Cp reference model and equal-condition mixing; no phase-dependent or latent heat closure.',
    'Acyclic material networks with separators, two-outlet splitters and two-inlet mixers only. No recycle convergence.',
]


def build(requirements):
    from .core import digest, semantic_hash
    r = deepcopy(requirements)
    feed_by_id = {s['id']: s['state'] for s in r['feeds']}
    connections = r['connections']
    streams = []
    for stream in r['streams']:
        links = [c for c in connections if c['stream_id'] == stream['id']]
        source = links[0]['source']['owner_id'] if len(links) == 1 else None
        streams.append(dict(stream, specified_state=deepcopy(feed_by_id.get(source))))
    f = dict(schema_version='1.3' if r['schema_version'] == '1.2' else '1.2', kind='flowsheet', case_id=r['case_id'], profile=r['profile'],
             units=r['units'], requirements_sha256=digest(r), components=r['components'],
             caloric_model=r['caloric_model'],
             boundaries=[dict(id=s['id'], type='source', ports=ports('source')) for s in r['feeds']] +
                        [dict(id=s['id'], type='sink', ports=ports('sink')) for s in r['sinks']],
             equipment=[dict(id=u['id'], type=u['type'], model=u['model'], ports=ports(u['type']),
                             operating_parameters=u['parameters']) for u in r['equipment']],
             streams=streams, connections=connections, solver={'method': 'topological'},
             calculation={'status': 'not_run', 'input_sha256': None},
             validation={'status': 'valid', 'messages': [warning()]}, presentation={'layout': 'wide'})
    # Topology is checked before assigning numbers; a cycle never receives a silent tear.
    validate(f, numbered=False)
    number_streams(f['streams'], f['connections'], list(feed_by_id))
    validate(f)
    f['calculation']['input_sha256'] = semantic_hash(f)
    return f


def warning():
    return {'code': 'DEVELOPMENT_MODEL', 'path': '/', 'severity': 'warning',
            'message': 'Synthetic prescribed recoveries, proportional splits and equal-condition mixing; no rigorous thermodynamics.'}


def validate(f, numbered=True):
    from .core import Invalid, validate_schema
    if numbered:
        validate_schema('flowsheet', f)
    def reject(message):
        raise Invalid(message)
    nodes = f['boundaries'] + f['equipment']
    by_id = {n['id']: n for n in nodes}
    if len(by_id) != len(nodes): reject('Duplicate equipment/boundary ID')
    components = set(f['components'])
    if len(components) != len(f['components']): reject('Duplicate component ID')
    cal = f['caloric_model']
    if set(cal['cp_J_kg_K']) != components: reject('Caloric component keys must match the component basis')
    sources = {n['id'] for n in f['boundaries'] if n['type'] == 'source'}
    sinks = {n['id'] for n in f['boundaries'] if n['type'] == 'sink'}
    if not sources or not sinks: reject('At least one explicit source and sink required')
    port_map = {}
    for node in nodes:
        expected = {p['id']: p['direction'] for p in ports(node['type'])}
        if len(node['ports']) != len(expected) or {p['id']: p['direction'] for p in node['ports']} != expected:
            reject(f"{node['id']}: invalid or duplicate required ports")
        port_map.update({(node['id'], p): direction for p, direction in expected.items()})
    stream_by_id = {s['id']: s for s in f['streams']}
    if len(stream_by_id) != len(f['streams']): reject('Duplicate stable stream ID')
    if numbered and len({s['engineering_number'] for s in f['streams']}) != len(f['streams']):
        reject('Engineering stream numbers must be unique')
    connections = f['connections']
    if len({c['id'] for c in connections}) != len(connections): reject('Duplicate connection ID')
    if len(connections) != len(stream_by_id) or {c['stream_id'] for c in connections} != set(stream_by_id):
        reject('Exactly one connection per stable stream ID required')
    occupied = set()
    for c in connections:
        for side, direction in [('source', 'out'), ('target', 'in')]:
            endpoint = c[side]
            key = (endpoint['owner_id'], endpoint['port_id'])
            if endpoint['owner_id'] not in by_id: reject('Unknown equipment/boundary ID in connection')
            if key not in port_map: reject('Unknown port in connection')
            if port_map[key] != direction: reject('Invalid source/destination port direction')
            if key in occupied: reject('Duplicate occupation of single-use port; use explicit splitter/mixer')
            occupied.add(key)
        state = stream_by_id[c['stream_id']]['specified_state']
        if c['source']['owner_id'] in sources:
            if state is None or set(state['component_mass_flow_kg_h']) != components:
                reject('Source stream requires the complete component basis')
            if sum(state['component_mass_flow_kg_h'].values()) <= 0:
                reject('Source feed must have positive total mass flow')
        elif state is not None: reject('Only source streams may independently specify state')
    if occupied != set(port_map): reject('Missing required input or output connection')
    for unit in f['equipment']:
        if unit['model'] != MODELS[unit['type']]['model']: reject('Unsupported equipment model')
        p = unit['operating_parameters']
        if unit['type'] == 'heater' and p['caloric_model'] != cal:
            reject('All equipment must share the network caloric basis')
        if unit['type'] == 'splitter':
            if abs(sum(p['fractions'].values()) - 1) >= SPLIT_TOLERANCE:
                reject('Splitter fractions must sum to one; values are not normalized')
        elif unit['type'] == 'three_phase_separator':
            if p['caloric_model'] != cal: reject('All equipment must share the network caloric basis')
            if set(p['recovery_fractions']) != components: reject('Recovery component keys must match the component basis')
            if any(abs(sum(row.values()) - 1) >= SPLIT_TOLERANCE for row in p['recovery_fractions'].values()):
                reject('Separator recoveries must sum to one')
    # Kahn dependency traversal, choosing the lexical stable ID among ready units.
    available = {c['stream_id'] for c in connections if c['source']['owner_id'] in sources}
    pending = {u['id']: u for u in f['equipment']}
    order = []
    while pending:
        ready = sorted(uid for uid in pending if
                       {c['stream_id'] for c in connections if c['target']['owner_id'] == uid} <= available)
        if not ready: reject('Cycle detected: recycle networks are not supported by this milestone')
        uid = ready[0]
        order.append(uid)
        available.update(c['stream_id'] for c in connections if c['source']['owner_id'] == uid)
        del pending[uid]
    return order


def mass_balance(inputs, outputs, components):
    from .core import Invalid
    residual = {c: sum(s['component_mass_flow_kg_h'][c] for s in inputs) -
                   sum(s['component_mass_flow_kg_h'][c] for s in outputs) for c in components}
    total = sum(s['mass_flow_kg_h'] for s in inputs) - sum(s['mass_flow_kg_h'] for s in outputs)
    total_tolerance = len(components) * COMPONENT_TOLERANCE
    if any(not math.isfinite(v) or abs(v) > COMPONENT_TOLERANCE for v in residual.values()) or not math.isfinite(total) or abs(total) > total_tolerance:
        raise Invalid('Component or total mass balance failed', code='CALCULATION_FAILED')
    return dict(status='passed', component_residual_kg_h=residual, total_residual_kg_h=total,
                component_tolerance_kg_h=COMPONENT_TOLERANCE, total_tolerance_kg_h=total_tolerance)


def calculate(f):
    from .core import Invalid, reference, EVALUATOR_HASH, implementation_hash, semantic_hash, validate_schema
    order = validate(f)
    cal = f['caloric_model']
    components = sorted(f['components'])
    states = {}
    for s in sorted(f['streams'], key=lambda s: s['id']):
        if s['specified_state'] is not None:
            state = s['specified_state']
            rates = deepcopy(state['component_mass_flow_kg_h'])
            # The same declared constant-Cp reference accounting as the preserved evaluator.
            h = sum(rates[c] * cal['cp_J_kg_K'][c] * (state['temperature_K'] - cal['reference_temperature_K']) / 3600 for c in components)
            states[s['id']] = state_from_rates(rates, state['temperature_K'], state['pressure_Pa_abs'], h)
    feed_states = list(states.values())
    units = {u['id']: u for u in f['equipment']}
    equipment = []
    for uid in order:
        unit = units[uid]
        incoming = {c['target']['port_id']: states[c['stream_id']] for c in f['connections'] if c['target']['owner_id'] == uid}
        try:
            if unit['type'] == 'three_phase_separator' and unit['operating_parameters']['separator']['pressure_Pa_abs'] > incoming['inlet']['pressure_Pa_abs']:
                raise ValueError('Separator cannot increase pressure')
            outgoing, duty = MODELS[unit['type']]['execute'](unit, incoming, reference.evaluate)
            balance = mass_balance(list(incoming.values()), list(outgoing.values()), components)
            energy = sum(s['enthalpy_flow_W'] for s in incoming.values()) + duty - sum(s['enthalpy_flow_W'] for s in outgoing.values())
            if not math.isfinite(energy) or abs(energy) > ENERGY_TOLERANCE:
                raise ValueError('Constant-Cp energy accounting failed')
        except (ValueError, ArithmeticError) as error:
            raise Invalid(f'{uid}: {error}', code='CALCULATION_FAILED') from error
        for c in f['connections']:
            if c['source']['owner_id'] == uid:
                states[c['stream_id']] = outgoing[c['source']['port_id']]
        equipment.append(dict(id=uid, type=unit['type'], model=unit['model'], duty_W=duty, work_W=0.0,
                              mass_balance=balance, energy_residual_W=energy))
    sink_ids = {b['id'] for b in f['boundaries'] if b['type'] == 'sink'}
    products = [states[c['stream_id']] for c in sorted(f['connections'], key=lambda c: c['stream_id']) if c['target']['owner_id'] in sink_ids]
    balance = mass_balance(feed_states, products, components)
    duty = sum(e['duty_W'] for e in equipment)
    energy = sum(s['enthalpy_flow_W'] for s in feed_states) + duty - sum(s['enthalpy_flow_W'] for s in products)
    if not math.isfinite(energy) or abs(energy) > ENERGY_TOLERANCE:
        raise Invalid('Network constant-Cp energy accounting failed', code='CALCULATION_FAILED')
    output = dict(schema_version=f['schema_version'], kind='results', case_id=f['case_id'], run_id=str(uuid.uuid4()),
                  input_sha256=semantic_hash(f), requirements_sha256=f['requirements_sha256'],
                  engine=dict(version='1.2.0' if f['schema_version'] == '1.3' else '1.1.0', implementation_sha256=implementation_hash(), evaluator_sha256=EVALUATOR_HASH, model=MODEL),
                  status='completed', units=f['units'], streams={sid: dict(states[sid], properties=unavailable_properties()) for sid in sorted(states)},
                  equipment=equipment, execution={'method': 'topological', 'equipment_order': order},
                  model_tolerances=dict(split_fraction=SPLIT_TOLERANCE, mixer_temperature_K=TEMPERATURE_TOLERANCE_K, mixer_pressure_Pa=PRESSURE_TOLERANCE_PA),
                  balances={'mass': balance, 'energy': dict(status='passed', residual_W=energy, tolerance_W=ENERGY_TOLERANCE,
                    duty_W=duty, model=cal['type'], reference_temperature_K=cal['reference_temperature_K'], positive_duty='heat_into_network')},
                  warnings=[warning()], limitations=LIMITATIONS if f['schema_version'] == '1.2' else [
                    'Acyclic separators, splitters, equal-condition mixers and specified-temperature constant-Cp heaters only; no recycle convergence.',
                    'Heating does not cause or predict downstream separator recoveries: these are independently prescribed synthetic inputs.',
                    'Constant-Cp sensible-heat accounting only: no latent heat, EOS, phase-equilibrium enthalpy, pressure work or rigorous property model.',
                    'Heater pressure is unchanged; no pressure drop, sizing, heat-transfer area or duty-specified temperature solve.',
                ],
                  unavailable=[dict(calculation='Rigorous thermodynamics and general mixer temperature', status='not calculated',
                                    reason='Only prescribed recoveries and equal-condition mixing with constant-Cp accounting are supported.' if f['schema_version'] == '1.2' else 'Only prescribed recoveries, material splitting/mixing and specified-temperature constant-Cp heaters are supported; no rigorous properties or duty-specified temperature solve.')])
    validate_schema('results', output)
    return output
