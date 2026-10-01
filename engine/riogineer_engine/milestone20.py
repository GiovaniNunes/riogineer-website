"""Input-only M20 demonstrations. All separator/pump outputs are runtime calculations."""
from copy import deepcopy
from .milestone17 import requirements as separator_requirements
from .separator_pump_scope import CASES,MODEL

def requirements(case='PH_FLASH_DP1000000.0'):
    row=next((c for c in CASES if c['qualification_id']==case),None)
    if row is None:raise ValueError('Unknown M20 demonstration')
    recipe=row['recipe'];feed=recipe['feed']
    r=separator_requirements(mode=recipe['mode'],Pout=recipe['separator_pressure_Pa_abs'],Tout=recipe.get('separator_temperature_K',350.))
    r.update(schema_version='1.12',profile='separator_pump_energy',case_id='MILESTONE_20_'+case.replace('.', '_'))
    r['feeds'][0]['state']=deepcopy(feed)
    sep=r['equipment'][0]
    r['equipment'].append(dict(id='PUMP_1',type='pump',model=deepcopy(MODEL),parameters={
        'property_package':sep['parameters']['property_package'],'bip':deepcopy(sep['parameters']['bip']),
        'outlet_pressure_Pa_abs':row['outlet_pressure_Pa_abs'],'isentropic_efficiency':row['isentropic_efficiency']}))
    liquid=next(c for c in r['connections'] if c['source']==dict(owner_id=sep['id'],port_id='liquid'))
    sink=deepcopy(liquid['target']);liquid['target']=dict(owner_id='PUMP_1',port_id='inlet')
    r['streams'].append(dict(id='PUMP_PRODUCT',service='PUMP_PRODUCT'))
    r['connections'].append(dict(id='PUMP_TO_PRODUCT',stream_id='PUMP_PRODUCT',source=dict(owner_id='PUMP_1',port_id='outlet'),target=sink))
    r['provenance']=dict(source='M20 qualified separator-liquid integration; explicit input tuple.',basis='qualified_equilibrium_energy')
    return r

if __name__=='__main__':
    import argparse,json
    from .core import build_flowsheet,calculate
    p=argparse.ArgumentParser();p.add_argument('--case',default='PH_FLASH_DP1000000.0');p.add_argument('--calculate',action='store_true');p.add_argument('--unsupported',action='store_true');a=p.parse_args()
    r=requirements(a.case)
    if a.unsupported:r['equipment'][1]['parameters']['outlet_pressure_Pa_abs']=8e6
    print(json.dumps(calculate(build_flowsheet(r)) if a.calculate else r,indent=2,allow_nan=False))
