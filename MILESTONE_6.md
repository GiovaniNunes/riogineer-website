# Milestone 6 — Deterministic Gas Compression

## Objective, qualification and relationship to Milestone 5

Milestone 6 adds a **pressure/work transformation** on the SEP_1 gas branch while preserving the Milestone 5 separator → heater → second-separator oil train and its numerical reference. The compressor is a deliberately restricted ideal-gas constant-property development model, not qualified compressor design or real-gas simulation. All values are synthetic development assumptions, not client or I-ET data.

Case ID: **MILESTONE_6_GAS_COMPRESSION**. Profile: **acyclic_development**. The independent reference is `contracts/examples/milestone-6-requirements.json`. Earlier fixtures remain unchanged and executable. Automated validation is documented separately below. **Final deterministic human-operated manual browser validation was successfully completed on 2026-09-28**, as reported by the user and recorded in the manual-validation section.

## Exact topology and independent branches

```text
FEED.outlet → SEP_1.inlet
SEP_1.gas → COMPRESSOR_1.inlet             [GAS_1]
COMPRESSOR_1.outlet → COMPRESSED_GAS_SINK.inlet [COMPRESSED_GAS]
SEP_1.oil → HEATER_1.inlet                [OIL_1]
HEATER_1.outlet → SEP_2.inlet             [HEATED_OIL]
SEP_1.water → WATER_1_SINK.inlet          [WATER_1]
SEP_2.gas → GAS_2_SINK.inlet              [GAS_2]
SEP_2.oil → OIL_PRODUCT_SINK.inlet        [OIL_PRODUCT]
SEP_2.water → WATER_2_SINK.inlet          [WATER_2]
```

There are four equipment objects, six boundaries, nine material streams and nine connections. GAS_2 is not compressed. After SEP_1, the compressor and heater branches are independently ready; SEP_2 depends on the heater. The existing dependency scheduler and lexical ready-unit tie-break yield **SEP_1 → COMPRESSOR_1 → HEATER_1 → SEP_2** for the reference IDs. Reordered arrays retain semantics; renamed IDs force another valid branch order with identical stream results. Each branch writes only its connected stable stream IDs. External balances count each source and sink-connected product exactly once.

## Registry and runtime state propagation

The authoritative `network_models.MODELS` registry maps `compressor` to **ideal_gas_isentropic_efficiency@1.0**, required `inlet/in/material` and `outlet/out/material` ports, and its executable adapter. There is no fixture-specific scheduler or calculation bypass. Existing owner/port/direction checks, unique occupation, complete required connections, one connection per stream and cycle rejection remain in force.

The executor passes the actual calculated SEP_1 gas state to the compressor using the incoming connection. The compressor preserves component flows, total flow and mass fractions, sets discharge pressure, calculates discharge temperature and adds gas power to inlet sensible enthalpy flow. That state is published as COMPRESSED_GAS and consumed by result projection and external balances; the frontend does no engineering reconstruction.

`EquipmentResult` extends the internal adapter result with explicit `streams`, `duty_W`, `work_W` and type-specific details. A compatibility wrapper preserves existing heat-only adapter return values and equations, assigning zero process work. The generic executor checks incoming enthalpy + heat + process work − outgoing enthalpy. This is a registry-based equipment result extension, not a separate compressor reporting pipeline.

## Declared operating basis and validation

Reference inlet (produced by SEP_1): methane 22000 kg/h, n_hexane/water 0, total 22000 kg/h, 313.15 K, 2000000 Pa absolute. Explicit compressor parameters:

| Parameter             |               Value |
| --------------------- | ------------------: |
| Discharge pressure    | 6000000 Pa absolute |
| Cp                    |       2200 J/(kg K) |
| k = Cp/Cv             |                1.30 |
| Isentropic efficiency |                0.75 |
| Mechanical efficiency |                0.98 |

`inlet_phase: gas` is an explicit development assumption, not an inferred or calculated phase. This model does not detect or handle liquid carryover. Neither Cp nor k comes from an EOS, correlation, CoolProp or external package. A runtime check requires the prescribed Cp to match the inlet's mass-weighted shared network caloric basis within 1e-8 J/(kg K), avoiding inconsistent material-stream enthalpy accounting. It does not calculate new gas properties.

