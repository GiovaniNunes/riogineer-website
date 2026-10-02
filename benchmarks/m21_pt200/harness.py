"""M21 verification orchestration derived from the frozen study; all solvers are production APIs."""
import sys,math,inspect
from dataclasses import asdict
from .common import *
from .profile import Profile,inverse,guard
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pr_flash import flash_pt
from riogineer_engine.pr_ps_flash import PSSpecification
from riogineer_engine.pr_ph_flash import PHSpecification
from riogineer_engine.thermodynamics import ThermodynamicState,MolarComposition
from riogineer_engine.separator_liquid_state import verify,identity,local,liquid,require,hb,ROUND
from riogineer_engine.separator_pump_process import ExecutionContext
from riogineer_engine.milestone20 import requirements
from riogineer_engine.core import build_flowsheet
from benchmarks.pump_energy.compare_production import BIP,PROVENANCE,state,inverse as diagnostic
from benchmarks.pump_energy.common import finish

PROVIDER=PengRobinsonProvider()
TRACE_LINE=next(j for j,line in enumerate(inspect.getsourcefile(flash_pt) and Path(inspect.getsourcefile(flash_pt)).read_text().splitlines(),1) if 'if max(abs(v) for v in fugacity)' in line)

def specification(T,P,z):return ThermodynamicState(T,P,MolarComposition(IDS,tuple(z)),PROVENANCE)
def pt(T,P,z,profile):return PROVIDER.equilibrium_caloric_PT(specification(T,P,z),BIP,profile.settings)
def numeric_without_budget(v):
    if isinstance(v,dict):return {k:numeric_without_budget(x) for k,x in v.items() if k not in ('flash_max_iterations','numerical_profile')}
    if isinstance(v,(list,tuple)):return [numeric_without_budget(x) for x in v]
    return v

def traced_pt(row,profile):
    trace=[]
    def observer(frame,event,arg):
        if frame.f_code is flash_pt.__code__ and event=='line' and frame.f_lineno==TRACE_LINE:
            d=frame.f_locals['diag'];trace.append(dict(iteration=d.iterations,K=list(frame.f_locals['k']),beta=frame.f_locals['rr'].beta,
                fugacity=list(d.fugacity_residual),material=list(d.material_residual),rr_iterations=d.rr_iterations,restarts=d.initialization.restart_count))
        return observer
    old=sys.gettrace()
    try:
        sys.settrace(observer);c=pt(row['T'],row['P'],row['z'],profile)
    finally:sys.settrace(old)
    d=asdict(c.equilibrium.diagnostics) if c.equilibrium else None
    return dict(status=c.status,message=c.message,state=state(c) if c.aggregate else None,PT=asdict(c.equilibrium),
        trace_sha256=hashed(trace),trace_events=len(trace),trace_RR_iterations=sum(t['rr_iterations'] for t in trace),
        result_without_budget_sha256=hashed(numeric_without_budget(asdict(c))),profile=profile.record())

class Evaluator:
    def __init__(self,profile):self.profile=profile;self.calls=[]
    def __call__(self,s,bip,settings):
        if settings!=self.profile.settings:raise ValueError('Requested profile mismatch')
        c=PROVIDER.equilibrium_caloric_PT(s,bip,settings)
        d=c.equilibrium.diagnostics if c.equilibrium else None
        self.calls.append(dict(T=s.temperature_K,P=s.pressure_Pa_abs,z=list(s.composition.molar_fractions),status=c.status,
            equilibrium_iterations=d.iterations if d else 0,stability_iterations=d.stability.iterations if d and d.stability else 0,
            final_stability_iterations=d.equilibrium_stability.iterations if d and d.equilibrium_stability else 0,
            restarts=d.initialization.restart_count if d else 0,pt_settings=asdict(settings)))
        return c

def solve(spec,profile,kind):
    evaluator=Evaluator(profile);r=inverse(spec,BIP,profile,kind,evaluator)
    return r,dict(diagnostics=diagnostic(r),calls=evaluator.calls,PT_evaluations=len(evaluator.calls),
                  equilibrium_iterations=sum(c['equilibrium_iterations'] for c in evaluator.calls),profile=profile.record())

def endpoint(T,P,z,profile,parent=None):
    c=pt(T,P,z,profile)
    require(c.aggregate is not None,'fresh_PT','unresolved')
    require(c.equilibrium.overall_state==specification(T,P,z) and c.equilibrium.provenance.settings==profile.settings,'fresh_association')
    require(liquid(c),'phase_inadmissible','rejected')
    # The unchanged local guard retains its own legacy witness semantics explicitly.
    legacy_guard=local(c,BIP,parent)
    candidate_witness=None
    if not (parent and parent.equilibrium.classification=='vapor_liquid'):
        w=pt(T,P*.9999,z,profile);require(w.aggregate is not None and liquid(w),'candidate_witness','unresolved');candidate_witness=state(w)
    legacy=pt(T,P,z,Profile(100));require(legacy.aggregate is not None and liquid(legacy),'legacy_final_probe','unresolved')
    return c,dict(candidate=state(c),candidate_settings=asdict(profile.settings),candidate_witness=candidate_witness,
                  legacy_fresh=state(legacy),legacy_settings=asdict(Profile(100).settings),legacy_local=legacy_guard)

def resolved_source(name,sources):
    r=sources[name]['result']
    # Existing admitted graph supplies the unchanged actual liquid connection.
    f=build_flowsheet(requirements(name+'_DP1000000.0'))
    ctx=ExecutionContext(f,identity(r));sep,pump=f['equipment'];ctx.completed[sep['id']]=r
    link=next(c for c in f['connections'] if c['target']==dict(owner_id=pump['id'],port_id='inlet'))
    stream,evidence=ctx.resolve(pump,link)
    return stream,evidence,identity(r)

