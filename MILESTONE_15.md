# Milestone 15 — Production rigorous two-stream Peng–Robinson heat exchanger

Milestone 15 automated acceptance: **COMPLETE — 2026-09-30**.

Human-operated M15 validation: **COMPLETE — 2026-09-30**.

## Human-operated validation record

The human reviewer reported successful execution and inspection on 2026-09-30 of `canonical`, `reciprocal`, `phase`, `zero_duty`, `temperature_scope`, `negative` and `summary --verify`. All reviewed modes passed. This human record is separate from the automated acceptance evidence below; numerical acceptance was not rerun for this documentation update.

The canonical `rigorous_two_stream_pr@1.0` calculation recovered hot 430 → 390 K and cold 300 → 323.404886727 K, with Q_hot = −223084.033026 W, Q_cold = +223084.033026 W and Q_exchanged = 223084.033026 W. The reviewed energy residual was approximately −1.86e−9 W and PH residual approximately −9.32e−12 J/mol, with one PH candidate and `high_accuracy` PT. The result passed against the frozen independent Pre-M15 evidence.

Reciprocal review confirmed Mode A/Mode B recovery within frozen allowances across all 19 primary cases, including independent hot/cold pressure drops, flow ratios, compositions, pure methane/n-hexane, `LIQUID_BOTH`, zero duty, explicit cold-specified operation and near-terminal equality. `DOUBLE_BOTH_FLOWS` preserved specific states while approximately doubling all three duties; the summary reported zero duty-scaling errors. `DOUBLE_HOT_FLOW` changed the recovered cold outlet as expected. These behaviors were inspected through reciprocal review, without claiming separate human execution of the flow, pressure, composition or pure CLI modes.

All six phase studies (`COLD_L_TO_VL`, `HOT_V_TO_VL`, `COLD_VL_TO_V`, `HOT_VL_TO_L`, `BUBBLE_ADJACENT`, `DEW_ADJACENT`) remained independently calculable and rejected as production service. `ZERO_DUTY` preserved temperatures at unchanged pressures with essentially zero duty. `ZERO_DUTY_COLD_DROP` recovered approximately 300 → 299.644960108 K on the cold side at essentially zero duty, confirming PH recovery when pressure changes.

`CANONICAL` and `NEAR_TERMINAL_EQUALITY` were accepted, the latter at approximately 390 K hot outlet and 389.75 K cold outlet without an arbitrary minimum approach. `REVERSED_DUTY` rejected with `heat_direction`; `TERMINAL_CROSSING` rejected with `terminal_temperature_crossing`. Terminal thermodynamic balance does not establish exchanger design feasibility or qualify UA, LMTD, NTU, pinch, minimum-approach design or sizing.

All 79 negative cases rejected without publishing an accepted exchanger result. Review covered invalid hot/cold flows, pressures and pressure gain, temperature/composition/component/BIP failures, invalid or missing/excess specifications, inlet-role and duty contradictions, crossing, unbracketed hot/cold recovery, controlled inlet/specified-outlet PT and recovered-outlet PH failures, ambiguity, property holes, fresh-final acceptance failure and pure-component coexistence gaps.

The human-reviewed `summary --verify` reported **PASS: 19 primary positive; 79 negative; 6 excluded phase studies; 1,165 numerical comparisons; 12 byte-identical call-order checks**. All numerical and reciprocal errors remained within frozen allowances. Reported maxima included cold-outlet temperature error 2.84217094e−13 K, PH residual 1.18234311e−11 J/mol (allowance 1e−6 J/mol), Q_cold and Q_exchanged errors 5.12227416e−9 W, and energy residual 3.7252903e−9 W. Both mass residuals and all three duty-scaling errors were zero. Existing numerical tables, tolerances, frozen evidence and the qualified scope below remain unchanged. No M16 work was performed.

## Baseline and authorization

Started on clean `main` at `e260836ec95ae63e33290a862adee6f818f9e98b`, equal to local `origin/main`; M14 and human-reviewed Pre-M15 were committed. All 320 tracked baseline files were inventoried by SHA-256 before implementation. No staging, commit or push was performed.

The original four-port contract/topology gate correctly stopped implementation. Separate explicit authorization permitted requirements 1.7, flowsheet 1.8 and results 1.9, modifying only the eight named existing contract/dispatch files during that gate. Runtime gate checks passed before thermodynamic implementation: 44 TypeScript contract/network tests, five new topology tests, 18 historical network tests, 36 M12 tests and 75 M14 tests, with schema parity and preservation of every historical JSON-schema branch.

The expanded results union subsequently exposed two historical fixture typing issues. Separate exact-file authorizations permitted discriminant guards in `tests/compression-fixture.ts` (schema 1.5 / process-result 1.4) and `tests/sequential-fixture.ts` (schema 1.5 / process-result 1.3). They preserve the existing schemas, engine payloads and assertions. Executing the old and new fixture modules against the same engine payload produced byte-identical JSON exports for each fixture. No `any`, `unknown`, optional-field workaround or fake M15 `balances.mass` was introduced. Complete type checking now passes.

## Versioned contracts and architecture

The additive model is `rigorous_two_stream_pr@1.0`, equipment type `two_stream_heat_exchanger`, profile `two_stream_heat_exchanger_energy`. Four named ports survive requirements connections, flowsheet, registry, execution, result associations and PFD: `hot_in`, `hot_out`, `cold_in`, `cold_out`. Material propagates hot-to-hot and cold-to-cold; only energy couples the paths.