Contracts require finite positive absolute temperatures/pressures and Cp, k > 1 and efficiencies in (0,1]. Runtime validation additionally requires positive inlet mass, nonnegative finite component rates, P2 > P1 and finite calculated ratio/temperatures/powers/enthalpy. Equal or decreasing pressure is rejected. Conditions depending on a calculated upstream inlet are validated at execution. Invalid or overflowing calculations raise a deterministic error and cannot publish a completed result.

## Equations and independently calculated benchmark

```text
ratio = P2/P1
T2s = T1 × ratio^((k−1)/k)
T2 = T1 + (T2s−T1)/eta_is
m_dot = mass_flow_kg_h / 3600
W_gas = m_dot × Cp × (T2−T1)
eta_mech = W_gas/W_shaft
W_shaft = W_gas/eta_mech
mechanical_loss = W_shaft−W_gas
```

The Python model evaluates these equations from explicit inputs. Tests independently evaluate them with 50-digit Decimal logarithm/exponential arithmetic: pressure-ratio tolerance 1e-12, temperature tolerance 1e-10 K and power tolerance 1e-6 W. Reference outputs (binary-floating-point calculation, shown to useful precision):

| Quantity                                 |       Calculated value |
| ---------------------------------------- | ---------------------: |
| Pressure ratio                           |                    3.0 |
| Isentropic discharge temperature         |    403.5128048846755 K |
| Actual discharge temperature             |   433.63373984623405 K |
| Mass flow for power                      | 6.111111111111111 kg/s |
| Gas/process power                        |   1619836.9468215914 W |
| Shaft power                              |   1652894.8436955013 W |
| Mechanical loss outside process boundary |    33057.89687390998 W |
| Compressor heat duty                     |                    0 W |
| Compressor energy residual               |                    0 W |

Positive heat/work means energy supplied to process material. The gas power is the gas sensible enthalpy-flow increase. **Gas power is not shaft power, and neither is heater duty.** Optional driver efficiency/electrical power is deferred: it is not needed to qualify the material-state/shaft-work boundary and would add utility fields without a driver model. No driver power or efficiency is invented.

## Process energy boundary and checks

The material-stream boundary excludes mechanical losses. Its accounting is:

```text
Hin + Qheat + Wprocess − Hout = residual
Wprocess = energy actually transferred to compressor gas
Wshaft = Wprocess + external mechanical losses
```

The network exposes heat input (`duty_W`), `process_work_W`, `shaft_power_W`, `mechanical_loss_W`, `external_enthalpy_change_W`, residual and the explicit `positive_work: work_into_process` convention. Existing `work_W` is the process work on each equipment; compressor shaft requirement is separately identified inside `compression`. Unrelated equipment does not populate compressor-only fields.

| Network quantity                         |     Reference result |
| ---------------------------------------- | -------------------: |
| Heat input                               |  953883.3333333329 W |
| Gas/process work input                   | 1619836.9468215914 W |
| Shaft input requirement                  | 1652894.8436955013 W |
| External sensible enthalpy-flow increase |  2573720.280154924 W |
| Energy residual                          |                  0 W |
| Energy tolerance                         |               1e-6 W |

The external increase closes against **heat + gas/process work**, not heat + shaft power. A regression explicitly verifies that using shaft power would leave the mechanical-loss discrepancy. There is no pressure-work/EOS property package; this is limited constant-Cp sensible-enthalpy accounting, not rigorous plant energy closure.

All equipment component and total mass residuals are zero in this reference; all equipment energy residuals close within 1e-6 W. Component tolerance remains 1e-8 kg/h; total tolerance remains component count × 1e-8 kg/h (3e-8 here). Compressor residuals are exactly zero in the reference execution. The unchanged SEP_2 evaluator's duty remains approximately −4.66e-10 W, numerically zero within tolerance, and is not hard-coded to zero.

## Actual deterministic stream numbering and results

The unchanged breadth-first stream-numbering algorithm assigns the following values from this new topology. They are not encoded in React or inferred from execution order. New topology numbering differs from Milestone 5 after stream 4 because the added compressor outlet is visited before the heater outlet. Existing stored assignments remain preserved; each independent fixture is built deterministically.

