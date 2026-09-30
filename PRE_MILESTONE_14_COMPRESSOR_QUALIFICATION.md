# Pre-Milestone 14 — Independent Peng–Robinson compressor qualification

**Automated independent qualification: COMPLETE — 2026-09-30.**

**Human-operated Pre-M14 validation: COMPLETE — 2026-09-30.**

No production M14 compressor was implemented. The existing M6 ideal-gas compressor remains a distinct historical capability.

## Objective, baseline and authority

Establish independent, reproducible numerical acceptance evidence for a future single-stage adiabatic PR compressor. Baseline: `94682d9d2bb499eea2d850d09831f553f694f01c` (`main`, completed M13). Before any file creation, the working tree was clean; HEAD, local origin/main and a read-only live remote query agreed. All 296 pre-existing tracked files were protected by SHA-256. No historical file is authorized to change.

Reference: `independent_methane_nhexane_compressor@1.0`, in `benchmarks/compressor_energy/methane_nhexane_compressor_reference.json`. SHA-256: `31972f6057f1c4191e25dc8fec317a0e21b20816d0a7c6513649fb7b630ed8cc`. After human review and commit, this exact frozen independent artifact is intended to become the numerical acceptance authority for future M14. Production must reproduce it within frozen allowances, never redefine it.

## Independence, provenance and thermodynamic methods

Reference generation imports only historical independent benchmark helpers. It does not import `engine/riogineer_engine`. The read-only production diagnostic is a separate script, run only after the independent JSON was generated. No production PT, PS, PH, H or S value seeds reference truth. Exact source hashes, component constants, Cp coefficients and reference conventions are frozen in JSON; benchmark-local requirements and third-party notices preserve the existing isolated environment. No production dependency was added.

| Package   | Version |
| --------- | ------- |
| chemicals | 1.5.2   |
| fluids    | 1.3.1   |
| numpy     | 2.2.6   |
| pandas    | 2.3.3   |
| scipy     | 1.15.3  |
| teqp      | 0.23.1  |
| thermo    | 0.6.0   |

Primary PT is Thermo `FlashVL.flash_TP_stability_test`, using PRMIX/PR with the already qualified PR coefficients (0.45724, 0.07780), explicit zero kij, `PT_SS_TOL=1e-26` and inherited stability tolerance. Every trial starts with stability testing; no prior-state warm start is used. Phase H/S come from Thermo. Independent direct ideal-gas integrals and PR departure equations audit the phase caloric values; no production equations are imported. Equilibrium H/S are molar phase-fraction-weighted values. The M10 reference convention is unchanged:

```json
{
  "P_ref_s_Pa_abs": 101325.0,
  "T_ref_h_K": 298.15,
  "T_ref_s_K": 298.15,
  "basis": "relative sensible; not third-law absolute; mixture includes ideal mixing entropy",
  "formation_included": false,
  "h_pure_ref_J_mol": [0.0, 0.0],
  "phase": "pure-component ideal gas",
  "s_pure_ref_J_mol_K": [0.0, 0.0]
}
```

Independent PS reuses committed Pre-M13: full 64-point 200–500 K scan, one candidate required, bisection, at most 100 iterations, 1e-10 K bracket tolerance and fresh absolute entropy residual <=1e-8 J/(mol K). A property hole or multiple candidates fails; a pure coexistence discontinuity cannot pass the fresh entropy gate.

Independent PH reuses committed Pre-M11: full 128-point 200–500 K scan, Brent root method, at most 100 iterations, 1e-10 K absolute root tolerance (1e-14 relative), and fresh absolute enthalpy residual <=1e-6 J/mol. Every positive compressor path has one candidate. Unsupported gaps fail the final residual rather than interpolating beta. JSON stores compact scans with hashes, brackets, candidate counts, iteration counts, root controls and fresh final residuals.

Method A is independent PT → PS → efficiency equation → PH. Method B reconstructs target H with `fsum([H2s/eta, H1*(1-1/eta)])`, efficiency and power from recovered stored states. A further cross-method calculation uses direct caloric equations, a tighter 1e-12 K PS bisection, and PH bisection instead of Brent. This is an equation/root cross-check sharing the independent PT library, not a claim of two unrelated thermodynamic libraries.

## Compressor convention and physical scope

Inputs are P1, T1, z, specified P2, eta and positive molar flow. Require `P2 > P1 > 0`, `0 < eta <= 1`, explicit constant zero kij, normalized nonnegative methane/n_hexane composition and every state inside 200–500 K. The ordered component IDs and 2×2 kij are global artifact metadata applying to every case. Pressure ratio is P2/P1, tabulated below.

`S2s = S1`; `H2_target = H1 + (H2s-H1)/eta`; actual state is independently recovered by PH(P2,H2_target,z). Reconstruct `eta=(H2s-H1)/(H2-H1)` and `eta_power=isentropic_fluid_power/fluid_power` from recovered PH H2. `fluid_power_W = molar_flow*(H2-H1)` is positive energy transferred **into the fluid**; `isentropic_fluid_power_W = molar_flow*(H2s-H1)`. H is J/mol, S is J/(mol K), flow is mol/s, power is W. Qdot=0, delta KE=0, delta PE=0. This is neither electrical motor power nor driver shaft input after mechanical losses.

No reaction or accumulation: total molar flow and overall composition are conserved. Phase compositions may change. Molecular weights are available in the frozen phase records for future unit conversion, but do not enter these molar equations. Initial equipment service is vapor-only at all three states; non-vapor calculation capability does not establish compressor design suitability.

## Positive matrix and canonical case

