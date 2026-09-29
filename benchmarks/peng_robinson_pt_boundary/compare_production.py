"""M8.1 production evidence; reads, never regenerates, the independent reference.

The fixed local dew H experiment is a benchmark conditioning diagnostic only.
It is not a production PH solver or a qualification of the PH case matrix.
No independent thermodynamic library is imported by this comparison.
"""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'engine'))
from riogineer_engine.pr_eos import BinaryInteractions, MODEL, PengRobinsonEOS
from riogineer_engine.pr_flash import SolverSettings, wilson
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.rachford_rice import residual, solve_rr
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance

REFERENCE = Path(__file__).with_name('methane_nhexane_pt_boundary_reference.json')
REFERENCE_SHA256 = 'e5346c3a65c17e2f128e1a581d354e7404fc86fbf86e578fa9f4dc9798f20ad0'
CASE_IDS = ('BUBBLE_STABLE_231_10', 'BUBBLE_MINUS_1MK', 'BUBBLE_MINUS_0_1MK',
            'BUBBLE_PLUS_0_1MK', 'BUBBLE_PLUS_1MK', 'BUBBLE_231_15',
            'BUBBLE_231_199', 'BUBBLE_231_25', 'BUBBLE_CENTER',
            'BUBBLE_231_349', 'BUBBLE_231_399', 'BUBBLE_231_45')


def read_reference(path=REFERENCE):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REFERENCE_SHA256:
        raise ValueError('Frozen Pre-M8.1 reference integrity mismatch')
    r = json.loads(raw)
    if r['reference_id'] != 'independent_pr_pt_boundary@1.0':
        raise ValueError('Unsupported independent reference version')
    if tuple(c['case_id'] for c in r['bubble_cases']) != CASE_IDS:
        raise ValueError('Incomplete bubble matrix')
    if r['metadata']['component_order'] != ['methane', 'n_hexane']:
        raise ValueError('Unexpected component order')
    return r


def inputs(r, record):
    m = r['metadata']
    ids = tuple(m['component_order'])
    bip = BinaryInteractions(m['BIP_identity'], ids, tuple(tuple(row) for row in m['kij']), m['BIP_provenance'])
    state = ThermodynamicState(record['T_K'], record['P_Pa_abs'],
        MolarComposition(ids, tuple(record['z'])), StateSpecificationProvenance(MODEL, bip.identifier))
    return state, bip


def evaluate(r, record, settings=SolverSettings(), caloric=False):
    state, bip = inputs(r, record)
    provider = PengRobinsonProvider()
    cal = provider.equilibrium_caloric_PT(state, bip, settings) if caloric else None
    pt = cal.equilibrium if caloric else provider.flash_PT(state, bip, settings)
    if pt is None or not pt.status.startswith('success') or (caloric and cal.aggregate is None):
        raise RuntimeError(f'Production failure at T={state.temperature_K}: {cal or pt}')
    if pt.overall_state.composition.component_ids != tuple(r['metadata']['component_order']):
        raise ValueError('Production component identity mismatch')
    phases = {p.identifier: dict(composition=p.composition, Z=p.Z, phi=p.phi, ln_phi=p.ln_phi) for p in pt.phases}
    if caloric:
        for p in cal.phases:
            phases[p.phase_identifier].update(h_ig_J_mol=p.h_ig_J_mol,
                h_res_J_mol=p.h_res_J_mol, h_J_mol=p.h_total_J_mol)
    return dict(T_K=state.temperature_K, P_Pa_abs=state.pressure_Pa_abs, z=record['z'],
        classification=pt.classification, beta=pt.beta, phases=phases,
        final_K=pt.final_K or None, log_fugacity_residual=pt.diagnostics.fugacity_residual,
        material_reconstruction_residual=pt.diagnostics.material_residual,
        diagnostics=asdict(pt.diagnostics), settings=asdict(pt.provenance.settings),
        status=pt.status, H_eq_J_mol=cal.aggregate.h_J_mol if caloric else None)


def number(checks, name, actual, expected, tol):
    allowed = tol['atol'] + tol['rtol'] * abs(expected)
    error = abs(actual - expected)
    checks.append(dict(quantity=name, actual=actual, reference=expected, absolute_error=error,
        allowed_error=allowed, allowance_fraction=error / allowed,
        passed=isfinite(actual) and error <= allowed))


