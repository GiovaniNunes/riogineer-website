"""Actual M19 callable AND process adapter against unchanged independent evidence."""
import json, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'engine'))
from benchmarks.pump_energy.common import finish
from benchmarks.pump_energy.compare_production import compare
from riogineer_engine.milestone19 import requirements
from riogineer_engine.variable_pump_energy import pump, PumpFailure
from riogineer_engine.network_models import state_from_rates
from riogineer_engine.core import build_flowsheet,calculate,Invalid
HERE=Path(__file__).resolve().parent


def normalize(s):
    return dict(T_K=s['temperature_K'],P_Pa_abs=s['pressure_Pa_abs'],z=list(s['z'].values()),
        classification=s['classification'],beta=s['beta'],H_eq_J_mol=s['H_eq_J_mol'],S_eq_J_mol_K=s['S_eq_J_mol_K'],
        phases={k:dict(composition=list(v['composition'].values()),Z=v['Z'],h_J_mol=v['h_J_mol'],s_J_mol_K=v['s_J_mol_K']) for k,v in s['phases'].items()},
        PT_diagnostics=dict(stability=s['stability']))


def run():
    paths=[HERE/'reference.json']
    cases=json.loads(paths[0].read_text())['cases']
    rows=[]
    for c in cases:
        i=c['inputs'];r=requirements(Tin=i['T1'],Pin=i['P1'],Pout=i['P2'],eta=i['eta'],F=i['flow'],z=i['z'])
        u=r['equipment'][0];s=r['feeds'][0]['state'];feed=state_from_rates(s['component_mass_flow_kg_h'],s['temperature_K'],s['pressure_Pa_abs'],None)
        expected=c['accepted'];checks=[]
        def equal(name,a,b):checks.append(dict(field=name,actual=a,reference=b,passed=a==b))
        errors=[];details=[]
        for kind in ('callable','adapter'):
            try:
                if kind=='callable':
                    v=pump(dict(u,operating_parameters=u['parameters']),{'inlet':feed});d=v.details['thermodynamics'];out=v.streams['outlet']
                else:
                    v=calculate(build_flowsheet(r));d=v['equipment'][0]['thermodynamics'];out=v['streams']['PUMP_PRODUCT']
                    for stream in v['streams'].values():
                        equal('molar_unit',stream['properties']['molar_flow']['unit'],'kmol/h')
                        checks.append(dict(field='molar_flow',actual=stream['properties']['molar_flow']['value'],reference=i['flow']*3.6,passed=abs(stream['properties']['molar_flow']['value']-i['flow']*3.6)<1e-10))
                        equal('density_unavailable',stream['properties']['density']['value'],None)
                equal(kind+'.accepted',True,expected)
                equal(kind+'.rates',out['component_mass_flow_kg_h'],s['component_mass_flow_kg_h'])
                states={k:normalize(d[v]) for k,v in [('inlet','inlet'),('outlet','actual_outlet')]}
                # Comparator-only identity alias; production explicitly publishes null.
                states['isentropic']=normalize(d['isentropic_outlet'] or d['inlet'])
                metrics=finish(i,states);reference=dict(c['result'],metrics=finish(i,c['result']['states']))
                diags={} if d['mode']=='identity' else {k.upper():dict(d[k],status='success') for k in ('ps','ph')}
                checks+=compare(i,reference,dict(states=states,metrics=metrics,diagnostics=diags))
                equal(kind+'.power',d['fluid_power_W'],d['F_mol_s']*(d['actual_outlet']['H_eq_J_mol']-d['inlet']['H_eq_J_mol']))
                if d['mode']=='identity':
                    equal('identity.reference',d['isentropic_outlet'],None);equal('identity.ps',d['ps'],dict(status='not_applicable'))
                    equal('identity.witness_count',len(d['witnesses']),1)
                w={k:normalize(v) for k,v in d['witnesses'].items()}
                if 'witnesses' in c:checks+=compare(i,dict(states=c['witnesses']),dict(states=w,diagnostics={}))
                details.append(d)
            except (PumpFailure,Invalid) as e:
                errors.append(dict(path=kind,message=str(e)));equal(kind+'.accepted',False,expected)
        if len(details)==2:equal('callable_adapter_details',details[0],details[1])
        rows.append(dict(case_id=c['case_id'],inputs=i,expected_accepted=expected,checks=checks,errors=errors,passed=all(v['passed'] for v in checks)))
        print(c['case_id'],rows[-1]['passed'],flush=True)
    output=dict(production_source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'engine/riogineer_engine').glob('*.py'))},
        reference_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        cases=rows,case_count=len(rows),accepted_count=sum(r['expected_accepted'] for r in rows),
        comparison_count=sum(len(r['checks']) for r in rows),passed=all(r['passed'] for r in rows))
    (HERE/'equipment_comparison.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    assert output['passed'], 'Equipment comparison failed'
    print({k:v for k,v in output.items() if k!='cases'})

if __name__=='__main__':run()
