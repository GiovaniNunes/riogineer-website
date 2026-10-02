"""Finite M22 application boundaries, actual propagation and atomic failure."""
import json
import sys
import unittest
from copy import deepcopy
from dataclasses import replace,asdict
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from riogineer_engine.core import build_flowsheet,calculate,Invalid,semantic_hash,validate_requirements
from riogineer_engine.milestone22 import requirements
from riogineer_engine.milestone20 import requirements as historical
from riogineer_engine.separator_pump_scope import qualify,PT200_CASES
from riogineer_engine.separator_pump_process import ExecutionContext
from riogineer_engine.separator_liquid_state import Failure,representation,identity,verify
from riogineer_engine.numerical_profiles import PT200
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pump_energy import inverse,PumpFailure
from benchmarks.m22_separator_pump.verify import verify as integration,NAMES,PROFILE
from benchmarks.low_pressure_separator_pump.phase_contract.negatives import cases as negatives

class M22Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=integration()

    def test_independent_application_paths(self):
        self.assertEqual(self.evidence['failed_checks'],0)
        self.assertEqual(len(self.evidence['cases']),2)
        for row in self.evidence['cases']:
            r=row['result'];f=row['flowsheet'];s,p=r['equipment'];d=p['thermodynamics']['diagnostics']
            self.assertEqual(r['schema_version'],'1.15');self.assertEqual(p['model']['version'],'2.0')
            self.assertEqual(s['model']['version'],'1.0');self.assertEqual(r['input_sha256'],semantic_hash(f))
            self.assertEqual(p['thermodynamics']['numerical_profile'],PROFILE)
            self.assertEqual(d['numerics']['pump_settings'],asdict(PT200))
            for name,e in d['numerics']['endpoints'].items():
                self.assertEqual(e['selected_settings'],asdict(PT200))
                self.assertEqual(e['legacy_settings']['flash_max_iterations'],100)
            a=d['inlet'];self.assertEqual(a['stream']['enthalpy_flow_W'],a['upstream_enthalpy_flow_W'])
            self.assertEqual(a['source_identity'],{k:r[k] for k in ('run_id','input_sha256','requirements_sha256')})
            self.assertAlmostEqual(d['target_H_J_mol'],a['fresh']['H_eq_J_mol']+(d['isentropic']['H_eq_J_mol']-a['fresh']['H_eq_J_mol'])/.8,places=8)

    def test_exact_recipes_and_fixtures(self):
        old=json.loads((ROOT/'benchmarks/pt_iteration_budget/sources.json').read_text())
        from riogineer_engine.milestone17 import requirements as source
        for n,label in zip(NAMES,['below','above']):
            r=requirements(n)
            self.assertEqual(r,json.loads((ROOT/f'contracts/examples/milestone-22-{label}-requirements.json').read_text()))
            self.assertEqual(r['feeds'][0]['state'],source(**old[n]['inputs'])['feeds'][0]['state'])
            self.assertEqual(validate_requirements(r)['validation']['status'],'valid')

    def test_boundaries_and_conflicts(self):
        for name in NAMES:
            for change in ['legacy','omit','null','unknown','pt400','settings','old_model','old_schema','pressure','near_pressure','efficiency','scale','composition','temperature','separator_pressure','separator_profile','independent_H','context']:
                r=requirements(name);p=r['equipment'][1]['parameters'];feed=r['feeds'][0]['state']
                if change=='legacy':r=historical(name+'_DP1000000.0');r['equipment'][1]['parameters']['outlet_pressure_Pa_abs']=8e6
                if change=='omit':p.pop('numerical_profile')
                if change=='null':p['numerical_profile']=None
                if change=='unknown':p['numerical_profile']='unknown'
                if change=='pt400':p['numerical_profile']='pr_high_accuracy_pt400@1'
                if change=='settings':p['pt_settings']={'flash_max_iterations':100}
                if change=='old_model':r['equipment'][1]['model']['version']='1.0'
                if change=='old_schema':r['schema_version']='1.12'
                if change=='pressure':p['outlet_pressure_Pa_abs']=7e6
                if change=='near_pressure':p['outlet_pressure_Pa_abs']=8000000.000000001
                if change=='efficiency':p['isentropic_efficiency']=.8000000000000002
                if change=='scale':feed['component_mass_flow_kg_h']={k:v*1.001 for k,v in feed['component_mass_flow_kg_h'].items()}
                if change=='composition':feed['component_mass_flow_kg_h']['methane']*=1.001
                if change=='temperature':feed['temperature_K']+=1e-7
                if change=='separator_pressure':r['equipment'][0]['parameters']['separator_pressure_Pa_abs']+=1
                if change=='separator_profile':r['equipment'][0]['parameters']['numerical_profile']=PROFILE
                if change=='independent_H':feed['enthalpy_flow_W']=0
                if change=='context':feed['state_context']={'specification_kind':'upstream_derived'}
                with self.subTest(name=name,change=change),self.assertRaises(Invalid):build_flowsheet(r)
        r=historical();r['schema_version']='1.13';r['equipment'][1]['model']['version']='2.0';r['equipment'][1]['parameters']['numerical_profile']=PROFILE
        with self.assertRaises(Invalid):build_flowsheet(r)

    def test_labels_do_not_authorize(self):
        r=requirements();r['case_id']='DISPLAY_ONLY';r['equipment'][1]['id']='RENAMED'
        for c in r['connections']:
            for side in ['source','target']:
                if c[side]['owner_id']=='PUMP_1':c[side]['owner_id']='RENAMED'
        self.assertEqual(qualify(build_flowsheet(r)),PT200_CASES[0]['qualification_id'])

    def test_profile_identity_and_stale(self):
        f=build_flowsheet(requirements());old=semantic_hash(f)
        f['equipment'][1]['operating_parameters']['numerical_profile']='unknown'
        self.assertNotEqual(old,semantic_hash(f))
        with self.assertRaises(Invalid):calculate(f)
        f=build_flowsheet(requirements());f['requirements_sha256']='0'*64
        with self.assertRaisesRegex(Invalid,'stale'):calculate(f)

    def test_actual_source_contradictions(self):
        # The freshly executed private source, with original separator material fields.
        for row in self.evidence['cases']:
            r=deepcopy(row['result']);r['equipment']=r['equipment'][:1]
            sid=r['equipment'][0]['material_streams']['liquid']
            r['streams'][sid].pop('state_context')
            for n in negatives(r):
                # The historical mutation writes 0.5, which is unchanged for this source.
                if n['case_id']=='composition_changed':
                    n['stream']['properties']['molar_composition']['value']['methane']=.4
                with self.subTest(source=row['case_id'],mutation=n['case_id']),self.assertRaises(Failure):verify(n['stream'],n['source'],n['current'])

    def test_private_execution_tampering(self):
        f=build_flowsheet(requirements());row=self.evidence['cases'][0];r=row['result'];ctx=ExecutionContext(f,identity(r));pump=f['equipment'][1]
        link=next(c for c in f['connections'] if c['target']['owner_id']==pump['id'])
        with self.assertRaises(Failure):ctx.resolve(pump,link)
        ctx.completed[f['equipment'][0]['id']]=deepcopy(r)
        ctx.completed[f['equipment'][0]['id']]['input_sha256']='0'*64
        with self.assertRaisesRegex(Failure,'stale_execution'):ctx.resolve(pump,link)

    def test_controlled_ps_failure_no_fallback(self):
        real=PengRobinsonProvider.flash_PS;calls=[]
        def fail(provider,spec,bip,**kwargs):
            calls.append(kwargs)
            return replace(real(provider,spec,bip,**kwargs),status='property_evaluation_failed',caloric=None)
        with patch.object(PengRobinsonProvider,'flash_PS',fail),patch.object(PengRobinsonProvider,'flash_PH',side_effect=AssertionError('PH after failure')):
            with self.assertRaises(Invalid) as ctx:calculate(build_flowsheet(requirements()))
        self.assertEqual(calls,[{'numerical_profile':PROFILE}]);self.assertNotIn('streams',ctx.exception.payload)

    def test_wrong_inverse_profile_rejected(self):
        real=PengRobinsonProvider.flash_PS
        def forged(provider,spec,bip,**kwargs):
            r=real(provider,spec,bip,**kwargs)
            from riogineer_engine.pr_flash import SolverSettings
            return replace(r,diagnostics=replace(r.diagnostics,pt_settings=SolverSettings.high_accuracy()))
        with patch.object(PengRobinsonProvider,'flash_PS',forged):
            with self.assertRaisesRegex(Invalid,'inverse_controls'):calculate(build_flowsheet(requirements()))

if __name__=='__main__':unittest.main()
