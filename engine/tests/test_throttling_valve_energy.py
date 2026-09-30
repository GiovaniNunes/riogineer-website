"""M16 public-path frozen acceptance, failure atomicity and stream ownership."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from benchmarks.throttling_valve import compare_production as comparison
from riogineer_engine.core import build_flowsheet,calculate,Invalid
from riogineer_engine.network_models import MODELS,ports
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.throttling_valve_energy import ValveFailure

REFERENCE=comparison.reference()


class Matrix(unittest.TestCase):pass


def positive(c):
    def test(self):self.assertTrue(all(x['passed'] for x in comparison.compare_case(c,comparison.evaluate(c['inputs']))))
    return test


def negative(c):
    def test(self):self.assertFalse(comparison.negative(c)['accepted_outlet'])
    return test


for c in REFERENCE['cases']:setattr(Matrix,'test_positive_'+c['case_id'],positive(c))
for c in REFERENCE['negative_cases']:setattr(Matrix,'test_negative_'+c['case_id'],negative(c))


class Integration(unittest.TestCase):
    def test_exactly_one_material_port_pair(self):
        self.assertEqual(ports('throttling_valve'),[dict(id='inlet',direction='in',kind='material'),dict(id='outlet',direction='out',kind='material')])

    def test_no_ps_dependency_and_no_heat_or_work_result(self):
        with patch.object(PengRobinsonProvider,'flash_PS',side_effect=AssertionError('Valve must not use PS')):
            r=comparison.evaluate(REFERENCE['cases'][0]['inputs'])
        e=r['equipment'][0]
        self.assertEqual(set(e['material_streams']),{'inlet','outlet'})
        self.assertFalse({'duty_W','work_W','fluid_power_W','efficiency'} & set(e))
        self.assertEqual(e['thermodynamics']['outlet']['classification'],'vapor_liquid')
        self.assertEqual(len(r['streams']),2)

    def test_public_failure_publishes_no_result(self):
        for name in ('PT','PH','FRESH_FINAL','HOLE','AMBIGUOUS'):
            with self.subTest(name=name),comparison.injection(name):
                with self.assertRaises(Invalid) as error:comparison.evaluate(REFERENCE['cases'][0]['inputs'])
                self.assertNotIn('PHTrial(',str(error.exception))
                self.assertLess(len(str(error.exception)),2000)

    def test_vl_inlet_is_not_valve_service(self):
        c=next(c for c in REFERENCE['separate_studies'] if c['case_id']=='TWO_PHASE_INLET')
        with self.assertRaisesRegex(Invalid,'inlet_service_scope'):comparison.evaluate(c['inputs'])

    def test_parameters_do_not_own_feed_or_temperature(self):
        for key,value in [('outlet_temperature_K',300.),('F_mol_s',100.),('pressure_ratio',.1),('Cv',1.),('efficiency',1.)]:
            r=comparison.requirements(REFERENCE['cases'][0]['inputs']);r['equipment'][0]['parameters'][key]=value
            with self.assertRaises(Invalid):build_flowsheet(r)

    def test_stream_changes_recompute_inlet_and_conserve_material(self):
        a=comparison.evaluate(REFERENCE['cases'][0]['inputs'])
        i=deepcopy(REFERENCE['cases'][0]['inputs']);i['F']*=2
        b=comparison.evaluate(i)
        da,db=[r['equipment'][0]['thermodynamics'] for r in (a,b)]
        self.assertEqual(db['F_mol_s'],2*da['F_mol_s'])
        self.assertEqual(da['outlet'],db['outlet'])
        self.assertNotEqual(a['input_sha256'],b['input_sha256'])


if __name__=='__main__':unittest.main()
