# Milestone 11 — Production standalone PH flash qualification

M11 automated acceptance: **COMPLETE — 2026-09-29**. Separately, M11 human-operated validation: **COMPLETE — 2026-09-29**, as reported by the human reviewer. Qualification remains limited to the documented standalone PH scope.

## Baseline, objective and independent authority

Implementation began on clean `main` at `1c4aef0ced7696af54082c0c6e2c510f090a5243` (`Implement and validate M8.2 PT vapor-parent restart`). Local HEAD, local origin/main and a read-only remote reference query agreed. M8/M8.1/M8.2/M10 and the tracked Pre-M11 benchmark were present. A SHA-256 snapshot protected all 263 pre-existing tracked files before edits.

The PH solver accepts pressure in Pa absolute, target molar enthalpy in J/mol, overall composition and explicit provider/BIP provenance. It solves `F(T)=H_eq(T,P,z)-H_target=0`, with T in K. Independent acceptance remains the unchanged `independent_methane_nhexane_pr_ph@1.0` reference in `benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json`, SHA-256 `e311738a66d7bedd37fe802f9b69297b35bf8f18aeb6e14eedd9a366af56a3b3`. All 55 independent tests passed unchanged.

## Architecture and API

`engine/riogineer_engine/pr_ph_flash.py` contains only specification validation, deterministic scanning, bracketed scalar inversion and immutable results/diagnostics. It imports no benchmark, independent solver, external thermodynamic package or EOS/caloric equations.

`PengRobinsonProvider.flash_PH(specification, bip, settings=PHSettings())` delegates to this module using the existing bound `equilibrium_caloric_PT` evaluator. `PHPropertyPackage` extends the existing caloric protocol. Capability `flash_PH` is advertised after numerical and focused test acceptance; this matches the method naming used by the existing caloric capability mechanism. No PS, water PH or equipment-energy capability is advertised.

`PHSpecification` carries `pressure_Pa_abs`, `enthalpy_J_mol`, existing `MolarComposition` and `StateSpecificationProvenance`. A reference temperature is neither required nor accepted as a PH input. Existing M10 input validation owns component IDs/order, composition normalization, BIP and caloric-domain checks, including declared zero-inventory species.

Every scan, root and final evaluation explicitly requests `SolverSettings.high_accuracy()` (1e-12 maximum log-fugacity target). The ordinary PT default remains standard (1e-11). M8.1 `K=S*w/z` and M8.2 `K=z/(S*w)` restarts are inherited through existing PT. No benchmark temperature or phase result appears in production code.

M10 `riogineer_caloric@1.0` and its `ideal_gas_sensible_298.15K_101325Pa@1.0` convention are unchanged: pure ideal-gas sensible h=0 at 298.15 K, no formation terms, and existing PR residual properties. The PH residual uses J/mol, never J/kg. Mass-specific fields remain available through the reused standalone M10 result and its existing conversion convention.

## Search, brackets and root acceptance

Defaults are the qualified domain **200–500 K**, **128 evenly spaced scan points**, and **100 maximum root iterations**. Optional bounds must remain inside this domain and pass existing caloric validation at both endpoints. Optional scan count is bounded to 3–4096; production qualification here uses 128, and coarser user controls do not inherit equivalent coverage automatically.

The full scan is evaluated without continuation or cached neighboring phase states. Every exact zero and adjacent strict sign change is collected. No candidate returns `enthalpy_target_not_bracketed`; multiple candidates return `multiple_ph_roots` before choosing a root. A failed trial aborts conservatively with its underlying status and message. No unknown interval is bridged. These finite scan observations do not establish mathematical global uniqueness or detect every possible unsampled root.

A single bracket is refined by bisection, retaining opposite residual signs across changes in phase classification. Bisection assumes neither a smooth derivative nor a fixed phase. Temperature convergence requires a bracket width <=1e-12 K, an exact zero, or representable-temperature exhaustion. The tighter internal temperature target protects downstream phase properties; the independent recovered-temperature acceptance remains unchanged at 1e-7 K absolute.

