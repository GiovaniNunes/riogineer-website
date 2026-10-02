"""Read-only M19 artifact checks; expensive matrix is explicitly reproduced separately."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class EvidenceTests(unittest.TestCase):
    def test_independent_freeze_and_boundary_reserve(self):
        r=json.loads((ROOT/'benchmarks/variable_composition_pump/reference.json').read_text())
        self.assertFalse(r['production_imported'])
        for p,h in r['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)
        self.assertEqual(r['boundary_summary']['accepted'],824)
        self.assertGreater(r['boundary_summary']['engineering_reserve_Pa'],338000)
        self.assertEqual(sum(c['accepted'] for c in r['cases']),53)
        self.assertEqual(len(r['cases']),64)
    def test_equipment_comparison_and_source_capture(self):
        r=json.loads((ROOT/'benchmarks/variable_composition_pump/equipment_comparison.json').read_text())
        self.assertTrue(r['passed']);self.assertEqual(r['case_count'],64)
        for p,h in (r['production_source_sha256']|r['reference_sha256']).items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)
    def test_separator_actual_outputs(self):
        r=json.loads((ROOT/'benchmarks/variable_composition_pump/separator_compatibility.json').read_text())
        self.assertEqual(len(r['cases']),25);self.assertEqual(r['direct_count'],1)
        self.assertFalse(r['production_network_integration'])
        for c in r['cases'][:-1]:self.assertFalse(c['direct'])
        c=r['cases'][-1];self.assertEqual(c['actual_liquid']['pressure_Pa_abs'],20e6)
        self.assertEqual(c['actual_liquid']['temperature_K'],300.)
        self.assertEqual(c['enthalpy_convention_residual_W'],0.)
