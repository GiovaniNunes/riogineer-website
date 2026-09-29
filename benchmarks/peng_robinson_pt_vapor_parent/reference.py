"""Independent vapor-parent restart qualification; no production imports.

Thermo supplies stationary stability and a separate full PT equilibrium.
The unchanged Pre-M8.1 experiment supplies physical RR and fugacity updates.
Reproduction reads the committed reference; --write creates this study only.
"""
import argparse
import hashlib
import inspect
import json
import math
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmarks.peng_robinson_pt_boundary.study import (
    Study, rr, rr_value, wilson, stability_iteration_Michelsen,
)

HERE = Path(__file__).resolve().parent
FROZEN = HERE / 'methane_nhexane_pt_vapor_parent_reference.json'
TEMPERATURES = [220., 224., 225.98425196850394, 228.3464566929134,
                230.70866141732284, 233.07086614173227, 233.2,
                233.234, 233.2341, 233.2342, 233.235, 234., 240.]
ORIGINAL = TEMPERATURES[2:6]
Z = [.5, .5]
P = 1000.


def orientation(parent_pip, trial_pip):
    if not all(math.isfinite(v) for v in (parent_pip, trial_pip)):
        raise ValueError('Finite phase identification parameters required')
    if parent_pip < 1 < trial_pip:
        return 'vapor_parent_liquid_trial'
    if trial_pip < 1 < parent_pip:
        return 'liquid_parent_vapor_trial'
    raise ValueError('Opposed unambiguous EOS phase identities required')


def seed(z, w, S, identity):
    if (len(z) != 2 or len(w) != 2 or
        not all(math.isfinite(v) and v > 0 for v in [*z, *w, S]) or
        abs(sum(z)-1) > 1e-12 or abs(sum(w)-1) > 1e-12):
        raise ValueError('Normalized positive binary compositions and finite positive S required')
    if identity == 'vapor_parent_liquid_trial':
        return [zi/(S*wi) for zi, wi in zip(z, w)]
    if identity == 'liquid_parent_vapor_trial':
        return [S*wi/zi for zi, wi in zip(z, w)]
    raise ValueError('Unsupported orientation')


def restart_required(unstable, identity, wilson_rr):
    if identity not in ('vapor_parent_liquid_trial', 'liquid_parent_vapor_trial'):
        raise ValueError('Unsupported orientation')
    return unstable and not wilson_rr['physical_interior_root']


def trial(s, T):
    parent = s.phase(T, P, Z, 'vapor')
    parent_ln = parent.lnphis_lowest_Gibbs()
    assert max(abs(a-b) for a,b in zip(parent_ln, parent.lnphis())) < 1e-12
    raw = [zi/ki for zi,ki in zip(Z,wilson(T,P))]
    calls = []
    def liquid_trial(q):
        # Fresh EOS instance selects the actual minimum-G root at each composition.
        # Avoid a gas-only cached lnphis_at_zs path that can return the trivial trial.
        calls.append(list(q))
        return s.phase(T,P,q,'liquid').lnphis_lowest_Gibbs()
    result = stability_iteration_Michelsen(
        T,P,list(Z),parent.fugacities_lowest_Gibbs(),
        [v/sum(raw) for v in raw],liquid_trial,maxiter=1000,xtol=1e-24)
    w = list(result[2])
    liquid = s.phase(T,P,w,'liquid')
    ln_trial = liquid.lnphis_lowest_Gibbs()
    assert max(abs(a-b) for a,b in zip(ln_trial,liquid.lnphis())) < 1e-12
    W = [zi*math.exp(a-b) for zi,a,b in zip(Z,parent_ln,ln_trial)]
    S = sum(W)
    tpd = sum(wi*(math.log(wi)+a-math.log(zi)-b)
              for wi,zi,a,b in zip(w,Z,ln_trial,parent_ln))
    error = max(abs(wi-Wi/S) for wi,Wi in zip(w,W))
    assert error < 1e-11 and abs(tpd+math.log(S)) < 1e-11
    identity = orientation(parent.PIP(),liquid.PIP())
    K = seed(Z,w,S,identity)
    direct = [math.exp(a-b) for a,b in zip(ln_trial,parent_ln)]
    assert max(abs(a/b-1) for a,b in zip(K,direct)) < 1e-11
    normalized = [zi/wi for zi,wi in zip(Z,w)]
    return dict(parent_composition=Z,trial_composition=w,unnormalized_W=W,S=S,
                tpd_RT=tpd,stationarity_error=error,iterations=len(calls),
                parent_phi=[math.exp(v) for v in parent_ln],
                trial_phi=[math.exp(v) for v in ln_trial],
                parent_PIP=parent.PIP(),trial_PIP=liquid.PIP(),orientation=identity,
                library_sum=result[0],library_trial_parent_ratios=result[1],
                derived_K=K,direct_fugacity_K=direct,derived_RR=rr(Z,K),
                normalized_only_K=normalized,
                normalized_only_RR=dict(F0=rr_value(Z,normalized,0.),
                    F1=rr_value(Z,normalized,1.),beta=1.,
                    physical_interior_root=False,status='analytic_vapor_endpoint'),
                Wilson_K=wilson(T,P),Wilson_RR=rr(Z,wilson(T,P)))


