"""M12 single-equipment process serialization; no network energy solver."""
from copy import deepcopy
import uuid
from .network_models import equipment_result, state_from_rates, MODELS
from .streams import unavailable_properties


def calculate(f):
    from .core import semantic_hash, implementation_hash, EVALUATOR_HASH, Invalid, validate_schema
    from .network import validate, mass_balance, MODEL
    from .heater_cooler_energy import ThermalFailure
    validate(f)
    unit = f['equipment'][0]
    inlet_link = next(c for c in f['connections'] if c['target']['owner_id'] == unit['id'])
    outlet_link = next(c for c in f['connections'] if c['source']['owner_id'] == unit['id'])
    source = next(s for s in f['streams'] if s['id'] == inlet_link['stream_id'])['specified_state']
    feed = state_from_rates(deepcopy(source['component_mass_flow_kg_h']), source['temperature_K'], source['pressure_Pa_abs'], None)
    try:
        result = equipment_result(MODELS['heater']['execute'](unit, {'inlet': feed}, None))
    except ThermalFailure as error:
        raise Invalid(f'{unit["id"]}: {error}', code='CALCULATION_FAILED') from error
    details = result.details['thermodynamics']
    feed['enthalpy_flow_W'] = details['F_mol_s'] * details['inlet']['H_eq_J_mol']
    outlet = result.streams['outlet']
    balance = mass_balance([feed], [outlet], f['components'])
    states = {inlet_link['stream_id']: feed, outlet_link['stream_id']: outlet}
    for state in states.values():
        state['properties'] = unavailable_properties()
    output = dict(schema_version='1.7', process_result_version='1.7', kind='results', case_id=f['case_id'],
        run_id=str(uuid.uuid4()), input_sha256=semantic_hash(f), requirements_sha256=f['requirements_sha256'],
        engine=dict(version='1.6.0', implementation_sha256=implementation_hash(), evaluator_sha256=EVALUATOR_HASH, model=MODEL),
        status='completed', units=f['units'], streams=states,
        equipment=[dict(id=unit['id'], type='heater', model=unit['model'], duty_W=result.duty_W, work_W=0.,
            mass_balance=balance, energy_residual_W=details['energy_residual_W'], thermodynamics=details)],
        execution=dict(method='topological', equipment_order=[unit['id']]),
        balances=dict(mass=balance, energy=dict(status='passed', residual_W=details['energy_residual_W'],
            tolerance_W=details['energy_allowance_W'], duty_W=result.duty_W,
            model='equilibrium_energy_balance_pr', positive_duty='heat_into_process')),
        warnings=[], limitations=[
            'One-stream methane/n_hexane equilibrium energy balance with explicit zero kij only.',
            'Outlet pressure is specified; no hydraulic, utility-side, exchanger sizing or network energy solver.',
            'Water, VLLE, critical/retrograde behavior and pure coexistence interpolation remain unqualified.'],
        unavailable=[dict(calculation='Heat-transfer sizing and hydraulic pressure drop', status='not calculated',
            reason='M12 qualifies steady-state duty and equilibrium outlet state only.')])
    validate_schema('results', output)
    return output
