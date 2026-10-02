"""M19 variable-composition guarded liquid pump. Composes unchanged PT/caloric, PS and PH providers."""
from dataclasses import replace
from math import fsum, isfinite
from sys import float_info
from .network_models import EquipmentResult, state_from_rates
from .property_packages import property_package
from .pr_flash import SolverSettings
from .pr_ps_flash import PSSpecification
from .pr_ph_flash import PHSpecification
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MODEL = {'id': 'rigorous_isentropic_pump_pr', 'version': '2.0'}
ROUND = 64*float_info.epsilon
IDS = ('methane', 'n_hexane')


from .pump_energy import PumpFailure, require, finite_tree, parameters, accepted, inverse


def inlet_specification(feed, p):
    """M7 owns conversion; 64 eps admits representation noise, never rewrites rates/z/F."""
    try:
        require(set(feed) <= {'component_mass_flow_kg_h', 'mass_flow_kg_h', 'component_mass_fractions',
                             'temperature_K', 'pressure_Pa_abs', 'enthalpy_flow_W', 'properties'},
                'specification', 'independent_caloric_input')
        require(feed.get('enthalpy_flow_W') is None, 'specification', 'independent_caloric_input')
        require(finite_tree(feed), 'specification', 'nonfinite_input')
        require(set(feed['component_mass_flow_kg_h']) == set(IDS), 'specification', 'composition_scope')
        molecular = MolecularCompositionProvider().enrich(feed)
        c = molecular.composition
        F = c.molar_flow_kmol_h/3.6
        require(c.molar_fractions is not None and .01-ROUND <= c.molar_fractions['methane'] <= .55+ROUND,
                'specification', 'composition_scope', 'Qualified methane mole fraction 0.01–0.55; n_hexane balance required')
        require(5-ROUND*5 <= F <= 200+ROUND*200, 'specification', 'flow_scope')
        T, P, P2 = molecular.temperature_K, molecular.pressure_Pa_abs, p['outlet_pressure_Pa_abs']
        require(300 <= T <= 350 and 20e6 <= P <= 25e6 and P <= P2 <= 30e6,
                'specification', 'input_range')
        require(P2 == P or P2-P >= 10000., 'specification', 'positive_rise_below_floor')
        require(abs(fsum(feed['component_mass_flow_kg_h'].values())-feed['mass_flow_kg_h']) <= ROUND*max(1.,feed['mass_flow_kg_h']),
                'specification', 'inconsistent_mass')
        return molecular, F
    except (KeyError, TypeError, ValueError, ArithmeticError) as error:
        if isinstance(error, PumpFailure): raise
        raise PumpFailure('specification', 'invalid_input', str(error)) from error


