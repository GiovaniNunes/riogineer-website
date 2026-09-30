"""Wall-separated terminal-state exchanger using qualified PT/M10 and PH/M11."""
from dataclasses import replace
from math import fsum
from sys import float_info
from .network_models import EquipmentResult, state_from_rates
from .compressor_energy import caloric_state, inverse_details, CompressorFailure
from .heater_cooler_energy import finite
from .property_packages import property_package
from .pr_eos import BinaryInteractions
from .pr_flash import SolverSettings
from .pr_ph_flash import PHSpecification
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MODEL = {'id': 'rigorous_two_stream_pr', 'version': '1.0'}


class ExchangerFailure(ValueError):
    def __init__(self, stage, status, message=''):
        self.stage, self.status = stage, status
        super().__init__(f'peng_robinson@1.0: {stage}: {status}; {message}')


def require(condition, stage, status, message):
    if not condition:
        raise ExchangerFailure(stage, status, message)


def parameters(p):
    mode = p.get('mode')
    side = {'specified_hot_outlet_temperature': 'hot', 'specified_cold_outlet_temperature': 'cold'}.get(mode)
    common = {'mode', 'property_package', 'bip', 'hot_outlet_pressure_Pa_abs', 'cold_outlet_pressure_Pa_abs'}
    require(side is not None and set(p) == common | {str(side)+'_outlet_temperature_K'},
            'specification', 'invalid_specification', 'Exactly one explicit outlet temperature mode required')
    require(p['property_package'] == 'peng_robinson@1.0', 'specification', 'unsupported_provider', 'Qualified PR provider required')
    try:
        bip = BinaryInteractions(**p['bip'])
    except (TypeError, ValueError) as error:
        raise ExchangerFailure('specification', 'unsupported_bip', str(error)) from error
    require(bip.component_ids == ('methane', 'n_hexane') and bip.model == 'peng_robinson@1.0' and
            bip.temperature_dependence == 'constant' and all(v == 0 for row in bip.values for v in row),
            'specification', 'unsupported_bip', 'Explicit constant zero methane/n_hexane BIP required')
    return side, bip


def accepted(c, stage):
    require(c.status.startswith('success') and c.aggregate is not None and c.equilibrium is not None,
            stage, c.status, c.message)
    require(c.equilibrium.provenance.settings == SolverSettings.high_accuracy(), stage,
            'pt_evaluation_failure', 'Qualified high_accuracy PT required')
    require(200 <= c.equilibrium.overall_state.temperature_K <= 500 and
            all(finite(v) for v in (c.aggregate.h_J_mol, c.aggregate.s_J_mol_K)),
            stage, 'final_acceptance_failed', 'Finite state inside 200–500 K required')
    return c