Mode A is `specified_hot_outlet_temperature`, with `hot_outlet_temperature_K`. Mode B is `specified_cold_outlet_temperature`, with `cold_outlet_temperature_K`. Strict discriminated branches require exactly one selected outlet temperature. Both modes require separate `hot_outlet_pressure_Pa_abs` and `cold_outlet_pressure_Pa_abs`, `peng_robinson@1.0` and explicit constant-zero binary interaction provenance. Inlets own component mass rates, inlet temperature and inlet pressure; M7 is authoritative for molar conversion.

The existing topological validator waits for all incoming streams, validates all four ports/connections and rejects cycles. An additive executor uses a fresh local state store for each calculation, calls each ready exchanger once, checks separate material balances, and publishes both outlets together only after success. Tests prove downstream propagation through two exchangers, distinct compositions, missing-input rejection, swapped-output rejection and partial-output rejection. Historical constant-Cp networks and one-stream M12/M14 adapters retain their original paths. The new profile supports acyclic exchanger chains; it does not introduce mixed-model network energy solving or recycle convergence.

Successful results contain four structured H/S states, both molar flows, signed duties, positive exchanged duty, energy residual/allowance, recovered enthalpy target, compact PH diagnostics, four authoritative stream associations and separate `material_balances.hot` / `.cold`. Process `balances.material_paths` retains those unit/path checks without a mixed-stream material balance. Environment duty and shaft work are zero. Failures use the unchanged error envelope and publish no accepted outlet pair.

## Thermodynamic sequence and acceptance

`two_stream_heat_exchanger_energy.py` composes existing production provider capabilities. It neither imports the independent benchmark nor duplicates PR equations. M14's existing caloric-state/compact inverse serialization helpers are reused without invoking compressor calculations or PS.

1. Validate both independent material streams, selected mode, provider, explicit zero BIP, finite positive flow, `0 < Pout <= Pin`, composition consistency and the 200–500 K domain.
2. Evaluate both inlets with M10 equilibrium caloric PT using `high_accuracy`.
3. Evaluate the specified outlet with the same production PT/caloric path.
4. Calculate `Q_specified = F_specified * (Hout - Hin)` and the opposite-side target `H_in - Q_specified/F_recovered`.
5. Recover the other outlet with unchanged M11 `flash_PH`: complete 128-point bounded scan, qualified candidate selection, bisection and fresh final PT/caloric evaluation.
6. Require one candidate, `high_accuracy`, final diagnostic provenance and fresh enthalpy residual no greater than 1e-6 J/mol. Validate finite H/S, domain, composition and specified pressure.
7. Independently calculate both duties from the accepted states and check their sum against recovered-flow times the unchanged PH residual budget plus arithmetic roundoff. Check hot-to-cold duty direction, primary phase scope and `Thi > Tco`, `Tho > Tci`, `Tho >= Tco`.
8. Preserve each side's exact component mass rates and M7 composition/molar-flow projection; return both outlets only after all checks pass.

`Q_hot` is heat into the hot material path (normally negative); `Q_cold` is heat into the cold path (normally positive). `Q_exchanged = max(0, Q_cold)` provides the positive transfer convention while both signed duties remain visible. Zero-duty roundoff remains subject to energy allowance. The energy residual is calculated from actual fresh states, not forced to zero by assignment.

## Qualified scope and limitations

All 19 frozen primary cases are accepted, including the explicitly primary `LIQUID_BOTH` case and pure methane/n-hexane endpoints. Six phase-change studies remain independently calculable thermodynamic evidence but are rejected as production service. The model remains restricted to methane/n_hexane, explicit constant zero kij, the frozen pressure/composition matrix and bounded 200–500 K states. Finite scanning demonstrates qualified candidates, not mathematical global uniqueness.

No water, arbitrary petroleum mixture/nonzero BIP, VLLE/three-phase behavior, critical-region generalization or pure coexistence-gap interpolation is qualified. No UA, U, area, LMTD, NTU/effectiveness, minimum-approach design criterion, distributed temperature profile, geometry, fouling, hydraulic pressure-drop correlation, heat loss, shaft/electrical work, equipment sizing, design feasibility, dynamics, controls or optimization is implemented. Outlet pressures are specifications. No M16 or later equipment was started.

## Canonical production result

| Quantity                    | Hot                               | Cold                              |
| --------------------------- | --------------------------------- | --------------------------------- |
| Flow, mol/s                 | 100                               | 200                               |
| Composition, mole fractions | {'methane': 0.9, 'n_hexane': 0.1} | {'methane': 0.9, 'n_hexane': 0.1} |
| Inlet P, Pa absolute        | 300000                            | 100000                            |
| Outlet P, Pa absolute       | 300000                            | 100000                            |
| Inlet T, K                  | 430                               | 300                               |
| Outlet T, K                 | 390                               | 323.404886727                     |
| Inlet H, J/mol              | 6762.80787871                     | 53.0231224156                     |
| Outlet H, J/mol             | 4531.96754845                     | 1168.44328754                     |
| Inlet phase                 | single_vapor                      | single_vapor                      |
| Outlet phase                | single_vapor                      | single_vapor                      |

