# Milestone 22 — Explicit PT200 separator-to-pump integration

Status: accepted by Giovani Nunes on 2026-10-02, America/Sao_Paulo, within the
finite scope recorded in the final acceptance and closeout entry below. Earlier
pending statements are historical and superseded. M21 remains accepted.

## Verified baseline

Branch `main`, full HEAD and read-only live remote `refs/heads/main`:
`253b91472a5007e7bd4749a6751c4efbc5066e14`. The index was empty. Only
`next-env.d.ts` and `tsconfig.json` were modified at task start. The initial
sandboxed remote lookup failed DNS; a permitted `git ls-remote` retry verified
that hash. No fetch, reset, stage or service shutdown occurred.

Task-start bytes were copied to `/tmp/riogineer-m22-baseline/` and recorded in
`benchmarks/m22_separator_pump/baseline.json`:

- `next-env.d.ts`: `0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc`
- `tsconfig.json`: `e2a28ab5d02bb5b555a28523be8786d9dc3a400fe125f14602261e24a6288126`

Both files and all frozen historical evidence are protected. The master context is
append-only. Next commands run in `.local/m22-validation`, with separate output
and symlinked dependencies, to prevent configuration regeneration in this checkout.

## Exact added capability

Only these two source recipes are newly admitted, each at **8000000 Pa absolute**
and **isentropic efficiency 0.8**, with explicit `pr_high_accuracy_pt200@1`:

| Qualification                |           Feed T K |      Separator T K | Source semantics                                                  |
| ---------------------------- | -----------------: | -----------------: | ----------------------------------------------------------------- |
| `PT_BUBBLE_BELOW_8MPA_PT200` | 230.60146798619095 | 231.06755435138734 | Compressed liquid, corroborated by lower-pressure witness         |
| `PT_BUBBLE_ABOVE_8MPA_PT200` |  230.7220225690974 | 231.16755435138973 | Phase-specific saturated liquid from verified two-phase separator |

Both feeds have Pin 7000000 Pa, separator pressure 6000000 Pa, component mass
rates methane **2887.704 kg/h**, n-hexane **15511.5648 kg/h**, total feed 100 mol/s,
feed mole fractions (0.5, 0.5), explicit constant zero 2x2 kij. The pump receives
actual calculated liquid rates/composition, not the total feed flow. The above
reference has approximately 99.94203100395112 mol/s liquid; the below reference has
100 mol/s. Full exact inputs are in `separator_pump_pt200_cases.json` and the two
requirements fixtures. They were recovered from committed source-input artifacts
and checked against existing exact M20 source recipes, never reconstructed from
rounded report tables.

The original 30 combinations remain on their historical branch and defaults.
Their list remains in the unchanged `separator_pump_cases.json`. Neither the two
new cases under historical selection nor historical cases with an unqualified
PT200 combination are admitted. No arbitrary flow scaling, neighboring pressure,
efficiency, composition or temperature combination is inferred from this scope.
Discharge/efficiency match exactly; source recipes retain M20's 64-machine-epsilon
serialization allowance, with actual received values preserved, never snapped.
Case names, equipment IDs and caller labels do not authorize admission.

## Contracts and profile propagation

| Contract/model         | Historical M20                        | Explicit M22                   |
| ---------------------- | ------------------------------------- | ------------------------------ |
| Requirements           | 1.12                                  | 1.13                           |
| Flowsheet              | 1.13                                  | 1.14                           |
| Results/process result | 1.14                                  | 1.15                           |
| Branch engine version  | 1.13.0                                | 1.14.0                         |
| Pump                   | `separator_liquid_pump_pr@1.0`        | `separator_liquid_pump_pr@2.0` |
| Separator              | `equilibrium_separator_energy_pr@1.0` | unchanged                      |
| Network profile        | `separator_pump_energy`               | unchanged                      |

The new pump parameters require `numerical_profile: "pr_high_accuracy_pt200@1"`.
It persists as `operating_parameters.numerical_profile` in the flowsheet and as
`thermodynamics.numerical_profile` in the pump result. JSON schemas are generated
from the matching TypeScript branches. Old branches remain closed and unchanged.
Unknown, omitted, null, PT400, extra settings and inconsistent model/schema/profile
combinations reject. There is no general numerical-settings editor.

