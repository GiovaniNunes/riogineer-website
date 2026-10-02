"""Opt-in PR caloric properties. PT equilibrium owns phase/root selection.

No equipment enrichment, PH/PS solver, benchmark imports or second EOS.
All molar properties use SI and the explicit sensible ideal-gas reference.
"""
from dataclasses import dataclass
from math import fsum, log, log1p, sqrt
from .caloric_data import DATASET, REFERENCE, SOURCE, SOURCE_SHA256, CaloricReference, IdealComponentCaloric, component_caloric
from .components import DATASET as COMPONENT_DATASET, component
from .pr_eos import (R, MODEL, SUPPORTED, BinaryInteractions, EOSState, PureParameters,
                     PengRobinsonEOS, ThermodynamicError, finite, normalized, positive, pure_parameters, require)
from .pr_flash import PTResult, SolverSettings, flash_pt
from .thermodynamics import Composition, MolarComposition, ThermodynamicState


@dataclass(frozen=True)
class CaloricProvenance:
    provider: str = MODEL
    component_dataset: str = COMPONENT_DATASET
    caloric_dataset: str = DATASET
    reference: CaloricReference = REFERENCE
    cp_source: str = SOURCE
    cp_source_sha256: str = SOURCE_SHA256
    bip_derivative_convention: str = 'Constant explicit zero kij; dkij/dT=0'
    scope: str = 'methane/n_hexane PR phase caloric properties; no process energy integration'


@dataclass(frozen=True)
class PhaseCaloricProperties:
    # Joins to equilibrium.phases; T/P, composition, Z and phase fraction stay there.
    phase_identifier: str
    mixture_MW_kg_kmol: float
    mixture_MW_kg_mol: float
    component_ideal: tuple[IdealComponentCaloric, ...]
    Cp_ig_J_mol_K: float
    h_ig_J_mol: float
    h_res_J_mol: float
    h_total_J_mol: float
    s_ig_temperature_J_mol_K: float
    s_ig_pressure_J_mol_K: float
    s_ig_mixing_J_mol_K: float
    s_ig_J_mol_K: float
    s_res_J_mol_K: float
    s_total_J_mol_K: float
    h_total_J_kg: float
    s_total_J_kg_K: float
    eos: EOSState
    pure_parameters: tuple[PureParameters, ...]
    T_da_minus_a_Pa_m6_mol2: float
    PR_log_term: float
    ln_Z_minus_B: float


@dataclass(frozen=True)
class EquilibriumCaloricAggregate:
    h_J_mol: float
    s_J_mol_K: float
    mixture_MW_kg_kmol: float
    h_J_kg: float
    s_J_kg_K: float
    phase_difference_h_J_mol: float | None
    phase_difference_s_J_mol_K: float | None


@dataclass(frozen=True)
class CaloricResult:
    status: str
    equilibrium: PTResult | None
    phases: tuple[PhaseCaloricProperties, ...] = ()
    aggregate: EquilibriumCaloricAggregate | None = None
    message: str = ''
    provenance: CaloricProvenance = CaloricProvenance()


def molar_to_mass(value, MW_kg_kmol):
    """J/mol -> J/kg or J/(mol K) -> J/(kg K), explicitly dividing MW by 1000."""
    require(finite(value), 'Nonfinite molar property')
    positive(MW_kg_kmol, 'MW kg/kmol')
    mw_kg_mol = MW_kg_kmol/1000.
    require(finite(mw_kg_mol) and mw_kg_mol > 0, 'MW conversion outside numerical domain', 'numerical_domain_error')
    mass_value = value/mw_kg_mol
    require(finite(mass_value), 'Nonfinite mass-specific property', 'numerical_domain_error')
    return mass_value


def enthalpy_flow_W(mass_flow_kg_h, h_J_kg):
    require(finite(mass_flow_kg_h) and mass_flow_kg_h >= 0, 'Mass flow must be finite and nonnegative')
    require(finite(h_J_kg), 'Specific enthalpy must be finite')
    value = mass_flow_kg_h/3600.*h_J_kg
    require(finite(value), 'Nonfinite enthalpy flow', 'numerical_domain_error')
    return value


