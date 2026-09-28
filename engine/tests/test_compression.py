import copy
import math
import unittest
from decimal import Decimal, localcontext
from unittest.mock import patch
from riogineer_engine.core import ROOT, loads, build_flowsheet, calculate, validate_requirements, Invalid
from riogineer_engine.network_models import MODELS, compressor, EquipmentResult


def requirements():
    return loads((ROOT / 'contracts/examples/milestone-6-requirements.json').read_text())


def expected(t=313.15, p=2000000, mass=22000):
    # Independent high-precision calculation, not the executable model or its outputs.
    with localcontext() as ctx:
        ctx.prec = 50
        d = lambda v: Decimal(str(v))
        ratio = d(6000000) / d(p)
        ts = d(t) * ((ratio.ln() * (d('1.3')-1) / d('1.3')).exp())
        ta = d(t) + (ts-d(t))/d('.75')
        gas = d(mass)/3600*d(2200)*(ta-d(t))
        return [float(v) for v in (ratio, ts, ta, gas, gas/d('.98'))]


class CompressionTests(unittest.TestCase):
    def test_reference_benchmark_mass_and_energy_boundary(self):
        r = requirements(); f = build_flowsheet(r); before = copy.deepcopy(f); o = calculate(f)
        self.assertEqual(f, before)
        e = next(e for e in o['equipment'] if e['type']=='compressor'); c = e['compression']
        for key, value, tolerance in zip(['pressure_ratio','isentropic_discharge_temperature_K','discharge_temperature_K','gas_power_W','shaft_power_W'], expected(), [1e-12,1e-10,1e-10,1e-6,1e-6]):
            self.assertAlmostEqual(c[key], value, delta=tolerance)
        gas, out = o['streams']['GAS_1'], o['streams']['COMPRESSED_GAS']
        self.assertEqual(out['component_mass_flow_kg_h'], gas['component_mass_flow_kg_h'])
        self.assertEqual(out['component_mass_fractions'], gas['component_mass_fractions'])
        self.assertEqual(out['mass_flow_kg_h'], 22000)
        self.assertEqual(out['pressure_Pa_abs'], 6000000)
        self.assertEqual(out['temperature_K'], c['discharge_temperature_K'])
        self.assertAlmostEqual(out['enthalpy_flow_W']-gas['enthalpy_flow_W'], c['gas_power_W'], delta=1e-6)
        self.assertEqual(e['duty_W'], 0)
        self.assertEqual(e['work_W'], c['gas_power_W'])
        self.assertAlmostEqual(c['shaft_power_W']*.98, c['gas_power_W'], delta=1e-6)
        for unit in o['equipment']:
            self.assertEqual(set(unit['mass_balance']['component_residual_kg_h'].values()), {0})
            self.assertEqual(unit['mass_balance']['total_residual_kg_h'], 0)
            self.assertLessEqual(abs(unit['energy_residual_W']), 1e-6)
        self.assertEqual(set(o['balances']['mass']['component_residual_kg_h'].values()), {0})
        self.assertEqual(o['balances']['mass']['total_residual_kg_h'], 0)
        energy=o['balances']['energy']
        self.assertAlmostEqual(energy['duty_W'], (77000*2200+550*4180)*20/3600, delta=1e-6)
        self.assertEqual(energy['process_work_W'], c['gas_power_W'])
        self.assertEqual(energy['shaft_power_W'], c['shaft_power_W'])
        self.assertAlmostEqual(energy['external_enthalpy_change_W'], energy['duty_W']+energy['process_work_W'], delta=1e-6)
        self.assertGreater(abs(energy['external_enthalpy_change_W']-energy['duty_W']-energy['shaft_power_W']), 1000)
        self.assertLessEqual(abs(energy['residual_W']), 1e-6)
        for s in o['streams'].values():
            for prop in s['properties'].values():
                self.assertIsNone(prop['value']); self.assertEqual(prop['status'],'not_calculated')

    def test_upstream_runtime_component_pressure_temperature_propagation(self):
        r=requirements(); r['feeds'][0]['state']['component_mass_flow_kg_h']['methane']=23000
        r['equipment'][0]['parameters']['separator'].update(temperature_K=323.15, pressure_Pa_abs=1500000)
        # Keep the other branch within the existing no-pressure-increase separator rule.
        r['equipment'][2]['parameters']['separator']['pressure_Pa_abs']=1500000
        seen=[]; execute=MODELS['compressor']['execute']
        def spy(unit, inputs, evaluate):
            seen.append(copy.deepcopy(inputs['inlet']))
            return execute(unit,inputs,evaluate)
        with patch.dict(MODELS['compressor'],execute=spy): o=calculate(build_flowsheet(r))
        for key,value in seen[0].items(): self.assertEqual(value,o['streams']['GAS_1'][key])
        self.assertEqual(seen[0]['temperature_K'],323.15)
        self.assertEqual(seen[0]['pressure_Pa_abs'],1500000)
        self.assertEqual(seen[0]['component_mass_flow_kg_h']['methane'],23000)
        c=next(e['compression'] for e in o['equipment'] if e['type']=='compressor')
        for key,value in zip(['pressure_ratio','isentropic_discharge_temperature_K','discharge_temperature_K','gas_power_W','shaft_power_W'],expected(323.15,1500000,23000)):
            self.assertAlmostEqual(c[key],value,delta=1e-6)

    def test_invalid_parameters_and_finite_enforcement(self):
        f=build_flowsheet(requirements()); unit=next(e for e in f['equipment'] if e['type']=='compressor')
        feed={'temperature_K':313.15,'pressure_Pa_abs':2000000,'component_mass_flow_kg_h':{'methane':22000,'n_hexane':0,'water':0},'enthalpy_flow_W':22000*2200*40/3600}
        cases={
            'discharge_pressure_Pa_abs':[2000000,1000000,0,-1,float('inf'),float('nan')],
            'cp_J_kg_K':[0,-1,float('inf'),float('nan')],
            'heat_capacity_ratio':[1,0,-1,float('inf'),float('nan')],
            'isentropic_efficiency':[0,-1,1.1,float('inf'),float('nan')],
            'mechanical_efficiency':[0,-1,1.1,float('inf'),float('nan')],
        }
        for key,values in cases.items():
            for value in values:
                with self.subTest(field=key,value=value):
                    u=copy.deepcopy(unit); u['operating_parameters'][key]=value
                    with self.assertRaises((ValueError,ArithmeticError)): compressor(u,{'inlet':feed},None)
        for field in ['temperature_K','pressure_Pa_abs']:
            for value in [0,-1,float('nan'),float('inf')]:
                state=copy.deepcopy(feed);state[field]=value
                with self.assertRaisesRegex(ValueError,'finite positive'):compressor(unit,{'inlet':state},None)
        state=copy.deepcopy(feed);state['component_mass_flow_kg_h']['methane']=0
        with self.assertRaisesRegex(ValueError,'mass flow'):compressor(unit,{'inlet':state},None)
        u=copy.deepcopy(unit);u['operating_parameters']['isentropic_efficiency']=1e-320
        with self.assertRaises((ValueError,ArithmeticError)):compressor(u,{'inlet':feed},None)
        with self.assertRaisesRegex(ValueError,'exactly one inlet'):compressor(unit,{},None)
        r=requirements();r['equipment'][3]['parameters']['isentropic_efficiency']=1e-320
        with self.assertRaisesRegex(Invalid,'finite'):calculate(build_flowsheet(r))
        for efficiency in ['isentropic_efficiency','mechanical_efficiency']:
            u=copy.deepcopy(unit);u['operating_parameters'][efficiency]=1
            result=compressor(u,{'inlet':feed},None)
            self.assertTrue(math.isfinite(result.work_W))

    def test_contracts_ports_and_caloric_basis_reject_inconsistent_inputs(self):
        for mutate in [lambda r:r['equipment'][3]['parameters'].pop('cp_J_kg_K'),
                       lambda r:r['equipment'][3]['parameters'].update(isentropic_efficiency=0),
                       lambda r:r['equipment'][3]['parameters'].update(inlet_phase='liquid'),
                       lambda r:r['connections'][-1]['source'].update(port_id='gas'),
                       lambda r:r['connections'][-1]['target'].update(owner_id='UNKNOWN'),
                       lambda r:r.update(schema_version='1.2')]:
            r=requirements();mutate(r)
            with self.assertRaises(Invalid):validate_requirements(r)
        r=requirements();r['equipment'][3]['parameters']['cp_J_kg_K']=2100
        with self.assertRaisesRegex(Invalid,'caloric basis'):calculate(build_flowsheet(r))
        r=requirements();r['equipment'][3]['parameters']['discharge_pressure_Pa_abs']=2000000
        with self.assertRaisesRegex(Invalid,'must exceed'):calculate(build_flowsheet(r))
        f=build_flowsheet(requirements());f['equipment'][3]['ports'].pop()
        with self.assertRaises(Invalid):calculate(f)
        f=build_flowsheet(requirements());f['streams'][-1]['specified_state']=copy.deepcopy(f['streams'][0]['specified_state'])
        with self.assertRaisesRegex(Invalid,'Only source'):calculate(f)

    def test_parallel_scheduling_reordering_renaming_and_stream_identity(self):
        r=requirements();f=build_flowsheet(r);original=copy.deepcopy(f['streams']);o=calculate(f)
        def assert_dependencies(order, names):
            sep,comp,heat,last=names
            self.assertLess(order.index(sep),order.index(comp));self.assertLess(order.index(sep),order.index(heat));self.assertLess(order.index(heat),order.index(last))
        assert_dependencies(o['execution']['equipment_order'],['SEP_1','COMPRESSOR_1','HEATER_1','SEP_2'])
        mapping={s['id']:s['engineering_number'] for s in f['streams']}
        self.assertEqual(len(set(mapping.values())),9)
        for key in ['equipment','streams','connections','sinks']:r[key].reverse()
        other=build_flowsheet(r)
        self.assertEqual({s['id']:s['engineering_number'] for s in other['streams']},mapping)
        self.assertEqual(calculate(other)['streams'],o['streams'])
        names={'SEP_1':'Z_SOURCE','COMPRESSOR_1':'Z_GAS','HEATER_1':'B_HEATER','SEP_2':'A_SECOND'}
        for e in r['equipment']:e['id']=names[e['id']]
        for c in r['connections']:
            for side in ['source','target']:c[side]['owner_id']=names.get(c[side]['owner_id'],c[side]['owner_id'])
        renamed=calculate(build_flowsheet(r));assert_dependencies(renamed['execution']['equipment_order'],list(names.values()))
        self.assertEqual(renamed['streams'],o['streams'])
        self.assertNotEqual(renamed['execution']['equipment_order'],[names[n] for n in o['execution']['equipment_order']])
        for _ in range(2):
            f['presentation']['layout']='compact';calculate(f);self.assertEqual(f['streams'],original)

    def test_original_oil_train_unchanged(self):
        old=calculate(build_flowsheet(loads((ROOT/'contracts/examples/milestone-5-requirements.json').read_text())))
        new=calculate(build_flowsheet(requirements()))
        for sid,state in old['streams'].items():self.assertEqual(new['streams'][sid],state)
        for unit in old['equipment']:self.assertEqual(next(e for e in new['equipment'] if e['id']==unit['id']),unit)

    def test_incorrect_work_and_cycles_fail(self):
        execute=MODELS['compressor']['execute']
        def bad(*args):
            e=execute(*args);return EquipmentResult(e.streams,e.duty_W,e.work_W+1,e.details)
        with patch.dict(MODELS['compressor'],execute=bad):
            with self.assertRaisesRegex(Invalid,'energy'):calculate(build_flowsheet(requirements()))
        r=requirements();r['connections'][0]['target'],r['connections'][-1]['target']=r['connections'][-1]['target'],r['connections'][0]['target']
        with self.assertRaisesRegex(Invalid,'Cycle'):build_flowsheet(r)
