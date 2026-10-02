"""Production witness comparison; no new admission policy or forced liquid root."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.configurable_separator_pump.common import *
from benchmarks.pump_energy.compare_production import state,compare,BIP,PROVENANCE
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import ThermodynamicState,MolarComposition
from riogineer_engine.pr_flash import SolverSettings

def build():
    rows=[]
    for r in read('phase_reference.json')['states']:
        c=PengRobinsonProvider().equilibrium_caloric_PT(ThermodynamicState(r['T_K'],r['P_Pa_abs']*.9999,MolarComposition(IDS,tuple(r['z'])),PROVENANCE),BIP,SolverSettings.high_accuracy())
        s=state(c) if c.aggregate else None;ref=r.get('lower_pressure_witness');checks=[]
        if s and ref:checks=compare({},dict(states={'probe':ref}),dict(states={'probe':s},diagnostics={}))
        rows.append(dict(associations=r['associations'],status=c.status,state=s,checks=checks,reference_available=ref is not None))
    return dict(states=rows,comparison_count=sum(len(r['checks']) for r in rows),failed_comparisons=sum(not c['passed'] for r in rows for c in r['checks']))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('phase_comparison.json',build(),p.parse_args().write)
