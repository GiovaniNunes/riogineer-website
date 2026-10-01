"""Separate read-only production provider experiment consuming frozen reference."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'engine'))
from benchmarks.pump_energy.common import (HERE, REFERENCE, PRODUCTION, IDS, TOLS,
    encode, digest, validate, liquid, finish, h_budget)
from riogineer_engine.pr_eos import BinaryInteractions
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_ps_flash import PSSpecification
from riogineer_engine.pr_ph_flash import PHSpecification
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance

BIP = BinaryInteractions('pre_m18_explicit_zero', IDS, ((0., 0.), (0., 0.)), 'Explicit study zero, not fitted')
PROVENANCE = StateSpecificationProvenance('peng_robinson@1.0', BIP.identifier)


def state(c):
    p = c.equilibrium
    return dict(T_K=p.overall_state.temperature_K, P_Pa_abs=p.overall_state.pressure_Pa_abs,
        z=list(p.evaluated_molar_composition), classification=p.classification, beta=p.beta,
        H_eq_J_mol=c.aggregate.h_J_mol, S_eq_J_mol_K=c.aggregate.s_J_mol_K,
        phases={q.identifier: dict(composition=list(q.composition), Z=q.Z,
            h_J_mol=a.h_total_J_mol, s_J_mol_K=a.s_total_J_mol_K)
            for q, a in zip(p.phases, c.phases)},
        PT_status=p.status, PT_diagnostics=asdict(p.diagnostics),
        PT_profile=p.provenance.settings.profile.value)


def inverse(r):
    d = asdict(r.diagnostics)
    d['candidate_count'] = len(d['brackets_K'])
    d['scan_count'] = sum(t['stage'] == 'scan' for t in d['trials'])
    d['fresh_final_count'] = sum(t['stage'] == 'final' and t['status'] == 'success' for t in d['trials'])
    d['failures'] = [t for t in d['trials'] if t['status'] != 'success']
    d['status'] = r.status
    d['residual'] = getattr(r, 'entropy_residual_J_mol_K', getattr(r, 'enthalpy_residual_J_mol', None))
    return d


def calculate(i):
    out = dict(status='pending', states={}, diagnostics={})
    error = validate(i)
    if error:
        return out | dict(status=error, stage='prototype_input')
    provider = PengRobinsonProvider()
    z = MolarComposition(IDS, tuple(i['z']))
    a = provider.equilibrium_caloric_PT(ThermodynamicState(i['T1'], i['P1'], z, PROVENANCE), BIP, SolverSettings.high_accuracy())
    if a.aggregate is None:
        return out | dict(status='production_failure', stage='inlet_PT', reason=a.status, message=a.message)
    out['states']['inlet'] = state(a)
    if not liquid(out['states']['inlet']):
        return out | dict(status='unsupported_phase', stage='inlet_PT')
    if i['P1'] == i['P2']:
        out['states'].update(isentropic=out['states']['inlet'], outlet=out['states']['inlet'])
    else:
        ps = provider.flash_PS(PSSpecification(i['P2'], a.aggregate.s_J_mol_K, z, PROVENANCE), BIP)
        out['diagnostics']['PS'] = inverse(ps)
        if ps.caloric is None or ps.status != 'success':
            return out | dict(status='production_failure', stage='PS', reason=ps.status)
        out['states']['isentropic'] = state(ps.caloric)
        if not liquid(out['states']['isentropic']):
            return out | dict(status='unsupported_phase', stage='PS')
        target = a.aggregate.h_J_mol+(ps.caloric.aggregate.h_J_mol-a.aggregate.h_J_mol)/i['eta']
        ph = provider.flash_PH(PHSpecification(i['P2'], target, z, PROVENANCE), BIP)
        out['diagnostics']['PH'] = inverse(ph)
        if ph.caloric is None or ph.status != 'success':
            return out | dict(status='production_failure', stage='PH', reason=ph.status)
        out['states']['outlet'] = state(ph.caloric)
        if not liquid(out['states']['outlet']):
            return out | dict(status='unsupported_phase', stage='PH')
    out['metrics'] = finish(i, out['states'])
    return out | dict(status='accepted' if out['metrics']['work_resolved'] else 'unresolved_work', stage='complete')


def compare(i, r, p):
    checks = []
    def check(field, actual, expected, allowance=0.):
        err = abs(actual-expected)
        checks.append(dict(field=field, actual=actual, reference=expected,
                           error=err, allowance=allowance, passed=err <= allowance))
    def equal(field, actual, expected):
        checks.append(dict(field=field, actual=actual, reference=expected, passed=actual == expected))
    # Partial states remain comparable even if either inverse path is unavailable.
    for key in sorted(r['states'].keys() & p['states'].keys()):
        a, b = p['states'][key], r['states'][key]
        equal(key+'.classification', a['classification'], b['classification'])
        for field, tol in [('T_K', TOLS['T']), ('P_Pa_abs', 0.), ('beta', 2e-9),
            ('H_eq_J_mol', h_budget(b['H_eq_J_mol'])),
            ('S_eq_J_mol_K', TOLS['S_abs']+TOLS['S_rel']*abs(b['S_eq_J_mol_K']))]:
            check(key+'.'+field, a[field], b[field], tol)
        for j in range(2):
            check(key+'.z'+str(j), a['z'][j], b['z'][j], TOLS['composition'])
        equal(key+'.phase_set', sorted(a['phases']), sorted(b['phases']))
        for phase in sorted(a['phases'].keys() & b['phases'].keys()):
            v, w = a['phases'][phase], b['phases'][phase]
            for field, tol in [('Z', TOLS['Z_abs']+TOLS['Z_rel']*abs(w['Z'])),
                ('h_J_mol', h_budget(w['h_J_mol'])),
                ('s_J_mol_K', TOLS['S_abs']+TOLS['S_rel']*abs(w['s_J_mol_K']))]:
                check(key+'.'+phase+'.'+field, v[field], w[field], tol)
            for j in range(2):
                check(key+'.'+phase+'.q'+str(j), v['composition'][j], w['composition'][j], TOLS['composition'])
        if liquid(a):
            stability = a['PT_diagnostics']['stability']
            equal(key+'.stable', stability['stable'], True)
            equal(key+'.stability_converged', stability['converged'], True)
            equal(key+'.pip_liquid', stability['phase_identification_parameter'] > 1, True)
    if 'metrics' in r and 'metrics' in p:
        a, b = p['metrics'], r['metrics']
        h1, hs, h2 = [h_budget(r['states'][k]['H_eq_J_mol']) for k in ('inlet', 'isentropic', 'outlet')]
        budgets = dict(delta_h_s_J_mol=h1+hs, delta_h_J_mol=h1+h2,
            h_target_J_mol=h1+(h1+hs)/i['eta'],
            W_target_W=i['flow']*(h1+hs)/i['eta'], W_recovered_W=i['flow']*(h1+h2))
        for k, tol in budgets.items():
            check(k, a[k], b[k], tol)
        check('PH_target_recovered', a['target_recovered_residual_J_mol'], 0., TOLS['PH_residual'])
        check('mass_balance', a['mass_residual_kg_s'], 0., 1e-12)
        for j in range(2):
            check('component_flow'+str(j), a['component_out_mol_s'][j], a['component_in_mol_s'][j], 1e-10)
        equal('work_resolution_policy', a['work_resolved'], b['work_resolved'])
        equal('entropy_generation', a['delta_s_J_mol_K'] >= -2e-8, True)
        if a['identity']:
            check('identity_power', a['W_recovered_W'], 0.)
            equal('identity_efficiency', a['reconstructed_efficiency'], None)
            equal('identity_diagnostics', p['diagnostics'], {})
        else:
            equal('positive_work', a['delta_h_J_mol'] > 0 and a['delta_h_s_J_mol'] > 0, True)
            if a['work_resolved']:
                # Conservative propagation of both independent enthalpy differences.
                dh = b['delta_h_J_mol']
                tol = ((h1+hs)+abs(b['raw_efficiency_diagnostic'])*(h1+h2))/(abs(dh)-(h1+h2))
                check('efficiency_reference', a['reconstructed_efficiency'], b['reconstructed_efficiency'], tol)
                check('efficiency_target', a['reconstructed_efficiency'], i['eta'], i['eta']*1e-6/abs(a['delta_h_J_mol'])+1e-12)
            if i['eta'] == 1:
                check('ideal_T', p['states']['outlet']['T_K'], p['states']['isentropic']['T_K'], 1e-7)
                check('ideal_S', a['delta_s_J_mol_K'], 0., 2e-8)
    for key, d in p['diagnostics'].items():
        if d['status'] == 'success':
            equal(key+'.candidates', d['candidate_count'], 1)
            equal(key+'.scan_count', d['scan_count'], 64 if key == 'PS' else 128)
            equal(key+'.fresh_final', d['fresh_final_count'], 1)
            check(key+'.residual', d['residual'], 0., TOLS[key+'_residual'])
    return checks


def standalone_ph(i, reference):
    """Reference-target diagnostic after PS failure; never an accepted pump path."""
    provider = PengRobinsonProvider()
    target = reference['metrics']['h_target_J_mol']
    result = provider.flash_PH(PHSpecification(i['P2'], target,
        MolarComposition(IDS, i['z']), PROVENANCE), BIP)
    return dict(purpose='Independent-target standalone PH only; failed PS remains failed',
                diagnostics=inverse(result),
                state=state(result.caloric) if result.caloric else None)


def build():
    frozen = json.loads(REFERENCE.read_text())
    assert frozen['tolerances'] == TOLS
    rows = []
    for c in frozen['cases']:
        result = calculate(c['inputs'])
        checks = compare(c['inputs'], c['result'], result)
        row = dict(case_id=c['case_id'], result=result, checks=checks,
                   comparisons_passed=all(q['passed'] for q in checks))
        if result['stage'] == 'PS' and result['status'] == 'production_failure' and 'metrics' in c['result']:
            row['standalone_PH_diagnostic'] = standalone_ph(c['inputs'], c['result'])
        rows.append(row)
        print(c['case_id'], result['status'], result['stage'], len(checks), row['comparisons_passed'], flush=True)
    probes = []
    provider = PengRobinsonProvider()
    for group in frozen['boundary_probes']:
        for q in group.get('probes', []):
            if 'state' not in q:
                continue
            r = q['state']
            c = provider.equilibrium_caloric_PT(ThermodynamicState(r['T_K'], r['P_Pa_abs'], MolarComposition(IDS, r['z']), PROVENANCE), BIP, SolverSettings.high_accuracy())
            probes.append(dict(name=group['name'], offset_K=q['offset_K'], status=c.status,
                               state=state(c) if c.aggregate else None, reference_classification=r['classification']))
    r = frozen['pure_supercritical_label_probe']['state']
    c = provider.equilibrium_caloric_PT(ThermodynamicState(r['T_K'], r['P_Pa_abs'],
        MolarComposition(IDS, r['z']), PROVENANCE), BIP, SolverSettings.high_accuracy())
    return dict(reference_sha256=digest(REFERENCE), comparison_source_sha256=digest(__file__),
                production_source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'engine/riogineer_engine').glob('*.py'))},
                cases=rows, boundary_probes=probes, pure_supercritical_label_probe=state(c) if c.aggregate else dict(status=c.status),
                comparison_count=sum(len(r['checks']) for r in rows),
                failed_comparison_count=sum(not q['passed'] for r in rows for q in r['checks']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = build()
    raw = encode(data)
    if args.write:
        PRODUCTION.write_text(raw)
    else:
        assert PRODUCTION.read_text() == raw, 'Production evidence reproduction differs'
    print('Recorded', data['comparison_count'], 'comparisons;', data['failed_comparison_count'], 'failed')
