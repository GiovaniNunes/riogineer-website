# Milestone 13 — Production standalone Peng–Robinson PS flash

**Automated M13 acceptance: COMPLETE — 2026-09-30.**
**Human-operated M13 validation: COMPLETE — 2026-09-30**

## Objective, baseline and independent authority

M13 adds standalone `P + S_target + z -> T + equilibrium state + H_eq` to the production property package. No compressor, turbine, valve, equipment energy integration or process-contract PS specification is implemented. No subsequent milestone was started.

Implementation resumed on clean main at `06de73563c2262974be7df8638158262a9191e7d`, containing committed Pre-M13. HEAD, origin/main and a read-only live remote query agreed. A SHA-256 snapshot protected all 291 pre-existing tracked files.

Independent qualification is separate from production qualification: Pre-M13 established the frozen targets/states using third-party PT/caloric calculations and independent entropy inversion. M13 consumes those exact values and allowances, without importing the independent solver or regenerating truth. Production uses only its existing standard-library PR/PT/M10 stack; no dependency was added.

Acceptance reference: `independent_methane_nhexane_pr_ps@1.0`; frozen JSON SHA-256 `3d147eb6a49d7caf9ac32f843577d0d01531c847383328d906b01fed7e264bae`. Authority: `PRE_MILESTONE_13_PR_PS_QUALIFICATION.md` and unchanged `benchmarks/peng_robinson_ps/methane_nhexane_pr_ps_reference.json`.

## Production architecture and API

`engine/riogineer_engine/pr_ps_flash.py` owns specification validation, bounded scan, provisional candidate detection, deterministic bisection and immutable result/diagnostic structures. It does not duplicate EOS, entropy, enthalpy, fugacity, stability or phase-split mathematics. M11 PH remains in its original module without refactoring or numerical changes.

`PSSpecification(pressure_Pa_abs, entropy_J_mol_K, composition, provenance)` uses existing `MolarComposition` and `StateSpecificationProvenance`. Explicit BIP is passed separately, matching PH conventions. Pressure is Pa absolute, entropy J/(mol K), and temperature K.

`PengRobinsonProvider.flash_PS(specification, bip, settings=PSSettings())` delegates to `flash_ps` using the bound `equilibrium_caloric_PT` evaluator. `PSPropertyPackage` extends the caloric protocol. The provider adds exactly one capability, `flash_PS`; `flash_PH` stays available. `water_PH`, `process_energy_balance` and the historical `PS_flash` alias remain absent.

`PSResult` carries status, capability, input specification, `PSDiagnostics`, recovered temperature, final entropy residual, existing caloric provenance and one existing `CaloricResult`. That reused payload retains final PT classification, phase fractions/compositions/Z, phase entropy/enthalpy and their decompositions, equilibrium S/H and mass-specific properties. No redundant phase state is fabricated. Single-phase results contain only the physical phase.

`PSDiagnostics` records the controls, high_accuracy PT settings, scalar trial summaries, near-exact scan temperatures, provisional candidate intervals, selected/final brackets, iteration count, reason, gap flag and final entropy span. Diagnostic trial states are not accepted solutions. Every failed result has `caloric=None`, `temperature_K=None`, and `entropy_residual_J_mol_K=None`.

## Thermodynamic equation and reference convention

```text
F(T) = S_eq(T, P, z) - S_target
single phase: S_eq = S_phase
vapor-liquid: S_eq = (1-beta) S_L(T,P,x) + beta S_V(T,P,y)
              H_eq = (1-beta) H_L(T,P,x) + beta H_V(T,P,y)
```

M10 supplies entropy and enthalpy from the actual PT phase compositions and roots. No extra mixing term, PS-specific correction, empirical fit or second entropy model exists. Enthalpy is required output and is checked for finiteness, but does not drive inversion.

Reference `ideal_gas_sensible_298.15K_101325Pa@1.0`: pure ideal-gas h=s=0 at 298.15 K and 101325 Pa. Relative sensible properties include pressure and ideal compositional entropy; formation and third-law offsets are absent. M10 formulas, constants, Cp data, units and reference metadata remain untouched.

## Controls, complete scan and final acceptance

Defaults: **200–500 K**, **64 evenly spaced scan points**, bisection, **100 maximum root iterations**, **1e-10 K** bracket tolerance, **1e-8 J/(mol K)** absolute fresh entropy residual. The independent recovered-temperature gate remains **1e-7 K**. Numerical allowances are the exact frozen Pre-M13 values, not the observed floating-point errors.

