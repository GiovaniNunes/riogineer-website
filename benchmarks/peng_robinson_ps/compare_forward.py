"""Read-only existing production PT/caloric diagnostic; no production PS call."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.pr_eos import MODEL, BinaryInteractions
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.property_packages import property_package
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance


def compare():
    frozen=json.loads(Path(__file__).with_name('methane_nhexane_pr_ps_reference.json').read_text())
    provider=property_package(MODEL)
    bip=BinaryInteractions('prem13_diagnostic_zero',('methane','n_hexane'),((0.,0.),(0.,0.)),'Explicit zero diagnostic')
    rows=[]
    for c in frozen['cases']:
        f=c['forward']
        state=ThermodynamicState(f['T_K'],f['P_Pa_abs'],MolarComposition(bip.component_ids,tuple(f['z'])),StateSpecificationProvenance(MODEL,bip.identifier))
        for profile,settings in [('standard',SolverSettings()),('high_accuracy',SolverSettings.high_accuracy())]:
            r=provider.equilibrium_caloric_PT(state,bip,settings)
            checks=[]
            def check(field,a,b,kind):
                t=frozen['tolerances'][kind]; allowance=t['atol']+t['rtol']*abs(b)
                checks.append(dict(field=field,error=abs(a-b),allowance=allowance,passed=abs(a-b)<=allowance))
            if r.aggregate:
                assert r.equilibrium.classification==f['classification']
                check('S_eq',r.aggregate.s_J_mol_K,f['S_eq_J_mol_K'],'s')
                check('H_eq',r.aggregate.h_J_mol,f['H_eq_J_mol'],'h')
                check('beta',r.equilibrium.beta,f['beta'],'beta')
                for phase,p in zip(r.equilibrium.phases,r.phases):
                    q=f['phases'][phase.identifier]
                    check(phase.identifier+'.S',p.s_total_J_mol_K,q['s_J_mol_K'],'s')
                    check(phase.identifier+'.H',p.h_total_J_mol,q['h_J_mol'],'h')
                    check(phase.identifier+'.Z',phase.Z,q['Z'],'Z')
                    for i,(a,b) in enumerate(zip(phase.composition,q['composition'])):
                        check(phase.identifier+'.q'+str(i),a,b,'composition')
            rows.append(dict(case_id=c['case_id'],profile=profile,status=r.status,
                             passed=bool(checks) and all(x['passed'] for x in checks),checks=checks))
    return dict(kind='Diagnostic existing production entropy; independent PS truth unchanged',rows=rows,
                high_accuracy_passed=all(r['passed'] for r in rows if r['profile']=='high_accuracy'))


if __name__=='__main__':
    result=compare()
    print(json.dumps(result,indent=2,allow_nan=False))
    raise SystemExit(0 if result['high_accuracy_passed'] else 1)