| Case           | P1 Pa  | T1 K           | P2/P1 | z methane | eta  | flow mol/s | T2s K          | T2 K           | power W        |
| -------------- | ------ | -------------- | ----- | --------- | ---- | ---------- | -------------- | -------------- | -------------- |
| CANONICAL      | 100000 | 300            | 3     | 0.9       | 0.8  | 100        | 362.1026370805 | 376.432590149  | 375283.3155876 |
| ETA_0.6        | 100000 | 300            | 3     | 0.9       | 0.6  | 100        | 362.1026370805 | 399.632816387  | 500377.7541168 |
| ETA_0.7        | 100000 | 300            | 3     | 0.9       | 0.7  | 100        | 362.1026370805 | 386.4773447103 | 428895.2178144 |
| ETA_0.75       | 100000 | 300            | 3     | 0.9       | 0.75 | 100        | 362.1026370805 | 381.139544208  | 400302.2032934 |
| ETA_0.85       | 100000 | 300            | 3     | 0.9       | 0.85 | 100        | 362.1026370805 | 372.250760463  | 353207.8264354 |
| ETA_0.9        | 100000 | 300            | 3     | 0.9       | 0.9  | 100        | 362.1026370805 | 368.5107388004 | 333585.1694112 |
| ETA_1.0        | 100000 | 300            | 3     | 0.9       | 1    | 100        | 362.1026370805 | 362.1026370805 | 300226.6524701 |
| RATIO_1.5      | 100000 | 300            | 1.5   | 0.9       | 0.8  | 100        | 322.2291574325 | 327.5849537778 | 130445.2477659 |
| RATIO_2.0      | 100000 | 300            | 2     | 0.9       | 0.8  | 100        | 338.50184364   | 347.6165383455 | 228657.4912913 |
| RATIO_5.0      | 100000 | 300            | 5     | 0.9       | 0.8  | 100        | 392.8836995982 | 413.617182619  | 574046.662737  |
| RATIO_8.0      | 100000 | 300            | 8     | 0.9       | 0.8  | 100        | 422.1880191214 | 448.6304991711 | 771141.3957599 |
| FLOW_1.0       | 100000 | 300            | 3     | 0.9       | 0.8  | 1          | 362.1026370805 | 376.432590149  | 3752.833155876 |
| FLOW_10.0      | 100000 | 300            | 3     | 0.9       | 0.8  | 10         | 362.1026370805 | 376.432590149  | 37528.33155876 |
| FLOW_200.0     | 100000 | 300            | 3     | 0.9       | 0.8  | 200        | 362.1026370805 | 376.432590149  | 750566.6311752 |
| BALANCED       | 100000 | 350            | 2     | 0.5       | 0.8  | 100        | 370.8580052426 | 375.6736546651 | 255052.8978264 |
| HEXANE_RICH    | 100000 | 360            | 2     | 0.3       | 0.8  | 100        | 377.0459051523 | 380.8913561399 | 258277.021619  |
| PURE_METHANE   | 100000 | 300            | 3     | 1         | 0.8  | 100        | 382.7579982417 | 401.9627372515 | 387717.0799001 |
| PURE_HEXANE    | 1000   | 300            | 2     | 0         | 0.8  | 100        | 312.0995845771 | 315.0620051251 | 220299.2875228 |
| BOUNDARY_VAPOR | 100000 | 322.4798988807 | 1.5   | 0.5       | 0.8  | 100        | 334.3963488609 | 337.1656963337 | 135668.6385523 |

There are 19 primary vapor cases, plus one separate thermodynamic-only VL study. Methane-rich 90/10, balanced 50/50, hexane-rich 30/70 and both pure endpoints are included. All selected pressure ratios (1.5, 2, 3, 5, 8) remain inside the temperature domain. This does not qualify every combination of these ranges.

| Canonical quantity       | Value              |
| ------------------------ | ------------------ |
| P1 Pa                    | 100000             |
| T1 K                     | 300                |
| P2 Pa                    | 300000             |
| P2/P1                    | 3                  |
| eta                      | 0.8                |
| flow mol/s               | 100                |
| H1 J/mol                 | 53.02312241561     |
| S1 J/(mol K)             | 3.02630436218      |
| T2s K                    | 362.1026370805     |
| H2s J/mol                | 3055.289647116     |
| H2 target J/mol          | 3805.856278291     |
| T2 K                     | 376.432590149      |
| H2 recovered J/mol       | 3805.856278291     |
| S2 J/(mol K)             | 5.058995619576     |
| isentropic fluid power W | 300226.6524701     |
| actual fluid power W     | 375283.3155876     |
| reconstructed eta        | 0.8                |
| eta from power           | 0.8                |
| energy residual W        | 2.273736754432e-11 |

All three canonical states are single vapor. P2>P1, H2>H2s>H1, S2>S1 and positive power are independently demonstrated, with no phase-boundary ambiguity.

## Efficiency, pressure ratio, flow and ideal limit

| eta  | T2s K          | H2s J/mol      | T2 K           | H2 J/mol       | fluid power W  |
| ---- | -------------- | -------------- | -------------- | -------------- | -------------- |
| 0.6  | 362.1026370805 | 3055.289647116 | 399.632816387  | 5056.800663583 | 500377.7541168 |
| 0.7  | 362.1026370805 | 3055.289647116 | 386.4773447103 | 4341.975300559 | 428895.2178144 |
| 0.75 | 362.1026370805 | 3055.289647116 | 381.139544208  | 4056.04515535  | 400302.2032934 |
| 0.8  | 362.1026370805 | 3055.289647116 | 376.432590149  | 3805.856278291 | 375283.3155876 |
| 0.85 | 362.1026370805 | 3055.289647116 | 372.250760463  | 3585.101386769 | 353207.8264354 |
| 0.9  | 362.1026370805 | 3055.289647116 | 368.5107388004 | 3388.874816527 | 333585.1694112 |
| 1    | 362.1026370805 | 3055.289647116 | 362.1026370805 | 3055.289647116 | 300226.6524701 |

