"""Explicit numerical policy, independent of physical property-package identity.

Only PT200 is a named extension. Unnamed custom PT controls remain supported;
they are never inferred to be qualified profiles from their iteration budget.
"""
from dataclasses import dataclass, fields, replace
from enum import Enum
from .pr_flash import AccuracyProfile, SolverSettings
from .pr_eos import require


class _Unspecified(Enum):
    VALUE = 'omitted'


UNSPECIFIED = _Unspecified.VALUE


class NumericalProfile(str, Enum):
    PT200 = 'pr_high_accuracy_pt200@1'


@dataclass(frozen=True)
class ProfiledPTSettings(SolverSettings):
    flash_max_iterations: int = 200
    fugacity_tolerance: float = 1e-12
    profile: AccuracyProfile = AccuracyProfile.HIGH_ACCURACY
    numerical_profile: str = NumericalProfile.PT200.value

    def validate(self):
        super().validate()
        require(self.numerical_profile == NumericalProfile.PT200.value,
                'Unknown numerical profile')
        expected = replace(SolverSettings.high_accuracy(), flash_max_iterations=200)
        require(all(getattr(self, f.name) == getattr(expected, f.name)
                    for f in fields(SolverSettings)), 'Conflicting numerical profile/settings')


PT200 = ProfiledPTSettings()


def resolve_pt_settings(numerical_profile=None, settings=UNSPECIFIED, *, default=SolverSettings()):
    """Resolve explicit policy before evaluation; invalid selection raises ValueError.

    Supplying matching unnamed controls alongside an identifier is allowed and
    returns canonical named controls. Omission never infers a named profile.
    """
    if numerical_profile is None:
        selected = default if settings is UNSPECIFIED else settings
        # Historical unnamed controls are validated by the existing PT/caloric
        # routine, retaining its controlled invalid-input result semantics.
        if isinstance(selected, ProfiledPTSettings):
            selected.validate()
        return selected
    require(isinstance(numerical_profile, str) and numerical_profile == NumericalProfile.PT200.value,
            'Unknown numerical profile')
    if settings is not UNSPECIFIED:
        require(isinstance(settings, SolverSettings), 'SolverSettings required')
        settings.validate()
        require(all(getattr(settings, f.name) == getattr(PT200, f.name)
                    for f in fields(SolverSettings)), 'Conflicting numerical profile/settings')
    return PT200
