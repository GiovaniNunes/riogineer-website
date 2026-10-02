# Milestone 21 — Explicit opt-in PT200 numerical infrastructure

Status: **accepted by Giovani Nunes on 2026-10-02 (America/Sao_Paulo)**.
Production implementation and review are complete; milestone commit and normal push
are authorized. Documented archival/formatting limitations and finite scope remain.
No deployment or running-service change is included.

## Baseline and preservation

Verified branch `main`, HEAD `b256ee38e1dedc62872e18b5fc8832bf12bc5a2c`, empty index.
Task-start changes were the existing master additions, both Pre-M21 reports/study
directories and unrelated `next-env.d.ts` / `tsconfig.json` changes. The new
`benchmarks/m21_pt200/baseline.json` records 548 existing paths and the complete
starting Git status. The master is appended only; prerequisite studies, phase audit,
raw failed comparisons, manifests and frozen independent expectations are unchanged.

Configuration SHA-256 values, identical at task start and completion:

- `next-env.d.ts`: `0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc`
- `tsconfig.json`: `e2a28ab5d02bb5b555a28523be8786d9dc3a400fe125f14602261e24a6288126`

Only four existing production files are edited: `property_packages.py`,
`pr_ps_flash.py`, `pr_ph_flash.py` and `pump_energy.py`. The new production module
is `numerical_profiles.py`. EOS, PT loop, stability, RR, caloric formulas/data,
components, explicit kij and all equipment call sites/admission rules are unchanged.
No public schema or physical property-package/model version is changed. The normal
implementation fingerprint changes because it includes production source bytes.

## Profile and APIs

`NumericalProfile.PT200` resolves exactly to `pr_high_accuracy_pt200@1` and the
immutable `PT200` / `ProfiledPTSettings` representation:

| Setting | Value |
|---|---:|
| PT equilibrium cap | 200 |
| Stability cap | 100 |
| RR cap | 200 |
| Fugacity tolerance | 1e-12 |
| Material tolerance | 1e-10 |
| Accuracy profile | high_accuracy |
| Explicit numerical identity | pr_high_accuracy_pt200@1 |

The numerical identity is distinct from physical package `peng_robinson@1.0`.
The frozen settings subclass adds identity only to explicitly selected PT200;
ordinary `SolverSettings` and default result shapes gain no new field. Arbitrary
custom settings are not identified as PT200 merely because their cap is 200.
Matching unnamed controls may accompany an explicit identifier; conflicting controls,
unknown identifiers, malformed named settings and named PT400 are rejected before
evaluation. Existing unnamed low-level custom PT controls remain available, including
controlled low-budget failures. This does not qualify a named 400 production policy.

The additive keyword-only argument is `numerical_profile=` on:

- Provider protocols and implementations: `flash_PT`, `phase_caloric_TP`,
  `equilibrium_caloric_PT`, `flash_PS`, `flash_PH`.
- Standalone `pr_ps_flash.flash_ps` and `pr_ph_flash.flash_ph`.
- `pump_energy.inverse`, where it specifies the **expected** profile explicitly.

Omitting selection preserves historical defaults: standard PT remains 100 with
its existing tolerance; nested inverse PT remains high_accuracy100. An internal
omission sentinel preserves the distinction from explicitly invalid `settings=None`: the
caloric API returns historical `invalid_input`, while raw PT retains its historical
`AttributeError`. An explicit named profile combined with None is rejected before
evaluation. No change to unnamed low-level invalid-object behavior is claimed.
No automatic pressure-based selection, retry, fallback or escalation exists.
Existing equipment calls do not select PT200. There is no UI selector or new model.

Example with the actual production API (using an already constructed specification
and explicit BIP):

```python
from riogineer_engine.numerical_profiles import NumericalProfile
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pump_energy import inverse

provider = PengRobinsonProvider()
result = provider.flash_PS(ps_specification, bip,
                           numerical_profile=NumericalProfile.PT200)
validated = inverse(result, ps_specification, 'PS',
                    numerical_profile=NumericalProfile.PT200)
```

