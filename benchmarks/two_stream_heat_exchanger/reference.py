"""Independent Pre-M15 truth. Default verifies; --write alone freezes new evidence."""
import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys

try:
    from .solver import ROOT, IDS, ZERO, EntropyPT, TrialFailure, solve_ph, calculate
except ImportError:
    from solver import ROOT, IDS, ZERO, EntropyPT, TrialFailure, solve_ph, calculate
from benchmarks.peng_robinson_caloric import reference as caloric

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE/'methane_nhexane_two_stream_hx_reference.json'
BASELINE = 'e17490f1b470645e9a042086d9330d52c90507de'
BASE = dict(hot=dict(F=100.,Tin=430.,Pin=3e5,Pout=3e5,z=[.9,.1]),
            cold=dict(F=200.,Tin=300.,Pin=1e5,Pout=1e5,z=[.9,.1]),T_hot_out=390.,kij=[list(r) for r in ZERO])
TOLS = dict(T=1e-7,H=1e-6,H_relative=1e-11,beta=2e-9,composition=2e-9,Z=2e-10,Z_relative=1e-9,PH_residual=1e-6)
MODES = ['canonical','reciprocal','pressure','flow','composition','pure','phase','zero_duty','temperature_scope','negative','summary']


def encode(x):
    return json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def patch(base=BASE, **changes):
    s=deepcopy(base)
    for key,value in changes.items():
        if key in ('hot','cold'):s[key].update(value)
        else:s[key]=value
    return s


def compact(r):
    r=deepcopy(r)
    ds=[r['PH']] if 'PH' in r else [r['PH_failure']['diagnostics']] if 'PH_failure' in r else []
    for d in ds:
        for key in ('scan','root_trials'):
            if key in d:
                rows=d.pop(key);d[key+'_count']=len(rows);d[key+'_sha256']=hashlib.sha256(encode(rows).encode()).hexdigest()
        d['candidate_count']=len(d.get('brackets',[]))
    return r


def positive_specs():
    rows=[('CANONICAL','canonical',patch()),
          ('HOT_PRESSURE_DROP','pressure',patch(hot=dict(Pout=2.7e5))),
          ('COLD_PRESSURE_DROP','pressure',patch(cold=dict(Pout=9e4))),
          ('BOTH_PRESSURE_DROP','pressure',patch(hot=dict(Pout=2.7e5),cold=dict(Pout=9e4))),
          ('FLOW_RATIO_1','flow',patch(cold=dict(F=100.))),
          ('FLOW_RATIO_2','flow',patch(cold=dict(F=50.))),
          ('DOUBLE_BOTH_FLOWS','flow',patch(hot=dict(F=200.),cold=dict(F=400.))),
          ('DOUBLE_HOT_FLOW','flow',patch(hot=dict(F=200.))),
          ('COLD_BALANCED','composition',patch(cold=dict(z=[.5,.5],Tin=350.,Pin=1e4,Pout=1e4),T_hot_out=410.)),
          ('COLD_HEXANE_RICH','composition',patch(cold=dict(z=[.3,.7],Tin=350.,Pin=1e4,Pout=1e4),T_hot_out=410.)),
          ('HOT_BALANCED','composition',patch(hot=dict(z=[.5,.5]))),
          ('HOT_HEXANE_RICH','composition',patch(hot=dict(z=[.3,.7]))),
          ('PURE_METHANE','pure',patch(hot=dict(z=[1.,0.]),cold=dict(z=[1.,0.]))),
          ('PURE_HEXANE','pure',patch(hot=dict(z=[0.,1.],Pin=1000.,Pout=1000.),cold=dict(z=[0.,1.],Pin=1000.,Pout=1000.))),
          ('LIQUID_BOTH','composition',patch(hot=dict(Tin=350.,Pin=3e7,Pout=3e7,z=[.5,.5]),cold=dict(Tin=250.,Pin=3e7,Pout=3e7,z=[.5,.5]),T_hot_out=320.)),
          ('ZERO_DUTY','zero_duty',patch(T_hot_out=430.)),
          ('ZERO_DUTY_COLD_DROP','zero_duty',patch(T_hot_out=430.,cold=dict(Pout=5e4)))]
    # A separately specified B case exercises the reverse B -> A reciprocal direction.
    b=patch(T_cold_out=320.);del b['T_hot_out'];rows.append(('COLD_SPECIFIED','reciprocal',b))
    # 0.25 K is a study location, never a proposed minimum approach requirement.
    pt=EntropyPT();s=patch();h=pt.evaluate(390.,3e5,[.9,.1])['H_eq_J_mol']-pt.evaluate(430.,3e5,[.9,.1])['H_eq_J_mol']
    rise=pt.evaluate(389.75,1e5,[.9,.1])['H_eq_J_mol']-pt.evaluate(300.,1e5,[.9,.1])['H_eq_J_mol']
    s['cold']['F']=-100*h/rise;rows.append(('NEAR_TERMINAL_EQUALITY','temperature_scope',s))
    return [dict(case_id=n,group=g,inputs=i) for n,g,i in rows]