| Quantity                               | Production         |
| -------------------------------------- | ------------------ |
| Q_hot_W                                | -223084.033026     |
| Q_cold_W                               | 223084.033026      |
| Q_exchanged_W                          | 223084.033026      |
| energy_residual_W                      | -1.86264514923e-09 |
| recovered_outlet_target_enthalpy_J_mol | 1168.44328754      |
| Recovered PH residual, J/mol           | -9.32232069317e-12 |

## Reciprocal and flow evidence

Every primary case traverses the public production requirements → flowsheet → registry → serialized result path in its original and reciprocal mode. The reciprocal calculation specifies the production-recovered temperature; it does not substitute a frozen answer. Allowances are the frozen sums recorded for each reciprocal quantity.

| Case                   | Maximum reciprocal ΔT, K | Maximum reciprocal ΔH, J/mol | Maximum reciprocal ΔQ, W |
| ---------------------- | ------------------------ | ---------------------------- | ------------------------ |
| CANONICAL              | 2.27373675443e-13        | 1.27329258248e-11            | 1.2805685401e-09         |
| HOT_PRESSURE_DROP      | 2.27373675443e-13        | 1.27329258248e-11            | 1.2805685401e-09         |
| COLD_PRESSURE_DROP     | 2.27373675443e-13        | 1.27329258248e-11            | 1.2805685401e-09         |
| BOTH_PRESSURE_DROP     | 2.27373675443e-13        | 1.27329258248e-11            | 1.2805685401e-09         |
| FLOW_RATIO_1           | 3.41060513165e-13        | 1.81898940355e-11            | 1.80443748832e-09        |
| FLOW_RATIO_2           | 2.27373675443e-13        | 1.27329258248e-11            | 1.2805685401e-09         |
| DOUBLE_BOTH_FLOWS      | 2.27373675443e-13        | 1.27329258248e-11            | 2.56113708019e-09        |
| DOUBLE_HOT_FLOW        | 3.41060513165e-13        | 1.81898940355e-11            | 3.60887497663e-09        |
| COLD_BALANCED          | 1.70530256582e-13        | 1.00044417195e-11            | 1.00408215076e-09        |
| COLD_HEXANE_RICH       | 1.70530256582e-13        | 1.00044417195e-11            | 1.00408215076e-09        |
| HOT_BALANCED           | 3.41060513165e-13        | 3.63797880709e-11            | 3.66708263755e-09        |
| HOT_HEXANE_RICH        | 3.41060513165e-13        | 4.54747350886e-11            | 4.54019755125e-09        |
| PURE_METHANE           | 3.41060513165e-13        | 1.36424205266e-11            | 1.36788003147e-09        |
| PURE_HEXANE            | 2.27373675443e-13        | 4.18367562816e-11            | 4.19095158577e-09        |
| LIQUID_BOTH            | 5.68434188608e-14        | 3.63797880709e-12            | 3.49245965481e-10        |
| ZERO_DUTY              | 2.27373675443e-13        | 1.1823431123e-11             | 1.1823431123e-09         |
| ZERO_DUTY_COLD_DROP    | 2.27373675443e-13        | 1.1823431123e-11             | 1.1823431123e-09         |
| COLD_SPECIFIED         | 5.68434188608e-14        | 2.72848410532e-12            | 5.23868948221e-10        |
| NEAR_TERMINAL_EQUALITY | 3.41060513165e-13        | 1.81898940355e-11            | 1.80443748832e-09        |

| Case              | Hot mol/s | Cold mol/s | Exchanged W   | Hot Tout K | Cold Tout K   | Energy residual W  |
| ----------------- | --------- | ---------- | ------------- | ---------- | ------------- | ------------------ |
| CANONICAL         | 100       | 200        | 223084.033026 | 390        | 323.404886727 | -1.86264514923e-09 |
| FLOW_RATIO_1      | 100       | 100        | 223084.033026 | 390        | 345.986654444 | 1.04773789644e-09  |
| FLOW_RATIO_2      | 100       | 50         | 223084.033026 | 390        | 388.872586186 | -3.20142135024e-10 |
| DOUBLE_BOTH_FLOWS | 200       | 400        | 446168.066052 | 390        | 323.404886727 | -3.72529029846e-09 |
| DOUBLE_HOT_FLOW   | 200       | 200        | 446168.066052 | 390        | 345.986654444 | 2.09547579288e-09  |

| Case              | Scaled duty           | Error W | Allowance W       |
| ----------------- | --------------------- | ------- | ----------------- |
| DOUBLE_BOTH_FLOWS | scaling.Q_cold_W      | 0       | 1.92210560462e-08 |
| DOUBLE_BOTH_FLOWS | scaling.Q_exchanged_W | 0       | 1.92210560462e-08 |
| DOUBLE_BOTH_FLOWS | scaling.Q_hot_W       | 0       | 1.92210560462e-08 |
| DOUBLE_HOT_FLOW   | scaling.Q_hot_W       | 0       | 1.92210560462e-08 |
| FLOW_RATIO_1      | scaling.Q_hot_W       | 0       | 9.61052802312e-09 |
| FLOW_RATIO_2      | scaling.Q_hot_W       | 0       | 9.61052802312e-09 |

All six flow-scaling errors are exactly zero. `DOUBLE_BOTH_FLOWS` also reproduces all four canonical thermodynamic states byte-identically.

## Pressure and zero-duty evidence

