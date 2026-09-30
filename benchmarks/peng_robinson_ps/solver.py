"""Independent bounded PS study. No production imports or forward-T input."""
try:
    from .equilibrium import EntropyPT, TrialFailure, IDS, finite
except ImportError:
    from equilibrium import EntropyPT, TrialFailure, IDS, finite

S_TOL = 1e-8  # J/(mol K); acceptance assessed by the independent sensitivity study.
T_TOL = 1e-10  # K, bracket width; separate recovered-state T gate is 1e-7 K.
SCAN_POINTS = 64


def solve_ps(P, z, S_target, bounds=(200., 500.), component_ids=IDS,
             kij=((0., 0.), (0., 0.)), grid_points=SCAN_POINTS,
             xtol=T_TOL, maxiter=100, evaluator=None, direct=False):
    d = dict(scan=[], brackets=[], roots=[], failed_evaluations=[], near_exact_scan_points=[],
             scan_evaluations=0, root_evaluations=0, final_evaluations=0,
             gap_detected=False, fresh_final=False,
             controls=dict(bounds_K=list(bounds) if isinstance(bounds, (list,tuple)) else None,
                           grid_points=grid_points, xtol_K=xtol, maxiter=maxiter,
                           entropy_tolerance_J_mol_K=S_TOL, method='bisection'))

    def result(status, message='', solution=None):
        d['candidate_count'] = len(d['brackets'])
        d['total_evaluations'] = sum(d[k+'_evaluations'] for k in ('scan','root','final'))
        out = dict(status=status, message=message, diagnostics=d)
        if solution is not None:
            out['solution'] = solution
        return out

    if not isinstance(component_ids, (tuple,list)) or tuple(component_ids) != IDS:
        return result('unsupported_components', 'Only ordered methane/n_hexane, including pure endpoints')
    if not isinstance(kij, (tuple,list)) or len(kij) != 2 or any(
        not isinstance(row, (tuple,list)) or len(row) != 2 or any(not finite(v) or v != 0 for v in row) for row in kij):
        return result('unsupported_bip', 'Explicit constant zero 2x2 BIP required')
    if not finite(P) or P <= 0 or not finite(S_target) or not isinstance(z, (tuple,list)) or len(z) != 2 or not all(
        finite(v) and v >= 0 for v in z) or abs(sum(z)-1) > 1e-12:
        return result('invalid_input', 'Finite positive P, finite S and normalized nonnegative z required')
    if not isinstance(bounds, (tuple,list)) or len(bounds) != 2 or not all(finite(v) for v in bounds) or not 200 <= bounds[0] < bounds[1] <= 500:
        return result('temperature_domain_invalid', 'Study bounds must lie within 200–500 K')
    if type(grid_points) is not int or not 3 <= grid_points <= 4096 or type(maxiter) is not int or not 1 <= maxiter <= 100 or not finite(xtol) or xtol <= 0:
        return result('invalid_input', 'Invalid bounded solver controls')
    oracle = evaluator or EntropyPT().evaluate
    key = 'S_eq_direct_J_mol_K' if direct else 'S_eq_J_mol_K'

    def evaluate(T, stage):
        d[stage+'_evaluations'] += 1
        try:
            state = oracle(T, P, z)
            F = state[key]-S_target
            if not finite(F):
                raise TrialFailure('caloric', 'Nonfinite entropy residual')
            return state, F
        except TrialFailure as error:
            d['failed_evaluations'].append(dict(T_K=T, stage=stage, reason=str(error)))
            raise

    lo, hi = bounds
    for i in range(grid_points):
        T = lo+(hi-lo)*i/(grid_points-1)
        try:
            state,F = evaluate(T, 'scan')
            d['scan'].append(dict(T_K=T, status='success', S_J_mol_K=state[key],
                                  residual_J_mol_K=F, classification=state['classification']))
            if abs(F) <= S_TOL:
                d['near_exact_scan_points'].append(T)
        except TrialFailure:
            d['scan'].append(dict(T_K=T, status='property_evaluation_failed'))
    rows = d['scan']
    for a in rows:
        if a['status'] == 'success' and a['residual_J_mol_K'] == 0:
            d['brackets'].append(dict(T_low=a['T_K'], T_high=a['T_K'], F_low=0., F_high=0.))
    for a,b in zip(rows, rows[1:]):
        if a['status'] == b['status'] == 'success' and a['residual_J_mol_K']*b['residual_J_mol_K'] < 0:
            d['brackets'].append(dict(T_low=a['T_K'], T_high=b['T_K'], F_low=a['residual_J_mol_K'], F_high=b['residual_J_mol_K']))
    if d['failed_evaluations']:
        return result('property_evaluation_failed', 'Complete scan contains a hole; no bridging or uniqueness claim')
    slopes = [(b['S_J_mol_K']-a['S_J_mol_K'])/(b['T_K']-a['T_K']) for a,b in zip(rows, rows[1:])]
    d['minimum_scan_slope_J_mol_K2'] = min(slopes)
    d['monotonicity'] = 'sampled_increasing' if min(slopes) > 0 else 'not_strictly_increasing'
    d['phase_transitions'] = [[a['T_K'],b['T_K'],a['classification'],b['classification']]
                             for a,b in zip(rows,rows[1:]) if a['classification'] != b['classification']]
    if not d['brackets']:
        return result('entropy_target_not_bracketed', 'No exact root or adjacent valid sign change')
    if len(d['brackets']) != 1:
        return result('ambiguous_ps_root', 'Multiple scan candidates; no arbitrary root selection')
    bracket = d['brackets'][0]
    low,high,fl,fh = (bracket[k] for k in ('T_low','T_high','F_low','F_high'))
    try:
        iterations = 0
        while high-low > xtol:
            if iterations >= maxiter:
                return result('ps_nonconvergence', 'Maximum root iterations reached')
            mid = low+(high-low)/2
            if mid in (low,high):
                break
            _,fm = evaluate(mid, 'root')
            iterations += 1
            if fm == 0:
                low=high=mid; fl=fh=0.
            elif fl*fm < 0:
                high,fh = mid,fm
            else:
                low,fl = mid,fm
        T = low if abs(fl) <= abs(fh) else high
        state,F = evaluate(T, 'final')
        physical = state['S_eq_J_mol_K']-S_target
        d['fresh_final'] = True
        d['final_bracket'] = dict(T_low=low, T_high=high, F_low=fl, F_high=fh,
                                  entropy_span_J_mol_K=abs(fh-fl))
        d['roots'].append(dict(T_K=T, iterations=iterations, residual_J_mol_K=physical))
        if abs(F) > S_TOL or abs(physical) > S_TOL:
            # Shrinking temperature bracket with finite opposite entropy residuals
            # is discontinuity evidence, never a successful entropy inversion.
            d['gap_detected'] = high-low <= xtol and fl*fh < 0 and min(abs(fl),abs(fh)) > S_TOL
            return result('ps_nonconvergence', 'Discontinuity/coexistence gap' if d['gap_detected'] else 'Fresh final entropy residual failed')
        state.update(S_target_J_mol_K=S_target, S_residual_J_mol_K=physical,
                     S_allowance_J_mol_K=S_TOL, S_margin_J_mol_K=S_TOL-abs(physical))
        return result('success', solution=state)
    except TrialFailure as error:
        return result('property_evaluation_failed', str(error))
