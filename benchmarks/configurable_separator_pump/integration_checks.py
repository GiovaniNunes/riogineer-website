"""Retained upstream enthalpy checks for all sources and prototype paths."""
import sys,argparse,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.configurable_separator_pump.common import *
from riogineer_engine.separator_liquid_state import representation,identity,verify,Failure,ROUND

def build():
    sources=read('sources.json');rows={};paths=[]
    for name,s in sources.items():
        r=s['result']
        try:rows[name]=dict(status='accepted',contract=verify(representation(r),r,identity(r)))
        except Failure as e:rows[name]=dict(status=e.category,reason=e.code)
    for c in read('production.json')['cases']:
        if not c['prototype'] or 'metrics' not in c['prototype']:continue
        a=rows[c['source']]['contract'];p=c['prototype'];r=sources[c['source']]['result'];d=r['equipment'][0]['thermodynamics'];e=r['equipment'][0]
        F=a['F_mol_s'];h2=p['states']['outlet']['H_eq_J_mol'];w=p['metrics']['W_recovered_W'];original=a['upstream_enthalpy_flow_W'];h2dot=F*h2
        pump_residual=math.fsum([h2dot,-original,-w]);pump_allowance=a['enthalpy_allowance_W']+ROUND*max(1.,abs(original),abs(h2dot),abs(w))
        vapor=r['streams'][e['material_streams']['vapor']]['enthalpy_flow_W']
        total=math.fsum([vapor,h2dot,-d['inlet_enthalpy_flow_W'],-d['duty_W'],-w])
        allowance=d['energy_allowance_W']+pump_allowance+ROUND*max(1.,abs(vapor),abs(h2dot),abs(d['inlet_enthalpy_flow_W']))
        paths.append(dict(case_id=c['case_id'],retained_upstream_enthalpy_flow_W=original,pump_energy_residual_W=pump_residual,pump_allowance_W=pump_allowance,
          integrated_energy_residual_W=total,integrated_allowance_W=allowance,passed=abs(total)<=allowance and abs(pump_residual)<=pump_allowance,
          qualifier='Local prototype only; unresolved production PS remains excluded'))
    return dict(sources=rows,prototype_paths=paths)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('integration_checks.json',build(),p.parse_args().write)
