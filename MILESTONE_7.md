# Milestone 7 — Thermodynamic Property Infrastructure

## Objective and scope

Milestone 7 adds deterministic molecular/composition enrichment to the existing Milestone 3–6 streams. It uses Milestone 6 (`MILESTONE_6_GAS_COMPRESSION`) as its primary integration reference, with the same topology, four process equipment objects, nine numbered material streams and ordinary calculation workflow. No duplicate fixture, equipment type or topology was introduced. Final deterministic human-operated manual browser validation of Milestone 7 was successfully completed on **2026-09-28**, as reported by the user. Manual observations and automated checks are recorded separately below.

Process equipment must not own future thermodynamic equations. This milestone establishes an offline component-data → composition → thermodynamic-state → property-provider boundary. Existing prescribed recoveries, splitter/mixer arithmetic, heater constant-Cp accounting and ideal-gas compressor equations remain unchanged. The molecular provider does not supply Cp/k to those development models or replace their sensible enthalpy basis.

## Authoritative component dataset and provenance

Dataset: **`riogineer_components@1.0`**, in `engine/riogineer_engine/components.py`. Frozen typed `Component` records and a read-only mapping provide canonical-ID lookup. Unit metadata is read-only. Display names do not affect lookup; unknown IDs, display names and case variants are rejected. No alias resolver or additional components were introduced. A future explicitly validated alias map can be added independently; ambiguous aliases must never select a component.

Repository inspection found no qualified critical-property/MW database in the integrated engine. `FLOWSHEET_03_ASSESSMENT.md` identifies earlier experimental MWs as demonstration assumptions, so those values were not reused.

One consistent source is the **CoolProp v7.1.0 tagged fluid database**, inspected during development on 2026-09-28. MW and omega come from `EOS[0].molar_mass` and `EOS[0].acentric`; critical T/P come from `STATES.critical.T/p`. These are stored constants, not runtime calls or imported EOS algorithms. Sources:

