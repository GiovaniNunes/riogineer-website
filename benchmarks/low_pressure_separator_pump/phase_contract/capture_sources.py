"""Capture real separator calculation identities once; verify without replacing UUIDs."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]));sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'engine'))
from benchmarks.low_pressure_separator_pump.phase_contract.common import *
from riogineer_engine.milestone17 import requirements
from riogineer_engine.core import build_flowsheet,calculate

def main(write):
    path=HERE/'sources.json'
    if write:assert not path.exists(),'Source captures are immutable; do not regenerate'
    frozen={} if write else read(path)['sources'];sources={}
    for name,i in source_specs().items():
        f=build_flowsheet(requirements(**i));r=calculate(f)
        if not write:
            a=frozen[name]['result']
            for k in ('streams','equipment','input_sha256','requirements_sha256','units','status'):
                assert a[k]==r[k],(name,k)
        sources[name]=dict(inputs=i,result=r)
        print(name,'captured' if write else 'numerics reproduced; original UUID retained',flush=True)
    if write:save('sources.json',dict(sources=sources,identity='Actual production run_id, not reconstructed historical UUID'),True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',action='store_true');main(p.parse_args().capture)
