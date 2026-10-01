# Milestone 17 — Energy-qualified two-phase separator with PT/PH modes

Automated implementation and qualification: **COMPLETE — 2026-10-01**.
Independent qualification, production integration, compatibility and completion
checks passed. User-operated PT, PH, equal-pressure and invalidation checks were
reported on 2026-10-01; their record is separate below. The subsequent general-table
correction is now visually accepted for the three recorded cases, as reported by
Giovani Nunes on 2026-10-01 (America/Sao_Paulo); see the separate acceptance record
below. No deployment is authorized.

## Baseline and relationship to existing capabilities

Started on clean `main` at `c0f03ca6d5fc022f97aac2b2df4115b0a38e3b4f`, completed M16.
Local `main`, locally recorded `origin/main`, and a live `git ls-remote` verification
all matched. No reset, historical fixture replacement or unrelated cleanup occurred.

M1 already provided multiple outlets; M4 generalized acyclic execution. M9 already
qualified PR/PT two-phase material separation. This milestone extends that capability
with explicit vessel pressure and rigorous energy. It reuses M10 calorics, M11 PH
and M16's current valid-interval handling. No new flash, EOS or caloric solver is
introduced. External legacy Flowsheet 03 fixed-K/immiscible-water experiments are
not the production model or numerical reference.

## Model, contracts and bounded topology

New model: `equilibrium_separator_energy_pr@1.0`.
Equipment type remains `equilibrium_separator_2phase`, allowing shared geometry and
ports. Profile: `separator_energy`. Requirements **1.9**, flowsheet **1.10**, results
and process-result **1.11**; engine serialization **1.10.0**.

The new identity is explicit because `pt_flash_separator@1.0` still means M9's
inlet-T/P, material-only calculation with unavailable energy. Historical schema
branches and examples remain intact. The original prescribed-recovery three-phase
model remains a development model. A small extracted `phase_outlets` helper shares
only M9's existing component inventory mapping; callers own energy semantics.

Topology is exactly source → one separator → vapor sink + liquid sink, with ports
`inlet`, `vapor`, `liquid`. No arbitrary mixed-equipment networks or implicit splits.
Stable IDs and engineering numbering remain M9's: feed 1, liquid 2, vapor 3.
Both TypeScript and generated Python JSON schemas distinguish the new mode branches.
Python also validates thermodynamic scope and the passive pressure restriction.

## Inputs, equations and sign conventions

The authoritative inlet is PT-defined: actual received component mass rates (kg/h),
temperature K and absolute pressure Pa. Independent inlet enthalpy is forbidden;
the adapter rejects it rather than silently choosing a state specification. The
actual inlet temperature and pressure are used for high-accuracy equilibrium calorics.
Positive total feed is required; zero, negative/nonfinite flow and inconsistent
component totals are rejected. Exact methane/n-hexane basis and explicit constant
zero kij are required; even zero-inventory water is unsupported.

M7 determines F in mol/s from component mass rates and qualified MWs. Inlet energy
is `Hdot_in = F * h_in[J/mol]`.

- `specified_temperature`: require `separator_pressure_Pa_abs` and
  `separator_temperature_K`. Evaluate high-accuracy equilibrium calorics at that
  P/T and actual overall feed composition. Calculate Q from phase outlet energies.
- `adiabatic`: require separator pressure; reject independent separator temperature
  or heat duty. Set Q=0 and call shared `flash_PH(Psep, Hdot_in/F, composition)`.
  Publish its freshly accepted caloric state, temperature and phase split. No
  equipment-owned outer temperature search exists.

Both modes have zero shaft work and neglect kinetic/potential energy changes.
`Q = Hdot_vapor + Hdot_liquid - Hdot_inlet`, positive into the equipment.
Reported residual is `Hdot_vapor + Hdot_liquid - Hdot_inlet - Q`.

Separator pressure must be positive and no greater than inlet pressure beyond the
existing absolute **1e-8 Pa** numerical comparison tolerance. Equal pressure and
pressure reduction are supported; outlet pressure is not clamped. This is a lumped
specified equipment boundary, not a hydraulic or valve-capacity prediction. Both
material outlets have the same equilibrium temperature and separator pressure.