def phase_specs():
    pt=EntropyPT();bubble=pt.flash.flash(P=6e6,VF=0.,zs=[.5,.5]).T;dew=pt.flash.flash(P=6e6,VF=1.,zs=[.5,.5]).T
    rows=[]
    def constructed(name,Th_in,Th_out,Ph,zh,Tc_in,Tc_out,Pc,zc,expected):
        s=patch(hot=dict(Tin=Th_in,Pin=Ph,Pout=Ph,z=zh),cold=dict(Tin=Tc_in,Pin=Pc,Pout=Pc,z=zc),T_hot_out=Th_out)
        dh=pt.evaluate(Th_out,Ph,zh)['H_eq_J_mol']-pt.evaluate(Th_in,Ph,zh)['H_eq_J_mol']
        dc=pt.evaluate(Tc_out,Pc,zc)['H_eq_J_mol']-pt.evaluate(Tc_in,Pc,zc)['H_eq_J_mol']
        s['hot']['F']=s['cold']['F']*dc/(-dh)
        rows.append(dict(case_id=name,group='phase',inputs=s,designed_cold_out_K=Tc_out,expected_phases=expected))
    constructed('COLD_L_TO_VL',480.,450.,1000.,[.9,.1],220.,300.,6e6,[.5,.5],['single_vapor','single_vapor','single_liquid','vapor_liquid'])
    constructed('HOT_V_TO_VL',480.,300.,6e6,[.5,.5],230.,270.,1000.,[.9,.1],['single_vapor','vapor_liquid','single_vapor','single_vapor'])
    constructed('COLD_VL_TO_V',495.,490.,1000.,[.9,.1],300.,480.,6e6,[.5,.5],['single_vapor','single_vapor','vapor_liquid','single_vapor'])
    constructed('HOT_VL_TO_L',300.,220.,6e6,[.5,.5],205.,210.,1000.,[1.,0.],['vapor_liquid','single_liquid','single_vapor','single_vapor'])
    constructed('BUBBLE_ADJACENT',480.,450.,1000.,[.9,.1],bubble-.05,bubble+.05,6e6,[.5,.5],['single_vapor','single_vapor','single_liquid','vapor_liquid'])
    constructed('DEW_ADJACENT',dew+.05,dew-.05,6e6,[.5,.5],250.,260.,1000.,[.9,.1],['single_vapor','vapor_liquid','single_vapor','single_vapor'])
    return rows,dict(P_Pa_abs=6e6,z=[.5,.5],bubble_K=bubble,dew_K=dew,offset_K=.05)


def fields(s):
    out=dict(T=s['T_K'],H=s['H_eq_J_mol'],beta=s['beta'])
    for name,p in s['phases'].items():
        out[name+'.Z']=p['Z'];out[name+'.H']=p['h_J_mol']
        for j,v in enumerate(p['composition']):out[name+'.q'+str(j)]=v
    return out


