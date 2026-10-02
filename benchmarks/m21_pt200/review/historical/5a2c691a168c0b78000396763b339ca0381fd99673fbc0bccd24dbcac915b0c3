"""New independent witnesses/probes only; existing independent artifacts untouched."""
import argparse,sys,importlib.metadata,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from benchmarks.low_pressure_separator_pump.phase_contract.common import *
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
from benchmarks.peng_robinson_caloric import reference as caloric

def specifications():
    specs={}
    for c in accepted():
        for key,s in c['result']['states'].items():
            spec=dict(T=s['T_K'],P=s['P_Pa_abs']*.9999,z=s['z'])
            token=hashed(spec);specs[token]=dict(kind='witness',inputs=spec)
    old=read(OLD/'reference.json')
    for name in ('PT_VL_HEATING','PH_FLASH','PT_BUBBLE_BELOW','PT_DEW_BELOW'):
        r=next(c for c in old['screen'] if c['case_id']==name);s=r['equilibrium'];P=r['boundary']['refined']['P_bubble']
        for dp in (-1e-3,-1e-6,0.,1e-6,1e-3):
            specs[name+'_P'+str(dp)]=dict(kind='boundary',source=name,offset=dict(relative_P=dp),inputs=dict(T=s['T_K'],P=P*(1+dp),z=s['z']))
        for dt in (-.01,.01):
            specs[name+'_T'+str(dt)]=dict(kind='boundary',source=name,offset=dict(delta_T_K=dt),inputs=dict(T=s['T_K']+dt,P=P,z=s['z']))
    return specs

def build():
    q=EntropyPT();rows=[]
    for key,c in specifications().items():
        i=c['inputs']
        try:r=q.evaluate(i['T'],i['P'],i['z'])
        except Exception as e:r=dict(error=type(e).__name__+': '+str(e))
        rows.append(dict(case_id=key,**c,result=r))
    old=read(OLD/'reference.json')
    assert {n:importlib.metadata.version(n) for n in old['dependencies']}==old['dependencies']
    library={Path(inspect.getfile(o)).name:digest(inspect.getfile(o)) for o in (caloric.PR,caloric.PRMIX,caloric.CEOSGas,caloric.FlashVL,caloric.HeatCapacityGas)}
    cp=digest(Path(caloric.hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv')
    assert library==old['library_source_sha256'] and cp==old['cp_source_sha256']
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(prior_reference_sha256=digest(OLD/'reference.json'),source_sha256=digest(__file__),
                plan_sha256=digest(HERE/'PLAN.md'),production_imported=False,dependencies=old['dependencies'],library_source_sha256=library,cp_source_sha256=cp,
                methodology='Unchanged Thermo PR/Poling model and units from first study; no new inverse solves',
                cases=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('reference.json',build(),p.parse_args().write)
