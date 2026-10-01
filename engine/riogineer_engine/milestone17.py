"""Reproducible M17 PT/PH demonstrations using stable M9 ports and stream IDs."""
from .milestone9 import requirements as historical
from .components import component
from .separator_energy import MODEL


def requirements(mode='specified_temperature', Pin=3e7, Tin=300., Pout=3e5, F=100., z=(.5,.5), Tout=350.):
    r=historical();r.update(schema_version='1.9',profile='separator_energy',case_id='MILESTONE_17_'+mode.upper())
    r['provenance']=dict(source='Independent Pre-M17 separator energy benchmark; explicit zero kij mathematical reference.',basis='qualified_equilibrium_energy')
    r['required_outputs']=['streams','mass_balance','energy_balance']
    r['feeds'][0]['state']=dict(temperature_K=Tin,pressure_Pa_abs=Pin,component_mass_flow_kg_h={i:F*q*component(i).molecular_weight*3.6 for i,q in zip(r['components'],z)})
    unit=r['equipment'][0];unit['model']=dict(MODEL)
    unit['parameters'].update(mode=mode,separator_pressure_Pa_abs=Pout)
    if mode=='specified_temperature':unit['parameters']['separator_temperature_K']=Tout
    return r


if __name__=='__main__':
    import argparse,json
    from .core import build_flowsheet,calculate
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['specified_temperature','adiabatic'],default='specified_temperature');p.add_argument('--calculate',action='store_true');a=p.parse_args()
    r=requirements(a.mode,Pout=1e6 if a.mode=='adiabatic' else 3e5)
    print(json.dumps(calculate(build_flowsheet(r)) if a.calculate else r,indent=2))
