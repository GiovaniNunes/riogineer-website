# Pre-M18 liquid pump-path study

Outcome: **passes for a narrower scope**. No production pump is implemented.
See [the qualification report](../../PRE_MILESTONE_18_LIQUID_PUMP_PATH_QUALIFICATION.md).

Run from the repository root using the existing environments:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/reference.py
engine/.venv/bin/python -B benchmarks/pump_energy/compare_production.py
engine/.venv/bin/python -B benchmarks/pump_energy/scope.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/pump_energy -p 'test_*.py' -v
```

The first three commands verify byte-identical artifacts. Add `--write` only for
intentional regeneration of these new artifacts, in the same order. Tests inspect
captured real executions and source hashes; generator/comparator verification
separately reruns thermodynamics. No application server is needed.

| File                                          | Purpose                                                                                       |
| --------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `reference.py`                                | Independent Thermo/direct-caloric PS/PH oracle, boundary and conditioning evidence            |
| `common.py`                                   | Fixed tolerances, candidate inputs and benchmark bookkeeping; no thermodynamic implementation |
| `liquid_pump_path_reference.json`             | Frozen independent numerical authority and provenance                                         |
| `compare_production.py`                       | Separate calls to unchanged production providers                                              |
| `production_comparison.json`                  | Production states, full scans, comparisons and controlled failures                            |
| `scope.py`                                    | Candidate ledger and executable exact-input scope proposal; not production pump validation    |
| `candidate_ledger.json`                       | All 20 candidates and their disposition; artifact hashes                                      |
| `test_reference.py`, `test_production.py`     | 18 focused evidence/consistency tests, including 13 invalid prototype input subcases          |
| `requirements.txt`, `THIRD_PARTY_NOTICES.txt` | Verified reference dependency pins and attribution                                            |

There are 13 accepted tuples, two PS failures, three unresolved positive-work
increments and two phase rejections. All 1,215 applicable field/policy comparisons
pass (827 numerical). The two PS-blocked paths remain rejected even though
independent-target PH diagnostics succeed. Exact identities do not invoke inverses.
The additional phase-label counterexample and saturation probes explain why a
general `single_liquid` check is insufficient for broader service admissibility.

Qualification is numerical agreement under shared PR/data assumptions plus
thermodynamic consistency, not experimental validation or cavitation safety.

## Configurable-scope extension

The separate [configurable study](configurable_scope/README.md) supports bounded
equimolar input ranges with phase witnesses and work guards, rather than an
exact-input allowlist. See [its qualification report](../../PRE_MILESTONE_18_CONFIGURABLE_PUMP_SCOPE_QUALIFICATION.md).
The first study and its conclusions above remain unchanged historical evidence.
No production pump has been implemented.
