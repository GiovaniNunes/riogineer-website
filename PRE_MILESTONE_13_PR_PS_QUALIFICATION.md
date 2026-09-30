# Pre-Milestone 13 — Independent Peng–Robinson PS qualification

## Objective, baseline and independence

Create frozen acceptance evidence for a future `PS(P, S_target, z) -> T, equilibrium state, H_eq`. Production PS remains unimplemented. This study does not qualify a compressor, turbine, equipment model or public contract. Human-operated Pre-M13 validation has not been performed or recorded.

Baseline: clean `main`, commit `4f6023621022f449e0c4761e56f1929e7859d4a2`. SHA-256 hashes protected all 282 pre-existing tracked files before creating this benchmark. No existing tracked file is authorized to change.

The new `benchmarks/peng_robinson_ps/` code imports only independent historical benchmark helpers and third-party libraries. `equilibrium.py` extends the unchanged Pre-M11 independent PT/caloric evaluator; `solver.py` implements benchmark-only bounded bisection. Neither imports production thermodynamics or a production PS solver. Forward library PT/entropy defines targets; production values never define truth. `compare_forward.py` is a separate read-only production PT/caloric diagnostic and is not imported by the reference generator.

The historical Pre-M10 helper configures Thermo PR coefficients to canonical 0.45724/0.07780, retains library roots/stability/caloric implementations, and cross-checks them against separate direct equations. Pre-M10 matched binary/pure phase H/S are explicitly checked unchanged. Source hashes, constants, Cp records, reference convention and versions are frozen in JSON.

## Thermodynamic scope and convention

Ordered components are methane/n_hexane, with explicit constant zero 2×2 kij. Pure feeds use [1,0] or [0,1]. The positive matrix contains equimolar binary states plus one [0.3,0.7] case. These sampled compositions do not qualify every possible mixture proportion.

The independently examined inversion domain is **200–500 K**. It lies within the joint Cp validity domain and was evaluated completely on 64-, 128- and 256-point scans for every positive case. No sampled holes or entropy reversals occurred at the primary independent PT accuracy. This supports these finite grids and frozen targets, not blanket qualification of every T/P/z in the rectangular domain.

Pressure matrix, Pa absolute: **1000, 100000, 101325, 300000, 1000000, 6000000, 30000000**. It covers dilute vapor, intermediate/VL, the inherited 6 MPa binary boundaries, and high-pressure liquid. No blanket pressure qualification is claimed.

Water, other components, nonzero or temperature-dependent BIPs, VLLE, three-phase/reactive systems, critical-region and general retrograde behavior are excluded. No deliberately near-critical case was added. Pure methane subcritical coexistence is outside the chosen domain; pure n-hexane coexistence interpolation remains excluded.

The M10 convention is preserved exactly: pure ideal-gas h=s=0 at T_ref=298.15 K, P_ref=101325 Pa, with sensible relative properties. Formation offsets and third-law absolute entropy are absent. Real phases need not have zero entropy at those conditions; ideal composition mixing remains included.

## Equations and independent verification

For phase composition q and Cp/R polynomial coefficients c_ij:

```text
Cp_i/R = sum(j=0..4, c_ij T^j)
h_i,ig = R sum(j=0..4, c_ij (T^(j+1)-Tref^(j+1))/(j+1))
s_i,T = R [c_i0 ln(T/Tref) + sum(j=1..4, c_ij (T^j-Tref^j)/j)]
s_ig = sum(q_i s_i,T) - R ln(P/Pref) - R sum(q_i ln(q_i))
L = ln[(Z+(1+sqrt(2))B)/(Z+(1-sqrt(2))B)]
h_res = RT(Z-1) + (T da/dT-a)L/(2 sqrt(2)b)
s_res = R ln(Z-B) + (da/dT)L/(2 sqrt(2)b)
h = h_ig+h_res; s = s_ig+s_res
S_eq = (1-beta)S_L + beta S_V
H_eq = (1-beta)H_L + beta H_V
```

R=8.31446261815324 J/(mol K). The analytic Soave alpha and quadratic mixing derivative are inherited from independent Pre-M10, with dkij/dT=0. Zero mole fractions use the continuous q ln(q)=0 limit. Each phase uses its own equilibrium composition/root; no extra macroscopic phase-mixing entropy is added.

Every scan, root and final PT evaluation independently compares library ideal/residual/total H/S against direct equations, then compares phase-weighted equilibrium entropy. Final states also retain residual Gibbs/fugacity and fixed-P, fixed-composition derivative identities. Pre-M10 Cp/T quadrature and frozen reproduction are rerun unchanged. Enthalpy never drives the PS residual.

## Independent environment and provenance

Existing `.local/pre-m8-venv` only; no package installation or environment changes. Python 3.10.10; Thermo 0.6.0, Chemicals 1.5.2, Fluids 1.3.1, NumPy 2.2.6, SciPy 1.15.3, Pandas 2.3.3. teqp 0.23.1 remains pinned from historical work but does not calculate this reference. Complete transitive pins and attribution are in the new requirements/notices files.

