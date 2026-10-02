"""New independent Thermo states and inverse/chain expectations; no production import."""
import sys,argparse,inspect,importlib.metadata
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.pt_iteration_budget.common import *
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
from benchmarks.peng_robinson_ps.solver import solve_ps
from benchmarks.peng_robinson_ph.solver import solve_ph
from benchmarks.pump_energy.reference import calculate
from benchmarks.two_phase_separator_energy.reference import qualify
from benchmarks.peng_robinson_caloric import reference as caloric

def inputs(c,source):
    r=source['result'];e=r['equipment'][0];s=r['streams'][e['material_streams']['liquid']];p=e['thermodynamics']['phases']['liquid']
    return dict(T1=s['temperature_K'],P1=s['pressure_Pa_abs'],P2=c['P2'],eta=c['eta'],flow=p['molar_flow_mol_s'],z=[p['composition'][k] for k in IDS])

def build():
    q=EntropyPT();pts=[];inverses=[];paths=[]
    for row in pt_cases():
        try:
            s=q.evaluate(row['T'],row['P'],row['z'])
            lnphis={name:(q.flash.liquid if name=='liquid' else q.flash.gas).to(T=row['T'],P=row['P'],zs=p['composition']).lnphis() for name,p in s['phases'].items()}
            pts.append(row|dict(status='success',state=s,lnphis=lnphis))
        except Exception as e:pts.append(row|dict(status='reference_unavailable',reason=type(e).__name__+': '+str(e)))
    for row in anchors():
        s=q.evaluate(row['T'],row['P'],row['z']);ss=solve_ps(row['P'],row['z'],s['S_eq_J_mol_K'],evaluator=q.evaluate);hh=solve_ph(row['P'],row['z'],s['H_eq_J_mol'],evaluator=q.evaluate)
        inverses.append(row|dict(forward=s,PS=ss,PH=hh))
    captures=read(HERE/'sources.json')
    for row in chains():
        i=inputs(row,captures[row['source']]);paths.append(row|dict(inputs=i,result=calculate(i,q)))
    source_reference={n:dict(status='success',result=qualify(dict(case_id=n,inputs=i))) for n,i in sources().items()}
    old=read(PRIOR/'reference.json')
    actual={Path(inspect.getfile(o)).name:digest(inspect.getfile(o)) for o in (caloric.PR,caloric.PRMIX,caloric.CEOSGas,caloric.FlashVL,caloric.HeatCapacityGas)}
    assert actual==old['library_source_sha256']
    cp=digest(Path(caloric.hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv');assert cp==old['cp_source_sha256']
    deps={n:importlib.metadata.version(n) for n in old['dependencies']};assert deps==old['dependencies']
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(PT=pts,inverses=inverses,chains=paths,sources=source_reference,production_imported=False,dependencies=deps,library_source_sha256=actual,cp_source_sha256=cp,
                **{k:old[k] for k in ('components','cp_data','convention','kij','units','tolerances')})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('reference.json',build(),p.parse_args().write)
