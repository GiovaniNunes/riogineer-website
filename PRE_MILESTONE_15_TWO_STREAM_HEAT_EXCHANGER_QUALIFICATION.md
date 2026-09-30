# Pre-Milestone 15 — Independent two-stream heat-exchanger qualification

Independent Pre-M15 automated qualification: **COMPLETE**.

Human-operated Pre-M15 validation: **COMPLETE — 2026-09-30**.

Production M15: **NOT IMPLEMENTED**.

## Human-operated validation — 2026-09-30

The human reviewer reported successful execution and inspection of `canonical`, `reciprocal`, `flow`, `phase`, `zero_duty`, `temperature_scope`, `negative` and `summary`. All eight reviewed modes passed. This human validation record is separate from the completed automated qualification below. Production M15 remains NOT IMPLEMENTED.

The canonical review confirmed two materially separate streams coupled only by energy transfer. The hot stream remained vapor at 100 mol/s, cooling from 430 K to 390 K; the cold stream remained vapor at 200 mol/s, warming from 300 K to approximately 323.404886727 K. Reviewed duties were approximately Q_hot = -223084.033026 W, Q_cold = +223084.033026 W and Q_exchanged = 223084.033026 W. The energy residual was approximately 2.04e-10 W and the PH residual approximately 9.09e-13 J/mol. The recovered outlet had one qualified PH candidate and a fresh final evaluation.

Reciprocal review confirmed consistency between Mode A (specified hot outlet temperature, recovered cold outlet) and Mode B (specified cold outlet temperature, recovered hot outlet). The reviewed matrix covered canonical, hot/cold/both pressure drops, flow ratios, doubled flows, composition variations, pure methane, pure n-hexane, the liquid case, zero duty, zero duty with pressure change, cold-specified mode and near-terminal equality. Recovered temperatures, enthalpies and duties remained within their frozen allowances.

Flow review confirmed that changing cold flow changes the recovered cold outlet for the same hot-side specification. Doubling both flows preserved specific thermodynamic states and doubled exchanged duty; doubling hot flow alone doubled hot duty and changed the cold outlet. All frozen scaling checks passed, with the relevant exact scaling errors equal to 0 W.

All six reviewed phase studies—`COLD_L_TO_VL`, `HOT_V_TO_VL`, `COLD_VL_TO_V`, `HOT_VL_TO_L`, `BUBBLE_ADJACENT` and `DEW_ADJACENT`—were thermodynamically calculable within their allowances. They remain separate thermodynamic studies with primary scope rejected. The recommended initial production scope remains single-phase inlet and outlet states; human review does not promote phase-change studies into that service scope.

Zero-duty review confirmed unchanged temperatures and zero exchanged heat when pressure is unchanged. In `ZERO_DUTY_COLD_DROP`, cold pressure decreased from 100000 Pa to 50000 Pa while heat transfer remained approximately zero and cold enthalpy remained constant within allowance; temperature changed from 300 K to approximately 299.644960108 K. Zero heat transfer therefore does not imply constant temperature under pressure change.

Temperature-scope review confirmed acceptance of `CANONICAL` and `NEAR_TERMINAL_EQUALITY`, the latter with hot outlet 390 K and cold outlet 389.75 K. No minimum approach temperature is qualified. The thermodynamically calculable `TERMINAL_CROSSING` and `REVERSED_DUTY` cases retained the respective `terminal_temperature_crossing` and `heat_direction` classifications and remain outside recommended initial equipment service. Terminal-state energy balance remains distinct from exchanger design feasibility; no UA, LMTD, NTU, pinch or design minimum approach is claimed.

All 79 reviewed negative cases passed with no accepted complete exchanger result. They covered hot/cold flow and pressure, pressure gain, temperature domain, composition, unsupported components/BIP, under/over-specification, inlet temperature direction, reversed duty, crossing, unbracketed recovered outlets, inlet/specified-outlet PT failures, recovered-outlet PH failures, ambiguous PH roots, property holes, fresh-final acceptance failure and pure-component coexistence gaps.

The human-reviewed summary reported **19 primary positives, six separate phase studies, 79 negatives, 2,002 numerical comparisons and 12 byte-identical call-order checks**, all passing. The maximum reported energy residual was approximately 1.09896e-7 W, within its frozen allowance. The maximum reported PH residual was approximately 1.73604e-8 J/mol against a 1e-6 J/mol allowance. Frozen SHA-256 remained `533797cb1b26a8f3e597907ab9cc1e480353bd189280cfde273157cd3fa0e4b1`.

All existing qualification limits and future contract/topology authorization boundaries remain unchanged. This record does not authorize or implement production M15.

## Baseline and boundaries

The clean working tree was on `main`, with HEAD and `origin/main` both equal to `e17490f1b470645e9a042086d9330d52c90507de`, the committed M14 state. Before creating files, all 313 existing tracked files were inventoried with SHA-256. No production equipment, contracts, dispatch, topology, application, dependencies, historical tests, evidence, tolerances or milestone reports were changed. The sole existing-file update is the authorized Master Context status paragraph after successful qualification.

This qualifies independent terminal-state thermodynamic calculations for a future `rigorous_two_stream_heat_exchanger@1.0`. It does not implement that production model. Thermodynamic energy-balance feasibility is distinct from physical exchanger design feasibility; no area, flow arrangement or distributed temperature profile is available to establish the latter.

## Independent methodology and provenance

Reference identity: `independent_two_stream_heat_exchanger@1.0`. This is an evidence identity, not a production equipment model. The benchmark imports only the established independent PT/caloric and PH helpers under `benchmarks/`; structural tests verify no `riogineer_engine` dependency. No production-forward diagnostic was created. Production does not supply expected states, duties, temperatures or phase classifications.

Thermo supplies the primary Peng–Robinson states, with the frozen 0.45724/0.07780 constants and classical quadratic mixing. Every PT trial explicitly enters `FlashVL.flash_TP_stability_test` / Michelsen stability; there is no previous-state warm start. The inherited entropy-capable PT helper supplies the established tighter `PT_SS_TOL = 1e-26`; no PS inversion is performed. PT material residuals must be <=1e-10 and two-phase log-fugacity residuals <=1e-9. Inherited independent analytic Cp integrals and PR departure equations audit library enthalpies. Entropy may appear in inherited state payloads but is not an exchanger acceptance/design criterion.

The isolated `.local/pre-m8-venv` environment and unchanged historical stack were reused. Active package versions:

| Package   | Version |
| --------- | ------- |
| chemicals | 1.5.2   |
| fluids    | 1.3.1   |
| numpy     | 2.2.6   |
| scipy     | 1.15.3  |
| thermo    | 0.6.0   |

