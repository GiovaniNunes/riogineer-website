"""Independent compressor experiment; no production dependencies or fallback model."""
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT, TrialFailure, IDS, finite
from benchmarks.peng_robinson_ps.solver import solve_ps
from benchmarks.peng_robinson_ph.solver import solve_ph

ZERO = ((0., 0.), (0., 0.))


def failure(category, stage, message, underlying=None):
    out = dict(status=category, failure_stage=stage, message=message, accepted_outlet=False)
    if underlying is not None:
        out['solver_failure'] = underlying
    return out


def calculate(P1, T1, P2, eta, flow, z, component_ids=IDS, kij=ZERO,
              service='vapor', oracle=None, ps_solver=solve_ps, ph_solver=solve_ph):
    """One adiabatic stage, positive power into fluid; benchmark service policy only."""
    if not finite(flow) or flow <= 0:
        return failure('invalid_flow', 'input', 'Positive finite molar flow required')
    if not all(finite(p) and p > 0 for p in (P1, P2)) or P2 <= P1:
        return failure('invalid_pressure', 'input', 'P2 > P1 > 0 required')
    if not finite(eta) or not 0 < eta <= 1:
        return failure('invalid_efficiency', 'input', '0 < eta <= 1 required; no clamping')
    if not isinstance(component_ids, (list, tuple)) or tuple(component_ids) != IDS:
        return failure('unsupported_components', 'input', 'Ordered methane/n_hexane only')
    if not isinstance(z, (list, tuple)) or len(z) != 2 or not all(finite(v) and v >= 0 for v in z) or abs(sum(z)-1) > 1e-12:
        return failure('invalid_composition', 'input', 'Normalized nonnegative mole fractions required')
    if not isinstance(kij, (list, tuple)) or len(kij) != 2 or any(
        not isinstance(row, (list, tuple)) or len(row) != 2 or any(not finite(v) or v != 0 for v in row) for row in kij):
        return failure('unsupported_bip', 'input', 'Explicit constant zero 2x2 kij required')
    if not finite(T1) or not 200 <= T1 <= 500:
        return failure('temperature_domain_invalid', 'input', 'Qualified 200–500 K only')
    if service not in ('vapor', 'thermodynamic_only'):
        return failure('compressor_state_invalid', 'input', 'Unknown service policy')
    pt = oracle or EntropyPT()
    try:
        a = pt.evaluate(T1, P1, z)
    except TrialFailure as error:
        return failure('pt_failure', 'inlet', str(error))
    if service == 'vapor' and a['classification'] != 'single_vapor':
        return failure('compressor_state_invalid', 'inlet', 'Outside initial vapor compressor service; not a PT failure')
    ps = ps_solver(P2, z, a['S_eq_J_mol_K'], evaluator=pt.evaluate)
    if ps['status'] != 'success':
        return failure('ps_failure', 'isentropic', ps['message'], ps)
    b = ps['solution']
    dhs = b['H_eq_J_mol']-a['H_eq_J_mol']
    target = a['H_eq_J_mol']+dhs/eta
    if not finite(target) or dhs <= 0:
        return failure('compressor_state_invalid', 'isentropic', 'Nonpositive isentropic rise or nonfinite target')
    ph = ph_solver(P2, z, target, bounds=(200., 500.), evaluator=pt.evaluate)
    if ph['status'] != 'success':
        return failure('ph_failure', 'actual_outlet', ph['message'], ph)
    c = ph['solution']
    if service == 'vapor' and any(s['classification'] != 'single_vapor' for s in (b, c)):
        return failure('compressor_state_invalid', 'actual_outlet', 'Phase transition outside initial vapor service')
    dh = c['H_eq_J_mol']-a['H_eq_J_mol']
    power = flow*dh
    if not finite(power) or dh <= 0:
        return failure('compressor_state_invalid', 'actual_outlet', 'Nonpositive actual rise or nonfinite power')
    return dict(status='success', accepted_outlet=True, service=service,
                inlet=a, isentropic=b, outlet=c, PS=ps['diagnostics'], PH=ph['diagnostics'],
                H2_target_J_mol=target, delta_H_is_J_mol=dhs, delta_H_actual_J_mol=dh,
                reconstructed_eta=dhs/dh, eta_error=dhs/dh-eta,
                eta_power=(flow*dhs)/power, isentropic_fluid_power_W=flow*dhs,
                fluid_power_W=power, power_identity_error_W=power-flow*dhs/eta,
                energy_residual_W=math.fsum([power, flow*a['H_eq_J_mol'], -flow*c['H_eq_J_mol']]),
                delta_S_actual_J_mol_K=c['S_eq_J_mol_K']-a['S_eq_J_mol_K'],
                molar_flow_in_mol_s=flow, molar_flow_out_mol_s=flow,
                mass_balance_residual_mol_s=0., z_in=list(z), z_out=list(z), composition_residual=[0.,0.])
