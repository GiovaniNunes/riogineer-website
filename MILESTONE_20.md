# Milestone 20 — Qualified separator-to-pump integration

Status: **accepted and complete within the documented M20 scope**.
Human acceptance: Giovani Nunes, 2026-10-01, America/Sao_Paulo.
See the final acceptance entry below; prior pending statements are historical.

## Baseline and ownership

Branch `main`; initial HEAD and verified live `origin/main`:
`2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0` (M19 accepted). The index was empty.
Both Pre-M20 studies and the existing master-context additions are prerequisite work.
Their bytes are preserved. The unrelated `next-env.d.ts` and `tsconfig.json` edits are
preserved and excluded from this implementation. The implementation baseline is
`benchmarks/m20_separator_pump/baseline.json`.

## Capability and versions

The existing network validation and topological scheduler execute one source → M17
rigorous separator; vapor → sink; liquid → M20 pump → second sink. The actual liquid
rates, composition, T/P and Hdot propagate directly. All properties are calculated at
runtime with the unchanged PR/PT/PH/PS/caloric/stability routines. No benchmark imports,
frozen outputs, Thermo or SciPy are production dependencies.

| Contract or model | Identity |
| --- | --- |
| Profile | `separator_pump_energy` |
| Separator | `equilibrium_separator_energy_pr@1.0` (unchanged) |
| Pump | `separator_liquid_pump_pr@1.0` |
| Requirements / flowsheet / results | 1.12 / 1.13 / 1.14 |
| Branch engine | 1.13.0 |

M17–M19 branches, qualification guards and result shapes remain unchanged. The additive
schemas change implementation/semantic fingerprints, as expected. The new implementation
matrix records old source fingerprints alongside fresh fingerprints and reconstructs
input correspondence from the original source recipe, not obsolete hashes or UUIDs.
The input-only JSON specification is included in the implementation hash.

## Exact supported set

`engine/riogineer_engine/separator_pump_cases.json` contains only qualified source input
recipes, discharge pressure, efficiency and qualification identifiers. Case labels,
equipment IDs and old calculation UUIDs do not authorize support. Source recipe numbers
permit only 64 machine-epsilon serialization noise; actual received values are retained.
Discharge pressure and efficiency match exactly. There is no interpolation or configurable
envelope. Rates in each source recipe are the actual or explicitly scaled source rates.

| Qualification identifier | Separator mode | Separator P (Pa abs) | Pump P (Pa abs) | Efficiency |
| --- | --- | ---: | ---: | ---: |
| `PT_VL_HEATING_DP0.0` | specified_temperature | 300000 | 300000 | 0.8 |
| `PT_VL_HEATING_DP10000.0` | specified_temperature | 300000 | 310000 | 0.8 |
| `PT_VL_HEATING_DP1000000.0` | specified_temperature | 300000 | 1300000 | 0.8 |
| `PT_VL_INLET_EQUAL_DP0.0` | specified_temperature | 300000 | 300000 | 0.8 |
| `PT_VL_INLET_EQUAL_DP10000.0` | specified_temperature | 300000 | 310000 | 0.8 |
| `PT_VL_INLET_EQUAL_DP1000000.0` | specified_temperature | 300000 | 1300000 | 0.8 |
| `PT_VAPOR_INLET_COOLING_DP0.0` | specified_temperature | 1000000 | 1000000 | 0.8 |
| `PT_VAPOR_INLET_COOLING_DP10000.0` | specified_temperature | 1000000 | 1010000 | 0.8 |
| `PT_VAPOR_INLET_COOLING_DP1000000.0` | specified_temperature | 1000000 | 2000000 | 0.8 |
| `PH_FLASH_DP0.0` | adiabatic | 1000000 | 1000000 | 0.8 |
| `PH_FLASH_DP10000.0` | adiabatic | 1000000 | 1010000 | 0.8 |
| `PH_FLASH_DP1000000.0` | adiabatic | 1000000 | 2000000 | 0.8 |
| `PH_HEXANE_RICH_DP0.0` | adiabatic | 100000 | 100000 | 0.8 |
| `PH_HEXANE_RICH_DP10000.0` | adiabatic | 100000 | 110000 | 0.8 |
| `PH_HEXANE_RICH_DP1000000.0` | adiabatic | 100000 | 1100000 | 0.8 |
| `PT_BUBBLE_BELOW_DP0.0` | specified_temperature | 6000000 | 6000000 | 0.8 |
| `PT_BUBBLE_BELOW_DP10000.0` | specified_temperature | 6000000 | 6010000 | 0.8 |
| `PT_BUBBLE_BELOW_DP1000000.0` | specified_temperature | 6000000 | 7000000 | 0.8 |
| `PT_BUBBLE_ABOVE_DP0.0` | specified_temperature | 6000000 | 6000000 | 0.8 |
| `PT_BUBBLE_ABOVE_DP10000.0` | specified_temperature | 6000000 | 6010000 | 0.8 |
| `PT_BUBBLE_ABOVE_DP1000000.0` | specified_temperature | 6000000 | 7000000 | 0.8 |
| `PT_DEW_BELOW_DP0.0` | specified_temperature | 6000000 | 6000000 | 0.8 |
| `PT_DEW_BELOW_DP10000.0` | specified_temperature | 6000000 | 6010000 | 0.8 |
| `PT_DEW_BELOW_DP1000000.0` | specified_temperature | 6000000 | 7000000 | 0.8 |
| `ETA0.6` | adiabatic | 1000000 | 2000000 | 0.6 |
| `ETA1.0` | adiabatic | 1000000 | 2000000 | 1.0 |
| `SMALL1000.0` | adiabatic | 1000000 | 1001000 | 0.8 |
| `SCALED5.0` | adiabatic | 1000000 | 2000000 | 0.8 |
| `SCALED17.3` | adiabatic | 1000000 | 2000000 | 0.8 |
| `SCALED200.0` | adiabatic | 1000000 | 2000000 | 0.8 |

