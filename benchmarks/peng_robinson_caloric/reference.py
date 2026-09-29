"""Independent pre-M10 caloric reference. No production EOS/caloric imports.

Default command reproduces and checks the frozen JSON. --write is explicit.
Thermo provides the primary results; equations.py supplies the second evidence.
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

from thermo import (PR, PRMIX, CEOSGas, CEOSLiquid, HeatCapacityGas,
                    ChemicalConstantsPackage, PropertyCorrelationsPackage, FlashVL)
from chemicals import heat_capacity as hc
from fluids.constants import R as LIBRARY_R
from scipy.integrate import quad

if __package__:
    from . import equations as eq
else:
    import equations as eq

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = Path(__file__).with_name('methane_nhexane_pr_caloric_reference.json')
M8_PATH = ROOT/'benchmarks/peng_robinson/methane_nhexane_pr_reference.json'
M8 = json.loads(M8_PATH.read_text())
R = eq.R
COMPONENTS = [
    dict(id='methane', MW_kg_kmol=16.0428, Tc_K=190.564, Pc_Pa_abs=4599200.0, omega=0.01142),
    dict(id='n_hexane', MW_kg_kmol=86.17536, Tc_K=507.82, Pc_Pa_abs=3044115.328359688, omega=0.3003189315498438),
]
CP_DATA = [
    dict(id='methane', CAS='74-82-8', coefficients=[4.568, -.008975, 3.631e-5, -3.407e-8, 1.091e-11], Tmin_K=50., Tmax_K=1000.),
    dict(id='n_hexane', CAS='110-54-3', coefficients=[8.831, -.000166, .00014302, -1.8314e-7, 7.124e-11], Tmin_K=200., Tmax_K=1000.),
]
KIJ = [[0., 0.], [0., 0.]]
Z_FEED = [.5, .5]
TOLS = {
    'Cp': dict(atol=1e-10, rtol=1e-12),
    'alpha': dict(atol=1e-13, rtol=1e-12),
    'dalpha_dT': dict(atol=1e-15, rtol=1e-11),
    'a': dict(atol=1e-13, rtol=1e-12),
    'da_dT': dict(atol=1e-13, rtol=1e-10),
    'b': dict(atol=1e-16, rtol=1e-12),
    'Z': dict(atol=1e-10, rtol=1e-9),
    'h_ig': dict(atol=1e-7, rtol=1e-11),
    's_ig': dict(atol=1e-9, rtol=1e-11),
    'h_res': dict(atol=1e-7, rtol=1e-11),
    's_res': dict(atol=1e-9, rtol=1e-11),
    'h_total': dict(atol=1e-7, rtol=1e-11),
    's_total': dict(atol=1e-9, rtol=1e-11),
}
MATRIX = [('A',300.,3e7,'L'), ('B',300.,3e5,'VL'), ('C',300.,1e3,'V')]
for temperature, split_p in [(280.,3e5), (350.,1e6), (400.,3e6)]:
    MATRIX.extend([(f'T{int(temperature)}_L',temperature,3e7,'L'),
                   (f'T{int(temperature)}_VL',temperature,split_p,'VL'),
                   (f'T{int(temperature)}_V',temperature,1e3,'V')])


class SpecifiedCoefficients:
    # Configuration only, including optimized Thermo constructor products.
    c1, c2 = .45724, .07780
    c1R2, c2R, c1R2_c2R = c1*R*R, c2*R, c1*R/c2


class BenchmarkPR(SpecifiedCoefficients, PR):
    pass


class BenchmarkPRMIX(SpecifiedCoefficients, PRMIX):
    eos_pure = BenchmarkPR


def molar_to_mass(value, mw_kg_kmol):
    """J/mol -> J/kg, or J/(mol K) -> J/(kg K)."""
    if not math.isfinite(mw_kg_kmol) or mw_kg_kmol <= 0:
        raise ValueError('Molecular weight must be positive and finite')
    kg_per_mol = mw_kg_kmol / 1000.0
    return value / kg_per_mol


def molar_enthalpy_flow(F_kmol_h, h_J_mol):
    return F_kmol_h * 1000.0 / 3600.0 * h_J_mol


def mass_enthalpy_flow(m_kg_h, h_J_kg):
    return m_kg_h / 3600.0 * h_J_kg


def reference_shift_checks(cases):
    b = next(c for c in cases if c['case_id'] == 'B')
    l, v, beta = b['phases']['liquid'], b['phases']['vapor'], b['beta']
    c = 12345.0
    difference = (v['h_total_J_mol']+c)-(l['h_total_J_mol']+c)
    close(difference, b['phase_difference_h_J_mol'], 'h_total')
    shifts = [10000.0, -3000.0]
    inlet_shift = sum(z*d for z,d in zip(Z_FEED,shifts))
    phase_shifts = [sum(z*d for z,d in zip(p['composition'],shifts)) for p in (l,v)]
    outlet_shift = (1-beta)*phase_shifts[0]+beta*phase_shifts[1]
    flow_error = molar_enthalpy_flow(1000.0,outlet_shift-inlet_shift)
    assert abs(flow_error) < 1e-6
    low = next(c for c in cases if c['case_id']=='T280_V')['phases']['vapor']['h_total_J_mol']
    high = next(c for c in cases if c['case_id']=='T400_V')['phases']['vapor']['h_total_J_mol']
    close((high+c)-(low+c),high-low,'h_total')
    return dict(common_shift_J_mol=c,phase_difference_after_common_shift_J_mol=difference,
        same_composition_temperature_difference_J_mol=high-low,
        temperature_difference_after_common_shift_J_mol=(high+c)-(low+c),
        component_shifts_J_mol=shifts,feed_shift_J_mol=inlet_shift,
        phase_shifts_J_mol=phase_shifts,weighted_outlet_shift_J_mol=outlet_shift,
        enthalpy_flow_difference_shift_error_W=flow_error,
        phase_difference_change_under_component_shifts_J_mol=phase_shifts[1]-phase_shifts[0])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(actual, expected, quantity):
    t = TOLS[quantity]
    assert math.isfinite(actual) and math.isfinite(expected), (quantity, actual, expected)
    assert abs(actual-expected) <= t['atol']+t['rtol']*abs(expected), (quantity, actual, expected)


def dataset_check():
    path = ROOT/'engine/riogineer_engine/components.py'
    spec = importlib.util.spec_from_file_location('pre_m10_component_data_only', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.DATASET == 'riogineer_components@1.0'
    assert COMPONENTS == M8['components']
    assert R == LIBRARY_R == M8['formulation']['R_J_mol_K']
    for c in COMPONENTS:
        actual = module.component(c['id'])
        assert (actual.molecular_weight, actual.critical_temperature, actual.critical_pressure, actual.acentric_factor) == (
            c['MW_kg_kmol'], c['Tc_K'], c['Pc_Pa_abs'], c['omega'])
    return sha(path)


def cp_models():
    models = []
    for d in CP_DATA:
        row = hc.Cp_data_Poling.loc[d['CAS']]
        assert [float(row[f'a{i}']) for i in range(5)] == d['coefficients']
        assert (float(row['Tmin']), float(row['Tmax'])) == (d['Tmin_K'], d['Tmax_K'])
        cp = HeatCapacityGas(CASRN=d['CAS'], method='POLING_POLY', extrapolation=None)
        assert cp.T_limits[cp.method] == (d['Tmin_K'], d['Tmax_K'])
        models.append(cp)
    return models


def require_cp_domain(T, reference=eq.T_REF):
    if not all(math.isfinite(v) and all(c['Tmin_K'] <= v <= c['Tmax_K'] for c in CP_DATA) for v in (T, reference)):
        raise ValueError('Temperature/integration reference outside joint Cp validity; no extrapolation')


def make_reference():
    cp = cp_models()
    kw = dict(Tcs=[c['Tc_K'] for c in COMPONENTS], Pcs=[c['Pc_Pa_abs'] for c in COMPONENTS],
              omegas=[c['omega'] for c in COMPONENTS], kijs=KIJ)
    constants = ChemicalConstantsPackage(**{k: kw[k] for k in ('Tcs','Pcs','omegas')}, MWs=[c['MW_kg_kmol'] for c in COMPONENTS])
    correlations = PropertyCorrelationsPackage(constants=constants, HeatCapacityGases=cp, skip_missing=True)
    phases = [cls(BenchmarkPRMIX, kw, HeatCapacityGases=cp, T=300., P=1e5, zs=Z_FEED) for cls in (CEOSGas,CEOSLiquid)]
    for phase in phases:
        assert (phase.T_REF_IG, phase.P_REF_IG) == (eq.T_REF, eq.P_REF)
    flash = FlashVL(constants, correlations, phases[0], phases[1])
    flash.PT_SS_TOL, flash.PT_SS_MAXITER = 1e-26, 1000
    flash.PT_STABILITY_XTOL, flash.PT_STABILITY_MAXITER = 1e-12, 1000
    return flash, kw, cp


def library_phase(T, P, q, label, kw, cp):
    require_cp_domain(T)
    cls = CEOSLiquid if label == 'liquid' else CEOSGas
    return cls(BenchmarkPRMIX, kw, HeatCapacityGases=cp, T=T, P=P, zs=list(q))


def phase_record(T, P, q, label, kw, cp, frozen_Z=None):
    p = library_phase(T,P,q,label,kw,cp)
    e = p.eos_mix
    z = p.Z()
    if frozen_Z is not None:
        close(z,frozen_Z,'Z')
    # Store library results. Direct equations only audit them, never replace them.
    ideal = eq.ideal(T,P,q,CP_DATA)
    pure, a, da, b = eq.parameters(T,q,COMPONENTS,KIJ)
    hr, sr = eq.departures(T,P,z,a,da,b)
    lib = dict(Cp_ig_J_mol_K=p.Cp_ideal_gas(), h_ig_J_mol=p.H_ideal_gas(), s_ig_J_mol_K=p.S_ideal_gas(),
               h_res_J_mol=p.H_dep(), s_res_J_mol_K=p.S_dep(), h_total_J_mol=p.H(), s_total_J_mol_K=p.S())
    direct = dict(ideal, h_res_J_mol=hr, s_res_J_mol_K=sr,
                  h_total_J_mol=ideal['h_ig_J_mol']+hr, s_total_J_mol_K=ideal['s_ig_J_mol_K']+sr)
    quantity = dict(zip(lib, ('Cp','h_ig','s_ig','h_res','s_res','h_total','s_total')))
    for key in lib:
        close(lib[key],direct[key],quantity[key])
    for i, d in enumerate(pure):
        close(e.a_alphas[i]/e.ais[i], d['alpha'], 'alpha')
        close(e.da_alpha_dTs[i]/e.ais[i], d['dalpha_dT_K_inv'], 'dalpha_dT')
        close(e.a_alphas[i], d['a_i_Pa_m6_mol2'], 'a')
        close(e.da_alpha_dTs[i], d['da_i_dT_Pa_m6_mol2_K'], 'da_dT')
    close(e.a_alpha,a,'a'); close(e.da_alpha_dT,da,'da_dT'); close(e.b,b,'b')
    mw = sum(v*c['MW_kg_kmol'] for v,c in zip(q,COMPONENTS))
    gibbs = R*T*sum(v*phi for v,phi in zip(q,p.lnphis()))
    close(lib['h_res_J_mol']-T*lib['s_res_J_mol_K'],gibbs,'h_res')
    # Fixed-composition, fixed-P derivative identities; auxiliary evidence only.
    dt = .01
    plus, minus = [library_phase(t,P,q,label,kw,cp) for t in (T+dt,T-dt)]
    dsdt = (plus.S_dep()-minus.S_dep())/(2*dt)
    dhdt = (plus.H_dep()-minus.H_dep())/(2*dt)
    identity = dhdt-T*dsdt
    assert abs(identity) < 2e-5, ('dHres/dT=T dSres/dT',identity)
    # Analytic da remains the primary reference; finite difference is cross-check.
    fd_da = (plus.eos_mix.a_alpha-minus.eos_mix.a_alpha)/(2*dt)
    assert math.isclose(fd_da,e.da_alpha_dT,rel_tol=1e-8,abs_tol=1e-11)
    return dict(T_K=T,P_Pa_abs=P,composition=list(q),phase=label,Z=z,
        frozen_M8_Z=frozen_Z, mixture_MW_kg_kmol=mw, mixture_MW_kg_mol=mw/1000,
        pure_parameters=[dict(id=c['id'],alpha=e.a_alphas[i]/e.ais[i],dalpha_dT_K_inv=e.da_alpha_dTs[i]/e.ais[i],
            a_i_Pa_m6_mol2=e.a_alphas[i],da_i_dT_Pa_m6_mol2_K=e.da_alpha_dTs[i],b_i_m3_mol=e.bs[i]) for i,c in enumerate(COMPONENTS)],
        a_mix_Pa_m6_mol2=e.a_alpha,da_mix_dT_Pa_m6_mol2_K=e.da_alpha_dT,b_mix_m3_mol=e.b,
        A=e.a_alpha*P/(R*T)**2,B=e.b*P/(R*T),**lib,
        departure_intermediates=dict(T_da_minus_a_Pa_m6_mol2=T*e.da_alpha_dT-e.a_alpha,
            PR_log_term=math.log1p(2*math.sqrt(2)*e.b*P/(R*T)/(z+(1-math.sqrt(2))*e.b*P/(R*T))),
            ln_Z_minus_B=math.log(z-e.b*P/(R*T))),
        ideal_entropy_terms={key:value for key,value in ideal.items() if key.startswith('s_ig_') and key != 's_ig_J_mol_K'},
        h_total_J_kg=molar_to_mass(lib['h_total_J_mol'],mw),s_total_J_kg_K=molar_to_mass(lib['s_total_J_mol_K'],mw),
        direct_equation_comparison=dict(reference=direct,library_minus_direct={key:lib[key]-direct[key] for key in lib}),
        consistency=dict(g_res_from_fugacity_J_mol=gibbs,g_res_identity_error_J_mol=lib['h_res_J_mol']-T*lib['s_res_J_mol_K']-gibbs,
            finite_difference_step_K=dt,da_mix_dT_finite_difference=fd_da,
            dHres_dT_minus_T_dSres_dT_J_mol_K=identity))


def build():
    component_hash=dataset_check()
    flash,kw,cp=make_reference()
    cases=[]
    for identifier,T,P,expected in MATRIX:
        solved=flash.flash(T=T,P=P,zs=Z_FEED)
        assert solved.phase == expected, (identifier,solved.phase)
        record=dict(case_id=identifier,T_K=T,P_Pa_abs=P,z=Z_FEED,classification=expected,
                    beta=solved.VF,equilibrium_source='Thermo PT flash',phases={})
        frozen = next((c for c in M8['cases'] if c['case_id']==identifier),None)
        if frozen:
            assert abs(solved.VF-frozen['beta']) <= 1e-9
            record.update(beta=frozen['beta'],equilibrium_source='Frozen M8 (unchanged); independently rechecked by Thermo')
        for label,p in [('liquid',solved.liquid0 if solved.liquids else None),('vapor',solved.gas)]:
            if p is None: continue
            q = frozen[label]['composition'] if frozen else p.zs
            if frozen: assert max(abs(a-b) for a,b in zip(q,p.zs)) <= 1e-9
            record['phases'][label]=phase_record(T,P,q,label,kw,cp,frozen[label]['Z'] if frozen else None)
        if expected=='VL':
            liquid,vapor=record['phases']['liquid'],record['phases']['vapor']; beta=record['beta']
            record['x'],record['y']=liquid['composition'],vapor['composition']
            record['material_residual']=[(1-beta)*x+beta*y-z for x,y,z in zip(record['x'],record['y'],Z_FEED)]
            assert max(abs(v) for v in record['material_residual'])<1e-10
            record['overall_h_J_mol']=(1-beta)*liquid['h_total_J_mol']+beta*vapor['h_total_J_mol']
            record['overall_s_J_mol_K']=(1-beta)*liquid['s_total_J_mol_K']+beta*vapor['s_total_J_mol_K']
            record['phase_difference_h_J_mol']=vapor['h_total_J_mol']-liquid['h_total_J_mol']
            record['phase_difference_s_J_mol_K']=vapor['s_total_J_mol_K']-liquid['s_total_J_mol_K']
            close(record['overall_h_J_mol'],solved.H(),'h_total')
            close(record['overall_s_J_mol_K'],solved.S(),'s_total')
            if identifier == 'B':
                record['benchmark_feed_kmol_h'] = 1000.0
                record['benchmark_equilibrium_enthalpy_flow_W'] = molar_enthalpy_flow(1000.,record['overall_h_J_mol'])
                record['benchmark_phase_enthalpy_flows_W'] = {
                    'liquid':molar_enthalpy_flow(1000.*(1-beta),liquid['h_total_J_mol']),
                    'vapor':molar_enthalpy_flow(1000.*beta,vapor['h_total_J_mol'])}
                record['benchmark_flow_is_not_separator_duty'] = True
        neighborhood=[]
        for dt in [-2.,0.,2.]:
            for factor in [.95,1.,1.05]:
                near=flash.flash(T=T+dt,P=P*factor,zs=Z_FEED)
                assert near.phase == expected, (identifier,dt,factor,near.phase)
                neighborhood.append(dict(T_K=T+dt,P_Pa_abs=P*factor,phase=near.phase,beta=near.VF))
        record['classification_neighborhood']=neighborhood
        cases.append(record)
    pure=[]
    for i,c in enumerate(COMPONENTS):
        q=[float(j==i) for j in range(2)]
        for T in [280.,300.,350.,400.]:
            for P,label in ([(1e5,'vapor')] if i==0 else [(1e3,'vapor'),(3e7,'liquid')]):
                row=phase_record(T,P,q,label,kw,cp)
                standalone=BenchmarkPR(Tc=c['Tc_K'],Pc=c['Pc_Pa_abs'],omega=c['omega'],T=T,P=P)
                suffix='l' if label=='liquid' else 'g'
                present=[s for s in ['l','g'] if hasattr(standalone,'G_dep_'+s)]
                assert getattr(standalone,'G_dep_'+suffix)<=min(getattr(standalone,'G_dep_'+s) for s in present)+1e-7
                close(row['h_res_J_mol'],getattr(standalone,'H_dep_'+suffix),'h_res')
                close(row['s_res_J_mol_K'],getattr(standalone,'S_dep_'+suffix),'s_res')
                row.update(component_id=c['id'],pure_EOS_h_res_J_mol=getattr(standalone,'H_dep_'+suffix),
                           pure_EOS_s_res_J_mol_K=getattr(standalone,'S_dep_'+suffix))
                pure.append(row)
    dilute=[]
    for q in [Z_FEED,[1.,0.],[0.,1.]]:
        rows=[phase_record(300.,P,q,'vapor',kw,cp) for P in [1000.,100.,10.,1.]]
        for key in ['h_res_J_mol','s_res_J_mol_K']:
            assert all(abs(a[key])>abs(b[key]) for a,b in zip(rows,rows[1:]))
        assert abs(rows[-1]['Z']-1)<1e-6
        assert abs(rows[-1]['h_res_J_mol'])<.01 and abs(rows[-1]['s_res_J_mol_K'])<1e-4
        dilute.extend(rows)
    cp_checks=[]
    for i,d in enumerate(CP_DATA):
        for T in [280.,eq.T_REF,300.,350.,400.]:
            analytical=eq.ideal_pure(T,d['coefficients'])
            lib=[cp[i](T),cp[i].T_dependent_property_integral(eq.T_REF,T),cp[i].T_dependent_property_integral_over_T(eq.T_REF,T)]
            numerical=[quad(lambda t:eq.ideal_pure(t,d['coefficients'])[0],eq.T_REF,T,epsabs=1e-9,epsrel=1e-12)[0],
                       quad(lambda t:eq.ideal_pure(t,d['coefficients'])[0]/t,eq.T_REF,T,epsabs=1e-11,epsrel=1e-12)[0]]
            for j,key in enumerate(['Cp','h_ig','s_ig']): close(lib[j],analytical[j],key)
            close(lib[1],numerical[0],'h_ig'); close(lib[2],numerical[1],'s_ig')
            cp_checks.append(dict(component_id=d['id'],T_K=T,Cp_ig_J_mol_K=lib[0],h_ig_J_mol=lib[1],
                s_ig_temperature_J_mol_K=lib[2],direct=list(analytical),quadrature_h_J_mol=numerical[0],quadrature_s_J_mol_K=numerical[1]))
    versions={name:importlib.metadata.version(name) for name in ['thermo','chemicals','fluids','numpy','scipy','pandas','teqp']}
    assert versions['thermo']=='0.6.0' and versions['chemicals']=='1.5.2'
    files={'thermo_eos':inspect.getsourcefile(PR),'thermo_eos_mix':inspect.getsourcefile(PRMIX),
           'thermo_ceos':inspect.getsourcefile(CEOSGas),'thermo_phase':inspect.getsourcefile(CEOSGas.Cpig_integrals_pure),
           'thermo_heat_capacity':inspect.getsourcefile(HeatCapacityGas),'chemicals_heat_capacity':hc.__file__,
           'poling_databank':Path(hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv'}
    return dict(benchmark_id='pre_m10_methane_nhexane_pr_caloric@1.0',component_dataset='riogineer_components@1.0',
        components=COMPONENTS,component_order=[c['id'] for c in COMPONENTS],kij=KIJ,dkij_dT='zero; temperature-independent BIPs only',
        formulation=dict(R_J_mol_K=R,OmegaA=.45724,OmegaB=.07780,kappa=[.37464,1.54226,-.26992],mixing='classical quadratic a, linear b'),
        reference_state=dict(T_ref_h_K=eq.T_REF,T_ref_s_K=eq.T_REF,P_ref_s_Pa_abs=eq.P_REF,
            phase='pure-component ideal gas',h_pure_ref_J_mol=[0.,0.],s_pure_ref_J_mol_K=[0.,0.],formation_included=False,
            basis='relative sensible; not third-law absolute; mixture includes ideal mixing entropy'),
        cp=dict(method='POLING_POLY',source='Poling, The Properties of Gases and Liquids, 5th edition; Chemicals 1.5.2 PolingDatabank.tsv',
            equation='Cp/R=sum(c_j*T^j), j=0..4',coefficient_units=['1','K^-1','K^-2','K^-3','K^-4'],
            components=CP_DATA,extrapolation=False,temperature_matrix_K=[280.,300.,350.,400.]),
        provenance=dict(library='Thermo',versions=versions,python=platform.python_version(),component_source_sha256=component_hash,
            M8_reference_sha256=sha(M8_PATH),source_sha256={key:sha(path) for key,path in files.items()},
            PT_squared_K_tolerance=1e-26,PT_stability_tolerance=1e-12,
            sources=['https://chemicals.readthedocs.io/chemicals.heat_capacity.html',
                     'https://thermo.readthedocs.io/thermo.phases.html','https://thermo.readthedocs.io/thermo.eos.html']),
        units=dict(temperature='K',pressure='Pa absolute',molar_enthalpy='J/mol',molar_entropy_and_Cp='J/(mol K)',
            mass_enthalpy='J/kg',mass_entropy='J/(kg K)',MW='kg/kmol and explicitly kg/mol',composition='mol/mol'),
        reference_shift_checks=reference_shift_checks(cases),acceptance_tolerances=TOLS,cases=cases,pure_states=pure,low_pressure_states=dilute,cp_integration_checks=cp_checks)


def compare(saved,fresh,path=''):
    """All input/provenance metadata match exactly; tight numerical reproduction."""
    if isinstance(saved,dict):
        assert saved.keys()==fresh.keys(),path
        for key in saved: compare(saved[key],fresh[key],path+'/'+key)
    elif isinstance(saved,list):
        assert len(saved)==len(fresh),path
        for i,(a,b) in enumerate(zip(saved,fresh)): compare(a,b,path+'/'+str(i))
    elif isinstance(saved,float):
        if path.split('/')[1] not in ('cases','pure_states','low_pressure_states','cp_integration_checks','reference_shift_checks'):
            assert saved==fresh,(path,saved,fresh)
        else:
            # Tighter reproduction than future-production acceptance; derivatives use subtraction.
            assert math.isfinite(saved) and math.isclose(saved,fresh,abs_tol=1e-10,rel_tol=1e-11),(path,saved,fresh)
    else:
        assert saved==fresh,(path,saved,fresh)


def print_phase(label, p):
    print(f"  {label}: T={p['T_K']:g} K; P={p['P_Pa_abs']:g} Pa; phase={p['phase']}; q={p['composition']}")
    print(f"    Z={p['Z']:.12g}; MW={p['mixture_MW_kg_kmol']:.12g} kg/kmol")
    print("    h [J/mol]: ideal={:.12g}; residual={:.12g}; total={:.12g}".format(p['h_ig_J_mol'],p['h_res_J_mol'],p['h_total_J_mol']))
    print("    s [J/(mol K)]: ideal={:.12g}; residual={:.12g}; total={:.12g}".format(p['s_ig_J_mol_K'],p['s_res_J_mol_K'],p['s_total_J_mol_K']))


def summary(data):
    for case in data['cases']:
        print(f"\n{case['case_id']}: T={case['T_K']:g} K; P={case['P_Pa_abs']:g} Pa; z={case['z']}; {case['classification']}")
        for label,p in case['phases'].items():
            print_phase(label,p)
        if case['classification']=='VL':
            print(f"  beta={case['beta']:.15g}; h_eq={case['overall_h_J_mol']:.12g} J/mol; s_eq={case['overall_s_J_mol_K']:.12g} J/(mol K)")
            print(f"  h_V-h_L={case['phase_difference_h_J_mol']:.12g} J/mol; s_V-s_L={case['phase_difference_s_J_mol_K']:.12g} J/(mol K)")
    print("\nPure-component checks:")
    for i,p in enumerate(data['pure_states']):
        print_phase(f"PURE_{i+1}_{p['component_id']}",p)
    print("\nIdeal-gas limit checks:")
    for i,p in enumerate(data['low_pressure_states']):
        print_phase(f"LIMIT_{i+1}",p)
    print(f"\nAuxiliary checks: {len(data['pure_states'])} pure states, {len(data['low_pressure_states'])} dilute states, {len(data['cp_integration_checks'])} Cp/integral points.")


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Explicit freeze after all equation-level gates pass')
    args=parser.parse_args()
    data=build()
    if args.write:
        ARTIFACT.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
        print('Wrote',ARTIFACT.relative_to(ROOT))
    else:
        compare(json.loads(ARTIFACT.read_text()),data)
        print('PASS: independent library, direct equations, Cp quadrature, identities, M8 equilibrium and frozen reproduction')

    summary(data)
