"""Independent extension oracle; production imports are prohibited."""
import argparse
import importlib.metadata
import inspect
import json
import math
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from benchmarks.pump_energy.configurable_scope.policy import HERE, ROOT, REFERENCE, cases, evaluate, P_WITNESS
from benchmarks.pump_energy.common import encode, digest, TOLS
from benchmarks.pump_energy.reference import calculate
from benchmarks.peng_robinson_ps.equilibrium import EntropyPT, TrialFailure
from benchmarks.peng_robinson_ps.solver import solve_ps
from benchmarks.peng_robinson_ph.solver import solve_ph
from benchmarks.peng_robinson_caloric import reference as caloric

OLD = ROOT/'benchmarks/pump_energy/liquid_pump_path_reference.json'
OLD_SHA = '6c0f7b33d9b4aea4ecd6b3f09bab70b22d46fa711a725bbfeab0cd3e63ad8f07'


def key(i):
    return tuple(i[k] for k in ('T1','P1','P2','eta','flow'))+tuple(i['z'])


def boundary(oracle):
    rows = []
    grid = [300+j*.5 for j in range(141)]
    holdouts = [301.137, 307.419, 313.863, 322.731, 329.053, 341.677, 354.311, 368.947]
    for T in grid+holdouts:
        row = dict(T_K=T, role='grid' if T in grid else 'holdout')
        try:
            b = oracle.flash.flash(T=T,VF=0.,zs=[.5,.5])
            reverse = oracle.flash.flash(P=b.P,VF=0.,zs=[.5,.5])
            l, v = b.liquids[0], b.gas
            fugacity = [math.log(l.zs[j])+l.lnphis()[j]-math.log(v.zs[j])-v.lnphis()[j] for j in range(2)]
            sides = [oracle.evaluate(T,b.P*f,[.5,.5]) for f in (.999,1.001)]
            witness = oracle.evaluate(T,P_WITNESS,[.5,.5])
            minus = oracle.flash.flash(T=T-.01,VF=0.,zs=[.5,.5]).P
            plus = oracle.flash.flash(T=T+.01,VF=0.,zs=[.5,.5]).P
            row.update(status='available', P_bubble_Pa_abs=b.P,
                roundtrip_T_error_K=reverse.T-T, fugacity_residual=fugacity,
                phase_composition_gap=abs(v.zs[0]-l.zs[0]), Z_gap=abs(v.Z()-l.Z()),
                derivative_Pa_K=(plus-minus)/.02,
                lower_phase=sides[0]['classification'], upper_phase=sides[1]['classification'],
                witness_phase=witness['classification'])
        except Exception as e:
            row.update(status='reference_unavailable', reason=type(e).__name__+': '+str(e))
        rows.append(row)
    valid = [r for r in rows if r['status']=='available']
    return dict(rows=rows, proposed_ceiling_Pa=16e6, grid_spacing_K=.5,
        engineering_slope_allowance_Pa_K=100000., nearest_node_allowance_Pa=25000.,
        numerical_allowance_Pa=1000.,
        sampled_max_bubble_Pa=max(r['P_bubble_Pa_abs'] for r in valid),
        observed_max_abs_derivative_Pa_K=max(abs(r['derivative_Pa_K']) for r in valid),
        caveat='Engineering enclosure supported by sampling and branch checks, not a proven derivative/global bound; runtime PT witness is mandatory')


def sensitivity(oracle, rows):
    """Independent perturbations of inverse targets at four limiting small rises."""
    out=[]
    for row in rows:
        if row['group'] != 'conditioning' or row['inputs']['P2']-row['inputs']['P1'] != 10000.:
            continue
        i,r=row['inputs'],row['result']
        if r['stage'] != 'complete':
            out.append(dict(case_id=row['case_id'], unavailable=r['status'])); continue
        a,b,c=[r['states'][k] for k in ('inlet','isentropic','outlet')]
        record=dict(case_id=row['case_id'], trials=[])
        for sign in (-1,1):
            ps=solve_ps(i['P2'],i['z'],a['S_eq_J_mol_K']+sign*1e-8,
                evaluator=oracle.evaluate,xtol=1e-12,direct=True)
            ph=solve_ph(i['P2'],i['z'],r['metrics']['h_target_J_mol']+sign*1e-6,
                evaluator=oracle.evaluate,xtol=1e-12,direct=True,method='bisect')
            q=dict(sign=sign, PS=ps, PH=ph)
            if ps['status']=='success':
                q['ps_dh_J_mol']=ps['solution']['H_eq_J_mol']-b['H_eq_J_mol']
            if ph['status']=='success':
                q['ph_dh_J_mol']=ph['solution']['H_eq_J_mol']-c['H_eq_J_mol']
            record['trials'].append(q)
        out.append(record)
    return out


def build():
    assert digest(OLD)==OLD_SHA
    old=json.loads(OLD.read_text())
    cached={key(c['inputs']):(c['result'],'prior:'+c['case_id']) for c in old['cases']}
    oracle=EntropyPT(); rows=[]
    for c in cases():
        k=key(c['inputs'])
        if k in cached:
            result,origin=cached[k]
        else:
            result=calculate(c['inputs'],oracle); origin='extension:'+c['case_id']
            cached[k]=(result,origin)
        witnesses={}
        for name,s in result['states'].items():
            try: witnesses[name]=oracle.evaluate(s['T_K'],P_WITNESS,[.5,.5])
            except TrialFailure: witnesses[name]=None
        policy=evaluate(c['inputs'],result,witnesses)
        rows.append(c|dict(result=result,witnesses=witnesses,policy=policy,evidence_origin=origin))
        print(c['case_id'],result['status'],policy['reason'],flush=True)
    bounds=boundary(oracle)
    perturbations=sensitivity(oracle,rows)
    sources=[Path(__file__),HERE/'policy.py',HERE/'PLAN.md']
    sources += [ROOT/'benchmarks'/p for p in ['pump_energy/common.py','pump_energy/reference.py',
        'peng_robinson_ps/equilibrium.py','peng_robinson_ps/solver.py',
        'peng_robinson_ph/equilibrium.py','peng_robinson_ph/solver.py',
        'peng_robinson_caloric/reference.py','peng_robinson_caloric/equations.py']]
    assert not any(n.startswith('riogineer_engine') for n in sys.modules)
    return dict(study='pre_m18_configurable_scope@1.0',baseline=old['baseline'],
        prior_reference_sha256=OLD_SHA, python=platform.python_version(),
        dependencies={n:importlib.metadata.version(n) for n in old['dependencies']},
        components=old['components'],cp_data=old['cp_data'],convention=old['convention'],kij=old['kij'],
        cp_source_sha256=digest(Path(caloric.hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv'),
        library_source_sha256={Path(inspect.getfile(o)).name:digest(inspect.getfile(o)) for o in
            (caloric.PR,caloric.PRMIX,caloric.CEOSGas,caloric.FlashVL,caloric.HeatCapacityGas)},
        source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sources},
        units=old['units'],tolerances=TOLS,cases=rows,boundary=bounds,sensitivity=perturbations,
        production_numerics_imported=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
    data=build();raw=encode(data)
    if args.write: REFERENCE.write_text(raw)
    else: assert REFERENCE.read_text()==raw,'Independent extension reproduction differs'
    print('PASS independent extension',len(data['cases']),'candidates',digest(REFERENCE))