Thermo `FlashVL.flash_TP_stability_test` is invoked at every trial, without warm starts. Primary PT controls: PT_SS_TOL=1e-26, PT_SS_MAXITER=1000, PT_STABILITY_XTOL=1e-12, PT_STABILITY_MAXITER=1000. These library controls are not numerically interchangeable with production log-fugacity tolerances. The inherited independent evaluator separately rejects maximum log-fugacity residual above 1e-9 and material residual above 1e-10.

## Scan, root acceptance and discontinuities

Selected scan: **64 evenly spaced points**, the loosest of the three studied densities that recovered the same single candidate/state for every positive case. All 15 cases were also inverted at 128 and 256 points; this includes grids where 300 K is not a scan point, so canonical exact-scan targets are not the sole evidence. The full 200–500 K scan always completes before root selection.

Exact scan zeros and adjacent strict sign changes become candidates. Near-exact scan points are recorded but never silently promoted to accepted roots. A failed scan evaluation leaves a hole: adjacent valid pairs may be diagnosed, but the solver refuses the whole inversion and never bridges the hole. Multiple candidates cause conservative ambiguity rejection before selecting any root. No physical multiple-root case was found; synthetic ambiguity is explicitly solver-only evidence.

A unique bracket is refined by deterministic bisection, with **100 maximum iterations** and **1e-10 K bracket-width tolerance**, exact-zero termination, or representable-temperature exhaustion. A fresh independent final PT/caloric call is mandatory. Final acceptance requires absolute entropy residual **<=1e-8 J/(mol K)** in both the driving and physical library entropy. Scan states are never published as the final solution.

If the temperature bracket collapses but both opposite-sign residuals remain above the entropy allowance, the solver records a discontinuity/gap and returns `ps_nonconvergence` without a solution. Thus signs or temperature convergence alone cannot certify a root. The physical pure saturation refinement below corroborates this diagnosis; it is not a universal discontinuity detector or a mathematical continuity proof.

## Positive matrix

Entropy is J/(mol K), enthalpy J/mol, pressure Pa absolute, temperature K. Display rounding does not alter full frozen precision. Beta is molar vapor fraction (0/1 for single phases).

| Case | P | z | T forward | S target | T PS | |ΔT| | Phase | beta | S residual | H eq |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_LIQUID | 30000000 | [0.5, 0.5] | 300 | -72.1588013237 | 300 | 0 | single_liquid | 0 | 0 | -16303.9480247 |
| B_VL | 300000 | [0.5, 0.5] | 300 | -45.1915326287 | 300 | 0 | vapor_liquid | 0.534642510224 | 0 | -14232.3399985 |
| C_VAPOR | 1000 | [0.5, 0.5] | 300 | 44.7134002185 | 300 | 0 | single_vapor | 1 | 0 | 164.368643728 |
| T350_LIQUID | 30000000 | [0.5, 0.5] | 350 | -52.8012816256 | 350 | 0 | single_liquid | 0 | 0 | -10017.8202563 |
| T350_VL | 1000000 | [0.5, 0.5] | 350 | -29.2950195875 | 350 | 0 | vapor_liquid | 0.569012139921 | 0 | -7277.0837901 |
| T350_VAPOR | 1000 | [0.5, 0.5] | 350 | 59.326777938 | 350 | 0 | single_vapor | 1 | 0 | 4910.98206552 |
| BUBBLE_BELOW | 6000000 | [0.5, 0.5] | 230.617554351 | -99.0915944373 | 230.617554351 | 2.14299689105e-11 | single_liquid | 0 | -1.01749719761e-11 | -25453.3357857 |
| BUBBLE_ABOVE | 6000000 | [0.5, 0.5] | 231.617554351 | -98.5195662863 | 231.617554351 | 9.15179043659e-12 | vapor_liquid | 0.0057349472485 | 4.98801000504e-12 | -25321.1064842 |
| DEW_BELOW | 6000000 | [0.5, 0.5] | 467.765889532 | 11.4743191401 | 467.765889532 | 2.13162820728e-11 | vapor_liquid | 0.986874454195 | -1.35251809752e-11 | 13176.5020618 |
| DEW_ABOVE | 6000000 | [0.5, 0.5] | 468.765889532 | 11.9579831629 | 468.765889532 | 9.09494701773e-12 | single_vapor | 1 | 3.06421554797e-12 | 13402.9489954 |
| NEAR_REFERENCE | 101325 | [1.0, 0.0] | 298.15 | -0.0429843186315 | 298.15 | 4.43378667114e-12 | single_vapor | 1 | -5.70675451339e-13 | -18.38865208 |
| PURE_METHANE | 100000 | [1.0, 0.0] | 300 | 0.289153545275 | 300 | 0 | single_vapor | 1 | 0 | 48.2859223994 |
| PURE_HEXANE_LIQUID | 30000000 | [0.0, 1.0] | 300 | -94.2838345692 | 300 | 0 | single_liquid | 0 | 0 | -28324.9107896 |
| PURE_HEXANE_VAPOR | 1000 | [0.0, 1.0] | 300 | 39.2781561945 | 300 | 0 | single_vapor | 1 | 0 | 261.530577736 |
| BINARY_30_70 | 300000 | [0.3, 0.7] | 300 | -63.4669082193 | 300 | 0 | vapor_liquid | 0.313889299412 | 0 | -20980.5415674 |