PT is not labelled adiabatic merely because temperature is specified. Its calculated
duty is independently compared; numerical zero would require `abs(Q)` no larger
than the reported `zero_duty_tolerance_W`. PH explicitly imposes zero duty.

## Phases, balances and acceptance

Independent M17 evidence establishes L/V/VL inlet and outlet categories within the
frozen matrix. The current thermodynamic domain remains 200–500 K, methane/n-hexane,
constant explicit zero kij. This is not a universal pressure/composition envelope.

Phase molar rates are F beta and F(1-beta); component mass rates use each actual
phase composition and MW. Phase energy uses the corresponding phase-specific H,
never the overall H assigned to both outlets. Single-phase inventory is preserved
exactly. Both outlet IDs remain present when one phase is absent:

- component/total/molar flows and enthalpy-flow contribution are zero;
- composition and specific phase enthalpy remain null/unavailable;
- no fictitious phase composition or intensive property is synthesized.

Independent M7 reconstruction checks phase compositions/fractions at 1e-12,
component molar closure at 1e-8 kmol/h, component mass closure at 1e-8 kg/h and total
mass closure at component-count × 1e-8 kg/h. Reconstructed phase enthalpy must agree
with equilibrium H within 1e-6 J/mol. Adiabatic residual allowance is
`F * 1e-6 J/mol + 64*machine_epsilon*max(1 W, abs(Hdot_in), abs(Hdot_out))`.
The arithmetic term permits only extensive floating-point roundoff. PT uses the
same reported energy allowance; its closure is partly an identity, so independent
phase enthalpies and duty are separate mandatory checks.

PH requires one candidate, high-accuracy PT, fresh final acceptance and the existing
1e-6 J/mol residual. M16 interval splitting, no bridging of failures and ambiguity
rejection remain unchanged. Failed units raise controlled calculation errors;
no successful partial result is published. The existing revision/fingerprint UI
invalidates prior results after input edits and hides the dedicated current panel.

## Independent qualification

See `PRE_MILESTONE_17_TWO_PHASE_SEPARATOR_ENERGY_QUALIFICATION.md` for provenance,
units, tolerances, matrix and frozen SHA-256. External reference generation imports
no production thermodynamics. **24 independent cases; 969 production comparisons;
six independent test methods.** Both modes cover equal/reduced pressure, L/V/VL
outlets, positive flow scaling, composition changes and near bubble/dew states.
PT includes positive/negative Q; PH includes liquid-to-VL pressure reduction.

Additional production tests cover real pure coexistence-gap rejection, injected
unbracketed/ambiguous/property-failure states, corrupted phase energies, conflicting
state/mode inputs, invalid ports/topology, actual inlet propagation and M9 preservation.
Synthetic failures are explicitly policy tests, not independent physical cases.

## Workflow and reproduction

Run the engine and website in separate terminals:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8101
RIOGINEER_ENGINE_URL=http://127.0.0.1:8101 npm run dev
```

At `http://127.0.0.1:3000/digital-engineer`:

1. Open **Engineering data / Advanced**.
2. Choose **Load Milestone 17 PT reference** or **Load Milestone 17 adiabatic PH reference**.
3. **Validate requirements → Generate PFD → Run engineering calculation**.
4. Review **Separator energy results**, the phase material/energy table and balance checks.

PT demonstration: 300 K/30 MPa inlet, 350 K/0.3 MPa separator, 100 mol/s equimolar
feed; Q ≈ +1.832535620 MW. PH demonstration: same inlet, 1 MPa separator; Q=0,
calculated T ≈ 291.74213866 K, separate vapor/liquid streams.

