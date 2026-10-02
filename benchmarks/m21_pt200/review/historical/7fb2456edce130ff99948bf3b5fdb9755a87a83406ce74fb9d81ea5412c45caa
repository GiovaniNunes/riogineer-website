"""Standalone bounded PS inversion; PT and caloric arithmetic remain in M8–M10.

A complete finite scan identifies candidates, not mathematical global uniqueness.
A discontinuity is never accepted without a fresh entropy residual check.
"""
from dataclasses import dataclass
from .pr_eos import ThermodynamicError, finite, require
from .pr_flash import SolverSettings
from .pr_caloric import CaloricResult, CaloricProvenance, validate_input
from .thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance


@dataclass(frozen=True)
class PSSpecification:
    pressure_Pa_abs: float
    entropy_J_mol_K: float
    composition: MolarComposition
    provenance: StateSpecificationProvenance


@dataclass(frozen=True)
class PSSettings:
    temperature_bounds_K: tuple[float, float] = (200., 500.)
    scan_points: int = 64
    max_iterations: int = 100
    temperature_tolerance_K: float = 1e-10
    entropy_tolerance_J_mol_K: float = 1e-8

    def validate(self):
        bounds = self.temperature_bounds_K
        require(isinstance(bounds, (tuple,list)) and len(bounds) == 2 and
                all(finite(v) for v in bounds) and 200 <= bounds[0] < bounds[1] <= 500,
                'PS bounds must lie in qualified 200–500 K domain', 'temperature_domain_invalid')
        require(type(self.scan_points) is int and 3 <= self.scan_points <= 4096 and
                type(self.max_iterations) is int and 1 <= self.max_iterations <= 100,
                'Invalid bounded PS solver controls')
        require(self.temperature_tolerance_K == 1e-10 and self.entropy_tolerance_J_mol_K == 1e-8,
                'PS qualification tolerances are fixed')


@dataclass(frozen=True)
class PSTrial:
    stage: str
    temperature_K: float
    status: str
    classification: str | None = None
    entropy_J_mol_K: float | None = None
    residual_J_mol_K: float | None = None
    underlying_status: str = ''
    message: str = ''


@dataclass(frozen=True)
class PSDiagnostics:
    settings: PSSettings
    pt_settings: SolverSettings
    trials: tuple[PSTrial, ...] = ()
    brackets_K: tuple[tuple[float, float], ...] = ()
    selected_bracket_K: tuple[float, float] | None = None
    final_bracket_K: tuple[float, float] | None = None
    root_iterations: int = 0
    reason: str = ''
    near_exact_scan_temperatures_K: tuple[float, ...] = ()
    gap_detected: bool = False
    final_entropy_span_J_mol_K: float | None = None


@dataclass(frozen=True)
class PSResult:
    status: str
    specification: PSSpecification
    diagnostics: PSDiagnostics
    caloric: CaloricResult | None = None
    temperature_K: float | None = None
    entropy_residual_J_mol_K: float | None = None
    provenance: CaloricProvenance = CaloricProvenance()
    capability: str = 'flash_PS'