The near-reference case has T=298.15 K and P=101325 Pa, pure methane; its small nonzero total entropy is the real-fluid departure. Absolute entropy gates apply near zero.

### Applicable recovered phase fields

| Case               | Phase  | CH4 mole fraction | nC6 mole fraction | Z               | S ideal            | S residual        | S total          | H total        |
| ------------------ | ------ | ----------------- | ----------------- | --------------- | ------------------ | ----------------- | ---------------- | -------------- |
| A_LIQUID           | liquid | 0.5               | 0.5               | 1.04595589144   | -40.9970708366     | -31.1617304872    | -72.1588013237   | -16303.9480247 |
| B_VL               | liquid | 0.015619720086    | 0.984380279914    | 0.0154696638024 | -7.47940068044     | -81.9732896688    | -89.4526903493   | -30575.8188227 |
| B_VL               | vapor  | 0.921608807469    | 0.0783911925306   | 0.988502784824  | -6.46622934043     | -0.200006744134   | -6.66623608457   | -6.83391849804 |
| C_VAPOR            | vapor  | 0.5               | 0.5               | 0.999796670205  | 44.7163306927      | -0.00293047412368 | 44.7134002185    | 164.368643728  |
| T350_LIQUID        | liquid | 0.5               | 0.5               | 0.97623404143   | -26.3845622079     | -26.4167194178    | -52.8012816256   | -10017.8202563 |
| T350_VL            | liquid | 0.0390590036323   | 0.960940996368    | 0.0470355883909 | 6.03772239083      | -64.1357552307    | -58.0980328399   | -20156.2201518 |
| T350_VL            | vapor  | 0.849131344851    | 0.150868655149    | 0.964367911024  | -6.80608072937     | -0.672622167355   | -7.47870289673   | 2477.98298396  |
| T350_VAPOR         | vapor  | 0.5               | 0.5               | 0.999867999231  | 59.3288393214      | -0.00206138333099 | 59.326777938     | 4910.98206552  |
| BUBBLE_BELOW       | liquid | 0.5               | 0.5               | 0.257665065527  | -49.3681190089     | -49.7234754284    | -99.0915944373   | -25453.3357857 |
| BUBBLE_ABOVE       | liquid | 0.497122277239    | 0.502877722761    | 0.257609898008  | -49.1068091464     | -49.7014421775    | -98.8082513239   | -25442.7101406 |
| BUBBLE_ABOVE       | vapor  | 0.99890941422     | 0.00109058577989  | 0.698632745799  | -42.6190825512     | -5.85129728402    | -48.4703798352   | -4238.7389189  |
| DEW_BELOW          | liquid | 0.213879399631    | 0.786120600369    | 0.313920884543  | 35.1130467472      | -26.2967373118    | 8.81630943541    | 9268.87369561  |
| DEW_BELOW          | vapor  | 0.50380543749     | 0.49619456251     | 0.696573782935  | 19.2532632712      | -7.74359229078    | 11.5096709804    | 13228.4739767  |
| DEW_ABOVE          | vapor  | 0.5               | 0.5               | 0.695214131051  | 19.7477870973      | -7.78980393444    | 11.9579831629    | 13402.9489954  |
| NEAR_REFERENCE     | vapor  | 1                 | 0                 | 0.997753671402  | -5.68434188608e-13 | -0.0429843186315  | -0.0429843186321 | -18.38865208   |
| PURE_METHANE       | vapor  | 1                 | 0                 | 0.997827938964  | 0.330981191506     | -0.0418276462309  | 0.289153545275   | 48.2859223994  |
| PURE_HEXANE_LIQUID | liquid | 0                 | 1                 | 1.49300934183   | -46.4275293403     | -47.8563052289    | -94.2838345692   | -28324.9107896 |
| PURE_HEXANE_VAPOR  | vapor  | 0                 | 1                 | 0.999435338705  | 39.2858721889      | -0.00771599440705 | 39.2781561945    | 261.530577736  |
| BINARY_30_70       | liquid | 0.015619720086    | 0.984380279914    | 0.0154696638024 | -7.47940068044     | -81.9732896688    | -89.4526903493   | -30575.8188227 |
| BINARY_30_70       | vapor  | 0.921608807469    | 0.0783911925306   | 0.988502784824  | -6.46622934043     | -0.200006744134   | -6.66623608457   | -6.83391849804 |

### Selected scan and conditioning

