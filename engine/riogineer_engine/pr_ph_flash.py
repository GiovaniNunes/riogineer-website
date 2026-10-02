"""Standalone bounded PH inversion; PT and caloric arithmetic remain in M8–M10.

A complete finite scan identifies candidates, not mathematical global uniqueness.
A discontinuity is never accepted without a fresh enthalpy residual check.
"""
from .numerical_profiles import resolve_pt_settings
from dataclasses import dataclass
from .pr_eos import ThermodynamicError, finite, require
from .pr_flash import SolverSettings
from .pr_caloric import CaloricResult, CaloricProvenance, validate_input
from .thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance


@dataclass(frozen=True)
class PHSpecification:
    pressure_Pa_abs: float
    enthalpy_J_mol: float
    composition: MolarComposition
    provenance: StateSpecificationProvenance


@dataclass(frozen=True)
class PHSettings:
    temperature_bounds_K: tuple[float, float] = (200., 500.)
    scan_points: int = 128
    max_iterations: int = 100
    temperature_tolerance_K: float = 1e-12
    enthalpy_tolerance_J_mol: float = 1e-6

    def validate(self):
        bounds = self.temperature_bounds_K
        require(isinstance(bounds, (tuple,list)) and len(bounds) == 2 and
                all(finite(v) for v in bounds) and 200 <= bounds[0] < bounds[1] <= 500,
                'PH bounds must lie in qualified 200–500 K domain', 'temperature_domain_invalid')
        require(type(self.scan_points) is int and 3 <= self.scan_points <= 4096 and
                type(self.max_iterations) is int and 1 <= self.max_iterations <= 100,
                'Invalid bounded PH solver controls')
        require(self.temperature_tolerance_K == 1e-12 and self.enthalpy_tolerance_J_mol == 1e-6,
                'PH qualification tolerances are fixed')


@dataclass(frozen=True)
class PHTrial:
    stage: str
    temperature_K: float
    status: str
    classification: str | None = None
    enthalpy_J_mol: float | None = None
    residual_J_mol: float | None = None
    underlying_status: str = ''
    message: str = ''


@dataclass(frozen=True)
class PHDiagnostics:
    settings: PHSettings
    pt_settings: SolverSettings
    trials: tuple[PHTrial, ...] = ()
    brackets_K: tuple[tuple[float, float], ...] = ()
    selected_bracket_K: tuple[float, float] | None = None
    final_bracket_K: tuple[float, float] | None = None
    root_iterations: int = 0
    reason: str = ''


@dataclass(frozen=True)
class PHResult:
    status: str
    specification: PHSpecification
    diagnostics: PHDiagnostics
    caloric: CaloricResult | None = None
    temperature_K: float | None = None
    enthalpy_residual_J_mol: float | None = None
    provenance: CaloricProvenance = CaloricProvenance()