The same explicit selection applies to actual PH and any PT reconstruction.
`PT200` may also be passed through the pre-existing low-level settings interface.
Standalone PS/PH still accept their existing inverse controls, while pump inverse
acceptance retains its exact qualified PS/PH controls. Selection errors raise a
controlled `ValueError`-family exception before evaluation; numerical failures retain
the original result/status and no accepted solution payload.

## Propagation, guards and diagnostics

Resolved named settings reach every scan, refinement and final PT evaluation.
Existing `pt_settings` and PT provenance carry the immutable named settings,
including the explicit identity. Iteration counts, failed trials, complete scans,
root/bracket diagnostics, residuals and final validations are retained.
`pump_energy.inverse` compares exact expected controls, then verifies final PT
settings and pressure/composition association. A PT200 result cannot pass an omitted
legacy guard. Explicit guard output includes the profile and complete settings;
legacy guard output retains its shape. No permissive `max_iterations >= 100` test.

PS retains its full 64-point 200–500 K scan, rejection on a failed sample, root
ambiguity rules, 100 root iterations, 1e-10 K width and 1e-8 entropy residual.
PH retains the full 128-point scan, M16 connected-valid-interval policy, ambiguity
rules, 100 root iterations, 1e-12 K width and 1e-6 enthalpy residual. Final phase,
work, entropy and mass/energy checks remain active. No AST transformation,
runtime monkey-patching, duplicated solver or reference phase normalization is
present in production.

## Frozen evidence and finite scope

Reviewed the supplemental phase-identity audit before implementation. Its six
reference phase-name exchanges were determined from independent PIP, volume,
density and reproduced phase roots, not production labels or values. The original
195 failed named comparisons and supplemental audit remain byte-identical. M21
consumes the frozen physically identified reference; it does not regenerate expected
values or transfer normalization into the physical solver.

The exact matrix is inherited from `benchmarks/pt_iteration_budget/PLAN.md`: 70 PT
inputs, six PS/PH anchors and 12 separator-liquid numerical chains, methane/n-hexane
with explicit zero kij. It includes the actual two cold sources, sampled 7/7.5/7.8/8
MPa discharges, nearby temperature samples, independently selected off-grid holdouts,
normal phase states and boundary/restart controls. Its extrema do not define a rectangle.

| Selection | PT accepted | Inverse anchors | Full numerical chains |
|---|---:|---:|---:|
| Historical high_accuracy100 | 41/70 | 6/6 | 6/12 |
| Explicit PT200 | 70/70 | 6/6 | 12/12 |

M21's frozen independent comparison ledger has **4,941 checks, 3,679 scalar
comparisons and zero failures**. Separate compatibility/propagation evidence has
**10,248 checks and zero failures**. Every one of the 140 PT runs matches the
historical numerical payload and iteration trace; only explicitly added numerical
identity is excluded when comparing named PT200 with the earlier unnamed experimental
controls. Default inverse anchors and chain numerical states/metrics/diagnostics also
match their preserved baseline. Source fingerprints and UUIDs are handled separately.

Peak observed work remains **199 iterations** at the 469.29133858267716 K PH scan
point, 8 MPa, for both cold source compositions. The margin under 200 is just one
iteration. This is finite numerical qualification, not universal convergence,
critical-region qualification, interpolation support, hydraulic/NPSH/cavitation
validation or new engineering equipment support. No naturally failing physical
PT200 case was discovered in this finite matrix. Synthetic failures are policy
tests, not independent physical qualification of such a case.

## Complete chains versus equipment admission

Fresh actual separator results were captured, preserving liquid component rates
and authoritative Hdot. Verification resolves each captured result through its
matching execution context using an already admitted source graph; it never submits
or relaxes an 8 MPa application graph. The numerical orchestration then calls real
production PS at inlet entropy/discharge pressure, derives isentropic H and the
actual efficiency-based H target, calls real production PH and guards, reconstructs
fresh endpoints and verifies phase, work and integrated energy closure. Independent
answers are not injected as pump targets or roots. Separate forward-defined inverse
anchors remain clearly separate diagnostics.