| Case               | Successful/failed scan | Candidates | Initial bracket K                  | Root iterations | Fresh finals | dS/dT, ΔT=.001 K |
| ------------------ | ---------------------- | ---------- | ---------------------------------- | --------------- | ------------ | ---------------- |
| A_LIQUID           | 64 / 0                 | 1          | ['300', '300']                     | 0               | 1            | 0.400128024957   |
| B_VL               | 64 / 0                 | 1          | ['300', '300']                     | 0               | 1            | 0.56681389718    |
| C_VAPOR            | 64 / 0                 | 1          | ['300', '300']                     | 0               | 1            | 0.299303223372   |
| T350_LIQUID        | 64 / 0                 | 1          | ['347.619047619', '352.380952381'] | 1               | 1            | 0.375689917529   |
| T350_VL            | 64 / 0                 | 1          | ['347.619047619', '352.380952381'] | 1               | 1            | 0.580247507736   |
| T350_VAPOR         | 64 / 0                 | 1          | ['347.619047619', '352.380952381'] | 1               | 1            | 0.286119661567   |
| BUBBLE_BELOW       | 64 / 0                 | 1          | ['228.571428571', '233.333333333'] | 36              | 1            | 0.477571759291   |
| BUBBLE_ABOVE       | 64 / 0                 | 1          | ['228.571428571', '233.333333333'] | 36              | 1            | 0.664020021709   |
| DEW_BELOW          | 64 / 0                 | 1          | ['466.666666667', '471.428571429'] | 36              | 1            | 0.628015619945   |
| DEW_ABOVE          | 64 / 0                 | 1          | ['466.666666667', '471.428571429'] | 36              | 1            | 0.337387546089   |
| NEAR_REFERENCE     | 64 / 0                 | 1          | ['295.238095238', '300']           | 36              | 1            | 0.120327375857   |
| PURE_METHANE       | 64 / 0                 | 1          | ['300', '300']                     | 0               | 1            | 0.119821231965   |
| PURE_HEXANE_LIQUID | 64 / 0                 | 1          | ['300', '300']                     | 0               | 1            | 0.608572277031   |
| PURE_HEXANE_VAPOR  | 64 / 0                 | 1          | ['300', '300']                     | 0               | 1            | 0.479117194455   |
| BINARY_30_70       | 64 / 0                 | 1          | ['300', '300']                     | 0               | 1            | 0.591416682202   |

The JSON retains scan counts, endpoints, deterministic full-scan hashes, failures, phase transitions, near-exact points, candidate brackets, final brackets and residuals. Full transient scans are recomputed during verification. There is one observed candidate in each complete finite scan; mathematical global uniqueness is not established.

## Scan-density and monotonicity study

| Case | 64-point |ΔT| | 128-point |ΔT| | 256-point |ΔT| | Candidates at each density |
| --- | --- | --- | --- | --- |
| A_LIQUID | 0 | 2.29647412198e-11 | 0 | 1 / 1 / 1 |
| B_VL | 0 | 2.29647412198e-11 | 0 | 1 / 1 / 1 |
| C_VAPOR | 0 | 2.29647412198e-11 | 0 | 1 / 1 / 1 |
| T350_LIQUID | 0 | 0 | 0 | 1 / 1 / 1 |
| T350_VL | 0 | 0 | 0 | 1 / 1 / 1 |
| T350_VAPOR | 0 | 0 | 0 | 1 / 1 / 1 |
| BUBBLE_BELOW | 2.14299689105e-11 | 5.76960701437e-12 | 1.48929757415e-11 | 1 / 1 / 1 |
| BUBBLE_ABOVE | 9.15179043659e-12 | 2.04920524993e-11 | 2.6147972676e-11 | 1 / 1 / 1 |
| DEW_BELOW | 2.13162820728e-11 | 5.96855898038e-12 | 1.48361323227e-11 | 1 / 1 / 1 |
| DEW_ABOVE | 9.09494701773e-12 | 2.06341610465e-11 | 2.63185029326e-11 | 1 / 1 / 1 |
| NEAR_REFERENCE | 4.43378667114e-12 | 3.17186277243e-11 | 1.09139364213e-11 | 1 / 1 / 1 |
| PURE_METHANE | 0 | 2.29647412198e-11 | 0 | 1 / 1 / 1 |
| PURE_HEXANE_LIQUID | 0 | 2.29647412198e-11 | 0 | 1 / 1 / 1 |
| PURE_HEXANE_VAPOR | 0 | 2.29647412198e-11 | 0 | 1 / 1 / 1 |
| BINARY_30_70 | 0 | 2.29647412198e-11 | 0 | 1 / 1 / 1 |

All 6,720 scan evaluations across the 15×(64+128+256) study succeeded at primary accuracy. Every sampled adjacent entropy increment was positive. The minimum sampled scan slope was 0.0929080029271 J/(mol K²). The smallest local central-difference slope in the positive matrix was **0.119821231965 J/(mol K²)**; both ±0.01 K and ±0.001 K estimates are frozen. No universal heat capacity is inferred.

The largest recovered-T error across all densities was 3.17186277243e-11 K (NEAR_REFERENCE, 128 points); largest entropy residual was 1.62856395036e-11 J/(mol K) (BUBBLE_ABOVE, 256 points). Candidate counts did not change. Phase changes were resolved as liquid→VL→vapor where applicable, while the pure n-hexane vapor scan retains the saturation jump. Positive slopes alone therefore do not prove continuity or target attainability.

