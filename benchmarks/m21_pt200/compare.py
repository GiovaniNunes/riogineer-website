"""Numerical qualification and deterministic counters; never writes old artifacts."""
import sys,argparse,math
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.m21_pt200.common import *
from benchmarks.m21_pt200.harness import *

from benchmarks.pump_energy.compare_production import compare as compare_state
from benchmarks.configurable_separator_pump.compare import source_checks
from riogineer_engine.separator_pump_scope import CASES,qualify


def physical(args):
    row,cap=args;profile=Profile(cap);r=traced_pt(row,profile);checks=[]
    if r['state'] and row['status']=='success':
        checks=compare_state({},dict(states={'PT':row['state']}),dict(states={'PT':r['state']},diagnostics={}))
        d=r['PT']['diagnostics'];single=row['state']['classification']!='vapor_liquid'
        checks.append(dict(field='initial_stability_converged',passed=d['stability']['converged']))
        checks.append(dict(field='initial_stability_conclusion',passed=d['stability']['stable']==single))
        if not single:
            checks += [dict(field='final_common_tangent',passed=bool(d['equilibrium_stability'] and d['equilibrium_stability']['converged'] and d['equilibrium_stability']['stable'])),
                       dict(field='fugacity_gate',passed=max(map(abs,d['fugacity_residual']))<=1e-12),dict(field='material_gate',passed=max(map(abs,d['material_residual']))<=1e-10),
                       dict(field='independent_fugacity_gate',passed=max(map(abs,row['state']['ln_fugacity_residual']))<=1e-9)]
        for p in r['PT']['phases']:
            for j,v in enumerate(p['ln_phi']):
                e=row['lnphis'][p['identifier']][j];checks.append(dict(field=p['identifier']+'.ln_phi'+str(j),actual=v,reference=e,allowance=2e-9,passed=abs(v-e)<=2e-9))
    return dict(case_id=row['case_id'],group=row['group'],inputs={k:row[k] for k in ('T','P','z')},cap=cap,result=r,reference_status=row['status'],checks=checks)

def path(args):
    row,sources,cap=args;r=chain(row,sources,Profile(cap));p=dict(states=r['states'],diagnostics={k:v['diagnostics'] for k,v in r['diagnostics'].items()})
    if 'metrics' in r:p['metrics']=r['metrics']
    checks=compare_state(row['inputs'],row['result'],p)
    print(row['case_id'],cap,r['status'],r['stage'],flush=True)
    return dict(case_id=row['case_id'],cap=cap,inputs=row['inputs'],result=r,reference_status=row['result']['status'],checks=checks)

def anchor(args):
    row,cap,kind=args;profile=Profile(cap);target=row['forward']['S_eq_J_mol_K' if kind=='PS' else 'H_eq_J_mol']
    spec=(PSSpecification if kind=='PS' else PHSpecification)(row['P'],target,MolarComposition(IDS,tuple(row['z'])),PROVENANCE)
    r,details=solve(spec,profile,kind);ref=row[kind];checks=[]
    if r.caloric and ref['status']=='success':checks=compare_state({},dict(states={'endpoint':ref['solution']}),dict(states={'endpoint':state(r.caloric)},diagnostics={kind:details['diagnostics']}))
    approved=None
    if r.status=='success':approved=guard(r,spec,profile,kind)
    # Cap=100 local orchestration must exactly reproduce unchanged public routines.
    legacy_equal=None
    if cap==100:
        native=(PROVIDER.flash_PS if kind=='PS' else PROVIDER.flash_PH)(spec,BIP)
        legacy_equal=asdict(native)==asdict(r)
    return dict(case_id=row['case_id'],kind=kind,cap=cap,status=r.status,record=details,state=state(r.caloric) if r.caloric else None,guard=approved,checks=checks,legacy_equal=legacy_equal)

def build():
    from concurrent.futures import ProcessPoolExecutor
    ref=read(FROZEN/'reference.json');sources=read(HERE/'sources.json')
    identities={r['case_id']:r for r in read(FROZEN/'phase_identity_reference.json')['cases']}
    for row in ref['PT']:
        identity=identities[row['case_id']];assert identity['status']=='verified'
        row.update(state=identity['state'],lnphis=identity['lnphis'])
    with ProcessPoolExecutor(max_workers=4) as pool:
        pts=list(pool.map(physical,[(r,c) for r in ref['PT'] for c in CAPS]))
        inv=list(pool.map(anchor,[(r,c,k) for r in ref['inverses'] for c in CAPS for k in ('PS','PH')]))
        paths=list(pool.map(path,[(r,sources,c) for r in ref['chains'] for c in CAPS]))
    compatibility=[]
    for i in range(0,len(pts),2):
        base=pts[i]['result']
        if base['state']:
            for c in pts[i+1:i+2]:
                compatibility.append(dict(case_id=c['case_id'],cap=c['cap'],same_payload_and_diagnostics=base['result_without_budget_sha256']==c['result']['result_without_budget_sha256'],
                                          same_iteration_sequence=base['trace_sha256']==c['result']['trace_sha256']))
    admission=[]
    for row in CASES:
        f=build_flowsheet(requirements(row['qualification_id']));admission.append(dict(case_id=row['qualification_id'],admitted=qualify(f)==row['qualification_id']))
    for n in ('PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE'):
        req=requirements(n+'_DP1000000.0');req['equipment'][1]['parameters']['outlet_pressure_Pa_abs']=8e6
        try:build_flowsheet(req);admission.append(dict(case_id=n+'_8MPa',admitted=True))
        except ValueError as e:admission.append(dict(case_id=n+'_8MPa',admitted=False,reason=str(e)))
    return dict(PT=pts,inverses=inv,chains=paths,compatibility=compatibility,source_checks={n:source_checks(s,ref['sources'][n]) for n,s in sources.items()},application_scope=admission,
                profiles=[Profile(c).record() for c in CAPS],reference_sha256=digest(FROZEN/'reference.json'),phase_identity_sha256=digest(FROZEN/'phase_identity_reference.json'))

def ledger(data):
    entries=[]
    for group in ('PT','inverses','chains'):
        for c in data[group]:
            status=c['status'] if group=='inverses' else c['result']['status'];passed=bool(c['checks']) and all(q['passed'] for q in c['checks'])
            entries.append(dict(group=group,case_id=c['case_id'],kind=c.get('kind'),cap=c['cap'],status=status,comparisons_passed=passed,
                disposition='accepted_finite_case' if (status.startswith('success') or status=='accepted_prototype') and passed else 'unresolved',
                reason=c.get('result',{}).get('reason',c.get('result',{}).get('message')),production_extension=False))
    checks=[q for g in ('PT','inverses','chains') for c in data[g] for q in c['checks']]+[q for cs in data['source_checks'].values() for q in cs]
    return dict(entries=entries,comparison_count=len(checks),failed_comparisons=sum(not q['passed'] for q in checks),
        scalar_comparison_count=sum('actual' in q and isinstance(q['actual'],(int,float)) and not isinstance(q['actual'],bool) for q in checks),
        profile_counts={str(cap):{g:dict(total=sum(e['group']==g and e['cap']==cap for e in entries),accepted=sum(e['group']==g and e['cap']==cap and e['disposition']=='accepted_finite_case' for e in entries)) for g in ('PT','inverses','chains')} for cap in CAPS})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();data=build();save('implementation.json',data,a.write);save('ledger.json',ledger(data),a.write)
