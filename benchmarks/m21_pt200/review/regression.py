"""Separate historical byte integrity, current numerical regression and freshness."""
import hashlib,json,subprocess
from pathlib import Path
from .archive import verify as historical_manifest
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
# Specific review-owned files, not a source-directory exclusion.
REVIEW_EDITS=frozenset([
    'MILESTONE_21.md','benchmarks/m21_pt200/README.md',
    'benchmarks/m21_pt200/capture_sources.py','benchmarks/m21_pt200/m20_admission.py',
    'benchmarks/m21_pt200/verify.py','benchmarks/m21_pt200/inventory.json','benchmarks/m21_pt200/manifest.json',
    'engine/tests/test_separator_pump_integration.py','engine/tests/test_variable_pump_evidence.py',
])
def load(name):return json.loads((ROOT/name).read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def preservation():
    b=load('benchmarks/m21_pt200/review/baseline.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==b['head']
    assert subprocess.check_output(['git','diff','--cached','--binary'],cwd=ROOT,text=True)==b['index']==''
    for name,expected in b['files'].items():
        if name in REVIEW_EDITS:continue
        raw=(ROOT/name).read_bytes()
        if name=='docs/RIOGINEER_MASTER_CONTEXT.md':raw=raw[:b['master_bytes']]
        assert hashlib.sha256(raw).hexdigest()==expected,name
    # The old current manifest/inventory and original source replay are archived verbatim.
    for name in ('manifest.json','inventory.json','verification_results.json','verify.py','capture_sources.py'):
        assert digest(HERE/('prior_'+name))==b['files']['benchmarks/m21_pt200/'+name]
    return b

def historical_integrity(group):
    rows=[r for r in historical_manifest()['entries'] if r['group']==group]
    for row in rows:
        name=row['path']
        if name.startswith('engine/riogineer_engine/'):
            assert row['status']=='verified_git_blob',name
        elif name not in ('next-env.d.ts','tsconfig.json'):
            # Immutable artifacts remain checked in the actual working tree as well.
            assert digest(ROOT/name)==row['expected_sha256'],name
    return rows

def archived_m20_semantics():
    frozen=load('benchmarks/m20_separator_pump/implementation.json')
    historical=load('benchmarks/m21_pt200/review/historical_semantics.json')
    assert len(historical['cases'])==len(frozen['cases'])==30
    for row in frozen['cases']:
        assert row['result']['input_sha256']==historical['cases'][row['case_id']]
        assert row['result']['engine']['implementation_sha256']==historical['engine_sha256']
    return frozen

def current_m20():
    from benchmarks.m21_pt200.m20_admission import verify
    from riogineer_engine.core import build_flowsheet,semantic_hash,implementation_hash
    from riogineer_engine.milestone20 import requirements
    result=verify()
    for row in result['cases']:
        flowsheet=build_flowsheet(requirements(row['case_id']));actual=row['result']
        assert actual['input_sha256']==semantic_hash(flowsheet)
        assert actual['requirements_sha256']==flowsheet['requirements_sha256']
        assert actual['engine']['implementation_sha256']==implementation_hash()
    return result

def current_m19():
    from benchmarks.variable_composition_pump.compare_equipment import normalize
    from benchmarks.pump_energy.compare_production import compare
    from benchmarks.pump_energy.common import finish
    from riogineer_engine.milestone19 import requirements
    from riogineer_engine.core import build_flowsheet,calculate,semantic_hash,implementation_hash
    c=next(c for c in load('benchmarks/variable_composition_pump/reference.json')['cases'] if c['case_id']=='NEW_CANONICAL')
    i=c['inputs'];f=build_flowsheet(requirements(Tin=i['T1'],Pin=i['P1'],Pout=i['P2'],eta=i['eta'],F=i['flow'],z=i['z']));r=calculate(f);d=r['equipment'][0]['thermodynamics']
    states={k:normalize(d[v]) for k,v in [('inlet','inlet'),('isentropic','isentropic_outlet'),('outlet','actual_outlet')]}
    checks=compare(i,dict(c['result'],metrics=finish(i,c['result']['states'])),dict(states=states,metrics=finish(i,states),diagnostics={k.upper():dict(d[k],status='success') for k in ('ps','ph')}))
    assert checks and all(q['passed'] for q in checks)
    assert r['input_sha256']==semantic_hash(f) and r['engine']['implementation_sha256']==implementation_hash()
    return checks