def allowances(spec,r,pt):
    slopes={};base={}
    for name,s in r['states'].items():
        pair=[pt.evaluate(s['T_K']+dt,s['P_Pa_abs'],s['z']) for dt in [-.001,.001]]
        assert all(x['classification']==s['classification'] for x in pair),(name,'conditioning crosses phase boundary')
        a,b=map(fields,pair);slopes[name]={k:(b[k]-a[k])/.002 for k in a}
        assert slopes[name]['H']>0,(name,'nonpositive local dH/dT')
        base[name]=TOLS['H']+TOLS['H_relative']*abs(s['H_eq_J_mol'])
    a=r['specified_side'];b=r['recovered_side'];ratio=spec[a]['F']/spec[b]['F']
    ht=base[b+'_in']+ratio*(base[a+'_out']+base[a+'_in'])
    dt=4*(ht+TOLS['PH_residual'])/slopes[b+'_out']['H']+TOLS['T']
    out={}
    for name,s in r['states'].items():
        out[name]={}
        for k,v in fields(s).items():
            kind=k.split('.')[-1]
            fixed=(TOLS['H']+TOLS['H_relative']*abs(v) if kind=='H' else TOLS['Z']+TOLS['Z_relative']*abs(v) if kind=='Z' else TOLS['composition'] if kind.startswith('q') else TOLS[k])
            out[name][k]=fixed+(abs(slopes[name][k])*dt if name==b+'_out' else 0.)
    duties={side:spec[side]['F']*(out[side+'_in']['H']+out[side+'_out']['H'])+r['arithmetic_allowance_W'] for side in ('hot','cold')}
    return dict(states=out,duty_W=duties,H_target_J_mol=ht,recovered_T_budget_K=dt,slopes=slopes,PH_residual_J_mol=1e-6,energy_W=r['energy_allowance_W'])


def qualify(row, service='primary'):
    spec=row['inputs'];pt=EntropyPT();r=calculate(spec,oracle=pt,service=service)
    assert r['status']=='success',(row['case_id'],r)
    if 'expected_phases' in row:
        assert [r['states'][k]['classification'] for k in ['hot_in','hot_out','cold_in','cold_out']]==row['expected_phases']
    a=allowances(spec,r,pt);checks=[]
    def check(field,x,y,tol):
        e=abs(x-y);assert math.isfinite(x) and math.isfinite(y) and e<=tol,(row['case_id'],field,e,tol)
        checks.append(dict(field=field,actual=x,reference=y,absolute_error=e,allowance=tol,passed=True))
    for name,s in r['states'].items():
        check(name+'.H_direct',s['H_eq_J_mol'],s['H_eq_direct_J_mol'],a['states'][name]['H'])
        for phase,p in s['phases'].items():check(name+'.'+phase+'.H_direct',p['h_J_mol'],p['direct_h_J_mol'],a['states'][name][phase+'.H'])
        side,end=name.split('_');check(name+'.P',s['P_Pa_abs'],spec[side]['Pin' if end=='in' else 'Pout'],0.)
        for j,z in enumerate(spec[side]['z']):check(name+'.z'+str(j),s['z'][j],z,0.)
    for side in ('hot','cold'):
        si,so=[r['states'][side+'_'+end] for end in ('in','out')];F=spec[side]['F']
        check('Q_'+side+'_direct',r['Q_'+side+'_W'],math.fsum([F*so['H_eq_direct_J_mol'],-F*si['H_eq_direct_J_mol']]),a['duty_W'][side])
        check(side+'.flow',r['material'][side]['F_out_mol_s'],F,0.)
    check('energy_residual',r['energy_residual_W'],0.,a['energy_W'])
    check('PH_residual',r['PH_residual_J_mol'],0.,1e-6)
    check('Q_exchanged',r['Q_exchanged_W'],-r['Q_hot_W'],a['energy_W'])
    recovered=r['recovered_side'];specified=r['specified_side'];target=math.fsum([r['states'][recovered+'_in']['H_eq_J_mol'],-r['Q_'+specified+'_W']/spec[recovered]['F']])
    check('target_reconstruction',r['H_target_J_mol'],target,r['arithmetic_allowance_W']/spec[recovered]['F'])
    refinement=[]
    for points,method,direct in [(256,'brentq',False),(512,'bisect',False),(128,'brentq',True)]:
        alt=solve_ph(spec[recovered]['Pout'],spec[recovered]['z'],r['H_target_J_mol'],bounds=(200.,500.),evaluator=pt.evaluate,grid_points=points,method=method,direct=direct)
        assert alt['status']=='success',(row['case_id'],points,alt)
        assert len(alt['diagnostics']['brackets'])==1 and alt['diagnostics']['final_evaluations']==1
        s=alt['solution'];original=r['states'][recovered+'_out'];assert s['classification']==original['classification']
        check('PH_residual',s['H_residual_J_mol'],0.,1e-6)
        for k,v in fields(s).items():check('refined.'+k,v,fields(original)[k],a['states'][recovered+'_out'][k])
        refinement.append(dict(grid_points=points,method=method,direct_caloric=direct,classification=s['classification'],T_K=s['T_K'],PH_residual_J_mol=s['H_residual_J_mol'],diagnostics=compact(dict(PH=alt['diagnostics']))['PH']))
    reciprocal=deepcopy(spec);reciprocal.pop('T_'+specified+'_out');reciprocal['T_'+recovered+'_out']=r['states'][recovered+'_out']['T_K']
    rr=calculate(reciprocal,service=service);assert rr['status']=='success',(row['case_id'],'reciprocal',rr)
    ar=allowances(reciprocal,rr,EntropyPT());rec_checks=[];rec_refinement=[]
    check('PH_residual',rr['PH_residual_J_mol'],0.,1e-6)
    check('energy_residual',rr['energy_residual_W'],0.,ar['energy_W'])
    for points,method in [(256,'brentq'),(512,'bisect')]:
        inverse=solve_ph(spec[specified]['Pout'],spec[specified]['z'],rr['H_target_J_mol'],bounds=(200.,500.),evaluator=pt.evaluate,grid_points=points,method=method)
        assert inverse['status']=='success',(row['case_id'],'reciprocal refinement',points,inverse)
        assert len(inverse['diagnostics']['brackets'])==1 and inverse['diagnostics']['final_evaluations']==1
        fresh=inverse['solution'];original=rr['states'][specified+'_out'];assert fresh['classification']==original['classification']
        check('PH_residual',fresh['H_residual_J_mol'],0.,1e-6)
        for k,v in fields(fresh).items():check('reciprocal_refined.'+k,v,fields(original)[k],ar['states'][specified+'_out'][k])
        rec_refinement.append(dict(grid_points=points,method=method,T_K=fresh['T_K'],classification=fresh['classification'],PH_residual_J_mol=fresh['H_residual_J_mol'],diagnostics=compact(dict(PH=inverse['diagnostics']))['PH']))
    for side in ('hot','cold'):
        for label,key in [('T','T_K'),('H','H_eq_J_mol')]:
            x=rr['states'][side+'_out'][key];y=r['states'][side+'_out'][key];tol=a['states'][side+'_out'][label]+ar['states'][side+'_out'][label]
            check('reciprocal.'+side+'.'+label,x,y,tol);rec_checks.append(checks[-1])
        check('reciprocal.Q_'+side,rr['Q_'+side+'_W'],r['Q_'+side+'_W'],a['duty_W'][side]+ar['duty_W'][side]);rec_checks.append(checks[-1])
    check('reciprocal.Q_exchanged',rr['Q_exchanged_W'],r['Q_exchanged_W'],sum(x['duty_W']['cold'] for x in [a,ar]));rec_checks.append(checks[-1])
    check('reciprocal.energy_residual',rr['energy_residual_W'],r['energy_residual_W'],a['energy_W']+ar['energy_W']);rec_checks.append(checks[-1])
    if service=='primary':assert r['Q_hot_W']<=a['energy_W'] and r['Q_cold_W']>=-a['energy_W']
    return dict(**row,result=compact(r),allowances=a,checks=checks,refinement=refinement,
                reciprocal=dict(inputs=reciprocal,result=compact(rr),checks=rec_checks,refinement=rec_refinement),accepted_primary_scope=service=='primary',passed=True)


