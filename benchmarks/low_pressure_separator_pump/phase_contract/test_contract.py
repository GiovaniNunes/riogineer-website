"""Focused executable contract, failure-atomicity, guard and evidence tests."""
import json,sys,unittest,subprocess,os
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[3]));sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'engine'))
from benchmarks.low_pressure_separator_pump.phase_contract.common import *
from benchmarks.low_pressure_separator_pump.phase_contract import adapter as a
from benchmarks.low_pressure_separator_pump.phase_contract.negatives import cases
from benchmarks.low_pressure_separator_pump.phase_contract.pump import run

class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=read(HERE/'sources.json')['sources'];cls.base=cls.sources['PH_FLASH']['result']
        cls.art=read(HERE/'production.json')
    def test_actual_stream_untouched(self):
        for key,r in self.sources.items():
            r=r['result'];s=a.representation(r);e=r['equipment'][0]
            self.assertEqual({k:v for k,v in s.items() if k!='state_context'},r['streams'][e['material_streams']['liquid']])
            if key=='PT_VAPOR':continue
            result=a.verify(s,r,a.identity(r))
            self.assertEqual(result['stream'],s)
            self.assertEqual(result['upstream_enthalpy_flow_W'],s['enthalpy_flow_W'])
    def test_negative_contracts(self):
        for c in cases(self.base):
            with self.subTest(c=c['case_id']),self.assertRaises(a.Failure) as failure:
                a.verify(c['stream'],c['source'],c['current'])
            self.assertEqual(failure.exception.category,c['expected_category'])
    def test_roundoff_without_snapping(self):
        for name in ('PH_FLASH','PT_BUBBLE_BELOW','PT_DEW_BELOW'):
            r=self.sources[name]['result'];s=a.representation(r)
            for k,v in s['component_mass_flow_kg_h'].items():s['component_mass_flow_kg_h'][k]=float(format(v,'.15g'))
            for k in ('temperature_K','pressure_Pa_abs'):s[k]=float(format(s[k],'.15g'))
            s['mass_flow_kg_h']=float(format(s['mass_flow_kg_h'],'.15g'))
            s['enthalpy_flow_W']=float(format(s['enthalpy_flow_W'],'.15g'))
            s=json.loads(json.dumps(s));before=deepcopy(s)
            out=a.verify(s,r,a.identity(r));self.assertEqual(out['stream'],before);self.assertEqual(s,before)
    def test_identity_does_not_call_inverses(self):
        s=a.representation(self.base)
        with patch.object(a.PengRobinsonProvider,'flash_PS',side_effect=AssertionError('identity PS')),patch.object(a.PengRobinsonProvider,'flash_PH',side_effect=AssertionError('identity PH')):
            out=run(s,self.base,a.identity(self.base),s['pressure_Pa_abs'],.8)
        self.assertEqual(out['outlet'],s);self.assertEqual(out['fluid_power_W'],0);self.assertIsNone(out['reconstructed_efficiency'])
    def test_source_failure_has_no_outlet(self):
        s=a.representation(self.base)
        with patch.object(a.PengRobinsonProvider,'equilibrium_caloric_PT',side_effect=a.Failure('unresolved','synthetic_PT_failure')):
            with self.assertRaises(a.Failure) as e:run(s,self.base,a.identity(self.base),2e6,.8)
        self.assertEqual(e.exception.category,'unresolved')
    def test_source_absence_and_false_saturation(self):
        r=self.sources['PT_VAPOR']['result']
        with self.assertRaises(a.Failure) as e:a.verify(a.representation(r),r,a.identity(r))
        self.assertEqual(e.exception.code,'absent_liquid')
        r=self.sources['PT_BUBBLE_BELOW']['result'];s=a.representation(r);s['state_context']['saturation']='source_vle'
        with self.assertRaises(a.Failure) as e:a.verify(s,r,a.identity(r))
        self.assertEqual(e.exception.code,'false_saturation')
    def test_vapor_and_bulk_VL(self):
        bip=a.bip_from(a.representation(self.base)['state_context']['thermodynamics'])
        for T,P in ((300.,1000.),(300.,3e5)):
            c=a.evaluate(T,P,[.5,.5],bip)
            with self.assertRaises(a.Failure) as e:a.local(c,bip)
            self.assertEqual(e.exception.category,'rejected')
    def test_ambiguous_and_failed_local_evidence(self):
        r=self.sources['PT_BUBBLE_BELOW']['result'];s=a.representation(r);bip=a.bip_from(s['state_context']['thermodynamics'])
        c=a.evaluate(s['temperature_K'],s['pressure_Pa_abs'],[.5,.5],bip)
        with patch('benchmarks.low_pressure_separator_pump.phase_contract.adapter.evaluate',side_effect=a.Failure('unresolved','synthetic_witness_failure')):
            with self.assertRaises(a.Failure) as e:a.local(c,bip)
        self.assertEqual(e.exception.category,'unresolved')
    def test_all_frozen_checks_and_original_tuples(self):
        self.assertEqual(self.art['failed_checks'],0);self.assertEqual(len(self.art['qualified_tuples']),30)
        self.assertTrue(all(c['status']=='accepted' for c in self.art['qualified_tuples']))
        self.assertTrue(all(c['passed'] for c in self.art['negatives']))
        self.assertEqual(len(self.art['known_unresolved']),2)
        for c in self.art['known_unresolved']:self.assertEqual(c['diagnostics']['PS']['status'],'property_evaluation_failed')
    def test_boundary_sides_and_no_false_subcooling(self):
        probes={c['case_id']:c for c in self.art['new_probes']}
        for name in ('PT_VL_HEATING','PH_FLASH','PT_BUBBLE_BELOW','PT_DEW_BELOW'):
            self.assertEqual(probes[name+'_P0.0']['local_without_source']['status'],'unresolved')
            self.assertEqual(probes[name+'_P-0.001']['local_without_source']['status'],'rejected')
            self.assertEqual(probes[name+'_P0.001']['local_without_source']['status'],'compressed_witness')
        for c in self.art['adapters']:
            if c['result']['status']=='accepted':self.assertIsNone(c['result']['local']['cavitation_safe'])
    def test_comparison_reproducible_across_hash_seeds(self):
        code="from benchmarks.low_pressure_separator_pump.phase_contract.compare import *;p=read(HERE/'production.json');q=next(x for x in p['new_probes'] if x['state']['classification']=='vapor_liquid');print(encode(checks(q['state'],q['state'])))"
        outputs=[subprocess.check_output([sys.executable,'-B','-c',code],cwd=ROOT,env=dict(os.environ,PYTHONHASHSEED=seed)) for seed in ('0','1','2')]
        self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[1],outputs[2])
    def test_no_reference_dependency_in_adapter_or_pump(self):
        for file in ('adapter.py','pump.py'):
            text=(HERE/file).read_text()
            for forbidden in ('import thermo','from thermo','import scipy','reference.json','production.json','read_text','read_bytes'):
                self.assertNotIn(forbidden,text)

if __name__=='__main__':unittest.main()
