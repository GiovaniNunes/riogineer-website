"""M20 upstream-derived state checks. No independent reference or file access."""
from copy import deepcopy
from dataclasses import asdict
from math import fsum,isfinite,log
from sys import float_info
from .property_packages import PengRobinsonProvider
from .thermodynamics import MolecularCompositionProvider,ThermodynamicState,MolarComposition,StateSpecificationProvenance
from .pr_eos import BinaryInteractions
from .pr_flash import SolverSettings
from .components import DATASET as COMPONENT_DATASET
from .caloric_data import DATASET as CALORIC_DATASET,REFERENCE

IDS=('methane','n_hexane')
ROUND=64*float_info.epsilon
UNITS=dict(component_mass_flow='kg/h',temperature='K',pressure='Pa_abs',duty='W')

class Failure(ValueError):
    def __init__(self,category,code):self.category,self.code=category,code;super().__init__(category+': '+code)
def require(ok,code,category='contradictory_evidence'):
    if not ok:raise Failure(category,code)
def close(a,b,absolute,relative=0.):
    return isinstance(a,(float,int)) and not isinstance(a,bool) and isfinite(a) and abs(a-b)<=absolute+relative*abs(b)
def hb(h):return 1e-6+1e-11*abs(h)
def identity(r):return {k:r[k] for k in ('run_id','input_sha256','requirements_sha256')}

def representation(r):
    """Add provenance; do not alter even one material-stream property."""
    e=r['equipment'][0];d=e['thermodynamics'];sid=e['material_streams']['liquid']
    s=deepcopy(r['streams'][sid])
    s['state_context']=dict(specification_kind='upstream_derived',phase='liquid',
        saturation='source_vle' if d['outlet']['classification']=='vapor_liquid' else 'unknown',
        source=identity(r)|dict(equipment_id=e['id'],port_id='liquid',stream_id=sid),
        thermodynamics={k:deepcopy(d[k]) for k in ('property_package','component_dataset','caloric_dataset','caloric_reference','bip')})
    return s

def bip_from(d):
    require(d['property_package']=='peng_robinson@1.0','property_package')
    require(d['component_dataset']==COMPONENT_DATASET,'component_dataset')
    require(d['caloric_dataset']==CALORIC_DATASET and d['caloric_reference']==REFERENCE.identifier,'caloric_reference')
    bip=BinaryInteractions(**d['bip'])
    require(bip.component_ids==IDS and bip.model=='peng_robinson@1.0' and bip.temperature_dependence=='constant' and all(v==0 for row in bip.values for v in row),'kij')
    return bip

def evaluate(T,P,z,bip):
    spec=ThermodynamicState(T,P,MolarComposition(IDS,tuple(z)),StateSpecificationProvenance('peng_robinson@1.0',bip.identifier))
    c=PengRobinsonProvider().equilibrium_caloric_PT(spec,bip,SolverSettings.high_accuracy())
    require(c.aggregate is not None and c.equilibrium is not None and c.status.startswith('success'),'PT_failure','unresolved')
    require(c.equilibrium.overall_state==spec and c.equilibrium.provenance.settings==SolverSettings.high_accuracy(),'PT_association')
    return c

def state(c):
    p=c.equilibrium
    return dict(T_K=p.overall_state.temperature_K,P_Pa_abs=p.overall_state.pressure_Pa_abs,
        z=list(p.evaluated_molar_composition),classification=p.classification,beta=p.beta,
        H_eq_J_mol=c.aggregate.h_J_mol,S_eq_J_mol_K=c.aggregate.s_J_mol_K,
        stability=asdict(p.diagnostics.stability),
        phases={q.identifier:dict(composition=list(q.composition),Z=q.Z,h_J_mol=h.h_total_J_mol,s_J_mol_K=h.s_total_J_mol_K) for q,h in zip(p.phases,c.phases)})

def liquid(c):
    e=c.equilibrium;d=e.diagnostics.stability
    return (e.classification=='single_liquid' and e.beta==0 and d is not None and d.stable is True and d.converged is True and d.phase_identification_parameter is not None and d.phase_identification_parameter>1 and len(e.phases)==len(c.phases)==1 and e.phases[0].identifier==c.phases[0].phase_identifier=='liquid' and e.phases[0].Z>0)

