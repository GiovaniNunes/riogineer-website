"""M20 input-only qualification set; exact cases, never a thermodynamic output table."""
import json
from copy import deepcopy
from math import isfinite
from pathlib import Path
from sys import float_info
from .separator_energy import MODEL as SEPARATOR_MODEL, parameters as separator_parameters

MODEL={'id':'separator_liquid_pump_pr','version':'1.0'}
CASES=tuple(json.loads(Path(__file__).with_name('separator_pump_cases.json').read_text()))
PT200_MODEL={'id':'separator_liquid_pump_pr','version':'2.0'}
PT200_CASES=tuple(json.loads(Path(__file__).with_name('separator_pump_pt200_cases.json').read_text()))
ROUND=64*float_info.epsilon

def same(a,b):
    if isinstance(b,dict):return isinstance(a,dict) and set(a)==set(b) and all(same(a[k],v) for k,v in b.items())
    if isinstance(b,(float,int)):
        return isinstance(a,(float,int)) and not isinstance(a,bool) and isfinite(a) and abs(a-b)<=ROUND*max(1.,abs(b))
    return a==b

def layout(f):
    """Validated graph role resolution; no labels authorize support."""
    eq=f['equipment'];boundaries=f['boundaries'];links=f['connections']
    sep=[u for u in eq if u['type']=='equilibrium_separator_2phase'];pump=[u for u in eq if u['type']=='pump']
    src=[b for b in boundaries if b['type']=='source'];sinks=[b for b in boundaries if b['type']=='sink']
    if len(eq)!=2 or len(sep)!=1 or len(pump)!=1 or len(src)!=1 or len(sinks)!=2 or len(links)!=4:
        raise ValueError('M20 topology: one source, one separator, one pump and two sinks required')
    sep,pump=sep[0],pump[0]
    if sep['model']!=SEPARATOR_MODEL or pump['model']!=(PT200_MODEL if f['schema_version']=='1.14' else MODEL):raise ValueError('M20 model identity mismatch')
    def link(owner,port):
        return next(c for c in links if c['source']==dict(owner_id=owner,port_id=port))
    feed=link(src[0]['id'],'outlet');liquid=link(sep['id'],'liquid');vapor=link(sep['id'],'vapor');product=link(pump['id'],'outlet')
    sink_ids={b['id'] for b in sinks}
    if feed['target']!=dict(owner_id=sep['id'],port_id='inlet') or liquid['target']!=dict(owner_id=pump['id'],port_id='inlet') or {vapor['target']['owner_id'],product['target']['owner_id']}!=sink_ids:
        raise ValueError('M20 topology: separator liquid must feed pump; vapor and pumped liquid go to separate sinks')
    return sep,pump,feed,liquid,vapor,product

def specification(f):
    sep,pump,feed,*_=layout(f);p=sep['operating_parameters'];separator_parameters(p)
    q=pump['operating_parameters']
    if set(q)!=({'outlet_pressure_Pa_abs','isentropic_efficiency','property_package','bip'} | ({'numerical_profile'} if pump['model']==PT200_MODEL else set())):raise ValueError('M20 pump parameters')
    if q['property_package']!=p['property_package'] or q['bip']!=p['bip']:raise ValueError('M20 incompatible thermodynamic basis')
    source=next(s['specified_state'] for s in f['streams'] if s['id']==feed['stream_id'])
    recipe=dict(feed=deepcopy(source),mode=p['mode'],separator_pressure_Pa_abs=p['separator_pressure_Pa_abs'])
    if p['mode']=='specified_temperature':recipe['separator_temperature_K']=p['separator_temperature_K']
    actual=dict(recipe=recipe,outlet_pressure_Pa_abs=q['outlet_pressure_Pa_abs'],isentropic_efficiency=q['isentropic_efficiency'])
    if pump['model']==PT200_MODEL:
        from .numerical_profiles import NumericalProfile,resolve_pt_settings
        if q['numerical_profile']!=NumericalProfile.PT200.value:raise ValueError('M22 explicit PT200 profile required')
        resolve_pt_settings(q['numerical_profile'])
        actual['numerical_profile']=q['numerical_profile']
    return actual

def qualify(f):
    actual=specification(f)
    for row in (PT200_CASES if 'numerical_profile' in actual else CASES):
        # Discharge and efficiency are exact; only recipe representation noise is recognized.
        if actual['outlet_pressure_Pa_abs']==row['outlet_pressure_Pa_abs'] and actual['isentropic_efficiency']==row['isentropic_efficiency'] and same(actual['recipe'],row['recipe']):
            return row['qualification_id']
    if 'numerical_profile' in actual:raise ValueError('M22 unsupported_qualified_tuple: only the two recorded cold-source recipes at 8 MPa and efficiency 0.8 with explicit PT200 are supported')
    raise ValueError('M20 unsupported_qualified_tuple: only the 30 listed source/Pout/efficiency combinations are supported; 8 MPa PS failures are excluded')
