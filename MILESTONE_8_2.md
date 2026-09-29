# Milestone 8.2 — Production vapor-parent / liquid-trial PT restart

M8.2 automated acceptance: **COMPLETE — 2026-09-29**. Separately, M8.2 human-operated validation: **COMPLETE — 2026-09-29**, as reported by the human reviewer. **M11 remains NOT IMPLEMENTED.**

## Scope and independent authority

M8.2 extends only the existing production stability-derived PT initialization dispatch in `engine/riogineer_engine/pr_flash.py`. The unchanged committed `PRE_M8_2_PT_VAPOR_PARENT_QUALIFICATION.md` and `benchmarks/peng_robinson_pt_vapor_parent/methane_nhexane_pt_vapor_parent_reference.json` are the independent numerical authority (`independent_pr_pt_vapor_parent_restart@1.0`). All 25 independent tests pass unchanged.

The previous complete Pre-M11 scan had 1,148 successes and four initialization failures. Stability correctly found instability, Wilson K had no interior RR root, and M8.1 rejected the vapor-parent/liquid-trial orientation. This was not an RR equation or caloric defect.

## Runtime mapping and implementation

The existing converged stability trials retain normalized composition w and TPD/RT. Production derives S=exp(-TPD/RT). Parent and trial phase character come from the PIP of their minimum-Gibbs EOS roots, not from pressure, temperature, Wilson signs, expected beta or fixture identity.

Preserving K=y/x:

- Liquid parent / vapor trial: **K=S\*w/z**, unchanged M8.1 formula.
- Vapor parent / liquid trial: **K=z/(S\*w)**, new M8.2 formula, equivalent to phi_L(trial)/phi_V(parent) at stationarity.

For a vapor parent, unnormalized W=z*phi_V/phi_L=S*w; therefore the physical K is z/W. Dropping S would lose the instability magnitude and leave a normalized-composition endpoint seed.

The existing trigger remains converged instability plus an initial Wilson RR endpoint tendency. Only a qualified opposite orientation supplies a seed; stable states and normal Wilson-root states do not restart. PIP exactly one or nonfinite values fail explicitly. Candidate selection remains deterministic. Positive binary feed/trial validation, finite positive K and S>1 guards remain in place. Pure and zero-inventory feeds retain their established semantics.

There is at most one restart. The seed must establish an interior physical RR root and then pass ordinary fugacity iteration, material closure and final equilibrium stability. Failed construction/nonconvergence publishes no phases, beta or final K. No EOS, stability mathematics, RR implementation/domain/tolerance, M10 caloric arithmetic/data, process equipment, contract, dependency or UI change was made.

Standard remains the default with maximum log-fugacity target 1e-11; explicit high_accuracy remains 1e-12. Iteration budgets are unchanged. Existing diagnostics expose orientation, parent/trial PIP, normalized trial, S, seed K, restart RR, count, settings and final residual.

## Four former failures

All states use 1,000 Pa absolute, ordered z=[0.5 methane, 0.5 n_hexane], and the explicit zero-kij benchmark specification. All have unstable feed stability, Wilson `vapor_tendency` without a physical interior root, one vapor-parent/liquid-trial restart, and final `vapor_liquid` / `success_two_phase`.

| T / K            | Profile       | Wilson         | Orientation               | Restarts | Final beta        | Phase        | Iterations | Max log-fugacity residual | Result |
| ---------------- | ------------- | -------------- | ------------------------- | -------- | ----------------- | ------------ | ---------- | ------------------------- | ------ |
| 225.984251968504 | standard      | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.697379882398025 | vapor_liquid | 4          | 2.17449756118038e-14      | PASS   |
| 225.984251968504 | high_accuracy | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.697379882398025 | vapor_liquid | 4          | 2.17449756118038e-14      | PASS   |
| 228.346456692913 | standard      | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.760162976345697 | vapor_liquid | 4          | 3.94180673345124e-15      | PASS   |
| 228.346456692913 | high_accuracy | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.760162976345697 | vapor_liquid | 4          | 3.94180673345124e-15      | PASS   |
| 230.708661417323 | standard      | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.850353181708272 | vapor_liquid | 3          | 7.30169104432715e-12      | PASS   |
| 230.708661417323 | high_accuracy | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.850353181703923 | vapor_liquid | 4          | 3.05224595598119e-15      | PASS   |
| 233.070866141732 | standard      | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.987859250435804 | vapor_liquid | 3          | 4.7202454618589e-13       | PASS   |
| 233.070866141732 | high_accuracy | vapor_tendency | vapor_parent_liquid_trial | 1        | 0.987859250435804 | vapor_liquid | 3          | 4.7202454618589e-13       | PASS   |

