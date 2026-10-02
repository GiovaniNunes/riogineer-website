"""Implementation-era checks; frozen prerequisite baselines are not rewritten."""
import hashlib
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from riogineer_engine.core import build_flowsheet, calculate, Invalid, semantic_hash
from riogineer_engine.milestone20 import requirements
from riogineer_engine.separator_pump_scope import CASES, qualify
from riogineer_engine.separator_liquid_state import representation, identity, verify, Failure, evaluate, local, bip_from
from riogineer_engine.separator_liquid_pump import run
from riogineer_engine.separator_pump_process import ExecutionContext
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.low_pressure_separator_pump.phase_contract.negatives import cases as negatives
from benchmarks.m21_pt200.review import regression

class SeparatorPumpIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=json.loads((ROOT/'benchmarks/low_pressure_separator_pump/phase_contract/sources.json').read_text())['sources']
        cls.source=cls.sources['PH_FLASH']['result']

    def test_all30_fresh_evidence(self):
        # Archived results retain their original verified source identity.
        evidence=regression.archived_m20_semantics()
        self.assertEqual(evidence['failed_checks'],0)
        self.assertEqual({r['case_id'] for r in evidence['cases']},{r['qualification_id'] for r in CASES})
        for r in evidence['cases']:
            self.assertTrue(all(c['passed'] for c in r['checks']))
        # Current identity belongs to freshly calculated current results. The adapter
        # also checks all 30 cases against the frozen independent numerical oracle.
        current=regression.current_m20()
        self.assertEqual(current['comparison_count'],1680)
        self.assertEqual(current['failed_checks'],0)

    def test_27_source_contradictions(self):
        for row in negatives(self.source):
            with self.subTest(row['case_id']),self.assertRaises(Failure) as ctx:
                verify(row['stream'],row['source'],row['current'])
            self.assertEqual(ctx.exception.category,row['expected_category'])

    def test_roundtrip_and_received_coordinates(self):
        s=json.loads(json.dumps(representation(self.source)))
        s['temperature_K']+=1e-12
        a=verify(s,self.source,identity(self.source))
        self.assertEqual(a['fresh']['T_K'],s['temperature_K'])
        self.assertEqual(a['upstream_enthalpy_flow_W'],s['enthalpy_flow_W'])

    def test_identity_skips_inverse(self):
        s=representation(self.source)
        with patch('riogineer_engine.separator_liquid_pump.inverse',side_effect=AssertionError('inverse called')):
            r=run(s,self.source,identity(self.source),s['pressure_Pa_abs'],.8)
        self.assertEqual(r['outlet'],s);self.assertEqual(r['fluid_power_W'],0);self.assertIsNone(r['reconstructed_efficiency'])

    def test_execution_resolution(self):
        f=build_flowsheet(requirements());ctx=ExecutionContext(f,identity(self.source));pump=f['equipment'][1]
        link=next(c for c in f['connections'] if c['target']['owner_id']==pump['id'])
        with self.assertRaisesRegex(Failure,'upstream_not_completed'):ctx.resolve(pump,link)
        ctx.completed[f['equipment'][0]['id']]=deepcopy(self.source)
        ctx.completed[f['equipment'][0]['id']]['run_id']='stale'
        with self.assertRaisesRegex(Failure,'stale_execution'):ctx.resolve(pump,link)
        forged=deepcopy(link);forged['source']['port_id']='vapor'
        with self.assertRaises(Failure):ctx.resolve(pump,forged)

    def test_names_do_not_authorize(self):
        r=requirements();r['case_id']='DIFFERENT_DISPLAY';r['equipment'][1]['id']='OTHER_PUMP'
        for c in r['connections']:
            for side in ['source','target']:
                if c[side]['owner_id']=='PUMP_1':c[side]['owner_id']='OTHER_PUMP'
        self.assertEqual(qualify(build_flowsheet(r)),'PH_FLASH_DP1000000.0')
        r['feeds'][0]['state']['temperature_K']+=1e-5
        with self.assertRaisesRegex(Invalid,'unsupported_qualified_tuple'):build_flowsheet(r)

    def test_unsupported_and_injected_evidence(self):
        for change in ['pressure','efficiency','scale','topology','context','independent_H']:
            r=requirements()
            if change=='pressure':r['equipment'][1]['parameters']['outlet_pressure_Pa_abs']=8e6
            if change=='efficiency':r['equipment'][1]['parameters']['isentropic_efficiency']=.9
            if change=='scale':r['feeds'][0]['state']['component_mass_flow_kg_h']['methane']*=1.01
            if change=='topology':r['connections'][1]['target'],r['connections'][2]['target']=r['connections'][2]['target'],r['connections'][1]['target']
            if change=='context':r['feeds'][0]['state']['state_context']=representation(self.source)['state_context']
            if change=='independent_H':r['feeds'][0]['state']['enthalpy_flow_W']=0
            with self.subTest(change),self.assertRaises(Invalid):build_flowsheet(r)

    def test_stale_and_atomic_failure(self):
        f=build_flowsheet(requirements());f['requirements_sha256']='0'*64
        with self.assertRaisesRegex(Invalid,'stale'):calculate(f)
        f=build_flowsheet(requirements())
        with patch('riogineer_engine.separator_pump_process.run',side_effect=Failure('unresolved','test_inverse_failure')):
            with self.assertRaises(Invalid) as ctx:calculate(f)
        self.assertEqual(ctx.exception.payload['error']['code'],'M20_UNRESOLVED')
        self.assertNotIn('streams',ctx.exception.payload)

    def test_absent_vapor_bulk_vl(self):
        source=self.sources['PT_VAPOR']['result']
        with self.assertRaisesRegex(Failure,'absent_liquid'):verify(representation(source),source,identity(source))
        b=bip_from(representation(self.source)['state_context']['thermodynamics'])
        for T,P,z in [(350.,3e5,[.5,.5]),(500.,1e5,[.5,.5])]:
            with self.subTest(T=T),self.assertRaises(Failure) as ctx:local(evaluate(T,P,z,b),b)
            self.assertEqual(ctx.exception.category,'rejected')

    def test_small_exception_work_screen(self):
        r=requirements('SMALL1000.0');f=build_flowsheet(r)
        self.assertEqual(qualify(f),'SMALL1000.0')
        r['equipment'][1]['parameters']['isentropic_efficiency']=1.
        with self.assertRaises(Invalid):build_flowsheet(r)
        s=representation(self.source)
        with patch('riogineer_engine.separator_liquid_pump.hb',return_value=1e9):
            with self.assertRaisesRegex(Failure,'work_resolution'):run(s,self.source,identity(self.source),2e6,.8)

    def test_preservation(self):
        regression.preservation()
        regression.historical_integrity('M20')
        from benchmarks.m21_pt200.verify import source_verify
        source_verify()
        baseline=json.loads((ROOT/'benchmarks/m20_separator_pump/baseline.json').read_text())
        master=(ROOT/'docs/RIOGINEER_MASTER_CONTEXT.md').read_bytes()[:baseline['master_prefix_bytes']]
        self.assertEqual(hashlib.sha256(master).hexdigest(),baseline['sha256']['docs/RIOGINEER_MASTER_CONTEXT.md'])

if __name__=='__main__':unittest.main()
