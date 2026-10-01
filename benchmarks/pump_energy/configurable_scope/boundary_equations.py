"""Independent local coexistence residual check, never a pump-state root selector."""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from benchmarks.pump_energy.configurable_scope.policy import ROOT,HERE,REFERENCE
from benchmarks.pump_energy.common import encode,digest
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
from scipy.optimize import root


def build():
    prior=json.loads(REFERENCE.read_text());oracle=EntropyPT();rows=[]
    for old in prior['boundary']['rows']:
        T=old['T_K'];row=dict(T_K=T)
        try:
            b=oracle.flash.flash(T=T,VF=0.,zs=[.5,.5])
            def residual(v):
                P=math.exp(v[0]);y=1/(1+math.exp(-v[1]))
                l=oracle.flash.liquid.to(T=T,P=P,zs=[.5,.5])
                g=oracle.flash.gas.to(T=T,P=P,zs=[y,1-y])
                return [math.log(.5)+l.lnphis()[j]-math.log(g.zs[j])-g.lnphis()[j] for j in range(2)]
            y0=b.gas.zs[0]
            answer=root(residual,[math.log(b.P),math.log(y0/(1-y0))],tol=1e-11)
            P=math.exp(answer.x[0]);y=1/(1+math.exp(-answer.x[1]));f=residual(answer.x)
            # Require the same nontrivial local branch and independently stable sides.
            sides=[oracle.evaluate(T,P*v,[.5,.5])['classification'] for v in (.999,1.001)]
            accepted=(max(map(abs,f))<=2e-10 and abs(P-old['P_bubble_Pa_abs'])<=1000 and
                      y-.5>.3 and sides==['vapor_liquid','single_liquid'])
            row.update(status='accepted' if accepted else 'unresolved',P_bubble_Pa_abs=P,
                y_methane=y,fugacity_residual=f,library_pressure_difference_Pa=P-old['P_bubble_Pa_abs'],
                root_reported_success=bool(answer.success),sides=sides)
        except Exception as e:
            row.update(status='reference_unavailable',reason=type(e).__name__+': '+str(e))
        rows.append(row)
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(reference_sha256=digest(REFERENCE),source_sha256=digest(__file__),
        purpose='Check fixed-T bubble pressure by two log-fugacity equalities, with local-branch and stability checks; no metastable pump state accepted',
        pressure_comparison_allowance_Pa=1000.,fugacity_allowance=2e-10,rows=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
    path=HERE/'boundary_equations.json';raw=encode(build())
    if args.write:path.write_text(raw)
    else:assert path.read_text()==raw,'Boundary-equation reproduction differs'
    print('PASS boundary-equation artifact',digest(path))