The isentropic state is byte-identical across eta; actual H, T and power strictly decrease as eta increases. The 0.60 case establishes low-efficiency sensitivity without approaching zero.

| P2/P1 | P2 Pa  | T2s K          | H2s J/mol      | T2 K           | H2 J/mol       | power W        |
| ----- | ------ | -------------- | -------------- | -------------- | -------------- | -------------- |
| 1.5   | 150000 | 322.2291574325 | 1096.585104543 | 327.5849537778 | 1357.475600075 | 130445.2477659 |
| 2     | 200000 | 338.50184364   | 1882.283052746 | 347.6165383455 | 2339.598035329 | 228657.4912913 |
| 3     | 300000 | 362.1026370805 | 3055.289647116 | 376.432590149  | 3805.856278291 | 375283.3155876 |
| 5     | 500000 | 392.8836995982 | 4645.396424312 | 413.617182619  | 5793.489749786 | 574046.662737  |
| 8     | 800000 | 422.1880191214 | 6222.154288494 | 448.6304991711 | 7764.437080014 | 771141.3957599 |

Isentropic enthalpy rise, actual enthalpy rise and power increase across this fixed-inlet, eta=0.8 regular-vapor series. This is an observed matrix trend, not a global theorem across phase changes.

| flow mol/s | T2 K          | H2 J/mol       | power W        |
| ---------- | ------------- | -------------- | -------------- |
| 1          | 376.432590149 | 3805.856278291 | 3752.833155876 |
| 10         | 376.432590149 | 3805.856278291 | 37528.33155876 |
| 100        | 376.432590149 | 3805.856278291 | 375283.3155876 |
| 200        | 376.432590149 | 3805.856278291 | 750566.6311752 |

Inlet, PS and PH states, H2 target and solver diagnostics are byte-identical across flow. At 100 and 200 mol/s the doubling error is exactly 0 W (relative error 0). All four scaling errors are 0 W; roundoff allowances are recorded individually.

At eta=1, H2 target equals H2s exactly. Recovered deviations: T2−T2s = 0 K; H2−H2s = 0 J/mol; S2−S1 = 2.321698389096e-12 J/(mol K); power minus isentropic power = 0 W. These are within 1e-7 K, 1e-6 J/mol, 2e-8 J/(mol K) and propagated power allowance. Any signed entropy deviation here is numerical residual, not clipped.

## Phase behavior, boundary and entropy generation

| Case                  | inlet phase / beta             | isentropic phase / beta        | actual phase / beta            |
| --------------------- | ------------------------------ | ------------------------------ | ------------------------------ |
| CANONICAL             | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| ETA_0.6               | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| ETA_0.7               | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| ETA_0.75              | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| ETA_0.85              | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| ETA_0.9               | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| ETA_1.0               | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| RATIO_1.5             | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| RATIO_2.0             | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| RATIO_5.0             | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| RATIO_8.0             | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| FLOW_1.0              | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| FLOW_10.0             | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| FLOW_200.0            | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| BALANCED              | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| HEXANE_RICH           | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| PURE_METHANE          | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| PURE_HEXANE           | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| BOUNDARY_VAPOR        | single_vapor / 1               | single_vapor / 1               | single_vapor / 1               |
| VL_THERMODYNAMIC_ONLY | vapor_liquid / 0.5346425102238 | vapor_liquid / 0.5193454031402 | vapor_liquid / 0.5216771958027 |

BOUNDARY_VAPOR uses the independent 50/50 dew temperature at 100000 Pa plus 2 K: T1=322.4798988807 K. It approaches a relevant phase boundary without requiring critical-region qualification. Pure n-hexane is included at 1000→2000 Pa because inlet, PS and PH are vapor and remain inside 200–500 K; no coexistence gap is bridged.

The separate VL study uses 300 K, 300000→600000 Pa, z=[0.5,0.5], eta=0.8 and 100 mol/s. It remains vapor-liquid through all three states, with changing beta shown above. Both nested inversions pass the same residual and uniqueness gates. Conclusion **B: thermodynamic two-phase path is calculable, but initial compressor production service should remain vapor-only**. Liquid and VL service rejections are equipment-policy evidence, not a global rejection of those states by PR. Pump qualification belongs elsewhere.

Every irreversible primary vapor case has strictly positive S2−S1; the minimum is 0.8029786566465 J/(mol K), governed by RATIO_1.5. T2>=T2s and H2>H2s hold throughout the regular-vapor matrix. No negative entropy generation is hidden or clipped.

## Negative matrix and conservative failure semantics