| 8 MPa source | Default | PT200 numerical chain | Isentropic T K | Actual T K | Fluid power W | M20 application |
|---|---|---|---:|---:|---:|---|
| PT_BUBBLE_BELOW | PS failure | passes | 231.62864734074992 | 232.0029774476092 | 20567.978871054584 | excluded |
| PT_BUBBLE_ABOVE | PS failure | passes | 231.7288906905257 | 232.1032000731769 | 20564.527568835445 | excluded |

Identity retains its material stream, zero work and no PS/PH evaluations. Candidate
endpoint checks use explicit PT200. The unchanged source/local guards and separately
recorded legacy endpoint probes keep their legacy controls; the verification does
not relabel them as PT200. The artifact label `accepted_prototype` is retained from
the chain harness format and means accepted numerical composition only; every
thermodynamic solve/guard now uses the real production API. `production_support`
remains false for these stand-alone chains.

All 30 original M20 combinations remain admitted; both 8 MPa requests remain rejected
with `unsupported_qualified_tuple`. A separate execution of all 30 current production
workflows passes **1,680 independent checks**, including identity, actual source
propagation, default numerical controls and balances. Equipment models, input-only
scope specification, requirements, network admission and user interfaces are unchanged.

## Implementation-stage historical identity and current integrity

The prerequisite studies intentionally pin old source bytes. Authorized M21 edits
invalidate current-source use of those pins; neither their manifests nor their
assertions were changed. Historical numerical evidence, historical source reproduction,
current numerical verification and task-start byte preservation are separate claims.
No historical source reconstruction/reproduction was attempted during initial implementation.
The final review below records subsequent recovery and maintained active coverage.

`source_manifest.json` captures all current engine files, schemas and the admission
specification. `verify.py` validates that current manifest and preserves every other
baseline file, with explicit allowances for the four production edits, frontend test
maintenance and appended master. `integrity_audit.json` classifies differences:

- M19's archived equipment source capture already mismatched `core.py` and `network.py`
  at task start. M21 additionally changes its four shared-source pins.
- M20's historical preservation assertion now mismatches the four authorized source
  edits and the pre-existing `next-env.d.ts` hash.
- M20's archived results have old implementation-dependent semantic input hashes;
  comparison of those hashes to a newly built flowsheet is not a numerical regression.

The historical next-env expected value remains
`1f2e4a6d7f55de2de72375901050f2af22ed89992a781fce74d6e6a4d3fc94f0`,
while current preserved bytes remain `0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc`.
No configuration or frozen expectation was changed to make an assertion pass.

Source captures were taken during implementation before an equivalent constructor
refactor and the explicit-None compatibility correction. Their real run and source identity is preserved. The source replay adapter
verifies fresh numerical fields, validates the fresh flowsheet's current semantic
hash, and records captured/current engine and input identities separately. It does
not forge fresh UUID equality or replace historical identities. Fresh source numeric
results match exactly. The initial strict input-hash replay failure is retained in
logs and explained by the source revision.

The active frontend freshness test is maintained because its original setup mixed a
new flowsheet with a frozen old result and asserted freshness. It now proves that the
archived result parses but is rejected as stale, then revalidates/rebuilds and uses an
actual current calculation for the positive case. The frozen fixture is untouched.
The test has a 30-second budget for the real numerical calculation, replacing its
previous five-second assumption for a fixture-only test. Existing archival Python
assertions remain visible, not silently excluded or reset to current hashes.

## Verification outcomes and exact commands

See the final verification record below and `benchmarks/m21_pt200/logs/` for original
runs and affected corrections. These are cumulative results, not a claim that the
initial full commands were all-green. No broad test group was excluded.

```sh
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_pt200_profile test_pr_ps_flash test_pr_ph_flash test_pump_energy -v
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
engine/.venv/bin/python -B benchmarks/m21_pt200/compare.py
engine/.venv/bin/python -B benchmarks/m21_pt200/evidence.py
engine/.venv/bin/python -B benchmarks/m21_pt200/capture_sources.py
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m21_pt200/m20_admission.py
engine/.venv/bin/python -B benchmarks/m21_pt200/integrity_audit.py
engine/.venv/bin/python -B benchmarks/m21_pt200/verify.py
```

