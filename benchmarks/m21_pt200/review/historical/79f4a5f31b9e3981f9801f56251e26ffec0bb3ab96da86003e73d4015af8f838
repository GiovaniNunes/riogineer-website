"""Explicit contradictory/missing source scenarios; no thermodynamic expectations."""
from copy import deepcopy
from .adapter import representation,identity

def cases(source):
    base=representation(source);out=[]
    def add(name,change,category='contradictory_evidence'):
        s,r,c=deepcopy(base),deepcopy(source),identity(source);change(s,r,c)
        out.append(dict(case_id=name,stream=s,source=r,current=c,expected_category=category))
    add('missing_context',lambda s,r,c:s.pop('state_context'),'missing_evidence')
    add('missing_run',lambda s,r,c:s['state_context']['source'].pop('run_id'),'missing_evidence')
    add('missing_parent',lambda s,r,c:r['equipment'][0]['thermodynamics'].pop('outlet'),'missing_evidence')
    add('missing_H',lambda s,r,c:s.update(enthalpy_flow_W=None),'missing_evidence')
    add('stale_current_run',lambda s,r,c:c.update(run_id='new-calculation'))
    add('mismatched_input',lambda s,r,c:s['state_context']['source'].update(input_sha256='different-input'))
    add('wrong_port',lambda s,r,c:s['state_context']['source'].update(port_id='vapor'))
    add('wrong_stream',lambda s,r,c:s['state_context']['source'].update(stream_id='VAPOR_PRODUCT'))
    add('wrong_phase',lambda s,r,c:s['state_context'].update(phase='vapor'))
    add('independent_H_spec',lambda s,r,c:s['state_context'].update(specification_kind='independent_caloric'))
    add('independent_PT_spec',lambda s,r,c:s['state_context'].update(specification_kind='independent_PT'))
    add('T_changed',lambda s,r,c:s.update(temperature_K=s['temperature_K']+.01))
    add('P_changed',lambda s,r,c:s.update(pressure_Pa_abs=s['pressure_Pa_abs']+10))
    add('rate_changed',lambda s,r,c:s['component_mass_flow_kg_h'].update(methane=s['component_mass_flow_kg_h']['methane']+.001))
    add('total_changed',lambda s,r,c:s.update(mass_flow_kg_h=s['mass_flow_kg_h']+.001))
    add('composition_changed',lambda s,r,c:s['properties']['molar_composition']['value'].update(methane=.5))
    add('molar_flow_changed',lambda s,r,c:s['properties']['molar_flow'].update(value=1.))
    add('H_changed',lambda s,r,c:s.update(enthalpy_flow_W=s['enthalpy_flow_W']+1.))
    add('units_changed',lambda s,r,c:s['properties']['molar_flow'].update(unit='mol/s'))
    add('extra_conflicting_units',lambda s,r,c:s.update(units={'pressure':'bar'}))
    add('extra_independent_entropy',lambda s,r,c:s.update(entropy_J_mol_K=10.))
    add('source_units_changed',lambda s,r,c:r['units'].update(pressure='bar'))
    add('reference_changed',lambda s,r,c:s['state_context']['thermodynamics'].update(caloric_reference='different-zero'))
    add('kij_changed',lambda s,r,c:s['state_context']['thermodynamics']['bip']['values'][0].__setitem__(1,.01))
    add('package_changed',lambda s,r,c:s['state_context']['thermodynamics'].update(property_package='other'))
    add('component_dataset_changed',lambda s,r,c:s['state_context']['thermodynamics'].update(component_dataset='other'))
    def coherent_forgery(s,r,c):
        # Even matching provenance/stream copies cannot overrule fresh calorics.
        e=r['equipment'][0];p=e['thermodynamics']['outlet'];sid=e['material_streams']['liquid']
        h=p['phases']['liquid']['h_J_mol']+10.;F=e['thermodynamics']['phases']['liquid']['molar_flow_mol_s']
        p['phases']['liquid']['h_J_mol']=h
        e['thermodynamics']['phases']['liquid']['h_J_mol']=h
        s['enthalpy_flow_W']=r['streams'][sid]['enthalpy_flow_W']=F*h
        e['thermodynamics']['phases']['liquid']['enthalpy_flow_W']=F*h
    add('coherent_forged_upstream_H',coherent_forgery)
    return out
