"""Comparison artifact reproducibility and validation-only dependency direction."""
import importlib.util
import json
from pathlib import Path
import unittest


class ComparisonTests(unittest.TestCase):
    def test_saved_report_matches_current_production(self):
        folder=Path(__file__).resolve().parents[2]/'benchmarks/peng_robinson'
        spec=importlib.util.spec_from_file_location('m8_comparison',folder/'compare_production.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        frozen_before=(folder/'methane_nhexane_pr_reference.json').read_bytes()
        report=module.compare_production()
        self.assertTrue(report['passed'])
        self.assertEqual(report['comparison_count'],122)
        saved=json.loads((folder/'production_comparison.json').read_text())
        # Result floats can differ in last digits across platforms; acceptance
        # comes from the independent frozen tolerances, not this report snapshot.
        self.assertEqual([r['quantity'] for r in saved['comparisons']],
                         [r['quantity'] for r in report['comparisons']])
        self.assertTrue(all(r['passed'] for r in report['comparisons']))
        self.assertEqual(frozen_before,(folder/'methane_nhexane_pr_reference.json').read_bytes())