Command-line calculations (JSON is printed, no file written):

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone17 --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone17 --mode adiabatic --calculate
```

For requirements JSON only, omit `--calculate`. Versioned examples are in
`contracts/examples/milestone-17-{pt,ph}-requirements.json`.

## Original implementation verification — 2026-10-01

Targeted production tests: 11 methods passed. TypeScript: five new tests passed.
Both new browser workflows passed against the real Python engine, including
Python-to-TypeScript schema parsing, PFD outlets, energy display, engineering-edit
invalidation and failed pressure-increase calculation. The first browser attempt
was blocked by sandbox localhost binding; the permitted retry passed.

Full TypeScript/Vitest: **265 passed**. Final full browser suite: **36 passed**.
Schema parity, ESLint, TypeScript checking, repository formatting, new-document
formatting, Python syntax/trailing whitespace and `git diff --check` passed.
The final production build passed; smoke passed 17 pages, 17 PNG social cards,
internal links, 404s, preview indexing and disabled contact delivery. Temporary
servers were stopped. No live LLM/provider call was made.

A final PFD label review distinguished PT/PH and imposed versus calculated duty.
The added diagram assertion initially also selected the Next.js dev-tools SVG;
restricting it to the accessible PFD image resolved that test-selector defect.
The subsequent full browser suite passed; no numerical tolerance or case changed.

The initial full Python run executed 618 tests with only the HTTP class setup
blocked by sandbox socket permissions. The separate 14-test engine/HTTP file
passed with socket permission. The final complete permitted rerun passed **all
620 Python tests in 711.028 seconds**, including the HTTP tests, historical M1–M16
qualification matrices and the 11 new M17 test methods. No unresolved blocker remains.

Reproduction of completion checks:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
npm test
npm run test:e2e
npm run contracts:check
npm run lint
npm run typecheck
npm run format:check
npm run build
```

Run smoke against a separately started production server (after browser tests,
not concurrently with their build directory):

```sh
SITE_URL=http://127.0.0.1:3200 RIOGINEER_LLM_PROVIDER='' npm run start -- --port 3200
SMOKE_URL=http://127.0.0.1:3200 npm run smoke
```

The server command and smoke command run in separate terminals; stop the temporary
server afterward. Local HTTP and browser tests require permission to bind sockets.

## Human verification and stream-table correction — 2026-10-01

The user reported the following user-operated checks, with screenshots reviewed
in the accompanying ChatGPT discussion. These are user observations, not manual
checks performed by the coding agent; no local screenshot files are claimed.

| Check                  | User-observed result                                                                                                                                                                                                                                                                                     |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PT reference           | Separator 300,000 Pa absolute, specified 350 K; feed 18,399.2688 kg/h, vapor approximately 15,585.658223 kg/h, liquid approximately 2,813.610577 kg/h; calculated Q approximately +1,832,535.619763 W; mass and energy checks passed.                                                                    |
| Adiabatic PH reference | Separator 1,000,000 Pa absolute; calculated T approximately 291.74213866 K; vapor approximately 3,001.467851 kg/h, liquid approximately 15,397.800949 kg/h; imposed Q=0 W; mass and energy checks passed; results current.                                                                               |
| Equal-pressure PH      | Only separator pressure changed to 30,000,000 Pa absolute, then recalculated: T approximately 300 K, liquid 18,399.2688 kg/h, vapor 0 kg/h, imposed Q=0 W; balances passed. Dedicated panel retained absent vapor with zero material/molar/enthalpy flows and unavailable composition/specific enthalpy. |
| Edit invalidation      | Separator pressure edited back to 1,000,000 Pa without validation/calculation: previous calculation panels disappeared; `results.json (not current)` and `flowsheet.json` displayed `null`; PFD/calculation buttons disabled; `Requirements await validation` displayed.                                 |

These observations verify the reported manual engineering results and invalidation
behavior. They also exposed the general Engineering Stream Table defect: molar
flow, molecular mass and molar fractions displayed `—` despite available values in
the dedicated panel. Human review of the subsequent correction was not yet
reported at that stage; completed visual acceptance is recorded separately below.

