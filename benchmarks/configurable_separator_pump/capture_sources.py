"""Fresh actual M17 sources; retain captured UUIDs and verify numeric reproduction."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.configurable_separator_pump.common import *
from riogineer_engine.milestone17 import requirements
from riogineer_engine.core import build_flowsheet,calculate

def build(write):
    specs,_=matrix();sources={};old={} if write else read('sources.json')
    for name,i in specs.items():
        r=calculate(build_flowsheet(requirements(**i)))
        if not write:
            for k in ('streams','equipment','input_sha256','requirements_sha256','units','status'):
                assert r[k]==old[name]['result'][k],(name,k)
        sources[name]=dict(inputs=i,result=r)
        print(name,'source reproduced' if not write else 'captured',flush=True)
    if write:save('sources.json',sources,True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',action='store_true');build(p.parse_args().capture)
