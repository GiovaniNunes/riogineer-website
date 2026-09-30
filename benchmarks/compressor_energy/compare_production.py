"""M14 production equipment acceptance against immutable independent Pre-M14 truth."""
import argparse
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.components import component
from riogineer_engine.compressor_energy import MODEL, CompressorFailure
from riogineer_engine.core import build_flowsheet, calculate, loads
from riogineer_engine.network_models import MODELS, state_from_rates
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.pr_ps_flash import flash_ps
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.thermodynamics import MolarComposition, MolecularCompositionProvider

HERE=Path(__file__).resolve().parent
REFERENCE=HERE/'methane_nhexane_compressor_reference.json'
ARTIFACT=HERE/'production_comparison.json'
SHA='31972f6057f1c4191e25dc8fec317a0e21b20816d0a7c6513649fb7b630ed8cc'
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
    ids=i.get('component_ids',IDS)
    # Fixture conversion only; production converts actual mass flows with M7.
    # Unknown component uses a dummy fixture weight so equipment itself rejects identity.
    rates={name:i['flow']*3600./1000.*z*component(name if name in IDS else 'methane').molecular_weight for name,z in zip(ids,i['z'])}
    feed=state_from_rates(rates,i['T1'],i['P1'],None)
    if abs(sum(i['z'])-1)>1e-12:feed['mass_flow_kg_h']=sum(rates.values())/sum(i['z'])
    p=dict(outlet_pressure_Pa_abs=i['P2'],isentropic_efficiency=i['eta'],property_package='peng_robinson@1.0',
           bip=dict(identifier='m14_qualified_zero@1.0',component_ids=list(IDS),values=i.get('kij',[[0.,0.],[0.,0.]]),
                    source='Explicit qualified constant zero kij; not fitted',model='peng_robinson@1.0'))
    return dict(id='COMPRESSOR_1',type='compressor',model=dict(MODEL),operating_parameters=p),{'inlet':feed}


def requirements(i):
    unit,streams=inputs(i)
    feed={k:streams['inlet'][k] for k in ('temperature_K','pressure_Pa_abs','component_mass_flow_kg_h')}
    return dict(schema_version='1.6',kind='requirements',case_id='M14_REFERENCE',profile='compressor_energy',
        units=dict(temperature='K',pressure='Pa_abs',component_mass_flow='kg/h',heat_capacity='J/(kg K)',duty='W',recovery='mass_fraction'),
        provenance=dict(source='Frozen Pre-M14 production acceptance',basis='qualified_equilibrium_energy'),components=list(IDS),
        feeds=[dict(id='SOURCE',state=feed)],sinks=[dict(id='SINK')],
        equipment=[dict(id=unit['id'],type=unit['type'],model=unit['model'],parameters=unit['operating_parameters'])],
        streams=[dict(id='FEED',service='feed'),dict(id='PRODUCT',service='product')],
        connections=[dict(id='C1',stream_id='FEED',source=dict(owner_id='SOURCE',port_id='outlet'),target=dict(owner_id=unit['id'],port_id='inlet')),
                     dict(id='C2',stream_id='PRODUCT',source=dict(owner_id=unit['id'],port_id='outlet'),target=dict(owner_id='SINK',port_id='inlet'))],
        required_outputs=['streams','mass_balance','energy_balance'])


def evaluate(i):
    # Every positive traverses requirements -> validated flowsheet -> registry -> public result.
    return calculate(build_flowsheet(requirements(i)))