## Former-failure production-versus-frozen errors

Absolute errors below use the existing frozen allowances. Values include both components; full production/reference values, relative errors and allowances are retained per comparison in `production_comparison.json`. No zero-reference relative error is fabricated.

| T / K            | Profile       | beta                 | x CH4                | x nC6                | y CH4                | y nC6                | Z_L                  | Z_V                  | K CH4                | K nC6                |
| ---------------- | ------------- | -------------------- | -------------------- | -------------------- | -------------------- | -------------------- | -------------------- | -------------------- | -------------------- | -------------------- |
| 225.984251968504 | standard      | 1.04360964314765e-14 | 2.53432257818487e-18 | 0                    | 6.88338275267597e-15 | 7.04991620636974e-15 | 1.35525271560688e-20 | 0                    | 1.72803993336856e-10 | 7.04991620636974e-15 |
| 225.984251968504 | high_accuracy | 1.04360964314765e-14 | 2.53432257818487e-18 | 0                    | 6.88338275267597e-15 | 7.04991620636974e-15 | 1.35525271560688e-20 | 0                    | 1.72803993336856e-10 | 7.04991620636974e-15 |
| 228.346456692913 | standard      | 1.22124532708767e-15 | 1.49077798716757e-19 | 1.11022302462516e-16 | 1.55431223447522e-15 | 1.38777878078145e-15 | 1.35525271560688e-20 | 0                    | 3.63797880709171e-12 | 1.4432899320127e-15  |
| 228.346456692913 | high_accuracy | 1.22124532708767e-15 | 1.49077798716757e-19 | 1.11022302462516e-16 | 1.55431223447522e-15 | 1.38777878078145e-15 | 1.35525271560688e-20 | 0                    | 3.63797880709171e-12 | 1.4432899320127e-15  |
| 230.708661417323 | standard      | 4.35007585508629e-12 | 1.59919820441612e-18 | 0                    | 3.00914848594402e-12 | 3.00920399709526e-12 | 2.71050543121376e-20 | 2.99760216648792e-15 | 4.67516656499356e-08 | 3.00937053054895e-12 |
| 230.708661417323 | high_accuracy | 1.55431223447522e-15 | 2.84603070277445e-19 | 0                    | 1.11022302462516e-15 | 9.99200722162641e-16 | 2.71050543121376e-20 | 2.22044604925031e-16 | 2.18278728425503e-11 | 9.99200722162641e-16 |
| 233.070866141732 | standard      | 4.53082016349526e-13 | 2.77826806699411e-19 | 0                    | 2.32036612146658e-13 | 2.3214763444912e-13  | 1.35525271560688e-20 | 1.11022302462516e-16 | 4.25825419370085e-09 | 2.3214763444912e-13  |
| 233.070866141732 | high_accuracy | 4.53082016349526e-13 | 2.77826806699411e-19 | 0                    | 2.32036612146658e-13 | 2.3214763444912e-13  | 1.35525271560688e-20 | 1.11022302462516e-16 | 4.25825419370085e-09 | 2.3214763444912e-13  |

Inherited PH beta/composition allowance is 1e-9+1e-9*abs(reference); Z is 1e-10+1e-9*abs(reference). Log-phi, material and RR checks use inherited M8 tolerances. K allowances are the exact interval propagated from frozen x/y allowances, as already used in Pre-M8.2/M8.1; no K tolerance was relaxed. Each profile also independently passes its stricter resolved fugacity target.

## Complete 13-state neighborhood

Both profiles pass every row. Their categorical outcomes, restart orientation and counts agree. “None” denotes no restart, not missing phase-stability evidence.

