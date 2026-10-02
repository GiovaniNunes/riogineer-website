# M21 implementation verification

Production profile: `pr_high_accuracy_pt200@1`. Read `MILESTONE_21.md` for the API,
finite qualification, test outcomes and open review items. This directory never
imports the qualification's AST parameterization. `profile.py` calls real provider
APIs; its observer subclass records evaluations through the provider's existing
method dispatch. `harness.py` reuses only study orchestration and diagnostics, not
a thermodynamic solver. Independent expected values remain in frozen prerequisite
artifacts; no reference generator is run or expected value regenerated here.

## Read-only reproduction

From the repository root, using the existing Python environment:

```sh
engine/.venv/bin/python -B benchmarks/m21_pt200/verify.py
engine/.venv/bin/python -B benchmarks/m21_pt200/compare.py
engine/.venv/bin/python -B benchmarks/m21_pt200/evidence.py
engine/.venv/bin/python -B benchmarks/m21_pt200/capture_sources.py
engine/.venv/bin/python -B benchmarks/m21_pt200/integrity_audit.py
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_pt200_profile -v
```

Comparison uses four worker processes and canonical ordered JSON. Numerical output
and evaluation traces are compared byte-for-byte to this implementation's artifacts.
The separate evidence adapter compares against the frozen historical numerical
results, excluding only the newly explicit `numerical_profile` provenance for PT200.
It never removes a numerical setting, residual or iteration count to make them agree.
Default100 result shapes and numerical data remain unchanged.

`capture_sources.py` re-executes actual sources and compares the complete result envelope, including balances, streams/equipment,
requirements, units, status and all non-implementation engine provenance. Its `source_replay.json` records captured and current
engine/input fingerprints and asserts fresh UUIDs. The captures were made during
implementation, before finalizing the equivalent PT200 constructor and explicit-None
compatibility correction; their source
hash is retained honestly. Source UUIDs and old semantic hashes are not replaced or
expected to equal fresh values. Current semantic hashes are recomputed from the
actual source flowsheet. The numerical chain consumes the captured actual material
and resolves its exact captured execution context, then uses current production APIs;
this is not admission of an 8 MPa application graph.

`--write`, `--capture`, `--record-identity` and `--capture-source` create artifacts
once and refuse existing paths. Do not use them to overwrite evidence. To repeat
the 30 actual M20 workflows without modifying frozen M20 evidence, use the M21
`m20_admission.py` adapter:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m21_pt200/m20_admission.py
```

Default mode compares current numerical check values read-only; lineage UUIDs are
validated against each fresh source, not against a previous run UUID. Optional
`--output /tmp/m21-new-m20.json` captures a fresh result at a new path only.

## Demonstration

```sh
engine/.venv/bin/python -B benchmarks/m21_pt200/demo.py
engine/.venv/bin/python -B benchmarks/m21_pt200/demo.py --chain below
engine/.venv/bin/python -B benchmarks/m21_pt200/demo.py --chain above
```

The first command performs real production PT at 466.6666666666667 K, 8 MPa,
z=(0.5,0.5), explicit zero kij: 152 iterations with named PT200. The other commands
compose the real PS→PH numerical APIs with captured separator liquids. Output
explicitly says `production_support: false`; no application graph is accepted.

## Artifact roles

- `baseline.json`: 548 task-start paths, status, branch, HEAD, empty index and master prefix.
- `source_manifest.json`: complete current engine/schema/source identity, including the new module.
  The `*.initial.json` files preserve intermediate source/identity/audit records and the initial extension manifest; they do not replace final manifests.
- `verify.py`: current source manifest plus task preservation. Allows only the four named existing
  production edits, maintained frontend test and appended master; protects all prerequisite bytes.
- `common.py`, `profile.py`, `harness.py`: current API verification and controlled numerical adapters.
- `capture_sources.py`, `sources.json`, `source_replay.json`: actual sources and explicit identity mapping.
- `compare.py`, `implementation.json`, `ledger.json`: 70 PT inputs, six inverse anchors and 12 chains
  under legacy100/PT200, independent comparisons, scan/final diagnostics, counts and admission checks.
- `evidence.py`, `evidence.json`: frozen numerical compatibility, propagation, finite bounds and phase-audit checks.
- `m20_admission.py`, `m20_current.json`: 30 current default-production workflows, 1,680 independent checks.
- `integrity_audit.py`, `integrity_audit.json`: pre-existing versus M21 historical source-pin mismatches.
- `demo.py`: explicit production selection without modifying application admission.
- `logs/`: commands' original failures, corrections, full suite and affected reruns.
- `verification_results.json`, `inventory.json`: exact outcomes and file ownership inventory.
- `manifest.json`: all final extension files, tests, milestone report and new master appendix.

The prerequisite source-pin verifiers still describe their original historical
implementation and are not valid current-source adapters after these authorized
edits. Their manifests and assertions are unchanged. Do not run a historical writer
such as `benchmarks/m20_separator_pump/verify.py`: it overwrites its old artifact.
M21's corresponding adapter preserves that evidence and checks current results.
Historical source reproduction was not attempted during initial implementation.
The final review subsequently recovered all production pins and reproduced historical
semantic construction; numerical comparison and historical byte integrity remain distinct.


## Final implementation review

See [review/README.md](review/README.md) for findings, retained coverage, historical
reproduction commands and the unavailable historical next-env snapshot.
[review/ASSERTION_LEDGER.md](review/ASSERTION_LEDGER.md) accounts for every assertion,
including masked failures. The active M19/M20 tests now distinguish recovered historical
source integrity from current independent numerical regression, current provenance
and review-start preservation. No historical expected hash was replaced.

`review/baseline.json` pins 615 review-start paths. `verify.py` additionally protects
that baseline, allowing the exact maintained tests and review documentation/adapters.
Production and both unrelated configuration files must retain review-start bytes.
The original current manifest/inventory and verification results are preserved in
`review/prior_*`; original numerical evidence, logs and source manifests are unchanged.
`review/verification_results.json` records the new single full Python run separately
from old failures and focused reruns. `review/inventory.json` lists exact review changes.
The parent `inventory.json` and `manifest.json` describe the final current handoff.
