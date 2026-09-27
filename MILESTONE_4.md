# Milestone 4 — First Deterministic Multi-Equipment Flowsheet

## 1. Objective and outcome

Milestone 4 adds a deterministic, acyclic material network with branching and merging to the existing RioGineer architecture. It retains the Milestone 3/3.1 single-separator reference and its unchanged Prescribed Component Recoveries — Development Model. Only splitter and mixer equipment are introduced. This is an architecture/reference demonstration using synthetic development assumptions, not a qualified offshore process simulator.

The new deterministic fixture is `contracts/examples/milestone-4-requirements.json`, case `MILESTONE_4_BRANCH_MERGE`. In the Digital Engineer workspace, open **Engineering data / Advanced**, select **Load Milestone 4 reference**, then **Validate requirements → Generate PFD → Run engineering calculation**. No LLM call or interpretation approval is represented by loading this explicit fixture. The existing natural-language interpretation/review path remains limited to its single-separator capability.

## 2. Relationship to the Flowsheet 03 assessment

`FLOWSHEET_03_ASSESSMENT.md` identified useful component-conservation, port-validation and dependency-readiness algorithms. These concepts were reimplemented in the current typed/versioned architecture. No legacy file, Stream class, plant network, drawing implementation, tear solver or thermodynamic model was migrated. The assessment proposed a branch/rejoin proof; the implementation follows the subsequently requested **60/40** split, not the assessment's illustrative 40/60 proposal.

## 3. Exact reference topology

```text
FEED.outlet -> SEP_1.inlet
                 gas   -> GAS_SINK.inlet
                 water -> WATER_SINK.inlet
                 oil   -> SPLIT_1.inlet
                              outlet_a -> MIX_1.inlet_a
                              outlet_b -> MIX_1.inlet_b
                                              outlet -> OIL_SINK.inlet
```

There are one source, three sinks, three equipment objects, seven streams and seven connections. The split/rejoin is a directed acyclic graph, not a recycle. Source node ID `FEED` and stream ID `FEED` inhabit distinct namespaces. Connectivity is specified explicitly in requirements and materialized in the structured flowsheet; calculation and rendering do not infer it from the service labels.

## 4. Equipment and model registry

`engine/riogineer_engine/network_models.py::MODELS` keeps executable adapters, model identifiers and required port directions together:

| Type                  | Model                               | Required input ports | Required output ports |
| --------------------- | ----------------------------------- | -------------------- | --------------------- |
| three_phase_separator | prescribed_component_recoveries@1.0 | inlet                | gas, oil, water       |
| splitter              | proportional_split@1.0              | inlet                | outlet_a, outlet_b    |
| mixer                 | equal_condition_mix@1.0             | inlet_a, inlet_b     | outlet                |

Source ports are `outlet/out/material`; sink ports are `inlet/in/material`. Separator execution calls the existing snapshotted `recovery_model.py::evaluate` without modifying its equations, recoveries or numerical fixtures. The new graph can schedule these registered types by connectivity, including multiple instances, but does not admit any other equipment type.

## 5. Splitter model

The splitter multiplies **each component mass flow** by the explicit outlet fraction, derives total mass and mass fractions, propagates inlet T/P unchanged and distributes the existing enthalpy-flow accounting by the same fraction. It adds no duty or work. Fractions must be finite and nonnegative; both named outputs are mandatory. The absolute fraction-sum error must be **less than 1e-12**. Fractions are never normalized or inferred. Equipment conservation checks must also pass, so fraction-sum acceptance alone cannot publish an imbalanced calculation.

| Quantity (kg/h) | Inlet | outlet_a, 0.60 | outlet_b, 0.40 |
| --------------- | ----: | -------------: | -------------: |
| methane         |     0 |              0 |              0 |
| n_hexane        | 77000 |          46200 |          30800 |
| water           |   550 |            330 |            220 |
| Total           | 77550 |          46530 |          31020 |

A zero fraction is valid: its stream has zero component/total flows, null mass fractions and unchanged specified T/P. Unavailable property fields remain null, not zero.

## 6. Mixer model

The mixer sums component flows, recomputes total flow and mass fractions, and sums the already available inlet enthalpy flows. It only supports equal inlet conditions: maximum-minus-minimum T must be **≤1e-8 K** and P **≤1e-8 Pa**. All connected inlets, including absent branches, are checked. The value from the lexically first inlet port is propagated; no averaging or enthalpy-based temperature solve occurs. Differences exceeding tolerance raise a deterministic `CALCULATION_FAILED` error naming the mixer and unsupported field, rather than returning an invented temperature or pressure.

