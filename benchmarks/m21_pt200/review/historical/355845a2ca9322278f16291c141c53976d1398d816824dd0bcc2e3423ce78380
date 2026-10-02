"""PT equipment adapter: molecular projection and phase-to-material mapping only."""
from dataclasses import asdict, replace
from math import isfinite
from .network_models import EquipmentResult, state_from_rates
from .pr_eos import BinaryInteractions
from .property_packages import property_package
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MOLAR_TOLERANCE_KMOL_H = 1e-8
ENERGY_REASON = 'Isothermal/isobaric PT equilibrium does not calculate phase-change enthalpy, heat duty, shaft work or an energy balance.'


def separator(unit, inputs, _evaluate):
    if set(inputs) != {'inlet'}:
        raise ValueError('PT separator requires exactly one inlet')
    feed = inputs['inlet']
    molecular = MolecularCompositionProvider().enrich(feed)
    c = molecular.composition
    if set(c.component_ids) != {'methane', 'n_hexane'} or c.molar_flow_kmol_h <= 0:
        raise ValueError('PT separator requires positive methane/n_hexane feed; water is unsupported')
    p = unit['operating_parameters']
    bip = BinaryInteractions(**p['bip'])
    state = replace(molecular, provenance=StateSpecificationProvenance(
        p['property_package'], bip.identifier, 'component_mass_flow_kg_h'))
    result = property_package(p['property_package']).flash_PT(state, bip)
    expected = {'vapor_liquid': ('success_two_phase', {'vapor', 'liquid'}),
                'single_liquid': ('success_single_phase', {'liquid'}),
                'single_vapor': ('success_single_phase', {'vapor'})}
    status, identities = expected.get(result.classification, (None, set()))
    phases = {phase.identifier: phase for phase in result.phases}
    if result.status != status or set(phases) != identities or len(phases) != len(result.phases) or result.beta is None:
        raise ValueError(f"{p['property_package']}: PT flash {result.status}; {detailed_failure(result)}")
    if not isfinite(result.beta) or not 0 <= result.beta <= 1:
        raise ValueError('Invalid PT phase fraction')
    outputs = phase_outlets(molecular, result)
    # Independently reconstruct both outlet compositions through M7, including zero semantics.
    reconstructed = {name: MolecularCompositionProvider().enrich(out).composition for name, out in outputs.items()}
    molar = {i: c.component_molar_flow_kmol_h[i] - sum(out.component_molar_flow_kmol_h[i] for out in reconstructed.values())
             for i in c.component_ids}
    if any(not isfinite(v) or abs(v) > MOLAR_TOLERANCE_KMOL_H for v in molar.values()):
        raise ValueError('PT separator component molar balance failed')
    for name, phase in phases.items():
        out = reconstructed[name]
        if out.molar_fractions is None or any(abs(out.molar_fractions[i]-q) > 1e-12 for i, q in zip(c.component_ids, phase.composition)):
            raise ValueError('PT separator molecular round trip failed')
    for name, fraction in [('vapor', result.beta), ('liquid', 1-result.beta)]:
        if abs(reconstructed[name].molar_flow_kmol_h/c.molar_flow_kmol_h-fraction) > 1e-12:
            raise ValueError('PT separator molar phase fraction failed')
    from .network import mass_balance
    balance = mass_balance([feed], list(outputs.values()), c.component_ids)
    def vector(values):
        return dict(zip(c.component_ids, values))
    def phase_value(name, field):
        phase = phases.get(name)
        if phase is None:
            return None
        value = getattr(phase, field)
        return vector(value) if isinstance(value, tuple) else value
    d = result.diagnostics
    details = dict(property_package=result.provenance.provider, component_dataset=result.provenance.component_dataset,
        bip=dict(asdict(result.provenance.bip), component_ids=list(bip.component_ids), values=[list(row) for row in bip.values]), input_basis='component_mass_flow_kg_h', fraction_basis='mol/mol',
        classification=result.classification, status=result.status, iterations=d.iterations,
        beta=result.beta, liquid_fraction=1-result.beta,
        x=phase_value('liquid', 'composition'), y=phase_value('vapor', 'composition'),
        Z_L=phase_value('liquid', 'Z'), Z_V=phase_value('vapor', 'Z'),
        phi_L=phase_value('liquid', 'phi'), phi_V=phase_value('vapor', 'phi'),
        final_K=vector(result.final_K) if result.final_K else None,
        fugacity_residual=vector(d.fugacity_residual) if d.fugacity_residual else None,
        rachford_rice_residual=d.rr_residual,
        material_reconstruction_residual=vector(d.material_residual) if d.material_residual else {i: 0.0 for i in c.component_ids},
        inlet_molar_flow_kmol_h=c.molar_flow_kmol_h,
        vapor_molar_flow_kmol_h=reconstructed['vapor'].molar_flow_kmol_h,
        liquid_molar_flow_kmol_h=reconstructed['liquid'].molar_flow_kmol_h,
        component_molar_residual_kmol_h=molar, component_molar_tolerance_kmol_h=MOLAR_TOLERANCE_KMOL_H,
        component_mass_residual_kg_h=balance['component_residual_kg_h'], total_mass_residual_kg_h=balance['total_residual_kg_h'])
    return EquipmentResult(outputs, None, None, {'thermodynamics': details})


def detailed_failure(result):
    d = result.diagnostics
    return (f'{d.message}; iterations={d.iterations}; fugacity_residual={d.fugacity_residual}; '
            f'RR_residual={d.rr_residual}; material_residual={d.material_residual}')


def phase_outlets(molecular, result):
    """Shared inventory mapping only; the caller owns caloric/energy semantics."""
    c = molecular.composition
    state = result.overall_state
    phases = {phase.identifier: phase for phase in result.phases}
    outputs = {}
    for name in ('vapor', 'liquid'):
        phase = phases.get(name)
        if phase is None:
            rates = {i: 0.0 for i in c.component_ids}
        elif len(phases) == 1:
            # Preserve the complete inventory exactly; absent phase has zero flow, no composition.
            rates = dict(c.component_mass_flow_kg_h)
        else:
            fraction = result.beta if name == 'vapor' else 1-result.beta
            rates = {i: c.molar_flow_kmol_h * fraction * q * molecular.provenance.molecular_weights_kg_kmol[i]
                     for i, q in zip(c.component_ids, phase.composition)}
        outputs[name] = state_from_rates(rates, state.temperature_K, state.pressure_Pa_abs, None)
    return outputs