def flash_ps(specification, bip, evaluator, settings=PSSettings()):
    """Evaluator is the existing provider equilibrium_caloric_PT method.

    No accepted payload is returned on failure. Trial summaries retain failures,
    without exposing an intermediate phase result as an accepted PS solution.
    """
    trials=[]; brackets=[]; selected=None; final_bracket=None; iterations=0
    near=[]; gap=False; span=None
    pt_settings=SolverSettings.high_accuracy()

    def result(status, reason='', caloric=None, temperature=None, residual=None):
        diagnostics=PSDiagnostics(settings,pt_settings,tuple(trials),tuple(brackets),
                                  selected,final_bracket,iterations,reason,tuple(near),gap,span)
        return PSResult(status,specification,diagnostics,caloric,temperature,residual)

    def state(T):
        return ThermodynamicState(T,specification.pressure_Pa_abs,specification.composition,
                                  specification.provenance)

    def evaluate_property(T, stage):
        c=evaluator(state(T),bip,settings=pt_settings)
        pt=c.equilibrium
        if pt is not None and not pt.status.startswith('success'):
            status='pt_evaluation_failure'
        elif c.aggregate is None or not c.status.startswith('success') or pt is None:
            status='caloric_evaluation_failure'
        else:
            status='success'
        if status != 'success':
            trials.append(PSTrial(stage,T,status,underlying_status=c.status,message=c.message))
            raise ThermodynamicError(status,c.status+': '+c.message)
        require(pt.provenance.settings == pt_settings,'Nested PT profile mismatch','pt_evaluation_failure')
        S=c.aggregate.s_J_mol_K
        residual=S-specification.entropy_J_mol_K
        if not finite(S) or not finite(residual) or not finite(c.aggregate.h_J_mol):
            trials.append(PSTrial(stage,T,'caloric_evaluation_failure',underlying_status='nonfinite_caloric_property'))
            raise ThermodynamicError('caloric_evaluation_failure','Nonfinite trial entropy, residual or enthalpy')
        trials.append(PSTrial(stage,T,'success',pt.classification,S,residual))
        return c,residual

    def evaluate(T, stage):
        before=len(trials)
        try:
            return evaluate_property(T,stage)
        except (ThermodynamicError,OverflowError,ZeroDivisionError) as error:
            if len(trials)==before:
                trials.append(PSTrial(stage,T,'property_evaluation_failed',
                    underlying_status=getattr(error,'status','numerical_domain_error'),message=str(error)))
            raise ThermodynamicError('property_evaluation_failed',str(error)) from error

    try:
        require(isinstance(specification,PSSpecification),'PSSpecification required')
        require(finite(specification.entropy_J_mol_K),'Finite molar entropy target required')
        require(isinstance(settings,PSSettings),'PSSettings required')
        settings.validate()
        low,high=settings.temperature_bounds_K
        # Existing composition, BIP, provider and component/Cp validation policy.
        validate_input(state(low),bip)
        validate_input(state(high),bip)
        points=[]; failures=[]
        for i in range(settings.scan_points):
            T=low+(high-low)*i/(settings.scan_points-1)
            try:
                _,F=evaluate(T,'scan')
            except ThermodynamicError as error:
                failures.append(str(error)); F=None
            points.append((T,F))
            if F is not None and abs(F)<=settings.entropy_tolerance_J_mol_K:near.append(T)
        for T,F in points:
            if F == 0:brackets.append((T,T))
        for (a,fa),(b,fb) in zip(points,points[1:]):
            if fa is not None and fb is not None and ((fa < 0 < fb) or (fb < 0 < fa)):
                brackets.append((a,b))
        if failures:
            return result('property_evaluation_failed','Complete scan contains property holes; no interval bridged: '+failures[0])
        # Near-exact points remain diagnostics when covered by a sign bracket.
        # An isolated near-exact point can qualify only via fresh final residual.
        for T in near:
            if not any(a<=T<=b for a,b in brackets):brackets.append((T,T))
        if not brackets:return result('entropy_target_not_bracketed','No exact scan root or adjacent sign change')
        if len(brackets)!=1:return result('ambiguous_ps_root','Multiple scan candidates; no qualified selection rule')
        selected=brackets[0];lo,hi=selected
        values=dict(points);flo,fhi=values[lo],values[hi]
        best=min(((lo,flo),(hi,fhi)),key=lambda q:abs(q[1]))
        # Sign intervals are provisional: collapse plus fresh residual must reject gaps.
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
                lo=hi=mid;flo=fhi=fm;best=(mid,fm);converged=True
            elif (flo < 0 < fm) or (fm < 0 < flo):
                hi,fhi=mid,fm
            else:
                lo,flo=mid,fm
            if hi-lo <= settings.temperature_tolerance_K:converged=True
            if converged:break
        final_bracket=(lo,hi)
        if not converged:return result('ps_nonconvergence','Root iteration limit reached')
        # Choose the smallest observed residual in the converged bracket only.
        candidates=[(lo,flo),(hi,fhi)]
        if lo <= best[0] <= hi:candidates.append(best)
        T=min(candidates,key=lambda q:abs(q[1]))[0]
        c,F=evaluate(T,'final')
        span=abs(fhi-flo)
        if abs(F)>settings.entropy_tolerance_J_mol_K:
            gap=(hi-lo<=settings.temperature_tolerance_K and flo*fhi<0 and
                 min(abs(flo),abs(fhi))>settings.entropy_tolerance_J_mol_K)
            return result('ps_nonconvergence','Fresh final entropy residual failed; a discontinuity/coexistence gap is not a PS solution')
        return result('success',caloric=c,temperature=T,residual=F)
    except ThermodynamicError as error:
        return result(error.status,str(error))
    except (OverflowError,ZeroDivisionError) as error:
        return result('ps_numerical_failure',type(error).__name__)
