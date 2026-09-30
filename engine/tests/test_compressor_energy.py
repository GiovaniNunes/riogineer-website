"""M14 immutable-reference, registry/process, failure and equipment closure protection."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from riogineer_engine.core import ROOT, build_flowsheet, calculate, validate_requirements, Invalid
from riogineer_engine.compressor_energy import compressor, CompressorFailure
from riogineer_engine.network_models import MODELS
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolecularCompositionProvider

spec=importlib.util.spec_from_file_location('m14_comparison',ROOT/'benchmarks/compressor_energy/compare_production.py')
cmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(cmp)


class FrozenCompressorMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.evidence=cmp.build()

    def test_flow_series_frozen_allowances(self):
        for c in self.evidence['flow_scaling']:self.assertTrue(c['passed'])
        doubled=next(c for c in self.evidence['flow_scaling'] if c['case_id']=='FLOW_200.0')
        self.assertEqual(doubled['absolute_error_W'],0.)

    def test_vl_study_is_not_an_accepted_service_case(self):
        self.assertEqual(len(self.evidence['cases']),19)
        self.assertFalse(self.evidence['service_scope'][0]['accepted_outlet'])

    def test_call_order_and_determinism(self):
        self.assertEqual(len(self.evidence['call_order']),18)
        self.assertTrue(all(c['byte_identical'] for c in self.evidence['call_order']))


def positive(index):
    def test(self):
        c=self.evidence['cases'][index]
        self.assertTrue(all(x['passed'] for x in c['comparisons']))
    return test


def negative(index):
    def test(self):
        c=self.evidence['negative_cases'][index]
        self.assertTrue(c['passed']);self.assertFalse(c['accepted_outlet'])
    return test


for index,c in enumerate(cmp.reference()['cases']):setattr(FrozenCompressorMatrix,'test_positive_'+c['case_id'],positive(index))
for index,c in enumerate(cmp.reference()['negative_cases']):setattr(FrozenCompressorMatrix,'test_negative_'+c['case_id'],negative(index))


class CompressorIntegration(unittest.TestCase):
    def setUp(self):
        self.i=cmp.reference()['cases'][0]['inputs']
        self.u,self.s=cmp.inputs(self.i)

    def test_normal_process_uses_registry_and_serializes(self):
        r=cmp.requirements(self.i);validate_requirements(r);f=build_flowsheet(r);before=deepcopy(f)
        original=MODELS['compressor']['execute'];calls=[]
        def spy(unit,inputs,evaluate):calls.append(unit['model']);return original(unit,inputs,evaluate)
        with patch.dict(MODELS['compressor'],execute=spy):out=calculate(f)
        self.assertEqual(calls,[cmp.MODEL]);self.assertEqual(f,before)
        self.assertEqual(out['schema_version'],'1.8');self.assertEqual(f['schema_version'],'1.7')
        self.assertEqual([s['engineering_number'] for s in f['streams']],[1,2])
        self.assertEqual(json.loads(json.dumps(out)),out)
        self.assertEqual(out['streams']['FEED']['component_mass_flow_kg_h'],out['streams']['PRODUCT']['component_mass_flow_kg_h'])

    def test_m7_flow_conversion_is_the_runtime_authority(self):
        result=compressor(self.u,self.s);d=result.details['thermodynamics']
        state=MolecularCompositionProvider().enrich(self.s['inlet'])
        self.assertEqual(d['F_mol_s'],state.composition.molar_flow_kmol_h*1000./3600.)
        self.assertAlmostEqual(d['F_mol_s'],100.,places=12)
        scaled=deepcopy(self.s)
        for key in scaled['inlet']['component_mass_flow_kg_h']:scaled['inlet']['component_mass_flow_kg_h'][key]*=2
        scaled['inlet']['mass_flow_kg_h']*=2
        doubled=compressor(self.u,scaled)
        self.assertEqual(doubled.work_W,2*result.work_W)
        self.assertEqual(doubled.details['thermodynamics']['actual_outlet'],d['actual_outlet'])

    def test_inlet_state_is_recomputed_from_stream(self):
        baseline=compressor(self.u,self.s)
        changed=deepcopy(self.s);changed['inlet']['temperature_K']=310.
        result=compressor(self.u,changed)
        self.assertEqual(result.details['thermodynamics']['inlet']['temperature_K'],310.)
        self.assertNotEqual(result.work_W,baseline.work_W)

    def test_process_failure_returns_no_result(self):
        r=cmp.requirements(dict(self.i,T1=490.,P2=8e5))
        with self.assertRaisesRegex(Invalid,'isentropic_PS.*entropy_target_not_bracketed'):calculate(build_flowsheet(r))

    def test_invalid_model_and_port_count(self):
        u=deepcopy(self.u);u['model']['version']='2.0'
        with self.assertRaises(CompressorFailure):compressor(u,self.s)
        with self.assertRaises(CompressorFailure):compressor(self.u,{})

    def test_successful_nested_ph_cannot_hide_invalid_enthalpy(self):
        original=PengRobinsonProvider.flash_PH
        def corrupt(provider,*args,**kwargs):
            r=original(provider,*args,**kwargs)
            return replace(r,caloric=replace(r.caloric,aggregate=replace(r.caloric.aggregate,h_J_mol=r.caloric.aggregate.h_J_mol+1.)))
        with patch.object(PengRobinsonProvider,'flash_PH',corrupt):
            with self.assertRaisesRegex(CompressorFailure,'enthalpy_residual_failed'):compressor(self.u,self.s)

    def test_successful_ps_cannot_hide_entropy_error(self):
        original=PengRobinsonProvider.flash_PS
        def corrupt(provider,*args,**kwargs):
            r=original(provider,*args,**kwargs)
            return replace(r,caloric=replace(r.caloric,aggregate=replace(r.caloric.aggregate,s_J_mol_K=r.caloric.aggregate.s_J_mol_K+.01)))
        with patch.object(PengRobinsonProvider,'flash_PS',corrupt):
            with self.assertRaisesRegex(CompressorFailure,'entropy_residual_failed'):compressor(self.u,self.s)

    def test_successful_ph_nonvapor_state_is_rejected(self):
        original=PengRobinsonProvider.flash_PH
        def corrupt(provider,*args,**kwargs):
            r=original(provider,*args,**kwargs)
            return replace(r,caloric=replace(r.caloric,equilibrium=replace(r.caloric.equilibrium,classification='vapor_liquid')))
        with patch.object(PengRobinsonProvider,'flash_PH',corrupt):
            with self.assertRaisesRegex(CompressorFailure,'compressor_service_scope'):compressor(self.u,self.s)

    def test_invalid_nested_diagnostics_are_rejected(self):
        original=PengRobinsonProvider.flash_PS
        def corrupt(provider,*args,**kwargs):
            r=original(provider,*args,**kwargs)
            return replace(r,diagnostics=replace(r.diagnostics,brackets_K=()))
        with patch.object(PengRobinsonProvider,'flash_PS',corrupt):
            with self.assertRaisesRegex(CompressorFailure,'invalid_nested_diagnostics'):compressor(self.u,self.s)

    def test_public_process_propagates_injected_ps_and_ph_failures(self):
        for name in ('flash_PS','flash_PH'):
            with patch.object(PengRobinsonProvider,name,return_value=SimpleNamespace(status='controlled_failure',caloric=None,diagnostics='injected')):
                with self.assertRaisesRegex(Invalid,'controlled_failure'):calculate(build_flowsheet(cmp.requirements(self.i)))


if __name__=='__main__':unittest.main()
