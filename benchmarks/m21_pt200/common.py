"""Current-source verification against unchanged qualification inputs."""
from benchmarks.pt_iteration_budget.common import *
HERE=ROOT/'benchmarks/m21_pt200'
FROZEN=ROOT/'benchmarks/pt_iteration_budget'
CAPS=(100,200)

def save(name,value,write=False):
    p=HERE/name;raw=encode(value)
    if write:
        assert not p.exists(),str(p)+' already exists'
        p.write_text(raw)
    else:assert p.read_text()==raw,name+' differs'
    print(name,digest(p),flush=True)

def numerical(v):
    # Only the new explicitly named settings provenance is excluded for comparison
    # to the unlabelled experimental 200 controls. No numerical field is removed.
    if isinstance(v,dict):return {k:numerical(x) for k,x in v.items() if k!='numerical_profile'}
    if isinstance(v,(list,tuple)):return [numerical(x) for x in v]
    return v
