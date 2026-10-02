"""M17: reuse PR/PT, calorics and shared PH; publish separate material phases."""
from dataclasses import replace
from math import fsum, isfinite
from sys import float_info
from .network_models import EquipmentResult
from .equilibrium_separator import phase_outlets
from .compressor_energy import caloric_state, inverse_details
from .property_packages import property_package
from .pr_eos import BinaryInteractions
from .pr_flash import SolverSettings
from .pr_ph_flash import PHSpecification
from .thermodynamics import MolecularCompositionProvider, StateSpecificationProvenance

MODEL={'id':'equilibrium_separator_energy_pr','version':'1.0'}
PRESSURE_TOLERANCE_PA=1e-8


class SeparatorFailure(ValueError):
    def __init__(self,stage,status,message=''):
        self.stage,self.status=stage,status
        super().__init__(f'{stage}: {status}; {message}')


def finite(v):return isinstance(v,(float,int)) and not isinstance(v,bool) and isfinite(v)


def require(ok,stage,status,message):
    if not ok:raise SeparatorFailure(stage,status,message)


def parameters(p):
    common={'mode','separator_pressure_Pa_abs','property_package','bip'}
    mode=p.get('mode') if isinstance(p,dict) else None
    require(mode in ('specified_temperature','adiabatic'),'specification','invalid_mode','Select PT or adiabatic PH')
    expected=common|({'separator_temperature_K'} if mode=='specified_temperature' else set())
    require(set(p)==expected,'specification','invalid_specification','Mode specifications are exclusive; independent heat duty is forbidden')
    require(p['property_package']=='peng_robinson@1.0','specification','unsupported_provider','Explicit PR required')
    require(finite(p['separator_pressure_Pa_abs']) and p['separator_pressure_Pa_abs']>0,'specification','invalid_pressure','Positive absolute separator pressure required')
    if mode=='specified_temperature':
        require(finite(p['separator_temperature_K']) and 200<=p['separator_temperature_K']<=500,'specification','temperature_domain_invalid','Qualified 200–500 K domain')
    try:bip=BinaryInteractions(**p['bip'])
    except (ValueError,TypeError) as error:raise SeparatorFailure('specification','unsupported_bip',str(error)) from error
    require(bip.component_ids==('methane','n_hexane') and bip.model=='peng_robinson@1.0' and bip.temperature_dependence=='constant' and all(v==0 for row in bip.values for v in row),'specification','unsupported_bip','Explicit constant zero methane/n_hexane kij required')
    return bip


def accepted(c,stage):
    require(c.status in ('success_single_phase','success_two_phase') and c.equilibrium is not None and c.aggregate is not None,stage,c.status,c.message)
    e=c.equilibrium
    expected={'single_liquid':{'liquid'},'single_vapor':{'vapor'},'vapor_liquid':{'vapor','liquid'}}
    require(e.classification in expected and {p.identifier for p in e.phases}==expected[e.classification] and
            {p.phase_identifier for p in c.phases}==expected[e.classification] and e.provenance.settings==SolverSettings.high_accuracy() and
            200<=e.overall_state.temperature_K<=500 and finite(c.aggregate.h_J_mol),stage,'invalid_state','Qualified finite phase state required')
    require(finite(e.beta) and 0<=e.beta<=1 and len(e.phases)==len(expected[e.classification]) and
            ((e.classification=='single_liquid' and e.beta==0) or (e.classification=='single_vapor' and e.beta==1) or
             (e.classification=='vapor_liquid' and 0<e.beta<1)),stage,'invalid_state','Phase identity and fraction must agree')
    return c


