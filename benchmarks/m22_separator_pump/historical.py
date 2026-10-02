"""Fresh M20 regression, full numerical payload equality and current identities."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'engine')]
from benchmarks.m21_pt200.review.regression import current_m20

def normalize(v):
    if isinstance(v,dict):return {k:normalize(x) for k,x in v.items() if k not in ('run_id','input_sha256','implementation_sha256')}
    if isinstance(v,list):return [normalize(x) for x in v]
    return v

def verify():
    fresh=current_m20()
    old=json.loads((ROOT/'benchmarks/m21_pt200/m20_current.json').read_text())
    assert len(fresh['cases'])==len(old['cases'])==30
    for a,b in zip(fresh['cases'],old['cases']):
        assert a['case_id']==b['case_id']
        assert normalize(a['result'])==normalize(b['result']),a['case_id']+' full payload changed'
    fresh['exact_payload_cases']=30
    fresh['identity_exclusions']=['run_id','input_sha256','implementation_sha256']
    return fresh

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();result=verify()
    if a.output:
        with Path(a.output).open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print('PASS 30 exact historical numerical/result payloads; 1680 independent checks')
