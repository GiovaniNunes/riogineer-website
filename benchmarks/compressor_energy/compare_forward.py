"""READ-ONLY diagnostic composition of production PT/M10, PS/M13 and PH/M11.

This benchmark utility neither registers nor exposes a production compressor.
The immutable independent JSON is its sole reference authority.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.pr_eos import MODEL, BinaryInteractions
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.pr_ps_flash import PSSpecification
from riogineer_engine.pr_ph_flash import PHSpecification
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance

ARTIFACT=Path(__file__).with_name('methane_nhexane_compressor_reference.json')


def fields(caloric,T):
    result=dict(T=T,H=caloric.aggregate.h_J_mol,S=caloric.aggregate.s_J_mol_K,beta=caloric.equilibrium.beta)
    for p,c in zip(caloric.equilibrium.phases,caloric.phases):
        for label,value in [('Z',p.Z),('H',c.h_total_J_mol),('S',c.s_total_J_mol_K)]:result[p.identifier+'.'+label]=value
        for j,v in enumerate(p.composition):result[p.identifier+'.q'+str(j)]=v
    return result


def reference_fields(s):
    out=dict(T=s['T_K'],H=s['H_eq_J_mol'],S=s['S_eq_J_mol_K'],beta=s['beta'])
    for name,p in s['phases'].items():
        for label,key in [('Z','Z'),('H','h_J_mol'),('S','s_J_mol_K')]:out[name+'.'+label]=p[key]
        for j,v in enumerate(p['composition']):out[name+'.q'+str(j)]=v
    return out


def compare():
    raw=ARTIFACT.read_bytes();frozen=json.loads(raw)
    rows=[];maxima={};provider=PengRobinsonProvider()
    bip=BinaryInteractions('pre_m14_diagnostic_zero',('methane','n_hexane'),((0.,0.),(0.,0.)),'Explicit constant zero benchmark diagnostic')
    prov=StateSpecificationProvenance(MODEL,bip.identifier)
    for c in frozen['cases']+frozen['thermodynamic_studies']:
        i=c['inputs'];expected=c['result'];allow=c['allowances'];checks=[]
        composition=MolarComposition(bip.component_ids,tuple(i['z']))
        a=provider.equilibrium_caloric_PT(ThermodynamicState(i['T1'],i['P1'],composition,prov),bip,SolverSettings.high_accuracy())
        assert a.status in ('success_single_phase','success_two_phase') and a.aggregate is not None,(c['case_id'],'PT',a.status)
        ps=provider.flash_PS(PSSpecification(i['P2'],a.aggregate.s_J_mol_K,composition,prov),bip)
        assert ps.status=='success',(c['case_id'],'PS',ps.status,ps.diagnostics)
        hs=ps.caloric.aggregate.h_J_mol;h1=a.aggregate.h_J_mol
        target=h1+(hs-h1)/i['eta']
        ph=provider.flash_PH(PHSpecification(i['P2'],target,composition,prov),bip)
        assert ph.status=='success',(c['case_id'],'PH',ph.status,ph.diagnostics)
        for r in (ps,ph):
            assert r.diagnostics.pt_settings==SolverSettings.high_accuracy()
            assert len(r.diagnostics.brackets_K)==1 and r.diagnostics.trials[-1].stage=='final'
        def check(field,value,ref,tol):
            error=abs(value-ref)
            row=dict(field=field,production=value,reference=ref,absolute_error=error,allowance=tol,passed=math.isfinite(value) and error<=tol)
            checks.append(row)
            if field not in maxima or error>maxima[field]['absolute_error']:maxima[field]=dict(case_id=c['case_id'],**row)
        for stage,caloric,T in [('inlet',a,i['T1']),('isentropic',ps.caloric,ps.temperature_K),('outlet',ph.caloric,ph.temperature_K)]:
            assert caloric.equilibrium.classification==expected[stage]['classification'],(c['case_id'],stage,'phase mismatch')
            actual=fields(caloric,T);ref=reference_fields(expected[stage]);assert actual.keys()==ref.keys()
            for k,v in actual.items():check(stage+'.'+k,v,ref[k],allow[stage][k])
        h2=ph.caloric.aggregate.h_J_mol;power=i['flow']*(h2-h1);ispower=i['flow']*(hs-h1)
        check('H2_target',target,expected['H2_target_J_mol'],allow['H2_target'])
        check('fluid_power',power,expected['fluid_power_W'],allow['fluid_power'])
        check('isentropic_power',ispower,expected['isentropic_fluid_power_W'],allow['isentropic_power'])
        check('eta',(hs-h1)/(h2-h1),expected['reconstructed_eta'],allow['eta'])
        check('eta_power',ispower/power,expected['eta_power'],allow['eta'])
        check('PS_residual',ps.entropy_residual_J_mol_K,0.,frozen['tolerances']['PS_residual'])
        check('PH_residual',ph.enthalpy_residual_J_mol,0.,frozen['tolerances']['PH_residual'])
        residual=math.fsum([power,i['flow']*h1,-i['flow']*h2])
        roundoff=64*sys.float_info.epsilon*max(1.,abs(power),abs(i['flow']*h1),abs(i['flow']*h2))
        check('energy_residual',residual,0.,roundoff)
        rows.append(dict(case_id=c['case_id'],checks=checks,passed=all(x['passed'] for x in checks)))
    assert ARTIFACT.read_bytes()==raw
    return dict(kind='Diagnostic only; no production compressor',reference_sha256=hashlib.sha256(raw).hexdigest(),
                rows=rows,maxima=maxima,comparison_count=sum(len(r['checks']) for r in rows),passed=all(r['passed'] for r in rows))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',action='store_true');args=p.parse_args()
    result=compare()
    if args.json:print(json.dumps(result,indent=2,allow_nan=False))
    else:
        for k,v in result['maxima'].items():print(k,v['absolute_error'],'<=',v['allowance'],v['case_id'])
        print('PASS' if result['passed'] else 'FAIL',len(result['rows']),'cases;',result['comparison_count'],'diagnostic comparisons')
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
