"""Independent follow-up to captured saturation precision/branch observations."""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from benchmarks.pump_energy.configurable_scope.policy import ROOT,HERE,REFERENCE
from benchmarks.pump_energy.common import encode,digest
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT
from scipy.optimize import brentq


def build():
    prior=json.loads(REFERENCE.read_text())
    oracle=EntropyPT()
    oracle.flash.DEW_BUBBLE_QUASI_NEWTON_XTOL=1e-12
    oracle.flash.DEW_BUBBLE_NEWTON_XTOL=1e-12
    rows=[]
    for old in prior['boundary']['rows']:
        T=old['T_K'];row=dict(T_K=T,original_status=old['status'])
        try:
            b=oracle.flash.flash(T=T,VF=0.,zs=[.5,.5])
            l,v=b.liquids[0],b.gas
            fug=[math.log(l.zs[j])+l.lnphis()[j]-math.log(v.zs[j])-v.lnphis()[j] for j in range(2)]
            row.update(status='available',P_bubble_Pa_abs=b.P,
                pressure_change_Pa=b.P-old['P_bubble_Pa_abs'],fugacity_residual=fug)
            # Targeted branch check only where unrestricted P->T selected another root.
            if abs(old.get('roundtrip_T_error_K',0.))>1e-5:
                def residual(t): return oracle.flash.flash(T=t,VF=0.,zs=[.5,.5]).P-b.P
                recovered=brentq(residual,T-.25,T+.25,xtol=1e-10,rtol=1e-14)
                row.update(original_inverse_T_K=T+old['roundtrip_T_error_K'],
                    local_branch_bracket_K=[T-.25,T+.25],local_branch_T_K=recovered,
                    local_branch_error_K=recovered-T)
        except Exception as e:
            row.update(status='reference_unavailable',reason=type(e).__name__+': '+str(e))
        rows.append(row)
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(reference_sha256=digest(REFERENCE),source_sha256=digest(__file__),
        reason='149 bubble-P precision checks and targeted inversions for four captured alternate-branch returns; original evidence unchanged',
        controls=dict(quasi_newton_xtol=1e-12,newton_xtol=1e-12),rows=rows,
        limitations='Local branch verification, not global uniqueness or a critical locus')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    raw=encode(build());path=HERE/'boundary_refinement.json'
    if args.write:path.write_text(raw)
    else:assert path.read_text()==raw,'Boundary refinement reproduction differs'
    print('PASS boundary refinement',digest(path))
