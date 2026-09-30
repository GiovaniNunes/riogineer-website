"""Production equipment comparison against read-only independent Pre-M12 evidence."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'engine'))
from riogineer_engine.components import component
from riogineer_engine.heater_cooler_energy import heater, MODEL, ThermalFailure
from riogineer_engine.network_models import state_from_rates
from riogineer_engine.thermodynamics import MolecularCompositionProvider

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'methane_nhexane_heater_cooler_reference.json'
SHA256 = '55b01cbae648a64f20c5a6f331c6de1dd4b9ff2ff00a1497efe9ce4db99fd371'


def reference():
    raw = REFERENCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA256, 'Independent reference integrity failure'
    return json.loads(raw)


def inputs(F, Pin, Tin, Pout, z, *, Tout=None, Q=None, ids=('methane','n_hexane')):
    # Test-side unit conversion only. Equipment reconstructs F/z via M7.
    weights = [component(i).molecular_weight for i in ids]
    rates = {i: F * 3600. / 1000. * q * mw for i,q,mw in zip(ids,z,weights)}
    feed = state_from_rates(rates, Tin, Pin, None)
    if abs(sum(z)-1) > 1e-12:
        # No independently editable z exists in the process API. Represent the
        # malformed composition as an inconsistent total/component mass inventory.
        feed['mass_flow_kg_h'] = sum(rates.values()) / sum(z)
    p = dict(property_package='peng_robinson@1.0',
        bip=dict(identifier='explicit_zero@1.0', component_ids=list(ids), values=[[0.,0.],[0.,0.]],
                 source='Explicit zero-kij independent M8 benchmark; not fitted physical interaction data', model='peng_robinson@1.0'),
        outlet_pressure_Pa_abs=Pout)
    if Tout is not None:
        p.update(mode='specified_outlet_temperature', outlet_temperature_K=Tout)
    else:
        p.update(mode='specified_heat_duty', duty_W=Q)
    return dict(id='HEATER_1', type='heater', model=MODEL, operating_parameters=p), {'inlet': feed}


def compare_case(case, tolerances):
    s, frozen = case['specification'], case['mode_A']
    rows, modes = [], {}
    def check(name, actual, expected, allowance=0.):
        if isinstance(expected, (str, dict)) or expected is None:
            row = dict(field=name, actual=actual, reference=expected, passed=actual == expected)
        else:
            error = abs(actual-expected)
            row = dict(field=name, actual=actual, reference=expected, absolute_error=error,
                relative_error=error/abs(expected) if expected else None, allowance=allowance, passed=error <= allowance)
        rows.append(row)
        assert row['passed'], (s['case_id'], row)
    def allow(value, kind):
        t = tolerances[kind]
        return t['atol'] + t['rtol'] * abs(value)
    for mode in ('A','B'):
        unit, streams = inputs(s['F'],s['Pin'],s['Tin'],s['Pout'],s['z'],
                              **({'Tout':s['Tout']} if mode=='A' else {'Q':frozen['Q_W']}))
        result = heater(unit, streams)
        d = result.details['thermodynamics']
        modes[mode] = asdict(result)
        prefix = mode + '.'
        check(prefix+'F_in',d['F_mol_s'],s['F'],64*sys.float_info.epsilon*max(1,s['F']))
        reconstructed = MolecularCompositionProvider().enrich(result.streams['outlet']).composition
        check(prefix+'F_out',reconstructed.molar_flow_kmol_h*1000./3600.,s['F'],64*sys.float_info.epsilon*max(1,s['F']))
        check(prefix+'material',result.streams['outlet']['component_mass_flow_kg_h'],streams['inlet']['component_mass_flow_kg_h'])
        for side in ('inlet','outlet'):
            actual, expected = d[side], frozen[side]
            check(prefix+side+'.phase',actual['classification'],expected['classification'])
            check(prefix+side+'.P',actual['pressure_Pa_abs'],expected['P_Pa_abs'])
            check(prefix+side+'.T',actual['temperature_K'],expected['T_K'],allow(expected['T_K'],'T'))
            check(prefix+side+'.H',actual['H_eq_J_mol'],expected['H_eq_J_mol'],allow(expected['H_eq_J_mol'],'h'))
            check(prefix+side+'.beta',actual['beta'],expected['beta'],allow(expected['beta'],'beta'))
            for i,z in zip(('methane','n_hexane'),expected['z']):
                check(prefix+side+'.z.'+i,actual['z'][i],z,allow(z,'composition'))
            check(prefix+side+'.phase_count',len(actual['phases']),len(expected['phases']))
            for phase,p in expected['phases'].items():
                a = actual['phases'][phase]
                for field,kind in [('Z','Z'),('h_ig_J_mol','h'),('h_res_J_mol','h'),('h_J_mol','h')]:
                    check(prefix+side+'.'+phase+'.'+field,a[field],p[field],allow(p[field],kind))
                for i,z in zip(('methane','n_hexane'),p['composition']):
                    check(prefix+side+'.'+phase+'.composition.'+i,a['composition'][i],z,allow(z,'composition'))
        h_budget = sum(allow(frozen[side]['H_eq_J_mol'],'h') for side in ('inlet','outlet'))
        check(prefix+'delta_H',d['delta_H_J_mol'],frozen['delta_H_J_mol'],h_budget)
        # Propagate the frozen field-specific enthalpy allowance into duty;
        # the much smaller arithmetic budget governs closure, not model error.
        check(prefix+'Q',result.duty_W,frozen['Q_W'],s['F']*h_budget+case['forward_energy_allowance_W'])
        closure = case['forward_energy_allowance_W'] if mode=='A' else case['inverse_energy_allowance_W']
        check(prefix+'energy_closure',d['energy_residual_W'],0.,closure)
        if mode == 'B':
            check(prefix+'H_target',d['H_out_target_J_mol'],case['mode_B']['H_out_target_J_mol'],allow(frozen['inlet']['H_eq_J_mol'],'h'))
            check(prefix+'H_residual',d['ph']['enthalpy_residual_J_mol'],0.,tolerances['H_residual']['atol'])
    for field,kind in [('temperature_K','T'),('H_eq_J_mol','h'),('beta','beta')]:
        left,right=[modes[m]['details']['thermodynamics']['outlet'][field] for m in ('A','B')]
        check('mode_equivalence.'+field,left,right,allow(right,kind))
    left,right=[modes[m]['details']['thermodynamics']['outlet'] for m in ('A','B')]
    check('mode_equivalence.phase',left['classification'],right['classification'])
    for phase,p in right['phases'].items():
        for field,kind in [('Z','Z'),('h_J_mol','h')]:
            check('mode_equivalence.'+phase+'.'+field,left['phases'][phase][field],p[field],allow(p[field],kind))
        for i,z in p['composition'].items():
            check('mode_equivalence.'+phase+'.composition.'+i,left['phases'][phase]['composition'][i],z,allow(z,'composition'))
    return dict(case_id=s['case_id'],specification=s,modes=modes,comparisons=rows)


def build():
    ref = reference()
    cases = [compare_case(c,ref['tolerances']['inherited_independent_PH']) for c in ref['cases']]
    negatives = []
    for c in ref['negative_cases']:
        spec = c['specification']
        p = {k: float(v) if isinstance(v,str) and v in ('nan','inf') else v for k,v in spec['inputs'].items()}
        unit, streams = inputs(**p)
        try:
            heater(unit, streams)
        except ThermalFailure as error:
            expected = spec['expected_status']
            assert error.status == expected, (spec, error.status, expected)
            negatives.append(dict(case_id=spec['case_id'],specification=spec,status=error.status,stage=error.stage,accepted_outlet=False))
        else:
            raise AssertionError(('Negative case succeeded',spec))
    maxima = {}
    for case in cases:
        for row in case['comparisons']:
            if 'absolute_error' not in row: continue
            key = row['field']
            if key not in maxima or row['absolute_error'] > maxima[key]['absolute_error']:
                maxima[key] = dict(case_id=case['case_id'], **row)
    scaling = cases[10]['modes']['A']['duty_W']-2*cases[0]['modes']['A']['duty_W']
    assert scaling == 0., scaling
    repeated = []
    # Recheck both representative modes after every relevant call class.
    for label,index in [('heating',0),('cooling',1),('two_phase',8),('opposite_mode',0),('failed',None)]:
        if index is None:
            u,s=inputs(100.,1000.,300.,1000.,[.5,.5],Q=float('nan'))
            try: heater(u,s)
            except ThermalFailure: pass
            else: raise AssertionError('Failed-call isolation setup succeeded')
        else:
            spec=ref['cases'][index]['specification']
            u,s=inputs(spec['F'],spec['Pin'],spec['Tin'],spec['Pout'],spec['z'],
                **({'Q':ref['cases'][index]['mode_A']['Q_W']} if label=='opposite_mode' else {'Tout':spec['Tout']}))
            heater(u,s)
        for mode in ('A','B'):
            spec=ref['cases'][0]['specification']
            u,s=inputs(spec['F'],spec['Pin'],spec['Tin'],spec['Pout'],spec['z'],
                **({'Tout':spec['Tout']} if mode=='A' else {'Q':ref['cases'][0]['mode_A']['Q_W']}))
            assert asdict(heater(u,s)) == cases[0]['modes'][mode], (label,mode,'Non-deterministic result')
        repeated.append(dict(after=label,both_modes_identical=True))
    return dict(reference_id=ref['reference_id'],reference_sha256=SHA256,model=MODEL,cases=cases,negative_cases=negatives,
                comparison_count=sum(len(c['comparisons']) for c in cases),maximum_errors=maxima,
                scaling_error_W=scaling,determinism=repeated)



def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write',action='store_true')
    p.add_argument('--case',default='summary',choices=['summary','representative','mode_a','mode_b','transitions','zero','scaling','pressure','negative'])
    args=p.parse_args(); report=build()
    if args.write:
        (HERE/'production_comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    selected = {
        'representative': ['LIQUID_TO_TWO_PHASE'], 'mode_a': ['LIQUID_TO_TWO_PHASE'],
        'mode_b': ['LIQUID_TO_TWO_PHASE'], 'zero': ['ZERO_DUTY'],
        'scaling': ['VAPOR_HEATING','VAPOR_HEATING_DOUBLE_FLOW'], 'pressure': ['SPECIFIED_OUTLET_PRESSURE'],
        'transitions': ['LIQUID_TO_TWO_PHASE','TWO_PHASE_TO_VAPOR','VAPOR_TO_TWO_PHASE','TWO_PHASE_TO_LIQUID'],
    }.get(args.case)
    if args.case == 'negative':
        for n in report['negative_cases']: print(n['case_id'],n['status'],'no accepted outlet','PASS')
    else:
        for c in report['cases']:
            if selected is not None and c['case_id'] not in selected: continue
            for mode,r in c['modes'].items():
                if args.case=='mode_a' and mode!='A' or args.case=='mode_b' and mode!='B': continue
                d=r['details']['thermodynamics']
                print(c['case_id'], mode, d['mode'], 'F=',d['F_mol_s'],'mol/s',
                      'inlet=',d['inlet']['temperature_K'],'K',d['inlet']['pressure_Pa_abs'],'Pa',d['inlet']['classification'],
                      'outlet=',d['outlet']['temperature_K'],'K',d['outlet']['pressure_Pa_abs'],'Pa',d['outlet']['classification'])
                print('  H_in=',d['inlet']['H_eq_J_mol'],'H_out=',d['outlet']['H_eq_J_mol'],
                      'delta_H=',d['delta_H_J_mol'],'J/mol; Q=',d['Q_W'],'W;',
                      'R_Q=',d['energy_residual_W'],'allowance=',d['energy_allowance_W'],'W PASS')
                if d['ph']: print('  H_target=',d['H_out_target_J_mol'],'J/mol; M11',d['ph'])
                for row in c['comparisons']:
                    if row['field'] in (mode+'.outlet.T', mode+'.Q', mode+'.outlet.H'):
                        print(' ',row['field'],'production=',row['actual'],'reference=',row['reference'],
                              'error=',row['absolute_error'],'allowance=',row['allowance'],'PASS')
    print('PASS:',len(report['cases']),'positive;',len(report['negative_cases']),'negative;',report['comparison_count'],'comparisons')
    print('Scaling error W:',report['scaling_error_W'],'; both-mode determinism and call-order checks passed')
    print('Human-operated M12 validation remains pending.')


if __name__=='__main__': main()
