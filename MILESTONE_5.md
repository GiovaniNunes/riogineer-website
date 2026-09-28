# Milestone 5 — Sequential Process Equipment: Heater and Second Separator

## Objective and relationship to Milestone 4

This milestone qualifies deterministic sequential state propagation through a condition-changing heater and a second instance of the existing prescribed-recovery separator. Milestone 4's splitter/mixer branch remains independently supported and unchanged. These are synthetic development assumptions, not I-ET or client data. Automated validation is recorded below; **manual browser validation has not been performed by the user and is not claimed**.

## Reference case and topology

Case ID: `MILESTONE_5_SEQUENTIAL_PROCESS`. Profile: `acyclic_development`. The existing acyclic profile still describes the solver/capability family; the distinct case ID and explicit contract versions distinguish this reference from Milestone 4 without a parallel identity system.

```text
FEED.outlet → SEP_1.inlet
SEP_1.gas → GAS_1_SINK.inlet
SEP_1.water → WATER_1_SINK.inlet
SEP_1.oil → HEATER_1.inlet
HEATER_1.outlet → SEP_2.inlet
SEP_2.gas → GAS_2_SINK.inlet
SEP_2.oil → OIL_PRODUCT_SINK.inlet
SEP_2.water → WATER_2_SINK.inlet
```

There are three equipment instances, six boundaries (one source and five sinks), eight material streams and eight explicit connections. No splitter, mixer or recycle occurs in this reference.

## Registry, heater and separator models

The existing Python `network_models.MODELS` registry remains the authoritative mapping from equipment type to model identity, required ports and executable adapter. It now additionally registers `heater` → `specified_outlet_temperature_constant_cp@1.0`, with exactly `inlet/in/material` and `outlet/out/material` ports. Existing separator, splitter and mixer adapters retain their equations.

The heater accepts a positive, finite explicit `outlet_temperature_K` and explicit `caloric_model`, which must equal the shared network caloric basis. It preserves each component mass flow, total flow, component mass fractions and pressure; only temperature and the declared enthalpy-flow accounting change. Cooling below the inlet temperature is rejected; zero temperature rise produces a calculated zero duty. There is no specified-duty temperature solve, inferred outlet temperature, pressure drop or sizing.

SEP_1 and SEP_2 both call the **same unchanged saved Bia evaluator**. SEP_1 retains temperature 313.15 K, pressure 2000000 Pa absolute and the original recoveries: methane 100% gas, n_hexane 100% oil, water 5% oil/95% water. SEP_2 explicitly specifies 333.15 K and 2000000 Pa absolute, with independent synthetic recoveries:

| Component |  gas |  oil | water |
| --------- | ---: | ---: | ----: |
| methane   |    1 |    0 |     0 |
| n_hexane  | 0.05 | 0.95 |     0 |
| water     |    0 | 0.10 |  0.90 |

Each component's recovery fractions must sum to one within the existing strict 1e-12 tolerance. **Heating OIL_1 does not cause or predict SEP_2 recoveries.** These are independently prescribed inputs, not temperature-derived equilibrium predictions. This limitation is also returned in results and displayed in the UI.

## Heater energy equation and benchmark correction

The unchanged declared basis is Tref = 273.15 K; Cp methane/n_hexane/water = 2200/2200/4180 J/(kg K). Mass flows are kg/h. Positive duty means **heat into the material stream/process/network**, matching the existing `heat_into_network` convention and the UI duty-column label.

```text
H(T) = Σ [m_i Cp_i (T − Tref)] / 3600 W
Qheater = Σ [m_i Cp_i (Tout − Tin)] / 3600 W
```

For Tin = 313.15 K and Tout = 333.15 K:

| Component | Exact expression (W)                    | Evaluated contribution (W) |
| --------- | --------------------------------------- | -------------------------: |
| n_hexane  | 77000 × 2200 × 20 / 3600                |             941111.111111… |
| water     | 550 × 4180 × 20 / 3600                  |              12772.222222… |
| methane   | 0 × 2200 × 20 / 3600                    |                          0 |
| Total     | (77000 × 2200 + 550 × 4180) × 20 / 3600 |         **953883.333333…** |

The requested narrative benchmark of 940555.555555… W for n_hexane and 953327.777777… W total contains an arithmetic error. The implementation follows the explicitly required calculation from the declared values, which remain unchanged: **953.883333… kW**. No benchmark value is hard-coded in the model.

OIL_1 enthalpy flow is 1907766.666666… W; HEATED_OIL enthalpy flow is 2861650 W. Their difference equals heater duty within 1e-6 W. SEP_1 duty is 0 W. The unchanged SEP_2 evaluator returns approximately −4.656612873077393e-10 W, numerically zero within the same tolerance; it is not forcibly replaced with zero. Network duty is approximately +953883.333333333 W and the reference external energy residual is 0 W.

This is **restricted constant-Cp sensible-heat accounting**, with no latent heat, EOS, phase-equilibrium enthalpy, pressure work or rigorous thermodynamic property model. It is not rigorous offshore-process or plant-energy validation.

