# Milestone 8 — Peng–Robinson EOS and Two-Phase PT Flash

## Objective and qualification boundary

Milestone 8 adds **standalone deterministic thermodynamic solver qualification** for methane/n_hexane. It builds on M7's component database, composition, ThermodynamicState and capability-scoped PropertyPackage boundary. It does not connect equilibrium to process equipment. The independent numerical oracle is the pre-existing `PRE_MILESTONE_8_PR_BENCHMARK.md` and frozen `benchmarks/peng_robinson/methane_nhexane_pr_reference.json`, generated with coefficient-configured Thermo 0.6.0 before this production implementation.

Provider/EOS identity: **`peng_robinson@1.0`**. Solver identity: **`binary_tpd_rr_ss@1.0`**. Stability algorithm identity: **`binary_tpd_grid_golden@1.0`**. Qualified capabilities are PR EOS, phase stability, single-phase PT classification and two-phase PT flash for the stated binary reference domain. This is mathematical agreement with an independent implementation, not experimental fluid-property validation or qualification of arbitrary near-critical/boundary states.

**Final human-operated manual validation of Milestone 8 was successfully completed on 2026-09-28**, as reported by the user. The manual execution and inspection of Cases A/B/C are recorded separately below from the automated qualification results.

## Component and interaction data

Production retrieves Tc, Pc and omega from the unchanged M7 **`riogineer_components@1.0`** dataset in `components.py`. It duplicates none of those constants. The dataset's source is the tagged CoolProp v7.1.0 fluid data, with exact selection/rounding documented in `MILESTONE_7.md`. Water remains in that dataset for M7 molecular projection but is explicitly rejected by the PR provider, even when supplied with zero mole fraction. Unknown IDs are also rejected; no component is removed, aliased or merged.

`BinaryInteractions` is an immutable, explicitly ordered, complete symmetric matrix with identifier, source and EOS applicability. Dimensions, finite values, exact symmetry and zero diagonal are validated. Missing entries are errors; there is no implicit zero default. The qualification specification is `methane_nhexane_explicit_zero@1.0`, with canonical order **methane, n_hexane** and matrix `[[0,0],[0,0]]`. Zero is an explicit mathematical specification, not a calibrated physical assumption. Tests also use the independently frozen nonzero symmetric value 0.02. Production permits explicit nonzero specifications without advertising their physical calibration.

Component IDs, composition, BIP rows/columns and output vectors share an explicit order. Consistent permutation is supported and tested; mismatched order is rejected. Immutable datasets may be shared, but roots, trial compositions, K, beta and all iteration state belong to each call. Results are independent of prior calls and tested concurrently.

## EOS equations and numerical root policy

The implementation uses SI **mol**, not kmol, in EOS equations:

```text
R = 8.31446261815324 J/(mol K)
kappa_i = 0.37464 + 1.54226 omega_i - 0.26992 omega_i²
alpha_i = [1 + kappa_i (1 - sqrt(T/Tc_i))]²
a_i(T) = 0.45724 R² Tc_i² alpha_i / Pc_i     [Pa m6/mol2]
b_i = 0.07780 R Tc_i / Pc_i                 [m3/mol]
a_ij = sqrt(a_i a_j) (1-kij)
a = sum_i sum_j q_i q_j a_ij
b = sum_i q_i b_i
A = a P/(RT)²
B = b P/(RT)
Z³ - (1-B) Z² + (A-3B²-2B) Z - (AB-B²-B³) = 0
```

This is canonical PR1976, with no PR78 kappa extension, volume translation or alternative library coefficients. `q` is the particular molar overall/phase composition. The standard library is the only numerical dependency; NumPy/SciPy, Thermo, teqp and the benchmark virtual environment are not runtime dependencies.

The real cubic solver uses the depressed-cubic Cardano branch for one real root and trigonometric branches for three roots. It uses a discriminant tolerance of `2e-15 * max(|(q/2)²|, |(p/3)³|, 1e-300)`, at most five Newton polishing steps and relative/absolute root deduplication `1e-12 * max(1, |Z|)`. Physical roots require `Z > B`; every distinct physical real root is retained and sorted. There is no complex-root imaginary-part filter because the implementation operates entirely in real arithmetic. Near-degenerate critical roots are not broadly qualified by the interior reference cases.

Liquid-like selection means smallest physical root at the liquid composition; vapor-like selection means largest at the vapor composition. The minimum residual Gibbs root at a fixed composition minimizes `sum(q_i ln(phi_i))` over the extreme roots. Neither root count nor Z magnitude establishes global stability. In particular, Case A is stable liquid with Z greater than one, while Case C is stable vapor with three roots.