def validate_input(state, bip):
    require(isinstance(state,ThermodynamicState), 'ThermodynamicState required')
    positive(state.temperature_K,'Temperature K')
    positive(state.pressure_Pa_abs,'Pressure Pa absolute')
    c = state.composition
    require(isinstance(c,(Composition,MolarComposition)), 'Molecular composition required')
    ids = c.component_ids
    require(bool(ids) and all(isinstance(i,str) for i in ids) and len(set(ids)) == len(ids), 'Unique canonical component IDs required')
    require(set(ids) <= SUPPORTED, 'Only methane/n_hexane caloric scope qualified; water excluded', 'unsupported_components')
    require(c.molar_fractions is not None, 'Molar composition unavailable')
    if isinstance(c,Composition):
        require(set(c.molar_fractions) == set(ids), 'Molar composition/component mismatch')
        fractions = tuple(c.molar_fractions[i] for i in ids)
    else:
        fractions = c.molar_fractions
    z = normalized(fractions)
    require(len(z) == len(ids), 'Molar composition/component dimensions')
    # A different BIP representation must explicitly qualify derivative semantics.
    require(type(bip) is BinaryInteractions and bip.temperature_dependence == 'constant',
            'Only explicitly constant BIP matrices supported for caloric derivatives', 'unsupported_bip')
    require(bip.component_ids == ids, 'BIP component order mismatch')
    require(all(v == 0 for row in bip.values for v in row), 'M10 caloric qualification requires explicit zero kij', 'unsupported_bip')
    require(getattr(state.provenance,'provider',None) == MODEL and
            getattr(state.provenance,'bip_specification',None) == bip.identifier, 'State/provider/BIP provenance mismatch')
    # Validate data for every declared component, including zero-inventory species.
    for i in ids:
        component_caloric(i,state.temperature_K)
    return ids,z


def _phase_properties(eos, phase):
    """Internal: phase is emitted by this call's successful qualified PT calculation."""
    t, p, q = eos.temperature_K, eos.pressure_Pa_abs, phase.composition
    mixed = eos.mixture(q)
    require(phase.identifier in ('liquid','vapor') and finite(phase.Z) and phase.Z in mixed.roots,
            'Invalid phase/root association', 'phase_mismatch')
    pure = tuple(pure_parameters(i,t) for i in eos.component_ids)
    require(all(finite(v) for c in pure for v in (c.alpha,c.da_dT,c.dalpha_dT)) and
            all(finite(v) for v in (mixed.a,mixed.b,mixed.A,mixed.B,mixed.da_dT)),
            'Nonfinite EOS caloric parameters/derivatives', 'numerical_domain_error')
    ideal = tuple(component_caloric(i,t) for i in eos.component_ids)
    cp = fsum(x*c.Cp_ig_J_mol_K for x,c in zip(q,ideal))
    hi = fsum(x*c.h_ig_J_mol for x,c in zip(q,ideal))
    st = fsum(x*c.s_ig_temperature_J_mol_K for x,c in zip(q,ideal))
    sp = -R*(log(p)-log(REFERENCE.pressure_Pa_abs))
    sm = -R*fsum(x*log(x) for x in q if x)
    si = st+sp+sm
    z, b, B = phase.Z, mixed.b, mixed.B
    denominator = z+(1-sqrt(2))*B
    require(b > 0 and B > 0 and z-B > 0 and denominator > 0,
            'Invalid PR caloric logarithm/denominator', 'numerical_domain_error')
    ratio = 2*sqrt(2)*B/denominator
    log_zb_argument = z-1-B
    require(finite(ratio) and ratio > -1 and finite(log_zb_argument) and log_zb_argument > -1,
            'PR caloric logarithm outside representable domain', 'numerical_domain_error')
    logarithm = log1p(ratio)
    ln_zb = log1p(log_zb_argument)
    derivative_term = t*mixed.da_dT-mixed.a
    hr = R*t*(z-1)+derivative_term*logarithm/(2*sqrt(2)*b)
    sr = R*ln_zb+mixed.da_dT*logarithm/(2*sqrt(2)*b)
    h, s = hi+hr, si+sr
    mw = fsum(x*component(i).molecular_weight for x,i in zip(q,eos.component_ids))
    require(all(finite(v) for v in (cp,hi,st,sp,sm,si,hr,sr,h,s,mw,logarithm,ln_zb,derivative_term)),
            'Nonfinite caloric intermediate/result', 'numerical_domain_error')
    return PhaseCaloricProperties(phase.identifier,mw,mw/1000.,ideal,cp,hi,hr,h,st,sp,sm,si,sr,s,
        molar_to_mass(h,mw),molar_to_mass(s,mw),mixed,pure,derivative_term,logarithm,ln_zb)


