"""Isolated PT iteration-budget sensitivity; no patch or solver-file modification."""
import sys,argparse
from pathlib import Path
from dataclasses import replace,asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.configurable_separator_pump.common import *
from benchmarks.configurable_separator_pump.prototype import solve
from benchmarks.pump_energy.compare_production import state,BIP,PROVENANCE
from riogineer_engine.separator_liquid_state import evaluate,local
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import ThermodynamicState,MolarComposition
from riogineer_engine.pr_flash import SolverSettings

def build():
    rows=[]
    for r in read('reference.json')['cases']:
        if r['role']!='8MPa_challenge':continue
        i=r['inputs'];a=evaluate(i['T1'],i['P1'],i['z'],BIP);target=a.aggregate.s_J_mol_K
        for cap in (200,400):
            settings=replace(SolverSettings.high_accuracy(),flash_max_iterations=cap)
            evaluations=[]
            def pt(t):
                c=PengRobinsonProvider().equilibrium_caloric_PT(ThermodynamicState(t,i['P2'],MolarComposition(IDS,tuple(i['z'])),PROVENANCE),BIP,settings)
                evaluations.append(dict(T_K=t,status=c.status,diagnostics=asdict(c.equilibrium.diagnostics)))
                if c.aggregate is None:raise ValueError(c.status)
                return state(c)
            result=solve(pt,target,'S_eq_J_mol_K',64,1e-8)
            scans=[t for t in result['trials'] if t['stage']=='scan'];ref=r['result']['diagnostics']['PS']['diagnostics']['scan'];checks=[]
            for p,q in zip(scans,ref):
                if p['status']=='success':
                    delta=p['residual']-(q['S_J_mol_K']-target)
                    checks.append(dict(T_K=p['T_K'],entropy_error=delta,passed=abs(delta)<=1e-8+1e-11*abs(q['S_J_mol_K']) and p['classification']==q['classification']))
            final=None
            if result['status']=='local_candidate':final=local(evaluate(result['state']['T_K'],i['P2'],i['z'],BIP),BIP)
            rows.append(dict(case_id=r['case_id'],PT_iteration_cap=cap,result=result,evaluations=evaluations,checks=checks,default_PT_final_guard=final,production_default_changed=False))
    return dict(cases=rows,comparison_count=sum(len(r['checks']) for r in rows),failed_comparisons=sum(not c['passed'] for r in rows for c in r['checks']))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('iteration_diagnostic.json',build(),p.parse_args().write)
