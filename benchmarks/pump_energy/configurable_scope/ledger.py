"""Complete extension disposition; no recalculation or omission of failed candidates."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from benchmarks.pump_energy.configurable_scope.policy import HERE,REFERENCE,PRODUCTION
from benchmarks.pump_energy.configurable_scope.runtime import admissibility
from benchmarks.pump_energy.common import digest,encode


def build():
    ref,prod=[json.loads(p.read_text()) for p in (REFERENCE,PRODUCTION)]
    assert prod['reference_sha256']==digest(REFERENCE)
    rows=[]
    for r,p in zip(ref['cases'],prod['cases']):
        assert r['case_id']==p['case_id']
        runtime=admissibility(r['inputs'],p['result'],p['witnesses'])
        rows.append(dict(case_id=r['case_id'],group=r['group'],inputs=r['inputs'],
            independent_status=r['result']['status'],production_status=p['result']['status'],
            reference_policy=r['policy'],production_policy=runtime,
            independent_evidence_origin=r['evidence_origin'],production_evidence_origin=p['evidence_origin'],
            compared_fields_pass=all(q['passed'] for q in p['checks']),
            flow_pass=all(q['passed'] for f in p['flow_checks'] for q in f['checks'])))
    alternates=[dict(T_K=r['T_K'],returned_T_K=r['T_K']+r['roundtrip_T_error_K'],
        classification='unrestricted saturation inverse selected another branch; retained, not used by runtime')
        for r in ref['boundary']['rows'] if r['status']=='available' and abs(r['roundtrip_T_error_K'])>1e-5]
    return dict(artifact_sha256={p.name:digest(p) for p in (REFERENCE,PRODUCTION,HERE/'boundary_refinement.json',HERE/'boundary_equations.json')},
        runtime_source_sha256=digest(HERE/'runtime.py'),rows=rows,boundary_alternate_returns=alternates,
        runtime_counts=dict(Counter(r['production_policy']['reason'] for r in rows)),
        statement='Configurable bounds and diagnostic policy; runtime reads no reference table or allowlist')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
    path=HERE/'candidate_ledger.json';raw=encode(build())
    if args.write:path.write_text(raw)
    else:assert path.read_text()==raw,'Extension ledger reproduction differs'
    print('PASS extension ledger')
