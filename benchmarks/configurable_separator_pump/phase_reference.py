"""Independent local witnesses at actual candidate endpoints, separate artifact."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.configurable_separator_pump.common import *
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT

def build():
    q=EntropyPT();states={}
    for c in read('reference.json')['cases']:
        for end,s in c['result']['states'].items():
            if s['classification']!='single_liquid':continue
            key=encode([s['T_K'],s['P_Pa_abs'],s['z']])
            if key in states:states[key]['associations'].append([c['case_id'],end]);continue
            r=dict(T_K=s['T_K'],P_Pa_abs=s['P_Pa_abs'],z=s['z'],associations=[[c['case_id'],end]])
            try:r['lower_pressure_witness']=q.evaluate(s['T_K'],s['P_Pa_abs']*.9999,s['z'])
            except Exception as e:r['witness_error']=type(e).__name__+': '+str(e)
            states[key]=r
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(reference_sha256=digest(HERE/'reference.json'),states=list(states.values()),production_imported=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('phase_reference.json',build(),p.parse_args().write)