| Number | Stable ID / displayed service | Total (kg/h) |    Temperature (K) | Pressure (Pa absolute) |
| -----: | ----------------------------- | -----------: | -----------------: | ---------------------: |
|      1 | FEED                          |       110000 |             313.15 |                2000000 |
|      2 | GAS_1                         |        22000 |             313.15 |                2000000 |
|      3 | OIL_1                         |        77550 |             313.15 |                2000000 |
|      4 | WATER_1                       |        10450 |             313.15 |                2000000 |
|      5 | COMPRESSED_GAS                |        22000 | 433.63373984623405 |                6000000 |
|      6 | HEATED_OIL                    |        77550 |             333.15 |                2000000 |
|      7 | GAS_2                         |         3850 |             333.15 |                2000000 |
|      8 | OIL_PRODUCT                   |        73205 |             333.15 |                2000000 |
|      9 | WATER_2                       |          495 |             333.15 |                2000000 |

Service/name, stable ID and engineering number remain distinct concepts even when labels match IDs. Owner/port endpoints remain in connections. Results join by stable ID and existing case/requirements/input fingerprints. Repeated calculation, display layout, input array reordering and PFD regeneration preserve the ID→number mapping.

COMPRESSED_GAS contains methane 22000 kg/h with mass fraction 1.0; n_hexane and water are calculated zeros. Every Milestone 5 stream's numerical state remains unchanged in the corresponding Milestone 6 stream, including OIL_1/HEATED_OIL composition 77000 kg/h n_hexane + 550 kg/h water. SEP_2 retains GAS_2 = 3850 kg/h n_hexane, OIL_PRODUCT = 73150 n_hexane + 55 water, and WATER_2 = 495 water. Heating still does not predict these independently prescribed recoveries.

## Network mass balances

Only external products are counted:

```text
Total: 110000 − (22000 + 10450 + 3850 + 73205 + 495) = 0 kg/h
methane: 22000 − 22000 = 0 kg/h
n_hexane: 77000 − (3850 + 73150) = 0 kg/h
water: 11000 − (10450 + 55 + 495) = 0 kg/h
```

Internal GAS_1, OIL_1 and HEATED_OIL do not add external inventory or energy. Equipment checks and network checks include both independent branches exactly once.

## PFD, Stream Table and engineering results

The PFD renders all ten nodes and nine material connections from structured data. A simple converging compressor symbol distinguishes it from the heater and separator; no proprietary artwork or independent reference drawing is used. It remains read-only.

The existing Stream Table automatically presents all nine numbered streams, source/destination, P/T, total/component flows and fractions. COMPRESSED_GAS shows calculated 6000000 Pa absolute and 433.63373984623405 K, formatted for display only; stored units remain SI with kg/h mass flow.

The compressor results view projects the deterministic equipment result: inlet/discharge pressure, ratio, inlet/isentropic/actual temperature, Cp, k, efficiencies, gas power, shaft power, mechanical loss, zero heat duty, all mass residuals and energy residual, with explicit units. A network section separately labels heat, process work, shaft requirement, external losses and external enthalpy change.

Density, molar flow, molecular mass, volumetric flows and molar composition remain null / `not_calculated`, displayed **—**, while calculated zero remains 0. No Z or real-gas enthalpy is fabricated.

## Contract changes and compatibility

The authoritative Zod definitions were inspected: Milestone 5 requirements 1.2 and flowsheet/results 1.3 do not admit a compressor or its parameters/results. The smallest explicit extensions are:

| Document     | New version | Structural reason                                                                                                   |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Requirements | 1.3         | Adds compressor equipment/model, discharge pressure, Cp, k, efficiencies and explicit gas assumption                |
| Flowsheet    | 1.4         | Adds compressor equipment/model, ports and operating parameters to the structured executable graph                  |
| Results      | 1.4         | Adds type-specific `compression` details and separate process/shaft/network energy quantities; engine wrapper 1.3.0 |

The profile and aggregate model remain `acyclic_development` / `acyclic_component_conservation@1.0`. Existing major-version API routes and schema-file locations remain. No older document is relabelled; new output versions follow submitted requirements versions. Previous contract branches remain unchanged and reject compressor documents mislabelled as earlier versions.

Bia remains requirements 1.0 / numbered flowsheet-results 1.1; Milestone 4 remains requirements 1.1 / flowsheet-results 1.2; Milestone 5 remains requirements 1.2 / flowsheet-results 1.3. Readers retain legacy flowsheet/results 1.0 support. Natural-language interpretation remains on its qualified single-separator requirements contract. No interpretation, evidence or approval capability expansion occurred.

