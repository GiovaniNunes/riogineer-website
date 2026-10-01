"""Freeze/verify candidate ledger and integrity, never write historical evidence."""
import argparse,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.low_pressure_separator_pump.common import *

def verify_preservation():
    old=json.loads((HERE/'preservation.json').read_text())
    for p,h in old.items():
        if p!='docs/RIOGINEER_MASTER_CONTEXT.md':assert digest(ROOT/p)==h,p
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()=='2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0'

def build():
    verify_preservation()
    r=json.loads((HERE/'reference.json').read_text());p=json.loads((HERE/'production.json').read_text())
    assert p['reference_sha256']==digest(HERE/'reference.json')
    for name,h in r['source_sha256'].items():assert digest(ROOT/name)==h,name
    rows=[]
    for a,b in zip(r['cases'],p['cases']):
        rows.append(dict(case_id=a['case_id'],source=a['source'],role=a['role'],inputs=a['inputs'],
            reference=a['policy'],production=b['policy'],stage=b['result'].get('stage'),
            disposition=b['disposition'],failed_checks=[c['field'] for c in b['checks'] if not c['passed']],
            production_extension=False))
    return dict(scope='Numerical tuples only; no production extension yet',cases=rows,
        counts={k:sum(c['disposition']==k for c in rows) for k in ('accepted_tuple','rejected','unresolved')},
        sha256={p.name:digest(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='candidate_ledger.json'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
    save('candidate_ledger.json',build(),a.write)
