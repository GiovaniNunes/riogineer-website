"""Compare production against independently frozen M17 equipment truth."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.milestone17 import requirements
from riogineer_engine.core import build_flowsheet,calculate
HERE=Path(__file__).resolve().parent
REFERENCE=HERE/'methane_nhexane_separator_energy_reference.json'
ARTIFACT=HERE/'production_comparison.json'
REFERENCE_SHA256='f6dfea8e4dad2729cef6ee33096a3f8c9fe76abfe8059e0dd8f18a6258242122'


def fields(s):
    out=dict(T=s['temperature_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
    for j,i in enumerate(('methane','n_hexane')):out['z'+str(j)]=s['z'][i]
    for name,p in s['phases'].items():
        for label,key in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:out[name+'.'+label]=p[key]
        for j,i in enumerate(('methane','n_hexane')):out[name+'.q'+str(j)]=p['composition'][i]
    return out


def expected_fields(s):
    out=dict(T=s['T_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
    for j,v in enumerate(s['z']):out['z'+str(j)]=v
    for name,p in s['phases'].items():
        for label,key in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:out[name+'.'+label]=p[key]
        for j,v in enumerate(p['composition']):out[name+'.q'+str(j)]=v
    return out


def compare():
    assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest()==REFERENCE_SHA256,'Frozen independent reference hash changed'
    reference=json.loads(REFERENCE.read_text());records=[]
    for row in reference['cases']:
        s=row['inputs'];r=calculate(build_flowsheet(requirements(**s)));unit=r['equipment'][0];d=unit['thermodynamics'];checks=[]
        def check(k,x,y,t):
            error=abs(x-y);assert math.isfinite(error) and error<=t,(row['case_id'],k,x,y,error,t)
            checks.append(dict(field=k,actual=x,expected=y,error=error,allowance=t))
        for end in ('inlet','outlet'):
            assert d[end]['classification']==row[end]['classification']
            actual=fields(d[end]);expected=expected_fields(row[end]);assert set(actual)==set(expected)
            for k,v in actual.items():check(end+'.'+k,v,expected[k],row['allowances'][end][k])
        for name in ('vapor','liquid'):
            p=d['phases'][name];e=row['outputs'][name];a=row['allowances']['phases'][name];stream=r['streams'][unit['material_streams'][name]]
            for k in ('molar_flow_mol_s','enthalpy_flow_W'):check(name+'.'+k,p[k],e[k],a[k])
            check(name+'.mass',stream['mass_flow_kg_h'],e['mass_flow_kg_h'],a['mass_flow_kg_h'])
            for j,i in enumerate(('methane','n_hexane')):check(name+'.'+i,stream['component_mass_flow_kg_h'][i],e['component_mass_flow_kg_h'][j],a['component_mass_flow_kg_h'][j])
            if e['h_J_mol'] is None:assert p['h_J_mol'] is None and p['composition'] is None and stream['component_mass_fractions'] is None and p['enthalpy_flow_W']==0
            else:check(name+'.h',p['h_J_mol'],e['h_J_mol'],row['allowances']['outlet'][name+'.H'])
        check('inlet_flow_H',d['inlet_enthalpy_flow_W'],row['inlet_enthalpy_flow_W'],s['F']*row['allowances']['inlet']['H'])
        check('duty',d['duty_W'],row['duty_W'],row['allowances']['duty_W'])
        check('energy_closure',d['energy_residual_W'],0,d['energy_allowance_W'])
        records.append(dict(case_id=row['case_id'],checks=checks,passed=True))
    return dict(reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),cases=records,comparison_count=sum(len(r['checks']) for r in records))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--verify',action='store_true');a=p.parse_args()
    result=compare();encoded=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n'
    if a.write:ARTIFACT.write_text(encoded)
    elif a.verify:assert ARTIFACT.read_text()==encoded,'Production evidence differs'
    print(f"PASS: {len(result['cases'])} cases, {result['comparison_count']} independent comparisons")