## Calculated state propagation and scheduling

The generic graph executor stores calculated stream states by stable stream ID. It constructs each unit's inlet map from that unit's incoming connections and the existing state map. Thus SEP_2 receives the actual HEATER_1 output; it cannot independently specify/reconstruct a fixture inlet. Only source-connected streams may contain specified states.

The unchanged dependency traversal derives **SEP_1 → HEATER_1 → SEP_2** from connectivity. Reversed arrays and adversarial equipment names retain dependency-valid execution. No case-specific execution branch or hard-coded equipment sequence exists.

Port validation retains valid owner/port IDs, exact directions and required port sets, exactly one connection per stream, single-use ports, complete required connectivity, explicit branching/merging and component/caloric-basis consistency. Cycles continue to fail before execution. There are no tears or recycle iterations.

## Actual deterministic numbering and reference results

The unchanged graph traversal produces the following engineering numbers. They are stored on structured streams and are not assigned by React, service names, calculation order or layout.

| Number | Stable stream ID / service | Source → target                    | methane (kg/h) | n_hexane (kg/h) | water (kg/h) | Total (kg/h) |  T (K) |
| -----: | -------------------------- | ---------------------------------- | -------------: | --------------: | -----------: | -----------: | -----: |
|      1 | FEED / feed                | FEED.outlet → SEP_1.inlet          |          22000 |           77000 |        11000 |       110000 | 313.15 |
|      2 | GAS_1 / gas_1              | SEP_1.gas → GAS_1_SINK.inlet       |          22000 |               0 |            0 |        22000 | 313.15 |
|      3 | OIL_1 / oil_1              | SEP_1.oil → HEATER_1.inlet         |              0 |           77000 |          550 |        77550 | 313.15 |
|      4 | WATER_1 / water_1          | SEP_1.water → WATER_1_SINK.inlet   |              0 |               0 |        10450 |        10450 | 313.15 |
|      5 | HEATED_OIL / heated_oil    | HEATER_1.outlet → SEP_2.inlet      |              0 |           77000 |          550 |        77550 | 333.15 |
|      6 | GAS_2 / gas_2              | SEP_2.gas → GAS_2_SINK.inlet       |              0 |            3850 |            0 |         3850 | 333.15 |
|      7 | OIL_PRODUCT / oil_product  | SEP_2.oil → OIL_PRODUCT_SINK.inlet |              0 |           73150 |           55 |        73205 | 333.15 |
|      8 | WATER_2 / water_2          | SEP_2.water → WATER_2_SINK.inlet   |              0 |               0 |          495 |          495 | 333.15 |

All pressures are **2000000 Pa absolute**. Component mass fractions are each component flow divided by the stream total; heater inlet/outlet fractions are identical. Each material stream retains its stable ID, independent service name, engineering number and owner/port endpoints. Calculation enriches by ID without replacing structured stream identities. Existing case/revision/requirements/input fingerprint guards remain unchanged.

## Equipment and external balances

Each of the three equipment reports all three component residuals, total mass residual, duty, zero shaft work and restricted energy residual. Reference component and total residuals are zero. Component tolerance is 1e-8 kg/h; total tolerance is component count × 1e-8 kg/h (3e-8 here); energy tolerance is 1e-6 W. A deliberately incorrect heater duty fails the energy check and cannot publish results.

Only source and final sink-connected streams enter external balances; internal oil streams are not counted again:

```text
Total: 110000 − (22000 + 10450 + 3850 + 73205 + 495) = 0 kg/h
methane: 22000 − 22000 = 0 kg/h
n_hexane: 77000 − (3850 + 73150) = 0 kg/h
water: 11000 − (10450 + 55 + 495) = 0 kg/h
Energy: Hfeed + ΣQequipment − ΣHexternal_products = 0 W within 1e-6 W
```

## PFD, Stream Table and duty display

The existing structured-graph layout renders every node and material connection. The heater has a simple generic coil/zigzag representation distinct from the rounded separator and plain boundary nodes; no proprietary symbol or separate reference drawing was introduced. The PFD is read-only.

The existing generic Stream Table joins results to structured stream IDs. All eight numbered columns include service/ID, source/destination, P/T, total and component flows and component mass fractions. It displays the 313.15 K → 333.15 K transition and prescribed SEP_2 redistribution. PFD and table use the same labels/numbers across calculation, layout changes and regeneration. The equipment-check table exposes heater duty explicitly with the positive-into-process sign convention; the existing results contain stream enthalpy flows.

Molar flow, molecular mass, density, gas/oil/water volumetric flows and molar composition remain null with `not_calculated`, displayed **—**. Calculated zeros remain 0.

## Explicit contract extension and compatibility

Authoritative Zod contracts add **requirements 1.2, flowsheet 1.3, results 1.3**; generated JSON schemas retain the existing major-version directory and HTTP routes. The new branches add the heater equipment/model alternative and strict `outlet_temperature_K` plus `caloric_model` parameters. Results include heater type/model with the existing per-equipment duty/balance fields and engine version 1.2.0. No new stream identity/property fields were needed.