| Case                | Hot Pout Pa | Cold Pout Pa | Hot Tout K | Cold Tout K   | Q hot W        | Q cold W           |
| ------------------- | ----------- | ------------ | ---------- | ------------- | -------------- | ------------------ |
| CANONICAL           | 300000      | 100000       | 390        | 323.404886727 | -223084.033026 | 223084.033026      |
| HOT_PRESSURE_DROP   | 270000      | 100000       | 390        | 323.337754444 | -222432.534702 | 222432.534702      |
| COLD_PRESSURE_DROP  | 300000      | 90000        | 390        | 323.344032404 | -223084.033026 | 223084.033026      |
| BOTH_PRESSURE_DROP  | 270000      | 90000        | 390        | 323.276873763 | -222432.534702 | 222432.534702      |
| ZERO_DUTY           | 300000      | 100000       | 430        | 300           | 0              | -1.06155084723e-09 |
| ZERO_DUTY_COLD_DROP | 300000      | 50000        | 430        | 299.644960108 | 0              | 3.52429196937e-10  |

Zero duty still calls PH. At reduced cold pressure, equal enthalpy recovers a different temperature; no temperature-copy shortcut exists. Pressure drops are specified, not hydraulically calculated.

## Service scope and failures

| Independent phase study | Production acceptance | Result              |
| ----------------------- | --------------------- | ------------------- |
| COLD_L_TO_VL            | No                    | phase_service_scope |
| HOT_V_TO_VL             | No                    | phase_service_scope |
| COLD_VL_TO_V            | No                    | phase_service_scope |
| HOT_VL_TO_L             | No                    | phase_service_scope |
| BUBBLE_ADJACENT         | No                    | phase_service_scope |
| DEW_ADJACENT            | No                    | phase_service_scope |

`CANONICAL` and `NEAR_TERMINAL_EQUALITY` pass. The latter recovers cold Tout approximately 389.75 K against hot Tout 390 K, without an invented minimum approach. `TERMINAL_CROSSING` and `REVERSED_DUTY` fail at `service_scope`, distinct from thermodynamic solver failure. Terminal-state balance is not exchanger design feasibility.

All 79 frozen negative semantics pass without an accepted complete exchanger result. Invalid molar fixtures are translated to authoritative mass-stream inputs without normalizing invalid compositions. Controlled PT/PH, ambiguity, property-hole and corrupted-final injections exercise production failure propagation; ambiguity/hole tests invoke the actual M11 scanner with controlled trial properties. Additional integration tests prove the same failures escape the public process path without publishing outputs.