def decode(x):
    if isinstance(x,str) and x in ('NaN','Infinity','-Infinity'):return float(x)
    if isinstance(x,list):return [decode(v) for v in x]
    if isinstance(x,dict):return {k:decode(v) for k,v in x.items()}
    return x


def negative_specs():
    rows=[]
    def add(name,s,status,stage,synthetic=None):rows.append(dict(case_id=name,inputs=s,expected_status=status,expected_stage=stage,synthetic=synthetic))
    for side in ('hot','cold'):
        for v in [0.,-1.,'NaN','Infinity','-Infinity']:add(side+'_FLOW_'+str(v),patch(**{side:dict(F=v)}),'invalid_flow',side+'_input')
        for field in ('Pin','Pout'):
            for v in [0.,-1.,'NaN','Infinity','-Infinity']:add(side+'_'+field+'_'+str(v),patch(**{side:{field:v}}),'invalid_pressure',side+'_input')
        add(side+'_PRESSURE_GAIN',patch(**{side:dict(Pout=BASE[side]['Pin']*2)}),'invalid_pressure',side+'_input')
        for v in [199.,501.,'NaN','Infinity']:add(side+'_TIN_'+str(v),patch(**{side:dict(Tin=v)}),'temperature_domain_invalid',side+'_input')
        for tag,z in [('SUM',[.4,.4]),('NEGATIVE',[-.1,1.1]),('NONFINITE',['NaN',.1])]:add(side+'_Z_'+tag,patch(**{side:dict(z=z)}),'invalid_composition',side+'_input')
        for c in ['water','unknown']:add(side+'_'+c.upper(),patch(**{side:dict(ids=['methane',c])}),'unsupported_component',side+'_input')
    for side in ('hot','cold'):
        for v in [199.,501.,'NaN','Infinity']:
            s=patch();s.pop('T_hot_out');s['T_'+side+'_out']=v;add(side+'_TOUT_'+str(v),s,'temperature_domain_invalid','specified_'+side+'_outlet_PT')
    add('NONZERO_KIJ',patch(kij=[[0.,.01],[.01,0.]]),'unsupported_bip','specification')
    s=patch();s.pop('T_hot_out');add('UNDER_SPECIFIED',s,'invalid_specification','specification')
    add('OVER_SPECIFIED',patch(T_cold_out=320.),'invalid_specification','specification')
    add('EQUAL_INLET_T',patch(hot=dict(Tin=300.)),'temperature_direction','service_scope')
    add('REVERSED_INLET_T',patch(hot=dict(Tin=290.)),'temperature_direction','service_scope')
    add('REVERSED_DUTY',patch(T_hot_out=440.),'heat_direction','service_scope')
    add('TERMINAL_CROSSING',patch(cold=dict(F=40.)),'terminal_temperature_crossing','service_scope')
    add('UNBRACKETED_COLD',patch(cold=dict(F=.01)),'enthalpy_target_not_bracketed','recovered_cold_outlet_PH')
    s=patch(hot=dict(F=.01),T_cold_out=400.);s.pop('T_hot_out');add('UNBRACKETED_HOT',s,'enthalpy_target_not_bracketed','recovered_hot_outlet_PH')
    for mode in ('A','B'):
        s=patch()
        if mode=='B':s.pop('T_hot_out');s['T_cold_out']=320.
        for stage in ['hot_inlet_PT','cold_inlet_PT','specified_'+('hot' if mode=='A' else 'cold')+'_outlet_PT']:
            add(mode+'_'+stage,s,'pt_evaluation_failure',stage,'PT:'+stage)
        recovered='cold' if mode=='A' else 'hot'
        add(mode+'_PH_INJECTED',s,'controlled_ph_failure','recovered_'+recovered+'_outlet_PH','PH')
    for tag,status in [('AMBIGUOUS','multiple_ph_roots'),('HOLE','pt_evaluation_failure'),('FRESH_FINAL','final_acceptance_failed')]:add(tag,patch(),status,'recovered_cold_outlet_PH',tag)
    pt=EntropyPT();sat=pt.flash.flash(P=1000.,VF=0.,zs=[0.,1.]).T
    pair=[pt.evaluate(sat+d,1000.,[0.,1.]) for d in [-1e-5,1e-5]];gap=sum(x['H_eq_J_mol'] for x in pair)/2
    s=patch(cold=dict(Tin=sat-2,Pin=1000.,Pout=1000.,z=[0.,1.]))
    dh=pt.evaluate(390.,3e5,[.9,.1])['H_eq_J_mol']-pt.evaluate(430.,3e5,[.9,.1])['H_eq_J_mol']
    s['hot']['F']=s['cold']['F']*(gap-pt.evaluate(sat-2,1000.,[0.,1.])['H_eq_J_mol'])/(-dh)
    add('PURE_COEXISTENCE_GAP',s,'ph_nonconvergence','recovered_cold_outlet_PH')
    return rows,dict(P_Pa_abs=1000.,z=[0.,1.],saturation_T_K=sat,one_sided_states=pair,excluded_target_J_mol=gap)


