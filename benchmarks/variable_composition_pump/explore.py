"""Independent exploratory boundary evidence, before choosing M19 candidate domain."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
q=EntropyPT();q.flash.DEW_BUBBLE_QUASI_NEWTON_XTOL=1e-12;q.flash.DEW_BUBBLE_NEWTON_XTOL=1e-12
rows=[]
for z in (0.,.01,.05,.1,.25,.5,.55,.6,.65,.75,.9,1.):
 for T in (300.,335.,370.):
  r=dict(z_methane=z,T_K=T)
  try:
   b=q.flash.flash(T=T,VF=0.,zs=[z,1-z]);w=q.evaluate(T,16e6,[z,1-z]);s=q.evaluate(T,20e6,[z,1-z])
   l,v=b.liquids[0],b.gas
   r.update(bubble_P=b.P,composition_gap=abs(v.zs[0]-l.zs[0]),Z_gap=abs(v.Z()-l.Z()),witness=w['classification'],actual=s['classification'])
  except Exception as e:r.update(error=type(e).__name__+': '+str(e))
  rows.append(r);print(r,flush=True)
assert not any(n.startswith('riogineer_engine') for n in sys.modules)
Path(__file__).with_name('exploration.json').write_text(json.dumps(rows,indent=2)+'\n')