| Case                       | Stage                    | Production status             | Accepted complete result |
| -------------------------- | ------------------------ | ----------------------------- | ------------------------ |
| hot_FLOW_0.0               | hot_input                | invalid_flow                  | No                       |
| hot_FLOW_-1.0              | hot_input                | invalid_flow                  | No                       |
| hot_FLOW_NaN               | hot_input                | invalid_flow                  | No                       |
| hot_FLOW_Infinity          | hot_input                | invalid_flow                  | No                       |
| hot_FLOW_-Infinity         | hot_input                | invalid_flow                  | No                       |
| hot_Pin_0.0                | hot_input                | invalid_pressure              | No                       |
| hot_Pin_-1.0               | hot_input                | invalid_pressure              | No                       |
| hot_Pin_NaN                | hot_input                | invalid_pressure              | No                       |
| hot_Pin_Infinity           | hot_input                | invalid_pressure              | No                       |
| hot_Pin_-Infinity          | hot_input                | invalid_pressure              | No                       |
| hot_Pout_0.0               | hot_input                | invalid_pressure              | No                       |
| hot_Pout_-1.0              | hot_input                | invalid_pressure              | No                       |
| hot_Pout_NaN               | hot_input                | invalid_pressure              | No                       |
| hot_Pout_Infinity          | hot_input                | invalid_pressure              | No                       |
| hot_Pout_-Infinity         | hot_input                | invalid_pressure              | No                       |
| hot_PRESSURE_GAIN          | hot_input                | invalid_pressure              | No                       |
| hot_TIN_199.0              | hot_input                | temperature_domain_invalid    | No                       |
| hot_TIN_501.0              | hot_input                | temperature_domain_invalid    | No                       |
| hot_TIN_NaN                | hot_input                | temperature_domain_invalid    | No                       |
| hot_TIN_Infinity           | hot_input                | temperature_domain_invalid    | No                       |
| hot_Z_SUM                  | hot_input                | invalid_composition           | No                       |
| hot_Z_NEGATIVE             | hot_input                | invalid_composition           | No                       |
| hot_Z_NONFINITE            | hot_input                | invalid_composition           | No                       |
| hot_WATER                  | hot_input                | unsupported_component         | No                       |
| hot_UNKNOWN                | hot_input                | unsupported_component         | No                       |
| cold_FLOW_0.0              | cold_input               | invalid_flow                  | No                       |
| cold_FLOW_-1.0             | cold_input               | invalid_flow                  | No                       |
| cold_FLOW_NaN              | cold_input               | invalid_flow                  | No                       |
| cold_FLOW_Infinity         | cold_input               | invalid_flow                  | No                       |
| cold_FLOW_-Infinity        | cold_input               | invalid_flow                  | No                       |
| cold_Pin_0.0               | cold_input               | invalid_pressure              | No                       |
| cold_Pin_-1.0              | cold_input               | invalid_pressure              | No                       |
| cold_Pin_NaN               | cold_input               | invalid_pressure              | No                       |
| cold_Pin_Infinity          | cold_input               | invalid_pressure              | No                       |
| cold_Pin_-Infinity         | cold_input               | invalid_pressure              | No                       |
| cold_Pout_0.0              | cold_input               | invalid_pressure              | No                       |
| cold_Pout_-1.0             | cold_input               | invalid_pressure              | No                       |
| cold_Pout_NaN              | cold_input               | invalid_pressure              | No                       |
| cold_Pout_Infinity         | cold_input               | invalid_pressure              | No                       |
| cold_Pout_-Infinity        | cold_input               | invalid_pressure              | No                       |
| cold_PRESSURE_GAIN         | cold_input               | invalid_pressure              | No                       |
| cold_TIN_199.0             | cold_input               | temperature_domain_invalid    | No                       |
| cold_TIN_501.0             | cold_input               | temperature_domain_invalid    | No                       |
| cold_TIN_NaN               | cold_input               | temperature_domain_invalid    | No                       |
| cold_TIN_Infinity          | cold_input               | temperature_domain_invalid    | No                       |
| cold_Z_SUM                 | cold_input               | invalid_composition           | No                       |
| cold_Z_NEGATIVE            | cold_input               | invalid_composition           | No                       |
| cold_Z_NONFINITE           | cold_input               | invalid_composition           | No                       |
| cold_WATER                 | cold_input               | unsupported_component         | No                       |
| cold_UNKNOWN               | cold_input               | unsupported_component         | No                       |
| hot_TOUT_199.0             | specified_hot_outlet_PT  | temperature_domain_invalid    | No                       |
| hot_TOUT_501.0             | specified_hot_outlet_PT  | temperature_domain_invalid    | No                       |
| hot_TOUT_NaN               | specified_hot_outlet_PT  | temperature_domain_invalid    | No                       |
| hot_TOUT_Infinity          | specified_hot_outlet_PT  | temperature_domain_invalid    | No                       |
| cold_TOUT_199.0            | specified_cold_outlet_PT | temperature_domain_invalid    | No                       |
| cold_TOUT_501.0            | specified_cold_outlet_PT | temperature_domain_invalid    | No                       |
| cold_TOUT_NaN              | specified_cold_outlet_PT | temperature_domain_invalid    | No                       |
| cold_TOUT_Infinity         | specified_cold_outlet_PT | temperature_domain_invalid    | No                       |
| NONZERO_KIJ                | specification            | unsupported_bip               | No                       |
| UNDER_SPECIFIED            | specification            | invalid_specification         | No                       |
| OVER_SPECIFIED             | specification            | invalid_specification         | No                       |
| EQUAL_INLET_T              | service_scope            | temperature_direction         | No                       |
| REVERSED_INLET_T           | service_scope            | temperature_direction         | No                       |
| REVERSED_DUTY              | service_scope            | heat_direction                | No                       |
| TERMINAL_CROSSING          | service_scope            | terminal_temperature_crossing | No                       |
| UNBRACKETED_COLD           | recovered_cold_outlet_PH | enthalpy_target_not_bracketed | No                       |
| UNBRACKETED_HOT            | recovered_hot_outlet_PH  | enthalpy_target_not_bracketed | No                       |
| A_hot_inlet_PT             | hot_inlet_PT             | pt_evaluation_failure         | No                       |
| A_cold_inlet_PT            | cold_inlet_PT            | pt_evaluation_failure         | No                       |
| A_specified_hot_outlet_PT  | specified_hot_outlet_PT  | pt_evaluation_failure         | No                       |
| A_PH_INJECTED              | recovered_cold_outlet_PH | controlled_ph_failure         | No                       |
| B_hot_inlet_PT             | hot_inlet_PT             | pt_evaluation_failure         | No                       |
| B_cold_inlet_PT            | cold_inlet_PT            | pt_evaluation_failure         | No                       |
| B_specified_cold_outlet_PT | specified_cold_outlet_PT | pt_evaluation_failure         | No                       |
| B_PH_INJECTED              | recovered_hot_outlet_PH  | controlled_ph_failure         | No                       |
| AMBIGUOUS                  | recovered_cold_outlet_PH | multiple_ph_roots             | No                       |
| HOLE                       | recovered_cold_outlet_PH | pt_evaluation_failure         | No                       |
| FRESH_FINAL                | recovered_cold_outlet_PH | final_acceptance_failed       | No                       |
| PURE_COEXISTENCE_GAP       | recovered_cold_outlet_PH | ph_nonconvergence             | No                       |

## Production versus independent numerical comparison

The comparator passes **1165 numerical checks**: 19 × 53 primary checks, 19 × 8 reciprocal checks and six scaling checks. Phase identity, failure classification, conservation identities and call-order assertions add structural evidence without inflating this numerical count. All recorded field-specific frozen allowances are retained. Entropy is exposed through unchanged M10 H/S structures; the Pre-M15 artifact does not freeze entropy comparison allowances, so this count does not invent an S tolerance.

