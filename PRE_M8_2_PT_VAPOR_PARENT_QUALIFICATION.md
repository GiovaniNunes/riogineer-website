# Pre-M8.2 — Vapor-parent / liquid-trial PT restart qualification

Date: 2026-09-29. **READY FOR PRODUCTION M8.2.** This is independent numerical qualification only. Production M8.2 has not been implemented. **M11 remains BLOCKED and NOT IMPLEMENTED.** Human review of these new artifacts remains separate from automated qualification.

## Problem and scope

The prior read-only PH scan evaluated 1,152 states across nine frozen grids: 1,148 PT successes and four failures at 1,000 Pa absolute with ordered molar composition `[0.5 methane, 0.5 n_hexane]`. The four failures have converged instability evidence, but Wilson K gives `vapor_tendency` without an interior RR root. The existing M8.1 restart rejects their vapor-parent/liquid-trial orientation. These production observations motivate this study; they are not used as expected equilibrium outputs.

M8.1 independently qualified liquid-parent/vapor-trial initialization. This study qualifies the opposite orientation with the same definition K = y/x. It does not change EOS equations, stability, RR semantics, standard/high-accuracy targets, historical benchmarks, caloric data, contracts, equipment, documentation status elsewhere, or process UI.

## Independent method and provenance

Identity: `independent_pr_pt_vapor_parent_restart@1.0`. New artifacts live in `benchmarks/peng_robinson_pt_vapor_parent/`. Thermo 0.6.0, Chemicals 1.5.2, fluids 1.3.1, NumPy 2.2.6 and SciPy 1.15.3 run in the existing isolated `.local/pre-m8-venv`. The directory contains exact inherited dependency pins and third-party notices. No production dependency was added. Reproduction is offline and does not import production modules.

The unchanged Pre-M11 `IndependentPT` and Pre-M8.1 `Study` provide the separate full stability/PT reference and the RR/successive-substitution experiment. The frozen JSON records dependency versions, input-source hashes, the exact installed Michelsen function hash, inherited component constants, gas constant, PR coefficients and PH tolerances. Constants and the caloric convention are inherited unchanged from Pre-M11/Pre-M10. BIP is explicitly the symmetric zero matrix: **explicit zero-kij independent M8 benchmark; not fitted physical interaction data**. No physical interaction fit is implied.

Thermo's installed `thermo.flash.flash_utils.stability_iteration_Michelsen` owns the stationary iteration. Its internal `Ks` represent unnormalized **trial/parent** ratios, not automatically physical vapor/liquid K. The frozen artifact records these internal ratios to verify that distinction. The separate full flash supplies equilibrium; its final K is never used to construct the restart seed.

Each liquid-trial evaluation constructs a fresh EOS state and selects `lnphis_lowest_Gibbs()`. This matters: a reused gas-only `lnphis_at_zs` path can stay on the gas branch and return the trivial parent trial despite a nominal most-stable argument. The study checks that the minimum-G parent root matches the vapor root and the final minimum-G trial root matches the liquid root. It does not mistake a class label for root evidence.

## Derivation from the stationary equations

At fixed T/P, let parent composition be z, normalized trial composition w, and parent/trial fugacity coefficients be phi_p and phi_t. Michelsen's fixed-point correction is parent fugacity divided by trial fugacity and the current unnormalized sum. At stationarity:

```text
W_i = z_i * phi_p,i / phi_t,i
S = sum_i W_i
w_i = W_i / S
ln(w_i) + ln(phi_t,i) - ln(z_i) - ln(phi_p,i) = -ln(S)
TPD(w)/(RT) = -ln(S)
```

The equality of phase fugacities gives `x_i phi_L,i = y_i phi_V,i`, hence `K_i = y_i/x_i = phi_L,i/phi_V,i`.

For a vapor parent and liquid trial, `phi_p = phi_V(z)` and `phi_t = phi_L(w)`. Therefore:

```text
K_seed,i = phi_L,i(w) / phi_V,i(z)
         = z_i / W_i
         = z_i / (S*w_i)
```

This is the inverse of the **parent/trial** fugacity ratio, but the direct physical **liquid/vapor** ratio. It is derived from stationarity and fugacity equality, not fitted to equilibrium. The trial is incipient stability evidence, not the final liquid composition or a prescribed phase fraction. S retains the instability magnitude.

For M8.1's liquid parent and vapor trial, the same stationary equations instead give `K_seed = W/z = S*w/z`. Both mappings preserve K=y/x. Orientation must be established before selecting either expression.

## Normalization and physical RR

