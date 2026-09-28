"""Binary tangent-plane minimization. Numerical qualification, not a global proof."""
from dataclasses import dataclass
from math import fsum, log, sqrt
from .pr_eos import MODEL, normalized, require


@dataclass(frozen=True)
class StabilityTrial:
    composition: tuple[float, ...]
    root_kind: str
    tpd_RT: float
    iterations: int
    interval_width: float
    converged: bool


@dataclass(frozen=True)
class StabilityResult:
    stable: bool | None
    classification: str | None
    converged: bool
    iterations: int
    minimum_tpd_RT: float
    trials: tuple[StabilityTrial, ...]
    phase_identification_parameter: float | None
    provider: str = MODEL
    algorithm: str = 'binary_tpd_grid_golden@1.0'


def stability(eos, composition, max_iterations=100, reference_potentials=None):
    """Minimize sum(w*(ln(w)+lnphi(w)-d)) on the binary simplex.

    Both liquid-like and vapor-like roots participate through the lower-Gibbs
    envelope. Fixed linear + log-endpoint grid brackets each sampled minimum;
    golden-section refinement has an explicit interval convergence criterion.
    Exact zero endpoints use the mathematical limit w*ln(w)=0, no log floor.
    Optional d evaluates an equilibrium common tangent after flash.
    """
    z = normalized(composition)
    require(isinstance(max_iterations,int) and not isinstance(max_iterations,bool) and max_iterations > 0, 'Invalid stability iteration limit')
    base_state = eos.mixture(z)
    base = eos.lowest_gibbs(base_state)
    active = tuple(i for i,v in enumerate(z) if v > 0)
    d = reference_potentials or tuple(log(v)+lp if v else None for v,lp in zip(z,base.ln_phi))

    def evaluate(w):
        state = eos.mixture(w)
        f = eos.lowest_gibbs(state)
        tpd = fsum(v*(log(v)+lp-di) for v,lp,di in zip(w,f.ln_phi,d) if v)
        kind = ('single_root' if len(state.roots)==1 else
                'liquid_like' if f.Z == state.roots[0] else 'vapor_like')
        return tpd, kind

    if len(active) == 1:
        # The feasible composition simplex is a point; competing roots were
        # compared by Gibbs energy. Coexisting pure roots are not qualified.
        pip = eos.phase_identification(base_state,base.Z)
        trial = StabilityTrial(z,'pure_component',0.,0,0.,True)
        return StabilityResult(True,'single_liquid' if pip > 1 else 'single_vapor',True,0,0.,(trial,),pip)
    require(len(z) == 2, 'Binary stability scope only', 'unsupported_components')
    grid = sorted(set([i/256 for i in range(257)] + [z[0]] +
                      [v for j in range(1,13) for v in (10.**-j,1-10.**-j)]))
    values = [evaluate((w,1-w))[0] for w in grid]
    trials = []
    for w in (0.,z[0],1.):
        val,kind = evaluate((w,1-w))
        trials.append(StabilityTrial((w,1-w),kind,val,0,0.,True))
    ratio = (sqrt(5)-1)/2
    for i in range(1,len(grid)-1):
        if values[i] > values[i-1] or values[i] > values[i+1]:
            continue
        lo,hi = grid[i-1],grid[i+1]
        c,e = hi-ratio*(hi-lo),lo+ratio*(hi-lo)
        fc,fe = evaluate((c,1-c))[0],evaluate((e,1-e))[0]
        converged = False
        for iteration in range(1,max_iterations+1):
            if fc <= fe:
                hi,e,fe = e,c,fc
                c = hi-ratio*(hi-lo); fc = evaluate((c,1-c))[0]
            else:
                lo,c,fc = c,e,fe
                e = lo+ratio*(hi-lo); fe = evaluate((e,1-e))[0]
            if hi-lo <= 1e-12:
                converged = True
                break
        w = c if fc <= fe else e
        val,kind = evaluate((w,1-w))
        trials.append(StabilityTrial((w,1-w),kind,val,iteration,hi-lo,converged))
    minimum = min(t.tpd_RT for t in trials)
    converged = all(t.converged for t in trials)
    stable = minimum >= -1e-9 if converged else None
    pip = eos.phase_identification(base_state,base.Z) if stable and reference_potentials is None else None
    classification = (('single_liquid' if pip > 1 else 'single_vapor') if stable else
                      ('vapor_liquid' if converged else None)) if reference_potentials is None else None
    return StabilityResult(stable,classification,converged,sum(t.iterations for t in trials),minimum,tuple(trials),pip)
