"""Independent Pre-M16 evidence. Default verifies; only --write replaces truth."""
import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform

try:
    from .solver import ROOT, IDS, ZERO, EntropyPT, TrialFailure, solve_ph, calculate
except ImportError:
    from solver import ROOT, IDS, ZERO, EntropyPT, TrialFailure, solve_ph, calculate
from benchmarks.peng_robinson_caloric import reference as caloric

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE/'methane_nhexane_throttling_valve_reference.json'
BASELINE = '6d18908ad5ed55e589af735be271a0f6b26663d1'
BASE = dict(Pin=3e7, Tin=300., Pout=1e6, F=100., z=[.5,.5])
MODES = ['canonical','pressure','flow','composition','phase','pure','negative','summary']
TOLS = dict(T=1e-7,H=1e-6,H_relative=1e-11,S=1e-8,S_relative=1e-11,
            beta=2e-9,composition=2e-9,Z=2e-10,Z_relative=1e-9,PH_residual=1e-6)


def encode(x):
    return json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec(**kw):
    return dict(deepcopy(BASE), **{}) | kw


def compact(r):
    r=deepcopy(r)
    ds=[r['PH']] if 'PH' in r else [r['PH_failure']['diagnostics']] if 'PH_failure' in r else []
    for d in ds:
        for key in ('scan','root_trials'):
            if key in d:
                rows=d.pop(key)
                d[key+'_count']=len(rows)
                d[key+'_sha256']=hashlib.sha256(encode(rows).encode()).hexdigest()
        d['candidate_count']=len(d.get('brackets',[]))
    return r


def positive_specs():
    rows=[('CANONICAL','canonical',spec())]
    for name,p in [('MILD',2.99e7),('MODERATE',2e7),('FLASH_ONSET',1e7),('INTERMEDIATE',6e6),('SUBSTANTIAL',3e6)]:
        rows.append(('PRESSURE_'+name,'pressure',spec(Pout=p, **({'qualified_interval':[280.,350.]} if name=='FLASH_ONSET' else {}))))
    rows += [('DOUBLE_FLOW','flow',spec(F=200.)),('LOW_FLOW','flow',spec(F=5.)),
             ('VAPOR_SIMPLE','phase',spec(Pin=6e6,Tin=400.,Pout=1e6,z=[.9,.1])),
             ('LIQUID_HEATING','phase',spec(Tin=350.,Pout=2e7)),
             ('NEGLIGIBLE_DROP','pressure',spec(Pout=3e7-10.)),
             ('METHANE_RICH','composition',spec(Pin=6e6,Tin=400.,z=[.9,.1])),
             ('HEXANE_RICH','composition',spec(Pin=6e6,Pout=1e5,z=[.1,.9])),
             ('BALANCED_COLD','composition',spec(Tin=250.)),
             ('INLET_PRESSURE','pressure',spec(Pin=2e7)),
             ('PURE_METHANE','pure',spec(Pin=6e6,Pout=1e5,z=[1.,0.])),
             ('PURE_HEXANE_VAPOR','pure',spec(Pin=3e5,Tin=450.,Pout=1e5,z=[0.,1.])),
             ('PURE_HEXANE_LIQUID','pure',spec(Pin=1e6,Pout=9e5,z=[0.,1.]))]
    # METHANE_RICH and VAPOR_SIMPLE would duplicate; retain one engineering case.
    rows=[r for r in rows if r[0]!='METHANE_RICH']
    return [dict(case_id=n,group=g,inputs=i) for n,g,i in rows]


