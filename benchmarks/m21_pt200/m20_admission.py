"""Fresh production integration against frozen independent evidence; no reference rerun."""
import json
import hashlib
import argparse
from pathlib import Path
from riogineer_engine.core import build_flowsheet, calculate
from riogineer_engine.milestone20 import requirements
from riogineer_engine.separator_pump_scope import CASES, specification
from riogineer_engine.separator_liquid_state import hb
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'benchmarks/m21_pt200'
PRIOR=ROOT/'benchmarks/low_pressure_separator_pump'

def verify(output=None):
    references={c['case_id']:c for c in json.loads((PRIOR/'reference.json').read_text())['cases']}
    ledger=json.loads((PRIOR/'phase_contract/candidate_ledger.json').read_text())
    accepted={c['case_id'] for c in ledger['cases'] if c['status']=='accepted'}
    assert {c['qualification_id'] for c in CASES}==accepted and len(CASES)==30
    sources=json.loads((PRIOR/'phase_contract/sources.json').read_text())['sources']
    rows=[]
    for row in CASES:
        cid=row['qualification_id']; ref=references[cid]; source=sources[cid if ref['role']=='scaled_flow' else ref['source']]['result']
        r=requirements(cid);f=build_flowsheet(r);out=calculate(f)
        sep,pump=out['equipment'];diag=pump['thermodynamics']['diagnostics']
        actual={'inlet':diag['inlet']['fresh'], 'isentropic':diag['isentropic'] or diag['inlet']['fresh'], 'outlet':diag.get('actual',diag['inlet']['fresh'])}
        checks=[]
        def check(label,a,b,tol=0):
            passed=abs(a-b)<=tol if isinstance(a,(float,int)) and not isinstance(a,bool) else a==b
            checks.append(dict(field=label,actual=a,reference=b,allowance=tol,passed=passed))
        # Independently derive input mapping from captured source and prior pressure/eta.
        source_sep=source['equipment'][0];sd=source_sep['thermodynamics'];sf=source['streams'][source_sep['material_streams']['inlet']]
        recipe=dict(feed={k:sf[k] for k in ('temperature_K','pressure_Pa_abs','component_mass_flow_kg_h')},mode=sd['mode'],separator_pressure_Pa_abs=sd['outlet']['pressure_Pa_abs'])
        if sd['mode']=='specified_temperature':recipe['separator_temperature_K']=sd['outlet']['temperature_K']
        assert row['recipe']==recipe
        assert row['outlet_pressure_Pa_abs']==ref['inputs']['P2'] and row['isentropic_efficiency']==ref['inputs']['eta']
        assert specification(f)=={k:v for k,v in row.items() if k!='qualification_id'}
        for key,a in actual.items():
            b=ref['result']['states'][key]
            for field,tol in [('T_K',1e-7),('P_Pa_abs',0),('H_eq_J_mol',hb(b['H_eq_J_mol'])),('S_eq_J_mol_K',1e-8+1e-11*abs(b['S_eq_J_mol_K'])),('beta',0),('classification',0)]:check(key+'.'+field,a[field],b[field],tol)
            for j in range(2):check(key+'.z'+str(j),a['z'][j],b['z'][j],1e-12)
            check(key+'.stable',a['stability']['stable'],True);check(key+'.converged',a['stability']['converged'],True)
            check(key+'.PIP',a['stability']['phase_identification_parameter']>1,True)
            for phase,values in a['phases'].items():
                target=b['phases'][phase]
                for field,tol in [('Z',1e-9),('h_J_mol',hb(target['h_J_mol'])),('s_J_mol_K',1e-8+1e-11*abs(target['s_J_mol_K']))]:check(key+'.'+phase+'.'+field,values[field],target[field],tol)
                for j in range(2):check(key+'.'+phase+'.x'+str(j),values['composition'][j],target['composition'][j],1e-12)
        check('power',pump['work_W'],ref['result']['metrics']['W_recovered_W'],ref['inputs']['flow']*(hb(actual['inlet']['H_eq_J_mol'])+hb(actual['outlet']['H_eq_J_mol'])))
        liquid=out['streams'][sep['material_streams']['liquid']];product=out['streams'][pump['material_streams']['outlet']]
        old=source['streams'][source_sep['material_streams']['liquid']]
        check('upstream_Hdot',liquid['enthalpy_flow_W'],old['enthalpy_flow_W'],diag['inlet']['enthalpy_allowance_W'])
        check('producer',product['state_context']['source']['equipment_id'],pump['id'])
        check('lineage',product['state_context']['lineage'][0],liquid['state_context']['source'])
        check('new_run',out['run_id']!=source['run_id'],True)
        if diag['identity']:
            check('identity_material',{k:v for k,v in product.items() if k!='state_context'},{k:v for k,v in liquid.items() if k!='state_context'})
            check('identity_PS',diag['PS'],None);check('identity_PH',diag['PH'],None)
        else:
            check('PS_scan',diag['PS']['scan_count'],64);check('PH_scan',diag['PH']['scan_count'],128)
            check('resolved_work',diag['work_ratio']<=1e-4,True)
        rows.append(dict(case_id=cid,checks=checks,result=out,original_input_sha256=source['input_sha256']))
        print(cid, 'PASS' if all(c['passed'] for c in checks) else 'FAIL', flush=True)
    result=dict(cases=rows,comparison_count=sum(len(r['checks']) for r in rows),failed_checks=sum(not c['passed'] for r in rows for c in r['checks']),reference_sha256=hashlib.sha256((PRIOR/'reference.json').read_bytes()).hexdigest())
    target=Path(output) if output else HERE/'m20_current.json'
    if output:
        assert not target.exists();target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    else:
        old=json.loads(target.read_text())
        assert old['comparison_count']==result['comparison_count'] and old['failed_checks']==result['failed_checks']
        assert len(result['cases'])==len(old['cases'])==30
        for actual,frozen in zip(result['cases'],old['cases']):
            assert actual['case_id']==frozen['case_id']
            assert len(actual['checks'])==len(frozen['checks'])
            for a,b in zip(actual['checks'],frozen['checks']):
                assert a['field']==b['field']
                if a['field']=='lineage':assert a['passed'] and b['passed']  # fresh UUID association, not UUID equality
                else:assert a==b
        print('PASS current M20 numerical comparisons; fresh UUIDs intentionally differ')
    assert result['failed_checks']==0
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args();verify(args.output)
