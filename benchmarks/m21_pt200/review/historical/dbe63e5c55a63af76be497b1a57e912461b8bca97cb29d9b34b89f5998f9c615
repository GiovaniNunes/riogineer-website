"""Versioned offline Cp/R polynomials, separate from M7 molecular constants.

Source: Poling et al., The Properties of Gases and Liquids, 5th ed. (2001),
Chemicals 1.5.2 Heat Capacity/PolingDatabank.tsv. See CALORIC_DATA_NOTICE.txt.
No runtime reference-library or network dependency.
"""
from dataclasses import dataclass
from types import MappingProxyType
from .pr_eos import R, finite, positive, require
from math import fsum, log

DATASET = 'riogineer_caloric@1.0'
SOURCE = 'Poling, The Properties of Gases and Liquids, 5th edition; Chemicals 1.5.2 PolingDatabank.tsv'
SOURCE_SHA256 = '9c707a81eb8896afc32cae53222b5596dabf98f318f6f26d97193016fe8f436b'


@dataclass(frozen=True)
class CaloricReference:
    identifier: str = 'ideal_gas_sensible_298.15K_101325Pa@1.0'
    temperature_K: float = 298.15
    pressure_Pa_abs: float = 101325.0
    enthalpy_convention: str = 'Pure ideal-gas h=0 at reference T; no formation terms'
    entropy_convention: str = 'Pure ideal-gas s=0 at reference T/P; pressure and ideal mixing included; not third-law absolute'


REFERENCE = CaloricReference()


@dataclass(frozen=True)
class CpCorrelation:
    component_id: str
    CAS: str
    coefficients: tuple[float, ...]
    Tmin_K: float
    Tmax_K: float
    dataset: str = DATASET
    form: str = 'Cp/R=sum(c_j*T^j), j=0..4'
    coefficient_units: tuple[str, ...] = ('1', 'K^-1', 'K^-2', 'K^-3', 'K^-4')
    output_unit: str = 'J/(mol K)'
    source: str = SOURCE
    source_sha256: str = SOURCE_SHA256

    def validate(self, temperature_K):
        positive(temperature_K, 'Temperature K')
        require(len(self.coefficients) == 5 and all(finite(v) for v in self.coefficients),
                'Missing or nonfinite Cp coefficients', 'invalid_caloric_data')
        require(finite(self.Tmin_K) and finite(self.Tmax_K) and 0 < self.Tmin_K <= self.Tmax_K,
                'Invalid Cp validity range', 'invalid_caloric_data')
        require(self.Tmin_K <= temperature_K <= self.Tmax_K and
                self.Tmin_K <= REFERENCE.temperature_K <= self.Tmax_K,
                'Temperature outside Cp validity for '+self.component_id, 'caloric_out_of_range')


CORRELATIONS = MappingProxyType({c.component_id:c for c in (
    CpCorrelation('methane','74-82-8',(4.568,-.008975,3.631e-5,-3.407e-8,1.091e-11),50.,1000.),
    CpCorrelation('n_hexane','110-54-3',(8.831,-.000166,.00014302,-1.8314e-7,7.124e-11),200.,1000.),
)})


@dataclass(frozen=True)
class IdealComponentCaloric:
    component_id: str
    Cp_ig_J_mol_K: float
    h_ig_J_mol: float
    s_ig_temperature_J_mol_K: float


def component_caloric(component_id, temperature_K):
    require(component_id in ('methane','n_hexane'), 'Only methane/n_hexane caloric data qualified; water excluded', 'unsupported_components')
    correlation = CORRELATIONS.get(component_id)
    require(isinstance(correlation,CpCorrelation), 'Missing caloric data: '+component_id, 'missing_caloric_data')
    correlation.validate(temperature_K)
    t, t0, c = temperature_K, REFERENCE.temperature_K, correlation.coefficients
    cp = R*fsum(v*t**j for j,v in enumerate(c))
    h = R*fsum(v*(t**(j+1)-t0**(j+1))/(j+1) for j,v in enumerate(c))
    s = R*(c[0]*log(t/t0)+fsum(c[j]*(t**j-t0**j)/j for j in range(1,5)))
    require(all(finite(v) for v in (cp,h,s)) and cp > 0, 'Nonfinite/nonpositive ideal Cp or nonfinite H/S', 'numerical_domain_error')
    return IdealComponentCaloric(component_id,cp,h,s)
