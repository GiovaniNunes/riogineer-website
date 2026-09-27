# Milestone 3.1 — Numbered Process Streams and Engineering Stream Table

## Purpose and reference review

This intermediate milestone documents material streams before multi-equipment or thermodynamic expansion. The PFD and Engineering Stream Table share the flowsheet's stream identities; numbers are engineering data, independent of drawing layout.

The requested Petrobras reference filename was `I-DE-3010.90-1223-943-PPC-001_B(3).pdf`. That exact filename was not found in the supplied attachments or the searched local locations. A local copy with the same drawing number and revision, `I-DE-3010.90-1223-943-PPC-001_B.pdf`, was reviewed using local text extraction and page rendering. The reviewed sheet places numbered material streams above a balance/composition table whose columns use those same numbers. These documentation principles informed this work. No proprietary layout, title block, process data, artwork, corporate formatting or equipment/document identifiers were copied into the RioGineer PFD, table or test fixtures. The reference was not sent to an external provider.

## Identity and numbering

Each flowsheet stream retains its existing stable `id`, `service` and `specified_state`; new version 1.1 streams additionally require a positive integer `engineering_number`. Exactly one connection joins each stream ID to its source owner/port and destination owner/port. Endpoint data remains authoritative in the existing connection object, avoiding a second copy that could drift. Stream names in the views are the service labels; result associations always use the stable ID.

The engine assigns numbers with `number_streams`:

1. Preserve valid existing assignments; reject duplicate/nonpositive numbers or incomplete stream-to-connection associations.
2. Start a directed breadth-first walk from source boundary IDs in lexical order.
3. Visit outgoing connections in lexical source-port order, then destination owner, destination port and stable stream ID. Queue downstream owners once visited; do not use array position or geometry.
4. Assign unnumbered streams consecutive integers above the largest retained number, starting at 1 for a new graph.
5. Number any disconnected/cyclic remainder in lexical source owner/port, destination owner/port and stream-ID order. This makes the helper future-compatible; it does not authorize disconnected graphs, recycles or additional equipment in the current engine.

For the registered single separator, the source feed is numbered first; the separator's `gas`, `oil`, `water` ports then sort in that order. The result is **1 FEED, 2 GAS, 3 OIL, 4 WATER**, without consulting the case name or numerical reference inputs. The helper preserves existing numbers when adding new identities; a completely rebuilt changed topology may have different assignments. Persist the numbered flowsheet to preserve engineering assignments across future editing operations. Layout changes and array reordering never renumber streams.

## PFD, results and table

The existing read-only SVG adds the engineering number next to each service label. Its connections resolve stream objects through `stream_id`. The table below the PFD sorts the same stream objects by their stored engineering numbers, joins the same connection objects by ID, and looks up results through `results.streams[stream.id]`.

No separately maintained table dataset, frontend numbering rule or thermodynamic arithmetic was introduced. A projection enumerates property rows and units; all populated values come directly from flowsheet specified states or engine results. Case, requirements and calculation fingerprints gate result association. The workspace withholds stale results; before a current calculation only available specified feed temperature, pressure and component flows are shown. Total flow is not reconstructed by the frontend.

`Download flowsheet` continues to export the complete structured flowsheet, including stable IDs, engineering numbers, connections, inputs and presentation metadata. No existing field is removed.

## Properties and missing values

| Row                                 | Unit/basis         | Current source                                            |
| ----------------------------------- | ------------------ | --------------------------------------------------------- |
| Stream number, service, internal ID | identity           | Structured flowsheet stream                               |
| Source and destination              | owner ID / port ID | Connection keyed by stream ID                             |
| Pressure                            | Pa absolute        | Engine result, or specified feed state before calculation |
| Temperature                         | K                  | Engine result, or specified feed state before calculation |
| Total mass flow                     | kg/h               | Engine result                                             |
| Component mass flows                | kg/h               | Engine result, or specified feed component flows          |
| Component mass fractions            | kg/kg              | Engine result; null for an absent outlet                  |
| Molar flow                          | kmol/h             | Not calculated                                            |
| Molecular mass                      | kg/kmol            | Not calculated                                            |
| Density                             | kg/m3              | Not calculated                                            |
| Gas, oil and water volumetric flows | m3/h               | Not calculated                                            |
| Component molar fractions           | mol/mol            | Not calculated                                            |

Version 1.1 results add a `properties` object to each existing stream result. Each future scalar property has `value`, `status` and an explicit unit. Molar composition uses the same status pattern with a component-fraction map when calculated. The current engine emits `value: null` and `status: "not_calculated"` for all seven property entries. The contract rejects numeric placeholders with that status, NaN and wrong units. Future qualified providers can use `status: "calculated"` and finite values without redefining stream identity, connectivity, numbering or the table.

The UI displays **—** for unavailable values, with the explanatory note “— = not calculated by the active engineering model.” Actual calculated zero remains **0**. Mass fractions are explicitly labelled kg/kg and never relabelled or converted into molar fractions. No density, molecular-weight, phase-equilibrium, volumetric-flow or other property estimate is introduced. A zero-flow outlet's undefined mass fractions remain unavailable.

