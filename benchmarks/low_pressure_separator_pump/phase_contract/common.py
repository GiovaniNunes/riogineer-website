"""Extension bookkeeping, immutable old expectations and provenance hashes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OLD=HERE.parent
IDS=('methane','n_hexane')

def encode(x):return json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashed(x):return hashlib.sha256(encode(x).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(name,x,write=False):
    p=HERE/name;raw=encode(x)
    if write:p.write_text(raw)
    else:assert p.read_text()==raw,name+' differs'
    print(name,digest(p),flush=True)
def accepted():return [c for c in read(OLD/'production.json')['cases'] if c['disposition']=='accepted_tuple']
def source_key(c):return c['case_id'] if c['role']=='scaled_flow' else c['source']
def source_specs():
    historical={c['case_id']:c['inputs'] for c in read(ROOT/'benchmarks/two_phase_separator_energy/methane_nhexane_separator_energy_reference.json')['cases']}
    specs={c['source']:historical[c['source']] for c in accepted()}
    specs['PT_VAPOR']=historical['PT_VAPOR']
    for c in accepted():
        if c['role']=='scaled_flow':
            old=next(x for x in accepted() if x['case_id']=='PH_FLASH_DP1000000.0')
            specs[source_key(c)]=historical['PH_FLASH']|dict(F=100*c['inputs']['flow']/old['inputs']['flow'])
    return specs
