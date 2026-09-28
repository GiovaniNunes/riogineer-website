"""Independent benchmark only. Never imported by the RioGineer production engine.

Thermo supplies EOS evaluation, roots, fugacity, Michelsen stability and PT flash.
This adapter sets constants, selects/scans states, exports results and checks them.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import math
from pathlib import Path
import platform
import sys

import numpy as np
from scipy.optimize import minimize_scalar
import teqp
import thermo
from thermo import PR, PRMIX, CEOSGas, CEOSLiquid, ChemicalConstantsPackage, PropertyCorrelationsPackage, FlashVL
from fluids.constants import R

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = Path(__file__).with_name('methane_nhexane_pr_reference.json')
IDS = ['methane', 'n_hexane']
DATASET = 'riogineer_components@1.0'
CONSTANTS = [
    dict(id='methane', MW_kg_kmol=16.0428, Tc_K=190.564, Pc_Pa_abs=4599200.0, omega=0.01142),
    dict(id='n_hexane', MW_kg_kmol=86.17536, Tc_K=507.82, Pc_Pa_abs=3044115.328359688, omega=0.3003189315498438),
]
Z = [0.5, 0.5]
KIJ = [[0.0, 0.0], [0.0, 0.0]]
T = 300.0
TOLS = {
    'alpha': dict(atol=1e-12, rtol=1e-11),
    'kappa': dict(atol=1e-13, rtol=1e-12),
    'a_i_Pa_m6_mol2': dict(atol=1e-12, rtol=1e-10),
    'b_i_m3_mol': dict(atol=1e-15, rtol=1e-10),
    'a_mix_Pa_m6_mol2': dict(atol=1e-12, rtol=1e-10),
    'b_mix_m3_mol': dict(atol=1e-15, rtol=1e-10),
    'A_B': dict(atol=1e-12, rtol=1e-10),
    'Z_roots': dict(atol=1e-10, rtol=1e-9),
    'ln_phi': dict(atol=1e-9, rtol=1e-9),
    'beta': dict(atol=1e-9, rtol=0.0),
    'x': dict(atol=1e-9, rtol=0.0),
    'y': dict(atol=1e-9, rtol=0.0),
    'composition_sum': dict(atol=1e-12, rtol=0.0),
    'material_reconstruction': dict(atol=1e-10, rtol=0.0),
    'ln_fugacity_equilibrium': dict(atol=1e-9, rtol=0.0),
    'rachford_rice': dict(atol=1e-10, rtol=0.0),
    'stability_TPD_negative_threshold': dict(atol=1e-9, rtol=0.0),
}


class SpecifiedCoefficients:
    """Configuration only: inherit every EOS/alpha/root/fugacity method unchanged.

    Thermo PRMIX uses c1R2_c2R and c2R in its optimized constructor;
    overriding c1/c2 alone would silently retain the wrong coefficients.
    """
    c1 = 0.45724
    c2 = 0.07780
    c1R2 = c1 * R * R
    c2R = c2 * R
    c1R2_c2R = c1 * R / c2


class BenchmarkPR(SpecifiedCoefficients, PR):
    """Keep any auxiliary pure-component calculation on the same coefficients."""


class BenchmarkPRMIX(SpecifiedCoefficients, PRMIX):
    eos_pure = BenchmarkPR


def dataset_check():
    # Read only the existing immutable data module, never any engine/EOS code.
    path = ROOT / 'engine/riogineer_engine/components.py'
    spec = importlib.util.spec_from_file_location('m7_benchmark_data', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.DATASET == DATASET
    for c in CONSTANTS:
        actual = module.component(c['id'])
        assert (actual.molecular_weight, actual.critical_temperature, actual.critical_pressure, actual.acentric_factor) == (c['MW_kg_kmol'], c['Tc_K'], c['Pc_Pa_abs'], c['omega'])
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_reference(kij=KIJ):
    kw = dict(Tcs=[c['Tc_K'] for c in CONSTANTS], Pcs=[c['Pc_Pa_abs'] for c in CONSTANTS],
              omegas=[c['omega'] for c in CONSTANTS], kijs=kij)
    constants = ChemicalConstantsPackage(Tcs=kw['Tcs'], Pcs=kw['Pcs'], omegas=kw['omegas'], MWs=[c['MW_kg_kmol'] for c in CONSTANTS])
    # No internal component lookup, vapor-pressure correlations or Cp data.
    correlations = PropertyCorrelationsPackage(constants=constants, skip_missing=True)
    gas = CEOSGas(BenchmarkPRMIX, kw, T=T, P=1e5, zs=Z)
    liquid = CEOSLiquid(BenchmarkPRMIX, kw, T=T, P=1e5, zs=Z)
    flash = FlashVL(constants, correlations, gas, liquid)
    flash.PT_SS_TOL = 1e-26  # library squared K-update criterion, not ln fugacity tolerance
    flash.PT_SS_MAXITER = 1000
    flash.PT_STABILITY_XTOL = 1e-12
    flash.PT_STABILITY_MAXITER = 1000
    return flash, kw


def eos_at(kw, temperature, pressure, composition):
    return BenchmarkPRMIX(**kw, T=temperature, P=pressure, zs=list(composition))


def phase_data(phase):
    return dict(composition=list(phase.zs), Z=phase.Z(), phi=phase.phis(), ln_phi=phase.lnphis())


def mixture_data(kw, temperature, pressure, composition):
    e = eos_at(kw, temperature, pressure, composition)
    # Thermo's volume solver returns 0 placeholders for absent/nonreal roots.
    roots = sorted(v*pressure/(R*temperature) for v in e.raw_volumes if v > e.b)
    A, B = e.a_alpha*pressure/(R*temperature)**2, e.b*pressure/(R*temperature)
    # Check all roots independently with the polynomial; do not implement a cubic solver.
    residuals = [r**3-(1-B)*r*r+(A-3*B*B-2*B)*r-(A*B-B*B-B**3) for r in roots]
    return dict(composition=list(composition), a_mix_Pa_m6_mol2=e.a_alpha, b_mix_m3_mol=e.b,
                A=A, B=B, physical_real_Z_roots=roots, smallest_real_root=roots[0], largest_real_root=roots[-1],
                cubic_polynomial_residuals=residuals)


def lowest_lnphis(kw, temperature, pressure, composition):
    e = eos_at(kw, temperature, pressure, composition)
    candidates = [getattr(e, name) for name in ('lnphis_l', 'lnphis_g') if hasattr(e, name)]
    return min(candidates, key=lambda lnphi: sum(z*v for z, v in zip(composition, lnphi)))


def tpd_scan(kw, temperature, pressure, reference_composition=Z):
    """Extra binary numerical evidence using library fugacities, not a flash solver.

    Scan the whole open composition interval plus endpoints, refine every grid
    local minimum with SciPy. The homogeneous reference is the minimum-G root.
    """
    reference = lowest_lnphis(kw, temperature, pressure, reference_composition)
    def tpd(x):
        zs = [float(x), float(1-x)]
        lp = lowest_lnphis(kw, temperature, pressure, zs)
        return sum(w*(math.log(w)+v-math.log(z)-ref) for w,v,z,ref in zip(zs,lp,reference_composition,reference))
    grid = np.unique(np.r_[np.linspace(1e-12,1-1e-12,1001), reference_composition[0]])
    values = [tpd(x) for x in grid]
    minima = [dict(methane_fraction=reference_composition[0], TPD_RT=tpd(reference_composition[0]))]
    for i in range(1,len(grid)-1):
        if values[i] <= values[i-1] and values[i] <= values[i+1]:
            sol = minimize_scalar(tpd, bounds=(grid[i-1],grid[i+1]), method='bounded', options={'xatol':1e-14})
            assert sol.success
            minima.append(dict(methane_fraction=float(sol.x), TPD_RT=float(sol.fun)))
    minima.extend([dict(methane_fraction=float(grid[i]),TPD_RT=float(values[i])) for i in (0,-1)])
    return dict(grid_points=len(grid), composition_interval=[1e-12,1-1e-12],
                grid_min_TPD_RT=min(values), refined_min_TPD_RT=min(m['TPD_RT'] for m in minima), minima=minima)


def stability(flash, kw, temperature, pressure):
    gas = flash.gas.to_TP_zs(T=temperature,P=pressure,zs=Z)
    liquid = flash.liquid.to_TP_zs(T=temperature,P=pressure,zs=Z)
    base = min([gas,liquid], key=lambda phase: phase.G_dep())
    other = liquid if base is gas else gas
    stable, details = flash.stability_test_Michelsen(temperature,pressure,Z,base,other)
    return dict(homogeneous_feed_stable=stable, michelsen_details=list(details),
                phase_identification_parameter=base.PIP(), binary_TPD_scan=tpd_scan(kw,temperature,pressure))


def build():
    assert R == 8.31446261815324
    assert thermo.__version__ == '0.6.0' and teqp.__version__ == '0.23.1'
    data_hash = dataset_check()
    flash, kw = make_reference()
    e = eos_at(kw,T,3e5,Z)
    pure = []
    for i,c in enumerate(CONSTANTS):
        # Read all reference parameters from the independent library.
        pure.append(dict(id=c['id'], kappa=e.kappas[i], alpha=e.a_alphas[i]/e.ais[i],
                         a_i_Pa_m6_mol2=e.a_alphas[i], b_i_m3_mol=e.bs[i]))
        # Verify both independent pure and mixture evaluators use the same configuration.
        standalone = BenchmarkPR(Tc=c['Tc_K'],Pc=c['Pc_Pa_abs'],omega=c['omega'],T=T,P=3e5)
        assert math.isclose(standalone.a_alpha, e.a_alphas[i], rel_tol=1e-14)
        assert standalone.b == e.bs[i]
        # Verify coefficient override against the requested definition.
        alpha = (1+(.37464+1.54226*c['omega']-.26992*c['omega']**2)*(1-math.sqrt(T/c['Tc_K'])))**2
        assert math.isclose(e.a_alphas[i], .45724*R*R*c['Tc_K']**2/c['Pc_Pa_abs']*alpha, rel_tol=1e-14)
        assert math.isclose(e.bs[i], .07780*R*c['Tc_K']/c['Pc_Pa_abs'],rel_tol=1e-14)
    scan = []
    for p in [1e3,1e4,3e4,1e5,2e5,3e5,5e5,1e6,5e6,1e7,2e7,3e7,5e7]:
        r = flash.flash(T=T,P=p,zs=Z)
        scan.append(dict(T_K=T,P_Pa_abs=p,phase=r.phase,beta=r.VF))
    bounds = {label: flash.flash(T=T,VF=vf,zs=Z).P for label,vf in [('bubble_pressure_Pa_abs',0),('dew_pressure_Pa_abs',1)]}
    cases = []
    for case_id,p,classification in [('A',3e7,'liquid'),('B',3e5,'vapor_liquid'),('C',1e3,'vapor')]:
        r = flash.flash(T=T,P=p,zs=Z)
        assert r.phase == dict(liquid='L',vapor_liquid='VL',vapor='V')[classification]
        case = dict(case_id=case_id,T_K=T,P_Pa_abs=p,z=Z,kij=KIJ,classification=classification,
                    beta=r.VF,liquid_fraction=1-r.VF,convergence=r.flash_convergence,
                    homogeneous_mixture=mixture_data(kw,T,p,Z),stability=stability(flash,kw,T,p))
        case['neighborhood'] = []
        for dt in [-5.,0.,5.]:
            for factor in [.8,1.,1.2]:
                near = flash.flash(T=T+dt,P=p*factor,zs=Z)
                assert near.phase == r.phase
                case['neighborhood'].append(dict(T_K=T+dt,P_Pa_abs=p*factor,phase=near.phase,beta=near.VF))
        if r.gas is not None: case['vapor'] = phase_data(r.gas)
        if r.liquids: case['liquid'] = phase_data(r.liquid0)
        if classification == 'vapor_liquid':
            x,y = r.liquid0.zs,r.gas.zs
            ks = [yi/xi for xi,yi in zip(x,y)]
            residuals = [math.log(xi)+pl-math.log(yi)-pv for xi,yi,pl,pv in zip(x,y,r.liquid0.lnphis(),r.gas.lnphis())]
            case['equilibrium_common_tangent_TPD'] = tpd_scan(kw,T,p,x)
            case.update(K=ks, mixture_at_x=mixture_data(kw,T,p,x), mixture_at_y=mixture_data(kw,T,p,y),
                material_residual=[(1-r.VF)*xi+r.VF*yi-zi for xi,yi,zi in zip(x,y,Z)],
                ln_fugacity_residual=residuals,
                rachford_rice_residual=sum(zi*(k-1)/(1+r.VF*(k-1)) for zi,k in zip(Z,ks)),
                Wilson_initial_K=[math.exp(math.log(c['Pc_Pa_abs']/p)+5.373*(1+c['omega'])*(1-c['Tc_K']/T)) for c in CONSTANTS])
            # Solver precision study: independent library at ordinary/tighter tolerances.
            flash.PT_SS_TOL=1e-18
            looser=flash.flash(T=T,P=p,zs=Z)
            case['precision_study'] = dict(looser_squared_K_tolerance=1e-18,
                beta_difference=looser.VF-r.VF, x_difference=[a-b for a,b in zip(looser.liquid0.zs,x)],
                y_difference=[a-b for a,b in zip(looser.gas.zs,y)])
            flash.PT_SS_TOL=1e-26
        cases.append(case)
    # Explicit BIP plumbing check, not an additional primary acceptance case.
    alternate, _ = make_reference([[0.,.02],[.02,0.]])
    alt = alternate.flash(T=T,P=3e5,zs=Z)
    # Record why the installed teqp default was not used for the requested rounded coefficients.
    teqp_meta = teqp.canonical_PR(kw['Tcs'],kw['Pcs'],kw['omegas'],KIJ).get_meta()
    assert teqp_meta['OmegaA'] != .45724 and teqp_meta['OmegaB'] != .07780
    functions = {'PRMIX_constructor':PRMIX.__init__,'PRMIX_fugacity':PRMIX.fugacity_coefficients,
                 'FlashVL_stability':FlashVL.stability_test_Michelsen,'FlashVL_PT_stability':FlashVL.flash_TP_stability_test}
    versions = {name:importlib.metadata.version(name) for name in ['thermo','chemicals','fluids','numpy','scipy','teqp','pandas']}
    result = dict(benchmark_id='pre_m8_methane_nhexane_canonical_pr@1.0',component_dataset=DATASET,
        component_order=IDS,components=CONSTANTS,z=Z,kij=KIJ,
        formulation=dict(name='Peng-Robinson',OmegaA=.45724,OmegaB=.07780,R_J_mol_K=R,
            kappa_coefficients=[.37464,1.54226,-.26992],mixing='classical quadratic a with sqrt(ai*aj)*(1-kij); linear b',
            units=dict(a='Pa m6/mol2',b='m3/mol',temperature='K',pressure='Pa absolute',composition='mol/mol')),
        independent_reference=dict(primary='thermo',versions=versions,python=platform.python_version(),
            component_source_sha256=data_hash,configuration='BenchmarkPRMIX: coefficient attributes only; all methods inherited',
            PT_SS_TOL=1e-26,PT_STABILITY_XTOL=1e-12,teqp_default_not_used=teqp_meta,
            source_sha256={name:hashlib.sha256(inspect.getsource(fn).encode()).hexdigest() for name,fn in functions.items()}),
        phase_scan=scan,saturation_at_300K=bounds,pure_parameters=dict(T_K=T,components=pure),cases=cases,
        optional_nonzero_kij=dict(kij=[[0.,.02],[.02,0.]],T_K=T,P_Pa_abs=3e5,beta=alt.VF,x=alt.liquid0.zs,y=alt.gas.zs),
        acceptance_tolerances=TOLS)
    validate(result)
    return result


def validate(data):
    dataset_check()
    assert data['components'] == CONSTANTS and data['component_dataset'] == DATASET
    assert data['z'] == Z and data['kij'] == KIJ
    def finite(value):
        if isinstance(value,float): assert math.isfinite(value)
        if isinstance(value,dict):
            for v in value.values(): finite(v)
        if isinstance(value,list):
            for v in value: finite(v)
    finite(data)
    assert [c['classification'] for c in data['cases']] == ['liquid','vapor_liquid','vapor']
    for c in data['cases']:
        assert abs(sum(c['z'])-1)<1e-12
        for phase in ('liquid','vapor'):
            if phase in c:
                assert abs(sum(c[phase]['composition'])-1)<1e-12
                assert all(v>0 for v in c[phase]['phi'])
                assert all(abs(math.log(p)-lp)<1e-12 for p,lp in zip(c[phase]['phi'],c[phase]['ln_phi']))
        split = c['classification']=='vapor_liquid'
        assert c['stability']['homogeneous_feed_stable'] is (not split)
        tpd=c['stability']['binary_TPD_scan']['refined_min_TPD_RT']
        assert tpd < -1e-3 if split else tpd >= -1e-9
        assert all(n['phase']==dict(liquid='L',vapor_liquid='VL',vapor='V')[c['classification']] for n in c['neighborhood'])
        if split:
            x,y=c['liquid']['composition'],c['vapor']['composition']; beta=c['beta']
            assert 0.1 < beta < 0.9
            assert c['equilibrium_common_tangent_TPD']['refined_min_TPD_RT'] >= -1e-9
            assert all(abs(k-yi/xi)<1e-12 for k,xi,yi in zip(c['K'],x,y))
            assert max(abs((1-beta)*xi+beta*yi-zi) for xi,yi,zi in zip(x,y,Z)) < 1e-12
            assert max(abs(math.log(xi)+pl-math.log(yi)-pv) for xi,yi,pl,pv in zip(x,y,c['liquid']['ln_phi'],c['vapor']['ln_phi'])) < 1e-11
            assert abs(sum(zi*(k-1)/(1+beta*(k-1)) for zi,k in zip(Z,c['K']))) < 1e-12
            assert len(c['mixture_at_x']['physical_real_Z_roots']) == 3
            assert abs(c['liquid']['Z']-c['mixture_at_x']['smallest_real_root'])<1e-12
            assert abs(c['vapor']['Z']-c['mixture_at_y']['largest_real_root'])<1e-12
            for key in ['homogeneous_mixture','mixture_at_x','mixture_at_y']:
                assert max(abs(v) for v in c[key]['cubic_polynomial_residuals'])<1e-12
    assert abs(data['optional_nonzero_kij']['beta']-data['cases'][1]['beta'])>1e-6


def compare(saved, fresh, path=''):
    """Reproduction check; source/reference inputs and text match exactly."""
    if isinstance(saved,dict):
        assert saved.keys()==fresh.keys(),path
        for key in saved: compare(saved[key],fresh[key],path+'/'+key)
    elif isinstance(saved,list):
        assert len(saved)==len(fresh),path
        for i,(a,b) in enumerate(zip(saved,fresh)): compare(a,b,path+'/'+str(i))
    elif isinstance(saved,float):
        # Binary TPD minimizer coordinates are less conditioned than flash outputs.
        tol=1e-7 if 'methane_fraction' in path else 1e-10
        assert math.isclose(saved,fresh,abs_tol=tol,rel_tol=1e-10),(path,saved,fresh)
    else: assert saved==fresh,(path,saved,fresh)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Explicitly regenerate frozen reference JSON')
    args=parser.parse_args()
    output=build()
    if args.write:
        ARTIFACT.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
        print('Wrote',ARTIFACT.relative_to(ROOT))
    else:
        saved=json.loads(ARTIFACT.read_text()); validate(saved); compare(saved,output)
        print('PASS: frozen artifact, exact component data, three robust phases, library reproduction and equilibrium checks')