For `F(beta) = sum z_i*(K_i-1)/(1+beta*(K_i-1))`, the physical domain is `[0,1]`. All derived unstable seeds have F(0)>0 and F(1)<0, so the monotone RR function has a genuine interior root. No beta or K is forced or clamped.

For the new orientation, `F(1)=1-S<0`. Using only normalized `K=z/w` instead gives `F(1)=1-sum(w)=0`: the vapor endpoint, with no finite liquid amount. Its floating-point endpoint residual may have either sign at roughly 1e-16. The artifact labels that analytically known endpoint explicitly; a tiny negative rounding residual is not evidence of an interior root. For M8.1's opposite orientation, `F(0)=S-1>0`, whereas normalized `w/z` loses the magnitude and gives F(0)=0.

The following endpoint values and phase data are generated directly from the new frozen JSON. Component arrays always follow methane, n_hexane. Full precision, normalized and unnormalized trials, phi, PIP, iteration histories and comparison allowances remain in JSON.

## Four original failures: stability and seed evidence

| T / K            | S                | TPD/RT              | parent PIP        | trial PIP        |
| ---------------- | ---------------- | ------------------- | ----------------- | ---------------- |
| 225.984251968504 | 1.76593678208463 | -0.568681304306963  | 0.998905755579208 | 15.8529016679236 |
| 228.346456692913 | 1.46059473755871 | -0.378843707266198  | 0.99893217425952  | 15.659243288035  |
| 230.708661417323 | 1.21342873424201 | -0.193450017012122  | 0.99895772252704  | 15.4696838930325 |
| 233.070866141732 | 1.0124359985513  | -0.0123593066932805 | 0.998982437151934 | 15.2840969043482 |

| T / K            | Wilson F(0)      | Wilson F(1)          | normalized-only F(0) | normalized-only F(1)  | derived F(0)     | derived F(1)        | derived beta      |
| ---------------- | ---------------- | -------------------- | -------------------- | --------------------- | ---------------- | ------------------- | ----------------- |
| 225.984251968504 | 5389.02837697168 | 0.000726750945739041 | 7491.81760918599     | -2.22044604925031e-16 | 4241.97046485489 | -0.765936782084635  | 0.697432477506665 |
| 228.346456692913 | 5650.73409204618 | 0.150523213480811    | 6416.56308813013     | 5.55111512312578e-17  | 4392.80132154704 | -0.460594737558713  | 0.760213943702819 |
| 230.708661417323 | 5919.39969622591 | 0.27545824903312     | 5514.60054723127     | 0                     | 4544.46722983011 | -0.213428734242006  | 0.850392434260748 |
| 233.070866141732 | 6195.00570627006 | 0.380022307826811    | 4755.25419028375     | -1.66533453693773e-16 | 4696.83195884925 | -0.0124359985513007 | 0.987863251027114 |

## Separate full equilibrium and restart convergence

All four independently reproduce the committed Pre-M11 scan beta values. Each full equilibrium is vapor_liquid. The full library flash requires three iterations for each; stationary liquid trials require four callback evaluations each. These counts describe different algorithms.

| T / K            | equilibrium beta  | x                                         | y                                      | Z_L                  | Z_V               |
| ---------------- | ----------------- | ----------------------------------------- | -------------------------------------- | -------------------- | ----------------- |
| 225.984251968504 | 0.697379882398014 | [8.44781041721593e-05, 0.999915521895828] | [0.7169326902677, 0.2830673097323]     | 6.41012679033976e-05 | 0.999779183972425 |
| 228.346456692913 | 0.760162976345696 | [7.48439714453317e-05, 0.999925156028555] | [0.65773007263284, 0.34226992736716]   | 6.35623394135514e-05 | 0.999736326024802 |
| 230.708661417323 | 0.850353181703922 | [6.46772064076404e-05, 0.999935322793592] | [0.587979597206861, 0.412020402793139] | 6.30362459737677e-05 | 0.999681092449362 |
| 233.070866141732 | 0.987859250435351 | [5.38726160037231e-05, 0.999946127383996] | [0.506144317346535, 0.493855682653465] | 6.25226366439068e-05 | 0.999609921476984 |