Every scan/root/final call requests `SolverSettings.high_accuracy()` with 1e-12 log-fugacity tolerance; mismatched returned PT provenance is rejected. Ordinary standalone PT retains its 1e-11 default. No new PT profile or change to RR/stability/PT arithmetic occurs.

The entire scan is evaluated before selection. Failed evaluations are recorded while scanning continues; no sign interval bridges a failed point. Any hole prevents acceptance over the requested domain. Exact zeros and adjacent valid sign changes define provisional candidates. Near-exact scan points are recorded; those already inside a candidate interval do not duplicate it. An isolated within-tolerance point still requires fresh final acceptance. Multiple candidates are conservatively rejected without choosing the first.

Bisection stays inside the selected provisional interval. Interval signs are not proof of continuity: temperature convergence alone is insufficient. An exact bisection root collapses both endpoints and their residuals consistently. Iteration exhaustion fails without payload. After convergence, the smallest-residual observed point inside the final bracket receives a completely fresh high_accuracy PT/M10 evaluation. Only its finite S/H and entropy residual can support success.

A collapsed temperature interval with persistent opposite residuals above allowance marks a discontinuity/coexistence gap. It returns `ps_nonconvergence`, never a phase-fraction interpolation or accepted coexistence state. This is the Pre-M13 qualified gap policy, not a universal mathematical continuity detector.

Optional bounds remain inside 200–500 K; optional scan counts follow existing bounded-control conventions (3–4096) and iteration limits can only remain at or below 100. These options do not automatically inherit qualification for every grid/bound choice. Acceptance uses the frozen 64-point default; the forced-iteration negative retains its frozen 128-point input. No density was increased to rescue a positive case.

Failures distinguish input/component/BIP/domain errors, `entropy_target_not_bracketed`, `ambiguous_ps_root`, `property_evaluation_failed`, `ps_nonconvergence`, and numerical failure. Underlying PT/caloric reasons remain in scalar diagnostics.

## Positive production matrix

P is Pa absolute; entropy is J/(mol K), enthalpy J/mol. Every row passes all applicable frozen phase fields, not just total entropy. Display values are rounded; JSON retains full precision.

| Case               | P        | S target           | T reference     | T production    | Phase         | beta              | S residual           | H eq             | Result |
| ------------------ | -------- | ------------------ | --------------- | --------------- | ------------- | ----------------- | -------------------- | ---------------- | ------ |
| A_LIQUID           | 30000000 | -72.158801323734   | 300             | 300             | single_liquid | 0                 | 2.8421709430404e-14  | -16303.948024671 | PASS   |
| B_VL               | 300000   | -45.19153262867    | 300             | 300             | vapor_liquid  | 0.5346425102238   | 9.6633812063374e-13  | -14232.339998531 | PASS   |
| C_VAPOR            | 1000     | 44.713400218542    | 300             | 300             | single_vapor  | 1                 | 2.8421709430404e-14  | 164.36864372839  | PASS   |
| T350_LIQUID        | 30000000 | -52.801281625649   | 350             | 350             | single_liquid | 0                 | 6.3948846218409e-14  | -10017.820256291 | PASS   |
| T350_VL            | 1000000  | -29.295019587535   | 350             | 350             | vapor_liquid  | 0.56901213992134  | -2.1529444893531e-12 | -7277.0837901043 | PASS   |
| T350_VAPOR         | 1000     | 59.326777938043    | 350             | 350             | single_vapor  | 1                 | 4.2632564145606e-14  | 4910.9820655153  | PASS   |
| BUBBLE_BELOW       | 6000000  | -99.091594437281   | 230.61755435139 | 230.61755435137 | single_liquid | 0                 | -1.0146550266654e-11 | -25453.335785746 | PASS   |
| BUBBLE_ABOVE       | 6000000  | -98.519566286271   | 231.61755435139 | 231.6175543514  | vapor_liquid  | 0.005734947248186 | -1.5631940186722e-13 | -25321.106484233 | PASS   |
| DEW_BELOW          | 6000000  | 11.474319140114    | 467.76588953163 | 467.76588953168 | vapor_liquid  | 0.98687445419296  | -1.5504042494285e-11 | 13176.502061838  | PASS   |
| DEW_ABOVE          | 6000000  | 11.957983162901    | 468.76588953163 | 468.76588953164 | single_vapor  | 1                 | 3.0855318300382e-12  | 13402.948995393  | PASS   |
| NEAR_REFERENCE     | 101325   | -0.042984318631506 | 298.15          | 298.15          | single_vapor  | 1                 | -5.3339277439335e-13 | -18.388652079953 | PASS   |
| PURE_METHANE       | 100000   | 0.28915354527507   | 300             | 300             | single_vapor  | 1                 | 2.031708135064e-14   | 48.285922399393  | PASS   |
| PURE_HEXANE_LIQUID | 30000000 | -94.283834569228   | 300             | 300             | single_liquid | 0                 | 2.8421709430404e-14  | -28324.910789598 | PASS   |
| PURE_HEXANE_VAPOR  | 1000     | 39.278156194498    | 300             | 300             | single_vapor  | 1                 | 2.8421709430404e-14  | 261.53057773566  | PASS   |
| BINARY_30_70       | 300000   | -63.466908219299   | 300             | 300             | vapor_liquid  | 0.31388929941238  | 9.5212726591853e-13  | -20980.541567383 | PASS   |