| Case           | Expected category          | Failure stage | Synthetic | Accepted outlet |
| -------------- | -------------------------- | ------------- | --------- | --------------- |
| FLOW_0.0       | invalid_flow               | input         | No        | No              |
| FLOW_-1.0      | invalid_flow               | input         | No        | No              |
| FLOW_NaN       | invalid_flow               | input         | No        | No              |
| FLOW_Infinity  | invalid_flow               | input         | No        | No              |
| FLOW_-Infinity | invalid_flow               | input         | No        | No              |
| P1_0.0         | invalid_pressure           | input         | No        | No              |
| P1_-1.0        | invalid_pressure           | input         | No        | No              |
| P1_NaN         | invalid_pressure           | input         | No        | No              |
| P1_Infinity    | invalid_pressure           | input         | No        | No              |
| P1_-Infinity   | invalid_pressure           | input         | No        | No              |
| P2_0.0         | invalid_pressure           | input         | No        | No              |
| P2_-1.0        | invalid_pressure           | input         | No        | No              |
| P2_NaN         | invalid_pressure           | input         | No        | No              |
| P2_Infinity    | invalid_pressure           | input         | No        | No              |
| P2_-Infinity   | invalid_pressure           | input         | No        | No              |
| P2_100000.0    | invalid_pressure           | input         | No        | No              |
| P2_50000.0     | invalid_pressure           | input         | No        | No              |
| ETA_0.0        | invalid_efficiency         | input         | No        | No              |
| ETA_-0.1       | invalid_efficiency         | input         | No        | No              |
| ETA_1.01       | invalid_efficiency         | input         | No        | No              |
| ETA_NaN        | invalid_efficiency         | input         | No        | No              |
| ETA_Infinity   | invalid_efficiency         | input         | No        | No              |
| ETA_-Infinity  | invalid_efficiency         | input         | No        | No              |
| BAD_SUM        | invalid_composition        | input         | No        | No              |
| NEGATIVE_Z     | invalid_composition        | input         | No        | No              |
| NONFINITE_Z    | invalid_composition        | input         | No        | No              |
| WATER          | unsupported_components     | input         | No        | No              |
| UNKNOWN        | unsupported_components     | input         | No        | No              |
| NONZERO_KIJ    | unsupported_bip            | input         | No        | No              |
| T_LOW          | temperature_domain_invalid | input         | No        | No              |
| T_HIGH         | temperature_domain_invalid | input         | No        | No              |
| T_NAN          | temperature_domain_invalid | input         | No        | No              |
| LIQUID_SERVICE | compressor_state_invalid   | inlet         | No        | No              |
| VL_SERVICE     | compressor_state_invalid   | inlet         | No        | No              |
| PS_UNBRACKETED | ps_failure                 | isentropic    | No        | No              |
| PH_UNBRACKETED | ph_failure                 | actual_outlet | No        | No              |
| PT_INJECTED    | pt_failure                 | inlet         | Yes       | No              |
| PS_INJECTED    | ps_failure                 | isentropic    | Yes       | No              |
| PH_INJECTED    | ph_failure                 | actual_outlet | Yes       | No              |
| PS_GAP         | ps_failure                 | isentropic    | Yes       | No              |
| PH_GAP         | ph_failure                 | actual_outlet | Yes       | No              |
| PS_AMBIGUOUS   | ps_failure                 | isentropic    | Yes       | No              |
| PS_HOLE        | ps_failure                 | isentropic    | Yes       | No              |

All 43 failures publish no accepted inlet/isentropic/outlet/power payload. Diagnostic solver failure records are separate. Nonfinite inputs are JSON-safe string tokens decoded only during execution. Efficiencies are never clamped. Equal/lower P2 is not compression; zero flow is not accepted. Natural PS_UNBRACKETED (T1=490 K, P2/P1=8) and PH_UNBRACKETED (eta=0.1, P2/P1=8) fail within the bounded domain; no extrapolation or ideal-gas fallback is used.

PT_INJECTED, PS_INJECTED and PH_INJECTED deliberately exercise failure propagation. PS_GAP/PH_GAP inject a genuine pure n-hexane saturation-gap target at 1000 Pa into the nested independent solver: the target is the mean of separately evaluated saturation-adjacent phase values at ±1e-5 K. These are synthetic compressor-stage injections, not natural vapor-compressor paths. Actual solvers reject the gap. PS_AMBIGUOUS and PS_HOLE use explicitly synthetic entropy oracles to prove rejection of multiple candidates and incomplete property scans.

## Tolerances, conditioning and energy closure

Base comparison scales come from unchanged Pre-M13/Pre-M11: temperature 1e-7 K; equilibrium/phase H 1e-6 + 1e-11|H| J/mol; S 1e-8 + 1e-11|S| J/(mol K); beta/composition 2e-9 (an envelope of historical 1e-9 absolute + 1e-9 relative on fractions); Z 2e-10 + 1e-9|Z|. Fresh inversion gates remain separately fixed at 1e-8 S and 1e-6 H.

For each case, centered ±0.001 K independent PT differences record local dH/dT, dS/dT and phase-property slopes without crossing phases. Let a1S,a1H be inlet allowances. Isentropic temperature propagation is `eTs = 4*(a1S+1e-8)/(dS/dT at 2s)+1e-7`; each state-property allowance is its base plus `|dproperty/dT|*eT`. Then `aTarget=a1H+(a2sH+a1H)/eta`, and `eT2=4*(aTarget+1e-6)/(dH/dT at 2)+1e-7`. The factor four reserves a conservative local sensitivity margin; this is a finite-matrix error budget, not a proof outside these neighborhoods. All numerical allowances were generated from independent states before the production diagnostic.

Power allowance is `flow*(a2H+a1H)+roundoff`; isentropic power uses `flow*(a2sH+a1H)`. Efficiency comparison propagates numerator/denominator uncertainty: `(a2sH+a1H+eta*(a2H+a1H))/deltaHactual`. Independent efficiency identity uses the much tighter fresh PH budget `eta*1e-6/|deltaHactual|+64*epsilon`. Energy closure is independently summed as `fsum([power, flow*H1, -flow*H2])`, with `64*epsilon*max(1, |power|, |flow*H1|, |flow*H2|)` W; flow scaling uses this same arithmetic bound. Overall flow and composition conservation use exact zero allowance. No universal tolerance substitutes for these distinct scales.

The VL thermodynamic-only study governs the largest production H and power differences; among all diagnostic fields the largest error/allowance ratio is 0.008947974750782 for RATIO_5.0 / energy_residual. Independent final entropy residual is governed by BOUNDARY_VAPOR. Thus boundary proximity and phase splitting are reported separately from regular-vapor compressor service. Within the primary vapor matrix, the largest normalized diagnostic error is 0.01051011837419 of allowance for FLOW_10.0 / energy_residual; this is arithmetic energy closure, not a loss of thermodynamic convergence.

