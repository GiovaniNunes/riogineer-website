"""Study-only orchestration of unchanged public production routines."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.low_pressure_separator_pump.common import *
from benchmarks.pump_energy.compare_production import calculate,compare,state,BIP,PROVENANCE
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import ThermodynamicState,MolarComposition
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.variable_pump_energy import pump,PumpFailure
from riogineer_engine.milestone19 import requirements

def pt(i,P,settings):
    r=PengRobinsonProvider().equilibrium_caloric_PT(ThermodynamicState(i['T1'],P,MolarComposition(IDS,tuple(i['z'])),PROVENANCE),BIP,settings)
    return state(r) if r.aggregate else dict(error=r.status,message=r.message)

def build():
    ref=json.loads((HERE/'reference.json').read_text());screen=[]
    source_cases=json.loads((ROOT/'benchmarks/two_phase_separator_energy/methane_nhexane_separator_energy_reference.json').read_text())['cases']
    for c,rr,sc in zip(inventory(),ref['screen'],source_cases):
        s=c['actual_liquid'];t=c['separator_thermodynamics'];row=dict(case_id=c['case_id'],mode=sc['inputs']['mode'],actual_liquid=s,
            parent=t['outlet'],vapor_coexists=t['outlet']['classification']=='vapor_liquid',
            absent=s['mass_flow_kg_h']==0,all_M19_scalar_reasons=c['reasons'],interface_reasons=['independent_caloric_input'])
        u=requirements()['equipment'][0];u=dict(u,operating_parameters=u['parameters'])
        try:pump(u,{'inlet':s});row['wrapper']='accepted'
        except PumpFailure as e:row['wrapper']=dict(stage=e.stage,status=e.status,message=str(e))
        if not row['absent']:
            i=specification(c);r=pt(i,i['P1'],SolverSettings.high_accuracy());row.update(inputs=i,equilibrium=r,
                standard_PT=pt(i,i['P1'],SolverSettings()),
                phase_H=t['outlet']['phases']['liquid']['h_J_mol'],phase_S=t['outlet']['phases']['liquid']['s_J_mol_K'],
                molar_flow_mol_s=c['F_mol_s'],composition=i['z'])
            row['probes']=[dict(relative_offset=d,state=pt(i,i['P1']*(1+d),SolverSettings.high_accuracy())) for d in (-1e-3,-1e-6,-1e-9,0.,1e-9,1e-6,1e-3)]
            if 'error' not in r:
                row['equilibrium_minus_separator_H']=r['H_eq_J_mol']-row['phase_H']
                row['equilibrium_minus_separator_S']=r['S_eq_J_mol_K']-row['phase_S']
            phase=rr['phase_specific'];row['independent_phase_errors']=dict(H=row['phase_H']-phase['h_total_J_mol'],S=row['phase_S']-phase['s_total_J_mol_K'])
            # Explicit PT projection diagnostic, never described as direct stream support.
            projected={k:v for k,v in s.items() if k in ('component_mass_flow_kg_h','mass_flow_kg_h','component_mass_fractions','temperature_K','pressure_Pa_abs')}
            try:pump(u,{'inlet':projected});row['projected_wrapper']='accepted'
            except PumpFailure as e:row['projected_wrapper']=dict(stage=e.stage,status=e.status)
        screen.append(row)
    rows=[]
    for c in ref['cases']:
        i=c['inputs']
        if not .6<=i['eta']<=1:r=dict(status='invalid_efficiency',stage='input',states={},diagnostics={})
        else:r=calculate(i)
        pol=policy(i,r);checks=compare(i,c['result'],r)
        if i['P1']==i['P2'] and r.get('stage')=='complete':
            actual=next(x['actual_liquid'] for x in inventory() if x['case_id']==c['source'])
            r['preserved_identity_stream']=actual
            r['identity_fluid_power_W']=0.

        numerical=pol in ('identity','resolved') and c['policy'] in ('identity','resolved') and all(k['passed'] for k in checks)
        disposition='accepted_tuple' if numerical else 'rejected' if pol in ('invalid_flow','invalid_pressure','invalid_efficiency','unsupported_phase','unresolved_work') else 'unresolved'
        rows.append(dict(case_id=c['case_id'],source=c['source'],role=c['role'],inputs=i,result=r,policy=pol,
                         checks=checks,disposition=disposition,production_supported=False))
        print(c['case_id'],pol,disposition,sum(not k['passed'] for k in checks),flush=True)
    return dict(reference_sha256=digest(HERE/'reference.json'),source_sha256=digest(__file__),inventory=screen,cases=rows,
        failed_checks=sum(not k['passed'] for c in rows for k in c['checks']),comparison_count=sum(len(c['checks']) for c in rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();save('production.json',build(),a.write)
