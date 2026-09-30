"""Production valve acceptance against the committed independent Pre-M16 JSON."""
import argparse
from contextlib import nullcontext, contextmanager
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.components import component
from riogineer_engine.throttling_valve_energy import MODEL, ValveFailure
from riogineer_engine.core import build_flowsheet,calculate
from riogineer_engine.network_models import MODELS,state_from_rates
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.pr_ph_flash import flash_ph, PHSpecification
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance
from riogineer_engine.pr_eos import BinaryInteractions
from riogineer_engine.compressor_energy import caloric_state

HERE=Path(__file__).resolve().parent
REFERENCE=HERE/'methane_nhexane_throttling_valve_reference.json'
ARTIFACT=HERE/'production_comparison.json'
SHA='ef0141ec3b72740175553381f2e0431290a0fa8eb937bd03ad0259a9aa2dbead'
IDS=('methane','n_hexane')


def encode(x):return json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n'


def reference():
    raw=REFERENCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
    return json.loads(raw)


def decode(x):
    if isinstance(x,str) and x in ('NaN','Infinity','-Infinity'):return float(x)
    if isinstance(x,list):return [decode(v) for v in x]
    if isinstance(x,dict):return {k:decode(v) for k,v in x.items()}
    return x


def inputs(i):
    ids=i.get('ids',IDS)
    rates={name:i['F']*3600./1000.*z*component(name if name in IDS else 'methane').molecular_weight for name,z in zip(ids,i['z'])}
    feed=state_from_rates(rates,i['Tin'],i['Pin'],None)
    if abs(sum(i['z'])-1)>1e-12:feed['mass_flow_kg_h']=sum(rates.values())/sum(i['z'])
    p=dict(outlet_pressure_Pa_abs=i['Pout'],property_package='peng_robinson@1.0',
        bip=dict(identifier='m16_qualified_zero@1.0',component_ids=list(IDS),values=i.get('kij',[[0.,0.],[0.,0.]]),
            source='Explicit qualified constant zero kij; not fitted',model='peng_robinson@1.0'))
    return dict(id='VALVE_1',type='throttling_valve',model=dict(MODEL),operating_parameters=p),{'inlet':feed}


def requirements(i):
    unit,streams=inputs(i)
    feed={k:streams['inlet'][k] for k in ('temperature_K','pressure_Pa_abs','component_mass_flow_kg_h')}
    return dict(schema_version='1.8',kind='requirements',case_id='M16_REFERENCE',profile='throttling_valve_energy',
        units=dict(temperature='K',pressure='Pa_abs',component_mass_flow='kg/h',heat_capacity='J/(kg K)',duty='W',recovery='mass_fraction'),
        provenance=dict(source='Frozen Pre-M16 production acceptance',basis='qualified_equilibrium_energy'),components=list(IDS),
        feeds=[dict(id='SOURCE',state=feed)],sinks=[dict(id='SINK')],
        equipment=[dict(id=unit['id'],type=unit['type'],model=unit['model'],parameters=unit['operating_parameters'])],
        streams=[dict(id='FEED',service='feed'),dict(id='PRODUCT',service='product')],
        connections=[dict(id='C1',stream_id='FEED',source=dict(owner_id='SOURCE',port_id='outlet'),target=dict(owner_id=unit['id'],port_id='inlet')),
            dict(id='C2',stream_id='PRODUCT',source=dict(owner_id=unit['id'],port_id='outlet'),target=dict(owner_id='SINK',port_id='inlet'))],
        required_outputs=['streams','mass_balance','energy_balance'])


def evaluate(i):return calculate(build_flowsheet(requirements(i)))


def interval_evidence(q):
    intervals=[];active=False;failed=[]
    for t in q.diagnostics.trials:
        if t.stage!='scan':continue
        if t.status!='success':failed.append(dict(T_K=t.temperature_K,status=t.status,underlying=t.underlying_status));active=False;continue
        if not active:intervals.append([t.temperature_K,t.temperature_K])
        else:intervals[-1][1]=t.temperature_K
        active=True
    return dict(valid_intervals_K=intervals,failed_scan_points=failed,candidates_K=q.diagnostics.brackets_K,
                fresh_final=q.diagnostics.trials[-1].stage=='final')


def evaluate_with_evidence(i):
    original=PengRobinsonProvider.flash_PH;records=[]
    def observe(self,*args,**kwargs):
        q=original(self,*args,**kwargs);records.append(interval_evidence(q));return q
    with patch.object(PengRobinsonProvider,'flash_PH',observe):r=evaluate(i)
    assert len(records)==1
    return r,records[0]


