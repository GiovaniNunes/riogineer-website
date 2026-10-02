"""Fixed finite study inputs and read-only artifact support; no thermodynamics."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
PRIOR=ROOT/'benchmarks/configurable_separator_pump'
CAPS=(100,200,400);IDS=('methane','n_hexane')
def encode(v):return json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n'
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashed(v):return hashlib.sha256(encode(v).encode()).hexdigest()
def save(name,v,write=False):
    p=HERE/name;raw=encode(v)
    if write:
        assert not p.exists(),'Refuse overwrite '+str(p)
        p.write_text(raw)
    else:assert p.read_text()==raw,name+' reproduction differs'
    print(name,digest(p),flush=True)
def sources():
    old=read(PRIOR/'sources.json')
    return {n:old[n]['inputs'] for n in ('PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE','PH_FLASH','PT_VL_HEATING','PT_DEW_BELOW')}
def pt_cases():
    old=read(PRIOR/'sources.json');rows=[]
    for n in ('PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE'):
        z=list(old[n]['result']['equipment'][0]['thermodynamics']['phases']['liquid']['composition'].values())
        for p in (7e6,7.5e6,7.8e6,8e6):
            for k in (55,56):
                for dt in (-.05,0.,.05):rows.append(dict(case_id=f'{n}_{p}_{k}_{dt}',group='failure_region',T=200+300*k/63+dt,P=p,z=z))
    holdouts=[(460.37,7.61e6,.4937),(464.23,7.83e6,.5063),(468.19,7.97e6,.5017),(470.11,7.69e6,.4873),(462.77,8.03e6,.4981),(466.13,7.37e6,.5129)]
    for j,(t,p,x) in enumerate(holdouts):rows.append(dict(case_id=f'HOLDOUT_{j}',group='holdout',T=t,P=p,z=[x,1-x]))
    for name,t,p in [('LIQUID',300.,3e7),('VAPOR',300.,1e3),('VL',300.,3e5)]:rows.append(dict(case_id=name,group='anchor',T=t,P=p,z=[.5,.5]))
    b=read(ROOT/'benchmarks/peng_robinson_pt_boundary/methane_nhexane_pt_boundary_reference.json')
    for c in b['bubble_cases']:
        if c['case_id'] in ('BUBBLE_STABLE_231_10','BUBBLE_PLUS_0_1MK','BUBBLE_CENTER'):
            s=c['reference'];rows.append(dict(case_id=c['case_id'],group='bubble',T=s['T_K'],P=s['P_Pa_abs'],z=s['z']))
    for name in ('PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE','PT_DEW_BELOW'):
        i=old[name]['inputs'];rows.append(dict(case_id=name+'_PARENT',group='source_boundary',T=i['Tout'],P=i['Pout'],z=i['z']))
    v=read(ROOT/'benchmarks/peng_robinson_pt_vapor_parent/methane_nhexane_pt_vapor_parent_reference.json')
    for j in (0,2,5,9,12):
        s=v['cases'][j]['independent_equilibrium'];rows.append(dict(case_id='VAPOR_PARENT_'+str(j),group='restart',T=s['T_K'],P=s['P_Pa_abs'],z=s['z']))
    ps=read(ROOT/'benchmarks/peng_robinson_ps/methane_nhexane_pr_ps_reference.json')
    for c in ps['cases']:
        if c['case_id'] in ('DEW_BELOW','DEW_ABOVE'):
            s=c['forward'];rows.append(dict(case_id=c['case_id'],group='dew',T=s['T_K'],P=s['P_Pa_abs'],z=s['z']))
    return rows
def chains():
    rows=[dict(case_id=f'{n}_{p}',source=n,P2=p,eta=.8) for n in ('PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE') for p in (7e6,7.5e6,7.8e6,8e6)]
    rows += [dict(case_id=n,source=n,P2=p,eta=.8) for n,p in [('PH_FLASH',2e6),('PT_VL_HEATING',1.3e6),('PT_DEW_BELOW',7e6),('PT_BUBBLE_BELOW',6e6)]]
    return rows
def anchors():
    return [dict(case_id=n,T=t,P=p,z=[.5,.5]) for n,t,p in [('LIQUID',300.,3e7),('VL',350.,1e6),('VAPOR',317.3,1e3)]]
