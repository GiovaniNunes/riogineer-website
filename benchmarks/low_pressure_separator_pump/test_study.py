"""Focused evidence/invariant tests. Real numerical reproduction is separate."""
import json,sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.low_pressure_separator_pump.common import *
from benchmarks.low_pressure_separator_pump.verify import verify_preservation

class Study(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((HERE/'reference.json').read_text());cls.p=json.loads((HERE/'production.json').read_text())
    def test_preservation(self):verify_preservation()
    def test_inventory(self):
        self.assertEqual(len(self.p['inventory']),24)
        self.assertEqual(sum(c['absent'] for c in self.p['inventory']),5)
        for c,old in zip(self.p['inventory'],inventory()):
            self.assertEqual(c['actual_liquid'],old['actual_liquid'])
            self.assertNotEqual(c['wrapper'],'accepted')
            if not c['absent']:
                e=c['independent_phase_errors']
                self.assertLessEqual(abs(e['H']),h_budget(c['phase_H']))
                self.assertLessEqual(abs(e['S']),1e-8+1e-11*abs(c['phase_S']))
                self.assertAlmostEqual(c['actual_liquid']['enthalpy_flow_W'],c['molar_flow_mol_s']*c['phase_H'],places=7)
    def test_local_boundary(self):
        for c in self.r['screen']:
            if c.get('absent'):continue
            b=c['boundary'];self.assertNotIn('error',b)
            self.assertEqual(b['sides'],['vapor_liquid','single_liquid'])
            self.assertGreater(b['composition_gap'],.01)
            self.assertGreater(b['Z_gap'],.01)
            self.assertLessEqual(max(map(abs,b['refined']['residual'])),2e-10)
            self.assertLessEqual(abs(b['refined']['library_difference_Pa']),1.)
            self.assertEqual(b['refined']['sides'],['vapor_liquid','single_liquid'])
            self.assertEqual(len(c['probes']),7)
    def test_acceptance_invariants(self):
        for c in self.p['cases']:
            self.assertFalse(c['production_supported'])
            if c['disposition']!='accepted_tuple':continue
            self.assertTrue(all(k['passed'] for k in c['checks']))
            r=c['result'];m=r['metrics'];i=c['inputs']
            self.assertLessEqual(abs(m['energy_identity_residual_W']),64*sys.float_info.epsilon*max(1,abs(i['flow']*r['states']['inlet']['H_eq_J_mol']),abs(i['flow']*r['states']['outlet']['H_eq_J_mol'])))
            for s in r['states'].values():self.assertTrue(liquid(s))
            if m['identity']:
                self.assertEqual(m['W_recovered_W'],0);self.assertIsNone(m['reconstructed_efficiency'])
                self.assertEqual(r['states']['inlet'],r['states']['outlet'])
                actual=next(x['actual_liquid'] for x in inventory() if x['case_id']==c['source'])
                self.assertEqual(r['preserved_identity_stream'],actual)
            else:self.assertLessEqual(r['work_screen']['ratio'],1e-4)
    def test_negatives_and_small_work(self):
        cs={c['case_id']:c for c in self.p['cases']}
        for n in ('INVALID_ETA0.0','INVALID_ETA0.59','INVALID_ETA1.01','PRESSURE_DECREASE','ABSENT_LIQUID','BULK_VL','VAPOR','SMALL10.0','SMALL100.0'):
            self.assertNotEqual(cs[n]['disposition'],'accepted_tuple')
    def test_scaling(self):
        cs={c['case_id']:c for c in self.p['cases']};base=cs['PH_FLASH_DP1000000.0']
        for n in ('SCALED5.0','SCALED17.3','SCALED200.0'):
            c=cs[n];self.assertEqual(c['result']['states'],base['result']['states'])
            if 'metrics' in c['result']:
                self.assertAlmostEqual(c['result']['metrics']['W_recovered_W']/c['inputs']['flow'],base['result']['metrics']['delta_h_J_mol'],places=10)
    def test_real_solver_holes_retained(self):
        cases={c['case_id']:c for c in self.p['cases']}
        for name in ('PT_BUBBLE_BELOW_8MPA','PT_BUBBLE_ABOVE_8MPA'):
            c=cases[name];self.assertEqual(c['disposition'],'unresolved')
            self.assertEqual(c['result']['stage'],'PS')
            self.assertNotIn('outlet',c['result']['states'])
            self.assertEqual(len(c['result']['diagnostics']['PS']['failures']),2)
    def test_independent_import_boundary(self):
        self.assertFalse(self.r['production_imported'])
        for name in ('reference.py','common.py'):
            s=(HERE/name).read_text();self.assertNotIn('from riogineer_engine',s);self.assertNotIn('import riogineer_engine',s)

if __name__=='__main__':unittest.main()
