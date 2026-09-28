"""M7 qualification: independent Decimal oracle, archived process fingerprints, no EOS."""
import copy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
import hashlib
import json
import math
import unittest
from unittest.mock import patch

from riogineer_engine.components import COMPONENTS, DATASET, UNITS, component
from riogineer_engine.thermodynamics import MolecularCompositionProvider, enrich_results
from riogineer_engine.core import ROOT, Invalid, build_flowsheet, calculate, _calculate_process, validate_schema

CASES = ['requirements.json', 'milestone-4-requirements.json', 'milestone-5-requirements.json', 'milestone-6-requirements.json']


def requirement(name=CASES[-1]):
    return json.loads((ROOT / 'contracts/examples' / name).read_text())


def process_digest(result):
    payload = {key: result[key] for key in ('equipment', 'balances')}
    payload['streams'] = {sid: {k: v for k, v in state.items() if k not in ('properties', 'property_provenance')}
                          for sid, state in result['streams'].items()}
    if 'execution' in result:
        payload['execution'] = result['execution']
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


# Captured before M7 from the validated M3–6 engines, excluding run/provenance/property metadata.
BASELINE = {'requirements.json': '49969632cb8bf43afe689411c81257d60706e86f0ab1f30cc51f93083c198110', 'milestone-4-requirements.json': '01ce791c2bc8408d5dbb82a422f5f4e91fb9cf88ffb7a03d07094faa4e17ebf5', 'milestone-5-requirements.json': '285912aa2f36daf6450a19c36cc99c642319c2294d275178f8cf9e4e456a85e1', 'milestone-6-requirements.json': '3629760cf01a65b9fd110f04f6185c61f8f50e898e3fc1a928002b178dbf18ff'}


