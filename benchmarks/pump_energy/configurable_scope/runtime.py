"""Benchmark runtime guard: finite diagnostics and configured range, no allowlist."""
import math
from benchmarks.pump_energy.configurable_scope.policy import evaluate


def finite_tree(value):
    if isinstance(value,float):return math.isfinite(value)
    if isinstance(value,dict):return all(finite_tree(v) for v in value.values())
    if isinstance(value,(list,tuple)):return all(finite_tree(v) for v in value)
    return True


def _admissibility(i,result,witnesses):
    # Never accept diagnostic NaN/Infinity or fabricated/unavailable witnesses.
    if not finite_tree(i) or not finite_tree(result) or not finite_tree(witnesses):
        return dict(accepted=False,reason='nonfinite_payload')
    policy=evaluate(i,result,witnesses)
    if not policy['accepted']:return policy
    for s in list(result['states'].values())+list(witnesses.values()):
        if s.get('PT_profile') != 'high_accuracy' or s.get('PT_status') != 'success_single_phase':
            return dict(accepted=False,reason='unqualified_PT_profile')
        phase=s['phases']['liquid']
        if phase['Z']<=0 or any(abs(v-.5)>1e-12 for v in phase['composition']):
            return dict(accepted=False,reason='phase_payload_mismatch')
    for key,d in result['diagnostics'].items():
        if list(d['settings']['temperature_bounds_K']) != [200.,500.] or d['pt_settings']['profile'] != 'high_accuracy':
            return dict(accepted=False,reason='unqualified_inverse_controls')
        if key=='PS' and d['failures']:
            return dict(accepted=False,reason='PS_property_hole')
        # PH can have holes, but no accepted bracket may bridge them.
        lo,hi=d['selected_bracket_K']
        if any(lo<=v['temperature_K']<=hi for v in d['failures']):
            return dict(accepted=False,reason='bracket_crosses_hole')
    a,b,c=[result['states'][k] for k in ('inlet','isentropic','outlet')]
    target=a['H_eq_J_mol']+(b['H_eq_J_mol']-a['H_eq_J_mol'])/i['eta']
    dh=c['H_eq_J_mol']-a['H_eq_J_mol']
    F=i['flow']
    power=F*dh;target_power=F*(target-a['H_eq_J_mol'])
    rounding=64*math.ulp(1.)*max(1.,abs(F*a['H_eq_J_mol']),abs(F*c['H_eq_J_mol']),abs(power))
    if not all(math.isfinite(v) for v in (power,target_power)) or abs(power-target_power)>F*1e-6+rounding:
        return dict(accepted=False,reason='power_residual')
    if i['P1']!=i['P2']:
        eta=(b['H_eq_J_mol']-a['H_eq_J_mol'])/dh
        if abs(eta-i['eta'])>i['eta']*1e-6/abs(dh)+64*math.ulp(1.):
            return dict(accepted=False,reason='efficiency_residual')
    return policy|dict(W_recovered_W=power,W_target_W=target_power)


def admissibility(i,result,witnesses):
    try:
        return _admissibility(i,result,witnesses)
    except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError):
        return dict(accepted=False,reason='invalid_payload')
