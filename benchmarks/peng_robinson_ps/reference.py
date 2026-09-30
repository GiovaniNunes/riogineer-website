"""Generate (--write) or verify independent Pre-M13 evidence; no production truth."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
try:
    from .equilibrium import EntropyPT, TrialFailure, caloric, ROOT
    from .solver import solve_ps, S_TOL, T_TOL, SCAN_POINTS
except ImportError:
    from equilibrium import EntropyPT, TrialFailure, caloric, ROOT
    from solver import solve_ps, S_TOL, T_TOL, SCAN_POINTS

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE/'methane_nhexane_pr_ps_reference.json'
TOLS = dict(T=dict(atol=1e-7, rtol=0.), S_residual=dict(atol=S_TOL, rtol=0.),
            beta=dict(atol=1e-9, rtol=1e-9), composition=dict(atol=1e-9, rtol=1e-9),
            Z=dict(atol=1e-10, rtol=1e-9), s=dict(atol=1e-8, rtol=1e-11),
            h=dict(atol=1e-6, rtol=1e-11))


def encode(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n'


def close(a, b, kind):
    t = TOLS[kind]
    assert math.isfinite(a) and abs(a-b) <= t['atol']+t['rtol']*abs(b), (kind,a,b)


def compare_states(a, b):
    assert a['classification'] == b['classification'] and a['phases'].keys() == b['phases'].keys()
    errors = {}
    for field,kind,label in [('T_K','T','T'),('beta','beta','beta'),('S_eq_J_mol_K','s','S_eq'),('H_eq_J_mol','h','H_eq')]:
        close(a[field],b[field],kind)
        errors[label] = abs(a[field]-b[field])
    for name,p in a['phases'].items():
        q = b['phases'][name]
        suffix = 'L' if name == 'liquid' else 'V'
        for field,kind,label in [('Z','Z','Z_'),('s_J_mol_K','s','S_'),('h_J_mol','h','H_')]:
            close(p[field],q[field],kind)
            errors[label+suffix] = abs(p[field]-q[field])
        for field,kind in [('s_ig_J_mol_K','s'),('s_res_J_mol_K','s'),('h_ig_J_mol','h'),('h_res_J_mol','h')]:
            close(p[field],q[field],kind)
        for x,y in zip(p['composition'],q['composition']):
            close(x,y,'composition')
        errors['x' if name == 'liquid' else 'y'] = max(abs(x-y) for x,y in zip(p['composition'],q['composition']))
    return errors


def compact(r):
    d = dict(r['diagnostics'])
    scan = d.pop('scan')
    d['scan_sha256'] = hashlib.sha256(encode(scan).encode()).hexdigest()
    d['successful_scan_evaluations'] = sum(x['status']=='success' for x in scan)
    d['scan_endpoints'] = [scan[0],scan[-1]] if scan else []
    return dict(status=r['status'], message=r['message'], diagnostics=d,
                **({'solution':r['solution']} if 'solution' in r else {}))


def negative_specs():
    # JSON-safe tokens are decoded only at execution; no NaN/Infinity JSON literals.
    return [
        ('NONFINITE_P', {'P':'NaN'}, 'invalid_input'),
        ('ZERO_P', {'P':0.}, 'invalid_input'),
        ('NEGATIVE_P', {'P':-1.}, 'invalid_input'),
        ('BAD_SUM', {'z':[.4,.4]}, 'invalid_input'),
        ('NEGATIVE_Z', {'z':[-.1,1.1]}, 'invalid_input'),
        ('WATER', {'component_ids':['methane','water']}, 'unsupported_components'),
        ('UNKNOWN', {'component_ids':['methane','unknown']}, 'unsupported_components'),
        ('NONZERO_BIP', {'kij':[[0.,.01],[.01,0.]]}, 'unsupported_bip'),
        ('INVALID_BOUNDS_LOW', {'bounds':[199.,500.]}, 'temperature_domain_invalid'),
        ('INVALID_BOUNDS_HIGH', {'bounds':[200.,501.]}, 'temperature_domain_invalid'),
        ('BELOW_RANGE', {'S_target':-1e6}, 'entropy_target_not_bracketed'),
        ('ABOVE_RANGE', {'S_target':1e6}, 'entropy_target_not_bracketed'),
        ('NONFINITE_S', {'S_target':'Infinity'}, 'invalid_input'),
        ('MAX_ITERATIONS', {'maxiter':1,'grid_points':128}, 'ps_nonconvergence'),
        ('SYNTHETIC_MULTIPLE', {'synthetic':'multiple','S_target':0.}, 'ambiguous_ps_root'),
        ('SYNTHETIC_HOLE', {'synthetic':'hole','S_target':0.}, 'property_evaluation_failed'),
    ]


def run_negative(overrides, default_target):
    kw = dict(P=3e5,z=[.5,.5],S_target=default_target)
    kw.update(overrides)
    synthetic = kw.pop('synthetic',None)
    for key in ('P','S_target'):
        if isinstance(kw[key],str):
            kw[key] = float(kw[key])
    if synthetic:
        def evaluator(T,P,z):
            if synthetic == 'hole' and 290 < T < 310:
                raise TrialFailure('pt','Synthetic property hole inside candidate region')
            s = (T-270)*(T-430) if synthetic == 'multiple' else T-300
            return dict(S_eq_J_mol_K=s,classification='synthetic')
        kw['evaluator'] = evaluator
    return solve_ps(**kw)


def build():
    oracle = EntropyPT()
    boundaries = {name:oracle.flash.flash(P=6e6,VF=vf,zs=[.5,.5]).T for name,vf in [('bubble',0.),('dew',1.)]}
    specs = [('A_LIQUID',300.,3e7,[.5,.5]),('B_VL',300.,3e5,[.5,.5]),('C_VAPOR',300.,1e3,[.5,.5]),
             ('T350_LIQUID',350.,3e7,[.5,.5]),('T350_VL',350.,1e6,[.5,.5]),('T350_VAPOR',350.,1e3,[.5,.5])]
    for name,T in boundaries.items():
        for sign,offset in [('BELOW',-.5),('ABOVE',.5)]:
            specs.append((name.upper()+'_'+sign,T+offset,6e6,[.5,.5]))
    specs += [('NEAR_REFERENCE',298.15,101325.,[1.,0.]),('PURE_METHANE',300.,1e5,[1.,0.]),
              ('PURE_HEXANE_LIQUID',300.,3e7,[0.,1.]),('PURE_HEXANE_VAPOR',300.,1e3,[0.,1.]),
              ('BINARY_30_70',300.,3e5,[.3,.7])]
    old = json.loads(caloric.ARTIFACT.read_text())
    cases=[]; density=[]; maxima={}; cross=[]; pt_sensitivity=[]; perturbations=[]
    for name,T,P,z in specs:
        forward=oracle.evaluate(T,P,z); S=forward['S_eq_J_mol_K']
        # Check against unchanged Pre-M10 phase entropy/enthalpy where matched.
        matched=[]
        for c in old['cases']:
            if c['T_K']==T and c['P_Pa_abs']==P and z==[.5,.5]:
                for label,p in forward['phases'].items():
                    q=c['phases'][label]
                    for field,oldfield,kind in [('s_J_mol_K','s_total_J_mol_K','s_total'),('h_J_mol','h_total_J_mol','h_total')]:
                        caloric.close(p[field],q[oldfield],kind)
                matched.append(c['case_id'])
        for q in old['pure_states']:
            if q['T_K']==T and q['P_Pa_abs']==P and q['composition']==z:
                p=next(iter(forward['phases'].values()))
                caloric.close(p['s_J_mol_K'],q['s_total_J_mol_K'],'s_total')
                caloric.close(p['h_J_mol'],q['h_total_J_mol'],'h_total')
                matched.append(q['component_id'])
        r=solve_ps(P,z,S)
        assert r['status']=='success',(name,r)
        final=r['solution']; errors=compare_states(final,forward)
        errors['S_residual']=abs(final['S_residual_J_mol_K'])
        for k,v in errors.items():
            if k not in maxima or v>maxima[k]['absolute_error']:
                maxima[k]=dict(absolute_error=v,case_id=name)
        slopes=[]
        for dt in [.01,.001]:
            a,b=[oracle.evaluate(T+sign*dt,P,z) for sign in [-1,1]]
            slopes.append(dict(delta_T_K=dt,dS_dT_J_mol_K2=(b['S_eq_J_mol_K']-a['S_eq_J_mol_K'])/(2*dt)))
        cases.append(dict(case_id=name,input=dict(P=P,z=z,S_target=S),forward=forward,inverse=compact(r),
                          errors=errors,conditioning=slopes,consistency=oracle.identities(final),pre_m10_matches=matched))
        studies=[]
        for n in [64,128,256]:
            alt=r if n==SCAN_POINTS else solve_ps(P,z,S,grid_points=n)
            assert alt['status']=='success',(name,n,alt)
            compare_states(alt['solution'],forward)
            studies.append(dict(grid_points=n,**compact(alt)))
        density.append(dict(case_id=name,runs=studies))
        direct=solve_ps(P,z,S,direct=True,xtol=1e-12)
        assert direct['status']=='success',(name,direct)
        cross.append(dict(case_id=name,method='direct entropy equation, bisection 1e-12 K',
                          errors=compare_states(direct['solution'],final),result=compact(direct)))
        for ds in [-.01,.01]:
            alt=solve_ps(P,z,S+ds)
            assert alt['status']=='success',(name,ds,alt)
            assert (alt['solution']['T_K']-T)*ds>0
            perturbations.append(dict(case_id=name,delta_S_J_mol_K=ds,result=compact(alt)))
        if name.startswith(('BUBBLE','DEW')):
            for accuracy in [1e-16,1e-22,1e-26,1e-28]:
                pt=EntropyPT(accuracy)
                alt=solve_ps(P,z,S,evaluator=pt.evaluate)
                # Looser PT is diagnostic, never allowed to redefine the primary truth.
                if alt['status'] != 'success':
                    assert accuracy > 1e-26, (name,accuracy,alt)
                    pt_sensitivity.append(dict(case_id=name,PT_SS_TOL=accuracy,result=compact(alt)))
                    continue
                a=alt['solution']
                pt_sensitivity.append(dict(case_id=name,PT_SS_TOL=accuracy,result=compact(alt),
                    delta_T_K=a['T_K']-T,delta_H_J_mol=a['H_eq_J_mol']-forward['H_eq_J_mol'],
                    delta_S_J_mol_K=a['S_eq_J_mol_K']-S,
                    phase_errors={k:dict(S=a['phases'][k]['s_J_mol_K']-v['s_J_mol_K'],H=a['phases'][k]['h_J_mol']-v['h_J_mol']) for k,v in forward['phases'].items()}))
    continuity=[]
    for name,T in boundaries.items():
        refinements=[]
        for dt in [.1,.01,.001,.0001,.00001]:
            states=[oracle.evaluate(T+sign*dt,6e6,[.5,.5]) for sign in [-1,1]]
            expected=['single_liquid','vapor_liquid'] if name=='bubble' else ['vapor_liquid','single_vapor']
            assert [s['classification'] for s in states]==expected
            span=states[1]['S_eq_J_mol_K']-states[0]['S_eq_J_mol_K']
            assert span>0
            refinements.append(dict(delta_T_K=dt,entropy_span_J_mol_K=span,states=states))
        assert all(b['entropy_span_J_mol_K']<a['entropy_span_J_mol_K'] for a,b in zip(refinements,refinements[1:]))
        continuity.append(dict(boundary=name,T_K=T,P_Pa_abs=6e6,z=[.5,.5],refinements=refinements))
    Tsat=oracle.flash.flash(P=1000.,VF=0.,zs=[0.,1.]).T
    gap=[]
    for dt in [.1,.01,.001,.0001,.00001]:
        states=[oracle.evaluate(Tsat+sign*dt,1000.,[0.,1.]) for sign in [-1,1]]
        gap.append(dict(delta_T_K=dt,states=states,entropy_span_J_mol_K=states[1]['S_eq_J_mol_K']-states[0]['S_eq_J_mol_K']))
    target=sum(s['S_eq_J_mol_K'] for s in gap[-1]['states'])/2
    g=solve_ps(1000.,[0.,1.],target)
    assert g['status']=='ps_nonconvergence' and g['diagnostics']['gap_detected'] and 'solution' not in g
    negatives=[]
    for name,overrides,expected in negative_specs():
        r=run_negative(overrides,cases[1]['input']['S_target'])
        assert r['status']==expected and 'solution' not in r,(name,r)
        negatives.append(dict(case_id=name,specification=dict(P=3e5,z=[.5,.5],S_target=cases[1]['input']['S_target'],**{})|overrides,
                              overrides=overrides,expected_status=expected,accepted_state=False,result=compact(r)))
    negatives.append(dict(case_id='PURE_COEXISTENCE_GAP',specification=dict(P=1000.,z=[0.,1.],S_target=target),
                          expected_status='ps_nonconvergence',accepted_state=False,result=compact(g)))
    # Same reusable oracle after reversed regimes and an unsuccessful inversion.
    order=[]
    for c in reversed(cases):
        solve_ps(3e5,[.5,.5],1e6,evaluator=oracle.evaluate)
        r=solve_ps(**c['input'],evaluator=oracle.evaluate)
        assert encode(compact(r))==encode(c['inverse']),c['case_id']
        order.append(c['case_id'])
    sources=[HERE/'solver.py',HERE/'equilibrium.py',HERE/'reference.py',
             ROOT/'benchmarks/peng_robinson_ph/equilibrium.py',
             ROOT/'benchmarks/peng_robinson_caloric/reference.py',
             ROOT/'benchmarks/peng_robinson_caloric/equations.py',caloric.ARTIFACT]
    return dict(reference_id='independent_methane_nhexane_pr_ps@1.0',
        metadata=dict(python=platform.python_version(),versions={n:importlib.metadata.version(n) for n in ['thermo','chemicals','fluids','numpy','scipy','pandas','teqp']},
            source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            entropy_reference=old['reference_state'],components=caloric.COMPONENTS,cp=old['cp'],kij=caloric.KIJ,
            eos=old['formulation'],temperature_domain_K=[200.,500.],pressure_matrix_Pa=sorted({c['input']['P'] for c in cases}),
            scan_points=SCAN_POINTS,root_method='bisection',maxiter=100,temperature_tolerance_K=T_TOL,entropy_tolerance_J_mol_K=S_TOL,
            PT_SS_TOL=1e-26,PT_STABILITY_XTOL=1e-12,
            generation_command='.local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_ps/reference.py --write',
            scope='Finite methane/n_hexane matrix; no critical/retrograde/general-mixture or pure coexistence interpolation qualification'),
        tolerances=TOLS,cases=cases,negative_cases=negatives,maximum_errors=maxima,
        minimum_matrix_slope_J_mol_K2=min(p['dS_dT_J_mol_K2'] for c in cases for p in c['conditioning']),
        scan_density=density,cross_method=cross,pt_accuracy_sensitivity=pt_sensitivity,
        boundary_continuity=continuity,pure_gap=dict(T_saturation_K=Tsat,P_Pa_abs=1000.,refinements=gap,target_S_J_mol_K=target),
        target_perturbations=perturbations,call_order=dict(reversed_cases=order,prior_failure=True,byte_identical=True))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    fresh=build(); data=encode(fresh)
    if args.write:
        ARTIFACT.write_text(data)
    else:
        assert ARTIFACT.read_text()==data,'Frozen byte reproduction failed'
    print('PASS:',len(fresh['cases']),'positive;',len(fresh['negative_cases']),'negative')
    print(encode(fresh['maximum_errors']))
    print('minimum slope',fresh['minimum_matrix_slope_J_mol_K2'])
    print('SHA256',hashlib.sha256(data.encode()).hexdigest())


if __name__=='__main__':
    main()