def run_negative(row,oracle=None):
    spec=decode(row['inputs']);name=row['synthetic'];pt=oracle or EntropyPT();kwargs=dict(oracle=pt)
    if name and name.startswith('PT:'):
        target=name[3:];index={'hot_inlet_PT':1,'cold_inlet_PT':2,'specified_hot_outlet_PT':3,'specified_cold_outlet_PT':3}[target]
        class Broken:
            count=0
            def evaluate(self,*args):
                self.count+=1
                if self.count==index:raise TrialFailure('pt','Controlled '+target+' failure')
                return pt.evaluate(*args)
        kwargs['oracle']=Broken()
    elif name=='PH':kwargs['ph_solver']=lambda *args,**kw:dict(status='controlled_ph_failure',message='Injected PH failure',diagnostics={})
    elif name in ('AMBIGUOUS','HOLE'):
        def inverse(P,z,H,**kw):
            def evaluate(T,P,z):
                if name=='HOLE' and 290<T<310:raise TrialFailure('pt','Controlled property hole')
                h=(T-270)*(T-430) if name=='AMBIGUOUS' else T-300
                return dict(T_K=T,H_eq_J_mol=h,classification='synthetic',beta=1.,phases={})
            return solve_ph(P,z,0.,evaluator=evaluate,bounds=(200.,500.))
        kwargs['ph_solver']=inverse
    elif name=='FRESH_FINAL':
        def corrupt(*args,**kw):
            r=solve_ph(*args,**kw);r['solution']['H_eq_J_mol']+=1.;return r
        kwargs['ph_solver']=corrupt
    r=calculate(spec,**kwargs)
    assert (r['status'],r.get('failure_stage'))==(row['expected_status'],row['expected_stage']),(row['case_id'],r)
    assert not r['accepted_complete_exchanger_result'] and 'states' not in r
    return dict(**row,result=compact(r),passed=True)