The 1,000 Pa rise exists only as `SMALL1000.0` and must pass the work-resolution screen.
The M18/M19 10,000 Pa general floor is unchanged. Both known 8 MPa PS failures remain
excluded and unresolved: failed scan samples near 461.9047619 K and 466.6666667 K.
No new water/component/kij/feed qualification, EOS, hydraulic sizing, NPSH, cavitation,
electrical power, general mixed network or recycle support is implied.

## State and provenance

The versioned result context distinguishes independent PT, independent caloric and
upstream-derived specifications. M20 feed is independent PT; independent caloric feed
inputs are not admitted. Derived contexts identify phase, saturation evidence, current
run/input/requirements, equipment/port/stream and PR/component/caloric/kij basis. Detailed
PT/TPD/fugacity/inverse evidence lives in equipment diagnostics.

The private per-run execution context registers a completed real separator execution and
resolves the validated liquid connection. Editable JSON cannot supply a completed source
record. Missing, stale or contradictory evidence yields structured `M20_*` errors. A stale
flowsheet must be rebuilt. Downstream failure returns an error without fabricated outlets
or successful global results. UI edits invalidate dependent results and disable downloads.

Pump output material preservation is separate from provenance assignment. Identity mode
copies all material fields exactly, returns zero power and null reconstructed efficiency,
and does not call PS/PH. The output producer is always the pump, with separator lineage.
Absent phases retain declared zero extensive quantities/unavailable intensive properties;
absent liquid cannot pass the pump adapter or yield a completed M20 process.

## Thermodynamic and numerical policy

The adapter checks rates, total and molar flow, mass/molar fractions, T/P, phase H/S, Hdot,
units and thermodynamic basis with the qualified tolerances. Hdot is retained, not removed
to bypass the M19 PT-only interface. Fresh high-accuracy PT, stable/converged TPD, exact
beta zero, liquid identity, valid calorics and PIP > 1 are required at admitted endpoints.

Saturated source liquid requires fresh parent equilibrium at received T/P and parent
composition: positive phase fractions, matched liquid calorics/composition, stable common
tangent, nontrivial composition/Z gaps > 0.01 and equilibrium-root fugacity residual ≤ 2e-10.
Compressed states require the same-T/composition witness at 0.9999 times received pressure.
This sampled evidence is not a bubble-pressure measurement or hydraulic reserve. Genuine
VL/vapor is rejected; insufficient or unconverged evidence remains controlled unresolved.
No clipping, forced roots, coordinate snapping, artificial cooling or scan-hole bridging.

