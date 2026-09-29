"""Create or independently reproduce the frozen Pre-M12 energy benchmark."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
try:
    from .solver import ROOT,mode_a,mode_b,roundoff_allowance
except ImportError:
    from solver import ROOT,mode_a,mode_b,roundoff_allowance
from benchmarks.peng_robinson_ph.reference import compare_states, TOLS
from benchmarks.peng_robinson_ph.equilibrium import IndependentPT

HERE=Path(__file__).resolve().parent
ARTIFACT=HERE/'methane_nhexane_heater_cooler_reference.json'
PH_REFERENCE=ROOT/'benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json'


def specifications():
    old=json.loads(PH_REFERENCE.read_text())
    refs={c['case_id']:c['forward']['T_K'] for c in old['cases']}
    # ID, F mol/s, Pin Pa, Tin K, Pout Pa, Tout K, required endpoint phases, duty sign.
    rows=[
      ('VAPOR_HEATING',100.,1000.,300.,1000.,350.,'single_vapor','single_vapor',1),
      ('VAPOR_COOLING',100.,1000.,350.,1000.,300.,'single_vapor','single_vapor',-1),
      ('LIQUID_HEATING',100.,3e7,280.,3e7,350.,'single_liquid','single_liquid',1),
      ('LIQUID_COOLING',100.,3e7,350.,3e7,280.,'single_liquid','single_liquid',-1),
      ('LIQUID_TO_TWO_PHASE',100.,6e6,220.,6e6,300.,'single_liquid','vapor_liquid',1),
      ('TWO_PHASE_TO_VAPOR',100.,6e6,300.,6e6,480.,'vapor_liquid','single_vapor',1),
      ('VAPOR_TO_TWO_PHASE',100.,6e6,480.,6e6,300.,'single_vapor','vapor_liquid',-1),
      ('TWO_PHASE_TO_LIQUID',100.,6e6,300.,6e6,220.,'vapor_liquid','single_liquid',-1),
      ('TWO_PHASE_TO_TWO_PHASE',100.,6e6,300.,6e6,350.,'vapor_liquid','vapor_liquid',1),
      ('SPECIFIED_OUTLET_PRESSURE',100.,6e6,300.,3e6,350.,'vapor_liquid','vapor_liquid',1),
      ('VAPOR_HEATING_DOUBLE_FLOW',200.,1000.,300.,1000.,350.,'single_vapor','single_vapor',1),
      ('ZERO_DUTY',100.,3e5,300.,3e5,300.,'vapor_liquid','vapor_liquid',0),
      ('BUBBLE_ADJACENT_HEATING',100.,6e6,refs['PH_BUBBLE_BELOW'],6e6,refs['PH_BUBBLE_ABOVE'],'single_liquid','vapor_liquid',1),
      ('DEW_ADJACENT_COOLING',100.,6e6,refs['PH_DEW_ABOVE'],6e6,refs['PH_DEW_BELOW'],'single_vapor','vapor_liquid',-1),
    ]
    return [dict(case_id=i,F=f,Pin=pi,Tin=ti,Pout=po,Tout=to,z=[.5,.5],
                 expected_inlet=ip,expected_outlet=op,expected_sign=sign)
            for i,f,pi,ti,po,to,ip,op,sign in rows]


def negative_specs():
    base=dict(F=100.,Pin=3e5,Tin=300.,Pout=3e5,Q=0.,z=[.5,.5])
    rows=[]
    for key,value,name,status in [
        ('F',0.,'ZERO_FLOW','invalid_flow'),('F',-1.,'NEGATIVE_FLOW','invalid_flow'),
        ('F','nan','NAN_FLOW','invalid_flow'),('F','inf','INFINITE_FLOW','invalid_flow'),
        ('Pin',0.,'INVALID_INLET_PRESSURE','invalid_pressure'),('Pout',-1.,'INVALID_OUTLET_PRESSURE','invalid_pressure'),
        ('z',[.4,.4],'INVALID_COMPOSITION','invalid_composition'),('ids',['methane','water'],'UNSUPPORTED_WATER','unsupported_component'),
        ('Tin',199.,'INLET_CP_EXTRAPOLATION','temperature_domain_invalid'),
        ('Q',1e10,'UNBRACKETED_HIGH_TARGET','enthalpy_target_not_bracketed'),
        ('Q',-1e10,'UNBRACKETED_LOW_TARGET','enthalpy_target_not_bracketed'),
        ('Q','nan','NAN_DUTY','invalid_duty'),('Q','inf','INFINITE_DUTY','invalid_duty')]:
        rows.append(dict(case_id=name,mode='B',inputs=dict(base,**{key:value}),expected_status=status))
    rows.append(dict(case_id='OUTLET_CP_EXTRAPOLATION',mode='A',inputs=dict(F=100.,Pin=3e5,Tin=300.,Pout=3e5,Tout=1001.,z=[.5,.5]),expected_status='temperature_domain_invalid'))
    old=json.loads(PH_REFERENCE.read_text());gap=old['pure_saturation_gap']
    Hin=IndependentPT().evaluate(300.,gap['P_Pa_abs'],[0.,1.])['H_eq_J_mol']
    Q=100.*(gap['excluded_target_J_mol']-Hin)
    rows.append(dict(case_id='PURE_COEXISTENCE_GAP',mode='B',inputs=dict(F=100.,Pin=gap['P_Pa_abs'],Tin=300.,Pout=gap['P_Pa_abs'],Q=Q,z=[0.,1.]),expected_status=gap['inversion']['status']))
    return rows


def run_negative(spec):
    inputs={k:float(v) if v in ('nan','inf') else v for k,v in spec['inputs'].items() if not isinstance(v,list)}
    inputs.update({k:v for k,v in spec['inputs'].items() if isinstance(v,list)})
    return (mode_a if spec['mode']=='A' else mode_b)(**inputs)


def build():
    cases=[]
    for spec in specifications():
        args={k:spec[k] for k in ('F','Pin','Tin','Pout','Tout','z')}
        a=mode_a(**args)
        assert a['status']=='success',(spec,a)
        b=mode_b(spec['F'],spec['Pin'],spec['Tin'],spec['Pout'],a['Q_W'],spec['z'])
        assert b['status']=='success',(spec,b)
        assert a['inlet']['classification']==spec['expected_inlet'],(spec,a['inlet'])
        assert a['outlet']['classification']==spec['expected_outlet'],(spec,a['outlet'])
        assert (1 if a['Q_W']>0 else -1 if a['Q_W']<0 else 0)==spec['expected_sign']
        errors=compare_states(b['outlet'],a['outlet'])
        compare_states(b['inlet'],a['inlet'])
        assert a['z_out']==b['z_out']==spec['z']
        assert a['F_out_mol_s']==b['F_out_mol_s']==spec['F']
        Hin=a['inlet']['H_eq_J_mol'];Hout=a['outlet']['H_eq_J_mol']
        arithmetic=roundoff_allowance(spec['F'],Hin,Hout,a['Q_W'])
        assert abs(a['R_Q_W'])<=arithmetic
        assert abs(b['R_H_J_mol'])<=TOLS['H_residual']['atol']
        inverse_allowance=spec['F']*TOLS['H_residual']['atol']+arithmetic
        assert abs(b['R_Q_W'])<=inverse_allowance
        errors.update(forward_R_Q_W=abs(a['R_Q_W']),inverse_R_Q_W=abs(b['R_Q_W']),
                      inverse_R_H_J_mol=abs(b['R_H_J_mol']),
                      H_target_reconstruction_J_mol=abs(b['H_out_target_J_mol']-Hout))
        cases.append(dict(specification=spec,mode_A=a,mode_B=b,absolute_errors=errors,
                          forward_energy_allowance_W=arithmetic,inverse_energy_allowance_W=inverse_allowance))
    original=cases[0]['mode_A'];scaled=cases[10]['mode_A']
    assert original['inlet']==scaled['inlet'] and original['outlet']==scaled['outlet']
    assert scaled['Q_W']==2*original['Q_W'] and scaled['delta_H_J_mol']==original['delta_H_J_mol']
    negative=[]
    for spec in negative_specs():
        result=run_negative(spec)
        assert result['status']==spec['expected_status'] and 'outlet' not in result,(spec,result)
        negative.append(dict(specification=spec,result=result))
    maxima={}
    for c in cases:
        for key,value in c['absolute_errors'].items():
            if key not in maxima or value>maxima[key]['absolute_error']:
                maxima[key]=dict(absolute_error=value,case_id=c['specification']['case_id'])
    old=json.loads(PH_REFERENCE.read_text())
    paths=['benchmarks/peng_robinson_ph/equilibrium.py','benchmarks/peng_robinson_ph/solver.py',
           'benchmarks/peng_robinson_ph/reference.py',str(PH_REFERENCE.relative_to(ROOT)),
           'benchmarks/peng_robinson_caloric/reference.py','benchmarks/peng_robinson_caloric/equations.py',
           'benchmarks/heater_cooler_energy/solver.py']
    return dict(reference_id='independent_methane_nhexane_heater_cooler@1.0',
        metadata=dict(thermodynamic_provenance=old['metadata'],
            units=dict(F='mol/s',H='J/mol',Q='W = J/s',P='Pa absolute',T='K'),
            convention='Q=F*(H_out-H_in); positive heat enters stream; no shaft work or KE/PE changes',
            generation_command='.local/pre-m8-venv/bin/python -B benchmarks/heater_cooler_energy/reference.py --write',
            packages={k:importlib.metadata.version(k) for k in ('thermo','chemicals','fluids','numpy','scipy')},
            source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}),
        tolerances=dict(inherited_independent_PH=TOLS,arithmetic='64*epsilon*max(1,abs(Q),abs(F*Hin),abs(F*Hout)) W',
                        inverse_energy='F*1e-6 J/mol + arithmetic allowance W'),
        cases=cases,negative_cases=negative,maximum_errors=maxima,
        flow_scaling=dict(cases=['VAPOR_HEATING','VAPOR_HEATING_DOUBLE_FLOW'],factor=2.,Q_ratio=scaled['Q_W']/original['Q_W'],identical_thermodynamic_states=True))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true')
    args=parser.parse_args();data=build();serialized=json.dumps(data,indent=2,allow_nan=False)+'\n'
    if args.write:ARTIFACT.write_text(serialized)
    else:assert serialized==ARTIFACT.read_text(),'Frozen Pre-M12 reproduction mismatch'
    print('Case / inlet phase / outlet phase / F mol/s / Q W / recovered T K / inverse R_H J/mol')
    for c in data['cases']:
        a,b=c['mode_A'],c['mode_B']
        print(c['specification']['case_id'],a['inlet']['classification'],a['outlet']['classification'],a['F_in_mol_s'],a['Q_W'],b['outlet']['T_K'],b['R_H_J_mol'])
    print('PASS:',len(data['cases']),'positive,',len(data['negative_cases']),'negative; deterministic independent reference')

if __name__=='__main__':main()