The benchmark-local requirements pin the full inherited environment, including transitive and previously installed packages. teqp is retained in those environment pins but is not called by this reference. No dependency was installed or changed for production. Third-party notices preserve the established Chemicals/Thermo MIT notices and NumPy/SciPy BSD attribution. Cp coefficients are the same two Poling rows distributed with Chemicals 1.5.2; there is no runtime network/data lookup.

Component order is always methane, n_hexane. Both sides use explicit constant zero kij, with distinct side-owned compositions. Frozen constants are:

| Component | MW (kg/kmol) | Tc (K)  | Pc (Pa absolute)  | omega              |
| --------- | ------------ | ------- | ----------------- | ------------------ |
| methane   | 16.0428      | 190.564 | 4599200.0         | 0.01142            |
| n_hexane  | 86.17536     | 507.82  | 3044115.328359688 | 0.3003189315498438 |

Exact Cp coefficients, their underlying ranges, component data, source hashes, numerical controls and all field-specific allowances are embedded in the JSON. The exchanger qualification is bounded to 200–500 K, even though the inherited Cp data cover a wider range. H is ideal-gas sensible enthalpy relative to 298.15 K; pressure is Pa absolute, temperature K, H J/mol, F mol/s, Q W. No separate flow-work term is added: pressure effects already enter molar enthalpy.

## Specification, conservation and sign convention

Mode A specifies hot outlet temperature. Independent PT evaluates hot inlet, cold inlet and hot outlet. The balance calculates `Q_hot = F_hot*(H_hot,out-H_hot,in)` and `H_cold,out,target = H_cold,in-Q_hot/F_cold`; independent PH recovers the cold outlet.

Mode B specifies cold outlet temperature. PT evaluates cold outlet, `Q_cold = F_cold*(H_cold,out-H_cold,in)` and `H_hot,out,target = H_hot,in-Q_cold/F_hot`; PH recovers the hot outlet. Exactly one temperature specification is required. Both and neither are rejected. No duty-specified or UA mode is qualified.

Duties are recalculated from fresh accepted states on both sides. Positive Q enters that material stream. Normal hot-to-cold service has Q_hot <= 0, Q_cold >= 0 and `Q_exchanged = Q_cold = -Q_hot` within the recorded energy allowance. The explicitly stored energy residual is `F_hot*(H_hot,out-H_hot,in) + F_cold*(H_cold,out-H_cold,in)`. Environmental heat and shaft work are zero. Numerical sign allowances permit only the documented PH/roundoff error around zero duty.

Each side preserves its own flow and composition exactly; no averaging, mixing, component transfer or pressure equalization occurs. Independent inlet/outlet pressure specifications obey `0 < P_out <= P_in`. Tests verify that changing cold pressure or composition leaves specified hot-side states and duty unchanged, and changing hot-side data does not alter cold inlet PT. The recovered opposite-side state may change through energy coupling only.

## PH controls, resolution and allowances

The inherited independent PH solver scans the complete 200–500 K domain with 128 points, requires one candidate and uses SciPy brentq with xtol 1e-10 K, rtol 1e-14 and at most 100 iterations. Acceptance requires a fresh final property evaluation with absolute enthalpy residual <=1e-6 J/mol. Property holes, multiple roots, unbracketed targets and unsupported pure coexistence gaps fail without an accepted complete exchanger result.

Every primary case and phase study also uses a 256-point brentq scan, a 512-point bisection scan, and a 128-point inversion using independently reconstructed caloric enthalpy. Every reciprocal solve additionally receives its own 256-point brentq and 512-point bisection checks, including recovered two-phase states. Candidate count stays one, classification stays unchanged and recovered states remain inside the frozen allowances. Bracket coordinates and root diagnostics for each resolution are recorded, rather than requiring identical scan brackets. Positive/study base, reciprocal and refinement scans performed 48,000 scan evaluations, excluding additional negative/call-order work. Pure-gap rejection was separately checked at 128, 256 and 512 points.

Base allowances are T = 1e-7 K; H = 1e-6 + 1e-11*abs(H) J/mol; beta and phase composition = 2e-9; Z = 2e-10 + 1e-9*abs(Z). These are inherited numerical scales, established before any production comparison. Actual per-case allowances are frozen, not derived by fitting observed production errors.

Local slopes use symmetric +/-0.001 K evaluations and require unchanged phase classification and positive dH/dT. The primary recovered-state dH/dT range is approximately 36.8838–152.8883 J/(mol K); the primary matrix does not depend on a nearly singular PH root. Phase-study slopes and conditioning budgets are recorded separately.

Let a denote the specified side and b the recovered side. The target-H budget is `E_H(b,in) + (F_a/F_b)*(E_H(a,out)+E_H(a,in))`. The recovered temperature budget is `1e-7 + 4*(target-H budget + 1e-6)/local_dH_dT`. Each recovered field adds its absolute local slope times that budget to its base allowance. The factor four is a conservative local linear-propagation margin, not a global conditioning guarantee.

Each side's duty comparison allowance is `F_side*(E_H,in+E_H,out)+roundoff`. Roundoff is `64*epsilon*max(1, abs(Q_hot), abs(Q_cold), abs(F_side*H_state))`. Equipment energy closure permits `F_recovered*1e-6 + roundoff`. Reciprocal comparisons use the sum of original and reciprocal field/duty allowances. No historical tolerance was altered.

## Canonical case

| Quantity               | Hot side      | Cold side     |
| ---------------------- | ------------- | ------------- |
| Flow (mol/s)           | 100.0         | 200.0         |
| Composition            | [0.9, 0.1]    | [0.9, 0.1]    |
| Inlet P (Pa absolute)  | 300000.0      | 100000.0      |
| Outlet P (Pa absolute) | 300000.0      | 100000.0      |
| Inlet T (K)            | 430           | 300           |
| Outlet T (K)           | 390           | 323.404886727 |
| Inlet H (J/mol)        | 6762.80787871 | 53.0231224156 |
| Outlet H (J/mol)       | 4531.96754845 | 1168.44328754 |
| Inlet phase            | single_vapor  | single_vapor  |
| Outlet phase           | single_vapor  | single_vapor  |
| Inlet beta             | 1             | 1             |
| Outlet beta            | 1             | 1             |

| Quantity          | Value             |
| ----------------- | ----------------- |
| Q_hot_W           | -223084.033026    |
| Q_cold_W          | 223084.033026     |
| Q_exchanged_W     | 223084.033026     |
| energy_residual_W | 2.03726813197e-10 |
| PH_residual_J_mol | 9.09494701773e-13 |