Selected parameters participate in requirements, semantic calculation and source
specification hashes. The new input-only admission file participates in the
implementation hash. Changing input or profile invalidates results and exports.
Existing structured `M20_*` execution errors remain used by the shared integration
adapter; they never return a fabricated successful process or pump outlet.

The separator and source/local guards retain high_accuracy100. The pump explicitly
uses M21's canonical PT200 settings for inlet corroboration, PS/PH nested calls,
fresh endpoints and candidate lower-pressure witnesses. Original historical local
witnesses and legacy endpoint compatibility probes remain active. Their actual
settings are recorded separately under `diagnostics.numerics`; source calculations
are never labeled PT200. Each PS/PH diagnostic retains its exact selected settings
and expected numerical identity. No shared solver, equation, tolerance, component
or caloric data is modified.

## Calculation and evidence

The private current execution registry resolves the actual separator liquid port
from the validated graph. It verifies current run/input/requirements, material
rates, total/molar flow, composition, thermodynamic basis and authoritative source
Hdot. Fresh source calorics and phase checks corroborate that stream. Saturated
source evidence requires the verified parent coexistence/common tangent and phase
gaps; a separator phase outlet is not relabeled an independently stable bulk feed.

The pump derives entropy and enthalpy from the received stream, performs full PS,
derives the efficiency enthalpy target, then performs full PH. No reference endpoint,
root, composition or enthalpy enters production. PS has the complete 64-point scan,
PH 128 points, both over 200–500 K, with unchanged ambiguity/hole/fresh-final rules.
Exact M21 inverse guards require the selected settings. Liquid admissibility,
positive/resolved work, reconstructed efficiency, entropy, component mass and both
equipment/process energy checks remain mandatory. Hdot is preserved throughout.

`benchmarks/m22_separator_pump/PLAN.md` was written before broad integration.
The preliminary fresh source-application-plus-pump path passed **207 checks**.
The final validation/build/network/serialization path passed **221 checks** across
both cases, using frozen independent source and pump references. These counts are
separate and overlap; they are not 428 distinct qualification cases.

| Reference      |     Isentropic T K |        Actual T K |      Fluid power W |
| -------------- | -----------------: | ----------------: | -----------------: |
| Below boundary | 231.62864734074992 | 232.0029774476092 | 20567.978871054584 |
| Above boundary |  231.7288906905257 | 232.1032000731769 | 20564.527568835445 |

These displayed values orient review. Authoritative expected values and allowances
come from `benchmarks/pt_iteration_budget/reference.json`, its source records, and
the inherited independently computed M17 allowances. T tolerance is 1e-7 K;
H 1e-6+1e-11|H| J/mol; S 1e-8+1e-11|S| J/(mol K); composition/beta 2e-9;
Z 2e-10+1e-9|Z|. Fluid power uses propagated inlet/outlet enthalpy allowances.
Production work screening retains E/Δh <= 1e-4 and the 500 K entropy term.
The independent library is not a production dependency and was not rerun.

See `benchmarks/m22_separator_pump/README.md`, `integration.json`, `historical.json`,
`source_manifest.json`, and verification logs for source manifests, actual outputs
and comparison records. Historical source identity and current regression are
separate: the accepted M21 source manifest is checked against the committed task
baseline, while a new manifest checks current M22 sources. Three existing test
files now call the current preservation/source adapter; their M19/M20 archival and
numerical assertions remain. No old manifest or frozen evidence is rewritten.

## Verification record

Final gate outcomes and exact commands are recorded in the integration report and
`benchmarks/m22_separator_pump/verification.json`. Initial focused Python run:
nine tests, one failure because an inherited mutation set methane fraction to 0.5,
already the below-source value. The new test now makes a real 0.4 mutation; the
historical helper is unchanged. Final focused run: nine passed, including 54 source
contradictions, boundary/profile rejection, private registry/stale checks and
controlled inverse failure without fallback. Initial frontend command discovered
no tests because the filename used `.tsx`; renamed to the configured `.test.ts`
convention. Seven focused frontend tests subsequently passed. Both focused browser
references passed, including all four stream columns, export equality, profile and
physical-input stale invalidation and rejection. Original logs are preserved.

## Commands and manual acceptance

