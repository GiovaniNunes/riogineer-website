"""Validation only: production against the unchanged independent caloric JSON.

Runs in the production environment; no Thermo/teqp or benchmark code imports.
Default is read-only. --write saves comparison evidence, never expected values.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.caloric_data import CORRELATIONS, DATASET, REFERENCE, component_caloric
from riogineer_engine.components import component
from riogineer_engine.pr_eos import MODEL, BinaryInteractions
from riogineer_engine.property_packages import property_package
from riogineer_engine.thermodynamics import MolarComposition, StateSpecificationProvenance, ThermodynamicState

FROZEN = Path(__file__).with_name('methane_nhexane_pr_caloric_reference.json')
REPORT = Path(__file__).with_name('production_comparison.json')


def compare_production():
    reference = json.loads(FROZEN.read_text())
    ids = tuple(reference['component_order'])
    bip = BinaryInteractions('methane_nhexane_explicit_zero@1.0',ids,tuple(tuple(r) for r in reference['kij']),
                             'Explicit zero-kij mathematical qualification specification; not calibrated physical data')
    provider = property_package(MODEL)
    comparisons = []
    case_results = []
    def compare(label, quantity, actual, expected, scale=1., field=None):
        tol = reference['acceptance_tolerances'].get(quantity)
        if quantity in ('MW','composition','fraction'):
            tol = dict(atol=1e-10 if quantity=='MW' else 1e-9,rtol=1e-12)
        assert tol is not None, quantity
        atol,rtol = tol['atol']*scale,tol['rtol']
        passed = math.isfinite(actual) and math.isfinite(expected) and abs(actual-expected) <= atol+rtol*abs(expected)
        comparisons.append(dict(state=label,quantity=quantity+('_mass' if scale != 1. else ''),actual=actual,expected=expected,
                                field=field or quantity,absolute_error=abs(actual-expected),
                                relative_error=abs(actual-expected)/abs(expected) if expected != 0 else None,
                                atol=atol,rtol=rtol,passed=passed))
    def state(t,p,q):
        return ThermodynamicState(t,p,MolarComposition(ids,tuple(q)),StateSpecificationProvenance(MODEL,bip.identifier))
    def phase_checks(label, result, expected, fixed_composition=True):
        assert result.status in ('success_single_phase','success_two_phase'), (label,result.status,result.message)
        c = next(p for p in result.phases if p.phase_identifier == expected['phase'])
        phase = next(p for p in result.equilibrium.phases if p.identifier == c.phase_identifier)
        for component_id,a,e in zip(ids,phase.composition,expected['composition']):compare(label,'composition',a,e,field=component_id)
        compare(label,'Z',phase.Z,expected['Z'])
        compare(label,'MW',c.mixture_MW_kg_kmol,expected['mixture_MW_kg_kmol'])
        for key,quantity in [('Cp_ig_J_mol_K','Cp'),('h_ig_J_mol','h_ig'),('h_res_J_mol','h_res'),('h_total_J_mol','h_total'),
                             ('s_ig_J_mol_K','s_ig'),('s_res_J_mol_K','s_res'),('s_total_J_mol_K','s_total')]:
            compare(label,quantity,getattr(c,key),expected[key],field=key)
        compare(label,'h_total',c.h_total_J_kg,expected['h_total_J_kg'],1/expected['mixture_MW_kg_mol'],field='h_total_J_kg')
        compare(label,'s_total',c.s_total_J_kg_K,expected['s_total_J_kg_K'],1/expected['mixture_MW_kg_mol'],field='s_total_J_kg_K')
        for field,value in expected['ideal_entropy_terms'].items():compare(label,'s_ig',getattr(c,field),value,field=field)
        # Tight EOS-parameter tolerances apply at identical input composition.
        # Runtime PT phase compositions have their own independently qualified tolerance.
        if fixed_composition:
            for actual,expected_pure in zip(c.pure_parameters,expected['pure_parameters']):
                for attr,key,quantity in [('alpha','alpha','alpha'),('dalpha_dT','dalpha_dT_K_inv','dalpha_dT'),
                    ('a','a_i_Pa_m6_mol2','a'),('da_dT','da_i_dT_Pa_m6_mol2_K','da_dT'),('b','b_i_m3_mol','b')]:
                    compare(label,quantity,getattr(actual,attr),expected_pure[key],field=expected_pure['id']+'/'+key)
            for attr,key,quantity in [('a','a_mix_Pa_m6_mol2','a'),('b','b_mix_m3_mol','b'),('da_dT','da_mix_dT_Pa_m6_mol2_K','da_dT')]:
                compare(label,quantity,getattr(c.eos,attr),expected[key],field=key)
            compare(label,'a',c.T_da_minus_a_Pa_m6_mol2,expected['departure_intermediates']['T_da_minus_a_Pa_m6_mol2'])
    for c in reference['components']:
        original = component(c['id'])
        assert (original.molecular_weight,original.critical_temperature,original.critical_pressure,original.acentric_factor)==(
            c['MW_kg_kmol'],c['Tc_K'],c['Pc_Pa_abs'],c['omega'])
    for c in reference['cp']['components']:
        actual = CORRELATIONS[c['id']]
        assert list(actual.coefficients)==c['coefficients'] and (actual.Tmin_K,actual.Tmax_K)==(c['Tmin_K'],c['Tmax_K'])
    assert REFERENCE.temperature_K==reference['reference_state']['T_ref_h_K']==reference['reference_state']['T_ref_s_K']
    assert REFERENCE.pressure_Pa_abs==reference['reference_state']['P_ref_s_Pa_abs']
    for case in reference['cases']:
        label = case['case_id']
        result = provider.equilibrium_caloric_PT(state(case['T_K'],case['P_Pa_abs'],case['z']),bip)
        assert result.status in ('success_single_phase','success_two_phase'), (label,result.status,result.message)
        expected_class = {'L':'single_liquid','V':'single_vapor','VL':'vapor_liquid'}[case['classification']]
        assert result.equilibrium.classification==expected_class
        compare(label,'fraction',result.equilibrium.beta,case['beta'],field='beta')
        compare(label,'fraction',1-result.equilibrium.beta,1-case['beta'],field='liquid_molar_fraction')
        for name,expected in case['phases'].items():phase_checks(label+'/'+name,result,expected,fixed_composition=False)
        if case['classification']=='VL':
            for attr,key,quantity in [('h_J_mol','overall_h_J_mol','h_total'),('s_J_mol_K','overall_s_J_mol_K','s_total'),
                ('phase_difference_h_J_mol','phase_difference_h_J_mol','h_total'),('phase_difference_s_J_mol_K','phase_difference_s_J_mol_K','s_total')]:
                compare(label,quantity,getattr(result.aggregate,attr),case[key],field=key)
        case_results.append(summarize_case(label,result))
    rows = [(case['case_id']+'/'+p['phase']+'/fixed',p) for case in reference['cases'] for p in case['phases'].values()]
    rows += [(f"pure_{p['component_id']}/{p['T_K']:g}K_{p['P_Pa_abs']:g}Pa",p) for p in reference['pure_states']]
    for p in reference['low_pressure_states']:
        species = 'equimolar' if p['composition']==[.5,.5] else 'methane' if p['composition'][0]==1 else 'n_hexane'
        rows.append((f"low_pressure/{species}_{p['P_Pa_abs']:g}Pa",p))
    for label,p in rows:
        result = provider.phase_caloric_TP(state(p['T_K'],p['P_Pa_abs'],p['composition']),bip,phase=p['phase'],root=p['Z'])
        phase_checks(label,result,p)
        if label.startswith(('pure_','low_pressure/')):
            case_results.append(summarize_case(label,result))
    for p in reference['cp_integration_checks']:
        actual = component_caloric(p['component_id'],p['T_K'])
        for key,quantity in [('Cp_ig_J_mol_K','Cp'),('h_ig_J_mol','h_ig'),('s_ig_temperature_J_mol_K','s_ig')]:
            compare(p['component_id']+'/'+str(p['T_K']),quantity,getattr(actual,key),p[key],field=key)
    maxima = {q:max(c['absolute_error'] for c in comparisons if c['quantity']==q) for q in sorted({c['quantity'] for c in comparisons})}
    relative_maxima = {q:max((c['relative_error'] for c in comparisons if c['quantity']==q and c['relative_error'] is not None),default=None) for q in maxima}
    return dict(reference_id=reference['benchmark_id'],reference_sha256=hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
                provider=MODEL,caloric_dataset=DATASET,passed=all(c['passed'] for c in comparisons),
                comparison_count=len(comparisons),maximum_absolute_errors=maxima,maximum_relative_errors=relative_maxima,case_results=case_results,comparisons=comparisons)


def summarize_case(label, result):
    pt = result.equilibrium
    by_id = {p.identifier:p for p in pt.phases}
    return dict(case_id=label,T_K=pt.overall_state.temperature_K,P_Pa_abs=pt.overall_state.pressure_Pa_abs,
        component_ids=list(pt.overall_state.composition.component_ids),classification=pt.classification,
        beta=pt.beta,liquid_molar_fraction=1-pt.beta,
        phases=[dict(phase=p.phase_identifier,composition=list(by_id[p.phase_identifier].composition),Z=by_id[p.phase_identifier].Z,
            **{key:getattr(p,key) for key in ('mixture_MW_kg_kmol','h_ig_J_mol','h_res_J_mol','h_total_J_mol',
                's_ig_J_mol_K','s_res_J_mol_K','s_total_J_mol_K','h_total_J_kg','s_total_J_kg_K')}) for p in result.phases],
        h_eq_J_mol=result.aggregate.h_J_mol,s_eq_J_mol_K=result.aggregate.s_J_mol_K,
        phase_difference_h_J_mol=result.aggregate.phase_difference_h_J_mol,
        phase_difference_s_J_mol_K=result.aggregate.phase_difference_s_J_mol_K)


def matches_case(label, selected):
    return selected is None or label==selected or label.startswith(selected+'/')


def print_report(report, case=None, details=False):
    print(f"{'PASS' if report['passed'] else 'FAIL'}: {report['comparison_count']} comparisons; {report['provider']}; {report['caloric_dataset']}")
    print('Referenced properties: pure ideal-gas h=s=0 at 298.15 K, 101325 Pa; no formation terms.')
    for result in report['case_results']:
        if not matches_case(result['case_id'],case):
            continue
        if case is None and not details and result['case_id'].startswith(('pure_','low_pressure/')):
            continue
        print(f"\nCase {result['case_id']}: {result['T_K']:g} K; {result['P_Pa_abs']:g} Pa absolute; {result['classification']}")
        for phase in result['phases']:
            print('  '+phase['phase'].capitalize())
            print('    molar composition: '+', '.join(f'{i}={q:.15g}' for i,q in zip(result['component_ids'],phase['composition'])))
            print(f"    Z={phase['Z']:.15g}; MW={phase['mixture_MW_kg_kmol']:.15g} kg/kmol")
            print('    h [J/mol]: h_ig={:.15g}; h_res={:.15g}; h_total={:.15g}'.format(
                phase['h_ig_J_mol'],phase['h_res_J_mol'],phase['h_total_J_mol']))
            print('    s [J/(mol K)]: s_ig={:.15g}; s_res={:.15g}; s_total={:.15g}'.format(
                phase['s_ig_J_mol_K'],phase['s_res_J_mol_K'],phase['s_total_J_mol_K']))
            print(f"    h_mass={phase['h_total_J_kg']:.15g} J/kg; s_mass={phase['s_total_J_kg_K']:.15g} J/(kg K)")
        print(f"  Overall equilibrium: liquid molar fraction={result['liquid_molar_fraction']:.15g}")
        print(f"    beta={result['beta']:.15g} (vapor molar fraction)")
        print(f"    h_eq={result['h_eq_J_mol']:.15g} J/mol; s_eq={result['s_eq_J_mol_K']:.15g} J/(mol K)")
        if result['phase_difference_h_J_mol'] is not None:
            print(f"    h_V-h_L={result['phase_difference_h_J_mol']:.15g} J/mol; s_V-s_L={result['phase_difference_s_J_mol_K']:.15g} J/(mol K)")
    print('\nMaximum errors by quantity class (relative error undefined for zero references):')
    for quantity,error in report['maximum_absolute_errors'].items():
        print(f"  {quantity}: absolute={error:.12g}; relative={report['maximum_relative_errors'][quantity]}")
    if details or case is not None:
        print('\nState | quantity/field | reference | production | absolute error | relative error | atol | rtol | result')
        for row in report['comparisons']:
            if not matches_case(row['state'],case):
                continue
            relative = 'undefined (zero reference)' if row['relative_error'] is None else f"{row['relative_error']:.8g}"
            print(f"{row['state']} | {row['quantity']}/{row['field']} | {row['expected']:.16g} | {row['actual']:.16g} | "
                  f"{row['absolute_error']:.8g} | {relative} | {row['atol']:.8g} | {row['rtol']:.8g} | {'PASS' if row['passed'] else 'FAIL'}")
    print('\nHuman-operated Milestone 10 validation remains pending.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Write comparison evidence only; never rewrite the independent reference')
    parser.add_argument('--case',choices=['A','B','C','T280_L','T280_VL','T280_V','T350_L','T350_VL','T350_V','T400_L','T400_VL','T400_V','pure_methane','pure_n_hexane','low_pressure'],
                        help='Focus the display; all acceptance comparisons still execute')
    parser.add_argument('--details',action='store_true',help='Print every comparison, including pure components and derivatives')
    parser.add_argument('--json',action='store_true',help='Print complete machine-readable comparison evidence')
    args=parser.parse_args()
    report=compare_production()
    if args.json:
        print(json.dumps(report,indent=2,allow_nan=False))
    else:
        print_report(report,args.case,args.details)
    if not report['passed']:
        if not args.json:print(json.dumps([c for c in report['comparisons'] if not c['passed']],indent=2))
        raise SystemExit(1)
    if args.write:REPORT.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