Reference output: methane 0, n_hexane 77000, water 550, total **77550 kg/h**, **313.15 K**, **2000000 Pa absolute**. Mass fractions are methane 0, n_hexane `77000/77550` and water `550/77550`. Tolerance-equivalent inputs are treated as the same development-model condition; this is not a general mixing or pressure-equalization model.

## 7. Generic port and connectivity validation

`engine/riogineer_engine/network.py::validate` validates the versioned schema and then graph semantics:

- Unique equipment/boundary IDs, stream IDs, connection IDs and engineering numbers; component keys match the declared basis.
- Exact registered required port sets and directions; no unknown owners or ports.
- Exactly one connection per stream and one occupation per required material port. Both input and output ports must be connected.
- Only source-connected streams carry independent specified states; source component flows must have the complete basis and positive total flow.
- At least one source and sink; registered type/model combinations only; common explicit caloric basis and valid recoveries/fractions.
- Cycles are rejected before execution and before a new graph is numbered.

Duplicate consumers/producers cannot implicitly create a split or merge. They require explicit splitter/mixer ports. Pressure increase across a separator is rejected when its upstream state is available at execution. Numerical overflow/nonfinite values, invalid balances and unsupported mixer conditions cannot produce a completed result.

## 8. Dependency scheduling

The engine uses a Kahn-style dependency traversal: source stream IDs are initially available; equipment is ready only when all its connected inputs are available. Among ready equipment it selects the lexically smallest stable ID, publishes that equipment's output availability and repeats. The resulting order drives the registered model adapters. Nothing hard-codes “separator, splitter, mixer” as an execution sequence.

For this graph the actual order is **SEP_1 → SPLIT_1 → MIX_1**. Tests rename those tags to reverse their lexical relationship, reverse input arrays and execute other graphs to prove dependency ordering. A separate independent-branch test checks canonical tie-breaking among simultaneously ready units.

## 9. Cycle detection

When pending equipment remains and no unit is ready, validation raises **“Cycle detected: recycle networks are not supported by this milestone”**. No tear is selected, no stream is guessed and no iteration runs. A regression creates a closed separator/splitter/mixer cycle while retaining valid single-use ports and an external feed-to-sink path; validation rejects the cycle rather than silently calculating the reachable fragment.

## 10. Stream identity and result association

The structured flowsheet retains stable IDs, stored engineering numbers, service labels and source/target owner-port connections. `network.calculate` never mutates the flowsheet or reallocates its stream identity objects. Its separate state map and returned results are keyed by stable stream ID, obtained from connections rather than service names. The existing workflow reducer retains the same stream array/object references across calculation and layout changes. The Stream Table joins those objects to current results by ID and case/requirements/input fingerprints.

Two streams in this reference deliberately share service `oil`: `OIL` (internal separator outlet) and `OIL_PRODUCT` (final mixer outlet). Their IDs and numbers distinguish them. Tests also rename every stream ID and assign an identical service label to all streams without changing calculation associations.

## 11. Actual deterministic numbering and connectivity

The unchanged Milestone 3.1 `streams.py::number_streams` assigns numbers by directed breadth-first traversal, lexical port/endpoints and stable-ID tie-breaking. It preserves existing assignments. Calculation, presentation and array order do not determine numbers.

| Number | Stable stream ID | Displayed service | Source           | Destination      |
| -----: | ---------------- | ----------------- | ---------------- | ---------------- |
|      1 | FEED             | FEED              | FEED.outlet      | SEP_1.inlet      |
|      2 | GAS              | GAS               | SEP_1.gas        | GAS_SINK.inlet   |
|      3 | OIL              | OIL               | SEP_1.oil        | SPLIT_1.inlet    |
|      4 | WATER            | WATER             | SEP_1.water      | WATER_SINK.inlet |
|      5 | OIL_A            | OIL_A             | SPLIT_1.outlet_a | MIX_1.inlet_a    |
|      6 | OIL_B            | OIL_B             | SPLIT_1.outlet_b | MIX_1.inlet_b    |
|      7 | OIL_PRODUCT      | OIL               | MIX_1.outlet     | OIL_SINK.inlet   |

