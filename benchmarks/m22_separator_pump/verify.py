"""M22 fresh application evidence against frozen independent physical references."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'engine')]
from riogineer_engine.core import build_flowsheet,calculate,validate_requirements
from riogineer_engine.milestone17 import requirements as source_requirements
from riogineer_engine.separator_liquid_state import representation,identity,hb
from riogineer_engine.separator_liquid_pump import run
from riogineer_engine.numerical_profiles import NumericalProfile
from benchmarks.configurable_separator_pump.compare import source_checks
HERE=Path(__file__).resolve().parent
NAMES=('PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE')
PROFILE=NumericalProfile.PT200.value

def read(name):return json.loads((ROOT/name).read_text())
def verify(preliminary=False):
    sources=read('benchmarks/pt_iteration_budget/sources.json')
    reference=read('benchmarks/pt_iteration_budget/reference.json')
    rows=[]
    for name in NAMES:
        ref=next(c for c in reference['chains'] if c['source']==name and c['P2']==8e6)
        if preliminary:
            req=source_requirements(**sources[name]['inputs']);f=build_flowsheet(req);result=calculate(f)
            stream=representation(result);answer=run(stream,result,identity(result),8e6,.8,numerical_profile=PROFILE)
        else:
            from riogineer_engine.milestone22 import requirements
            req=requirements(name);validation=validate_requirements(req);assert validation['validation']['status']=='valid',validation
            f=build_flowsheet(req);result=calculate(f);answer=result['equipment'][1]['thermodynamics']['diagnostics']
            stream=result['streams'][result['equipment'][0]['material_streams']['liquid']]
        checks=source_checks(dict(result=result),reference['sources'][name])
        def check(label,a,b,tol=0):
            ok=abs(a-b)<=tol if isinstance(a,(int,float)) and not isinstance(a,bool) else a==b
            checks.append(dict(field=label,actual=a,reference=b,allowance=tol,passed=ok))
        states=dict(inlet=answer['inlet']['fresh'],isentropic=answer['isentropic'],outlet=answer['actual'])
        for end,a in states.items():
            b=ref['result']['states'][end]
            for field,tol in [('T_K',1e-7),('P_Pa_abs',0),('H_eq_J_mol',hb(b['H_eq_J_mol'])),('S_eq_J_mol_K',1e-8+1e-11*abs(b['S_eq_J_mol_K'])),('beta',2e-9),('classification',0)]:check(end+'.'+field,a[field],b[field],tol)
            for j in range(2):check(end+'.z'+str(j),a['z'][j],b['z'][j],2e-9)
            check(end+'.stable',a['stability']['stable'],True);check(end+'.converged',a['stability']['converged'],True)
            check(end+'.PIP',a['stability']['phase_identification_parameter']>1,True)
            for phase,q in a['phases'].items():
                t=b['phases'][phase]
                for field,tol in [('Z',2e-10+1e-9*abs(t['Z'])),('h_J_mol',hb(t['h_J_mol'])),('s_J_mol_K',1e-8+1e-11*abs(t['s_J_mol_K']))]:check(end+'.'+phase+'.'+field,q[field],t[field],tol)
                for j in range(2):check(end+'.'+phase+'.x'+str(j),q['composition'][j],t['composition'][j],2e-9)
        check('power',answer['fluid_power_W'],ref['result']['metrics']['W_recovered_W'],ref['inputs']['flow']*(hb(states['inlet']['H_eq_J_mol'])+hb(states['outlet']['H_eq_J_mol'])))
        check('source_Hdot',answer['inlet']['upstream_enthalpy_flow_W'],stream['enthalpy_flow_W'])
        check('source_semantics',answer['inlet']['local']['status'],'compressed_witness' if name.endswith('BELOW') else 'saturated_source_liquid')
        check('work',answer['work_ratio']<=1e-4,True);check('entropy',answer['entropy_generation_J_mol_K']>=-2e-8,True)
        for kind,n in [('PS',64),('PH',128)]:
            check(kind+'.profile',answer[kind]['numerical_profile'],PROFILE)
            check(kind+'.scan',answer[kind]['scan_count'],n)
            check(kind+'.cap',answer[kind]['pt_settings']['flash_max_iterations'],200)
            check(kind+'.failures',answer[kind]['failure_count'],0)
        check('source_cap',answer['numerics']['source_and_local_settings']['flash_max_iterations'],100)
        check('fallback',answer['numerics']['fallback'],None)
        if not preliminary:
            product=result['streams'][result['equipment'][1]['material_streams']['outlet']]
            check('component_rates',product['component_mass_flow_kg_h'],stream['component_mass_flow_kg_h'])
            check('total_mass',product['mass_flow_kg_h'],stream['mass_flow_kg_h'])
            check('lineage',product['state_context']['lineage'][0],stream['state_context']['source'])
            check('mass',result['balances']['mass']['status'],'passed')
            check('energy',abs(result['balances']['energy']['residual_W'])<=result['balances']['energy']['tolerance_W'],True)
            check('effective_profile',result['equipment'][1]['thermodynamics']['numerical_profile'],PROFILE)
            check('serialization',json.loads(json.dumps(result,allow_nan=False)),result)
        rows.append(dict(case_id=name,requirements=req,flowsheet=f,result=result,checks=checks,pump=answer if preliminary else None))
        print(name,len(checks),'PASS' if all(c['passed'] for c in checks) else 'FAIL',flush=True)
    refs=['benchmarks/pt_iteration_budget/reference.json','benchmarks/pt_iteration_budget/sources.json','benchmarks/configurable_separator_pump/reference.json']
    data=dict(path='source_application_then_pump' if preliminary else 'complete_application',cases=rows,comparison_count=sum(len(r['checks']) for r in rows),failed_checks=sum(not c['passed'] for r in rows for c in r['checks']),references={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in refs})
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preliminary',action='store_true');p.add_argument('--output');a=p.parse_args()
    data=verify(a.preliminary)
    if a.output:
        with Path(a.output).open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
    assert data['failed_checks']==0,[c for r in data['cases'] for c in r['checks'] if not c['passed']]
