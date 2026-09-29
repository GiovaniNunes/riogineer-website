# Milestone 9 — First Process Integration of Qualified PT Flash

## Objective and architecture

M9 integrates the qualified standalone M8 `peng_robinson@1.0` PT provider with a new registered `equilibrium_separator_2phase` equipment type, model `pt_flash_separator@1.0`. The existing prescribed-recovery three-phase separators, splitter, mixer, heater and ideal-gas development compressor retain their models and numerical results. No natural-language interpretation or live LLM call is involved.

The primary independent case is `MILESTONE_9_PT_FLASH_SEPARATOR`, profile `pt_flash_separator`. Its authoritative structured topology is:

```text
HYDROCARBON_FEED.outlet → SEP_PR_1.inlet
SEP_PR_1.vapor → VAPOR_PRODUCT_SINK.inlet  (VAPOR_PRODUCT)
SEP_PR_1.liquid → LIQUID_PRODUCT_SINK.inlet (LIQUID_PRODUCT)
```

The separator has exactly inlet/vapor/liquid material ports. It has no water port, recovery fractions, pressure drop, temperature adjustment, heat-duty specification or sizing inputs. Explicit model/provider intent selects PR; component presence and UI labels never select the provider. The controlled profile accepts one separator, one source, two sinks and three streams. It does not authorize arbitrary networks mixing development caloric models with PR phases.

Runtime chain:

```text
source component mass flows + T/P
→ runtime material state
→ MolecularCompositionProvider.enrich
→ M7 Composition (including mass-derived molar fractions)
→ ThermodynamicState with explicit PR/BIP selection
→ PropertyPackage.flash_PT
→ qualified PhaseResult collection
→ phase molar flows × M7 molecular weights
→ outlet material states
→ independent M7 outlet molecular enrichment
→ equipment/process checks, PFD and Engineering Stream Table
```

The adapter retains the actual M7 Composition when selecting PR state provenance. It never constructs an independently stored z-vector. PR parameters, cubic roots, fugacity, stability and Rachford–Rice equations remain in the unchanged M8 provider. Only provider success states produce outlets. Failure reports identify equipment, provider, flash status, iteration count and underlying residual/message diagnostics; no partial result is published.

## Feed, dataset and BIP provenance

Authoritative component dataset: `riogineer_components@1.0`; molecular provider: `molecular_composition@1.0`. The fixture builder multiplies 500 kmol/h of each component by M7 molecular weights, 16.0428 and 86.17536 kg/kmol. Stored engineering inputs are methane **8021.4 kg/h**, n_hexane **43087.68 kg/h**, total **51109.08 kg/h**. M7 reconstructs 500 + 500 = **1000 kmol/h**, z = **[0.5, 0.5]**, mixture MW **51.10908 kg/kmol**.

All three streams are at **300 K** and **300000 Pa absolute** in the primary Case B. The separator is isothermal/isobaric at runtime inlet conditions.

BIP identity: `m9_methane_nhexane_zero_kij@1.0`, explicit ordered components methane/n_hexane and matrix `[[0,0],[0,0]]`, model `peng_robinson@1.0`. Source is the M8 frozen mathematical reference `pre_m8_methane_nhexane_canonical_pr@1.0`; zero kij is not a calibrated physical recommendation. Missing BIPs/provider, nonzero or inconsistent BIPs, invalid T/P/rates, water and unknown components are rejected. No species is silently removed. M9 deliberately permits only the two named components and explicit zero-BIP benchmark scope.

## Phase mapping and balances

For positive feed molar rate F, the calculated beta gives V = beta F and L = (1−beta) F. Each phase component rate is V y_i or L x_i; multiplying by the same authoritative M7 MW produces the outlet component mass rate. Stable engineering identity comes from topology, not phase-object identity: vapor maps to VAPOR_PRODUCT and liquid to LIQUID_PRODUCT.

