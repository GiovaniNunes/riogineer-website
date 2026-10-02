"""Standalone PT successive substitution with explicit stability and closure gates."""
from dataclasses import dataclass, replace
from enum import Enum
from math import log
from .components import DATASET, component
from .pr_eos import MODEL, BinaryInteractions, PengRobinsonEOS, ThermodynamicError, finite, normalized, require, safe_exp
from .pr_stability import StabilityResult, stability
from .rachford_rice import RRResult, reconstruct, solve_rr
from .thermodynamics import ThermodynamicState, MolarComposition


class AccuracyProfile(str, Enum):
    STANDARD = 'standard'
    HIGH_ACCURACY = 'high_accuracy'


@dataclass(frozen=True)
class SolverSettings:
    flash_max_iterations: int = 100
    stability_max_iterations: int = 100
    rr_max_iterations: int = 200
    # Qualification tolerances are intentionally fixed, not user-loosenable.
    fugacity_tolerance: float = 1e-11
    material_tolerance: float = 1e-10
    profile: AccuracyProfile = AccuracyProfile.STANDARD

    @classmethod
    def high_accuracy(cls):
        return cls(fugacity_tolerance=1e-12, profile=AccuracyProfile.HIGH_ACCURACY)

    def validate(self):
        require(all(isinstance(v,int) and not isinstance(v,bool) and v > 0 for v in
                    (self.flash_max_iterations,self.stability_max_iterations,self.rr_max_iterations)), 'Invalid solver iteration limit')
        require(isinstance(self.profile, AccuracyProfile), 'Explicit qualified accuracy profile required')
        target = 1e-12 if self.profile == AccuracyProfile.HIGH_ACCURACY else 1e-11
        require(self.fugacity_tolerance == target and self.material_tolerance == 1e-10, 'Qualification tolerances are fixed per profile')


@dataclass(frozen=True)
class RestartSeed:
    component_ids: tuple[str, ...]
    trial_composition: tuple[float, ...]
    trial_tpd_RT: float
    stability_sum: float
    K: tuple[float, ...]
    parent_pip: float
    trial_pip: float
    orientation: str = 'liquid_parent_vapor_trial'
    algorithm: str = 'stationary_tpd_scaled_trial@1.0'


@dataclass(frozen=True)
class InitializationDiagnostics:
    strategy: str = 'wilson'
    initial_K: tuple[float, ...] = ()
    initial_rr: RRResult | None = None
    restart_count: int = 0
    restart_seed: RestartSeed | None = None
    restart_rr: RRResult | None = None


def stability_restart_seed(eos, z, stab):
    """Reuse the converged TPD minimum with either qualified phase orientation.

    At stationary normalized w, S=exp(-TPD/RT). K=y/x is S*w/z for a
    liquid parent and z/(S*w) for a vapor parent. PIP uses the
    existing EOS phase-identification API, including for a single cubic root;
    it labels orientation AFTER instability, never establishes instability.
    No minimization or EOS equations are repeated here.
    """
    # Preserve the existing failed-initialization status; message identifies
    # why a safe seed was unavailable rather than implying RR iteration failed.
    status = 'rachford_rice_not_converged'
    require(stab.converged and stab.stable is False, 'Restart requires converged instability', status)
    require(len(z) == len(eos.component_ids) == 2 and all(v > 0 for v in z),
            'Restart requires positive binary feed fractions; pure feeds retain the stable path', status)
    parent = eos.mixture(z)
    parent_pip = eos.phase_identification(parent, eos.lowest_gibbs(parent).Z)
    require(finite(parent_pip) and parent_pip != 1, 'Ambiguous restart parent phase', status)
    candidates = sorted((t for t in stab.trials if t.converged and t.iterations > 0 and t.tpd_RT < -1e-9),
                        key=lambda t: (t.tpd_RT, t.composition))
    for trial in candidates:
        w = trial.composition
        require(len(w) == len(z) and all(finite(v) and v > 0 for v in w), 'Invalid restart trial composition', status)
        normalized(w)
        mixed = eos.mixture(w)
        pip = eos.phase_identification(mixed, eos.lowest_gibbs(mixed).Z)
        require(finite(pip) and pip != 1, 'Ambiguous restart trial phase', status)
        if (parent_pip > 1) == (pip > 1):
            continue
        s = safe_exp(-trial.tpd_RT)
        require(finite(s) and s > 1, 'Invalid instability sum', status)
        if parent_pip > 1:
            orientation = 'liquid_parent_vapor_trial'
            k = tuple(s*wi/zi for wi,zi in zip(w,z))
        else:
            orientation = 'vapor_parent_liquid_trial'
            k = tuple(zi/(s*wi) for wi,zi in zip(w,z))
        require(all(finite(v) and v > 0 for v in k), 'Invalid stability-derived K', status)
        return RestartSeed(eos.component_ids,w,trial.tpd_RT,s,k,parent_pip,pip,orientation)
    message = ('No converged vapor-like unstable trial for liquid-parent restart' if parent_pip > 1
               else 'No qualified opposite phase orientation: expected liquid-like parent/vapor-like trial or vapor-like parent/liquid-like trial')
    require(False, message, status)


