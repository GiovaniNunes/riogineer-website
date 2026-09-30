"""One-stream equilibrium energy adapter; all thermodynamics belongs to providers."""
from dataclasses import replace
from math import isfinite
from sys import float_info
from .network_models import EquipmentResult, state_from_rates
from .property_packages import property_package
from .pr_eos import BinaryInteractions
from .pr_flash import SolverSettings
from .pr_ph_flash import PHSpecification
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MODEL = {'id': 'equilibrium_energy_balance_pr', 'version': '1.0'}


class ThermalFailure(ValueError):
    def __init__(self, stage, status, diagnostics=''):
        self.stage, self.status, self.diagnostics = stage, status, diagnostics
        super().__init__(f'peng_robinson@1.0: {stage}: {status}; {diagnostics}')


def finite(v):
    return isinstance(v, (float, int)) and not isinstance(v, bool) and isfinite(v)


def check(condition, status, message):
    if not condition:
        raise ThermalFailure('specification', status, message)


def parameters(p):
    check(p.get('property_package') == 'peng_robinson@1.0', 'unsupported_provider', 'Explicit PR provider required')
    common = {'mode', 'property_package', 'bip', 'outlet_pressure_Pa_abs'}
    mode = p.get('mode')
    field = {'specified_outlet_temperature': 'outlet_temperature_K', 'specified_heat_duty': 'duty_W'}.get(mode)
    check(field is not None and set(p) == common | {field}, 'invalid_specification', 'Exactly one T_out or Q must control the selected mode')
    check(finite(p['outlet_pressure_Pa_abs']) and p['outlet_pressure_Pa_abs'] > 0, 'invalid_pressure', 'Positive outlet absolute pressure required')
    if field == 'duty_W':
        check(finite(p[field]), 'invalid_duty', 'Finite signed duty required')
    else:
        check(finite(p[field]) and 200 <= p[field] <= 500, 'temperature_domain_invalid', 'Qualified temperature interval is 200–500 K')
    try:
        bip = BinaryInteractions(**p['bip'])
    except (TypeError, ValueError) as error:
        raise ThermalFailure('specification', 'unsupported_bip', str(error)) from error
    check(bip.component_ids == ('methane', 'n_hexane') and
          all(v == 0 for row in bip.values for v in row) and bip.temperature_dependence == 'constant',
          'unsupported_bip', 'Explicit constant zero methane/n_hexane BIP required')
    return bip


def state_details(caloric):
    pt = caloric.equilibrium
    ids = pt.overall_state.composition.component_ids
    cp = {p.phase_identifier: p for p in caloric.phases}
    phases = {p.identifier: dict(composition=dict(zip(ids, p.composition)), Z=p.Z,
        h_ig_J_mol=cp[p.identifier].h_ig_J_mol, h_res_J_mol=cp[p.identifier].h_res_J_mol,
        h_J_mol=cp[p.identifier].h_total_J_mol) for p in pt.phases}
    fractions = pt.overall_state.composition.molar_fractions
    z = dict(fractions) if hasattr(fractions, 'keys') else dict(zip(ids, fractions))
    return dict(temperature_K=pt.overall_state.temperature_K, pressure_Pa_abs=pt.overall_state.pressure_Pa_abs,
        z=z, classification=pt.classification, beta=pt.beta, H_eq_J_mol=caloric.aggregate.h_J_mol,
        phases=phases, pt_status=pt.status,
        max_log_fugacity_residual=max(map(abs, pt.diagnostics.fugacity_residual or ()), default=0.))


def accepted(caloric, stage):
    if not caloric.status.startswith('success') or caloric.aggregate is None or caloric.equilibrium is None:
        raise ThermalFailure(stage, caloric.status, caloric.message)
    return caloric