def compare_case(c,output):
    d=output['equipment'][0]['thermodynamics'];i=c['inputs'];r=c['result'];a=c['allowances'];checks=[]
    assert output['equipment'][0]['model']==MODEL and output['schema_version']=='1.8'
    def check(field,x,y,tol=0.):
        error=abs(x-y);row=dict(field=field,actual=x,reference=y,absolute_error=error,allowance=tol,passed=error<=tol)
        checks.append(row);assert row['passed'],(c['case_id'],row)
    def equal(field,x,y):assert x==y,(c['case_id'],field,x,y)
    check('eta_specified',d['isentropic_efficiency'],i['eta'])
    check('pressure_ratio',d['pressure_ratio'],i['P2']/i['P1'])
    check('molar_flow',d['F_mol_s'],i['flow'],64*sys.float_info.epsilon*max(1,i['flow']))
    for prod,ref in [('inlet','inlet'),('isentropic_outlet','isentropic'),('actual_outlet','outlet')]:
        p=d[prod];q=r[ref];tol=a[ref]
        equal(prod+'.phase',p['classification'],q['classification']);equal(prod+'.phases',p['phases'].keys(),q['phases'].keys())
        for field,x,y,limit in [('T',p['temperature_K'],q['T_K'],tol['T']),('P',p['pressure_Pa_abs'],q['P_Pa_abs'],0.),
            ('H',p['H_eq_J_mol'],q['H_eq_J_mol'],tol['H']),('S',p['S_eq_J_mol_K'],q['S_eq_J_mol_K'],tol['S']),('beta',p['beta'],q['beta'],tol['beta'])]:check(ref+'.'+field,x,y,limit)
        for j,k in enumerate(IDS):check(ref+'.z.'+k,p['z'][k],q['z'][j],2e-9)
        for phase,t in q['phases'].items():
            v=p['phases'][phase]
            for field,key in [('Z','Z'),('h_J_mol','H'),('s_J_mol_K','S')]:check(ref+'.'+phase+'.'+key,v[field],t[field],tol[phase+'.'+key])
            for j,k in enumerate(IDS):check(ref+'.'+phase+'.q'+str(j),v['composition'][k],t['composition'][j],tol[phase+'.q'+str(j)])
    for field,key,tol in [('H_out_target_J_mol','H2_target_J_mol',a['H2_target']),('fluid_power_W','fluid_power_W',a['fluid_power']),
        ('isentropic_fluid_power_W','isentropic_fluid_power_W',a['isentropic_power']),('reconstructed_efficiency','reconstructed_eta',a['eta']),
        ('eta_power','eta_power',a['eta']),('delta_H_is_J_mol','delta_H_is_J_mol',a['isentropic']['H']+a['inlet']['H']),
        ('delta_H_actual_J_mol','delta_H_actual_J_mol',a['outlet']['H']+a['inlet']['H']),
        ('delta_S_actual_J_mol_K','delta_S_actual_J_mol_K',a['outlet']['S']+a['inlet']['S'])]:check(field,d[field],r[key],tol)
    for inverse,cap,field,tol in [('ps','flash_PS','entropy_residual_J_mol_K',1e-8),('ph','flash_PH','enthalpy_residual_J_mol',1e-6)]:
        equal(inverse+'.status',d[inverse]['status'],'success');equal(inverse+'.capability',d[inverse]['capability'],cap)
        equal(inverse+'.pt_profile',d[inverse]['pt_profile'],'high_accuracy');equal(inverse+'.candidates',d[inverse]['candidate_count'],1)
        check(inverse+'.residual',d[inverse][field],0.,tol)
    check('eta_identity',d['reconstructed_efficiency'],i['eta'],next(x['allowance'] for x in c['checks'] if x['field']=='eta'))
    check('eta_power_identity',d['eta_power'],i['eta'],next(x['allowance'] for x in c['checks'] if x['field']=='eta_power'))
    check('energy_residual',d['energy_residual_W'],0.,next(x['allowance'] for x in c['checks'] if x['field']=='energy_residual'))
    check('power_identity',d['power_identity_residual_W'],0.,next(x['allowance'] for x in c['checks'] if x['field']=='power_identity'))
    equal('mass_inventory',output['streams']['FEED']['component_mass_flow_kg_h'],output['streams']['PRODUCT']['component_mass_flow_kg_h'])
    out=MolecularCompositionProvider().enrich(output['streams']['PRODUCT']).composition
    check('out_molar_flow',out.molar_flow_kmol_h*1000./3600.,i['flow'],64*sys.float_info.epsilon*max(1,i['flow']))
    for key,z in zip(IDS,i['z']):check('out_composition.'+key,out.molar_fractions[key],z,2e-9)
    check('mass_residual',output['balances']['mass']['total_residual_kg_h'],0.)
    equal('outlet_z',d['actual_outlet']['z'],d['inlet']['z'])
    return checks


