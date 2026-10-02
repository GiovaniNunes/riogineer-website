"""Deterministic M18 requirements/CLI; no frozen evidence in production runtime."""
from .milestone17 import requirements as separator_requirements
from .components import component
from .pump_energy import MODEL


def requirements(Tin=300., Pin=20e6, Pout=30e6, eta=.8, F=100., z=(.5,.5)):
    r=separator_requirements()
    r.update(schema_version='1.10',profile='pump_energy',case_id='MILESTONE_18_LIQUID_PUMP')
    r['provenance']['source']='M18 guarded liquid pump deterministic reference; explicit constant zero kij.'
    r['feeds'][0]['state']=dict(temperature_K=Tin,pressure_Pa_abs=Pin,
        component_mass_flow_kg_h={i:F*q*component(i).molecular_weight*3.6 for i,q in zip(r['components'],z)})
    bip=r['equipment'][0]['parameters']['bip']
    r['equipment']=[dict(id='PUMP_1',type='pump',model=dict(MODEL),parameters=dict(
        property_package='peng_robinson@1.0',bip=bip,outlet_pressure_Pa_abs=Pout,isentropic_efficiency=eta))]
    r['sinks']=[dict(id='PRODUCT_SINK')]
    r['streams']=[dict(id='HYDROCARBON_FEED',service='HYDROCARBON_FEED'),dict(id='PUMP_PRODUCT',service='PUMP_PRODUCT')]
    r['connections']=[dict(id='C_FEED',stream_id='HYDROCARBON_FEED',source=dict(owner_id='HYDROCARBON_FEED',port_id='outlet'),target=dict(owner_id='PUMP_1',port_id='inlet')),
        dict(id='C_PRODUCT',stream_id='PUMP_PRODUCT',source=dict(owner_id='PUMP_1',port_id='outlet'),target=dict(owner_id='PRODUCT_SINK',port_id='inlet'))]
    return r


if __name__=='__main__':
    import argparse,json
    from .core import build_flowsheet,calculate
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['canonical','identity','off_grid','flow','floor','sub_floor'],default='canonical')
    p.add_argument('--calculate',action='store_true');a=p.parse_args()
    edits={'canonical':{},'identity':dict(Pout=20e6),'off_grid':dict(Tin=306.85,Pin=23655000.,Pout=26313555.,eta=.7132),
           'flow':dict(F=50.),'floor':dict(Pout=20010000.),'sub_floor':dict(Pout=20001000.)}
    r=requirements(**edits[a.mode])
    print(json.dumps(calculate(build_flowsheet(r)) if a.calculate else r,indent=2))
