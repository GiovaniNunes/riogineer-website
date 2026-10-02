# PRE-M21 PT iteration budget extension

Study only. Start with the root `PRE_MILESTONE_21_PT_ITERATION_BUDGET_QUALIFICATION.md`,
`PLAN.md`, and `summary.json`. The recommended finite-scope candidate is
`pr_high_accuracy_pt200@1`; legacy production remains at 100 and the two 8 MPa
challenges remain excluded by application scope.

## Evidence and code

- `baseline.json`: 513 task-start file hashes, HEAD, branch, index, status and master prefix.
- `common.py`: predeclared physical inputs and create-once/read-only artifact utilities.
- `capture_sources.py`, `sources.json`: actual M17 calculations and retained run identities.
- `reference.py`, `reference.json`: independent Thermo reference and dependency/data identity.
- `profile.py`: immutable opt-in profiles; isolated parameter injection into PS, PH and guard.
- `harness.py`: passive iteration tracing, actual source resolution and full pump chains.
- `compare.py`, `production.json`: complete settings, transformations, states, scans, residuals,
  counts, fresh validations, source checks, balances, compatibility and scope results.
- `candidate_ledger.json`: original named-reference comparisons; preserves 195 failures.
- `phase_identity_reference.py`, `phase_identity_reference.json`: supplementary independent
  PIP, volume and density evidence for the six swapped reference phase names.
- `phase_identity_compare.py`, `phase_identity_comparison.json`, `qualified_ledger.json`:
  separately audited physical phase matching and final dispositions; no overwritten raw data.
- `test_budget.py`: physical-evidence assertions and separately identified synthetic guards.
- `performance.py`, `performance.json`: serial timing samples and deterministic work.
- `summarize.py`, `summary.json`: compact reproducible evidence for implementation planning.
- `logs/`: original regression failure, initial study failure, final tests and reproduction logs.
- `verify.py`, `manifest.json`: complete extension hashes and task-start preservation.

## Read-only reproduction

Run from the repository root with the existing environments. No installation, service,
frontend suite, fixture rewrite or production change is needed. `-B` suppresses bytecode.

```sh
engine/.venv/bin/python -B benchmarks/pt_iteration_budget/verify.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/verify.py
engine/.venv/bin/python -B benchmarks/pt_iteration_budget/capture_sources.py
.local/pre-m8-venv/bin/python -B benchmarks/pt_iteration_budget/reference.py
engine/.venv/bin/python -B benchmarks/pt_iteration_budget/compare.py
.local/pre-m8-venv/bin/python -B benchmarks/pt_iteration_budget/phase_identity_reference.py
engine/.venv/bin/python -B benchmarks/pt_iteration_budget/phase_identity_compare.py
engine/.venv/bin/python -B benchmarks/pt_iteration_budget/performance.py
engine/.venv/bin/python -B benchmarks/pt_iteration_budget/summarize.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/pt_iteration_budget -p 'test_*.py' -v
```

Independent reference generation imports no production engine. `compare.py` uses four
worker **processes**, with deterministically ordered output; these are not delegated agents.
Fresh source reproduction compares numerical/structural results and retains the frozen
original UUIDs; new UUIDs are not falsely expected to match. Default numerical artifact
commands compare canonical bytes rather than overwriting them. `--write` is only for
first creation and refuses existing destinations. The supplementary phase audit remains
separate from raw reference reproduction.

Performance verification replays deterministic work and result hashes, not elapsed seconds.
For new timings without altering evidence:

```sh
engine/.venv/bin/python -B benchmarks/pt_iteration_budget/performance.py --output /tmp/pt-budget-new-timings.json
```

Use a new output path. Method: serial, untraced, one warmup per case/profile, three timed
repetitions with rotated profile order; every repetition checks the same result/work.
Existing services were left alone, so elapsed times include ordinary host scheduling noise.

Existing regression command actually executed:

```sh
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_pr_eos test_pr_flash test_pr_pt_boundary test_pr_pt_vapor_parent test_pr_caloric test_pr_ps_flash test_pr_ph_flash test_pr_ph_intervals test_pump_energy test_separator_pump_integration -v
```

That command is **not all-green**: 274 tests, 273 passed, one historical M20
`test_preservation` next-env hash failure. Do not alter the assertion or current config
bytes to make it pass. The initial new 13-test run also failed its raw-reference comparison
assertion; the independent phase-identity audit is the documented resolution. Final new
suite: 14 passed. Frozen logs preserve both outcomes.

The manifests protect historical/prerequisite bytes separately from the current study.
The master prefix is protected, and the new manifest also hashes this task's appendix.
Minimum planning upload: root report, `summary.json`, `profile.py`, `PLAN.md`.
For a reproducible review, provide this entire directory plus the existing repository
and prerequisite references; the compact upload does not replace full numerical evidence.
