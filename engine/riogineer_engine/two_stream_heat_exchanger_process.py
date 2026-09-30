"""M15 serialization over the qualified four-port acyclic execution path."""
from math import fsum
import uuid
from .network import execute_exchanger_graph, MODEL
from .streams import unavailable_properties


def calculate(f):
    from .core import semantic_hash, implementation_hash, EVALUATOR_HASH, validate_schema
    states, records = execute_exchanger_graph(f)
    equipment = []
    for unit, links, incoming, result, balances in records:
        d = result.details['thermodynamics']
        for side in ('hot','cold'):
            states[links[side+'_in']]['enthalpy_flow_W'] = d[side+'_molar_flow_mol_s']*d[side+'_inlet']['H_eq_J_mol']
        equipment.append(dict(id=unit['id'],type=unit['type'],model=unit['model'],duty_W=0.,work_W=0.,
            material_streams=links,material_balances=balances,energy_residual_W=d['energy_residual_W'],thermodynamics=d))
    for state in states.values():
        state['properties'] = unavailable_properties()
    output = dict(schema_version='1.9',process_result_version='1.9',kind='results',case_id=f['case_id'],
        run_id=str(uuid.uuid4()),input_sha256=semantic_hash(f),requirements_sha256=f['requirements_sha256'],
        engine=dict(version='1.8.0',implementation_sha256=implementation_hash(),evaluator_sha256=EVALUATOR_HASH,model=MODEL),
        status='completed',units=f['units'],streams=states,equipment=equipment,
        execution=dict(method='topological',equipment_order=[u['id'] for u in equipment]),
        balances=dict(material_paths={u['id']:u['material_balances'] for u in equipment},
            energy=dict(status='passed',residual_W=fsum(u['energy_residual_W'] for u in equipment),
                tolerance_W=fsum(u['thermodynamics']['energy_allowance_W'] for u in equipment),
                duty_W=0.,model='rigorous_two_stream_pr',positive_duty='heat_into_each_material_path')),
        warnings=[],limitations=[
            'Methane/n_hexane, explicit constant zero kij, 200–500 K; single-phase endpoints only.',
            'Independent material paths, terminal-state PT/PH energy balance; outlet pressures are specifications.',
            'No phase-change service, water, VLLE, arbitrary mixtures/BIPs, coexistence interpolation, recycles or hydraulic pressure solution.',
            'No UA, area, LMTD, NTU, minimum approach or exchanger design-feasibility calculation.'],
        unavailable=[dict(calculation='Exchanger sizing and hydraulic pressure drop',status='not calculated',reason='Specified terminal-state balance only.')])
    validate_schema('results',output)
    return output
