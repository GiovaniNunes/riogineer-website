"""Independent liquid pump-path oracle. No production numerical imports."""
import argparse
import importlib.metadata
import inspect
import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmarks.pump_energy.common import (ROOT, HERE, REFERENCE, BASELINE, IDS, TOLS,
    cases, encode, digest, validate, liquid, finish)
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT, TrialFailure
from benchmarks.peng_robinson_ps.solver import solve_ps
from benchmarks.peng_robinson_ph.solver import solve_ph
from benchmarks.peng_robinson_caloric import reference as caloric


def calculate(i, oracle):
    error = validate(i)
    out = dict(status=error or 'pending', states={}, diagnostics={})
    if error:
        return out | dict(stage='input')
    try:
        a = oracle.evaluate(i['T1'], i['P1'], i['z'])
    except TrialFailure as e:
        return out | dict(status='reference_unavailable', stage='inlet_PT', reason=str(e))
    out['states']['inlet'] = a
    if not liquid(a):
        return out | dict(status='unsupported_phase', stage='inlet_PT')
    if i['P1'] == i['P2']:
        out['states'].update(isentropic=a, outlet=a)
    else:
        ps = solve_ps(i['P2'], i['z'], a['S_eq_J_mol_K'], evaluator=oracle.evaluate)
        out['diagnostics']['PS'] = ps
        if ps['status'] != 'success':
            return out | dict(status='reference_unavailable', stage='PS', reason=ps['status'])
        b = ps['solution']
        out['states']['isentropic'] = b
        if not liquid(b):
            return out | dict(status='unsupported_phase', stage='PS')
        target = a['H_eq_J_mol']+(b['H_eq_J_mol']-a['H_eq_J_mol'])/i['eta']
        ph = solve_ph(i['P2'], i['z'], target, bounds=(200., 500.), evaluator=oracle.evaluate)
        out['diagnostics']['PH'] = ph
        if ph['status'] != 'success':
            return out | dict(status='reference_unavailable', stage='PH', reason=ph['status'])
        out['states']['outlet'] = ph['solution']
        if not liquid(ph['solution']):
            return out | dict(status='unsupported_phase', stage='PH')
    out['metrics'] = finish(i, out['states'])
    return out | dict(status='accepted' if out['metrics']['work_resolved'] else 'unresolved_work', stage='complete')


def boundary_probes(oracle):
    """Independent saturation calculation plus explicit two-sided PT probes."""
    rows = []
    for name, P, z in [('binary', 6e6, [.5, .5]), ('hexane', 1e6, [0., 1.])]:
        try:
            sat = oracle.flash.flash(P=P, VF=0., zs=z)
            row = dict(name=name, P_Pa_abs=P, z=z, bubble_T_K=sat.T, probes=[])
            for offset in (-.5, -.1, -.001, 0., .001, .1):
                try:
                    state = oracle.evaluate(sat.T+offset, P, z)
                    row['probes'].append(dict(offset_K=offset, state=state))
                except TrialFailure as e:
                    row['probes'].append(dict(offset_K=offset, unavailable=str(e)))
            rows.append(row)
        except Exception as e:
            rows.append(dict(name=name, unavailable=type(e).__name__+': '+str(e)))
    return rows


def endpoint_boundaries(rows, oracle):
    """Local saturation corroboration, explicitly not a mixture critical locus."""
    states = {}
    for row in rows:
        for name, s in row['result']['states'].items():
            key = (s['T_K'], s['P_Pa_abs'], tuple(s['z']))
            if key in states or not liquid(s):
                continue
            record = dict(T_K=s['T_K'], P_Pa_abs=s['P_Pa_abs'], z=s['z'], probes=[])
            try:
                bubble = oracle.flash.flash(T=s['T_K'], VF=0., zs=s['z'])
                record.update(bubble_P_Pa_abs=bubble.P,
                              relative_pressure_margin=(s['P_Pa_abs']-bubble.P)/bubble.P)
                for factor in (.999, 1.001):
                    try:
                        q = oracle.evaluate(s['T_K'], bubble.P*factor, s['z'])
                        record['probes'].append(dict(pressure_factor=factor,
                            classification=q['classification'], beta=q['beta']))
                    except TrialFailure as e:
                        record['probes'].append(dict(pressure_factor=factor, unavailable=str(e)))
            except Exception as e:
                record['unavailable'] = type(e).__name__+': '+str(e)
            states[key] = record
    return list(states.values())