def study(c):
    i=c['inputs'];b=BinaryInteractions('m16_study_zero@1.0',IDS,((0.,0.),(0.,0.)),'Explicit zero')
    p=PengRobinsonProvider();z=MolarComposition(IDS,tuple(i['z']));pr=StateSpecificationProvenance('peng_robinson@1.0',b.identifier)
    a=p.equilibrium_caloric_PT(ThermodynamicState(i['Tin'],i['Pin'],z,pr),b,SolverSettings.high_accuracy())
    q=p.flash_PH(PHSpecification(i['Pout'],a.aggregate.h_J_mol,z,pr),b)
    assert q.status=='success',(c['case_id'],q.status)
    checks=[];states={}
    for end,v in [('inlet',a),('outlet',q.caloric)]:
        s=caloric_state(v);e=c['result'][end];states[end]=s;assert s['classification']==e['classification']
        values=dict(T=s['temperature_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
        targets=dict(T=e['T_K'],H=e['H_eq_J_mol'],S=e['S_eq_J_mol_K'],beta=e['beta'])
        for j,k in enumerate(IDS):values['z'+str(j)]=s['z'][k];targets['z'+str(j)]=e['z'][j]
        for phase,v in e['phases'].items():
            for key,name in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:values[phase+'.'+key]=s['phases'][phase][name];targets[phase+'.'+key]=v[name]
            for j,k in enumerate(IDS):values[phase+'.q'+str(j)]=s['phases'][phase]['composition'][k];targets[phase+'.q'+str(j)]=v['composition'][j]
        for k,target in targets.items():
            err=abs(values[k]-target);allow=c['allowances'][end][k];assert err<=allow,(c['case_id'],end,k,err,allow)
            checks.append(dict(field=end+'.'+k,error=err,allowance=allow))
    return dict(case_id=c['case_id'],role='separate thermodynamic study; not primary equipment service qualification',states=states,checks=checks,ph=interval_evidence(q))


def compare_case(c,r):
    d=r['equipment'][0]['thermodynamics'];checks=[]
    assert r['schema_version']=='1.10' and r['equipment'][0]['model']==MODEL
    assert r['equipment'][0]['material_streams']==dict(inlet='FEED',outlet='PRODUCT') and len(r['streams'])==2
    def check(field,a,b,tol):
        error=abs(a-b);row=dict(field=field,actual=a,reference=b,absolute_error=error,allowance=tol,passed=error<=tol)
        checks.append(row);assert row['passed'],(c['case_id'],row)
    for end in ('inlet','outlet'):
        p=d[end];e=c['result'][end];tol=c['allowances'][end]
        assert p['classification']==e['classification'] and p['phases'].keys()==e['phases'].keys()
        for key,a,b in [('T',p['temperature_K'],e['T_K']),('H',p['H_eq_J_mol'],e['H_eq_J_mol']),
            ('S',p['S_eq_J_mol_K'],e['S_eq_J_mol_K']),('beta',p['beta'],e['beta'])]:check(end+'.'+key,a,b,tol[key])
        check(end+'.P',p['pressure_Pa_abs'],e['P_Pa_abs'],0.)
        for j,k in enumerate(IDS):check(end+'.z'+str(j),p['z'][k],e['z'][j],tol['z'+str(j)])
        for phase,v in e['phases'].items():
            q=p['phases'][phase]
            for key,name in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:check(end+'.'+phase+'.'+key,q[name],v[name],tol[phase+'.'+key])
            for j,k in enumerate(IDS):check(end+'.'+phase+'.q'+str(j),q['composition'][k],v['composition'][j],tol[phase+'.q'+str(j)])
    check('target_H',d['H_out_target_J_mol'],c['result']['H_out_target_J_mol'],c['allowances']['target_H'])
    check('delta_S',d['delta_S_J_mol_K'],c['result']['delta_S_J_mol_K'],c['allowances']['inlet']['S']+c['allowances']['outlet']['S'])
    check('enthalpy_residual',d['enthalpy_residual_J_mol'],0.,1e-6)
    check('energy_residual',d['energy_residual_W'],0.,c['allowances']['energy_W'])
    check('PH_residual',d['ph']['enthalpy_residual_J_mol'],0.,c['allowances']['PH_residual'])
    check('F',d['F_mol_s'],c['inputs']['F'],64*sys.float_info.epsilon*max(1.,c['inputs']['F']))
    check('pressure_ratio',d['pressure_ratio'],c['result']['pressure_ratio'],0.)
    assert d['ph']['candidate_count']==1 and d['ph']['status']=='success' and d['ph']['pt_profile']=='high_accuracy'
    assert r['streams']['FEED']['component_mass_flow_kg_h']==r['streams']['PRODUCT']['component_mass_flow_kg_h']
    assert d['inlet']['z']==d['outlet']['z'] and r['balances']['mass']['total_residual_kg_h']==0
    return checks


def injection(name):
    if not name:return nullcontext()
    if name=='PT':return patch.object(PengRobinsonProvider,'equilibrium_caloric_PT',return_value=CaloricResult('pt_evaluation_failure',None,message='Controlled inlet PT failure'))
    if name=='PH':return patch.object(PengRobinsonProvider,'flash_PH',return_value=SimpleNamespace(status='controlled_ph_failure',caloric=None,diagnostics='Controlled PH failure'))
    if name in ('AMBIGUOUS','HOLE','UNBRACKETED'):
        def synthetic(self,s,bip,settings=None):
            seed=self.equilibrium_caloric_PT(ThermodynamicState(300.,s.pressure_Pa_abs,s.composition,s.provenance),bip,SolverSettings.high_accuracy())
            def evaluator(state,bip,settings):
                T=state.temperature_K
                if name=='HOLE' and 290<T<310:return CaloricResult('flash_not_converged',replace(seed.equilibrium,status='flash_not_converged',phases=(),beta=None,final_K=()),message='Controlled property hole')
                h=(T-270)*(T-430) if name=='AMBIGUOUS' else T+1e6 if name=='UNBRACKETED' else T-300
                return replace(seed,aggregate=replace(seed.aggregate,h_J_mol=h))
            return flash_ph(replace(s,enthalpy_J_mol=0.),bip,evaluator)
        return patch.object(PengRobinsonProvider,'flash_PH',synthetic)
    if name=='FRESH_FINAL':return final_injection()
    raise AssertionError(name)


@contextmanager
def final_injection():
    original_ph=PengRobinsonProvider.flash_PH
    original_pt=PengRobinsonProvider.equilibrium_caloric_PT
    corrupt=False
    def inverse(self,*args,**kwargs):
        nonlocal corrupt
        result=original_ph(self,*args,**kwargs);corrupt=True
        return result
    def evaluate(self,*args,**kwargs):
        c=original_pt(self,*args,**kwargs)
        return replace(c,aggregate=replace(c.aggregate,h_J_mol=c.aggregate.h_J_mol+1.)) if corrupt else c
    with patch.object(PengRobinsonProvider,'flash_PH',inverse), patch.object(PengRobinsonProvider,'equilibrium_caloric_PT',evaluate):
        yield


def negative(c):
    u,s=inputs(decode(c['inputs']));expected=c['expected_status'];stage=c['expected_stage']
    if c['case_id'] in ('Z_NEGATIVE','Z_NAN','Z_INF'):expected='invalid_flow'
    if c['case_id']=='Z_LENGTH':expected='unsupported_component'
    with injection(c['injection']):
        try:MODELS['throttling_valve']['execute'](u,s,None)
        except ValveFailure as error:
            assert (error.status,error.stage)==(expected,stage),(c['case_id'],expected,stage,error.status,error.stage)
            return dict(case_id=c['case_id'],independent_category=c['expected_status'],status=error.status,stage=error.stage,accepted_outlet=False,passed=True)
    raise AssertionError((c['case_id'],'Unexpected accepted outlet'))


def stable(r):
    r=deepcopy(r);r.pop('run_id');return r


def build():
    ref=reference();rows=[];maxima={}
    for c in ref['cases']:
        r,internal=evaluate_with_evidence(c['inputs']);checks=compare_case(c,r)
        for x in checks:
            if x['field'] not in maxima or x['absolute_error']>maxima[x['field']]['absolute_error']:maxima[x['field']]=dict(case_id=c['case_id'],**x)
        rows.append(dict(case_id=c['case_id'],group=c['group'],inputs=c['inputs'],production=stable(r),ph_intervals=internal,comparisons=checks,passed=True))
    negatives=[negative(c) for c in ref['negative_cases']]
    studies=[study(c) for c in ref['separate_studies']]
    c=next(c for c in ref['separate_studies'] if c['case_id']=='TWO_PHASE_INLET')
    u,inputs_map=inputs(c['inputs'])
    try:MODELS['throttling_valve']['execute'](u,inputs_map,None)
    except ValveFailure as error:assert error.status=='inlet_service_scope'
    else:raise AssertionError('VL inlet accepted')
    next(c for c in studies if c['case_id']=='TWO_PHASE_INLET')['equipment_service']='rejected: VL inlet'
    scaling=[]
    base=rows[0]['production']['equipment'][0]['thermodynamics']
    for item in ref['flow_scaling']:
        row=next(c for c in rows if c['case_id']==item['case_id'])
        d=row['production']['equipment'][0]['thermodynamics']
        assert all(d[k]==base[k] for k in ('inlet','outlet','H_out_target_J_mol'))
        error=abs(d['energy_residual_W']-d['F_mol_s']/base['F_mol_s']*base['energy_residual_W'])
        assert error<=item['allowance_W'],(item,error)
        scaling.append(dict(case_id=item['case_id'],error_W=error,allowance_W=item['allowance_W'],intensive_byte_identical=True))
    order=[];byid={c['case_id']:c for c in rows}
    for target,history in [('CANONICAL','PRESSURE_FLASH_ONSET'),('LIQUID_HEATING','VAPOR_SIMPLE'),
            ('VAPOR_SIMPLE','HEXANE_RICH'),('CANONICAL','PH'),('CANONICAL','PURE_METHANE'),
            ('PRESSURE_FLASH_ONSET','HOLE'),('PURE_HEXANE_LIQUID','AMBIGUOUS'),('CANONICAL','FRESH_FINAL')]:
        if history in byid:evaluate(byid[history]['inputs'])
        else:negative(next(c for c in ref['negative_cases'] if c['case_id']==history))
        c=byid[target]
        assert stable(evaluate(c['inputs']))==c['production']
        order.append(dict(case_id=target,history=history,byte_identical=True))
    return dict(reference_sha256=SHA,model=MODEL,positive_cases=rows,negative_cases=negatives,separate_studies=studies,
        flow_scaling=scaling,maxima=maxima,comparisons=sum(len(x['comparisons']) for x in rows),call_order=order,passed=True)


def review(mode):
    ref=reference();rows=[]
    for c in ref['cases']:
        if c['group']==mode or (mode in ('flow','phase') and c['case_id']=='CANONICAL'):
            r,internal=evaluate_with_evidence(c['inputs'])
            rows.append(dict(case_id=c['case_id'],group=c['group'],inputs=c['inputs'],production=stable(r),ph_intervals=internal,comparisons=compare_case(c,r)))
    negatives=[negative(c) for c in ref['negative_cases'] if mode=='negative' or (mode=='pure' and c['case_id']=='PURE_COEXISTENCE_GAP')]
    studies=[study(c) for c in ref['separate_studies']] if mode=='phase' else []
    if mode=='phase':
        i=next(c['inputs'] for c in ref['separate_studies'] if c['case_id']=='TWO_PHASE_INLET');u,feed=inputs(i)
        try:MODELS['throttling_valve']['execute'](u,feed,None)
        except ValveFailure as error:assert error.status=='inlet_service_scope'
        else:raise AssertionError('VL inlet accepted')
        next(c for c in studies if c['case_id']=='TWO_PHASE_INLET')['equipment_service']='rejected: VL inlet'
    scaling=[]
    if mode=='flow':
        base=rows[0]['production']['equipment'][0]['thermodynamics']
        for item in ref['flow_scaling']:
            d=next(c for c in rows if c['case_id']==item['case_id'])['production']['equipment'][0]['thermodynamics']
            assert all(d[k]==base[k] for k in ('inlet','outlet','H_out_target_J_mol'))
            error=abs(d['energy_residual_W']-d['F_mol_s']/base['F_mol_s']*base['energy_residual_W']);assert error<=item['allowance_W']
            scaling.append(dict(case_id=item['case_id'],error_W=error,allowance_W=item['allowance_W'],intensive_byte_identical=True))
    return dict(positive_cases=rows,negative_cases=negatives,separate_studies=studies,flow_scaling=scaling,call_order=[],comparisons=sum(len(c['comparisons']) for c in rows))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',default='summary',choices=['canonical','pressure','flow','composition','phase','pure','negative','summary'])
    parser.add_argument('--write',action='store_true');parser.add_argument('--verify',action='store_true')
    a=parser.parse_args()
    if a.case=='summary' or a.write or a.verify:
        r=build();raw=encode(r)
        if a.write:ARTIFACT.write_text(raw)
        if a.verify:assert ARTIFACT.read_text()==raw,'Production artifact differs'
    else:
        r=review(a.case)
    for c in r['positive_cases']:
        if a.case=='summary' or (a.case=='phase' and c['case_id']=='CANONICAL') or (a.case=='canonical' and c['case_id']=='CANONICAL') or c['group']==a.case:
            d=c['production']['equipment'][0]['thermodynamics'];print(c['case_id'],'PASS',d['outlet'],'closure',d['enthalpy_residual_J_mol'],d['energy_residual_W'],'PH',d['ph'])
    if a.case=='summary':
        for field,maximum in r['maxima'].items():print(field,maximum)
    if a.case=='flow':
        for row in r['flow_scaling']:print(row)
    if a.case=='phase':
        for row in r['separate_studies']:print(row)
    if a.case in ('negative','pure'):
        for c in r['negative_cases']:print(c)
    print('PASS:',len(r['positive_cases']),'positive;',len(r['negative_cases']),'negative;',r['comparisons'],'comparisons;',len(r['call_order']),'call-order checks')
    print('Human-operated M16 validation remains pending.')


if __name__=='__main__':main()
