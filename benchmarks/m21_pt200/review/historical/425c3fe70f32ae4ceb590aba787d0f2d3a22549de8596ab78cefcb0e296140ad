"""Vapor-service adiabatic compressor: compose qualified PT/M10, PS/M13, PH/M11."""
from dataclasses import replace
from math import fsum, isfinite
from sys import float_info
from .network_models import EquipmentResult, state_from_rates
from .heater_cooler_energy import state_details
from .property_packages import property_package
from .pr_eos import BinaryInteractions
from .pr_flash import SolverSettings
from .pr_ps_flash import PSSpecification
from .pr_ph_flash import PHSpecification
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MODEL = {'id': 'rigorous_isentropic_pr', 'version': '1.0'}


class CompressorFailure(ValueError):
    def __init__(self, stage, status, diagnostics=''):
        self.stage, self.status, self.diagnostics = stage, status, diagnostics
        super().__init__(f'peng_robinson@1.0: {stage}: {status}; {diagnostics}')


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and isfinite(v)


def require(condition, stage, status, message):
    if not condition:
        raise CompressorFailure(stage, status, message)


def parameters(p):
    require(set(p) == {'outlet_pressure_Pa_abs', 'isentropic_efficiency', 'property_package', 'bip'},
            'specification', 'invalid_specification', 'Exactly the rigorous model fields are required')
    require(p['property_package'] == 'peng_robinson@1.0', 'specification', 'unsupported_provider', 'Explicit PR provider required')
    require(finite(p['outlet_pressure_Pa_abs']) and p['outlet_pressure_Pa_abs'] > 0,
            'specification', 'invalid_pressure', 'Finite positive outlet pressure required')
    require(finite(p['isentropic_efficiency']) and 0 < p['isentropic_efficiency'] <= 1,
            'specification', 'invalid_efficiency', '0 < eta <= 1 required')
    try:
        bip = BinaryInteractions(**p['bip'])
    except (TypeError, ValueError) as error:
        raise CompressorFailure('specification', 'unsupported_bip', str(error)) from error
    require(bip.component_ids == ('methane', 'n_hexane') and bip.temperature_dependence == 'constant' and
            bip.model == 'peng_robinson@1.0' and all(v == 0 for row in bip.values for v in row),
            'specification', 'unsupported_bip', 'Qualified explicit constant zero methane/n_hexane BIP required')
    return bip


def accepted(c, stage):
    require(c.status.startswith('success') and c.aggregate is not None and c.equilibrium is not None,
            stage, c.status, c.message)
    require(c.equilibrium.classification == 'single_vapor', stage, 'compressor_service_scope',
            'Single-vapor compressor service only; no global thermodynamic restriction')
    require(200 <= c.equilibrium.overall_state.temperature_K <= 500 and
            all(finite(v) for v in (c.aggregate.h_J_mol, c.aggregate.s_J_mol_K)),
            stage, 'compressor_state_invalid', 'Finite caloric state inside qualified 200–500 K domain required')
    return c


def caloric_state(c):
    out = state_details(c)
    out['S_eq_J_mol_K'] = c.aggregate.s_J_mol_K
    for p in c.phases:
        out['phases'][p.phase_identifier].update(s_ig_J_mol_K=p.s_ig_J_mol_K,
            s_res_J_mol_K=p.s_res_J_mol_K, s_J_mol_K=p.s_total_J_mol_K)
    return out


def inverse_details(result, capability):
    d = result.diagnostics
    require(d.pt_settings == SolverSettings.high_accuracy() and len(d.brackets_K) == 1 and
            d.selected_bracket_K is not None and d.final_bracket_K is not None and
            bool(d.trials) and d.trials[-1].stage == 'final',
            capability, 'invalid_nested_diagnostics', 'One candidate, high_accuracy and fresh final evaluation required')
    out = dict(status=result.status, capability=capability, pt_profile='high_accuracy',
               candidate_count=len(d.brackets_K), bracket_K=list(d.selected_bracket_K),
               final_bracket_K=list(d.final_bracket_K), root_iterations=d.root_iterations,
               evaluation_count=len(d.trials))
    if capability == 'flash_PS':out['entropy_residual_J_mol_K'] = result.entropy_residual_J_mol_K
    else:out['enthalpy_residual_J_mol'] = result.enthalpy_residual_J_mol
    return out