Each case records high_accuracy provenance, all 64 successful scan trials, exactly one candidate, and one successful fresh final evaluation. The comparator makes an additional independent production forward call at recovered T and requires identical caloric results and the frozen entropy residual allowance.

### Applicable phase-state fidelity

| Case               | Phase  | CH4 fraction      | nC6 fraction       | Z                 | S                  | H                |
| ------------------ | ------ | ----------------- | ------------------ | ----------------- | ------------------ | ---------------- |
| A_LIQUID           | liquid | 0.5               | 0.5                | 1.0459558914383   | -72.158801323734   | -16303.948024671 |
| B_VL               | liquid | 0.015619720085966 | 0.98438027991403   | 0.015469663802427 | -89.452690349285   | -30575.818822715 |
| B_VL               | vapor  | 0.92160880746936  | 0.078391192530639  | 0.98850278482401  | -6.6662360845689   | -6.833918498044  |
| C_VAPOR            | vapor  | 0.5               | 0.5                | 0.99979667020519  | 44.713400218542    | 164.36864372839  |
| T350_LIQUID        | liquid | 0.5               | 0.5                | 0.97623404143003  | -52.801281625649   | -10017.820256291 |
| T350_VL            | liquid | 0.039059003632274 | 0.96094099636773   | 0.047035588390858 | -58.098032839863   | -20156.220151789 |
| T350_VL            | vapor  | 0.84913134485059  | 0.15086865514941   | 0.9643679110245   | -7.4787028967307   | 2477.9829839558  |
| T350_VAPOR         | vapor  | 0.5               | 0.5                | 0.99986799923123  | 59.326777938043    | 4910.9820655153  |
| BUBBLE_BELOW       | liquid | 0.5               | 0.5                | 0.25766506552674  | -99.091594437291   | -25453.335785746 |
| BUBBLE_ABOVE       | liquid | 0.4971222772396   | 0.5028777227604    | 0.25760989800756  | -98.808251323844   | -25442.710140642 |
| BUBBLE_ABOVE       | vapor  | 0.99890941422011  | 0.0010905857798854 | 0.69863274579897  | -48.470379835231   | -4238.7389189001 |
| DEW_BELOW          | liquid | 0.213879399631    | 0.786120600369     | 0.31392088454278  | 8.8163094354552    | 9268.8736956294  |
| DEW_BELOW          | vapor  | 0.50380543749058  | 0.49619456250942   | 0.69657378293577  | 11.509670980432    | 13228.473976705  |
| DEW_ABOVE          | vapor  | 0.5               | 0.5                | 0.69521413105128  | 11.957983162904    | 13402.948995393  |
| NEAR_REFERENCE     | vapor  | 1                 | 0                  | 0.99775367140176  | -0.042984318632039 | -18.388652079953 |
| PURE_METHANE       | vapor  | 1                 | 0                  | 0.99782793896428  | 0.28915354527509   | 48.285922399393  |
| PURE_HEXANE_LIQUID | liquid | 0                 | 1                  | 1.4930093418267   | -94.283834569228   | -28324.910789598 |
| PURE_HEXANE_VAPOR  | vapor  | 0                 | 1                  | 0.99943533870504  | 39.278156194498    | 261.53057773566  |
| BINARY_30_70       | liquid | 0.015619720085966 | 0.98438027991403   | 0.015469663802427 | -89.452690349285   | -30575.818822715 |
| BINARY_30_70       | vapor  | 0.92160880746936  | 0.078391192530641  | 0.98850278482401  | -6.6662360845689   | -6.8339184980442 |

