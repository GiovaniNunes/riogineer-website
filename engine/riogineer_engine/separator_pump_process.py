"""Bounded M20 process using the existing validated network schedule."""
from copy import deepcopy
from math import fsum
import uuid
import json
from .network_models import equipment_result, state_from_rates, MODELS
from .streams import unavailable_properties
from .thermodynamics import MolecularCompositionProvider, quantity
from .separator_pump_scope import layout, qualify, specification
from .separator_liquid_state import representation, identity, require, Failure, ROUND
from .separator_liquid_pump import run


class ExecutionContext:
    """Private per-calculation evidence; never populated from editable stream JSON."""
    def __init__(self, flowsheet, current):
        self.flowsheet = flowsheet
        self.current = current
        self.completed = {}

    def resolve(self, consumer, link):
        require(link in self.flowsheet['connections'], 'current_connection')
        require(link['target'] == dict(owner_id=consumer['id'], port_id='inlet'), 'consumer_port')
        require(link['source']['port_id'] == 'liquid', 'liquid_port')
        source = self.completed.get(link['source']['owner_id'])
        require(source is not None, 'upstream_not_completed', 'missing_evidence')
        require(identity(source) == self.current, 'stale_execution')
        require(source['equipment'][0]['material_streams']['liquid'] == link['stream_id'], 'source_stream')
        return representation(source), source


def enrich(s):
    m = MolecularCompositionProvider().enrich(s).composition
    s['properties'] = unavailable_properties()
    s['properties'].update(molar_flow=quantity(m.molar_flow_kmol_h, 'kmol/h'),
        molecular_mass=quantity(m.molecular_weight_kg_kmol, 'kg/kmol'),
        molar_composition=quantity(dict(m.molar_fractions) if m.molar_fractions is not None else None, 'mol/mol'))


