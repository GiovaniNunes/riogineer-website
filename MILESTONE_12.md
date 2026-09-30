# Milestone 12 — Production Heater/Cooler Energy-Balance Integration

Automated acceptance completed on 2026-09-29. Human-operated M12 validation was separately completed successfully on 2026-09-29, as reported by the human reviewer.

## Architecture and scope

The existing `heater` equipment type retains `specified_outlet_temperature_constant_cp@1.0`. That historical model permits heating to a specified temperature, keeps inlet pressure, uses supplied constant component Cp, and rejects cooling. Its equations, serialized examples and tests remain unchanged.

The separate `equilibrium_energy_balance_pr@1.0` model implements one-stream steady-state heating and cooling. `network_models.heater` dispatches by explicit model identity. The new adapter consumes the actual inlet mass-flow stream, invokes production `peng_robinson@1.0`, and returns the existing EquipmentResult with signed duty and a structured thermodynamic extension. No EOS, stability, caloric or PH equations are copied into equipment.

A narrowly scoped `heater_cooler_energy` process profile connects one source → one heater → one sink. It uses existing topology validation, stable stream IDs, deterministic numbering, fingerprinting and material balances. Its process serializer publishes the two actual streams and the equipment result. This is not a network energy solver; mixed caloric networks, recycle, downstream equipment PH integration and general thermal mixing are not qualified. The integration test obtains stream numbers 1 FEED and 2 PRODUCT through the unchanged numbering algorithm.

M8/M8.1/M8.2 own equilibrium and initialization recovery. M10 owns caloric properties. M11 owns PH inversion. M12 uses explicit high_accuracy for its inlet and Mode A PT/caloric calls; Mode B calls the normal M11 PH API, which selects its own qualified nested high_accuracy policy. Historical PT defaults and all thermodynamic settings/equations remain unchanged.

## Independent authority and numerical policy

Acceptance authority is the unchanged `independent_methane_nhexane_heater_cooler@1.0` reference in `benchmarks/heater_cooler_energy/methane_nhexane_heater_cooler_reference.json`, SHA-256 `55b01cbae648a64f20c5a6f331c6de1dd4b9ff2ff00a1497efe9ce4db99fd371`. All 14 positive and 15 negative cases are exercised. Production does not read that file; only the separate comparator does. The independent generator, solver, tests, report and dependency pins remain unchanged.

Provider provenance is `peng_robinson@1.0`, component dataset `riogineer_components@1.0`, molecular provider `molecular_composition@1.0`, caloric dataset `riogineer_caloric@1.0`, and reference `ideal_gas_sensible_298.15K_101325Pa@1.0`. The BIP is an explicitly supplied constant zero methane/n_hexane matrix with identifier, source and model, rather than a silent default. No formation terms or new production dependencies are introduced.

Field comparisons use the frozen independent allowances: T 1e-7 K absolute; final H residual 1e-6 J/mol absolute; beta/composition 1e-9 absolute + 1e-9 relative; Z 1e-10 absolute + 1e-9 relative; enthalpies 1e-7 J/mol absolute + 1e-11 relative. Phase classification must match exactly.

The independent reference defines direct enthalpy tolerances and arithmetic/closure budgets, not a separate fixed production Q tolerance. The comparator propagates the frozen inlet/outlet H allowances into delta_H and multiplies by F for Q, adding the frozen arithmetic budget. That protects against conflating production-versus-reference thermodynamic error with arithmetic energy closure. No frozen tolerance was changed.

## Balance and operating modes

M7 reconstructs component molar flows and z from `component_mass_flow_kg_h`. Its total kmol/h is explicitly multiplied by 1000 and divided by 3600 to obtain F in mol/s. No new molecular-weight implementation or independently editable z is added. Focused tests verify 100 mol/s = 360 kmol/h and exact scaling to 200 mol/s.

With H in J/mol, Q in W, P in Pa absolute and T in K:

```text
Mode A: inlet PT/caloric; outlet PT/caloric at specified T_out/P_out
        Q = F*(H_out - H_in)
Mode B: inlet PT/caloric; H_target = H_in + Q/F
        existing production flash_PH(P_out, H_target, z) -> accepted outlet
R_Q = Q - F*(H_out - H_in)
```