The final PFD/table label is **7 — OIL**, with **ID: OIL_PRODUCT** in the table. Numbers are not embedded in React or in the requirements fixture. All seven derive from the structured graph. Regenerating the same graph, reversing arrays, changing layout and repeating calculation preserve these assignments. Calculation also preserves nonconsecutive preassigned numbers.

## 12. PFD generation

`src/lib/digital-engineer/pfd-layout.ts::graphLayout` derives deterministic presentation layers from owner-to-owner dependencies. Ports within each direction determine connection attachment positions. It only computes geometry; it does not assign stream identity or perform engineering calculations. `pfd.tsx` renders each structured connection and uses the same `streamLabel` formatter as the table. Every node and material stream is rendered from the data, with no separate reference drawing. The existing single-separator view remains supported.

The new graph is a read-only SVG with horizontal scrolling when needed. The display-width toggle changes presentation only. Graphical editing, optimized diagram routing and a drawing-to-model importer are outside scope.

## 13. Engineering Stream Table

The existing table/projection already enumerates structured streams and component rows. Its properties branch now also reads results 1.2. It displays all seven stream numbers/services/IDs, owner/port endpoints, pressure, temperature, mass flow, component flows and mass fractions. Larger tables scroll horizontally, including the final product column.

Molar flow, molecular mass, density, gas/oil/water volumetric flow and component molar fractions remain **null / not_calculated**, displayed **—**. Real calculated zeros remain **0**. No thermodynamic estimates were added to the frontend or Python property metadata.

## 14. Equipment and branch/merge balances

For each executed equipment, component residual is Σin−Σout; total mass residual independently compares summed inlet/outlet totals. Component tolerance is **1e-8 kg/h**, total tolerance is **component count × 1e-8 kg/h** (3e-8 here). Exceeding either tolerance fails the calculation. Results contain each equipment's model/type, component/total residuals, tolerances, duty, work and constant-Cp energy residual. The UI exposes equipment checks and execution order.

| Equipment | methane residual | n_hexane residual | water residual | Total residual (kg/h) | Energy residual (W) |
| --------- | ---------------: | ----------------: | -------------: | --------------------: | ------------------: |
| SEP_1     |                0 |                 0 |              0 |                     0 |                   0 |
| SPLIT_1   |                0 |                 0 |              0 |                     0 |                   0 |
| MIX_1     |                0 |                 0 |              0 |                     0 |                   0 |

These explicitly include splitter inlet = sum of branches and mixer sum of branches = outlet. A test injects a nonconserving adapter result and verifies it cannot be published.

## 15. Network balances and final products

External balances count **source streams and sink-connected streams only**. Internal streams are not counted as additional feed/product inventory.

| Product sink | Stream ID   | Total (kg/h) |
| ------------ | ----------- | -----------: |
| GAS_SINK     | GAS         |        22000 |
| WATER_SINK   | WATER       |        10450 |
| OIL_SINK     | OIL_PRODUCT |        77550 |

`110000 − (22000 + 10450 + 77550) = 0 kg/h`. Every external component residual is also zero: methane `22000−22000`, n_hexane `77000−77000`, water `11000−(10450+550)`. Tests assert both equipment and network balances rather than treating internal circulation as external flow.

## 16. Energy-accounting scope

The preserved separator evaluator remains the only separator equation implementation. Network source enthalpy accounting uses the same existing declared `Σ(m_i Cp_i (T−Tref))/3600` convention. A single common constant-Cp/reference-temperature basis is required across the network. Splitters scale that accounting; equal-condition mixers sum it. They have zero duty/work and do not solve a new thermodynamic state.

Equipment and network residuals compare incoming enthalpy flow plus separator duties with outgoing enthalpy flow, at **1e-6 W** tolerance. Reference duty and residual are **0 W**. Tests also preserve the original nonzero-duty reference behavior with separator temperature 333.15 K. The new result sign convention explicitly says `heat_into_network`; old result versions retain `heat_into_separator`.

This is accounting closure **within the declared constant-Cp development model and supported equal-condition mixing only**. It is not rigorous plant energy closure, phase-equilibrium prediction, pressure-work accounting, latent-heat modeling or general enthalpy-based mixing.

## 17. Reference numerical results

