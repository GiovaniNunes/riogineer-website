"""Validated acyclic execution over existing stable stream identities."""
from copy import deepcopy
import math
import uuid
from .network_models import MODELS, ports, state_from_rates, equipment_result, SPLIT_TOLERANCE, TEMPERATURE_TOLERANCE_K, PRESSURE_TOLERANCE_PA
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
    f = dict(schema_version={'1.1': '1.2', '1.2': '1.3', '1.3': '1.4', '1.4': '1.5', '1.5': '1.6', '1.6': '1.7', '1.7': '1.8', '1.8': '1.9'}[r['schema_version']], kind='flowsheet', case_id=r['case_id'], profile=r['profile'],
             units=r['units'], requirements_sha256=digest(r), components=r['components'],
             boundaries=[dict(id=s['id'], type='source', ports=ports('source')) for s in r['feeds']] +
                        [dict(id=s['id'], type='sink', ports=ports('sink')) for s in r['sinks']],
             equipment=[dict(id=u['id'], type=u['type'], model=u['model'], ports=ports(u['type']),
                             operating_parameters=u['parameters']) for u in r['equipment']],
             streams=streams, connections=connections, solver={'method': 'topological'},
             calculation={'status': 'not_run', 'input_sha256': None},
             validation={'status': 'valid', 'messages': [warning()]}, presentation={'layout': 'wide'})
    if r['profile'] == 'pt_flash_separator':
        f['validation']['messages'] = [equilibrium_warning()]
    elif r['profile'] not in ('heater_cooler_energy', 'compressor_energy', 'two_stream_heat_exchanger_energy', 'throttling_valve_energy'):
        f['caloric_model'] = r['caloric_model']
    else:
        f['validation']['messages'] = []
    # Topology is checked before assigning numbers; a cycle never receives a silent tear.
    validate(f, numbered=False)
    number_streams(f['streams'], f['connections'], list(feed_by_id))
    validate(f)
    f['calculation']['input_sha256'] = semantic_hash(f)
    return f


