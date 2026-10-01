"""Pre-M18 study policy and arithmetic only; no thermodynamic implementation."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'liquid_pump_path_reference.json'
PRODUCTION = HERE / 'production_comparison.json'
BASELINE = '81d183d804755bcf6e995b1c126407a4404cf94a'
IDS = ('methane', 'n_hexane')
MW = (16.0428, 86.17536)
# Fixed before production comparison: inherited state gates; propagated work budget.
TOLS = dict(T=1e-7, H_abs=1e-6, H_rel=1e-11, S_abs=1e-8,
            S_rel=1e-11, Z_abs=2e-10, Z_rel=1e-9, composition=2e-9,
            PS_residual=1e-8, PH_residual=1e-6, work_relative_limit=1e-4)


def encode(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate(i):
    """Benchmark prototype guards, not production pump functionality."""
    if not finite(i['flow']) or i['flow'] <= 0:
        return 'invalid_flow'
    if not all(finite(i[k]) and i[k] > 0 for k in ('P1', 'P2')) or i['P2'] < i['P1']:
        return 'invalid_pressure'
    if not finite(i['eta']) or not 0 < i['eta'] <= 1:
        return 'invalid_efficiency'
    if not finite(i['T1']) or not 200 <= i['T1'] <= 500:
        return 'temperature_domain_invalid'
    z = i['z']
    if not isinstance(z, (list, tuple)) or len(z) != 2 or not all(finite(v) and v >= 0 for v in z) or abs(sum(z)-1) > 1e-12:
        return 'invalid_composition'
    if tuple(i.get('component_ids', IDS)) != IDS:
        return 'unsupported_components'
    if i.get('kij', [[0., 0.], [0., 0.]]) != [[0., 0.], [0., 0.]]:
        return 'unsupported_bip'
    return None


def liquid(s):
    return s['classification'] == 'single_liquid' and s['beta'] == 0 and set(s['phases']) == {'liquid'}


def h_budget(h):
    return TOLS['H_abs'] + TOLS['H_rel']*abs(h)


def finish(i, states):
    """Bookkeeping independently compared to stored oracle thermodynamics."""
    a, b, c = (states[k] for k in ('inlet', 'isentropic', 'outlet'))
    h1, hs, h2 = (s['H_eq_J_mol'] for s in (a, b, c))
    identity = i['P1'] == i['P2']
    ds, dh = hs-h1, h2-h1
    target = h1 if identity else h1+ds/i['eta']
    budget = h_budget(h1)+h_budget(h2)
    # Conservative prospective accuracy qualification, distinct from positive sign.
    resolved = identity or (ds > 0 and dh > 0 and budget/dh <= TOLS['work_relative_limit'])
    F = i['flow']
    component_in = [F*z for z in i['z']]
    component_out = [F*z for z in c['z']]
    mass_in = [v*m/1000 for v, m in zip(component_in, MW)]
    mass_out = [v*m/1000 for v, m in zip(component_out, MW)]
    return dict(identity=identity, delta_h_s_J_mol=ds, delta_h_J_mol=dh,
                h_target_J_mol=target, W_target_W=F*(target-h1), W_recovered_W=F*dh,
                target_recovered_residual_J_mol=h2-target,
                reconstructed_efficiency=None if identity or not resolved else ds/dh,
                raw_efficiency_diagnostic=None if identity or dh == 0 else ds/dh,
                delta_s_J_mol_K=c['S_eq_J_mol_K']-a['S_eq_J_mol_K'],
                work_error_budget_J_mol=budget,
                relative_work_budget=None if identity or dh == 0 else budget/abs(dh),
                work_resolved=resolved,
                component_in_mol_s=component_in, component_out_mol_s=component_out,
                component_mass_in_kg_s=mass_in, component_mass_out_kg_s=mass_out,
                mass_residual_kg_s=math.fsum(mass_in)-math.fsum(mass_out),
                energy_identity_residual_W=math.fsum([F*h2, -F*h1, -F*dh]))


def cases(bubble_below):
    base = dict(T1=300., P1=20e6, P2=30e6, eta=.8, flow=100., z=[.5, .5])
    rows = [('CANONICAL', 'pressure', {}), ('P22', 'pressure', dict(P2=22e6)),
            ('ETA1', 'efficiency', dict(eta=1.)), ('ETA06', 'efficiency', dict(eta=.6)),
            ('HEXANE_P2', 'pure', dict(P1=1e6, P2=2e6, z=[0., 1.])),
            ('HEXANE_P6', 'pure', dict(P1=1e6, P2=6e6, z=[0., 1.])),
            ('T350', 'temperature', dict(T1=350.)),
            ('HEXANE_RICH', 'composition', dict(P1=6e6, P2=10e6, z=[.1, .9])),
            ('BUBBLE_BELOW', 'boundary', dict(P1=6e6, P2=8e6, T1=bubble_below)),
            ('BUBBLE_MINUS_01', 'boundary', dict(P1=6e6, P2=8e6, T1=bubble_below+.4)),
            ('BUBBLE_PLUS_01', 'boundary', dict(P1=6e6, P2=8e6, T1=bubble_below+.6)),
            ('FLOW5', 'flow', dict(flow=5.)), ('FLOW200', 'flow', dict(flow=200.)),
            ('IDENTITY_BINARY', 'identity', dict(P2=20e6)),
            ('IDENTITY_HEXANE', 'identity', dict(P1=1e6, P2=1e6, z=[0., 1.])),
            ('VAPOR_REJECTION', 'service', dict(P1=1e3, P2=2e3))]
    rows += [('DP_'+str(dp), 'conditioning', dict(P2=20e6+dp)) for dp in (1000., 10., .1, .001)]
    return [dict(case_id=n, group=g, inputs=base | patch) for n, g, patch in rows]
