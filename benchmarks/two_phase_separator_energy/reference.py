"""Independent M17 equipment reference. No production imports. Default verifies."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.throttling_valve.reference import EntropyPT, solve_ph, fields, fixed, allowances, encode
from benchmarks.peng_robinson_caloric import reference as caloric
HERE=Path(__file__).resolve().parent
ARTIFACT=HERE/'methane_nhexane_separator_energy_reference.json'
IDS=('methane','n_hexane')
MW=(16.0428,86.17536)


def specifications():
    base=dict(Pin=3e7,Tin=300.,Pout=3e5,F=100.,z=[.5,.5])
    rows=[]
    def add(name,mode,**kw):rows.append(dict(case_id=name,inputs=dict(base,mode=mode,**kw)))
    add('PT_VL_HEATING','specified_temperature',Tout=350.)
    add('PT_LIQUID_COOLING','specified_temperature',Tout=280.,Pout=3e7)
    add('PT_VAPOR','specified_temperature',Tout=400.,Pout=1000.)
    add('PT_VL_INLET_EQUAL','specified_temperature',Pin=3e5,Tout=300.)
    add('PT_VAPOR_INLET_COOLING','specified_temperature',Pin=6e6,Tin=400.,Pout=1e6,Tout=280.,z=[.9,.1])
    add('PT_DOUBLE_FLOW','specified_temperature',Tout=350.,F=200.)
    add('PT_LOW_FLOW','specified_temperature',Tout=350.,F=5.)
    add('PH_FLASH','adiabatic',Pout=1e6)
    add('PH_LIQUID_EQUAL','adiabatic',Pout=3e7)
    add('PH_VAPOR','adiabatic',Pin=6e6,Tin=400.,Pout=1e6,z=[.9,.1])
    add('PH_VAPOR_EQUAL','adiabatic',Pin=1000.,Pout=1000.)
    add('PH_VL_EQUAL','adiabatic',Pin=3e5,Pout=3e5)
    add('PH_VL_REDUCTION','adiabatic',Pin=6e6,Pout=1e6)
    add('PH_DOUBLE_FLOW','adiabatic',Pout=1e6,F=200.)
    add('PH_LOW_FLOW','adiabatic',Pout=1e6,F=5.)
    add('PH_HEXANE_RICH','adiabatic',Pin=6e6,Pout=1e5,z=[.1,.9])
    # Independently established M16 boundary experiments become explicitly tested M17 cases.
    prior=json.loads((ROOT/'benchmarks/throttling_valve/methane_nhexane_throttling_valve_reference.json').read_text())
    # Locate rows recursively without relying on a production artifact.
    def visit(x):
        if isinstance(x,dict):
            if x.get('case_id','').startswith(('BUBBLE_','DEW_')) and 'inputs' in x and 'result' in x:
                return [x]
            return sum((visit(v) for v in x.values()),[])
        return sum((visit(v) for v in x),[]) if isinstance(x,list) else []
    for row in visit(prior):
        s=row['inputs'];name=row['case_id']
        add('PH_'+name,'adiabatic',**{k:s[k] for k in ('Pin','Tin','Pout','F','z')})
        add('PT_'+name,'specified_temperature',Tout=row['result']['outlet']['T_K'],**{k:s[k] for k in ('Pin','Tin','Pout','F','z')})
    return rows


def map_outputs(s,out):
    result={}
    for name,w in [('vapor',out['beta']),('liquid',1-out['beta'])]:
        p=out['phases'].get(name);f=s['F']*w
        result[name]=dict(molar_flow_mol_s=f,composition=p['composition'] if p else None,
            h_J_mol=p['h_J_mol'] if p else None,enthalpy_flow_W=f*p['h_J_mol'] if p else 0.,
            component_mass_flow_kg_h=[f*q*mw*3.6 for q,mw in zip(p['composition'],MW)] if p else [0.,0.])
        result[name]['mass_flow_kg_h']=math.fsum(result[name]['component_mass_flow_kg_h'])
    return result


def validate_spec(s):
    mode=s.get('mode');expected={'mode','Pin','Tin','Pout','F','z'}|({'Tout'} if mode=='specified_temperature' else set())
    def finite(v):return isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v)
    if mode not in ('specified_temperature','adiabatic') or set(s)!=expected:raise ValueError('invalid_specification')
    if not finite(s['F']) or s['F']<=0:raise ValueError('invalid_flow')
    if any(not finite(s[k]) or s[k]<=0 for k in ('Pin','Pout')) or s['Pout']-s['Pin']>1e-8:raise ValueError('invalid_pressure')
    if any(not finite(s[k]) or not 200<=s[k]<=500 for k in ('Tin','Tout') if k in s):raise ValueError('temperature_domain_invalid')
    if len(s['z'])!=2 or any(not finite(v) or v<0 for v in s['z']) or abs(sum(s['z'])-1)>1e-12:raise ValueError('invalid_composition')


def qualify(row):
    s=row['inputs'];validate_spec(s);pt=EntropyPT();a=pt.evaluate(s['Tin'],s['Pin'],s['z'])
    if s['mode']=='adiabatic':
        inv=solve_ph(s['Pout'],s['z'],a['H_eq_J_mol'],evaluator=pt.evaluate)
        assert inv['status']=='success',(row['case_id'],inv['status'],inv.get('message'))
        o=pt.evaluate(inv['solution']['T_K'],s['Pout'],s['z'])
        budget=allowances(dict(inlet=a,outlet=o,energy_allowance_W=s['F']*1e-6),pt)
        # Independently repeat inverse using a different grid and algorithm.
        alt=solve_ph(s['Pout'],s['z'],a['H_eq_J_mol'],evaluator=pt.evaluate,grid_points=256,method='bisect')
        assert alt['status']=='success'
        for k,v in fields(alt['solution']).items():assert abs(v-fields(o)[k])<=budget['outlet'][k],(row['case_id'],k)
    else:
        o=pt.evaluate(s['Tout'],s['Pout'],s['z'])
        budget=dict(inlet={k:fixed(k,v) for k,v in fields(a).items()},outlet={k:fixed(k,v) for k,v in fields(o).items()})
    outputs=map_outputs(s,o);hin=s['F']*a['H_eq_J_mol'];hout=math.fsum(p['enthalpy_flow_W'] for p in outputs.values())
    duty=hout-hin if s['mode']=='specified_temperature' else 0.
    residual=math.fsum([hout,-hin,-duty]);assert abs(residual)<=s['F']*1e-6+1e-8
    # Independent reconstructed equipment tolerances propagate frozen phase uncertainties.
    phase_budgets={}
    for name,p in outputs.items():
        b=budget['outlet'];beta=b['beta'];q=b.get(name+'.q0',0.);h=b.get(name+'.H',0.)
        phase_budgets[name]=dict(molar_flow_mol_s=s['F']*beta,
            mass_flow_kg_h=s['F']*3.6*sum(MW)*(beta+q),
            component_mass_flow_kg_h=[s['F']*3.6*mw*(beta+q) for mw in MW],
            enthalpy_flow_W=s['F']*(beta*abs(p['h_J_mol'] or 0.)+h)+1e-8)
    duty_allowance=s['F']*budget['inlet']['H']+sum(p['enthalpy_flow_W'] for p in phase_budgets.values())
    for j,z in enumerate(s['z']):
        assert abs(sum(p['component_mass_flow_kg_h'][j] for p in outputs.values())-s['F']*z*MW[j]*3.6)<1e-8
    return dict(**row,inlet=a,outlet=o,outputs=outputs,inlet_enthalpy_flow_W=hin,duty_W=duty,
                energy_residual_W=residual,allowances=dict(**budget,phases=phase_budgets,duty_W=duty_allowance))


def build():
    rows=[qualify(r) for r in specifications()]
    for mode in ('adiabatic','specified_temperature'):
        assert {r['outlet']['classification'] for r in rows if r['inputs']['mode']==mode}=={'single_liquid','single_vapor','vapor_liquid'}
    assert {r['inlet']['classification'] for r in rows}=={'single_liquid','single_vapor','vapor_liquid'}
    assert any(r['duty_W']>0 for r in rows) and any(r['duty_W']<0 for r in rows)
    files=[Path(__file__),ROOT/'benchmarks/peng_robinson_ph/equilibrium.py',ROOT/'benchmarks/peng_robinson_ph/solver.py',ROOT/'benchmarks/peng_robinson_caloric/reference.py',ROOT/'benchmarks/peng_robinson_ps/equilibrium.py',ROOT/'benchmarks/throttling_valve/reference.py']
    return dict(identifier='independent_separator_energy@1.0',packages={p:importlib.metadata.version(p) for p in ('thermo','chemicals','scipy','numpy')},
        convention='Canonical PR 0.45724/0.07780; explicit zero kij; pure ideal H=S=0 at 298.15 K, 101325 Pa; MW kg/kmol; F mol/s; duty positive into equipment',
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},cases=rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    data=build();encoded=encode(data)
    if args.write:ARTIFACT.write_text(encoded)
    else:assert ARTIFACT.read_text()==encoded,'Frozen reference differs'
    print(f"PASS: {len(data['cases'])} independent separator cases; both modes, L/V/VL inlet and outlet, balances and inverse refinement")