| Field                      | Maximum absolute error | Allowance at governing case | Governing case         |
| -------------------------- | ---------------------- | --------------------------- | ---------------------- |
| H_target                   | 5.45696821064e-12      | 5.27116250831e-06           | NEAR_TERMINAL_EQUALITY |
| PH_residual                | 1.1823431123e-11       | 1e-06                       | COLD_HEXANE_RICH       |
| Q_cold                     | 5.12227416039e-09      | 0.00541631460879            | LIQUID_BOTH            |
| Q_exchanged                | 5.12227416039e-09      | 0.00541631460879            | LIQUID_BOTH            |
| Q_hot                      | 9.31322574615e-10      | 0.000223938686614           | LIQUID_BOTH            |
| cold.duty_identity         | 0                      | 0                           | CANONICAL              |
| cold.flow                  | 0                      | 2.84217094304e-12           | CANONICAL              |
| cold.mass_residual         | 0                      | 0                           | CANONICAL              |
| cold_in.H                  | 7.27595761418e-12      | 1.22037801719e-06           | LIQUID_BOTH            |
| cold_in.P                  | 0                      | 0                           | CANONICAL              |
| cold_in.T                  | 0                      | 1e-07                       | CANONICAL              |
| cold_in.beta               | 0                      | 2e-09                       | CANONICAL              |
| cold_in.liquid.H           | 7.27595761418e-12      | 1.22037801719e-06           | LIQUID_BOTH            |
| cold_in.liquid.Z           | 0                      | 1.37098540027e-09           | LIQUID_BOTH            |
| cold_in.liquid.q0          | 0                      | 2e-09                       | LIQUID_BOTH            |
| cold_in.liquid.q1          | 0                      | 2e-09                       | LIQUID_BOTH            |
| cold_in.vapor.H            | 4.54747350886e-12      | 1.0609449212e-06            | COLD_HEXANE_RICH       |
| cold_in.vapor.Z            | 1.11022302463e-16      | 1.19562900038e-09           | CANONICAL              |
| cold_in.vapor.q0           | 0                      | 2e-09                       | CANONICAL              |
| cold_in.vapor.q1           | 0                      | 2e-09                       | CANONICAL              |
| cold_in.z0                 | 0                      | 2e-09                       | CANONICAL              |
| cold_in.z1                 | 0                      | 2e-09                       | CANONICAL              |
| cold_out.H                 | 1.81898940355e-11      | 2.58608818507e-05           | LIQUID_BOTH            |
| cold_out.P                 | 0                      | 0                           | CANONICAL              |
| cold_out.T                 | 2.84217094304e-13      | 6.6566063581e-07            | NEAR_TERMINAL_EQUALITY |
| cold_out.beta              | 0                      | 2e-09                       | CANONICAL              |
| cold_out.liquid.H          | 1.81898940355e-11      | 2.58608818507e-05           | LIQUID_BOTH            |
| cold_out.liquid.Z          | 2.22044604925e-16      | 1.9067999142e-09            | LIQUID_BOTH            |
| cold_out.liquid.q0         | 0                      | 2e-09                       | LIQUID_BOTH            |
| cold_out.liquid.q1         | 0                      | 2e-09                       | LIQUID_BOTH            |
| cold_out.vapor.H           | 1.54614099301e-11      | 3.15171645125e-05           | NEAR_TERMINAL_EQUALITY |
| cold_out.vapor.Z           | 2.22044604925e-16      | 1.20764550354e-09           | COLD_PRESSURE_DROP     |
| cold_out.vapor.q0          | 0                      | 2e-09                       | CANONICAL              |
| cold_out.vapor.q1          | 0                      | 2e-09                       | CANONICAL              |
| cold_out.z0                | 0                      | 2e-09                       | CANONICAL              |
| cold_out.z1                | 0                      | 2e-09                       | CANONICAL              |
| duty_closure               | 3.72529029846e-09      | 0.000400019221056           | DOUBLE_BOTH_FLOWS      |
| energy_residual            | 3.72529029846e-09      | 0.000400019221056           | DOUBLE_BOTH_FLOWS      |
| hot.duty_identity          | 0                      | 0                           | CANONICAL              |
| hot.flow                   | 0                      | 1.42108547152e-12           | CANONICAL              |
| hot.mass_residual          | 0                      | 0                           | CANONICAL              |
| hot_in.H                   | 9.09494701773e-12      | 1.10017820256e-06           | LIQUID_BOTH            |
| hot_in.P                   | 0                      | 0                           | CANONICAL              |
| hot_in.T                   | 0                      | 1e-07                       | CANONICAL              |
| hot_in.beta                | 0                      | 2e-09                       | CANONICAL              |
| hot_in.liquid.H            | 9.09494701773e-12      | 1.10017820256e-06           | LIQUID_BOTH            |
| hot_in.liquid.Z            | 2.22044604925e-16      | 1.17623404143e-09           | LIQUID_BOTH            |
| hot_in.liquid.q0           | 0                      | 2e-09                       | LIQUID_BOTH            |
| hot_in.liquid.q1           | 0                      | 2e-09                       | LIQUID_BOTH            |
| hot_in.vapor.H             | 1.81898940355e-12      | 1.13357035553e-06           | HOT_BALANCED           |
| hot_in.vapor.Z             | 1.11022302463e-16      | 1.17856575822e-09           | HOT_BALANCED           |
| hot_in.vapor.q0            | 0                      | 2e-09                       | CANONICAL              |
| hot_in.vapor.q1            | 0                      | 2e-09                       | CANONICAL              |
| hot_in.z0                  | 0                      | 2e-09                       | CANONICAL              |
| hot_in.z1                  | 0                      | 2e-09                       | CANONICAL              |
| hot_out.H                  | 3.63797880709e-12      | 1.14696357554e-06           | PURE_HEXANE            |
| hot_out.P                  | 0                      | 0                           | CANONICAL              |
| hot_out.T                  | 5.68434188608e-14      | 6.46158886858e-07           | COLD_SPECIFIED         |
| hot_out.beta               | 0                      | 2e-09                       | CANONICAL              |
| hot_out.liquid.H           | 0                      | 1.13858231158e-06           | LIQUID_BOTH            |
| hot_out.liquid.Z           | 2.22044604925e-16      | 1.21253680944e-09           | LIQUID_BOTH            |
| hot_out.liquid.q0          | 0                      | 2e-09                       | LIQUID_BOTH            |
| hot_out.liquid.q1          | 0                      | 2e-09                       | LIQUID_BOTH            |
| hot_out.vapor.H            | 3.63797880709e-12      | 1.14696357554e-06           | PURE_HEXANE            |
| hot_out.vapor.Z            | 3.33066907388e-16      | 1.1997247487e-09            | PURE_HEXANE            |
| hot_out.vapor.q0           | 0                      | 2e-09                       | CANONICAL              |
| hot_out.vapor.q1           | 0                      | 2e-09                       | CANONICAL              |
| hot_out.z0                 | 0                      | 2e-09                       | CANONICAL              |
| hot_out.z1                 | 0                      | 2e-09                       | CANONICAL              |
| reciprocal.Q_cold          | 5.23868948221e-10      | 0.00421655605216            | COLD_SPECIFIED         |
| reciprocal.Q_exchanged     | 5.23868948221e-10      | 0.00421655605216            | COLD_SPECIFIED         |
| reciprocal.Q_hot           | 4.54019755125e-09      | 0.00432518105803            | HOT_HEXANE_RICH        |
| reciprocal.cold.H          | 2.72848410532e-12      | 1.90816236931e-05           | COLD_SPECIFIED         |
| reciprocal.cold.T          | 5.68434188608e-14      | 5.53464954855e-07           | COLD_SPECIFIED         |
| reciprocal.energy_residual | 4.54019755125e-09      | 0.000300047180426           | HOT_HEXANE_RICH        |
| reciprocal.hot.H           | 4.54747350886e-11      | 4.09193360419e-05           | HOT_HEXANE_RICH        |
| reciprocal.hot.T           | 3.41060513165e-13      | 6.02583100748e-07           | FLOW_RATIO_1           |
| scaling.Q_cold_W           | 0                      | 1.92210560462e-08           | DOUBLE_BOTH_FLOWS      |
| scaling.Q_exchanged_W      | 0                      | 1.92210560462e-08           | DOUBLE_BOTH_FLOWS      |
| scaling.Q_hot_W            | 0                      | 1.92210560462e-08           | DOUBLE_BOTH_FLOWS      |

