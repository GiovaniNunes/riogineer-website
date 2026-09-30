"""M13 production acceptance against immutable independent Pre-M13 evidence."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.pr_ps_flash import PSSpecification,PSSettings,flash_ps
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_eos import BinaryInteractions,MODEL
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolarComposition,StateSpecificationProvenance,ThermodynamicState

HERE=Path(__file__).resolve().parent
REFERENCE=HERE/'methane_nhexane_pr_ps_reference.json'
ARTIFACT=HERE/'production_comparison.json'
IDS=('methane','n_hexane')
BIP=BinaryInteractions('m13_explicit_zero@1.0',IDS,((0.,0.),(0.,0.)),'Explicit constant zero kij')
PROVENANCE=StateSpecificationProvenance(MODEL,BIP.identifier)


def read_reference():
    return json.loads(REFERENCE.read_text())


def specification(inputs):
    return PSSpecification(inputs['P'],inputs['S_target'],MolarComposition(IDS,tuple(inputs['z'])),PROVENANCE)


def evaluate(inputs):
    return PengRobinsonProvider().flash_PS(specification(inputs),BIP)


def payload(r):
    out=dict(status=r.status,capability=r.capability,diagnostics=asdict(r.diagnostics),
             temperature_K=r.temperature_K,entropy_residual_J_mol_K=r.entropy_residual_J_mol_K,
             provenance=asdict(r.provenance))
    if r.caloric is not None:
        c=r.caloric;p=c.equilibrium
        out['state']=dict(T_K=r.temperature_K,P_Pa_abs=r.specification.pressure_Pa_abs,
            S_target_J_mol_K=r.specification.entropy_J_mol_K,classification=p.classification,beta=p.beta,
            z=list(p.evaluated_molar_composition),S_eq=c.aggregate.s_J_mol_K,H_eq=c.aggregate.h_J_mol,
            phases={q.identifier:dict(composition=list(q.composition),Z=q.Z,S=v.s_total_J_mol_K,
                H=v.h_total_J_mol,s_ig=v.s_ig_J_mol_K,s_res=v.s_res_J_mol_K,
                h_ig=v.h_ig_J_mol,h_res=v.h_res_J_mol) for q,v in zip(p.phases,c.phases)})
    return out


def compare(reference,case,r):
    assert r.status=='success',(case['case_id'],r.status,r.diagnostics)
    expected=case['forward'];c=r.caloric;p=c.equilibrium;checks=[]
    def check(field,actual,value,kind):
        tol=reference['tolerances'][kind];allowance=tol['atol']+tol['rtol']*abs(value)
        checks.append(dict(field=field,production=actual,reference=value,absolute_error=abs(actual-value),
                           allowance=allowance,passed=abs(actual-value)<=allowance))
    assert p.classification==expected['classification']
    assert {q.identifier for q in p.phases}==set(expected['phases'])
    assert p.provenance.settings==SolverSettings.high_accuracy()
    assert r.capability=='flash_PS'
    assert len(r.diagnostics.brackets_K)==1 and r.diagnostics.trials[-1].stage=='final'
    assert sum(t.stage=='scan' for t in r.diagnostics.trials)==64
    assert all(t.status=='success' for t in r.diagnostics.trials)
    check('T',r.temperature_K,expected['T_K'],'T')
    check('S_residual',r.entropy_residual_J_mol_K,0.,'S_residual')
    check('S_eq',c.aggregate.s_J_mol_K,expected['S_eq_J_mol_K'],'s')
    check('H_eq',c.aggregate.h_J_mol,expected['H_eq_J_mol'],'h')
    check('beta',p.beta,expected['beta'],'beta')
    for phase,v in zip(p.phases,c.phases):
        e=expected['phases'][phase.identifier];suffix='L' if phase.identifier=='liquid' else 'V'
        for field,actual,key,kind in [('Z_',phase.Z,'Z','Z'),('S_',v.s_total_J_mol_K,'s_J_mol_K','s'),
            ('H_',v.h_total_J_mol,'h_J_mol','h'),('s_ig_',v.s_ig_J_mol_K,'s_ig_J_mol_K','s'),
            ('s_res_',v.s_res_J_mol_K,'s_res_J_mol_K','s'),('h_ig_',v.h_ig_J_mol,'h_ig_J_mol','h'),('h_res_',v.h_res_J_mol,'h_res_J_mol','h')]:
            check(field+suffix,actual,e[key],kind)
        for j,(a,b) in enumerate(zip(phase.composition,e['composition'])):
            check(('x' if suffix=='L' else 'y')+str(j),a,b,'composition')
    assert all(x['passed'] for x in checks),(case['case_id'],[x for x in checks if not x['passed']])
    # An additional forward call demonstrates consistency separately from inversion.
    fresh=PengRobinsonProvider().equilibrium_caloric_PT(p.overall_state,BIP,SolverSettings.high_accuracy())
    assert fresh==c
    check('fresh_S_residual',fresh.aggregate.s_J_mol_K,r.specification.entropy_J_mol_K,'S_residual')
    assert checks[-1]['passed']
    return checks


def negative(case):
    i=dict(case['specification']);synthetic=i.pop('synthetic',None)
    for key in ('P','S_target'):
        if isinstance(i[key],str):i[key]=float(i[key])
    ids=tuple(i.get('component_ids',IDS))
    b=BinaryInteractions(BIP.identifier,ids,i.get('kij',BIP.values),BIP.source)
    s=PSSpecification(i['P'],i['S_target'],MolarComposition(ids,tuple(i['z'])),PROVENANCE)
    settings=PSSettings(temperature_bounds_K=tuple(i.get('bounds',(200.,500.))),
                        scan_points=i.get('grid_points',64),max_iterations=i.get('maxiter',100))
    provider=PengRobinsonProvider()
    if synthetic:
        base=provider.equilibrium_caloric_PT(ThermodynamicState(300.,3e5,MolarComposition(IDS,(.5,.5)),PROVENANCE),BIP,SolverSettings.high_accuracy())
        def evaluator(state,bip,settings):
            T=state.temperature_K
            if synthetic=='hole' and 290<T<310:
                return CaloricResult('flash_not_converged',None,message='Synthetic property hole')
            S=(T-270)*(T-430) if synthetic=='multiple' else T-300
            return replace(base,aggregate=replace(base.aggregate,s_J_mol_K=S))
        return flash_ps(s,b,evaluator,settings)
    return provider.flash_PS(s,b,settings)


def build():
    ref=read_reference();rows=[];neg=[];maximum={}
    for c in ref['cases']:
        r=evaluate(c['input']);checks=compare(ref,c,r)
        for x in checks:
            key='x' if x['field'].startswith('x') else 'y' if x['field'].startswith('y') else x['field']
            if key not in maximum or x['absolute_error']>maximum[key]['absolute_error']:
                maximum[key]=dict(case_id=c['case_id'],**x)
        rows.append(dict(case_id=c['case_id'],production=payload(r),comparisons=checks,passed=True))
    for c in ref['negative_cases']:
        r=negative(c)
        assert r.status==c['expected_status'],(c['case_id'],r.status,c['expected_status'])
        assert r.caloric is None and r.temperature_K is None and r.entropy_residual_J_mol_K is None
        if c['case_id']=='PURE_COEXISTENCE_GAP':assert r.diagnostics.gap_detected
        neg.append(dict(case_id=c['case_id'],specification=c['specification'],expected_status=c['expected_status'],
                        status=r.status,accepted_state=False,diagnostics=asdict(r.diagnostics),passed=True))
    # Each representative independently repeats after each phase and each failure class.
    order=[]
    for prior in [*ref['cases'][:3],ref['negative_cases'][0],ref['negative_cases'][-1]]:
        if 'forward' in prior:evaluate(prior['input'])
        else:negative(prior)
        for c,baseline in zip(ref['cases'][:3],rows[:3]):
            assert payload(evaluate(c['input']))==baseline['production']
        order.append(prior['case_id'])
    return dict(reference_id=ref['reference_id'],reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        baseline_commit='06de73563c2262974be7df8638158262a9191e7d',provider=MODEL,
        positive_cases=rows,negative_cases=neg,maximum_errors=maximum,
        comparison_count=sum(len(r['comparisons']) for r in rows),passed=True,
        determinism=dict(representatives=[c['case_id'] for c in ref['cases'][:3]],after_cases=order,identical=True))


def display(report,selection):
    groups={'liquid':['A_LIQUID'],'two_phase':['B_VL'],'vapor':['C_VAPOR'],
        'bubble':['BUBBLE_BELOW','BUBBLE_ABOVE'],'dew':['DEW_BELOW','DEW_ABOVE'],
        'pure':['PURE_METHANE','PURE_HEXANE_LIQUID','PURE_HEXANE_VAPOR'],'near_zero':['NEAR_REFERENCE']}
    if selection not in ('summary','negative'):
        for row in report['positive_cases']:
            if row['case_id'] not in groups[selection]:continue
            p=row['production'];s=p['state'];d=p['diagnostics']
            print(row['case_id'], 'P=',s['P_Pa_abs'],'S_target=',s['S_target_J_mol_K'],'T=',s['T_K'],
                s['classification'],'beta=',s['beta'],'R_S=',p['entropy_residual_J_mol_K'],'H_eq=',s['H_eq'],
                'PT=high_accuracy','candidates=',len(d['brackets_K']),'bracket=',d['selected_bracket_K'],'PASS')
            print('field | production | reference | absolute error | allowance | result')
            for x in row['comparisons']:
                print(x['field'],x['production'],x['reference'],x['absolute_error'],x['allowance'],'PASS')
    if selection=='negative':
        for row in report['negative_cases']:
            print(row['case_id'],row['status'],'accepted state=no',row['diagnostics']['reason'],'PASS')
    if selection=='summary':
        for row in report['positive_cases']:
            p=row['production'];s=p['state']
            print(row['case_id'],s['P_Pa_abs'],s['S_target_J_mol_K'],s['T_K'],s['classification'],s['beta'],p['entropy_residual_J_mol_K'],s['H_eq'],'high_accuracy',len(p['diagnostics']['brackets_K']),'PASS')
        print('Maximum errors (quantity / case / absolute error / allowance):')
        for key,x in report['maximum_errors'].items():print(key,x['case_id'],x['absolute_error'],x['allowance'])
    print('PASS:',len(report['positive_cases']),'positive;',len(report['negative_cases']),'negative;',report['comparison_count'],'field comparisons; determinism/call order passed')
    print('Reference SHA256:',report['reference_sha256'])
    print('Human-operated M13 validation remains pending.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=['liquid','two_phase','vapor','bubble','dew','pure','near_zero','negative','summary'],default='summary')
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--verify',action='store_true',help='Require byte-identical saved production artifact')
    args=parser.parse_args();report=build();data=json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n'
    if args.verify:assert ARTIFACT.read_text()==data,'Production artifact differs'
    if args.write:ARTIFACT.write_text(data)
    display(report,args.case)


if __name__=='__main__':main()
