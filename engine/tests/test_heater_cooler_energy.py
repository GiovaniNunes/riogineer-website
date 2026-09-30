"""M12 equipment, runtime conversion, failure and single-unit process integration."""
from copy import deepcopy
from dataclasses import asdict
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from riogineer_engine.core import build_flowsheet, calculate, validate_requirements, ROOT
from riogineer_engine.heater_cooler_energy import heater, ThermalFailure
from riogineer_engine.pr_caloric import CaloricResult
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.thermodynamics import MolecularCompositionProvider

spec = importlib.util.spec_from_file_location('m12_compare', ROOT/'benchmarks/heater_cooler_energy/compare_production.py')
cmp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmp)


def requirements(mode='A'):
    unit, streams = cmp.inputs(100., 1000., 300., 1000., [.5,.5], **({'Tout':350.} if mode=='A' else {'Q':0.}))
    feed = {k:v for k,v in streams['inlet'].items() if k in ('component_mass_flow_kg_h','temperature_K','pressure_Pa_abs')}
    return dict(schema_version='1.5',kind='requirements',case_id='M12_TEST',profile='heater_cooler_energy',
        units=dict(temperature='K',pressure='Pa_abs',component_mass_flow='kg/h',heat_capacity='J/(kg K)',duty='W',recovery='mass_fraction'),
        provenance=dict(source='M12 integration test',basis='qualified_equilibrium_energy'),components=['methane','n_hexane'],
        feeds=[dict(id='SOURCE',state=feed)],sinks=[dict(id='SINK')],
        equipment=[dict(id=unit['id'],type=unit['type'],model=unit['model'],parameters=unit['operating_parameters'])],
        streams=[dict(id='FEED',service='feed'),dict(id='PRODUCT',service='product')],
        connections=[dict(id='C1',stream_id='FEED',source=dict(owner_id='SOURCE',port_id='outlet'),target=dict(owner_id='HEATER_1',port_id='inlet')),
                     dict(id='C2',stream_id='PRODUCT',source=dict(owner_id='HEATER_1',port_id='outlet'),target=dict(owner_id='SINK',port_id='inlet'))],
        required_outputs=['streams','mass_balance','energy_balance'])


class FrozenMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = cmp.build()


def positive(index):
    def check(self):
        case = self.evidence['cases'][index]
        self.assertTrue(all(c['passed'] for c in case['comparisons']))
    return check


for index,c in enumerate(cmp.reference()['cases']):
    setattr(FrozenMatrix,'test_'+c['specification']['case_id'],positive(index))
for index,c in enumerate(cmp.reference()['negative_cases']):
    def negative(self,index=index):
        self.assertFalse(self.evidence['negative_cases'][index]['accepted_outlet'])
    setattr(FrozenMatrix,'test_reject_'+c['specification']['case_id'],negative)


