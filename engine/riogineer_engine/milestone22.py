"""Two explicitly selected PT200 application references; no endpoint tables."""
from copy import deepcopy
from .milestone20 import requirements as historical
from .separator_pump_scope import PT200_CASES,PT200_MODEL


def requirements(case='PT_BUBBLE_BELOW'):
    row=next((r for r in PT200_CASES if r['qualification_id']==case+'_8MPA_PT200'),None)
    if row is None:raise ValueError('Unknown M22 reference')
    r=historical(case+'_DP1000000.0')
    r.update(schema_version='1.13',case_id='MILESTONE_22_'+case)
    r['feeds'][0]['state']=deepcopy(row['recipe']['feed'])
    r['equipment'][1]['model']=deepcopy(PT200_MODEL)
    r['equipment'][1]['parameters'].update(outlet_pressure_Pa_abs=row['outlet_pressure_Pa_abs'],
        isentropic_efficiency=row['isentropic_efficiency'],numerical_profile=row['numerical_profile'])
    r['provenance']=dict(source='M22 finite cold-source reference; explicit PT200 pump selection.',basis='qualified_equilibrium_energy')
    return r


if __name__=='__main__':
    import argparse,json
    from .core import build_flowsheet,calculate,Invalid
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE'],default='PT_BUBBLE_BELOW');p.add_argument('--calculate',action='store_true');p.add_argument('--unsupported',action='store_true');a=p.parse_args()
    r=requirements(a.case)
    if a.unsupported:r['equipment'][1]['parameters']['isentropic_efficiency']=.81
    try:result=calculate(build_flowsheet(r)) if a.calculate else r
    except Invalid as e:
        print(json.dumps(e.payload,indent=2));raise SystemExit(1)
    print(json.dumps(result,indent=2,allow_nan=False))