Bubble below/above classify as single_liquid/vapor_liquid; dew below/above classify as vapor_liquid/single_vapor. All pass unchanged gates with high_accuracy nested PT. Pure methane vapor and pure n-hexane liquid/vapor pass. The near-reference methane case uses absolute entropy acceptance near zero. No bubble/dew-specific branch or frozen input appears in production solver logic.

## Negative matrix and coexistence gap

| Case                 | Expected / actual status     | Candidates | Gap detected | Accepted state |
| -------------------- | ---------------------------- | ---------- | ------------ | -------------- |
| NONFINITE_P          | invalid_input                | 0          | False        | no             |
| ZERO_P               | invalid_input                | 0          | False        | no             |
| NEGATIVE_P           | invalid_input                | 0          | False        | no             |
| BAD_SUM              | invalid_input                | 0          | False        | no             |
| NEGATIVE_Z           | invalid_input                | 0          | False        | no             |
| WATER                | unsupported_components       | 0          | False        | no             |
| UNKNOWN              | unsupported_components       | 0          | False        | no             |
| NONZERO_BIP          | unsupported_bip              | 0          | False        | no             |
| INVALID_BOUNDS_LOW   | temperature_domain_invalid   | 0          | False        | no             |
| INVALID_BOUNDS_HIGH  | temperature_domain_invalid   | 0          | False        | no             |
| BELOW_RANGE          | entropy_target_not_bracketed | 0          | False        | no             |
| ABOVE_RANGE          | entropy_target_not_bracketed | 0          | False        | no             |
| NONFINITE_S          | invalid_input                | 0          | False        | no             |
| MAX_ITERATIONS       | ps_nonconvergence            | 1          | False        | no             |
| SYNTHETIC_MULTIPLE   | ambiguous_ps_root            | 2          | False        | no             |
| SYNTHETIC_HOLE       | property_evaluation_failed   | 0          | False        | no             |
| PURE_COEXISTENCE_GAP | ps_nonconvergence            | 1          | True         | no             |

Pure n-hexane gap target: P=1000 Pa, z=[0,1], S_target=-58.4640774719777 J/(mol K). The provisional sign interval [238.0952380952381, 242.85714285714286] shrinks to [242.82833185293606, 242.82833185300535], but final entropy span remains 139.184972259501 J/(mol K). The diagnostic final entropy residual is -69.5924852335801, far outside 1e-8. Status is ps_nonconvergence, gap_detected=True, with no accepted caloric payload or T.

Synthetic ambiguity and property-hole cases are labeled solver-only evidence, not physical multiple roots or fabricated thermodynamic states. Additional focused tests cover returned and raised provider failures, wrong PT profile, nonfinite entropy/enthalpy, exact/near scan roots, exact bisection roots, iteration exhaustion and changed/failed final evaluation.

## Maximum production-versus-independent errors

| Quantity   | Maximum absolute error | Allowance at governing field | Governing case |
| ---------- | ---------------------- | ---------------------------- | -------------- |
| T          | 4.7975845518522e-11    | 1e-07                        | DEW_BELOW      |
| S_residual | 1.5504042494285e-11    | 1e-08                        | DEW_BELOW      |
| S_eq       | 1.5504042494285e-11    | 1.0114743191401e-08          | DEW_BELOW      |
| beta       | 2.8367308502197e-12    | 1.9868744541958e-09          | DEW_BELOW      |
| x          | 1.3822276656583e-13    | 1.5028777227605e-09          | BUBBLE_ABOVE   |
| y          | 8.3311135767872e-13    | 1.5038054374897e-09          | DEW_BELOW      |
| Z_L        | 1.1290968160438e-13    | 4.1392088454266e-10          | DEW_BELOW      |
| Z_V        | 1.0812462036824e-12    | 7.9657378293469e-10          | DEW_BELOW      |
| S_L        | 2.8393287720974e-11    | 1.0088163094354e-08          | DEW_BELOW      |
| S_V        | 8.3471007883418e-12    | 1.0115096709804e-08          | DEW_BELOW      |
| H_L        | 1.3529643183574e-08    | 1.0926887369562e-06          | DEW_BELOW      |
| H_V        | 3.8635334931314e-09    | 1.132284739767e-06           | DEW_BELOW      |
| H_eq       | 7.2432158049196e-09    | 1.1317650206185e-06          | DEW_BELOW      |