def injection(name):
    if not name:return nullcontext()
    if name=='PT_INJECTED':return patch.object(PengRobinsonProvider,'equilibrium_caloric_PT',return_value=CaloricResult('controlled_pt_failure',None,message='Synthetic inlet failure'))
    if name in ('PS_INJECTED','PH_INJECTED'):
        return patch.object(PengRobinsonProvider,'flash_PS' if name.startswith('PS') else 'flash_PH',return_value=SimpleNamespace(status='controlled_solver_failure',caloric=None,diagnostics='Synthetic stage failure'))
    if name in ('PS_GAP','PH_GAP'):
        method='flash_PS' if name=='PS_GAP' else 'flash_PH';original=getattr(PengRobinsonProvider,method)
        def gap(self,s,bip,settings=None):
            if name=='PS_GAP':
                ref=json.loads((ROOT/'benchmarks/peng_robinson_ps/methane_nhexane_pr_ps_reference.json').read_text())
                target=next(c for c in ref['negative_cases'] if c['case_id']=='PURE_COEXISTENCE_GAP')['specification']['S_target']
                spec=replace(s,pressure_Pa_abs=1000.,entropy_J_mol_K=target,composition=MolarComposition(IDS,(0.,1.)))
            else:
                ref=json.loads((ROOT/'benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json').read_text())
                spec=replace(s,pressure_Pa_abs=1000.,enthalpy_J_mol=ref['pure_saturation_gap']['excluded_target_J_mol'],composition=MolarComposition(IDS,(0.,1.)))
            return original(self,spec,bip)
        return patch.object(PengRobinsonProvider,method,gap)
    if name in ('PS_AMBIGUOUS','PS_HOLE'):
        def synthetic(self,s,bip,settings=None):
            base=self.equilibrium_caloric_PT.__func__
            from riogineer_engine.thermodynamics import ThermodynamicState
            seed=base(self,ThermodynamicState(300.,s.pressure_Pa_abs,s.composition,s.provenance),bip,SolverSettings.high_accuracy())
            def evaluator(state,bip,settings):
                T=state.temperature_K
                if name=='PS_HOLE' and 290<T<310:return CaloricResult('controlled_property_hole',None,message='Synthetic hole')
                entropy=(T-270)*(T-430) if name=='PS_AMBIGUOUS' else T-300
                return replace(seed,aggregate=replace(seed.aggregate,s_J_mol_K=entropy))
            return flash_ps(replace(s,entropy_J_mol_K=0.),bip,evaluator)
        return patch.object(PengRobinsonProvider,'flash_PS',synthetic)
    raise AssertionError(name)


def negative(c):
    i=decode(c['inputs']);name=i.pop('synthetic',None);u,s=inputs(i)
    expected={'invalid_flow':('specification','invalid_flow'),'invalid_pressure':('specification','invalid_pressure'),
        'invalid_efficiency':('specification','invalid_efficiency'),'invalid_composition':('specification','invalid_composition'),
        'unsupported_components':('specification','unsupported_component'),'unsupported_bip':('specification','unsupported_bip'),
        'temperature_domain_invalid':('specification','temperature_domain_invalid'),
        'compressor_state_invalid':('inlet_PT','compressor_service_scope'),
        'pt_failure':('inlet_PT','controlled_pt_failure')} .get(c['expected_status'])
    if c['case_id'] in ('NEGATIVE_Z','NONFINITE_Z'):expected=('specification','invalid_flow')
    nested={'PS_UNBRACKETED':('isentropic_PS','entropy_target_not_bracketed'),'PH_UNBRACKETED':('actual_PH','enthalpy_target_not_bracketed'),
            'PS_INJECTED':('isentropic_PS','controlled_solver_failure'),'PH_INJECTED':('actual_PH','controlled_solver_failure'),
            'PS_GAP':('isentropic_PS','ps_nonconvergence'),'PH_GAP':('actual_PH','ph_nonconvergence'),
            'PS_AMBIGUOUS':('isentropic_PS','ambiguous_ps_root'),'PS_HOLE':('isentropic_PS','property_evaluation_failed')}
    expected=nested.get(c['case_id'],expected)
    with injection(name):
        try:MODELS['compressor']['execute'](u,s,None)
        except CompressorFailure as error:
            assert (error.stage,error.status)==expected,(c['case_id'],expected,error.stage,error.status)
            return dict(case_id=c['case_id'],independent_category=c['expected_status'],synthetic=bool(name),
                        mapping='Equivalent production nested injection' if name else 'Actual mass-stream equipment input',
                        stage=error.stage,status=error.status,accepted_outlet=False,passed=True)
    raise AssertionError((c['case_id'],'Unexpected accepted outlet'))