def caloric_pt(state, bip, settings=SolverSettings(), *, phase=None, root=None, single_phase=False):
    """Fresh PT evaluation prevents stale, fabricated or mismatched phase enrichment.

    Failure returns no phase caloric values or aggregate, even after PT success.
    Existing PT results/diagnostics are retained as evidence when available.
    """
    equilibrium = None
    try:
        ids,z = validate_input(state,bip)
        require(isinstance(settings,SolverSettings), 'SolverSettings required')
        settings.validate()
        require(phase is None or phase in ('liquid','vapor'), 'Invalid phase label')
        require(root is None or finite(root) and root > 0, 'Invalid phase root')
        require(single_phase or (phase is None and root is None), 'Phase/root selectors require single-phase evaluation')
        equilibrium = flash_pt(state,bip,settings)
        if equilibrium.status not in ('success_single_phase','success_two_phase'):
            return CaloricResult(equilibrium.status,equilibrium,message=equilibrium.diagnostics.message)
        if single_phase:
            require(len(equilibrium.phases) == 1, 'State requires two-phase equilibrium caloric evaluation', 'phase_mismatch')
            selected = equilibrium.phases[0]
            require(phase is None or selected.identifier == phase, 'Requested phase is not the stable phase', 'phase_mismatch')
            # Root is a check, never permission to substitute an arbitrary EOS root.
            require(root is None or abs(root-selected.Z) <= 1e-12*max(1.,abs(selected.Z)), 'Requested root differs from stable PT root', 'phase_mismatch')
        eos = PengRobinsonEOS(ids,state.temperature_K,state.pressure_Pa_abs,bip)
        phases = tuple(_phase_properties(eos,p) for p in equilibrium.phases)
        h = fsum(p.fraction*c.h_total_J_mol for p,c in zip(equilibrium.phases,phases))
        s = fsum(p.fraction*c.s_total_J_mol_K for p,c in zip(equilibrium.phases,phases))
        mw = fsum(x*component(i).molecular_weight for x,i in zip(z,ids))
        by_id = {c.phase_identifier:c for c in phases}
        dh = by_id['vapor'].h_total_J_mol-by_id['liquid'].h_total_J_mol if len(phases)==2 else None
        ds = by_id['vapor'].s_total_J_mol_K-by_id['liquid'].s_total_J_mol_K if len(phases)==2 else None
        require(all(finite(v) for v in (h,s,mw)) and all(v is None or finite(v) for v in (dh,ds)),
                'Nonfinite equilibrium caloric aggregate', 'numerical_domain_error')
        aggregate = EquilibriumCaloricAggregate(h,s,mw,molar_to_mass(h,mw),molar_to_mass(s,mw),dh,ds)
        return CaloricResult(equilibrium.status,equilibrium,phases,aggregate)
    except ThermodynamicError as error:
        return CaloricResult(error.status,equilibrium,message=str(error))
    except (OverflowError,ZeroDivisionError,ValueError) as error:
        return CaloricResult('numerical_domain_error',equilibrium,message='Caloric arithmetic outside numerical domain: '+str(error))
