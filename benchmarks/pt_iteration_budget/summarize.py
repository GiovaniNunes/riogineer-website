"""Compact, deterministic index of the frozen evidence; read-only by default."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.pt_iteration_budget.common import *

def summary():
    p=read(HERE/'production.json');q=read(HERE/'qualified_ledger.json')
    result=dict(decision='A',recommended_profile=p['profiles'][1],scope='Finite PLAN.md matrix only; no production admission',
                ledger={k:v for k,v in q.items() if k!='entries'},cost={},challenges=[])
    for cap in CAPS:
        pts=[r['result'] for r in p['PT'] if r['cap']==cap]
        chains=[r for r in p['chains'] if r['cap']==cap]
        calls=[dict(case_id=r['case_id'],kind=k,**c) for r in chains for k,d in r['result']['diagnostics'].items() for c in d['calls']]
        result['cost'][str(cap)]=dict(PT_matrix_peak=max(r['PT']['diagnostics']['iterations'] for r in pts),
            inverse_PT_evaluations=len(calls),inverse_equilibrium_iterations=sum(c['equilibrium_iterations'] for c in calls),
            failed_inverse_PT_evaluations=sum(not c['status'].startswith('success') for c in calls),
            peak_inverse_call=max(calls,key=lambda c:c['equilibrium_iterations']))
        for row in chains:
            if row['case_id'].endswith('8000000.0'):
                r=row['result'];record=dict(cap=cap,case_id=row['case_id'],status=r['status'],stage=r['stage'])
                if 'metrics' in r:
                    record.update(states={k:{n:v for n,v in s.items() if n in ('T_K','P_Pa_abs','H_eq_J_mol','S_eq_J_mol_K','beta','z','classification')} for k,s in r['states'].items()},
                                  metrics=r['metrics'],energy=r['energy'],retained_upstream_Hdot_W=r['retained_upstream_Hdot_W'])
                result['challenges'].append(record)
    by={(r['case_id'],r['cap']):r['result'] for r in p['PT']}
    result['compatibility']=dict(legacy_successful_PT_pairs=len(p['compatibility']),
        legacy_pairs_exact=all(r['same_iteration_sequence'] and r['same_payload_and_diagnostics'] for r in p['compatibility']),
        PT_200_400_exact=sum(all(by[(c['case_id'],200)][k]==by[(c['case_id'],400)][k] for k in ('trace_sha256','result_without_budget_sha256')) for c in pt_cases()),
        legacy_inverse_anchors_exact=all(r['legacy_equal'] for r in p['inverses'] if r['cap']==100))
    result['timings']=[{k:r[k] for k in ('case_id','kind','cap','median_seconds','deterministic')} for r in read(HERE/'performance.json')['records']]
    result['artifact_sha256']={n:digest(HERE/n) for n in ('production.json','qualified_ledger.json','reference.json','phase_identity_reference.json','phase_identity_comparison.json','performance.json')}
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    save('summary.json',summary(),args.write)