All seven streams have **313.15 K** and **2000000 Pa absolute**. Feed/reference T, Cps and separator recoveries are unchanged from Bia: Tref 273.15 K; Cp methane/n_hexane/water = 2200/2200/4180 J/(kg K); methane entirely gas, n_hexane entirely oil, water 5% oil/95% water.

| Stream ID   | methane (kg/h) | n_hexane (kg/h) | water (kg/h) | Total (kg/h) |
| ----------- | -------------: | --------------: | -----------: | -----------: |
| FEED        |          22000 |           77000 |        11000 |       110000 |
| GAS         |          22000 |               0 |            0 |        22000 |
| OIL         |              0 |           77000 |          550 |        77550 |
| WATER       |              0 |               0 |        10450 |        10450 |
| OIL_A       |              0 |           46200 |          330 |        46530 |
| OIL_B       |              0 |           30800 |          220 |        31020 |
| OIL_PRODUCT |              0 |           77000 |          550 |        77550 |

The original `contracts/examples/requirements.json` and `engine/fixtures/treinamento-bia-110000/` remain unchanged and independently reproducible. The new case does not overwrite the old fixture or reuse its case ID.

## 18. Tests and validation

New Python coverage in `engine/tests/test_network.py` covers exact topology/numbers; component/total splits and recombination; P/T and fractions; unavailable versus zero; invalid split values/sums; unequal-condition mixer rejection and tolerance boundaries; node/port/direction/occupation errors; duplicates/missing ports; cycles; caloric/component basis; invalid model/pressure increases; generic dependency ordering/tie-breaking; renamed stream IDs/duplicate services; immutability; layout/reordering; repeated runs and engineering-fingerprint invalidation. Existing snapshot tests compare all original Bia quantities and byte hashes.

`tests/network.test.ts` and `tests/network-fixture.ts` exercise real Python-produced contracts, the API boundary, version separation from interpretation, seven-stream results, shared-object projection, stale-result exclusion, unknown properties, generic layout and ID/number preservation. `tests/e2e/network.spec.ts` exercises the actual local API/engine through the browser, verifies all nodes/streams, PFD/table number equality before/after repeated runs/layout/regeneration, numerical rows, all unavailable-property rows and zero values, plus invalid-split blocking. Desktop/mobile screenshots were inspected; all columns remain available by horizontal scrolling.

Final validation results are recorded below after the completed suite. No live-provider call is required or made; browser interpretation tests use controlled responses.

## 19. Explicit contract version changes

The authoritative Zod definitions remain in `src/lib/digital-engineer/contracts.ts`; generated JSON schemas remain under major-version directory `contracts/v1/` and HTTP endpoints remain `/v1/`.

| Document            | Existing support preserved                               | New branch and fields                                                                                                                                                                                            |
| ------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Requirements        | 1.0 single separator unchanged                           | 1.1 `acyclic_development`: explicit sinks, streams/service labels and owner/port connections, registered equipment array with parameters, shared caloric model; splitter fractions explicit                      |
| Flowsheet           | 1.0/1.1 unchanged; new single-separator builds still 1.1 | 1.2 numbered graph: variable-length supported nodes/streams/connections, equipment-specific parameters, shared caloric model, `solver.method=topological`                                                        |
| Results             | 1.0/1.1 readable; single-separator results still 1.1     | 1.2 seven/arbitrary graph stream IDs, per-equipment balance/duty/work records, execution order, model tolerances; network duty sign; engine wrapper 1.1.0 and aggregate model acyclic_component_conservation@1.0 |
| Validation response | Original single-separator response readable              | Deterministic response can contain either supported requirements branch                                                                                                                                          |

The original `requirementsSchema`/`Requirements` and `validationResponseSchema` exports remain single-separator-only for interpretation/review. New `engineeringRequirementsSchema` and `engineeringValidationResponseSchema` unions serve the deterministic API and schema generator. This intentionally avoids expanding natural-language capability or weakening approval/provenance controls.

New graph contracts bound equipment to 50, streams/connections to 200, feeds to 50, sinks to 100 and components to the existing 50 limit. Only the three registered equipment types are allowed. Strict schema validation is followed by graph/model validation; schema acceptance alone is not engineering approval. Old strict clients must upgrade to read the new graph versions; no old document is relabelled silently.

## 20. Limitations and deliberately deferred functionality