Repository frontend/schema gates were run in `/tmp/riogineer-m21-gates`, an isolated
copy with the changed engine files, to protect current Next/TS files and the running
development server's output. Commands: `npm run contracts:check`, `npm test`,
`npm run lint`, `npm run typecheck`, `npm run build`. The initial build stalled in the
sandbox at compile; only its own test-build PID was terminated, and the isolated
build passed outside the sandbox. Existing development/engine services were untouched.
The local HTTP fixture's sandbox bind error was retried only for
`PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_engine.HttpTests -v`;
its two tests passed on a temporary random port.

Browser/E2E tests were not run: this is an internal-only numerical API change with
unchanged UI and equipment admission, and the user expressly requires no invented
browser acceptance requirement or running-service changes. CI's broader browser
workflow is not claimed as executed. Frontend unit coverage, schema generation,
types, lint and isolated production build provide the applicable cross-language gates.

## Reproducible demonstration

```sh
engine/.venv/bin/python -B benchmarks/m21_pt200/demo.py
engine/.venv/bin/python -B benchmarks/m21_pt200/demo.py --chain below
engine/.venv/bin/python -B benchmarks/m21_pt200/demo.py --chain above
```

The PT example converges in 152 iterations and prints explicit named settings.
The chain examples report numerical success and `production_support: false`.
They neither construct an accepted 8 MPa application workflow nor modify any service.

## Inventory and review

Implementation-owned existing-file edits: the four production files above,
`tests/separator-pump.test.ts`, and the appended `docs/RIOGINEER_MASTER_CONTEXT.md`.
New implementation files: `engine/riogineer_engine/numerical_profiles.py`,
`engine/tests/test_pt200_profile.py`, `MILESTONE_21.md`, and the separately inventoried
`benchmarks/m21_pt200/` directory. Its README explains every artifact; `inventory.json`
and `manifest.json` give the exact complete file list and final hashes.

Prerequisite files are separate: both `PRE_MILESTONE_21_*_QUALIFICATION.md` reports,
`benchmarks/configurable_separator_pump/`, `benchmarks/pt_iteration_budget/`, all
older frozen references and the master prefix. Their task-start bytes are preserved.
The unrelated configuration modifications remain present and are not M21 changes.

Before closeout, review the API/default/None compatibility, strict named-setting and
final-state checks, finite scope/199-iteration margin, source-identity adapter and
remaining archival assertion outcomes. Review the maintained frontend freshness
regression and source manifest/inventory. Human implementation acceptance is pending;
no browser acceptance is requested. Any equipment integration, broader admission,
operating envelope, shared-default change or named PT400 requires separate authorization.

## Original implementation verification record (preserved history)

The full Python command ran once after initial focused stabilization: **680 tests
in 748.503 seconds; eight failed assertions and one class-setup error**. These
counts include five failing subtests in one preservation method; they are not eight
separate failing test methods. Its log remains unedited.

- Functional failure: explicit `None` on the caloric provider had inadvertently
  become omission. Corrected with a distinct omission sentinel. Final affected
  command below: **74 passed**, including the 13 new M21 tests, all caloric tests
  and PT/flash tests. A new test initially assumed raw PT's historical None behavior
  was also an `invalid_input` result; inspection showed its existing AttributeError.
  The test now preserves that existing distinction. Both intermediate logs remain.
- Sandbox setup error: `test_engine.HttpTests.setUpClass` could not bind its temporary
  fixture. An outside-sandbox class-only retry passed **2/2**.
- Remaining historical assertions, **seven across three methods**: M20
  `test_all30_fresh_evidence` compares archived semantic identity to current source;
  M20 `test_preservation` has four authorized source differences plus the known
  next-env mismatch; M19 `test_equipment_comparison_and_source_capture` first hits
  the pre-existing core.py snapshot mismatch. These assertions remain failing and
  unmodified. The separate current-source/numerical adapters pass; that does not
  relabel the historical command all-green.

```sh
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_pt200_profile test_pr_caloric test_pr_flash -v
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_engine.HttpTests -v
```