def chain(row,sources,profile):
    stream,source,current=resolved_source(row['source'],sources)
    a=verify(stream,source,current);z=a['z'];P1=stream['pressure_Pa_abs'];P2=row['P2'];eta=row['eta'];T=stream['temperature_K'];F=a['F_mol_s']
    out=dict(case_id=row['case_id'],source=row['source'],source_identity=current,profile=profile.record(),stage='inlet',status='pending',states={},diagnostics={},guards={},
             retained_upstream_Hdot_W=stream['enthalpy_flow_W'],component_rates=stream['component_mass_flow_kg_h'],F_mol_s=F,production_support=False)
    try:
        require(math.isfinite(P2) and P2>=P1 and math.isfinite(eta) and .6<=eta<=1,'input','rejected')
        parent_data=source['equipment'][0]['thermodynamics']['outlet'];parent=pt(T,P1,[parent_data['z'][k] for k in IDS],profile)
        c,eg=endpoint(T,P1,z,profile,parent);out['guards']['inlet']=eg
        h1,s1=c.aggregate.h_J_mol,c.aggregate.s_J_mol_K
        require(abs(h1-a['fresh']['H_eq_J_mol'])<=hb(h1) and abs(s1-a['fresh']['S_eq_J_mol_K'])<=1e-8+1e-11*abs(s1),'inlet_consistency')
        out['states']['inlet']=state(c)
        if P1==P2:
            out['states'].update(isentropic=state(c),outlet=state(c));out['outlet']=stream.copy();out['identity']=True
        else:
            out['stage']='PS';spec=PSSpecification(P2,s1,MolarComposition(IDS,tuple(z)),PROVENANCE)
            ps,rec=solve(spec,profile,'PS');out['diagnostics']['PS']=rec;out['guards']['PS']=guard(ps,spec,profile,'PS')
            require(ps.caloric.equilibrium.overall_state.pressure_Pa_abs==P2 and ps.caloric.equilibrium.overall_state.composition==spec.composition,'PS_association')
            b,eg=endpoint(ps.temperature_K,P2,z,profile);out['guards']['isentropic']=eg
            require(abs(b.aggregate.s_J_mol_K-s1)<=1e-8,'fresh_PS_residual');out['states']['isentropic']=state(b)
            target=h1+(b.aggregate.h_J_mol-h1)/eta;out['target_H_J_mol']=target;out['stage']='PH'
            spec=PHSpecification(P2,target,MolarComposition(IDS,tuple(z)),PROVENANCE)
            ph,rec=solve(spec,profile,'PH');out['diagnostics']['PH']=rec;out['guards']['PH']=guard(ph,spec,profile,'PH')
            require(ph.caloric.equilibrium.overall_state.pressure_Pa_abs==P2 and ph.caloric.equilibrium.overall_state.composition==spec.composition,'PH_association')
            c,eg=endpoint(ph.temperature_K,P2,z,profile);out['guards']['outlet']=eg
            require(abs(c.aggregate.h_J_mol-target)<=1e-6,'fresh_PH_residual');out['states']['outlet']=state(c)
            out['outlet']={k:v for k,v in stream.items() if k!='state_context'}
            out['outlet'].update(temperature_K=ph.temperature_K,pressure_Pa_abs=P2,enthalpy_flow_W=F*c.aggregate.h_J_mol)
            out['identity']=False
        i=dict(T1=T,P1=P1,P2=P2,z=z,eta=eta,flow=F);m=finish(i,out['states']);out['metrics']=m
        h1,hs,h2=[out['states'][k]['H_eq_J_mol'] for k in ('inlet','isentropic','outlet')]
        E=(hb(h1)+hb(hs))/eta+hb(h1)+hb(h2)+500e-8/eta+1e-6+ROUND*max(1,abs(h1),abs(hs),abs(h2))/eta
        if P2>P1:
            require(hs>h1 and h2>h1 and E/(h2-h1)<=1e-4,'work_resolution','rejected')
            require(abs(m['reconstructed_efficiency']-eta)<=eta*1e-6/(h2-h1)+ROUND,'efficiency')
            require(m['delta_s_J_mol_K']>=-2e-8,'entropy')
        W=m['W_recovered_W'];pumped=out['outlet']['enthalpy_flow_W'];original=stream['enthalpy_flow_W']
        pump_residual=math.fsum([pumped,-original,-W]);pump_allowance=a['enthalpy_allowance_W']+ROUND*max(1,abs(pumped),abs(original),abs(W))
        require(abs(pump_residual)<=pump_allowance,'pump_energy')
        unit=source['equipment'][0];d=unit['thermodynamics'];vapor=source['streams'][unit['material_streams']['vapor']]
        total=math.fsum([vapor['enthalpy_flow_W'],pumped,-d['inlet_enthalpy_flow_W'],-d['duty_W'],-W])
        allowance=d['energy_allowance_W']+pump_allowance+ROUND*max(1,abs(pumped),abs(vapor['enthalpy_flow_W']),abs(d['inlet_enthalpy_flow_W']))
        require(abs(total)<=allowance,'integrated_energy')
        require(out['outlet']['component_mass_flow_kg_h']==stream['component_mass_flow_kg_h'] and out['outlet']['mass_flow_kg_h']==stream['mass_flow_kg_h'],'mass')
        out.update(status='accepted_prototype',stage='complete',energy=dict(pump_residual_W=pump_residual,pump_allowance_W=pump_allowance,integrated_residual_W=total,integrated_allowance_W=allowance),work_budget_J_mol=E)
    except (ValueError,ArithmeticError) as e:out.update(status='failed',reason=str(e),error_type=type(e).__name__)
    return out