After convergence, the endpoint or candidate within the final bracket with the smallest observed absolute residual is evaluated afresh through high_accuracy PT and M10. Success also requires the fresh absolute H residual <=1e-6 J/mol. Small temperature increments alone cannot qualify success. Scan data is never returned as an accepted final state. No new production dependency was added.

## Results, diagnostics and failures

A successful immutable `PHResult` contains the original specification, recovered T, final H residual and one reused `CaloricResult`. Its nested PT result owns phase classification, beta, x/y, Z, BIP and PT controls; the caloric result owns phase H, equilibrium H, molecular/component/caloric datasets and reference convention. No parallel phase payload is fabricated in PH.

`PHDiagnostics` records requested controls, explicit nested PT controls, scan/root/final trial summaries, all candidate brackets, selected and final brackets, root iterations and reason. Successful/failed evaluation counts and phase transitions are auditable from the deterministic trial sequence; the comparator also reports stage counts. Failed PH results have `caloric=None`, `temperature_K=None` and `enthalpy_residual_J_mol=None`. Diagnostic trial H values, when valid, remain explicitly unaccepted evidence.

Statuses include `invalid_input`, inherited `unsupported_components`/`unsupported_bip`/caloric-domain errors, `temperature_domain_invalid`, `pt_evaluation_failure`, `caloric_evaluation_failure`, `enthalpy_target_not_bracketed`, `multiple_ph_roots`, `ph_numerical_failure` and `ph_nonconvergence`. The latter distinguishes iteration exhaustion from final H-residual failure through its reason. The independent negative benchmark's singular `unsupported_component` maps semantically to existing production `unsupported_components`; no component is dropped to satisfy that comparison.

## Canonical A/B/C

The exact production and reference inputs/results are retained in the comparison artifact. Rounded table display below does not replace machine-readable values.

| Case               | P / Pa absolute | H target / J mol−1 | Recovered T / K   | Phase         | Beta               | H residual / J mol−1   |
| ------------------ | --------------- | ------------------ | ----------------- | ------------- | ------------------ | ---------------------- |
| PH_A_SINGLE_LIQUID | 30000000        | -16303.94802467107 | 299.9999999999999 | single_liquid | 0                  | -1.637090463191271e-11 |
| PH_B_VAPOR_LIQUID  | 300000          | -14232.3399985311  | 299.9999999999977 | vapor_liquid  | 0.5346425102238044 | 9.094947017729282e-12  |
| PH_C_SINGLE_VAPOR  | 1000            | 164.3686437283909  | 299.9999999999999 | single_vapor  | 1                  | -1.017497197608463e-11 |

Case B final phase properties:

| Phase  | Composition methane / n_hexane            | Z                  | h / J mol−1        |
| ------ | ----------------------------------------- | ------------------ | ------------------ |
| liquid | [0.015619720085966047, 0.984380279914034] | 0.015469663802427  | -30575.81882271537 |
| vapor  | [0.9216088074693669, 0.07839119253063306] | 0.9885027848240123 | -6.833918498143873 |

Case B H_eq = -14232.33999853109 J/mol. The tests independently sum final phase fractions times phase enthalpies and require equality with the existing M10 aggregate: `(1-beta)*h_L + beta*h_V`. Frozen phase/state comparisons are additional gates, so matching total H alone is insufficient.

## Complete positive matrix

All 29 frozen cases pass. For each, the comparator checks status, phase identities/classification, explicit high_accuracy provenance, recovered T, absolute H residual, equilibrium H, beta, applicable phase compositions, Z and phase H, and fresh final evaluation. Detailed two-phase beta errors and all field allowances are preserved in JSON.

