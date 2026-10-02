"""Extension integrity/ledger; never rerun or rewrite the first study."""
import argparse,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from benchmarks.low_pressure_separator_pump.phase_contract.common import *

def preservation():
    baseline=read(HERE/'baseline.json')
    for path,h in read(HERE/'preservation.json').items():
        if path=='docs/RIOGINEER_MASTER_CONTEXT.md':
            raw=(ROOT/path).read_bytes()[:baseline['master_prefix_bytes']]
            assert hashlib.sha256(raw).hexdigest()==h,path+' original prefix changed'
        else:assert digest(ROOT/path)==h,path
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==baseline['head']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='main'
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)

def build():
    preservation();r=read(HERE/'reference.json');p=read(HERE/'production.json')
    assert r['prior_reference_sha256']==digest(OLD/'reference.json')
    assert r['source_sha256']==digest(HERE/'reference.py') and r['plan_sha256']==digest(HERE/'PLAN.md')
    assert p['reference_sha256']==digest(HERE/'reference.json') and p['sources_sha256']==digest(HERE/'sources.json')
    for name,h in p['source_sha256'].items():assert digest(HERE/name)==h,name
    assert p['failed_checks']==0 and all(c['passed'] for c in p['negatives'])
    assert all(c['status']=='accepted' for c in p['qualified_tuples'])
    rows=[]
    for c in p['qualified_tuples']:rows.append(dict(case_id=c['case_id'],group='prior_tuple_local_qualification',status=c['status'],source=c['source']))
    for c in p['new_probes']:rows.append(dict(case_id=c['case_id'],group=c['kind'],status=c['local_without_source']['status']))
    for c in p['negatives']:rows.append(dict(case_id=c['case_id'],group='contract_negative',status=c['result']['status'],reason=c['result']['reason']))
    rows.extend(p['known_unresolved'])
    return dict(decision='A: sufficient for future production restricted to the explicit qualified tuples; no implementation',
        comparisons=p['comparison_count'],cases=rows,
        proposed_production_allowlist=[dict(case_id=c['case_id'],source_input_sha256=read(HERE/'sources.json')['sources'][source_key(c)]['result']['input_sha256'],P2=c['inputs']['P2'],eta=c['inputs']['eta']) for c in accepted()],
        sha256={f.name:digest(f) for f in sorted(HERE.iterdir()) if f.is_file() and f.name!='candidate_ledger.json'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('candidate_ledger.json',build(),p.parse_args().write)
