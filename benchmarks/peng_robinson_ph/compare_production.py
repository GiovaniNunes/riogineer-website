"""Production PH acceptance against immutable independent evidence; no reference imports."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.pr_eos import BinaryInteractions, MODEL
from riogineer_engine.pr_ph_flash import PHSpecification, PHSettings
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolarComposition, StateSpecificationProvenance

HERE=Path(__file__).resolve().parent
REFERENCE=HERE/'methane_nhexane_pr_ph_reference.json'
REFERENCE_SHA256='e311738a66d7bedd37fe802f9b69297b35bf8f18aeb6e14eedd9a366af56a3b3'


def read_reference():
    raw=REFERENCE.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=REFERENCE_SHA256:raise ValueError('Frozen PH integrity mismatch')
    r=json.loads(raw)
    if r['reference_id']!='independent_methane_nhexane_pr_ph@1.0' or len(r['cases'])!=29 or len(r['negative_cases'])!=8:
        raise ValueError('Frozen matrix identity/coverage mismatch')
    return r


def evaluate(r,P,H,z,ids=('methane','n_hexane'),bounds=(200.,500.),maxiter=100):
    ids=tuple(ids)
    bip=BinaryInteractions('explicit_zero@1.0',ids,tuple(tuple(0. for _ in ids) for _ in ids),r['metadata']['BIP_provenance'])
    spec=PHSpecification(P,H,MolarComposition(ids,tuple(z)),StateSpecificationProvenance(MODEL,bip.identifier))
    return PengRobinsonProvider().flash_PH(spec,bip,PHSettings(tuple(bounds),max_iterations=maxiter))


def compare(r,case,result):
    e=case['inverse']['solution']; checks=[]
    def equal(name,a,b):checks.append(dict(quantity=name,actual=a,reference=b,passed=a==b))
    def number(name,a,b,key):
        t=r['tolerances'][key];error=abs(a-b);allow=t['atol']+t['rtol']*abs(b)
        checks.append(dict(quantity=name,actual=a,reference=b,absolute_error=error,
            relative_error=error/abs(b) if b else None,allowed_error=allow,passed=error<=allow))
    equal('status',result.status,'success')
    if result.status!='success':return checks
    c=result.caloric;pt=c.equilibrium
    equal('phase',pt.classification,e['classification'])
    equal('profile',pt.provenance.settings.profile.value,'high_accuracy')
    equal('phase identities',sorted(p.identifier for p in pt.phases),sorted(e['phases']))
    number('T',result.temperature_K,e['T_K'],'T')
    number('H_residual',result.enthalpy_residual_J_mol,0.,'H_residual')
    number('H_eq',c.aggregate.h_J_mol,e['H_eq_J_mol'],'h')
    number('beta',pt.beta,e['beta'],'beta')
    caloric={p.phase_identifier:p for p in c.phases}
    for phase in pt.phases:
        label=phase.identifier;expected=e['phases'][label]
        number(label+'.Z',phase.Z,expected['Z'],'Z')
        number(label+'.h',caloric[label].h_total_J_mol,expected['h_J_mol'],'h')
        for j,v in enumerate(phase.composition):number(label+'.q'+str(j),v,expected['composition'][j],'composition')
    equal('final evaluation fresh',result.diagnostics.trials[-1].stage,'final')
    return checks


def build():
    r=read_reference();positive=[];negative=[];all_checks=[];maxima={}
    for case in r['cases']:
        i=case['input'];p=evaluate(r,i['P_Pa_abs'],i['H_target_J_mol'],i['z'],bounds=i['T_bounds_K'])
        checks=compare(r,case,p)
        failures=[c for c in checks if not c['passed']]
        if failures:raise AssertionError(json.dumps(dict(case_id=case['case_id'],input=i,failures=failures,result=asdict(p)),indent=2))
        all_checks.extend(checks)
        for c in checks:
            if 'absolute_error' not in c:continue
            q=c['quantity'];m=maxima.setdefault(q,dict(absolute_error=-1.,relative_error=None,case_id=None,relative_case_id=None))
            if c['absolute_error']>m['absolute_error']:m.update(absolute_error=c['absolute_error'],case_id=case['case_id'],allowance=c['allowed_error'])
            if c['relative_error'] is not None and (m['relative_error'] is None or c['relative_error']>m['relative_error']):m.update(relative_error=c['relative_error'],relative_case_id=case['case_id'])
        positive.append(dict(case_id=case['case_id'],input=i,reference_temperature_K=case['inverse']['solution']['T_K'],
                             result=asdict(p),comparisons=checks,workload=dict(Counter(t.stage for t in p.diagnostics.trials))))
    specs=list(r['negative_cases'])
    gap=r['pure_saturation_gap']
    specs.append(dict(case_id='PURE_COEXISTENCE_GAP',expected_status=gap['inversion']['status'],
                      inputs=dict(P=gap['P_Pa_abs'],H_target=gap['excluded_target_J_mol'],z=[0.,1.])))
    for case in specs:
        i=case['inputs'];p=evaluate(r,i['P'],i['H_target'],i['z'],i.get('component_ids',('methane','n_hexane')),i.get('bounds',(200.,500.)),i.get('maxiter',100))
        expected=case['expected_status']
        # Existing production validation uses plural; independent singular is equivalent.
        mapped='unsupported_component' if p.status=='unsupported_components' else p.status
        ok=mapped==expected and p.caloric is None and p.temperature_K is None and p.enthalpy_residual_J_mol is None
        if not ok:raise AssertionError(json.dumps(dict(case_id=case['case_id'],expected=expected,result=asdict(p)),indent=2))
        negative.append(dict(case_id=case['case_id'],input=i,expected_status=expected,result=asdict(p),passed=True))
    return dict(reference_id=r['reference_id'],reference_sha256=REFERENCE_SHA256,positive_cases=positive,
                negative_cases=negative,comparisons=len(all_checks),maxima=maxima,passed=True)


def display(e,selected):
    aliases={'A':'PH_A_SINGLE_LIQUID','B':'PH_B_VAPOR_LIQUID','C':'PH_C_SINGLE_VAPOR','bubble':'PH_BUBBLE_ABOVE',
             'dew':'PH_DEW_BELOW','near_zero':'PH_NEAR_ZERO_H','pure':'PH_PURE_N_HEXANE_300K_1000PA'}
    chosen=aliases.get(selected,selected)
    print('Case / P Pa / H target J/mol / T reference K / T PH K / abs T error / phase / H residual J/mol / result')
    for c in e['positive_cases']:
        if selected not in ('all','summary') and c['case_id']!=chosen:continue
        p=c['result'];pt=p['caloric']['equilibrium'];i=c['input']
        print(c['case_id'],i['P_Pa_abs'],i['H_target_J_mol'],c['reference_temperature_K'],p['temperature_K'],abs(p['temperature_K']-c['reference_temperature_K']),pt['classification'],p['enthalpy_residual_J_mol'],'PASS')
        if selected not in ('all','summary','negative'):
            print('beta:',pt['beta'],'profile:',p['diagnostics']['pt_settings']['profile'],'workload:',c['workload'],'brackets:',p['diagnostics']['brackets_K'])
            for check in c['comparisons']:
                if 'absolute_error' in check:print(check['quantity'],'production',check['actual'],'reference',check['reference'],'abs error',check['absolute_error'],'allowance',check['allowed_error'],'PASS')
    if selected in ('all','negative'):
        for c in e['negative_cases']:print(c['case_id'],c['result']['status'],c['result']['diagnostics']['reason'],'no accepted payload: PASS')
    print('PASS:',len(e['positive_cases']),'positive,',len(e['negative_cases']),'negative/gap;',e['comparisons'],'positive field comparisons')
    print('Human-operated M11 validation remains pending.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',default='summary',choices=['A','B','C','bubble','dew','near_zero','pure','summary','negative','all'])
    parser.add_argument('--write',action='store_true',help='Write production artifact only')
    args=parser.parse_args();e=build();display(e,args.case)
    if args.write:(HERE/'production_comparison.json').write_text(json.dumps(e,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
