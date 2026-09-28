"""Molecular projection of existing material states; no energy equations or phase inference."""
from dataclasses import dataclass
from math import fsum, isfinite
from types import MappingProxyType
from typing import Mapping, Protocol
from .components import DATASET, component

PROVIDER = 'molecular_composition@1.0'
MASS_TOLERANCE_KG_H = 1e-8  # per component; same as process balance basis
FRACTION_TOLERANCE = 1e-12


def immutable(values):
    return MappingProxyType(dict(values))


def valid(value, name, positive=False):
    if isinstance(value, bool) or not isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError('Invalid finite ' + name)
    return value


@dataclass(frozen=True)
class Composition:
    component_ids: tuple[str, ...]
    component_mass_flow_kg_h: Mapping[str, float]
    mass_flow_kg_h: float
    mass_fractions: Mapping[str, float] | None
    component_molar_flow_kmol_h: Mapping[str, float]
    molar_flow_kmol_h: float
    molar_fractions: Mapping[str, float] | None
    molecular_weight_kg_kmol: float | None


@dataclass(frozen=True)
class PropertyProvenance:
    provider: str
    component_dataset: str
    molecular_weights_kg_kmol: Mapping[str, float]
    status: str = 'completed'


@dataclass(frozen=True)
class ThermodynamicState:
    temperature_K: float
    pressure_Pa_abs: float
    composition: Composition
    provenance: PropertyProvenance
    # Future providers may extend state with an arbitrary collection of phases.
    # Absence of phase fields means unqualified, not single-phase or zero phases.


class PropertyPackage(Protocol):
    """Capability-scoped boundary; flash is deliberately outside this interface."""
    identifier: str
    capabilities: frozenset[str]

    def enrich(self, state: Mapping) -> ThermodynamicState: ...


@dataclass(frozen=True)
class MolecularCompositionProvider:
    identifier: str = PROVIDER
    capabilities: frozenset[str] = frozenset({'molecular_composition'})

    def enrich(self, state: Mapping) -> ThermodynamicState:
        rates = dict(sorted(state['component_mass_flow_kg_h'].items()))
        if not rates:
            raise ValueError('Composition must have canonical components')
        weights = {c: component(c).molecular_weight for c in rates}
        for c, rate in rates.items():
            valid(rate, c + ' mass flow')
        total = valid(state['mass_flow_kg_h'], 'total mass flow')
        if abs(fsum(rates.values()) - total) > len(rates) * MASS_TOLERANCE_KG_H:
            raise ValueError('Total mass flow is inconsistent with component flows')
        molar = {c: valid(rate / weights[c], c + ' molar flow') for c, rate in rates.items()}
        n = valid(fsum(molar.values()), 'total molar flow')
        z = {c: molar[c] / n for c in rates} if n > 0 else None
        mw = valid(total / n, 'mixture molecular weight', positive=True) if n > 0 else None
        if total > 0 and n == 0:
            raise ValueError('Positive mass flow cannot produce zero molar flow')
        if z is not None and abs(fsum(z.values()) - 1) > FRACTION_TOLERANCE:
            raise ValueError('Molar fractions do not sum to one')
        composition = Composition(tuple(rates), immutable(rates), total,
            immutable({c: rate / total for c, rate in rates.items()}) if total > 0 else None,
            immutable(molar), n, immutable(z) if z is not None else None, mw)
        return ThermodynamicState(valid(state['temperature_K'], 'temperature', True),
            valid(state['pressure_Pa_abs'], 'pressure', True), composition,
            PropertyProvenance(self.identifier, DATASET, immutable(weights)))


def quantity(value, unit):
    return dict(value=value, status='not_calculated' if value is None else 'calculated', unit=unit)


def enrich_results(output):
    """Called only after process execution. Stable-ID states and process numbers stay intact."""
    from copy import deepcopy
    enriched = deepcopy(output)
    provider: PropertyPackage = MolecularCompositionProvider()
    for state in enriched['streams'].values():
        thermo = provider.enrich(state)
        c, p = thermo.composition, thermo.provenance
        state['properties'].update(
            molar_flow=quantity(c.molar_flow_kmol_h, 'kmol/h'),
            molecular_mass=quantity(c.molecular_weight_kg_kmol, 'kg/kmol'),
            molar_composition=quantity(dict(c.molar_fractions) if c.molar_fractions is not None else None, 'mol/mol'),
            component_molar_flow=quantity(dict(c.component_molar_flow_kmol_h), 'kmol/h'))
        state['property_provenance'] = dict(provider=p.provider, component_dataset=p.component_dataset,
            molecular_weights_kg_kmol=dict(p.molecular_weights_kg_kmol), status=p.status,
            input_basis='component_mass_flow_kg_h')
    enriched['process_result_version'] = output['schema_version']
    enriched['schema_version'] = '1.5'
    enriched['engine']['version'] = '1.4.0'
    return enriched
