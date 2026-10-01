"""Independent frozen extension evidence -> unchanged public production providers."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from benchmarks.pump_energy.configurable_scope.policy import ROOT,HERE,REFERENCE,PRODUCTION,evaluate,P_WITNESS
from benchmarks.pump_energy.common import encode,digest,h_budget,MW
from benchmarks.pump_energy.compare_production import (calculate,compare,state,PengRobinsonProvider,
    ThermodynamicState,MolarComposition,PROVENANCE,BIP,IDS,SolverSettings)
from riogineer_engine.thermodynamics import MolecularCompositionProvider

OLD=ROOT/'benchmarks/pump_energy/production_comparison.json'
OLD_SHA='84c8d031f04a9d1da81cc0b787a4bcf33cf7a278d55e1f3b5ace9852f6f92a40'


def key(i):
    return tuple(i[k] for k in ('T1','P1','P2','eta','flow'))+tuple(i['z'])


def flow_checks(i,r,p):
    rows=[]
    for F in (5.,17.3,83.7,137.2,200.):
        rates={name:F*3.6*z*mw for name,z,mw in zip(IDS,i['z'],MW)}
        feed=dict(temperature_K=i['T1'],pressure_Pa_abs=i['P1'],mass_flow_kg_h=sum(rates.values()),component_mass_flow_kg_h=rates)
        m=MolecularCompositionProvider().enrich(feed).composition
        actual_F=m.molar_flow_kmol_h/3.6
        checks=[]
        def check(name,a,b,tol):
            checks.append(dict(field=name,actual=a,reference=b,error=abs(a-b),allowance=tol,passed=abs(a-b)<=tol))
        check('molar_flow',actual_F,F,1e-10)
        check('mass_flow',sum(rates.values())/3600,F*sum(z*mw/1000 for z,mw in zip(i['z'],MW)),1e-12)
        for name,z in zip(IDS,i['z']):
            check('z.'+name,m.molar_fractions[name],z,1e-12)
            check('component_molar.'+name,actual_F*m.molar_fractions[name],F*z,1e-10)
        for name in ('inlet','outlet'):
            rh=r['states'][name]['H_eq_J_mol'];ph=p['states'][name]['H_eq_J_mol']
            check(name+'.enthalpy_flow_W',actual_F*ph,F*rh,F*h_budget(rh)+1e-7)
        ref_delta=r['states']['outlet']['H_eq_J_mol']-r['states']['inlet']['H_eq_J_mol']
        prod_delta=p['states']['outlet']['H_eq_J_mol']-p['states']['inlet']['H_eq_J_mol']
        budget=F*(h_budget(r['states']['inlet']['H_eq_J_mol'])+h_budget(r['states']['outlet']['H_eq_J_mol']))
        check('power_W',actual_F*prod_delta,F*ref_delta,budget)
        # Reconstructed outlet keeps the independently checked component rates.
        outlet=feed|dict(temperature_K=p['states']['outlet']['T_K'],pressure_Pa_abs=i['P2'])
        out=MolecularCompositionProvider().enrich(outlet).composition
        check('molar_closure',out.molar_flow_kmol_h,m.molar_flow_kmol_h,0.)
        check('mass_closure',outlet['mass_flow_kg_h'],feed['mass_flow_kg_h'],0.)
        rows.append(dict(flow_mol_s=F,intensive_source='same calculated state, no repeat inversion',checks=checks))
    return rows


def build():
    frozen=json.loads(REFERENCE.read_text())
    assert digest(OLD)==OLD_SHA
    prior_ref=json.loads((ROOT/'benchmarks/pump_energy/liquid_pump_path_reference.json').read_text())
    prior_prod=json.loads(OLD.read_text())
    # Exact source compatibility is required before reusing captured calculations.
    for path,sha in prior_prod['production_source_sha256'].items(): assert digest(ROOT/path)==sha
    cached={key(r['inputs']):(p['result'],'prior:'+r['case_id']) for r,p in zip(prior_ref['cases'],prior_prod['cases'])}
    provider=PengRobinsonProvider();rows=[]
    for c in frozen['cases']:
        i=c['inputs'];k=key(i)
        if k in cached: result,origin=cached[k]
        else:
            result=calculate(i);origin='extension:'+c['case_id'];cached[k]=(result,origin)
        witnesses={}
        for name,s in result['states'].items():
            raw=provider.equilibrium_caloric_PT(ThermodynamicState(s['T_K'],P_WITNESS,MolarComposition(IDS,i['z']),PROVENANCE),BIP,SolverSettings.high_accuracy())
            witnesses[name]=state(raw) if raw.aggregate else None
        checks=compare(i,c['result'],result)
        policy=evaluate(i,result,witnesses)
        if 'metrics' in result and 'metrics' in c['result']:
            # Test runtime work policy against independent work discrepancies.
            error=abs(result['metrics']['delta_h_J_mol']-c['result']['metrics']['delta_h_J_mol'])
            allowance=policy.get('work',{}).get('budget_J_mol',0.)
            if policy['accepted']:
                checks.append(dict(field='runtime_work_policy_comparison',error=error,allowance=allowance,passed=error<=allowance))
        checks.append(dict(field='policy_agreement',actual=policy['accepted'],reference=c['policy']['accepted'],passed=policy['accepted']==c['policy']['accepted']))
        flows=flow_checks(i,c['result'],result) if policy['accepted'] and c['policy']['accepted'] else []
        rows.append(dict(case_id=c['case_id'],evidence_origin=origin,result=result,witnesses=witnesses,policy=policy,checks=checks,flow_checks=flows))
        print(c['case_id'],result['status'],policy['reason'],sum(not q['passed'] for q in checks),flush=True)
    allchecks=[q for r in rows for q in r['checks']]+[q for r in rows for f in r['flow_checks'] for q in f['checks']]
    return dict(reference_sha256=digest(REFERENCE),prior_production_sha256=OLD_SHA,
        source_sha256={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),HERE/'policy.py',ROOT/'benchmarks/pump_energy/compare_production.py']},
        production_source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'engine/riogineer_engine').glob('*.py'))},
        cases=rows,comparison_count=len(allchecks),failed_comparisons=sum(not q['passed'] for q in allchecks))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
    data=build();raw=encode(data)
    if args.write: PRODUCTION.write_text(raw)
    else: assert PRODUCTION.read_text()==raw,'Production extension reproduction differs'
    print('Comparisons',data['comparison_count'],'failed',data['failed_comparisons'])
    if data['failed_comparisons']: raise SystemExit(1)
