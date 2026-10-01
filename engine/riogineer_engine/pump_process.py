"""M18 one-source/pump/sink serialization; no general network energy solve."""
from copy import deepcopy
import uuid
from .network_models import equipment_result, state_from_rates, MODELS
from .streams import unavailable_properties


def calculate(f):
    from .core import semantic_hash, implementation_hash, EVALUATOR_HASH, Invalid, validate_schema
    from .network import validate, mass_balance, MODEL
    from .pump_energy import PumpFailure
    validate(f)
    unit = f['equipment'][0]
    inlet_link = next(c for c in f['connections'] if c['target']['owner_id'] == unit['id'])
    outlet_link = next(c for c in f['connections'] if c['source']['owner_id'] == unit['id'])
    source = next(s for s in f['streams'] if s['id'] == inlet_link['stream_id'])['specified_state']
    feed = state_from_rates(deepcopy(source['component_mass_flow_kg_h']), source['temperature_K'], source['pressure_Pa_abs'], None)
    try:
        executed = equipment_result(MODELS['pump']['execute'](unit, {'inlet':feed}, None))
    except PumpFailure as error:
        raise Invalid(f'{unit["id"]}: {error}', code='CALCULATION_FAILED') from error
    d = executed.details['thermodynamics']
    feed['enthalpy_flow_W'] = d['F_mol_s']*d['inlet']['H_eq_J_mol']
    outlet = executed.streams['outlet']
    balance = mass_balance([feed], [outlet], f['components'])
    states = {inlet_link['stream_id']:feed,outlet_link['stream_id']:outlet}
    from .thermodynamics import MolecularCompositionProvider, quantity
    for state in states.values():
        c = MolecularCompositionProvider().enrich(state).composition
        state['properties'] = unavailable_properties()
        state['properties'].update(molar_flow=quantity(c.molar_flow_kmol_h,'kmol/h'),
            molecular_mass=quantity(c.molecular_weight_kg_kmol,'kg/kmol'),
            molar_composition=quantity(dict(c.molar_fractions),'mol/mol'))
    result = dict(schema_version='1.12',process_result_version='1.12',kind='results',case_id=f['case_id'],
        run_id=str(uuid.uuid4()),input_sha256=semantic_hash(f),requirements_sha256=f['requirements_sha256'],
        engine=dict(version='1.11.0',implementation_sha256=implementation_hash(),evaluator_sha256=EVALUATOR_HASH,model=MODEL),
        status='completed',units=f['units'],streams=states,
        equipment=[dict(id=unit['id'],type='pump',model=unit['model'],duty_W=0.,work_W=executed.work_W,
                        material_streams=dict(inlet=inlet_link['stream_id'],outlet=outlet_link['stream_id']),
                        mass_balance=balance,energy_residual_W=d['energy_residual_W'],thermodynamics=d)],
        execution=dict(method='topological',equipment_order=[unit['id']]),
        balances=dict(mass=balance,energy=dict(status='passed',residual_W=d['energy_residual_W'],
            tolerance_W=d['energy_allowance_W'],duty_W=0.,fluid_power_W=d['fluid_power_W'],
            model='rigorous_isentropic_pump_pr',positive_work='work_into_process')),
        warnings=[],limitations=[
            'Fixed equimolar methane/n_hexane, explicit constant zero kij; Tin 300–350 K, Pin 20–25 MPa absolute.',
            'Pout equals Pin exactly or Pin+10000 Pa <= Pout <= 30 MPa; eta 0.6–1; flow 5–200 mol/s.',
            'All actual states 300–370 K and 20–30 MPa; fresh auxiliary stable-liquid witnesses at 16 MPa.',
            'Work screening is an engineering numerical allowance, not certified uncertainty or experimental validation.',
            'The energy balance is algebraic consistency; independent comparisons supply separate accuracy evidence.',
            'One source -> pump -> sink; no sizing, head, curves, NPSH, cavitation prediction or mechanical/electrical losses.'],
        unavailable=[dict(calculation='Electrical power, pump sizing and cavitation safety',status='not calculated',
                         reason='M18 qualifies thermodynamic fluid power within guarded liquid scope only.')])
    validate_schema('results',result)
    return result