x/y maxima include both component entries. Phase maxima include only applicable phases. All phase ideal/residual H/S decompositions are also compared. The production artifact contains production/reference/error/allowance/PASS for every comparison. Field rule is frozen `atol + rtol*abs(reference)`; final entropy residual uses absolute allowance.

Recovered H_eq maximum error is 7.2432158049196e-09 J/mol (DEW_BELOW); H is independently checked against forward evidence and never used as the root equation. Pre-M13 minimum local conditioning 0.1198212319653 J/(mol K²) remains contextual evidence for that matrix, not a universal physical lower bound.

## Determinism, internal consistency and historical capability update

The production artifact was generated and then reconstructed in a separate fresh process using `--verify`; byte identity passed with no timestamps or machine-specific paths. Representative liquid/VL/vapor results, complete scalar diagnostics and iteration counts repeat identically after liquid, VL, vapor, invalid-input and coexistence-gap calls. Separate production PT→S→PS tests establish internal round-trip consistency; they do not substitute for external frozen acceptance.

M11 originally and correctly tested that PS was not exposed. The user explicitly authorized updating only that obsolete capability assertion for M13. The test now requires flash_PH and flash_PS while retaining the PS_flash alias, water_PH and process_energy_balance exclusions. Its name was minimally updated to describe the new boundary. An AST comparison verifies every other statement in the historical PH test file is unchanged. No PH expected value, tolerance, positive/negative case, control, failure rule, comparator or frozen evidence changed. MILESTONE_11.md remains unchanged. The capability test passed separately; the full M11 test suite and comparator passed.

## Executed automated gates

| Gate                                        | Actual result                                                                                        |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| M13 production matrix                       | 15 positive; 17 negative; 270 field comparisons passed                                               |
| M13 focused production                      | 55 tests passed                                                                                      |
| Updated M11 capability test                 | 1 test passed separately                                                                             |
| Complete Python                             | 339 tests passed                                                                                     |
| Complete TypeScript                         | 208 tests in 19 files passed                                                                         |
| Complete browser                            | 31 tests passed                                                                                      |
| Independent M8 / M8.1 / M8.2                | 7 / 28 / 25 tests passed                                                                             |
| Independent Pre-M10 / Pre-M11 / Pre-M13     | 23 / 55 / 46 tests passed                                                                            |
| Pre-M13 frozen reproduction                 | Two fresh independent subprocesses reproduced identical frozen JSON bytes                            |
| M8 comparison                               | 122 comparisons passed                                                                               |
| M8.1 comparison                             | 325 comparisons passed                                                                               |
| M8.2 comparison and scan                    | 749 comparisons; 1,152/1,152 states on 9 high_accuracy grids; zero unexpected failures               |
| M10 production                              | 35 tests; 1,526 comparisons passed                                                                   |
| M11 production                              | 53 tests; 29 positive, 9 negative/gap; 401 positive field comparisons passed                         |
| M12 focused production                      | 36 tests; 14 positive, 15 negative; 1,264 comparisons passed                                         |
| Contracts / lint / TypeScript types         | All passed; public contracts unchanged                                                               |
| Repository formatting / syntax / whitespace | All passed                                                                                           |
| Production build                            | Passed                                                                                               |
| Production smoke                            | 17 pages, 17 PNG cards, links, 404s, indexing and disabled contact delivery passed                   |
| Production artifact determinism             | Fresh-process byte equality passed                                                                   |
| Protected integrity                         | 288 of 291 pre-existing tracked files hash-identical; only three explicitly authorized files changed |

The historical M8.1 standard-profile caloric diagnostic retains its known non-gating failure; qualified high_accuracy protection passes unchanged. Browser and complete Python tests used permission for local server fixtures. The initial smoke attempt on port 3113 used the default site URL and correctly returned origin rejection; rerunning with SITE_URL=http://127.0.0.1:3113 passed without product changes. Next-generated next-env.d.ts returned to its baseline contents after type generation/build. No incidental tracked changes remain.

## Human-operated validation — 2026-09-30

The human reviewer reported successful completion on 2026-09-30, separately from the automated acceptance recorded above. The reviewer executed the production comparator modes `liquid`, `two_phase`, `vapor`, `bubble`, `dew`, `pure`, `negative` and `summary`. All reviewed modes passed.