@dataclass(frozen=True)
class PhaseResult:
    identifier: str
    fraction: float
    composition: tuple[float, ...]
    Z: float
    ln_phi: tuple[float, ...]
    phi: tuple[float, ...]
    fugacity_Pa: tuple[float, ...]


@dataclass(frozen=True)
class FlashDiagnostics:
    iterations: int = 0
    fugacity_residual: tuple[float, ...] = ()
    rr_residual: float | None = None
    material_residual: tuple[float, ...] = ()
    raw_composition_sum_errors: tuple[float, ...] = ()
    rr_iterations: int = 0
    stability: StabilityResult | None = None
    equilibrium_stability: StabilityResult | None = None
    message: str = ''
    initialization: InitializationDiagnostics = InitializationDiagnostics()


@dataclass(frozen=True)
class FlashProvenance:
    provider: str
    component_dataset: str
    bip: BinaryInteractions
    formulation: str
    solver: str
    settings: SolverSettings


@dataclass(frozen=True)
class PTResult:
    status: str
    classification: str | None
    overall_state: ThermodynamicState
    evaluated_molar_composition: tuple[float, ...]
    phases: tuple[PhaseResult, ...]
    beta: float | None
    final_K: tuple[float, ...]
    diagnostics: FlashDiagnostics
    provenance: FlashProvenance


def wilson(eos):
    return tuple(safe_exp(log(component(c).critical_pressure)-log(eos.pressure_Pa_abs)
                  +5.373*(1+component(c).acentric_factor)*(1-component(c).critical_temperature/eos.temperature_K))
                 for c in eos.component_ids)