def equal(checks, name, actual, expected):
    checks.append(dict(quantity=name, actual=actual, reference=expected, passed=actual == expected))


def compare(r, actual, expected, caloric=False):
    checks = []
    t = r['inherited_acceptance_tolerances']['PH']
    m8 = r['inherited_acceptance_tolerances']['M8']
    equal(checks, 'classification', actual['classification'], expected['classification'])
    equal(checks, 'phase identities', sorted(actual['phases']), sorted(expected['phases']))
    number(checks, 'T', actual['T_K'], expected['T_K'], t['T'])
    number(checks, 'beta', actual['beta'], expected['beta'], t['beta'])
    for label, p in expected['phases'].items():
        a = actual['phases'][label]
        for i, component in enumerate(r['metadata']['component_order']):
            number(checks, label+'.composition.'+component, a['composition'][i], p['composition'][i], t['composition'])
            number(checks, label+'.ln_phi.'+component, a['ln_phi'][i], p['ln_phi'][i], m8['ln_phi'])
        number(checks, label+'.Z', a['Z'], p['Z'], t['Z'])
        if caloric:
            for name in ('h_ig_J_mol', 'h_res_J_mol', 'h_J_mol'):
                number(checks, label+'.'+name, a[name], p[name], t['h'])
    if expected['final_K'] is not None:
        for i, component in enumerate(r['metadata']['component_order']):
            x, y = expected['phases']['liquid']['composition'][i], expected['phases']['vapor']['composition'][i]
            dx, dy = (t['composition']['atol'] + t['composition']['rtol'] * abs(q) for q in (x, y))
            # Exact interval propagation of inherited composition allowances.
            allowed = max((y+dy)/(x-dx)-y/x, y/x-(y-dy)/(x+dx))
            number(checks, 'K.'+component, actual['final_K'][i], expected['final_K'][i], dict(atol=allowed, rtol=0))
        for i, v in enumerate(actual['log_fugacity_residual']):
            number(checks, 'equilibrium residual.'+str(i), v, 0., m8['ln_fugacity_equilibrium'])
        equal(checks, 'resolved fugacity target satisfied',
              max(map(abs, actual['log_fugacity_residual'])) <= actual['settings']['fugacity_tolerance'], True)
        for i, v in enumerate(actual['material_reconstruction_residual']):
            number(checks, 'material residual.'+str(i), v, 0., m8['material_reconstruction'])
        number(checks, 'RR residual', actual['diagnostics']['rr_residual'], 0., m8['rachford_rice'])
    if caloric:
        number(checks, 'H_eq', actual['H_eq_J_mol'], expected['H_eq_J_mol'], t['h'])
    return checks


def local_dew_margin(r):
    """Reproduce only the frozen +/-0.001 K conditioning experiment, not PH scope."""
    expected = r['dew_reference']
    trial = next(s for s in r['dew_precision_study'] if s['requested_log_fugacity_tolerance'] == 1e-12)
    lo, hi = trial['local_H_matching']['T_bracket_K']
    target = expected['H_eq_J_mol']
    history = []
    def value(t):
        a = evaluate(r, dict(expected, T_K=t), SolverSettings.high_accuracy(), True)
        if a['classification'] != 'vapor_liquid':
            raise RuntimeError('Local conditioning experiment left its qualified VLE interval')
        error = a['H_eq_J_mol']-target
        history.append(dict(T_K=t, H_residual_J_mol=error, iterations=a['diagnostics']['iterations']))
        return a, error
    _, flo = value(lo)
    _, fhi = value(hi)
    if not flo < 0 < fhi:
        raise RuntimeError('Frozen local diagnostic bracket no longer brackets H')
    for _ in range(60):
        mid = (lo+hi)/2
        if mid in (lo, hi):
            break
        a, f = value(mid)
        if f > 0:
            hi = mid
        else:
            lo = mid
    # Evaluate the best representable endpoint afresh; never return a cached trial.
    best = min(history, key=lambda h: abs(h['H_residual_J_mol']))
    a, error = value(best['T_K'])
    checks = compare(r, a, expected, True)
    number(checks, 'H residual', error, 0., r['inherited_acceptance_tolerances']['PH']['H_residual'])
    # Same downstream quantities as the frozen local-H experiment; EOS residual
    # gates have their own acceptance and are not downstream field-error margins.
    fields = [c for c in checks if 'allowance_fraction' in c and
              (c['quantity'] in ('T','beta','H_eq') or '.composition.' in c['quantity'] or
               c['quantity'].endswith(('.Z','.h_ig_J_mol','.h_res_J_mol','.h_J_mol')))]
    governing = max(fields, key=lambda c: c['allowance_fraction'])
    margin = 1/governing['allowance_fraction']
    equal(checks, 'required downstream margin', margin >= r['recommendation']['minimum_required_margin_factor'], True)
    return dict(result=a, evaluations=history, comparisons=checks,
        H_residual_J_mol=error, minimum_margin_factor=margin, governing=governing)


