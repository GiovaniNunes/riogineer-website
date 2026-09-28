"""Validation only: production PR versus immutable independent reference (no Thermo needed)."""
import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.pr_eos import BinaryInteractions, MODEL, PengRobinsonEOS, pure_parameters
from riogineer_engine.property_packages import property_package
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance

ARTIFACT = Path(__file__).with_name('methane_nhexane_pr_reference.json')


def compare_production(selected=None):
    ref=json.loads(ARTIFACT.read_text())
    ids=tuple(ref['component_order'])
    bip=BinaryInteractions('methane_nhexane_explicit_zero@1.0',ids,ref['kij'],
                           'Explicit zero-kij mathematical qualification specification; not calibrated physical data')
    rows=[]; results={}

    def check(name,actual,expected,quantity,tolerance=None):
        t=tolerance or ref['acceptance_tolerances'][quantity]
        absolute=abs(actual-expected)
        limit=t['atol']+t['rtol']*abs(expected)
        rows.append(dict(quantity=name,quantity_class=quantity,reference=expected,production=actual,
                         absolute_error=absolute,relative_error=absolute/abs(expected) if expected else None,
                         tolerance=t,allowed_absolute_error=limit,passed=absolute <= limit))

    def phase_checks(prefix,actual,expected):
        check(prefix+'.Z',actual.Z,expected['Z'],'Z_roots')
        for i in range(len(ids)):
            check(prefix+'.ln_phi.'+ids[i],actual.ln_phi[i],expected['ln_phi'][i],'ln_phi')
            t=ref['acceptance_tolerances']['ln_phi']; lp=expected['ln_phi'][i]
            # Frozen JSON specifies ln(phi), not a separate phi tolerance.
            # Propagate its exact bound through exp without changing the oracle.
            tolerance=dict(atol=expected['phi'][i]*math.expm1(t['atol']+t['rtol']*abs(lp)),rtol=0.)
            check(prefix+'.phi.'+ids[i],actual.phi[i],expected['phi'][i],'phi_from_ln_phi',tolerance)

    for p in ref['pure_parameters']['components']:
        actual=pure_parameters(p['id'],ref['pure_parameters']['T_K'])
        for attr,key in [('kappa','kappa'),('alpha','alpha'),('a','a_i_Pa_m6_mol2'),('b','b_i_m3_mol')]:
            check('pure.'+p['id']+'.'+attr,getattr(actual,attr),p[key],key)
    for c in ref['cases']:
        name=c['case_id']
        if selected and name != selected: continue
        eos=PengRobinsonEOS(ids,c['T_K'],c['P_Pa_abs'],bip)
        for key in ('homogeneous_mixture','mixture_at_x','mixture_at_y'):
            if key not in c: continue
            saved=c[key]; m=eos.mixture(saved['composition'])
            for attr,k,q in [('a','a_mix_Pa_m6_mol2','a_mix_Pa_m6_mol2'),('b','b_mix_m3_mol','b_mix_m3_mol'),('A','A','A_B'),('B','B','A_B')]:
                check(name+'.'+key+'.'+attr,getattr(m,attr),saved[k],q)
            check(name+'.'+key+'.root_count',len(m.roots),len(saved['physical_real_Z_roots']),'root_count',dict(atol=0,rtol=0))
            for i,(a,b) in enumerate(zip(m.roots,saved['physical_real_Z_roots'])):
                check(name+'.'+key+'.root.'+str(i),a,b,'Z_roots')
            for index,k in [(0,'smallest_real_root'),(-1,'largest_real_root')]:
                check(name+'.'+key+'.'+k,m.roots[index],saved[k],'Z_roots')
        for label,index in [('liquid',0),('vapor',-1)]:
            if label not in c: continue
            m=eos.mixture(c[label]['composition'])
            phase_checks(name+'.fixed_'+label,eos.fugacity(m,m.roots[index]),c[label])
        state=ThermodynamicState(c['T_K'],c['P_Pa_abs'],MolarComposition(ids,c['z']),StateSpecificationProvenance(MODEL,bip.identifier))
        result=property_package(MODEL).flash_PT(state,bip)
        results[name]=asdict(result)
        expected={'liquid':'single_liquid','vapor_liquid':'vapor_liquid','vapor':'single_vapor'}[c['classification']]
        rows.append(dict(quantity=name+'.classification',quantity_class='classification',reference=expected,
                         production=result.classification,absolute_error=None,relative_error=None,tolerance='exact',
                         passed=result.classification==expected and result.status.startswith('success_')))
        if not result.status.startswith('success_'): continue
        check(name+'.minimum_TPD',result.diagnostics.stability.minimum_tpd_RT,
              c['stability']['binary_TPD_scan']['refined_min_TPD_RT'],'stability_TPD_negative_threshold')
        check(name+'.beta',result.beta,c['beta'],'beta')
        for phase in result.phases:
            phase_checks(name+'.flash_'+phase.identifier,phase,c[phase.identifier])
            key='x' if phase.identifier=='liquid' else 'y'
            for i,(a,b) in enumerate(zip(phase.composition,c[phase.identifier]['composition'])):
                check(name+'.'+key+'.'+ids[i],a,b,key)
            check(name+'.sum_'+key,sum(phase.composition),1.,'composition_sum')
        if result.classification=='vapor_liquid':
            liquid,vapor=result.phases
            for i in range(len(ids)):
                x,y=liquid.composition[i],vapor.composition[i]
                dx=ref['acceptance_tolerances']['x']['atol']; dy=ref['acceptance_tolerances']['y']['atol']
                xr,yr=c['liquid']['composition'][i],c['vapor']['composition'][i]
                # K tolerance propagated from frozen x/y bounds; no new relaxed oracle.
                ktol=(yr+dy)/(xr-dx)-yr/xr
                check(name+'.K.'+ids[i],result.final_K[i],c['K'][i],'K_from_x_y',dict(atol=ktol,rtol=0))
                check(name+'.material.'+ids[i],(1-result.beta)*x+result.beta*y-c['z'][i],0.,'material_reconstruction')
                check(name+'.fugacity_residual.'+ids[i],math.log(x*liquid.phi[i])-math.log(y*vapor.phi[i]),0.,'ln_fugacity_equilibrium')
            rr=sum(z*(k-1)/(1+result.beta*(k-1)) for z,k in zip(c['z'],result.final_K))
            check(name+'.RR_residual',rr,0.,'rachford_rice')
    maxima={}
    for row in rows:
        if row['absolute_error'] is not None:
            q=row['quantity_class']; maxima[q]=max(maxima.get(q,0.),row['absolute_error'])
    return dict(reference_id=ref['benchmark_id'],provider=MODEL,passed=all(r['passed'] for r in rows),
                comparison_count=len(rows),maximum_absolute_errors=maxima,comparisons=rows,production_results=results)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=['A','B','C'],help='Omit to evaluate all three cases')
    parser.add_argument('--output',type=Path,help='Write comparison report (never the frozen reference)')
    args=parser.parse_args()
    report=compare_production(args.case)
    if args.output:
        if args.output.resolve()==ARTIFACT.resolve(): parser.error('Frozen independent reference is read-only')
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for name,result in report['production_results'].items():
        print('Case',name)
        print(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in report.items() if k not in ('production_results','comparisons')},indent=2))
    sys.exit(0 if report['passed'] else 1)