Positive Q adds heat; negative Q removes heat. Shaft work is zero in this equipment balance and kinetic/potential energy changes are neglected. Exactly one controlling thermal specification is required. Zero Q is valid and distinct from missing Q. P_out is specified, including a 6 MPa → 3 MPa case; no hydraulic pressure drop is calculated.

The inlet enthalpy is always recalculated by the provider. An arbitrary supplied inlet enthalpy is not trusted. Two-phase enthalpy is the M10 equilibrium aggregate. The final outlet comes from actual accepted PT or PH, with its phase classification, molar beta, phase compositions, roots and phase enthalpies. No phase rule or latent-heat interpolation is added in equipment.

Outlet component mass flows are copied exactly. Consequently overall composition, component inventory and total molar flow are conserved; the comparator also reconstructs outlet molar flow independently through M7. Phase split may change without separating material.

Arithmetic closure uses the frozen 64-epsilon enthalpy-flow budget. Mode B adds F times the unchanged 1e-6 J/mol PH residual allowance. Failure at inlet PT/caloric, outlet PT/caloric or PH raises a stage/status diagnostic without an accepted outlet. The process API identifies HEATER_1 and propagates failure instead of publishing partial results. PH diagnostic details survive in the exception; successful results expose a concise nested PH summary rather than flattening the scan into process fields.

## Versioned contracts and compatibility

| Contract     | Previous latest | New version | Reason                                                                          |
| ------------ | --------------- | ----------- | ------------------------------------------------------------------------------- |
| Requirements | 1.4             | 1.5         | Explicit rigorous heater model, exclusive T/Q, specified P_out and provider/BIP |
| Flowsheet    | 1.5             | 1.6         | Registered rigorous operating parameters on the existing heater type            |
| Results      | 1.6             | 1.7         | Structured inlet/outlet caloric equilibrium, duty, closure and PH provenance    |

Old readers and every historical branch remain available. No automatic migration or reinterpretation occurs; callers must explicitly select the new model/profile/version. The validation-response JSON schema changes only because it embeds the expanded requirements union; its envelope is unchanged. The error contract is unchanged. M9's result extension is byte-for-byte structurally preserved.

The result extension reports mode, provider/component/molecular/caloric identities, caloric reference, BIP, F, inlet/outlet states, delta_H, signed Q, R_Q, allowance, optional H_target and nested PH capability/status/profile/iteration/residual summary. T/P, beta, compositions, Z and enthalpy have one canonical state representation inside that extension.

Existing mass-flow stream fields and the Stream Table are not redesigned. The M12 serializer leaves optional Stream Table property rows unavailable; calculated equilibrium/caloric information is in the equipment extension, and enthalpy flow uses the existing stream field. Historical streams still follow their unchanged M7 enrichment path. The only workspace adjustment guards the historical reference-temperature field and labels the new energy model correctly; it does not add UI controls or a visual redesign.

Eight new TypeScript contract tests qualify historical inputs/results, both new modes and zero Q, both/neither rejection, invalid pressure/provenance, rigorous result serialization/version discrimination, requirements/flowsheet round trips and unchanged M9 results.

## Positive matrix

All cases pass Mode A and Mode B, including explicit comparisons between their recovered phase states. Values below are production Mode A duties; complete values, references, errors, allowances and both results are in `production_comparison.json`.