def flash_pt(state, bip, settings=SolverSettings()):
    """Failures publish no phases/beta/K. Last closure metrics remain diagnostic only."""
    provenance = FlashProvenance(MODEL,DATASET,bip,'PR1976: 0.45724/0.07780; classical quadratic a, linear b',
                                'binary_tpd_rr_ss@1.0',settings)
    diag = FlashDiagnostics()
    z = ()

    def result(status,classification=None,phases=(),beta=None,k=()):
        return PTResult(status,classification,state,z,phases,beta,k,diag,provenance)

    def phase(label,fraction,composition,f):
        fugacities=tuple(v*p*state.pressure_Pa_abs for v,p in zip(composition,f.phi))
        from .pr_eos import finite
        require(all(finite(v) for v in fugacities), 'Nonfinite fugacity', 'numerical_domain_error')
        return PhaseResult(label,fraction,composition,f.Z,f.ln_phi,f.phi,fugacities)

    try:
        settings.validate()
        require(isinstance(state,ThermodynamicState), 'ThermodynamicState required')
        c = state.composition
        ids = c.component_ids
        require(state.provenance.provider == MODEL, 'State must explicitly select the PR provider')
        require(getattr(state.provenance,'bip_specification',None) == getattr(bip,'identifier',None), 'State/BIP specification identity mismatch')
        require(c.molar_fractions is not None, 'Molar composition unavailable')
        fractions = c.molar_fractions if isinstance(c,MolarComposition) else tuple(c.molar_fractions[i] for i in ids)
        z = normalized(fractions)
        eos = PengRobinsonEOS(ids,state.temperature_K,state.pressure_Pa_abs,bip)
        require(len(ids)==len(z), 'Composition/component dimensions')
        stab = stability(eos,z,settings.stability_max_iterations)
        diag = FlashDiagnostics(stability=stab)
        if not stab.converged:
            return result('stability_not_converged')
        if stab.stable:
            f = eos.lowest_gibbs(eos.mixture(z))
            label = 'liquid' if stab.classification == 'single_liquid' else 'vapor'
            return result('success_single_phase',stab.classification,(phase(label,1.,z,f),),0. if label=='liquid' else 1.)
        k = wilson(eos)
        initialization = InitializationDiagnostics(initial_K=k)
        for iteration in range(1,settings.flash_max_iterations+1):
            rr = solve_rr(z,k,settings.rr_max_iterations)
            if iteration == 1:
                initialization = replace(initialization, initial_rr=rr)
                if rr.converged and rr.status in ('liquid_tendency','vapor_tendency'):
                    initialization = replace(initialization, restart_count=1)
                    diag = replace(diag, initialization=initialization)
                    seed = stability_restart_seed(eos,z,stab)
                    k = seed.K
                    initialization = replace(initialization, restart_seed=seed)
                    diag = replace(diag, initialization=initialization)
                    rr = solve_rr(z,k,settings.rr_max_iterations)
                    initialization = replace(initialization, restart_rr=rr)
            diag = FlashDiagnostics(iteration,rr_residual=rr.residual,rr_iterations=rr.iterations,stability=stab,
                                    initialization=initialization)
            if not rr.converged or rr.status != 'two_phase':
                diag = replace(diag,message='RR did not establish a physical split; see initialization diagnostics')
                return result('rachford_rice_not_converged')
            x,y,sums,material = reconstruct(z,k,rr.beta)
            lm,vm = eos.mixture(x),eos.mixture(y)
            lf,vf = eos.fugacity(lm,lm.roots[0]),eos.fugacity(vm,vm.roots[-1])
            # Zero inventory species contributes no chemical-potential constraint.
            fugacity = tuple(log(xi)+pl-log(yi)-pv if zi else 0.
                             for xi,yi,pl,pv,zi in zip(x,y,lf.ln_phi,vf.ln_phi,z))
            diag = FlashDiagnostics(iteration,fugacity,rr.residual,material,sums,rr.iterations,stab,initialization=initialization)
            if max(abs(v) for v in fugacity) <= settings.fugacity_tolerance and max(abs(v) for v in material) <= settings.material_tolerance:
                tangent = tuple(log(xi)+pl if xi else None for xi,pl in zip(x,lf.ln_phi))
                equilibrium = stability(eos,z,settings.stability_max_iterations,tangent)
                diag = replace(diag,equilibrium_stability=equilibrium)
                if not equilibrium.converged:
                    return result('stability_not_converged')
                if not equilibrium.stable:
                    return result('flash_not_converged')
                return result('success_two_phase','vapor_liquid',
                              (phase('liquid',1-rr.beta,x,lf),phase('vapor',rr.beta,y,vf)),rr.beta,tuple(yi/xi for xi,yi in zip(x,y)))
            k = tuple(safe_exp(a-b) for a,b in zip(lf.ln_phi,vf.ln_phi))
        return result('flash_not_converged')
    except ThermodynamicError as error:
        diag = replace(diag,message=str(error))
        return result(error.status)
    except (OverflowError, ZeroDivisionError) as error:
        diag = replace(diag,message='Arithmetic outside representable numerical domain: '+type(error).__name__)
        return result('numerical_domain_error')