def build():
    cases=[qualify(s) for s in positive_specs()]
    specs,boundaries=phase_specs();studies=[qualify(s,'thermodynamic_only') for s in specs]
    for c in studies:
        rejected=calculate(c['inputs']);assert rejected['status']=='phase_service_scope',(c['case_id'],rejected)
        c['primary_service_result']=compact(rejected)
    ns,gap=negative_specs();negatives=[run_negative(s) for s in ns]
    gap['refinement']=[]
    for points in [128,256,512]:
        rejected=solve_ph(gap['P_Pa_abs'],gap['z'],gap['excluded_target_J_mol'],bounds=(200.,500.),grid_points=points,evaluator=EntropyPT().evaluate)
        assert rejected['status']=='ph_nonconvergence',('pure gap refinement',points,rejected)
        gap['refinement'].append(dict(grid_points=points,result=compact(dict(PH_failure=rejected))))
    byid={c['case_id']:c for c in cases};base=byid['CANONICAL'];scaling=[]
    for name in ['DOUBLE_BOTH_FLOWS','DOUBLE_HOT_FLOW']:
        c=byid[name];factor=c['inputs']['hot']['F']/base['inputs']['hot']['F']
        e=abs(c['result']['Q_hot_W']-factor*base['result']['Q_hot_W']);tol=c['result']['arithmetic_allowance_W']
        assert e<=tol
        if name=='DOUBLE_BOTH_FLOWS':
            assert c['result']['states']==base['result']['states']
            for quantity in ['Q_cold','Q_exchanged']:
                error=abs(c['result'][quantity+'_W']-factor*base['result'][quantity+'_W']);assert error<=tol
                scaling.append(dict(case_id=name,quantity=quantity,absolute_error_W=error,allowance_W=tol,passed=True))
        scaling.append(dict(case_id=name,quantity='Q_hot',absolute_error_W=e,allowance_W=tol,passed=True))
    for name in ['FLOW_RATIO_1','FLOW_RATIO_2']:
        c=byid[name];assert c['result']['Q_hot_W']==base['result']['Q_hot_W']
        scaling.append(dict(case_id=name,quantity='Q_hot',absolute_error_W=0.,allowance_W=c['result']['arithmetic_allowance_W'],passed=True))
    assert byid['FLOW_RATIO_2']['result']['states']['cold_out']['T_K']>byid['FLOW_RATIO_1']['result']['states']['cold_out']['T_K']>base['result']['states']['cold_out']['T_K']
    # Explicit pressure/composition isolation: unchanged side PT inputs are identical.
    for name,side in [('HOT_PRESSURE_DROP','cold'),('COLD_PRESSURE_DROP','hot'),('HOT_BALANCED','cold'),('HOT_HEXANE_RICH','cold')]:
        assert byid[name]['result']['states'][side+'_in']==base['result']['states'][side+'_in']
    for name in ['ZERO_DUTY','ZERO_DUTY_COLD_DROP']:
        r=byid[name]['result'];assert r['Q_hot_W']==0. and abs(r['Q_cold_W'])<=r['energy_allowance_W']
    assert abs(byid['ZERO_DUTY_COLD_DROP']['result']['states']['cold_out']['T_K']-300.)>1e-6
    cross=next(c for c in negatives if c['case_id']=='TERMINAL_CROSSING')
    raw=calculate(cross['inputs'],service='thermodynamic_only');assert raw['status']=='success'
    reversed_case=next(c for c in negatives if c['case_id']=='REVERSED_DUTY')
    opposite=calculate(reversed_case['inputs'],service='thermodynamic_only');assert opposite['status']=='success'
    temperature_scope=[dict(case_id=c['case_id'],inputs=c['inputs'],thermodynamic=compact(c['result']),recommended_equipment_status='accepted') for c in [base,byid['NEAR_TERMINAL_EQUALITY']]]
    for c,raw in [(cross,raw),(reversed_case,opposite)]:temperature_scope.append(dict(case_id=c['case_id'],inputs=c['inputs'],thermodynamic=compact(raw),recommended_equipment_status=c['result']['status']))
    order=[];oracle=EntropyPT()
    for history in ['clean','positive','phase','negative','PH_failure','reciprocal_first']:
        if history=='positive':calculate(byid['LIQUID_BOTH']['inputs'],oracle=oracle)
        elif history=='phase':calculate(studies[0]['inputs'],oracle=oracle,service='thermodynamic_only')
        elif history=='negative':run_negative(ns[0],oracle=oracle)
        elif history=='PH_failure':run_negative(next(n for n in ns if n['case_id']=='A_PH_INJECTED'),oracle=oracle)
        elif history=='reciprocal_first':calculate(base['reciprocal']['inputs'],oracle=oracle)
        got=compact(calculate(base['inputs'],oracle=oracle));assert encode(got)==encode(base['result']),history
        order.append(dict(after=history,case_id='CANONICAL',byte_identical=True))
        rev=compact(calculate(base['reciprocal']['inputs'],oracle=oracle));assert encode(rev)==encode(base['reciprocal']['result'])
        order.append(dict(after=history,case_id='CANONICAL_RECIPROCAL',byte_identical=True))
    maxima={}
    for c in cases+studies:
        for x in c['checks']:
            if x['field'] not in maxima or x['absolute_error']>maxima[x['field']]['absolute_error']:maxima[x['field']]=dict(case_id=c['case_id'],**x)
    sources=['benchmarks/two_stream_heat_exchanger/solver.py','benchmarks/two_stream_heat_exchanger/reference.py',
             'benchmarks/peng_robinson_ph/solver.py','benchmarks/peng_robinson_ph/equilibrium.py','benchmarks/peng_robinson_ps/equilibrium.py',
             'benchmarks/peng_robinson_caloric/reference.py','benchmarks/peng_robinson_caloric/equations.py']
    return dict(reference_id='independent_two_stream_heat_exchanger@1.0',metadata=dict(baseline=BASELINE,
        packages={k:importlib.metadata.version(k) for k in ['thermo','chemicals','fluids','numpy','scipy']},
        components=caloric.COMPONENTS,Cp_data=caloric.CP_DATA,component_order=IDS,EOS='Peng-Robinson 0.45724 / 0.07780; classical quadratic mixing',
        kij=ZERO,reference='Ideal-gas sensible H=0 at 298.15 K; S reference 298.15 K, 101325 Pa, ideal mixing',
        units=dict(T='K',P='Pa absolute',H='J/mol',F='mol/s',Q='W'),temperature_domain_K=[200.,500.],
        controls=dict(scan_points=128,refined_scan_points=[256,512],root='SciPy brentq; bisect cross-check',xtol_K=1e-10,rtol=1e-14,maxiter=100,PT_SS_TOL=1e-26,fresh_PH_residual_J_mol=1e-6),
        source_sha256={p:sha(ROOT/p) for p in sources}),
        tolerances=dict(base=TOLS,combined='atol + rtol*abs(reference); recovered fields add local slope times propagated target-H temperature budget',
            recovered_temperature='1e-7 + 4*(target_H_allowance + 1e-6)/local_dH_dT',
            energy='F_recovered*1e-6 + 64*epsilon*max(1, abs(Qh),abs(Qc),abs(Fside*Hstate))',
            duty='Fside*(Hin_allowance+Hout_allowance)+roundoff',reciprocal='sum of original and reciprocal field/duty allowances'),
        recommended_scope='A: single-phase inlet and outlet only; frozen matrix, no terminal crossing',recommended_modes=['A','B'],
        terminal_rule='Thi > Tco and Tho > Tci and Tho >= Tco; no qualified design minimum approach',
        cases=cases,phase_studies=studies,boundary_evidence=boundaries,pure_gap=gap,negative_cases=negatives,
        temperature_scope=temperature_scope,flow_scaling=scaling,call_order=order,maximum_errors=maxima,
        comparison_count=sum(len(c['checks']) for c in cases+studies)+len(scaling),passed=True)


