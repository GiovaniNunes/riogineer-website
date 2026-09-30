"""M15 production frozen-matrix qualification and public-path failure atomicity."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import unittest
from unittest.mock import patch
from riogineer_engine.core import ROOT, build_flowsheet, calculate, Invalid
from riogineer_engine.two_stream_heat_exchanger_energy import exchanger, ExchangerFailure
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.network_models import MODELS

spec=importlib.util.spec_from_file_location('m15_comparison',ROOT/'benchmarks/two_stream_heat_exchanger/compare_production.py')
cmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(cmp)


class FrozenExchangerMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.evidence=cmp.build()

    def test_reciprocal_both_modes_through_public_path(self):
        for c in self.evidence['cases']:
            self.assertTrue(c['reciprocal']['passed'])
            a=c['production']['equipment'][0]['thermodynamics'];b=c['reciprocal']['production']['equipment'][0]['thermodynamics']
            self.assertNotEqual(a['specification_mode'],b['specification_mode'])

    def test_flow_scaling_and_determinism(self):
        self.assertTrue(all(c['passed'] for c in self.evidence['flow_scaling']))
        self.assertEqual(len(self.evidence['call_order']),12)
        self.assertTrue(all(c['byte_identical'] for c in self.evidence['call_order']))


def frozen_test(group,index):
    def test(self):self.assertTrue(self.evidence[group][index]['passed'])
    return test


for group,reference_group in [('cases','cases'),('negative_cases','negative_cases'),('service_scope','phase_studies')]:
    for index,c in enumerate(cmp.reference()[reference_group]):
        setattr(FrozenExchangerMatrix,'test_'+group+'_'+c['case_id'],frozen_test(group,index))


class ExchangerIntegration(unittest.TestCase):
    def setUp(self):
        self.i=cmp.reference()['cases'][0]['inputs'];self.u,self.s=cmp.inputs(self.i)

    def test_public_registry_call_and_input_immutability(self):
        f=build_flowsheet(cmp.requirements(self.i));before=deepcopy(f);calls=[];original=MODELS['two_stream_heat_exchanger']['execute']
        def spy(u,i,e):calls.append(set(i));return original(u,i,e)
        with patch.dict(MODELS['two_stream_heat_exchanger'],execute=spy):r=calculate(f)
        self.assertEqual(calls,[{'hot_in','cold_in'}]);self.assertEqual(f,before)
        self.assertEqual(r['schema_version'],'1.9');self.assertNotIn('mass',r['balances'])
        for side in ('hot','cold'):
            self.assertEqual(r['streams'][side.upper()+'_IN']['component_mass_flow_kg_h'],r['streams'][side.upper()+'_OUT']['component_mass_flow_kg_h'])

    def test_public_injected_failures_publish_no_result(self):
        negatives=[c for c in cmp.reference()['negative_cases'] if c['synthetic']]
        for c in negatives:
            f=build_flowsheet(cmp.requirements(c['inputs']));before=deepcopy(f)
            with self.subTest(case=c['case_id']),cmp.injection(c['synthetic']):
                with self.assertRaises(Invalid):calculate(f)
            self.assertEqual(f,before)

    def test_zero_duty_still_calls_ph(self):
        i=deepcopy(self.i);i['T_hot_out']=i['hot']['Tin'];i['cold']['Pout']=5e4
        original=PengRobinsonProvider.flash_PH;calls=[]
        def spy(provider,*a,**kw):calls.append(1);return original(provider,*a,**kw)
        with patch.object(PengRobinsonProvider,'flash_PH',spy):d=cmp.evaluate(i)['equipment'][0]['thermodynamics']
        self.assertEqual(len(calls),1);self.assertNotEqual(d['cold_inlet']['temperature_K'],d['cold_outlet']['temperature_K'])
        self.assertLessEqual(abs(d['cold_outlet']['H_eq_J_mol']-d['cold_inlet']['H_eq_J_mol']),1e-6)

    def test_failed_ph_diagnostics_cannot_be_accepted(self):
        original=PengRobinsonProvider.flash_PH
        def bad(provider,*a,**kw):
            r=original(provider,*a,**kw);return replace(r,diagnostics=replace(r.diagnostics,brackets_K=()))
        with patch.object(PengRobinsonProvider,'flash_PH',bad):
            with self.assertRaisesRegex(ExchangerFailure,'final_acceptance_failed'):exchanger(self.u,self.s)

    def test_fresh_final_pressure_cannot_drift(self):
        original=PengRobinsonProvider.flash_PH
        def bad(provider,*a,**kw):
            r=original(provider,*a,**kw);c=r.caloric;pt=c.equilibrium
            return replace(r,caloric=replace(c,equilibrium=replace(pt,overall_state=replace(pt.overall_state,pressure_Pa_abs=1.01*pt.overall_state.pressure_Pa_abs))))
        with patch.object(PengRobinsonProvider,'flash_PH',bad):
            with self.assertRaisesRegex(ExchangerFailure,'material_balance_failed'):exchanger(self.u,self.s)

    def test_inconsistent_mass_fraction_is_not_normalized(self):
        s=deepcopy(self.s);s['hot_in']['component_mass_fractions']['methane']=.123
        with self.assertRaisesRegex(ExchangerFailure,'invalid_composition'):exchanger(self.u,s)

    def test_upstream_outputs_propagate_to_second_exchanger(self):
        r=cmp.requirements(self.i);second=deepcopy(r['equipment'][0]);second['id']='HX2';second['parameters']['hot_outlet_temperature_K']=370.;r['equipment'].insert(0,second)
        for side in ('hot','cold'):
            sid=side.upper()+'_OUT';link=next(c for c in r['connections'] if c['stream_id']==sid);sink=link['target'];link['target']=dict(owner_id='HX2',port_id=side+'_in')
            r['streams'].append(dict(id=sid+'2',service=side+'_out2'))
            r['connections'].append(dict(id='C_'+sid+'2',stream_id=sid+'2',source=dict(owner_id='HX2',port_id=side+'_out'),target=sink))
        out=calculate(build_flowsheet(r));self.assertEqual(out['execution']['equipment_order'],['HX','HX2'])
        a,b=[e['thermodynamics'] for e in out['equipment']]
        for side in ('hot','cold'):
            self.assertEqual(a[side+'_outlet'],b[side+'_inlet'])
            self.assertEqual(out['streams'][side.upper()+'_IN']['component_mass_flow_kg_h'],out['streams'][side.upper()+'_OUT2']['component_mass_flow_kg_h'])

if __name__=='__main__':unittest.main()