| Case                      | F mol/s | Inlet → outlet phase          |        Mode A Q W | Mode B recovered T K |   Mode B R_Q W |
| ------------------------- | ------: | ----------------------------- | ----------------: | -------------------: | -------------: |
| VAPOR_HEATING             |     100 | single_vapor → single_vapor   |  474661.342178687 |                  350 |  -2.910383e-10 |
| VAPOR_COOLING             |     100 | single_vapor → single_vapor   | -474661.342178687 |                  300 |  1.2805685e-09 |
| LIQUID_HEATING            |     100 | single_liquid → single_liquid |  864298.802261745 |                  350 |  2.3283064e-10 |
| LIQUID_COOLING            |     100 | single_liquid → single_liquid | -864298.802261745 |                  280 |  3.4924597e-09 |
| LIQUID_TO_TWO_PHASE       |     100 | single_liquid → vapor_liquid  |  1027573.33513019 |      299.99999999999 |  2.0954758e-09 |
| TWO_PHASE_TO_VAPOR        |     100 | vapor_liquid → single_vapor   |  3149688.25032847 |     480.000000000007 |  -3.259629e-09 |
| VAPOR_TO_TWO_PHASE        |     100 | single_vapor → vapor_liquid   | -3149688.25032847 |      299.99999999999 |  2.3283064e-09 |
| TWO_PHASE_TO_LIQUID       |     100 | vapor_liquid → single_liquid  | -1027573.33513019 |      220.00000000001 |  9.3132257e-10 |
| TWO_PHASE_TO_TWO_PHASE    |     100 | vapor_liquid → vapor_liquid   |  670599.903638732 |     350.000000000006 |  1.9790605e-09 |
| SPECIFIED_OUTLET_PRESSURE |     100 | vapor_liquid → vapor_liquid   |  730502.909453498 |      350.00000000001 | -2.3283064e-09 |
| VAPOR_HEATING_DOUBLE_FLOW |     200 | single_vapor → single_vapor   |  949322.684357374 |                  350 | -5.8207661e-10 |
| ZERO_DUTY                 |     100 | vapor_liquid → vapor_liquid   |                 0 |                  300 |  1.6370905e-09 |
| BUBBLE_ADJACENT_HEATING   |     100 | single_liquid → vapor_liquid  |  13222.9301508713 |     231.617554351397 | -1.4551915e-09 |
| DEW_ADJACENT_COOLING      |     100 | single_vapor → vapor_liquid   |  -22644.693356632 |     467.765889531704 |   2.910383e-09 |

All four cross-phase directions pass. The VL → VL and boundary-adjacent cases also pass. The zero-duty case recovers the inlet state through PH; equal endpoint Mode A duty is exactly zero. Doubling F gives exactly double duty with identical inlet/outlet thermodynamics and delta_H; observed scaling error is 0 W. The specified-pressure case uses the actual P_out in both modes.

## Maximum errors

These are maximum absolute production-versus-frozen errors over both modes and applicable phases, except energy closure which is measured against zero. No absent phase is assigned a fabricated property.

| Quantity         | Maximum absolute error | Governing case / field                                     | Applicable allowance |
| ---------------- | ---------------------: | ---------------------------------------------------------- | -------------------: |
| T_out K          |   7.09974301571492e-11 | DEW_ADJACENT_COOLING / B.outlet.T                          |                1e-07 |
| H_in J/mol       |   1.05683284346014e-09 | TWO_PHASE_TO_VAPOR / A.inlet.H                             | 2.63339553084298e-07 |
| H_out J/mol      |   2.08019628189504e-08 | DEW_ADJACENT_COOLING / A.outlet.H                          | 2.31765020618457e-07 |
| delta_H J/mol    |   2.08056007977575e-08 | DEW_ADJACENT_COOLING / A.delta_H                           | 4.65794510572368e-07 |
| Q W              |   2.08056007977575e-06 | DEW_ADJACENT_COOLING / A.Q                                 | 4.65984977933297e-05 |
| energy closure W |   3.49245965480804e-09 | LIQUID_COOLING / B.energy_closure                          | 0.000100026518603532 |
| beta             |    3.9735992274359e-12 | DEW_ADJACENT_COOLING / A.outlet.beta                       | 1.98687445419579e-09 |
| x                |   3.58046925441613e-13 | LIQUID_TO_TWO_PHASE / A.outlet.liquid.composition.n_hexane | 1.70762307160002e-09 |
| y                |   1.16751053269581e-12 | DEW_ADJACENT_COOLING / A.outlet.vapor.composition.methane  | 1.50380543748975e-09 |
| Z_L              |   1.59094959428785e-13 | DEW_ADJACENT_COOLING / B.outlet.liquid.Z                   | 4.13920884542664e-10 |
| Z_V              |   1.31838984174237e-12 | DEW_ADJACENT_COOLING / A.outlet.vapor.Z                    | 7.96573782934688e-10 |
| h_L J/mol        |   1.97560439119115e-08 | DEW_ADJACENT_COOLING / B.outlet.liquid.h_J_mol             | 1.92688736956159e-07 |
| h_V J/mol        |   8.35825630929321e-09 | DEW_ADJACENT_COOLING / B.outlet.vapor.h_J_mol              | 2.32284739767014e-07 |

Mode-equivalence maxima (Mode A versus Mode B):

