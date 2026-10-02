"""Current-source integrity and session preservation, separate from historical pins."""
import sys,argparse,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.m21_pt200.common import *
CHANGED=frozenset('engine/riogineer_engine/'+n for n in ('property_packages.py','pr_ps_flash.py','pr_ph_flash.py','pump_energy.py'))

def preservation():
    b=read(HERE/'baseline.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==b['head']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==b['branch']
    assert subprocess.check_output(['git','diff','--cached','--binary'],cwd=ROOT,text=True)==b['index']==''
    for name,expected in b['files'].items():
        if name in CHANGED or name=='tests/separator-pump.test.ts':continue
        raw=(ROOT/name).read_bytes()
        if name=='docs/RIOGINEER_MASTER_CONTEXT.md':raw=raw[:b['master_bytes']]
        assert hashlib.sha256(raw).hexdigest()==expected,name+' unexpectedly changed'
    return b

def sources():
    paths=sorted((ROOT/'engine/riogineer_engine').glob('*.py'))+sorted((ROOT/'contracts/v1').glob('*.json'))+[ROOT/'engine/riogineer_engine/separator_pump_cases.json']
    return {str(p.relative_to(ROOT)):digest(p) for p in paths}

def source_verify():
    assert sources()==read(HERE/'source_manifest.json')['files'],'Current M21 source manifest differs'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture-source',action='store_true');p.add_argument('--write',action='store_true');a=p.parse_args();b=preservation()
    if a.capture_source:save('source_manifest.json',dict(files=sources(),baseline_head=b['head'],authorized_existing_source_changes=sorted(CHANGED)),True)
    else:
        source_verify()
        paths=sorted(p for p in HERE.rglob('*') if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts)
        paths += [ROOT/'MILESTONE_21.md',ROOT/'engine/tests/test_pt200_profile.py',ROOT/'tests/separator-pump.test.ts']
        appendix=(ROOT/'docs/RIOGINEER_MASTER_CONTEXT.md').read_bytes()[b['master_bytes']:]
        save('manifest.json',dict(files={str(p.relative_to(ROOT)):digest(p) for p in paths},master_appendix_sha256=hashlib.sha256(appendix).hexdigest()),a.write)
    print('PASS current source and preservation; four explicitly authorized existing production files may differ; all other baseline paths protected')