## Contract versioning and compatibility

Requirements remain at version **1.0**, byte-identical in schema and reference inputs. The registered recovery model and engine evaluator remain unchanged.

New flowsheets and results explicitly use **1.1** because the new mandatory stream number and property fields would otherwise violate the old strict 1.0 schemas. The authoritative Zod schemas and generated JSON schemas under `contracts/v1/` accept both version branches; the directory and HTTP `/v1/` paths denote the existing major version. Version 1.0 flowsheets remain accepted for calculation and version 1.0 results remain readable. New engine responses are 1.1; old strict clients must upgrade with the engine to read those responses. No document is silently relabelled as a different version.

A legacy flowsheet without numbers is displayed without frontend-invented numbering and carries guidance to regenerate it through the engine. Current builder output always contains validated unique numbers. The Python semantic validator retains all existing supported-topology/numerical checks and adds number uniqueness for 1.1. Stream number changes are engineering-data changes and therefore affect the semantic fingerprint; presentation-only changes remain excluded. Wrapper/schema changes also alter implementation hashes, so prior results may require recalculation even though the numerical model is unchanged.

## Reference results and model scope

The case remains synthetic development assumptions, not I-ET or client data. The active model is **Prescribed Component Recoveries — Development Model**, with unchanged recoveries, constant Cp, feed/operating conditions and reference temperature.

| Stream  | Total mass flow (kg/h) |
| ------- | ---------------------: |
| 1 FEED  |                 110000 |
| 2 GAS   |                  22000 |
| 3 OIL   |                  77550 |
| 4 WATER |                  10450 |

Separator duty remains **0 W**. Existing regression tests compare all stream values, component flows, fractions, temperature/pressure, energy accounting and balances against the unchanged saved reference snapshots. The new property metadata does not add physical calculations.

## Tests and validation

Added Python tests prove deterministic/reference numbering, unique valid assignments, layout and order independence, generic internal-stream traversal and preservation of existing assignments, result associations after stream-ID changes, unavailable-property semantics and legacy compatibility. The generic graph test exercises only the numbering helper, not additional process simulation.

Added TypeScript tests verify shared-object projections, ID-based joins despite reordered arrays, exact reference flows, component flows/fractions, units/bases, unavailable-versus-zero semantics, stale-result exclusion, version compatibility and invalid unavailable placeholders. The browser regression verifies matching SVG/table identities, pre-calculation unavailability, calculated results, units, zero and em-dash rendering, layout stability, downloaded numbered flowsheets and responsive overflow. Desktop/mobile screenshots are reviewed locally.

Final validation results:

| Check                                | Result                                                                                                     |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| TypeScript unit/integration tests    | 176 passed in 13 files                                                                                     |
| Python tests                         | 19 passed, including unchanged numerical/reference checks                                                  |
| Browser suite                        | 17 passed; focused numbered-stream rerun also passed after label positioning                               |
| Contract parity                      | Passed                                                                                                     |
| ESLint                               | Passed                                                                                                     |
| TypeScript type checking             | Passed                                                                                                     |
| Repository and new report formatting | Passed                                                                                                     |
| Production build                     | Passed                                                                                                     |
| Smoke checks                         | 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery passed |
| Diff whitespace                      | Passed                                                                                                     |
| Live-provider calls                  | 0                                                                                                          |

The first browser run exposed an assertion comparing visible text with DOM text; the consistent visible-text comparison passed. Desktop/mobile PFD and table screenshots were inspected. Python HTTP and browser tests used temporary localhost servers with the required sandbox access. No engineering evaluator, reference fixture, requirements/approval validator, evidence anchoring, topology normalization or LLM behavior was changed.

## Files

Created:

- `MILESTONE_3_1.md`
- `engine/riogineer_engine/streams.py`
- `engine/tests/test_streams.py`
- `src/lib/digital-engineer/stream-table.ts`
- `src/app/digital-engineer/stream-table.tsx`
- `tests/stream-table.test.ts`

Modified:

- `src/lib/digital-engineer/contracts.ts`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/README.md`
- `engine/riogineer_engine/core.py` (numbering, metadata and contract versions only)
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/workspace.tsx`
- `tests/e2e/digital-engineer.spec.ts`
- `docs/RIOGINEER_MASTER_CONTEXT.md` (sections 36, 42, 61 and 62 only)

Generated development/test caches and ignored screenshots are not project deliverables.

## Limitations and next step

Only the existing one-feed / one-three-phase-separator / three-outlet topology is enabled. No multi-equipment execution, recycle solving, graphical editing, new equipment, rigorous equilibrium, flash algorithm, EOS, viscosity/density correlation or enthalpy model is implemented. The PFD remains its existing simple read-only layout. The table may scroll horizontally on small screens.

The architectural sequence is **topology and stream identity first, rigorous thermodynamics later**. Next, review the numbered documentation and define the scope/tests for any future multi-equipment topology milestone. Qualified thermodynamic/property providers should later enrich these same identified streams. Neither expansion is part of this work.