For each selected root:

```text
ln(phi_i) = (b_i/b)(Z-1) - ln(Z-B)
            - A/(2 sqrt(2) B) [2 sum_j(q_j a_ij)/a - b_i/b]
              ln[(Z+(1+sqrt(2))B)/(Z+(1-sqrt(2))B)]
```

The ratio logarithm uses `log1p` for accuracy. Domain checks cover positive finite T/P, valid composition, finite parameters, positive attraction/co-volume, physical roots and logarithm arguments. Exponents outside [-700,700] fail explicitly; there is no clipping, arbitrary log epsilon or silently constrained final K. Fugacities are `q_i phi_i P` in Pa and checked for finite output. Analytical temperature derivatives of a are used only for phase identification, not caloric properties.

**The seven EOS tests passed before stability/flash implementation began**, independently checking frozen kappa, alpha, a_i, b_i, mixture a/b/A/B, all roots, selected roots and ln(phi)/phi. Flash iteration did not compensate for an EOS mismatch.

## Phase stability and single-phase labels

Stability uses explicit binary tangent-plane-distance minimization, an alternative to Michelsen successive-substitution trials:

```text
d_i = ln(z_i) + ln(phi_i(z))                 [lowest-Gibbs homogeneous root]
TPD/(RT) = sum_i w_i [ln(w_i)+ln(phi_i(w))-d_i]
```

For every trial composition, both liquid-like and vapor-like extreme roots participate through the minimum-Gibbs envelope. A deterministic grid contains 257 evenly spaced points, the actual overall composition and logarithmically spaced endpoint points `10^-j` and `1-10^-j`, j=1…12. Every sampled interior minimum is bracketed by its neighbors and refined with golden-section minimization to an interval width at most **1e-12**, maximum **100 iterations per minimum**. Endpoints and the original composition are retained as explicit trials. At an exact zero, the analytic limit `w ln(w)=0` is used; no fictitious trace inventory is added. A single active component has a point composition simplex and uses minimum-Gibbs root comparison.

The minimum TPD must be at least **-1e-9** for numerical stability. A negative value beyond that threshold requires a split. Every refinement must converge; otherwise the provider returns `stability_not_converged`, never a valid single-phase result. Trial diagnostics include composition, selected root kind, TPD, iterations, interval-width residual and convergence. Iteration count is the sum of refinement steps, not the number of EOS grid evaluations. This is reproducible binary numerical evidence, not an analytic guarantee that no unsampled narrow minimum exists outside the qualified domain.

After homogeneous stability, the phase-identification parameter labels a stable state:

```text
P = RT/(V-b) - a/(V²+2bV-b²)
PIP = V [P_VT/P_T - P_VV/P_V]
```