def compressor(unit, inputs, _evaluate=None):
    require(unit['model'] == MODEL, 'specification', 'unsupported_model', 'Explicit rigorous model required')
    require(set(inputs) == {'inlet'}, 'specification', 'invalid_input', 'Exactly one inlet required')
    p = unit['operating_parameters']; bip = parameters(p); feed = inputs['inlet']
    rates = feed['component_mass_flow_kg_h']; P1 = feed['pressure_Pa_abs']; T1 = feed['temperature_K']
    P2 = p['outlet_pressure_Pa_abs']; eta = p['isentropic_efficiency']
    require(set(rates) == {'methane', 'n_hexane'}, 'specification', 'unsupported_component', 'Only methane/n_hexane; pure endpoints retain zero-flow component')
    require(all(finite(v) and v >= 0 for v in rates.values()) and finite(feed['mass_flow_kg_h']) and feed['mass_flow_kg_h'] > 0,
            'specification', 'invalid_flow', 'Positive total and nonnegative finite component mass flows required')
    require(abs(sum(rates.values())-feed['mass_flow_kg_h']) <= 1e-12*max(1.,feed['mass_flow_kg_h']),
            'specification', 'invalid_composition', 'Component flows must reconstruct total; no normalization of inconsistent input')
    require(finite(P1) and 0 < P1 < P2, 'specification', 'invalid_pressure', 'P2 > P1 > 0 required')
    require(finite(T1) and 200 <= T1 <= 500, 'specification', 'temperature_domain_invalid', 'Qualified 200–500 K domain required')
    try:
        molecular = MolecularCompositionProvider().enrich(feed)
    except (ValueError, ArithmeticError) as error:
        raise CompressorFailure('specification', 'invalid_composition', str(error)) from error
    F = molecular.composition.molar_flow_kmol_h*1000./3600.
    require(finite(F) and F > 0, 'specification', 'invalid_flow', 'Finite positive molar flow required')
    state = replace(molecular, provenance=StateSpecificationProvenance(p['property_package'], bip.identifier, 'component_mass_flow_kg_h'))
    provider = property_package(p['property_package'])
    inlet = accepted(provider.equilibrium_caloric_PT(state, bip, SolverSettings.high_accuracy()), 'inlet_PT')
    H1, S1 = inlet.aggregate.h_J_mol, inlet.aggregate.s_J_mol_K
    ps = provider.flash_PS(PSSpecification(P2, S1, state.composition, state.provenance), bip)
    if ps.status != 'success' or ps.caloric is None:
        raise CompressorFailure('isentropic_PS', ps.status, ps.diagnostics)
    isentropic = accepted(ps.caloric, 'isentropic_PS')
    Hs = isentropic.aggregate.h_J_mol
    ps_details = inverse_details(ps, 'flash_PS')
    require(abs(isentropic.aggregate.s_J_mol_K-S1) <= 1e-8, 'isentropic_PS', 'entropy_residual_failed', 'Fresh PS entropy equality required')
    dhs = Hs-H1; target = H1+dhs/eta
    require(finite(target) and dhs > 0 and target >= Hs-1e-6, 'isentropic_PS', 'compressor_state_invalid', 'Positive compression enthalpy rise required')
    ph = provider.flash_PH(PHSpecification(P2, target, state.composition, state.provenance), bip)
    if ph.status != 'success' or ph.caloric is None:
        raise CompressorFailure('actual_PH', ph.status, ph.diagnostics)
    outlet = accepted(ph.caloric, 'actual_PH'); ph_details = inverse_details(ph, 'flash_PH')
    H2, S2 = outlet.aggregate.h_J_mol, outlet.aggregate.s_J_mol_K
    dh = H2-H1
    require(abs(H2-target) <= 1e-6 and dh > 0 and H2 >= Hs-1e-6, 'closure', 'enthalpy_residual_failed', 'Recovered PH enthalpy and compressor ordering required')
    power = F*dh; ideal_power = F*dhs
    require(finite(power) and power > 0 and finite(ideal_power),
            'closure', 'compressor_state_invalid', 'Finite positive power required before efficiency division')
    reconstructed = dhs/dh; eta_power = ideal_power/power
    arithmetic = 64*float_info.epsilon*max(1.,abs(power),abs(F*H1),abs(F*H2))
    eta_allowance = eta*1e-6/abs(dh)+64*float_info.epsilon
    residual = fsum([power,F*H1,-F*H2]); power_residual = power-ideal_power/eta
    require(all(finite(v) for v in (power,ideal_power,residual,reconstructed,eta_power,power_residual)) and power > 0,
            'closure', 'compressor_state_invalid', 'Finite positive fluid power required')
    require(abs(reconstructed-eta) <= eta_allowance and abs(eta_power-eta) <= eta_allowance,
            'closure', 'efficiency_reconstruction_failed', 'Recovered state must reconstruct specified efficiency')
    require(abs(residual) <= arithmetic and abs(power_residual) <= F*1e-6+arithmetic,
            'closure', 'energy_balance_failure', 'Independent energy/power closure required')
    require(S2-S1 >= -2e-8 and outlet.equilibrium.overall_state.temperature_K >= isentropic.equilibrium.overall_state.temperature_K-1e-7,
            'closure', 'compressor_state_invalid', 'Vapor entropy and temperature ordering failed')
    if eta == 1:
        require(abs(S2-S1) <= 2e-8 and abs(outlet.equilibrium.overall_state.temperature_K-isentropic.equilibrium.overall_state.temperature_K) <= 1e-7,
                'closure', 'isentropic_limit_failed', 'eta=1 must reproduce isentropic state')
    states = [caloric_state(c) for c in (inlet,isentropic,outlet)]
    require(all(s['z'] == states[0]['z'] for s in states) and states[1]['pressure_Pa_abs'] == states[2]['pressure_Pa_abs'] == P2,
            'closure', 'material_balance_failure', 'Composition and pressure specifications must be preserved')
    stream = state_from_rates(dict(rates),states[2]['temperature_K'],P2,F*H2)
    projected = MolecularCompositionProvider().enrich(stream).composition
    require(projected.molar_flow_kmol_h == molecular.composition.molar_flow_kmol_h and projected.molar_fractions == molecular.composition.molar_fractions,
            'closure', 'material_balance_failure', 'Molar flow and overall composition must be conserved')
    details = dict(property_package=inlet.provenance.provider,component_dataset=inlet.provenance.component_dataset,
        molecular_provider=molecular.provenance.provider,caloric_dataset=inlet.provenance.caloric_dataset,
        caloric_reference=inlet.provenance.reference.identifier,bip=p['bip'],F_mol_s=F,
        inlet=states[0],isentropic_outlet=states[1],actual_outlet=states[2],pressure_ratio=P2/P1,
        isentropic_efficiency=eta,reconstructed_efficiency=reconstructed,eta_power=eta_power,efficiency_allowance=eta_allowance,
        H_out_target_J_mol=target,delta_H_is_J_mol=dhs,delta_H_actual_J_mol=dh,
        isentropic_fluid_power_W=ideal_power,fluid_power_W=power,delta_S_actual_J_mol_K=S2-S1,
        energy_residual_W=residual,energy_allowance_W=arithmetic,power_identity_residual_W=power_residual,
        power_identity_allowance_W=F*1e-6+arithmetic,ps=ps_details,ph=ph_details)
    return EquipmentResult({'outlet':stream},0.,power,{'thermodynamics':details})