The cold PH solve had one candidate and 5 root iterations, with one fresh final evaluation. Both streams remain vapor. Hot inlet > hot outlet > cold outlet > cold inlet; independent side pressures remain distinct.

## Primary matrix and reciprocal recovery

All 19 primary cases passed. Each also has a reciprocal calculation; these paired calculations are not counted as extra primary cases. Mode A -> B and Mode B -> A both pass. All four state payloads, beta and phase properties are stored at full precision.

| Case                   | Group             | Mode | Hot Tout (K) | Cold Tout (K) | Q exchanged (W)   |
| ---------------------- | ----------------- | ---- | ------------ | ------------- | ----------------- |
| CANONICAL              | canonical         | A    | 390          | 323.404886727 | 223084.033026     |
| HOT_PRESSURE_DROP      | pressure          | A    | 390          | 323.337754444 | 222432.534702     |
| COLD_PRESSURE_DROP     | pressure          | A    | 390          | 323.344032404 | 223084.033026     |
| BOTH_PRESSURE_DROP     | pressure          | A    | 390          | 323.276873763 | 222432.534702     |
| FLOW_RATIO_1           | flow              | A    | 390          | 345.986654444 | 223084.033026     |
| FLOW_RATIO_2           | flow              | A    | 390          | 388.872586186 | 223084.033026     |
| DOUBLE_BOTH_FLOWS      | flow              | A    | 390          | 323.404886727 | 446168.066052     |
| DOUBLE_HOT_FLOW        | flow              | A    | 390          | 345.986654444 | 446168.066052     |
| COLD_BALANCED          | composition       | A    | 410          | 355.618546399 | 113242.840131     |
| COLD_HEXANE_RICH       | composition       | A    | 410          | 354.50585517  | 113242.840131     |
| HOT_BALANCED           | composition       | A    | 390          | 346.933827343 | 455699.414216     |
| HOT_HEXANE_RICH        | composition       | A    | 390          | 358.485059172 | 573092.939417     |
| PURE_METHANE           | pure              | A    | 390          | 322.701088248 | 165296.07938      |
| PURE_HEXANE            | pure              | A    | 390          | 324.88743049  | 738163.320371     |
| LIQUID_BOTH            | composition       | A    | 320          | 267.258578057 | 384041.090131     |
| ZERO_DUTY              | zero_duty         | A    | 430          | 300           | 0                 |
| ZERO_DUTY_COLD_DROP    | zero_duty         | A    | 430          | 299.644960108 | 2.00373051484e-10 |
| COLD_SPECIFIED         | reciprocal        | B    | 396.06571038 | 320           | 190126.400313     |
| NEAR_TERMINAL_EQUALITY | temperature_scope | A    | 390          | 389.75        | 223084.033026     |

Reciprocal errors below are the maximum of the two side-specific outlet errors; the JSON retains both sides and all allowances.

| Pair                   | Original mode | Reciprocal mode | Max outlet dT (K) | Max outlet dH (J/mol) | Max dQ (W)        |
| ---------------------- | ------------- | --------------- | ----------------- | --------------------- | ----------------- |
| CANONICAL              | A             | B               | 0                 | 0                     | 0                 |
| HOT_PRESSURE_DROP      | A             | B               | 1.13686837722e-13 | 9.09494701773e-12     | 9.02218744159e-10 |
| COLD_PRESSURE_DROP     | A             | B               | 0                 | 0                     | 0                 |
| BOTH_PRESSURE_DROP     | A             | B               | 1.13686837722e-13 | 4.54747350886e-12     | 4.65661287308e-10 |
| FLOW_RATIO_1           | A             | B               | 5.68434188608e-14 | 2.72848410532e-12     | 2.61934474111e-10 |
| FLOW_RATIO_2           | A             | B               | 5.68434188608e-14 | 2.72848410532e-12     | 2.61934474111e-10 |
| DOUBLE_BOTH_FLOWS      | A             | B               | 0                 | 0                     | 0                 |
| DOUBLE_HOT_FLOW        | A             | B               | 5.68434188608e-14 | 2.72848410532e-12     | 5.23868948221e-10 |
| COLD_BALANCED          | A             | B               | 5.68434188608e-14 | 2.72848410532e-12     | 2.76486389339e-10 |
| COLD_HEXANE_RICH       | A             | B               | 1.13686837722e-13 | 4.54747350886e-12     | 4.51109372079e-10 |
| HOT_BALANCED           | A             | B               | 0                 | 0                     | 0                 |
| HOT_HEXANE_RICH        | A             | B               | 0                 | 0                     | 0                 |
| PURE_METHANE           | A             | B               | 0                 | 0                     | 0                 |
| PURE_HEXANE            | A             | B               | 0                 | 0                     | 0                 |
| LIQUID_BOTH            | A             | B               | 1.70530256582e-13 | 1.27329258248e-11     | 1.2805685401e-09  |
| ZERO_DUTY              | A             | B               | 0                 | 0                     | 0                 |
| ZERO_DUTY_COLD_DROP    | A             | B               | 0                 | 0                     | 0                 |
| COLD_SPECIFIED         | B             | A               | 0                 | 0                     | 0                 |
| NEAR_TERMINAL_EQUALITY | A             | B               | 5.68434188608e-14 | 2.72848410532e-12     | 2.61934474111e-10 |

## Flow, pressure and composition

The canonical flow ratio is 0.5, supplemented by ratios 1 and 2. Fixed specified-hot states keep Q_hot unchanged when only cold flow changes; recovered cold enthalpy rise increases inversely with cold flow. Doubling hot flow doubles hot duty. Doubling both flows preserves the states and doubles both duties and exchanged duty, with zero recorded scaling error. Side-specific material conservation is independent of equal flow.

| Case              | F_hot | F_cold | Q exchanged (W) | Hot Tout (K) | Cold Tout (K) | Energy residual (W) |
| ----------------- | ----- | ------ | --------------- | ------------ | ------------- | ------------------- |
| CANONICAL         | 100.0 | 200.0  | 223084.033026   | 390          | 323.404886727 | 2.03726813197e-10   |
| FLOW_RATIO_1      | 100.0 | 100.0  | 223084.033026   | 390          | 345.986654444 | -2.91038304567e-11  |
| FLOW_RATIO_2      | 100.0 | 50.0   | 223084.033026   | 390          | 388.872586186 | -1.16415321827e-10  |
| DOUBLE_BOTH_FLOWS | 200.0 | 400.0  | 446168.066052   | 390          | 323.404886727 | 4.07453626394e-10   |
| DOUBLE_HOT_FLOW   | 200.0 | 200.0  | 446168.066052   | 390          | 345.986654444 | -5.82076609135e-11  |