| Case                             | P / Pa   | H target / J mol−1 | T ref / K         | T PH / K          | Absolute T error / K  | Phase         | H residual / J mol−1   | Result |
| -------------------------------- | -------- | ------------------ | ----------------- | ----------------- | --------------------- | ------------- | ---------------------- | ------ |
| PH_A_SINGLE_LIQUID               | 30000000 | -16303.94802467107 | 300.0000000000001 | 299.9999999999999 | 1.70530256582424e-13  | single_liquid | -1.637090463191271e-11 | PASS   |
| PH_B_VAPOR_LIQUID                | 300000   | -14232.3399985311  | 299.9999999999849 | 299.9999999999977 | 1.27897692436818e-11  | vapor_liquid  | 9.094947017729282e-12  | PASS   |
| PH_C_SINGLE_VAPOR                | 1000     | 164.3686437283909  | 300               | 299.9999999999999 | 1.13686837721616e-13  | single_vapor  | -1.017497197608463e-11 | PASS   |
| PH_T280_L                        | 30000000 | -18660.80827890863 | 279.9999999999999 | 279.9999999999997 | 2.842170943040401e-13 | single_liquid | -2.546585164964199e-11 | PASS   |
| PH_T280_VL                       | 300000   | -17232.37170453695 | 280               | 280.0000000000002 | 2.273736754432321e-13 | vapor_liquid  | 1.455191522836685e-11  | PASS   |
| PH_T280_V                        | 1000     | -1591.316759996721 | 280               | 280.0000000000002 | 2.273736754432321e-13 | single_vapor  | 1.955413608811796e-11  | PASS   |
| PH_T350_L                        | 30000000 | -10017.82025629118 | 349.9999999999999 | 350               | 5.684341886080801e-14 | single_liquid | 9.094947017729282e-12  | PASS   |
| PH_T350_VL                       | 1000000  | -7277.083790103556 | 349.9999999999874 | 350.0000000000032 | 1.580247044330463e-11 | vapor_liquid  | -2.91038304567337e-11  | PASS   |
| PH_T350_V                        | 1000     | 4910.982065515258  | 350               | 350               | 0                     | single_vapor  | 2.728484105318785e-12  | PASS   |
| PH_T400_L                        | 30000000 | -3155.140149505612 | 400               | 400.0000000000001 | 1.13686837721616e-13  | single_liquid | 2.182787284255028e-11  | PASS   |
| PH_T400_VL                       | 3000000  | -167.0320235372674 | 400.0000000000006 | 400.0000000000151 | 1.455191522836685e-11 | vapor_liquid  | -2.319211489520967e-11 | PASS   |
| PH_T400_V                        | 1000     | 10182.64326016231  | 400               | 400.0000000000001 | 1.13686837721616e-13  | single_vapor  | 1.455191522836685e-11  | PASS   |
| PH_PURE_METHANE_280K_100000PA    | 100000   | -663.08882247365   | 279.9999999999999 | 280.0000000000002 | 2.842170943040401e-13 | single_vapor  | 9.094947017729282e-12  | PASS   |
| PH_PURE_METHANE_300K_100000PA    | 100000   | 48.28592239939235  | 300               | 299.9999999999999 | 1.13686837721616e-13  | single_vapor  | -3.453237695794087e-12 | PASS   |
| PH_PURE_METHANE_350K_100000PA    | 100000   | 1898.378759969079  | 350               | 350               | 0                     | single_vapor  | 9.094947017729282e-13  | PASS   |
| PH_PURE_METHANE_400K_100000PA    | 100000   | 3867.286192823054  | 399.9999999999999 | 400.0000000000001 | 1.70530256582424e-13  | single_vapor  | 5.002220859751105e-12  | PASS   |
| PH_PURE_N_HEXANE_280K_1000PA     | 1000     | -2540.614308766374 | 280.0000000000001 | 280.0000000000002 | 1.70530256582424e-13  | single_vapor  | 3.001332515850663e-11  | PASS   |
| PH_PURE_N_HEXANE_280K_30000000PA | 30000000 | -31906.84983603188 | 280               | 280.0000000000002 | 2.273736754432321e-13 | single_liquid | 4.729372449219227e-11  | PASS   |
| PH_PURE_N_HEXANE_300K_1000PA     | 1000     | 261.5305777356607  | 300               | 299.9999999999999 | 1.13686837721616e-13  | single_vapor  | -1.671196514507756e-11 | PASS   |
| PH_PURE_N_HEXANE_300K_30000000PA | 30000000 | -28324.9107895984  | 299.9999999999999 | 299.9999999999999 | 5.684341886080801e-14 | single_liquid | -1.455191522836685e-11 | PASS   |
| PH_PURE_N_HEXANE_350K_1000PA     | 1000     | 7908.868890623369  | 349.9999999999999 | 350               | 5.684341886080801e-14 | single_vapor  | 5.456968210637569e-12  | PASS   |
| PH_PURE_N_HEXANE_350K_30000000PA | 30000000 | -18746.91254742185 | 349.9999999999999 | 350               | 1.13686837721616e-13  | single_liquid | 2.182787284255028e-11  | PASS   |
| PH_PURE_N_HEXANE_400K_1000PA     | 1000     | 16486.34254560971  | 399.9999999999999 | 400.0000000000001 | 1.70530256582424e-13  | single_vapor  | 2.182787284255028e-11  | PASS   |
| PH_PURE_N_HEXANE_400K_30000000PA | 30000000 | -8243.459421114356 | 400               | 400.0000000000001 | 1.13686837721616e-13  | single_liquid | 3.637978807091713e-11  | PASS   |
| PH_BUBBLE_BELOW                  | 6000000  | -25453.33578574337 | 230.6175543513873 | 230.6175543513872 | 1.13686837721616e-13  | single_liquid | -7.275957614183426e-12 | PASS   |
| PH_BUBBLE_ABOVE                  | 6000000  | -25321.10648423328 | 231.6175543513875 | 231.6175543513971 | 9.578116078046151e-12 | vapor_liquid  | 2.182787284255028e-11  | PASS   |
| PH_DEW_BELOW                     | 6000000  | 13176.50206184565  | 467.7658895316328 | 467.7658895317036 | 7.082689990056679e-11 | vapor_liquid  | -2.546585164964199e-11 | PASS   |
| PH_DEW_ABOVE                     | 6000000  | 13402.94899539117  | 468.765889531638  | 468.7658895316328 | 5.229594535194337e-12 | single_vapor  | 3.637978807091713e-11  | PASS   |
| PH_NEAR_ZERO_H                   | 1000     | 0.3897345866866999 | 298.17            | 298.17            | 5.684341886080801e-14 | single_vapor  | -3.434585948980384e-12 | PASS   |