| Field                                        | Maximum absolute difference | Governing case          |
| -------------------------------------------- | --------------------------: | ----------------------- |
| mode_equivalence.H_eq_J_mol                  |        2.07764969673008e-08 | DEW_ADJACENT_COOLING    |
| mode_equivalence.beta                        |        1.81898940354586e-12 | DEW_ADJACENT_COOLING    |
| mode_equivalence.liquid.Z                    |         1.6286971771251e-13 | DEW_ADJACENT_COOLING    |
| mode_equivalence.liquid.composition.methane  |        4.31321645066873e-14 | BUBBLE_ADJACENT_HEATING |
| mode_equivalence.liquid.composition.n_hexane |        4.30766533554561e-14 | BUBBLE_ADJACENT_HEATING |
| mode_equivalence.liquid.h_J_mol              |        1.98670022655278e-08 | DEW_ADJACENT_COOLING    |
| mode_equivalence.temperature_K               |        7.09974301571492e-11 | DEW_ADJACENT_COOLING    |
| mode_equivalence.vapor.Z                     |        3.95794508278868e-13 | DEW_ADJACENT_COOLING    |
| mode_equivalence.vapor.composition.methane   |        5.34683408659475e-13 | DEW_ADJACENT_COOLING    |
| mode_equivalence.vapor.composition.n_hexane  |        5.34738919810707e-13 | DEW_ADJACENT_COOLING    |
| mode_equivalence.vapor.h_J_mol               |        1.34914444060996e-08 | DEW_ADJACENT_COOLING    |

## Controlled negatives and failure semantics

| Frozen negative         | Observed production status    | Accepted outlet |
| ----------------------- | ----------------------------- | --------------- |
| ZERO_FLOW               | invalid_flow                  | No              |
| NEGATIVE_FLOW           | invalid_flow                  | No              |
| NAN_FLOW                | invalid_flow                  | No              |
| INFINITE_FLOW           | invalid_flow                  | No              |
| INVALID_INLET_PRESSURE  | invalid_pressure              | No              |
| INVALID_OUTLET_PRESSURE | invalid_pressure              | No              |
| INVALID_COMPOSITION     | invalid_composition           | No              |
| UNSUPPORTED_WATER       | unsupported_component         | No              |
| INLET_CP_EXTRAPOLATION  | temperature_domain_invalid    | No              |
| UNBRACKETED_HIGH_TARGET | enthalpy_target_not_bracketed | No              |
| UNBRACKETED_LOW_TARGET  | enthalpy_target_not_bracketed | No              |
| NAN_DUTY                | invalid_duty                  | No              |
| INFINITE_DUTY           | invalid_duty                  | No              |
| OUTLET_CP_EXTRAPOLATION | temperature_domain_invalid    | No              |
| PURE_COEXISTENCE_GAP    | ph_nonconvergence             | No              |

The process API has no editable molar z input. The independent malformed-z negative is therefore represented as inconsistent component/total mass inventory and rejected by M7, preserving the invalid-composition meaning. Unsupported water is rejected before BIP or thermodynamic execution. Pure n-hexane coexistence-gap failure is inherited from M11 without interpolation. Additional production tests reject ambiguous/missing specifications and inject inlet/outlet caloric and PH failures.

## Determinism and automated acceptance

Representative results in both modes are exactly identical after heating, cooling, a two-phase case, the opposite mode and a failed call. Repeated process calculations preserve the structured flowsheet, IDs, numbering, equipment results and input fingerprint; the standard run ID remains per-run metadata. A fresh interpreter reproduced the complete production comparison artifact byte-for-byte.

