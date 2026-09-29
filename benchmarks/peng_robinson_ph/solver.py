"""Benchmark-only PH inversion. Forward reference temperature is never an input."""
from scipy.optimize import brentq, bisect
try:
    from .equilibrium import IndependentPT, TrialFailure, IDS, finite
except ImportError:
    from equilibrium import IndependentPT, TrialFailure, IDS, finite

H_TOL = 1e-6


def solve_ph(P, z, H_target, bounds=(200., 500.), component_ids=IDS,
             grid_points=128, xtol=1e-10, maxiter=100, method='brentq',
             direct=False, evaluator=None):
    diagnostics = dict(scan=[], brackets=[], roots=[], root_trials=[], scan_evaluations=0,
                       root_evaluations=0, final_evaluations=0)

    def result(status, message='', solution=None):
        diagnostics['total_evaluations'] = sum(diagnostics[k] for k in
            ('scan_evaluations', 'root_evaluations', 'final_evaluations'))
        out = dict(status=status, message=message, diagnostics=diagnostics)
        if solution is not None:
            out['solution'] = solution
        return out

    if not isinstance(component_ids, (list, tuple)) or tuple(component_ids) != IDS:
        return result('unsupported_component', 'Only methane/n_hexane in declared order')
    if (not finite(P) or P <= 0 or not finite(H_target) or
        not isinstance(z, (list, tuple)) or len(z) != 2 or
        not all(finite(v) and v >= 0 for v in z) or abs(sum(z)-1) > 1e-12):
        return result('invalid_input', 'Positive finite P, finite H and normalized molar z required')
    if (not isinstance(bounds, (list, tuple)) or len(bounds) != 2 or not all(finite(v) for v in bounds) or
        not 200 <= bounds[0] < bounds[1] <= 1000):
        return result('temperature_domain_invalid', 'Bounds must lie within joint Cp range 200–1000 K')
    if (not isinstance(grid_points, int) or grid_points < 3 or
        not finite(xtol) or xtol <= 0 or not isinstance(maxiter, int) or maxiter < 1 or
        method not in ('brentq', 'bisect')):
        return result('invalid_input', 'Invalid solver controls')
    oracle = evaluator or IndependentPT().evaluate
    key = 'H_eq_direct_J_mol' if direct else 'H_eq_J_mol'

    def evaluate(T, stage):
        diagnostics[stage+'_evaluations'] += 1
        state = oracle(float(T), P, z)
        F = state[key]-H_target
        if stage == 'root':
            diagnostics['root_trials'].append(dict(T_K=float(T), F_J_mol=F,
                classification=state['classification'], beta=state['beta']))
        return state, F

    failures = []
    lo, hi = bounds
    for i in range(grid_points):
        T = lo+(hi-lo)*i/(grid_points-1)
        try:
            state, F = evaluate(T, 'scan')
            row = dict(T_K=T, P_Pa_abs=P, z=list(z), status='success',
                       classification=state['classification'], beta=state['beta'],
                       H_eq_J_mol=state[key], F_J_mol=F,
                       phase_h_J_mol={k:v['h_J_mol'] for k,v in state['phases'].items()})
        except TrialFailure as error:
            failures.append(error)
            row = dict(T_K=T, P_Pa_abs=P, z=list(z), status=error.stage+'_evaluation_failure', message=str(error))
        diagnostics['scan'].append(row)
    rows = diagnostics['scan']
    if failures:
        # Refuse to certify uniqueness across a domain with holes. Never bridge them.
        diagnostics['monotonicity'] = 'unresolved'
        return result(failures[0].stage+'_evaluation_failure', str(failures[0]))
    differences = [b['H_eq_J_mol']-a['H_eq_J_mol'] for a,b in zip(rows,rows[1:])]
    diagnostics['monotonicity'] = ('increasing' if min(differences)>0 else
                                  'decreasing' if max(differences)<0 else 'nonmonotonic')
    diagnostics['phase_transitions'] = [[a['T_K'], b['T_K'], a['classification'], b['classification']]
        for a,b in zip(rows,rows[1:]) if a['classification'] != b['classification']]
    for row in rows:
        if row['F_J_mol'] == 0:
            diagnostics['brackets'].append(dict(T_low=row['T_K'], T_high=row['T_K'], F_low=0., F_high=0.))
    for a,b in zip(rows, rows[1:]):
        if a['F_J_mol']*b['F_J_mol'] < 0:
            diagnostics['brackets'].append(dict(T_low=a['T_K'], T_high=b['T_K'], F_low=a['F_J_mol'], F_high=b['F_J_mol']))
    if not diagnostics['brackets']:
        return result('enthalpy_target_not_bracketed', 'No adjacent valid sign change or exact root')
    states = []
    try:
        for bracket in diagnostics['brackets']:
            low, high = bracket['T_low'], bracket['T_high']
            if low == high:
                T, iterations = low, 0
            else:
                fn = brentq if method == 'brentq' else bisect
                T, info = fn(lambda t: evaluate(t, 'root')[1], low, high,
                             xtol=xtol, rtol=1e-14, maxiter=maxiter, full_output=True)
                iterations = info.iterations
            # Fresh independent state; no cached solver state is published.
            state, F = evaluate(T, 'final')
            physical_residual = state['H_eq_J_mol']-H_target
            diagnostics['roots'].append(dict(T_K=T, iterations=iterations,
                residual_J_mol=physical_residual, equation_residual_J_mol=F))
            if abs(physical_residual) > H_TOL or abs(F) > H_TOL:
                return result('ph_nonconvergence', 'Final absolute enthalpy residual failed')
            state.update(H_residual_J_mol=physical_residual,
                         H_absolute_residual_J_mol=abs(physical_residual),
                         H_normalized_residual=physical_residual/max(abs(H_target),1.))
            if not any(abs(T-s['T_K']) < 1e-7 for s in states):
                states.append(state)
    except TrialFailure as error:
        return result(error.stage+'_evaluation_failure', str(error))
    except (RuntimeError, ValueError) as error:
        return result('ph_nonconvergence', str(error))
    if len(states) != 1:
        return result('multiple_ph_roots', 'More than one residual-qualified root; no selection rule')
    return result('success', solution=states[0])
