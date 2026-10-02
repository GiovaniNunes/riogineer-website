"""Capture fresh current separator executions once; numeric replay is read-only."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.m21_pt200.common import *
from riogineer_engine.milestone17 import requirements
from riogineer_engine.core import calculate,build_flowsheet,semantic_hash

def build(write,record_identity=False):
    identities=[];result={};old={} if write else read(HERE/'sources.json')
    for name,i in sources().items():
        f=build_flowsheet(requirements(**i));r=calculate(f)
        assert r['input_sha256']==semantic_hash(f)
        if not write:
            for k in ('streams','equipment','requirements_sha256','units','status'):assert r[k]==old[name]['result'][k],(name,k)
        if not write:
            identities.append(dict(source=name,numerical_fields_equal=True,captured_input_sha256=old[name]['result']['input_sha256'],current_input_sha256=r['input_sha256'],captured_engine=old[name]['result']['engine'],current_engine=r['engine'],fresh_run=r['run_id']!=old[name]['result']['run_id']))
        result[name]=dict(inputs=i,result=r)
    if write:save('sources.json',result,True)
    else:
        save('source_replay.json',identities,record_identity)
        print('PASS fresh numerical source replay; source-identity differences recorded separately, captured UUIDs unchanged')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',action='store_true');p.add_argument('--record-identity',action='store_true');a=p.parse_args();build(a.capture,a.record_identity)
