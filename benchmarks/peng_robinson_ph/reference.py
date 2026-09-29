"""Generate (--write) or reproduce the independent, benchmark-only PH reference."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
try:
    from .equilibrium import IndependentPT, caloric, ROOT
    from .solver import solve_ph, H_TOL
except ImportError:
    from equilibrium import IndependentPT, caloric, ROOT
    from solver import solve_ph, H_TOL

ARTIFACT = Path(__file__).with_name('methane_nhexane_pr_ph_reference.json')
TOLS = dict(T=dict(atol=1e-7,rtol=0.), H_residual=dict(atol=H_TOL,rtol=0.),
            beta=dict(atol=1e-9,rtol=1e-9), composition=dict(atol=1e-9,rtol=1e-9),
            Z=dict(atol=1e-10,rtol=1e-9), h=dict(atol=1e-7,rtol=1e-11))


def close(a,b,quantity):
    tol=TOLS[quantity]
    assert abs(a-b)<=tol['atol']+tol['rtol']*abs(b), (quantity,a,b)


def compare_states(actual, expected):
    assert actual['classification']==expected['classification']
    close(actual['T_K'],expected['T_K'],'T')
    close(actual['beta'],expected['beta'],'beta')
    close(actual['H_eq_J_mol'],expected['H_eq_J_mol'],'h')
    errors=dict(T=abs(actual['T_K']-expected['T_K']),beta=abs(actual['beta']-expected['beta']),composition=0.,Z=0.,h=0.)
    assert actual['phases'].keys()==expected['phases'].keys()
    for label,p in actual['phases'].items():
        q=expected['phases'][label]
        for key,kind in [('Z','Z'),('h_J_mol','h'),('h_ig_J_mol','h'),('h_res_J_mol','h')]:
            close(p[key],q[key],kind)
            errors[kind]=max(errors[kind],abs(p[key]-q[key]))
        for a,b in zip(p['composition'],q['composition']):
            close(a,b,'composition')
            errors['composition']=max(errors['composition'],abs(a-b))
    return errors


def old_reference_check(state, old):
    close(state['beta'],old['beta'],'beta')
    assert state['classification']=={'L':'single_liquid','V':'single_vapor','VL':'vapor_liquid'}[old['classification']]
    for label,p in state['phases'].items():
        q=old['phases'][label]
        close(p['Z'],q['Z'],'Z')
        for a,b in zip(p['composition'],q['composition']): close(a,b,'composition')
        for newkey,oldkey,quantity in [('h_J_mol','h_total_J_mol','h_total'),('s_J_mol_K','s_total_J_mol_K','s_total')]:
            caloric.close(p[newkey],q[oldkey],quantity)


def compact(result):
    return dict(status=result['status'], solution=result.get('solution'),
                roots=result['diagnostics']['roots'], brackets=result['diagnostics']['brackets'],
                total_evaluations=result['diagnostics']['total_evaluations'])


def build():
    oracle=IndependentPT()
    old=json.loads(caloric.ARTIFACT.read_text())
    cases=[]
    specs=[]
    for ident,T,P,phase in caloric.MATRIX:
        name={'A':'PH_A_SINGLE_LIQUID','B':'PH_B_VAPOR_LIQUID','C':'PH_C_SINGLE_VAPOR'}.get(ident,'PH_'+ident)
        specs.append((name,T,P,[.5,.5],ident))
    for component,z,pressures in [('methane',[1.,0.],[1e5]),('n_hexane',[0.,1.],[1e3,3e7])]:
        for T in [280.,300.,350.,400.]:
            for P in pressures:
                specs.append((f'PH_PURE_{component.upper()}_{int(T)}K_{int(P)}PA',T,P,z,None))
    boundaries={name:oracle.flash.flash(P=6e6,VF=vf,zs=[.5,.5]).T
                for name,vf in [('bubble',0.),('dew',1.)]}
    for name,T in boundaries.items():
        for offset in [-.5,.5]:
            specs.append((f'PH_{name.upper()}_{"BELOW" if offset<0 else "ABOVE"}',T+offset,6e6,[.5,.5],None))
    specs.append(('PH_NEAR_ZERO_H',298.17,1000.,[.5,.5],None))
    for name,T,P,z,oldid in specs:
        forward=oracle.evaluate(T,P,z)
        H=forward['H_eq_J_mol']
        if oldid:
            prior=next(c for c in old['cases'] if c['case_id']==oldid)
            old_reference_check(forward,prior)
            H=prior.get('overall_h_J_mol',next(iter(prior['phases'].values()))['h_total_J_mol'])
            close(H,forward['H_eq_J_mol'],'h')
        elif name.startswith('PH_PURE'):
            prior=next(c for c in old['pure_states'] if c['T_K']==T and c['P_Pa_abs']==P and c['composition']==z)
            p=next(iter(forward['phases'].values()))
            close(p['h_J_mol'],prior['h_total_J_mol'],'h')
            close(p['Z'],prior['Z'],'Z')
        inverse=solve_ph(P,z,H)
        assert inverse['status']=='success',(name,inverse['status'],inverse['message'])
        errors=compare_states(inverse['solution'],forward)
        cases.append(dict(case_id=name,input=dict(P_Pa_abs=P,z=z,H_target_J_mol=H,T_bounds_K=[200.,500.]),
                          forward=forward,inverse=inverse,round_trip_errors=errors,old_reference_case=oldid))
    sensitivity=[]
    for case in cases[:3]:
        inp=case['input']; P,z,H=inp['P_Pa_abs'],inp['z'],inp['H_target_J_mol']
        alternatives={}
        for name,options in [('scan_191',dict(grid_points=191)),('bisect_direct',dict(method='bisect',direct=True))]:
            r=solve_ph(P,z,H,**options)
            assert r['status']=='success',(case['case_id'],name,r['message'])
            compare_states(r['solution'],case['forward'])
            alternatives[name]=compact(r)
        perturbations=[]
        for dH in [-10.,10.]:
            r=solve_ph(P,z,H+dH)
            assert r['status']=='success'
            assert (r['solution']['T_K']-case['forward']['T_K'])*dH>0
            perturbations.append(dict(delta_H_J_mol=dH,**compact(r)))
        study=[]
        for tolerance in [1e-6,1e-8,1e-10,1e-12]:
            r=solve_ph(P,z,H,xtol=tolerance)
            study.append(dict(xtol_K=tolerance,**compact(r)))
        sensitivity.append(dict(case_id=case['case_id'],alternatives=alternatives,perturbations=perturbations,tolerance_study=study))
    continuity=[]
    transition_specs=[(name,T,6e6) for name,T in boundaries.items()]
    transition_specs.extend((f'dew_at_{int(P)}Pa',oracle.flash.flash(P=P,VF=1.,zs=[.5,.5]).T,P) for P in [1000.,3e5])
    for name,T,P in transition_specs:
        refinement=[]
        for dt in [1.,.1,.01,.001,.0001,.00001]:
            states=[oracle.evaluate(T-dt,P,[.5,.5]),oracle.evaluate(T+dt,P,[.5,.5])]
            refinement.append(dict(delta_T_K=dt,states=states,enthalpy_span_J_mol=states[1]['H_eq_J_mol']-states[0]['H_eq_J_mol']))
        assert all(b['enthalpy_span_J_mol']<a['enthalpy_span_J_mol'] for a,b in zip(refinement,refinement[1:]))
        continuity.append(dict(boundary=name,T_K=T,P_Pa_abs=P,refinement=refinement))
    # Pure-fluid saturation has a latent-heat jump in single-valued PT H(T).
    # A PH target inside that gap needs a coexistence lever rule, outside this task.
    pure_T=oracle.flash.flash(P=1000.,VF=0.,zs=[0.,1.]).T
    pure_refinement=[]
    for dt in [1.,.1,.01,.001,.0001]:
        states=[oracle.evaluate(pure_T-dt,1000.,[0.,1.]),oracle.evaluate(pure_T+dt,1000.,[0.,1.])]
        pure_refinement.append(dict(delta_T_K=dt,states=states,
            enthalpy_span_J_mol=states[1]['H_eq_J_mol']-states[0]['H_eq_J_mol']))
    gap_target=sum(s['H_eq_J_mol'] for s in pure_refinement[-1]['states'])/2
    gap_result=solve_ph(1000.,[0.,1.],gap_target)
    assert gap_result['status']=='ph_nonconvergence' and 'solution' not in gap_result
    pure_gap=dict(T_saturation_K=pure_T,P_Pa_abs=1000.,refinement=pure_refinement,
        excluded_target_J_mol=gap_target,inversion=compact(gap_result),
        interpretation='Physical pure-fluid latent heat; no single-valued PT temperature root inside gap. Coexistence lever rule excluded.')
    negatives=[]
    for name,kw,expected in [
        ('PH_BELOW_RANGE',dict(H_target=-1e6),'enthalpy_target_not_bracketed'),
        ('PH_ABOVE_RANGE',dict(H_target=1e6),'enthalpy_target_not_bracketed'),
        ('PH_INVALID_P',dict(P=0.),'invalid_input'),
        ('PH_INVALID_Z',dict(z=[.4,.4]),'invalid_input'),
        ('PH_UNSUPPORTED_WATER',dict(component_ids=['methane','water']),'unsupported_component'),
        ('PH_INVALID_BOUNDS',dict(bounds=[500.,200.]),'temperature_domain_invalid'),
        ('PH_CP_EXTRAPOLATION',dict(bounds=[199.,500.]),'temperature_domain_invalid'),
        ('PH_MAXITER',dict(maxiter=1),'ph_nonconvergence')]:
        inputs=dict(P=3e5,z=[.5,.5],H_target=cases[1]['input']['H_target_J_mol']); inputs.update(kw)
        r=solve_ph(**inputs)
        assert r['status']==expected,(name,r['status'])
        assert 'solution' not in r
        negatives.append(dict(case_id=name,inputs=inputs,expected_status=expected,actual_status=r['status'],message=r['message']))
    sources=['benchmarks/peng_robinson/methane_nhexane_pr_reference.json',
             'benchmarks/peng_robinson_caloric/methane_nhexane_pr_caloric_reference.json',
             'benchmarks/peng_robinson_caloric/reference.py','benchmarks/peng_robinson_caloric/equations.py']
    return dict(reference_id='independent_methane_nhexane_pr_ph@1.0',
        metadata=dict(packages={p:importlib.metadata.version(p) for p in ['thermo','chemicals','fluids','numpy','scipy']},
            source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
            component_constant_identity='riogineer_components@1.0 (frozen independent constants)',
            caloric_convention_identity='pre-M10 Poling reference, shared by riogineer_caloric@1.0',
            eos='canonical PR1976',R_J_mol_K=caloric.R,omega_a=.45724,omega_b=.07780,
            components=caloric.COMPONENTS,cp_data=caloric.CP_DATA,kij=caloric.KIJ,
            BIP_provenance='Explicit zero-kij independent M8 benchmark; not fitted physical interaction data',
            caloric_reference=dict(T_ref_K=298.15,P_ref_Pa_abs=101325.,pure_ideal_h_ref_J_mol=0.,pure_ideal_s_ref_J_mol_K=0.,formation=False),
            basis='T K; P Pa absolute; H J/mol; S J/(mol K); z/x/y and vapor beta molar',
            solver=dict(method='scipy.optimize.brentq',scan_points=128,xtol_K=1e-10,rtol=1e-14,maxiter=100,bounds_K=[200.,500.]),
            limitations=['Selected zero-kij methane/n_hexane states only','No production PH qualification','No pure coexistence lever-rule solver','No critical, retrograde, water, VLLE, PS or equipment qualification']),
        tolerances=TOLS,cases=cases,sensitivity=sensitivity,continuity=continuity,pure_saturation_gap=pure_gap,negative_cases=negatives)


def serialize(data):
    return json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    data=build(); rendered=serialize(data)
    if args.write: ARTIFACT.write_text(rendered)
    else: assert ARTIFACT.read_text()==rendered,'Frozen reference reproduction differs'
    for case in data['cases']:
        s=case['inverse']['solution']
        print(f"{case['case_id']}: P={s['P_Pa_abs']:.12g} Pa H_target={case['input']['H_target_J_mol']:.14g} J/mol T={s['T_K']:.14g} K {s['classification']} RH={s['H_residual_J_mol']:+.6g} J/mol")
    print(f"PASS: {len(data['cases'])} PH round trips; {len(data['negative_cases'])} negative cases; sensitivity and continuity checks")


if __name__=='__main__': main()