Initial focused PS/PH/pump plus new-policy run: **133 passed**. A separate selection
run passed three tests. Initial nine-policy run had a missing explicit guard-output
identity error, corrected before focused/full stabilization. Final matrix,
ledger and evidence reproduction are byte-identical; fresh source replay records
identity changes separately and passes. All 30 current M20 workflows and 1,680
checks pass, including a final-source read-only reproduction after the None fix.

Frontend full unit command: **276/277 passed**, with the historical/current freshness
fixture failure described above. Its correction needed explicit revalidation after
stale rejection and a real-calculation timeout budget; both intermediate failures
are retained. Affected two-file rerun: **6 passed**. Final-source maintained file:
**2 passed**. This is cumulative verification, not a new 277-test all-green run.

```sh
npx vitest run tests/separator-pump.test.ts tests/separator-pump-summary.test.ts
npx vitest run tests/separator-pump.test.ts
npx eslint tests/separator-pump.test.ts
npx prettier --check tests/separator-pump.test.ts
```

Contracts check, repository lint, TypeScript/type generation, corrected-test
lint/format and isolated production build passed. The build passed after its
sandbox-only retry; no second full Python or full frontend suite was run. The
source corrections after the full run were checked by the affected scope and full
finite numerical replay. No browser tests or user acceptance are claimed.

Final Git status:

```text
 M docs/RIOGINEER_MASTER_CONTEXT.md
 M engine/riogineer_engine/pr_ph_flash.py
 M engine/riogineer_engine/pr_ps_flash.py
 M engine/riogineer_engine/property_packages.py
 M engine/riogineer_engine/pump_energy.py
 M next-env.d.ts
 M tests/separator-pump.test.ts
 M tsconfig.json
?? MILESTONE_21.md
?? PRE_MILESTONE_21_CONFIGURABLE_SEPARATOR_PUMP_QUALIFICATION.md
?? PRE_MILESTONE_21_PT_ITERATION_BUDGET_QUALIFICATION.md
?? benchmarks/configurable_separator_pump/
?? benchmarks/m21_pt200/
?? benchmarks/pt_iteration_budget/
?? engine/riogineer_engine/numerical_profiles.py
?? engine/tests/test_pt200_profile.py
```

The two configuration modifications and both prerequisite studies predate M21.
HEAD/index remain unchanged. `verification_results.json` is the compact machine-readable
handoff; `inventory.json` identifies every implementation path separately from the
preserved prerequisites. No review/acceptance, commit or push has been performed.


## Final implementation review and regression maintenance — 2026-10-02

Implementation review is complete; M21 is ready for user acceptance with the
limitations below. Acceptance and authorized closeout remain pending. This review
changes no production or frontend code. Exact named controls, explicit-None behavior,
PT/caloric/PS/PH propagation, final inverse state association, controlled failures,
legacy defaults and unchanged equipment admission were inspected and verified.

The source replay adapter now verifies the full result envelope, including balances
and exact non-implementation engine provenance, current semantic/evaluator/engine
identities, requirements/case association and a fresh UUID. Mutation tests reject
meaningful changes. The M20 adapter also rejects truncated case/check lists.

The three maintained historical-identity methods retain separate coverage for
historical source integrity, fresh independent numerical regression, current identity
and actual review-start preservation. The complete ledger accounts for **169 assertions**,
including **41 obsolete comparisons**, **34 masked by original failures**. The original
seven observed failures across three methods and all original logs remain preserved.
No expected historical hash was replaced, and no test group was skipped or xfailed.

Historical integrity: **103/104 pinned entries verified**, including every production
pin; all 36 M19 production pins match one coherent Git snapshot. All 30 archived M20
semantic identities reproduce from the historical Git snapshot. This is source-byte
and semantic-construction verification, not a historical numerical solver rerun.
The original next-env snapshot remains unavailable; the strict complete-archive
command explicitly exits 1. Current next-env and tsconfig bytes remain unchanged.

New verification, separate from the original implementation records above:

- Focused run: **29 test methods passed**, 146.527 seconds.
- Standard full Python discovery, run **once** after stabilization: **684 test
  methods passed**, 841.731 seconds; zero failing assertions/subtests and zero
  setup errors. Temporary HTTP fixtures passed; existing services were untouched.
- These are overlapping single-run totals, not a cumulative unique-test count.
- Source replay, schema checks, repository lint, TypeScript checking and preservation passed.
- Repository formatting **failed only on the pre-existing `tsconfig.json`**; its bytes
  were preserved as required. No all-checks-green claim.
- Frontend test source is unchanged; no new frontend suite/build/browser run was needed.
  The original full frontend failure and later affected passes remain separate records.

The unchanged source manifest supports reuse of **4,941 independent checks**, including
**3,679 scalar comparisons**, and **10,248 compatibility/propagation checks**. Fresh
M20 calculations also pass **1,680 checks across 30 workflows**. The finite 70 PT / six
anchor / 12-chain scope, peak **199 iterations**, default policy, and application
exclusion of 8 MPa cases remain unchanged. Source hashes are identity evidence, not
an independent numerical oracle.

See [review findings and coverage](benchmarks/m21_pt200/review/README.md),
[complete assertion ledger](benchmarks/m21_pt200/review/ASSERTION_LEDGER.md),
[verification results](benchmarks/m21_pt200/review/verification_results.json), and
[exact review inventory and Git status](benchmarks/m21_pt200/review/inventory.json).
The parent current manifest/inventory are updated; their prior bytes are retained.
HEAD remains `b256ee38e1dedc62872e18b5fc8832bf12bc5a2c`, branch `main`, index empty.
No commit, push, deployment, equipment expansion, service change or user acceptance.

## User acceptance — 2026-10-02 (America/Sao_Paulo)

**Giovani Nunes accepts Milestone 21**, its documented implementation and completed
review, based on the evidence presented. This is acceptance of internal numerical
infrastructure within its documented finite scope. No browser acceptance is required
or claimed; this record does not claim independent code inspection or user-executed
numerical verification by Giovani Nunes.

The accepted capability is explicit opt-in `pr_high_accuracy_pt200@1` through the
production numerical APIs. Historical defaults, failure policies and M20 application
admission remain unchanged. No automatic fallback or escalation, continuous operating
envelope or expanded equipment admission is authorized. The 8 MPa chains succeed
numerically but remain excluded from application workflows. The finite qualification
remains 70 PT inputs, six inverse anchors and 12 numerical chains, with an observed
peak of 199 iterations. Broader equipment integration requires a separately defined
next milestone.

Acceptance relies on the recorded single full run of **684 passed test methods**
and the separate focused run of **29 passed test methods**; these overlapping runs
are not combined. Three historical-identity methods were maintained. The complete
ledger covers **169 assertions**, including **41 obsolete comparisons** and **34 masked
mismatches**. Independent evidence remains 4,941 checks including 3,679 scalar
comparisons, 10,248 compatibility/propagation checks and 1,680 checks across the 30
existing M20 workflows. No lengthy regression suite is repeated for this documentation
closeout because no substantive implementation change is made.

The historical distinctions and limitations remain: 103/104 historical pins are
verified, including every production pin; the old `next-env.d.ts` snapshot is
unavailable. Historical source and semantic reconstruction are distinct from a
historical numerical solver rerun, which is not claimed. The pre-existing
`tsconfig.json` formatting failure remains. Both unrelated configuration files retain
their exact starting bytes and are excluded from the milestone commit. Original
failed-run history, subsequent corrections, frozen prerequisites and final review
records remain intact; earlier pending-acceptance entries are historical records.

The user authorizes the exact milestone/evidence commit and a normal push to verified
`origin/main`, with the message **Complete Milestone 21 opt-in PT200 profile and record
user acceptance**. See `benchmarks/m21_pt200/closeout/inventory.json` for the exact
commit scope. The pre-closeout current manifest and inventory are retained there as
`review_manifest.json` and `review_inventory.json`. Session-preservation commands
record pre-staging HEAD/index conditions; final commit identity and remote agreement
are verified separately after the authorized commit. No deployment, M22 work or
running-service changes are authorized or performed.
