"""Independent M19 pump paths and composition-dependent coexistence evidence."""
from pathlib import Path
import sys,json,math,hashlib,argparse,importlib.metadata,platform
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.variable_composition_pump.cases import cases,input_reason
from benchmarks.pump_energy.reference import calculate
from benchmarks.pump_energy.common import encode,digest,liquid,TOLS
from benchmarks.pump_energy.configurable_scope.policy import work_policy
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
from scipy.optimize import root
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def boundary(q,z,T,role):
 r=dict(z_methane=z,T_K=T,role=role)
 try:
  zs=[z,1-z];b=q.flash.flash(T=T,VF=0.,zs=zs)
  def residual(v):
   P=math.exp(v[0]);y=1/(1+math.exp(-v[1]));l=q.flash.liquid.to(T=T,P=P,zs=zs);g=q.flash.gas.to(T=T,P=P,zs=[y,1-y])
   return [math.log(zs[j])+l.lnphis()[j]-math.log(g.zs[j])-g.lnphis()[j] for j in range(2)]
  y0=b.gas.zs[0];answer=root(residual,[math.log(b.P),math.log(y0/(1-y0))],tol=1e-11)
  P=math.exp(answer.x[0]);y=1/(1+math.exp(-answer.x[1]));res=residual(answer.x)
  sides=[q.evaluate(T,P*f,zs)['classification'] for f in (.999,1.001)]
  w=q.evaluate(T,16e6,zs);zgap=abs(b.gas.Z()-b.liquids[0].Z())
  dT=(q.flash.flash(T=T+.01,VF=0.,zs=zs).P-q.flash.flash(T=T-.01,VF=0.,zs=zs).P)/.02
  dz=(q.flash.flash(T=T,VF=0.,zs=[z+1e-5,1-z-1e-5]).P-q.flash.flash(T=T,VF=0.,zs=[z-1e-5,1-z+1e-5]).P)/2e-5
  ok=max(map(abs,res))<=2e-10 and abs(P-b.P)<=1000 and y-z>.30 and zgap>.24 and sides==['vapor_liquid','single_liquid'] and liquid(w) and abs(dT)<=1e5 and abs(dz)<=4e7
  r.update(status='accepted' if ok else 'unresolved',P_bubble=P,library_P=b.P,y_methane=y,Z_gap=zgap,residual=res,sides=sides,witness=w['classification'],dP_dT=dT,dP_dz=dz)
 except Exception as e:r.update(status='unavailable',reason=type(e).__name__+': '+str(e))
 return r

def build():
 old=json.loads((ROOT/'benchmarks/pump_energy/configurable_scope/reference.json').read_text());q=EntropyPT()
 q.flash.DEW_BUBBLE_QUASI_NEWTON_XTOL=1e-12;q.flash.DEW_BUBBLE_NEWTON_XTOL=1e-12
 rows=[]
 for c in cases():
  i=c['inputs'];r=calculate(i,q);w={}
  for k,s in r['states'].items():
   try:w[k]=q.evaluate(s['T_K'],16e6,i['z'])
   except Exception as e:w[k]=dict(error=str(e))
  reason=input_reason(i)
  if reason is None:
   if r['stage']!='complete':reason=r['status']
   elif any(not 300<=s['T_K']<=370 or not liquid(s) or not liquid(w[k]) for k,s in r['states'].items()):reason='state_or_witness'
   elif work_policy(i,r['states'])['status'] not in ('identity','resolved'):reason='work'
  rows.append(dict(c,result=r,witnesses=w,accepted=reason is None,reason=reason))
  print(c['case_id'],r['status'],reason,flush=True)
 bounds=[]
 for j in range(28):
  for k in range(29):bounds.append(boundary(q,.01+.02*j,300+2.5*k,'grid'))
  print('BOUNDARY_ROW',j,'failures',sum(r['status']!='accepted' for r in bounds),flush=True)
 for j in range(12):bounds.append(boundary(q,.01+.54*((j*.61803398875+.137)%1),300+70*((j*.41421356237+.731)%1),'holdout'))
 good=[r for r in bounds if r['status']=='accepted'];maximum=max(r['P_bubble'] for r in good)
 assert not any(n.startswith('riogineer_engine') for n in sys.modules)
 sources=[Path(__file__),HERE/'cases.py',HERE/'PLAN.md',ROOT/'benchmarks/pump_energy/reference.py',ROOT/'benchmarks/pump_energy/common.py',ROOT/'benchmarks/pump_energy/configurable_scope/policy.py']
 sources += [ROOT/'benchmarks'/s for s in ['peng_robinson_ps/equilibrium.py','peng_robinson_ps/solver.py','peng_robinson_ph/equilibrium.py','peng_robinson_ph/solver.py','peng_robinson_caloric/reference.py','peng_robinson_caloric/equations.py']]
 return dict(baseline='2a2f4cc9c3e827187af1d64be9f1773b23389618',production_imported=False,python=platform.python_version(),
  dependencies={n:importlib.metadata.version(n) for n in old['dependencies']},components=old['components'],cp_data=old['cp_data'],convention=old['convention'],kij=old['kij'],units=old['units'],tolerances=TOLS,
  library_source_sha256=old['library_source_sha256'],cp_source_sha256=old['cp_source_sha256'],
  source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sources},cases=rows,boundary=bounds,
  boundary_summary=dict(count=len(bounds),accepted=len(good),maximum_P=maximum,engineering_reserve_Pa=16e6-maximum-526000,not_a_global_bound=True))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();raw=encode(build());path=HERE/'reference.json'
 if a.write:path.write_text(raw)
 else:assert path.read_text()==raw,'Independent reproduction differs'
 print('Frozen reference',digest(path))
