"""M17 one-source/separator/two-sink serialization; no general network energy solve."""
from copy import deepcopy
import uuid
from .network_models import equipment_result, state_from_rates, MODELS
from .streams import unavailable_properties
from .thermodynamics import MolecularCompositionProvider, quantity


def calculate(f):
    from .core import semantic_hash, implementation_hash, EVALUATOR_HASH, Invalid, validate_schema
    from .network import validate, mass_balance, MODEL
    from .separator_energy import SeparatorFailure
    validate(f)
    unit = f['equipment'][0]
    inlet_link = next(c for c in f['connections'] if c['target']['owner_id'] == unit['id'])
    outlet_links = {c['source']['port_id']:c for c in f['connections'] if c['source']['owner_id'] == unit['id']}
    source = next(s for s in f['streams'] if s['id'] == inlet_link['stream_id'])['specified_state']
    feed = state_from_rates(deepcopy(source['component_mass_flow_kg_h']), source['temperature_K'], source['pressure_Pa_abs'], None)
    try:
        executed = equipment_result(MODELS['equilibrium_separator_2phase']['execute'](unit, {'inlet':feed}, None))
    except SeparatorFailure as error:
        diagnostic = str(error)
        raise Invalid(f'{unit["id"]}: {error.stage}: {error.status}; {diagnostic}', code='CALCULATION_FAILED') from error
    d = executed.details['thermodynamics']
    feed['enthalpy_flow_W'] = d['F_mol_s']*d['inlet']['H_eq_J_mol']
    balance = mass_balance([feed], list(executed.streams.values()), f['components'])
    states = {inlet_link['stream_id']:feed, **{outlet_links[k]['stream_id']:v for k,v in executed.streams.items()}}
    molecular = MolecularCompositionProvider()
    for state in states.values():
        composition = molecular.enrich(state).composition
        state['properties'] = unavailable_properties()
        state['properties'].update(
            molar_flow=quantity(composition.molar_flow_kmol_h, 'kmol/h'),
            molecular_mass=quantity(composition.molecular_weight_kg_kmol, 'kg/kmol'),
            molar_composition=quantity(dict(composition.molar_fractions)
                if composition.molar_fractions is not None else None, 'mol/mol'))
    result = dict(schema_version='1.11',process_result_version='1.11',kind='results',case_id=f['case_id'],
        run_id=str(uuid.uuid4()),input_sha256=semantic_hash(f),requirements_sha256=f['requirements_sha256'],
        engine=dict(version='1.10.0',implementation_sha256=implementation_hash(),evaluator_sha256=EVALUATOR_HASH,model=MODEL),
        status='completed',units=f['units'],streams=states,
        equipment=[dict(id=unit['id'],type='equilibrium_separator_2phase',model=unit['model'],
                        material_streams=dict(inlet=inlet_link['stream_id'],**{k:v['stream_id'] for k,v in outlet_links.items()}),
                        duty_W=executed.duty_W,work_W=0.,
                        mass_balance=balance,energy_residual_W=d['energy_residual_W'],thermodynamics=d)],
        execution=dict(method='topological',equipment_order=[unit['id']]),
        balances=dict(mass=balance,energy=dict(status='passed',residual_W=d['energy_residual_W'],
            tolerance_W=d['energy_allowance_W'],model='equilibrium_separator_energy_pr',duty_W=executed.duty_W,positive_duty='heat_into_equipment')),
        warnings=[],limitations=[
            'Methane/n_hexane, explicit constant zero kij, 200–500 K; qualified frozen matrix only.',
            'PT-defined positive-flow inlet; L/V/VL inlet and outlet states within independently qualified scope.',
            'PT mode calculates duty; adiabatic PH imposes zero duty. No shaft work or kinetic/potential energy changes.',
            'Specified equal/reduced pressure; no hydraulics, vessel sizing, entrainment or separation-efficiency prediction.',
            'One source -> separator -> vapor and liquid sinks; no mixed rigorous network, water, recycles or three-phase qualification.'],
        unavailable=[dict(calculation='Vessel sizing and entrainment',status='not calculated',reason='M17 qualifies equilibrium separation and energy only.')])
    validate_schema('results',result)
    return result