Derivatives are analytical at fixed composition. PIP > 1 is liquid-like; PIP < 1 is vapor-like. Singular/mechanically unstable derivatives and |PIP-1| <= 1e-10 return a numerical-domain failure. This labeling follows the [documented PIP definition](https://chemicals.readthedocs.io/chemicals.utils.html#chemicals.utils.phase_identification_parameter), independently tested against the frozen PIP values. It is not itself the stability criterion. TPD is the conventional tangent-plane criterion; see the [Thermopack flash formulation](https://thermotools.github.io/thermopack/memo/flash/flash.pdf). No external library algorithm is called by production.

Single-phase results contain exactly one phase with fraction 1, `single_liquid`/beta=0 or `single_vapor`/beta=1. No absent-phase composition is invented. Following a converged two-phase flash, the same binary search checks the **equilibrium common tangent**; its diagnostic classification is null because stability of a tangent does not label the overall state as homogeneous.

## Rachford–Rice, reconstruction and PT iteration

Wilson initialization is explicitly distinct from equilibrium:

```text
ln(K_i,initial) = ln(Pc_i) - ln(P) + 5.373(1+omega_i)(1-Tc_i/T)
F(beta) = sum_i z_i (K_i-1) / [(1-beta)+beta K_i]
x_i = z_i / [(1-beta)+beta K_i]
y_i = K_i x_i
K_i,new = exp(ln(phi_i,L)-ln(phi_i,V))
```

Rachford–Rice uses bisection on [0,1], positive finite K and denominator checks, residual tolerance **2e-14**, maximum **200 iterations**. Endpoint all-liquid/all-vapor tendencies are explicitly labeled as RR tendencies, never used as stability conclusions. If stability has already identified an unstable state and Wilson/current K cannot establish a two-phase RR bracket, the flash fails rather than selecting beta=0 or 1.

The normalization policy is consistent: input molar sums within **1e-12** may be normalized in a working copy; materially inconsistent inputs are rejected. The original ThermodynamicState and its supplied composition remain unchanged. Reconstructed x/y raw sum errors are recorded, must be within 1e-12 and only then permit roundoff normalization. Material reconstruction is checked after that normalization. Zero inventory species adds no log chemical-potential constraint. Material mass-to-mole conversion remains M7's responsibility; the standalone input is explicitly molar.

PT sequence: input validation → homogeneous stability → one-phase return or Wilson initialization → RR → reconstruction → liquid/vapor fugacities → undamped successive substitution. There is no acceleration, random initialization, implicit warm start or empirical correction. Maximum flash iterations: **100**. Acceptance requires **max |ln(x_i phi_i,L)-ln(y_i phi_i,V)| <= 1e-11**, material residual <= **1e-10**, RR/normalization closure and a converged nonnegative equilibrium common-tangent check. K-change alone never establishes convergence. Solver settings are recorded; acceptance tolerances cannot be loosened through the API.

Failure statuses: `invalid_input`, `unsupported_components`, `stability_not_converged`, `rachford_rice_not_converged`, `flash_not_converged`, `numerical_domain_error`. Success statuses: `success_single_phase`, `success_two_phase`. Failures carry diagnostics but no valid phases, beta or final K. Exhausted flash iterations preserve last fugacity/RR/material residuals and iteration count. Numerical errors are reported without stack traces or default noisy logging.

## Typed state, provider and contract boundaries

`ThermodynamicState` now accepts either the existing M7 mass-derived Composition or an immutable `MolarComposition` standalone specification. `StateSpecificationProvenance` explicitly selects the PR provider and BIP identity. The shared PropertyPackage protocol retains identity/capabilities; `MolecularPropertyPackage` and `PTPropertyPackage` declare their respective operations. The immutable registry contains both providers. Existing process calculation still directly selects `MolecularCompositionProvider`, with unchanged runtime numerical behavior.

The PR adapter returns internal typed `PTResult`, `PhaseResult`, diagnostics and provenance. Phases are an arbitrary-length tuple architecture, although M8 only qualifies liquid/vapor. Overall state is preserved separately from phase compositions. Provenance records model, solver, component dataset, full BIP specification, ordered input, T/P and numerical settings. A caller can explicitly select PR for an M7-projected state, but no equipment does so.

**No requirements, flowsheet or results contract/schema changed.** M6 requirements 1.3, flowsheet 1.4 and M7 results 1.5 remain in force, including old readers. No new public endpoint, frontend feature, fixture or Stream Table quantity was added. Implementation fingerprints naturally change with new engine source files; process numerical values, stable IDs, numbering and model selection do not.

## Production reference results and independent comparison

All cases use 300 K, z=[0.5,0.5] and explicit zero kij. Values below are actual production floating-point outputs. Full precision, all 122 individual comparisons, errors, applicable tolerances and pass/fail are in `benchmarks/peng_robinson/production_comparison.json`. The independent frozen JSON and reproduction script are unchanged.

| Case | P (Pa absolute) | Classification |               Beta | Flash iterations | Initial stability refinement steps |
| ---- | --------------: | -------------- | -----------------: | ---------------: | ---------------------------------: |
| A    |        30000000 | single_liquid  |                  0 |                0 |                                 48 |
| B    |          300000 | vapor_liquid   | 0.5346425102238044 |                7 |                                 94 |
| C    |            1000 | single_vapor   |                  1 |                0 |                                 48 |

Case A: Z=**1.04595589143832**, phi=**[0.9297889066599622, 0.0035632605196677367]**. Frozen Z agrees exactly; maximum phi difference is 2.22e-16. Minimum TPD=0 and PIP=7.836225504723406.

Case C: Z=**0.9997966702051944**, phi=**[1.0000680508858557, 0.9995254326595929]**. Frozen Z agrees exactly; maximum phi difference is 4.44e-16. Minimum TPD=-5.09e-17 and PIP=0.9994441541503631. Its three physical roots are retained despite the stable-vapor result.

Case B:

| Quantity                                                | Production                                       |
| ------------------------------------------------------- | ------------------------------------------------ |
| x                                                       | [0.015619720085965972, 0.984380279914034]        |
| y                                                       | [0.9216088074693606, 0.07839119253063942]        |
| Z_L                                                     | 0.015469663802426934                             |
| Z_V                                                     | 0.9885027848240121                               |
| phi_L                                                   | [58.659556020112824, 0.07365204255092793]        |
| phi_V                                                   | [0.9941808693398859, 0.9248694390534127]         |
| Final K=y/x                                             | [59.002901613928984, 0.0796350700335904]         |
| Maximum diagnostic log-fugacity residual                | 2.4541479959339085e-13                           |
| Final RR iteration residual                             | 1.021405182655144e-14                            |
| RR residual independently reconstructed from returned K | 8.104628079763643e-15                            |
| Maximum material residual                               | 2.275957200481571e-15                            |
| Raw x/y sum errors                                      | [-5.440092820663267e-15, 4.6629367034256575e-15] |
| Initial homogeneous TPD minimum                         | -1.7686866157831618                              |
| Final equilibrium common-tangent minimum                | -2.3755042165576793e-15                          |
| Final RR iterations                                     | 46                                               |
| Final common-tangent refinement steps                   | 96                                               |

The tiny distinction between diagnostics and independently recomputed residuals is ordinary operation-order/roundoff normalization. Both satisfy the unchanged frozen tolerances. Wilson K=[111.30087562398208,0.08024450358776494] is only the initial estimate.

The comparison tool uses `atol + rtol*abs(reference)` from the frozen JSON. For phi, which has no separately frozen tolerance, it propagates the frozen ln(phi) bound through exp. For K, it propagates the frozen x/y bounds through y/x. These derived limits and their numerical values are recorded on each report row. No frozen tolerances were changed.

| Quantity class                                | Maximum absolute error |
| --------------------------------------------- | ---------------------: |
| kappa                                         | 1.1102230246251565e-16 |
| alpha                                         |                      0 |
| a_i                                           |  4.440892098500626e-16 |
| b_i                                           |                      0 |
| a_mix                                         |  8.881784197001252e-16 |
| b_mix                                         |                      0 |
| A/B                                           | 2.7755575615628914e-17 |
| Z roots/selected Z                            | 1.3322676295501878e-15 |
| ln(phi)                                       |  6.217248937900877e-15 |
| phi                                           | 4.3298697960381105e-15 |
| minimum TPD                                   |  8.881784197001252e-16 |
| beta                                          |   8.43769498715119e-15 |
| x                                             |  3.122502256758253e-17 |
| y                                             | 1.8568480086855743e-14 |
| K                                             | 1.0658141036401503e-12 |
| composition sums                              |                      0 |
| material closure                              |  2.275957200481571e-15 |
| independently recomputed log-fugacity closure | 2.4513724383723456e-13 |
| independently recomputed RR closure           |  8.104628079763643e-15 |

## Reproducible human-operated validation path

From the repository root, using the ordinary engine environment (not the isolated Thermo environment):

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py --case A
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py --case B
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py --case C
```

Omit `--case` for all three. The command prints classification, full phase compositions, fractions, Z, ln(phi)/phi, fugacities, final K, closure metrics, convergence/iterations, stability trials and provenance. Its exit status is nonzero on a comparison failure. To save a fresh detailed comparison without changing the independent reference:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py --output /tmp/m8-production-comparison.json
```

The tool is validation-only: it imports production code and reads the frozen JSON; production never imports this tool or the benchmark directory. No service, browser, LLM or network is needed. The independent benchmark's seven tests still run separately in `.local/pre-m8-venv` and reproduce their unchanged artifact.

## Automated acceptance and regression coverage

The new M8 tests cover pure/mixture/root/fugacity gates, PIP derivatives, independent RR, stability/TPD, A/B/C, all 27 nearby states, the 13-point independent pressure scan, nonzero kij, recomputed fugacity/material closure, phase normalization, changed T/P/z, consistent ordering, immutable inputs, history/thread independence, explicit M7 adapter selection, registry capabilities, malformed conditions/compositions/BIPs, unsupported water/unknown components, extreme domains, missing RR bracket and forced stability/RR/flash nonconvergence. An AST dependency check excludes runtime benchmark/Thermo/teqp/NumPy/SciPy imports. The saved comparison is reproduced against current production in normal Python discovery.

Completed automated validation on 2026-09-28:

| Check                               | Result                                                                                                |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------- |
| New M8 Python tests                 | **34 passed** (7 EOS, 26 RR/stability/flash, 1 comparison artifact)                                   |
| Complete Python discovery           | **98 passed**, including the unchanged 64 existing tests and local HTTP integration                   |
| TypeScript/Vitest                   | **197 passed in 17 files**                                                                            |
| Playwright browser suite            | **28 passed**                                                                                         |
| Independent pre-M8 benchmark suite  | **7 passed**, including complete frozen reproduction                                                  |
| Production-versus-frozen comparison | **122 comparisons passed**                                                                            |
| Contract parity                     | Passed                                                                                                |
| ESLint                              | Passed                                                                                                |
| TypeScript type checking            | Passed                                                                                                |
| Repository formatting / M8 Markdown | Passed                                                                                                |
| Diff whitespace                     | Passed                                                                                                |
| Production build                    | Passed                                                                                                |
| Production smoke                    | **17 pages and 17 PNG social cards passed**, plus links, 404s, indexing and disabled contact delivery |

All seven acceptance gates pass: EOS, stability, flash, equilibrium, material, RR and M3–M7 regression. There is no unresolved benchmark discrepancy or process-compatibility failure. The original benchmark files, component constants, runtime dependency manifest, process models, contracts and fixtures have no changes.

The first smoke attempt used port 3200 with a mismatched configured site origin, correctly returning HTTP 403 at the contact origin guard. Restarting the local production server with `SITE_URL=http://127.0.0.1:3200` resolved the configuration mismatch; the complete smoke suite then passed. No application workaround was introduced. The local production server used an empty LLM-provider selector, and browser interpretation tests use the existing mocks; no live-provider call occurred.

Reproduction commands (run from the repository root unless a working directory is shown):

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_pr*.py' -v
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
npm test
npm run contracts:check
npm run lint
npm run typecheck
npm run format:check
node_modules/.bin/prettier --check MILESTONE_8.md
git diff --check
npm run test:e2e
npm run build
```

For production smoke, start the server in one terminal with `SITE_URL=http://127.0.0.1:3200 SITE_INDEXABLE=false RIOGINEER_LLM_PROVIDER='' npm run start -- --port 3200`, then run `SMOKE_URL=http://127.0.0.1:3200 npm run smoke` in another.

## Files created and modified

Created:

- `engine/riogineer_engine/pr_eos.py` — pure parameters, BIPs, mixing, roots, fugacity and PIP.
- `engine/riogineer_engine/pr_stability.py` — binary TPD search and trial diagnostics.
- `engine/riogineer_engine/rachford_rice.py` — bracketed RR and material reconstruction.
- `engine/riogineer_engine/pr_flash.py` — typed standalone PT results and iteration.
- `engine/riogineer_engine/property_packages.py` — capability-specific adapter and immutable registry.
- `engine/tests/test_pr_eos.py` — independent EOS gate.
- `engine/tests/test_pr_flash.py` — RR, stability, flash and failure qualification.
- `engine/tests/test_pr_comparison.py` — comparison reproduction without frozen-reference mutation.
- `benchmarks/peng_robinson/compare_production.py` — deterministic human inspection/comparison command.
- `benchmarks/peng_robinson/production_comparison.json` — production comparison evidence, distinct from the frozen oracle.
- `MILESTONE_8.md` — this report.

Modified:

- `engine/riogineer_engine/thermodynamics.py` — internal molar state/provenance types and capability-specific protocol; existing numerical enrichment unchanged.
- `docs/RIOGINEER_MASTER_CONTEXT.md` — current state and next-step sections only.

## Process compatibility and deliberately deferred capabilities

M3/Bia, M4, M5, M6 and M7 calculations remain unchanged. Existing exact process fingerprints protect stream states, component flows, equipment outputs, scheduling and balances; independent Decimal tests protect molecular enrichment. Numbering/layout/PFD and unavailable-property browser regressions remain in place. No source changes were made to equipment, process execution, frontend, fixtures, component constants, interpretation, evidence anchoring or topology normalization.

M8 implements no PH/PS flash, water-containing VLE, VLLE, third phase, rigorous enthalpy/entropy, PR heat capacities, speed of sound, density, phase volumetric flow, transport properties, public bubble/dew calculation, phase-envelope UI, recycle handling or equipment integration. Existing separators retain prescribed recoveries; heater constant-Cp accounting and compressor ideal-gas Cp/k/efficiency results are untouched. Current density/volumetric rows continue to display **—**. No live LLM/provider call was made.

## Limitations and evidence-based next milestone

The frozen interior cases, neighborhood and pressure scan close against the independent library; fugacity/material/RR acceptance passes, stability agrees with independent numerical TPD evidence, explicit failures are exercised, water is blocked and the provider remains independent of equipment. On that evidence, recommend a separately approved **Milestone 9 — First Process Integration of Qualified PT Flash**. Human inspection of Cases A/B/C was completed on 2026-09-28, as recorded below. No M9 work is implemented here.

The binary grid/refinement method is intentionally transparent and bounded. It is not a global proof, general multi-component stability solver, near-critical conditioning study or arbitrary-BIP physical validation. Exact phase boundaries, degenerate roots, pure-fluid coexistence and challenging trace regimes require separate qualification. Unstable states without an admissible Wilson RR bracket fail explicitly; there is no broader fallback promise. These limitations must remain visible when scoping any integration.

A future controlled separator could evolve from prescribed component recoveries to:

```text
MaterialStream → ThermodynamicState → PropertyPackage.flash_PT
               → PhaseResult(s) → separator outlet material streams
```

The separator would orchestrate the operation and consume qualified results; PR equations would remain inside the provider. That milestone must define explicit phase-to-stream mapping (qualified hydrocarbon vapor → gas, hydrocarbon liquid → oil), preserve identity/units, define failure handling and qualify process conservation. No phase mapping is implemented now.

**Water-containing three-phase VLLE is not the same next step as methane/n-hexane two-phase VLE integration.** Aqueous/hydrocarbon-liquid/vapor modeling and their outlet mapping require a separate qualification milestone. M8 does not generalize a hydrocarbon binary split to water-bearing process streams.

## Completed human-operated manual validation — 2026-09-28

The user reported that the **final human-operated manual validation of Milestone 8 was successfully completed on 2026-09-28**. The user manually executed the production-versus-independent-reference comparison commands from the repository root and inspected the output for Cases A, B and C. This record is distinct from the automated test coverage above; the coding agent did not rerun the calculations for this documentation update.

### Case A — stable single liquid

Command executed by the user:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py --case A
```

Manual inspection confirmed provider **`peng_robinson@1.0`**, **`passed: true`** and **32 production-versus-reference comparisons passed**. This is the qualified high-pressure single-liquid benchmark. Production PR parameters, roots, fugacity quantities and stability quantities matched the frozen independent reference within tolerance. Maximum numerical differences were approximately at floating-point precision.

### Case B — vapor + liquid equilibrium

Command executed by the user:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py --case B
```

Manual inspection confirmed provider **`peng_robinson@1.0`**, **`passed: true`** and **72 production-versus-reference comparisons passed**. This is the qualified vapor-liquid PT-flash benchmark.

Production reproduced the frozen reference for vapor fraction beta, liquid composition x, vapor composition y, liquid and vapor compressibility factors, liquid and vapor fugacity coefficients, equilibrium K-values, material reconstruction, Rachford–Rice and fugacity equilibrium.

Observed approximate maximum absolute errors:

| Quantity                 | Maximum absolute error |
| ------------------------ | ---------------------: |
| beta                     |               8.44e-15 |
| x                        |               3.12e-17 |
| y                        |               1.86e-14 |
| Z roots                  |               1.33e-15 |
| ln(phi)                  |               6.22e-15 |
| K from x/y               |               1.07e-12 |
| Material reconstruction  |               2.28e-15 |
| Log-fugacity equilibrium |               2.45e-13 |
| Rachford–Rice            |               8.10e-15 |

### Case C — stable single vapor

Command executed by the user:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py --case C
```

Manual inspection confirmed provider **`peng_robinson@1.0`**, **`passed: true`** and **34 production-versus-reference comparisons passed**. This is the qualified low-pressure single-vapor benchmark. Production PR parameters, roots, fugacity quantities and stability quantities matched the frozen independent reference within tolerance. Numerical differences were approximately at floating-point precision.

### Manual validation scope

The human-operated validation covered all three reference phase regimes: **A — stable single liquid; B — vapor + liquid equilibrium; C — stable single vapor**. It confirms the **standalone production Peng–Robinson/PT-flash implementation against the independently frozen reference**.

It does **not** validate:

- Integration with SEP_1 or any process equipment.
- Water-containing equilibrium.
- VLLE.
- PH flash.
- PS flash.
- Rigorous enthalpy or entropy.
- Near-critical behavior beyond the existing automated qualification.

Those capabilities remain outside Milestone 8. This documentation update changes no source code, tests, contracts, fixtures, frozen benchmark or thermodynamic calculations. No live-provider call was made.