Outlet pressures are specifications, not calculated hydraulic losses. Zero drop and independent hot, cold and combined drops pass.

| Case               | Hot Pin/Pout (Pa) | Cold Pin/Pout (Pa) | Hot Tout (K) | Cold Tout (K) | Q exchanged (W) |
| ------------------ | ----------------- | ------------------ | ------------ | ------------- | --------------- |
| CANONICAL          | 300000.0/300000.0 | 100000.0/100000.0  | 390          | 323.404886727 | 223084.033026   |
| HOT_PRESSURE_DROP  | 300000.0/270000.0 | 100000.0/100000.0  | 390          | 323.337754444 | 222432.534702   |
| COLD_PRESSURE_DROP | 300000.0/300000.0 | 100000.0/90000.0   | 390          | 323.344032404 | 223084.033026   |
| BOTH_PRESSURE_DROP | 300000.0/270000.0 | 100000.0/90000.0   | 390          | 323.276873763 | 222432.534702   |

Methane-rich, balanced and n-hexane-rich cases exhibit different caloric response without combining composition vectors. Both-liquid service is demonstrated separately within the primary single-phase matrix. Pure methane and pure n-hexane vapor cases pass. Pure endpoints retain the two-component basis with a zero mole fraction.

## Phase-change and coexistence studies

Six cases are independently calculable but excluded from the initial primary service recommendation. All pass reciprocal recovery and refinement. Constructed study flow ratios use independently evaluated enthalpy differences to place a selected opposite-side endpoint; the frozen result is subsequently recovered by PH without passing that endpoint temperature to the inversion.

| Case            | Side | Inlet phase   | Outlet phase  | beta out          | Accepted primary scope? |
| --------------- | ---- | ------------- | ------------- | ----------------- | ----------------------- |
| COLD_L_TO_VL    | hot  | single_vapor  | single_vapor  | 1                 | No                      |
| COLD_L_TO_VL    | cold | single_liquid | vapor_liquid  | 0.298866797488    | No                      |
| HOT_V_TO_VL     | hot  | single_vapor  | vapor_liquid  | 0.298866797488    | No                      |
| HOT_V_TO_VL     | cold | single_vapor  | single_vapor  | 1                 | No                      |
| COLD_VL_TO_V    | hot  | single_vapor  | single_vapor  | 1                 | No                      |
| COLD_VL_TO_V    | cold | vapor_liquid  | single_vapor  | 1                 | No                      |
| HOT_VL_TO_L     | hot  | vapor_liquid  | single_liquid | 0                 | No                      |
| HOT_VL_TO_L     | cold | single_vapor  | single_vapor  | 1                 | No                      |
| BUBBLE_ADJACENT | hot  | single_vapor  | single_vapor  | 1                 | No                      |
| BUBBLE_ADJACENT | cold | single_liquid | vapor_liquid  | 0.000579689961115 | No                      |
| DEW_ADJACENT    | hot  | single_vapor  | vapor_liquid  | 0.998666944704    | No                      |
| DEW_ADJACENT    | cold | single_vapor  | single_vapor  | 1                 | No                      |

At 6000000 Pa and z = [0.5, 0.5], the independent bubble and dew temperatures are 231.117554351 K and 468.265889532 K. Studies use +/-0.05 K endpoints and +/-0.001 K conditioning evaluations. Phase identity remains stable under refinement; beta, x/y, Z_L/Z_V and H_L/H_V are frozen wherever those phases exist. No absent-phase payload is fabricated.

The pure n-hexane coexistence study at 1000 Pa locates saturation near 242.828331853 K and records one-sided states +/-1e-5 K from it. An enthalpy target between these states fails fresh residual acceptance at all three scan resolutions. No interpolation through that discontinuity is permitted.

## Zero-duty and temperature-scope conclusions

Zero duty at unchanged pressures preserves the states within the PH residual tolerance. Zero hot duty with cold pressure falling from 100000 to 50000 Pa remains isenthalpic on the cold side, whose recovered temperature is approximately 299.644960108 K rather than 300 K. Zero heat transfer is not equivalent to equal temperature when pressure changes.

The proposed initial terminal rule is `T_hot,in > T_cold,out`, `T_hot,out > T_cold,in`, and `T_hot,out >= T_cold,out`, together with the declared hot inlet hotter than the cold inlet and the signed-duty requirements. No arbitrary 5 K/10 K minimum approach is imposed. The near-equality probe uses 0.25 K separation only as a test location, not a qualified minimum approach.

| Case                   | Specification   | Thi / Tho (K) | Tci / Tco (K)       | Thermodynamic status | Recommended equipment status  |
| ---------------------- | --------------- | ------------- | ------------------- | -------------------- | ----------------------------- |
| CANONICAL              | T_hot_out=390.0 | 430 / 390     | 300 / 323.404886727 | success              | accepted                      |
| NEAR_TERMINAL_EQUALITY | T_hot_out=390.0 | 430 / 390     | 300 / 389.75        | success              | accepted                      |
| TERMINAL_CROSSING      | T_hot_out=390.0 | 430 / 390     | 300 / 409.278540656 | success              | terminal_temperature_crossing |
| REVERSED_DUTY          | T_hot_out=440.0 | 430 / 440     | 300 / 293.784415099 | success              | heat_direction                |

The terminal-crossing solution balances energy and has a unique thermodynamic outlet, but the conservative initial equipment policy rejects it. That rejection does not claim such terminals are impossible in every flow arrangement. Reversed declared heat duty is also rejected without relabeling sides. Equality/reversal of inlet hot/cold temperatures is rejected before state calculation.

## Negative matrix

All 79 negatives reject without an accepted complete exchanger result or an accepted outlet pair. Cases include each side's invalid/nonfinite flow, all four pressures and pressure gains, inlet/specified temperatures, compositions, unsupported components/water, nonzero BIP, over/under-specification, contradictory direction, crossing, unbracketed targets, pure coexistence gap, ambiguity, property hole and failed fresh acceptance.

Controlled PT failures cover both inlets and each specified outlet; PH failures cover either recovered side. Ambiguity/property-hole fixtures exercise the actual independent PH solver with a clearly synthetic evaluator. A corrupted nominally successful PH payload tests fresh acceptance checks. These are deliberately labeled controls, not physical fluid states. The pure-gap and unbracketed cases use actual thermodynamic states. An initial synthetic ambiguity fixture omitted its required temperature field; that new-fixture error was corrected before qualification without changing historical code or tolerances.