## Maximum independent errors and allowances

Every listed maximum has its governing case and its own allowance. Cross-method T/H/S, beta, composition and Z rows compare direct caloric/alternative-root results to primary library results. Identity rows compare reconstructed quantities and residuals. Tables retain maxima, not averages.

| Quantity             | Maximum absolute error | Allowance at governing case | Governing case        |
| -------------------- | ---------------------- | --------------------------- | --------------------- |
| H1_direct            | 6.36646291241e-12      | 1.072052130086e-06          | HEXANE_RICH           |
| H2_direct            | 2.273736754432e-12     | 1.040560451553e-06          | ETA_0.75              |
| H2_recovered         | 1.382431946695e-10     | 1e-06                       | VL_THERMODYNAMIC_ONLY |
| H2_target            | 9.094947017729e-13     | 7.186145955392e-11          | ETA_0.6               |
| H2s_direct           | 9.094947017729e-12     | 1.132992559334e-06          | VL_THERMODYNAMIC_ONLY |
| S1_direct            | 5.684341886081e-14     | 1.045191532629e-08          | VL_THERMODYNAMIC_ONLY |
| S2_direct            | 5.107025913276e-14     | 1.002265678572e-08          | PURE_METHANE          |
| S2s_direct           | 8.171241461241e-14     | 1.027309792845e-08          | HEXANE_RICH           |
| S2s_residual         | 9.496403663434e-12     | 1e-08                       | BOUNDARY_VAPOR        |
| energy_residual      | 1.455191522837e-10     | 2.022537159765e-08          | VL_THERMODYNAMIC_ONLY |
| eta                  | 9.514611321038e-14     | 6.859116813092e-10          | VL_THERMODYNAMIC_ONLY |
| eta_power            | 9.503509090791e-14     | 6.859116813092e-10          | VL_THERMODYNAMIC_ONLY |
| fluid_power          | 1.455191522837e-10     | 2.022537159765e-08          | VL_THERMODYNAMIC_ONLY |
| ideal_H              | 0                      | 1e-06                       | ETA_1.0               |
| ideal_S              | 2.321698389096e-12     | 2e-08                       | ETA_1.0               |
| ideal_T              | 0                      | 1e-07                       | ETA_1.0               |
| inlet.H              | 0                      | 1.000530231224e-06          | CANONICAL             |
| inlet.S              | 0                      | 1.003026304362e-08          | CANONICAL             |
| inlet.T              | 0                      | 1e-07                       | CANONICAL             |
| inlet.beta           | 0                      | 2e-09                       | CANONICAL             |
| inlet.liquid.H       | 0                      | 1.305758188227e-06          | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.S       | 0                      | 1.089452690349e-08          | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.Z       | 0                      | 2.154696638024e-10          | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.q0      | 0                      | 2e-09                       | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.q1      | 0                      | 2e-09                       | VL_THERMODYNAMIC_ONLY |
| inlet.vapor.H        | 0                      | 1.000530231224e-06          | CANONICAL             |
| inlet.vapor.S        | 0                      | 1.003026304362e-08          | CANONICAL             |
| inlet.vapor.Z        | 0                      | 1.195629000384e-09          | CANONICAL             |
| inlet.vapor.q0       | 0                      | 2e-09                       | CANONICAL             |
| inlet.vapor.q1       | 0                      | 2e-09                       | CANONICAL             |
| isentropic.H         | 3.180957719451e-09     | 3.772496713316e-05          | BOUNDARY_VAPOR        |
| isentropic.S         | 9.515943588667e-12     | 1.198573859948e-07          | BOUNDARY_VAPOR        |
| isentropic.T         | 3.410605131648e-11     | 9.67988565265e-07           | PURE_METHANE          |
| isentropic.beta      | 8.215650382226e-15     | 2.403281947801e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.H  | 1.007720129564e-09     | 4.97738219806e-05           | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.S  | 3.296918293927e-12     | 1.680714965554e-07          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.Z  | 2.706168622524e-16     | 2.435506169015e-10          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.q0 | 1.144917494145e-15     | 2.058319318585e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.q1 | 1.110223024625e-15     | 2.058319318577e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.vapor.H   | 3.180957719451e-09     | 3.772496713316e-05          | BOUNDARY_VAPOR        |
| isentropic.vapor.S   | 9.515943588667e-12     | 1.198573859948e-07          | BOUNDARY_VAPOR        |
| isentropic.vapor.Z   | 6.550315845288e-15     | 1.256548810397e-09          | HEXANE_RICH           |
| isentropic.vapor.q0  | 1.321165399304e-14     | 2.649255450019e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.vapor.q1  | 1.329492071989e-14     | 2.649255450032e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic_power     | 1.164153218269e-10     | 1.103392872894e-08          | RATIO_8.0             |
| molar_flow           | 0                      | 0                           | CANONICAL             |
| outlet.H             | 4.070898285136e-09     | 0.0002330929729968          | BALANCED              |
| outlet.S             | 1.086419842977e-11     | 7.545012950553e-07          | PURE_HEXANE           |
| outlet.T             | 4.058620106662e-11     | 4.877233291065e-06          | PURE_METHANE          |
| outlet.beta          | 9.547918011776e-15     | 4.448777439052e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.H      | 1.084117684513e-09     | 0.000282826833475           | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.S      | 3.481659405224e-12     | 9.192568870808e-07          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.Z      | 2.914335439641e-16     | 3.067453538594e-10          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.q0     | 1.318389841742e-15     | 2.334235820512e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.q1     | 1.443289932013e-15     | 2.334235820528e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.vapor.H       | 4.070898285136e-09     | 0.0002330929729968          | BALANCED              |
| outlet.vapor.S       | 1.086419842977e-11     | 7.545012950553e-07          | PURE_HEXANE           |
| outlet.vapor.Z       | 7.216449660064e-15     | 1.591141138703e-09          | BOUNDARY_VAPOR        |
| outlet.vapor.q0      | 1.543210004229e-14     | 5.928499704048e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.vapor.q1      | 1.530719995202e-14     | 5.92849970409e-09           | VL_THERMODYNAMIC_ONLY |
| power_identity       | 1.385342329741e-08     | 0.0001000202253716          | VL_THERMODYNAMIC_ONLY |
| z0                   | 0                      | 0                           | CANONICAL             |
| z1                   | 0                      | 0                           | CANONICAL             |