The energy path is inlet PT H/S → full PS(Pout, Sin) → efficiency target H → full PH.
Existing 64-point PS and 128-point PH scans over 200–500 K, unique bracket and fresh-final
checks are retained. The inverse association verifies the exact received specification;
evaluated mole fractions allow the qualified 1e-12 tolerance for PR normalization roundoff.
No shared solver changed. Positive work, target recovery, entropy, reconstructed efficiency,
component conservation and the propagated work allowance (including its 500 K term) remain
mandatory. Equipment and overall energy balances use actual upstream Hdot, separator duty,
pump fluid power and both products. Endpoint evidence does not prove continuous-path safety.

## Startup and demonstrations

From repository root, use separate terminals and unused ports:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8120
RIOGINEER_ENGINE_URL=http://127.0.0.1:8120 npm run dev -- --port 3120
```

Open `http://127.0.0.1:3120/digital-engineer`; expand Engineering data / Advanced and
load a Milestone 20 example. No provenance IDs need manual editing. Existing services
must remain running undisturbed. Next commands can regenerate local Next/TS configuration;
verification for this milestone uses an isolated copied workspace to preserve original bytes.

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone20 --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone20 --case PH_FLASH_DP0.0 --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone20 --case PT_VL_HEATING_DP1000000.0 --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone20 --case SCALED17.3 --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone20 --unsupported --calculate
```

The final command intentionally rejects the unsupported tuple. Omit `--calculate` to
print requirements. The UI provides all five corresponding example loaders.

## Original human acceptance checklist — pending at initial implementation

- Load canonical reference; validate, generate PFD and calculate. Confirm separator,
  vapor sink, liquid link, pump and pumped-product sink; stream numbers 1, 2, 3, 4.
- Confirm liquid inlet 291.742138656979 K / 1 MPa; discharge 2 MPa; efficiency 0.8;
  pump fluid power about 8,068.18515750 W; outlet 292.169147283087 K; separator duty 0 W.
- Confirm liquid Hdot is preserved at about −1,608,463.02313545 W; source and pump-output
  identities are correct; equipment/overall mass and energy checks pass.
- Download current results and compare with the table and panel. Unavailable properties
  show an em dash; zero duty and zero identity power display zero.
- Load identity, alternate and scaled examples. Identity has unavailable reconstructed
  efficiency and zero work. Inspect lineage in downloaded JSON.
- Edit upstream feed or topology; verify stale status and disabled result export. Load
  unsupported example; confirm explicit rejection, no successful process or pump outlet.

Browser automation is implementation verification, not human acceptance.

## Verification

Fresh implementation evidence: **30/30 tuples; 1,680 checks; zero failed comparisons**.
The input-only scope is reconstructed independently from the captured source recipe and
accepted ledger. Original and fresh semantic fingerprints are recorded without modifying
frozen evidence. The independent Thermo/SciPy matrix was not rerun.

- Focused Python: 11 tests passed, including 27 source contradictions, exact identity/no
  inverse, received-coordinate preservation, missing/stale execution evidence, unsupported
  inputs/topology/injected context, absent/vapor/VL rejection, atomic failure, work screen
  and protected-file hashes.
- Focused M17/M18/M19 compatibility: 46 tests passed.
- TypeScript: 273 tests across 26 files passed, including all 30 M20 result round trips,
  input/build contracts and stale workflow behavior.
- Browser: 40 tests passed in one final full-suite run on isolated ports 3120/8120.
  Focused M20 retries preceded that run: fixed missing PFD version routing; corrected a
  test assumption because switching case IDs removes old results, while same-case edits
  retain stale results with disabled download. The final run includes all four successful
  demonstrations, unsupported input, real engine calls, PFD numbering, exact JSON export,
  and stale upstream edits. A PFD screenshot was visually inspected; the long feed label
  now uses existing label fitting within M20 only.
- Schema parity, TypeScript types, lint and `git diff --check`: passed.
- Production build: passed in isolated copy. The sandboxed compiler stalled at compile
  with no CPU activity; only that test build was stopped and rerun outside the sandbox.
- Smoke: passed 17 pages, 17 PNG cards, internal links, 404s, indexing and disabled contact
  delivery. First attempt returned 403 instead of expected 503 because SITE_URL still
  identified the default port; restarting only the isolated smoke server with its actual
  SITE_URL corrected the environment. No application change was needed.
- Formatting: repository check reports only the preexisting `tsconfig.json` formatting.
  That file is intentionally unchanged. All implementation TypeScript/TSX passes formatting.
- Python repository regression: **668 tests passed in 723.171 s**, one final filtered full-suite run.

The repository Python runner discovers 669 tests and excludes exactly one unchanged
historical M19 assertion that pins all pre-M20 production source bytes:
`test_variable_pump_evidence.EvidenceTests.test_equipment_comparison_and_source_capture`.
It is an obsolete whole-source snapshot for this authorized implementation, not a newly
failed thermodynamic assertion. The original test and frozen baseline are untouched.
`test_separator_pump_integration.test_preservation` checks the implementation-era protection
boundary, including unchanged legacy model/solver files and prerequisite evidence. The
other historical evidence tests still run. This is explicitly a current regression suite
with one historical snapshot excluded, not an unfiltered clean 669-test run.

Actual gate commands (root unless an isolated-copy directory is specified):

```sh
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m20_separator_pump/verify.py
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_separator_pump_integration -v
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_separator_energy engine.tests.test_pump_energy engine.tests.test_variable_pump_energy -v
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m20_separator_pump/regression.py
npx vitest run tests/separator-pump.test.ts
npm test
npm run contracts:check
npm run lint
npm run format:check
git diff --check
```

Next/browser/build commands ran in `.local/m20-validation`, a copy excluding `.git`,
`.local`, `.next`, `node_modules`, `engine/.venv` and caches, with dependencies symlinked
back to the originals. Only the copied Playwright config changes 3100/8101 to 3120/8120.
The original Next/TS files never receive Next regeneration.

```sh
npm run typecheck
npx playwright test tests/e2e/separator-pump.spec.ts
npx playwright test
RIOGINEER_E2E_DIST_DIR=.next/m20-build NEXT_TELEMETRY_DISABLED=1 npm run build
SITE_URL=http://127.0.0.1:3121 RIOGINEER_LLM_PROVIDER='' RIOGINEER_E2E_DIST_DIR=.next/m20-build NEXT_TELEMETRY_DISABLED=1 npm run start -- --port 3121
SMOKE_URL=http://127.0.0.1:3121 npm run smoke
```

Local HTTP/browser checks required a permitted sandbox retry for socket binding. All test
servers used isolated ports and output; existing user services were not stopped. Exact
verification counts and preservation/Git checks are in
`benchmarks/m20_separator_pump/verification.json`.


## Exact implementation inventory

- `MILESTONE_20.md`
- `benchmarks/m20_separator_pump/README.md`
- `benchmarks/m20_separator_pump/baseline.json`
- `benchmarks/m20_separator_pump/implementation.json`
- `benchmarks/m20_separator_pump/regression.py`
- `benchmarks/m20_separator_pump/verification.json`
- `benchmarks/m20_separator_pump/verify.py`
- `contracts/examples/milestone-20-alternate-requirements.json`
- `contracts/examples/milestone-20-identity-requirements.json`
- `contracts/examples/milestone-20-reference-requirements.json`
- `contracts/examples/milestone-20-scaled-requirements.json`
- `contracts/examples/milestone-20-unsupported-requirements.json`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `docs/RIOGINEER_MASTER_CONTEXT.md`
- `engine/riogineer_engine/core.py`
- `engine/riogineer_engine/milestone20.py`
- `engine/riogineer_engine/network.py`
- `engine/riogineer_engine/separator_liquid_pump.py`
- `engine/riogineer_engine/separator_liquid_state.py`
- `engine/riogineer_engine/separator_pump_cases.json`
- `engine/riogineer_engine/separator_pump_process.py`
- `engine/riogineer_engine/separator_pump_scope.py`
- `engine/tests/test_separator_pump_integration.py`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/separator-pump-results.tsx`
- `src/app/digital-engineer/workspace.tsx`
- `src/lib/digital-engineer/contracts.ts`
- `tests/e2e/separator-pump.spec.ts`
- `tests/separator-pump.test.ts`
- `tests/separator-pump-summary.test.ts`