def display(r,mode):
    if mode=='negative':
        for c in r['negative_cases']:print(c['case_id'],c['result']['failure_stage'],c['result']['status'],'accepted exchanger result = no; PASS')
    elif mode=='summary':
        for k,x in r['maximum_errors'].items():print(k,x['absolute_error'],'<=',x['allowance'],x['case_id'],'PASS')
        print('Flow scaling:',r['flow_scaling'])
        print('Call order:',len(r['call_order']),'byte-identical checks')
    elif mode=='reciprocal':
        print('case | original -> reciprocal | hot dT | cold dT | hot dH | cold dH | hot dQ | cold dQ | allowances')
        for c in r['cases']:
            checks=c['reciprocal']['checks'];print(c['case_id'],c['result']['specification_mode']+' -> '+c['reciprocal']['result']['specification_mode'],[(x['field'],x['absolute_error'],x['allowance']) for x in checks],'PASS',sep=' | ')
    elif mode=='temperature_scope':
        for c in r['temperature_scope']:
            d=c['thermodynamic'];print(c['case_id'],c['inputs'],{k:s['T_K'] for k,s in d['states'].items()},'thermodynamics:',d['status'],'recommended equipment:',c['recommended_equipment_status'],'PASS')
        print('Terminal balance is not design feasibility; no qualified minimum approach, UA, LMTD or pinch model.')
    else:
        rows=r['phase_studies'] if mode=='phase' else [c for c in r['cases'] if c['group']==mode or (mode in ['pressure','flow'] and c['group']=='canonical')]
        for c in rows:
            d=c['result'];print(c['case_id'],d['specification_mode'],'primary scope' if c['accepted_primary_scope'] else 'separate thermodynamic study; primary scope rejected')
            for side in ('hot','cold'):
                i=c['inputs'][side];a,b=[d['states'][side+'_'+end] for end in ['in','out']]
                print(side,'F',i['F'],'z',i['z'],'Pin/Pout',i['Pin'],i['Pout'],'Tin/Tout',a['T_K'],b['T_K'],'Hin/Hout',a['H_eq_J_mol'],b['H_eq_J_mol'],'phases',a['classification'],b['classification'],'beta',a['beta'],b['beta'])
            print('Q_hot',d['Q_hot_W'],'Q_cold',d['Q_cold_W'],'Q_exchanged',d['Q_exchanged_W'],'energy residual',d['energy_residual_W'],'PH residual',d['PH_residual_J_mol'],'PASS')
            if mode in ['canonical','phase']:print('PH diagnostics',d['PH'])
        if mode=='flow':print('Scaling checks',r['flow_scaling'])
    print('PASS:',len(r['cases']),'primary positives;',len(r['phase_studies']),'separate phase studies;',len(r['negative_cases']),'negative;',r['comparison_count'],'numerical comparisons;',len(r['call_order']),'byte-identical call-order checks')
    print('Production M15: NOT IMPLEMENTED; human-operated Pre-M15 validation: PENDING')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');p.add_argument('--case',choices=MODES,default='summary')
    p.add_argument('--review',action='store_true',help='Read frozen evidence for concise human review; default freshly reproduces it')
    args=p.parse_args()
    if args.write and args.review:p.error('--review does not write evidence')
    if args.review:
        r=json.loads(ARTIFACT.read_text())
        for path,h in r['metadata']['source_sha256'].items():assert sha(ROOT/path)==h,'Source changed; reproduce before review'
    else:
        r=build();serialized=encode(r)
        if args.write:ARTIFACT.write_text(serialized)
        else:assert ARTIFACT.read_text()==serialized,'Frozen byte reproduction failed; default never rewrites'
    display(r,args.case);print('Frozen SHA256:',sha(ARTIFACT))


if __name__=='__main__':main()
