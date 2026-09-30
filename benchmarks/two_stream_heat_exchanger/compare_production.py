"""M15 production acceptance against immutable independent Pre-M15 evidence."""
from copy import deepcopy
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.components import component
from riogineer_engine.core import build_flowsheet, calculate
from riogineer_engine.network_models import state_from_rates
from riogineer_engine.two_stream_heat_exchanger_energy import MODEL, exchanger, ExchangerFailure
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.pr_ph_flash import flash_ph
from riogineer_engine.pr_flash import SolverSettings

HERE = Path(__file__).resolve().parent
REFERENCE = HERE/'methane_nhexane_two_stream_hx_reference.json'
ARTIFACT = HERE/'production_comparison.json'
SHA = '533797cb1b26a8f3e597907ab9cc1e480353bd189280cfde273157cd3fa0e4b1'
IDS = ('methane','n_hexane')


def encode(x):return json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n'


def reference():
    raw=REFERENCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==SHA
    return json.loads(raw)


def decode(x):
    if isinstance(x,str) and x in ('NaN','Infinity','-Infinity'):return float(x)
    if isinstance(x,list):return [decode(v) for v in x]
    if isinstance(x,dict):return {k:decode(v) for k,v in x.items()}
    return x


def inputs(i):
    streams={}
    for side in ('hot','cold'):
        s=i[side];ids=s.get('ids',IDS)
        rates={k:s['F']*3.6*z*component(k if k in IDS else 'methane').molecular_weight for k,z in zip(ids,s['z'])}
        # Invalid fixture compositions must remain invalid after the unit conversion.
        feed=state_from_rates(rates,s['Tin'],s['Pin'],None)
        if all(math.isfinite(z) for z in s['z']) and abs(sum(s['z'])-1)>1e-12:
            feed['mass_flow_kg_h']=sum(rates.values())/sum(s['z'])
        if not all(math.isfinite(z) for z in s['z']):
            feed['mass_flow_kg_h']=s['F']*3.6*component('methane').molecular_weight
        streams[side+'_in']=feed
    p=dict(property_package='peng_robinson@1.0',hot_outlet_pressure_Pa_abs=i['hot']['Pout'],cold_outlet_pressure_Pa_abs=i['cold']['Pout'],
        bip=dict(identifier='m15_qualified_zero@1.0',component_ids=list(IDS),values=i.get('kij',[[0.,0.],[0.,0.]]),source='Explicit qualified constant zero kij',model='peng_robinson@1.0'))
    if 'T_hot_out' in i:p.update(mode='specified_hot_outlet_temperature',hot_outlet_temperature_K=i['T_hot_out'])
    if 'T_cold_out' in i:p.update(mode='specified_cold_outlet_temperature',cold_outlet_temperature_K=i['T_cold_out'])
    return dict(id='HX',type='two_stream_heat_exchanger',model=dict(MODEL),operating_parameters=p),streams


def requirements(i):
    u,s=inputs(i)
    r=dict(schema_version='1.7',kind='requirements',case_id='M15_REFERENCE',profile='two_stream_heat_exchanger_energy',
        units=dict(temperature='K',pressure='Pa_abs',component_mass_flow='kg/h',heat_capacity='J/(kg K)',duty='W',recovery='mass_fraction'),
        provenance=dict(source='Frozen Pre-M15 production acceptance',basis='qualified_equilibrium_energy'),components=list(IDS),feeds=[],sinks=[],
        equipment=[dict(id=u['id'],type=u['type'],model=u['model'],parameters=u['operating_parameters'])],streams=[],connections=[],required_outputs=['streams','mass_balance','energy_balance'])
    for side in ('hot','cold'):
        source=side.upper()+'_SOURCE';sink=side.upper()+'_SINK'
        r['feeds'].append(dict(id=source,state={k:s[side+'_in'][k] for k in ('temperature_K','pressure_Pa_abs','component_mass_flow_kg_h')}));r['sinks'].append(dict(id=sink))
        for end in ('in','out'):
            sid=side.upper()+'_'+end.upper();port=side+'_'+end
            r['streams'].append(dict(id=sid,service=port))
            r['connections'].append(dict(id='C_'+sid,stream_id=sid,
                source=dict(owner_id=source,port_id='outlet') if end=='in' else dict(owner_id='HX',port_id=port),
                target=dict(owner_id='HX',port_id=port) if end=='in' else dict(owner_id=sink,port_id='inlet')))
    return r


