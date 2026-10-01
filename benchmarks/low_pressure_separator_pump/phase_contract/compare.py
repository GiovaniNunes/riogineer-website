"""Extension experiments only; consumes immutable prior and new independent evidence."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]));sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'engine'))
from benchmarks.low_pressure_separator_pump.phase_contract.common import *
from benchmarks.low_pressure_separator_pump.phase_contract import adapter as a
from benchmarks.low_pressure_separator_pump.phase_contract.pump import run
from benchmarks.low_pressure_separator_pump.phase_contract.negatives import cases as negatives

def checks(p,r):
    rows=[]
    def number(k,x,y,b):rows.append(dict(field=k,error=abs(x-y),allowance=b,passed=abs(x-y)<=b))
    rows.append(dict(field='classification',passed=p['classification']==r['classification']))
    for k,b in [('T_K',1e-7),('P_Pa_abs',0.),('beta',2e-9),('H_eq_J_mol',a.hb(r['H_eq_J_mol'])),('S_eq_J_mol_K',1e-8+1e-11*abs(r['S_eq_J_mol_K']))]:number(k,p[k],r[k],b)
    for j in range(2):number('z'+str(j),p['z'][j],r['z'][j],2e-9)
    rows.append(dict(field='phase_set',passed=set(p['phases'])==set(r['phases'])))
    for k in sorted(p['phases'].keys() & r['phases'].keys()):
        x,y=p['phases'][k],r['phases'][k]
        for f,b in [('Z',2e-10+1e-9*abs(y['Z'])),('h_J_mol',a.hb(y['h_J_mol'])),('s_J_mol_K',1e-8+1e-11*abs(y['s_J_mol_K']))]:number(k+'.'+f,x[f],y[f],b)
        for j in range(2):number(k+'.z'+str(j),x['composition'][j],y['composition'][j],2e-9)
    return rows

def attempt(fn):
    try:return fn()
    except a.Failure as e:return dict(status=e.category,reason=e.code)

def build():
    sources=read(HERE/'sources.json')['sources'];ref=read(HERE/'reference.json');oldref={c['case_id']:c for c in read(OLD/'reference.json')['cases']}
    adapters=[]
    for key,x in sources.items():
        r=x['result'];out=attempt(lambda:a.verify(a.representation(r),r,a.identity(r)))
        adapters.append(dict(source=key,result=out));print('ADAPTER',key,out['status'],flush=True)
    qualified=[]
    for c in accepted():
        r=sources[source_key(c)]['result'];s=a.representation(r);ad=a.verify(s,r,a.identity(r));bip=a.bip_from(s['state_context']['thermodynamics']);states={};comparisons=[]
        for k,v in c['result']['states'].items():
            if k=='inlet':states[k]=dict(state=ad['fresh'],local=ad['local'])
            elif c['inputs']['P1']==c['inputs']['P2']:states[k]=states['inlet']
            else:
                p=a.evaluate(v['T_K'],v['P_Pa_abs'],v['z'],bip)
                states[k]=dict(state=a.state(p),local=attempt(lambda:a.local(p,bip)))
            comparisons.extend(checks(states[k]['state'],oldref[c['case_id']]['result']['states'][k]))
        ok=all(x['passed'] for x in comparisons) and all(x['local']['status'] in ('saturated_source_liquid','compressed_witness') for x in states.values())
        qualified.append(dict(case_id=c['case_id'],source=source_key(c),states=states,checks=comparisons,status='accepted' if ok else 'unresolved'))
    base=sources['PH_FLASH']['result'];bip=a.bip_from(a.representation(base)['state_context']['thermodynamics'])
    probes=[]
    for c in ref['cases']:
        i=c['inputs'];p=a.evaluate(i['T'],i['P'],i['z'],bip);st=a.state(p)
        decision=attempt(lambda:a.local(p,bip))
        probes.append(dict(case_id=c['case_id'],kind=c['kind'],inputs=i,state=st,local_without_source=decision,checks=checks(st,c['result'])))
    bad=[]
    for c in negatives(base):
        r=attempt(lambda:a.verify(c['stream'],c['source'],c['current']))
        bad.append(dict(case_id=c['case_id'],result=r,expected=c['expected_category'],passed=r['status']==c['expected_category']))
    pumps=[]
    for name in ('PT_VL_HEATING','PH_FLASH','PT_BUBBLE_BELOW','PT_DEW_BELOW'):
        r=sources[name]['result'];s=a.representation(r)
        for dp in (0.,1e6):
            key=name+'_DP'+str(dp);out=run(s,r,a.identity(r),s['pressure_Pa_abs']+dp,.8);rr=oldref[key]['result'];cc=[]
            if dp:
                for k,pp in [('inlet',out['inlet']['fresh']),('isentropic',out['isentropic']),('outlet',out['actual'])]:cc.extend(checks(pp,rr['states'][k]))
            else:cc.append(dict(field='identity_exact',passed=out['outlet']==s and out['PS'] is None and out['PH'] is None))
            allowance=out['inlet']['F_mol_s']*(a.hb(rr['states']['inlet']['H_eq_J_mol'])+a.hb(rr['states']['outlet']['H_eq_J_mol']))
            cc.append(dict(field='fluid_power_W',error=abs(out['fluid_power_W']-rr['metrics']['W_recovered_W']),allowance=allowance,passed=abs(out['fluid_power_W']-rr['metrics']['W_recovered_W'])<=allowance))
            pumps.append(dict(case_id=key,result=out,checks=cc));print('PUMP',key,flush=True)
    old=read(OLD/'production.json');known=[dict(case_id=c['case_id'],status='unresolved',evidence='reused immutable first study, not rerun',diagnostics=c['result']['diagnostics']) for c in old['cases'] if c['disposition']=='unresolved']
    allchecks=[k for group in (qualified,probes,pumps) for c in group for k in c['checks']]
    return dict(sources_sha256=digest(HERE/'sources.json'),reference_sha256=digest(HERE/'reference.json'),
        adapters=adapters,qualified_tuples=qualified,new_probes=probes,negatives=bad,pumps=pumps,known_unresolved=known,
        comparison_count=len(allchecks),failed_checks=sum(not c['passed'] for c in allchecks),
        source_sha256={p.name:digest(p) for p in HERE.glob('*.py') if p.name not in ('test_contract.py','verify.py')})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('production.json',build(),p.parse_args().write)