New automated reproduction distinguishes one detail from the user report above:
a same-case pressure edit retains raw results marked `not current`, shows
`Previous results are stale. Validate, generate the PFD and calculate again.`,
and retains the generic results section marked STALE. The dedicated separator
panel disappears, flowsheet is null and PFD/calculation buttons are disabled.
The unchanged workflow reducer deliberately preserves same-case stale results;
changing case identity clears them. The cause of the different manually reported
JSON/status display was not established. This correction does not alter historical
invalidation behavior or present stale results as current. Initial new browser
assertions expecting the reported validation text were corrected to the verified
existing behavior; the molecular-property assertions already passed.

Root cause: the M17 serializer initialized every stream's `properties` using
`unavailable_properties()`. Rigorous result versions intentionally bypass generic
historical enrichment, while the dedicated panel reads separate thermodynamics
fields. The table faithfully rendered the unavailable serialized properties.

Correction: M17 serialization now uses the existing M7
`MolecularCompositionProvider` and qualified component molecular weights to populate
existing molar-flow, molecular-mass and molar-composition fields for inlet and both
outlets. General-table units are kmol/h and kg/kmol; panel flow in mol/s converts
by 3.6. No schema change, new solver, shared-provider modification or fixture value
hardcoding was needed. Absent phases have zero molar flow, unavailable molecular
mass/fractions, and unchanged zero material/enthalpy flows. Density and volumetric
flows remain unavailable. The table explanation now covers unsupported properties
and undefined intensive properties of absent phases.

Follow-up edits are confined to `separator_energy_process.py`, the Stream Table
component, Python M17 tests, M17 browser tests, this report and the master context.
A copied third-party-notice heading and descriptions were also corrected from
throttling-valve to two-phase separator energy; license text is unchanged.

### Newly executed correction checks

- Focused Python: **29 passed** — 12 M17, seven historical M9, ten M7 molecular-property tests.
- Full TypeScript/Vitest: **265 passed**, including historical table compatibility.
- Production benchmark `--verify`: **24 cases / 969 comparisons passed** against unchanged frozen bytes.
- PT, PH and equal-pressure before/after results matched exactly outside the intended stream molecular properties, run identity and code-dependent fingerprints. Temperatures, phase splits, material flows, duties, enthalpies and residuals were unchanged.
- Focused M17 browser workflows: **3 passed**; final full browser suite: **37 passed**, including PT/PH table values, unit conversion, equal-pressure absent vapor and continued invalidation.
- Schema parity, lint, TypeScript checking, repository/document formatting and `git diff --check` passed. Generated schema review confirmed all historical branches are identical to the baseline.
- Final production build and smoke passed (17 pages, 17 PNG social cards, links, 404s, preview indexing and disabled contact delivery); temporary test servers were stopped.

The original full **620 Python / 265 TypeScript / 36 browser** results and six
independent tests above remain dated implementation evidence. The 12-minute full
Python suite and independent reference-generation suite were not rerun solely for
this isolated serialization correction; shared numerical code did not change.
The new molecular-property test increases M17 methods from 11 to 12.

Unchanged artifact SHA-256 values:

- Independent reference: `f6dfea8e4dad2729cef6ee33096a3f8c9fe76abfe8059e0dd8f18a6258242122`.
- Production comparison: `840b6295dc63c3e8e4c9eedf1cd0e2f91d8e9b13da5d61387bc6a2c463d24665`.

## Completed visual acceptance of the corrected interface

Visual acceptance of the corrected molecular table: **COMPLETE — 2026-10-01,
America/Sao_Paulo**, for the three cases below. Giovani Nunes reported manually
executing the corrected interface. Screenshots were supplied to and reviewed in
the ChatGPT design conversation. This is user-operated evidence with screenshot
review in ChatGPT, not manual execution or direct screenshot inspection by this
Codex session. No screenshots are claimed to be stored in the repository.

All three cases displayed current results and passing mass/energy checks:

- **PT reference:** feed 360 kmol/h and molecular mass 51.10908 kg/kmol;
  liquid 32.85692419 kmol/h; vapor 327.14307581 kmol/h. Molecular masses and mole
  fractions populated consistently. Calculated duty: +1832535.619763 W.
