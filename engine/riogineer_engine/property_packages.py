"""Capability-scoped provider registry. Process calculation still selects M7 directly."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol
from .pr_eos import MODEL, SUPPORTED, BinaryInteractions, PengRobinsonEOS
from .pr_flash import PTResult, SolverSettings, flash_pt
from .pr_stability import stability
from .numerical_profiles import UNSPECIFIED, _Unspecified, resolve_pt_settings
from .pr_ph_flash import PHSpecification, PHSettings, PHResult, flash_ph
from .pr_ps_flash import PSSpecification, PSSettings, PSResult, flash_ps
from .pr_caloric import CaloricResult, caloric_pt
from .thermodynamics import MolecularCompositionProvider, PropertyPackage, ThermodynamicState


class PTPropertyPackage(PropertyPackage, Protocol):
    def flash_PT(self, state: ThermodynamicState, bip: BinaryInteractions,
                 settings: SolverSettings | None | _Unspecified = UNSPECIFIED, *, numerical_profile=None) -> PTResult: ...


class CaloricPropertyPackage(PTPropertyPackage, Protocol):
    def phase_caloric_TP(self, state: ThermodynamicState, bip: BinaryInteractions,
                         *, phase: str | None = None, root: float | None = None,
                         settings: SolverSettings | None | _Unspecified = UNSPECIFIED, numerical_profile=None) -> CaloricResult: ...

    def equilibrium_caloric_PT(self, state: ThermodynamicState, bip: BinaryInteractions,
                               settings: SolverSettings | None | _Unspecified = UNSPECIFIED, *, numerical_profile=None) -> CaloricResult: ...


class PHPropertyPackage(CaloricPropertyPackage, Protocol):
    def flash_PH(self, specification: PHSpecification, bip: BinaryInteractions,
                 settings: PHSettings = PHSettings(), *, numerical_profile=None) -> PHResult: ...


class PSPropertyPackage(CaloricPropertyPackage, Protocol):
    def flash_PS(self, specification: PSSpecification, bip: BinaryInteractions,
                 settings: PSSettings = PSSettings(), *, numerical_profile=None) -> PSResult: ...


@dataclass(frozen=True)
class PengRobinsonProvider:
    identifier: str = MODEL
    capabilities: frozenset[str] = frozenset({'pr_eos','phase_stability','single_phase_PT','two_phase_PT_flash','phase_caloric_TP','equilibrium_caloric_PT','flash_PH','flash_PS'})
    qualified_components: frozenset[str] = SUPPORTED

    def flash_PS(self, specification: PSSpecification, bip: BinaryInteractions,
                 settings: PSSettings = PSSettings(), *, numerical_profile=None) -> PSResult:
        return flash_ps(specification,bip,self.equilibrium_caloric_PT,settings,numerical_profile=numerical_profile)

    def flash_PH(self, specification: PHSpecification, bip: BinaryInteractions,
                 settings: PHSettings = PHSettings(), *, numerical_profile=None) -> PHResult:
        return flash_ph(specification,bip,self.equilibrium_caloric_PT,settings,numerical_profile=numerical_profile)

    def eos(self, component_ids, temperature_K, pressure_Pa_abs, bip):
        return PengRobinsonEOS(component_ids,temperature_K,pressure_Pa_abs,bip)

    def stability(self, eos, molar_composition, max_iterations=100):
        return stability(eos,molar_composition,max_iterations)

    def flash_PT(self, state, bip, settings=UNSPECIFIED, *, numerical_profile=None):
        return flash_pt(state,bip,resolve_pt_settings(numerical_profile,settings))

    def phase_caloric_TP(self, state, bip, *, phase=None, root=None, settings=UNSPECIFIED, numerical_profile=None):
        return caloric_pt(state,bip,resolve_pt_settings(numerical_profile,settings),phase=phase,root=root,single_phase=True)

    def equilibrium_caloric_PT(self, state, bip, settings=UNSPECIFIED, *, numerical_profile=None):
        return caloric_pt(state,bip,resolve_pt_settings(numerical_profile,settings))


PROVIDERS = MappingProxyType({p.identifier:p for p in (MolecularCompositionProvider(),PengRobinsonProvider())})


def property_package(identifier):
    return PROVIDERS[identifier]