## Bubble/dew continuity and PT sensitivity

Bubble temperature at 6 MPa, z=[0.5,0.5]: **231.117554351 K**.

| Symmetric temperature offset K | S(above)-S(below), J/(mol K) |
| ------------------------------ | ---------------------------- |
| 0.1                            | 0.114604472734               |
| 0.01                           | 0.0114649680044              |
| 0.001                          | 0.00114654211477             |
| 0.0001                         | 0.000114654675798            |
| 1e-05                          | 1.14654846328e-05            |

Dew temperature at 6 MPa, z=[0.5,0.5]: **468.265889532 K**.

| Symmetric temperature offset K | S(above)-S(below), J/(mol K) |
| ------------------------------ | ---------------------------- |
| 0.1                            | 0.0968874431181              |
| 0.01                           | 0.00969224411224             |
| 0.001                          | 0.000969261995046            |
| 0.0001                         | 9.69291246911e-05            |
| 1e-05                          | 9.69549206431e-06            |

At every offset the bubble sides are liquid/VL and the dew sides VL/vapor. Entropy spans shrink approximately with offset down to 1e-5 K; no unresolved finite binary jump appeared. Primary PS round trips at ±0.5 K recover both boundaries correctly. The refinement points are forward continuity evidence, not additional individually qualified PS targets.

| Case | Thermo PT_SS_TOL | Status | ΔT K | ΔH eq J/mol | Max phase |ΔS| |
| --- | --- | --- | --- | --- | --- |
| BUBBLE_BELOW | 1e-16 | property_evaluation_failed | — | — | — |
| BUBBLE_BELOW | 1e-22 | success | -2.14299689105e-11 | -2.35013430938e-09 | 1.01749719761e-11 |
| BUBBLE_BELOW | 1e-26 | success | -2.14299689105e-11 | -2.35013430938e-09 | 1.01749719761e-11 |
| BUBBLE_BELOW | 1e-28 | success | -2.14299689105e-11 | -2.35013430938e-09 | 1.01749719761e-11 |
| BUBBLE_ABOVE | 1e-16 | property_evaluation_failed | — | — | — |
| BUBBLE_ABOVE | 1e-22 | success | 1.47736045619e-10 | 6.98491930962e-10 | 2.08871142604e-10 |
| BUBBLE_ABOVE | 1e-26 | success | 9.15179043659e-12 | 1.14232534543e-09 | 3.11217718263e-12 |
| BUBBLE_ABOVE | 1e-28 | success | 9.15179043659e-12 | 1.47701939568e-09 | 2.22399876293e-12 |
| DEW_BELOW | 1e-16 | property_evaluation_failed | — | — | — |
| DEW_BELOW | 1e-22 | success | -5.75653302803e-10 | 1.07320374809e-09 | 3.40335759574e-10 |
| DEW_BELOW | 1e-26 | success | -2.13162820728e-11 | -6.3100742409e-09 | 1.26618715512e-11 |
| DEW_BELOW | 1e-28 | success | -2.13162820728e-11 | -7.64885044191e-09 | 1.42144074289e-11 |
| DEW_ABOVE | 1e-16 | property_evaluation_failed | — | — | — |
| DEW_ABOVE | 1e-22 | success | 9.09494701773e-12 | 1.44063960761e-09 | 3.06421554797e-12 |
| DEW_ABOVE | 1e-26 | success | 9.09494701773e-12 | 1.44063960761e-09 | 3.06421554797e-12 |
| DEW_ABOVE | 1e-28 | success | 9.09494701773e-12 | 1.44063960761e-09 | 3.06421554797e-12 |

The deliberately loose 1e-16 PT setting produces scan holes because the independent fugacity gate rejects trial states. These are retained diagnostic failures, not failed primary cases or relaxed acceptance. At 1e-22, boundary phase enthalpy error reaches 1.6113e-7 J/mol; 1e-26 and 1e-28 agree much more closely. The primary reference keeps inherited 1e-26 precision.

## Target perturbations and noise

Every positive target was perturbed by ±0.01 J/(mol K), generating 30 independent inversions. All found one candidate and passed fresh residual acceptance; temperatures changed in the expected direction. The offsets are well above observed numerical noise. They are diagnostics, not a broadened physical qualification.