def stable_result(r):
    r=deepcopy(r);r.pop('run_id');return r


def build():
    ref=reference();rows=[];maxima={}
    for c in ref['cases']:
        r=evaluate(c['inputs']);checks=compare_case(c,r)
        for x in checks:
            if x['field'] not in maxima or x['absolute_error']>maxima[x['field']]['absolute_error']:maxima[x['field']]=dict(case_id=c['case_id'],**x)
        rows.append(dict(case_id=c['case_id'],group=c['group'],inputs=c['inputs'],production=stable_result(r),comparisons=checks,passed=True))
    negatives=[negative(c) for c in ref['negative_cases']]
    scope=[]
    for c in ref['thermodynamic_studies']:
        u,s=inputs(c['inputs'])
        try:MODELS['compressor']['execute'](u,s,None)
        except CompressorFailure as error:
            assert error.status=='compressor_service_scope'
            scope.append(dict(case_id=c['case_id'],status=error.status,accepted_outlet=False,independent_thermodynamics='calculable',passed=True))
        else:raise AssertionError('VL service accepted')
    byid={c['case_id']:c for c in rows};canonical=rows[0]['production']['equipment'][0]['thermodynamics'];scaling=[]
    for x in ref['flow_scaling']:
        row=byid[x['case_id']];d=row['production']['equipment'][0]['thermodynamics']
        # Each row already compares states to frozen field-specific allowances.
        # Establish that those independent states are exactly the same across flow;
        # do not impose byte equality on mass-to-molar floating-point projection.
        frozen=next(c for c in ref['cases'] if c['case_id']==x['case_id'])
        for key in ('inlet','isentropic','outlet','H2_target_J_mol'):
            assert frozen['result'][key]==ref['cases'][0]['result'][key]
        ratio=row['inputs']['flow']/rows[0]['inputs']['flow'];error=abs(d['fluid_power_W']-ratio*canonical['fluid_power_W'])
        assert error<=x['allowance_W'],(x,error)
        scaling.append(dict(case_id=x['case_id'],absolute_error_W=error,allowance_W=x['allowance_W'],passed=True))
    efficiency=sorted([rows[0]]+[x for x in rows if x['group']=='efficiency'],key=lambda x:x['inputs']['eta'])
    pressure=sorted([rows[0]]+[x for x in rows if x['group']=='pressure'],key=lambda x:x['inputs']['P2'])
    for series,sign in [(efficiency,-1),(pressure,1)]:
        for a,b in zip(series,series[1:]):
            da,db=[c['production']['equipment'][0]['thermodynamics'] for c in (a,b)]
            for key in ('fluid_power_W','delta_H_actual_J_mol'):assert sign*(db[key]-da[key])>0
            if sign==-1:assert da['isentropic_outlet']==db['isentropic_outlet']
            else:assert db['delta_H_is_J_mol']>da['delta_H_is_J_mol']
    order=[]
    old=loads((ROOT/'contracts/examples/milestone-6-requirements.json').read_text())
    for history in ['historical','positive','ideal','negative','PS_INJECTED','PH_INJECTED']:
        for c in [rows[0],byid['PURE_METHANE'],byid['BOUNDARY_VAPOR']]:
            if history=='historical':calculate(build_flowsheet(old))
            elif history in ('positive','ideal'):evaluate(byid['ETA_0.6' if history=='positive' else 'ETA_1.0']['inputs'])
            else:
                name='FLOW_0.0' if history=='negative' else history
                negative(next(c for c in ref['negative_cases'] if c['case_id']==name))
            r=stable_result(evaluate(c['inputs']));assert encode(r)==encode(c['production']),(history,c['case_id'])
            order.append(dict(after=history,case_id=c['case_id'],byte_identical=True))
    return dict(reference_sha256=SHA,reference_id=ref['reference_id'],model=MODEL,cases=rows,negative_cases=negatives,service_scope=scope,
                comparison_count=sum(len(c['comparisons']) for c in rows),maximum_errors=maxima,flow_scaling=scaling,call_order=order,passed=True)


