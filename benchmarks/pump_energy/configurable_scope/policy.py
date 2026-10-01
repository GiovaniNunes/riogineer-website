"""Benchmark-only configurable policy. No production pump or EOS implementation."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmarks.pump_energy.common import validate, liquid, h_budget, TOLS

HERE = Path(__file__).resolve().parent
REFERENCE = HERE/'reference.json'
PRODUCTION = HERE/'production.json'
T_STATE = (300., 370.)
P_WITNESS = 16e6
MIN_DP = 10000.
FLOW = (5., 200.)


def inputs(i):
    reason = validate(i)
    if reason:
        return reason
    # Fixed recipe: no silent rounding of a different composition into scope.
    if list(i['z']) != [.5, .5]:
        return 'composition_scope'
    if not 300 <= i['T1'] <= 350 or not 20e6 <= i['P1'] <= 25e6 or not i['P1'] <= i['P2'] <= 30e6:
        return 'input_range'
    if not .6 <= i['eta'] <= 1 or not FLOW[0] <= i['flow'] <= FLOW[1]:
        return 'input_range'
    if i['P2'] != i['P1'] and i['P2']-i['P1'] < MIN_DP:
        return 'positive_rise_below_floor'
    return None


def work_policy(i, states):
    a, b, c = [states[k] for k in ('inlet', 'isentropic', 'outlet')]
    h1, hs, h2 = [s['H_eq_J_mol'] for s in (a, b, c)]
    dhs, dh = hs-h1, h2-h1
    if i['P1'] == i['P2']:
        return dict(status='identity', budget_J_mol=0., ratio=None, reconstructed_eta=None)
    # Engineering screening budget, NOT a rigorous property-error bound.
    # Comparison allowances + full PS residual capacity mapped by dh=T ds at P,z
    # + PH residual capacity + subtraction roundoff; all from runtime quantities.
    B1, Bs, B2 = [h_budget(h) for h in (h1, hs, h2)]
    rounding = 64*sys.float_info.epsilon*max(1., abs(h1), abs(hs), abs(h2))/i['eta']
    ps_capacity = T_STATE[1]*TOLS['PS_residual']/i['eta']
    budget = (B1+Bs)/i['eta']+B1+B2+ps_capacity+TOLS['PH_residual']+rounding
    ratio = budget/dh if dh > 0 else None
    return dict(status='resolved' if dhs > 0 and dh > 0 and ratio <= 1e-4 else 'unresolved',
                budget_J_mol=budget, ratio=ratio, ps_capacity_J_mol=ps_capacity,
                reconstructed_eta=dhs/dh if dh > 0 and ratio <= 1e-4 else None)


def state_guard(s, witness):
    try:
        values = [s[k] for k in ('T_K', 'P_Pa_abs', 'H_eq_J_mol', 'S_eq_J_mol_K', 'beta')]
        values += [v for p in s['phases'].values() for v in (p['Z'], p['h_J_mol'], p['s_J_mol_K'], *p['composition'])]
        if not all(math.isfinite(v) for v in values):
            return 'nonfinite_state'
        if not T_STATE[0] <= s['T_K'] <= T_STATE[1] or not 20e6 <= s['P_Pa_abs'] <= 30e6 or s['z'] != [.5, .5]:
            return 'state_domain'
        if not liquid(s):
            return 'non_liquid'
        for q in (s, witness):
            if not q or not liquid(q):
                return 'phase_witness_failure'
            if q['z'] != [.5, .5] or q['T_K'] != s['T_K']:
                return 'phase_witness_mismatch'
            if 'PT_diagnostics' in q and 'stability' in q['PT_diagnostics']:
                d = q['PT_diagnostics']['stability']
                if not d or d['stable'] is not True or not d['converged'] or d['phase_identification_parameter'] <= 1:
                    return 'stability_failure'
        if witness['P_Pa_abs'] != P_WITNESS:
            return 'phase_witness_mismatch'
    except (KeyError, TypeError, ValueError):
        return 'invalid_state'
    return None


def evaluate(i, result, witnesses):
    reason = inputs(i)
    if reason:
        return dict(accepted=False, reason=reason)
    if result.get('stage') != 'complete':
        return dict(accepted=False, reason='inverse_or_property_failure')
    for name, s in result['states'].items():
        reason = state_guard(s, witnesses.get(name))
        if reason:
            return dict(accepted=False, reason=reason)
    a, b, c = [result['states'][k] for k in ('inlet', 'isentropic', 'outlet')]
    if a['P_Pa_abs'] != i['P1'] or a['T_K'] != i['T1'] or b['P_Pa_abs'] != i['P2'] or c['P_Pa_abs'] != i['P2']:
        return dict(accepted=False, reason='state_specification_mismatch')
    identity = i['P1'] == i['P2']
    if identity:
        if a != b or a != c or result['diagnostics']:
            return dict(accepted=False, reason='invalid_identity')
    else:
        for key, count in [('PS', 64), ('PH', 128)]:
            d = result['diagnostics'].get(key, {})
            if 'candidate_count' in d:  # production adapter
                ok = (d.get('status') == 'success' and d['candidate_count'] == 1 and
                      d.get('scan_count') == count and d.get('fresh_final_count') == 1 and
                      abs(d.get('residual', float('inf'))) <= TOLS[key+'_residual'])
            else:  # independent adapter; no numerical implementation shared
                g = d.get('diagnostics', {})
                ok = (d.get('status') == 'success' and len(g.get('brackets', [])) == 1 and
                      g.get('scan_evaluations') == count and g.get('final_evaluations') == 1)
            if not ok:
                return dict(accepted=False, reason='inverse_diagnostics')
        target = a['H_eq_J_mol']+(b['H_eq_J_mol']-a['H_eq_J_mol'])/i['eta']
        if abs(c['H_eq_J_mol']-target) > 1e-6 or abs(b['S_eq_J_mol_K']-a['S_eq_J_mol_K']) > 1e-8:
            return dict(accepted=False, reason='inverse_residual')
        if c['S_eq_J_mol_K']-a['S_eq_J_mol_K'] < -2e-8:
            return dict(accepted=False, reason='entropy_generation')
        if i['eta'] == 1 and (abs(c['T_K']-b['T_K']) > 1e-7 or abs(c['S_eq_J_mol_K']-a['S_eq_J_mol_K']) > 2e-8):
            return dict(accepted=False, reason='ideal_efficiency')
    work = work_policy(i, result['states'])
    return dict(accepted=work['status'] in ('identity', 'resolved'), reason=work['status'], work=work)


def cases():
    rows = []
    def add(name, group, T, P1, P2, eta):
        rows.append(dict(case_id=name, group=group, inputs=dict(T1=T, P1=P1, P2=P2, eta=eta, flow=100., z=[.5,.5])))
    for T in (300., 350.):
        for P1 in (20e6, 25e6):
            for eta in (.6, 1.):
                for mode, P2 in [('floor', P1+MIN_DP), ('max', 30e6)]:
                    add(f'CORNER_{T}_{P1}_{eta}_{mode}', 'corner', T, P1, P2, eta)
            add(f'IDENTITY_{T}_{P1}', 'identity', T, P1, P1, .8)
    for j, (T, P1, fraction, eta) in enumerate([
        (325.,22.5e6,.5,.8),(310.,20e6,.3,.7),(340.,25e6,.7,.9),
        (300.,23e6,.6,.6),(350.,21e6,.4,1.),(327.,24e6,.8,.65)]):
        add('INTERIOR_'+str(j), 'development', T, P1, P1+fraction*(30e6-P1), eta)
    # Predeclared deterministic holdouts: not used to select guard constants.
    for j, (u,v,w,e) in enumerate([
        (.137,.731,.419,.283),(.863,.269,.781,.917),(.419,.113,.637,.541),
        (.677,.887,.193,.139),(.053,.457,.913,.763),(.947,.593,.347,.397),
        (.311,.967,.557,.031),(.789,.037,.071,.669)]):
        P1 = 20e6+5e6*v
        add('HOLDOUT_'+str(j), 'holdout', 300+50*u, P1, P1+w*(30e6-P1), .6+.4*e)
    for j,(T,P1,eta) in enumerate([(300.,20e6,1.),(300.,25e6,.6),(350.,20e6,.6),(350.,25e6,1.)]):
        for dp in (10.,1000.,MIN_DP):
            add(f'CONDITION_{j}_{dp}', 'conditioning', T, P1, P1+dp, eta)
    return rows