| Gate                                                    | Actual result                                                                                           |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| M12 production comparison                               | 14 positive, 15 negative; 1264 comparisons passed                                                       |
| New M12 Python tests                                    | 36 passed                                                                                               |
| New M12 contract tests                                  | 8 passed                                                                                                |
| Independent Pre-M12                                     | 36 passed; frozen JSON reproduced byte-for-byte                                                         |
| Pre-M8 / M8 comparison                                  | 7 tests / 122 comparisons passed                                                                        |
| Pre-M8.1 / M8.1 comparison                              | 28 tests / 325 comparisons passed                                                                       |
| Pre-M8.2 / M8.2 comparison                              | 25 tests / 749 comparisons passed                                                                       |
| M8.2 full scan                                          | 9 grids; 1152/1152 successes; zero unexpected failures; four vapor-parent and one liquid-parent restart |
| M9 integration                                          | 7 tests passed in the full Python suite                                                                 |
| Pre-M10 / M10 comparison                                | 23 tests / 1526 comparisons passed                                                                      |
| Pre-M11 / M11 comparison                                | 55 tests; 29 positive + nine negative/gap; 401 field comparisons passed                                 |
| M11 focused production tests                            | All 53 passed in the full Python suite                                                                  |
| Complete Python                                         | 284 passed, including historical equipment/flowsheet tests                                              |
| Complete TypeScript                                     | 208 passed, 19 files                                                                                    |
| Complete browser                                        | 31 passed                                                                                               |
| Contract parity / ESLint / TypeScript checking          | Passed                                                                                                  |
| Formatting / Python syntax and indentation / whitespace | Passed                                                                                                  |
| Production build                                        | Passed                                                                                                  |
| Production smoke                                        | 17 pages, 17 PNG cards, links, 404s, preview indexing and disabled contact delivery passed              |
| Historical protected evidence                           | Unchanged against pre-edit SHA-256 snapshot                                                             |

The full suites used `PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_*.py' -v`, `npm test`, `npm run test:e2e`, `npm run contracts:check`, `npm run lint`, `npm run typecheck`, and `npm run format:check`. Build used `SITE_URL=http://127.0.0.1:3210 npm run build`; smoke used the built server on port 3210 and `SMOKE_URL=http://127.0.0.1:3210 npm run smoke`. Local-server permissions were provided without changing product behavior. No live LLM/provider call was made. All historical independent/comparator commands match the unchanged Pre-M12 report, with no reference-writing flags.

## Integrity and files

The initial tree was clean on main at `4dda4f51f800d7013c1a74f0d47276c59e49b9fe`, matching remote origin/main. A pre-edit SHA-256 snapshot covered every tracked file. All benchmark/reference stacks, fixtures, prior thermodynamic equations/data/providers, M9 adapter and historical tests remain unchanged. Generated Next.js environment paths were restored by the production build; no incidental generated file remains in the final diff.

New files:

- `engine/riogineer_engine/heater_cooler_energy.py`: equipment adapter and controlled failure semantics.
- `engine/riogineer_engine/thermal_process.py`: single-equipment process result serialization.
- `engine/tests/test_heater_cooler_energy.py`: frozen matrix and integration/failure/conversion tests.
- `tests/heater-energy-contracts.test.ts`: versioning and serialization tests.
- `benchmarks/heater_cooler_energy/compare_production.py`: production-only comparator and human-review CLI.
- `benchmarks/heater_cooler_energy/production_comparison.json`: deterministic production evidence, separate from the independent reference.
- `MILESTONE_12.md`: this acceptance record.

Modified files:

- `engine/riogineer_engine/network_models.py`: explicit rigorous-model dispatch while preserving the historical heater.
- `engine/riogineer_engine/network.py`: new profile validation/build mapping and scoped execution dispatch.
- `engine/riogineer_engine/core.py`: new version routing and retention of the dedicated public result.
- `src/lib/digital-engineer/contracts.ts`: additive versioned input/flowsheet/result branches.
- `contracts/v1/requirements.schema.json`, `contracts/v1/flowsheet.schema.json`, `contracts/v1/results.schema.json`, `contracts/v1/validation.schema.json`: generated parity with those definitions.
- `src/app/digital-engineer/workspace.tsx`: minimal energy-model display compatibility guard.
- `docs/RIOGINEER_MASTER_CONTEXT.md`: minimal qualified-scope status update.

No staging, commit or push was performed. Final changes are intentional M12 files only.

## Human-operated validation — 2026-09-29

This record documents the human review reported by the user, separately from the automated acceptance above. The reviewer executed the documented production comparator from the repository root. It does not extend the existing M12 qualification scope.