def _pump(unit, inputs, _evaluate=None):
    require(unit['model'] == MODEL and set(inputs) == {'inlet'}, 'specification', 'unsupported_model_or_ports')
    p = unit['operating_parameters']; bip = parameters(p); feed = inputs['inlet']
    molecular,F = inlet_specification(feed,p)
    state = replace(molecular,provenance=StateSpecificationProvenance(p['property_package'],bip.identifier,'component_mass_flow_kg_h'))
    provider = property_package(p['property_package']); witnesses = {}
    def guarded(c, expected, name):
        out = accepted(c,expected,bip,name)
        w = replace(expected,pressure_Pa_abs=16e6)
        witnesses[name] = accepted(provider.equilibrium_caloric_PT(w,bip,SolverSettings.high_accuracy()),w,bip,name+'_witness',True)
        return out
    inlet_caloric = provider.equilibrium_caloric_PT(state,bip,SolverSettings.high_accuracy())
    inlet = guarded(inlet_caloric,state,'inlet')
    h1,s1 = inlet['H_eq_J_mol'],inlet['S_eq_J_mol_K']; P2=p['outlet_pressure_Pa_abs']; eta=p['isentropic_efficiency']
    identity = P2 == state.pressure_Pa_abs
    psd = phd = dict(status='not_applicable'); ideal = None; reconstructed = None
    budget = ratio = None; hs = h1; target = h1
    if identity:
        outlet = dict(inlet)
    else:
        spec = PSSpecification(P2,s1,state.composition,state.provenance)
        ps = provider.flash_PS(spec,bip); psd = inverse(ps,spec,'PS')
        ideal = guarded(ps.caloric,replace(state,temperature_K=ps.temperature_K,pressure_Pa_abs=P2),'isentropic')
        hs = ideal['H_eq_J_mol']; target = h1+(hs-h1)/eta
        require(isfinite(target) and hs > h1, 'work', 'nonpositive_isentropic_rise')
        spec = PHSpecification(P2,target,state.composition,state.provenance)
        ph = provider.flash_PH(spec,bip); phd = inverse(ph,spec,'PH')
        outlet = guarded(ph.caloric,replace(state,temperature_K=ph.temperature_K,pressure_Pa_abs=P2),'outlet')
    h2,s2=outlet['H_eq_J_mol'],outlet['S_eq_J_mol_K']; dh=h2-h1
    power=F*dh; target_power=F*(target-h1)
    rounding=ROUND*max(1.,abs(F*h1),abs(F*h2),abs(power))
    residual=fsum([F*h2,-F*h1,-power]); power_residual=power-target_power
    if not identity:
        require(dh > 0 and abs(h2-target) <= 1e-6 and abs(ideal['S_eq_J_mol_K']-s1) <= 1e-8,
                'work', 'inverse_residual')
        B=lambda h:1e-6+1e-11*abs(h)
        budget=(B(h1)+B(hs))/eta+B(h1)+B(h2)+370*1e-8/eta+1e-6+ROUND*max(1.,abs(h1),abs(hs),abs(h2))/eta
        ratio=budget/abs(dh)
        require(ratio <= 1e-4, 'work', 'unresolved_work')
        reconstructed=(hs-h1)/dh
        require(abs(reconstructed-eta) <= eta*1e-6/abs(dh)+ROUND, 'work', 'efficiency_residual')
        require(s2-s1 >= -2e-8, 'work', 'entropy_generation')
        if eta == 1:
            require(abs(outlet['temperature_K']-ideal['temperature_K']) <= 1e-7 and abs(s2-s1) <= 2e-8,
                    'work', 'ideal_efficiency')
    require(all(isfinite(v) for v in (F*h1,F*h2,power,target_power,residual,power_residual)) and
            abs(residual) <= rounding and abs(power_residual) <= F*1e-6+rounding, 'closure', 'energy_balance_failure')
    details=dict(property_package=p['property_package'],component_dataset=inlet_caloric.provenance.component_dataset,
        molecular_provider=molecular.provenance.provider,caloric_dataset=inlet_caloric.provenance.caloric_dataset,
        caloric_reference=inlet_caloric.provenance.reference.identifier,bip=p['bip'],F_mol_s=F,
        mode='identity' if identity else 'pressure_rise',guard_status='accepted',
        inlet=inlet,isentropic_outlet=ideal,actual_outlet=outlet,witnesses=witnesses,
        outlet_pressure_Pa_abs=P2,isentropic_efficiency=eta,reconstructed_efficiency=reconstructed,
        H_out_target_J_mol=target,delta_H_is_J_mol=hs-h1,delta_H_actual_J_mol=dh,
        target_fluid_power_W=target_power,fluid_power_W=power,delta_S_actual_J_mol_K=s2-s1,
        work_screening_allowance_J_mol=budget,work_screening_ratio=ratio,
        energy_residual_W=residual,energy_allowance_W=rounding,power_identity_residual_W=power_residual,
        power_identity_allowance_W=F*1e-6+rounding,ps=psd,ph=phd)
    require(finite_tree(details),'closure','nonfinite_payload')
    return EquipmentResult({'outlet':state_from_rates(dict(feed['component_mass_flow_kg_h']),outlet['temperature_K'],P2,F*h2)},0.,power,{'thermodynamics':details})


def pump(unit, inputs, _evaluate=None):
    """Atomic public boundary: malformed inputs never expose a partial outlet."""
    try:
        return _pump(unit, inputs, _evaluate)
    except (KeyError, TypeError, AttributeError, ValueError, ArithmeticError) as error:
        if isinstance(error, PumpFailure): raise
        raise PumpFailure('pump', 'invalid_payload', str(error)) from error
