"""Serial timings kept separate from byte-deterministic numerical evidence."""
import sys,argparse,time,statistics,platform
from pathlib import Path
from dataclasses import replace,asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'engine'))
from benchmarks.pt_iteration_budget.common import *
from benchmarks.pt_iteration_budget.harness import pt,chain,Profile,PROVIDER,specification,BIP
from riogineer_engine.pr_flash import SolverSettings

def cases():
    pts=pt_cases();selected=[next(r for r in pts if r['case_id']==n) for n in ('LIQUID','VAPOR','VL','PT_BUBBLE_BELOW_8000000.0_55_0.0','PT_BUBBLE_BELOW_8000000.0_56_0.0','HOLDOUT_2')]
    selected.append(dict(case_id='INVALID_PRESSURE',T=300.,P=-1.,z=[.5,.5]))
    rows=[dict(kind='PT',case_id=r['case_id'],inputs=r,caps=CAPS) for r in selected]
    rows.append(dict(kind='PT',case_id='CAP1_EXHAUSTION',inputs=dict(T=350.,P=3e5,z=[.5,.5]),caps=(1,)))
    for name in ('PH_FLASH','PT_BUBBLE_ABOVE_8000000.0'):
        c=next(r for r in chains() if r['case_id']==name);rows.append(dict(kind='chain',case_id=name,inputs=c,caps=CAPS))
    return rows

def evaluate(row,cap,sources):
    if row['kind']=='PT':
        i=row['inputs'];settings=replace(SolverSettings.high_accuracy(),flash_max_iterations=cap)
        c=PROVIDER.equilibrium_caloric_PT(specification(i['T'],i['P'],i['z']), BIP,settings)
        d=c.equilibrium.diagnostics if c.equilibrium else None
        return dict(status=c.status,equilibrium_iterations=d.iterations if d else 0,PT_evaluations=int(d is not None),property_evaluation_attempts=1,
                    stability_iterations=d.stability.iterations if d and d.stability else 0,
                    final_stability_iterations=d.equilibrium_stability.iterations if d and d.equilibrium_stability else 0,
                    restarts=d.initialization.restart_count if d else 0,has_payload=c.aggregate is not None,result_sha256=hashed(asdict(c)))
    r=chain(row['inputs'],sources,Profile(cap));calls=[q for d in r['diagnostics'].values() for q in d['calls']]
    return dict(status=r['status'],stage=r['stage'],equilibrium_iterations=sum(q['equilibrium_iterations'] for q in calls),PT_evaluations=len(calls),
        stability_iterations=sum(q['stability_iterations']+q['final_stability_iterations'] for q in calls),
        restarts=sum(q['restarts'] for q in calls),has_payload='outlet' in r,result_sha256=hashed(r),
        counts_scope='PS/PH evaluator calls; timing also includes context/inlet/final/local/balance guards')

def measure():
    sources=read(HERE/'sources.json');records=[]
    for row in cases():
        expected={cap:evaluate(row,cap,sources) for cap in row['caps']};samples={cap:[] for cap in row['caps']}
        for rep in range(3):
            order=list(row['caps']);order=order[rep%len(order):]+order[:rep%len(order)]
            for cap in order:
                start=time.perf_counter();value=evaluate(row,cap,sources);elapsed=time.perf_counter()-start
                assert value==expected[cap],(row['case_id'],cap,'deterministic work changed');samples[cap].append(elapsed)
        for cap in row['caps']:
            records.append(dict(case_id=row['case_id'],kind=row['kind'],cap=cap,deterministic=expected[cap],seconds=samples[cap],median_seconds=statistics.median(samples[cap])))
        print('timed',row['case_id'],flush=True)
    return dict(method='serial; no tracing; one warmup per case/profile; three repetitions; rotated profile order',python=platform.python_version(),platform=platform.platform(),timer=vars(time.get_clock_info('perf_counter')),records=records)

def verify():
    frozen=read(HERE/'performance.json');sources=read(HERE/'sources.json');by={c['case_id']:c for c in cases()}
    for row in frozen['records']:assert evaluate(by[row['case_id']],row['cap'],sources)==row['deterministic'],row['case_id']
    print('PASS performance deterministic work; stored timing samples intentionally not byte-reproduced')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--output');a=p.parse_args()
    if a.output:
        dest=Path(a.output);assert not dest.exists();dest.write_text(encode(measure()))
    elif a.write:save('performance.json',measure(),True)
    else:verify()