| Case               | T(S−.01)      | T(S+.01)      | Lower / upper phases          |
| ------------------ | ------------- | ------------- | ----------------------------- |
| A_LIQUID           | 299.975008461 | 300.024992463 | single_liquid / single_liquid |
| B_VL               | 299.982355764 | 300.017640714 | vapor_liquid / vapor_liquid   |
| C_VAPOR            | 299.96658967  | 300.033411536 | single_vapor / single_vapor   |
| T350_LIQUID        | 349.97338269  | 350.026618082 | single_liquid / single_liquid |
| T350_VL            | 349.982764473 | 350.017232523 | vapor_liquid / vapor_liquid   |
| T350_VAPOR         | 349.965050049 | 350.034950873 | single_vapor / single_vapor   |
| BUBBLE_BELOW       | 230.596615569 | 230.638494092 | single_liquid / single_liquid |
| BUBBLE_ABOVE       | 231.602496408 | 231.632615982 | vapor_liquid / vapor_liquid   |
| DEW_BELOW          | 467.749965097 | 467.781811438 | vapor_liquid / vapor_liquid   |
| DEW_ABOVE          | 468.736251844 | 468.795530855 | single_vapor / single_vapor   |
| NEAR_REFERENCE     | 298.066901246 | 298.23311446  | single_vapor / single_vapor   |
| PURE_METHANE       | 299.916550155 | 300.08346548  | single_vapor / single_vapor   |
| PURE_HEXANE_LIQUID | 299.983568288 | 300.016432092 | single_liquid / single_liquid |
| PURE_HEXANE_VAPOR  | 299.979128453 | 300.020871893 | single_vapor / single_vapor   |
| BINARY_30_70       | 299.9830906   | 300.016907705 | vapor_liquid / vapor_liquid   |

Direct-equation entropy inversion with tighter 1e-12 K bisection cross-checks all 15 final states. Maximum differences from primary results: T=2.17141860048e-11 K, S_eq=1.36193278877e-11 J/(mol K), H_eq=6.36100594420e-9 J/mol, governed by DEW_BELOW. Library/direct phase entropy at primary finals differs by at most 9.94759830064e-14 J/(mol K). These observations, scan-density changes, PT sensitivity and boundary refinements bound observed numerical noise; they do not establish behavior at arbitrarily small temperature increments.

## Pure coexistence gap

Pure n-hexane at 1000 Pa has independent saturation T=242.828331853 K. The rejected target is S=-58.464077472 J/(mol K).

| Offset K | S liquid side  | S vapor side  | Persistent span |
| -------- | -------------- | ------------- | --------------- |
| 0.1      | -128.125355234 | 11.1792617918 | 139.304617026   |
| 0.01     | -128.063441317 | 11.1334950893 | 139.196936406   |
| 0.001    | -128.05725056  | 11.1289181108 | 139.186168671   |
| 0.0001   | -128.056631491 | 11.1284604099 | 139.1850919     |
| 1e-05    | -128.056569584 | 11.1284146397 | 139.184984223   |

The initial apparent bracket is 238.095238095–242.857142857 K. After 36 bisections, the bracket is approximately 6.92921e-11 K wide but retains entropy span 139.184972259 J/(mol K). The fresh residual is -69.5924852335, versus allowance 1e-8. Result: `ps_nonconvergence`, gap detected, **no accepted state**. No vapor-fraction interpolation or constructed coexistence mixture is used.

## Negative matrix

| Case                 | Specification override / target                                | Expected failure             | Diagnostic reason                                                 | Accepted state |
| -------------------- | -------------------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------- | -------------- |
| NONFINITE_P          | {'P': 'NaN'}                                                   | invalid_input                | Finite positive P, finite S and normalized nonnegative z required | no             |
| ZERO_P               | {'P': 0.0}                                                     | invalid_input                | Finite positive P, finite S and normalized nonnegative z required | no             |
| NEGATIVE_P           | {'P': -1.0}                                                    | invalid_input                | Finite positive P, finite S and normalized nonnegative z required | no             |
| BAD_SUM              | {'z': [0.4, 0.4]}                                              | invalid_input                | Finite positive P, finite S and normalized nonnegative z required | no             |
| NEGATIVE_Z           | {'z': [-0.1, 1.1]}                                             | invalid_input                | Finite positive P, finite S and normalized nonnegative z required | no             |
| WATER                | {'component_ids': ['methane', 'water']}                        | unsupported_components       | Only ordered methane/n_hexane, including pure endpoints           | no             |
| UNKNOWN              | {'component_ids': ['methane', 'unknown']}                      | unsupported_components       | Only ordered methane/n_hexane, including pure endpoints           | no             |
| NONZERO_BIP          | {'kij': [[0.0, 0.01], [0.01, 0.0]]}                            | unsupported_bip              | Explicit constant zero 2x2 BIP required                           | no             |
| INVALID_BOUNDS_LOW   | {'bounds': [199.0, 500.0]}                                     | temperature_domain_invalid   | Study bounds must lie within 200–500 K                            | no             |
| INVALID_BOUNDS_HIGH  | {'bounds': [200.0, 501.0]}                                     | temperature_domain_invalid   | Study bounds must lie within 200–500 K                            | no             |
| BELOW_RANGE          | {'S_target': -1000000.0}                                       | entropy_target_not_bracketed | No exact root or adjacent valid sign change                       | no             |
| ABOVE_RANGE          | {'S_target': 1000000.0}                                        | entropy_target_not_bracketed | No exact root or adjacent valid sign change                       | no             |
| NONFINITE_S          | {'S_target': 'Infinity'}                                       | invalid_input                | Finite positive P, finite S and normalized nonnegative z required | no             |
| MAX_ITERATIONS       | {'grid_points': 128, 'maxiter': 1}                             | ps_nonconvergence            | Maximum root iterations reached                                   | no             |
| SYNTHETIC_MULTIPLE   | {'S_target': 0.0, 'synthetic': 'multiple'}                     | ambiguous_ps_root            | Multiple scan candidates; no arbitrary root selection             | no             |
| SYNTHETIC_HOLE       | {'S_target': 0.0, 'synthetic': 'hole'}                         | property_evaluation_failed   | Complete scan contains a hole; no bridging or uniqueness claim    | no             |
| PURE_COEXISTENCE_GAP | {'P': 1000.0, 'S_target': -58.46407747197774, 'z': [0.0, 1.0]} | ps_nonconvergence            | Discontinuity/coexistence gap                                     | no             |

