"""Independent Thermo reference. Production outputs supply inputs, never expected values."""
import sys,argparse,inspect,importlib.metadata,platform,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.low_pressure_separator_pump.common import *
from benchmarks.pump_energy.reference import calculate,endpoint_boundaries
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
from benchmarks.peng_robinson_caloric import reference as caloric
from scipy.optimize import root

def safe(q,T,P,z):
    try:return q.evaluate(T,P,z)
    except Exception as e:return dict(error=type(e).__name__+': '+str(e))

def build():
    q=EntropyPT();screen=[]
    q.flash.DEW_BUBBLE_QUASI_NEWTON_XTOL=1e-12
    q.flash.DEW_BUBBLE_NEWTON_XTOL=1e-12
    for c in inventory():
        row=dict(case_id=c['case_id'])
        if 'z_methane' not in c:row['absent']=True;screen.append(row);continue
        i=specification(c);T,P,z=i['T1'],i['P1'],i['z']
        row['equilibrium']=safe(q,T,P,z)
        # Phase properties are independent diagnostics, NOT equilibrium or a fallback.
        row['phase_specific']=caloric.phase_record(T,P,z,'liquid',q.kw,q.cp)
        row['probes']=[dict(relative_offset=d,state=safe(q,T,P*(1+d),z)) for d in (-1e-3,-1e-6,-1e-9,0.,1e-9,1e-6,1e-3)]
        try:
            b=q.flash.flash(T=T,VF=0,zs=z);l=b.liquids[0];v=b.gas
            res=[math.log(z[j])+l.lnphis()[j]-math.log(v.zs[j])-v.lnphis()[j] for j in range(2)]
            sides=[safe(q,T,b.P*f,z) for f in (.999,1.001)]
            row['boundary']=dict(P_bubble=b.P,margin_Pa=P-b.P,y=v.zs,
                composition_gap=max(abs(a-bb) for a,bb in zip(z,v.zs)),Z_gap=abs(l.Z()-v.Z()),
                fugacity_residual=res,sides=[s.get('classification',s.get('error')) for s in sides])
            def residual(u):
                pressure=math.exp(u[0]);y=1/(1+math.exp(-u[1]))
                ll=q.flash.liquid.to(T=T,P=pressure,zs=z)
                vv=q.flash.gas.to(T=T,P=pressure,zs=[y,1-y])
                return [math.log(z[j])+ll.lnphis()[j]-math.log(vv.zs[j])-vv.lnphis()[j] for j in range(2)]
            ans=root(residual,[math.log(b.P),math.log(v.zs[0]/v.zs[1])],tol=1e-11)
            pressure=math.exp(ans.x[0]);y=1/(1+math.exp(-ans.x[1]))
            row['boundary']['refined']=dict(P_bubble=pressure,margin_Pa=P-pressure,
                y_methane=y,residual=residual(ans.x),library_difference_Pa=pressure-b.P,
                sides=[safe(q,T,pressure*f,z).get('classification') for f in (.999,1.001)])
        except Exception as e:row['boundary']=dict(error=type(e).__name__+': '+str(e))
        screen.append(row)
        print('SCREEN',c['case_id'],row['equilibrium'].get('classification'),flush=True)
    rows=[]
    for c in cases():
        if not .6<=c['inputs']['eta']<=1:r=dict(status='invalid_efficiency',stage='input',states={},diagnostics={})
        else:r=calculate(c['inputs'],q)
        p=policy(c['inputs'],r);rows.append(c|dict(result=r,policy=p));print(c['case_id'],p,flush=True)
    old=json.loads((ROOT/'benchmarks/variable_composition_pump/reference.json').read_text())
    actual={Path(inspect.getfile(o)).name:digest(inspect.getfile(o)) for o in (caloric.PR,caloric.PRMIX,caloric.CEOSGas,caloric.FlashVL,caloric.HeatCapacityGas)}
    assert actual==old['library_source_sha256']
    cp=digest(Path(caloric.hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv');assert cp==old['cp_source_sha256']
    versions={n:importlib.metadata.version(n) for n in old['dependencies']};assert versions==old['dependencies']
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    sources=[Path(__file__),HERE/'common.py',HERE/'PLAN.md',SOURCE]
    sources += [ROOT/p for p in old['source_sha256'] if 'low_pressure' not in p]
    return dict(production_imported=False,python=platform.python_version(),dependencies=versions,
        library_source_sha256=actual,cp_source_sha256=cp,
        source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sources if p.name not in ('compare.py','test_study.py')},
        **{k:old[k] for k in ('components','cp_data','convention','kij','units')},
        tolerances=TOLS,screen=screen,cases=rows,endpoint_boundaries=endpoint_boundaries(rows,q))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
    save('reference.json',build(),a.write)