## Determinism and immutable evidence

Twelve byte-identical call-order checks compare canonical and reciprocal public results after clean start, another positive, a pure-component case, invalid input, injected PH failure and reciprocal-first evaluation. Existing random `run_id` is excluded from the deterministic comparison artifact; input, requirements and implementation hashes remain. No timestamps or machine-specific absolute paths are stored.

Independent identity: `independent_two_stream_heat_exchanger@1.0`. Its frozen SHA-256 remains:

```text
533797cb1b26a8f3e597907ab9cc1e480353bd189280cfde273157cd3fa0e4b1
```

Explicit production `--write` generation succeeded. A fresh `--verify --case summary` recalculated the complete matrix and reproduced the production artifact byte-for-byte. The initial and verified production SHA-256 is:

```text
a082d6d839e25cd4000437c38ab3634a1d655f8dcb9652e4fb25494890696bb5
```

Historical independent evidence, historical production artifacts and tolerances were not regenerated. Historical production comparison commands freshly passed their numerical/structural gates; saved historical implementation-hash provenance remains untouched.

## Executed automated gates

| Gate                                               | Actual result                                                                                         |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Contract/topology gate                             | 44 TypeScript tests; 5 topology tests; 18 historical network tests; 36 M12 tests; 75 M14 tests passed |
| Focused M15 production                             | 113 tests passed                                                                                      |
| Complete Python suite                              | 532 tests passed; no failures or skips reported                                                       |
| Complete TypeScript                                | 231 tests in 21 files passed                                                                          |
| Browser/E2E                                        | 33 tests passed                                                                                       |
| Production build                                   | Passed; 41/41 static paths generated                                                                  |
| Production smoke                                   | 17 pages and 17 PNG social cards, links, 404s, preview indexing and disabled delivery passed          |
| Schema parity / historical schema branches         | Passed; every historical branch structurally identical                                                |
| Lint / types / formatting                          | Passed                                                                                                |
| Python syntax and indentation / deterministic JSON | Passed                                                                                                |
| Human-review CLI modes                             | All 11 executed automatically and passed; separate human record above                            |
| Changed-line whitespace / git diff --check         | Passed                                                                                                |
| Frozen and protected-file integrity                | Passed; see inventory below                                                                           |

The first browser launch was blocked by sandbox localhost permissions; the permitted unchanged rerun executed the suite. The new M15 test initially used an ambiguous alert selector; it was narrowed to the named Engineering error element, and the complete 33-test rerun passed. Historical browser tests were not changed. Smoke first required localhost permission and a running production server; after starting the built application, all checks passed. The task-owned production server was stopped afterward. These environment/setup failures were not treated as thermodynamic regressions.