| T / K            | final K                               | phi_L                                 | phi_V                                 | full flash max log-fugacity residual |
| ---------------- | ------------------------------------- | ------------------------------------- | ------------------------------------- | ------------------------------------ |
| 225.984251968504 | [8486.60960485869, 0.283091224742274] | [8486.66352943113, 0.28286594141377]  | [1.00000635407718, 0.999204202360181] | 3.60215329786584e-15                 |
| 228.346456692913 | [8788.01672240584, 0.34229554612524]  | [8788.30255703575, 0.342010602779181] | [1.00003252549909, 0.999167551698281] | 3.37230243729891e-15                 |
| 230.708661417323 | [9090.98629741377, 0.412047052845425] | [9091.60570282491, 0.411688257703291] | [1.00006813401658, 0.999129237450785] | 5.35953659924759e-15                 |
| 233.070866141732 | [9395.20585582026, 0.493882289384392] | [9396.29986502834, 0.493433517832102] | [1.0001164433462, 0.999091339045891]  | 7.48804230427114e-16                 |

| T / K            | standard iterations | standard residual    | high iterations | high residual        |
| ---------------- | ------------------- | -------------------- | --------------- | -------------------- |
| 225.984251968504 | 4                   | 3.60193645743134e-15 | 4               | 3.60193645743134e-15 |
| 228.346456692913 | 4                   | 3.81639164714898e-15 | 4               | 3.81639164714898e-15 |
| 230.708661417323 | 3                   | 7.32395828012544e-12 | 4               | 1.79603510883086e-15 |
| 233.070866141732 | 3                   | 4.6679435490582e-13  | 3               | 4.6679435490582e-13  |

The independent SS experiment starts from the stability seed, solves RR in [0,1], reconstructs x/y, evaluates the phase fugacities and updates K=phi_L/phi_V. Standard and high targets remain 1e-11 and 1e-12 respectively. Both agree with the separate full equilibrium under inherited acceptance limits.

## Extended neighborhood and restart gating

| T / K            | independent phase | beta              | Wilson RR      | restart required | standard/high iterations |
| ---------------- | ----------------- | ----------------- | -------------- | ---------------- | ------------------------ |
| 220              | vapor_liquid      | 0.603336511192069 | two_phase      | False            | 4/4                      |
| 224              | vapor_liquid      | 0.658264854479915 | two_phase      | False            | 4/4                      |
| 225.984251968504 | vapor_liquid      | 0.697379882398014 | vapor_tendency | True             | 4/4                      |
| 228.346456692913 | vapor_liquid      | 0.760162976345696 | vapor_tendency | True             | 4/4                      |
| 230.708661417323 | vapor_liquid      | 0.850353181703922 | vapor_tendency | True             | 3/4                      |
| 233.070866141732 | vapor_liquid      | 0.987859250435351 | vapor_tendency | True             | 3/3                      |
| 233.2            | vapor_liquid      | 0.997427519334506 | vapor_tendency | True             | 3/3                      |
| 233.234          | vapor_liquid      | 0.999991442919406 | vapor_tendency | True             | 2/2                      |
| 233.2341         | vapor_liquid      | 0.999999011800079 | vapor_tendency | True             | 2/2                      |
| 233.2342         | single_vapor      | 1                 | vapor_tendency | False            | not run                  |
| 233.235          | single_vapor      | 1                 | vapor_tendency | False            | not run                  |
| 234              | single_vapor      | 1                 | vapor_tendency | False            | not run                  |
| 240              | single_vapor      | 1                 | vapor_tendency | False            | not run                  |

The 13 deterministic states include nine VLE states and four stable vapors. The dew transition is bracketed by 233.2341 and 233.2342 K. At 220 and 224 K, Wilson already has a physical root: the proposed restart is not requested. Derived-seed experiments are also run at those VLE controls solely to check consistency; they do not imply that production should restart there. At stable controls, S<1 and the separate full stability/flash returns single vapor. No restart experiment is run and no liquid phase is published.