- **Adiabatic PH at 1000000 Pa:** calculated temperature approximately
  291.74213866 K; liquid 187.40076793 kmol/h; vapor 172.59923207 kmol/h.
  Molecular masses and mole fractions populated consistently. Imposed duty: 0 W.
- **Equal-pressure adiabatic PH at 30000000 Pa** (separator pressure equals inlet
  pressure): calculated temperature approximately 300 K; liquid 18399.2688 kg/h
  and 360 kmol/h; liquid molecular mass 51.10908 kg/kmol; liquid mole fractions
  methane 0.5 and n-hexane 0.5. Absent vapor had zero mass, molar, component and
  enthalpy flows. Vapor molecular mass, mass/mole fractions and specific enthalpy
  displayed unavailable (—). Imposed duty: 0 W.

The subsequent molecular-table correction is now visually accepted for these
three cases; no discrepancies were reported in the supplied screenshots. This
acceptance does not broaden the documented qualification scope or supersede the
prior distinction between stale results retained as “not current” and cleared
results. Prior automated evidence remains unchanged. This documentation-only
registration did not rerun numerical or browser regression suites.

## Scope and remaining work

No water, aqueous phase, three-phase implementation, pump, separate KO solver,
entrainment/efficiency correlation, vessel sizing, residence time, hydraulics,
recycles or arbitrary mixed rigorous network is implemented.
Future KO service may reuse this thermodynamic core with its own service evidence.
Future three-phase work may assume mutually immiscible oil/water with no mutual
solubility; full VLLE is not required by that scope. It still needs explicit water
caloric/volatility treatment and independent qualification. Water cannot be passed
to today's PR provider. General mixed-equipment propagation remains separate work.

No historical thermodynamic core equations or tolerances were changed.

## Changed-file inventory

Production engine:

- `engine/riogineer_engine/core.py`
- `engine/riogineer_engine/network.py`
- `engine/riogineer_engine/network_models.py`
- `engine/riogineer_engine/equilibrium_separator.py`
- `engine/riogineer_engine/separator_energy.py`
- `engine/riogineer_engine/separator_energy_process.py`
- `engine/riogineer_engine/milestone17.py`

Contracts and UI:

- `src/lib/digital-engineer/contracts.ts`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `contracts/examples/milestone-17-pt-requirements.json`
- `contracts/examples/milestone-17-ph-requirements.json`
- `src/app/digital-engineer/workspace.tsx`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/stream-table.tsx`
- `src/app/digital-engineer/separator-energy-results.tsx`

Tests and independent evidence:

- `engine/tests/test_separator_energy.py`
- `tests/separator-energy.test.ts`
- `tests/e2e/separator-energy.spec.ts`
- `benchmarks/two_phase_separator_energy/reference.py`
- `benchmarks/two_phase_separator_energy/test_reference.py`
- `benchmarks/two_phase_separator_energy/compare_production.py`
- `benchmarks/two_phase_separator_energy/methane_nhexane_separator_energy_reference.json`
- `benchmarks/two_phase_separator_energy/production_comparison.json`
- `benchmarks/two_phase_separator_energy/requirements.txt`
- `benchmarks/two_phase_separator_energy/THIRD_PARTY_NOTICES.txt`

Documentation:

- `PRE_MILESTONE_17_TWO_PHASE_SEPARATOR_ENERGY_QUALIFICATION.md`
- `MILESTONE_17.md`
- `docs/RIOGINEER_MASTER_CONTEXT.md`

## Repository closeout

The handoff baseline was verified as `main` at
`c0f03ca6d5fc022f97aac2b2df4115b0a38e3b4f`, with 12 modified tracked and 18 new M17
files, nothing staged and no unrelated changes. After this correction, the complete
inventory above contains **31 M17 files: 13 modified tracked and 18 new files**.
The live remote matched the baseline during closeout inspection.

The user explicitly authorized committing completed M17 and normally pushing to
existing `origin/main`, with message
`Complete Milestone 17 energy-qualified separator with PT/PH modes`.
The resulting commit identity and actual push outcome are reported separately in
the closeout response and Git history. No deployment or M18 work is included.