## Preserved prerequisite inventory

These existing uncommitted files remain byte-for-byte intact (separate from M20 changes):

- `PRE_MILESTONE_20_LOW_PRESSURE_SEPARATOR_PUMP_QUALIFICATION.md`
- `PRE_MILESTONE_20_SEPARATOR_LIQUID_CONTRACT_QUALIFICATION.md`
- `benchmarks/low_pressure_separator_pump/PLAN.md`
- `benchmarks/low_pressure_separator_pump/README.md`
- `benchmarks/low_pressure_separator_pump/candidate_ledger.json`
- `benchmarks/low_pressure_separator_pump/common.py`
- `benchmarks/low_pressure_separator_pump/compare.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/PLAN.md`
- `benchmarks/low_pressure_separator_pump/phase_contract/README.md`
- `benchmarks/low_pressure_separator_pump/phase_contract/adapter.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/baseline.json`
- `benchmarks/low_pressure_separator_pump/phase_contract/candidate_ledger.json`
- `benchmarks/low_pressure_separator_pump/phase_contract/capture_sources.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/common.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/compare.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/negatives.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/preservation.json`
- `benchmarks/low_pressure_separator_pump/phase_contract/production.json`
- `benchmarks/low_pressure_separator_pump/phase_contract/pump.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/reference.json`
- `benchmarks/low_pressure_separator_pump/phase_contract/reference.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/sources.json`
- `benchmarks/low_pressure_separator_pump/phase_contract/test_contract.py`
- `benchmarks/low_pressure_separator_pump/phase_contract/verify.py`
- `benchmarks/low_pressure_separator_pump/preservation.json`
- `benchmarks/low_pressure_separator_pump/production.json`
- `benchmarks/low_pressure_separator_pump/reference.json`
- `benchmarks/low_pressure_separator_pump/reference.py`
- `benchmarks/low_pressure_separator_pump/test_study.py`
- `benchmarks/low_pressure_separator_pump/verify.py`