def exchanger(unit, inputs):
    require(unit.get('model') == MODEL, 'specification', 'unsupported_model', 'Explicit rigorous exchanger identity required')
    require(set(inputs) == {'hot_in', 'cold_in'}, 'specification', 'invalid_input', 'Both current inlet streams required')
    p = unit['operating_parameters']
    specified, bip = parameters(p)
    recovered = 'cold' if specified == 'hot' else 'hot'
    molecular, flows = {}, {}
    for side in ('hot', 'cold'):
        feed = inputs[side+'_in']; stage = side+'_input'
        rates = feed['component_mass_flow_kg_h']
        require(set(rates) == {'methane', 'n_hexane'}, stage, 'unsupported_component', 'Only the qualified binary basis, including pure endpoints')
        require(finite(feed['mass_flow_kg_h']) and feed['mass_flow_kg_h'] > 0,
                stage, 'invalid_flow', 'Finite positive total flow required')
        require(all(finite(v) and v >= 0 for v in rates.values()) and
                abs(sum(rates.values())-feed['mass_flow_kg_h']) <= 1e-12*max(1., feed['mass_flow_kg_h']),
                stage, 'invalid_composition', 'Finite nonnegative rates must reconstruct total without normalization')
        fractions = feed.get('component_mass_fractions')
        require(isinstance(fractions, dict) and set(fractions) == set(rates) and
                all(finite(fractions[k]) and abs(fractions[k]-rates[k]/feed['mass_flow_kg_h']) <= 1e-12 for k in rates),
                stage, 'invalid_composition', 'Composition must agree with authoritative component flows')
        pin, pout = feed['pressure_Pa_abs'], p[side+'_outlet_pressure_Pa_abs']
        require(all(finite(v) and v > 0 for v in (pin, pout)) and pout <= pin,
                stage, 'invalid_pressure', '0 < outlet pressure <= inlet pressure required')
        require(finite(feed['temperature_K']) and 200 <= feed['temperature_K'] <= 500,
                stage, 'temperature_domain_invalid', 'Qualified 200–500 K inlet domain')
        try:
            state = MolecularCompositionProvider().enrich(feed)
        except (ValueError, ArithmeticError) as error:
            raise ExchangerFailure(stage, 'invalid_composition', str(error)) from error
        flows[side] = state.composition.molar_flow_kmol_h*1000./3600.
        require(finite(flows[side]) and flows[side] > 0, stage, 'invalid_flow', 'Finite positive molar flow required')
        molecular[side] = replace(state, provenance=StateSpecificationProvenance(p['property_package'], bip.identifier, 'component_mass_flow_kg_h'))
    temperature = p[specified+'_outlet_temperature_K']
    require(finite(temperature) and 200 <= temperature <= 500, 'specified_'+specified+'_outlet_PT',
            'temperature_domain_invalid', 'Qualified specified outlet domain is 200–500 K')
    require(molecular['hot'].temperature_K > molecular['cold'].temperature_K, 'service_scope',
            'temperature_direction', 'Declared hot inlet must exceed cold inlet')
    provider = property_package(p['property_package']); states = {}
    for side in ('hot', 'cold'):
        states[side+'_inlet'] = accepted(provider.equilibrium_caloric_PT(molecular[side], bip, SolverSettings.high_accuracy()), side+'_inlet_PT')
    outlet_spec = replace(molecular[specified], temperature_K=temperature, pressure_Pa_abs=p[specified+'_outlet_pressure_Pa_abs'])
    states[specified+'_outlet'] = accepted(provider.equilibrium_caloric_PT(outlet_spec, bip, SolverSettings.high_accuracy()), 'specified_'+specified+'_outlet_PT')
    def enthalpy(side, end):
        return states[side+'_'+end].aggregate.h_J_mol
    specified_duty = flows[specified]*(enthalpy(specified, 'outlet')-enthalpy(specified, 'inlet'))
    target = enthalpy(recovered, 'inlet')-specified_duty/flows[recovered]
    stage = 'recovered_'+recovered+'_outlet_PH'
    require(finite(target), stage, 'invalid_enthalpy_target', 'Finite target required')
    inverse = provider.flash_PH(PHSpecification(p[recovered+'_outlet_pressure_Pa_abs'], target,
        molecular[recovered].composition, molecular[recovered].provenance), bip)
    if inverse.status != 'success' or inverse.caloric is None:
        raise ExchangerFailure(stage, inverse.status, inverse.diagnostics)
    states[recovered+'_outlet'] = accepted(inverse.caloric, stage)
    try:
        ph = inverse_details(inverse, 'flash_PH')
    except CompressorFailure as error:
        raise ExchangerFailure(stage, 'final_acceptance_failed', str(error)) from error
    residual_h = enthalpy(recovered, 'outlet')-target
    require(finite(residual_h) and abs(residual_h) <= 1e-6, stage, 'final_acceptance_failed', 'Fresh final enthalpy residual failed')
    ph['enthalpy_residual_J_mol'] = residual_h
    duties = {side: flows[side]*(enthalpy(side, 'outlet')-enthalpy(side, 'inlet')) for side in ('hot','cold')}
    residual = fsum(duties.values())
    arithmetic = 64*float_info.epsilon*max(1., *map(abs, duties.values()),
        *(abs(flows[side]*enthalpy(side,end)) for side in ('hot','cold') for end in ('inlet','outlet')))
    allowance = flows[recovered]*1e-6+arithmetic
    require(all(finite(v) for v in (*duties.values(), residual, allowance)) and abs(residual) <= allowance,
            'energy_balance', 'energy_balance_failed', 'Fresh accepted states must close energy')
    require(duties['hot'] <= allowance and duties['cold'] >= -allowance,
            'service_scope', 'heat_direction', 'Declared hot-to-cold transfer required')
    require(all(c.equilibrium.classification in ('single_liquid', 'single_vapor') for c in states.values()),
            'service_scope', 'phase_service_scope', 'Single-phase endpoints only; phase studies excluded')
    rendered = {name: caloric_state(c) for name,c in states.items()}
    thi,tho,tci,tco = [rendered[k]['temperature_K'] for k in ('hot_inlet','hot_outlet','cold_inlet','cold_outlet')]
    require(thi > tco and tho > tci and tho >= tco, 'service_scope', 'terminal_temperature_crossing',
            'Require Thi > Tco, Tho > Tci, Tho >= Tco; no minimum approach or sizing claim')
    outputs = {}
    for side in ('hot','cold'):
        si,so = rendered[side+'_inlet'],rendered[side+'_outlet']
        require(si['z'] == so['z'] and so['pressure_Pa_abs'] == p[side+'_outlet_pressure_Pa_abs'],
                side+'_material', 'material_balance_failed', 'Composition and specified pressure must be preserved')
        outputs[side+'_out'] = state_from_rates(dict(inputs[side+'_in']['component_mass_flow_kg_h']),so['temperature_K'],so['pressure_Pa_abs'],flows[side]*so['H_eq_J_mol'])
        projected = MolecularCompositionProvider().enrich(outputs[side+'_out']).composition
        require(projected == molecular[side].composition, side+'_material', 'material_balance_failed', 'M7 material projection must remain identical')
    provenance = states['hot_inlet'].provenance
    details = dict(property_package=provenance.provider,component_dataset=provenance.component_dataset,
        molecular_provider='molecular_composition@1.0',caloric_dataset=provenance.caloric_dataset,
        caloric_reference=provenance.reference.identifier,bip=p['bip'],specification_mode=p['mode'],
        hot_molar_flow_mol_s=flows['hot'],cold_molar_flow_mol_s=flows['cold'],**rendered,
        Q_hot_W=duties['hot'],Q_cold_W=duties['cold'],Q_exchanged_W=max(0.,duties['cold']),
        energy_residual_W=residual,energy_allowance_W=allowance,
        recovered_outlet_target_enthalpy_J_mol=target,ph=ph)
    return EquipmentResult(outputs, 0., 0., {'thermodynamics': details})
