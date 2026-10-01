# Configurable liquid-pump scope study

See [the qualification report](../../../PRE_MILESTONE_18_CONFIGURABLE_PUMP_SCOPE_QUALIFICATION.md)
for supported ranges, phase evidence and limitations. No production pump is implemented.

The prototype supports fixed equimolar methane/n-hexane, 300–350 K inlet,
20–25 MPa inlet pressure, discharge up to 30 MPa, eta 0.6–1 and flow 5–200 mol/s.
Positive rise must be at least 10,000 Pa; exact identity is separate. All three
states must pass the temperature/pressure, 16 MPa liquid-witness and work guards.
This is a numerically supported operational region, not a guaranteed global envelope.

From repository root, verify without writing:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/configurable_scope/reference.py
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/configurable_scope/boundary_refinement.py
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/configurable_scope/boundary_equations.py
engine/.venv/bin/python -B benchmarks/pump_energy/configurable_scope/compare_production.py
engine/.venv/bin/python -B benchmarks/pump_energy/configurable_scope/ledger.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/pump_energy/configurable_scope -p 'test_*.py' -v
```

Only explicit `--write` regenerates a new extension artifact. Do not regenerate
the first study. Dependencies reuse the existing isolated environments and pinned
requirements; no application server or production-library installation is needed.

- `PLAN.md`: sampling and acceptance choices made before comparison.
- `reference.py`, `reference.json`: independent path, boundary and sensitivity evidence.
- `boundary_refinement.py/.json`: tighter library checks and four alternate-branch investigations.
- `boundary_equations.py/.json`: separate coexistence-equation and stable-side checks.
- `compare_production.py`, `production.json`: unchanged public-provider comparisons and flow scaling.
- `policy.py`, `runtime.py`: configurable benchmark guards, with no reference-table lookup.
- `ledger.py`, `candidate_ledger.json`: all outcomes, including sub-floor rejections and alternate boundary returns.
- `test_scope.py`: 13 focused test methods; captured real cases and labelled synthetic failure tests.
- `requirements.txt`, `THIRD_PARTY_NOTICES.txt`: pinned reference dependencies and notices.

There are 46 candidate entries (42 distinct intensive tuples), eight off-grid
holdouts, 149 boundary temperatures, 190 flow-scaling records and 5,522 passing
field/policy checks. The policy accepts 38 entries (34 distinct tuples), rejects
eight below-floor entries and admits continuous values within its guarded ranges.
No experimental, hydraulic, NPSH or cavitation qualification is claimed.