| T / K            | Frozen phase | Production phase | Stability | Wilson physical root | Restart orientation       | Count | Standard / high |
| ---------------- | ------------ | ---------------- | --------- | -------------------- | ------------------------- | ----- | --------------- |
| 220              | vapor_liquid | vapor_liquid     | unstable  | True                 | None                      | 0     | PASS / PASS     |
| 224              | vapor_liquid | vapor_liquid     | unstable  | True                 | None                      | 0     | PASS / PASS     |
| 225.984251968504 | vapor_liquid | vapor_liquid     | unstable  | False                | vapor_parent_liquid_trial | 1     | PASS / PASS     |
| 228.346456692913 | vapor_liquid | vapor_liquid     | unstable  | False                | vapor_parent_liquid_trial | 1     | PASS / PASS     |
| 230.708661417323 | vapor_liquid | vapor_liquid     | unstable  | False                | vapor_parent_liquid_trial | 1     | PASS / PASS     |
| 233.070866141732 | vapor_liquid | vapor_liquid     | unstable  | False                | vapor_parent_liquid_trial | 1     | PASS / PASS     |
| 233.2            | vapor_liquid | vapor_liquid     | unstable  | False                | vapor_parent_liquid_trial | 1     | PASS / PASS     |
| 233.234          | vapor_liquid | vapor_liquid     | unstable  | False                | vapor_parent_liquid_trial | 1     | PASS / PASS     |
| 233.2341         | vapor_liquid | vapor_liquid     | unstable  | False                | vapor_parent_liquid_trial | 1     | PASS / PASS     |
| 233.2342         | single_vapor | single_vapor     | stable    | False                | None                      | 0     | PASS / PASS     |
| 233.235          | single_vapor | single_vapor     | stable    | False                | None                      | 0     | PASS / PASS     |
| 234              | single_vapor | single_vapor     | stable    | False                | None                      | 0     | PASS / PASS     |
| 240              | single_vapor | single_vapor     | stable    | False                | None                      | 0     | PASS / PASS     |

Four stable vapor controls never restart or publish liquid. The two normal-Wilson controls keep their normal initialization. Seven neighborhood states use the newly qualified restart; only four of those temperatures occur in the complete frozen scan below.

## Profiles, determinism and prior blockers

The comparator verifies standard → high_accuracy → standard exact result/settings equality, repeated high_accuracy equality, and identical standard results after stable vapor and M8.1 restart calls. No continuation between temperatures is used. Full result dictionary equality includes thermodynamic fields, settings, seed, count, iterations and residuals. The focused tests verify both formulas and would reject swapped mappings.

The original M8.1 bubble center at 231.29921259842519 K / 6 MPa continues to use liquid-parent/vapor-trial initialization and passes its frozen comparisons. The exact frozen dew state is evaluated with high_accuracy and existing M10 caloric properties and passes its inherited comparisons. No PH inversion was implemented for these rechecks. The required unchanged M8.1 comparator also retains its existing local conditioning diagnostic.

## Complete frozen Pre-M11 PT scan

The comparator deduplicates the exact committed scan arrays by P, z and temperature sequence. It checks for nine grids and 1,152 total entries, then independently executes normal production PT at every frozen temperature with explicit high_accuracy. It does not skip points, change spacing, carry phase state between points or inject reference phase values.

- Frozen grids: **9**.
- Total states evaluated: **1,152**.
- Successfully handled states: **1,152**.
- Unexpected failures: **0**.
- Vapor-parent/liquid-trial restarts: **4**.
- Liquid-parent/vapor-trial restarts: **1**.
- States without a restart: **1,147**.

The scan is PT evaluability coverage, not PH implementation or PH acceptance. The Pre-M11 benchmark remains unchanged. Per-state results and input hash are retained in the separate production comparison artifact.

## Production comparison and maximum errors

**749 comparisons passed.** This count includes both profiles for the 13-state neighborhood, categorical and initialization checks, isolation/determinism checks and M8.1 bubble/dew protection. The scan is reported separately and is not inflated into that comparison count.

The following maxima include the M8.1 bubble/dew protection checks as well as the new neighborhood. Maximum absolute and maximum relative error for a quantity need not occur in the same state.

| Quantity                    | Maximum absolute error | Maximum relative error | Largest fraction of allowed error |
| --------------------------- | ---------------------- | ---------------------- | --------------------------------- |
| beta                        | 9.06095294281317e-12   | 4.31582049342059e-09   | 0.00904196956274829               |
| vapor.composition.methane   | 3.00914848594402e-12   | 5.117777045732e-12     | 0.00189495412361525               |
| vapor.composition.n_hexane  | 3.00920399709526e-12   | 8.63628250517582e-12   | 0.00213113350992854               |
| vapor.Z                     | 1.31838984174237e-12   | 1.89267795320684e-12   | 0.00165507561256315               |
| liquid.composition.methane  | 4.53981296999473e-12   | 9.09872739687282e-12   | 0.00302866139158972               |
| liquid.composition.n_hexane | 4.53981296999473e-12   | 9.06060451655724e-12   | 0.00302442553259353               |
| liquid.Z                    | 1.0012546347582e-12    | 3.8894843498581e-12    | 0.00280129163635929               |
| K.methane                   | 4.67516656499356e-08   | 9.0987357088279e-12    | 0.00181782510935025               |
| K.n_hexane                  | 3.00937053054895e-12   | 9.08127223012889e-12   | 0.0013457324144694                |