From repository root:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone22 --case PT_BUBBLE_BELOW --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone22 --case PT_BUBBLE_ABOVE --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone22 --unsupported --calculate
```

The third command intentionally exits 1 with unsupported-tuple rejection (efficiency
0.81). Omit `--calculate` to print input requirements. Historical M20 CLI is unchanged.

Test services use the isolated copy and are stopped by Playwright after its run.
Before starting manual services, check `lsof -nP -iTCP -sTCP:LISTEN`; reuse any
already-running matching service rather than starting duplicates. From the isolated
copy, if ports 8122/3122 are free, use separate terminals:

```sh
cd .local/m22-validation
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8122
# Separate terminal, same isolated-copy directory:
RIOGINEER_ENGINE_URL=http://127.0.0.1:8122 npm run dev -- --port 3122
```

Open `http://127.0.0.1:3122/digital-engineer`, expand **Engineering data / Advanced**.

1. Load **Milestone 22 below-boundary PT200 reference**; validate, generate PFD,
   calculate. Check compressed-source label, explicit pump PT200 and historical
   separator settings; four numbered streams and separate heat duty/fluid power.
2. Load **Milestone 22 above-boundary PT200 reference** and repeat. Check that the
   liquid comes from a two-phase separator and actual liquid flow is retained.
3. Compare both outlet temperatures and fluid powers with the table above. Review
   isentropic temperatures in results JSON diagnostics and passing balances.
4. In Advanced JSON change pump efficiency from 0.8 to **0.81**, validate, and
   confirm explicit unsupported-tuple rejection, no current successful panel and
   disabled PFD/calculation/export. Do not change input back without revalidation.
5. Recalculate a supported case, change an input or replace the pump profile with
   `unknown`; confirm stale warning and disabled results download immediately.
   Validation must reject the unknown profile. Old values may remain clearly stale.
6. Restore a supported case and calculate; download results and compare temperatures,
   pressure, component/total/molar flow and molar fractions with all stream-table
   columns. Confirm exported profile, source lineage, Hdot and displayed energy values.

Automated browser evidence is not human acceptance. No manual acceptance is claimed.

## Continued limitations

This is a finite equipment integration, not general 8 MPa pump support or a continuous
operating envelope. No arbitrary combinations, interpolation, flow/efficiency scaling,
new components/kij, hydraulics, NPSH, cavitation qualification, sizing or electrical
power. M21 observed a **199-iteration peak under the 200 cap**, one iteration of
observed headroom. No universal convergence claim follows. Controlled failure remains
rejection; there is no automatic retry, fallback, cap escalation or named PT400.
Endpoint/local checks do not prove safety or admissibility along a continuous path.
The known missing archival next-env bytes and pre-existing tsconfig formatting remain
historical limitations; task-start configuration bytes remain protected.

Exact final changed-file inventory follows below; full Git status is recorded in
`benchmarks/m22_separator_pump/final_status.txt`. All task changes remain unstaged.

## Final automated verification — 2026-10-02

| Check                                                     | Final single-run result                                                                 |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Ordinary full Python discovery, no exclusions             | **693 passed in 871.395 s**                                                             |
| Focused M22 Python                                        | 9 passed in 15.958 s                                                                    |
| Focused maintained historical/M21 compatibility tests     | 29 passed in 168.339 s                                                                  |
| Full frontend suite                                       | **280 passed across 28 files**                                                          |
| Focused frontend                                          | 7 passed                                                                                |
| Full browser suite                                        | **42 passed**, one full run                                                             |
| Focused new browser workflows                             | 2 passed                                                                                |
| Independent complete M22 integration                      | 2 workflows, 221 checks, zero failures                                                  |
| Preliminary source-plus-pump integration                  | 2 workflows, 207 checks, zero failures                                                  |
| Historical M20 regression                                 | 30 workflows, 1,680 independent checks; all complete numerical payloads unchanged       |
| Schema generation parity / old-branch structural equality | passed                                                                                  |
| TypeScript / lint / isolated production build             | passed                                                                                  |
| Production smoke                                          | 17 pages, 17 PNG cards, links, 404s, preview indexing, disabled contact delivery passed |
| Repository format                                         | only pre-existing protected tsconfig.json fails                                         |
| Whitespace / source and historical preservation           | passed                                                                                  |