| Flow-scaling case | Absolute error W   | Relative error     | Allowance W        |
| ----------------- | ------------------ | ------------------ | ------------------ |
| FLOW_1.0          | 4.547473508865e-13 | 1.211744119705e-16 | 5.408447063774e-11 |
| FLOW_10.0         | 7.275957614183e-12 | 1.938790591527e-16 | 5.408447063774e-10 |
| CANONICAL         | 0                  | 0                  | 5.408447063774e-09 |
| FLOW_200.0        | 0                  | 0                  | 1.081689412755e-08 |

## Read-only production thermodynamic diagnostic

`compare_forward.py` calls existing production PT/M10 → PS(P2,S1_prod) → efficiency equation → PH(P2,Htarget_prod), with high_accuracy nested PT, and compares against the already frozen independent states. It is not a registered production compressor, process model, dispatcher or contract. All 20 paths (19 vapor plus separate VL) pass all 715 diagnostic numerical comparisons and phase checks. One qualified candidate and a fresh final trial are required for both inversions.

| Quantity             | Maximum absolute error | Allowance at governing case | Governing case        |
| -------------------- | ---------------------- | --------------------------- | --------------------- |
| H2_target            | 4.311004886404e-10     | 5.527498984166e-05          | VL_THERMODYNAMIC_ONLY |
| PH_residual          | 1.091393642128e-10     | 1e-06                       | VL_THERMODYNAMIC_ONLY |
| PS_residual          | 9.432454817215e-12     | 1e-08                       | BOUNDARY_VAPOR        |
| energy_residual      | 7.366907084361e-11     | 8.233044112822e-09          | RATIO_5.0             |
| eta                  | 1.696420781627e-13     | 2.039389068296e-07          | VL_THERMODYNAMIC_ONLY |
| eta_power            | 1.696420781627e-13     | 2.039389068296e-07          | VL_THERMODYNAMIC_ONLY |
| fluid_power          | 9.385985322297e-08     | 0.02431990111629            | VL_THERMODYNAMIC_ONLY |
| inlet.H              | 2.601154847071e-10     | 1.142323399985e-06          | VL_THERMODYNAMIC_ONLY |
| inlet.S              | 9.663381206337e-13     | 1.045191532629e-08          | VL_THERMODYNAMIC_ONLY |
| inlet.T              | 0                      | 1e-07                       | CANONICAL             |
| inlet.beta           | 8.437694987151e-15     | 2e-09                       | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.H       | 7.275957614183e-12     | 1.305758188227e-06          | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.S       | 1.136868377216e-13     | 1.089452690349e-08          | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.Z       | 3.469446951954e-18     | 2.154696638024e-10          | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.q0      | 3.122502256758e-17     | 2e-09                       | VL_THERMODYNAMIC_ONLY |
| inlet.liquid.q1      | 0                      | 2e-09                       | VL_THERMODYNAMIC_ONLY |
| inlet.vapor.H        | 6.36646291241e-12      | 1.072052130086e-06          | HEXANE_RICH           |
| inlet.vapor.S        | 3.987921104454e-13     | 1.006666236085e-08          | VL_THERMODYNAMIC_ONLY |
| inlet.vapor.Z        | 1.33226762955e-15      | 1.188502784824e-09          | VL_THERMODYNAMIC_ONLY |
| inlet.vapor.q0       | 1.854072451124e-14     | 2e-09                       | VL_THERMODYNAMIC_ONLY |
| inlet.vapor.q1       | 1.856848008686e-14     | 2e-09                       | VL_THERMODYNAMIC_ONLY |
| isentropic.H         | 2.928572939709e-10     | 4.216380975335e-05          | VL_THERMODYNAMIC_ONLY |
| isentropic.S         | 9.734435479913e-13     | 1.423554731043e-07          | VL_THERMODYNAMIC_ONLY |
| isentropic.T         | 0                      | 7.600849035591e-07          | CANONICAL             |
| isentropic.beta      | 9.769962616701e-15     | 2.403281947801e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.H  | 1.455191522837e-11     | 4.97738219806e-05           | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.S  | 2.84217094304e-14      | 1.680714965554e-07          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.Z  | 2.081668171172e-17     | 2.435506169015e-10          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.q0 | 8.014422459013e-16     | 2.058319318585e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.liquid.q1 | 7.771561172376e-16     | 2.058319318577e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.vapor.H   | 1.045918907039e-11     | 1.299449529585e-05          | VL_THERMODYNAMIC_ONLY |
| isentropic.vapor.S   | 5.844214001627e-13     | 6.381772439022e-08          | VL_THERMODYNAMIC_ONLY |
| isentropic.vapor.Z   | 3.10862446895e-15      | 1.21201735064e-09           | VL_THERMODYNAMIC_ONLY |
| isentropic.vapor.q0  | 2.48689957516e-14      | 2.649255450019e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic.vapor.q1  | 2.477185123695e-14     | 2.649255450032e-09          | VL_THERMODYNAMIC_ONLY |
| isentropic_power     | 5.529727786779e-08     | 0.004330613315334           | VL_THERMODYNAMIC_ONLY |
| outlet.H             | 6.784830475226e-10     | 0.0002420564855092          | VL_THERMODYNAMIC_ONLY |
| outlet.S             | 2.010835942201e-12     | 7.812781871071e-07          | VL_THERMODYNAMIC_ONLY |
| outlet.T             | 1.762145984685e-12     | 3.704122150946e-06          | RATIO_1.5             |
| outlet.beta          | 2.597921877623e-14     | 4.448777439052e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.H      | 1.164153218269e-10     | 0.000282826833475           | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.S      | 4.831690603169e-13     | 9.192568870808e-07          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.Z      | 3.816391647149e-17     | 3.067453538594e-10          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.q0     | 3.122502256758e-17     | 2.334235820512e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.liquid.q1     | 1.110223024625e-16     | 2.334235820528e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.vapor.H       | 8.549250196666e-11     | 0.0001773064159102          | RATIO_1.5             |
| outlet.vapor.S       | 8.046896482483e-13     | 3.266057006479e-07          | VL_THERMODYNAMIC_ONLY |
| outlet.vapor.Z       | 4.884981308351e-15     | 1.378741461568e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.vapor.q0      | 3.652633751017e-14     | 5.928499704048e-09          | VL_THERMODYNAMIC_ONLY |
| outlet.vapor.q1      | 3.69426711444e-14      | 5.92849970409e-09           | VL_THERMODYNAMIC_ONLY |