NaN/Infinity inputs use JSON-safe string tokens decoded only when executing the negative test. The multiple-candidate polynomial and interior property hole are explicitly synthetic solver tests, not thermodynamic evidence. Failure top-level payloads contain no solution/T/phase/beta/composition/Z/H/S; root and scan values remain unaccepted diagnostics. A separate test forces fresh-final evaluation failure after an exact scan root.

## Numerical tolerances and justification

| Quantity / applicable fields                               | Absolute allowance | Relative allowance |
| ---------------------------------------------------------- | ------------------ | ------------------ |
| Recovered T / K                                            | 1e-7               | 0                  |
| Fresh entropy residual / J/(mol K)                         | 1e-8               | 0                  |
| beta                                                       | 1e-9               | 1e-9               |
| Each x or y component                                      | 1e-9               | 1e-9               |
| Z_L, Z_V                                                   | 1e-10              | 1e-9               |
| S_L, S_V, S_eq and phase entropy decomposition / J/(mol K) | 1e-8               | 1e-11              |
| H_L, H_V, H_eq and phase enthalpy decomposition / J/mol    | 1e-6               | 1e-11              |

Field comparisons use `atol + rtol*abs(reference)`; near-zero values retain their absolute allowance. Internal bracket tolerance (1e-10 K) is stricter than the recovered-T comparison gate (1e-7 K). The matrix minimum local slope maps 1e-8 J/(mol K) entropy to approximately 8.35e-8 K, below the recovered-T gate. The wider scan minimum would map it to approximately 1.08e-7 K, so residual tolerance alone is not a universal temperature guarantee; the bracket and recovered-state gates remain independent.

Observed residuals are at most 1.63e-11 over all densities, providing over 600-fold headroom to 1e-8. Primary residual margin is at least 9.98647481902e-9 J/(mol K). Exact byte reproduction, library/direct agreement, 1e-12 K root cross-checks, and the tighter PT sensitivity runs support this entropy-specific gate. It is not copied from PH enthalpy units.

The 1e-6 J/mol recovered-enthalpy absolute gate is over 150 times the observed primary error, accommodates temperature/root and phase-composition propagation, and remains distinct from unchanged tighter Pre-M10 same-state gates. Composition/beta errors remain below 6e-13 against ~1e-9 gates; Z errors remain below 1.4e-13 against at least 1e-10. These numerical allowances are not PR/correlation experimental accuracy claims and were not relaxed to accept a failed primary case.

### Maximum errors — selected 64-point primary matrix

| Quantity   | Maximum absolute error | Governing case |
| ---------- | ---------------------- | -------------- |
| H_L        | 5.95355231781e-09      | DEW_BELOW      |
| H_V        | 4.06907929573e-09      | DEW_BELOW      |
| H_eq       | 6.3100742409e-09       | DEW_BELOW      |
| S_L        | 1.26618715512e-11      | DEW_BELOW      |
| S_V        | 1.20099485912e-11      | DEW_BELOW      |
| S_eq       | 1.35251809752e-11      | DEW_BELOW      |
| S_residual | 1.35251809752e-11      | DEW_BELOW      |
| T          | 2.14299689105e-11      | BUBBLE_BELOW   |
| Z_L        | 4.86277684786e-14      | DEW_BELOW      |
| Z_V        | 1.23123733431e-13      | DEW_BELOW      |
| beta       | 5.59219337504e-13      | DEW_BELOW      |
| x          | 1.88737914186e-14      | BUBBLE_ABOVE   |
| y          | 1.64479541098e-13      | DEW_BELOW      |

x/y errors cover both component entries; absent phases are excluded. Recovered enthalpy is checked against the independently computed forward state, not used to obtain the temperature. Maximum residual Gibbs identity error is 1.27329258248e-11 J/mol; maximum fixed-composition dHres/dT−T dSres/dT error is 1.15805733003e-7 J/(mol K), below inherited 2e-5 finite-difference allowance.

## Production forward diagnostic and future M13 controls

Existing production PT/caloric calculations were compared read-only at all 15 forward states under both existing profiles. Both pass the new recovered-state field gates. Standard maximum S_eq/H_eq discrepancies are 4.5428e-10 J/(mol K) and 2.1248e-7 J/mol; high_accuracy reduces these to 4.4514e-11 and 2.0802e-8, respectively (DEW_BELOW). The independent reference is unchanged by this comparison.