No recycles, tears, convergence iterations, compressors, pumps, valves, heaters/coolers, heat exchangers, treaters, hydrocyclones, flotation or TEG were introduced. No EOS, flash, rigorous equilibrium, phase-state prediction, new density/viscosity/molar property calculation, graphical editing or complete Flowsheet 03 migration exists in this milestone. Mixer topology has exactly two inlets; splitter has exactly two outputs. Direct source data must have positive total flow; zero downstream branches are supported, but a zero-feed separator is not newly qualified.

The PFD layout is a simple dependency-layer view, not an optimized routing engine for arbitrary large diagrams. Natural-language interpretation still rejects multi-equipment requests; the new capability is deliberately a deterministic Advanced reference. Python's local server does not hot-reload code: restart it after upgrading before manual use of the new schema versions.

## 21. Files and reproducibility

The complete created/modified file list and final validation counts are recorded in the closing validation section. The implementation is reproducible without an external provider by loading the new fixture in the workspace or invoking `build_flowsheet` and `calculate` with it in the existing Python environment. The original **Restore reference** action continues to load the single-separator Bia fixture.

## 22. Recommended next milestone

First collect engineering review of the multi-equipment identity, branch/merge checks and read-only views. Preserve both deterministic cases as independent regressions. A separately approved future milestone may qualify one analytically testable recycle with explicit solver contracts and failure diagnostics. Rigorous thermodynamics and additional physical equipment models require separate model qualification; they are not part of this implementation.

## Closing validation and file inventory

| Check                                                                 | Final result                                                                                                   |
| --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| TypeScript unit/integration                                           | 183 passed in 14 files                                                                                         |
| Python suite                                                          | 38 passed, including 18 new network tests and the unchanged reference snapshot checks                          |
| Browser suite                                                         | 19 passed, including both new network browser tests                                                            |
| Contract parity                                                       | Passed                                                                                                         |
| ESLint                                                                | Passed                                                                                                         |
| TypeScript checking                                                   | Passed                                                                                                         |
| Repository formatting and milestone/contract documentation formatting | Passed                                                                                                         |
| Production build                                                      | Passed; 41 static pages generated                                                                              |
| Production smoke                                                      | 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery passed     |
| Diff whitespace                                                       | Passed                                                                                                         |
| Local engine after restart                                            | Both original and Milestone 4 references validated/built/calculated successfully; zero external mass residuals |
| Live-provider calls                                                   | 0                                                                                                              |

Python HTTP tests, browser tests and production smoke used temporary local servers. Browser provider responses were controlled; no external LLM request was made. The existing port-8001 engine was restarted with the current code to avoid the stale-process failure documented in Milestone 3.1. Temporary browser/production servers were stopped; the local development engine remains available.

The original requirements fixture, entire saved Bia evaluator/reference fixture directory, numbering helper, interpretation/evidence/topology modules and specification review component have no changes. Master Context updates are limited to sections 36, 61 and 62. Generated test caches/screenshots are ignored artifacts, not source deliverables.

Created:

- `MILESTONE_4.md`
- `contracts/examples/milestone-4-requirements.json`
- `engine/riogineer_engine/network.py`
- `engine/riogineer_engine/network_models.py`
- `engine/tests/test_network.py`
- `src/lib/digital-engineer/pfd-layout.ts`
- `tests/e2e/network.spec.ts`
- `tests/network-fixture.ts`
- `tests/network.test.ts`

Modified:

- `contracts/README.md`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `docs/RIOGINEER_MASTER_CONTEXT.md`
- `engine/riogineer_engine/core.py`
- `scripts/generate-engine-contracts.mjs`
- `src/app/digital-engineer/page.tsx`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/workspace.tsx`
- `src/lib/digital-engineer/api.ts`
- `src/lib/digital-engineer/contracts.ts`
- `src/lib/digital-engineer/stream-table.ts`
- `tests/engine-fixture.ts`
- `tests/engineering-contracts.test.ts`

Stopped after the deterministic reference, documentation and complete validation. No recycle solver, additional equipment or new thermodynamic model was implemented.

## Manual browser validation correction — requirements feedback

The first manual test loaded the Milestone 4 reference and received HTTP 200 from **Validate requirements**, but the unchanged `null` JSON panels and lack of nearby confirmation made validation appear ineffective.

The response contains exactly `requirements` (the unchanged validated input, including version 1.1 and numerical values) and `validation` (`status: valid` and model messages). The client already parses the engineering validation-response union and dispatches the revision-guarded `validated` action, setting `validated=true` and `busy=false`. It neither replaces the draft nor publishes a flowsheet or results. There was no lost response or requirements-version mismatch. Success feedback and the enabled PFD controls were farther down the page, while the validation button stayed enabled. The same presentation defect affected the original version-1.0 Bia reference.

The Advanced requirements controls now include an accessible live confirmation, **Requirements validated**, with a **Generate PFD** link to the existing PFD controls. Repeat validation is disabled while the current requirements remain validated. Engineering edits invalidate that confirmation and enable validation again. Errors show a distinct nearby message linking to the existing detailed engineering error; unsuccessful validation cannot enable PFD generation.

The intended workflow remains **Load reference → Validate requirements → Generate PFD → Run engineering calculation**. Immediately after initial validation, `flowsheet.json` and `results.json` **should both be null**. Generate PFD publishes the numbered structured flowsheet; only the explicit calculation action produces results. Version-1.1 backend validation internally builds a temporary graph to check graph/model semantics, but does not execute the engineering calculation or return that graph. This existing behavior was preserved. No frontend stream numbering was introduced.

Two new browser regressions exercise the exact load/validate sequence for Milestone 4 and the original reference. They assert HTTP 200, the complete unchanged returned requirements, unchanged editor data, in-viewport confirmation, disabled repeat validation, enabled PFD generation, navigation to its controls, null flowsheet/results, and no build/calculation requests during validation. Both failed on the missing local confirmation before the correction. The invalid-split test now also verifies successful validation followed by edit invalidation and distinguishable failure feedback. Existing browser and Python tests continue to verify deterministic PFD/table numbering, layout/regeneration stability and both numerical references.

Only `src/app/digital-engineer/workspace.tsx`, `tests/e2e/network.spec.ts` and this document changed. No contracts, reducers, engine calculations, graph execution, numbering, reference values, interpretation or provenance code changed. No live-provider call was made.

Correction validation: **183 TypeScript tests in 14 files, 38 Python tests and 21 browser tests passed**. Contract parity, ESLint, TypeScript checking, repository/document formatting and diff whitespace checks passed. The production build generated 41 static pages; production smoke passed 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery. Both engineering reference cases and their identity regressions passed unchanged. Temporary test servers were stopped. Live-provider calls: **0**.

## Manual case-transition diagnosis and correction

The reported browser observation was the old `THREE_PHASE_SEPARATOR_DEV_001` / `single_separator_development` identity and single-separator limitations after the Milestone 4 workflow. A deterministic browser reproduction first completed Bia, then loaded, validated, built and calculated Milestone 4 using the real local API/Python engine. No provider was called. The test records full request/response and displayed-state objects in its `case-transition-trace.json` attachment.

**Reproduced root cause:** the requirements `edit` reducer cleared validation and flowsheet but retained `results` unconditionally. The first mixed-case display occurred immediately at **Load Milestone 4 reference → local state**: active requirements were Milestone 4 and flowsheet was null, but the raw results and limitations still belonged to Bia. They were labelled not-current/STALE and could not be downloaded as current, yet remained visible through Validate and Generate PFD. Human approval of a different case had the same retention behavior.

**Diagnostic limit:** no actual active-case replacement was reproduced. All Milestone 4 validation/build/calculation requests and responses retained the correct identity, and the successful final calculation replaced the stale Bia results even before this correction. An old final flowsheet with `single_separator_development` was not reproduced; results themselves do not have a `profile` field. The reported final-case reversion therefore cannot be attributed to the engine on this evidence. The demonstrated defect is cross-case stale presentation, not a numerical engine failure.

The page initializes Bia only through `useReducer` initialization. Load Milestone 4 and Restore reference dispatch their respective fixtures as edits; no effect resets them. Build reads the current draft and calculate reads the current stored flowsheet. The Next API forwards the validated request payload unchanged; the Python POST adapter dispatches that payload, with requirements 1.1 selecting the network builder. The separate GET reference endpoint is not used by these actions. There is no default-fixture substitution in this path.

### Captured identity at each boundary

`M4` below means case **MILESTONE_4_BRANCH_MERGE**; `Bia` means **THREE_PHASE_SEPARATOR_DEV_001**. M4 equipment IDs are **SEP_1, SPLIT_1, MIX_1**, and boundary IDs are **FEED, GAS_SINK, WATER_SINK, OIL_SINK**. The prior Bia equipment ID is **SG-1223002**, with four streams. M4's requirements profile is already distinct; no identity/version correction was necessary.

| Boundary                                 | Case | Schema | Profile / model                    | Equipment IDs         | Streams |
| ---------------------------------------- | ---- | ------ | ---------------------------------- | --------------------- | ------: |
| Loaded local requirements                | M4   | 1.1    | acyclic_development                | SEP_1, SPLIT_1, MIX_1 |       7 |
| Validate request                         | M4   | 1.1    | acyclic_development                | SEP_1, SPLIT_1, MIX_1 |       7 |
| Validate response requirements           | M4   | 1.1    | acyclic_development                | SEP_1, SPLIT_1, MIX_1 |       7 |
| Validated local requirements             | M4   | 1.1    | acyclic_development                | SEP_1, SPLIT_1, MIX_1 |       7 |
| Generate PFD / build request             | M4   | 1.1    | acyclic_development                | SEP_1, SPLIT_1, MIX_1 |       7 |
| Build response / stored flowsheet        | M4   | 1.2    | acyclic_development                | SEP_1, SPLIT_1, MIX_1 |       7 |
| Calculation request                      | M4   | 1.2    | acyclic_development                | SEP_1, SPLIT_1, MIX_1 |       7 |
| Calculation response / displayed results | M4   | 1.2    | acyclic_component_conservation@1.0 | SEP_1, SPLIT_1, MIX_1 |       7 |

M4 equipment models remain prescribed_component_recoveries@1.0, proportional_split@1.0 and equal_condition_mix@1.0. Before the fix, the results display at Load, Validate and Generate additionally retained Bia results schema 1.1 / prescribed_component_recoveries@1.0 / SG-1223002 / four streams. The new browser regression failed those three null-result assertions before production code changed; its other identity and final numerical assertions passed.

### Correction and intended state machine

On an engineering edit or approval, results are now cleared when their existing `case_id` differs from the new draft's case. The existing revision increment and late-response guard remain authoritative. Within-case numerical edits still retain explicitly stale results for the established Milestone 3 comparison workflow. Layout and formatting-only edits preserve their existing behavior.

Build acceptance additionally checks flowsheet case/profile against the active draft. Calculation acceptance and current-result status now check case ID and `requirements_sha256` as well as the existing `input_sha256`; the current flowsheet must also match the draft case/profile. No parallel numbering, revision, hash algorithm or identity system was added. Mismatches cannot publish current results.

| Completed action  | Active requirements           | Validation | Flowsheet                               | Results                                     |
| ----------------- | ----------------------------- | ---------- | --------------------------------------- | ------------------------------------------- |
| Load M4 after Bia | M4 1.1, new local revision    | Invalid    | null                                    | null                                        |
| Validate          | Same M4 requirements/revision | Current    | null                                    | null                                        |
| Generate PFD      | Same M4 requirements/revision | Current    | M4 1.2, seven numbered streams, not_run | null                                        |
| Calculate         | Same M4 requirements/revision | Current    | Same M4 identity/streams, current       | M4 1.2, matching case and both fingerprints |

The browser regression checks each request and response, stored artifacts, all seven PFD nodes, splitter/mixer visibility, seven table columns, unchanged stream identity/numbers and reference mass flows **110000, 22000, 77550, 10450, 46530, 31020, 77550 kg/h**. Unit regressions cover cross-case edit/approval invalidation, late responses, wrong-case/profile builds and mismatching result case/requirements hashes even with a matching input hash. Existing Bia and same-case stale-result regressions remain in place.

Files changed for this correction: `src/lib/digital-engineer/workflow.ts`, `tests/engineering-workflow.test.ts`, `tests/e2e/network.spec.ts`, and `MILESTONE_4.md`. No contracts, reference identifiers, reference values, Python code, numerical models, graph scheduling, stream numbering, evidence anchoring or interpretation code changed.

Case-transition correction validation: **186 TypeScript tests in 14 files, 38 Python tests, and 22 browser tests passed**. Contract parity, ESLint, type checking, repository/document formatting and whitespace checks passed. Production build passed with 41 static pages; smoke passed 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery. Original Bia snapshots and both reference numerical results remain unchanged. Temporary validation servers were stopped. Live-provider calls: **0**.