The adapter independently projects outlet mass rates back through M7. It checks reconstructed compositions against flash x/y, reconstructed V/F and L/F against molar phase fractions, each component molar balance, each component mass balance and total mass balance. Public stream properties are enriched again through the established M7 result path. The frontend does not copy x/y into stream cells.

Process residuals use **feed minus outlets**, with units kg/h or kmol/h. Flash material reconstruction uses the M8 sign convention **(1−beta)x + beta y − z** in mol/mol. Fugacity log residuals and Rachford–Rice residuals are dimensionless. Passing a process material balance is not proof of equilibrium; both layers have independent gates.

Tolerances:

- Frozen beta/x/y comparisons: **1e-9 absolute**, unchanged from M8.
- M8 material reconstruction **1e-10**, log-fugacity reference residual **1e-9**, RR **1e-10**; runtime solver remains stricter where already qualified.
- Expected phase component molar flow: **1e-8 kmol/h**; component mass: **1e-8 kg/h**; total mass: **2e-8 kg/h**.
- Process component molar balance: **1e-8 kmol/h**.
- M7 outlet composition/phase-fraction round trip: **1e-12 absolute**.

These tolerate floating-point multiplication/division and the frozen reference's finite precision without loosening provider equilibrium gates. Extremely large flows outside this controlled case may fail the fixed engineering tolerances; no relative-tolerance expansion is claimed.

## Independently calculated numerical reference

The following values were generated with 40-digit Decimal arithmetic from the frozen M8 Case B beta/x/y and authoritative molecular weights, independently of the equipment output. Display uses 17 significant digits. Formulae are F=1000, V=F beta, L=F(1−beta), n_i=phase flow × phase composition, m_i=n_i MW_i and mixture MW=sum(m_i)/sum(n_i). The same independent arithmetic is exercised in the Python acceptance test.

| Quantity                                                                                                                                               | HYDROCARBON_FEED |       VAPOR_PRODUCT |       LIQUID_PRODUCT |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------: | ------------------: | -------------------: |
| Methane (kmol/h)                                                                                                                                       |            500.0 |  492.73124626978786 |   7.2687537302120945 |
| n-Hexane (kmol/h)                                                                                                                                      |            500.0 |  41.911263954008011 |   458.08873604599201 |
| Total (kmol/h)                                                                                                                                         |             1000 |  534.64251022379590 |   465.35748977620410 |
| Methane (kg/h)                                                                                                                                         |       8021.40000 |  7904.7888376569527 |   116.61116234304659 |
| n-Hexane (kg/h)                                                                                                                                        |     43087.680000 |  3611.7182592916638 |   39475.961740708338 |
| Total (kg/h)                                                                                                                                           |     51109.080000 |  11516.507096948616 |   39592.572903051384 |
| Methane z (mol/mol)                                                                                                                                    |              0.5 |  0.9216088074693791 | 0.015619720085966004 |
| n-Hexane z (mol/mol)                                                                                                                                   |              0.5 | 0.07839119253062085 |    0.984380279914034 |
| Mixture MW (kg/kmol)                                                                                                                                   |         51.10908 |  21.540575013625319 |   85.079909043887784 |
| Temperature (K)                                                                                                                                        |              300 |                 300 |                  300 |
| Pressure (Pa absolute)                                                                                                                                 |           300000 |              300000 |               300000 |
| Frozen beta = **0.5346425102237959**; liquid fraction = **0.4653574897762041**. Production differences below are well inside the specified tolerances. |

## Actual production result

Component vector order throughout this section is methane, n_hexane.