def display(r,mode):
    if mode=='negative':
        for c in r['negative_cases']:print(c['case_id'],c['stage'],c['status'],'accepted outlet = no; PASS')
    elif mode=='service_scope':
        print('single_vapor: accepted (19 frozen cases)')
        for c in r['negative_cases']:
            if c['status']=='compressor_service_scope':print(c['case_id'],'rejected as compressor service; accepted outlet = no; PASS')
        print(encode(r['service_scope']))
    elif mode=='summary':
        for key,x in r['maximum_errors'].items():print(key,x['absolute_error'],'<=',x['allowance'],x['case_id'],'PASS')
        print('Flow scaling:',encode(r['flow_scaling']))
        print('Call order:',len(r['call_order']),'byte-identical checks')
    else:
        groups={'canonical':['canonical'],'efficiency':['canonical','efficiency'],'pressure':['canonical','pressure'],'flow':['canonical','flow'],
                'ideal':[],'pure':['pure'],'boundary':['boundary']}
        rows=[c for c in r['cases'] if c['inputs']['eta']==1] if mode=='ideal' else [c for c in r['cases'] if c['group'] in groups[mode]]
        if mode in ('efficiency','pressure','flow'):
            print('case | eta | P2/P1 | P2 Pa | flow mol/s | T2s K | H2s J/mol | T2 K | H2 J/mol | fluid power W | eta recovered')
        for c in rows:
            d=c['production']['equipment'][0]['thermodynamics']
            if mode in ('efficiency','pressure','flow'):
                print(c['case_id'],*[d[k] for k in ('isentropic_efficiency','pressure_ratio')],d['actual_outlet']['pressure_Pa_abs'],d['F_mol_s'],d['isentropic_outlet']['temperature_K'],d['isentropic_outlet']['H_eq_J_mol'],d['actual_outlet']['temperature_K'],d['actual_outlet']['H_eq_J_mol'],d['fluid_power_W'],d['reconstructed_efficiency'],'PASS',sep=' | ')
            else:
                print(c['case_id'],MODEL,'PASS')
                for key in ('inlet','isentropic_outlet','actual_outlet'):
                    s=d[key];print(key,{k:s[k] for k in ('temperature_K','pressure_Pa_abs','classification','beta','H_eq_J_mol','S_eq_J_mol_K')})
                for key in ('pressure_ratio','isentropic_efficiency','F_mol_s','H_out_target_J_mol','reconstructed_efficiency','eta_power','isentropic_fluid_power_W','fluid_power_W','energy_residual_W','ps','ph'):print(key,d[key])
        if mode=='flow':print('Scaling error:',encode(r['flow_scaling']))
    print('PASS:',len(r['cases']),'vapor positive;',len(r['negative_cases']),'negative;',len(r['service_scope']),'VL service rejection;',r['comparison_count'],'numerical comparisons; determinism/call order passed')
    print('Frozen SHA256:',SHA)


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group();g.add_argument('--write',action='store_true');g.add_argument('--verify',action='store_true')
    p.add_argument('--case',choices=['canonical','efficiency','pressure','flow','ideal','pure','boundary','service_scope','negative','summary'],default='summary')
    args=p.parse_args();r=build();data=encode(r)
    if args.write:ARTIFACT.write_text(data)
    if args.verify:assert ARTIFACT.read_text()==data,'Production artifact byte reproduction failed'
    display(r,args.case)


if __name__=='__main__':main()