| Case                       | Expected failure              | Failure stage            | Accepted complete result |
| -------------------------- | ----------------------------- | ------------------------ | ------------------------ |
| hot_FLOW_0.0               | invalid_flow                  | hot_input                | No                       |
| hot_FLOW_-1.0              | invalid_flow                  | hot_input                | No                       |
| hot_FLOW_NaN               | invalid_flow                  | hot_input                | No                       |
| hot_FLOW_Infinity          | invalid_flow                  | hot_input                | No                       |
| hot_FLOW_-Infinity         | invalid_flow                  | hot_input                | No                       |
| hot_Pin_0.0                | invalid_pressure              | hot_input                | No                       |
| hot_Pin_-1.0               | invalid_pressure              | hot_input                | No                       |
| hot_Pin_NaN                | invalid_pressure              | hot_input                | No                       |
| hot_Pin_Infinity           | invalid_pressure              | hot_input                | No                       |
| hot_Pin_-Infinity          | invalid_pressure              | hot_input                | No                       |
| hot_Pout_0.0               | invalid_pressure              | hot_input                | No                       |
| hot_Pout_-1.0              | invalid_pressure              | hot_input                | No                       |
| hot_Pout_NaN               | invalid_pressure              | hot_input                | No                       |
| hot_Pout_Infinity          | invalid_pressure              | hot_input                | No                       |
| hot_Pout_-Infinity         | invalid_pressure              | hot_input                | No                       |
| hot_PRESSURE_GAIN          | invalid_pressure              | hot_input                | No                       |
| hot_TIN_199.0              | temperature_domain_invalid    | hot_input                | No                       |
| hot_TIN_501.0              | temperature_domain_invalid    | hot_input                | No                       |
| hot_TIN_NaN                | temperature_domain_invalid    | hot_input                | No                       |
| hot_TIN_Infinity           | temperature_domain_invalid    | hot_input                | No                       |
| hot_Z_SUM                  | invalid_composition           | hot_input                | No                       |
| hot_Z_NEGATIVE             | invalid_composition           | hot_input                | No                       |
| hot_Z_NONFINITE            | invalid_composition           | hot_input                | No                       |
| hot_WATER                  | unsupported_component         | hot_input                | No                       |
| hot_UNKNOWN                | unsupported_component         | hot_input                | No                       |
| cold_FLOW_0.0              | invalid_flow                  | cold_input               | No                       |
| cold_FLOW_-1.0             | invalid_flow                  | cold_input               | No                       |
| cold_FLOW_NaN              | invalid_flow                  | cold_input               | No                       |
| cold_FLOW_Infinity         | invalid_flow                  | cold_input               | No                       |
| cold_FLOW_-Infinity        | invalid_flow                  | cold_input               | No                       |
| cold_Pin_0.0               | invalid_pressure              | cold_input               | No                       |
| cold_Pin_-1.0              | invalid_pressure              | cold_input               | No                       |
| cold_Pin_NaN               | invalid_pressure              | cold_input               | No                       |
| cold_Pin_Infinity          | invalid_pressure              | cold_input               | No                       |
| cold_Pin_-Infinity         | invalid_pressure              | cold_input               | No                       |
| cold_Pout_0.0              | invalid_pressure              | cold_input               | No                       |
| cold_Pout_-1.0             | invalid_pressure              | cold_input               | No                       |
| cold_Pout_NaN              | invalid_pressure              | cold_input               | No                       |
| cold_Pout_Infinity         | invalid_pressure              | cold_input               | No                       |
| cold_Pout_-Infinity        | invalid_pressure              | cold_input               | No                       |
| cold_PRESSURE_GAIN         | invalid_pressure              | cold_input               | No                       |
| cold_TIN_199.0             | temperature_domain_invalid    | cold_input               | No                       |
| cold_TIN_501.0             | temperature_domain_invalid    | cold_input               | No                       |
| cold_TIN_NaN               | temperature_domain_invalid    | cold_input               | No                       |
| cold_TIN_Infinity          | temperature_domain_invalid    | cold_input               | No                       |
| cold_Z_SUM                 | invalid_composition           | cold_input               | No                       |
| cold_Z_NEGATIVE            | invalid_composition           | cold_input               | No                       |
| cold_Z_NONFINITE           | invalid_composition           | cold_input               | No                       |
| cold_WATER                 | unsupported_component         | cold_input               | No                       |
| cold_UNKNOWN               | unsupported_component         | cold_input               | No                       |
| hot_TOUT_199.0             | temperature_domain_invalid    | specified_hot_outlet_PT  | No                       |
| hot_TOUT_501.0             | temperature_domain_invalid    | specified_hot_outlet_PT  | No                       |
| hot_TOUT_NaN               | temperature_domain_invalid    | specified_hot_outlet_PT  | No                       |
| hot_TOUT_Infinity          | temperature_domain_invalid    | specified_hot_outlet_PT  | No                       |
| cold_TOUT_199.0            | temperature_domain_invalid    | specified_cold_outlet_PT | No                       |
| cold_TOUT_501.0            | temperature_domain_invalid    | specified_cold_outlet_PT | No                       |
| cold_TOUT_NaN              | temperature_domain_invalid    | specified_cold_outlet_PT | No                       |
| cold_TOUT_Infinity         | temperature_domain_invalid    | specified_cold_outlet_PT | No                       |
| NONZERO_KIJ                | unsupported_bip               | specification            | No                       |
| UNDER_SPECIFIED            | invalid_specification         | specification            | No                       |
| OVER_SPECIFIED             | invalid_specification         | specification            | No                       |
| EQUAL_INLET_T              | temperature_direction         | service_scope            | No                       |
| REVERSED_INLET_T           | temperature_direction         | service_scope            | No                       |
| REVERSED_DUTY              | heat_direction                | service_scope            | No                       |
| TERMINAL_CROSSING          | terminal_temperature_crossing | service_scope            | No                       |
| UNBRACKETED_COLD           | enthalpy_target_not_bracketed | recovered_cold_outlet_PH | No                       |
| UNBRACKETED_HOT            | enthalpy_target_not_bracketed | recovered_hot_outlet_PH  | No                       |
| A_hot_inlet_PT             | pt_evaluation_failure         | hot_inlet_PT             | No                       |
| A_cold_inlet_PT            | pt_evaluation_failure         | cold_inlet_PT            | No                       |
| A_specified_hot_outlet_PT  | pt_evaluation_failure         | specified_hot_outlet_PT  | No                       |
| A_PH_INJECTED              | controlled_ph_failure         | recovered_cold_outlet_PH | No                       |
| B_hot_inlet_PT             | pt_evaluation_failure         | hot_inlet_PT             | No                       |
| B_cold_inlet_PT            | pt_evaluation_failure         | cold_inlet_PT            | No                       |
| B_specified_cold_outlet_PT | pt_evaluation_failure         | specified_cold_outlet_PT | No                       |
| B_PH_INJECTED              | controlled_ph_failure         | recovered_hot_outlet_PH  | No                       |
| AMBIGUOUS                  | multiple_ph_roots             | recovered_cold_outlet_PH | No                       |
| HOLE                       | pt_evaluation_failure         | recovered_cold_outlet_PH | No                       |
| FRESH_FINAL                | final_acceptance_failed       | recovered_cold_outlet_PH | No                       |
| PURE_COEXISTENCE_GAP       | ph_nonconvergence             | recovered_cold_outlet_PH | No                       |