Recommend existing **high_accuracy** for future nested production PT: it provides roughly tenfold aggregate boundary margin and preserves M11 practice. This study does not claim standard fails the new PS forward gates; unchanged M8.1 protection separately retains its known standard-profile caloric diagnostic failure. No new production PT profile is proposed.

Candidate M13 controls: 200–500 K; complete 64-point scan; bisection; at most 100 root iterations; 1e-10 K bracket criterion; 1e-8 J/(mol K) fresh entropy residual; independent recovered-state gates above; fresh final high_accuracy PT/caloric evaluation; conservative ambiguity/hole rejection; explicit pure-gap rejection with no accepted payload. Production qualification must reproduce these controls/evidence before advertising PS. Near-critical/general composition/retrograde expansion requires separate evidence.

A future compressor can use the independently frozen recovered H_eq as H_2s after entropy inversion, then apply separately qualified equipment-efficiency and PH steps. Neither equipment implementation nor efficiency/power calculations are part of Pre-M13.

## Determinism, tests and historical protection

Two fresh independent subprocess rebuilds reproduced the frozen JSON byte-for-byte, and their stdout summaries also matched. Reversed case order, intervening failed targets and changes of phase regime already reproduce identical compact results using a reusable independent oracle. Source hashes identify the local numerical implementation; byte identity is scoped to the recorded Python/platform/library environment.

All required gates passed:

| Protection                        | Actual result                                                                                                                  |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| New independent Pre-M13 suite     | 46 tests passed, including 15 positive and 17 negative cases, fresh final failure, studies and two fresh-process reproductions |
| M8 independent                    | 7 tests passed                                                                                                                 |
| Pre-M10 independent caloric       | 23 tests passed                                                                                                                |
| Pre-M8.1 independent boundary     | 28 tests passed                                                                                                                |
| Pre-M8.2 independent vapor-parent | 25 tests passed                                                                                                                |
| Pre-M11 independent PH            | 55 tests passed                                                                                                                |
| M10 production caloric            | 35 tests; 1,526 comparisons passed                                                                                             |
| M8 production                     | 122 comparisons passed                                                                                                         |
| M8.1 production                   | 325 comparisons passed; inherited standard-profile diagnostic failure remains explicitly non-gating                            |
| M8.2 production                   | Comparator passed; 9 grids, 1,152/1,152 high_accuracy PT states, zero unexpected failures                                      |
| M11 production                    | 53 tests; 29 positive, 9 negative/gap, 401 positive field comparisons passed                                                   |
| M12 focused protection            | 36 tests; 14 positive, 15 negative, 1,264 comparisons passed                                                                   |
| New forward production diagnostic | Both profiles pass all 15 forward states; no production PS invoked                                                             |
| Repository integrity              | All 282 pre-existing tracked SHA-256 hashes unchanged                                                                          |

New Python syntax, Markdown formatting, new-file whitespace and final `git diff --check` passed. Only the nine intended new Pre-M13 files remain untracked. Historical commands were run without `--write`; no old frozen reference was regenerated.

## Reproduction commands

Run from the repository root. Commands below use installed isolated environments; no installation is needed. Default verification does not write the reference.

```sh
# Verify a complete independent rebuild byte-for-byte.
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_ps/reference.py

# Explicit regeneration of only the new Pre-M13 JSON.
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_ps/reference.py --write

# Independent positive, negative, study and two-fresh-process reproduction tests.
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ps -p test_reference.py -v

# Optional read-only existing production forward-entropy diagnostic.
PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_forward.py
```

Historical protection commands, unchanged:

```sh
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_boundary -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_vapor_parent -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 .local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ph -p 'test_*.py' -q
PYTHONPATH=engine PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B -m unittest discover -s engine/tests -p test_pr_caloric.py -q
PYTHONPATH=engine PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B -m unittest discover -s engine/tests -p test_pr_ph_flash.py -q
PYTHONPATH=engine PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B -m unittest discover -s engine/tests -p test_heater_cooler_energy.py -q
PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py
PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case scan
PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case summary
PYTHONDONTWRITEBYTECODE=1 engine/.venv/bin/python -B benchmarks/heater_cooler_energy/compare_production.py
```

## New-file boundary

Only this report and `benchmarks/peng_robinson_ps/{equilibrium.py,solver.py,reference.py,test_reference.py,compare_forward.py,methane_nhexane_pr_ps_reference.json,requirements.txt,THIRD_PARTY_NOTICES.txt}` are new. The additional equilibrium adapter makes entropy aggregation explicit without changing historical helpers; the additional comparator separates production diagnostics from independent truth.

No `engine/riogineer_engine/pr_ps_flash.py`, provider capability, contract or equipment change was created. No files were staged, committed or pushed. Temporary hash snapshots and execution logs were created under `/tmp`, outside the repository.

Frozen JSON SHA-256: `3d147eb6a49d7caf9ac32f843577d0d01531c847383328d906b01fed7e264bae`.
