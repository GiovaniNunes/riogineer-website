"""M16 one-source/valve/sink serialization; no general network energy solve."""
from copy import deepcopy
import uuid
from .network_models import equipment_result, state_from_rates, MODELS
from .streams import unavailable_properties


def calculate(f):
    from .core import semantic_hash, implementation_hash, EVALUATOR_HASH, Invalid, validate_schema
    from .network import validate, mass_balance, MODEL
    from .throttling_valve_energy import ValveFailure
    validate(f)
    unit = f['equipment'][0]
    inlet_link = next(c for c in f['connections'] if c['target']['owner_id'] == unit['id'])
    outlet_link = next(c for c in f['connections'] if c['source']['owner_id'] == unit['id'])
    source = next(s for s in f['streams'] if s['id'] == inlet_link['stream_id'])['specified_state']
    feed = state_from_rates(deepcopy(source['component_mass_flow_kg_h']), source['temperature_K'], source['pressure_Pa_abs'], None)
    try:
        executed = equipment_result(MODELS['throttling_valve']['execute'](unit, {'inlet':feed}, None))
    except ValveFailure as error:
        diagnostic = getattr(error.diagnostics, 'reason', error.diagnostics)
        raise Invalid(f'{unit["id"]}: {error.stage}: {error.status}; {diagnostic}', code='CALCULATION_FAILED') from error
    d = executed.details['thermodynamics']
    feed['enthalpy_flow_W'] = d['F_mol_s']*d['inlet']['H_eq_J_mol']
    outlet = executed.streams['outlet']
    balance = mass_balance([feed], [outlet], f['components'])
    states = {inlet_link['stream_id']:feed,outlet_link['stream_id']:outlet}
    for state in states.values():state['properties'] = unavailable_properties()
    result = dict(schema_version='1.10',process_result_version='1.10',kind='results',case_id=f['case_id'],
        run_id=str(uuid.uuid4()),input_sha256=semantic_hash(f),requirements_sha256=f['requirements_sha256'],
        engine=dict(version='1.9.0',implementation_sha256=implementation_hash(),evaluator_sha256=EVALUATOR_HASH,model=MODEL),
        status='completed',units=f['units'],streams=states,
        equipment=[dict(id=unit['id'],type='throttling_valve',model=unit['model'],
                        material_streams=dict(inlet=inlet_link['stream_id'],outlet=outlet_link['stream_id']),
                        mass_balance=balance,energy_residual_W=d['energy_residual_W'],thermodynamics=d)],
        execution=dict(method='topological',equipment_order=[unit['id']]),
        balances=dict(mass=balance,energy=dict(status='passed',residual_W=d['energy_residual_W'],
            tolerance_W=d['energy_allowance_W'],model='rigorous_isenthalpic_pr')),
        warnings=[],limitations=[
            'Single-phase methane/n_hexane inlet, explicit constant zero kij, 200–500 K qualified matrix only.',
            'One overall equilibrium outlet, including VL; internal phases are not separate material streams.',
            'Specified outlet pressure; no flow prediction, sizing, Cv/Kv, choking, cavitation, erosion or non-equilibrium flashing.',
            'Adiabatic isenthalpic model neglects kinetic/potential energy; no power, efficiency or heat duty.',
            'One source -> valve -> sink; no recycle convergence or network pressure solution.'],
        unavailable=[dict(calculation='Valve sizing and hydraulic flow prediction',status='not calculated',
                         reason='M16 qualifies equilibrium isenthalpic outlet state only.')])
    validate_schema('results',result)
    return result