def separator(unit,inputs,_evaluate=None):
    require(unit.get('model')==MODEL,'specification','unsupported_model','Explicit M17 model required')
    require(set(inputs)=={'inlet'},'specification','invalid_input','Exactly one material inlet required')
    p=unit['operating_parameters'];bip=parameters(p);feed=inputs['inlet'];rates=feed['component_mass_flow_kg_h']
    require(set(rates)=={'methane','n_hexane'},'specification','unsupported_component','Water and other components excluded, even at zero inventory')
    require(all(finite(v) and v>=0 for v in rates.values()) and finite(feed['mass_flow_kg_h']) and feed['mass_flow_kg_h']>0,'specification','invalid_flow','Positive finite total inlet flow required')
    require(abs(fsum(rates.values())-feed['mass_flow_kg_h'])<=1e-12*max(1.,feed['mass_flow_kg_h']),'specification','invalid_composition','Component flows must reconstruct total')
    require(feed.get('enthalpy_flow_W') is None,'specification','conflicting_state','M17 accepts PT-defined inlet only; independent inlet enthalpy is not accepted')
    T1=feed['temperature_K'];P1=feed['pressure_Pa_abs'];P2=p['separator_pressure_Pa_abs']
    require(finite(T1) and 200<=T1<=500,'specification','temperature_domain_invalid','Inlet temperature must lie within 200–500 K')
    require(finite(P1) and P1>0 and P2-P1<=PRESSURE_TOLERANCE_PA,'specification','invalid_pressure','Passive separator requires P_separator <= P_inlet (1e-8 Pa tolerance)')
    try:molecular=MolecularCompositionProvider().enrich(feed)
    except ValueError as error:raise SeparatorFailure('specification','invalid_composition',str(error)) from error
    state=replace(molecular,provenance=StateSpecificationProvenance(p['property_package'],bip.identifier,'component_mass_flow_kg_h'))
    provider=property_package(p['property_package']);settings=SolverSettings.high_accuracy()
    inlet=accepted(provider.equilibrium_caloric_PT(state,bip,settings),'inlet_PT')
    F=molecular.composition.molar_flow_kmol_h*1000/3600
    require(finite(F) and F>0,'specification','invalid_flow','Positive finite molar flow required')
    hin=F*inlet.aggregate.h_J_mol;ph_details=None
    if p['mode']=='specified_temperature':
        outlet=accepted(provider.equilibrium_caloric_PT(replace(state,temperature_K=p['separator_temperature_K'],pressure_Pa_abs=P2),bip,settings),'outlet_PT')
    else:
        ph=provider.flash_PH(PHSpecification(P2,hin/F,state.composition,state.provenance),bip)
        require(ph.status=='success' and ph.caloric is not None,'outlet_PH',ph.status,ph.diagnostics.reason)
        try:ph_details=inverse_details(ph,'flash_PH')
        except ValueError as error:raise SeparatorFailure('outlet_PH','invalid_nested_diagnostics',str(error)) from error
        require(finite(ph.enthalpy_residual_J_mol) and abs(ph.enthalpy_residual_J_mol)<=1e-6,'outlet_PH','invalid_residual','PH residual must pass')
        outlet=accepted(ph.caloric,'outlet_PH')
        require(outlet.equilibrium.overall_state.temperature_K==ph.temperature_K,'outlet_PH','invalid_state','PH temperature/state mismatch')
    require(caloric_state(outlet)['z']==caloric_state(inlet)['z'],'outlet','material_balance_failure','Overall composition must be conserved')
    e=outlet.equilibrium
    require(e.overall_state.pressure_Pa_abs==P2,'outlet','invalid_state','Specified pressure must be conserved')
    outputs=phase_outlets(molecular,e)
    calorics={c.phase_identifier:c for c in outlet.phases};phase_details={};reconstructed={}
    for name,out in outputs.items():
        projection=MolecularCompositionProvider().enrich(out).composition;reconstructed[name]=projection
        cp=calorics.get(name);fp=projection.molar_flow_kmol_h*1000/3600
        out['enthalpy_flow_W']=fp*cp.h_total_J_mol if cp else 0.
        phase_details[name]=dict(molar_flow_mol_s=fp,composition=dict(projection.molar_fractions) if projection.molar_fractions else None,
            h_J_mol=cp.h_total_J_mol if cp else None,enthalpy_flow_W=out['enthalpy_flow_W'])
    molar={i:molecular.composition.component_molar_flow_kmol_h[i]-fsum(c.component_molar_flow_kmol_h[i] for c in reconstructed.values()) for i in rates}
    require(all(finite(v) and abs(v)<=1e-8 for v in molar.values()),'outlet','material_balance_failure','Component molar closure required')
    for phase in e.phases:
        actual=reconstructed[phase.identifier]
        require(actual.molar_fractions is not None and all(abs(actual.molar_fractions[i]-q)<=1e-12 for i,q in zip(molecular.composition.component_ids,phase.composition)), 'outlet','material_balance_failure','Phase composition round trip required')
    for name,weight in [('vapor',e.beta),('liquid',1-e.beta)]:
        require(abs(phase_details[name]['molar_flow_mol_s']/F-weight)<=1e-12,'outlet','material_balance_failure','Molar phase fraction must reconstruct')
    from .network import mass_balance
    mass_balance([feed],list(outputs.values()),rates)
    hout=fsum(out['enthalpy_flow_W'] for out in outputs.values());arithmetic=64*float_info.epsilon*max(1.,abs(hin),abs(hout))
    require(abs(hout/F-outlet.aggregate.h_J_mol)<=1e-6,'outlet','energy_balance_failure','Phase energy must reconstruct equilibrium enthalpy')
    duty=hout-hin if p['mode']=='specified_temperature' else 0.
    residual=fsum([hout,-hin,-duty]);allow=F*1e-6+arithmetic
    require(all(finite(v) for v in (hin,hout,duty,residual,allow)) and abs(residual)<=allow,'outlet','energy_balance_failure','Reported outlet energy must close against inlet and duty')
    d=dict(mode=p['mode'],property_package=p['property_package'],component_dataset=inlet.provenance.component_dataset,
        molecular_provider=molecular.provenance.provider,caloric_dataset=inlet.provenance.caloric_dataset,caloric_reference=inlet.provenance.reference.identifier,
        bip=p['bip'],F_mol_s=F,inlet=caloric_state(inlet),outlet=caloric_state(outlet),ph=ph_details,
        phases=phase_details,inlet_enthalpy_flow_W=hin,duty_W=duty,energy_residual_W=residual,energy_allowance_W=allow,
        component_molar_residual_kmol_h=molar,zero_duty_tolerance_W=allow)
    return EquipmentResult(outputs,duty,0.,{'thermodynamics':d})
