"""Executable benchmark scope proposal; not a registered production pump guard."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmarks.pump_energy.common import HERE, REFERENCE, PRODUCTION, digest, encode, validate


def ledger():
    ref, prod = [json.loads(p.read_text()) for p in (REFERENCE, PRODUCTION)]
    assert prod['reference_sha256'] == digest(REFERENCE)
    rows = []
    for r, p in zip(ref['cases'], prod['cases']):
        assert r['case_id'] == p['case_id']
        rs, ps = r['result']['status'], p['result']['status']
        admitted = rs == ps == 'accepted' and p['comparisons_passed']
        reason = ('Exact tested operating case; stable liquid, resolved work and independent comparison' if admitted
                  else 'Production PS whole-scan rejection; independent path available' if ps == 'production_failure'
                  else 'Positive work is insufficiently resolved under fixed error budget' if ps == 'unresolved_work'
                  else 'Inlet is outside liquid service' if ps == 'unsupported_phase'
                  else 'Unresolved reference or comparison failure')
        rows.append(dict(case_id=r['case_id'], group=r['group'], inputs=r['inputs'],
            reference_status=rs, production_status=ps, stage=p['result']['stage'],
            admitted_to_proposed_scope=admitted, reason=reason))
    return dict(reference_sha256=digest(REFERENCE), production_sha256=digest(PRODUCTION),
        policy='Exact tested T/P/z/eta/flow tuples only, including two identity tuples; no interpolation or rectangular envelope',
        runtime_status='Benchmark policy proposal only; no production pump',
        rows=rows, reference_counts=dict(Counter(r['reference_status'] for r in rows)),
        production_counts=dict(Counter(r['production_status'] for r in rows)))


def admissible(i, evidence):
    """A narrow enforceable option avoiding an unqualified general critical guard."""
    if validate(i):
        return False
    keys = ('T1', 'P1', 'P2', 'eta', 'flow', 'z')
    return any(r['admitted_to_proposed_scope'] and all(i[k] == r['inputs'][k] for k in keys)
               for r in evidence['rows'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = encode(ledger())
    path = HERE/'candidate_ledger.json'
    if args.write:
        path.write_text(data)
    else:
        assert path.read_text() == data
    print('PASS candidate ledger')