Orientation uses the selected parent/trial EOS roots and their phase identification parameter (PIP): parent<1/trial>1 identifies vapor/liquid; parent>1/trial<1 identifies liquid/vapor. Equal-to-one, nonfinite, same-side or otherwise ambiguous evidence must fail explicitly. This follows the [Chemicals PIP definition and phase convention](https://chemicals.readthedocs.io/chemicals.utils.html#chemicals.utils.phase_identification_parameter). It is not a pressure, temperature, K-magnitude or expected-beta heuristic. The new study verifies both orientation branches algebraically; the unchanged Pre-M8.1 tests retain numerical qualification of the opposite branch.

A future restart must additionally require converged, nontrivial negative-TPD evidence and the existing initial-Wilson no-interior-root condition. S alone is not a replacement for complete stability analysis. Here negative stationary TPD agrees with the separate full stability/PT classification at every state. Positive TPD from a single trial alone would not prove global stability; stable controls are also checked by the full independent oracle.

## Precision, tolerances and iteration budgets

No historical tolerance is changed. State comparisons use inherited Pre-M11 absolute+relative allowances: beta/composition 1e-9+1e-9*abs(reference); Z 1e-10+1e-9*abs(reference). Log-phi uses inherited M8 1e-9+1e-9*abs(reference), fugacity closure 1e-9 and material closure 1e-10. Final K is compared with the interval induced by the inherited x/y allowances, not a newly relaxed K threshold. The stricter standard/high log-fugacity stopping targets are also asserted independently.

RR uses the unchanged independent bracketed helper (SciPy brentq, xtol=1e-16, rtol=1e-15); every iteration's RR residual is checked <=2e-14. This shows a physical root without changing RR semantics or requiring a looser tolerance. It does not qualify a modified production RR algorithm. No RR tolerance change is recommended.

All experiments finish in 2–4 outer iterations, well inside production's 100-iteration budget. The inherited experimental helper has a 200-iteration ceiling; this study separately asserts <=100 for every run. Its stationary Michelsen helper retains maxiter=1000 and xtol=1e-24 from the independent stack, but the actual trials take four evaluations. Neither independent setting is a request to change production settings. No iteration-limit increase is justified.

## Tests, regressions and reproducibility

New independent suite: **25 tests passed** (13 state-specific tests and 12 algebra, orientation, gating, invalid-input, independence and determinism tests). Two independent rebuilds equal the frozen object; the normal reference command also checks exact serialized reproduction. Each VLE state checks beta, x/y, Z, K, log-phi, fugacity/material closure, physical RR through the iteration history and both precision profiles. Stable states check no restart and absent liquid output. Invalid orientation, nonfinite/zero inputs, non-normalized compositions and unsupported dimensions fail explicitly.

Historical checks, all executed without reference generation:

| Check                      | Result                   |
| -------------------------- | ------------------------ |
| Pre-M8 independent tests   | 7 passed                 |
| M8 production comparison   | 122 comparisons passed   |
| Pre-M8.1 independent tests | 28 passed                |
| M8.1 production comparison | 325 comparisons passed   |
| Pre-M10 independent tests  | 23 passed                |
| M10 production comparison  | 1,526 comparisons passed |
| Pre-M11 independent tests  | 55 passed                |

Final SHA-256 verification confirmed all 253 pre-existing tracked files unchanged. Markdown Prettier checking, new-file whitespace checks, Python AST parsing and `git diff --check` passed. Only the new report and independent benchmark directory are untracked.

No production M11 suite was run: M11 does not exist. No live LLM/provider call was made. Public source documentation was consulted; benchmark reproduction performs no network calls. No production implementation or previous acceptance evidence was modified.

From repository root, using the already installed isolated environment:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/reference.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_vapor_parent -p 'test_*.py' -v
```

The reference script's `--write` option was used only to create this new artifact during qualification. Normal reproduction does not write or regenerate references. Exact pins for recreating an isolated environment are in the new directory's `requirements.txt`; no production installation is needed.

Historical reproduction commands:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_boundary -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ph -p 'test_*.py' -v
```

## Smallest proposed production correction — not implemented

Extend only the existing M8.1 stability-derived seed orientation dispatch. For converged vapor-parent/liquid-trial evidence, construct K=z/(S*w), equivalently phi_L(trial)/phi_V(parent), retaining the existing single restart, component guards, phase-identity checks, initial-Wilson trigger and physical RR validation. Preserve the liquid-parent branch, standard default, explicit high-accuracy policy, EOS equations and all residual/iteration limits. Add separately authorized production acceptance against this new frozen artifact before claiming M8.2 capability.

The four PT holes prevent conservative PH bracket discovery and uniqueness checking from evaluating the entire required scan. Skipping them could hide a crossing or break the continuity evidence used to justify a bracket. Changing PH scan policy to bypass failed thermodynamic evaluations would not resolve the PT limitation. M11 must stay blocked pending a separately authorized production correction and regression qualification.

## Limitations and disposition

This numerical qualification is restricted to the methane/n_hexane, positive binary, explicit zero-kij, 1,000 Pa neighborhood shown here. It is not universal phase-stability proof, critical-region qualification, multicomponent/VLLE support, pure-component coexistence handling or PH implementation. The full equilibrium and SS experiments are separate algorithms in the same independent Thermo stack, not two independently authored EOS libraries. Shared EOS systematics remain protected by the prior independent PR qualification, not eliminated by this restart study. Stable controls and PIP guards do not authorize extrapolation to ambiguous orientations.

All requested independent gates and historical checks passed. **READY FOR PRODUCTION M8.2** means ready for a separately authorized implementation; it does not mean production capability is present. **M11 remains BLOCKED.** No commit or push was performed.
