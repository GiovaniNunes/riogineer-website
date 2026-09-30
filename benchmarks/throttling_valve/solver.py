"""Independent adiabatic throttling experiment; no production imports."""
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT, TrialFailure, IDS, finite
from benchmarks.peng_robinson_ph.solver import solve_ph, H_TOL

ZERO = ((0., 0.), (0., 0.))


def failure(status, stage, message, inverse=None):
    result = dict(status=status, failure_stage=stage, message=message, accepted_outlet=False)
    if inverse is not None:
        result['PH_failure'] = inverse
    return result


def valid_state(s, T, P, z):
    if not (s['T_K'] == T and 200 <= T <= 500 and s['P_Pa_abs'] == P and s['z'] == list(z)):
        return False
    if not all(finite(s[k]) for k in ('H_eq_J_mol', 'S_eq_J_mol_K', 'beta')):
        return False
    b = s['beta']
    expected = {'single_liquid': {'liquid'}, 'single_vapor': {'vapor'}, 'vapor_liquid': {'liquid', 'vapor'}}
    if s['classification'] not in expected or set(s['phases']) != expected[s['classification']]:
        return False
    if not (0 <= b <= 1) or (s['classification'] == 'vapor_liquid' and not 0 < b < 1):
        return False
    if s['classification'] == 'single_liquid' and b != 0 or s['classification'] == 'single_vapor' and b != 1:
        return False
    weights = {'liquid': 1-b, 'vapor': b}
    for p in s['phases'].values():
        if len(p['composition']) != 2 or not all(finite(v) and 0 <= v <= 1 for v in p['composition']):
            return False
        if abs(sum(p['composition'])-1) > 1e-10 or not all(finite(p[k]) for k in ('Z', 'h_J_mol', 's_J_mol_K')):
            return False
    material = [math.fsum(weights[k]*p['composition'][j] for k,p in s['phases'].items())-z[j] for j in range(2)]
    reconstructed = math.fsum(weights[k]*p['h_J_mol'] for k,p in s['phases'].items())
    return max(map(abs, material)) <= 1e-10 and abs(reconstructed-s['H_eq_J_mol']) <= H_TOL


def calculate(Pin, Tin, Pout, F, z, ids=IDS, kij=ZERO, service='single_phase_inlet',
              oracle=None, ph_solver=solve_ph, controls=None, qualified_interval=(200., 500.)):
    """Positive pressure reduction, supplied molar flow, one overall outlet."""
    if not finite(F) or F <= 0:
        return failure('invalid_flow', 'specification', 'Positive finite flow required')
    if not all(finite(v) and v > 0 for v in (Pin, Pout)) or Pout >= Pin:
        return failure('invalid_pressure', 'specification', 'Require 0 < Pout < Pin')
    if not finite(Tin) or not 200 <= Tin <= 500:
        return failure('temperature_domain_invalid', 'specification', 'Qualified 200–500 K domain')
    if not isinstance(ids, (list, tuple)) or tuple(ids) != IDS:
        return failure('unsupported_component', 'specification', 'Ordered methane/n_hexane only')
    if not isinstance(z, (list, tuple)) or len(z) != 2 or not all(finite(v) and v >= 0 for v in z) or abs(sum(z)-1) > 1e-12:
        return failure('invalid_composition', 'specification', 'Normalized nonnegative binary composition required')
    if not isinstance(kij, (list, tuple)) or len(kij) != 2 or any(not isinstance(r, (list, tuple)) or len(r) != 2 or any(not finite(v) or v != 0 for v in r) for r in kij):
        return failure('unsupported_bip', 'specification', 'Explicit constant zero 2x2 kij required')
    if service not in ('single_phase_inlet', 'thermodynamic_study'):
        return failure('invalid_service', 'specification', 'Unknown study policy')
    if (not isinstance(qualified_interval, (list, tuple)) or len(qualified_interval) != 2 or
        not all(finite(v) for v in qualified_interval) or not 200 <= qualified_interval[0] < qualified_interval[1] <= 500):
        return failure('temperature_domain_invalid', 'specification', 'Explicit qualified interval must lie within 200–500 K')
    pt = oracle or EntropyPT()
    try:
        inlet = pt.evaluate(Tin, Pin, z)
    except TrialFailure as e:
        return failure('pt_evaluation_failure', 'inlet_PT', str(e))
    if not valid_state(inlet, Tin, Pin, z):
        return failure('invalid_state', 'inlet_PT', 'Invalid inlet thermodynamic state')
    if service == 'single_phase_inlet' and inlet['classification'] == 'vapor_liquid':
        return failure('inlet_service_scope', 'service_scope', 'Two-phase inlet retained as separate study')
    target = inlet['H_eq_J_mol']
    ph = ph_solver(Pout, z, target, bounds=tuple(qualified_interval), evaluator=pt.evaluate, **(controls or {}))
    if ph['status'] != 'success':
        return failure(ph['status'], 'outlet_PH', ph.get('message', ''), ph)
    out, d = ph['solution'], ph['diagnostics']
    if not qualified_interval[0] <= out['T_K'] <= qualified_interval[1] or len(d['brackets']) != 1 or d['final_evaluations'] != 1 or not valid_state(out, out['T_K'], Pout, z) or abs(out['H_eq_J_mol']-target) > H_TOL:
        return failure('final_acceptance_failed', 'final_acceptance', 'Unique, fresh, physical outlet required')
    # Additional fresh endpoint evaluation verifies the state actually being published.
    try:
        fresh = pt.evaluate(out['T_K'], Pout, z)
    except TrialFailure as e:
        return failure('pt_evaluation_failure', 'final_acceptance', str(e))
    if not valid_state(fresh, out['T_K'], Pout, z) or fresh['classification'] != out['classification'] or abs(fresh['H_eq_J_mol']-target) > H_TOL:
        return failure('final_acceptance_failed', 'final_acceptance', 'Fresh endpoint failed closure or phase checks')
    dh = fresh['H_eq_J_mol']-target
    energy = F*dh
    if not finite(energy):
        return failure('nonfinite_energy_residual', 'final_acceptance', 'Nonfinite extensive closure')
    return dict(status='success', accepted_outlet=True, inlet=inlet, outlet=fresh, PH=d,
                H_out_target_J_mol=target, enthalpy_residual_J_mol=dh, PH_residual_J_mol=dh,
                energy_residual_W=energy, energy_allowance_W=F*H_TOL,
                delta_S_J_mol_K=fresh['S_eq_J_mol_K']-inlet['S_eq_J_mol_K'],
                delta_T_K=fresh['T_K']-Tin, pressure_ratio=Pout/Pin, pressure_reduction_Pa=Pin-Pout,
                F_in_mol_s=F, F_out_mol_s=F, z_in=list(z), z_out=list(z),
                component_residual_mol_s=[F*(a-b) for a,b in zip(fresh['z'],inlet['z'])],
                final_endpoint_evaluations=1)