class EquipmentIntegration(unittest.TestCase):
    def test_both_and_neither_rejected(self):
        u,s=cmp.inputs(100.,1000.,300.,1000.,[.5,.5],Tout=350.)
        for p in (dict(u['operating_parameters'],duty_W=0.),{k:v for k,v in u['operating_parameters'].items() if k!='outlet_temperature_K'}):
            with self.assertRaises(ThermalFailure):heater(dict(u,operating_parameters=p),s)

    def test_m7_conversion_and_scaling(self):
        u,s=cmp.inputs(100.,1000.,300.,1000.,[.5,.5],Tout=350.)
        original=heater(u,s)
        self.assertAlmostEqual(original.details['thermodynamics']['F_mol_s'],100.,places=12)
        u2,s2=cmp.inputs(200.,1000.,300.,1000.,[.5,.5],Tout=350.)
        scaled=heater(u2,s2)
        self.assertEqual(scaled.duty_W,2*original.duty_W)
        for key in ('inlet','outlet','delta_H_J_mol'):
            self.assertEqual(original.details['thermodynamics'][key],scaled.details['thermodynamics'][key])
        molecular=MolecularCompositionProvider().enrich(original.streams['outlet']).composition
        self.assertAlmostEqual(molecular.molar_flow_kmol_h,360.,places=12)
        self.assertEqual(dict(molecular.molar_fractions),{'methane':.5,'n_hexane':.5})

    def test_pt_and_ph_failure_propagation(self):
        for stage in ('inlet','outlet'):
            u,s=cmp.inputs(100.,1000.,300.,1000.,[.5,.5],Tout=350.)
            calls=[]
            real=PengRobinsonProvider().equilibrium_caloric_PT
            def evaluate(*args,**kw):
                calls.append(1)
                if len(calls)==(1 if stage=='inlet' else 2):return CaloricResult('controlled_failure',None,message='injected')
                return real(*args,**kw)
            with patch('riogineer_engine.heater_cooler_energy.property_package',return_value=SimpleNamespace(equilibrium_caloric_PT=evaluate)):
                with self.assertRaises(ThermalFailure) as failure:heater(u,s)
            self.assertEqual(failure.exception.status,'controlled_failure')
        u,s=cmp.inputs(100.,1000.,300.,1000.,[.5,.5],Q=0.)
        with patch.object(PengRobinsonProvider,'flash_PH',return_value=SimpleNamespace(status='ph_nonconvergence',caloric=None,diagnostics='injected PH failure')):
            with self.assertRaises(ThermalFailure) as failure:heater(u,s)
        self.assertEqual(failure.exception.stage,'outlet_PH')
        self.assertEqual(failure.exception.diagnostics,'injected PH failure')

    def test_mode_a_does_not_call_ph(self):
        u,s=cmp.inputs(100.,1000.,300.,1000.,[.5,.5],Tout=350.)
        with patch.object(PengRobinsonProvider,'flash_PH',side_effect=AssertionError('Unnecessary PH')):
            heater(u,s)

    def test_process_identity_serialization_and_runtime(self):
        for mode in ('A','B'):
            r=requirements(mode)
            validate_requirements(r)
            f=build_flowsheet(r);before=deepcopy(f)
            result=calculate(f)
            self.assertEqual(f,before)
            self.assertEqual(result['schema_version'],'1.7')
            self.assertEqual(set(result['streams']),{'FEED','PRODUCT'})
            self.assertEqual(result['equipment'][0]['id'],'HEATER_1')
            self.assertEqual(result['streams']['FEED']['component_mass_flow_kg_h'],result['streams']['PRODUCT']['component_mass_flow_kg_h'])
            self.assertEqual([s['engineering_number'] for s in f['streams']],[1,2])
            repeated=calculate(f)
            self.assertEqual(result['equipment'],repeated['equipment'])
            self.assertEqual(result['input_sha256'],repeated['input_sha256'])
        r=requirements(); r['feeds'][0]['state']['temperature_K']=310.
        changed=calculate(build_flowsheet(r))
        self.assertEqual(changed['equipment'][0]['thermodynamics']['inlet']['temperature_K'],310.)
        self.assertNotEqual(changed['equipment'][0]['duty_W'],result['equipment'][0]['duty_W'])

    def test_process_failure_has_no_results(self):
        r=requirements('B');r['equipment'][0]['parameters']['duty_W']=1e10
        with self.assertRaisesRegex(ValueError,'HEATER_1.*enthalpy_target_not_bracketed'):
            calculate(build_flowsheet(r))

    def test_determinism_and_call_order(self):
        u,s=cmp.inputs(100.,1000.,300.,1000.,[.5,.5],Q=10000.)
        reference=asdict(heater(u,s))
        cases=[dict(Tin=300.,Tout=350.,P=1000.),dict(Tin=350.,Tout=300.,P=1000.),dict(Tin=300.,Tout=350.,P=6e6)]
        for c in cases:
            a,b=cmp.inputs(100.,c['P'],c['Tin'],c['P'],[.5,.5],Tout=c['Tout']);heater(a,b)
            self.assertEqual(reference,asdict(heater(u,s)))
        bad=deepcopy(u);bad['operating_parameters']['duty_W']=float('nan')
        with self.assertRaises(ThermalFailure):heater(bad,s)
        self.assertEqual(reference,asdict(heater(u,s)))


if __name__=='__main__':unittest.main()