def local(c,bip,parent=None):
    """Finite local evidence, no bubble-pressure lookup or forced phase root."""
    if c.equilibrium.classification in ('single_vapor','vapor_liquid'):
        raise Failure('rejected','non_liquid_'+c.equilibrium.classification)
    require(liquid(c),'ambiguous_liquid','unresolved')
    s=state(c)
    if parent is not None and parent.equilibrium.classification=='vapor_liquid':
        e=parent.equilibrium;ph={p.identifier:p for p in e.phases}
        require(0<e.beta<1 and e.diagnostics.stability is not None and e.diagnostics.stability.converged,'parent_equilibrium','unresolved')
        common=e.diagnostics.equilibrium_stability
        require(common is not None and common.converged and common.stable is True,'parent_common_tangent','unresolved')
        a,b=ph['liquid'],ph['vapor']
        require(e.overall_state.temperature_K==s['T_K'] and e.overall_state.pressure_Pa_abs==s['P_Pa_abs'],'parent_state')
        require(all(close(x,y,1e-12) for x,y in zip(s['z'],a.composition)),'parent_liquid_composition')
        eos=PengRobinsonProvider().eos(IDS,s['T_K'],s['P_Pa_abs'],bip)
        fa=eos.fugacity(eos.mixture(a.composition),a.Z)
        fb=eos.fugacity(eos.mixture(b.composition),b.Z)
        residual=[log(x)+u-log(y)-v for x,u,y,v in zip(a.composition,fa.ln_phi,b.composition,fb.ln_phi)]
        gap=max(abs(x-y) for x,y in zip(a.composition,b.composition));zgap=abs(a.Z-b.Z)
        require(gap>.01 and zgap>.01 and max(map(abs,residual))<=2e-10,'coexistence_branch','unresolved')
        return dict(status='saturated_source_liquid',fugacity_residual=residual,composition_gap=gap,Z_gap=zgap,common_tangent_stability=asdict(common),
                    same_T_composition_bubble_evidence='fresh verified parent liquid/vapor common tangent',cavitation_safe=None)
    witness=evaluate(s['T_K'],s['P_Pa_abs']*.9999,s['z'],bip)
    require(liquid(witness),'boundary_unresolved','unresolved')
    return dict(status='compressed_witness',witness=state(witness),sampled_pressure_decrement_Pa=s['P_Pa_abs']*.0001,
                quantified_bubble_margin_Pa=None,cavitation_safe=None)