def equilibrium_warning():
    from .equilibrium_separator import ENERGY_REASON
    return dict(code='PT_ENERGY_UNAVAILABLE', path='/', severity='warning', message=ENERGY_REASON)


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
    equilibrium = f['profile'] == 'pt_flash_separator'
    thermal = f['profile'] == 'heater_cooler_energy'
    compression = f['profile'] == 'compressor_energy'
    exchanger = f['profile'] == 'two_stream_heat_exchanger_energy'
    valve = f['profile'] == 'throttling_valve_energy'
    cal = f.get('caloric_model')
    if not valve and not equilibrium and not thermal and not compression and not exchanger and set(cal['cp_J_kg_K']) != components: reject('Caloric component keys must match the component basis')
    sources = {n['id'] for n in f['boundaries'] if n['type'] == 'source'}
    sinks = {n['id'] for n in f['boundaries'] if n['type'] == 'sink'}
    if not sources or not sinks: reject('At least one explicit source and sink required')
    if equilibrium:
        if components != {'methane', 'n_hexane'} or len(sources) != 1 or len(sinks) != 2:
            reject('PT separator requires one binary hydrocarbon feed and two product sinks')
        if len(f['equipment']) != 1 or f['equipment'][0]['type'] != 'equilibrium_separator_2phase':
            reject('PT reference supports one equilibrium separator only')
    if thermal:
        if components != {'methane', 'n_hexane'} or len(sources) != 1 or len(sinks) != 1 or len(f['equipment']) != 1 or f['equipment'][0]['type'] != 'heater':
            reject('M12 supports one binary hydrocarbon heater between one source and sink')
    if compression:
        if components != {'methane', 'n_hexane'} or len(sources) != 1 or len(sinks) != 1 or len(f['equipment']) != 1 or f['equipment'][0]['type'] != 'compressor':
            reject('M14 supports one binary hydrocarbon compressor between one source and sink')
    if valve:
        if components != {'methane', 'n_hexane'} or len(sources) != 1 or len(sinks) != 1 or len(f['equipment']) != 1 or f['equipment'][0]['type'] != 'throttling_valve':
            reject('M16 supports one binary hydrocarbon valve between one source and sink')
    if exchanger:
        if components != {'methane', 'n_hexane'} or len(sources) < 2 or len(sinks) < 2 or any(u['type'] != 'two_stream_heat_exchanger' for u in f['equipment']):
            reject('M15 requires separate binary hydrocarbon paths and explicit rigorous exchangers')
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
        if thermal:
            from .heater_cooler_energy import MODEL as thermal_model, parameters
            if unit['model'] != thermal_model: reject('Unsupported thermal model')
            try: parameters(unit['operating_parameters'])
            except ValueError as error: reject(str(error))
        elif valve:
            from .throttling_valve_energy import parameters as valve_parameters
            if unit['model'] != MODELS['throttling_valve']['model']: reject('Unsupported rigorous valve model')
            try: valve_parameters(unit['operating_parameters'])
            except ValueError as error: reject(str(error))
        elif compression:
            from .compressor_energy import MODEL as compression_model, parameters as compressor_parameters
            if unit['model'] != compression_model: reject('Unsupported rigorous compressor model')
            try: compressor_parameters(unit['operating_parameters'])
            except ValueError as error: reject(str(error))
        elif unit['model'] != MODELS[unit['type']]['model']: reject('Unsupported equipment model')
        p = unit['operating_parameters']
        if unit['type'] == 'heater' and not thermal and p['caloric_model'] != cal:
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
    if f['profile'] == 'throttling_valve_energy':
        from .throttling_valve_process import calculate as calculate_valve
        return calculate_valve(f)
    if f['profile'] == 'two_stream_heat_exchanger_energy':
        from .two_stream_heat_exchanger_process import calculate as calculate_exchanger
        return calculate_exchanger(f)
    if f['profile'] == 'compressor_energy':
        from .compressor_process import calculate as calculate_compression
        return calculate_compression(f)
    if f['profile'] == 'heater_cooler_energy':
        from .thermal_process import calculate as calculate_thermal
        return calculate_thermal(f)
    from .core import Invalid, reference, EVALUATOR_HASH, implementation_hash, semantic_hash, validate_schema
    order = validate(f)
    equilibrium = f['profile'] == 'pt_flash_separator'
    cal = f.get('caloric_model')
    components = sorted(f['components'])
    states = {}
    for s in sorted(f['streams'], key=lambda s: s['id']):
        if s['specified_state'] is not None:
            state = s['specified_state']
            rates = deepcopy(state['component_mass_flow_kg_h'])
            # The same declared constant-Cp reference accounting as the preserved evaluator.
            h = None if equilibrium else sum(rates[c] * cal['cp_J_kg_K'][c] * (state['temperature_K'] - cal['reference_temperature_K']) / 3600 for c in components)
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
            if unit['type'] == 'compressor':
                feed = incoming['inlet']
                rates = feed['component_mass_flow_kg_h']
                total = sum(rates.values())
                if total <= 0: raise ValueError('Compressor requires positive inlet mass flow')
                effective_cp = sum(rates[c] / total * cal['cp_J_kg_K'][c] for c in components)
                if not math.isclose(effective_cp, unit['operating_parameters']['cp_J_kg_K'], rel_tol=0, abs_tol=1e-8):
                    raise ValueError('Compressor Cp must match the runtime mass-weighted network caloric basis')
            executed = equipment_result(MODELS[unit['type']]['execute'](unit, incoming, reference.evaluate))
            outgoing, duty, work = executed.streams, executed.duty_W, executed.work_W
            balance = mass_balance(list(incoming.values()), list(outgoing.values()), components)
            energy = None if equilibrium else sum(s['enthalpy_flow_W'] for s in incoming.values()) + duty + work - sum(s['enthalpy_flow_W'] for s in outgoing.values())
            if not equilibrium and (not math.isfinite(energy) or abs(energy) > ENERGY_TOLERANCE):
                raise ValueError('Constant-Cp energy accounting failed')
        except (ValueError, ArithmeticError) as error:
            raise Invalid(f'{uid}: {error}', code='CALCULATION_FAILED') from error
        for c in f['connections']:
            if c['source']['owner_id'] == uid:
                states[c['stream_id']] = outgoing[c['source']['port_id']]
        if equilibrium:
            executed.details['material_streams'] = {
                'inlet': next(c['stream_id'] for c in f['connections'] if c['target']['owner_id'] == uid),
                **{c['source']['port_id']: c['stream_id'] for c in f['connections'] if c['source']['owner_id'] == uid},
            }
        equipment.append(dict(id=uid, type=unit['type'], model=unit['model'], duty_W=duty, work_W=work, **executed.details,
                              mass_balance=balance, energy_residual_W=energy))
    sink_ids = {b['id'] for b in f['boundaries'] if b['type'] == 'sink'}
    products = [states[c['stream_id']] for c in sorted(f['connections'], key=lambda c: c['stream_id']) if c['target']['owner_id'] in sink_ids]
    balance = mass_balance(feed_states, products, components)
    duty = None if equilibrium else sum(e['duty_W'] for e in equipment)
    work = None if equilibrium else sum(e['work_W'] for e in equipment)
    energy = None if equilibrium else sum(s['enthalpy_flow_W'] for s in feed_states) + duty + work - sum(s['enthalpy_flow_W'] for s in products)
    if not equilibrium and (not math.isfinite(energy) or abs(energy) > ENERGY_TOLERANCE):
        raise Invalid('Network constant-Cp energy accounting failed', code='CALCULATION_FAILED')
    output = dict(schema_version='1.6' if equilibrium else f['schema_version'], kind='results', case_id=f['case_id'], run_id=str(uuid.uuid4()),
                  input_sha256=semantic_hash(f), requirements_sha256=f['requirements_sha256'],
                  engine=dict(version={'1.2': '1.1.0', '1.3': '1.2.0', '1.4': '1.3.0', '1.5': '1.5.0'}[f['schema_version']], implementation_sha256=implementation_hash(), evaluator_sha256=EVALUATOR_HASH, model=MODEL),
                  status='completed', units=f['units'], streams={sid: dict(states[sid], properties=unavailable_properties()) for sid in sorted(states)},
                  equipment=equipment, execution={'method': 'topological', 'equipment_order': order},
                  model_tolerances=dict(split_fraction=SPLIT_TOLERANCE, mixer_temperature_K=TEMPERATURE_TOLERANCE_K, mixer_pressure_Pa=PRESSURE_TOLERANCE_PA),
                  balances={'mass': balance, 'energy': dict(status='not_calculated', reason=equilibrium_warning()['message'], duty_W=None, residual_W=None) if equilibrium else dict(status='passed', residual_W=energy, tolerance_W=ENERGY_TOLERANCE,
                    duty_W=duty, model=cal['type'], reference_temperature_K=cal['reference_temperature_K'], positive_duty='heat_into_network')},
                  warnings=[warning()], limitations=LIMITATIONS if f['schema_version'] == '1.2' else [
                    'Acyclic separators, splitters, equal-condition mixers and specified-temperature constant-Cp heaters only; no recycle convergence.',
                    'Heating does not cause or predict downstream separator recoveries: these are independently prescribed synthetic inputs.',
                    'Constant-Cp sensible-heat accounting only: no latent heat, EOS, phase-equilibrium enthalpy, pressure work or rigorous property model.',
                    'Heater pressure is unchanged; no pressure drop, sizing, heat-transfer area or duty-specified temperature solve.',
                ],
                  unavailable=[dict(calculation='Rigorous thermodynamics and general mixer temperature', status='not calculated',
                                    reason='Only prescribed recoveries and equal-condition mixing with constant-Cp accounting are supported.' if f['schema_version'] == '1.2' else 'Only prescribed recoveries, material splitting/mixing and specified-temperature constant-Cp heaters are supported; no rigorous properties or duty-specified temperature solve.')])
    if f['schema_version'] == '1.4':
        shaft = sum(e.get('compression', {}).get('shaft_power_W', 0) for e in equipment)
        output['balances']['energy'].update(process_work_W=work, shaft_power_W=shaft,
            mechanical_loss_W=shaft-work, positive_work='work_into_process',
            external_enthalpy_change_W=sum(s['enthalpy_flow_W'] for s in products)-sum(s['enthalpy_flow_W'] for s in feed_states))
        output['limitations'][0] = 'Acyclic separators, splitters, equal-condition mixers, specified-temperature heaters and ideal-gas compressors only; no recycles.'
        output['limitations'].extend([
            'Compressor is an ideal-gas development model with constant Cp/k and prescribed isentropic/mechanical efficiencies; inlet gas phase is explicitly assumed, not predicted.',
            'No EOS, Z correction, real-gas enthalpy, compressor map, polytropic calculation, surge/choke, speed, stage design, intercooling, aftercooling, liquid carryover handling, mechanical sizing or driver sizing.',
            'Positive process work is energy transferred to gas. Shaft power includes mechanical losses outside the material-stream energy boundary; driver power is not calculated.',
        ])
        output['unavailable'][0]['reason'] = 'Only registered deterministic development models; no rigorous properties, phase prediction or driver power.'
    if equilibrium:
        output.pop('model_tolerances')
        output['warnings'] = [equilibrium_warning()]
        output['limitations'] = [
            'Qualified methane/n_hexane hydrocarbon PT flash with explicit zero kij only; no water, VLLE, PH/PS flash or sizing.',
            'Isothermal and isobaric at inlet conditions; beta is a molar fraction, not a mass fraction.',
            equilibrium_warning()['message'],
        ]
        output['unavailable'] = [dict(calculation='Rigorous phase-change energy balance', status='not calculated',
                                      reason=equilibrium_warning()['message'])]
        # M9 has a single public enriched result contract, validated by core.calculate.
    else:
        validate_schema('results', output)
    return output


