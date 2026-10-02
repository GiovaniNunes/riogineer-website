"""Immutable offline component data. Provenance/rounding: MILESTONE_7.md."""
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping

DATASET = 'riogineer_components@1.0'
UNITS = MappingProxyType(dict(molecular_weight='kg/kmol', critical_temperature='K',
                              critical_pressure='Pa absolute', acentric_factor='dimensionless'))
SOURCE = 'https://raw.githubusercontent.com/CoolProp/CoolProp/v7.1.0/dev/fluids/'


@dataclass(frozen=True)
class Component:
    id: str
    display_name: str
    molecular_weight: float
    critical_temperature: float
    critical_pressure: float
    acentric_factor: float
    source: str

    def __post_init__(self):
        if not self.id or not self.display_name or not self.source:
            raise ValueError('Component identity and provenance are required')
        for name in ('molecular_weight', 'critical_temperature', 'critical_pressure', 'acentric_factor'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isfinite(value) or (name != 'acentric_factor' and value <= 0):
                raise ValueError('Invalid component ' + name)


COMPONENTS: Mapping[str, Component] = MappingProxyType({c.id: c for c in (
    Component('methane', 'Methane', 16.0428, 190.564, 4599200.0, 0.01142, SOURCE + 'Methane.json'),
    Component('n_hexane', 'n-Hexane', 86.17536, 507.82, 3044115.328359688,
              0.3003189315498438, SOURCE + 'n-Hexane.json'),
    Component('water', 'Water', 18.015268, 647.096, 22064000.0, 0.3442920843, SOURCE + 'Water.json'),
)})


def component(component_id: str) -> Component:
    """Canonical IDs only; display names and aliases never select a component."""
    try:
        return COMPONENTS[component_id]
    except KeyError as error:
        raise ValueError('Unknown canonical component ID: ' + component_id) from error