## Determinism, tests and reproduction

All 66 independent tests passed. They include every negative case separately, fresh PT residual checks, ideal limit, sensitivity/flow/phase checks, source-isolation/provenance checks, and deliberate corrupt-outlet/corrupt-power detection. The frozen reference contains 918 independent numerical checks, plus exact reproducibility, phase, monotonicity and call-order assertions. Full JSON verification is byte-identical, with zero allowance for serialization differences.

Eighteen call-order checks exercise three representative regimes (canonical, balanced vapor and VL study) with a shared independent oracle after another positive, low efficiency, eta=1, invalid input, injected PS failure and injected PH failure. Each complete result, including controls, candidate counts, residuals and diagnostics, is byte-identical to its isolated calculation. All ten review CLI modes and the default verification were exercised in separate fresh processes and verified identical bytes; normal verification never writes the artifact.

## Historical regression protection

Historical results are recorded from unchanged commands and evidence. The complete Python suite passed **339 tests** unchanged. The first sandboxed run executed 337 tests but could not initialize the HTTP fixture because localhost binding was denied; the full unchanged suite was then rerun with local-server permission and passed all 339 tests. This was an execution-permission issue, not a numerical regression.

| Independent historical suite | Tests passed |
| ---------------------------- | ------------ |
| Pre-M8                       | 7            |
| Pre-M8.1                     | 28           |
| Pre-M8.2                     | 25           |
| Pre-M10                      | 23           |
| Pre-M11                      | 55           |
| Pre-M12                      | 36           |
| Pre-M13                      | 46           |

| Production protection | Executed result                                                               |
| --------------------- | ----------------------------------------------------------------------------- |
| M8                    | 122 field comparisons                                                         |
| M8.1                  | 325 comparisons; both precision profiles                                      |
| M8.2                  | 749 comparisons plus complete high_accuracy scan: 1152/1152 across nine grids |
| M10                   | 1526 comparisons                                                              |
| M11                   | 29 positive; 9 negative/gap; 401 field comparisons                            |
| M12                   | 14 positive; 15 negative; 1264 comparisons                                    |
| M13                   | 15 positive; 17 negative; 270 field comparisons; determinism/call order       |

Separate focused production suites passed unchanged: PT 26 tests, M10 caloric 35, M11 PH 53, M12 Heater/Cooler 36 and M13 PS 55. M13 liquid, two_phase, vapor, bubble, dew, pure, negative and summary views are exercised by automated commands; this is not human validation. The historical M8.1 standard-profile caloric diagnostic retains its known non-gating failure; the qualified high_accuracy comparison passes. Old comparator prose describing later milestones as pending is historical output, not the current repository status.

TypeScript, browser and build suites were not required for independent benchmark-only qualification because all pre-existing application files remained unchanged. They were not executed and are not reported as passing. No contract generation or unrelated formatting was run.

## Existing equipment and future M14 recommendation

Read-only inspection found an operational M6 `ideal_gas_isentropic_efficiency@1.0` compressor in `engine/riogineer_engine/network_models.py`, not a PR placeholder. It takes discharge pressure, specified Cp/k, isentropic and mechanical efficiencies and an assumed gas inlet. It computes ideal-gas temperatures and distinguishes gas/process power from shaft power/mechanical loss. This capability and its contracts remain unchanged.

Future M14 should compose the qualified production PT/M10, PS/M13 and PH/M11 primitives, not copy the independent benchmark solver. Validate inputs and vapor-service scope; calculate H1/S1; call PS(P2,S1); calculate Htarget; call PH(P2,Htarget); reconstruct efficiency, power, material balance and energy closure; publish an outlet only after every gate passes. No case-ID-specific equations, hard-coded benchmark pressures, temperatures or compositions should enter production.