## Negative cases and coexistence limitation

All eight frozen negative specifications and the separately frozen pure n-hexane gap case fail with the required semantics and no accepted PH payload.

| Case                 | Production status             | Outcome                 |
| -------------------- | ----------------------------- | ----------------------- |
| PH_BELOW_RANGE       | enthalpy_target_not_bracketed | PASS; no accepted state |
| PH_ABOVE_RANGE       | enthalpy_target_not_bracketed | PASS; no accepted state |
| PH_INVALID_P         | invalid_input                 | PASS; no accepted state |
| PH_INVALID_Z         | invalid_input                 | PASS; no accepted state |
| PH_UNSUPPORTED_WATER | unsupported_components        | PASS; no accepted state |
| PH_INVALID_BOUNDS    | temperature_domain_invalid    | PASS; no accepted state |
| PH_CP_EXTRAPOLATION  | temperature_domain_invalid    | PASS; no accepted state |
| PH_MAXITER           | ph_nonconvergence             | PASS; no accepted state |
| PURE_COEXISTENCE_GAP | ph_nonconvergence             | PASS; no accepted state |

The pure n-hexane target inside the latent-heat gap at 1,000 Pa has a sign-changing interval but no qualified single-valued PT temperature solution. Narrowing that interval does not satisfy H; fresh final evaluation fails with `ph_nonconvergence`, matching frozen semantics. No lever rule, interpolation or forced beta is implemented. This conservative rejection also covers an injected discontinuous scalar residual.

PT and caloric trial failures are separately injected and checked for preserved diagnostics, absent H where unavailable and no accepted phase payload. Controlled tests cover multiple candidates, exact scan roots, no bracket, narrow/invalid bounds, nonfinite input, invalid caloric domain, iteration exhaustion and a changed final evaluation that must not reuse cached success.

## Maximum errors

