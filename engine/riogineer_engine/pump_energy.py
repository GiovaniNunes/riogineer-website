"""M18 guarded liquid pump. Composes unchanged PT/caloric, PS and PH providers."""
from dataclasses import asdict, replace
from math import fsum, isfinite
import json
from sys import float_info
from .compressor_energy import caloric_state, parameters as compressor_parameters
from .network_models import EquipmentResult, state_from_rates
from .property_packages import property_package
from .pr_flash import SolverSettings
from .pr_ps_flash import PSSpecification, PSSettings
from .pr_ph_flash import PHSpecification, PHSettings
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MODEL = {'id': 'rigorous_isentropic_pump_pr', 'version': '1.0'}
ROUND = 64*float_info.epsilon
IDS = ('methane', 'n_hexane')


class PumpFailure(ValueError):
    def __init__(self, stage, status, diagnostics=''):
        self.stage, self.status, self.diagnostics = stage, status, diagnostics
        super().__init__(f'{stage}: {status}; {diagnostics}')


def require(ok, stage, status, message=''):
    if not ok: raise PumpFailure(stage, status, message)


def finite_tree(v):
    if isinstance(v, float): return isfinite(v)
    if isinstance(v, dict): return all(finite_tree(x) for x in v.values())
    if isinstance(v, (tuple, list)): return all(finite_tree(x) for x in v)
    return True


def parameters(p):
    try:
        bip = compressor_parameters(p)
        require(.6 <= p['isentropic_efficiency'] <= 1 and 20e6 <= p['outlet_pressure_Pa_abs'] <= 30e6,
                'specification', 'input_range')
        return bip
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, PumpFailure): raise
        raise PumpFailure('specification', 'invalid_parameters', str(error)) from error


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
        require(c.molar_fractions is not None and all(abs(c.molar_fractions[i]-.5) <= ROUND for i in IDS),
                'specification', 'composition_scope', 'Fixed equimolar methane/n_hexane required')
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


def accepted(c, expected, bip, stage, witness=False):
    """Validate payload association as well as successful stable-liquid status."""
    try:
        require(c.status.startswith('success') and c.aggregate is not None and c.equilibrium is not None,
                stage, 'property_failure', c.message)
        pt = c.equilibrium; s = pt.overall_state; d = pt.diagnostics.stability
        require(pt.status == 'success_single_phase' and pt.classification == 'single_liquid' and pt.beta == 0,
                stage, 'non_liquid')
        require(pt.provenance.settings == SolverSettings.high_accuracy() and pt.provenance.bip == bip,
                stage, 'unqualified_PT_controls')
        require(d is not None and d.stable is True and d.converged is True and
                d.phase_identification_parameter > 1, stage, 'stability_failure')
        require(s.temperature_K == expected.temperature_K and s.pressure_Pa_abs == expected.pressure_Pa_abs and
                s.composition == expected.composition and 300 <= s.temperature_K <= 370 and
                (s.pressure_Pa_abs == 16e6 if witness else 20e6 <= s.pressure_Pa_abs <= 30e6),
                stage, 'state_specification_mismatch')
        z = tuple(expected.composition.molar_fractions[i] for i in IDS)
        require(s.composition.component_ids == IDS and len(pt.evaluated_molar_composition) == 2 and
                all(abs(a-b) <= ROUND for a,b in zip(pt.evaluated_molar_composition,z)), stage, 'composition_mismatch')
        require(len(pt.phases) == len(c.phases) == 1, stage, 'phase_payload_mismatch')
        phase, cp = pt.phases[0], c.phases[0]
        require(phase.identifier == cp.phase_identifier == 'liquid' and phase.fraction == 1 and phase.Z > 0 and
                len(phase.composition) == 2 and all(abs(a-b) <= ROUND for a,b in zip(phase.composition,z)) and
                cp.eos.composition == phase.composition and phase.Z in cp.eos.roots and
                c.aggregate.h_J_mol == cp.h_total_J_mol and c.aggregate.s_J_mol_K == cp.s_total_J_mol_K,
                stage, 'phase_payload_mismatch')
        out = caloric_state(c)
        out.update(pt_profile='high_accuracy', stability=json.loads(json.dumps(asdict(d),allow_nan=False)))
        require(finite_tree(out) and finite_tree(asdict(pt.diagnostics)) and
                finite_tree(asdict(phase)) and finite_tree(asdict(cp)) and finite_tree(asdict(c.aggregate)), stage, 'nonfinite_payload')
        return out
    except (KeyError, TypeError, AttributeError, ValueError, ArithmeticError) as error:
        if isinstance(error, PumpFailure): raise
        raise PumpFailure(stage, 'invalid_payload', str(error)) from error


def inverse(result, specification, capability):
    stage = capability; is_ps = capability == 'PS'
    try:
        d = result.diagnostics
        require(result.status == 'success' and result.caloric is not None, stage, result.status, d.reason)
        require(result.specification == specification and d.settings == (PSSettings() if is_ps else PHSettings()) and
                d.pt_settings == SolverSettings.high_accuracy(), stage, 'inverse_controls')
        scans = [t for t in d.trials if t.stage == 'scan']; finals = [t for t in d.trials if t.stage == 'final']
        failures = [t for t in d.trials if t.status != 'success']
        n = 64 if is_ps else 128
        require(len(scans) == n and [t.temperature_K for t in scans] == [200.+300.*j/(n-1) for j in range(n)] and
                len(d.brackets_K) == 1 and d.selected_bracket_K == d.brackets_K[0] and d.final_bracket_K is not None and
                len(finals) == 1 and finals[0] == d.trials[-1] and finals[0].status == 'success', stage, 'inverse_diagnostics')
        lo,hi = d.selected_bracket_K; flo,fhi = d.final_bracket_K
        require(200 <= lo <= flo <= fhi <= hi <= 500 and flo <= result.temperature_K <= fhi and
                finals[0].temperature_K == result.temperature_K == result.caloric.equilibrium.overall_state.temperature_K,
                stage, 'inverse_payload_mismatch')
        require(not failures if is_ps else all(t.stage == 'scan' and t.status == 'pt_evaluation_failure' and
                not lo <= t.temperature_K <= hi for t in failures), stage, 'inverse_property_hole')
        actual = result.caloric.aggregate.s_J_mol_K if is_ps else result.caloric.aggregate.h_J_mol
        target = specification.entropy_J_mol_K if is_ps else specification.enthalpy_J_mol
        residual = result.entropy_residual_J_mol_K if is_ps else result.enthalpy_residual_J_mol
        final_residual = finals[0].residual_J_mol_K if is_ps else finals[0].residual_J_mol
        final_value = finals[0].entropy_J_mol_K if is_ps else finals[0].enthalpy_J_mol
        require(finite_tree(asdict(d)) and residual == final_residual == actual-target and final_value == actual,
                stage, 'fresh_residual_mismatch')
        require(isfinite(residual) and abs(residual) <= (1e-8 if is_ps else 1e-6), stage, 'inverse_residual')
        return dict(status='success', capability=capability, pt_profile='high_accuracy', candidate_count=1,
            scan_count=n, fresh_final_count=1, temperature_bounds_K=[200.,500.], bracket_K=list(d.selected_bracket_K),
            final_bracket_K=list(d.final_bracket_K), root_iterations=d.root_iterations,
            evaluation_count=len(d.trials), residual=residual, failure_count=len(failures))
    except (KeyError, TypeError, AttributeError, ValueError, ArithmeticError) as error:
        if isinstance(error, PumpFailure): raise
        raise PumpFailure(stage, 'invalid_inverse_payload', str(error)) from error


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
