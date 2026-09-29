"""M10 property qualification against independent frozen references and failures."""
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
from math import log
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from riogineer_engine import caloric_data
from riogineer_engine.caloric_data import CORRELATIONS, DATASET, REFERENCE, component_caloric
from riogineer_engine.pr_caloric import enthalpy_flow_W, molar_to_mass
from riogineer_engine.pr_eos import MODEL, BinaryInteractions, ThermodynamicError
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.property_packages import property_package
from riogineer_engine.thermodynamics import MolarComposition, StateSpecificationProvenance, ThermodynamicState

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT/'benchmarks/peng_robinson_caloric/methane_nhexane_pr_caloric_reference.json'
IDS = ('methane','n_hexane')
BIP = BinaryInteractions('methane_nhexane_explicit_zero@1.0',IDS,((0.,0.),(0.,0.)),'Explicit zero-kij benchmark')


def state(t=300., p=300000., q=(.5,.5), ids=IDS, bip=BIP):
    return ThermodynamicState(t,p,MolarComposition(ids,q),StateSpecificationProvenance(MODEL,bip.identifier))


class CaloricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(FROZEN.read_text())
        cls.provider = property_package(MODEL)

    def failed(self, result, status):
        self.assertEqual(result.status,status,result.message)
        self.assertEqual(result.phases,())
        self.assertIsNone(result.aggregate)
        self.assertTrue(result.message or result.equilibrium is not None)

    def test_complete_frozen_comparison_and_readonly_reference(self):
        before = FROZEN.read_bytes()
        path = FROZEN.with_name('compare_production.py')
        spec = importlib.util.spec_from_file_location('m10_comparison',path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        report = module.compare_production()
        self.assertTrue(report['passed'],[r for r in report['comparisons'] if not r['passed']])
        self.assertEqual(report['comparison_count'],1526)
        self.assertEqual(before,FROZEN.read_bytes())
        saved = json.loads(path.with_name('production_comparison.json').read_text())
        self.assertEqual(saved['reference_sha256'],hashlib.sha256(before).hexdigest())
        self.assertEqual([c['state'] for c in saved['comparisons']],[c['state'] for c in report['comparisons']])

    def test_opt_in_capabilities(self):
        self.assertIn('phase_caloric_TP',self.provider.capabilities)
        self.assertIn('equilibrium_caloric_PT',self.provider.capabilities)
        self.assertFalse({'PH_flash','PS_flash','process_energy_balance'} & self.provider.capabilities)
        pt = self.provider.flash_PT(state(),BIP)
        self.assertNotIn('caloric',asdict(pt))
        enriched = self.provider.equilibrium_caloric_PT(state(),BIP)
        self.assertEqual(pt,enriched.equilibrium)
        self.assertEqual(enriched.provenance.caloric_dataset,DATASET)
        self.assertEqual(enriched.provenance.reference,REFERENCE)

    def test_dataset_provenance_immutable_and_exact(self):
        for expected in self.reference['cp']['components']:
            actual = CORRELATIONS[expected['id']]
            self.assertEqual(list(actual.coefficients),expected['coefficients'])
            self.assertEqual(actual.source,self.reference['cp']['source'])
            self.assertEqual((actual.Tmin_K,actual.Tmax_K),(expected['Tmin_K'],expected['Tmax_K']))
        with self.assertRaises(TypeError):CORRELATIONS['water'] = None

    def test_single_phase_semantics(self):
        for p,label in [(3e7,'liquid'),(1000.,'vapor')]:
            r = self.provider.phase_caloric_TP(state(p=p),BIP,phase=label)
            self.assertEqual(r.status,'success_single_phase')
            self.assertEqual([x.phase_identifier for x in r.phases],[label])
            self.assertIsNone(r.aggregate.phase_difference_h_J_mol)
            self.assertIsNone(r.aggregate.phase_difference_s_J_mol_K)
            self.assertEqual(r.aggregate.h_J_mol,r.phases[0].h_total_J_mol)

    def test_two_phase_aggregation_and_flow(self):
        r = self.provider.equilibrium_caloric_PT(state(),BIP)
        self.assertEqual(r.status,'success_two_phase')
        liquid,vapor = r.phases
        beta = r.equilibrium.beta
        self.assertAlmostEqual(r.aggregate.h_J_mol,(1-beta)*liquid.h_total_J_mol+beta*vapor.h_total_J_mol,places=10)
        self.assertAlmostEqual(r.aggregate.s_J_mol_K,(1-beta)*liquid.s_total_J_mol_K+beta*vapor.s_total_J_mol_K,places=12)
        H = sum(enthalpy_flow_W(p.fraction*1000*c.mixture_MW_kg_kmol,c.h_total_J_kg) for p,c in zip(r.equilibrium.phases,r.phases))
        expected = self.reference['cases'][1]['benchmark_equilibrium_enthalpy_flow_W']
        self.assertAlmostEqual(H,expected,delta=1e-4)
        self.assertAlmostEqual(H,enthalpy_flow_W(51109.08,r.aggregate.h_J_kg),delta=1e-6)
        self.assertNotEqual(r.equilibrium.phases[0].composition,r.equilibrium.evaluated_molar_composition)
        self.assertNotEqual(r.equilibrium.phases[1].composition,r.equilibrium.evaluated_molar_composition)

    def test_ideal_mixing_pressure_and_reference(self):
        r1 = self.provider.phase_caloric_TP(state(t=300.,p=1000.),BIP)
        r2 = self.provider.phase_caloric_TP(state(t=300.,p=100.),BIP)
        a,b = r1.phases[0],r2.phases[0]
        frozen = self.reference['low_pressure_states'][0]
        self.assert_quantity(a.h_ig_J_mol,frozen['h_ig_J_mol'],'h_ig')
        self.assert_quantity(a.s_ig_J_mol_K,frozen['s_ig_J_mol_K'],'s_ig')
        self.assert_quantity(b.s_ig_J_mol_K,self.reference['low_pressure_states'][1]['s_ig_J_mol_K'],'s_ig')
        self.assertEqual(a.h_ig_J_mol,b.h_ig_J_mol)
        R = self.reference['formulation']['R_J_mol_K']
        self.assertAlmostEqual(a.s_ig_mixing_J_mol_K,R*log(2),places=12)
        no_mixing_entropy = a.s_ig_temperature_J_mol_K+a.s_ig_pressure_J_mol_K
        self.assertAlmostEqual(a.s_ig_J_mol_K-no_mixing_entropy,R*log(2),places=12)
        self.assertNotAlmostEqual(a.s_ig_J_mol_K,no_mixing_entropy,places=6)
        self.assertAlmostEqual(b.s_ig_J_mol_K-a.s_ig_J_mol_K,R*log(10),places=12)
        for i in IDS:
            ideal = component_caloric(i,298.15)
            self.assertEqual((ideal.h_ig_J_mol,ideal.s_ig_temperature_J_mol_K),(0.,0.))

    def test_low_pressure_limits(self):
        for q in [(1.,0.),(0.,1.),(.5,.5)]:
            results = [self.provider.phase_caloric_TP(state(p=p,q=q),BIP).phases[0] for p in (1000.,100.,10.,1.)]
            for attr in ('h_res_J_mol','s_res_J_mol_K'):
                self.assertTrue(all(abs(getattr(a,attr)) > abs(getattr(b,attr)) > 0 for a,b in zip(results,results[1:])))

    def test_exact_single_component_ids(self):
        for i,q in [('methane',(1.,0.)),('n_hexane',(0.,1.))]:
            bip = BinaryInteractions(i+'_zero',(i,),((0.,),),'Explicit pure-component zero')
            a = self.provider.phase_caloric_TP(state(p=1000.,q=(1.,),ids=(i,),bip=bip),bip)
            b = self.provider.phase_caloric_TP(state(p=1000.,q=q),BIP)
            self.assertEqual(a.status,'success_single_phase')
            self.assertAlmostEqual(a.aggregate.h_J_mol,b.aggregate.h_J_mol,places=10)

    def test_reordered_component_ids(self):
        ids = tuple(reversed(IDS))
        bip = BinaryInteractions('reverse_zero',ids,((0.,0.),(0.,0.)),'Explicit zero')
        a = self.provider.equilibrium_caloric_PT(state(q=(.3,.7)),BIP)
        b = self.provider.equilibrium_caloric_PT(state(q=(.7,.3),ids=ids,bip=bip),bip)
        self.assertAlmostEqual(a.aggregate.h_J_mol,b.aggregate.h_J_mol,delta=1e-7)

    def test_invalid_temperature_pressure(self):
        for value in (0.,-1.,float('nan'),float('inf'),True,'300'):
            with self.subTest(value=value):
                self.failed(self.provider.equilibrium_caloric_PT(state(t=value),BIP),'invalid_input')
                self.failed(self.provider.equilibrium_caloric_PT(state(p=value),BIP),'invalid_input')

    def test_invalid_composition(self):
        for q in ((),(.4,.5),(-.1,1.1),(float('nan'),.5),(float('inf'),0.),(.5,.5,0.),(True,False)):
            self.failed(self.provider.equilibrium_caloric_PT(state(q=q),BIP),'invalid_input')
        self.failed(self.provider.equilibrium_caloric_PT(state(ids=('methane','methane')),BIP),'invalid_input')
        self.failed(self.provider.equilibrium_caloric_PT(None,BIP),'invalid_input')

    def test_unsupported_component_not_dropped_even_zero(self):
        for ids in [('methane','water'),('methane','unknown')]:
            for q in [(.5,.5),(1.,0.)]:
                self.failed(self.provider.equilibrium_caloric_PT(state(ids=ids,q=q),BIP),'unsupported_components')

    def test_cp_out_of_range_no_partial_results(self):
        for t in (199.999,1000.001):
            self.failed(self.provider.equilibrium_caloric_PT(state(t=t),BIP),'caloric_out_of_range')
        # Each component's own documented range, no silent clamp/extrapolation.
        for i,limits in [('methane',(50.,1000.)),('n_hexane',(200.,1000.))]:
            for t in limits:self.assertGreater(component_caloric(i,t).Cp_ig_J_mol_K,0)
            for t in (limits[0]-.001,limits[1]+.001):
                with self.assertRaises(ThermodynamicError):component_caloric(i,t)

    def test_missing_and_invalid_cp_data(self):
        with patch.object(caloric_data,'CORRELATIONS',{}):
            self.failed(self.provider.equilibrium_caloric_PT(state(),BIP),'missing_caloric_data')
        for coefficients in [(1.,2.),(float('nan'),0.,0.,0.,0.),(float('inf'),0.,0.,0.,0.)]:
            data = dict(CORRELATIONS)
            data['methane'] = replace(data['methane'],coefficients=coefficients)
            with patch.object(caloric_data,'CORRELATIONS',data):
                self.failed(self.provider.equilibrium_caloric_PT(state(),BIP),'invalid_caloric_data')

    def test_nonfinite_intermediate_not_published(self):
        data = dict(CORRELATIONS)
        data['methane'] = replace(data['methane'],coefficients=(1e308,1e308,1e308,1e308,1e308))
        with patch.object(caloric_data,'CORRELATIONS',data):
            self.failed(self.provider.equilibrium_caloric_PT(state(),BIP),'numerical_domain_error')

    def test_invalid_phase_and_root(self):
        for label in ('solid','gas',''):
            self.failed(self.provider.phase_caloric_TP(state(p=1000.),BIP,phase=label),'invalid_input')
        for root in (0.,-1.,float('nan'),float('inf'),True):
            self.failed(self.provider.phase_caloric_TP(state(p=1000.),BIP,root=root),'invalid_input')
        self.failed(self.provider.phase_caloric_TP(state(p=1000.),BIP,root=.5),'phase_mismatch')
        self.failed(self.provider.phase_caloric_TP(state(p=1000.),BIP,phase='liquid'),'phase_mismatch')
        self.failed(self.provider.phase_caloric_TP(state(),BIP),'phase_mismatch')

    def test_unqualified_bips_and_provenance(self):
        nonzero = replace(BIP,values=((0.,.01),(.01,0.)))
        self.failed(self.provider.equilibrium_caloric_PT(state(bip=nonzero),nonzero),'unsupported_bip')
        self.failed(self.provider.equilibrium_caloric_PT(state(),None),'unsupported_bip')
        class TemperatureDependentBIP(BinaryInteractions):
            @property
            def temperature_dependence(self):return 'temperature_function'
        td = TemperatureDependentBIP(BIP.identifier,IDS,BIP.values,BIP.source)
        self.failed(self.provider.equilibrium_caloric_PT(state(),td),'unsupported_bip')
        bad = replace(state(),provenance=StateSpecificationProvenance('other',BIP.identifier))
        self.failed(self.provider.equilibrium_caloric_PT(bad,BIP),'invalid_input')

    def test_nonconvergence_propagates_without_caloric_values(self):
        r = self.provider.equilibrium_caloric_PT(state(),BIP,SolverSettings(flash_max_iterations=1))
        self.failed(r,'flash_not_converged')
        self.assertEqual(r.equilibrium.status,'flash_not_converged')
        r = self.provider.equilibrium_caloric_PT(state(),BIP,SolverSettings(stability_max_iterations=1))
        self.failed(r,'stability_not_converged')
        self.failed(self.provider.equilibrium_caloric_PT(state(),BIP,None),'invalid_input')

    def test_units_and_invalid_helpers(self):
        self.assertEqual(molar_to_mass(100.,20.),5000.)
        self.assertEqual(molar_to_mass(-100.,20.),-5000.)
        self.assertEqual(enthalpy_flow_W(72.,5000.),100.)
        self.assertEqual(enthalpy_flow_W(0.,-1000.),0.)
        for mw in (0.,-1.,float('nan'),True,5e-324):
            with self.assertRaises(ThermodynamicError):molar_to_mass(1.,mw)
        for flow,h in [(-1.,1.),(float('inf'),1.),(1.,float('nan')),(True,1.)]:
            with self.assertRaises(ThermodynamicError):enthalpy_flow_W(flow,h)

    def test_consistent_reference_shift(self):
        r = self.provider.equilibrium_caloric_PT(state(),BIP)
        l,v = r.phases
        C = 12345.
        self.assertAlmostEqual((v.h_total_J_mol+C)-(l.h_total_J_mol+C),r.aggregate.phase_difference_h_J_mol,places=10)
        shifts = (10000.,-3000.)
        feed = sum(q*c for q,c in zip(r.equilibrium.evaluated_molar_composition,shifts))
        output = sum(p.fraction*sum(q*c for q,c in zip(p.composition,shifts)) for p in r.equilibrium.phases)
        self.assertAlmostEqual(feed,output,delta=1e-8)
        self.assertEqual(r.provenance.reference,REFERENCE)

    def assert_quantity(self, actual, expected, quantity):
        tol = self.reference['acceptance_tolerances'][quantity]
        self.assertLessEqual(abs(actual-expected),tol['atol']+tol['rtol']*abs(expected))

    def frozen_phases(self):
        for case in self.reference['cases']:
            for expected in case['phases'].values():
                r = self.provider.phase_caloric_TP(state(t=expected['T_K'],p=expected['P_Pa_abs'],q=tuple(expected['composition'])),BIP,
                                                   phase=expected['phase'],root=expected['Z'])
                self.assertEqual(r.status,'success_single_phase',r.message)
                yield expected,r.phases[0]

    def test_methane_cp_frozen(self):
        for expected in self.reference['cp_integration_checks']:
            if expected['component_id']=='methane':
                self.assert_quantity(component_caloric('methane',expected['T_K']).Cp_ig_J_mol_K,expected['Cp_ig_J_mol_K'],'Cp')

    def test_n_hexane_cp_frozen(self):
        for expected in self.reference['cp_integration_checks']:
            if expected['component_id']=='n_hexane':
                self.assert_quantity(component_caloric('n_hexane',expected['T_K']).Cp_ig_J_mol_K,expected['Cp_ig_J_mol_K'],'Cp')

    def test_component_ideal_h_s_integrals_frozen(self):
        for expected in self.reference['cp_integration_checks']:
            actual = component_caloric(expected['component_id'],expected['T_K'])
            self.assert_quantity(actual.h_ig_J_mol,expected['h_ig_J_mol'],'h_ig')
            self.assert_quantity(actual.s_ig_temperature_J_mol_K,expected['s_ig_temperature_J_mol_K'],'s_ig')

    def test_phase_mixture_ideal_h_frozen(self):
        for expected,actual in self.frozen_phases():
            self.assert_quantity(actual.h_ig_J_mol,expected['h_ig_J_mol'],'h_ig')

    def test_phase_mixture_ideal_s_frozen(self):
        for expected,actual in self.frozen_phases():
            self.assert_quantity(actual.s_ig_J_mol_K,expected['s_ig_J_mol_K'],'s_ig')

    def test_analytic_alpha_derivative_frozen(self):
        for expected,actual in self.frozen_phases():
            for a,e in zip(actual.pure_parameters,expected['pure_parameters']):
                self.assert_quantity(a.dalpha_dT,e['dalpha_dT_K_inv'],'dalpha_dT')

    def test_analytic_pure_attraction_derivative_frozen(self):
        for expected,actual in self.frozen_phases():
            for a,e in zip(actual.pure_parameters,expected['pure_parameters']):
                self.assert_quantity(a.da_dT,e['da_i_dT_Pa_m6_mol2_K'],'da_dT')

    def test_analytic_mixture_attraction_derivative_frozen(self):
        for expected,actual in self.frozen_phases():
            self.assert_quantity(actual.eos.da_dT,expected['da_mix_dT_Pa_m6_mol2_K'],'da_dT')

    def test_residual_h_s_frozen(self):
        for expected,actual in self.frozen_phases():
            self.assert_quantity(actual.h_res_J_mol,expected['h_res_J_mol'],'h_res')
            self.assert_quantity(actual.s_res_J_mol_K,expected['s_res_J_mol_K'],'s_res')

    def test_total_phase_h_s_frozen(self):
        for expected,actual in self.frozen_phases():
            self.assert_quantity(actual.h_total_J_mol,expected['h_total_J_mol'],'h_total')
            self.assert_quantity(actual.s_total_J_mol_K,expected['s_total_J_mol_K'],'s_total')

    def test_frozen_temperature_sensitivity(self):
        expected = {c['case_id']:c['phases']['vapor'] for c in self.reference['cases'] if c['case_id'] in ('T280_V','T400_V')}
        low = self.provider.phase_caloric_TP(state(t=280.,p=1000.),BIP).phases[0]
        high = self.provider.phase_caloric_TP(state(t=400.,p=1000.),BIP).phases[0]
        for attr,quantity in [('Cp_ig_J_mol_K','Cp'),('h_ig_J_mol','h_ig'),('s_ig_J_mol_K','s_ig'),('h_res_J_mol','h_res'),('s_res_J_mol_K','s_res')]:
            self.assert_quantity(getattr(low,attr),expected['T280_V'][attr],quantity)
            self.assert_quantity(getattr(high,attr),expected['T400_V'][attr],quantity)
            self.assertNotEqual(getattr(low,attr),getattr(high,attr))

    def test_determinism_is_independent_of_call_order(self):
        first = self.provider.equilibrium_caloric_PT(state(),BIP)
        self.provider.phase_caloric_TP(state(t=400.,p=1000.),BIP)
        self.provider.equilibrium_caloric_PT(state(p=3e7),BIP)
        self.assertEqual(first,self.provider.equilibrium_caloric_PT(state(),BIP))
        self.assertEqual(first.equilibrium.overall_state,state())

    def test_numerical_guards_abort_without_partial_properties(self):
        from riogineer_engine import pr_caloric
        original = pr_caloric._phase_properties
        for field,value in [('da_dT',float('nan')),('b',0.),('B',2.)]:
            def corrupt(eos,phase):
                # Leave liquid successful, then fail vapor: no partial payload may escape.
                if phase.identifier=='liquid':return original(eos,phase)
                mixed = replace(eos.mixture(phase.composition),**{field:value})
                from types import SimpleNamespace
                proxy = SimpleNamespace(temperature_K=eos.temperature_K,pressure_Pa_abs=eos.pressure_Pa_abs,
                                        component_ids=eos.component_ids,mixture=lambda _:mixed)
                return original(proxy,phase)
            with patch.object(pr_caloric,'_phase_properties',side_effect=corrupt):
                self.failed(self.provider.equilibrium_caloric_PT(state(),BIP),'numerical_domain_error')

    def test_manual_comparison_output_and_relative_error(self):
        command = [sys.executable,'-B',str(FROZEN.with_name('compare_production.py'))]
        before = FROZEN.read_bytes()
        output = subprocess.run(command+['--case','B'],capture_output=True,text=True,check=True).stdout
        for token in ['Liquid','Vapor','molar composition: methane=','Z=','MW=','h_mass=','s_mass=',
                      'liquid molar fraction=','h_eq=','s_eq=','h_V-h_L=','s_V-s_L=',
                      'reference | production','relative error | atol | rtol','PASS',
                      'Human-operated Milestone 10 validation remains pending.']:
            self.assertIn(token,output)
        self.assertNotIn('Case A:',output)
        machine = json.loads(subprocess.run(command+['--json'],capture_output=True,text=True,check=True).stdout)
        for row in machine['comparisons']:
            if row['expected']==0:self.assertIsNone(row['relative_error'])
            else:self.assertEqual(row['relative_error'],row['absolute_error']/abs(row['expected']))
        self.assertTrue(machine['passed'])
        self.assertEqual(before,FROZEN.read_bytes())

    def test_offline_production_has_no_benchmark_or_library_runtime(self):
        code = """
from riogineer_engine.property_packages import property_package
from riogineer_engine.pr_eos import BinaryInteractions, MODEL
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance
import sys
p = property_package(MODEL)
b = BinaryInteractions('offline_zero', ('methane','n_hexane'), ((0.,0.),(0.,0.)), 'Explicit zero')
s = ThermodynamicState(300.,300000.,MolarComposition(b.component_ids,(.5,.5)),StateSpecificationProvenance(MODEL,b.identifier))
r = p.equilibrium_caloric_PT(s,b)
assert r.status == 'success_two_phase', r
assert not any(k.split('.')[0] in ('thermo','teqp','numpy','scipy','benchmarks') for k in sys.modules)
print(p.identifier)
"""
        import os
        env = dict(os.environ,PYTHONPATH=str(ROOT/'engine'))
        result = subprocess.run([sys.executable,'-B','-c',code],cwd='/tmp',env=env,capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),MODEL)


if __name__=='__main__':unittest.main()