def execute_exchanger_graph(f):
    """Evaluate each ready four-port unit once; publish neither outlet on failure.

    The local state store is recreated per call. No prior run is an input.
    Separate material checks precede publication, even for injected evaluators.
    """
    from .core import Invalid
    order = validate(f)
    states = {s['id']: state_from_rates(deepcopy(s['specified_state']['component_mass_flow_kg_h']),
        s['specified_state']['temperature_K'], s['specified_state']['pressure_Pa_abs'], None)
        for s in f['streams'] if s['specified_state'] is not None}
    records = []
    for uid in order:
        unit = next(u for u in f['equipment'] if u['id'] == uid)
        links = {c['target']['port_id']: c['stream_id'] for c in f['connections'] if c['target']['owner_id'] == uid}
        links.update({c['source']['port_id']: c['stream_id'] for c in f['connections'] if c['source']['owner_id'] == uid})
        incoming = {p: deepcopy(states[links[p]]) for p in ('hot_in', 'cold_in')}
        try:
            result = equipment_result(MODELS['two_stream_heat_exchanger']['execute'](unit, deepcopy(incoming), None))
            if set(result.streams) != {'hot_out', 'cold_out'}:
                raise ValueError('Both exchanger outlets are required atomically')
            balances = {}
            for side in ('hot', 'cold'):
                feed, out = incoming[side+'_in'], result.streams[side+'_out']
                if feed['component_mass_flow_kg_h'] != out['component_mass_flow_kg_h'] or feed['mass_flow_kg_h'] != out['mass_flow_kg_h'] or feed['component_mass_fractions'] != out['component_mass_fractions']:
                    raise ValueError(side+': wall-separated material path violated')
                balances[side] = mass_balance([feed], [out], f['components'])
        except (ValueError, ArithmeticError) as error:
            raise Invalid(f'{uid}: {error}', code='CALCULATION_FAILED') from error
        states.update({links[p]: deepcopy(result.streams[p]) for p in ('hot_out', 'cold_out')})
        records.append((unit, links, incoming, result, balances))
    return states, records
