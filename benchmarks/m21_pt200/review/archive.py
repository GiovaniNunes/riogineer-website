"""Recover historical pinned bytes from Git, never substitute current hashes."""
import sys,json,hashlib,subprocess,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def pins():
    m19=read('benchmarks/variable_composition_pump/equipment_comparison.json')
    m20=read('benchmarks/m20_separator_pump/baseline.json')['sha256']
    protected={p:h for p,h in m20.items() if p.startswith('benchmarks/low_pressure_separator_pump/') or p.startswith('PRE_MILESTONE_20_') or p in ('next-env.d.ts','tsconfig.json') or (p.startswith('engine/riogineer_engine/') and p not in ('engine/riogineer_engine/core.py','engine/riogineer_engine/network.py'))}
    return {'M19':m19['production_source_sha256']|m19['reference_sha256'],'M20':protected}

def recover():
    rows=[];cache={}
    for group,entries in pins().items():
        for name,expected in entries.items():
            key=(name,expected)
            if key not in cache:
                commits=subprocess.check_output(['git','log','--all','--format=%H','--',name],cwd=ROOT,text=True).splitlines()
                found=None
                for commit in commits:
                    q=subprocess.run(['git','show',commit+':'+name],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                    if q.returncode==0 and sha(q.stdout)==expected:
                        dest=HERE/'historical'/expected;dest.parent.mkdir(exist_ok=True)
                        if dest.exists():assert dest.read_bytes()==q.stdout
                        else:dest.write_bytes(q.stdout)
                        found=dict(status='verified_git_blob',commit=commit,snapshot=str(dest.relative_to(ROOT)));break
                if not found and sha((ROOT/name).read_bytes())==expected:
                    dest=HERE/'historical'/expected;dest.parent.mkdir(exist_ok=True)
                    if not dest.exists():dest.write_bytes((ROOT/name).read_bytes())
                    found=dict(status='verified_existing_bytes',snapshot=str(dest.relative_to(ROOT)))
                cache[key]=found or dict(status='unavailable',searched_commits=commits,reason='No matching historical bytes found in reachable path history or current file')
            rows.append(dict(group=group,path=name,expected_sha256=expected,**cache[key]))
    return dict(entries=rows,scope='Pinned-byte integrity only; not a historical numerical solver rerun')

def verify():
    manifest=json.loads((HERE/'historical_manifest.json').read_text());expected={(g,p):h for g,ps in pins().items() for p,h in ps.items()}
    assert {(r['group'],r['path']):r['expected_sha256'] for r in manifest['entries']}==expected
    for row in manifest['entries']:
        if row['status']!='unavailable':assert sha((ROOT/row['snapshot']).read_bytes())==row['expected_sha256'],row['path']
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--recover',action='store_true');p.add_argument('--require-complete',action='store_true');a=p.parse_args()
    if a.recover:
        target=HERE/'historical_manifest.json';assert not target.exists();target.write_text(json.dumps(recover(),indent=2,sort_keys=True)+'\n')
    r=verify();missing=[x for x in r['entries'] if x['status']=='unavailable'];print('Historical pinned entries:',len(r['entries']),'verified:',len(r['entries'])-len(missing),'unavailable:',[(x['path'],x['expected_sha256']) for x in missing])

    if a.require_complete and missing:sys.exit(1)