Exact added input fields are `discharge_pressure_Pa_abs`, `cp_J_kg_K`, `heat_capacity_ratio`, `isentropic_efficiency`, `mechanical_efficiency`, `inlet_phase`. The strict compressor result `compression` object adds inlet/discharge pressure, pressure ratio, inlet/isentropic/actual temperatures, Cp/k, both efficiencies, `gas_power_W`, `shaft_power_W`, `mechanical_loss_W`. New network energy fields are listed in the boundary section above. Existing heat and work fields retain their physical separation; old heat-only equipment always had zero work.

## Tests, reproducibility and manual preparation

`engine/tests/test_compression.py` independently computes the analytical benchmark, tests invalid inputs and finite enforcement, verifies exact conservation and energy semantics, captures changed runtime SEP_1 gas P/T/component flow, compares the entire oil-train state against the unchanged Milestone 5 fixture, exercises alternate branch orders, identity/layout/rebuild behavior, port/caloric mismatches, cycles and failed energy adapters.

TypeScript integration checks old/new version separation, exact API payload forwarding and ID-based projection. Browser tests verify every PFD node and numbered stream, all stream flows/P/T/fractions, unavailable properties, every compressor results label/value, process versus shaft display, layout/regeneration and all six cross-case transitions between Milestone 6 and Bia/Milestones 4–5. Cross-case changes clear validation, flowsheet and results; existing revision/fingerprint protections remain authoritative.

To reproduce the validated workflow, restart any already-running pre-Milestone-6 Python process, then run `PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8001` and `npm run dev` in separate terminals. At `/digital-engineer` use **Engineering data / Advanced → Load Milestone 6 reference → Validate requirements → Generate PFD → Run engineering calculation**. The Python process does not hot-reload. No LLM call is needed. The completed human-operated validation is recorded separately below.

## Physical limitations, future providers and recommendation

The compressor assumes ideal gas, constant Cp/k, prescribed isentropic/mechanical efficiencies and a gas-only inlet. It has no EOS (PR/SRK), Z correction, real-gas enthalpy, property correlation, compressor map, polytropic calculation, surge/choke, speed, stage count/design, intercooling, aftercooling, liquid carryover handling, mechanical sizing or driver sizing. No driver model, pump, valve, generic exchanger, anti-surge recycle, tear/convergence solver, PT/PH/PS flash, VLE/VLLE/phase envelope, graphical editing, arbitrary-network LLM interpretation or complete Flowsheet 03 migration was implemented.

A future qualified property provider may supply Cp, Cv/k, Z, enthalpy, entropy, density and phase state behind the registered equipment/state interfaces. Stable equipment/stream identity, ports, graph topology, numbering and PFD/table projection need not change. No such provider is implemented now.

**Recommend A: qualified thermodynamic/property infrastructure next**, following the completed manual validation of Milestone 6. Milestones 3–6 have exercised prescribed separation, branch/merge, sequential state propagation, heat/temperature and pressure/work transformations, and independent branches. Another simplified equipment adapter would now add less architectural evidence than qualifying consistent thermodynamic states, reference enthalpy and phase/property validity. Define a narrow provider interface and independent benchmark/acceptance criteria before implementing any EOS. This recommendation is not implementation or authorization for the next milestone.

## Implementation file inventory

Created:

- `MILESTONE_6.md`
- `contracts/examples/milestone-6-requirements.json`
- `engine/tests/test_compression.py`
- `src/app/digital-engineer/compression-results.tsx`
- `tests/compression-fixture.ts`
- `tests/compression.test.ts`
- `tests/e2e/compression.spec.ts`

Modified:

- `docs/RIOGINEER_MASTER_CONTEXT.md` (minimal current-state/next-step update)
- `src/lib/digital-engineer/contracts.ts`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `engine/riogineer_engine/core.py`
- `engine/riogineer_engine/network.py`
- `engine/riogineer_engine/network_models.py`
- `src/app/digital-engineer/page.tsx`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/workspace.tsx`
- `tests/engine-fixture.ts` (legacy-result type narrowing)

## Completed automated validation — 2026-09-28

These are automated checks and agent inspection of automated screenshots, **not human-operated manual browser acceptance**:

- TypeScript/Vitest: **192 tests passed in 16 files**.
- Python unittest discovery: **54 tests passed**, including seven compressor regression methods and local HTTP integration. Local HTTP binding required running the suite outside the restricted sandbox; the final complete run passed.
- Playwright: **26 browser tests passed**, including two new Milestone 6 tests and all six cross-case transitions.
- Contract generation parity, ESLint, TypeScript checking, repository formatting and documentation/reference-fixture formatting: **passed**.
- `git diff --check`: **passed**.
- Production build: **passed**.
- Production smoke: **17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery passed**. The server logged `NoFallbackError` during the 404 probes; the expected HTTP behavior and smoke assertions passed.
- Automated PFD and compressor/network-energy screenshots were visually inspected. All nine numbered connections and the separate heat/work/power quantities are displayed; the wide Stream Table remains horizontally scrollable.
- Protected earlier reference fixtures, stream-property implementation, interpretation and workflow modules have no diff. The full earlier-case regression suite passed, and the Milestone 5 oil-train comparison passed.

The temporary production server was stopped after validation. No live-provider/LLM call was made. Human-operated manual validation was subsequently completed and is recorded separately below. No next-milestone implementation was started.

## Completed human-operated manual browser validation — 2026-09-28

The user reported successful completion of the final deterministic human-operated manual browser validation of Milestone 6 on **2026-09-28**. This record documents human inspection of the browser workflow and results; it is separate from the automated test coverage and agent screenshot inspection recorded above.

The manually validated workflow was:

**Load Milestone 6 reference → Validate requirements → Generate PFD → Run engineering calculation.**

The manual inspection confirmed the complete Milestone 6 PFD containing FEED, SEP_1, COMPRESSOR_1, COMPRESSED_GAS_SINK, WATER_1_SINK, HEATER_1, SEP_2, GAS_2_SINK, OIL_PRODUCT_SINK and WATER_2_SINK.

Nine numbered material streams were present:

| Engineering number | Stream service / stable ID |
| -----------------: | -------------------------- |
|                  1 | FEED                       |
|                  2 | GAS_1                      |
|                  3 | OIL_1                      |
|                  4 | WATER_1                    |
|                  5 | COMPRESSED_GAS             |
|                  6 | HEATED_OIL                 |
|                  7 | GAS_2                      |
|                  8 | OIL_PRODUCT                |
|                  9 | WATER_2                    |

The observed deterministic execution order was **SEP_1 → COMPRESSOR_1 → HEATER_1 → SEP_2**.

Manual inspection confirmed that COMPRESSOR_1 consumes the **calculated SEP_1 gas stream** and that its calculated outlet pressure, temperature and composition propagate to **COMPRESSED_GAS**:

| Observed quantity        | Compressor inlet | Compressor outlet |
| ------------------------ | ---------------: | ----------------: |
| Total mass flow (kg/h)   |            22000 |             22000 |
| Pressure (Pa absolute)   |          2000000 |           6000000 |
| Temperature (K)          |           313.15 |      433.63373985 |
| Methane mass flow (kg/h) |            22000 |             22000 |

The following compressor values were manually confirmed:

| Quantity                                              |            Observed value |
| ----------------------------------------------------- | ------------------------: |
| Pressure ratio                                        |                       3.0 |
| Isentropic discharge temperature                      |              403.512805 K |
| Actual discharge temperature                          | approximately 433.63374 K |
| Cp                                                    |             2200 J/(kg K) |
| k                                                     |                       1.3 |
| Isentropic efficiency                                 |                      0.75 |
| Gas/process power                                     |          1619836.946822 W |
| Mechanical efficiency                                 |                      0.98 |
| Shaft power                                           |          1652894.843696 W |
| Mechanical losses outside the process-stream boundary |            33057.896874 W |
| Compressor heat duty                                  |                       0 W |
| Compressor total and component mass residuals         |                    0 kg/h |
| Compressor energy residual                            |                       0 W |

The manual inspection also confirmed the network and unchanged heater results:

| Quantity                               |   Observed value |
| -------------------------------------- | ---------------: |
| HEATER_1 duty                          |  953883.333333 W |
| Network heat input                     |  953883.333333 W |
| Network gas/process work input         | 1619836.946822 W |
| External sensible enthalpy-flow change | 2573720.280155 W |
| Network energy residual                |              0 W |

Global and component mass-balance checks passed with zero residuals. Milestone 5 oil-train values remained unchanged. Unsupported thermodynamic properties continued to display as **—**.

The UI clearly distinguished gas/process power from shaft power and mechanical losses. The displayed limitations correctly identified the compressor as an **ideal-gas constant-Cp/k development model with prescribed efficiencies**, with no EOS, Z correction, real-gas enthalpy, compressor map or rigorous compressor design.

This documentation update records the user-reported manual validation only. No source code, tests, contracts, fixtures or calculations were changed, and no live-provider call was made for this update.
