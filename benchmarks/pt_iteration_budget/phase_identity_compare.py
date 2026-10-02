"""Supplementary comparisons; raw failures remain immutable and visible."""
import sys,argparse,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.pt_iteration_budget.common import *
from benchmarks.pump_energy.compare_production import compare

def build():
    production=read(HERE/'production.json');refs={r['case_id']:r for r in read(HERE/'phase_identity_reference.json')['cases']};rows=[]
    invariant={'initial_stability_converged','initial_stability_conclusion','final_common_tangent','fugacity_gate','material_gate','independent_fugacity_gate'}
    for row in production['PT']:
        r=row['result'];ref=refs[row['case_id']];checks=[]
        if r['state'] and ref['status']=='verified':
            checks=compare({},dict(states={'PT':ref['state']}),dict(states={'PT':r['state']},diagnostics={}))
            checks += [q for q in row['checks'] if q['field'] in invariant]
            for phase in r['PT']['phases']:
                for j,v in enumerate(phase['ln_phi']):
                    e=ref['lnphis'][phase['identifier']][j];checks.append(dict(field=phase['identifier']+'.ln_phi'+str(j),actual=v,reference=e,allowance=2e-9,passed=abs(v-e)<=2e-9))
        rows.append(dict(case_id=row['case_id'],cap=row['cap'],status=r['status'],reference_identity=ref['status'],reference_swapped=ref.get('swapped'),checks=checks,
                         raw_failed_checks=sum(not q['passed'] for q in row['checks'])))
    return dict(cases=rows,comparison_count=sum(len(r['checks']) for r in rows),failed_comparisons=sum(not q['passed'] for r in rows for q in r['checks']),
                production_sha256=digest(HERE/'production.json'),identity_reference_sha256=digest(HERE/'phase_identity_reference.json'))

def ledger(data):
    raw=read(HERE/'candidate_ledger.json');p=read(HERE/'production.json');out=copy.deepcopy(raw)
    mapped={(r['case_id'],r['cap']):r for r in data['cases']}
    for e in out['entries']:
        if e['group']=='PT':
            r=mapped[e['case_id'],e['cap']];e['raw_named_reference_disposition']=e['disposition'];e['raw_failed_checks']=r['raw_failed_checks'];e['reference_mapping_verified']=r['reference_identity']=='verified';e['reference_swapped']=r['reference_swapped']
            e['comparisons_passed']=bool(r['checks']) and all(q['passed'] for q in r['checks'])
            e['disposition']='accepted_finite_case' if e['status'].startswith('success') and e['comparisons_passed'] else 'unresolved'
    checks=[q for c in data['cases'] for q in c['checks']]+[q for g in ('inverses','chains') for c in p[g] for q in c['checks']]+[q for cs in p['source_checks'].values() for q in cs]
    out.update(raw_named_reference_failed_comparisons=raw['failed_comparisons'],comparison_count=len(checks),failed_comparisons=sum(not q['passed'] for q in checks),
        scalar_comparison_count=sum('actual' in q and isinstance(q['actual'],(int,float)) and not isinstance(q['actual'],bool) for q in checks))
    for cap in CAPS:
        for group in ('PT','inverses','chains'):
            out['profile_counts'][str(cap)][group]['accepted']=sum(e['group']==group and e['cap']==cap and e['disposition']=='accepted_finite_case' for e in out['entries'])
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();data=build();save('phase_identity_comparison.json',data,a.write);save('qualified_ledger.json',ledger(data),a.write)
