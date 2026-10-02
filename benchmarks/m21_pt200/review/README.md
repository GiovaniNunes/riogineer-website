# M21 final implementation review — 2026-10-02

This review makes no production change. It maintains three active historical-identity
methods, strengthens two verification adapters, and adds replay mutation tests.
User acceptance and authorized closeout remain pending. No commit, push, deployment,
equipment expansion, service change or browser acceptance occurred.

## Review findings

The explicit immutable `pr_high_accuracy_pt200@1` selection and exact settings are
correct. Unknown/conflicting selections reject before evaluation; unnamed controls
retain their historical behavior and do not acquire a PT200 label. The omission
sentinel preserves explicit-None behavior. PT/caloric/PS/PH propagate the selected
controls through scans, refinement and final reconstruction. Inverse guards require
the expected profile and preserve specification, pressure, composition, temperature,
final residual and stable-phase association. Failures do not trigger fallback.
Existing equipment calls, default100 policy and the 30-case admission set are unchanged.
No production AST rewriting or duplicate thermodynamic solver was found.

The frontend freshness test correctly marks archived results stale under current
source identity, rebuilds and calculates a genuine current result, accepts that
result, then rejects it after an input edit. Its source is unchanged in this review.

Concrete verification corrections:

- `capture_sources.validate_replay` now compares every result field except the fresh
  UUID and explicitly checked source-dependent semantic/implementation identities.
  It checks all other engine provenance exactly, current evaluator identity,
  requirements/case association, input identity, balances and fresh UUID. Mutation
  tests reject altered numerical envelopes and provenance. Frozen captures and the
  existing replay record remain byte-identical.
- `m20_admission.verify` verifies equal case/check counts before zip comparison to
  prevent silent truncation, and returns fresh results for active freshness checks.

## Complete assertion accounting

[ASSERTION_LEDGER.md](ASSERTION_LEDGER.md) and [assertion_ledger.json](assertion_ledger.json)
list all 169 assertions from the three original methods, with full expected/observed
values, classification, review-start status, evidence and retained coverage.
There are 41 obsolete historical/current comparisons: 30 M20 semantic hashes,
six M19 source hashes, and five M20 preservation hashes. Of these, 34 mismatches
were masked by the original first failures (29 semantic and five M19 source checks).
All existed at review start. Eight shared source comparisons plus 30 semantics follow
from authorized M21 edits; M19 core/network and M20 next-env predate M21.

Original full-run observations were seven failing assertions in these three methods:
one semantic failure, five preservation subtests, and one M19 source failure.
The original full log additionally contains the then-unfixed explicit-None failure
and one HTTP class setup error (680 methods, eight failure entries, one setup error).
Final review observations use final implementation bytes, which can differ from
intermediate hashes printed in that original log. That log is unchanged.

## Retained coverage

| Original assertion | Current regression | Historical / preservation coverage |
|---|---|---|
| M20 old input hash equals live input hash, all 30 | Fresh execution of all 30 workflows, 1,680 checks against frozen independent references; fresh semantic, requirements and engine identity | All 30 old semantic identities reproduced from the recorded Git snapshot and compared with frozen results |
| M20 production files equal old source hashes | Exact current production source manifest; current numerical regression | Original expected bytes recovered from Git and SHA-verified |
| M20 immutable artifacts and master prefix | Original artifact hashes and original master prefix still asserted | Review-start byte preservation also covers prerequisites and old evidence/logs |
| M20 next-env and tsconfig equal old hashes | Both files must retain exact review-start bytes | Original hashes retained; historical tsconfig bytes verified; missing historical next-env explicitly reported |
| M19 production/reference source pins | Current source manifest plus fresh canonical pump versus independent frozen reference; ordinary full suite retains variable-pump coverage | Every original source pin recovered and verified; immutable reference file still checked at original location |
| M19 passed/64 cases; M20 passed/30 cases/per-case checks | Original assertions retained | Historical artifacts remain byte-identical |

The M19 64-case artifact is historical, not a claim that this review reran that
entire comparison. Likewise a source manifest proves identity, not numerical accuracy.

## Historical reproduction and its limitation

`historical_manifest.json` contains 104 original pinned entries: 103 verified,
one unavailable. All production pins are recovered from Git. All 36 M19 production
pins also match the coherent snapshot `2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0`.
All 30 M20 semantic identities and historical implementation identity reproduce from
`b256ee38e1dedc62872e18b5fc8832bf12bc5a2c` in an isolated temporary checkout.
This checks source bytes and semantic construction; it is not a historical numerical
solver rerun. Recovered files are content-addressed in `historical/`.

Unavailable historical `next-env.d.ts` SHA-256:
`1f2e4a6d7f55de2de72375901050f2af22ed89992a781fce74d6e6a4d3fc94f0`.
Reachable Git path history and the current file did not supply those bytes.
`archive.py --require-complete` therefore **fails with exit 1**, deliberately;
`logs/archive-complete.log` records that remaining archival limitation. The ordinary
current suite does not claim full historical restoration. Current next-env remains
`0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc`.

Read-only reproduction from repository root:

```sh
engine/.venv/bin/python -B benchmarks/m21_pt200/review/archive.py
engine/.venv/bin/python -B benchmarks/m21_pt200/review/reproduce_history.py
engine/.venv/bin/python -B benchmarks/m21_pt200/review/archive.py --require-complete
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_separator_pump_integration test_variable_pump_evidence test_pt200_profile test_m21_review -v
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
```

The third command is expected to fail until genuine historical next-env bytes are
recovered. Do not replace the old expected hash. `archive.py --recover` is a create-once
procedure and refuses to replace the manifest. `assertions.py` regenerates only the
new review ledger, not any old evidence. Prior test/adapter/manifest/inventory copies
are retained verbatim as `prior_*`. Original production evidence remains unchanged.

## Evidence scope

Artifact counts remain 4,941 independent checks including 3,679 scalar comparisons,
10,248 compatibility/propagation checks, and 1,680 checks for 30 M20 workflows.
The unchanged current production source manifest supports reuse of the finite
70 PT / six inverse-anchor / 12-chain matrix under legacy100 and explicit PT200.
Observed peak remains 199 iterations. Default policy is unchanged. Numerically passing
8 MPa chains remain excluded from application admission. No broader envelope is claimed.

Final single-run results and exact review changes are recorded in
`verification_results.json` and `inventory.json`; the full ordinary-discovery log is
`logs/full-python.log`. Focused and full runs overlap and must not be summed into a
unique test count. Older failure records remain available in the parent directory.