def build():
    r = read_reference()
    bubbles = []
    all_checks = []
    for c in r['bubble_cases']:
        expected = c['reference']
        a = evaluate(r, expected)
        state, bip = inputs(r, expected)
        k = wilson(PengRobinsonEOS(bip.component_ids, state.temperature_K, state.pressure_Pa_abs, bip))
        rr = solve_rr(expected['z'], k)
        checks = compare(r, a, expected)
        equal(checks, 'restart count', a['diagnostics']['initialization']['restart_count'], int(c['needs_stability_restart']))
        all_checks.extend(checks)
        bubbles.append(dict(case_id=c['case_id'], reference=expected, production=a, comparisons=checks,
            Wilson_K=k, Wilson_RR=dict(asdict(rr), F0=residual(expected['z'],k,0.), F1=residual(expected['z'],k,1.)),
            passed=all(v['passed'] for v in checks)))
    dew = {}
    for label, settings in [('standard', SolverSettings()), ('high_accuracy', SolverSettings.high_accuracy())]:
        a = evaluate(r, r['dew_reference'], settings, True)
        # Standard preserves historical PT, not the new downstream caloric
        # precision gate. Retain all its caloric errors as diagnostic evidence.
        checks = compare(r, a, r['dew_reference'], label == 'high_accuracy')
        equal(checks, 'profile', a['settings']['profile'], label)
        equal(checks, 'fugacity target', a['settings']['fugacity_tolerance'],
              r['recommendation'][label+'_log_fugacity_tolerance'])
        all_checks.extend(checks)
        dew[label] = dict(production=a, comparisons=checks,
            diagnostic_comparisons=compare(r, a, r['dew_reference'], True) if label == 'standard' else [],
            passed=all(v['passed'] for v in checks))
    isolation = evaluate(r, r['dew_reference'], SolverSettings(), True) == dew['standard']['production']
    repeat = evaluate(r, r['dew_reference'], SolverSettings.high_accuracy(), True) == dew['high_accuracy']['production']
    equal(all_checks, 'standard/high/standard isolation', isolation, True)
    equal(all_checks, 'high accuracy repeatability', repeat, True)
    local = local_dew_margin(r)
    all_checks.extend(local['comparisons'])
    return dict(reference_id=r['reference_id'], reference_sha256=REFERENCE_SHA256, provider=MODEL,
        bubble_cases_discovered=len(r['bubble_cases']), bubble_cases_compared=len(bubbles),
        bubble_cases_passed=sum(c['passed'] for c in bubbles), bubble_cases_failed=sum(not c['passed'] for c in bubbles),
        bubble_boundary=r['bubble_boundary']['T_K'], Wilson_no_root_region=r['Wilson_no_root_region'],
        bubble_cases=bubbles, dew_reference=r['dew_reference'], dew_precision=dew,
        local_dew_margin=local, standard_high_standard_identical=isolation, high_accuracy_repeat_identical=repeat,
        comparisons=len(all_checks), passed=all(v['passed'] for v in all_checks),
        failures=[c for c in all_checks if not c['passed']])