## Maximum errors and governing cases

The following errors compare library enthalpy with independent direct equations, base inversion with independent equation/resolution/method checks, reciprocal recovery, or conservation identities. They are not production-exchanger errors. Every row passes its recorded governing-case allowance. `q0`/`q1` denote methane/n-hexane phase fractions (x for liquid, y for vapor). Full-precision per-case evidence is in the JSON.

| Quantity                   | Maximum absolute error | Allowance         | Governing case   |
| -------------------------- | ---------------------- | ----------------- | ---------------- |
| hot inlet H                | 5.45696821064e-12      | 1.10017820256e-06 | LIQUID_BOTH      |
| cold inlet H               | 1.09139364213e-11      | 1.25403750361e-06 | BUBBLE_ADJACENT  |
| specified-side outlet H    | 5.45696821064e-12      | 1.13309057823e-06 | DEW_ADJACENT     |
| recovered-side outlet T    | 6.36077857052e-11      | 2.98918535403e-07 | COLD_HEXANE_RICH |
| recovered-side outlet H    | 1.73367880052e-08      | 3.96282520096e-05 | DEW_ADJACENT     |
| recovered-side PH residual | 1.73604348674e-08      | 1e-06             | DEW_ADJACENT     |
| Q_hot                      | 4.28990460932e-08      | 0.00871345645954  | DEW_ADJACENT     |
| Q_cold                     | 1.71712599695e-09      | 0.00544950063115  | COLD_HEXANE_RICH |
| energy residual            | 1.09896063805e-07      | 0.0200739931266   | COLD_VL_TO_V     |
| reciprocal T recovery      | 8.50832293509e-10      | 2.36717901885e-05 | BUBBLE_ADJACENT  |
| reciprocal H recovery      | 5.02095645061e-08      | 0.00138726078836  | BUBBLE_ADJACENT  |
| reciprocal duty recovery   | 1.09896063805e-07      | 0.385348176305    | COLD_VL_TO_V     |

Complete field maxima, including applicable phase fractions, compositions, compressibility and phase enthalpy:

| Quantity                     | Maximum absolute error | Allowance         | Governing case   |
| ---------------------------- | ---------------------- | ----------------- | ---------------- |
| PH_residual                  | 1.73604348674e-08      | 1e-06             | DEW_ADJACENT     |
| Q_cold_direct                | 1.71712599695e-09      | 0.00544950063115  | COLD_HEXANE_RICH |
| Q_exchanged                  | 7.34871719033e-08      | 0.000200072201801 | BUBBLE_ADJACENT  |
| Q_hot_direct                 | 4.28990460932e-08      | 0.00871345645954  | DEW_ADJACENT     |
| cold.flow                    | 0                      | 0                 | CANONICAL        |
| cold_in.H_direct             | 1.09139364213e-11      | 1.25403750361e-06 | BUBBLE_ADJACENT  |
| cold_in.P                    | 0                      | 0                 | CANONICAL        |
| cold_in.liquid.H_direct      | 1.09139364213e-11      | 1.25403750361e-06 | BUBBLE_ADJACENT  |
| cold_in.vapor.H_direct       | 3.63797880709e-12      | 1.0609449212e-06  | COLD_HEXANE_RICH |
| cold_in.z0                   | 0                      | 0                 | CANONICAL        |
| cold_in.z1                   | 0                      | 0                 | CANONICAL        |
| cold_out.H_direct            | 9.09494701773e-12      | 7.2435442116e-05  | COLD_L_TO_VL     |
| cold_out.P                   | 0                      | 0                 | CANONICAL        |
| cold_out.liquid.H_direct     | 1.09139364213e-11      | 6.45398066105e-05 | COLD_L_TO_VL     |
| cold_out.vapor.H_direct      | 4.54747350886e-12      | 2.61864635802e-05 | COLD_HEXANE_RICH |
| cold_out.z0                  | 0                      | 0                 | CANONICAL        |
| cold_out.z1                  | 0                      | 0                 | CANONICAL        |
| energy_residual              | 1.09896063805e-07      | 0.0200739931266   | COLD_VL_TO_V     |
| hot.flow                     | 0                      | 0                 | CANONICAL        |
| hot_in.H_direct              | 5.45696821064e-12      | 1.10017820256e-06 | LIQUID_BOTH      |
| hot_in.P                     | 0                      | 0                 | CANONICAL        |
| hot_in.liquid.H_direct       | 5.45696821064e-12      | 1.10017820256e-06 | LIQUID_BOTH      |
| hot_in.vapor.H_direct        | 5.45696821064e-12      | 1.13331746547e-06 | DEW_ADJACENT     |
| hot_in.z0                    | 0                      | 0                 | CANONICAL        |
| hot_in.z1                    | 0                      | 0                 | CANONICAL        |
| hot_out.H_direct             | 5.45696821064e-12      | 1.13309057823e-06 | DEW_ADJACENT     |
| hot_out.P                    | 0                      | 0                 | CANONICAL        |
| hot_out.liquid.H_direct      | 1.81898940355e-12      | 1.09395060578e-06 | DEW_ADJACENT     |
| hot_out.vapor.H_direct       | 5.45696821064e-12      | 1.13314282362e-06 | DEW_ADJACENT     |
| hot_out.z0                   | 0                      | 0                 | CANONICAL        |
| hot_out.z1                   | 0                      | 0                 | CANONICAL        |
| reciprocal.Q_cold            | 0                      | 0.00422102866556  | CANONICAL        |
| reciprocal.Q_exchanged       | 0                      | 0.00422102866556  | CANONICAL        |
| reciprocal.Q_hot             | 1.09896063805e-07      | 0.385348176305    | COLD_VL_TO_V     |
| reciprocal.cold.H            | 0                      | 1.91039867601e-05 | CANONICAL        |
| reciprocal.cold.T            | 0                      | 5.51988887438e-07 | CANONICAL        |
| reciprocal.energy_residual   | 1.09896063805e-07      | 0.0202770522311   | COLD_VL_TO_V     |
| reciprocal.hot.H             | 5.02095645061e-08      | 0.00138726078836  | BUBBLE_ADJACENT  |
| reciprocal.hot.T             | 8.50832293509e-10      | 2.36717901885e-05 | BUBBLE_ADJACENT  |
| reciprocal_refined.H         | 1.73367880052e-08      | 3.96282520096e-05 | DEW_ADJACENT     |
| reciprocal_refined.T         | 5.92024207435e-11      | 5.03009747663e-06 | HOT_VL_TO_L      |
| reciprocal_refined.beta      | 1.55730983664e-12      | 5.46859573892e-09 | DEW_ADJACENT     |
| reciprocal_refined.liquid.H  | 1.65437086252e-08      | 3.77093985814e-05 | DEW_ADJACENT     |
| reciprocal_refined.liquid.Z  | 1.37556632751e-13      | 8.1931466835e-10  | DEW_ADJACENT     |
| reciprocal_refined.liquid.q0 | 3.28070903777e-14      | 3.94349153207e-09 | HOT_V_TO_VL      |
| reciprocal_refined.liquid.q1 | 3.27515792264e-14      | 3.94349153207e-09 | HOT_V_TO_VL      |
| reciprocal_refined.vapor.H   | 1.12268025987e-08      | 2.6018471392e-05  | DEW_ADJACENT     |
| reciprocal_refined.vapor.Z   | 3.33066907388e-13      | 1.63766563603e-09 | DEW_ADJACENT     |
| reciprocal_refined.vapor.q0  | 4.46642722807e-13      | 2.99456954032e-09 | DEW_ADJACENT     |
| reciprocal_refined.vapor.q1  | 4.46476189353e-13      | 2.99456954032e-09 | DEW_ADJACENT     |
| refined.H                    | 9.20590537135e-09      | 0.000913031572107 | COLD_VL_TO_V     |
| refined.T                    | 6.36077857052e-11      | 2.98918535403e-07 | COLD_HEXANE_RICH |
| refined.beta                 | 5.20347653854e-13      | 3.83792888591e-09 | BUBBLE_ADJACENT  |
| refined.liquid.H             | 4.77666617371e-09      | 2.58608818507e-05 | LIQUID_BOTH      |
| refined.liquid.Z             | 1.14130926931e-13      | 1.9067999142e-09  | LIQUID_BOTH      |
| refined.liquid.q0            | 2.60069743518e-13      | 2.91805293345e-09 | BUBBLE_ADJACENT  |
| refined.liquid.q1            | 2.59903210065e-13      | 2.91805293345e-09 | BUBBLE_ADJACENT  |
| refined.vapor.H              | 9.20590537135e-09      | 0.000913031572107 | COLD_VL_TO_V     |
| refined.vapor.Z              | 2.29372076888e-13      | 1.70795106881e-09 | BUBBLE_ADJACENT  |
| refined.vapor.q0             | 9.21485110439e-15      | 2.22638553649e-09 | COLD_L_TO_VL     |
| refined.vapor.q1             | 9.20444276353e-15      | 2.22638553648e-09 | COLD_L_TO_VL     |
| target_reconstruction        | 0                      | 4.80526401156e-11 | CANONICAL        |

