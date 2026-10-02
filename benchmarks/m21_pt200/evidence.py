"""Compare current numerical results to frozen independent and legacy evidence."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.m21_pt200.common import *

def build():
    current=read(HERE/'implementation.json');old=read(FROZEN/'production.json');ledger=read(HERE/'ledger.json')
    checks=[]
    def check(label,passed):checks.append(dict(field=label,passed=bool(passed)))
    for group in ('PT','inverses','chains'):
        baseline={(r['case_id'],r['cap'],r.get('kind')):r for r in old[group]}
        for row in current[group]:
            previous=baseline[row['case_id'],row['cap'],row.get('kind')];label=f"{group}:{row['case_id']}:{row['cap']}:{row.get('kind')}"
            if group=='PT':
                for k in ('status','trace_sha256','trace_events','result_without_budget_sha256'):check(label+':'+k,row['result'][k]==previous['result'][k])
            elif group=='inverses':
                for k in ('status','state','record'):check(label+':'+k,numerical(row[k])==numerical(previous[k]))
            else:
                for k in ('status','states','metrics','diagnostics','energy','retained_upstream_Hdot_W','component_rates'):
                    check(label+':'+k,numerical(row['result'].get(k))==numerical(previous['result'].get(k)))
    check('independent_comparisons',ledger['failed_comparisons']==0)
    for cap,pt_count,chain_count in ((100,41,6),(200,70,12)):
        for group,count in (('PT',pt_count),('inverses',6),('chains',chain_count)):
            check(f'count:{cap}:{group}',ledger['profile_counts'][str(cap)][group]['accepted']==count)
    check('M20_30_admitted',len(current['application_scope'])==32 and all(r['admitted'] for r in current['application_scope'][:30]))
    check('8MPa_still_excluded',all(not r['admitted'] for r in current['application_scope'][30:]))
    peaks=[]
    for row in current['chains']:
        for kind,d in row['result']['diagnostics'].items():
            trials=d['diagnostics']['trials'] if 'trials' in d['diagnostics'] else None
            for call in d['calls']:
                expected='pr_high_accuracy_pt200@1' if row['cap']==200 else None
                check(f"propagation:{row['case_id']}:{row['cap']}:{kind}:{call['T']}",call['pt_settings'].get('numerical_profile')==expected and call['pt_settings']['flash_max_iterations']==row['cap'])
                check('bounded_PT',call['equilibrium_iterations']<=row['cap'])
                peaks.append(call['equilibrium_iterations'])
    check('peak199',max(peaks)==199)
    audit=read(FROZEN/'phase_identity_reference.json')
    check('independent_identity',not audit['production_imported'] and all(r['status']=='verified' for r in audit['cases']) and sum(r['swapped'] for r in audit['cases'])==6)
    check('raw195_preserved',read(FROZEN/'qualified_ledger.json')['raw_named_reference_failed_comparisons']==195)
    return dict(checks=checks,failed_checks=sum(not c['passed'] for c in checks),comparison_count=len(checks),independent_ledger={k:v for k,v in ledger.items() if k!='entries'},peak_iterations=max(peaks),implementation_sha256=digest(HERE/'implementation.json'),frozen_production_sha256=digest(FROZEN/'production.json'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();result=build();save('evidence.json',result,a.write)
    assert result['failed_checks']==0,result['failed_checks']
