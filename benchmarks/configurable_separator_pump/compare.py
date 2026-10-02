"""Read-only production experiments, independent comparisons and isolated prototype."""
import sys,argparse,math
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.configurable_separator_pump.common import *
from benchmarks.configurable_separator_pump.prototype import solve
from benchmarks.pump_energy.compare_production import calculate,compare,state,BIP,PROVENANCE,standalone_ph,inverse
from benchmarks.pump_energy.common import finish
from benchmarks.low_pressure_separator_pump.common import policy
from benchmarks.two_phase_separator_energy.compare_production import fields,expected_fields
from benchmarks.low_pressure_separator_pump.phase_contract.negatives import cases as negatives
from riogineer_engine.separator_liquid_state import representation,identity,verify,evaluate,local,Failure
from riogineer_engine.separator_liquid_pump import run
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import ThermodynamicState,MolarComposition
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_ph_flash import PHSpecification
from riogineer_engine.core import build_flowsheet,calculate as process
from riogineer_engine.milestone20 import requirements
from riogineer_engine.milestone17 import requirements as source_requirements

def attempt(f):
    try:return dict(status='success',result=f())
    except Exception as e:return dict(status='failed',type=type(e).__name__,reason=str(e),category=getattr(e,'category',None),code=getattr(e,'code',None))

def source_checks(source,ref):
    if ref['status']!='success':return []
    r=source['result'];d=r['equipment'][0]['thermodynamics'];e=ref['result'];checks=[]
    def check(k,a,b,t=0.):checks.append(dict(field=k,actual=a,reference=b,allowance=t,passed=math.isfinite(a) and abs(a-b)<=t))
    for end in ('inlet','outlet'):
        checks.append(dict(field=end+'.phase',passed=d[end]['classification']==e[end]['classification']))
        a,b=fields(d[end]),expected_fields(e[end])
        checks.append(dict(field=end+'.fields',passed=set(a)==set(b)))
        for k in sorted(a.keys() & b.keys()):check(end+'.'+k,a[k],b[k],e['allowances'][end][k])
    for name in ('liquid','vapor'):
        p=d['phases'][name];v=e['outputs'][name];a=e['allowances']['phases'][name]
        stream=r['streams'][r['equipment'][0]['material_streams'][name]]
        for k in ('molar_flow_mol_s','enthalpy_flow_W'):check(name+'.'+k,p[k],v[k],a[k])
        for j,c in enumerate(IDS):check(name+'.'+c,stream['component_mass_flow_kg_h'][c],v['component_mass_flow_kg_h'][j],a['component_mass_flow_kg_h'][j])
        check(name+'.mass',stream['mass_flow_kg_h'],v['mass_flow_kg_h'],a['mass_flow_kg_h'])
    check('duty',d['duty_W'],e['duty_W'],e['allowances']['duty_W'])
    check('energy',d['energy_residual_W'],0.,d['energy_allowance_W'])
    return checks

def app_requirements(row,source):
    r=requirements();sr=source_requirements(**source['inputs'])
    r['feeds'][0]['state']=sr['feeds'][0]['state']
    r['equipment'][0]['parameters']=sr['equipment'][0]['parameters']
    r['equipment'][1]['parameters'].update(outlet_pressure_Pa_abs=row['P2'],isentropic_efficiency=row['eta'])
    return r

def prototype(i):
    def pt(t,p=i['P2']):return state(evaluate(t,p,i['z'],BIP))
    a=pt(i['T1'],i['P1']);ps=solve(pt,a['S_eq_J_mol_K'],'S_eq_J_mol_K',64,1e-8)
    out=dict(status='unresolved',PS=ps,production_qualified=False)
    if ps['status']!='local_candidate':return out
    b=ps['state'];target=a['H_eq_J_mol']+(b['H_eq_J_mol']-a['H_eq_J_mol'])/i['eta']
    ph=solve(pt,target,'H_eq_J_mol',128,1e-6,xtol=1e-12);out['PH']=ph
    full=PengRobinsonProvider().flash_PH(PHSpecification(i['P2'],target,MolarComposition(IDS,tuple(i['z'])),PROVENANCE),BIP)
    out['full_production_PH_from_prototype_PS']=inverse(full)
    if ph['status']!='local_candidate':return out
    c=ph['state'];out['endpoint_guards']=[attempt(lambda s=s:local(evaluate(s['T_K'],s['P_Pa_abs'],i['z'],BIP),BIP)) for s in (b,c)]
    out['states']=dict(inlet=a,isentropic=b,outlet=c);out['metrics']=finish(i,out['states'])
    out['status']='local_path_candidate' if all(g['status']=='success' for g in out['endpoint_guards']) else 'unresolved_phase'
    return out