All comparisons use unchanged `abs_error <= atol + rtol*abs(reference)`. T tolerance is 1e-7 K absolute; H residual is 1e-6 J/mol absolute; beta/composition is 1e-9+1e-9*abs(reference); Z is 1e-10+1e-9*abs(reference); H is 1e-7+1e-11*abs(reference). Zero references have no manufactured relative error. The near-zero-H case passes absolute residual acceptance.

| Quantity   | Maximum absolute error | Case producing absolute maximum  | Allowance at that case | Maximum relative error | Case producing relative maximum |
| ---------- | ---------------------- | -------------------------------- | ---------------------- | ---------------------- | ------------------------------- |
| T          | 7.082689990056679e-11  | PH_DEW_BELOW                     | 1e-07                  | 1.514152730791994e-13  | PH_DEW_BELOW                    |
| H_residual | 4.729372449219227e-11  | PH_PURE_N_HEXANE_280K_30000000PA | 1e-06                  | not applicable         | not applicable                  |
| H_eq       | 2.570232027210295e-09  | PH_B_VAPOR_LIQUID                | 2.423233999853365e-07  | 8.81262804561244e-12   | PH_NEAR_ZERO_H                  |
| beta       | 2.150390976396466e-12  | PH_DEW_BELOW                     | 1.98687445419579e-09   | 3.637477867621365e-11  | PH_BUBBLE_ABOVE                 |
| liquid.Z   | 1.583733144627786e-13  | PH_DEW_BELOW                     | 4.13920884542665e-10   | 5.045007269698046e-13  | PH_DEW_BELOW                    |
| liquid.h   | 1.969601726159453e-08  | PH_DEW_BELOW                     | 1.926887369561591e-07  | 2.124963389123595e-12  | PH_DEW_BELOW                    |
| liquid.q0  | 1.052491427344648e-13  | PH_BUBBLE_ABOVE                  | 1.497122277239493e-09  | 2.117168100349687e-13  | PH_BUBBLE_ABOVE                 |
| liquid.q1  | 1.052491427344648e-13  | PH_BUBBLE_ABOVE                  | 1.502877722760507e-09  | 2.092937069407413e-13  | PH_BUBBLE_ABOVE                 |
| vapor.Z    | 9.210410212290299e-13  | PH_DEW_BELOW                     | 7.965737829346894e-10  | 1.322244741036122e-12  | PH_DEW_BELOW                    |
| vapor.h    | 8.338247425854206e-09  | PH_DEW_BELOW                     | 2.32284739767014e-07   | 8.10235285239323e-11   | PH_B_VAPOR_LIQUID               |
| vapor.q0   | 6.316058787092516e-13  | PH_DEW_BELOW                     | 1.503805437489749e-09  | 1.253670230032211e-12  | PH_DEW_BELOW                    |
| vapor.q1   | 6.315503675580203e-13  | PH_DEW_BELOW                     | 1.496194562510252e-09  | 1.272787763660696e-12  | PH_DEW_BELOW                    |

The dew-sensitive liquid enthalpy is the largest liquid-H discrepancy, about 1.97e-8 J/mol versus its unchanged approximately 1.93e-7 J/mol allowance. M10 equations and independent PH tolerances were not changed.

## Workload, determinism and scan protection

Each accepted case evaluates all 128 scan temperatures, identifies exactly one bracket and performs one fresh final evaluation. Root iteration/evaluation counts and every selected bracket are in the artifact. Representative counts:

| Case               | Scan evaluations | Root evaluations | Final evaluations | Total PT/caloric calls |
| ------------------ | ---------------- | ---------------- | ----------------- | ---------------------- |
| PH_A_SINGLE_LIQUID | 128              | 42               | 1                 | 171                    |
| PH_B_VAPOR_LIQUID  | 128              | 42               | 1                 | 171                    |
| PH_C_SINGLE_VAPOR  | 128              | 42               | 1                 | 171                    |

Representative PH results compare identically after single-liquid, two-phase, single-vapor and failed calls. Repeated full production comparison reproduced the serialized artifact exactly, including all accepted states, diagnostics and negative outcomes. No mutable numerical state or continuation is used.