class ThermodynamicsTests(unittest.TestCase):
    def setUp(self):
        self.f = build_flowsheet(requirement())
        self.r = calculate(self.f)
        self.provider = MolecularCompositionProvider()

    def assert_oracle(self, state):
        # Independent high precision conversion; only the authoritative MW inputs are shared.
        with localcontext() as ctx:
            ctx.prec = 50
            m = {c: Decimal(str(v)) for c, v in state['component_mass_flow_kg_h'].items()}
            n = {c: v / Decimal(str(component(c).molecular_weight)) for c, v in m.items()}
            total = sum(n.values())
            p = state['properties']
            self.assertAlmostEqual(p['molar_flow']['value'], float(total), delta=1e-10)
            for c in m:
                actual = p['component_molar_flow']['value'][c]
                self.assertAlmostEqual(actual, float(n[c]), delta=1e-10)
                self.assertAlmostEqual(actual * component(c).molecular_weight, float(m[c]), delta=1e-8)
                if total:
                    self.assertAlmostEqual(p['molar_composition']['value'][c], float(n[c]/total), delta=1e-12)
            if total:
                mw = p['molecular_mass']['value']
                self.assertAlmostEqual(mw, float(sum(m.values()) / total), delta=1e-12)
                self.assertAlmostEqual(mw * p['molar_flow']['value'], state['mass_flow_kg_h'], delta=3e-8)
                self.assertAlmostEqual(sum(p['molar_composition']['value'].values()), 1, delta=1e-12)

    def test_database_constants_units_version_and_immutability(self):
        expected = {'methane': (16.0428,190.564,4599200,.01142),
                    'n_hexane': (86.17536,507.82,3044115.328359688,.3003189315498438),
                    'water': (18.015268,647.096,22064000,.3442920843)}
        self.assertEqual(DATASET, 'riogineer_components@1.0')
        self.assertEqual(dict(UNITS), dict(molecular_weight='kg/kmol', critical_temperature='K', critical_pressure='Pa absolute', acentric_factor='dimensionless'))
        self.assertEqual(set(COMPONENTS), set(expected))
        for key, values in expected.items():
            c = component(key)
            self.assertEqual(c.id, key)
            self.assertTrue(c.display_name)
            self.assertIn('/v7.1.0/', c.source)
            self.assertEqual((c.molecular_weight,c.critical_temperature,c.critical_pressure,c.acentric_factor), values)
            self.assertTrue(all(math.isfinite(v) for v in values))
            with self.assertRaises(FrozenInstanceError): c.display_name = 'changed'
        with self.assertRaises(TypeError): COMPONENTS['x'] = component('water')
        for key in ['METHANE', 'Methane', 'n-Hexane', 'unknown']:
            with self.assertRaises(ValueError): component(key)
        self.assertEqual(replace(component('methane'), display_name='METHANE').id, 'methane')

    def test_database_rejects_invalid_values(self):
        for field in ['molecular_weight','critical_temperature','critical_pressure','acentric_factor']:
            for value in [float('nan'),float('inf'),True] + ([] if field == 'acentric_factor' else [0,-1]):
                with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                    replace(component('methane'), **{field:value})

    def test_feed_and_all_products_independent_decimal_benchmark(self):
        for state in self.r['streams'].values():
            self.assert_oracle(state)
        for sid, species, flow in [('GAS_1','methane',22000),('COMPRESSED_GAS','methane',22000),('GAS_2','n_hexane',3850),('WATER_2','water',495)]:
            state = self.r['streams'][sid]; p = state['properties']
            self.assertEqual(state['component_mass_flow_kg_h'][species], flow)
            self.assertEqual(p['molar_composition']['value'][species], 1)
            self.assertAlmostEqual(p['molecular_mass']['value'], component(species).molecular_weight, delta=1e-12)
            for c in COMPONENTS:
                if c != species:
                    self.assertEqual(p['molar_composition']['value'][c], 0)
                    self.assertEqual(p['component_molar_flow']['value'][c], 0)
        self.assertEqual(self.r['streams']['OIL_PRODUCT']['component_mass_flow_kg_h'], dict(methane=0,n_hexane=73150,water=55))

    def test_temperature_and_pressure_do_not_change_composition(self):
        streams = self.r['streams']
        for a,b in [('OIL_1','HEATED_OIL'),('GAS_1','COMPRESSED_GAS')]:
            self.assertEqual(streams[a]['properties'], streams[b]['properties'])
            self.assertEqual(streams[a]['property_provenance'], streams[b]['property_provenance'])
            self.assertNotEqual(streams[a]['temperature_K'], streams[b]['temperature_K'])
        for sid,t in [('OIL_1',313.15),('HEATED_OIL',333.15)]:
            self.assertEqual(streams[sid]['component_mass_flow_kg_h'], dict(methane=0,n_hexane=77000,water=550))
            self.assertEqual(streams[sid]['mass_flow_kg_h'],77550)
            self.assertEqual(streams[sid]['temperature_K'],t)

    def test_runtime_input_changes_and_renamed_streams(self):
        r = requirement(); r['feeds'][0]['state']['component_mass_flow_kg_h']['methane'] = 23000
        f = build_flowsheet(r)
        for s in f['streams']: s['id'] = 'X_' + s['id']
        for c in f['connections']: c['stream_id'] = 'X_' + c['stream_id']
        output = calculate(f)
        self.assertEqual(output['streams']['X_COMPRESSED_GAS']['component_mass_flow_kg_h']['methane'],23000)
        for state in output['streams'].values(): self.assert_oracle(state)

    def test_zero_flow_ratios_and_unavailable_properties(self):
        r = requirement(CASES[0]); r['equipment'][0]['parameters']['recovery_fractions']['methane'].update(gas=0,oil=1)
        out = calculate(build_flowsheet(r)); zero = out['streams']['GAS']['properties']
        self.assertEqual(zero['molar_flow']['value'],0)
        self.assertEqual(zero['molar_flow']['status'],'calculated')
        self.assertTrue(all(v == 0 for v in zero['component_molar_flow']['value'].values()))
        for name in ['molar_composition','molecular_mass']:
            self.assertIsNone(zero[name]['value']); self.assertEqual(zero[name]['status'],'not_calculated')
        for state in out['streams'].values():
            for name in ['density','gas_volumetric_flow','oil_volumetric_flow','water_volumetric_flow']:
                self.assertIsNone(state['properties'][name]['value'])

    def test_invalid_composition_and_state_fail_explicitly(self):
        base = self.r['streams']['FEED']
        for val in [-1, float('nan'), float('inf'), True]:
            s = copy.deepcopy(base); s['component_mass_flow_kg_h']['methane'] = val
            with self.assertRaises(ValueError): self.provider.enrich(s)
        for change in [dict(component_mass_flow_kg_h={'unknown':110000}),dict(mass_flow_kg_h=110001),dict(temperature_K=0),dict(pressure_Pa_abs=float('inf')),dict(component_mass_flow_kg_h={})]:
            with self.assertRaises(ValueError): self.provider.enrich(dict(base,**change))
        tiny = replace(component('methane'), molecular_weight=1e-320)
        with patch('riogineer_engine.thermodynamics.component',return_value=tiny), self.assertRaises(ValueError):
            self.provider.enrich(base)
        with patch('riogineer_engine.thermodynamics.MolecularCompositionProvider.enrich',side_effect=ValueError('bad property')), self.assertRaises(Invalid):
            calculate(self.f)

    def test_state_provider_provenance_and_capability_boundary(self):
        s = self.provider.enrich(self.r['streams']['FEED'])
        self.assertEqual(s.temperature_K,313.15); self.assertEqual(s.pressure_Pa_abs,2e6)
        self.assertEqual(s.provenance.component_dataset,DATASET)
        self.assertEqual(self.provider.capabilities, frozenset({'molecular_composition'}))
        self.assertFalse(hasattr(self.provider,'flash_pt'))
        self.assertFalse(hasattr(s,'phase_state'))
        with self.assertRaises(TypeError): s.composition.component_mass_flow_kg_h['water'] = 1
        for state in self.r['streams'].values():
            p = state['property_provenance']
            self.assertEqual(p['provider'],self.provider.identifier)
            self.assertEqual(p['input_basis'],'component_mass_flow_kg_h')
            self.assertEqual(p['molecular_weights_kg_kmol'], {c:component(c).molecular_weight for c in state['component_mass_flow_kg_h']})

    def test_all_previous_process_fingerprints_and_old_contract_readers(self):
        for name in CASES:
            with self.subTest(case=name):
                f = build_flowsheet(requirement(name)); original = copy.deepcopy(f)
                legacy = _calculate_process(f); result = calculate(f)
                self.assertEqual(process_digest(result),BASELINE[name])
                self.assertEqual(f,original)
                self.assertEqual(result['schema_version'],'1.5')
                self.assertEqual(result['process_result_version'],legacy['schema_version'])
                validate_schema('results',legacy); validate_schema('results',result)
                self.assertEqual(enrich_results(legacy)['streams'],result['streams'])
                before = copy.deepcopy(legacy); enrich_results(legacy); self.assertEqual(legacy,before)
        legacy = _calculate_process(build_flowsheet(requirement(CASES[0])))
        legacy['schema_version']='1.0'
        for state in legacy['streams'].values(): del state['properties']
        validate_schema('results',legacy)

    def test_repeat_layout_reorder_regeneration_identity(self):
        original = copy.deepcopy(self.f['streams'])
        self.f['streams'].reverse(); self.f['connections'].reverse()
        self.f['presentation']['layout']='compact'
        for _ in range(2): self.assertEqual(calculate(self.f)['streams'],self.r['streams'])
        self.assertEqual(build_flowsheet(requirement())['streams'],original)
        self.assertEqual(self.f['streams'],list(reversed(original)))
