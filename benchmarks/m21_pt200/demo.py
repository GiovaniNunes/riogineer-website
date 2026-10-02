"""Demonstrate explicit production selection; no network application is admitted."""
import sys,argparse,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.m21_pt200.harness import PROVIDER,BIP,specification,chain,Profile
from benchmarks.m21_pt200.common import HERE,read,chains
from riogineer_engine.numerical_profiles import NumericalProfile
from dataclasses import asdict

p=argparse.ArgumentParser();p.add_argument('--chain',choices=['below','above']);a=p.parse_args()
if a.chain:
    name='PT_BUBBLE_'+a.chain.upper()+'_8000000.0'
    r=chain(next(c for c in chains() if c['case_id']==name),read(HERE/'sources.json'),Profile(200))
    result={k:r[k] for k in ('status','stage','profile','production_support','metrics','energy')}
else:
    r=PROVIDER.flash_PT(specification(466.6666666666667,8e6,[.5,.5]),BIP,numerical_profile=NumericalProfile.PT200)
    result=dict(status=r.status,iterations=r.diagnostics.iterations,settings=asdict(r.provenance.settings),physical_package=PROVIDER.identifier)
print(json.dumps(result,indent=2,allow_nan=False))
