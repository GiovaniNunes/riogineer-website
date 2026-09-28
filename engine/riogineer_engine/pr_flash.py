"""Standalone PT successive substitution with explicit stability and closure gates."""
from dataclasses import dataclass
from math import log
from .components import DATASET, component
from .pr_eos import MODEL, BinaryInteractions, PengRobinsonEOS, ThermodynamicError, normalized, require, safe_exp
from .pr_stability import StabilityResult, stability
from .rachford_rice import reconstruct, solve_rr
from .thermodynamics import ThermodynamicState, MolarComposition


@dataclass(frozen=True)
class SolverSettings:
    flash_max_iterations: int = 100
    stability_max_iterations: int = 100
    rr_max_iterations: int = 200
    # Qualification tolerances are intentionally fixed, not user-loosenable.
    fugacity_tolerance: float = 1e-11
    material_tolerance: float = 1e-10

    def validate(self):
        require(all(isinstance(v,int) and not isinstance(v,bool) and v > 0 for v in
                    (self.flash_max_iterations,self.stability_max_iterations,self.rr_max_iterations)), 'Invalid solver iteration limit')
        require(self.fugacity_tolerance == 1e-11 and self.material_tolerance == 1e-10, 'Qualification tolerances are fixed')


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
        for iteration in range(1,settings.flash_max_iterations+1):
            rr = solve_rr(z,k,settings.rr_max_iterations)
            diag = FlashDiagnostics(iteration,rr_residual=rr.residual,rr_iterations=rr.iterations,stability=stab)
            if not rr.converged or rr.status != 'two_phase':
                return result('rachford_rice_not_converged')
            x,y,sums,material = reconstruct(z,k,rr.beta)
            lm,vm = eos.mixture(x),eos.mixture(y)
            lf,vf = eos.fugacity(lm,lm.roots[0]),eos.fugacity(vm,vm.roots[-1])
            # Zero inventory species contributes no chemical-potential constraint.
            fugacity = tuple(log(xi)+pl-log(yi)-pv if zi else 0.
                             for xi,yi,pl,pv,zi in zip(x,y,lf.ln_phi,vf.ln_phi,z))
            diag = FlashDiagnostics(iteration,fugacity,rr.residual,material,sums,rr.iterations,stab)
            if max(abs(v) for v in fugacity) <= settings.fugacity_tolerance and max(abs(v) for v in material) <= settings.material_tolerance:
                tangent = tuple(log(xi)+pl if xi else None for xi,pl in zip(x,lf.ln_phi))
                equilibrium = stability(eos,z,settings.stability_max_iterations,tangent)
                diag = FlashDiagnostics(iteration,fugacity,rr.residual,material,sums,rr.iterations,stab,equilibrium)
                if not equilibrium.converged:
                    return result('stability_not_converged')
                if not equilibrium.stable:
                    return result('flash_not_converged')
                return result('success_two_phase','vapor_liquid',
                              (phase('liquid',1-rr.beta,x,lf),phase('vapor',rr.beta,y,vf)),rr.beta,tuple(yi/xi for xi,yi in zip(x,y)))
            k = tuple(safe_exp(a-b) for a,b in zip(lf.ln_phi,vf.ln_phi))
        return result('flash_not_converged')
    except ThermodynamicError as error:
        from dataclasses import replace
        diag = replace(diag,message=str(error))
        return result(error.status)
    except (OverflowError, ZeroDivisionError) as error:
        from dataclasses import replace
        diag = replace(diag,message='Arithmetic outside representable numerical domain: '+type(error).__name__)
        return result('numerical_domain_error')