def evaluate(i):
    output=calculate(build_flowsheet(requirements(i)))
    del output['run_id']  # Existing public API run identity is deliberately random.
    return output


def compare_case(c,output):
    d=output['equipment'][0]['thermodynamics'];r=c['result'];a=c['allowances'];checks=[]
    def check(field,x,y,tol):
        error=abs(x-y);row=dict(field=field,actual=x,reference=y,absolute_error=error,allowance=tol,passed=math.isfinite(error) and error<=tol)
        checks.append(row)
        assert row['passed'],(c['case_id'],row)
    for side in ('hot','cold'):
        for end in ('in','out'):
            key=side+'_'+end;p=d[side+'_'+('inlet' if end=='in' else 'outlet')];q=r['states'][key];t=a['states'][key]
            assert p['classification']==q['classification'] and p['phases'].keys()==q['phases'].keys(),(c['case_id'],key)
            for label,pf,qf in [('T','temperature_K','T_K'),('H','H_eq_J_mol','H_eq_J_mol'),('beta','beta','beta')]:check(key+'.'+label,p[pf],q[qf],t[label])
            check(key+'.P',p['pressure_Pa_abs'],q['P_Pa_abs'],0.)
            for j,k in enumerate(IDS):check(key+'.z'+str(j),p['z'][k],q['z'][j],2e-9)
            for phase,v in q['phases'].items():
                w=p['phases'][phase]
                for label,field in [('Z','Z'),('H','h_J_mol')]:check(key+'.'+phase+'.'+label,w[field],v[field],t[phase+'.'+label])
                for j,k in enumerate(IDS):check(key+'.'+phase+'.q'+str(j),w['composition'][k],v['composition'][j],t[phase+'.q'+str(j)])
        check('Q_'+side,d['Q_'+side+'_W'],r['Q_'+side+'_W'],a['duty_W'][side])
        check(side+'.flow',d[side+'_molar_flow_mol_s'],c['inputs'][side]['F'],64*sys.float_info.epsilon*max(1.,c['inputs'][side]['F']))
        si=output['streams'][side.upper()+'_IN'];so=output['streams'][side.upper()+'_OUT']
        assert si['component_mass_flow_kg_h']==so['component_mass_flow_kg_h'] and si['component_mass_fractions']==so['component_mass_fractions']
        check(side+'.mass_residual',so['mass_flow_kg_h']-si['mass_flow_kg_h'],0.,0.)
        check(side+'.duty_identity',d['Q_'+side+'_W'],d[side+'_molar_flow_mol_s']*(d[side+'_outlet']['H_eq_J_mol']-d[side+'_inlet']['H_eq_J_mol']),0.)
    check('Q_exchanged',d['Q_exchanged_W'],r['Q_exchanged_W'],a['duty_W']['cold'])
    check('energy_residual',d['energy_residual_W'],0.,a['energy_W'])
    check('PH_residual',d['ph']['enthalpy_residual_J_mol'],0.,a['PH_residual_J_mol'])
    check('H_target',d['recovered_outlet_target_enthalpy_J_mol'],r['H_target_J_mol'],a['H_target_J_mol'])
    check('duty_closure',d['Q_hot_W']+d['Q_cold_W'],0.,a['energy_W'])
    assert d['ph']['candidate_count']==1 and d['ph']['pt_profile']=='high_accuracy'
    return checks