def calculate(f):
    from .core import semantic_hash, implementation_hash, EVALUATOR_HASH, Invalid, validate_schema, digest
    from .network import validate, mass_balance, MODEL
    from .separator_energy import SeparatorFailure
    from .pump_energy import PumpFailure
    order = validate(f)
    qualification = qualify(f)
    sep, pump, feed_link, liquid_link, vapor_link, product_link = layout(f)
    current = dict(run_id=str(uuid.uuid4()), input_sha256=semantic_hash(f), requirements_sha256=f['requirements_sha256'])
    if f['calculation']['input_sha256'] != current['input_sha256']:
        raise Invalid('M20 stale flowsheet: rebuild from current requirements', code='M20_STALE_INPUT')
    context = ExecutionContext(f, current)
    source = next(s['specified_state'] for s in f['streams'] if s['id'] == feed_link['stream_id'])
    feed = state_from_rates(deepcopy(source['component_mass_flow_kg_h']), source['temperature_K'], source['pressure_Pa_abs'], None)
    states = {feed_link['stream_id']: feed}
    equipment = []
    try:
        for uid in order:
            if uid == sep['id']:
                result = equipment_result(MODELS['equilibrium_separator_2phase']['execute'](sep, {'inlet': feed}, None))
                d = result.details['thermodynamics']
                feed['enthalpy_flow_W'] = d['F_mol_s'] * d['inlet']['H_eq_J_mol']
                states.update({liquid_link['stream_id']: result.streams['liquid'], vapor_link['stream_id']: result.streams['vapor']})
                for s in states.values(): enrich(s)
                equipment.append(dict(id=uid, type=sep['type'], model=sep['model'],
                    material_streams=dict(inlet=feed_link['stream_id'], liquid=liquid_link['stream_id'], vapor=vapor_link['stream_id']),
                    duty_W=result.duty_W, work_W=0., thermodynamics=d, energy_residual_W=d['energy_residual_W'],
                    mass_balance=mass_balance([feed], list(result.streams.values()), f['components'])))
                context.completed[uid] = deepcopy(dict(**current, status='completed', units=f['units'], streams=states, equipment=equipment))
            else:
                inlet, evidence = context.resolve(pump, liquid_link)
                p = pump['operating_parameters']
                answer = run(inlet, evidence, current, p['outlet_pressure_Pa_abs'], p['isentropic_efficiency'])
                states[liquid_link['stream_id']] = inlet
                outlet = answer['outlet']
                outlet['state_context'] = deepcopy(inlet['state_context'])
                outlet['state_context'].update(saturation=inlet['state_context']['saturation'] if answer['identity'] else 'compressed_witness',
                    source=current | dict(equipment_id=uid, port_id='outlet', stream_id=product_link['stream_id']),
                    lineage=[deepcopy(inlet['state_context']['source'])])
                states[product_link['stream_id']] = outlet
                allowance = answer.get('energy_allowance_W', answer['inlet']['enthalpy_allowance_W'])
                equipment.append(dict(id=uid, type='pump', model=pump['model'],
                    material_streams=dict(inlet=liquid_link['stream_id'], outlet=product_link['stream_id']),
                    duty_W=0., work_W=answer['fluid_power_W'], energy_residual_W=answer['energy_residual_W'],
                    mass_balance=mass_balance([inlet], [outlet], f['components']),
                    thermodynamics=dict(qualification_id=qualification, source_spec_sha256=digest(specification(f)),
                        identity=answer['identity'], isentropic_efficiency=p['isentropic_efficiency'],
                        reconstructed_efficiency=answer['reconstructed_efficiency'], energy_allowance_W=allowance,
                        diagnostics={k:v for k,v in answer.items() if k != 'outlet'})))
    except Failure as error:
        raise Invalid(f'M20 incomplete process: {error}', path='/equipment', code='M20_'+error.category.upper()) from error
    except (SeparatorFailure, PumpFailure) as error:
        raise Invalid(f'M20 incomplete process: {error}', path='/equipment', code='M20_CALCULATION_FAILED') from error
    feed['state_context'] = dict(specification_kind='independent_PT')
    vapor, product = states[vapor_link['stream_id']], states[product_link['stream_id']]
    vapor['state_context'] = deepcopy(states[liquid_link['stream_id']]['state_context'])
    vapor['state_context'].update(phase='vapor', saturation='unknown',
        source=current | dict(equipment_id=sep['id'], port_id='vapor', stream_id=vapor_link['stream_id']))
    duty, power = equipment[0]['duty_W'], equipment[1]['work_W']
    residual = fsum([vapor['enthalpy_flow_W'], product['enthalpy_flow_W'], -feed['enthalpy_flow_W'], -duty, -power])
    tolerance = equipment[0]['thermodynamics']['energy_allowance_W'] + allowance + ROUND * max(1, abs(feed['enthalpy_flow_W']), abs(product['enthalpy_flow_W']), abs(vapor['enthalpy_flow_W']))
    if abs(residual) > tolerance: raise Invalid('M20 overall energy balance failed', code='M20_CALCULATION_FAILED')
    balance = mass_balance([feed], [vapor, product], f['components'])
    output = dict(schema_version='1.14', process_result_version='1.14', kind='results', case_id=f['case_id'], **current,
        engine=dict(version='1.13.0', implementation_sha256=implementation_hash(), evaluator_sha256=EVALUATOR_HASH, model=MODEL),
        status='completed', units=f['units'], streams=states, equipment=equipment,
        execution=dict(method='topological', equipment_order=order), balances=dict(mass=balance,
            energy=dict(status='passed', residual_W=residual, tolerance_W=tolerance, duty_W=duty, fluid_power_W=power,
                model='separator_pump_energy', positive_duty='heat_into_process', positive_work='work_into_process')),
        warnings=[], limitations=[
            'Only 30 listed qualified source/pressure/efficiency tuples; no operating envelope or interpolation.',
            'Methane/n_hexane, explicit zero kij; existing PR caloric and full inverse routines.',
            'Local sampled phase evidence and endpoint checks do not prove continuous-path admissibility.',
            'No bubble-pressure measurement, cavitation or NPSH prediction, hydraulic sizing or electrical power.',
            'Known 8 MPa PS failures remain excluded and unresolved.'],
        unavailable=[dict(calculation='Hydraulic sizing and cavitation', status='not calculated', reason='M20 qualifies material and fluid-energy integration only.')])
    output = json.loads(json.dumps(output, allow_nan=False))
    validate_schema('results', output)
    return output
