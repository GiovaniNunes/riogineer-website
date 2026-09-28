# Pre-Milestone 8 — Independent Peng–Robinson / PT-Flash Benchmark

## Objective and scope

This study freezes independent numerical references **before** a separately approved RioGineer Peng–Robinson/two-phase PT-flash implementation. It is an offline benchmark artifact, not Milestone 8 implementation, process-engine integration or physical validation against experiments. Production modules, contracts, UI/PFD/Stream Table, component constants, fixtures and existing test expectations were not changed.

The binary system is methane/n-hexane, in that order, with overall **z = [0.50, 0.50] mol/mol**. Water is excluded. The complete symmetric **kij matrix is [[0, 0], [0, 0]]**. Zero kij defines this mathematical benchmark; it is not a universal physical recommendation or calibrated methane/n-hexane interaction parameter.

Benchmark identity: **`pre_m8_methane_nhexane_canonical_pr@1.0`**. Component dataset: **`riogineer_components@1.0`**.

## Independent reference and exact formulation

The primary independent implementation is **Thermo 0.6.0**, with Chemicals 1.5.2 and Fluids 1.3.1. Neither Thermo nor teqp was initially available. Both were installed only in `.local/pre-m8-venv`; all benchmark dependency versions are pinned in `benchmarks/peng_robinson/requirements.txt`. No dependency was added to RioGineer's runtime manifests or engine virtual environment.

Thermo supplies every EOS evaluator, alpha function, cubic volume solver, fugacity calculation, Michelsen stability iteration and PT-flash iteration. `reference.py` configures those classes, scans conditions, exports values and checks consistency. Its `BenchmarkPR`/`BenchmarkPRMIX` subclasses override **coefficient attributes only**, including the cached coefficient products used by the optimized library constructors. No EOS/root/fugacity/flash method is copied or rewritten. Auxiliary pure-component calculations use the same configured coefficients.

This configuration is necessary: both Thermo's default PR and installed **teqp 0.23.1** use OmegaA = 0.4572355289213822 and OmegaB = 0.07779607390388846. Those differ from this request. The tested teqp generic-cubic factory rejected explicit `OmegaA`/`OmegaB` overrides, so its default model was **not** used as the numerical reference. teqp is retained in the isolated benchmark dependencies only to reproduce the recorded default-coefficient audit; it does not supply frozen equilibrium values. The exact Thermo constructor/source and model attributes were inspected, and both configured pure/mixture coefficients are checked against the specified equations on every generation.

Primary documentation/source references:

- [Thermo PR mixture documentation and implementation](https://thermo.readthedocs.io/thermo.eos_mix.html)
- [Thermo flash algorithms and stability options](https://thermo.readthedocs.io/thermo.flash.html)
- [Thermo FlashVL source](https://thermo.readthedocs.io/_modules/thermo/flash/flash_vl.html)
- [teqp cubic-model coefficients](https://teqp.readthedocs.io/en/latest/models/cubics.html)

Online documentation may advance independently of installed releases. The machine-readable artifact records **installed package versions and SHA-256 hashes of the inspected Thermo constructor, fugacity and stability methods**. These identify the actual reference used here.

The gas constant is **R = 8.31446261815324 J/(mol K)**, explicitly checked against the pinned Fluids constant. All EOS quantities use a **mol**, not kmol, basis. Molecular weights below are kg/kmol as in M7; they do not replace this EOS molar-unit convention.

```text
a_i(T) = 0.45724 R² Tc_i² / Pc_i × alpha_i(T)
b_i = 0.07780 R Tc_i / Pc_i
alpha_i(T) = [1 + kappa_i(1 − sqrt(T/Tc_i))]²
kappa_i = 0.37464 + 1.54226 omega_i − 0.26992 omega_i²

a_mix = sum_i sum_j q_i q_j sqrt(a_i a_j)(1 − kij)
b_mix = sum_i q_i b_i
A = a_mix P/(R² T²)
B = b_mix P/(RT)
```

Here q is the particular overall or phase mole-fraction vector. These are the classical quadratic-a/linear-b mixing rules, with no volume translation or alternative alpha model. a has units **Pa m⁶/mol²**; b has units **m³/mol**. A, B, Z, phi, kappa, alpha and all phase fractions are dimensionless. Later implementation must retain the specified 0.45724/0.07780 coefficients rather than silently selecting the library defaults.

## Exact component inputs

No internal library component lookup is used. Every component constant is explicitly supplied. The benchmark reads the existing M7 data module solely to assert exact equality and record its file hash; it does not import engine calculations or any future RioGineer EOS code.

| Component | MW (kg/kmol) |  Tc (K) |  Pc (Pa absolute) |              omega |
| --------- | -----------: | ------: | ----------------: | -----------------: |
| methane   |      16.0428 | 190.564 |           4599200 |            0.01142 |
| n_hexane  |     86.17536 |  507.82 | 3044115.328359688 | 0.3003189315498438 |

These are the already documented M7 CoolProp v7.1.0-derived constants. None was replaced by a Thermo/teqp internal component value. No heat-capacity or vapor-pressure correlation package is populated; only PT fugacity equilibrium is used.

## Phase mapping and case selection

The library was first scanned at **300 K** over 1000–50000000 Pa. The full thirteen-point scan is stored in JSON. It finds vapor at low pressure, vapor–liquid through the intermediate range and liquid at high pressure. Independent library saturation calculations at the same overall composition give:

- Dew pressure: **44484.799489176294 Pa**.
- Bubble pressure: **11488247.24995131 Pa**.

These saturation pressures are selection diagnostics; the primary acceptance references are the three interior cases, not boundary points.

| Case | T (K) | P (Pa absolute) | Classification        |     Vapor fraction |
| ---- | ----: | --------------: | --------------------- | -----------------: |
| A    |   300 |        30000000 | Stable single liquid  |                  0 |
| B    |   300 |          300000 | Stable vapor + liquid | 0.5346425102237959 |
| C    |   300 |            1000 | Stable single vapor   |                  1 |

All cases use exactly z = [0.5, 0.5] and the zero kij matrix. Case A is about 2.61 times the bubble pressure; B is about 6.74 times the dew pressure and far below the bubble pressure; C is about 44.5 times below the dew pressure. **Every case keeps its classification at all nine combinations of T = 295/300/305 K and P = 0.8/1.0/1.2 times its selected pressure.** These actual independent calculations, not assumed root counts, establish useful separation from phase boundaries.

## Stability evidence

Thermo `FlashVL.flash_TP_stability_test` compares homogeneous-phase Gibbs criteria and calls its **Michelsen tangent-plane stability procedure** with Wilson-derived and other incipient composition guesses. The stability implementation evaluates trial fugacities and seeks nontrivial destabilizing compositions. Stable single-phase identification also uses the library's phase-identification parameter (PIP) when homogeneous roots have equal Gibbs criteria. A root count alone is never used as evidence of global phase stability.

An additional benchmark-only binary check uses the library's lowest-Gibbs-root fugacities to evaluate:

```text
TPD/(RT) = sum_i w_i [ln(w_i) + ln(phi_i(w)) − ln(z_i) − ln(phi_i(z))]
```

It scans 1002 compositions across methane mole fraction [1e-12, 1−1e-12], including the reference composition, and refines every detected grid local minimum with SciPy bounded minimization. No negative minimum beyond 1e-9 is accepted for a stable reference. For Case B the same check is also repeated against the **equilibrium common tangent**, using x and its liquid fugacities as the reference.

| Case / reference              | Library homogeneous stability  | Minimum refined TPD/(RT) |
| ----------------------------- | ------------------------------ | -----------------------: |
| A, feed z                     | Stable                         |                        0 |
| B, homogeneous feed z         | Unstable                       |      −1.7686866157831627 |
| C, feed z                     | Stable                         |  −3.9547184801827073e-16 |
| B, equilibrium common tangent | No lower sampled/refined state |   −5.265732301738133e-16 |

The tiny negative values are floating-point noise, far below the 1e-9 threshold. Case B's common-tangent minima occur near both equilibrium phase compositions. The initial homogeneous-feed TPD minimizer need not equal the final equilibrium liquid composition; it identifies instability, not the final flash solution.

This is converged numerical stability evidence from the independent implementation plus a binary composition scan, **not an analytic proof over every possible composition or a general multiphase-stability guarantee**. Neither liquid–liquid nor water-containing equilibrium is qualified by this study.

## Pure-component parameters at 300 K

Values are read from the configured independent library and checked against the requested coefficient definitions. No UI rounding is applied to the JSON.

| Component |               kappa |              alpha |   a_i (Pa m⁶/mol²) |            b_i (m³/mol) |
| --------- | ------------------: | -----------------: | -----------------: | ----------------------: |
| methane   | 0.39221740720531195 | 0.8101834074909086 | 0.2022066134114174 | 0.000026802317444263274 |
| n_hexane  |  0.8134653963141592 | 1.4118862442770883 | 3.7806876057403356 |  0.00010791019597217473 |

## Mixture parameters at Case B: 300 K, 300000 Pa

| Composition          | a_mix (Pa m⁶/mol²) |         b_mix (m³/mol) |                    A |                     B |
| -------------------- | -----------------: | ---------------------: | -------------------: | --------------------: |
| z = [0.5, 0.5]       |   1.43289630014247 |   0.000067356256708219 |  0.06909158192772549 |  0.008101095621159913 |
| Equilibrium liquid x |  3.690440196318239 | 0.00010664331361280222 |  0.17794612991040662 |  0.012826242477771728 |
| Equilibrium vapor y  | 0.3213157286530708 | 0.00003316046076569499 | 0.015493243990296529 | 0.0039882867105920546 |

The benchmark-only tests separately check classical mixing arithmetic using the library's pure a_i/b_i values. This isolates mixture-rule errors from flash errors without implementing an EOS or flash solver.

## Cubic roots and selection

All physically admissible real roots returned by the independent volume solver are retained, converted by Z = PV/(RT), sorted and checked with:

```text
Z³ − (1−B)Z² + (A−3B²−2B)Z − (AB−B²−B³) = 0
```

The library returns zero volume placeholders for missing/nonreal roots. Those are excluded; physical roots require V > b, equivalently Z > B. Intermediate real roots are retained in the artifact, even though they are not selected as equilibrium phases.

| Case B composition | All physical real Z roots, increasing                            |
| ------------------ | ---------------------------------------------------------------- |
| z                  | 0.012080482090302068; 0.043641122848020186; 0.936177299440518    |
| x                  | **0.01546966380242693**; 0.17075834711857774; 0.8009457466012236 |
| y                  | **0.9885027848240134**                                           |

The liquid uses the smallest root **at x**; the vapor uses the largest root **at y** (its only real physical root). The middle liquid-composition root is mechanically unstable; the largest root at x is a competing vapor-like homogeneous state, not the flash vapor at y. Phase equilibrium and stability decide the split; selecting small/large roots at z is not a flash.

Case C has **three physical real roots** at z: 0.000040395465984364656, 0.0001359306767507044 and **0.9997966702051944**. It is nevertheless stable single vapor. Case A has one root **1.04595589143832** and is stable liquid; Z > 1 is not evidence that a phase must be vapor.

## Case B PT-flash and fugacity references

At **300 K, 300000 Pa**, z = [0.5, 0.5]:

- Vapor fraction beta: **0.5346425102237959**.
- Liquid fraction: **0.4653574897762041**.
- Liquid x: **[0.015619720085966004, 0.984380279914034]**.
- Vapor y: **[0.9216088074693791, 0.07839119253062085]**.
- Z_L: **0.01546966380242693**.
- Z_V: **0.9885027848240134**.

| Component |               phi_L |          ln(phi_L) |              phi_V |             ln(phi_V) |             K = y/x |
| --------- | ------------------: | -----------------: | -----------------: | --------------------: | ------------------: |
| methane   |  58.659556020112824 |  4.071750494821597 | 0.9941808693398857 | −0.005836127771952308 |   59.00290161393005 |
| n_hexane  | 0.07365204255092747 | −2.608403403247907 |  0.924869439053417 |  −0.07810269840116162 | 0.07963507003357154 |

Explicit checks:

- sum(x) and sum(y) equal 1 within 1e-12.
- `(1−beta)x + beta y − z` = **[0, 0]** in the recorded floating-point evaluation.
- `ln(x_i phi_i,L) − ln(y_i phi_i,V)` = **[2.085137618124122e-15, −1.9165224962591765e-14]**.
- Rachford–Rice `sum(z_i (K_i−1)/(1+beta(K_i−1)))` = **0** in the recorded evaluation.

Pressure is common, so the log residuals establish equality of component fugacities. The benchmark also checks phi against exp(ln phi), phase normalization, material reconstruction and root-polynomial residuals. Zero recorded residuals do not imply exact arithmetic; future comparisons use the tolerances below.

Wilson **initialization values**, computed as `ln K_i = ln(Pc_i/P) + 5.373(1+omega_i)(1−Tc_i/T)`, are **[111.30087562398208, 0.08024450358776494]**. They differ from final equilibrium K, especially methane. They are not PR-equilibrium outputs or acceptance substitutes for the converged flash.

## Single-phase references

Case A: **300 K, 30000000 Pa**, z = [0.5, 0.5], stable liquid, beta = 0, Z = **1.04595589143832**.

- phi = **[0.929788906659962, 0.0035632605196677333]**.
- ln phi = **[−0.07279770068523028, −5.637079276965833]**.
- Michelsen test reports stable, refined TPD minimum is zero, and the neighborhood remains liquid. A future flash must not force a vapor–liquid split.

Case C: **300 K, 1000 Pa**, z = [0.5, 0.5], stable vapor, beta = 1, Z = **0.9997966702051944**.

- phi = **[1.000068050885856, 0.9995254326595934]**.
- ln phi = **[0.00006804857049937677, −0.0004746799831260287]**.
- Michelsen test reports stable, refined TPD minimum is numerically zero, and the neighborhood remains vapor despite three real cubic roots. No absent-phase composition is fabricated.

## Precision and recommended future acceptance tolerances

Library PT successive substitution uses a **squared K-update tolerance of 1e-26** and maximum 1000 iterations. Stability iteration tolerance is 1e-12, maximum 1000 iterations. The squared K criterion is not a log-fugacity tolerance; explicit fugacity residual checks independently establish equilibrium closure.

A second Case B calculation at the looser squared K tolerance 1e-18 changes beta by 3.4274805216227833e-12, liquid fractions by at most 1.36e-15 and vapor fractions by at most 5.81e-12. Root-polynomial residuals are below 1e-15. These results justify tolerances above floating-point/reference noise while remaining tight enough to expose coefficient, mixing, root or flash errors at these well-separated states.

Use `abs(actual−reference) <= atol + rtol*abs(reference)` for value comparisons. Residual and normalization checks use absolute tolerances.

| Quantity                          | Absolute tolerance | Relative tolerance |
| --------------------------------- | -----------------: | -----------------: |
| alpha                             |              1e-12 |              1e-11 |
| kappa                             |              1e-13 |              1e-12 |
| a_i, a_mix (Pa m⁶/mol²)           |              1e-12 |              1e-10 |
| b_i, b_mix (m³/mol)               |              1e-15 |              1e-10 |
| A, B                              |              1e-12 |              1e-10 |
| Z roots                           |              1e-10 |               1e-9 |
| ln(phi)                           |               1e-9 |               1e-9 |
| beta                              |               1e-9 |                  0 |
| each x_i                          |               1e-9 |                  0 |
| each y_i                          |               1e-9 |                  0 |
| Composition sums                  |              1e-12 |                  0 |
| Material reconstruction           |              1e-10 |                  0 |
| Log-fugacity-equilibrium residual |               1e-9 |                  0 |
| Rachford–Rice residual            |              1e-10 |                  0 |
| Negative TPD stability threshold  |               1e-9 |                  0 |

Tc/Pc/omega/MW, R, kij, formulation coefficients and component ordering are specified inputs and must match exactly, not be adjusted within numerical tolerances. These tolerances qualify these interior cases; near-critical roots, traces or near-boundary phase fractions require separate conditioning studies.

## Optional nonzero-kij plumbing check

At Case B T/P and z, with symmetric kij = 0.02, the same independent machinery gives beta **0.5351623537032419**, x **[0.014571203415107516, 0.9854287965848927]**, y **[0.9216394850791656, 0.07836051492083437]**. This confirms explicit BIPs affect the calculation. It is not a calibrated physical BIP or an additional primary M8 acceptance case.

## Reproducibility and files

Executed with **Python 3.10.10 on macOS arm64**. The dependency lock pins Thermo 0.6.0, teqp 0.23.1, Chemicals 1.5.2, Fluids 1.3.1, NumPy 2.2.6, SciPy 1.15.3 and supporting packages. All files below are benchmark-only; production code must not import them.

Created:

- `PRE_MILESTONE_8_PR_BENCHMARK.md` — this report.
- `benchmarks/peng_robinson/reference.py` — independent-library configuration, phase scan, export and verification.
- `benchmarks/peng_robinson/methane_nhexane_pr_reference.json` — full-precision frozen numerical reference and provenance.
- `benchmarks/peng_robinson/test_reference.py` — benchmark-only checks, including corruption rejection.
- `benchmarks/peng_robinson/requirements.txt` — isolated dependency pins.

From the repository root:

```sh
python3.10 -m venv .local/pre-m8-venv
.local/pre-m8-venv/bin/python -m pip install -r benchmarks/peng_robinson/requirements.txt
.local/pre-m8-venv/bin/python benchmarks/peng_robinson/reference.py
.local/pre-m8-venv/bin/python -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
```

The default script command **checks** the existing frozen artifact against a fresh independent calculation. It does not overwrite it. The original generation command was:

```sh
.local/pre-m8-venv/bin/python benchmarks/peng_robinson/reference.py --write
```

Use `--write` only for an intentional, reviewed regeneration; changes to the benchmark definition require an explicit version/provenance decision. The JSON retains full float precision. Source hashes, installed versions and Python version are checked by reproduction; a different environment should be reviewed rather than silently re-freezing data. TPD minimizer coordinates have a looser reproduction tolerance (1e-7) than well-conditioned equilibrium quantities because coordinates near a shallow minimum are more sensitive than the TPD value.

Completed checks: **7 benchmark-only tests passed**; frozen artifact reproduction passed; exact M7 constant equality passed; all reported numeric values finite; stability/neighborhood, mass, fugacity and Rachford–Rice checks passed. No production suite or live LLM/provider call was needed for this isolated study. Formatting/whitespace and repository scope were checked separately. No production code, contracts, dependencies, historical fixtures or test expectations changed.

## Limitations and recommended Milestone 8 sequence

This is a mathematical PR reference, not experimental thermodynamic qualification. The coefficient-configured Thermo library is independent of future RioGineer code, but it is one primary flash implementation. teqp's different default coefficients must not be treated as an interchangeable second oracle. A later second-library comparison would need exactly the same specified coefficients and constants.

The three robust states intentionally avoid critical/boundary conditioning. They do not qualify every mixture, negative-flash regime, near-critical degeneracy or convergence failure. Numerical TPD scanning supplements the library's Michelsen checks; it is not a universal global-optimization proof. No density, enthalpy, process equipment or production thermodynamics integration was added.

Before authorizing M8, retain these exact constants and define an explicit phase-stability and convergence-failure policy. Recommended separately approved implementation sequence:

1. Pure PR parameters and classical mixing, tested against the frozen unit references.
2. All real cubic roots and physically admissible-root selection, including the stable-vapor/three-root Case C.
3. Component log-fugacity coefficients at fixed compositions, tested independently of flash.
4. Wilson initialization and a bounded Rachford–Rice solver, keeping initial K distinct from equilibrium K.
5. Explicit homogeneous-state stability and single-phase handling; do not infer phase count from roots.
6. Two-phase PT iteration with fugacity equality, material closure, convergence diagnostics and stable-solution checks against A/B/C.
7. Only after that qualification, scope provider/stream integration separately; do not change existing equipment energy models implicitly.

**Hydrocarbon two-phase VLE comes first. Water-containing oil/gas VLLE requires distinct qualification and must not be forced into this binary two-phase benchmark.** Physically calibrated future BIPs need separate provenance and qualification. This task stops at reference artifacts; no RioGineer EOS, cubic solver, fugacity evaluator, Rachford–Rice solver or flash implementation was added.