def flash_ph(specification, bip, evaluator, settings=PHSettings(), *, numerical_profile=None):
    """Evaluator is the existing provider equilibrium_caloric_PT method.

    No accepted payload is returned on failure. Trial summaries retain failures,
    without exposing an intermediate phase result as an accepted PH solution.
    """
    trials=[]; brackets=[]; selected=None; final_bracket=None; iterations=0
    pt_settings=resolve_pt_settings(numerical_profile, default=SolverSettings.high_accuracy())

    def result(status, reason='', caloric=None, temperature=None, residual=None):
        diagnostics=PHDiagnostics(settings,pt_settings,tuple(trials),tuple(brackets),
                                  selected,final_bracket,iterations,reason)
        return PHResult(status,specification,diagnostics,caloric,temperature,residual)

    def state(T):
        return ThermodynamicState(T,specification.pressure_Pa_abs,specification.composition,
                                  specification.provenance)

    def evaluate(T, stage):
        c=evaluator(state(T),bip,settings=pt_settings)
        pt=c.equilibrium
        if pt is not None and not pt.status.startswith('success'):
            status='pt_evaluation_failure'
        elif c.aggregate is None or not c.status.startswith('success') or pt is None:
            status='caloric_evaluation_failure'
        else:
            status='success'
        if status != 'success':
            trials.append(PHTrial(stage,T,status,underlying_status=c.status,message=c.message))
            raise ThermodynamicError(status,c.status+': '+c.message)
        require(pt.provenance.settings == pt_settings,'Nested PT profile mismatch','pt_evaluation_failure')
        H=c.aggregate.h_J_mol
        residual=H-specification.enthalpy_J_mol
        if not finite(H) or not finite(residual):
            trials.append(PHTrial(stage,T,'caloric_evaluation_failure',underlying_status='nonfinite_enthalpy'))
            raise ThermodynamicError('caloric_evaluation_failure','Nonfinite trial enthalpy/residual')
        trials.append(PHTrial(stage,T,'success',pt.classification,H,residual))
        return c,residual

    try:
        require(isinstance(specification,PHSpecification),'PHSpecification required')
        require(finite(specification.enthalpy_J_mol),'Finite molar enthalpy target required')
        require(isinstance(settings,PHSettings),'PHSettings required')
        settings.validate()
        low,high=settings.temperature_bounds_K
        # Existing composition, BIP, provider and component/Cp validation policy.
        validate_input(state(low),bip)
        validate_input(state(high),bip)
        intervals=[]; interval=[]; scan_failure=None
        for i in range(settings.scan_points):
            T=low+(high-low)*i/(settings.scan_points-1)
            before=len(trials)
            try:
                _,F=evaluate(T,'scan')
            except ThermodynamicError as error:
                # Only recorded, controlled PT failures partition the scan.
                if (error.status != 'pt_evaluation_failure' or len(trials) != before+1 or
                        trials[-1].status != 'pt_evaluation_failure'):
                    raise
                if scan_failure is None:scan_failure=error
                if interval:intervals.append(interval);interval=[]
                continue
            interval.append((T,F))
        if interval:intervals.append(interval)
        # Failed points break connectivity; brackets cannot span unavailable regions.
        for points in intervals:
            for T,F in points:
                if F == 0:brackets.append((T,T))
            for (a,fa),(b,fb) in zip(points,points[1:]):
                if (fa < 0 < fb) or (fb < 0 < fa):brackets.append((a,b))
        if not brackets:
            if scan_failure is not None:return result(scan_failure.status,str(scan_failure))
            return result('enthalpy_target_not_bracketed','No exact scan root or adjacent sign change')
        if len(brackets)!=1:return result('multiple_ph_roots','Multiple scan candidates; no qualified selection rule')
        selected=brackets[0];lo,hi=selected
        values=dict(point for points in intervals for point in points);flo,fhi=values[lo],values[hi]
        best=min(((lo,flo),(hi,fhi)),key=lambda q:abs(q[1]))
        # Bisection retains a sign bracket across phase changes; no smoothness assumption.
        converged=lo == hi
        for iterations in range(1,settings.max_iterations+1):
            if converged:
                iterations-=1
                break
            mid=lo+(hi-lo)/2
            if mid in (lo,hi):
                converged=True
                break
            _,fm=evaluate(mid,'root')
            if abs(fm)<abs(best[1]):best=(mid,fm)
            if fm == 0:
                lo=hi=mid;best=(mid,fm);converged=True
            elif (flo < 0 < fm) or (fm < 0 < flo):
                hi,fhi=mid,fm
            else:
                lo,flo=mid,fm
            if hi-lo <= settings.temperature_tolerance_K:converged=True
            if converged:break
        final_bracket=(lo,hi)
        if not converged:return result('ph_nonconvergence','Root iteration limit reached')
        # Choose the smallest observed residual in the converged bracket only.
        candidates=[(lo,flo),(hi,fhi)]
        if lo <= best[0] <= hi:candidates.append(best)
        T=min(candidates,key=lambda q:abs(q[1]))[0]
        c,F=evaluate(T,'final')
        if abs(F)>settings.enthalpy_tolerance_J_mol:
            return result('ph_nonconvergence','Fresh final enthalpy residual failed; a discontinuity/coexistence gap is not a PH solution')
        return result('success',caloric=c,temperature=T,residual=F)
    except ThermodynamicError as error:
        return result(error.status,str(error))
    except (OverflowError,ZeroDivisionError) as error:
        return result('ph_numerical_failure',type(error).__name__)