def heater(unit, inputs, _evaluate=None):
    check(set(inputs) == {'inlet'}, 'invalid_input', 'Exactly one inlet required')
    p = unit['operating_parameters']
    feed = inputs['inlet']
    rates = feed['component_mass_flow_kg_h']
    check(set(rates) == {'methane', 'n_hexane'}, 'unsupported_component', 'Only methane/n_hexane caloric scope; water unsupported')
    bip = parameters(p)
    check(all(finite(v) and v >= 0 for v in rates.values()) and finite(feed['mass_flow_kg_h']) and feed['mass_flow_kg_h'] > 0,
          'invalid_flow', 'Finite nonnegative components and positive total mass flow required')
    check(finite(feed['temperature_K']) and 200 <= feed['temperature_K'] <= 500, 'temperature_domain_invalid', 'Qualified inlet temperature interval is 200–500 K')
    check(finite(feed['pressure_Pa_abs']) and feed['pressure_Pa_abs'] > 0, 'invalid_pressure', 'Positive inlet absolute pressure required')
    try:
        molecular = MolecularCompositionProvider().enrich(feed)
    except (ValueError, ArithmeticError) as error:
        raise ThermalFailure('specification', 'invalid_composition', str(error)) from error
    # kmol/h -> mol/s. Molecular weights and mass-to-molar projection are owned by M7.
    F = molecular.composition.molar_flow_kmol_h * 1000. / 3600.
    check(finite(F) and F > 0, 'invalid_flow', 'Positive finite molar flow required')
    state = replace(molecular, provenance=StateSpecificationProvenance(p['property_package'], bip.identifier, 'component_mass_flow_kg_h'))
    provider = property_package(p['property_package'])
    inlet = accepted(provider.equilibrium_caloric_PT(state, bip, settings=SolverSettings.high_accuracy()), 'inlet_PT_caloric')
    Hin = inlet.aggregate.h_J_mol
    ph, target = None, None
    if p['mode'] == 'specified_outlet_temperature':
        out_state = replace(state, temperature_K=p['outlet_temperature_K'], pressure_Pa_abs=p['outlet_pressure_Pa_abs'])
        outlet = accepted(provider.equilibrium_caloric_PT(out_state, bip, settings=SolverSettings.high_accuracy()), 'outlet_PT_caloric')
        Q = F * (outlet.aggregate.h_J_mol - Hin)
    else:
        Q = p['duty_W']
        target = Hin + Q / F
        result = provider.flash_PH(PHSpecification(p['outlet_pressure_Pa_abs'], target, state.composition, state.provenance), bip)
        if result.status != 'success' or result.caloric is None:
            raise ThermalFailure('outlet_PH', result.status, result.diagnostics)
        outlet = accepted(result.caloric, 'outlet_PH_caloric')
        ph = dict(status=result.status, capability='flash_PH', pt_profile='high_accuracy',
                  root_iterations=result.diagnostics.root_iterations, evaluation_count=len(result.diagnostics.trials),
                  enthalpy_residual_J_mol=result.enthalpy_residual_J_mol)
    Hout = outlet.aggregate.h_J_mol
    residual = Q - F * (Hout - Hin)
    arithmetic = 64 * float_info.epsilon * max(1., abs(Q), abs(F * Hin), abs(F * Hout))
    allowance = arithmetic + (F * 1e-6 if ph is not None else 0.)
    check(all(finite(v) for v in (Q, Hout, residual, allowance)) and abs(residual) <= allowance,
          'energy_balance_failure', 'Energy closure outside roundoff / qualified PH residual budget')
    out = state_details(outlet)
    details = dict(mode=p['mode'], property_package=inlet.provenance.provider,
        component_dataset=inlet.provenance.component_dataset, molecular_provider=molecular.provenance.provider,
        caloric_dataset=inlet.provenance.caloric_dataset, caloric_reference=inlet.provenance.reference.identifier,
        bip=p['bip'], F_mol_s=F, inlet=state_details(inlet), outlet=out, delta_H_J_mol=Hout-Hin,
        Q_W=Q, energy_residual_W=residual, energy_allowance_W=allowance, H_out_target_J_mol=target, ph=ph)
    stream = state_from_rates(dict(rates), out['temperature_K'], out['pressure_Pa_abs'], F * Hout)
    return EquipmentResult({'outlet': stream}, Q, 0., {'thermodynamics': details})
