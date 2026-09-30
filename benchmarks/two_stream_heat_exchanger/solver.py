"""Independent Pre-M15 terminal-state experiment, never production equipment."""
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT, TrialFailure, IDS, finite
from benchmarks.peng_robinson_ph.solver import solve_ph

ZERO = ((0., 0.), (0., 0.))
H_TOL = 1e-6
T_TOL = 1e-7


def failure(status, stage, message, nested=None):
    out = dict(status=status, failure_stage=stage, message=message,
               accepted_complete_exchanger_result=False)
    if nested is not None:
        out['PH_failure'] = nested
    return out


def roundoff(spec, states, duties):
    scale = [1., *map(abs, duties)]
    for side in ('hot', 'cold'):
        scale.extend(abs(spec[side]['F']*states[side+'_'+end]['H_eq_J_mol']) for end in ('in', 'out'))
    return 64*sys.float_info.epsilon*max(scale)


def calculate(spec, oracle=None, ph_solver=solve_ph, controls=None, service='primary'):
    """Couple enthalpy balances only; independently retain each material side."""
    if service not in ('primary', 'thermodynamic_only'):
        return failure('invalid_specification', 'specification', 'Unknown benchmark service policy')
    keys = [k for k in ('T_hot_out', 'T_cold_out') if k in spec]
    if len(keys) != 1:
        return failure('invalid_specification', 'specification', 'Exactly one outlet-temperature specification required')
    if set(spec)-{'hot', 'cold', 'T_hot_out', 'T_cold_out', 'kij'}:
        return failure('invalid_specification', 'specification', 'Unsupported thermal specification')
    for side in ('hot', 'cold'):
        s = spec.get(side, {})
        if not isinstance(s, dict) or set(s)-{'F', 'Tin', 'Pin', 'Pout', 'z', 'ids'} or not {'F','Tin','Pin','Pout','z'} <= set(s):
            return failure('invalid_specification', side+'_input', 'Incomplete side specification')
        if not finite(s['F']) or s['F'] <= 0:
            return failure('invalid_flow', side+'_input', 'Positive finite molar flow required')
        if not all(finite(s[k]) and s[k] > 0 for k in ('Pin', 'Pout')) or s['Pout'] > s['Pin']:
            return failure('invalid_pressure', side+'_input', '0 < Pout <= Pin; independent side pressures')
        if tuple(s.get('ids', IDS)) != IDS:
            return failure('unsupported_component', side+'_input', 'Ordered methane/n_hexane only')
        z = s['z']
        if not isinstance(z, (list, tuple)) or len(z) != 2 or not all(finite(v) and v >= 0 for v in z) or abs(sum(z)-1) > 1e-12:
            return failure('invalid_composition', side+'_input', 'Normalized nonnegative mole fractions required')
        if not finite(s['Tin']) or not 200 <= s['Tin'] <= 500:
            return failure('temperature_domain_invalid', side+'_input', '200–500 K qualified domain')
    kij = spec.get('kij', ZERO)
    if not isinstance(kij, (list, tuple)) or len(kij) != 2 or any(not isinstance(row, (list, tuple)) or len(row) != 2 or any(not finite(v) or v != 0 for v in row) for row in kij):
        return failure('unsupported_bip', 'specification', 'Explicit constant zero kij only')
    key = keys[0]; specified = 'hot' if key == 'T_hot_out' else 'cold'
    recovered = 'cold' if specified == 'hot' else 'hot'
    if not finite(spec[key]) or not 200 <= spec[key] <= 500:
        return failure('temperature_domain_invalid', 'specified_'+specified+'_outlet_PT', '200–500 K qualified domain')
    if service == 'primary' and spec['hot']['Tin'] <= spec['cold']['Tin']:
        return failure('temperature_direction', 'service_scope', 'Declared hot inlet must exceed cold inlet; no relabeling')
    pt = oracle or EntropyPT(); states = {}
    for side, end, T, P, stage in [
        ('hot','in',spec['hot']['Tin'],spec['hot']['Pin'],'hot_inlet_PT'),
        ('cold','in',spec['cold']['Tin'],spec['cold']['Pin'],'cold_inlet_PT'),
        (specified,'out',spec[key],spec[specified]['Pout'],'specified_'+specified+'_outlet_PT')]:
        try:
            states[side+'_'+end] = pt.evaluate(T, P, spec[side]['z'])
        except TrialFailure as error:
            return failure(error.stage+'_evaluation_failure', stage, str(error))
    H = lambda side, end: states[side+'_'+end]['H_eq_J_mol']
    Q_spec = spec[specified]['F']*(H(specified,'out')-H(specified,'in'))
    target = H(recovered,'in')-Q_spec/spec[recovered]['F']
    inverse = ph_solver(spec[recovered]['Pout'], spec[recovered]['z'], target,
                        bounds=(200.,500.), evaluator=pt.evaluate, **(controls or {}))
    stage = 'recovered_'+recovered+'_outlet_PH'
    if inverse['status'] != 'success':
        return failure(inverse['status'], stage, inverse.get('message',''), inverse)
    state = inverse['solution']; d = inverse['diagnostics']
    if len(d['brackets']) != 1 or d['final_evaluations'] != 1 or abs(state['H_eq_J_mol']-target) > H_TOL:
        return failure('final_acceptance_failed', stage, 'One candidate and fresh enthalpy residual required')
    states[recovered+'_out'] = state
    duties = {side:spec[side]['F']*(H(side,'out')-H(side,'in')) for side in ('hot','cold')}
    residual = math.fsum(duties.values()); arithmetic = roundoff(spec,states,duties.values())
    allowance = spec[recovered]['F']*H_TOL+arithmetic
    if not all(finite(v) for v in [target,*duties.values(),residual]) or abs(residual) > allowance:
        return failure('energy_balance_failed', 'energy_balance', 'Fresh-state energy closure failed')
    if service == 'primary':
        if duties['hot'] > allowance or duties['cold'] < -allowance:
            return failure('heat_direction', 'service_scope', 'Contradictory declared hot-to-cold duty')
        if any(s['classification'] not in ('single_vapor','single_liquid') for s in states.values()):
            return failure('phase_service_scope', 'service_scope', 'Initial recommendation: single-phase endpoints only')
        Tho, Tco = states['hot_out']['T_K'], states['cold_out']['T_K']
        if not (spec['hot']['Tin'] > Tco and Tho > spec['cold']['Tin'] and Tho >= Tco):
            return failure('terminal_temperature_crossing', 'service_scope', 'Require Thi > Tco, Tho > Tci, Tho >= Tco; no design feasibility claim')
    material = {}
    for side in ('hot','cold'):
        if any(states[side+'_'+end]['z'] != list(spec[side]['z']) for end in ('in','out')):
            return failure('material_balance_failed', side+'_material', 'No composition transfer allowed')
        material[side] = dict(F_in_mol_s=spec[side]['F'],F_out_mol_s=spec[side]['F'],
                             z_in=list(spec[side]['z']),z_out=list(spec[side]['z']),
                             flow_residual_mol_s=0.,composition_residual=[0.,0.])
    return dict(status='success',accepted_complete_exchanger_result=True,service=service,
                specification_mode='A' if specified=='hot' else 'B',specified_side=specified,recovered_side=recovered,
                states=states,material=material,Q_hot_W=duties['hot'],Q_cold_W=duties['cold'],Q_exchanged_W=duties['cold'],
                energy_residual_W=residual,energy_allowance_W=allowance,arithmetic_allowance_W=arithmetic,
                H_target_J_mol=target,PH_residual_J_mol=state['H_eq_J_mol']-target,PH=d,
                environment_heat_W=0.,shaft_work_W=0.)