The preexisting master-context prefix and unrelated `next-env.d.ts` / `tsconfig.json` bytes are also protected.

## Initial implementation Git handoff (before label correction)

Branch `main`; HEAD remains `2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0`.
Index empty; 12 modified tracked files and 52 untracked files, all unstaged.
This includes 32 implementation files, 30 preserved prerequisite files and the two
unrelated configuration files. The master-context file contains preserved prior additions
plus the new M20 append. Full path-by-path porcelain status is recorded in
`benchmarks/m20_separator_pump/verification.json`. No commit, push or deployment; human
acceptance remains pending.

## User-reported browser verification and label correction — 2026-10-01

**Reporter:** Giovani Nunes. **Date/time zone:** 2026-10-01, America/Sao_Paulo.
These are the user's reported browser observations, distinct from the automated evidence
above. The assistant did not operate the user's browser for these checks. No repository
screenshot paths are asserted. Final M20 closeout remains pending visual review of the
corrected energy summary; these observations do not accept the correction in advance.

- **Canonical PH:** Four-stream separator-to-pump topology inspected; pump pressure
  1 → 2 MPa; outlet approximately 292.169147283 K; fluid power approximately
  8068.185157497 W. Mass and energy checks passed. Exported JSON was reviewed in the
  accompanying ChatGPT discussion and matched displayed results; it preserved component
  flows, upstream enthalpy and consistent run/source lineage.
- **Identity:** Pump inlet/outlet at 1 MPa and approximately 291.742138657 K; zero fluid
  power; flow, composition and enthalpy preserved; reconstructed efficiency unavailable
  for equal-pressure identity; balances passed.
- **Alternative PT (`PT_VL_HEATING_DP1000000.0`):** Pump pressure 0.3 → 1.3 MPa;
  liquid flow approximately 2813.610577 kg/h; pump temperature 350 → 350.57142487 K;
  fluid power approximately 1585.58354265 W; separator heat duty approximately
  1832535.61976255 W; balances passed. The detailed panel distinguished these values,
  but the general summary incorrectly called the separator's calculated heat duty
  “Imposed pump heat duty.” This was the remaining reported UI defect.