The separate unchanged M8.2 comparator passed 749 checks. Its exact nine-grid scan again evaluated 1,152 states successfully, with zero unexpected failures, four vapor-parent/liquid-trial restarts and one liquid-parent/vapor-trial restart. PH scanning receives these capabilities through PT without naming the restart temperatures in production.

## Automated acceptance

| Gate                                             | Actual result                                                                                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Pre-M8 independent                               | 7 passed                                                                                                                       |
| M8 production comparison                         | 122 passed                                                                                                                     |
| Pre-M8.1 independent                             | 28 passed                                                                                                                      |
| M8.1 production comparison                       | 325 passed                                                                                                                     |
| Pre-M8.2 independent                             | 25 passed                                                                                                                      |
| M8.2 production comparison and scan              | 749 checks; 1,152/1,152 states passed                                                                                          |
| M9 integration                                   | 7 passed                                                                                                                       |
| Pre-M10 independent                              | 23 passed                                                                                                                      |
| M10 production comparison                        | 1,526 passed                                                                                                                   |
| Pre-M11 independent                              | 55 passed unchanged                                                                                                            |
| M11 production comparison                        | 29 positive; 8 negative + 1 gap; 401 positive field checks passed                                                              |
| New M11 production tests                         | 53 passed in complete suite (52 focused tests passed before capability advertisement; capability test included in final suite) |
| Complete Python suite                            | 248 passed                                                                                                                     |
| Complete TypeScript suite                        | 200 passed, 18 files                                                                                                           |
| Complete browser suite                           | 31 passed                                                                                                                      |
| Contract parity, ESLint, type checking           | Passed                                                                                                                         |
| Repository formatting, Python syntax, whitespace | Passed; 53 Python files parsed                                                                                                 |
| Production build                                 | Passed                                                                                                                         |
| Production smoke                                 | 17 pages, 17 PNG cards, links, 404s, preview indexing and disabled contact delivery passed                                     |
| Exact production artifact reproduction           | Passed                                                                                                                         |
| Protected-file integrity                         | Passed                                                                                                                         |

HTTP/browser/smoke tests used local-server permissions as required by the sandbox. Smoke used `SITE_URL=http://127.0.0.1:3210` on the built server and matching `SMOKE_URL`; no code was changed to bypass origin checks. No live external LLM/provider call was made. Remote Git verification read only the main reference.

## Protected evidence and files

All frozen Pre-M8/M8, Pre-M8.1/M8.1, Pre-M8.2/M8.2, M9 fixtures, Pre-M10/M10 and Pre-M11 evidence remains byte-identical to the pre-implementation SHA-256 snapshot. All existing production thermodynamic equations, PT settings, datasets and tests are unchanged. Only the existing provider registry/protocol file and the minimal Master Context update differ among baseline tracked files. Contracts remain requirements 1.4, flowsheet 1.5 and results 1.6. No production dependency was added.

Created:

- `engine/riogineer_engine/pr_ph_flash.py`
- `engine/tests/test_pr_ph_flash.py`
- `benchmarks/peng_robinson_ph/compare_production.py`
- `benchmarks/peng_robinson_ph/production_comparison.json`
- `MILESTONE_11.md`

Modified:

- `engine/riogineer_engine/property_packages.py`
- `docs/RIOGINEER_MASTER_CONTEXT.md`

Temporary diagnostics are outside the repository. No staging, commit or push was performed. The changes remain for human inspection.

## Human-operated validation — complete, 2026-09-29

The human reviewer reported successful execution and inspection of the documented production comparator from the repository root on 2026-09-29, using `--case A`, `B`, `C`, `bubble`, `dew`, `near_zero`, `negative` and `summary`. This manual record is separate from automated acceptance above. No comparator, test or thermodynamic calculation was rerun for this documentation task.

For canonical A/B/C, the reviewer confirmed the HIGH_ACCURACY nested PT profile, 128-point scan, one candidate bracket and fresh final evaluation. Temperature, absolute H residual and all applicable phase-state comparisons passed:

| Selector | P / Pa absolute | H target / J mol−1  | Recovered T / K   | Phase         | Beta               |
| -------- | --------------- | ------------------- | ----------------- | ------------- | ------------------ |
| A        | 30000000        | -16303.948024671074 | approximately 300 | single_liquid | 0                  |
| B        | 300000          | -14232.339998531099 | approximately 300 | vapor_liquid  | 0.5346425102238044 |
| C        | 1000            | 164.3686437283909   | approximately 300 | single_vapor  | 1                  |

Case A liquid composition, Z and enthalpy passed. Case B beta, both phase compositions, Z_L/Z_V and h_L/h_V passed, confirming the correct two-phase equilibrium state rather than only agreement in total enthalpy. Case C vapor composition, Z and enthalpy passed.

The boundary-adjacent review confirmed:

| Selector | P / Pa absolute | Recovered T / K, approximately | Beta, approximately | Phase        |
| -------- | --------------- | ------------------------------ | ------------------- | ------------ |
| bubble   | 6000000         | 231.617554351397               | 0.00573494724819    | vapor_liquid |
| dew      | 6000000         | 467.765889531704               | 0.986874454193639   | vapor_liquid |

Both boundary runs used HIGH_ACCURACY, a 128-point scan and one candidate bracket. Temperature, H residual and beta/x/y/Z/h phase comparisons passed. The bubble case confirmed PH operation through the region protected by M8.1 PT behavior. The dew case's liquid enthalpy remained within the unchanged frozen allowance, confirming the explicit high-accuracy policy resolves the previously identified precision sensitivity without changing M10 equations or frozen tolerances.

The near-zero-H review confirmed H_target approximately 0.3897345866867 J/mol, T approximately 298.17 K, single_vapor, beta=1 and HIGH_ACCURACY. Temperature, absolute H residual and vapor-state comparisons passed.

The negative selector confirmed nine controlled rejections: below and above the enthalpy range, invalid pressure, invalid composition, unsupported water, invalid temperature bounds, caloric/Cp extrapolation domain, root iteration exhaustion and the pure-component coexistence gap. Every rejection returned the expected failure semantics with **no accepted payload**; no unqualified PH state was published.

The complete positive summary confirmed all 29 frozen cases, including single-liquid, vapor-liquid and single-vapor states; 280/350/400 K binary states; pure methane; qualified pure n-hexane; both sides of the bubble/dew boundaries; and near-zero H. The final comparator summary was:

```text
PASS: 29 positive, 9 negative/gap;
401 positive field comparisons
```

The reviewer visually confirmed the phase sequence: bubble below → single_liquid; bubble above → vapor_liquid; dew below → vapor_liquid; dew above → single_vapor. Human validation does not broaden the qualification limits below, and no subsequent milestone is authorized by this record.

The documented commands are retained below for reproduction, including the additional pure-component selector. Each selector performs all positive and negative comparisons, then limits displayed detail; no raw scan dump is required. `--write` is unnecessary for review and only writes the separate production artifact, never independent references.

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case A
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case B
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case C
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case bubble
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case dew
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case near_zero
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case pure
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case summary
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case negative
```

Focused production test reproduction:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_pr_ph_flash.py' -v
```

The bubble/dew selectors display PH_BUBBLE_ABOVE and PH_DEW_BELOW; the summary includes both sides of each boundary. The pure selector displays the 300 K / 1,000 Pa pure n-hexane case; the complete matrix contains all frozen pure methane/n-hexane cases.

## Qualification limits and next boundary

Qualified evidence is restricted to the committed methane/n_hexane cases, explicit zero kij, existing M10 caloric reference and 200–500 K scan domain. It does not establish arbitrary petroleum mixtures, nonzero BIPs, water, VLLE, critical/retrograde behavior, other EOS/caloric datasets or pure coexistence interpolation. A finite scan establishes only observed candidates, not global uniqueness.

PH is standalone. HEATER_1, COMPRESSOR_1 and SEP_PR_1 remain unchanged; separator rigorous duty/energy remains unavailable. No process-network energy integration, Stream Table caloric enrichment, frontend PH controls or PS flash was added. Any future process integration or PS qualification requires a separate scope and authorization after human review. No later milestone was started.

**M11 automated acceptance: COMPLETE. M11 human-operated validation: COMPLETE — 2026-09-29.**
