"""Adiabatic isenthalpic throttling through qualified PT/caloric and PH providers."""
from dataclasses import replace
from math import fsum, isfinite
from sys import float_info
from .network_models import EquipmentResult, state_from_rates
from .compressor_energy import caloric_state
from .property_packages import property_package
from .pr_eos import BinaryInteractions
from .pr_flash import SolverSettings
from .pr_ph_flash import PHSpecification
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MODEL={'id':'rigorous_isenthalpic_pr','version':'1.0'}


class ValveFailure(ValueError):
    def __init__(self,stage,status,diagnostics=''):
        self.stage,self.status,self.diagnostics=stage,status,diagnostics
        super().__init__(f'peng_robinson@1.0: {stage}: {status}; {diagnostics}')


def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and isfinite(v)


def require(condition,stage,status,message):
    if not condition:raise ValveFailure(stage,status,message)


def parameters(p):
    require(isinstance(p,dict) and set(p)=={'outlet_pressure_Pa_abs','property_package','bip'},
            'specification','invalid_specification','Exactly the rigorous valve fields are required')
    require(p['property_package']=='peng_robinson@1.0','specification','unsupported_provider','Explicit PR provider required')
    require(finite(p['outlet_pressure_Pa_abs']) and p['outlet_pressure_Pa_abs']>0,
            'specification','invalid_pressure','Finite positive absolute outlet pressure required')
    try:bip=BinaryInteractions(**p['bip'])
    except (TypeError,ValueError) as error:raise ValveFailure('specification','unsupported_bip',str(error)) from error
    require(bip.component_ids==('methane','n_hexane') and bip.temperature_dependence=='constant' and
            bip.model=='peng_robinson@1.0' and all(v==0 for row in bip.values for v in row),
            'specification','unsupported_bip','Qualified explicit constant zero methane/n_hexane BIP required')
    return bip


def accepted(c,stage):
    require(c.status.startswith('success') and c.aggregate is not None and c.equilibrium is not None,
            stage,c.status,c.message)
    e=c.equilibrium
    require(e.status.startswith('success') and e.provenance.settings==SolverSettings.high_accuracy() and
            200<=e.overall_state.temperature_K<=500 and
            all(finite(v) for v in (c.aggregate.h_J_mol,c.aggregate.s_J_mol_K)),
            stage,'invalid_state','Finite qualified high_accuracy caloric state required')
    require(e.classification in ('single_liquid','single_vapor','vapor_liquid'),stage,'invalid_state','Unsupported phase state')
    if stage=='inlet_PT':
        require(e.classification!='vapor_liquid','service_scope','inlet_service_scope','Single-phase valve inlet service required')
    return c