| Reviewed command selector | Human-confirmed result                                                                                                                                                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--case mode_a`           | Specified outlet temperature produced the expected liquid → vapor-liquid heating state, enthalpy and duty through PT/M10.                                                                                                                  |
| `--case mode_b`           | Specified duty called M11 `flash_PH` with `pt_profile = high_accuracy`, recovering approximately 300 K and vapor_liquid. Temperature, enthalpy, duty and energy closure passed.                                                            |
| `--case zero`             | Both modes passed. Zero duty was a valid specification; H_out and T_out reproduced the inlet within tolerance, with consistent phase and successful Mode B PH. Mode A closure was zero; Mode B closure stayed within the frozen allowance. |
| `--case scaling`          | Increasing F from 100 to 200 mol/s preserved inlet/outlet enthalpies, delta_H, outlet temperature and equilibrium phase while doubling Q. Both modes passed; scaling error was 0.0 W.                                                      |
| `--case transitions`      | Both modes passed all four qualified phase-transition directions. Heating duties were positive and cooling duties negative; Mode B explicitly used successful M11 PH with high_accuracy PT.                                                |
| `--case negative`         | All 15 frozen negative cases produced the expected controlled failures and no accepted outlet.                                                                                                                                             |
| `--case summary`          | The reviewer inspected the beginning and end of the output, including ordinary heating/cooling and dew-adjacent cooling. The final summary reported 14 positive cases, 15 negative cases and 1264 comparisons passing.                     |

The representative Mode A case had F = 100 mol/s, inlet 220 K and 6 MPa absolute, and outlet 300 K and 6 MPa absolute. The human review confirmed H_in approximately -26609.68866 J/mol, H_out approximately -16333.95531 J/mol, delta_H approximately +10275.73335 J/mol and Q approximately +1.027573 MW, with R_Q = 0 W. Outlet temperature, enthalpy and duty comparisons passed. These are reported review observations; the frozen numerical evidence above remains unchanged.

The corresponding Mode B review confirmed the chain `specified Q → H_out,target → M11 PH → T_out / equilibrium state`. The output identified `capability = flash_PH` and `pt_profile = high_accuracy`. The review confirmed reuse of the qualified PH capability and property-package phase determination, without a second equipment PH solver or equipment-specific phase rules.

The transitions reviewed were `single_liquid → vapor_liquid`, `vapor_liquid → single_vapor`, `single_vapor → vapor_liquid` and `vapor_liquid → single_liquid`.

The negative review covered zero, negative, NaN and infinite flow; invalid inlet/outlet pressure; invalid composition; unsupported water; inlet/outlet caloric extrapolation; high/low unbracketed enthalpy targets; NaN/infinite duty; and the pure-component coexistence gap. No rejected specification published a successful-looking outlet.

The complete summary reported `PASS: 14 positive; 15 negative; 1264 comparisons`, `Scaling error W: 0.0`, and successful both-mode determinism and call-order checks. The dew-adjacent Mode B output explicitly showed successful high_accuracy M11 PH within the frozen temperature, enthalpy and duty allowances.

**M12 automated acceptance: COMPLETE.**

**M12 human-operated validation: COMPLETE — 2026-09-29.**

The historical constant-Cp Heater remains distinct from `equilibrium_energy_balance_pr@1.0`. All qualification limits below remain in force; this review authorizes no additional thermodynamic domain or subsequent milestone.

## Human-operated validation commands

From the repository root, each selector evaluates the entire matrix and limits displayed detail:

```sh
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case representative
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case mode_a
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case mode_b
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case zero
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case scaling
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case pressure
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case transitions
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case negative
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py --case summary
```

The transitions selector includes all four required directions. Output identifies the controlling mode, F, inlet/outlet T/P and phase, H_in, H_out, delta_H, signed Q, closure/allowance and production-versus-frozen values. Mode B explicitly shows the M11 `flash_PH` capability, target H and accepted residual without dumping the scan. These commands do not write evidence. The optional `--write` flag writes only the separate production artifact and is unnecessary for manual review.

Independent reproduction remains:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/heater_cooler_energy/reference.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/heater_cooler_energy -p 'test_*.py' -v
```

## Qualification limits

Only the frozen methane/n_hexane explicit-zero-kij scope is qualified, with temperatures restricted to 200–500 K. No arbitrary mixtures, water, nonzero BIP, VLLE, three-phase, critical/retrograde behavior or pure coexistence interpolation is qualified. No exchanger area, U, LMTD/NTU, geometry, utilities, hydraulic pressure-drop correlation, mechanical sizing or dynamics is implemented. No PS, compressor, valve, two-stream exchanger, network energy solver or broad Stream Table caloric enrichment was started. Human review remains separate from automated qualification.

**Milestone 12 automated acceptance is complete. Human-operated validation completed successfully on 2026-09-29.**
