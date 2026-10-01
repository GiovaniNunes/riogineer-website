"""Read-only evidence/source integrity and qualified work-policy equivalence."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'engine'))
from benchmarks.pump_energy.configurable_scope.policy import work_policy
from benchmarks.pump_energy.m18.compare_equipment import normalize
HERE=Path(__file__).resolve().parent


def verify():
    result=json.loads((HERE/'equipment_comparison.json').read_text())
    preserved=json.loads((HERE/'preservation.json').read_text())
    checks=[]
    for kind,rows in [('production',result['production_source_sha256']),('reference',result['reference_sha256']),
                      ('preserved',{p:v['baseline_sha256'] for p,v in preserved['files'].items()})]:
        for p,h in rows.items():
            checks.append(dict(field=kind+':'+p,passed=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h))
    for row in result['cases']:
        if not row['expected_accepted']:continue
        d=next(c['actual'] for c in row['checks'] if c['field']=='callable_adapter_details')
        if d['mode']=='identity':continue
        states={k:normalize(d[v]) for k,v in [('inlet','inlet'),('isentropic','isentropic_outlet'),('outlet','actual_outlet')]}
        policy=work_policy(row['inputs'],states)
        for field,key in [('work_screening_allowance_J_mol','budget_J_mol'),('work_screening_ratio','ratio')]:
            checks.append(dict(field=row['case_id']+':'+field,actual=d[field],expected=policy[key],passed=d[field]==policy[key]))
    output=dict(check_count=len(checks),passed=all(c['passed'] for c in checks),checks=checks)
    (HERE/'evidence_verification.json').write_text(json.dumps(output,indent=2)+'\n')
    assert output['passed'],[c for c in checks if not c['passed']]
    print(f"{len(checks)} source/preservation/work-policy checks passed")

if __name__=='__main__':verify()
