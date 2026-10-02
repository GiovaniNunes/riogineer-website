# Low-pressure separator-liquid pump prerequisite study

Non-production orchestration of unchanged thermodynamic routines. No production
pump support or configurable domain is added. See the root
`PRE_MILESTONE_20_LOW_PRESSURE_SEPARATOR_PUMP_QUALIFICATION.md` for conclusions.

From the repository root, verify without rewriting frozen artifacts:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/low_pressure_separator_pump/reference.py
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/compare.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/low_pressure_separator_pump -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/verify.py
```

For initial creation only, `--write` on reference.py, compare.py and verify.py
writes their respective new JSON artifacts in that order. Normal runs compare
byte-for-byte. Do not regenerate historical artifacts. No browser/server needed.
`preservation.json` captures hashes of all initially tracked working-tree files,
including both unrelated modified files. Only the master-context edit is exempt
from byte preservation. `verify.py` also checks unchanged HEAD and empty staging.

Independent environment: existing `.local/pre-m8-venv`, dependency pins and
third-party notices in `../pump_energy/configurable_scope/requirements.txt` and
`../pump_energy/configurable_scope/THIRD_PARTY_NOTICES.txt`. No new installation.
Reference JSON records actual versions, component/ideal Cp data, conventions,
installed Thermo source and Poling-data hashes and inherited benchmark hashes.
Those installed hashes/versions are checked against M19 before generation.
The reference imports benchmark-only Thermo/independent inverse code, never
RioGineer production numerics; a runtime module assertion enforces separation.
Reading historical production outlet T/P/composition as *inputs* is deliberate.
Expected H/S, phase and pump results are independently computed, not copied.

`production.json` contains the full 24-row inventory, unchanged material streams,
wrapper rejection, phase-specific separator H/S, PT calorics, boundary probes,
all inverse trials, comparisons and accepted/rejected/unresolved outcomes.
`reference.json` contains independent screening, separate phase diagnostics,
raw/refined saturation evidence, pump paths and endpoint bubble checks.
`candidate_ledger.json` lists every candidate and hashes every other study file.
`PLAN.md` records original criteria and the targeted refinement, preserving failed
raw bubble residuals and the rationale for two additional 8 MPa challenges.

The numerical prototype inherits M18 bookkeeping but explicitly uses a 500 K
PS residual-to-enthalpy allowance across the full inverse domain. Its independent
and production paths both use equilibrium PT inlet properties. Separate
phase-specific reference properties diagnose inlet representation; they never
replace an equilibrium failure. Identities additionally retain the complete actual
separator stream and zero power. Partial diagnostic states are not accepted outlets.

The frozen comparison deliberately retains numerical failure diagnostics, if any;
verification success means reproducible evidence and honest dispositions, not
that every candidate is accepted. No global convergence or experimental claim.