| Quantity                                 | Production value                                  |
| ---------------------------------------- | ------------------------------------------------- |
| Phase classification / convergence       | vapor_liquid / success_two_phase                  |
| Flash iterations                         | 7                                                 |
| Beta, molar fraction                     | 0.5346425102238044                                |
| Liquid fraction, molar                   | 0.4653574897761956                                |
| Liquid x, mol/mol                        | [0.015619720085965972, 0.984380279914034]         |
| Vapor y, mol/mol                         | [0.9216088074693606, 0.07839119253063942]         |
| Vapor total, kmol/h                      | 534.6425102238044                                 |
| Liquid total, kmol/h                     | 465.35748977619556                                |
| Vapor components, kmol/h                 | [492.7312462697858, 41.9112639540186]             |
| Liquid components, kmol/h                | [7.268753730211947, 458.08873604598364]           |
| Vapor components, kg/h                   | [7904.78883765692, 3611.7182592925765]            |
| Liquid components, kg/h                  | [116.61116234304423, 39475.961740707615]          |
| Vapor total, kg/h                        | 11516.507096949495                                |
| Liquid total, kg/h                       | 39592.572903050655                                |
| Z_L / Z_V                                | 0.015469663802426934 / 0.9885027848240121         |
| phi_L                                    | [58.659556020112824, 0.07365204255092793]         |
| phi_V                                    | [0.9941808693398859, 0.9248694390534127]          |
| Final K                                  | [59.002901613928984, 0.0796350700335904]          |
| Log-fugacity residual                    | [1.93196153519537e-14, -2.4541479959339085e-13]   |
| RR residual                              | 1.021405182655144e-14                             |
| Flash material residual, mol/mol         | [-2.275957200481571e-15, 2.220446049250313e-15]   |
| Process component molar residual, kmol/h | [2.2737367544323206e-12, -2.2168933355715126e-12] |
| Process component mass residual, kg/h    | [3.54702933691442e-11, -1.8917489796876907e-10]   |
| Process total mass residual, kg/h        | -1.4551915228366852e-10                           |

M7 reconstructed vapor molar fractions are **[0.9216088074693606, 0.07839119253063942]** and liquid fractions are **[0.015619720085965974, 0.9843802799140341]**, agreeing with y/x within 1e-12. Reconstructed vapor/liquid mixture MWs are **21.54057501362662 / 85.07990904388778 kg/kmol**. Density and all phase volumetric properties remain null/not_calculated; Z is only a separator thermodynamic result.

## Single-phase semantics

The same provider/equipment path handles A/B/C; no frozen phase result is embedded in production.

- **Case A**, 300 K / 30000000 Pa: `single_liquid`, beta=0. All feed component mass goes to liquid unchanged. Vapor remains a declared zero-flow engineering stream, with zero component/total mass and molar rates, null mass/molar fractions and null mixture MW. Vapor composition, Z and phi are absent; K and two-phase fugacity/RR residuals are unavailable.
- **Case B**, 300 K / 300000 Pa: both populated outlets are reconstructed from calculated beta/x/y.
- **Case C**, 300 K / 1000 Pa: `single_vapor`, beta=1. All feed material goes to vapor unchanged; liquid has the corresponding zero/undefined semantics. No liquid composition, Z or phi is fabricated.

Both declared outlet connections and engineering numbers persist for A/C. Present-phase composition equals feed composition and T/P remain unchanged. Zero is a known flow; an absent-phase composition ratio is undefined, not zero or 0.5/0.5.

## Energy and unavailable properties

Isothermal equilibrium does **not** imply zero heat transfer. SEP_PR_1 does not calculate rigorous phase enthalpy, heat duty or shaft work. These fields and enthalpy-flow fields are null; network energy status is `not_calculated`, with an explicit reason. No constant-Cp latent heat or rigorous energy closure is fabricated. Earlier cases retain their existing constant-Cp energy calculations.

No density, phase volumetric flow, entropy, rigorous enthalpy, PH/PS, water/VLLE, pressure drop, sizing, residence time, entrainment, settling/demister/level design, PR heater/compressor integration, recycle or phase-envelope UI is provided. No M10 implementation is included.

## Contracts, provenance and workflow

Only new explicit branches extend the existing versioned readers:

| Contract     | M9 version                                    | Historical readers |
| ------------ | --------------------------------------------- | ------------------ |
| Requirements | 1.4                                           | 1.0–1.3 retained   |
| Flowsheet    | 1.5                                           | 1.0–1.4 retained   |
| Results      | 1.6; process_result_version 1.6; engine 1.5.0 | 1.0–1.5 retained   |

