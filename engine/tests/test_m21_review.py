"""Regression checks for the read-only source replay envelope."""
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmarks.m21_pt200.capture_sources import validate_replay
from riogineer_engine.core import build_flowsheet, calculate
from riogineer_engine.milestone17 import requirements

class SourceReplayReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.captured = next(iter(json.loads((ROOT / 'benchmarks/m21_pt200/sources.json').read_text()).values()))
        cls.inputs = cls.captured['inputs']
        cls.flow = build_flowsheet(requirements(**cls.inputs))
        cls.current = calculate(cls.flow)

    def test_current_replay(self):
        validate_replay(self.inputs, self.flow, self.current, self.captured)

    def test_meaningful_mismatches_rejected(self):
        changes = {
            'balances': lambda r: r.__setitem__('balances', {}),
            'semantic': lambda r: r.__setitem__('input_sha256', '0' * 64),
            'requirements': lambda r: r.__setitem__('requirements_sha256', '0' * 64),
            'case': lambda r: r.__setitem__('case_id', 'wrong'),
            'run': lambda r: r.__setitem__('run_id', self.captured['result']['run_id']),
            'implementation': lambda r: r['engine'].__setitem__('implementation_sha256', '0' * 64),
            'evaluator': lambda r: r['engine'].__setitem__('evaluator_sha256', '0' * 64),
            'engine_fields': lambda r: r['engine'].__setitem__('unexpected', True),
            'result_fields': lambda r: r.__setitem__('unexpected', True),
            'streams': lambda r: r.__setitem__('streams', []),
        }
        for label, change in changes.items():
            with self.subTest(label):
                result = copy.deepcopy(self.current)
                change(result)
                with self.assertRaises(AssertionError):
                    validate_replay(self.inputs, self.flow, result, self.captured)
        with self.assertRaises(AssertionError):
            validate_replay({}, self.flow, self.current, self.captured)