The maximum energy residual is 1.09896063805e-07 W and maximum recovered PH residual across base, reciprocal and refinement solves is 1.73604348674e-08 J/mol, governed respectively by COLD_VL_TO_V and DEW_ADJACENT. The comparison count is 2002: 1,996 stored state/refinement/reciprocal/conservation comparisons plus six explicit flow-scaling comparisons. Structural, phase-identity and failure checks are additional, not inflated into this numerical count.

## Determinism and executed gates

Explicit `--write` generation succeeded. A subsequent fresh process using default verification reproduced the artifact byte-for-byte without rewriting it; the independent test process independently rebuilt and matched it again. The artifact contains no timestamps or machine-specific absolute paths. Source hashes cover new and inherited independent calculation helpers.

Twelve byte-identical call-order checks cover canonical and reciprocal calculations after clean start, another positive, a phase study, invalid input, injected PH failure and reciprocal-first ordering. The real PT oracle is reused across histories to expose hidden state dependence. All 11 human-review commands were executed automatically; they do not constitute human validation.

The new independent suite passed **116 tests**. Complete historical Python protection passed **414 tests**. All 22 separately executed historical gates passed unchanged:

| Historical gate                           | Actual result           |
| ----------------------------------------- | ----------------------- |
| independent_peng_robinson                 | 7 tests passed          |
| independent_peng_robinson_pt_boundary     | 28 tests passed         |
| independent_peng_robinson_pt_vapor_parent | 25 tests passed         |
| independent_peng_robinson_caloric         | 23 tests passed         |
| independent_peng_robinson_ph              | 55 tests passed         |
| independent_heater_cooler_energy          | 36 tests passed         |
| independent_peng_robinson_ps              | 46 tests passed         |
| independent_compressor_energy             | 66 tests passed         |
| production_peng_robinson                  | 122 comparisons passed  |
| production_peng_robinson_pt_boundary      | 325 comparisons passed  |
| production_peng_robinson_pt_vapor_parent  | 749 comparisons passed  |
| production_peng_robinson_caloric          | 1526 comparisons passed |
| production_peng_robinson_ph               | 401 comparisons passed  |
| production_heater_cooler_energy           | 1264 comparisons passed |
| production_peng_robinson_ps               | 270 comparisons passed  |
| production_compressor_energy              | 1083 comparisons passed |
| tests_pr_flash                            | 26 tests passed         |
| tests_pr_caloric                          | 35 tests passed         |
| tests_pr_ph_flash                         | 53 tests passed         |
| tests_heater_cooler_energy                | 36 tests passed         |
| tests_pr_ps_flash                         | 55 tests passed         |
| tests_compressor_energy                   | 75 tests passed         |

The unchanged M8.2 production comparator also passed its nine-grid high-accuracy scan: 1,152/1,152 successes and zero unexpected failures. M14 protection includes its 75 focused tests, canonical/service-scope/frozen comparison, result validation and fresh byte-identical production artifact verification. Hash protection preserves its contracts and numerical implementation.

