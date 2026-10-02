"""M14 one-source/compressor/sink serialization; no general network energy solve."""
from copy import deepcopy
import uuid
from .network_models import equipment_result, state_from_rates, MODELS
from .streams import unavailable_properties


def calculate(f):
    from .core import semantic_hash, implementation_hash, EVALUATOR_HASH, Invalid, validate_schema
    from .network import validate, mass_balance, MODEL
    from .compressor_energy import CompressorFailure
    validate(f)
    unit = f['equipment'][0]
    inlet_link = next(c for c in f['connections'] if c['target']['owner_id'] == unit['id'])
    outlet_link = next(c for c in f['connections'] if c['source']['owner_id'] == unit['id'])
    source = next(s for s in f['streams'] if s['id'] == inlet_link['stream_id'])['specified_state']
    feed = state_from_rates(deepcopy(source['component_mass_flow_kg_h']), source['temperature_K'], source['pressure_Pa_abs'], None)
    try:
        executed = equipment_result(MODELS['compressor']['execute'](unit, {'inlet':feed}, None))
    except CompressorFailure as error:
        raise Invalid(f'{unit["id"]}: {error}', code='CALCULATION_FAILED') from error
    d = executed.details['thermodynamics']
    feed['enthalpy_flow_W'] = d['F_mol_s']*d['inlet']['H_eq_J_mol']
    outlet = executed.streams['outlet']
    balance = mass_balance([feed], [outlet], f['components'])
    states = {inlet_link['stream_id']:feed,outlet_link['stream_id']:outlet}
    for state in states.values():state['properties'] = unavailable_properties()
    result = dict(schema_version='1.8',process_result_version='1.8',kind='results',case_id=f['case_id'],
        run_id=str(uuid.uuid4()),input_sha256=semantic_hash(f),requirements_sha256=f['requirements_sha256'],
        engine=dict(version='1.7.0',implementation_sha256=implementation_hash(),evaluator_sha256=EVALUATOR_HASH,model=MODEL),
        status='completed',units=f['units'],streams=states,
        equipment=[dict(id=unit['id'],type='compressor',model=unit['model'],duty_W=0.,work_W=executed.work_W,
                        mass_balance=balance,energy_residual_W=d['energy_residual_W'],thermodynamics=d)],
        execution=dict(method='topological',equipment_order=[unit['id']]),
        balances=dict(mass=balance,energy=dict(status='passed',residual_W=d['energy_residual_W'],
            tolerance_W=d['energy_allowance_W'],duty_W=0.,fluid_power_W=d['fluid_power_W'],
            model='rigorous_isentropic_pr',positive_work='work_into_process')),
        warnings=[],limitations=[
            'One adiabatic vapor-service methane/n_hexane PR compressor with explicit constant zero kij, 200–500 K only.',
            'Liquid/VL compressor service, water, arbitrary mixtures/nonzero BIPs and coexistence interpolation are unqualified.',
            'Fluid power enters the material stream; no mechanical, motor, driver or gearbox losses.',
            'No maps, polytropic model, sizing, stages, intercooling, recycle or network pressure solution.'],
        unavailable=[dict(calculation='Driver power and compressor sizing',status='not calculated',
                         reason='M14 qualifies thermodynamic fluid power and vapor outlet state only.')])
    validate_schema('results',result)
    return result