def injection(name):
    if not name:return nullcontext()
    if name.startswith('PT:'):
        index={'hot_inlet_PT':1,'cold_inlet_PT':2,'specified_hot_outlet_PT':3,'specified_cold_outlet_PT':3}[name[3:]]
        original=PengRobinsonProvider.equilibrium_caloric_PT;calls=[]
        def broken(self,*args,**kwargs):
            calls.append(1)
            if len(calls)==index:return CaloricResult('pt_evaluation_failure',None,message='Controlled PT failure')
            return original(self,*args,**kwargs)
        return patch.object(PengRobinsonProvider,'equilibrium_caloric_PT',broken)
    if name=='PH':
        return patch.object(PengRobinsonProvider,'flash_PH',return_value=SimpleNamespace(status='controlled_ph_failure',caloric=None,diagnostics='Injected failure'))
    if name=='FRESH_FINAL':
        original=PengRobinsonProvider.flash_PH
        def corrupt(self,*args,**kwargs):
            r=original(self,*args,**kwargs)
            return replace(r,caloric=replace(r.caloric,aggregate=replace(r.caloric.aggregate,h_J_mol=r.caloric.aggregate.h_J_mol+1.)))
        return patch.object(PengRobinsonProvider,'flash_PH',corrupt)
    if name in ('AMBIGUOUS','HOLE'):
        def synthetic(self,s,bip,settings=None):
            from riogineer_engine.thermodynamics import ThermodynamicState
            seed=self.equilibrium_caloric_PT(ThermodynamicState(300.,s.pressure_Pa_abs,s.composition,s.provenance),bip,SolverSettings.high_accuracy())
            def evaluator(state,bip,settings):
                T=state.temperature_K
                if name=='HOLE' and 290<T<310:
                    return replace(seed,status='controlled_hole',aggregate=None,equilibrium=replace(seed.equilibrium,status='controlled_hole'))
                h=(T-270)*(T-430) if name=='AMBIGUOUS' else T-300
                return replace(seed,aggregate=replace(seed.aggregate,h_J_mol=h))
            return flash_ph(replace(s,enthalpy_J_mol=0.),bip,evaluator)
        return patch.object(PengRobinsonProvider,'flash_PH',synthetic)
    raise AssertionError(name)


def negative(c):
    u,i=inputs(decode(c['inputs']))
    with injection(c['synthetic']):
        try:exchanger(u,i)
        except ExchangerFailure as error:
            assert (error.stage,error.status)==(c['expected_stage'],c['expected_status']),(c['case_id'],error.stage,error.status,c['expected_stage'],c['expected_status'])
            return dict(case_id=c['case_id'],independent_status=c['expected_status'],stage=error.stage,status=error.status,
                synthetic=c['synthetic'],accepted_complete_exchanger_result=False,passed=True)
    raise AssertionError((c['case_id'],'Unexpected accepted result'))


def reciprocal(c,original):
    # Use production's recovered temperature as the opposite specification.
    i=deepcopy(c['inputs']);specified='hot' if 'T_hot_out' in i else 'cold';recovered='cold' if specified=='hot' else 'hot'
    d=original['equipment'][0]['thermodynamics']
    del i['T_'+specified+'_out'];i['T_'+recovered+'_out']=d[recovered+'_outlet']['temperature_K']
    out=evaluate(i);rev=out['equipment'][0]['thermodynamics'];checks=[]
    for row in c['reciprocal']['checks']:
        field=row['field'];suffix=field.removeprefix('reciprocal.')
        if suffix in ('hot.T','hot.H','cold.T','cold.H'):
            side,key=suffix.split('.');key={'T':'temperature_K','H':'H_eq_J_mol'}[key]
            x,y=rev[side+'_outlet'][key],d[side+'_outlet'][key]
        else:
            key=suffix+'_W';x,y=rev[key],d[key]
        error=abs(x-y);assert math.isfinite(error) and error<=row['allowance'],(c['case_id'],field,error,row['allowance'])
        checks.append(dict(field=field,actual=x,reference=y,absolute_error=error,allowance=row['allowance'],passed=True))
    assert rev['ph']['candidate_count']==1 and abs(rev['ph']['enthalpy_residual_J_mol'])<=1e-6
    assert abs(rev['energy_residual_W'])<=rev['energy_allowance_W']
    for side in ('hot','cold'):
        assert rev[side+'_outlet']['classification']==d[side+'_outlet']['classification']
    return dict(inputs=i,production=out,comparisons=checks,passed=True)