def candidate(args):
    rr,sources,sc=args
    row={k:rr[k] for k in ('case_id','source','role','P2','eta')};i=rr['inputs'];source=sources[row['source']];r=source['result'];stream=representation(r)
    admission=attempt(lambda:build_flowsheet(app_requirements(row,source)))
    app=dict(status='admitted' if admission['status']=='success' else 'rejected',reason=admission.get('reason'))
    guarded=attempt(lambda:run(stream,r,identity(r),i['P2'],i['eta']))
    raw=calculate(i) if .6<=i['eta']<=1 else dict(status='invalid_efficiency',stage='input',states={},diagnostics={})
    pol=policy(i,raw);checks=compare(i,rr['result'],raw)
    supported=sc[row['source']]['passed'] and guarded['status']=='success' and rr['policy'] in ('resolved','identity') and pol in ('resolved','identity') and all(c['passed'] for c in checks)
    disposition='accepted' if supported else 'rejected' if guarded.get('category')=='rejected' or pol in ('invalid_pressure','invalid_efficiency','invalid_flow','unresolved_work','unsupported_phase') else 'unresolved'
    record=row|dict(inputs=i,source_identity=identity(r),source_qualified=sc[row['source']]['passed'],application=app,guarded_callable=guarded,production_numerics=raw,reference_status=rr['policy'],checks=checks,disposition=disposition,prototype=None)
    if guarded['status']=='success':
        g=guarded['result'];d=r['equipment'][0]['thermodynamics'];e=r['equipment'][0]
        vapor=r['streams'][e['material_streams']['vapor']]
        closure=math.fsum([vapor['enthalpy_flow_W'],g['outlet']['enthalpy_flow_W'],-d['inlet_enthalpy_flow_W'],-d['duty_W'],-g['fluid_power_W']])
        rounding=64*sys.float_info.epsilon*max(1.,abs(d['inlet_enthalpy_flow_W']),abs(g['outlet']['enthalpy_flow_W']),abs(vapor['enthalpy_flow_W']))
        allowance=d['energy_allowance_W']+g.get('energy_allowance_W',g['inlet']['enthalpy_allowance_W'])+rounding
        record['integrated_energy']=dict(residual_W=closure,allowance_W=allowance,passed=abs(closure)<=allowance)
        if abs(closure)>allowance:record['disposition']='unresolved'
    if row['role']=='8MPa_challenge':
        record['prototype']=prototype(i)
        pr=record['prototype']
        if 'states' in pr:
            fake=dict(states=pr['states'],metrics=pr['metrics'],diagnostics={})
            record['prototype_checks']=compare(i,rr['result'],fake)
            record['prototype_policy']=policy(i,fake|dict(stage='complete',status='local_candidate'))
        record['reference_target_PH_diagnostic']=standalone_ph(i,rr['result'])
        record['scan_neighborhoods']=[]
        for probe in rr['scan_neighborhoods']:
            t=probe['T_K'];c=PengRobinsonProvider().equilibrium_caloric_PT(ThermodynamicState(t,i['P2'],MolarComposition(IDS,tuple(i['z'])),PROVENANCE),BIP,SolverSettings.high_accuracy())
            record['scan_neighborhoods'].append(dict(T_K=t,status=c.status,message=c.message,PT=asdict(c.equilibrium),state=state(c) if c.aggregate else None))
        record['pressure_path_samples']=[dict(fraction=p['fraction'],result=calculate(i|dict(P2=i['P1']+p['fraction']*(i['P2']-i['P1'])))) for p in rr['pressure_path_samples']]
    print(row['case_id'],disposition,guarded['status'],raw['stage'],flush=True)
    return record

def build():
    ref=read('reference.json');sources=read('sources.json');records=[];sc={}
    for name,s in sources.items():
        checks=source_checks(s,ref['sources'][name]);sc[name]=dict(checks=checks,independent_status=ref['sources'][name]['status'],passed=bool(checks) and all(c['passed'] for c in checks))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(candidate,[(rr,sources,sc) for rr in ref['cases']]))
    neg=[]
    for n in negatives(sources['PH_FLASH']['result']):
        a=attempt(lambda:verify(n['stream'],n['source'],n['current']))
        neg.append(dict(case_id=n['case_id'],outcome=a,expected=n['expected_category'],passed=a.get('category')==n['expected_category']))
    return dict(source_checks=sc,cases=records,contract_negatives=neg,reference_sha256=digest(HERE/'reference.json'))

def ledger(data):
    rows=[]
    for c in data['cases']:
        rows.append({k:c[k] for k in ('case_id','source','role','inputs','source_identity','source_qualified','application','reference_status','disposition')}|dict(
          production_stage=c['production_numerics']['stage'],production_status=c['production_numerics']['status'],
          guarded_status=c['guarded_callable']['status'],guarded_reason=c['guarded_callable'].get('reason'),
          prototype_status=c['prototype']['status'] if c['prototype'] else 'not_run',
          remaining_gap='No continuous-domain qualification; application scope unchanged' if c['disposition']=='accepted' else 'See retained solver/guard/reference diagnostics'))
    checks=[q for c in data['cases'] for q in c['checks']]+[q for s in data['source_checks'].values() for q in s['checks']]
    proto=[q for c in data['cases'] for q in c.get('prototype_checks',[])]
    return dict(candidates=rows,counts={k:sum(c['disposition']==k for c in rows) for k in ('accepted','rejected','unresolved')},
      comparison_count=len(checks),failed_comparisons=sum(not c['passed'] for c in checks),
      prototype_comparison_count=len(proto),prototype_failed_comparisons=sum(not c['passed'] for c in proto),
      numeric_comparison_count=sum('actual' in c and isinstance(c['actual'],(int,float)) and not isinstance(c['actual'],bool) for c in checks),
      contract_negative_count=len(data['contract_negatives']),contract_negative_failures=sum(not c['passed'] for c in data['contract_negatives']))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();data=build();save('production.json',data,a.write);save('candidate_ledger.json',ledger(data),a.write)