def study_specs():
    rows=[dict(case_id='TWO_PHASE_INLET',group='phase',inputs=spec(Pin=6e6),reason='Separate inlet-service study; initial single-phase inlet recommendation')]
    pt=EntropyPT()
    boundaries={}
    for name,beta in [('BUBBLE',0.),('DEW',1.)]:
        T=pt.flash.flash(P=6e6,VF=beta,zs=[.5,.5]).T
        boundaries[name]=T
        for sign in [-1,1]:
            target=pt.evaluate(T+sign*.05,6e6,[.5,.5])['H_eq_J_mol']
            inv=solve_ph(7e6,[.5,.5],target,evaluator=pt.evaluate)
            assert inv['status']=='success',(name,inv)
            rows.append(dict(case_id=name+('_BELOW' if sign<0 else '_ABOVE'),group='phase',
                inputs=spec(Pin=7e6,Tin=inv['solution']['T_K'],Pout=6e6),
                designed_outlet_T_K=T+sign*.05,reason='Separate boundary perturbation study, not primary service'))
    return rows,dict(Pout_Pa_abs=6e6,z=[.5,.5],offset_K=.05,temperatures_K=boundaries)


def fields(s):
    out=dict(T=s['T_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
    for j,v in enumerate(s['z']):out['z'+str(j)]=v
    for name,p in s['phases'].items():
        for label,key in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:out[name+'.'+label]=p[key]
        for j,v in enumerate(p['composition']):out[name+'.q'+str(j)]=v
    return out


def fixed(k,v):
    k=k.split('.')[-1]
    if k in ('H','S','Z'):return TOLS[k]+TOLS[k+'_relative']*abs(v)
    if k.startswith(('q','z')):return TOLS['composition']
    return TOLS[k]


def allowances(r,pt):
    s=r['outlet'];pair=[pt.evaluate(s['T_K']+d,s['P_Pa_abs'],s['z']) for d in [-.001,.001]]
    assert all(a['classification']==s['classification'] for a in pair),'Conditioning crosses boundary'
    a,b=map(fields,pair);slopes={k:(b[k]-a[k])/.002 for k in a}
    assert slopes['H']>0
    target=fixed('H',r['inlet']['H_eq_J_mol'])
    dt=TOLS['T']+4*(target+TOLS['PH_residual'])/slopes['H']
    return dict(inlet={k:fixed(k,v) for k,v in fields(r['inlet']).items()},
                outlet={k:fixed(k,v)+abs(slopes[k])*dt for k,v in fields(s).items()},
                outlet_slopes=slopes,temperature_budget_K=dt,target_H=target,
                PH_residual=1e-6,energy_W=r['energy_allowance_W'])


def qualify(row,study=False):
    pt=EntropyPT();s=row['inputs'];r=calculate(**s,oracle=pt,service='thermodynamic_study' if study else 'single_phase_inlet')
    assert r['status']=='success',(row['case_id'],r)
    assert r['delta_S_J_mol_K']>=-1e-8,('Investigate negative entropy',row['case_id'],r['delta_S_J_mol_K'])
    a=allowances(r,pt);checks=[]
    def check(k,x,y,t):
        e=abs(x-y);assert math.isfinite(e) and e<=t,(row['case_id'],k,e,t)
        checks.append(dict(field=k,actual=x,reference=y,absolute_error=e,allowance=t,passed=True))
    for end in ('inlet','outlet'):
        state=r[end];w={'liquid':1-state['beta'],'vapor':state['beta']}
        check(end+'.H',state['H_eq_J_mol'],state['H_eq_direct_J_mol'],a[end]['H'])
        check(end+'.S',state['S_eq_J_mol_K'],state['S_eq_direct_J_mol_K'],a[end]['S'])
        check(end+'.P',state['P_Pa_abs'],s['Pin' if end=='inlet' else 'Pout'],0.)
        for j,z in enumerate(s['z']):
            check(end+'.z'+str(j),state['z'][j],z,0.)
            check(end+'.reconstruction'+str(j),math.fsum(w[k]*p['composition'][j] for k,p in state['phases'].items()),z,1e-10)
        check(end+'.phase_H_reconstruction',math.fsum(w[k]*p['h_J_mol'] for k,p in state['phases'].items()),state['H_eq_J_mol'],1e-6)
        for name,p in state['phases'].items():
            check(end+'.'+name+'.sum',sum(p['composition']),1.,1e-10)
            check(end+'.'+name+'.H',p['h_J_mol'],p['direct_h_J_mol'],a[end][name+'.H'])
            check(end+'.'+name+'.S',p['s_J_mol_K'],p['direct_s_J_mol_K'],a[end][name+'.S'])
    check('enthalpy_residual',r['enthalpy_residual_J_mol'],0.,1e-6)
    check('PH_residual',r['PH_residual_J_mol'],0.,1e-6)
    check('energy_residual',r['energy_residual_W'],0.,a['energy_W'])
    check('flow',r['F_out_mol_s'],s['F'],0.)
    for j,v in enumerate(r['component_residual_mol_s']):check('component_material'+str(j),v,0.,0.)
    refinements=[]
    for points,method,direct in [(256,'brentq',False),(512,'bisect',False),(128,'brentq',True)]:
        alt=solve_ph(s['Pout'],s['z'],r['H_out_target_J_mol'],bounds=tuple(s.get('qualified_interval',(200.,500.))),evaluator=pt.evaluate,grid_points=points,method=method,direct=direct)
        assert alt['status']=='success',(row['case_id'],points,alt)
        assert len(alt['diagnostics']['brackets'])==1 and alt['diagnostics']['final_evaluations']==1
        assert alt['solution']['classification']==r['outlet']['classification']
        for k,v in fields(alt['solution']).items():check('refined.'+k,v,fields(r['outlet'])[k],a['outlet'][k])
        check('PH_residual',alt['solution']['H_residual_J_mol'],0.,1e-6)
        refinements.append(dict(grid_points=points,method=method,direct=direct,T_K=alt['solution']['T_K'],PH=compact(dict(PH=alt['diagnostics']))['PH']))
    if 'designed_outlet_T_K' in row:check('boundary_T',r['outlet']['T_K'],row['designed_outlet_T_K'],a['outlet']['T'])
    return dict(**row,result=compact(r),allowances=a,checks=checks,refinements=refinements,accepted_primary_scope=not study,passed=True)


def decode(x):
    if isinstance(x,str) and x in ('NaN','Infinity','-Infinity'):return float(x)
    if isinstance(x,list):return [decode(v) for v in x]
    if isinstance(x,dict):return {k:decode(v) for k,v in x.items()}
    return x


def negative_specs():
    rows=[]
    def add(n,s,status,stage='specification',injection=None):
        rows.append(dict(case_id=n,inputs=s,expected_status=status,expected_stage=stage,injection=injection))
    for field in ('F','Pin','Pout'):
        for v in [0.,-1.,'NaN','Infinity','-Infinity']:
            add(field+'_'+str(v),spec(**{field:v}),'invalid_flow' if field=='F' else 'invalid_pressure')
    for n,p in [('EQUAL_PRESSURE',3e7),('PRESSURE_GAIN',4e7)]:add(n,spec(Pout=p),'invalid_pressure')
    for v in [199.,501.,'NaN','Infinity','-Infinity']:add('TIN_'+str(v),spec(Tin=v),'temperature_domain_invalid')
    for n,z in [('SUM',[.4,.4]),('NEGATIVE',[-.1,1.1]),('NAN',['NaN',.5]),('INF',['Infinity',.5]),('LENGTH',[1.])]:add('Z_'+n,spec(z=z),'invalid_composition')
    for c in ['water','unknown']:add(c.upper(),spec(ids=['methane',c]),'unsupported_component')
    add('NONZERO_KIJ',spec(kij=[[0.,.01],[.01,0.]]),'unsupported_bip')
    add('VL_INLET_SERVICE',spec(Pin=6e6),'inlet_service_scope','service_scope')
    for n,status,stage in [('PT','pt_evaluation_failure','inlet_PT'),('PH','controlled_ph_failure','outlet_PH'),
        ('UNBRACKETED','enthalpy_target_not_bracketed','outlet_PH'),('AMBIGUOUS','multiple_ph_roots','outlet_PH'),
        ('HOLE','pt_evaluation_failure','outlet_PH'),('FRESH_FINAL','final_acceptance_failed','final_acceptance')]:
        add(n,spec(),status,stage,n)
    add('PURE_COEXISTENCE_GAP',spec(Pin=1e7,Tin=350.,Pout=1000.,z=[0.,1.]),'ph_nonconvergence','outlet_PH')
    return rows


def run_negative(row,oracle=None):
    pt=oracle or EntropyPT();args=dict(oracle=pt);n=row['injection']
    if n=='PT':
        class Broken:
            def evaluate(self,*args):raise TrialFailure('pt','Controlled inlet PT failure')
        args['oracle']=Broken()
    elif n=='PH':args['ph_solver']=lambda *a,**k:dict(status='controlled_ph_failure',message='Controlled PH failure',diagnostics={})
    elif n in ('AMBIGUOUS','HOLE','UNBRACKETED'):
        def inverse(P,z,H,**kw):
            def evaluate(T,P,z):
                if n=='HOLE' and 290<T<310:raise TrialFailure('pt','Controlled property hole')
                h=(T-270)*(T-430) if n=='AMBIGUOUS' else T+1e6 if n=='UNBRACKETED' else T-300
                return dict(T_K=T,H_eq_J_mol=h,classification='synthetic',beta=1.,phases={})
            return solve_ph(P,z,0.,evaluator=evaluate,bounds=(200.,500.))
        args['ph_solver']=inverse
    elif n=='FRESH_FINAL':
        class CorruptFinal:
            corrupt=False
            def evaluate(self,*a):
                s=pt.evaluate(*a)
                if self.corrupt:s['H_eq_J_mol']+=1.
                return s
        wrapped=CorruptFinal();args['oracle']=wrapped
        def inverse(*a,**kw):
            r=solve_ph(*a,**kw);wrapped.corrupt=True;return r
        args['ph_solver']=inverse
    r=calculate(**decode(row['inputs']),**args)
    assert (r['status'],r.get('failure_stage'))==(row['expected_status'],row['expected_stage']),(row['case_id'],r)
    assert not r['accepted_outlet'] and 'outlet' not in r
    return dict(**row,result=compact(r),passed=True)


def investigate_hole():
    """Reproduce unavailable states; never substitute these diagnostics into PH."""
    center=461.1764705882353
    def evaluate(T):
        try:return dict(status='success',state=EntropyPT().evaluate(T,1e7,[.5,.5]))
        except TrialFailure as e:return dict(status=e.stage+'_evaluation_failure',message=str(e),T_K=T)
    grids=[('offsets',[center+x*s for x in [0,.0001,.001,.01,.02,.05,.1,.2,.5,1,2,5,10] for s in ([-1,1] if x else [1])]),
           ('step_0.1',[center-2+.1*i for i in range(41)]),
           ('step_0.02',[center-1+.02*i for i in range(101)]),
           ('step_0.005',[center-.25+.005*i for i in range(101)])]
    scans=[dict(label=n,rows=[evaluate(t) for t in grid]) for n,grid in grids]
    pt=EntropyPT();alternate=[]
    for offset in [-2.,-1.,-.5,.5,1.,2.]:
        try:
            seed=pt.flash.flash(T=center+offset,P=1e7,zs=[.5,.5])
            result=pt.flash.flash(T=center,P=1e7,zs=[.5,.5],hot_start=seed)
            alternate.append(dict(seed_T_K=center+offset,status='success',phase=result.phase,beta=result.VF,H=result.H(),S=result.S()))
        except Exception as e:alternate.append(dict(seed_T_K=center+offset,status=type(e).__name__,message=str(e)))
    connected=[];H=pt.evaluate(300.,3e7,[.5,.5])['H_eq_J_mol']
    for points,method in [(128,'brentq'),(256,'brentq'),(512,'bisect'),(1024,'brentq')]:
        r=solve_ph(1e7,[.5,.5],H,bounds=(280.,350.),grid_points=points,method=method,evaluator=pt.evaluate)
        assert r['status']=='success' and len(r['diagnostics']['brackets'])==1
        assert all(x['status']=='success' and x['classification']=='vapor_liquid' for x in r['diagnostics']['scan'])
        assert r['diagnostics']['monotonicity']=='increasing'
        connected.append(dict(points=points,method=method,result=compact(dict(PH=r['diagnostics'])),state=r['solution']))
    return dict(classification='B: finite numerical property hole near loss of distinguishable phases; not an exact qualified boundary',
                outcome='A: root qualified only on explicit connected 280–350 K interval; failed region remains unavailable',
                center_K=center,P_Pa_abs=1e7,z=[.5,.5],kij=ZERO,scans=scans,alternate_initializations=alternate,connected_interval=connected,
                limitations='Finite scans establish sampled robustness, not mathematical global uniqueness; no claim for excluded 350–500 K region')


def build():
    cases=[qualify(row) for row in positive_specs()]
    specs,boundaries=study_specs();studies=[qualify(row,True) for row in specs]
    negatives=[run_negative(row) for row in negative_specs()]
    base=cases[0];scaling=[]
    for c in cases:
        if c['group']!='flow':continue
        r=c['result'];factor=c['inputs']['F']/base['inputs']['F']
        assert encode(r['outlet'])==encode(base['result']['outlet'])
        assert encode(r['inlet'])==encode(base['result']['inlet'])
        error=abs(r['energy_residual_W']-factor*base['result']['energy_residual_W']);assert error==0.
        scaling.append(dict(case_id=c['case_id'],intensive_byte_identical=True,energy_scaling_error_W=error,allowance_W=0.,passed=True))
    order=[];pt=EntropyPT();allrows=cases+studies
    for c in [base,next(c for c in cases if c['case_id']=='VAPOR_SIMPLE'),next(c for c in cases if c['case_id']=='PURE_HEXANE_LIQUID'),studies[0]]:
        for history in [cases[-3],studies[-1],None]:
            if history is None:run_negative(next(n for n in negative_specs() if n['case_id']=='PH'),pt)
            else:calculate(**history['inputs'],oracle=pt,service='thermodynamic_study')
            actual=compact(calculate(**c['inputs'],oracle=pt,service='thermodynamic_study' if not c['accepted_primary_scope'] else 'single_phase_inlet'))
            assert encode(actual)==encode(c['result']),(c['case_id'],'call order')
            order.append(dict(case_id=c['case_id'],after=history['case_id'] if history else 'PH_FAILURE',byte_identical=True))
    maxima={}
    for c in allrows:
        for x in c['checks']:
            if x['field'] not in maxima or x['absolute_error']>maxima[x['field']]['absolute_error']:maxima[x['field']]=dict(case_id=c['case_id'],**x)
    sources=['benchmarks/throttling_valve/'+n for n in ['solver.py','reference.py']]+[
        'benchmarks/peng_robinson_ph/solver.py','benchmarks/peng_robinson_ph/equilibrium.py',
        'benchmarks/peng_robinson_ps/equilibrium.py','benchmarks/peng_robinson_caloric/reference.py','benchmarks/peng_robinson_caloric/equations.py']
    return dict(reference_id='independent_throttling_valve@1.0',metadata=dict(baseline=BASELINE,python=platform.python_version(),
        packages={k:importlib.metadata.version(k) for k in ['thermo','chemicals','fluids','numpy','scipy']},components=caloric.COMPONENTS,
        Cp_data=caloric.CP_DATA,component_order=IDS,EOS='Peng-Robinson 0.45724 / 0.07780; classical quadratic mixing',kij=ZERO,
        caloric_reference='Ideal-gas sensible H=0 at 298.15 K; S reference 298.15 K, 101325 Pa, ideal mixing',
        units=dict(T='K',P='Pa absolute',H='J/mol',S='J/(mol K)',F='mol/s',energy_residual='W'),temperature_domain_K=[200.,500.],
        equation='H_out = H_in; Q=0; Wshaft=0; delta_KE=delta_PE=0; one overall material stream',
        pressure_ratio='Pout/Pin < 1',controls=dict(scan_points=128,refined_scan_points=[256,512],root='SciPy brentq; bisect cross-check',
        xtol_K=1e-10,rtol=1e-14,maxiter=100,PT_SS_TOL=1e-26,fresh_PH_residual_J_mol=1e-6),source_sha256={p:sha(ROOT/p) for p in sources}),
        tolerances=dict(base=TOLS,derivation='Inherited M10/M11/M13/Pre-M15 allowances; outlet adds absolute local slope times 1e-7 + 4*(inlet H allowance + PH residual allowance)/dH_dT; no fit to observed errors'),
        recommended_scope='Single-phase methane/n_hexane inlet; liquid/vapor/VL outlet within frozen matrix. Two-phase inlet and boundary perturbations remain separate studies.',
        property_hole_investigation=investigate_hole(),cases=cases,separate_studies=studies,boundaries=boundaries,negative_cases=negatives,flow_scaling=scaling,call_order=order,
        maximum_errors=maxima,comparison_count=sum(len(c['checks']) for c in allrows)+len(scaling),passed=True)


def display(data,mode):
    if mode=='negative':
        for c in data['negative_cases']:print(c['case_id'],c['result']['failure_stage'],c['result']['status'],'accepted_outlet=False PASS')
    elif mode=='summary':
        for k,x in data['maximum_errors'].items():print(k,x['absolute_error'],'<=',x['allowance'],x['case_id'],'PASS')
        print('Flow invariance/scaling:',data['flow_scaling'])
    else:
        rows=data['cases']+data['separate_studies']
        if mode=='canonical':rows=rows[:1]
        elif mode=='phase':pass
        elif mode=='pressure':rows=[r for r in rows if r['group'] in ('canonical','pressure')]
        elif mode=='flow':rows=[r for r in rows if r['group'] in ('canonical','flow')]
        elif mode=='composition':rows=[r for r in rows if r['group'] in ('canonical','composition') or r['case_id']=='VAPOR_SIMPLE']
        else:rows=[r for r in rows if r['group']==mode]
        print('case | scope | F | z | Pin | Pout | ratio | Tin | Tout | phase in -> out | beta | Hin | Hout | dH | Sin | Sout | dS | PH residual | candidates')
        for c in rows:
            r=c['result'];a,b=r['inlet'],r['outlet'];s=c['inputs']
            print(c['case_id'],'primary' if c['accepted_primary_scope'] else 'separate study',s['F'],s['z'],s['Pin'],s['Pout'],r['pressure_ratio'],a['T_K'],b['T_K'],a['classification']+' -> '+b['classification'],b['beta'],a['H_eq_J_mol'],b['H_eq_J_mol'],r['enthalpy_residual_J_mol'],a['S_eq_J_mol_K'],b['S_eq_J_mol_K'],r['delta_S_J_mol_K'],r['PH_residual_J_mol'],r['PH']['candidate_count'],'PASS',sep=' | ')
            if mode=='canonical':print('Outlet phases:',b['phases'])
    print('SHA256:',sha(ARTIFACT))
    print(f"PASS: {len(data['cases'])} primary; {len(data['separate_studies'])} separate studies; {len(data['negative_cases'])} negative; {data['comparison_count']} numerical comparisons; {len(data['call_order'])} byte-identical call-order checks")


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--case',choices=MODES,default='summary')
    args=parser.parse_args();data=build();raw=encode(data)
    if args.write:ARTIFACT.write_text(raw)
    else:assert ARTIFACT.read_text()==raw,'Frozen artifact differs; verification never rewrites it'
    display(data,args.case)


if __name__=='__main__':main()