The review directly confirmed:

- Single-liquid, vapor-liquid and single-vapor PS recovery; bubble-boundary and dew-boundary behavior on both sides.
- Accepted pure methane and pure n-hexane states; recovered equilibrium entropy and enthalpy.
- All 17 negative/failure cases, with no accepted state for failures; pure-component coexistence-gap, ambiguity and property-hole rejection.
- `high_accuracy` nested PT and one qualified candidate for reviewed positive cases.
- The deterministic/call-order qualification summary.

The final summary reported:

```text
PASS: 15 positive; 17 negative; 270 field comparisons;
determinism/call order passed
```

This human validation record preserves the existing qualified scope and all limitations below.

## Reproduction and human-review commands

Run from the repository root. Every selector runs the full production matrix and determinism checks, then displays concise selected results. The reviewer need not manually rerun repository-wide suites.

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case liquid
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case two_phase
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case vapor
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case bubble
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case dew
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case pure
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case near_zero
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case negative
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --case summary
```

The positive views show P, target S, recovered T, phase/beta, entropy residual, H_eq, high_accuracy, candidate count/bracket and each frozen field comparison. Summary identifies maxima and allowances. Negative view explicitly shows no accepted state. These reproduction commands include `near_zero`; the modes reported as human-operated are recorded separately above.

```sh
# Read-only production artifact verification
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --verify
# Explicit write of production evidence only
engine/.venv/bin/python -B benchmarks/peng_robinson_ps/compare_production.py --write
# Production and independent tests
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p test_pr_ps_flash.py -v
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ps -p test_reference.py -v
.local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_ps/reference.py
```

Historical commands executed are the unchanged comparison commands for peng_robinson, peng_robinson_pt_boundary, peng_robinson_pt_vapor_parent (`--case all` includes the full scan), peng_robinson_caloric, peng_robinson_ph (`--case summary`) and heater_cooler_energy. Independent suites used `.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/<directory> -p "test_*.py" -q`. Focused production suites used PYTHONPATH=engine and engine/.venv for test_pr_caloric.py, test_pr_ph_flash.py and test_heater_cooler_energy.py.

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
npm run contracts:check
npm run lint
npm run test
npm run format:check
npm run test:e2e
NEXT_TELEMETRY_DISABLED=1 npm run typecheck
NEXT_TELEMETRY_DISABLED=1 npm run build
# In separate terminals for the production smoke
SITE_URL=http://127.0.0.1:3113 npm run start -- --port 3113
SMOKE_URL=http://127.0.0.1:3113 npm run smoke
git diff --check
```

## Integrity, exact change scope and limitations

Existing files modified: `engine/riogineer_engine/property_packages.py` (PS protocol/dispatch/capability); `engine/tests/test_pr_ph_flash.py` (authorized capability-only assertion/name); `docs/RIOGINEER_MASTER_CONTEXT.md` (minimal post-acceptance current-state update).

New files: `engine/riogineer_engine/pr_ps_flash.py`; `engine/tests/test_pr_ps_flash.py`; `benchmarks/peng_robinson_ps/compare_production.py`; `benchmarks/peng_robinson_ps/production_comparison.json`; `MILESTONE_13.md`. All prior independent files, milestone records, M8/M8.1/M8.2/M9/M10/M11/M12 numerical code/evidence and public contracts remain unchanged. Temporary logs/hash snapshots/report-generation helper reside outside the repository under /tmp. Changes remain unstaged; no commit or push was made.

Qualification is limited to the frozen methane/n-hexane pure/binary matrix, explicit constant zero kij, M10 convention and bounded 200–500 K inversion. Sampled pressures are 1000, 100000, 101325, 300000, 1000000, 6000000 and 30000000 Pa absolute; accepting a positive finite pressure in the API is not blanket pressure qualification. No water, arbitrary petroleum mixtures/nonzero BIPs, VLLE, three-phase/reaction equilibrium, critical-region or general retrograde qualification is claimed. Pure coexistence interpolation remains unavailable. A finite complete scan establishes observed candidates only, not mathematical global uniqueness.

M13 supplies standalone thermodynamic inversion and H_eq for future separately authorized equipment work. No compressor, turbine, valve, efficiency, shaft power, equipment PS integration or process-contract PS specification is implemented.

**Milestone 13 automated acceptance is complete. Human-operated validation is complete — 2026-09-30.**
