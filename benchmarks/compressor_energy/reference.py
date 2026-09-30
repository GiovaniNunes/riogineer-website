"""Independent Pre-M14 evidence. Default verifies; only --write freezes new truth."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys

try:
    from .solver import ROOT, IDS, ZERO, EntropyPT, TrialFailure, calculate, solve_ps, solve_ph
except ImportError:
    from solver import ROOT, IDS, ZERO, EntropyPT, TrialFailure, calculate, solve_ps, solve_ph

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE/'methane_nhexane_compressor_reference.json'
BASELINE = '94682d9d2bb499eea2d850d09831f553f694f01c'
BASE = dict(P1=1e5, T1=300., P2=3e5, eta=.8, flow=100., z=[.9,.1])
TOLS = dict(T=1e-7, H=1e-6, S=1e-8, beta=2e-9, composition=2e-9, Z=2e-10,
            H_relative=1e-11, S_relative=1e-11, Z_relative=1e-9,
            PH_residual=1e-6, PS_residual=1e-8)


def encode(x):
    return json.dumps(x, sort_keys=True, indent=2, allow_nan=False)+'\n'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive_specs():
    cases = [('CANONICAL', 'canonical', {})]
    cases += [('ETA_'+str(e), 'efficiency', dict(eta=e)) for e in [.6,.7,.75,.85,.9,1.]]
    cases += [('RATIO_'+str(r), 'pressure', dict(P2=1e5*r)) for r in [1.5,2.,5.,8.]]
    cases += [('FLOW_'+str(f), 'flow', dict(flow=f)) for f in [1.,10.,200.]]
    cases += [('BALANCED', 'composition', dict(T1=350., P2=2e5, z=[.5,.5])),
              ('HEXANE_RICH', 'composition', dict(T1=360., P2=2e5, z=[.3,.7])),
              ('PURE_METHANE', 'pure', dict(z=[1.,0.])),
              ('PURE_HEXANE', 'pure', dict(P1=1e3, P2=2e3, z=[0.,1.]))]
    oracle = EntropyPT()
    dew = oracle.flash.flash(P=1e5, VF=1., zs=[.5,.5]).T
    cases += [('BOUNDARY_VAPOR', 'boundary', dict(T1=dew+2., P2=1.5e5, z=[.5,.5]))]
    return [(name, group, BASE | patch) for name,group,patch in cases]


def negative_specs():
    out=[]
    for field, category, values in [
        ('flow','invalid_flow',[0.,-1.,'NaN','Infinity','-Infinity']),
        ('P1','invalid_pressure',[0.,-1.,'NaN','Infinity','-Infinity']),
        ('P2','invalid_pressure',[0.,-1.,'NaN','Infinity','-Infinity',1e5,5e4]),
        ('eta','invalid_efficiency',[0.,-.1,1.01,'NaN','Infinity','-Infinity'])]:
        out += [(field.upper()+'_'+str(v), {field:v}, category, 'input') for v in values]
    out += [('BAD_SUM',dict(z=[.4,.4]),'invalid_composition','input'),
            ('NEGATIVE_Z',dict(z=[-.1,1.1]),'invalid_composition','input'),
            ('NONFINITE_Z',dict(z=['NaN',.1]),'invalid_composition','input'),
            ('WATER',dict(component_ids=['methane','water']),'unsupported_components','input'),
            ('UNKNOWN',dict(component_ids=['methane','unknown']),'unsupported_components','input'),
            ('NONZERO_KIJ',dict(kij=[[0.,.01],[.01,0.]]),'unsupported_bip','input'),
            ('T_LOW',dict(T1=199.),'temperature_domain_invalid','input'),
            ('T_HIGH',dict(T1=501.),'temperature_domain_invalid','input'),
            ('T_NAN',dict(T1='NaN'),'temperature_domain_invalid','input'),
            ('LIQUID_SERVICE',dict(P1=3e7,P2=4e7,z=[.5,.5]),'compressor_state_invalid','inlet'),
            ('VL_SERVICE',dict(P1=3e5,P2=6e5,z=[.5,.5]),'compressor_state_invalid','inlet'),
            ('PS_UNBRACKETED',dict(T1=490.,P2=8e5),'ps_failure','isentropic'),
            ('PH_UNBRACKETED',dict(eta=.1,P2=8e5),'ph_failure','actual_outlet')]
    for name,stage in [('PT_INJECTED','inlet'),('PS_INJECTED','isentropic'),('PH_INJECTED','actual_outlet'),
                       ('PS_GAP','isentropic'),('PH_GAP','actual_outlet'),('PS_AMBIGUOUS','isentropic'),('PS_HOLE','isentropic')]:
        out.append((name,dict(synthetic=name), 'pt_failure' if stage=='inlet' else 'ps_failure' if stage=='isentropic' else 'ph_failure',stage))
    return out


def decode(x):
    if isinstance(x,str) and x in ('NaN','Infinity','-Infinity'):return float(x)
    if isinstance(x,list):return [decode(v) for v in x]
    if isinstance(x,dict):return {k:decode(v) for k,v in x.items()}
    return x


def run_negative(patch, oracle=None):
    kw = BASE | decode(patch)
    name = kw.pop('synthetic',None)
    if oracle is not None:kw['oracle']=oracle
    if name == 'PT_INJECTED':
        class Broken:
            def evaluate(self,*args):raise TrialFailure('pt','Synthetic inlet PT failure')
        kw['oracle']=Broken()
    elif name in ('PS_INJECTED','PH_INJECTED'):
        def fail(*args,**kwargs):
            return dict(status='injected_failure',message='Synthetic nested failure',diagnostics={})
        kw['ps_solver' if name.startswith('PS') else 'ph_solver']=fail
    elif name in ('PS_GAP','PH_GAP'):
        def gap(*args,**kwargs):
            oracle=EntropyPT();T=oracle.flash.flash(P=1000.,VF=0.,zs=[0.,1.]).T
            pair=[oracle.evaluate(T+d,1000.,[0.,1.]) for d in [-1e-5,1e-5]]
            key='S_eq_J_mol_K' if name=='PS_GAP' else 'H_eq_J_mol'
            target=sum(s[key] for s in pair)/2
            fn=solve_ps if name=='PS_GAP' else solve_ph
            return fn(1000.,[0.,1.],target,evaluator=oracle.evaluate)
        kw['ps_solver' if name=='PS_GAP' else 'ph_solver']=gap
    elif name in ('PS_AMBIGUOUS','PS_HOLE'):
        def injected(*args,**kwargs):
            def evaluator(T,P,z):
                if name=='PS_HOLE' and 290<T<310:raise TrialFailure('pt','Synthetic property hole')
                S=(T-270)*(T-430) if name=='PS_AMBIGUOUS' else T-300
                return dict(S_eq_J_mol_K=S,classification='synthetic')
            return solve_ps(3e5,[.9,.1],0.,evaluator=evaluator)
        kw['ps_solver']=injected
    return calculate(**kw)


def compact_diagnostics(d):
    out=dict(d)
    for key in ('scan','root_trials'):
        if key in out:
            rows=out.pop(key)
            out[key+'_sha256']=hashlib.sha256(encode(rows).encode()).hexdigest()
            out[key+'_count']=len(rows)
    out['candidate_count']=len(d.get('brackets',[]))
    return out


def compact(result):
    r=dict(result)
    for key in ('PS','PH'):
        if key in r:r[key]=compact_diagnostics(r[key])
    if 'solver_failure' in r:
        r['solver_failure']=dict(r['solver_failure'])
        r['solver_failure']['diagnostics']=compact_diagnostics(r['solver_failure']['diagnostics'])
    return r


def roundoff(i,r):
    return 64*sys.float_info.epsilon*max(1.,abs(r['fluid_power_W']),abs(i['flow']*r['inlet']['H_eq_J_mol']),abs(i['flow']*r['outlet']['H_eq_J_mol']))


def audit(i,r):
    """Method B: fsum reconstruction using stored states, not target-formula echoes."""
    a,b,c=[r[k] for k in ('inlet','isentropic','outlet')]
    H1,Hs,H2=[s['H_eq_J_mol'] for s in (a,b,c)]
    S1,Ss,S2=[s['S_eq_J_mol_K'] for s in (a,b,c)]
    dhs=math.fsum([Hs,-H1]);dh=math.fsum([H2,-H1]);F=i['flow'];eta=i['eta']
    budget=roundoff(i,r)
    checks=[]
    def check(field,x,y,tol):
        error=abs(x-y)
        checks.append(dict(field=field,actual=x,reference=y,absolute_error=error,allowance=tol))
        assert math.isfinite(x) and error<=tol,(field,x,y,tol)
    check('S2s_residual',Ss,S1,TOLS['PS_residual'])
    check('H2_target',r['H2_target_J_mol'],math.fsum([Hs/eta,H1*(1-1/eta)]),budget/F)
    check('H2_recovered',H2,r['H2_target_J_mol'],TOLS['PH_residual'])
    eta_tol=eta*TOLS['PH_residual']/abs(dh)+64*sys.float_info.epsilon
    check('eta',dhs/dh,eta,eta_tol)
    check('eta_power',(F*dhs)/r['fluid_power_W'],eta,eta_tol)
    check('fluid_power',r['fluid_power_W'],math.fsum([F*H2,-F*H1]),budget)
    check('isentropic_power',r['isentropic_fluid_power_W'],math.fsum([F*Hs,-F*H1]),budget)
    check('power_identity',r['fluid_power_W'],F*dhs/eta,F*TOLS['PH_residual']+budget)
    check('energy_residual',r['energy_residual_W'],0.,budget)
    check('molar_flow',r['molar_flow_out_mol_s'],F,0.)
    for j,(x,y) in enumerate(zip(r['z_out'],i['z'])):check('z'+str(j),x,y,0.)
    for label,s in zip(('1','2s','2'),(a,b,c)):
        assert 200<=s['T_K']<=500
        check('H'+label+'_direct',s['H_eq_J_mol'],s['H_eq_direct_J_mol'],TOLS['H']+TOLS['H_relative']*abs(s['H_eq_J_mol']))
        check('S'+label+'_direct',s['S_eq_J_mol_K'],s['S_eq_direct_J_mol_K'],TOLS['S']+TOLS['S_relative']*abs(s['S_eq_J_mol_K']))
    assert dhs>0 and dh>0 and r['fluid_power_W']>0
    assert H2>=Hs-TOLS['PH_residual'] and S2>=S1-2*TOLS['S']
    if eta<1:assert H2>Hs and S2>S1
    if i.get('service','vapor')=='vapor':
        assert all(s['classification']=='single_vapor' for s in (a,b,c))
        assert c['T_K']>=b['T_K']-TOLS['T']
    if eta==1:
        check('ideal_T',c['T_K'],b['T_K'],TOLS['T'])
        check('ideal_S',S2,S1,2*TOLS['S'])
        check('ideal_H',H2,Hs,TOLS['PH_residual'])
    assert len(r['PS']['brackets'])==len(r['PH']['brackets'])==1
    assert r['PS']['fresh_final'] and r['PH']['final_evaluations']==1
    return checks


def state_fields(s):
    fields=dict(T=s['T_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
    for name,p in s['phases'].items():
        for label,key in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:fields[name+'.'+label]=p[key]
        for j,x in enumerate(p['composition']):fields[name+'.q'+str(j)]=x
    return fields


def sensitivity(s):
    oracle=EntropyPT();dt=.001
    pair=[oracle.evaluate(s['T_K']+d,s['P_Pa_abs'],s['z']) for d in [-dt,dt]]
    assert all(p['classification']==s['classification'] for p in pair)
    a,b=map(state_fields,pair)
    return {k:(b[k]-a[k])/(2*dt) for k in a}


def state_allowances(s,slopes,temperature_error):
    result={}
    for k,v in state_fields(s).items():
        kind=k.split('.')[-1]
        base=(TOLS['H']+TOLS['H_relative']*abs(v) if kind=='H' else
              TOLS['S']+TOLS['S_relative']*abs(v) if kind=='S' else
              TOLS['Z']+TOLS['Z_relative']*abs(v) if kind=='Z' else
              TOLS['composition'] if kind.startswith('q') else TOLS.get(kind,0.))
        result[k]=base+abs(slopes[k])*temperature_error
    return result


def allowances(i,r):
    a,b,c=[r[k] for k in ('inlet','isentropic','outlet')]
    slopes=[sensitivity(s) for s in (a,b,c)]
    assert all(s['H']>0 and s['S']>0 for s in slopes)
    first=state_allowances(a,slopes[0],0.)
    # Fourfold local linear propagation budget, additional to inherited base gates.
    ts=4*(first['S']+TOLS['PS_residual'])/slopes[1]['S']+TOLS['T']
    second=state_allowances(b,slopes[1],ts)
    ht=first['H']+(second['H']+first['H'])/i['eta']
    tout=4*(ht+TOLS['PH_residual'])/slopes[2]['H']+TOLS['T']
    third=state_allowances(c,slopes[2],tout)
    power=i['flow']*(third['H']+first['H'])+roundoff(i,r)
    return dict(inlet=first,isentropic=second,outlet=third,H2_target=ht,
                fluid_power=power,isentropic_power=i['flow']*(second['H']+first['H']),
                eta=(second['H']+first['H']+i['eta']*(third['H']+first['H']))/r['delta_H_actual_J_mol'],
                slopes=slopes,temperature_error_2s=ts,temperature_error_2=tout)


def maxima(rows):
    out={}
    for name,checks in rows:
        for c in checks:
            if c['field'] not in out or c['absolute_error']>out[c['field']]['absolute_error']:
                out[c['field']]=dict(case_id=name,**c)
    return out


def build():
    cases=[]
    for name,group,i in positive_specs():
        r=calculate(**i)
        assert r['status']=='success',(name,i,r)
        checks=audit(i,r)
        cases.append(dict(case_id=name,group=group,inputs=i,result=compact(r),checks=checks,allowances=allowances(i,r)))
    neg=[]
    for name,patch,status,stage in negative_specs():
        r=run_negative(patch)
        assert r['status']==status and r['failure_stage']==stage and not r['accepted_outlet'],(name,r)
        assert not any(k in r for k in ('inlet','isentropic','outlet','H2_target_J_mol','fluid_power_W'))
        neg.append(dict(case_id=name,inputs=BASE|patch,overrides=patch,expected_status=status,expected_stage=stage,
                        synthetic='synthetic' in patch,result=compact(r)))
    studies=[]
    i=BASE|dict(P1=3e5,P2=6e5,z=[.5,.5],service='thermodynamic_only')
    r=calculate(**i)
    assert r['status']=='success',r
    studies.append(dict(case_id='VL_THERMODYNAMIC_ONLY',inputs=i,result=compact(r),checks=audit(i,r),allowances=allowances(i,r)))
    # Cross-method solve uses direct caloric equations and alternative PH bisection.
    cross=[]
    for c in cases+studies:
        i=c['inputs'];o=EntropyPT();a=o.evaluate(i['T1'],i['P1'],i['z'])
        ps=solve_ps(i['P2'],i['z'],a['S_eq_direct_J_mol_K'],direct=True,xtol=1e-12,evaluator=o.evaluate)
        assert ps['status']=='success',(c['case_id'],ps)
        h=a['H_eq_direct_J_mol']+(ps['solution']['H_eq_direct_J_mol']-a['H_eq_direct_J_mol'])/i['eta']
        ph=solve_ph(i['P2'],i['z'],h,direct=True,method='bisect',xtol=1e-12,evaluator=o.evaluate)
        assert ph['status']=='success',(c['case_id'],ph)
        checks=[]
        for stage,s in [('inlet',a),('isentropic',ps['solution']),('outlet',ph['solution'])]:
            expected=state_fields(c['result'][stage]);actual=state_fields(s)
            assert s['classification']==c['result'][stage]['classification']
            for key,v in actual.items():
                error=abs(v-expected[key]);tol=c['allowances'][stage][key]
                assert error<=tol,(c['case_id'],stage,key,error,tol)
                checks.append(dict(field=stage+'.'+key,absolute_error=error,allowance=tol))
        cross.append(dict(case_id=c['case_id'],checks=checks))
    canonical=cases[0]
    def series(group,key,reverse=False):
        chosen=[canonical]+[c for c in cases if c['group']==group]
        return sorted(chosen,key=lambda c:c['inputs'][key],reverse=reverse)
    efficiencies=series('efficiency','eta',True)
    pressures=series('pressure','P2')
    for group in (efficiencies,pressures):
        for a,b in zip(group,group[1:]):
            for key in ('delta_H_actual_J_mol','fluid_power_W'):
                assert b['result'][key]>a['result'][key]
            assert b['result']['outlet']['T_K']>a['result']['outlet']['T_K']
    assert all(c['result']['isentropic']==canonical['result']['isentropic'] for c in efficiencies)
    assert all(b['result']['delta_H_is_J_mol']>a['result']['delta_H_is_J_mol'] for a,b in zip(pressures,pressures[1:]))
    scaling=[]
    for c in series('flow','flow'):
        r=c['result'];ref=canonical['result'];ratio=c['inputs']['flow']/BASE['flow']
        assert all(r[k]==ref[k] for k in ('inlet','isentropic','outlet','H2_target_J_mol','PS','PH'))
        error=abs(r['fluid_power_W']-ratio*ref['fluid_power_W']);tol=roundoff(c['inputs'],r)
        assert error<=tol
        scaling.append(dict(case_id=c['case_id'],absolute_error_W=error,relative_error=error/abs(r['fluid_power_W']),allowance_W=tol))
    # Reuse a single oracle across positive, negative and injected-failure histories.
    o=EntropyPT();order=[]
    sequences=[('positive',cases[-1]['inputs']),('low_efficiency',BASE|dict(eta=.6)),('ideal',BASE|dict(eta=1.)),
               ('invalid',dict(flow=0.)),('PS_failure',dict(synthetic='PS_INJECTED')),('PH_failure',dict(synthetic='PH_INJECTED'))]
    representatives=[canonical,cases[14],studies[0]]
    for name,prior in sequences:
        for c in representatives:
            if name in ('positive','low_efficiency','ideal'):calculate(**prior,oracle=o)
            else:run_negative(prior,o)
            actual=compact(calculate(**c['inputs'],oracle=o))
            assert encode(actual)==encode(c['result']),(name,c['case_id'])
            order.append(dict(after=name,case_id=c['case_id'],byte_identical=True))
    old=json.loads((ROOT/'benchmarks/peng_robinson_ps/methane_nhexane_pr_ps_reference.json').read_text())
    sources=[HERE/'solver.py',HERE/'reference.py']+[ROOT/'benchmarks'/p for p in [
        'peng_robinson_ps/solver.py','peng_robinson_ps/equilibrium.py','peng_robinson_ph/solver.py',
        'peng_robinson_ph/equilibrium.py','peng_robinson_caloric/reference.py','peng_robinson_caloric/equations.py',
        'peng_robinson_ps/methane_nhexane_pr_ps_reference.json','peng_robinson_ph/methane_nhexane_pr_ph_reference.json',
        'peng_robinson_caloric/methane_nhexane_pr_caloric_reference.json']]
    return dict(reference_id='independent_methane_nhexane_compressor@1.0',baseline=BASELINE,
                metadata=dict(versions={n:importlib.metadata.version(n) for n in ['thermo','chemicals','fluids','numpy','scipy','pandas','teqp']},
                    source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sources},
                    component_ids=IDS,kij=ZERO,temperature_domain_K=[200.,500.],
                    thermodynamic_convention=old['metadata']['entropy_reference'],components=old['metadata']['components'],cp=old['metadata']['cp'],
                    convention='H2target=H1+(H2s-H1)/eta; power=flow*(H2-H1); positive into fluid; Q=KE=PE=0',
                    controls=dict(PS_scan=64,PH_scan=128,bounds_K=[200.,500.],PS_method='bisection',PH_method='brentq',
                                  max_iterations=100,xtol_K=1e-10,PS_residual=1e-8,PH_residual=1e-6,PT_SS_TOL=1e-26),
                    scope='Single-vapor service, finite zero-kij methane/n_hexane matrix; separate VL algorithm evidence only'),
                tolerances=TOLS,cases=cases,negative_cases=neg,thermodynamic_studies=studies,cross_method=cross,
                maximum_errors=maxima([(c['case_id'],c['checks']) for c in cases+studies]+[(c['case_id'],c['checks']) for c in cross]),
                flow_scaling=scaling,call_order=order,
                comparison_count=sum(len(c['checks']) for c in cases+studies+cross))


def display(data,mode):
    if mode=='negative':
        for c in data['negative_cases']:print(c['case_id'],c['expected_status'],c['expected_stage'],'accepted_outlet=False')
    elif mode=='summary':
        print('Maximum errors:',encode(data['maximum_errors']))
        print('Flow scaling:',encode(data['flow_scaling']))
        print('Call order:',len(data['call_order']),'byte-identical checks')
    else:
        groups={'canonical':['canonical'],'efficiency':['canonical','efficiency'],'pressure':['canonical','pressure'],
                'flow':['canonical','flow'],'ideal':[],'pure':['pure'],'boundary':['boundary'],'phases':[]}
        rows=data['cases']
        if mode=='ideal':rows=[c for c in rows if c['inputs']['eta']==1]
        elif mode=='phases':rows=rows+data['thermodynamic_studies']
        else:rows=[c for c in rows if c['group'] in groups[mode]]
        for c in rows:
            r=c['result'];i=c['inputs']
            print(c['case_id'],encode(dict(inputs=i,states={k:{f:r[k][f] for f in ['T_K','classification','beta','H_eq_J_mol','S_eq_J_mol_K']} for k in ['inlet','isentropic','outlet']},
                H2_target=r['H2_target_J_mol'],eta=r['reconstructed_eta'],eta_power=r['eta_power'],
                fluid_power_W=r['fluid_power_W'],isentropic_fluid_power_W=r['isentropic_fluid_power_W'],
                energy_residual_W=r['energy_residual_W'],delta_S=r['delta_S_actual_J_mol_K'])))
    print('PASS:',len(data['cases']),'vapor positive;',len(data['thermodynamic_studies']),'separate VL study;',len(data['negative_cases']),
          'negative;',data['comparison_count'],'independent numerical checks')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write',action='store_true')
    p.add_argument('--case',choices=['canonical','efficiency','pressure','flow','ideal','pure','boundary','phases','negative','summary'],default='summary')
    args=p.parse_args();fresh=build();text=encode(fresh)
    if args.write:ARTIFACT.write_text(text)
    else:assert ARTIFACT.read_text()==text,'Frozen byte reproduction failed; never rewritten by verification'
    display(fresh,args.case)
    print('SHA256',hashlib.sha256(text.encode()).hexdigest())


if __name__=='__main__':main()
