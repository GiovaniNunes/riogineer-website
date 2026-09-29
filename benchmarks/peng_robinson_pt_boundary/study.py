"""Independent boundary/precision experiments. No production imports or equations.

Thermo owns PR fugacity and caloric properties. SciPy owns bracketed RR roots.
This explicit SS experiment measures a log-fugacity stopping policy; it is not
production M8.1 and does not change any existing solver setting.
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmarks.peng_robinson_ph.equilibrium import IndependentPT
from benchmarks.peng_robinson_caloric import reference as caloric
from thermo import CEOSGas, CEOSLiquid
from thermo.flash.flash_utils import stability_iteration_Michelsen
from scipy.optimize import brentq


def wilson(T, P):
    return [math.exp(math.log(c['Pc_Pa_abs']) - math.log(P)
                     + 5.373*(1+c['omega'])*(1-c['Tc_K']/T))
            for c in caloric.COMPONENTS]


def rr_value(z, K, beta):
    return math.fsum(q*(k-1)/(1+beta*(k-1)) for q,k in zip(z,K))


def rr(z, K):
    if len(z) != len(K) or not all(math.isfinite(k) and k > 0 for k in K):
        raise ValueError('Positive finite ordered K required')
    f0, f1 = rr_value(z,K,0.), rr_value(z,K,1.)
    if f0 <= 0:
        return dict(status='liquid_tendency',beta=0.,F0=f0,F1=f1,physical_interior_root=False)
    if f1 >= 0:
        return dict(status='vapor_tendency',beta=1.,F0=f0,F1=f1,physical_interior_root=False)
    beta = brentq(lambda b: rr_value(z,K,b), 0., 1., xtol=1e-16, rtol=1e-15)
    residual = rr_value(z,K,beta)
    assert abs(residual) <= 2e-14
    return dict(status='two_phase',beta=beta,F0=f0,F1=f1,
                physical_interior_root=True,residual=residual)


class Study:
    def __init__(self):
        self.oracle = IndependentPT()

    def phase(self, T, P, q, label):
        cls = CEOSLiquid if label == 'liquid' else CEOSGas
        return cls(caloric.BenchmarkPRMIX, self.oracle.kw,
                   HeatCapacityGases=self.oracle.cp, T=T, P=P, zs=list(q))

    def phase_record(self, p):
        q = list(p.zs)
        ideal = caloric.eq.ideal(p.T,p.P,q,caloric.CP_DATA)
        _,a,da,b = caloric.eq.parameters(p.T,q,caloric.COMPONENTS,caloric.KIJ)
        hr,sr = caloric.eq.departures(p.T,p.P,p.Z(),a,da,b)
        caloric.close(p.H(),ideal['h_ig_J_mol']+hr,'h_total')
        caloric.close(p.S(),ideal['s_ig_J_mol_K']+sr,'s_total')
        return dict(composition=q,Z=p.Z(),phi=p.phis(),ln_phi=p.lnphis(),
                    h_ig_J_mol=p.H_ideal_gas(),h_res_J_mol=p.H_dep(),h_J_mol=p.H(),
                    s_J_mol_K=p.S(),a_mix=a,da_mix_dT=da,b_mix=b)

    def assemble(self, T, P, z, beta, phases):
        data = {label:self.phase_record(p) for label,p in phases}
        if len(data) == 2:
            x,y = data['liquid']['composition'],data['vapor']['composition']
            residual = [math.log(xi)+lp-math.log(yi)-vp for xi,yi,lp,vp in
                        zip(x,y,data['liquid']['ln_phi'],data['vapor']['ln_phi'])]
            K = [yi/xi for xi,yi in zip(x,y)]
        else:
            residual, K = [], None
        material = [sum((beta if label=='vapor' else 1-beta)*p['composition'][i]
                        for label,p in data.items())-zi for i,zi in enumerate(z)]
        H = sum((beta if label=='vapor' else 1-beta)*p['h_J_mol'] for label,p in data.items())
        assert max(abs(v) for v in material) <= 1e-10
        return dict(T_K=T,P_Pa_abs=P,z=list(z),classification='vapor_liquid' if len(data)==2
                    else 'single_'+next(iter(data)),beta=beta,phases=data,final_K=K,
                    log_fugacity_residual=residual,material_reconstruction_residual=material,H_eq_J_mol=H)

    def equilibrium(self, T, P, z):
        # The unchanged independent oracle supplies full stability/PT equilibrium.
        self.oracle.evaluate(T,P,z)
        g, liquids, _, fractions, conv = self.oracle.flash.flash_TP_stability_test(
            T,P,list(z),self.oracle.flash.liquid,self.oracle.flash.gas)
        phases = ([] if g is None else [('vapor',g)]) + [('liquid',p) for p in liquids]
        beta = fractions[0] if g is not None else 0.
        result = self.assemble(T,P,z,beta,phases)
        result['convergence'] = conv
        return result

    def incipient_vapor(self, T, P, z):
        """Bubble-side liquid parent; distinguish nontrivial trial from equilibrium.

        W_i = z_i phi_i(parent) / phi_i(trial), S=sum(W), w=W/S.
        K_i = W_i/z_i = S*w_i/z_i. At stationarity TPD(w)/RT=-ln(S).
        The independent library supplies the stationary trial, not production.
        """
        liquid, gas = self.phase(T,P,z,'liquid'), self.phase(T,P,z,'vapor')
        initial = [q*k for q,k in zip(z,wilson(T,P))]
        total = sum(initial)
        guess = [v/total for v in initial]
        solution = stability_iteration_Michelsen(
            T=T,P=P,zs_trial=list(z),fugacities_trial=liquid.fugacities_lowest_Gibbs(),
            zs_test=guess,test_phase=lambda w:gas.lnphis_at_zs(w,most_stable=True),
            maxiter=1000,xtol=1e-24)
        library_sum, library_K, w, _, _, _, _ = solution
        parent_lnphi = liquid.lnphis_lowest_Gibbs()
        trial_lnphi = gas.lnphis_at_zs(w,most_stable=True)
        K = [math.exp(a-b) for a,b in zip(parent_lnphi,trial_lnphi)]
        W = [q*k for q,k in zip(z,K)]; S = sum(W)
        stationary_error = max(abs(wi-Wi/S) for wi,Wi in zip(w,W))
        tpd = sum(wi*(math.log(wi)+lp-math.log(zi)-base)
                  for wi,zi,lp,base in zip(w,z,trial_lnphi,parent_lnphi))
        assert stationary_error < 1e-11
        assert abs(tpd+math.log(S)) < 1e-11
        return dict(parent='liquid',trial='incipient_vapor',composition=w,
                    unnormalized_W=W,S=S,tpd_RT=tpd,stationarity_error=stationary_error,
                    seed_K=K,seed_RR=rr(z,K),normalized_only_K=[wi/zi for wi,zi in zip(w,z)],
                    normalized_only_F0=rr_value(z,[wi/zi for wi,zi in zip(w,z)],0.),
                    library_sum=library_sum,library_K=library_K,
                    interpretation='Stationary vapor trial; negative TPD establishes instability, not final phase amounts')

    def successive_substitution(self, T, P, z, tolerance, initial_K=None):
        """Controlled independent precision/restart experiment, no phase locking API.

        Used only after independent equilibrium establishes the chosen VLE state.
        It has no stability or single-phase fallback and fails without a RR root.
        """
        K = list(initial_K) if initial_K is not None else wilson(T,P)
        history = []
        for iteration in range(1,201):
            split = rr(z,K)
            if not split['physical_interior_root']:
                raise ValueError('Independent SS initial/updated K has no physical RR root')
            beta = split['beta']
            x = [zi/(1+beta*(ki-1)) for zi,ki in zip(z,K)]
            y = [ki*xi for ki,xi in zip(K,x)]
            assert abs(sum(x)-1) < 1e-12 and abs(sum(y)-1) < 1e-12
            x = [v/sum(x) for v in x]; y = [v/sum(y) for v in y]
            liquid, vapor = self.phase(T,P,x,'liquid'), self.phase(T,P,y,'vapor')
            lp,vp = liquid.lnphis(),vapor.lnphis()
            residual = [math.log(xi)+a-math.log(yi)-b for xi,yi,a,b in zip(x,y,lp,vp)]
            maximum = max(abs(v) for v in residual)
            history.append(dict(iteration=iteration,beta=beta,K=K,max_log_fugacity_residual=maximum))
            if maximum <= tolerance:
                result = self.assemble(T,P,z,beta,[('liquid',liquid),('vapor',vapor)])
                result.update(iterations=iteration,requested_log_fugacity_tolerance=tolerance,
                              max_log_fugacity_residual=maximum,history=history)
                return result
            K = [math.exp(a-b) for a,b in zip(lp,vp)]
        raise ValueError('Independent SS iteration limit reached')