def compare(actual, expected):
    """Unchanged inherited PH state allowances; M8 fugacity/material gates."""
    errors = {}
    def close(name,a,b,atol,rtol):
        error = abs(a-b); allowed = atol+rtol*abs(b)
        if error > allowed:
            raise AssertionError(f'{name}: {a} vs {b}; error {error} > {allowed}')
        errors[name] = dict(error=error,allowance=allowed)
    assert actual['classification'] == expected['classification']
    close('beta',actual['beta'],expected['beta'],1e-9,1e-9)
    for label,ref in expected['phases'].items():
        got = actual['phases'][label]
        for i,(a,b) in enumerate(zip(got['composition'],ref['composition'])):
            close(f'{label}.q{i}',a,b,1e-9,1e-9)
        close(label+'.Z',got['Z'],ref['Z'],1e-10,1e-9)
        for i,(a,b) in enumerate(zip(got['ln_phi'],ref['ln_phi'])):
            close(f'{label}.lnphi{i}',a,b,1e-9,1e-9)
    if expected['final_K']:
        for i,(a,b) in enumerate(zip(actual['final_K'],expected['final_K'])):
            x=expected['phases']['liquid']['composition'][i]
            y=expected['phases']['vapor']['composition'][i]
            dx=1e-9+1e-9*abs(x); dy=1e-9+1e-9*abs(y)
            allowed=max((y+dy)/(x-dx)-b,b-(y-dy)/(x+dx))
            close(f'K{i}',a,b,allowed,0)
    assert max(map(abs,actual['material_reconstruction_residual'])) <= 1e-10
    assert max(map(abs,actual['log_fugacity_residual']),default=0) <= 1e-9
    return errors


def build():
    s = Study(); cases = []
    phpath=ROOT/'benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json'
    ph=json.loads(phpath.read_text())
    scan=next(c for c in ph['cases'] if c['case_id']=='PH_C_SINGLE_VAPOR')['inverse']['diagnostics']['scan']
    for T in TEMPERATURES:
        evidence=trial(s,T); eq=s.equilibrium(T,P,Z)
        unstable=evidence['tpd_RT'] < 0
        assert unstable == (eq['classification']=='vapor_liquid')
        fire=restart_required(unstable,evidence['orientation'],evidence['Wilson_RR'])
        runs={}
        if unstable:
            assert evidence['derived_RR']['physical_interior_root']
            for name,tol in [('standard',1e-11),('high_accuracy',1e-12)]:
                run=s.successive_substitution(T,P,Z,tol,evidence['derived_K'])
                assert run['iterations'] <= 100
                run['comparison']=compare(run,eq)
                runs[name]=run
        if T in ORIGINAL:
            old=next(row for row in scan if row['T_K']==T)
            assert abs(eq['beta']-old['beta']) <= 1e-9+1e-9*abs(old['beta'])
        cases.append(dict(case_id=f'T_{T}',original_failure=T in ORIGINAL,
                          stability=evidence,independent_equilibrium=eq,
                          restart_required=fire,precision_experiments=runs))
    paths=['benchmarks/peng_robinson_pt_boundary/study.py',
           'benchmarks/peng_robinson_ph/equilibrium.py',
           'benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json',
           'benchmarks/peng_robinson_caloric/reference.py']
    return dict(identity='independent_pr_pt_vapor_parent_restart@1.0',
                components=['methane','n_hexane'],P_Pa_abs=P,z=Z,
                inherited_constants={k:ph['metadata'][k] for k in
                    ['R_J_mol_K','component_constant_identity','components',
                     'caloric_convention_identity','omega_a','omega_b']},
                inherited_PH_tolerances=ph['tolerances'],
                kij=[[0.,0.],[0.,0.]],BIP_provenance='Explicit zero-kij independent M8 benchmark; not fitted physical interaction data',
                dependencies={k:version(k) for k in ['thermo','chemicals','fluids','numpy','scipy']},
                input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
                Michelsen_source_sha256=hashlib.sha256(inspect.getsource(stability_iteration_Michelsen).encode()).hexdigest(),
                cases=cases)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true')
    args=parser.parse_args(); result=build()
    serialized=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.write:
        FROZEN.write_text(serialized)
    else:
        assert serialized == FROZEN.read_text(), 'Frozen independent reproduction mismatch'
    for c in result['cases']:
        t=c['stability']; e=c['independent_equilibrium']; runs=c['precision_experiments']
        print(f"T={e['T_K']:.14g} {e['classification']} beta={e['beta']:.16g} "
              f"S={t['S']:.12g} Wilson={t['Wilson_RR']['status']} restart={c['restart_required']} "
              f"iterations={[(k,v['iterations']) for k,v in runs.items()]}")
    print(f"PASS: {len(result['cases'])} independent states; exact frozen reproduction")

if __name__ == '__main__':
    main()
