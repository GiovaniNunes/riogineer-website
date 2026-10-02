"""Independent Thermo sources and pump paths; never imports production numerics."""
import sys,argparse,inspect,importlib.metadata,platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.configurable_separator_pump.common import *
from benchmarks.two_phase_separator_energy.reference import qualify
from benchmarks.pump_energy.reference import calculate
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
from benchmarks.peng_robinson_ps.solver import solve_ps
from benchmarks.peng_robinson_caloric import reference as caloric
from benchmarks.low_pressure_separator_pump.common import policy

def build():
    frozen=read('sources.json');specs,rows=matrix();sources={};q=EntropyPT();results=[]
    for name,i in specs.items():
        try:sources[name]=dict(status='success',result=qualify(dict(case_id=name,inputs=i)))
        except Exception as e:sources[name]=dict(status='unresolved',reason=type(e).__name__+': '+str(e))
        print('reference source',name,sources[name]['status'],flush=True)
    for row in rows:
        i=pump_inputs(frozen[row['source']],row)
        if not .6<=i['eta']<=1:r=dict(status='invalid_efficiency',stage='input',states={},diagnostics={})
        else:r=calculate(i,q)
        record=row|dict(inputs=i,result=r,policy=policy(i,r))
        if row['role']=='8MPa_challenge':
            record['alternate_PS_256']=solve_ps(i['P2'],i['z'],r['states']['inlet']['S_eq_J_mol_K'],grid_points=256,evaluator=q.evaluate)
            record['scan_neighborhoods']=[]
            # Entire high-temperature scan segment includes both historical observations.
            for k in range(53,60):
                t=200+300*k/63
                for off in (-.1,-.01,0.,.01,.1):
                    try:
                        s=q.evaluate(t+off,i['P2'],i['z'])
                        record['scan_neighborhoods'].append(dict(T_K=t+off,state=s,entropy_residual=s['S_eq_J_mol_K']-r['states']['inlet']['S_eq_J_mol_K']))
                    except Exception as e:record['scan_neighborhoods'].append(dict(T_K=t+off,error=str(e)))
            record['pressure_path_samples']=[]
            for fraction in (.1,.25,.5,.75,.9):
                ii=i|dict(P2=i['P1']+fraction*(i['P2']-i['P1']))
                record['pressure_path_samples'].append(dict(fraction=fraction,result=calculate(ii,q)))
        results.append(record);print('reference path',row['case_id'],record['policy'],flush=True)
    old=json.loads((ROOT/'benchmarks/low_pressure_separator_pump/reference.json').read_text())
    actual={Path(inspect.getfile(o)).name:digest(inspect.getfile(o)) for o in (caloric.PR,caloric.PRMIX,caloric.CEOSGas,caloric.FlashVL,caloric.HeatCapacityGas)}
    assert actual==old['library_source_sha256']
    cp=digest(Path(caloric.hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv');assert cp==old['cp_source_sha256']
    versions={n:importlib.metadata.version(n) for n in old['dependencies']};assert versions==old['dependencies']
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(sources=sources,cases=results,production_imported=False,python=platform.python_version(),dependencies=versions,
      library_source_sha256=actual,cp_source_sha256=cp,**{k:old[k] for k in ('components','cp_data','convention','kij','units')},
      source_inputs_sha256=digest(HERE/'sources.json'),tolerances=TOLS)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('reference.json',build(),p.parse_args().write)