The requirements/flowsheet branches omit the constant-Cp caloric model and carry explicit separator/provider/BIP parameters. The result branch requires null energy fields, enriched M7 stream properties and one typed thermodynamic equipment record. Generated validation schema follows the widened requirements union; unrelated error schema is unchanged. No old version is reinterpreted.

Equipment results are keyed by SEP_PR_1 and include inlet/vapor/liquid stable stream-ID references. Result stream maps carry actual T/P, component mass flows and M7 dataset/provider/MW provenance. Case ID, requirements fingerprint, semantic input/implementation fingerprint and run ID preserve association. Solver status and explicit BIP provenance are in the equipment record. Geometry, array position and stream number do not join results.

Validation and PFD building execute no flash. Building uses the existing topological validation and numbering. The read-only symbol is a rounded two-phase vessel with a phase-interface line; it is generated from structured nodes/ports/connections. Vapor is displayed above liquid by port semantics, independently of numbering.

Actual deterministic numbering is **1 HYDROCARBON_FEED; 2 LIQUID_PRODUCT; 3 VAPOR_PRODUCT**. Repeated building/calculation, array reordering and presentation changes retain identity and numbering. Calculation does not mutate the flowsheet. The Stream Table shows source/destination ports, T/P, mass/molar flow, MW and component mass/molar properties, with unavailable properties as **—**. The equipment panel labels beta as vapor molar fraction of total feed, x/y as liquid/vapor molar compositions, and displays convergence, Z, final K and separate thermodynamic/process residuals.

Loading M9 or another case clears previous validation, flowsheet and results. Tests cover M5↔M9 and M6↔M9. Same-case edits retain only explicitly stale historical results; the M9 thermodynamic panel is rendered only for current results. Layout changes preserve current results and do not call the engine. Regeneration follows the existing stale-result semantics.

## Validation and acceptance gates

New coverage: **7 Python tests, 3 TypeScript tests and 3 browser tests**. Parameterized cases exercise additional branches within these counts. Tests qualify independent expected process flows, full molecular round trip, A/C zero semantics, runtime T/P/mass sensitivity, specification errors/water/unknown species, forced real flash nonconvergence and every failure status, stable identity/numbering, layout/regeneration/repetition, schema strictness and cross-case clearing. The primary browser regression uses the real local Python PR provider, not a mocked flash.

Validation results are recorded below after the complete suite finishes. The feed reconstruction, thermodynamic, phase-flow, mass-conversion, round-trip, process-balance, single-phase, identity and regression gates are explicitly exercised; general suite success alone is not the acceptance basis.

## Manual validation preparation and next step

**Human-operated M9 validation has not occurred.** Automated browser tests and coding-agent visual inspection are separate evidence.

Start the ordinary local Python engine and website, then open `/digital-engineer`:

**Engineering data / Advanced → Load Milestone 9 reference → Validate requirements → Generate PFD → Run engineering calculation.**

Inspect the three-stream diagram, SEP_PR_1, source/sink identity, Stream Table mass/molar results, beta, x/y, phase molar flows, Z, convergence and separate flash/process residuals. Confirm duty/energy and density/volumetric quantities remain unavailable. Switch back to M5/M6 and confirm M9 results clear.

After automated qualification and separate human review, recommend separately scoping **Milestone 10 — Rigorous PR caloric properties / PH flash infrastructure**. Qualified phase enthalpy/entropy is the main missing dependency for process energy accounting and later heater/compressor integration. Water/VLLE remains a separate possible project requiring its own evidence; M9 provides no reason to treat it as automatically qualified. The fixed binary stability scope, zero-BIP benchmark and lack of caloric properties remain deliberate architectural boundaries, not unresolved claims of general process simulation.

## Files and reproduction

Created:

- `engine/riogineer_engine/equilibrium_separator.py` — registered equipment adapter, phase mapping and process checks.
- `engine/riogineer_engine/milestone9.py` — deterministic mass-basis fixture builder.
- `contracts/examples/milestone-9-requirements.json` — generated primary Case B requirements.
- `src/app/digital-engineer/equilibrium-results.tsx` — structured thermodynamic result panel.
- `engine/tests/test_equilibrium_separator.py`, `tests/equilibrium.test.ts`, `tests/e2e/equilibrium.spec.ts` — equipment, contract/UI projection and real-browser qualification.
- `MILESTONE_9.md` — this report.

Modified:

- Engine `core.py`, `network.py`, `network_models.py`, `thermodynamics.py` — version routing, registry, scoped unavailable-energy execution and enrichment.
- `src/lib/digital-engineer/contracts.ts` and generated `contracts/v1/{requirements,flowsheet,results,validation}.schema.json` — explicit compatible new branches.
- `src/lib/digital-engineer/pfd-layout.ts`, `stream-table.ts` — phase-port display order and M9 component molar-flow rows.
- `src/app/digital-engineer/page.tsx`, `workspace.tsx`, `pfd.tsx` — reference loading, conditional result rendering and new symbol.
- `docs/RIOGINEER_MASTER_CONTEXT.md` — current integration and next-step sections only.

Existing component data, M8 solver/provider modules, frozen benchmarks, previous fixtures, interpretation, numbering algorithm and workflow reducer are unchanged. The registry addition does not modify any existing equipment evaluator function.

Reproduce from the repository root:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_equilibrium_separator.py' -v
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
npm test
npm run test:e2e
npm run contracts:check
npm run lint
npm run typecheck
npm run format:check
node_modules/.bin/prettier --check MILESTONE_9.md contracts/examples/milestone-9-requirements.json
git diff --check
npm run build
```

For production smoke, start `SITE_URL=http://127.0.0.1:3200 SITE_INDEXABLE=false RIOGINEER_LLM_PROVIDER='' npm run start -- --port 3200` and run `SMOKE_URL=http://127.0.0.1:3200 npm run smoke` in another terminal. The local browser configuration explicitly disables live LLM selection; existing interpretation regressions use mocks. M9 uses the local real Python thermodynamic provider.

## Completed automated validation — 2026-09-29

| Check                    | Result                                                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Python full suite        | **105 passed**, including all M8 tests and 7 new M9 tests                                                              |
| TypeScript/Vitest        | **200 passed in 18 files**, including 3 new M9 tests                                                                   |
| Browser full suite       | **31 passed**, including 3 new M9 tests against the real local engine                                                  |
| Frozen pre-M8 benchmark  | **7 passed**, including exact frozen-artifact reproduction                                                             |
| M8 production comparison | **122 comparisons passed** across A/B/C; frozen artifacts and solver unchanged                                         |
| Contract parity          | Passed                                                                                                                 |
| ESLint / TypeScript      | Passed                                                                                                                 |
| Formatting / whitespace  | Passed                                                                                                                 |
| Production build         | Passed                                                                                                                 |
| Production smoke         | **17 pages and 17 PNG social cards passed**, plus internal links, 404s, preview indexing and disabled contact delivery |

All nine M9 gates pass. Existing exact M3–M7 process-fingerprint regressions and M8 reference comparisons pass; previous recovery/energy calculations remain unchanged. No live external LLM/provider call was made. Water/VLLE remains unsupported. There are no unresolved acceptance failures; human-operated M9 review remains pending.

The initial sandbox prevented the Python HTTP fixture and browser servers from binding local ports; rerunning those checks with local-server permission passed. An initial new browser assertion treated a horizontal stroked SVG line as a nonzero-area element; the test now checks the line's attachment and the vessel's visibility separately. Visual inspection also caught a long feed label overlapping its source symbol; M9 labels are now fitted to the available connection span. These corrections do not change process calculation or numbering.

Coding-agent inspection of automated screenshots covered the three-stream PFD and thermodynamic result panel. Screenshots under `.local/` are local QA artifacts, not claims of human-operated validation.