def build():
    ref=reference();rows=[];maxima={}
    for c in ref['cases']:
        out=evaluate(c['inputs']);checks=compare_case(c,out);rev=reciprocal(c,out)
        rows.append(dict(case_id=c['case_id'],group=c['group'],inputs=c['inputs'],production=out,comparisons=checks,reciprocal=rev,passed=True))
    negatives=[negative(c) for c in ref['negative_cases']]
    scope=[]
    for c in ref['phase_studies']:
        try:evaluate(c['inputs'])
        except ValueError as error:
            assert 'phase_service_scope' in str(error),(c['case_id'],str(error))
            scope.append(dict(case_id=c['case_id'],independent_thermodynamics='calculable',production_status='phase_service_scope',accepted_complete_exchanger_result=False,passed=True))
        else:raise AssertionError((c['case_id'],'Unexpected phase-service acceptance'))
    byid={c['case_id']:c for c in rows};base=rows[0];d=base['production']['equipment'][0]['thermodynamics'];scaling=[]
    for frozen in ref['flow_scaling']:
        row=byid[frozen['case_id']];q=frozen['quantity']+'_W';v=row['production']['equipment'][0]['thermodynamics']
        ratio=row['inputs']['hot']['F']/base['inputs']['hot']['F'];error=abs(v[q]-ratio*d[q]);assert error<=frozen['allowance_W'],(frozen,error)
        scaling.append(dict(case_id=row['case_id'],field='scaling.'+q,actual=v[q],reference=ratio*d[q],absolute_error=error,allowance=frozen['allowance_W'],passed=True))
    doubled=byid['DOUBLE_BOTH_FLOWS']['production']['equipment'][0]['thermodynamics']
    for state in ('hot_inlet','hot_outlet','cold_inlet','cold_outlet'):assert doubled[state]==d[state]
    for name in ('ZERO_DUTY','ZERO_DUTY_COLD_DROP'):
        v=byid[name]['production']['equipment'][0]['thermodynamics'];assert v['Q_hot_W']==0. and abs(v['Q_cold_W'])<=v['energy_allowance_W']
    z=byid['ZERO_DUTY_COLD_DROP']['production']['equipment'][0]['thermodynamics'];assert abs(z['cold_outlet']['temperature_K']-z['cold_inlet']['temperature_K'])>1e-6
    order=[];negative_byid={c['case_id']:c for c in ref['negative_cases']}
    for history in ('clean','positive','pure','negative','PH_failure','reciprocal_first'):
        if history=='positive':evaluate(byid['LIQUID_BOTH']['inputs'])
        elif history=='pure':evaluate(byid['PURE_HEXANE']['inputs'])
        elif history=='negative':negative(ref['negative_cases'][0])
        elif history=='PH_failure':negative(negative_byid['A_PH_INJECTED'])
        elif history=='reciprocal_first':evaluate(base['reciprocal']['inputs'])
        for name,inputs_,expected in [('CANONICAL',base['inputs'],base['production']),('CANONICAL_RECIPROCAL',base['reciprocal']['inputs'],base['reciprocal']['production'])]:
            actual=evaluate(inputs_);assert encode(actual)==encode(expected),(history,name)
            order.append(dict(after=history,case_id=name,byte_identical=True))
    count=0
    for c in rows:
        for x in c['comparisons']+c['reciprocal']['comparisons']:
            count+=1
            if x['field'] not in maxima or x['absolute_error']>maxima[x['field']]['absolute_error']:maxima[x['field']]=dict(case_id=c['case_id'],**x)
    for x in scaling:
        count+=1
        if x['field'] not in maxima or x['absolute_error']>maxima[x['field']]['absolute_error']:maxima[x['field']]=x
    return dict(reference_id=ref['reference_id'],reference_sha256=SHA,model=MODEL,cases=rows,negative_cases=negatives,
        service_scope=scope,flow_scaling=scaling,call_order=order,maximum_errors=maxima,comparison_count=count,passed=True)


MODES=('canonical','reciprocal','flow','phase','zero_duty','temperature_scope','negative','summary','pressure','composition','pure')


