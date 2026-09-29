"""Independent steady-state energy experiment, not production equipment.

Only the qualified independent PT/caloric oracle and PH solver are reused.
Positive heat enters the material stream. No shaft work, KE or PE changes.
"""
from pathlib import Path
import math
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.peng_robinson_ph.equilibrium import IndependentPT, TrialFailure, IDS, finite
from benchmarks.peng_robinson_ph.solver import solve_ph


def validate(F,Pin,Tin,Pout,z,ids):
    if tuple(ids)!=IDS:return 'unsupported_component'
    if not finite(F) or F<=0:return 'invalid_flow'
    if not finite(Pin) or Pin<=0 or not finite(Pout) or Pout<=0:return 'invalid_pressure'
    if not isinstance(z,(tuple,list)) or len(z)!=2 or not all(finite(v) and v>=0 for v in z) or abs(sum(z)-1)>1e-12:return 'invalid_composition'
    if not finite(Tin) or not 200<=Tin<=500:return 'temperature_domain_invalid'
    return None


def failed(status,message=''):
    # A failed specification never contains an outlet state.
    return dict(status=status,message=message)


def mode_a(F,Pin,Tin,Pout,Tout,z,ids=IDS):
    error=validate(F,Pin,Tin,Pout,z,ids)
    if error:return failed(error)
    if not finite(Tout) or not 200<=Tout<=500:return failed('temperature_domain_invalid')
    try:
        oracle=IndependentPT()
        inlet=oracle.evaluate(Tin,Pin,z);outlet=oracle.evaluate(Tout,Pout,z)
        delta=outlet['H_eq_J_mol']-inlet['H_eq_J_mol']
        Q=F*delta
        if not finite(Q):return failed('numerical_failure','Nonfinite duty')
        return dict(status='success',inlet=inlet,outlet=outlet,F_in_mol_s=F,F_out_mol_s=F,
                    z_in=list(z),z_out=list(z),delta_H_J_mol=delta,Q_W=Q,
                    R_Q_W=Q-F*(outlet['H_eq_J_mol']-inlet['H_eq_J_mol']))
    except TrialFailure as error:
        return failed(error.stage+'_evaluation_failure',str(error))


def mode_b(F,Pin,Tin,Pout,Q,z,ids=IDS):
    error=validate(F,Pin,Tin,Pout,z,ids)
    if error:return failed(error)
    if not finite(Q):return failed('invalid_duty')
    try:
        inlet=IndependentPT().evaluate(Tin,Pin,z)
        target=inlet['H_eq_J_mol']+Q/F
        if not finite(target):return failed('numerical_failure','Nonfinite target')
        # No target/forward temperature, warm-start or production dependency.
        inverse=solve_ph(Pout,z,target,bounds=(200.,500.),component_ids=ids)
        if inverse['status']!='success':return failed(inverse['status'],inverse['message'])
        outlet=inverse['solution']
        return dict(status='success',inlet=inlet,outlet=outlet,F_in_mol_s=F,F_out_mol_s=F,
                    z_in=list(z),z_out=list(z),H_out_target_J_mol=target,Q_W=Q,
                    R_H_J_mol=outlet['H_eq_J_mol']-target,
                    R_Q_W=Q-F*(outlet['H_eq_J_mol']-inlet['H_eq_J_mol']),
                    PH_diagnostics=inverse['diagnostics'])
    except TrialFailure as error:
        return failed(error.stage+'_evaluation_failure',str(error))


def roundoff_allowance(F,Hin,Hout,Q):
    """Conservative 64-epsilon budget for subtraction/multiplication, including cancellation."""
    return 64*sys.float_info.epsilon*max(1.,abs(Q),abs(F*Hin),abs(F*Hout))