Milestone 4 remains requirements 1.1 / flowsheet and results 1.2, with engine version 1.1.0. Bia remains requirements 1.0 / numbered flowsheet and results 1.1. Old readers/branches remain unchanged and reject heater documents mislabeled as an older version. New builds select the output version from the submitted requirements contract; old documents are not silently relabelled. Implementation fingerprints naturally change with code/schema changes, requiring fresh builds for current calculations.

Natural-language interpretation/review remains on its qualified single-separator contract. No provider capability, anchoring or topology-normalization scope was expanded.

## Fixture and manual-test preparation

Independent fixture: `contracts/examples/milestone-5-requirements.json`. The original Bia and Milestone 4 fixtures are unchanged.

Start/restart the local Python engine with the updated code (`PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8001`), and run the website with `npm run dev`. The Python server does not hot-reload; an already-running pre-Milestone-5 process must be stopped/restarted before testing the new contract.

At `/digital-engineer` use **Engineering data / Advanced → Load Milestone 5 reference → Validate requirements → Generate PFD → Run engineering calculation**. No LLM call is required. Cross-case loading clears previous validation, flowsheet and results; validation alone produces neither PFD nor calculation results. Manual validation remains for the user to perform separately.

## Automated tests

Python coverage checks all reference component/total flows, composition/P/T, heater duty/enthalpy change, equipment/network balances, unavailable properties, invalid/missing/nonfinite temperature/Cp/caloric basis, component incompatibility, invalid ports/owners, independent-state injection, cooling rejection, recovery rejection and cycles. Zero ΔT yields a calculated zero. A spy on the real separator evaluator proves that changing heater outlet temperature and upstream component flow changes the actual SEP_2 inlet; its imposed operating temperature then produces the expected compensating separator duty. Reordering/renaming proves scheduling independence; repeated calculation/layout/regeneration preserve numbering.

TypeScript integration uses real Python-produced fixtures to check version boundaries, API forwarding, stable-object joins and cross-case invalidation. Browser coverage checks all nine nodes, eight labelled streams, distinct heater representation, every component flow/fraction, temperature change, unavailable properties, duty, limitations, regeneration/layout and Bia ↔ Milestone 5 ↔ Milestone 4 transitions. Existing Bia/Milestone 4 regressions remain part of the full suite.

## Deferred scope and future compatibility

No EOS (PR/SRK), PT/PH/PS flash, VLE/VLLE, phase envelopes, latent heat, rigorous enthalpy/density/viscosity, molecular-weight flow conversion, molar composition, pressure drop, sizing, area/UA, compressor, pump, valve, cooler, generic exchanger, recycle/tears/convergence, graphical editing, full Flowsheet 03 migration or broad natural-language network interpretation was added. No legacy thermodynamic code was copied.

A future qualified property/equipment adapter can enrich the same ID-keyed state map through the registry while retaining structured topology, ports, numbering, PFD and table joins. No future property provider is implemented here. Recommended next gate: separate user manual validation and engineering review of this sequential case, followed by an explicitly scoped model-qualification milestone; do not infer authorization for new thermodynamics or recycles from this demonstration.

## File inventory

Created: `MILESTONE_5.md`, `contracts/examples/milestone-5-requirements.json`, `engine/tests/test_sequential.py`, `tests/sequential-fixture.ts`, `tests/sequential.test.ts`, `tests/e2e/sequential.spec.ts`.

Modified: `docs/RIOGINEER_MASTER_CONTEXT.md` (sections 61–62 only), `src/lib/digital-engineer/contracts.ts`, generated `contracts/v1/{requirements,flowsheet,results,validation}.schema.json`, `engine/riogineer_engine/{core,network,network_models}.py`, `src/app/digital-engineer/{page,pfd,workspace}.tsx`, and `tests/engine-fixture.ts` (type narrowing for the unchanged Bia fixture).

The existing unrelated About-page edit is retained separately. No original Bia/Milestone 4 fixture, separator evaluator, numbering helper, interpretation/evidence code or workflow reducer was modified for this milestone.

## Completed automated validation

- TypeScript unit/integration: **189 tests passed in 15 files**.
- Python: **47 tests passed**, including nine sequential/heater tests and unchanged Bia/Milestone 4 regressions.
- Browser: **24 tests passed**, including both new sequential/case-transition tests. Generated PFD screenshot inspected; long stream labels were positioned clear of destination nodes.
- Contract parity, ESLint, TypeScript checking, repository/new-document formatting and diff whitespace: **passed**.
- Production build: **passed**, 41 static pages generated.
- Production smoke: **passed**, 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery.
- Protected original fixtures/evaluator, stream numbering and interpretation modules: no diff.
- Live-provider calls: **0**. Temporary browser/production servers stopped. User manual validation remains pending; restart any pre-existing local Python engine before testing the new contract versions.
