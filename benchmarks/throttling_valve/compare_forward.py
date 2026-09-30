"""Read-only PT/M10 + PH/M11 diagnostic, never a production valve acceptance."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.pr_eos import BinaryInteractions
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_ph_flash import PHSpecification, PHSettings
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolarComposition, StateSpecificationProvenance, ThermodynamicState
from riogineer_engine.compressor_energy import caloric_state

REFERENCE=Path(__file__).with_name('methane_nhexane_throttling_valve_reference.json')


def fields(s):
    d=dict(T=s['temperature_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
    for j,c in enumerate(('methane','n_hexane')):d['z'+str(j)]=s['z'][c]
    for name,p in s['phases'].items():
        for label,key in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:d[name+'.'+label]=p[key]
        for j,c in enumerate(('methane','n_hexane')):d[name+'.q'+str(j)]=p['composition'][c]
    return d


def expected(s):
    d=dict(T=s['T_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
    for j,v in enumerate(s['z']):d['z'+str(j)]=v
    for name,p in s['phases'].items():
        for label,key in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:d[name+'.'+label]=p[key]
        for j,v in enumerate(p['composition']):d[name+'.q'+str(j)]=v
    return d


def main():
    raw=REFERENCE.read_bytes();data=json.loads(raw);print('Independent SHA256',hashlib.sha256(raw).hexdigest(),flush=True)
    ids=('methane','n_hexane');bip=BinaryInteractions('pre_m16_diagnostic_zero@1.0',ids,((0.,0.),(0.,0.)),'Explicit qualified constant zero kij')
    provider=PengRobinsonProvider();provenance=StateSpecificationProvenance('peng_robinson@1.0',bip.identifier)
    count=0;maxima={}
    for c in data['cases']+data['separate_studies']:
        i=c['inputs'];composition=MolarComposition(ids,tuple(i['z']))
        a=provider.equilibrium_caloric_PT(ThermodynamicState(i['Tin'],i['Pin'],composition,provenance),bip,SolverSettings.high_accuracy())
        if not a.status.startswith('success'):
            print('BLOCKER',c['case_id'],'inlet_PT',a.status,a.message,flush=True);return 1
        h=a.aggregate.h_J_mol
        r=provider.flash_PH(PHSpecification(i['Pout'],h,composition,provenance),bip,PHSettings(tuple(i.get('qualified_interval',(200.,500.)))))
        if r.status!='success':
            print('BLOCKER',c['case_id'],'outlet_PH',r.status,'target_H',h,'diagnostics',r.diagnostics,flush=True);return 1
        for end,result in [('inlet',a),('outlet',r.caloric)]:
            s=caloric_state(result);e=c['result'][end]
            if s['classification']!=e['classification']:
                print('BLOCKER',c['case_id'],end,'phase',s['classification'],e['classification'],flush=True);return 1
            actual=fields(s);target=expected(e)
            for k,v in target.items():
                err=abs(actual[k]-v);allow=c['allowances'][end][k];count+=1
                if err>allow:
                    print('BLOCKER',c['case_id'],end,k,'error',err,'allowance',allow,'actual',actual[k],'expected',v,flush=True);return 1
                label=end+'.'+k
                if label not in maxima or err>maxima[label]['error']:maxima[label]=dict(case=c['case_id'],error=err,allowance=allow)
        assert abs(r.enthalpy_residual_J_mol)<=1e-6 and len(r.diagnostics.brackets_K)==1 and r.diagnostics.trials[-1].stage=='final'
        count+=1
        print(c['case_id'],'PASS',r.temperature_K,r.caloric.equilibrium.classification,'H residual',r.enthalpy_residual_J_mol,flush=True)
    print('MAXIMA',json.dumps(maxima,sort_keys=True),flush=True)
    print('PASS:',count,'production thermodynamic diagnostic field comparisons; no production M16 equipment',flush=True)
    assert REFERENCE.read_bytes()==raw
    return 0


if __name__=='__main__':raise SystemExit(main())
