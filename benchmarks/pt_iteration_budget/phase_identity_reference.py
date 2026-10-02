"""Independent phase-identity audit preserving every raw reference value."""
import sys,argparse,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.pt_iteration_budget.common import *
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT

def build():
    q=EntropyPT();rows=[]
    for raw in read(HERE/'reference.json')['PT']:
        s=raw['state'];props={}
        for name,p in s['phases'].items():
            obj=(q.flash.liquid if name=='liquid' else q.flash.gas).to(T=s['T_K'],P=s['P_Pa_abs'],zs=p['composition'])
            props[name]=dict(PIP=obj.PIP(),V_m3_mol=obj.V(),rho_kg_m3=p['MW_kg_kmol']/(1000*obj.V()),Z=obj.Z(),recorded_Z=p['Z'])
        mapping={};reason=None
        for name,p in props.items():
            if abs(p['Z']-p['recorded_Z'])>1e-10:reason='phase root not reproduced';break
            label='liquid' if p['PIP']>1 else 'vapor' if p['PIP']<1 else None
            if label is None or label in mapping.values():reason='ambiguous PIP';break
            mapping[name]=label
        if len(props)==2 and not reason:
            inv={v:k for k,v in mapping.items()};l,v=props[inv['liquid']],props[inv['vapor']]
            gap=max(abs(a-b) for a,b in zip(s['phases'][inv['liquid']]['composition'],s['phases'][inv['vapor']]['composition']))
            if not (l['V_m3_mol']<v['V_m3_mol'] and l['rho_kg_m3']>v['rho_kg_m3'] and abs(l['Z']-v['Z'])>.01 and gap>.01):reason='nontrivial ordered phase evidence missing'
        row=dict(case_id=raw['case_id'],raw_state_sha256=hashed(s),phase_identity=props,mapping=mapping,status='unresolved' if reason else 'verified',reason=reason)
        if not reason:
            t=copy.deepcopy(s);t['phases']={mapping[k]:v for k,v in s['phases'].items()}
            t['beta']=sum((s['beta'] if k=='vapor' else 1-s['beta']) for k,v in mapping.items() if v=='vapor')
            t['classification']='vapor_liquid' if len(props)==2 else 'single_'+next(iter(mapping.values()))
            if mapping.get('liquid')=='vapor':t['ln_fugacity_residual']=[-v for v in s['ln_fugacity_residual']]
            row['state']=t;row['lnphis']={mapping[k]:v for k,v in raw['lnphis'].items()};row['swapped']=any(k!=v for k,v in mapping.items())
        rows.append(row)
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(cases=rows,raw_reference_sha256=digest(HERE/'reference.json'),production_imported=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');save('phase_identity_reference.json',build(),p.parse_args().write)
