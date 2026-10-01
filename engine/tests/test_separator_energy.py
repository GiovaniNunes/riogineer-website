"""M17 independent evidence, adapter failure safety and historical compatibility."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from riogineer_engine.core import build_flowsheet,calculate,validate_requirements,validate_schema,Invalid
from riogineer_engine.milestone17 import requirements
from riogineer_engine.milestone9 import requirements as old_requirements
from riogineer_engine.separator_energy import separator,parameters,SeparatorFailure
from riogineer_engine.network_models import state_from_rates
from riogineer_engine.property_packages import property_package
ROOT=Path(__file__).resolve().parents[2]


def unit_feed(**kw):
    r=requirements(**kw);u=r['equipment'][0];s=r['feeds'][0]['state']
    return dict(u,operating_parameters=u['parameters']),state_from_rates(s['component_mass_flow_kg_h'],s['temperature_K'],s['pressure_Pa_abs'],None)


class SeparatorEnergyTests(unittest.TestCase):
    def test_general_table_molecular_properties_in_all_demonstrations(self):
        from riogineer_engine.components import component
        for mode,pressure in [('specified_temperature',3e5),('adiabatic',1e6),('adiabatic',3e7)]:
            with self.subTest(mode=mode,pressure=pressure):
                r=calculate(build_flowsheet(requirements(mode,Pout=pressure)))
                u=r['equipment'][0];d=u['thermodynamics']
                for port,sid in u['material_streams'].items():
                    state=r['streams'][sid];props=state['properties']
                    expected=sum(rate/component(i).molecular_weight for i,rate in state['component_mass_flow_kg_h'].items())
                    self.assertAlmostEqual(props['molar_flow']['value'],expected,places=10)
                    self.assertEqual(props['molar_flow']['unit'],'kmol/h')
                    self.assertEqual(props['molecular_mass']['unit'],'kg/kmol')
                    panel_flow=d['F_mol_s'] if port=='inlet' else d['phases'][port]['molar_flow_mol_s']
                    self.assertAlmostEqual(props['molar_flow']['value'],3.6*panel_flow,places=10)
                    if expected:
                        self.assertAlmostEqual(props['molecular_mass']['value'],state['mass_flow_kg_h']/expected,places=10)
                        expected_z=d['inlet']['z'] if port=='inlet' else d['phases'][port]['composition']
                        for i,z in expected_z.items():self.assertAlmostEqual(props['molar_composition']['value'][i],z,places=12)
                    else:
                        self.assertEqual(props['molar_flow']['status'],'calculated')
                        self.assertEqual(state['enthalpy_flow_W'],0)
                        self.assertIsNone(state['component_mass_fractions'])
                        self.assertIsNone(props['molar_composition']['value'])
                        self.assertIsNone(props['molecular_mass']['value'])
                        self.assertIsNone(d['phases'][port]['h_J_mol'])
                    for key in ('density','gas_volumetric_flow','oil_volumetric_flow','water_volumetric_flow'):
                        self.assertIsNone(props[key]['value'])
                if mode=='adiabatic' and pressure==3e7:
                    for port in ('inlet','liquid'):
                        props=r['streams'][u['material_streams'][port]]['properties']
                        self.assertAlmostEqual(props['molar_flow']['value'],360.)
                        for value in props['molar_composition']['value'].values():self.assertAlmostEqual(value,.5)

    def test_all_independent_cases(self):
        spec=importlib.util.spec_from_file_location('m17_compare',ROOT/'benchmarks/two_phase_separator_energy/compare_production.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        result=mod.compare();self.assertEqual(len(result['cases']),24);self.assertEqual(result['comparison_count'],969)

    def test_mode_contracts_reject_extra_missing_or_conflicting_fields(self):
        for mode in ('specified_temperature','adiabatic'):
            r=requirements(mode)
            validate_requirements(r)
            changes=[('duty_W',0),('mode','unknown'),('separator_pressure_Pa_abs',0),('separator_pressure_Pa_abs',float('nan'))]
            if mode=='adiabatic':changes.append(('separator_temperature_K',300))
            else:changes.extend([('separator_temperature_K',199),('separator_temperature_K',501)])
            for key,value in changes:
                with self.subTest(mode=mode,key=key,value=value):
                    bad=deepcopy(r);bad['equipment'][0]['parameters'][key]=value
                    with self.assertRaises((Invalid,ValueError)):validate_requirements(bad)
                    with self.assertRaises(ValueError):parameters(bad['equipment'][0]['parameters'])
            for key in r['equipment'][0]['parameters']:
                bad=deepcopy(r);del bad['equipment'][0]['parameters'][key]
                with self.assertRaises((Invalid,ValueError)):validate_requirements(bad)

    def test_ports_topology_and_independent_enthalpy_rejected(self):
        r=requirements();r['feeds'][0]['state']['enthalpy_flow_W']=0
        with self.assertRaises(Invalid):validate_requirements(r)
        for mutate in (lambda f:f['equipment'][0]['ports'].pop(),lambda f:f['connections'][1]['source'].update(port_id='water'),lambda f:f['streams'][1].update(specified_state=f['streams'][0]['specified_state']),lambda f:f['boundaries'].pop()):
            f=build_flowsheet(requirements());mutate(f)
            with self.assertRaises(Invalid):calculate(f)
        u,feed=unit_feed();feed['enthalpy_flow_W']=0
        with self.assertRaisesRegex(SeparatorFailure,'conflicting_state'):separator(u,{'inlet':feed})
        with self.assertRaisesRegex(SeparatorFailure,'invalid_input'):separator(u,{'feed':feed})

    def test_invalid_material_and_conditions_fail_before_provider(self):
        for key,value in [('mass_flow_kg_h',0),('mass_flow_kg_h',-1),('mass_flow_kg_h',float('inf')),('temperature_K',199),('temperature_K',501),('pressure_Pa_abs',0),('pressure_Pa_abs',float('nan'))]:
            with self.subTest(key=key,value=value):
                u,f=unit_feed();f[key]=value
                with patch('riogineer_engine.separator_energy.property_package') as provider:
                    with self.assertRaises(SeparatorFailure):separator(u,{'inlet':f})
                    provider.assert_not_called()
        for key,value in [('water',0),('unknown',0),('methane',-1),('methane',float('nan')),('methane',0)]:
            u,f=unit_feed();f['component_mass_flow_kg_h'][key]=value
            with self.assertRaises(SeparatorFailure):separator(u,{'inlet':f})

    def test_pressure_equal_reduction_and_increase(self):
        for mode in ('specified_temperature','adiabatic'):
            for pout in (3e7,1e6):calculate(build_flowsheet(requirements(mode,Pout=pout)))
            with self.assertRaisesRegex(Invalid,'invalid_pressure'):calculate(build_flowsheet(requirements(mode,Pout=3e7+1)))

    def test_actual_inlet_and_flow_scaling_without_mutation(self):
        provider=property_package('peng_robinson@1.0')
        u,f=unit_feed(Tin=320.,Pin=2e7,z=(.4,.6));original=deepcopy(f);seen=[]
        def forward(state,*a,**kw):seen.append(state);return provider.equilibrium_caloric_PT(state,*a,**kw)
        with patch('riogineer_engine.separator_energy.property_package',return_value=SimpleNamespace(equilibrium_caloric_PT=forward)):
            separator(u,{'inlet':f})
        self.assertEqual(f,original);self.assertEqual((seen[0].temperature_K,seen[0].pressure_Pa_abs),(320.,2e7))
        self.assertAlmostEqual(seen[0].composition.molar_fractions['methane'],.4)
        for mode in ('specified_temperature','adiabatic'):
            a=calculate(build_flowsheet(requirements(mode,F=100,Pout=1e6)));b=calculate(build_flowsheet(requirements(mode,F=200,Pout=1e6)))
            da=a['equipment'][0]['thermodynamics'];db=b['equipment'][0]['thermodynamics']
            self.assertEqual(da['outlet'],db['outlet']);self.assertEqual(db['duty_W'],2*da['duty_W'])
            for sid,v in a['streams'].items():
                self.assertAlmostEqual(b['streams'][sid]['enthalpy_flow_W'],2*v['enthalpy_flow_W'])
                self.assertAlmostEqual(b['streams'][sid]['mass_flow_kg_h'],2*v['mass_flow_kg_h'])

    def test_provider_failure_never_publishes(self):
        provider=property_package('peng_robinson@1.0')
        for status in ('enthalpy_target_not_bracketed','multiple_ph_roots','pt_evaluation_failure','ph_nonconvergence'):
            inverse=SimpleNamespace(status=status,caloric=None,diagnostics=SimpleNamespace(reason='controlled failure'))
            fake=SimpleNamespace(equilibrium_caloric_PT=provider.equilibrium_caloric_PT,flash_PH=lambda *a,**k:inverse)
            with self.subTest(status=status),patch('riogineer_engine.separator_energy.property_package',return_value=fake):
                with self.assertRaisesRegex(Invalid,status):calculate(build_flowsheet(requirements('adiabatic')))
        fake=SimpleNamespace(equilibrium_caloric_PT=lambda *a,**k:SimpleNamespace(status='pt_nonconvergence',aggregate=None,equilibrium=None,message='controlled'))
        with patch('riogineer_engine.separator_energy.property_package',return_value=fake):
            with self.assertRaisesRegex(Invalid,'pt_nonconvergence'):calculate(build_flowsheet(requirements()))

    def test_real_unsupported_pure_coexistence_gap(self):
        with self.assertRaises(Invalid):calculate(build_flowsheet(requirements('adiabatic',Pin=1e7,Tin=350.,Pout=1000.,z=(0.,1.))))

    def test_ph_target_and_corrupt_energy_payload_rejected(self):
        provider=property_package('peng_robinson@1.0')
        def inverse(spec,bip):return provider.flash_PH(replace(spec,enthalpy_J_mol=1e10),bip)
        with patch('riogineer_engine.separator_energy.property_package',return_value=SimpleNamespace(equilibrium_caloric_PT=provider.equilibrium_caloric_PT,flash_PH=inverse)):
            with self.assertRaisesRegex(Invalid,'enthalpy_target_not_bracketed'):calculate(build_flowsheet(requirements('adiabatic')))
        def corrupt(spec,bip):
            ph=provider.flash_PH(spec,bip)
            c=ph.caloric;bad=replace(c,phases=tuple(replace(p,h_total_J_mol=p.h_total_J_mol+100) for p in c.phases))
            return replace(ph,caloric=bad)
        with patch('riogineer_engine.separator_energy.property_package',return_value=SimpleNamespace(equilibrium_caloric_PT=provider.equilibrium_caloric_PT,flash_PH=corrupt)):
            with self.assertRaisesRegex(Invalid,'energy_balance_failure'):calculate(build_flowsheet(requirements('adiabatic')))

    def test_absent_phase_and_reported_energy_identity(self):
        for pressure,temperature,absent in ((3e7,280.,'vapor'),(1000.,400.,'liquid')):
            r=calculate(build_flowsheet(requirements(Pout=pressure,Tout=temperature)));u=r['equipment'][0];d=u['thermodynamics']
            p=d['phases'][absent];self.assertIsNone(p['composition']);self.assertIsNone(p['h_J_mol']);self.assertEqual(p['enthalpy_flow_W'],0)
            stream=r['streams'][u['material_streams'][absent]];self.assertIsNone(stream['component_mass_fractions']);self.assertEqual(stream['mass_flow_kg_h'],0)
            h=r['streams'];m=u['material_streams']
            self.assertAlmostEqual(h[m['vapor']]['enthalpy_flow_W']+h[m['liquid']]['enthalpy_flow_W']-h[m['inlet']]['enthalpy_flow_W']-u['duty_W'],d['energy_residual_W'])

    def test_old_model_and_numbering_unchanged(self):
        old=calculate(build_flowsheet(old_requirements()));self.assertEqual(old['schema_version'],'1.6');self.assertEqual(old['balances']['energy']['status'],'not_calculated')
        self.assertTrue(all(s['enthalpy_flow_W'] is None for s in old['streams'].values()))
        f=build_flowsheet(requirements());original=deepcopy(f);calculate(f);self.assertEqual(f,original)
        self.assertEqual({s['id']:s['engineering_number'] for s in f['streams']},{s['id']:s['engineering_number'] for s in build_flowsheet(old_requirements())['streams']})


if __name__=='__main__':unittest.main()
