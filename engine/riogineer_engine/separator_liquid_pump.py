"""M20 qualified separator-liquid pump; M18/M19 wrappers remain unchanged."""
from copy import deepcopy
from math import fsum,isfinite
from .separator_liquid_state import (verify,close,bip_from,evaluate,local,state,require,hb,ROUND,IDS,
                      PengRobinsonProvider,MolarComposition,StateSpecificationProvenance)
from .pr_ps_flash import PSSpecification
from .pr_ph_flash import PHSpecification
from .pump_energy import inverse
from dataclasses import asdict
from .numerical_profiles import resolve_pt_settings
from .pr_flash import SolverSettings
from .separator_liquid_state import liquid
from .thermodynamics import ThermodynamicState


def profiled_endpoint(T,P,z,bip,profile,parent=None):
    """M21 selected endpoint plus unchanged historical local evidence."""
    settings=resolve_pt_settings(profile,default=SolverSettings.high_accuracy())
    spec=ThermodynamicState(T,P,MolarComposition(IDS,tuple(z)),StateSpecificationProvenance('peng_robinson@1.0',bip.identifier))
    c=PengRobinsonProvider().equilibrium_caloric_PT(spec,bip,numerical_profile=profile)
    require(c.aggregate is not None and c.equilibrium is not None,'profile_PT_failure','unresolved')
    require(c.equilibrium.overall_state==spec and c.equilibrium.provenance.settings==settings,'profile_PT_association')
    require(liquid(c),'profile_liquid','unresolved')
    guard=local(c,bip,parent)
    legacy=evaluate(T,P,z,bip)
    require(liquid(legacy) and close(c.aggregate.h_J_mol,legacy.aggregate.h_J_mol,hb(legacy.aggregate.h_J_mol)) and close(c.aggregate.s_J_mol_K,legacy.aggregate.s_J_mol_K,1e-8,1e-11),'profile_legacy_compatibility')
    witness=None
    if parent is None or parent.equilibrium.classification!='vapor_liquid':
        ws=ThermodynamicState(T,P*.9999,spec.composition,spec.provenance)
        w=PengRobinsonProvider().equilibrium_caloric_PT(ws,bip,numerical_profile=profile)
        require(w.aggregate is not None and w.equilibrium is not None and w.equilibrium.overall_state==ws and w.equilibrium.provenance.settings==settings and liquid(w),'profile_witness','unresolved')
        witness=state(w)
    return c,dict(selected=state(c),selected_settings=asdict(settings),selected_witness=witness,
                  legacy_fresh=state(legacy),legacy_local=guard,legacy_settings=asdict(SolverSettings.high_accuracy()))