Python syntax/compile, indentation, canonical deterministic JSON formatting, applicable Markdown checks, new/changed-line whitespace and `git diff --check` passed. Complete TypeScript/browser/build/smoke checks were not rerun: no application, contract or production file changed, and this independent benchmark has no application integration. Historical application files remain hash-identical. No unexecuted application check is claimed as passed.

## Future M15 recommendation — not implementation

Select **Scope A: single-phase inlet and outlet states only**, limited to the frozen matrix; expansion requires separate evidence. Both vapor and liquid examples exist; the six stable phase-change cases remain separate thermodynamic evidence. Their successful terminal recovery does not establish distributed phase-change exchanger design or authorize broader service.

Select **Option 2: both mutually exclusive temperature specification modes**, because both A -> B and B -> A reciprocal recovery pass. No duty-specified, simultaneous two-temperature, UA or effectiveness specification is recommended here.

A mandatory future contract/topology gate is required before production work. The current contracts expose distinct historical and PR single-stream heater/compressor branches, not a rigorous two-stream exchanger. M12 restricts its profile to one source, one heater, one sink and two material streams. The equipment registry has separate mixer and splitter port patterns, but no four-port exchanger identity. The generic scheduler passes inputs by target port and outputs by source port; this infrastructure alone does not authorize a new model, schema or side-specific material balances. Existing aggregate unit mass-balance handling is insufficient evidence of wall-separated composition propagation.

Recommend an additive, explicitly versioned `rigorous_two_stream_heat_exchanger@1.0` with `hot_in`, `cold_in`, `hot_out`, `cold_out` roles, two source identities and two sink identities. If current contracts/topology cannot express it, future M15 must STOP and request a separate minimal extension authorization. Do not bypass the gate with ad-hoc dictionaries or reinterpret an existing heater as an exchanger. The latest committed requirements/flowsheet/results versions are 1.6/1.7/1.8; this Pre-M15 task does not change or preauthorize their successors.

Inlets should continue owning flow, composition, temperature and pressure. Proposed equipment-owned fields are an explicit model/version, mutually exclusive hot- or cold-outlet-temperature mode, `hot_outlet_pressure_Pa_abs`, `cold_outlet_pressure_Pa_abs`, the selected outlet temperature, PR provider and explicit BIP provenance. Reuse the qualified M7 mass-to-molar conversion in future production; do not create an exchanger-specific molecular-weight model.

Proposed structured results should expose four caloric states; `F_hot_mol_s`, `F_cold_mol_s`; `Q_hot_W`, `Q_cold_W`, `Q_exchanged_W`; `energy_residual_W`; separate hot/cold material and composition residuals; specification mode; provider/BIP provenance; and compact recovered-side PH diagnostics (status, capability, PT profile, candidate count, selected/final bracket where available, iterations, evaluation count and final enthalpy residual). Do not flatten these into an opaque generic dictionary or add irrelevant PS fields.

Future Mode A should compose existing qualified PT/M10 at both inlets and hot outlet, the signed energy balance, cold PH/M11 and a fresh final state check. Mode B reverses the specified/recovered sides. Publish both material outlets only after all state, uniqueness, residual, side-specific conservation, pressure, direction and service checks pass. Failure at any mandatory stage fails the complete exchanger. A separate future `compare_production.py` and `production_comparison.json` should compare production against this committed independent truth; neither production artifact is created now.

## Limits

This is frozen methane/n-hexane, constant-zero-kij, bounded 200–500 K, equilibrium terminal-state energy qualification. It does not qualify water, arbitrary petroleum mixtures/nonzero BIPs, VLLE/three-phase behavior, critical regions, global root uniqueness, or interpolation across pure coexistence gaps. Accepted terminal states do not guarantee physical design feasibility.

No UA, U, area, LMTD, NTU/effectiveness, fouling/correction factors, pass count, shell-and-tube/plate geometry, exchanger sizing, distributed temperature profile, qualified design minimum approach, hydraulic pressure-drop correlation, environmental heat loss, shaft/electrical work, exergy/efficiency/entropy-minimization claim, dynamics, controls or network optimization is added. No production M15, M16 valve, M17 pump or other subsequent milestone is implemented.

## Protected files and exact changes

All 313 baseline tracked files were hashed before work. At automated qualification completion, 312 remained byte-identical and the only changed existing file is `docs/RIOGINEER_MASTER_CONTEXT.md`, minimally recording independent automated completion, then-pending human validation and production M15 not implemented. Historical M14 and earlier reports, tests, frozen JSON, code, contracts, dependencies and application files are unchanged.

New files:

- `PRE_MILESTONE_15_TWO_STREAM_HEAT_EXCHANGER_QUALIFICATION.md` — this qualification report.
- `benchmarks/two_stream_heat_exchanger/THIRD_PARTY_NOTICES.txt` — external attribution.
- `benchmarks/two_stream_heat_exchanger/requirements.txt` — independent environment pins.
- `benchmarks/two_stream_heat_exchanger/solver.py` — independent terminal-state experiment and rejection policy.
- `benchmarks/two_stream_heat_exchanger/reference.py` — matrix, audits, freeze/verify and review modes.
- `benchmarks/two_stream_heat_exchanger/test_reference.py` — independent acceptance tests.
- `benchmarks/two_stream_heat_exchanger/methane_nhexane_two_stream_hx_reference.json` — deterministic independent truth.

No temporary diagnostics, logs or bytecode are retained in the repository. Nothing is staged, committed or pushed.

## Frozen SHA-256

`533797cb1b26a8f3e597907ab9cc1e480353bd189280cfde273157cd3fa0e4b1`

## Tested repository-root commands

Freshly reproduce and verify the existing artifact without rewriting it:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --case summary
```

Explicit generation of this new reference, tested during qualification:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --write --case canonical
```

Independent test suite:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/two_stream_heat_exchanger -p 'test_*.py' -v
```

The following fast human-review commands read frozen evidence and verify source hashes. They do not rewrite truth or rerun the complete suite. Full fresh reproduction is the separate default command above. Each prints relevant engineering evidence and ends with PASS, counts and SHA-256. All commands below were tested automatically; the separate human review of eight modes is recorded above.

```sh
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case canonical
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case reciprocal
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case pressure
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case flow
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case composition
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case pure
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case phase
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case zero_duty
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case temperature_scope
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case negative
.local/pre-m8-venv/bin/python -B benchmarks/two_stream_heat_exchanger/reference.py --review --case summary
```

Independent Pre-M15 automated qualification: COMPLETE. Human-operated Pre-M15 validation: COMPLETE — 2026-09-30. Production M15: NOT IMPLEMENTED.