- **Scaled (`SCALED17.3`):** Pump liquid flow 17.3 mol/s = 62.28 kmol/h; fluid power
  approximately 2681.34745204 W. Pressure, temperature and composition were consistent
  with the canonical case; extensive quantities scaled with flow. Balances passed and
  results were current. The 17.3 mol/s value is pump liquid flow, not total process-feed flow.
- **Unsupported:** Explicit `unsupported_qualified_tuple` rejection observed, identifying
  the restriction to 30 qualified combinations and exclusion of known 8 MPa PS failures.
  No PFD was generated and the calculation button was disabled.
- **Stale results:** Editing canonical feed temperature displayed “Engineering results —
  STALE,” a warning that retained results belonged to a previous calculation, and disabled
  Download results. Historical values remained visible with the stale warning; they were
  not cleared.

### Presentation correction

The generic summary grouped results version 1.14 with the M18/M19 pump-only branches,
labelling `balances.energy.duty_W` as imposed pump duty. In M20 that field is process-total
heat duty, including the separator. M20 now has its own presentation branch:

- “Total process heat duty” reads `balances.energy.duty_W`.
- “Total power transferred to the fluid” reads `balances.energy.fluid_power_W`.
- Both lines explicitly state positive into the process. Fluid power is not electrical power.
- The detailed separator heat-duty label reads `separator.thermodynamics.mode`: PT is
  calculated; adiabatic is imposed zero. Its value remains `separator.duty_W`.
- Zero and unavailable-efficiency rendering remain distinct. No separate pump heat-duty
  value is added. Historical equipment summary branches retain their existing behavior.

Only these five files changed in this follow-up:
`src/app/digital-engineer/workspace.tsx`,
`src/app/digital-engineer/separator-pump-results.tsx`,
`tests/separator-pump-summary.test.ts`, `MILESTONE_20.md`, and
`docs/RIOGINEER_MASTER_CONTEXT.md`.

### Focused automated verification of the correction

Commands actually executed:

```sh
npx vitest run tests/separator-pump-summary.test.ts tests/separator-pump.test.ts
npx tsc --noEmit --project .local/m20-label-correction/tsconfig.json
npx eslint src/app/digital-engineer/workspace.tsx src/app/digital-engineer/separator-pump-results.tsx tests/separator-pump-summary.test.ts
npx prettier --check src/app/digital-engineer/workspace.tsx src/app/digital-engineer/separator-pump-results.tsx tests/separator-pump-summary.test.ts
git diff --check
```

Six frontend tests across two files passed. Four render the actual workspace general
summary from existing numerical evidence: alternative PT, canonical adiabatic, identity,
and a synthetic presentation-only zero PT duty to guard against magnitude-based labels.
The other two existing tests cover result round trips and workflow freshness. Types,
changed-file lint and formatting passed. Type checking used a temporary config extending
the untouched repository config with explicit source/test/generated-type includes and
incremental output disabled; no Next regeneration or service commands were run.

No lengthy thermodynamic qualification or full regression suite was rerun for this
presentation-only correction. The previous testing history, historical M19 exclusion,
numerical fixtures, contracts, solvers, qualification scope and frozen evidence remain
unchanged. A before/after SHA-256 manifest in `.local/m20-label-correction/` verifies that
only the five listed files changed or were added. The current unrelated configuration
hashes were captured before this correction and remain:

- `next-env.d.ts`: `0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc`
- `tsconfig.json`: `e2a28ab5d02bb5b555a28523be8786d9dc3a400fe125f14602261e24a6288126`

### Visual-review request and Git status at the label-correction handoff

Refresh the existing development browser session and reload/recalculate the alternative
PT and canonical PH examples. No engine restart is required; the existing Next development
server can pick up this presentation change. No duplicate server was started or existing
service stopped.

- Alternative PT: general heat duty ≈ 1,832,535.619763 W; separate fluid power ≈
  1,585.583543 W; detailed separator heat duty labelled calculated; positive signs explicit.
- Canonical PH: general heat duty 0 W; separate fluid power ≈ 8,068.185157 W; detailed
  separator heat duty labelled imposed zero. Identity still shows 0 W fluid power and
  unavailable reconstructed efficiency.

Branch `main`; HEAD `2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0`; index empty.
Current status: 12 modified tracked files and 53 untracked files, including all prior work;
all changes unstaged. The implementation inventory now contains 33 files. The earlier
verification JSON and initial Git handoff above remain historical records, unchanged.
No commit, push, deployment or M21 work. **Final M20 closeout remains pending the user's
visual review of this correction.**

