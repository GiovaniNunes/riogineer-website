"""Capability-scoped provider registry. Process calculation still selects M7 directly."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol
from .pr_eos import MODEL, SUPPORTED, BinaryInteractions, PengRobinsonEOS
from .pr_flash import PTResult, SolverSettings, flash_pt
from .pr_stability import stability
from .thermodynamics import MolecularCompositionProvider, PropertyPackage, ThermodynamicState


class PTPropertyPackage(PropertyPackage, Protocol):
    def flash_PT(self, state: ThermodynamicState, bip: BinaryInteractions,
                 settings: SolverSettings = SolverSettings()) -> PTResult: ...


@dataclass(frozen=True)
class PengRobinsonProvider:
    identifier: str = MODEL
    capabilities: frozenset[str] = frozenset({'pr_eos','phase_stability','single_phase_PT','two_phase_PT_flash'})
    qualified_components: frozenset[str] = SUPPORTED

    def eos(self, component_ids, temperature_K, pressure_Pa_abs, bip):
        return PengRobinsonEOS(component_ids,temperature_K,pressure_Pa_abs,bip)

    def stability(self, eos, molar_composition, max_iterations=100):
        return stability(eos,molar_composition,max_iterations)

    def flash_PT(self, state, bip, settings=SolverSettings()):
        return flash_pt(state,bip,settings)


PROVIDERS = MappingProxyType({p.identifier:p for p in (MolecularCompositionProvider(),PengRobinsonProvider())})


def property_package(identifier):
    return PROVIDERS[identifier]
