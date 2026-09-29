"""Independent PT/caloric oracle, reusing only the qualified benchmark stack."""
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.peng_robinson_caloric import reference as caloric

IDS = ('methane','n_hexane')
CLASSIFICATION = {'L':'single_liquid','V':'single_vapor','VL':'vapor_liquid'}


class TrialFailure(ValueError):
    def __init__(self, stage, message):
        super().__init__(message)
        self.stage = stage


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


class IndependentPT:
    """No production imports, no PH library call, no prior-state warm start."""
    def __init__(self):
        self.flash, self.kw, self.cp = caloric.make_reference()

    def evaluate(self, T, P, z):
        if not finite(T) or not 200. <= T <= 1000.:
            raise TrialFailure('caloric','Temperature outside joint 200–1000 K Cp range')
        try:
            # Explicit stability-first entry point at EVERY trial, including two phases.
            gas,liquids,solids,betas,convergence = self.flash.flash_TP_stability_test(
                T,P,list(z),self.flash.liquid,self.flash.gas)
            if solids or len(liquids)>1:
                raise ValueError('Outside VLE reference scope')
            phase_label = 'VL' if gas is not None and liquids else 'V' if gas is not None else 'L'
            ordered = ([] if gas is None else [('vapor',gas)])+[( 'liquid',p) for p in liquids]
            if len(ordered) != len(betas) or not ordered:
                raise ValueError('Invalid phase amounts')
            fractions = {name:float(fraction) for (name,_),fraction in zip(ordered,betas)}
            beta = fractions.get('vapor',0.)
            if not all(finite(f) and 0 <= f <= 1 for f in betas) or abs(sum(betas)-1)>1e-10:
                raise ValueError('Invalid molar phase fractions')
            material = [sum(fractions[name]*p.zs[i] for name,p in ordered)-zi for i,zi in enumerate(z)]
            if max(abs(v) for v in material)>1e-10:
                raise ValueError('PT material balance failed')
            fugacity = []
            if phase_label=='VL':
                liq = liquids[0]
                fugacity = [math.log(liq.zs[i])+liq.lnphis()[i]-math.log(gas.zs[i])-gas.lnphis()[i] for i,zi in enumerate(z) if zi]
                if max(abs(v) for v in fugacity)>1e-9:
                    raise ValueError('PT fugacity convergence failed')
        except Exception as error:
            raise TrialFailure('pt',str(error)) from error
        phases = {}
        try:
            for name,p in ordered:
                q,Z = list(p.zs),p.Z()
                ideal = caloric.eq.ideal(T,P,q,caloric.CP_DATA)
                pure,a,da,b = caloric.eq.parameters(T,q,caloric.COMPONENTS,caloric.KIJ)
                hr,sr = caloric.eq.departures(T,P,Z,a,da,b)
                direct_h = ideal['h_ig_J_mol']+hr
                direct_s = ideal['s_ig_J_mol_K']+sr
                # Library values are primary; direct equations are audit evidence.
                h,s = p.H(),p.S()
                for actual,expected,quantity in [(p.H_ideal_gas(),ideal['h_ig_J_mol'],'h_ig'),
                    (p.S_ideal_gas(),ideal['s_ig_J_mol_K'],'s_ig'),(p.H_dep(),hr,'h_res'),(p.S_dep(),sr,'s_res'),
                    (h,direct_h,'h_total'),(s,direct_s,'s_total')]:
                    caloric.close(actual,expected,quantity)
                if not all(finite(v) for v in [Z,h,s,*q]) or abs(sum(q)-1)>1e-10:
                    raise ValueError('Nonfinite caloric state or invalid phase composition')
                phases[name] = dict(composition=q,Z=Z,h_ig_J_mol=p.H_ideal_gas(),h_res_J_mol=p.H_dep(),
                    h_J_mol=h,s_ig_J_mol_K=p.S_ideal_gas(),s_res_J_mol_K=p.S_dep(),s_J_mol_K=s,direct_h_J_mol=direct_h,direct_s_J_mol_K=direct_s,
                    library_minus_direct_h_J_mol=h-direct_h,MW_kg_kmol=sum(qi*c['MW_kg_kmol'] for qi,c in zip(q,caloric.COMPONENTS)))
            H = sum(fractions[name]*p['h_J_mol'] for name,p in phases.items())
            H_direct = sum(fractions[name]*p['direct_h_J_mol'] for name,p in phases.items())
            if not finite(H) or not finite(H_direct):
                raise ValueError('Nonfinite equilibrium enthalpy')
        except Exception as error:
            raise TrialFailure('caloric',str(error)) from error
        return dict(T_K=float(T),P_Pa_abs=float(P),z=list(z),classification=CLASSIFICATION[phase_label],beta=beta,
            phases=phases,H_eq_J_mol=H,H_eq_direct_J_mol=H_direct,
            material_residual=material,ln_fugacity_residual=fugacity,
            PT_diagnostics=dict(iterations=int(convergence['iterations']),error=float(convergence['err']),
                                stability_entry='FlashVL.flash_TP_stability_test -> stability_test_Michelsen'))