## Historical test semantics and failure protection

The original `test_unstable_state_without_rr_bracket_is_failure` dates to M8 commit `bec5088`, which had no restart path. Mocking Wilson K=(2,3) at qualified Case B produced an endpoint and immediate failure. Its unconditional PT-failure expectation became obsolete when the independently justified vapor-parent recovery was added. Following a read-only audit and explicit user authorization, only that historical test was replaced with `test_unstable_no_root_wilson_recovers_via_qualified_restart`.

The replacement preserves exact mocked K, unchanged RR `vapor_tendency` and positive endpoint residuals, verifies converged instability, one runtime-derived restart with the correct formula, an interior restart RR root, ordinary convergence and final stability, frozen beta/x/y/Z comparisons with historical tolerances, and the resolved standard fugacity target. It does not require bitwise equality between distinct iteration paths.

No existing genuine failure tests were removed. The 23 new M8.2 production tests cover the matrix, profile isolation, formulas, stable and normal-Wilson controls, invalid S/trials/orientation, zero inventory, nonconvergence, bounded RR restart and candidate ordering. The added integration test injects `ThermodynamicError` from seed construction and verifies controlled status/message with no phases, beta, final K or phase classification.

## Final automated validation

All rows below were actually rerun successfully after the authorized test update. The previous partial/interrupted runs are not counted as final acceptance.

| Gate                                          | Final result                                                                       |
| --------------------------------------------- | ---------------------------------------------------------------------------------- |
| Modified historical test + focused M8.2 tests | 24 passed: 1 revised + 23 new                                                      |
| Pre-M8 independent                            | 7 passed                                                                           |
| M8 production comparison                      | 122 passed                                                                         |
| Pre-M8.1 independent                          | 28 passed                                                                          |
| M8.1 production comparison                    | 325 passed                                                                         |
| Pre-M8.2 independent, unchanged               | 25 passed                                                                          |
| M8.2 production comparison                    | 749 passed                                                                         |
| Relevant M9 equipment integration             | 7 passed                                                                           |
| Pre-M10 independent                           | 23 passed                                                                          |
| M10 production comparison                     | 1,526 passed                                                                       |
| Pre-M11 independent                           | 55 passed                                                                          |
| Complete Python suite                         | 195 passed                                                                         |
| Complete TypeScript suite                     | 200 passed across 18 files                                                         |
| Complete browser suite                        | 31 passed                                                                          |
| Contracts / ESLint / formatting               | Passed                                                                             |
| Type checking                                 | Passed                                                                             |
| Python AST syntax                             | 50 files passed                                                                    |
| Whitespace / git diff --check                 | Passed                                                                             |
| Production build                              | Passed                                                                             |
| Production smoke                              | 17 pages, 17 PNG cards, links, 404s, preview indexing and disabled delivery passed |
| Exact frozen PT grid scan                     | 1,152 / 1,152 passed                                                               |

The initial sandbox could not bind localhost for HTTP/browser tests. Final runs used the normal commands with OS permission to bind the local test servers. Smoke initially used port 3210 with a mismatched default site origin and correctly received contact HTTP 403. Restarting with the documented `SITE_URL=http://127.0.0.1:3210` and matching `SMOKE_URL` produced the final successful run; neither product code nor smoke assertions changed. No live external LLM/provider call was made.

## Integrity and files

A pre-implementation SHA-256 snapshot covers 259 tracked files. Except for the intentionally modified production flash, authorized historical test and this milestone's minimal Master Context update, all baseline files remain byte-identical. In particular, all committed Pre-M8.2 independent files, Pre-M8/M8, Pre-M8.1/M8.1, Pre-M10/M10, Pre-M11 and M9 fixture evidence are unchanged. No benchmark tolerance, RR file, caloric data, EOS equation, contract or existing process equipment changed. Browser-generated `next-env.d.ts` changes were restored; temporary diagnostics remain outside the repository.

Created:

- `benchmarks/peng_robinson_pt_vapor_parent/compare_production.py`
- `benchmarks/peng_robinson_pt_vapor_parent/production_comparison.json`
- `engine/tests/test_pr_pt_vapor_parent.py`
- `MILESTONE_8_2.md`

Modified:

- `engine/riogineer_engine/pr_flash.py`
- `engine/tests/test_pr_flash.py` (one explicitly authorized historical test)
- `docs/RIOGINEER_MASTER_CONTEXT.md`

No staging, commit or push occurred. These seven intentional files remain available for human inspection.

## Human-operated validation — complete, 2026-09-29

The human reviewer reported successful execution and inspection of the documented `--case representative`, `--case former_failures`, `--case orientations` and `--case scan` commands from the repository root on 2026-09-29. This manual record is separate from the automated acceptance above; no comparator or thermodynamic calculation was rerun for this documentation update.

The representative state at 225.98425196850394 K matched frozen and production `vapor_liquid` classification. Stability identified instability, Wilson had no physical interior RR root, and exactly one `vapor_parent_liquid_trial` restart was used. Both standard and high_accuracy passed with beta 0.6973798823980246, maximum log-fugacity residual approximately 2.1745e-14 and frozen beta absolute error approximately 1.04e-14. Composition, Z and K comparisons, isolation, determinism and call-order checks passed.

For all four former failures, the reviewer confirmed unstable feed stability, no physical Wilson RR root, exactly one vapor-parent/liquid-trial restart, final vapor_liquid classification and passing frozen beta/composition/Z/K comparisons under both profiles:

| T / K              | Observed standard beta | Observed high_accuracy beta |
| ------------------ | ---------------------- | --------------------------- |
| 225.98425196850394 | 0.6973798823980246     | 0.6973798823980246          |
| 228.3464566929134  | 0.760162976345697      | 0.760162976345697           |
| 230.70866141732284 | 0.8503531817082717     | 0.8503531817039232          |
| 233.07086614173227 | 0.9878592504358039     | 0.9878592504358039          |

The orientations review explicitly displayed the existing M8.1 `liquid_parent_vapor_trial` seed alongside M8.2 `vapor_parent_liquid_trial` states. Normal Wilson-root states retained zero restarts; both profiles, isolation, determinism and call-order checks passed. Near the vapor boundary, 233.2341 K remained vapor_liquid with beta approximately 0.999999 and one restart, while 233.2342 K was stable single_vapor with zero restarts. The reviewer confirmed phase-boundary behavior without forced two-phase classification within the qualified scope.

The complete high_accuracy scan reported 9 grids, 1,152 total states, 1,152 successes, zero unexpected failures, four vapor_parent_liquid_trial restarts and one liquid_parent_vapor_trial restart. The displayed frozen reference SHA-256 was:

`e311738a66d7bedd37fe802f9b69297b35bf8f18aeb6e14eedd9a366af56a3b3`

Human validation does not broaden the documented M8.2 thermodynamic qualification. M11 remains NOT IMPLEMENTED.

The documented repository-root commands are retained below for reproduction, including the separate neighborhood selector. They do not write the frozen reference or implement PH. Each command performs the full 749-comparison gate; selectors control concise output. The scan command additionally runs every frozen PT grid state.

```sh
# Representative former failure: 225.98425196850394 K, both profiles
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case representative

# All four former failures, with field errors and allowances
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case former_failures

# Complete 13-state neighborhood, both profiles
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case neighborhood

# Complete 1,152-state high-accuracy scan summary
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case scan

# Coexistence of M8.1 and M8.2 restart orientations
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case orientations
```

`--write` is reserved for the separate production evidence artifact and never changes independent reference files; it is not needed for human review. The successful human inspection is recorded separately above.

## Limits and milestone boundary

Qualification remains scoped to the independent methane/n_hexane, explicit zero-kij evidence. It does not qualify arbitrary mixtures, nonzero BIPs, water, VLLE, critical/retrograde regions or other EOS models. The architecture is reusable; these tests do not establish broader thermodynamic coverage. No new production dependency was added.

M11 remains NOT IMPLEMENTED. Human-operated M8.2 validation and its documentation are complete; commit/push and a clean repository remain outstanding milestone prerequisites. This documentation task does not authorize starting M11. No PH/PS solver, `MILESTONE_11.md`, equipment energy integration or frontend PH controls were created.

**M8.2 automated acceptance: COMPLETE. M8.2 human-operated validation: COMPLETE — 2026-09-29. M11 remains NOT IMPLEMENTED.**