| Historical benchmark          | Independent suite           | Production comparisons passed |
| ----------------------------- | --------------------------- | ----------------------------- |
| peng_robinson                 | 7 independent tests passed  | 122                           |
| peng_robinson_pt_boundary     | 28 independent tests passed | 325                           |
| peng_robinson_pt_vapor_parent | 25 independent tests passed | 749                           |
| peng_robinson_caloric         | 23 independent tests passed | 1526                          |
| peng_robinson_ph              | 55 independent tests passed | 401                           |
| heater_cooler_energy          | 36 independent tests passed | 1264                          |
| peng_robinson_ps              | 46 independent tests passed | 270                           |
| compressor_energy             | 66 independent tests passed | 1083                          |

M8.2 also passed nine high-accuracy grids: 1,152/1,152 successes and zero unexpected failures. Historical CLI footer statements about then-pending milestones/human validation are retained historical wording; this run does not revise their qualification reports.

## UI, PFD and freshness

M15 is available through the existing Advanced JSON validation/build/calculate workflow. Natural-language interpretation scope is unchanged. The result view identifies the rigorous model, Mode A/B, specified/recovered sides, four states, independent flows, signed duties, transferred duty, energy closure, BIP/provider and compact PH diagnostics. The PFD shows four named ports on two separate material lines. A rendered screenshot was inspected. Existing workflow revision/input hashes make both outlets stale together, hide the accepted M15 view after edits/failure, and reject stale responses. Browser coverage exercises canonical Mode A, reciprocal Mode B, specification change and rejected heat direction. Unit workflow coverage also edits each inlet independently.

## Exact files and integrity

Of 320 baseline tracked files, **307 remain byte-identical** and **13 are intentionally modified**. There are **10 new M15 files**. All historical thermodynamic equations, independent benchmark code/reference JSON, historical production evidence, historical assertions, dependencies, global stream definitions and `error.schema.json` remain unchanged. The only historical test-source changes are the two explicitly authorized fixture discriminant guards. The generated `next-env.d.ts` returned to its baseline bytes after the production build.

| Existing file modified                      |
| ------------------------------------------- |
| `contracts/v1/flowsheet.schema.json`        |
| `contracts/v1/requirements.schema.json`     |
| `contracts/v1/results.schema.json`          |
| `contracts/v1/validation.schema.json`       |
| `docs/RIOGINEER_MASTER_CONTEXT.md`          |
| `engine/riogineer_engine/core.py`           |
| `engine/riogineer_engine/network.py`        |
| `engine/riogineer_engine/network_models.py` |
| `src/app/digital-engineer/pfd.tsx`          |
| `src/app/digital-engineer/workspace.tsx`    |
| `src/lib/digital-engineer/contracts.ts`     |
| `tests/compression-fixture.ts`              |
| `tests/sequential-fixture.ts`               |

| New file created                                                  |
| ----------------------------------------------------------------- |
| `MILESTONE_15.md`                                                 |
| `benchmarks/two_stream_heat_exchanger/compare_production.py`      |
| `benchmarks/two_stream_heat_exchanger/production_comparison.json` |
| `engine/riogineer_engine/two_stream_heat_exchanger_energy.py`     |
| `engine/riogineer_engine/two_stream_heat_exchanger_process.py`    |
| `engine/tests/test_two_stream_heat_exchanger_energy.py`           |
| `engine/tests/test_two_stream_heat_exchanger_topology.py`         |
| `src/app/digital-engineer/two-stream-heat-exchanger-results.tsx`  |
| `tests/e2e/two-stream-heat-exchanger.spec.ts`                     |
| `tests/two-stream-heat-exchanger-contracts.test.ts`               |

## Tested human-review commands

Run from the repository root. Each mode freshly calculates its displayed cases. Summary/verification executes all gates; normal review never rewrites either reference or production evidence. These commands were exercised by automation and do not constitute human-operated validation.

```sh
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case canonical
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case reciprocal
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case flow
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case phase
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case zero_duty
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case temperature_scope
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case negative
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case summary --verify
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case pressure
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case composition
engine/.venv/bin/python -B benchmarks/two_stream_heat_exchanger/compare_production.py --case pure
```

## Final Git state

All changes remain unstaged, uncommitted and unpushed.

```text
 M contracts/v1/flowsheet.schema.json
 M contracts/v1/requirements.schema.json
 M contracts/v1/results.schema.json
 M contracts/v1/validation.schema.json
 M docs/RIOGINEER_MASTER_CONTEXT.md
 M engine/riogineer_engine/core.py
 M engine/riogineer_engine/network.py
 M engine/riogineer_engine/network_models.py
 M src/app/digital-engineer/pfd.tsx
 M src/app/digital-engineer/workspace.tsx
 M src/lib/digital-engineer/contracts.ts
 M tests/compression-fixture.ts
 M tests/sequential-fixture.ts
?? MILESTONE_15.md
?? benchmarks/two_stream_heat_exchanger/compare_production.py
?? benchmarks/two_stream_heat_exchanger/production_comparison.json
?? engine/riogineer_engine/two_stream_heat_exchanger_energy.py
?? engine/riogineer_engine/two_stream_heat_exchanger_process.py
?? engine/tests/test_two_stream_heat_exchanger_energy.py
?? engine/tests/test_two_stream_heat_exchanger_topology.py
?? src/app/digital-engineer/two-stream-heat-exchanger-results.tsx
?? tests/e2e/two-stream-heat-exchanger.spec.ts
?? tests/two-stream-heat-exchanger-contracts.test.ts
```

Milestone 15 automated acceptance is complete. Human-operated M15 validation is complete — 2026-09-30.
