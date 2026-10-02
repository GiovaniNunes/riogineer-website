"""Bracketed molar Rachford–Rice. Endpoint tendencies are NOT phase stability."""
from dataclasses import dataclass
from math import fsum
from .pr_eos import finite, normalized, require


@dataclass(frozen=True)
class RRResult:
    status: str
    beta: float | None
    residual: float
    converged: bool
    iterations: int


def residual(z, k, beta):
    require(finite(beta) and 0 <= beta <= 1, 'RR beta domain', 'numerical_domain_error')
    denominators = tuple((1-beta)+beta*v for v in k)
    require(all(finite(v) and v > 0 for v in denominators), 'RR denominator domain', 'numerical_domain_error')
    result = fsum(zi*((ki-1)/di) for zi,ki,di in zip(z,k,denominators))
    require(finite(result), 'RR nonfinite residual', 'numerical_domain_error')
    return result


def solve_rr(z, k, max_iterations=200):
    z,k = normalized(z),tuple(k)
    require(len(z)==len(k) and all(finite(v) and v > 0 for v in k), 'RR requires positive finite ordered K')
    require(isinstance(max_iterations,int) and not isinstance(max_iterations,bool) and max_iterations > 0, 'Invalid RR iteration limit')
    low,high = residual(z,k,0.),residual(z,k,1.)
    if low <= 0:
        return RRResult('liquid_tendency',0.,low,True,0)
    if high >= 0:
        return RRResult('vapor_tendency',1.,high,True,0)
    lo,hi = 0.,1.
    for iteration in range(1,max_iterations+1):
        beta=(lo+hi)/2
        value=residual(z,k,beta)
        if abs(value) <= 2e-14:
            return RRResult('two_phase',beta,value,True,iteration)
        if value > 0: lo=beta
        else: hi=beta
    return RRResult('not_converged',None,value,False,max_iterations)


def reconstruct(z, k, beta):
    """Record raw sum errors before roundoff-only normalization (<=1e-12)."""
    residual(z,k,beta)
    x=tuple(zi/((1-beta)+beta*ki) for zi,ki in zip(z,k))
    y=tuple(ki*xi for ki,xi in zip(k,x))
    sums=(fsum(x)-1,fsum(y)-1)
    require(max(abs(v) for v in sums) <= 1e-12, 'RR phase normalization inconsistent', 'numerical_domain_error')
    x,y=normalized(x),normalized(y)
    material=tuple((1-beta)*xi+beta*yi-zi for xi,yi,zi in zip(x,y,z))
    require(max(abs(v) for v in material) <= 1e-10, 'RR material reconstruction', 'numerical_domain_error')
    return x,y,sums,material