def display(evidence, selected, details):
    if selected in ('all','bubble_center'):
        center = next(c for c in evidence['bubble_cases'] if c['case_id'] == 'BUBBLE_CENTER')
        p = center['production']; d = p['diagnostics']; init = d['initialization']
        print('Bubble center: T=',p['T_K'],'K; P=',p['P_Pa_abs'],'Pa absolute')
        print('Stability: stable=',d['stability']['stable'],'minimum TPD/RT=',d['stability']['minimum_tpd_RT'])
        print('Wilson K:',center['Wilson_K'],'RR:',center['Wilson_RR'])
        print('Restart count:',init['restart_count'],'seed:',init['restart_seed'],'initial RR:',init['restart_rr'])
        print('Phase:',p['classification'],'beta:',p['beta'],'final K:',p['final_K'])
        for label, phase in p['phases'].items(): print(label,phase)
        print('Maximum log-fugacity residual:',max(map(abs,p['log_fugacity_residual'])),'iterations:',d['iterations'])
    if selected == 'all':
        print('\nBubble matrix: T / reference phase / production phase / Wilson root / restart / beta ref / beta prod / result')
        for c in evidence['bubble_cases']:
            p=c['production'];q=c['reference']
            print(p['T_K'],q['classification'],p['classification'],c['Wilson_RR']['status']=='two_phase',
                  p['diagnostics']['initialization']['restart_count'],q['beta'],p['beta'],'PASS' if c['passed'] else 'FAIL')
    if selected in ('all','dew_precision'):
        print('\nDew precision: exact frozen T=',evidence['dew_reference']['T_K'],'K')
        standard=evidence['dew_precision']['standard']
        high=evidence['dew_precision']['high_accuracy']
        s,h=standard['production'],high['production']
        def row(name, a, b, reference='—'):
            a,b=getattr(a,'value',a),getattr(b,'value',b)
            print(f'{name:34} | {str(a):23} | {str(b):23} | {reference}')
        row('Quantity','Standard','High accuracy','Independent reference / allowance')
        row('Resolved profile',s['settings']['profile'],h['settings']['profile'])
        row('Fugacity target',s['settings']['fugacity_tolerance'],h['settings']['fugacity_tolerance'])
        row('Iterations',s['diagnostics']['iterations'],h['diagnostics']['iterations'])
        row('Max log-fugacity residual',max(map(abs,s['log_fugacity_residual'])),max(map(abs,h['log_fugacity_residual'])))
        sc={c['quantity']:c for c in standard['diagnostic_comparisons'] if 'absolute_error' in c}
        hc={c['quantity']:c for c in high['comparisons'] if 'absolute_error' in c}
        names=('beta','liquid.composition.methane','liquid.composition.n_hexane',
               'vapor.composition.methane','vapor.composition.n_hexane',
               'liquid.Z','vapor.Z','liquid.h_J_mol','vapor.h_J_mol','H_eq')
        for name in names:
            row(name,sc[name]['actual'],hc[name]['actual'],hc[name]['reference'])
        print('Absolute errors (all high-accuracy fields must pass):')
        for name in names:
            row(name,sc[name]['absolute_error'],hc[name]['absolute_error'],
                str(hc[name]['allowed_error'])+' '+('PASS' if hc[name]['passed'] else 'FAIL'))
        row('Profile acceptance','PASS' if standard['passed'] else 'FAIL','PASS' if high['passed'] else 'FAIL')
        for c in standard['diagnostic_comparisons']:
            if not c['passed']:
                print('Standard caloric DIAGNOSTIC (not a high-accuracy gate):',c)
        local=evidence['local_dew_margin']
        print('Local high-accuracy H-conditioning margin:',local['minimum_margin_factor'],'governing:',local['governing'])
        print('Standard/high/standard identical:',evidence['standard_high_standard_identical'],
              'high repeat identical:',evidence['high_accuracy_repeat_identical'])
    if details:
        print(json.dumps(evidence,indent=2,allow_nan=False))
    print('\n'+('PASS' if evidence['passed'] else 'FAIL')+f": {evidence['comparisons']} comparisons; {evidence['provider']}; {evidence['reference_id']}")
    print('Human-operated M8.1 validation remains pending. M11 remains blocked.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=('all','bubble_center','dew_precision'),default='all')
    parser.add_argument('--details',action='store_true')
    parser.add_argument('--write',action='store_true',help='Write production evidence only; never the independent reference')
    args=parser.parse_args()
    evidence=build()
    display(evidence,args.case,args.details)
    if args.write:
        Path(__file__).with_name('production_comparison.json').write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
    return 0 if evidence['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