## Manual-test correction — stream numbers (2026-09-27)

The manual browser test reported correct numerical results and unavailable-property markers, but headers `— FEED`, `— GAS`, `— OIL`, `— WATER`. The expected engineering cross-references are **1 — FEED, 2 — GAS, 3 — OIL, 4 — WATER**, matching the corresponding PFD material streams. FEED/GAS/OIL/WATER are service names; the internal IDs happen to use the same strings in this reference and are separate software identities.

### Confirmed root cause and trace

A direct deterministic reference build against the running local Python server on port 8001 returned `schema_version: "1.0"` and four streams with no `engineering_number`. That process had loaded the older engine implementation. Python's HTTP server does not reload imported modules when source files change. Fresh test processes used the current 1.1 builder, explaining why earlier tests passed while the manual UI still lacked numbers.

The loss therefore occurred at **structured flowsheet creation by the stale running engine**, before the PFD, rather than during calculation:

1. The API accepted a legacy 1.0 response as a successful new build because its document reader supports both versions.
2. The PFD received streams with no numbers; it previously displayed service names alone.
3. Calculation returned properties keyed by stable stream ID. The reducer retained the original flowsheet streams, including their absence of numbers.
4. The Stream Table joined results to those same objects and rendered its missing-number fallback. It did not overwrite or discard numbered streams.

### Correction and identity preservation

New `build-flowsheet` responses must now be numbered 1.1 documents. An old engine response produces an actionable `ENGINE_VERSION` error instructing the user to restart the Python engine and generate the PFD again. Legacy documents remain readable and calculable; no contract schema changed and no frontend migration or numbering rule was added.

The confirmed stale engine was restarted with the current repository implementation. Its reference build then returned numbers 1–4; repeated generation preserved those numbers. A deterministic calculation against that restarted server confirmed the unchanged reference values: 2,000,000 Pa absolute and 313.15 K for all four streams; mass flows 110000, 22000, 77550 and 10450 kg/h for FEED, GAS, OIL and WATER respectively. An already open browser's legacy state must be regenerated with **Generate PFD** before recalculation; restarting the server cannot mutate an existing browser document.

A shared display formatter now renders the stored engineering number followed by the service name (`1 — FEED`) in both views. The table retains `ID: FEED` as secondary traceability. Legacy unnumbered labels explicitly say `Unnumbered — FEED`; unavailable _properties_ still display `—`.

Calculation continues to enrich the view of the existing structured streams through `results.streams[stream.id]`. The reducer retains the same stream array and object references, updating only calculation status and the separately keyed results. Neither calculation nor layout assigns numbers. No replacement streams, duplicate identity fields or second numbering system were introduced.

### Regression coverage and validation

New API coverage reproduces the observed legacy build response, verifies its rejection with restart guidance, preserves legacy calculation compatibility, and checks the numbered response is forwarded unchanged. Reducer/projection coverage proves object identity survives repeated calculation and layout changes, using reordered streams, different internal IDs and engineering numbers 21–24 to rule out service-name or array-index numbering. Python coverage proves calculation leaves the complete numbered flowsheet unchanged, retains stream objects and arbitrary assigned numbers, and regenerates the same reference stream identities.

Browser coverage explicitly checks matching PFD/table labels before calculation, after calculation, after layout changes, after repeated calculation and after PFD regeneration. It also checks exported numbering, reference mass flows, all-stream pressure/temperature, actual zero and unavailable-property rendering. The first full browser run passed 16/17: the new regeneration test incorrectly expected initial-validation status while the existing results were still current. The test now regenerates through the enabled PFD action and awaits its response.

No engineering evaluator, reference fixture, contracts, evidence anchoring, topology normalization, LLM interpretation or equipment/thermodynamic scope changed. No live-provider call was made. No Flowsheet 03 work was started.

Final correction validation:

| Check                                            | Result                                                                                                     |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| TypeScript unit/integration tests                | 178 passed in 13 files                                                                                     |
| Python suite                                     | 20 passed, including reference snapshot integrity and every saved numerical quantity                       |
| Browser suite                                    | 17 passed on final full run                                                                                |
| Contract parity, lint, type checking             | Passed                                                                                                     |
| Repository/report formatting and diff whitespace | Passed                                                                                                     |
| Production build                                 | Passed; 41 static pages generated                                                                          |
| Production smoke checks                          | 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery passed |
| Restarted local engine                           | 1.1 numbered reference build, unchanged reference calculation and deterministic regeneration verified      |
| Live-provider calls                              | 0                                                                                                          |

Correction files:

- Added `src/lib/digital-engineer/stream-label.ts`.
- Modified `src/lib/digital-engineer/api.ts`, `src/app/digital-engineer/pfd.tsx` and `src/app/digital-engineer/stream-table.tsx`.
- Extended `tests/engineering-api.test.ts`, `tests/engineering-workflow.test.ts`, `tests/e2e/digital-engineer.spec.ts` and `engine/tests/test_streams.py`.
- Updated this report. No contract files changed.