The focused/full/artifact runs overlap; no cumulative unique-test count is claimed.
Original focused test-harness failures remain in the logs described above. A read-only
schema inspection first attempted recursive reference expansion; JSON's recursive
schema makes that inappropriate. The final audit compares literal branches and all
shared definitions directly, which proves they are unchanged without expansion.
No production fix, expectation change or tolerance relaxation followed that inspection.

Both CLI references completed with the documented values; efficiency 0.81 exited 1
with structured `M20_UNSUPPORTED_INPUT` / `M22 unsupported_qualified_tuple` rejection.
The new result artifacts match the final production implementation/semantic identity.
PFD screenshot evidence is in `benchmarks/m22_separator_pump/screenshots/`; the above
PFD was visually inspected. Automated checks do not constitute human acceptance.

Final read-only remote main still matches the starting HEAD. The index remains empty.
Final inspection found no listeners on 3122, 8122 or 3123. Playwright stopped its own
services; the task-owned smoke server was stopped afterward. No existing user service
was stopped or replaced. Manual startup therefore needs the two isolated-copy services
above, unless another instance has since been started. Both task-start configuration
hashes and every frozen historical file remain unchanged. No engineering blocker was
found for the two exact new combinations; finite-scope and archival/format limitations
remain as documented. No stage, commit, push, deployment or human acceptance.

## Exact M22 file inventory

70 task-owned paths; all unstaged. The two pre-existing configuration edits
are excluded and byte-preserved.

