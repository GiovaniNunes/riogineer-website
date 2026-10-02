"""Study input ledger and numerical policy; no production thermodynamics."""
import json
from pathlib import Path
from benchmarks.pump_energy.common import *
HERE = Path(__file__).resolve().parent
SOURCE = ROOT/'benchmarks/variable_composition_pump/separator_compatibility.json'

def inventory():
    return json.loads(SOURCE.read_text())['cases'][:24]

def specification(c):
    s=c['actual_liquid']
    return dict(T1=s['temperature_K'], P1=s['pressure_Pa_abs'],
                P2=s['pressure_Pa_abs']+1e6, z=[c['z_methane'],1-c['z_methane']],
                flow=c['F_mol_s'],eta=.8)

def cases():
    by={c['case_id']:c for c in inventory()}; rows=[]
    selected=['PT_VL_HEATING','PT_VL_INLET_EQUAL','PT_VAPOR_INLET_COOLING','PH_FLASH',
              'PH_HEXANE_RICH','PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE','PT_DEW_BELOW']
    def add(name,source,role,**patch):
        rows.append(dict(case_id=name,source=source,role=role,inputs=specification(by[source])|patch))
    for name in selected:
        for dp in (0.,10000.,1e6):
            add(name+'_DP'+str(dp),name,'unchanged_historical',P2=by[name]['actual_liquid']['pressure_Pa_abs']+dp)
    for name in ('PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE'):
        add(name+'_8MPA',name,'historical_solver_challenge',P2=8e6)
    for eta in (.6,1.):add('ETA'+str(eta),'PH_FLASH','efficiency',eta=eta)
    for dp in (10.,100.,1000.):add('SMALL'+str(dp),'PH_FLASH','small_work',P2=1e6+dp)
    for flow in (5.,17.3,200.):add('SCALED'+str(flow),'PH_FLASH','scaled_flow',flow=flow)
    for eta in (0.,.59,1.01):add('INVALID_ETA'+str(eta),'PH_FLASH','negative',eta=eta)
    add('PRESSURE_DECREASE','PH_FLASH','negative',P2=9e5)
    absent=by['PT_VAPOR']['actual_liquid']
    rows.append(dict(case_id='ABSENT_LIQUID',source='PT_VAPOR',role='negative',inputs=dict(T1=absent['temperature_K'],P1=absent['pressure_Pa_abs'],P2=2000.,flow=0.,z=None,eta=.8)))
    add('BULK_VL','PT_VL_INLET_EQUAL','negative',z=[.5,.5])
    add('VAPOR','PT_VL_INLET_EQUAL','negative',P1=1000.,P2=2000.)
    return rows

def policy(i,r):
    if not .6<=i['eta']<=1:return 'invalid_efficiency'
    if r.get('stage')!='complete':return r['status']
    if i['P1']==i['P2']:return 'identity'
    a,b,c=[r['states'][k]['H_eq_J_mol'] for k in ('inlet','isentropic','outlet')]
    E=(h_budget(a)+h_budget(b))/i['eta']+h_budget(a)+h_budget(c)+500e-8/i['eta']+1e-6+64*2.220446049250313e-16*max(1,abs(a),abs(b),abs(c))/i['eta']
    r['work_screen']=dict(budget_J_mol=E,ratio=E/(c-a) if c>a else None)
    return 'resolved' if c>a and b>a and E/(c-a)<=1e-4 else 'unresolved_work'

def save(name,data,write):
    path=HERE/name;raw=encode(data)
    if write:path.write_text(raw)
    else:assert path.read_text()==raw, name+' reproduction differs'
    print(name,digest(path),flush=True)