def display(r,mode):
    if mode=='negative':
        for c in r['negative_cases']:print(c['case_id'],c['stage'],c['status'],'accepted: No PASS')
    elif mode=='phase':
        for c in r['service_scope']:print(c['case_id'],'independent: calculable; production: rejected; PASS')
    elif mode=='summary':
        for field,c in sorted(r['maximum_errors'].items()):print(f"{field:30s} error={c['absolute_error']:.9g} allowance={c['allowance']:.9g} case={c['case_id']} PASS")
    else:
        rows=[c for c in r['cases'] if c['group']==mode or mode=='reciprocal' or (mode=='temperature_scope' and c['case_id']=='CANONICAL')]
        for c in rows:
            d=c['production']['equipment'][0]['thermodynamics']
            print(f"{c['case_id']}: {d['specification_mode']} hot {d['hot_inlet']['temperature_K']:.9f} -> {d['hot_outlet']['temperature_K']:.9f} K; cold {d['cold_inlet']['temperature_K']:.9f} -> {d['cold_outlet']['temperature_K']:.9f} K")
            print(f"  Q_hot={d['Q_hot_W']:.12g} Q_cold={d['Q_cold_W']:.12g} Q_exchanged={d['Q_exchanged_W']:.12g} W; energy={d['energy_residual_W']:.9g} W; PH={d['ph']['enthalpy_residual_J_mol']:.9g} J/mol; candidates=1; high_accuracy PASS")
            if mode=='reciprocal':
                for x in c['reciprocal']['comparisons']:print(f"  {x['field']} error={x['absolute_error']:.9g} allowance={x['allowance']:.9g} PASS")
        if mode=='flow':
            for x in r['flow_scaling']:print(x['case_id'],x['field'],'error=',x['absolute_error'],'allowance=',x['allowance'],'PASS')
        if mode=='temperature_scope':
            for c in r['negative_cases']:
                if c['case_id'] in ('TERMINAL_CROSSING','REVERSED_DUTY'):print(c['case_id'],c['status'],'accepted: No PASS')
            print('Terminal thermodynamic balance does not establish design feasibility; no minimum approach criterion.')
    print(f"PASS: {len(r['cases'])} primary positive; {len(r['negative_cases'])} negative; {len(r['service_scope'])} excluded phase studies; {r['comparison_count']} numerical comparisons; {len(r['call_order'])} byte-identical call-order checks")


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',choices=MODES,default='summary')
    parser.add_argument('--write',action='store_true');parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    # Summary and artifact operations execute every gate. Other review modes
    # freshly calculate their displayed subset without rewriting acceptance truth.
    if args.case=='summary' or args.write or args.verify:
        r=build()
    else:
        ref=reference();r=dict(cases=[],negative_cases=[],service_scope=[],flow_scaling=[],call_order=[],comparison_count=0)
        if args.case in ('negative','temperature_scope'):
            selected=ref['negative_cases'] if args.case=='negative' else [c for c in ref['negative_cases'] if c['case_id'] in ('TERMINAL_CROSSING','REVERSED_DUTY')]
            r['negative_cases']=[negative(c) for c in selected]
        if args.case=='phase':
            for c in ref['phase_studies']:
                try:evaluate(c['inputs'])
                except ValueError as error:
                    assert 'phase_service_scope' in str(error)
                    r['service_scope'].append(dict(case_id=c['case_id'],passed=True))
                else:raise AssertionError('Unexpected accepted phase study')
        for c in ref['cases']:
            if c['group']==args.case or args.case=='reciprocal' or (args.case in ('flow','temperature_scope') and c['case_id']=='CANONICAL'):
                out=evaluate(c['inputs']);checks=compare_case(c,out)
                row=dict(case_id=c['case_id'],group=c['group'],inputs=c['inputs'],production=out,comparisons=checks)
                if args.case=='reciprocal':row['reciprocal']=reciprocal(c,out);checks=checks+row['reciprocal']['comparisons']
                r['cases'].append(row);r['comparison_count']+=len(checks)
        if args.case=='flow':
            byid={c['case_id']:c for c in r['cases']};base=byid['CANONICAL'];d=base['production']['equipment'][0]['thermodynamics']
            for frozen in ref['flow_scaling']:
                row=byid[frozen['case_id']];q=frozen['quantity']+'_W';ratio=row['inputs']['hot']['F']/base['inputs']['hot']['F']
                error=abs(row['production']['equipment'][0]['thermodynamics'][q]-ratio*d[q]);assert error<=frozen['allowance_W']
                r['flow_scaling'].append(dict(case_id=row['case_id'],field=q,absolute_error=error,allowance=frozen['allowance_W']))
                r['comparison_count']+=1
    text=encode(r)
    if args.write:ARTIFACT.write_text(text)
    if args.verify:assert ARTIFACT.read_text()==text,'Production evidence differs'
    display(r,args.case)

if __name__=='__main__':main()
