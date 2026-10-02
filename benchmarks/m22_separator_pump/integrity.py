"""Current M22 integrity, distinct from archived M21 source identity."""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
# Exact authorized existing paths; no directory-wide historical exclusions.
CHANGED=frozenset([
 'docs/RIOGINEER_MASTER_CONTEXT.md',
 'engine/riogineer_engine/core.py','engine/riogineer_engine/network.py',
 'engine/riogineer_engine/separator_liquid_pump.py','engine/riogineer_engine/separator_pump_process.py','engine/riogineer_engine/separator_pump_scope.py',
 'src/lib/digital-engineer/contracts.ts','src/app/digital-engineer/workspace.tsx',
 'src/app/digital-engineer/pfd.tsx','src/app/digital-engineer/separator-pump-results.tsx',
 'contracts/v1/requirements.schema.json','contracts/v1/flowsheet.schema.json','contracts/v1/results.schema.json','contracts/v1/validation.schema.json',
 'engine/tests/test_separator_pump_integration.py','engine/tests/test_variable_pump_evidence.py','engine/tests/test_pt200_profile.py',
])
def read(path):return json.loads((ROOT/path).read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def sources():
    paths=sorted((ROOT/'engine/riogineer_engine').glob('*.py'))+sorted((ROOT/'contracts/v1').glob('*.json'))+sorted((ROOT/'engine/riogineer_engine').glob('separator_pump*cases.json'))
    return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths}
def source_verify():
    assert sources()==read('benchmarks/m22_separator_pump/source_manifest.json')['files'],'M22 current source differs'
    # Old M21 source expectations describe the committed baseline, not current M22.
    old=read('benchmarks/m21_pt200/source_manifest.json')['files']
    baseline=read('benchmarks/m22_separator_pump/baseline.json')
    for name,expected in old.items():
        assert baseline['files'][name]==expected,name
        blob=subprocess.check_output(['git','show',baseline['head']+':'+name],cwd=ROOT)
        assert sha(blob)==expected,name
    return True

def preservation():
    b=read('benchmarks/m22_separator_pump/baseline.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==b['head']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==b['branch']
    assert subprocess.check_output(['git','diff','--cached','--binary'],cwd=ROOT,text=True)==''
    for name,expected in b['files'].items():
        if name in CHANGED and name!='docs/RIOGINEER_MASTER_CONTEXT.md':continue
        raw=(ROOT/name).read_bytes()
        if name=='docs/RIOGINEER_MASTER_CONTEXT.md':raw=raw[:b['master_bytes']]
        assert sha(raw)==expected,name
    return b

if __name__=='__main__':
    preservation();source_verify();print('PASS M22 current source, archived M21 source, preserved historical files/configs/master prefix/HEAD/index')
