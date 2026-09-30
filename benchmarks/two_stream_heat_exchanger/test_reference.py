"""Independent Pre-M15 acceptance; no production exchanger imports."""
import ast
from copy import deepcopy
import importlib.metadata
import json
from pathlib import Path
import sys
import unittest

try:
    from . import reference as ref
except ImportError:
    import reference as ref


class FrozenQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=ref.build()

    def test_frozen_byte_reproduction(self):
        self.assertEqual(ref.encode(self.evidence),ref.ARTIFACT.read_text())

    def test_independent_import_graph(self):
        self.assertFalse(any(n.startswith('riogineer_engine') for n in sys.modules))
        for name in self.evidence['metadata']['source_sha256']:
            tree=ast.parse((ref.ROOT/name).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith('riogineer_engine'))
                if isinstance(node,ast.Import):self.assertFalse(any(n.name.startswith('riogineer_engine') for n in node.names))

    def test_dependency_pins(self):
        for row in (ref.HERE/'requirements.txt').read_text().splitlines():
            if row and not row.startswith('#'):
                name,version=row.split('==');self.assertEqual(importlib.metadata.version(name),version)

    def test_call_order_matrix(self):
        self.assertEqual({x['after'] for x in self.evidence['call_order']},{'clean','positive','phase','negative','PH_failure','reciprocal_first'})
        self.assertTrue(all(x['byte_identical'] for x in self.evidence['call_order']))

    def test_reference_contains_no_machine_paths(self):
        text=ref.encode(self.evidence)
        for prefix in ['/Users/','/home/','/tmp/']:self.assertNotIn(prefix,text)

    def test_two_side_material_identity(self):
        for c in self.evidence['cases']+self.evidence['phase_studies']:
            for side in ['hot','cold']:
                material=c['result']['material'][side];self.assertEqual(material['z_in'],material['z_out'])
                self.assertEqual(material['F_in_mol_s'],material['F_out_mol_s'])
                self.assertEqual(material['z_out'],c['inputs'][side]['z'])

    def test_reciprocal_both_directions_and_fresh_final(self):
        directions=set()
        for c in self.evidence['cases']:
            r=c['result'];rr=c['reciprocal']['result'];directions.add((r['specification_mode'],rr['specification_mode']))
            self.assertEqual(r['PH']['candidate_count'],1);self.assertEqual(rr['PH']['candidate_count'],1)
            self.assertEqual(r['PH']['final_evaluations'],1);self.assertEqual(rr['PH']['final_evaluations'],1)
            self.assertEqual([x['grid_points'] for x in c['reciprocal']['refinement']],[256,512])
        self.assertEqual(directions,{('A','B'),('B','A')})

    def test_zero_duty_pressure_is_not_isothermal(self):
        rows={c['case_id']:c for c in self.evidence['cases']}
        for name in ['ZERO_DUTY','ZERO_DUTY_COLD_DROP']:
            r=rows[name]['result'];self.assertEqual(r['Q_hot_W'],0.)
            self.assertLessEqual(abs(r['Q_cold_W']),r['energy_allowance_W'])
        self.assertGreater(abs(rows['ZERO_DUTY_COLD_DROP']['result']['states']['cold_out']['T_K']-300.),1e-6)

    def test_pressure_and_composition_do_not_cross_wall(self):
        r=ref.calculate(ref.BASE)
        for change in [dict(cold=dict(Pout=9e4)),dict(cold=dict(z=[1.,0.]))]:
            alt=ref.calculate(ref.patch(**change));self.assertEqual(alt['status'],'success')
            for end in ['in','out']:self.assertEqual(r['states']['hot_'+end],alt['states']['hot_'+end])
            self.assertEqual(r['Q_hot_W'],alt['Q_hot_W'])

    def test_inputs_not_mutated(self):
        spec=deepcopy(ref.BASE);before=deepcopy(spec);ref.calculate(spec);self.assertEqual(spec,before)

    def test_crossing_not_design_feasibility(self):
        c=next(c for c in self.evidence['temperature_scope'] if c['case_id']=='TERMINAL_CROSSING')
        self.assertEqual(c['thermodynamic']['status'],'success')
        self.assertEqual(c['recommended_equipment_status'],'terminal_temperature_crossing')
        s=c['thermodynamic']['states'];self.assertGreater(s['cold_out']['T_K'],s['hot_out']['T_K'])

    def test_phase_and_gap_evidence_remain_separate(self):
        for c in self.evidence['phase_studies']:
            self.assertFalse(c['accepted_primary_scope'])
            self.assertFalse(c['primary_service_result']['accepted_complete_exchanger_result'])
            self.assertEqual(c['primary_service_result']['status'],'phase_service_scope')
        gap=next(c for c in self.evidence['negative_cases'] if c['case_id']=='PURE_COEXISTENCE_GAP')
        self.assertEqual(gap['result']['status'],'ph_nonconvergence')


def positive(index):
    def test(self):
        c=self.evidence['cases'][index]
        self.assertTrue(c['passed']);self.assertTrue(c['result']['accepted_complete_exchanger_result'])
        self.assertTrue(all(x['passed'] for x in c['checks']))
    return test


def phase(index):
    def test(self):
        c=self.evidence['phase_studies'][index]
        self.assertTrue(c['passed']);self.assertFalse(c['accepted_primary_scope'])
        self.assertEqual([x['grid_points'] for x in c['refinement']],[256,512,128])
    return test


def negative(index):
    def test(self):
        c=self.evidence['negative_cases'][index]
        self.assertTrue(c['passed']);self.assertFalse(c['result']['accepted_complete_exchanger_result'])
        self.assertNotIn('states',c['result'])
    return test


for i,c in enumerate(ref.positive_specs()):setattr(FrozenQualification,'test_positive_'+c['case_id'],positive(i))
for i,c in enumerate(ref.phase_specs()[0]):setattr(FrozenQualification,'test_phase_'+c['case_id'],phase(i))
for i,c in enumerate(ref.negative_specs()[0]):setattr(FrozenQualification,'test_negative_'+c['case_id'],negative(i))

if __name__=='__main__':unittest.main()