## Final human acceptance — 2026-10-01

**Current status: M20 accepted and complete within its documented scope.**
Reviewer: **Giovani Nunes**. Acceptance date: **2026-10-01**.
Timezone: **America/Sao_Paulo**.

Evidence type: user-operated browser checks, with screenshots and an exported JSON
reviewed in the accompanying ChatGPT discussion. The assistant did not perform
these manual checks. No repository paths are asserted for screenshots or uploaded
files. Earlier pending-acceptance statements describe the historical stages before
this final acceptance and are superseded by this entry.

The previously recorded canonical, identity, alternative PT, scaled-flow,
unsupported-combination and stale-result observations remain intact above. They
include agreement of the canonical export with displayed results, preserved
component flows/upstream enthalpy/run-source lineage, and retained historical
values with a stale warning and disabled download after an upstream edit.

Giovani confirmed the corrected energy-summary presentation:

| Case                                        | Total process heat duty (W) | Power transferred to the fluid (W) | Detailed separator label           | Mass / energy checks |
| ------------------------------------------- | --------------------------: | ---------------------------------: | ---------------------------------- | -------------------- |
| Alternative PT: `PT_VL_HEATING_DP1000000.0` |              1832535.619763 |                        1585.583543 | Separator heat duty — calculated   | Passed / passed      |
| Canonical PH: `PH_FLASH_DP1000000.0`        |                           0 |                        8068.185157 | Separator heat duty — imposed zero | Passed / passed      |

The identified heat-duty attribution defect has been corrected and visually
reviewed by the user. Heat and fluid power are separate, with the positive-into-process
conventions retained. Fluid power is not electrical power.

Acceptance is limited to **exactly 30 qualified separator-to-pump combinations**,
methane/n-hexane with explicit zero kij, and the existing local phase and numerical
guards. There is no continuous operating envelope or interpolation. Known 8 MPa PS
failures remain unresolved and excluded. NPSH, cavitation safety, hydraulic sizing
and electrical-power qualification remain outside the completed scope.

### Closeout inventory and verification

The two inventories above reconcile to **63 unique committed paths**: 33 M20
implementation paths (including `tests/separator-pump-summary.test.ts`) and 30
prerequisite paths. `docs/RIOGINEER_MASTER_CONTEXT.md` is counted once, although it
contains both prerequisite history and M20 records. No temporary logs, local
virtual environments or copied validation workspaces are included.

`next-env.d.ts` and `tsconfig.json` remain excluded and byte-for-byte preserved
against the current closeout baseline, with the hashes recorded in the preceding
correction section. The working tree is intentionally not described as clean.

Closeout checks comprise documentation/inventory reconciliation, read-only
source/evidence SHA-256 comparisons, the existing 30-case evidence/fingerprint
check without numerical recalculation, schema parity, formatting of the changed
document sections, working-tree and staged whitespace checks, and complete staged
path/diff review. Frozen evidence and historical hashes are not regenerated.

The original verification history remains unchanged: 30 cases / 1,680 comparisons,
668 Python tests with the explicitly documented historical hash assertion excluded,
273 TypeScript tests and 40 browser tests, followed by the six focused frontend
tests and associated checks for the label correction. These are historical results,
not newly rerun full suites. No lengthy qualification or full regression rerun was
required for this documentation closeout.

The user explicitly authorized the reviewed commit and a normal push to the
existing `origin/main` tracking branch, with commit message:

```text
Complete Milestone 20 separator-to-pump integration and record human acceptance
```

No deployment, M21 work, scope expansion or service shutdown is part of this
closeout. After committing and pushing, verify local `main`, `origin/main` and
live remote `main` against the resulting commit; the two unrelated modifications
must remain and the index must be empty.

### Handoff for a fresh conversation

M20 is accepted for exactly 30 qualified combinations, including the corrected
PT/PH energy-summary labels and user-reviewed export/provenance/stale behavior.
Broader separator-to-pump operation and the known 8 MPa PS failures remain outside
the completed scope. Start from the accepted M20 commit and this document; preserve
any unrelated configuration edits. Further milestone or qualification work needs
separate authorization.