def _verify(s,r,current):
    require('state_context' in s,'state_context','missing_evidence');ctx=s['state_context']
    for key in ('specification_kind','phase','saturation','source','thermodynamics'):
        require(key in ctx,key,'missing_evidence')
    require(ctx['specification_kind']=='upstream_derived','independent_specification_kind')
    require(ctx['phase']=='liquid','phase_identity')
    require(ctx['saturation'] in ('source_vle','unknown'),'saturation_evidence')
    for k in ('run_id','input_sha256','requirements_sha256','equipment_id','port_id','stream_id'):
        require(k in ctx['source'],k,'missing_evidence')
    for k in ('property_package','component_dataset','caloric_dataset','caloric_reference','bip'):
        require(k in ctx['thermodynamics'],k,'missing_evidence')
    require(r['status']=='completed','source_not_completed','missing_evidence')
    for k,v in current.items():require(identity(r).get(k)==v and ctx['source'].get(k)==v,'stale_'+k)
    require(set(current)==set(identity(r)),'current_identity','missing_evidence')
    e=next((e for e in r['equipment'] if e['id']==ctx['source'].get('equipment_id')),None)
    require(e is not None,'source_equipment')
    require(e['model']=={'id':'equilibrium_separator_energy_pr','version':'1.0'},'separator_model')
    require(ctx['source'].get('port_id')=='liquid' and ctx['source'].get('stream_id')==e['material_streams']['liquid'],'source_port')
    d=e['thermodynamics'];old=r['streams'][ctx['source']['stream_id']];p=d['outlet']
    require(set(s)==set(old)|{'state_context'},'unexpected_stream_fields')
    require(set(ctx)=={'specification_kind','phase','saturation','source','thermodynamics'},'unexpected_context_fields')
    for k,v in UNITS.items():require(r['units'].get(k)==v,'units_'+k)
    require(ctx['thermodynamics']=={k:d[k] for k in ctx['thermodynamics']} and set(ctx['thermodynamics'])=={'property_package','component_dataset','caloric_dataset','caloric_reference','bip'},'thermodynamic_provenance')
    bip=bip_from(ctx['thermodynamics'])
    require(set(s['component_mass_flow_kg_h'])==set(IDS),'components')
    for key,ab,rel in (('temperature_K',1e-8,1e-12),('pressure_Pa_abs',1e-5,1e-12),('mass_flow_kg_h',1e-8,1e-12)):
        require(close(s[key],old[key],ab,rel),'source_'+key)
    require(close(s['temperature_K'],p['temperature_K'],1e-8,1e-12) and close(s['pressure_Pa_abs'],p['pressure_Pa_abs'],1e-5,1e-12),'phase_TP')
    for k in IDS:require(close(s['component_mass_flow_kg_h'][k],old['component_mass_flow_kg_h'][k],1e-8,1e-12),'source_component_'+k)
    require(close(fsum(s['component_mass_flow_kg_h'].values()),s['mass_flow_kg_h'],1e-8,1e-12),'total_mass')
    m=MolecularCompositionProvider().enrich(s).composition;F=m.molar_flow_kmol_h/3.6
    if F==0:
        require(s['enthalpy_flow_W']==0 and d['phases']['liquid']['h_J_mol'] is None,'absent_intensives')
        raise Failure('rejected','absent_liquid')
    z=[m.molar_fractions[k] for k in IDS];phase=p['phases']['liquid'];h,entropy=phase['h_J_mol'],phase['s_J_mol_K']
    require(close(F,d['phases']['liquid']['molar_flow_mol_s'],1e-10,1e-12),'molar_flow')
    require(close(F,d['F_mol_s']*(1-p['beta']),1e-10,1e-12),'parent_phase_flow')
    require(close(d['phases']['liquid']['h_J_mol'],h,hb(h)),'source_phase_enthalpy')
    require(all(close(z[j],phase['composition'][k],1e-12) for j,k in enumerate(IDS)),'phase_composition')
    require(all(close(s['component_mass_fractions'][k],m.mass_fractions[k],1e-12) for k in IDS),'mass_fractions')
    require(s.get('enthalpy_flow_W') is not None,'upstream_enthalpy','missing_evidence')
    budget=F*hb(h)+ROUND*max(1,abs(F*h))
    require(close(s['enthalpy_flow_W'],F*h,budget) and close(s['enthalpy_flow_W'],old['enthalpy_flow_W'],budget) and close(s['enthalpy_flow_W'],d['phases']['liquid']['enthalpy_flow_W'],budget),'enthalpy_flow')
    props=s.get('properties',{})
    for key,unit,expected,tol in [('molar_flow','kmol/h',F*3.6,3.6e-10),('molecular_mass','kg/kmol',m.molecular_weight_kg_kmol,1e-8)]:
        if key in props:require(props[key]['unit']==unit and props[key]['status']=='calculated' and close(props[key]['value'],expected,tol,1e-12),'property_'+key)
    if 'molar_composition' in props:
        q=props['molar_composition'];require(q['unit']=='mol/mol' and q['status']=='calculated' and all(close(q['value'][k],z[j],1e-12) for j,k in enumerate(IDS)),'property_composition')
    fresh=evaluate(s['temperature_K'],s['pressure_Pa_abs'],z,bip)
    require(close(fresh.aggregate.h_J_mol,h,hb(h)) and close(fresh.aggregate.s_J_mol_K,entropy,1e-8,1e-11),'fresh_caloric')
    # Fresh parent corroboration; provenance alone cannot override inconsistent data.
    parent=evaluate(s['temperature_K'],s['pressure_Pa_abs'],[p['z'][k] for k in IDS],bip)
    require(parent.equilibrium.classification==p['classification'] and close(parent.equilibrium.beta,p['beta'],2e-9),'parent_classification')
    actual={q.identifier:(q,cp) for q,cp in zip(parent.equilibrium.phases,parent.phases)}
    require('liquid' in actual,'parent_missing_liquid')
    q,cp=actual['liquid']
    require(all(close(x,phase['composition'][k],1e-12) for x,k in zip(q.composition,IDS)) and close(cp.h_total_J_mol,h,hb(h)) and close(cp.s_total_J_mol_K,entropy,1e-8,1e-11),'fresh_parent_phase')
    require(ctx['saturation']!='source_vle' or parent.equilibrium.classification=='vapor_liquid','false_saturation')
    # Both fresh evaluations use the received T/P after strict source agreement;
    # no snapping to the stored source coordinates is performed.
    associated=parent if fresh.equilibrium.overall_state.temperature_K==parent.equilibrium.overall_state.temperature_K and fresh.equilibrium.overall_state.pressure_Pa_abs==parent.equilibrium.overall_state.pressure_Pa_abs else None
    guard=local(fresh,bip,associated)
    return dict(status='accepted',stream=deepcopy(s),F_mol_s=F,z=z,fresh=state(fresh),local=guard,
                source_identity=identity(r),upstream_enthalpy_flow_W=s['enthalpy_flow_W'],enthalpy_allowance_W=budget)

def verify(s,r,current):
    try:return _verify(s,r,current)
    except Failure:raise
    except KeyError as e:
        raise Failure('missing_evidence','missing_'+str(e)) from e
    except (TypeError,ValueError,ArithmeticError,StopIteration) as e:
        raise Failure('contradictory_evidence','malformed_'+type(e).__name__) from e