def run(stream,source,current,P2,eta,*,numerical_profile=None):
    settings=resolve_pt_settings(numerical_profile,default=SolverSettings.high_accuracy())
    a=verify(stream,source,current)
    require(isfinite(P2) and P2>=stream['pressure_Pa_abs'],'pressure_decrease','rejected')
    require(isfinite(eta) and .6<=eta<=1,'efficiency','rejected')
    if P2==stream['pressure_Pa_abs']:
        return dict(status='accepted',inlet=a,outlet=deepcopy(stream),fluid_power_W=0.,reconstructed_efficiency=None,
                    isentropic=None,PS=None,PH=None,energy_residual_W=0.,identity=True)
    bip=bip_from(stream['state_context']['thermodynamics']);q=PengRobinsonProvider()
    z=MolarComposition(IDS,tuple(a['z']));provenance=StateSpecificationProvenance('peng_robinson@1.0',bip.identifier)
    h1,s1=a['fresh']['H_eq_J_mol'],a['fresh']['S_eq_J_mol_K']
    selected={}
    if numerical_profile is not None:
        parent_data=source['equipment'][0]['thermodynamics']['outlet']
        parent=evaluate(stream['temperature_K'],stream['pressure_Pa_abs'],[parent_data['z'][k] for k in IDS],bip)
        c,selected['inlet']=profiled_endpoint(stream['temperature_K'],stream['pressure_Pa_abs'],a['z'],bip,numerical_profile,parent)
        require(close(c.aggregate.h_J_mol,h1,hb(h1)) and close(c.aggregate.s_J_mol_K,s1,1e-8,1e-11),'profile_inlet_consistency')
        h1,s1=c.aggregate.h_J_mol,c.aggregate.s_J_mol_K
    ps_spec=PSSpecification(P2,s1,z,provenance);ps=q.flash_PS(ps_spec,bip,numerical_profile=numerical_profile);psd=inverse(ps,ps_spec,'PS',numerical_profile=numerical_profile)
    # PR retains the exact specification and normalizes evaluated fractions at roundoff.
    require(ps.caloric.equilibrium.overall_state.pressure_Pa_abs==P2 and ps.caloric.equilibrium.overall_state.composition==z and all(close(x,y,1e-12) for x,y in zip(ps.caloric.equilibrium.evaluated_molar_composition,a['z'])),'PS_association')
    ideal_guard=local(ps.caloric,bip);hs=ps.caloric.aggregate.h_J_mol
    if numerical_profile is not None:
        c,selected['isentropic']=profiled_endpoint(ps.temperature_K,P2,a['z'],bip,numerical_profile)
        require(abs(c.aggregate.s_J_mol_K-s1)<=1e-8,'profile_PS_residual')
        hs=c.aggregate.h_J_mol
    target=h1+(hs-h1)/eta
    ph_spec=PHSpecification(P2,target,z,provenance);ph=q.flash_PH(ph_spec,bip,numerical_profile=numerical_profile);phd=inverse(ph,ph_spec,'PH',numerical_profile=numerical_profile)
    require(ph.caloric.equilibrium.overall_state.pressure_Pa_abs==P2 and ph.caloric.equilibrium.overall_state.composition==z and all(close(x,y,1e-12) for x,y in zip(ph.caloric.equilibrium.evaluated_molar_composition,a['z'])),'PH_association')
    actual_guard=local(ph.caloric,bip);h2,s2=ph.caloric.aggregate.h_J_mol,ph.caloric.aggregate.s_J_mol_K
    if numerical_profile is not None:
        c,selected['actual']=profiled_endpoint(ph.temperature_K,P2,a['z'],bip,numerical_profile)
        require(abs(c.aggregate.h_J_mol-target)<=1e-6,'profile_PH_residual')
        h2,s2=c.aggregate.h_J_mol,c.aggregate.s_J_mol_K
    dh=h2-h1;E=(hb(h1)+hb(hs))/eta+hb(h1)+hb(h2)+500e-8/eta+1e-6+ROUND*max(1,abs(h1),abs(hs),abs(h2))/eta
    require(hs>h1 and dh>0 and E/dh<=1e-4,'work_resolution','rejected')
    reconstructed=(hs-h1)/dh
    require(abs(h2-target)<=1e-6 and abs(reconstructed-eta)<=eta*1e-6/dh+ROUND,'efficiency_residual')
    require(s2-s1>=-2e-8,'entropy')
    if eta==1:require(abs(ph.temperature_K-ps.temperature_K)<=1e-7 and abs(s2-s1)<=2e-8,'unity_efficiency')
    F=a['F_mol_s'];W=F*dh
    outlet={k:deepcopy(v) for k,v in stream.items() if k!='state_context'}
    outlet.update(temperature_K=ph.temperature_K,pressure_Pa_abs=P2,enthalpy_flow_W=F*h2)
    residual=fsum([outlet['enthalpy_flow_W'],-stream['enthalpy_flow_W'],-W])
    rounding=ROUND*max(1,abs(F*h1),abs(F*h2),abs(W))
    require(abs(residual)<=a['enthalpy_allowance_W']+rounding,'upstream_energy_consistency')
    require(abs(W-F*(target-h1))<=F*1e-6+rounding,'target_power')
    require(outlet['component_mass_flow_kg_h']==stream['component_mass_flow_kg_h'] and outlet['mass_flow_kg_h']==stream['mass_flow_kg_h'],'mass_conservation')
    result=dict(status='accepted',identity=False,inlet=a,outlet=outlet,isentropic=state(ps.caloric),actual=state(ph.caloric),
        local_isentropic=ideal_guard,local_actual=actual_guard,PS=psd,PH=phd,fluid_power_W=W,
        reconstructed_efficiency=reconstructed,energy_residual_W=residual,energy_allowance_W=a['enthalpy_allowance_W']+rounding,
        target_H_J_mol=target,work_allowance_J_mol=E,work_ratio=E/dh,entropy_generation_J_mol_K=s2-s1)

    if numerical_profile is not None:
        result['numerics']=dict(numerical_profile=numerical_profile,pump_settings=asdict(settings),
            source_and_local_settings=asdict(SolverSettings.high_accuracy()),fallback=None,endpoints=selected)
    return result
