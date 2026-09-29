"""M8.2 production comparison; frozen authority is read-only. No PH inversion."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'engine')]
from benchmarks.peng_robinson_pt_boundary import compare_production as prior
from riogineer_engine.pr_flash import SolverSettings, wilson
from riogineer_engine.pr_eos import PengRobinsonEOS
from riogineer_engine.rachford_rice import solve_rr

HERE = Path(__file__).resolve().parent
REFERENCE = HERE/'methane_nhexane_pt_vapor_parent_reference.json'
REFERENCE_SHA256 = '27a54f54314d54b882229df653472b0f5a4581d85f958fb451b6259fbaf54c91'


def read_reference():
    raw = REFERENCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REFERENCE_SHA256:
        raise ValueError('Frozen Pre-M8.2 integrity mismatch')
    r = json.loads(raw)
    if r['identity'] != 'independent_pr_pt_vapor_parent_restart@1.0' or len(r['cases']) != 13:
        raise ValueError('Unexpected frozen identity/matrix')
    return r


def context():
    r = read_reference()
    old = prior.read_reference()
    # Reuse prior production adapter and inherited field-specific comparisons.
    old['metadata'] = dict(old['metadata'], component_order=r['components'],
                           kij=r['kij'], BIP_provenance=r['BIP_provenance'])
    return r, old


def checked(checks):
    failures = [c for c in checks if not c['passed']]
    if failures:
        raise AssertionError(json.dumps(failures,indent=2))


def build():
    r, ctx = context(); rows=[]; checks=[]
    for c in r['cases']:
        e = c['independent_equilibrium']
        state,bip = prior.inputs(ctx,e)
        rr = solve_rr(e['z'],wilson(PengRobinsonEOS(bip.component_ids,e['T_K'],e['P_Pa_abs'],bip)))
        for label,settings in [('standard',SolverSettings()),('high_accuracy',SolverSettings.high_accuracy())]:
            a = prior.evaluate(ctx,e,settings)
            init = a['diagnostics']['initialization']; stab=a['diagnostics']['stability']
            local=prior.compare(ctx,a,e)
            prior.equal(local,'stability converged',stab['converged'],True)
            prior.equal(local,'stability stable',stab['stable'],e['classification']=='single_vapor')
            prior.equal(local,'Wilson physical root',rr.status=='two_phase',c['stability']['Wilson_RR']['physical_interior_root'])
            prior.equal(local,'restart count',init['restart_count'],int(c['restart_required']))
            prior.equal(local,'resolved profile',a['settings']['profile'],label)
            prior.equal(local,'resolved target',a['settings']['fugacity_tolerance'],settings.fugacity_tolerance)
            if c['restart_required']:
                seed=init['restart_seed']
                prior.equal(local,'orientation',seed['orientation'],'vapor_parent_liquid_trial')
                prior.equal(local,'restart RR',init['restart_rr']['status'],'two_phase')
                prior.equal(local,'restart interior beta',0 < init['restart_rr']['beta'] < 1,True)
                prior.equal(local,'seed formula',seed['K'],tuple(zi/(seed['stability_sum']*wi) for zi,wi in zip(e['z'],seed['trial_composition'])))
            else:
                prior.equal(local,'no restart seed',init['restart_seed'],None)
            for check in local:
                check['case_id']=c['case_id'];check['profile']=label
                if 'absolute_error' in check:
                    check['relative_error']=check['absolute_error']/abs(check['reference']) if check['reference'] else None
            checked(local); checks.extend(local)
            rows.append(dict(case_id=c['case_id'],original_failure=c['original_failure'],profile=label,
                             frozen_phase=e['classification'],production=a,Wilson_RR=asdict(rr),comparisons=local))
    target=next(c['independent_equilibrium'] for c in r['cases'] if c['original_failure'])
    first=prior.evaluate(ctx,target)
    high=prior.evaluate(ctx,target,SolverSettings.high_accuracy())
    prior.equal(checks,'standard/high/standard isolation',prior.evaluate(ctx,target),first)
    prior.equal(checks,'high repeat deterministic',prior.evaluate(ctx,target,SolverSettings.high_accuracy()),high)
    stable=r['cases'][-1]['independent_equilibrium']
    prior.evaluate(ctx,stable)
    prior.equal(checks,'after stable vapor identical',prior.evaluate(ctx,target),first)
    old=prior.read_reference()
    bubble=next(c['reference'] for c in old['bubble_cases'] if c['case_id']=='BUBBLE_CENTER')
    bubble_result=prior.evaluate(old,bubble)
    checks.extend(prior.compare(old,bubble_result,bubble))
    seed=bubble_result['diagnostics']['initialization']['restart_seed']
    prior.equal(checks,'M8.1 orientation',seed['orientation'],'liquid_parent_vapor_trial')
    prior.equal(checks,'M8.1 formula',seed['K'],tuple(seed['stability_sum']*wi/zi for zi,wi in zip(bubble['z'],seed['trial_composition'])))
    prior.equal(checks,'after M8.1 identical',prior.evaluate(ctx,target),first)
    dew=prior.evaluate(old,old['dew_reference'],SolverSettings.high_accuracy(),True)
    checks.extend(prior.compare(old,dew,old['dew_reference'],True))
    checked(checks)
    maxima={}
    for c in checks:
        if 'absolute_error' not in c:continue
        q=c['quantity']; m=maxima.setdefault(q,dict(max_absolute_error=0.,max_relative_error=None,max_allowance_fraction=0.))
        m['max_absolute_error']=max(m['max_absolute_error'],c['absolute_error'])
        if c['reference']:
            m['max_relative_error']=max(m['max_relative_error'] or 0.,c['absolute_error']/abs(c['reference']))
        m['max_allowance_fraction']=max(m['max_allowance_fraction'],c['allowance_fraction'])
    return dict(reference_id=r['identity'],reference_sha256=REFERENCE_SHA256,rows=rows,
                M8_1_bubble=bubble_result,high_accuracy_dew=dew,comparisons=len(checks),
                maxima=maxima,passed=True)


def scan():
    """Exact frozen input grids; independent trials, no continuation or PH root solver."""
    _,ctx=context()
    path=ROOT/'benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json'
    r=json.loads(path.read_text()); grids={}
    for c in r['cases']:
        rows=c['inverse']['diagnostics']['scan']
        key=(c['input']['P_Pa_abs'],tuple(c['input']['z']),tuple(v['T_K'] for v in rows))
        grids.setdefault(key,rows)
    if len(grids)!=9 or sum(map(len,grids.values()))!=1152:
        raise ValueError('Frozen grid coverage changed')
    counts=Counter(); results=[]
    for rows in grids.values():
        for frozen in rows:
            a=prior.evaluate(ctx,frozen,SolverSettings.high_accuracy())
            init=a['diagnostics']['initialization']; seed=init['restart_seed']
            if init['restart_count'] > 1:raise AssertionError('Unbounded restart')
            if seed:counts[seed['orientation']]+=init['restart_count']
            results.append(dict(T_K=a['T_K'],P_Pa_abs=a['P_Pa_abs'],z=a['z'],
                status=a['status'],classification=a['classification'],beta=a['beta'],
                restart_count=init['restart_count'],orientation=seed['orientation'] if seed else None))
    return dict(grids=len(grids),total=len(results),successful=len(results),unexpected_failures=0,
                restarts_by_orientation=dict(counts),frozen_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),states=results)


def display(e, selection):
    print('T / profile / frozen phase / production phase / stable / Wilson root / orientation / restarts / beta / max log-fugacity / result')
    for row in e['rows']:
        if selection=='former_failures' and not row['original_failure']:continue
        if selection=='representative' and row['production']['T_K']!=225.98425196850394:continue
        p=row['production'];i=p['diagnostics']['initialization'];seed=i['restart_seed']
        print(p['T_K'],row['profile'],row['frozen_phase'],p['classification'],p['diagnostics']['stability']['stable'],
              row['Wilson_RR']['status']=='two_phase',seed['orientation'] if seed else 'none',i['restart_count'],p['beta'],
              max(map(abs,p['log_fugacity_residual']),default=0.),'PASS')
    if selection in ('representative','former_failures'):
        for row in e['rows']:
            if row['original_failure'] and (selection!='representative' or row['production']['T_K']==225.98425196850394):
                print('Errors:',row['production']['T_K'],row['profile'])
                for c in row['comparisons']:
                    if c['quantity']=='beta' or '.composition.' in c['quantity'] or c['quantity'].endswith('.Z') or c['quantity'].startswith('K.'):
                        print(c['quantity'],'production=',c['actual'],'reference=',c['reference'],'abs=',c['absolute_error'],'rel=',c['relative_error'],'allowance=',c['allowed_error'],'PASS')
    if selection=='orientations':
        print('M8.1 seed:',e['M8_1_bubble']['diagnostics']['initialization']['restart_seed'])
    print(f"PASS: {e['comparisons']} comparisons; both profiles; isolation, determinism and call order passed")
    print('Human-operated M8.2 validation remains pending. M11 not implemented.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=['representative','former_failures','neighborhood','orientations','scan','all'],default='neighborhood')
    p.add_argument('--write',action='store_true',help='Write production evidence only')
    args=p.parse_args();e=build()
    if args.case!='scan':display(e,args.case)
    if args.case in ('scan','all') or args.write:
        e['complete_scan']=scan()
        print('High-accuracy scan:',{k:v for k,v in e['complete_scan'].items() if k!='states'})
    if args.write:
        (HERE/'production_comparison.json').write_text(json.dumps(e,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