- [Methane source data](https://raw.githubusercontent.com/CoolProp/CoolProp/v7.1.0/dev/fluids/Methane.json)
- [n-Hexane source data](https://raw.githubusercontent.com/CoolProp/CoolProp/v7.1.0/dev/fluids/n-Hexane.json)
- [Water source data](https://raw.githubusercontent.com/CoolProp/CoolProp/v7.1.0/dev/fluids/Water.json)

| Canonical ID | Display name | MW (kg/kmol) |  Tc (K) |  Pc (Pa absolute) | omega (dimensionless) |
| ------------ | ------------ | -----------: | ------: | ----------------: | --------------------: |
| methane      | Methane      |      16.0428 | 190.564 |         4599200.0 |               0.01142 |
| n_hexane     | n-Hexane     |     86.17536 |  507.82 | 3044115.328359688 |    0.3003189315498438 |
| water        | Water        |    18.015268 | 647.096 |        22064000.0 |          0.3442920843 |

MW is converted from source kg/mol to kg/kmol by multiplying by 1000. n-Hexane's source binary-serialization spelling `0.08617535999999999` is represented as 86.17536 kg/kmol (eight significant digits, removing the floating-point serialization tail). Other constants retain the published digits. For n-hexane, the first EOS entry's omega is deliberately used, not the alternative entry's 0.299; the selected critical pressure is the explicit critical-state value, not the alternative reducing pressure 3034000 Pa. No values from different releases or secondary references are silently mixed. Later changes require a dataset-version change and recorded qualification.

**Tc, Pc and omega are stored but are not used in any Milestone 7 equilibrium, density or molecular calculation.** The engine requires no network, external property API or CoolProp runtime installation.

## Composition, state and provider architecture

`engine/riogineer_engine/thermodynamics.py` defines:

- **Composition:** immutable projection holding sorted canonical component IDs, component and total mass flows, mass fractions, component and total molar flows, molar fractions and mixture molecular weight. Maps are read-only copies. Existing stream component mass flows remain the authoritative engineering basis; this is not a second independently editable composition or a replacement MaterialStream.
- **ThermodynamicState:** temperature, absolute pressure, Composition and PropertyProvenance. It carries no guessed phase or rigorous energy property. Future providers can extend it with a collection of phase records without altering material-stream IDs or restricting phase count to one vapor/one liquid.
- **PropertyPackage:** a typed protocol with provider identity, explicit capabilities and an `enrich` operation. This milestone implements only `molecular_composition`; PT evaluation and PT/PH/PS flash are outside the implemented interface. There are no fake flash methods or placeholder physical results.
- **MolecularCompositionProvider:** **`molecular_composition@1.0`**, deterministic and offline. It derives only the molecular quantities below.
- **PropertyProvenance:** provider, component dataset, actual molecular weights and completion status. Serialized stream provenance also identifies `component_mass_flow_kg_h` as the input basis.

Calculated stream mass flows, T/P and result fingerprints stay together under the existing stable stream ID. Provenance points to the actual component mass-flow map in the same stream result, avoiding another independent copy. Result case, requirements and input fingerprints continue to gate UI association. The implementation fingerprint includes both new Python modules and generated schemas, so a dataset/code change invalidates previous calculation identity.

## Equations, validation and zero semantics

For mass flow `m_i` in kg/h and molecular weight `MW_i` in kg/kmol:

```text
n_i = m_i / MW_i                       [kmol/h]
n_total = sum(n_i)                     [kmol/h]
z_i = n_i / n_total                   [mol/mol]
MW_mix = m_total / n_total            [kg/kmol]
```

Mass composition is never replaced by molar composition. Positive-flow molar fractions derive from the actual component rates, including separator output distribution; heating or compression alone cannot change these quantities. Composition conversion makes no assertion that oil/water mixtures are a single phase.

Component construction rejects nonfinite MW/Tc/Pc/omega, nonpositive MW/Tc/Pc and booleans. Canonical lookup rejects unknown IDs. The provider rejects empty composition, negative/nonfinite component rates, invalid total mass, inconsistent total mass, invalid T/P, nonfinite molar results and nonpositive/undefined mixture MW for positive flow. Failures abort result publication through the existing structured calculation error. It does not normalize materially inconsistent inputs.

Tolerances:

- Total mass consistency: component count × `1e-8 kg/h`, matching existing balance tolerance.
- Positive-flow molar-fraction sum: `1e-12` absolute.
- Independent tests use 50-digit Decimal arithmetic: molar flow `1e-10 kmol/h`, component mass reconstruction `1e-8 kg/h`, molar fractions and MW `1e-12`, and total mass reconstruction `3e-8 kg/h` for these three components.

Known zero component mass yields calculated zero component molar flow and, for positive total flow, zero molar fraction. For an entirely zero-flow stream, component/total molar flow are calculated zero; molar fractions and mixture MW are null / `not_calculated`. Undefined ratios are never replaced by zero. Density and phase volumetric flow remain null / `not_calculated` for every stream.

## Calculation lifecycle and contract compatibility

The existing deterministic process calculation runs first and still validates its process result. The public calculation entry point then calls molecular enrichment on a copied result, joined by stable stream ID, and validates the enriched result. No equipment evaluator, scheduler, numbering algorithm, flowsheet stream object or PFD source was changed. There is no new user button or separate thermodynamic state lifecycle.

Only the **results contract advances to 1.5**, with engine wrapper **1.4.0**. New fields are:

- `process_result_version`, identifying the preserved process-result structure (1.1, 1.2, 1.3 or 1.4);
- per-stream `properties.component_molar_flow`, with a component-value map, `calculated` status and `kmol/h` unit;
- per-stream `property_provenance`: provider, dataset, molecular-weight map, status and input basis.

Existing molar-flow, molecular-mass and molar-composition property slots now contain genuine calculated values. Their explicit units/status conventions are retained. The new strict result branches retain each earlier process structure and require molecular metadata; older result branches are not reinterpreted or relabelled.

| Reference    | Requirements (unchanged) | Flowsheet (unchanged) | Process-result basis | New calculation result |
| ------------ | ------------------------ | --------------------- | -------------------- | ---------------------- |
| Bia / M3–3.1 | 1.0                      | 1.1                   | 1.1                  | 1.5                    |
| Milestone 4  | 1.1                      | 1.2                   | 1.2                  | 1.5                    |
| Milestone 5  | 1.2                      | 1.3                   | 1.3                  | 1.5                    |
| Milestone 6  | 1.3                      | 1.4                   | 1.4                  | 1.5                    |

All results readers **1.0–1.4 remain supported**, covered explicitly by Python schema and TypeScript reader tests. Legacy flowsheet 1.0 remains calculable without assigning new stream numbers. Requirements schemas 1.0–1.3 and flowsheet schemas 1.0–1.4 remain unchanged; no fixture snapshots were rewritten. Strict clients that only understand old results need the updated reader to accept newly enriched 1.5 responses.

## Reference molecular results

These are actual engine binary-floating-point results, not hard-coded implementation benchmarks. The independent Decimal test oracle uses the declared molecular weights. Component order in the following tables is methane, n_hexane, water.

| Stream                 |   Methane (kmol/h) | n_hexane (kmol/h) |     Water (kmol/h) |     Total (kmol/h) |  MW_mix (kg/kmol) |
| ---------------------- | -----------------: | ----------------: | -----------------: | -----------------: | ----------------: |
| FEED                   | 1371.3316877353082 | 893.5268735749987 |  610.5931923965827 | 2875.4517537068896 | 38.25485851334263 |
| GAS_1 / COMPRESSED_GAS | 1371.3316877353082 |                 0 |                  0 | 1371.3316877353082 |           16.0428 |
| OIL_1 / HEATED_OIL     |                  0 | 893.5268735749987 | 30.529659619829136 |  924.0565331948278 | 83.92343673160242 |
| GAS_2                  |                  0 | 44.67634367874994 |                  0 |  44.67634367874994 |          86.17536 |
| OIL_PRODUCT            |                  0 | 848.8505298962488 | 3.0529659619829137 |  851.9034958582316 | 85.93109472599501 |
| WATER_2                |                  0 |                 0 | 27.476693657846223 | 27.476693657846223 |         18.015268 |

| Stream                 |           z_methane |         z_n_hexane |               z_water |
| ---------------------- | ------------------: | -----------------: | --------------------: |
| FEED                   | 0.47690999717434157 | 0.3107431284225542 |   0.21234687440310424 |
| GAS_1 / COMPRESSED_GAS |                   1 |                  0 |                     0 |
| OIL_1 / HEATED_OIL     |                   0 | 0.9669612642483291 |   0.03303873575167102 |
| GAS_2                  |                   0 |                  1 |                     0 |
| OIL_PRODUCT            |                   0 | 0.9964163006997556 | 0.0035836993002444128 |
| WATER_2                |                   0 |                  0 |                     1 |

FEED remains 110000 kg/h (22000 methane, 77000 n_hexane, 11000 water). OIL_1 and HEATED_OIL remain 77550 kg/h (77000 n_hexane + 550 water), at 313.15 and 333.15 K respectively. GAS_1 and COMPRESSED_GAS remain 22000 kg/h methane, despite pressure increasing from 2000000 to 6000000 Pa and temperature from 313.15 to 433.63373984623405 K. Their molecular projections are identical.

All Milestone 3–6 process-state/equipment/balance values are protected by pre-change fingerprints and existing numerical regressions. HEATER_1 duty remains 953883.333333… W; compressor gas/shaft powers remain 1619836.9468215914 / 1652894.8436955013 W. Network energy residual remains zero. Molecular conversion does not participate in these equations.

## Stream Table, identity and workflow reproduction

The existing table projection already reads the property slots; no frontend MW constants or conversion equations were added. It now shows calculated **Molar flow (kmol/h)**, **Molecular mass (kg/kmol)** and **component molar fraction (mol/mol)**. Mass flow, component mass flow and mass fraction rows remain. Copy clarifies the two composition bases and unavailable density/volumetric flow. Per-stream provider provenance is available in `results.json` without adding a dashboard or cluttering cells.

Density, gas/oil/water volumetric flows continue to show **—**. There is no inferred phase, vapor fraction, rigorous enthalpy, entropy or Z. PFD/table numbers still come exclusively from the structured flowsheet: **1 FEED, 2 GAS_1, 3 OIL_1, 4 WATER_1, 5 COMPRESSED_GAS, 6 HEATED_OIL, 7 GAS_2, 8 OIL_PRODUCT, 9 WATER_2**.

To reproduce the manually validated workflow, restart an older Python engine process so the new code is loaded, then use the ordinary local website/engine setup:

**Engineering data / Advanced → Load Milestone 6 reference → Validate requirements → Generate PFD → Run engineering calculation → inspect Engineering Stream Table.**

Expected change: molecular rows populate while topology, stream numbering and process results remain the same. No new milestone fixture or live LLM request is needed. The completed human-operated Milestone 7 validation is recorded separately below.

## Regression coverage

New Python tests validate all component constants/units/provenance and immutable lookup; invalid constants, unknown components and nonfinite/inconsistent states; independent Decimal conversions for every reference stream; pure methane/hexane/water; changed upstream mass and renamed stream IDs; heater/compressor molecular invariance; zero-flow ratios; unavailable properties; provider capabilities and provenance; all historical contract readers; unchanged exact process fingerprints for four references; repeated calculation/layout/reordering/regeneration identity.

New TypeScript tests cover historical result readers, strict enriched metadata, units and finite-value rejection, stable-ID projection with repeated labels/reversed arrays, stale case/input/requirements fingerprints, and zero versus unavailable values. Existing unsupported-property assertions were narrowed only to properties still unavailable; original engineering regressions remain.

Browser coverage checks every enriched stream row against backend results, PFD/table numbering, unchanged unavailable rows, a real zero-flow Bia outlet and all six M6↔Bia/M4/M5 transitions with molecular-result clearing and current-case association.

## Deferred capabilities and next milestone

No EOS, PR/SRK parameters, cubic roots, fugacity, activity coefficients, Wilson K values, Rachford–Rice, phase stability, VLE/VLLE, PT/PH/PS flash, phase envelope, density or phase volumetric-flow estimation is implemented. In particular, `rho = P MW / RT` is not used to invent an ideal-gas phase for these streams. Existing constant-Cp sensible enthalpy accounting is not replaced by rigorous thermodynamics.

Binary interaction data is **deferred** because this provider has no use for it. No `kij = 0` assumption is made. A future BIP dataset must identify canonical pairs, symmetry where applicable, provenance/model applicability and explicit absence. There is no pseudo-component characterization or expanded component catalog.

A future provider can consume the stored critical data, actual stream T/P and overall molar composition without redesigning stream identity. Phase results should support a collection of phase records with fractions, compositions, properties, convergence status and provider provenance. Water is present in today's composition conversion, but this establishes no water equilibrium model and does not constrain future results to two phases.

**Recommend a separately approved Peng–Robinson EOS + two-phase PT flash qualification milestone**, initially methane + n_hexane without water. It should qualify pure-component PR parameters, alpha function, mixture rules, cubic roots, fugacity coefficients, phase stability/single-phase handling, K initialization, Rachford–Rice, iterative fugacity equality, convergence diagnostics and independent PT-flash benchmarks. **Water-containing three-phase VLLE requires separate qualification** and must not silently become the same two-phase hydrocarbon VLE problem. None of this next-milestone work was implemented.

## Completed automated validation — 2026-09-28

These checks and the agent's inspection of an automated screenshot are distinct from the completed human-operated manual validation recorded below.

| Check                                                   | Result                                                                                                                                  |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| TypeScript/Vitest                                       | **197 tests passed in 17 files**, including five new molecular-property tests                                                           |
| Python unittest discovery                               | **64 tests passed**, including ten new thermodynamic-infrastructure tests and local HTTP integration                                    |
| Playwright                                              | **28 browser tests passed**, including two new molecular-property tests and molecular checks across all six M6↔earlier-case transitions |
| Contract parity                                         | Passed                                                                                                                                  |
| ESLint                                                  | Passed                                                                                                                                  |
| TypeScript type checking                                | Passed                                                                                                                                  |
| Repository formatting and milestone Markdown formatting | Passed                                                                                                                                  |
| Diff whitespace                                         | Passed                                                                                                                                  |
| Production build                                        | Passed                                                                                                                                  |
| Production smoke                                        | **17 pages, 17 PNG social cards**, internal links, expected 404s, preview indexing and disabled contact delivery passed                 |

The production server logged `NoFallbackError` during 404 smoke probes, as in the preceding milestone; the expected HTTP responses and smoke assertions passed. The temporary production server was stopped after validation. Browser test servers were managed by Playwright. Provider interpretation was disabled for browser tests; **no live LLM/provider call was made**. External browsing was limited to development-time component-data provenance research, never runtime property evaluation.

The automated Stream Table screenshot was visually inspected: the new molar rows are populated, unavailable density/volumetric rows remain **—**, and the original PFD/numbering is intact. The table remains horizontally scrollable.

Diff inspection confirmed that all requirements/flowsheet/validation schemas, earlier reference fixtures, snapshotted evaluator, network executor/equipment models, numbering helper, PFD, interpretation and workflow identity modules are unchanged. Pre-M7 process fingerprints for Bia/M4/M5/M6 match exactly. No next-milestone implementation was started.

## File inventory

Created:

- `MILESTONE_7.md`
- `engine/riogineer_engine/components.py`
- `engine/riogineer_engine/thermodynamics.py`
- `engine/tests/test_thermodynamics.py`
- `tests/molecular-properties.test.ts`
- `tests/e2e/molecular-properties.spec.ts`

Modified:

- `docs/RIOGINEER_MASTER_CONTEXT.md` (current-state/next-step sections only)
- `engine/riogineer_engine/core.py` (post-process result enrichment entry point)
- `src/lib/digital-engineer/contracts.ts`
- `contracts/v1/results.schema.json`
- `src/app/digital-engineer/stream-table.tsx` (composition explanatory copy)
- `src/app/digital-engineer/workspace.tsx` (retain process reporting for enriched result versions)
- `src/app/digital-engineer/compression-results.tsx` (accept enriched compressor results)
- `engine/tests/test_compression.py`
- `engine/tests/test_network.py`
- `engine/tests/test_sequential.py`
- `engine/tests/test_streams.py`
- `tests/engine-fixture.ts`
- `tests/network.test.ts`
- `tests/stream-table.test.ts`
- `tests/e2e/compression.spec.ts`
- `tests/e2e/network.spec.ts`
- `tests/e2e/sequential.spec.ts`

## Completed human-operated manual browser validation — 2026-09-28

The user reported that the **final deterministic human-operated manual browser validation of Milestone 7 was successfully completed on 2026-09-28**. This section records the user's browser inspection, separately from the automated test coverage and agent screenshot inspection above. The coding agent did not rerun this manual validation.

The manual validation used the existing Milestone 6 reference workflow:

**Load Milestone 6 reference → Validate requirements → Generate PFD → Run engineering calculation.**

Manual inspection confirmed that the Milestone 6 PFD topology and all nine numbered material streams remained unchanged: **1 FEED, 2 GAS_1, 3 OIL_1, 4 WATER_1, 5 COMPRESSED_GAS, 6 HEATED_OIL, 7 GAS_2, 8 OIL_PRODUCT, 9 WATER_2**. The Engineering Stream Table successfully displayed the new Milestone 7 molecular-property enrichment.

The following displayed FEED values were confirmed:

- Total molar flow: **2875.45175371 kmol/h**.
- Mixture molecular mass: **38.25485851 kg/kmol**.
- Methane molar fraction: approximately **0.47691**.
- n_hexane molar fraction: approximately **0.31074313**.
- Water molar fraction: approximately **0.21234687**.

Both GAS_1 and COMPRESSED_GAS showed:

- Total molar flow: approximately **1371.33168774 kmol/h**.
- Molecular mass: **16.0428 kg/kmol**.
- Methane molar fraction: **1**.
- n_hexane molar fraction: **0**.
- Water molar fraction: **0**.

OIL_1 showed:

- Total molar flow: approximately **924.05653319 kmol/h**.
- Mixture molecular mass: approximately **83.92343673 kg/kmol**.
- Methane molar fraction: **0**.
- n_hexane molar fraction: approximately **0.96696126**.
- Water molar fraction: approximately **0.03303874**.

Molar fractions are dimensionless (mol/mol). These values record the displayed precision observed manually; the full-precision reference calculations above remain unchanged.

Manual inspection also confirmed that molecular properties derive from component mass flows and that mass composition remains authoritative. Compressor pressure/temperature changes do not change molecular composition; the heater temperature change likewise does not change molecular composition.

Density, gas volumetric flow, oil volumetric flow and water volumetric flow all remained displayed as **—**. Calculated zero remained distinct from unavailable / `not_calculated`. Milestone 6 process calculations, balances, compressor results and heater results remained unchanged.

**This manual validation does not validate Peng–Robinson, any EOS, phase equilibrium, PT/PH/PS flash, VLE, VLLE, density or phase volumetric flow. No such capability was implemented in Milestone 7.** The manual validation confirms the bounded deterministic molecular-property enrichment and its integration with the existing workflow.

This documentation update changes no source code, tests, contracts, fixtures, component constants or calculations. No live-provider call was made for this update.