- `MILESTONE_22.md`
- `benchmarks/m22_separator_pump/PLAN.md`
- `benchmarks/m22_separator_pump/README.md`
- `benchmarks/m22_separator_pump/baseline.json`
- `benchmarks/m22_separator_pump/contract_compatibility.json`
- `benchmarks/m22_separator_pump/contracts.py`
- `benchmarks/m22_separator_pump/final_status.txt`
- `benchmarks/m22_separator_pump/finalize.py`
- `benchmarks/m22_separator_pump/historical.json`
- `benchmarks/m22_separator_pump/historical.py`
- `benchmarks/m22_separator_pump/integration.json`
- `benchmarks/m22_separator_pump/integrity.py`
- `benchmarks/m22_separator_pump/inventory.json`
- `benchmarks/m22_separator_pump/logs/browser-focused.log`
- `benchmarks/m22_separator_pump/logs/browser-full.log`
- `benchmarks/m22_separator_pump/logs/build.log`
- `benchmarks/m22_separator_pump/logs/cli-above.json`
- `benchmarks/m22_separator_pump/logs/cli-below.json`
- `benchmarks/m22_separator_pump/logs/cli-unsupported.log`
- `benchmarks/m22_separator_pump/logs/compatibility-focused.log`
- `benchmarks/m22_separator_pump/logs/contract-compatibility.log`
- `benchmarks/m22_separator_pump/logs/contracts.log`
- `benchmarks/m22_separator_pump/logs/diff-check.log`
- `benchmarks/m22_separator_pump/logs/focused-final.log`
- `benchmarks/m22_separator_pump/logs/focused-initial.log`
- `benchmarks/m22_separator_pump/logs/format.log`
- `benchmarks/m22_separator_pump/logs/frontend-focused-final.log`
- `benchmarks/m22_separator_pump/logs/frontend-focused.log`
- `benchmarks/m22_separator_pump/logs/frontend-full.log`
- `benchmarks/m22_separator_pump/logs/historical.log`
- `benchmarks/m22_separator_pump/logs/initial-types.log`
- `benchmarks/m22_separator_pump/logs/integration.log`
- `benchmarks/m22_separator_pump/logs/integrity.log`
- `benchmarks/m22_separator_pump/logs/lint.log`
- `benchmarks/m22_separator_pump/logs/preliminary.log`
- `benchmarks/m22_separator_pump/logs/python-full.log`
- `benchmarks/m22_separator_pump/logs/smoke.log`
- `benchmarks/m22_separator_pump/logs/typecheck-final.log`
- `benchmarks/m22_separator_pump/logs/typecheck.log`
- `benchmarks/m22_separator_pump/manifest.json`
- `benchmarks/m22_separator_pump/preliminary.json`
- `benchmarks/m22_separator_pump/screenshots/above-pfd.png`
- `benchmarks/m22_separator_pump/screenshots/below-pfd.png`
- `benchmarks/m22_separator_pump/source_manifest.json`
- `benchmarks/m22_separator_pump/verification.json`
- `benchmarks/m22_separator_pump/verify.py`
- `contracts/examples/milestone-22-above-requirements.json`
- `contracts/examples/milestone-22-below-requirements.json`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `docs/RIOGINEER_MASTER_CONTEXT.md`
- `engine/riogineer_engine/core.py`
- `engine/riogineer_engine/milestone22.py`
- `engine/riogineer_engine/network.py`
- `engine/riogineer_engine/separator_liquid_pump.py`
- `engine/riogineer_engine/separator_pump_process.py`
- `engine/riogineer_engine/separator_pump_pt200_cases.json`
- `engine/riogineer_engine/separator_pump_scope.py`
- `engine/tests/test_m22_separator_pump.py`
- `engine/tests/test_pt200_profile.py`
- `engine/tests/test_separator_pump_integration.py`
- `engine/tests/test_variable_pump_evidence.py`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/separator-pump-results.tsx`
- `src/app/digital-engineer/workspace.tsx`
- `src/lib/digital-engineer/contracts.ts`
- `tests/e2e/m22-separator-pump.spec.ts`
- `tests/m22-separator-pump.test.ts`

## M22 manual review and targeted presentation corrections — 2026-10-02

**Corrections implemented; final user acceptance remains pending.** Giovani Nunes
exercised both references on 2026-10-02, America/Sao_Paulo. The following are
user-session observations and a reported external ChatGPT review of downloaded
JSON, not a claim that the assistant inspected unavailable attachments.

- Below boundary: outlet approximately 232.00297745 K; fluid power 20567.97887105 W;
  efficiency 0.8; zero vapor flow with unavailable composition; passing mass/energy
  checks and current results. Pump PT200 and historical separator settings were
  displayed separately. The inlet summary read “liquid; evidence: unknown”.
- Above boundary: outlet approximately 232.10320007 K; fluid power 20564.52756884 W;
  liquid approximately 18395.9051504 kg/h and vapor 3.3636496 kg/h; passing balances,
  current results and source_vle evidence.
- Changing efficiency 0.8 → 0.81 marked retained results STALE with an explicit
  warning, disabled PFD/calculation/download and rejected validation with
  `M22 unsupported_qualified_tuple`. Old values remained visibly stale.
- The user downloaded the above JSON. External review reported agreement with
  displayed values, schema 1.15, completed status, explicit `pr_high_accuracy_pt200@1`,
  separately recorded historical source/local settings, liquid saturation source_vle,
  pumped outlet compressed_witness, preserved separator lineage and calculated
  separator duty **−2.0256265997886658e-7 W**.

### Root cause and correction

`separator_liquid_state.representation` intentionally sets source saturation metadata
`source_vle` for a VL parent and `unknown` otherwise. The private execution registry
resolves that real separator liquid without changing metadata. `verify` separately
performs the actual local admission check; its accepted return contains
`inlet.local.status = compressed_witness` below the boundary and
`saturated_source_liquid` above it. The pump serializes those diagnostics under
`equipment[pump].thermodynamics.diagnostics.inlet.local`. Thus the below source has
verified compressed-liquid evidence; “unknown” was never a missing admissibility
check. The frontend incorrectly used the saturation metadata as its generic
“evidence” label.

The panel now reports **Source saturation metadata** and **Local phase evidence**
separately. It reads the accepted inlet diagnostics and reports the lower-pressure
compressed witness or verified parent coexistence. Missing, unrecognized or
unaccepted diagnostics report unavailable evidence. Reference names no longer carry
an inferred phase-success description. No source context, lineage, numerical setting,
guard, serialization, solver or admission change was needed.

A shared display formatter suppresses the string `-0` only after Intl rounds at
the requested precision. The summary keeps six decimals and displays **0 W**; the
8-decimal detail retains **−0.0000002 W** for the above calculated duty. Resolved
nonzero signs and scientific residuals remain. PT duty is still calculated, never
reclassified as imposed adiabatic duty. Raw numbers and downloads are unchanged.

For M22's visible Unavailable calculations list only, the old exact M20 sentence is
presented as **“This model qualifies material and fluid-energy integration only.”**
Historical M20 rendering and the raw legacy JSON reason remain unchanged. The visible
wording is a presentation paraphrase; numerical/export agreement is exact and no
serialized value is rewritten. Hydraulic/NPSH/cavitation/electrical exclusions remain.

### Targeted verification and preservation

Both cases were freshly reproduced locally: **221 checks passed**. Complete result
payloads equal the original M22 payloads exactly after excluding only fresh run UUIDs;
implementation/input hashes, temperatures, flows, enthalpies, power, balances, settings,
phase evidence and lineage associations remain unchanged. Fresh evidence is additive
under `benchmarks/m22_separator_pump/manual_review/`; original M22 artifacts/logs and
all earlier frozen evidence remain byte-identical.

- Focused frontend: **13 passed across three files** (six new defect tests, existing
  M22 contract/freshness coverage and four historical M20 rendering checks).
- Targeted browser: **2 passed** against existing services on 3122/8122, with
  Playwright service management disabled. Checks cover phase labels, calculated
  near-zero duty, neutral limitation text, all stream columns/export equality,
  stale input/profile edits and unsupported efficiency.
- `tsc --noEmit`, affected-file ESLint/Prettier and diff checks pass.
- The initial frontend run had two assertion failures because a whole-page search
  included the deliberately unchanged raw JSON viewer. Assertions now target the
  Unavailable calculations section; original failure log is retained. No product or
  numerical expectation was altered to resolve that test-scope error.

Commands: `PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m22_separator_pump/verify.py --output benchmarks/m22_separator_pump/manual_review/reproduced.json`;
`npx vitest run tests/m22-manual-review.test.ts tests/m22-separator-pump.test.ts tests/separator-pump-summary.test.ts`;
`npx tsc --noEmit`; affected-path `npx eslint` and `npx prettier --check`;
`git diff --check`. In `.local/m22-validation`,
`npx playwright test --config playwright.manual-review.config.ts tests/e2e/m22-separator-pump.spec.ts`
uses a temporary local config with `webServer: []`, preserving running services.

The earlier full **693 Python / 280 frontend / 42 browser** results remain prior
recorded evidence and were **not rerun**. No lengthy full suite, qualification matrix
or build was repeated for these presentation-only corrections. Qualification stays
at the two exact PT200 cases plus 30 historical tuples; no automatic fallback or
scope expansion. The M21 observed 199/200 iteration peak remains prior evidence.

### Review the corrected screens

Corrected application and test files are in the main checkout and synchronized to
`.local/m22-validation`. Existing backend/frontend listeners remain on 8122/3122.
**Refresh the browser; no backend restart is needed.** No running service was stopped
or replaced. Reload/recalculate both references if the page no longer holds results.

Confirm below-source metadata is still unknown/unspecified while local evidence says
verified compressed liquid; above-source metadata is source_vle with verified parent
coexistence. Confirm summary 0 W, calculated PT detail retaining its small negative
value, neutral Unavailable calculations wording, and unchanged results/downloads.
The raw JSON reason retains its legacy wording by design. Recheck the 0.81 rejection
and stale warning if desired. Final acceptance of these corrected screens remains
pending; no acceptance, commit, push or deployment is claimed.

The initial 70-path inventory/manifest above is retained as the initial implementation
record. The current combined inventory, exact correction delta, current hashes and
final Git status are in `benchmarks/m22_separator_pump/manual_review/inventory.json`,
`manifest.json` and `final_status.txt`. Original engine/schema source manifest remains
valid because no backend source changed. Task-start configuration bytes are preserved.

## M22 acceptance and closeout — 2026-10-02

**Current status: accepted by Giovani Nunes on 2026-10-02, America/Sao_Paulo.**
This entry supersedes earlier pending-acceptance and pending-correction-review
statements, which remain historical records. Evidence classification: user-reported
browser acceptance, supported by screenshots and an exported above-boundary results
JSON reviewed in the design conversation. These are the user's observations; Codex
did not perform the human review.

The user accepted both corrected references and the following behavior:

- **PT_BUBBLE_BELOW:** current results and expected separator-to-pump stream mapping;
  discharge 8 MPa absolute, efficiency 0.8, pump outlet approximately 232.00297745 K,
  fluid power approximately 20567.97887105 W. The absent vapor outlet retains
  appropriate unavailable-property semantics; material and energy balances pass.
- **PT_BUBBLE_ABOVE:** current results with separate liquid and small vapor outlets;
  discharge 8 MPa absolute, efficiency 0.8, pump outlet approximately 232.10320007 K,
  fluid power approximately 20564.52756884 W. Material and energy balances pass.
  Downloaded results JSON agrees with displayed values, phase/source context, and
  separate separator and pump numerical settings.
- **Unsupported edit:** changing efficiency from 0.8 to 0.81 invalidates the results,
  explicitly marks previous results stale, and rejects the unsupported tuple.
  Calculation, PFD, and export availability reflect the invalid state. Retained
  historical displays do not represent current acceptance.
- **Corrected presentation, both references:** source-saturation metadata and
  verified local phase evidence are separate. Below-boundary shows verified
  compressed-liquid evidence from the lower-pressure witness with unspecified
  source-saturation metadata. Above-boundary shows verified saturated source-liquid
  evidence from parent equilibrium coexistence with `source_vle` metadata. Summary
  heat duty displays 0 W without negative zero; above-boundary detailed duty retains
  approximately -0.0000002 W, labeled calculated. The corrected M22 limitation reads
  “This model qualifies material and fluid-energy integration only.” No misleading
  M20 reference remains in that visible limitation; the historical raw JSON reason
  remains unchanged, as documented in the correction record.

Acceptance is finite: only the exact documented `PT_BUBBLE_BELOW` and
`PT_BUBBLE_ABOVE` source recipes, 8 MPa absolute discharge, efficiency 0.8, explicit
pump profile `pr_high_accuracy_pt200@1`, and methane/n-hexane with explicit zero
`kij`. Historical separator numerical settings and historical M20 admission with
its 30 workflows remain preserved. There is no automatic fallback/profile selection,
interpolation or continuous operating-envelope qualification, hydraulic sizing,
NPSH, or cavitation qualification. The previously observed 199/200 iteration peak
remains a limitation.

Closeout changes only acceptance documentation and adds closeout bookkeeping.
Solvers, contracts, model scope, numerical outputs, and frozen evidence are unchanged
from the reviewed implementation. The original 70-file inventory and subsequent
90-file combined manual-review inventory remain historical snapshots. The exact
commit inventory is **94 files**: those 90 paths plus four closeout records in
`benchmarks/m22_separator_pump/closeout/` (`baseline.json`, `inventory.json`,
`checks.json`, and `manifest.json`). The closeout manifest records current hashes,
excluding itself; the baseline retains all 90 pre-closeout hashes, allowing the two
updated documents to be distinguished from frozen implementation/evidence files.

Focused closeout verification passed: inventory reconciliation; reviewed evidence
hashes; current engine/schema provenance and archived M21 source identity;
historical artifact and configuration preservation; historical schema branch/shared
definition preservation; generated schema parity; edited-document formatting; and
working-tree whitespace. Explicit staging, staged whitespace, inventory/hash review,
and a normal push are required transaction gates. The final commit and remote
identity are reported in the closeout response, rather than embedded recursively
in the commit itself. `next-env.d.ts` and `tsconfig.json` remain excluded and retain
their task-start bytes. No deployment or service restart/shutdown is authorized.

Earlier automated results retain their original scope and caveats: the implementation
record contains 693 Python, 280 frontend, and 42 browser tests; the later correction
record separately contains 13 final focused frontend tests, two browser workflows,
and 221 numerical comparisons across two cases. Those runs were not repeated or
combined into a new full-suite pass during closeout. Historical intermediate failures
and the documented pre-existing configuration-formatting condition remain recorded.

Next conversation: M22 is accepted only within the finite scope above. Use this
entry and the closeout inventory alongside the earlier qualification evidence;
any broader admission, numerical strategy, or hydraulic claims require separate
work. This closeout does not start M23.

Staged whitespace review found 16 warnings in 10 frozen raw tool logs (trailing
spaces, terminal output indentation, and blank lines at EOF). The full
`git diff --cached --check` returned 2; this is recorded, not a clean full check.
Every affected log matches its reviewed pre-closeout hash. An explicit check of
all other staged paths passed. The logs remain unchanged under the requirement to
preserve frozen evidence; exact diagnostics and paths are in `closeout/checks.json`.
