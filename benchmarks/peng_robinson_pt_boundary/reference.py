"""Independent pre-M8.1 evidence. Default reproduces; only --write freezes."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
from scipy.optimize import brentq
try:
    from .study import ROOT, Study, caloric, wilson, rr_value, rr
except ImportError:
    from study import ROOT, Study, caloric, wilson, rr_value, rr

ARTIFACT = Path(__file__).with_name('methane_nhexane_pt_boundary_reference.json')
PH_PATH = ROOT/'benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json'
M8_PATH = ROOT/'benchmarks/peng_robinson/methane_nhexane_pr_reference.json'
TARGETS = (1e-10,1e-11,3e-12,1e-12,3e-13,1e-13)
# A design margin for this NEW study, not a change to any inherited tolerance.
MAX_DOWNSTREAM_ALLOWANCE_FRACTION = .2  # >=5-fold margin on every inherited PH check


def compare(actual, expected, tolerances):
    checks = []
    def check(name,a,b,kind):
        t=tolerances[kind];error=abs(a-b);limit=t['atol']+t['rtol']*abs(b)
        checks.append(dict(quantity=name,actual=a,reference=b,absolute_error=error,
            allowed_error=limit,allowance_fraction=error/limit,passed=error<=limit))
    check('T',actual['T_K'],expected['T_K'],'T')
    check('beta',actual['beta'],expected['beta'],'beta')
    check('H_eq',actual['H_eq_J_mol'],expected['H_eq_J_mol'],'h')
    assert actual['classification']==expected['classification']
    for label,p in actual['phases'].items():
        q=expected['phases'][label]
        for i,(a,b) in enumerate(zip(p['composition'],q['composition'])):
            check(label+'.composition.'+caloric.COMPONENTS[i]['id'],a,b,'composition')
        check(label+'.Z',p['Z'],q['Z'],'Z')
        for name in ('h_ig_J_mol','h_res_J_mol','h_J_mol'):
            check(label+'.'+name,p[name],q[name],'h')
    return checks


def build():
    ph=json.loads(PH_PATH.read_text());m8=json.loads(M8_PATH.read_text());s=Study()
    bubble_case=next(c for c in ph['cases'] if c['case_id']=='PH_BUBBLE_ABOVE')
    dew_case=next(c for c in ph['cases'] if c['case_id']=='PH_DEW_BELOW')
    P=bubble_case['input']['P_Pa_abs'];z=bubble_case['input']['z']
    sat=s.oracle.flash.flash(P=P,VF=0.,zs=list(z))
    # P/VF locates the boundary. Refine the incipient condition S(T)=1 so the
    # NEW saturation composition meets the inherited equilibrium residual gate.
    boundary=brentq(lambda T:s.incipient_vapor(T,P,z)['S']-1.,sat.T-.01,sat.T+.01,
                    xtol=1e-12,rtol=1e-14)
    trial=s.incipient_vapor(boundary,P,z)
    liquid=s.phase_record(s.phase(boundary,P,z,'liquid'))
    incipient=s.phase_record(s.phase(boundary,P,trial['composition'],'vapor'))
    boundary_residual=[math.log(x)+lp-math.log(y)-vp for x,y,lp,vp in
        zip(z,incipient['composition'],liquid['ln_phi'],incipient['ln_phi'])]
    assert max(abs(v) for v in boundary_residual)<1e-11
    raw_residual=[math.log(x)+lp-math.log(y)-vp for x,y,lp,vp in
        zip(z,sat.gas.zs,sat.liquid0.lnphis(),sat.gas.lnphis())]
    boundary_evidence=dict(T_K=boundary,P_Pa_abs=P,z=z,
        method='Independent P/VF=0 location followed by stationary-vapor S(T)=1 Brent refinement',
        liquid=liquid,incipient_vapor=incipient,log_fugacity_residual=boundary_residual,
        stationary_trial=trial,
        raw_PVF_diagnostic=dict(T_K=sat.T,incipient_composition=sat.gas.zs,
            log_fugacity_residual=raw_residual,refinement_delta_T_K=boundary-sat.T,
            note='Unrefined phase composition is diagnostic, not an acceptance oracle'),
        note='Saturation/incipient-phase evidence, not finite vapor inventory or an exact-boundary classification gate')
    center=231.29921259842519
    matrix=[('BUBBLE_STABLE_231_10',231.10),('BUBBLE_MINUS_1MK',boundary-.001),
            ('BUBBLE_MINUS_0_1MK',boundary-.0001),('BUBBLE_PLUS_0_1MK',boundary+.0001),
            ('BUBBLE_PLUS_1MK',boundary+.001),('BUBBLE_231_15',231.15),
            ('BUBBLE_231_199',231.1992125984252),('BUBBLE_231_25',231.25),
            ('BUBBLE_CENTER',center),('BUBBLE_231_349',231.3492125984252),
            ('BUBBLE_231_399',231.39921259842518),('BUBBLE_231_45',231.45)]
    cases=[]
    for name,T in matrix:
        equilibrium=s.equilibrium(T,P,z);trial=s.incipient_vapor(T,P,z)
        K=wilson(T,P);tendency=rr(z,K)
        split=equilibrium['classification']=='vapor_liquid'
        assert (trial['tpd_RT']<0)==split
        restart=None
        if split:
            restart=s.successive_substitution(T,P,z,1e-12,trial['seed_K'])
            checks=compare(restart,equilibrium,ph['tolerances'])
            assert all(c['passed'] for c in checks),(name,[c for c in checks if not c['passed']])
        cases.append(dict(case_id=name,reference=equilibrium,stability_trial=trial,
            independent_homogeneous_stable=not split,Wilson_K=K,Wilson_RR=tendency,
            needs_stability_restart=split and not tendency['physical_interior_root'],
            stability_seed_experiment=restart))
    threshold=brentq(lambda T:rr_value(z,wilson(T,P),0.),231.35,231.45,xtol=1e-12,rtol=1e-14)
    dewT=dew_case['forward']['T_K'];P=dew_case['input']['P_Pa_abs'];z=dew_case['input']['z']
    dew=s.equilibrium(dewT,P,z)
    assert all(c['passed'] for c in compare(dew,dew_case['forward'],ph['tolerances']))
    # Slopes are diagnostic central differences, not new production derivatives.
    dt=.0001
    lower,upper=s.equilibrium(dewT-dt,P,z),s.equilibrium(dewT+dt,P,z)
    slopes=dict(H_eq_J_mol_K=(upper['H_eq_J_mol']-lower['H_eq_J_mol'])/(2*dt),
        h_liquid_J_mol_K=(upper['phases']['liquid']['h_J_mol']-lower['phases']['liquid']['h_J_mol'])/(2*dt),
        delta_T_K=dt)
    sensitivity=[]
    for tolerance in TARGETS:
        fixed=s.successive_substitution(dewT,P,z,tolerance)
        fixed_checks=compare(fixed,dew,ph['tolerances'])
        H_target=dew_case['input']['H_target_J_mol']
        evaluations=[]
        def local_residual(T):
            # This local sensitivity experiment is not a general PH implementation.
            independent=s.equilibrium(T,P,z)
            assert independent['classification']=='vapor_liquid'
            v=s.successive_substitution(T,P,z,tolerance)
            residual=v['H_eq_J_mol']-H_target
            evaluations.append(dict(T_K=T,H_residual_J_mol=residual,PT_iterations=v['iterations']))
            return residual
        recovered=brentq(local_residual,dewT-.001,dewT+.001,xtol=1e-12,rtol=1e-14)
        final=s.successive_substitution(recovered,P,z,tolerance)
        downstream=compare(final,dew_case['forward'],ph['tolerances'])
        H_residual=final['H_eq_J_mol']-H_target
        assert abs(H_residual)<=ph['tolerances']['H_residual']['atol']
        fraction=max(c['allowance_fraction'] for c in downstream)
        predicted_delta_T=-(fixed['H_eq_J_mol']-dew['H_eq_J_mol'])/slopes['H_eq_J_mol_K']
        sensitivity.append(dict(requested_log_fugacity_tolerance=tolerance,fixed_T_result=fixed,
            fixed_T_comparisons=fixed_checks,predicted_delta_T_K=predicted_delta_T,
            predicted_liquid_h_shift_J_mol=predicted_delta_T*slopes['h_liquid_J_mol_K'],
            local_H_matching=dict(description='Local PT accuracy propagation experiment, NOT production/general PH qualification',
                T_bracket_K=[dewT-.001,dewT+.001],evaluations=evaluations,result=final,
                H_target_J_mol=H_target,H_residual_J_mol=H_residual,comparisons=downstream,
                all_passed=all(c['passed'] for c in downstream),max_allowance_fraction=fraction,
                minimum_margin_factor=1/fraction)))
    recommended=next(row for row in sensitivity if row['local_H_matching']['max_allowance_fraction']<=MAX_DOWNSTREAM_ALLOWANCE_FRACTION)
    source_paths=[M8_PATH,PH_PATH,caloric.ARTIFACT,
        ROOT/'benchmarks/peng_robinson_caloric/reference.py',ROOT/'benchmarks/peng_robinson_caloric/equations.py',
        ROOT/'benchmarks/peng_robinson_ph/equilibrium.py']
    return dict(reference_id='independent_pr_pt_boundary@1.0',
        metadata=dict(component_order=[c['id'] for c in caloric.COMPONENTS],components=caloric.COMPONENTS,
            R_J_mol_K=caloric.R,PR_coefficients=[.45724,.07780],kij=caloric.KIJ,
            BIP_identity='methane_nhexane_explicit_zero@1.0',BIP_provenance=ph['metadata']['BIP_provenance'],
            caloric_reference=ph['metadata']['caloric_reference'],cp_data=caloric.CP_DATA,
            packages={p:importlib.metadata.version(p) for p in ['thermo','chemicals','fluids','numpy','scipy']},
            source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
            independence='Thermo EOS/caloric/stability and SciPy RR; no production imports',
            precision_experiment='Undamped log-fugacity SS; Wilson start at dew; stability seed at bubble; max 200 outer iterations',
            limitations=['Only equimolar methane/n_hexane, explicit zero kij, selected 6 MPa states',
                         'No production correction; M11 blocked; no exact-boundary finite-phase claim',
                         'No general near-critical, pure coexistence, water/VLLE or arbitrary-mixture qualification']),
        inherited_acceptance_tolerances=dict(M8=m8['acceptance_tolerances'],M10=caloric.TOLS,PH=ph['tolerances']),
        bubble_boundary=boundary_evidence,bubble_cases=cases,
        Wilson_no_root_region=dict(independent_bubble_T_K=boundary,Wilson_F0_zero_T_K=threshold,
            interpretation='Observed split region above independent bubble and below Wilson F0 sign change; endpoint equality is not a two-phase RR root'),
        dew_reference=dew,dew_source_case_id=dew_case['case_id'],dew_precision_study=sensitivity,
        local_sensitivity=slopes,recommendation=dict(high_accuracy_log_fugacity_tolerance=recommended['requested_log_fugacity_tolerance'],
            standard_log_fugacity_tolerance=1e-11,minimum_required_margin_factor=1/MAX_DOWNSTREAM_ALLOWANCE_FRACTION,
            observed_minimum_margin_factor=recommended['local_H_matching']['minimum_margin_factor'],
            fixed_T_iterations=recommended['fixed_T_result']['iterations'],
            scope='Recommendation for separately authorized M8.1 implementation/qualification; not an implemented production profile'))


def serialize(data):
    return json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Freeze only the NEW boundary artifact')
    args=parser.parse_args();data=build();text=serialize(data)
    if args.write:ARTIFACT.write_text(text)
    else:assert ARTIFACT.read_text()==text,'Frozen boundary evidence differs'
    print('Bubble boundary:',data['bubble_boundary']['T_K'],'K')
    for c in data['bubble_cases']:
        s=c['reference'];print(c['case_id'],s['T_K'],s['classification'],'beta',s['beta'],'Wilson',c['Wilson_RR']['status'])
    print('Dew study: tolerance | iterations | H_eq error J/mol | downstream min margin')
    for s in data['dew_precision_study']:
        d=s['fixed_T_result'];print(s['requested_log_fugacity_tolerance'],d['iterations'],
            d['H_eq_J_mol']-data['dew_reference']['H_eq_J_mol'],s['local_H_matching']['minimum_margin_factor'])
    print('Recommendation:',data['recommendation'])
    print('PASS: independent boundary and precision evidence reproduced; no production qualification')


if __name__=='__main__':main()