Minimum recommended inputs: specified outlet pressure, isentropic efficiency, PR property-package/model identity and explicit BIP/provenance; inlet stream supplies flow, composition, P and T/state. Mass-based stream conversion belongs to the existing production molecular-weight layer. Recommended result: all three equilibrium states, H1/S1/H2s/H2, target and recovered enthalpy rises, specified/reconstructed efficiency, fluid and isentropic power, energy/material residuals, and nested PS/PH statuses, candidate counts, brackets and residuals for traceability. Public UI need not expose all solver internals.

Current strict compressor input/result schemas in `src/lib/digital-engineer/contracts.ts` encode only the ideal-gas model and Cp/k/mechanical-efficiency payload. A separately discriminated PR compressor model and corresponding result/version extension would likely be needed for PR/BIP provenance, caloric states and nested diagnostics. Do not reinterpret the historical Cp/k model. **Future M14 must stop for explicit authorization before modifying protected contracts**, under the M12 contract-change discipline. This report recommends the extension; it does not implement or authorize it.

Future failure propagation should retain explicit input, service, inlet PT, isentropic PS, actual PH and closure stages. Reject unsupported inlet/final phases, ambiguity, property holes, coexistence gaps, invalid H2s/target, out-of-domain states and residual failures. Do not expose partial states as accepted outlets. Initial service recommendation is single-vapor only; liquid pressure increase is pump work and pressure reduction is valve work.

## Integrity, files and limitations

New files only: this report; `benchmarks/compressor_energy/reference.py`, `solver.py`, `test_reference.py`, `compare_forward.py`, `methane_nhexane_compressor_reference.json`, `requirements.txt`, and `THIRD_PARTY_NOTICES.txt`. Historical milestone reports and Master Context were not edited. All source/artifact changes remain untracked; nothing staged, committed or pushed. All 296 protected tracked files remain SHA-256-identical. Python AST/syntax/in-memory compile and indentation checks passed for all four new Python modules. Deterministic JSON formatting, report Prettier formatting, new-file whitespace/final-newline checks and `git diff --check` passed. No historical file or frozen evidence was reformatted. Temporary execution logs and the protected-file hash inventory are outside the repository under `/tmp`.

Qualification is limited to the finite methane/n-hexane pure/binary matrix, constant zero kij, inherited caloric convention, bounded 200–500 K and one adiabatic stage with specified P2/eta. Finite scans establish observed candidates, not mathematical global uniqueness. The separate VL study is algorithm evidence outside initial compressor service. No water, arbitrary petroleum mixtures/nonzero BIPs, VLLE, three-phase/reaction equilibrium, critical-region or general retrograde qualification, or pure-coexistence interpolation is claimed.

No mechanical heat loss, polytropic head/efficiency, compressor sizing/maps, surge/choke/stonewall, speed curves, empirical efficiency prediction, stages/intercooling, recycle/anti-surge, driver/electrical/gearbox/mechanical efficiency or external pressure-drop/hydraulic model is included. No network execution, flowsheet dispatch, stream table, process result, frontend or PFD change is implemented. Production M14, pump, turbine and valve work have not begun.

## Human-operated validation — 2026-09-30

The human reviewer reported successful completion on 2026-09-30, separately from the automated qualification recorded above. The `canonical`, `efficiency`, `pressure`, `flow`, `ideal`, `pure`, `boundary`, `negative` and `summary` modes were executed and inspected. The reviewed results were consistent with automated Pre-M14 qualification.

The final summary confirmed 19 vapor positive cases, 1 separate vapor-liquid thermodynamic study, 43 negative cases, 918 independent numerical checks and 18 byte-identical call-order checks. The reviewed frozen reference SHA-256 was `31972f6057f1c4191e25dc8fec317a0e21b20816d0a7c6513649fb7b630ed8cc`.

Human review confirmed:

- Physically consistent canonical compressor behavior; lower isentropic efficiency increases actual outlet enthalpy, temperature and fluid power.
- Increasing pressure ratio increases required compression work over the reviewed qualified cases; eta=1 reproduces the isentropic state.
- Fluid power scales linearly with molar flow. Scaling error was zero for the canonical and doubled-flow cases; other reported scaling residuals were negligible and within allowance.
- Consistent pure methane and pure n-hexane vapor behavior; the qualified boundary-vapor case remains vapor throughout the calculation.
- All reviewed negative cases reject the calculation without publishing an accepted outlet. Liquid and vapor-liquid inlets remain rejected as compressor service.
- The separate VL case remains a thermodynamic study only and does not authorize VL compressor service.

All reported maximum numerical errors were within their recorded allowances. This human validation record preserves the existing qualified scope, numerical evidence, tolerances and limitations. Production M14 compressor has not been implemented.

## Repository-root verification and human-review commands

Use the existing isolated environment. The default and every view compute the full independent matrix and verify frozen bytes without rewriting. `--write` is the explicit regeneration operation used to create this new evidence; once committed as authority, any truth change requires separate requalification authorization. The human-operated modes actually reviewed are recorded separately above; the commands below remain available for reproduction, including the additional `phases` view.

```sh
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --write
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/compressor_energy -p test_reference.py -v
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_forward.py
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_forward.py --json
```

```sh
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case canonical
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case efficiency
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case pressure
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case flow
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case ideal
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case pure
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case boundary
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case phases
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case negative
.local/pre-m8-venv/bin/python -B benchmarks/compressor_energy/reference.py --case summary
```

Historical independent protections used the following command for each directory listed above:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p "test_*.py" -q
```

The same executed command applies with directories `peng_robinson_pt_boundary`, `peng_robinson_pt_vapor_parent`, `peng_robinson_caloric`, `peng_robinson_ph`, `heater_cooler_energy`, and `peng_robinson_ps`. Production comparator commands:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case all
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case summary
engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case summary
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -q
git diff --check
```

**Independent Pre-Milestone 14 Compressor qualification completed. Production M14 compressor has not been implemented.**
