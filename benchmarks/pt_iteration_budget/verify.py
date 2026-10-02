"""Preserve the task-start tree and verify this extension, without rewriting."""
import sys,argparse,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.pt_iteration_budget.common import *

def verify():
    b=read(HERE/'baseline.json')
    for command,expected in ((['rev-parse','HEAD'],b['head']),(['branch','--show-current'],b['branch'])):
        assert subprocess.check_output(['git',*command],cwd=ROOT).decode().strip()==expected
    assert subprocess.check_output(['git','diff','--cached','--binary'],cwd=ROOT).decode()==b['index']==''
    for name,expected in b['files'].items():
        raw=(ROOT/name).read_bytes()
        if name=='docs/RIOGINEER_MASTER_CONTEXT.md':raw=raw[:b['master_bytes']]
        assert hashlib.sha256(raw).hexdigest()==expected,name+' changed'
    return b

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args();b=verify()
    paths=sorted(p for p in HERE.rglob('*') if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts)
    paths.append(ROOT/'PRE_MILESTONE_21_PT_ITERATION_BUDGET_QUALIFICATION.md')
    appendix=(ROOT/'docs/RIOGINEER_MASTER_CONTEXT.md').read_bytes()[b['master_bytes']:]
    save('manifest.json',dict(files={str(p.relative_to(ROOT)):digest(p) for p in paths},master_appendix_sha256=hashlib.sha256(appendix).hexdigest()),args.write)
    print('PASS:',len(b['files']),'task-start paths preserved; master prefix, HEAD, branch and empty index unchanged')