def cross_method(rows, oracle):
    """Tighter direct-caloric roots; shares library PT, not a second EOS."""
    checks = []
    for row in rows:
        if row['case_id'] not in ('CANONICAL', 'DP_1000.0', 'DP_0.001'):
            continue
        i, r = row['inputs'], row['result']
        inlet = oracle.evaluate(i['T1'], i['P1'], i['z'])
        ps = solve_ps(i['P2'], i['z'], inlet['S_eq_J_mol_K'], evaluator=oracle.evaluate,
                      direct=True, xtol=1e-12)
        record = dict(case_id=row['case_id'], PS=ps)
        if ps['status'] == 'success':
            target = inlet['H_eq_J_mol']+(ps['solution']['H_eq_J_mol']-inlet['H_eq_J_mol'])/i['eta']
            ph = solve_ph(i['P2'], i['z'], target, evaluator=oracle.evaluate,
                          direct=True, method='bisect', xtol=1e-12)
            record['PH'] = ph
            if ph['status'] == 'success':
                dh = ph['solution']['H_eq_J_mol']-inlet['H_eq_J_mol']
                record.update(delta_h_J_mol=dh,
                    difference_from_primary_J_mol=dh-r['metrics']['delta_h_J_mol'],
                    relative_difference_from_primary=abs(dh-r['metrics']['delta_h_J_mol'])/abs(dh))
        checks.append(record)
    return checks


def build():
    old = json.loads((ROOT/'benchmarks/peng_robinson_ps/methane_nhexane_pr_ps_reference.json').read_text())
    # Read the exact documented forward temperature, never its printed rounding.
    entry = next(c for c in old['cases'] if c['case_id'] == 'BUBBLE_BELOW')
    bubble = entry['forward']['T_K']
    oracle = EntropyPT()
    rows = []
    for c in cases(bubble):
        result = calculate(c['inputs'], oracle)
        rows.append(c | dict(result=result))
        print(c['case_id'], result['status'], result['stage'], flush=True)
    sources = [Path(__file__), HERE/'common.py']
    sources += [ROOT/'benchmarks'/p for p in (
        'peng_robinson_ps/equilibrium.py', 'peng_robinson_ps/solver.py',
        'peng_robinson_ph/equilibrium.py', 'peng_robinson_ph/solver.py',
        'peng_robinson_caloric/reference.py', 'peng_robinson_caloric/equations.py',
        'peng_robinson_ps/methane_nhexane_pr_ps_reference.json',
        'peng_robinson/methane_nhexane_pr_reference.json')]
    library_sources = {inspect.getfile(obj) for obj in (caloric.PR, caloric.PRMIX,
        caloric.CEOSGas, caloric.CEOSLiquid, caloric.FlashVL, caloric.HeatCapacityGas)}
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    critical_probe = oracle.evaluate(300., 30e6, [1., 0.])
    # A pure-fluid counterexample is not used as a mixture critical criterion.
    pure_supercritical = dict(state=critical_probe, pure_Tc_K=190.564,
        pure_Pc_Pa_abs=4599200., interpretation='T>Tc and P>Pc but oracle labels single_liquid')
    return dict(study='independent_liquid_pump_path@1.0', baseline=BASELINE,
        production_numerics_imported=False, python=platform.python_version(),
        dependencies={n: importlib.metadata.version(n) for n in ('thermo', 'chemicals', 'fluids', 'numpy', 'scipy', 'pandas', 'teqp', 'python-dateutil', 'pytz', 'six', 'tzdata')},
        source_sha256={str(p.relative_to(ROOT)): digest(p) for p in sources},
        library_source_sha256={Path(p).name: digest(p) for p in sorted(library_sources)},
        cp_source_sha256=digest(Path(caloric.hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv'),
        components=caloric.COMPONENTS, cp_data=caloric.CP_DATA, kij=caloric.KIJ,
        convention=dict(Tref_K=298.15, Pref_Pa_abs=101325., ideal_pure_h_s_zero=True,
                        PR_a=.45724, PR_b=.07780, R=caloric.R),
        units=dict(T='K', P='Pa absolute', h='J/mol', s='J/(mol K)', flow='mol/s', power='W'),
        tolerances=TOLS, cases=rows, boundary_probes=boundary_probes(oracle),
        endpoint_boundaries=endpoint_boundaries(rows, oracle),
        pure_supercritical_label_probe=pure_supercritical,
        cross_method=cross_method(rows, oracle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = build()
    raw = encode(data)
    if args.write:
        REFERENCE.write_text(raw)
    else:
        assert REFERENCE.read_text() == raw, 'Independent artifact reproduction differs'
    print('PASS independent', len(data['cases']), 'candidates; sha256', digest(REFERENCE))


if __name__ == '__main__':
    main()