def valve(unit,inputs,_evaluate=None):
    require(unit.get('model')==MODEL,'specification','unsupported_model','Explicit rigorous valve identity required')
    require(set(inputs)=={'inlet'},'specification','invalid_input','Exactly one material inlet required')
    p=unit['operating_parameters'];bip=parameters(p);feed=inputs['inlet'];rates=feed['component_mass_flow_kg_h']
    require(set(rates)=={'methane','n_hexane'},'specification','unsupported_component','Complete methane/n_hexane basis required')
    require(all(finite(v) and v>=0 for v in rates.values()) and finite(feed['mass_flow_kg_h']) and feed['mass_flow_kg_h']>0,
            'specification','invalid_flow','Finite positive total flow and nonnegative component flows required')
    require(abs(fsum(rates.values())-feed['mass_flow_kg_h'])<=1e-12*max(1.,feed['mass_flow_kg_h']),
            'specification','invalid_composition','Component flows must reconstruct the supplied total')
    P1=feed['pressure_Pa_abs'];P2=p['outlet_pressure_Pa_abs'];T1=feed['temperature_K']
    require(finite(P1) and P1>P2>0,'specification','invalid_pressure','P_in > P_out > 0 required')
    require(finite(T1) and 200<=T1<=500,'specification','temperature_domain_invalid','Qualified 200–500 K inlet domain required')
    try:molecular=MolecularCompositionProvider().enrich(feed)
    except (ValueError,ArithmeticError) as error:raise ValveFailure('specification','invalid_composition',str(error)) from error
    F=molecular.composition.molar_flow_kmol_h*1000./3600.
    require(finite(F) and F>0,'specification','invalid_flow','Finite positive molar flow required')
    state=replace(molecular,provenance=StateSpecificationProvenance(p['property_package'],bip.identifier,'component_mass_flow_kg_h'))
    provider=property_package(p['property_package'])
    inlet=accepted(provider.equilibrium_caloric_PT(state,bip,SolverSettings.high_accuracy()),'inlet_PT')
    H1=inlet.aggregate.h_J_mol;S1=inlet.aggregate.s_J_mol_K
    ph=provider.flash_PH(PHSpecification(P2,H1,state.composition,state.provenance),bip)
    if ph.status!='success' or ph.caloric is None:raise ValveFailure('outlet_PH',ph.status,ph.diagnostics)
    d=ph.diagnostics
    require(d.pt_settings==SolverSettings.high_accuracy() and len(d.brackets_K)==1 and
            d.selected_bracket_K is not None and d.final_bracket_K is not None and
            d.trials and d.trials[-1].stage=='final' and finite(ph.enthalpy_residual_J_mol) and
            abs(ph.enthalpy_residual_J_mol)<=1e-6,'outlet_PH','invalid_nested_diagnostics',d)
    # Equipment acceptance uses a fresh PT state, never a cached inverse payload.
    final_state=replace(state,temperature_K=ph.temperature_K,pressure_Pa_abs=P2)
    outlet=accepted(provider.equilibrium_caloric_PT(final_state,bip,SolverSettings.high_accuracy()),'final_acceptance')
    H2=outlet.aggregate.h_J_mol;S2=outlet.aggregate.s_J_mol_K;dh=H2-H1
    require(abs(dh)<=1e-6,'final_acceptance','final_acceptance_failed','Fresh outlet violates isenthalpic residual')
    a,o=caloric_state(inlet),caloric_state(outlet)
    require(o['z']==a['z'] and o['pressure_Pa_abs']==P2,'final_acceptance','material_balance_failure','Overall composition and specified pressure must be conserved')
    e=outlet.equilibrium
    if e.classification=='vapor_liquid':
        require(0<e.beta<1 and set(o['phases'])=={'liquid','vapor'},'final_acceptance','invalid_state','Complete internal VL state required')
    weights={'liquid':1-e.beta,'vapor':e.beta}
    require(all(abs(fsum(v['composition'].values())-1)<=1e-10 for v in o['phases'].values()),
            'final_acceptance','material_balance_failure','Phase compositions must close')
    require(all(abs(fsum(weights[k]*v['composition'][c] for k,v in o['phases'].items())-z)<=1e-10 for c,z in o['z'].items()),
            'final_acceptance','material_balance_failure','Phase compositions must reconstruct overall composition')
    require(abs(fsum(weights[k]*v['h_J_mol'] for k,v in o['phases'].items())-H2)<=1e-6,
            'final_acceptance','final_acceptance_failed','Phase enthalpy must reconstruct equilibrium enthalpy')
    residual=F*dh;allow=F*1e-6
    arithmetic=64*float_info.epsilon*max(1.,abs(F*H1),abs(F*H2))
    require(abs(fsum([F*H2,-F*H1])-residual)<=arithmetic,'final_acceptance','energy_balance_failure','Stream enthalpy flows must reconstruct closure')
    require(finite(residual) and abs(residual)<=allow,'final_acceptance','energy_balance_failure','Adiabatic isenthalpic closure required')
    stream=state_from_rates(dict(rates),o['temperature_K'],P2,F*H2)
    projected=MolecularCompositionProvider().enrich(stream).composition
    require(projected.molar_flow_kmol_h==molecular.composition.molar_flow_kmol_h and
            projected.molar_fractions==molecular.composition.molar_fractions,'final_acceptance','material_balance_failure','Flow and composition must be conserved')
    details=dict(property_package=inlet.provenance.provider,component_dataset=inlet.provenance.component_dataset,
        molecular_provider=molecular.provenance.provider,caloric_dataset=inlet.provenance.caloric_dataset,
        caloric_reference=inlet.provenance.reference.identifier,bip=p['bip'],F_mol_s=F,inlet=a,outlet=o,
        pressure_ratio=P2/P1,pressure_drop_Pa=P1-P2,H_out_target_J_mol=H1,delta_H_J_mol=dh,
        delta_S_J_mol_K=S2-S1,enthalpy_residual_J_mol=dh,energy_residual_W=residual,energy_allowance_W=allow,
        ph=dict(status=ph.status,capability='flash_PH',pt_profile='high_accuracy',candidate_count=len(d.brackets_K),
            bracket_K=list(d.selected_bracket_K),final_bracket_K=list(d.final_bracket_K),root_iterations=d.root_iterations,
            evaluation_count=len(d.trials),enthalpy_residual_J_mol=ph.enthalpy_residual_J_mol))
    return EquipmentResult({'outlet':stream},0.,0.,{'thermodynamics':details})
