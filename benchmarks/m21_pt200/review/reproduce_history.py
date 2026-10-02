"""Read-only historical source and semantic identity reproduction from Git."""
import json, hashlib, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
expected=json.loads((HERE/'historical_semantics.json').read_text())
coherent='2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0'
pins=json.loads((ROOT/'benchmarks/variable_composition_pump/equipment_comparison.json').read_text())['production_source_sha256']
for path,digest in pins.items():
    raw=subprocess.check_output(['git','show',coherent+':'+path],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()==digest,path
with tempfile.TemporaryDirectory(prefix='m21-historical-') as temp:
    raw=subprocess.check_output(['git','archive',expected['commit'],'engine/riogineer_engine','engine/fixtures','contracts'],cwd=ROOT)
    subprocess.run(['tar','-x','-C',temp],input=raw,check=True)
    code="""
import json
from riogineer_engine.core import build_flowsheet, semantic_hash, implementation_hash
from riogineer_engine.milestone20 import requirements
from riogineer_engine.separator_pump_scope import CASES
print(json.dumps(dict(engine_sha256=implementation_hash(),cases={r['qualification_id']:semantic_hash(build_flowsheet(requirements(r['qualification_id']))) for r in CASES})))
"""
    env=dict(os.environ,PYTHONPATH=str(Path(temp)/'engine'),PYTHONDONTWRITEBYTECODE='1')
    actual=json.loads(subprocess.check_output([sys.executable,'-B','-c',code],cwd=temp,env=env,text=True))
assert actual=={k:v for k,v in expected.items() if k!='commit'}
print(json.dumps(dict(m19_coherent_commit=coherent,source_pins=len(pins),m20_semantic_commit=expected['commit'],semantic_identities=len(actual['cases']),historical_numerical_solver_rerun=False),indent=2))
