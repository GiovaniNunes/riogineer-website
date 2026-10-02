"""Capture fresh current separator executions once; numeric replay is read-only."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.m21_pt200.common import *
from riogineer_engine.milestone17 import requirements
from riogineer_engine.core import calculate,build_flowsheet,semantic_hash,implementation_hash,EVALUATOR_HASH

def validate_replay(inputs,flowsheet,current,captured):
    """Only run UUID and source-dependent identities may differ; all else is exact."""
    old=captured['result']
    assert captured['inputs']==inputs,'source inputs changed'
    assert set(current)==set(old),'result fields changed'
    assert current['run_id']!=old['run_id'],'source calculation was not fresh'
    assert current['input_sha256']==semantic_hash(flowsheet),'current semantic identity'
    assert current['requirements_sha256']==flowsheet['requirements_sha256'],'requirements association'
    assert current['case_id']==flowsheet['case_id'],'case association'
    assert current['engine']['implementation_sha256']==implementation_hash(),'current engine identity'
    assert current['engine']['evaluator_sha256']==EVALUATOR_HASH,'evaluator identity'
    assert {k:v for k,v in current['engine'].items() if k!='implementation_sha256'}=={k:v for k,v in old['engine'].items() if k!='implementation_sha256'},'engine provenance changed'
    for key in set(current)-{'run_id','input_sha256','engine'}:
        assert current[key]==old[key],key+' changed'


def build(write,record_identity=False):
    identities=[];result={};old={} if write else read(HERE/'sources.json')
    for name,i in sources().items():
        f=build_flowsheet(requirements(**i));r=calculate(f)
        assert r['input_sha256']==semantic_hash(f)
        if not write:
            validate_replay(i,f,r,old[name])
        if not write:
            identities.append(dict(source=name,numerical_fields_equal=True,captured_input_sha256=old[name]['result']['input_sha256'],current_input_sha256=r['input_sha256'],captured_engine=old[name]['result']['engine'],current_engine=r['engine'],fresh_run=r['run_id']!=old[name]['result']['run_id']))
        result[name]=dict(inputs=i,result=r)
    if write:save('sources.json',result,True)
    else:
        save('source_replay.json',identities,record_identity)
        print('PASS fresh numerical source replay; source-identity differences recorded separately, captured UUIDs unchanged')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',action='store_true');p.add_argument('--record-identity',action='store_true');a=p.parse_args();build(a.capture,a.record_identity)
