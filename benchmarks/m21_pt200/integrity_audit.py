"""Classify historical source-pin differences without changing archived evidence."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.m21_pt200.common import *

def build():
    start=read(HERE/'baseline.json')['files'];rows=[]
    def inspect(group,pins):
        for name,expected in pins.items():
            actual=digest(ROOT/name)
            if actual!=expected:
                rows.append(dict(check=group,path=name,historical=expected,task_start=start.get(name),current=actual,
                    classification='pre_existing_historical_mismatch' if start.get(name)==actual else 'authorized_M21_source_change'))
    old=read(ROOT/'benchmarks/variable_composition_pump/equipment_comparison.json')
    inspect('M19_equipment_source_capture',old['production_source_sha256']|old['reference_sha256'])
    b=read(ROOT/'benchmarks/m20_separator_pump/baseline.json');pins=b['sha256']
    inspect('M20_preservation',{p:h for p,h in pins.items() if p.startswith('benchmarks/low_pressure_separator_pump/') or p.startswith('PRE_MILESTONE_20_') or p in ['next-env.d.ts','tsconfig.json'] or (p.startswith('engine/riogineer_engine/') and p not in ['engine/riogineer_engine/core.py','engine/riogineer_engine/network.py'])})
    return dict(mismatches=rows,policy='Historical expected hashes remain unchanged; current source_manifest.json and task-start preservation are separate checks.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();save('integrity_audit.json',build(),a.write)
