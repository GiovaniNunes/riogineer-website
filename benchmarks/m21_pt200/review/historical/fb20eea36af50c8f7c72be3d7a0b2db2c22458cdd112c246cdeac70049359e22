"""Canonical PR (1976), SI molar basis. No process equipment or benchmark dependencies."""
from dataclasses import dataclass
from math import acos, cos, copysign, exp, fsum, isfinite, log, log1p, pi, sqrt
from .components import component

R = 8.31446261815324
MODEL = 'peng_robinson@1.0'
COMPOSITION_TOLERANCE = 1e-12
SUPPORTED = frozenset({'methane', 'n_hexane'})


class ThermodynamicError(ValueError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def require(condition, message, status='invalid_input'):
    if not condition:
        raise ThermodynamicError(status, message)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def positive(value, name):
    require(finite(value) and value > 0, name + ' must be finite and positive')
    return value


def normalized(values):
    values = tuple(values)
    require(bool(values) and all(finite(v) and v >= 0 for v in values), 'Invalid molar composition')
    total = fsum(values)
    require(abs(total - 1) <= COMPOSITION_TOLERANCE, 'Molar composition must sum to one')
    return tuple(v / total for v in values)


def safe_exp(value):
    # Reject unrepresentable/extreme updates rather than clipping the equilibrium.
    require(finite(value) and -700 <= value <= 700, 'Exponent outside numerical domain', 'numerical_domain_error')
    return exp(value)


@dataclass(frozen=True)
class BinaryInteractions:
    identifier: str
    component_ids: tuple[str, ...]
    values: tuple[tuple[float, ...], ...]
    source: str
    model: str = MODEL

    @property
    def temperature_dependence(self):
        """This numeric matrix represents constant BIPs, never a temperature model."""
        return 'constant'

    def __post_init__(self):
        object.__setattr__(self, 'component_ids', tuple(self.component_ids))
        object.__setattr__(self, 'values', tuple(tuple(row) for row in self.values))
        n = len(self.component_ids)
        require(bool(self.identifier) and bool(self.source) and self.model == MODEL, 'BIP identity/source/model required')
        require(n > 0 and len(set(self.component_ids)) == n, 'BIP component identities must be unique')
        require(len(self.values) == n and all(len(row) == n for row in self.values), 'Missing BIP entries/dimensions')
        require(all(finite(v) for row in self.values for v in row), 'Nonfinite BIP')
        require(all(self.values[i][i] == 0 for i in range(n)), 'BIP diagonal must be zero')
        require(all(self.values[i][j] == self.values[j][i] for i in range(n) for j in range(n)), 'BIP must be symmetric')


@dataclass(frozen=True)
class PureParameters:
    kappa: float
    alpha: float
    a: float  # Pa m6/mol2
    b: float  # m3/mol
    da_dT: float

    @property
    def dalpha_dT(self):
        """Recover alpha derivative from the existing analytic da/dT and a=a0*alpha."""
        return self.da_dT*self.alpha/self.a


def pure_parameters(component_id, temperature):
    positive(temperature, 'Temperature K')
    require(component_id in SUPPORTED, 'Component outside qualified PR scope', 'unsupported_components')
    c = component(component_id)
    k = .37464 + 1.54226*c.acentric_factor - .26992*c.acentric_factor**2
    s = sqrt(temperature/c.critical_temperature)
    term = 1 + k*(1-s)
    a0 = .45724*R**2*c.critical_temperature**2/c.critical_pressure
    result = PureParameters(k, term**2, a0*term**2,
                            .07780*R*c.critical_temperature/c.critical_pressure,
                            -a0*term*k/(c.critical_temperature*s))
    require(all(finite(v) for v in vars(result).values()) and result.a > 0,
            'Pure parameter domain', 'numerical_domain_error')
    return result


def real_cubic_roots(c2, c1, c0):
    """All distinct real roots of a monic cubic; real Cardano/trigonometric branches.

    Newton polishing removes cancellation in small PR roots. No complex-root
    imaginary tolerance is needed. Near-multiple roots use a scaled discriminant.
    """
    p = c1 - c2*c2/3
    q = 2*c2**3/27 - c2*c1/3 + c0
    d = (q/2)**2 + (p/3)**3
    eps = 2e-15*max(abs((q/2)**2), abs((p/3)**3), 1e-300)
    if d > eps:
        cb = lambda v: copysign(abs(v)**(1/3), v)
        u = cb(-q/2 - copysign(sqrt(d), q))
        roots = [u - p/(3*u) - c2/3] if u else [-c2/3]
    elif p < 0:
        angle = acos(max(-1., min(1., -q/(2*sqrt(-(p/3)**3)))))
        roots = [2*sqrt(-p/3)*cos((angle+2*i*pi)/3)-c2/3 for i in range(3)]
    else:
        roots = [-c2/3]
    polished = []
    for z in sorted(roots):
        for _ in range(5):
            f = ((z+c2)*z+c1)*z+c0
            df = (3*z+2*c2)*z+c1
            if abs(df) <= 1e-14:
                break
            step = f/df
            z -= step
            if abs(step) < 1e-16*max(1, abs(z)):
                break
        require(finite(z), 'Nonfinite cubic root', 'numerical_domain_error')
        if not polished or abs(z-polished[-1]) > 1e-12*max(1, abs(z)):
            polished.append(z)
    return tuple(sorted(polished))


@dataclass(frozen=True)
class EOSState:
    composition: tuple[float, ...]
    a: float
    b: float
    A: float
    B: float
    roots: tuple[float, ...]
    a_rows: tuple[float, ...]
    da_dT: float


@dataclass(frozen=True)
class Fugacity:
    Z: float
    ln_phi: tuple[float, ...]
    phi: tuple[float, ...]


@dataclass(frozen=True)
class PengRobinsonEOS:
    component_ids: tuple[str, ...]
    temperature_K: float
    pressure_Pa_abs: float
    bip: BinaryInteractions

    def __post_init__(self):
        object.__setattr__(self, 'component_ids', tuple(self.component_ids))
        ids = self.component_ids
        require(bool(ids) and len(set(ids)) == len(ids), 'Unique component identities required')
        require(set(ids) <= SUPPORTED, 'Only methane/n_hexane qualified; water excluded', 'unsupported_components')
        positive(self.temperature_K, 'Temperature K')
        positive(self.pressure_Pa_abs, 'Pressure Pa absolute')
        require(isinstance(self.bip, BinaryInteractions) and self.bip.component_ids == ids, 'Explicit ordered BIP specification required')

    def mixture(self, composition):
        x = normalized(composition)
        require(len(x) == len(self.component_ids), 'Composition/order dimensions')
        pure = tuple(pure_parameters(c, self.temperature_K) for c in self.component_ids)
        n = len(x)
        aij = tuple(tuple(sqrt(pure[i].a)*sqrt(pure[j].a)*(1-self.bip.values[i][j])
                          for j in range(n)) for i in range(n))
        rows = tuple(fsum(x[j]*aij[i][j] for j in range(n)) for i in range(n))
        a = fsum(x[i]*rows[i] for i in range(n))
        b = fsum(x[i]*pure[i].b for i in range(n))
        at = fsum(x[i]*x[j]*aij[i][j]*.5*(pure[i].da_dT/pure[i].a+pure[j].da_dT/pure[j].a)
                  for i in range(n) for j in range(n))
        rt = R*self.temperature_K
        A, B = a*self.pressure_Pa_abs/rt**2, b*self.pressure_Pa_abs/rt
        require(all(finite(v) for v in (a,b,at,A,B)) and a > 0 and B > 0,
                'Mixture parameter domain', 'numerical_domain_error')
        roots = real_cubic_roots(B-1, A-3*B*B-2*B, -A*B+B*B+B**3)
        roots = tuple(z for z in roots if z > B)
        require(bool(roots), 'No physical Z > B root', 'numerical_domain_error')
        return EOSState(x, a, b, A, B, roots, rows, at)

    def fugacity(self, state, root):
        """Classical quadratic-mixing derivative; phi dimensionless, natural logs."""
        require(root in state.roots and root > state.B, 'Invalid selected root', 'numerical_domain_error')
        B, A, z = state.B, state.A, root
        denominator = z + (1-sqrt(2))*B
        require(denominator > 0, 'Invalid PR logarithm', 'numerical_domain_error')
        ratio_log = log1p(2*sqrt(2)*B/denominator)
        lnphi = []
        for i, c in enumerate(self.component_ids):
            br = pure_parameters(c, self.temperature_K).b/state.b
            lnphi.append(br*(z-1)-log(z-B)-A/(2*sqrt(2)*B)*(2*state.a_rows[i]/state.a-br)*ratio_log)
        return Fugacity(z, tuple(lnphi), tuple(safe_exp(v) for v in lnphi))

    def lowest_gibbs(self, state):
        candidates = [self.fugacity(state, z) for z in (state.roots[0], state.roots[-1])]
        return min(candidates, key=lambda f: fsum(x*v for x,v in zip(state.composition, f.ln_phi)))

    def phase_identification(self, state, root):
        """PIP = V*(P_VT/P_T - P_VV/P_V); >1 liquid-like, <1 vapor-like.

        Used only AFTER stability, never as evidence of phase-count stability.
        Analytical PR derivatives at fixed composition; no caloric properties.
        """
        t, a, b, at = self.temperature_K, state.a, state.b, state.da_dT
        v = root*R*t/self.pressure_Pa_abs
        d = v*v+2*b*v-b*b
        dv = 2*(v+b)
        pt = R/(v-b)-at/d
        pv = -R*t/(v-b)**2+a*dv/d**2
        pvt = -R/(v-b)**2+at*dv/d**2
        pvv = 2*R*t/(v-b)**3+a*(2/d**2-2*dv**2/d**3)
        require(pt != 0 and pv < 0, 'Singular/unstable PIP domain', 'numerical_domain_error')
        pip = v*(pvt/pt-pvv/pv)
        require(finite(pip) and abs(pip-1) > 1e-10, 'Indeterminate phase label', 'numerical_domain_error')
        return pip
