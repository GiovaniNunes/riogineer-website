"""Capture fresh current separator executions once; numeric replay is read-only."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.pt_iteration_budget.common import *
from riogineer_engine.milestone17 import requirements
from riogineer_engine.core import calculate,build_flowsheet

def build(write):
    result={};old={} if write else read(HERE/'sources.json')
    for name,i in sources().items():
        r=calculate(build_flowsheet(requirements(**i)))
        if not write:
            for k in ('streams','equipment','input_sha256','requirements_sha256','units','status'):assert r[k]==old[name]['result'][k],(name,k)
        result[name]=dict(inputs=i,result=r)
    if write:save('sources.json',result,True)
    else:print('PASS fresh numeric source replay; captured UUIDs retained')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',action='store_true');build(p.parse_args().capture)
