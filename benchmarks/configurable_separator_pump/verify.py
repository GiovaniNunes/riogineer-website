"""Read-only byte preservation; optional create-once study manifest."""
import sys,hashlib,subprocess,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.configurable_separator_pump.common import *

def verify():
    b=read('baseline.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==b['head']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()==b['branch']
    assert subprocess.check_output(['git','diff','--cached','--binary'],cwd=ROOT).decode()==b['index_diff']==''
    for name,h in b['files'].items():
        if name=='docs/RIOGINEER_MASTER_CONTEXT.md':
            raw=(ROOT/name).read_bytes()[:b['master_bytes']];assert hashlib.sha256(raw).hexdigest()==h
        else:assert digest(ROOT/name)==h,name+' changed'
    return len(b['files'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args();n=verify()
    paths=sorted(p for p in HERE.iterdir() if p.is_file() and p.name!='manifest.json')
    paths.append(ROOT/'PRE_MILESTONE_21_CONFIGURABLE_SEPARATOR_PUMP_QUALIFICATION.md')
    save('manifest.json',dict(files={str(p.relative_to(ROOT)):digest(p) for p in paths}),args.write)
    print('PASS preserved',n,'original tracked files (master prefix protected); HEAD and empty index unchanged')
