# Milestone 8.1 — PT Boundary Robustness and Precision Controls

## Status and objective

**Milestone 8.1 automated acceptance is complete. Human-operated validation was successfully completed on 2026-09-29.**

Production M8.1 implements a bounded stability-derived restart and explicit
opt-in PT precision. The human-operated validation record below is separate from
automated coverage. **M11 remains NOT IMPLEMENTED** and blocked pending separate
authorization; no PH/PS implementation or equipment integration is introduced.

The independent acceptance authority is the committed
`PRE_M8_1_PT_BOUNDARY_QUALIFICATION.md` and
`independent_pr_pt_boundary@1.0` JSON. Production never imports independent
thermodynamic libraries or uses frozen answers as initial guesses.

## Original blockers and correction

Bubble-side failure was not an RR numerical-convergence defect. Stability found
an unstable feed, but Wilson K gave F(0)<0 and F(1)<0, so those initial K had no
physical interior RR root. PT had no alternative initialization. A single restart
now supplies a stability-derived seed to the existing RR/successive-substitution
loop. No RR equation, [0,1] domain, endpoint classification, bisection, 2e-14
internal residual target or iteration limit changed.

Dew-side liquid-enthalpy error after local H matching arose from finite PT
accuracy propagating into recovered temperature, not a material M10 caloric
arithmetic discrepancy. M10 equations, data and reference conventions are
unchanged. High accuracy is an explicit consumer choice; existing equipment
continues to use the historical standard profile.

## Architecture and runtime seed

Only `engine/riogineer_engine/pr_flash.py` changes production. After converged
instability and an **initial**, converged RR endpoint tendency, the flash attempts
one stability seed. Nonconverged RR and later K-update failures do not trigger
restart. Stable feeds retain the existing single-phase path.

The helper reuses actual converged TPD trials. It evaluates the existing EOS
`lowest_gibbs` and `phase_identification` APIs at parent and candidate compositions
to label orientation; it neither repeats stability minimization nor duplicates
EOS equations. This matters because these vapor-like trials have one cubic root
and the original trial label is `single_root`. Existing PIP semantics, after
instability is established, distinguish liquid parent (PIP>1) and vapor trial
(PIP<1). Singular/ambiguous PIP remains an explicit numerical failure.

Candidates must be converged, refined negative-TPD minima (TPD/RT < -1e-9).
Candidates are ordered by lowest TPD then composition; the first qualified
vapor-like candidate is selected. Opposite orientation is not inferred from K
magnitude. Unsupported orientation/no candidate returns the historical
`rachford_rice_not_converged` failed-initialization status with a specific message.
It is not a claim that RR numerically iterated without convergence.

For stationary normalized trial w:

```text
S = exp(-TPD(w)/(R*T))
K_i,seed = S*w_i/z_i
         = phi_i(parent)/phi_i(trial)    [at stationarity]
```

S retains the instability magnitude. Normalized w/z alone puts F(0) near zero.
The production golden-section stationary composition has finite numerical
precision; the equation-level fugacity-ratio equivalence is at stationarity,
not a claim that its finite seed must equal the independently refined seed
bit-for-bit. Final equilibrium still passes all normal acceptance gates.

The mapping requires positive binary feed fractions. Pure/zero-inventory feeds
retain their existing stable path and component identity. An artificial unstable
zero-feed seed request fails before division. Trial dimensions/normalization,
positive finite K and finite S>1 are checked. Component order comes from the
same validated EOS/feed/BIP used for stability. No species is removed.

Compact initialization diagnostics retain Wilson K/RR, restart count, actual
trial w/TPD/S, ordered seed K, parent/trial PIP and restart RR beta/status. Existing
final fugacity/material/common-tangent stability checks remain mandatory. Failed
attempts publish no valid phase/beta/K result. Process serializers continue to
select their existing fields, so no process contract or equipment edit is needed.

## Immutable precision controls

`SolverSettings()` remains standard. `SolverSettings.high_accuracy()` explicitly
selects `AccuracyProfile.HIGH_ACCURACY`. The immutable dataclass carries profile,
resolved fugacity/material targets and historical iteration limits in provenance.
Conflicting profile/tolerance inputs are rejected, not silently overridden. There
are no arbitrary tolerance overrides or mutable global settings.

| Control                            | Standard | High accuracy |
| ---------------------------------- | -------- | ------------- |
| Max absolute log-fugacity residual | 1e-11    | 1e-12         |
| Material target                    | 1e-10    | 1e-10         |
| Outer flash limit                  | 100      | 100           |
| Stability refinement limit         | 100      | 100           |
| RR limit                           | 200      | 200           |
| RR internal residual target        | 2e-14    | 2e-14         |

Provider remains `peng_robinson@1.0`; component data remains
`riogineer_components@1.0`, caloric data `riogineer_caloric@1.0`.
BIP is `methane_nhexane_explicit_zero@1.0`: explicit zero kij independent M8
benchmark, not fitted physical interaction data.

## Bubble boundary and complete neighborhood

Independent equilibrium onset is **231.1175543513151 K**. Wilson F(0) changes sign at **231.39704486494975 K**. The first is a physical equilibrium boundary; the second is a numerical capability of raw Wilson initialization. P=6000000 Pa absolute, z=[0.5,0.5] in methane/n_hexane order throughout this matrix.

| Case                 | T K                | Reference phase | Production phase | Wilson root? | Restarts | Beta ref               | Beta prod              | Result |
| -------------------- | ------------------ | --------------- | ---------------- | ------------ | -------- | ---------------------- | ---------------------- | ------ |
| BUBBLE_STABLE_231_10 | 231.09999999999999 | single_liquid   | single_liquid    | False        | 0        | 0                      | 0                      | PASS   |
| BUBBLE_MINUS_1MK     | 231.1165543513151  | single_liquid   | single_liquid    | False        | 0        | 0                      | 0                      | PASS   |
| BUBBLE_MINUS_0_1MK   | 231.1174543513151  | single_liquid   | single_liquid    | False        | 0        | 0                      | 0                      | PASS   |
| BUBBLE_PLUS_0_1MK    | 231.11765435131511 | vapor_liquid    | vapor_liquid     | False        | 1        | 1.1607702196446834e-06 | 1.1607652652401157e-06 | PASS   |
| BUBBLE_PLUS_1MK      | 231.11855435131511 | vapor_liquid    | vapor_liquid     | False        | 1        | 1.160745192158919e-05  | 1.1607439205363335e-05 | PASS   |
| BUBBLE_231_15        | 231.15000000000001 | vapor_liquid    | vapor_liquid     | False        | 1        | 0.00037632691268735914 | 0.00037632690603572883 | PASS   |
| BUBBLE_231_199       | 231.19921259842519 | vapor_liquid    | vapor_liquid     | False        | 1        | 0.00094601040972386568 | 0.0009460104055847296  | PASS   |
| BUBBLE_231_25        | 231.25             | vapor_liquid    | vapor_liquid     | False        | 1        | 0.0015325152906187189  | 0.0015325152839125167  | PASS   |
| BUBBLE_CENTER        | 231.29921259842519 | vapor_liquid    | vapor_liquid     | False        | 1        | 0.0020994740065362959  | 0.0020994739974753429  | PASS   |
| BUBBLE_231_349       | 231.3492125984252  | vapor_liquid    | vapor_liquid     | False        | 1        | 0.0026741381030192229  | 0.0026741380916064372  | PASS   |
| BUBBLE_231_399       | 231.39921259842518 | vapor_liquid    | vapor_liquid     | True         | 0        | 0.0032474302768552639  | 0.0032474302734613048  | PASS   |
| BUBBLE_231_45        | 231.44999999999999 | vapor_liquid    | vapor_liquid     | True         | 0        | 0.003828351194879182   | 0.003828351183074119   | PASS   |

12 discovered, 12 compared, 12 passed, 0 failed. Three stable-liquid controls have no vapor payload; seven of nine split states use a restart. The two Wilson-root controls follow the original path.

## Bubble-center detailed comparison

| Quantity                        | Independent reference       | Production                | Absolute error / status              |
| ------------------------------- | --------------------------- | ------------------------- | ------------------------------------ |
| T_K                             | 231.29921259842519          | 231.29921259842519        | 0                                    |
| P_Pa_abs                        | 6000000                     | 6000000                   | 0                                    |
| classification                  | vapor_liquid                | vapor_liquid              | matches                              |
| beta                            | 0.0020994740065362959       | 0.0020994739974753429     | 9.0609529428131719e-12               |
| Minimum TPD/RT                  | -0.0015658454268388793      | -0.0015658454268390068    | 1.2750217548429532e-16               |
| Trial orientation               | liquid_parent_vapor_trial   | liquid_parent_vapor_trial | matches                              |
| Stability S                     | 1.0015670720029153          | 1.0015670720029153        | 0                                    |
| Wilson K methane                | 1.9960975002122512          | 1.9960975002122512        | 0                                    |
| Wilson K n_hexane               | 0.00011962800146122918      | 0.00011962800146122918    | 0                                    |
| Wilson RR F0                    | -0.001891435893143778       | -0.001891435893143778     | 0                                    |
| Wilson RR F1                    | -4178.8739372271621         | -4178.8739372281789       | 1.0168150765821338e-09               |
| Wilson RR status                | liquid_tendency             | liquid_tendency           | matches                              |
| Seed K methane                  | 2.0009815141035125          | 2.0009815138277616        | 2.7575097760745848e-10               |
| Seed K n_hexane                 | 0.0021526299023181417       | 0.0021526301780690621     | 2.7575092036158377e-10               |
| Restart initial beta            | 0.0015689126962169708       | 0.0015689126970812595     | 8.6428867535071063e-13               |
| liquid composition methane      | 0.49895032260830607         | 0.49895032261284589       | 4.5398129699947276e-12               |
| liquid composition n_hexane     | 0.50104967739169393         | 0.50104967738715411       | 4.5398129699947276e-12               |
| liquid Z                        | 0.25742606080796449         | 0.25742606080696323       | 1.0012546347581974e-12               |
| liquid phi methane              | 1.4890043030078843          | 1.4890043030044591        | 3.425260075573533e-12                |
| liquid phi n_hexane             | 0.00011255787622721597      | 0.0001125578762274737     | 2.5772840892696047e-16               |
| vapor composition methane       | 0.99892192903255184         | 0.99892192903255184       | 0                                    |
| vapor composition n_hexane      | 0.0010780709674481168       | 0.0010780709674481389     | 2.211772431870429e-17                |
| vapor Z                         | 0.69701848436195368         | 0.69701848436195324       | 4.4408920985006262e-16               |
| vapor phi methane               | 0.74374098291189794         | 0.74374098291189739       | 5.5511151231257827e-16               |
| vapor phi n_hexane              | 0.052312963871978334        | 0.052312963871978167      | 1.6653345369377348e-16               |
| Final K methane                 | 2.0020468647271352          | 2.0020468647089191        | 1.8216095298839718e-11               |
| Final K n_hexane                | 0.0021516249108475892       | 0.0021516249108671287     | 1.9539491552533761e-14               |
| Max final log-fugacity residual | 2.7644553313166398e-14      | 6.8266503561176251e-12    | production <= 1e-11                  |
| Flash iterations                | 17                          | 14                        | diagnostic; different initialization |
| Restart count                   | independent seed experiment | 1                         | one bounded production attempt       |

Runtime proof: w=[0.99892536893522055, 0.0010746310647794521]; TPD/RT=-0.0015658454268390068; S=exp(-TPD/RT)=1.0015670720029153. Multiplying S*w/[0.5,0.5] gives exactly the recorded production seed [2.0009815138277616, 0.0021526301780690621]. Parent PIP=10.23170679133558, trial PIP=0.23129499497429745; restart RR beta=0.0015689126970812595. Focused tests reconstruct this identity from runtime diagnostics and change feed composition to prove the seed changes with the actual feed. No frozen seed is imported by production.

## Dew precision and downstream M10 propagation

Exact frozen T=467.7658895316326 K, P=6000000.0 Pa absolute, z=[0.5, 0.5]. Existing `equilibrium_caloric_PT` evaluates fresh PT with the supplied settings, then enriches precisely those phases; no M10 formula is copied or changed.

| Quantity                    | Standard              | High accuracy          | Independent reference        |
| --------------------------- | --------------------- | ---------------------- | ---------------------------- |
| Profile                     | standard              | high_accuracy          | independent equilibrium      |
| Fugacity target             | 1e-11                 | 1e-12                  | independent full equilibrium |
| Iterations                  | 59                    | 65                     | 61                           |
| Max log-fugacity residual   | 7.812306357379839e-12 | 7.2308825593836445e-13 | 5.4511950509095186e-14       |
| beta                        | 0.98687445415521324   | 0.9868744541918204     | 0.986874454195794            |
| liquid composition methane  | 0.2138793996309635    | 0.21387939963096689    | 0.21387939963097552          |
| liquid composition n_hexane | 0.78612060036903653   | 0.78612060036903297    | 0.78612060036902454          |
| liquid Z                    | 0.31392088454265898   | 0.31392088454266048    | 0.31392088454266426          |
| liquid h_ig_J_mol           | 24703.1493530802      | 24703.14935308012      | 24703.149353079923           |
| liquid h_res_J_mol          | -15434.275657464506   | -15434.275657464375    | -15434.275657464068          |
| liquid h_J_mol              | 9268.8736956156936    | 9268.8736956157445     | 9268.8736956158555           |
| vapor composition methane   | 0.5038054375016694    | 0.50380543749091478    | 0.50380543748974727          |
| vapor composition n_hexane  | 0.49619456249833055   | 0.49619456250908522    | 0.49619456251025273          |
| vapor Z                     | 0.6965737829481472    | 0.69657378293600625    | 0.69657378293468786          |
| vapor h_ig_J_mol            | 18085.681121280042    | 18085.681121525515     | 18085.681121552159           |
| vapor h_res_J_mol           | -4857.2071446311393   | -4857.2071448292627    | -4857.2071448507759          |
| vapor h_J_mol               | 13228.473976648904    | 13228.473976696252     | 13228.473976701385           |
| H_eq J/mol                  | 13176.502061633173    | 13176.502061824849     | 13176.502061845651           |

| Quantity                    | Standard absolute error | High-accuracy absolute error | Frozen allowance       |
| --------------------------- | ----------------------- | ---------------------------- | ---------------------- |
| beta                        | 4.0580760973796259e-11  | 3.9735992274358978e-12       | 1.9868744541957942e-09 |
| liquid.composition.methane  | 1.201816424156732e-14   | 8.6319840164605921e-15       | 1.2138793996309757e-09 |
| liquid.composition.n_hexane | 1.1990408665951691e-14  | 8.4376949871511897e-15       | 1.7861206003690245e-09 |
| vapor.composition.methane   | 1.1922129949937244e-11  | 1.1675105326958146e-12       | 1.5038054374897475e-09 |
| vapor.composition.n_hexane  | 1.1922185461088475e-11  | 1.1675105326958146e-12       | 1.4961945625102529e-09 |
| liquid.Z                    | 5.2735593669694936e-15  | 3.7747582837255322e-15       | 4.1392088454266432e-10 |
| vapor.Z                     | 1.3459344749833235e-11  | 1.3183898417423734e-12       | 7.9657378293468788e-10 |
| liquid.h_J_mol              | 1.6189005691558123e-10  | 1.1095835361629725e-10       | 1.9268873695615854e-07 |
| vapor.h_J_mol               | 5.2481482271105051e-08  | 5.133188096806407e-09        | 2.3228473976701385e-07 |
| H_eq                        | 2.1247797121759504e-07  | 2.0801962818950415e-08       | 2.317650206184565e-07  |

Standard remains numerically identical to committed pre-change standard PT at
this state (beta, compositions, Z, K and fugacity residuals; 59 iterations).
The comparison retains standard caloric errors as **diagnostics**, not new
high-accuracy acceptance gates: standard vapor residual h differs by
2.1963660401524976e-7 J/mol versus 1.4857207144850777e-7 allowed by the tighter
caloric field comparison. This expected finite-PT-precision diagnostic is visible
and is not hidden by changing a tolerance. Standard is explicitly not required to
meet the newly qualified downstream margin. High accuracy passes all such checks.

The high-accuracy local H-conditioning diagnostic reproduces only the frozen
T_ref±0.001 K VLE interval, evaluates the existing provider at every trial and
checks a fresh final state. It is benchmark-only evidence, not a production PH
solver or qualification of the PH matrix. It uses no SciPy in production tooling.

| Downstream item                | Production evidence    |
| ------------------------------ | ---------------------- |
| Recovered diagnostic T K       | 467.76588953170369     |
| H residual J/mol               | 1.8189894035458565e-12 |
| Governing field                | liquid.h_J_mol         |
| Actual error J/mol             | 1.9805156625807285e-08 |
| Frozen allowance J/mol         | 1.9268873695615854e-07 |
| Minimum allowance/error margin | 9.7292205558765321     |
| Required margin                | 5                      |

High accuracy takes 6 additional iterations (10.169492%) at this dew state only. All iteration limits are unchanged. Standard/high/standard state, controls and diagnostics are identical; repeated high-accuracy results are identical. The JSON records these checks.

## Maximum errors across the comparison

| Quantity                          | Bubble matrix max error   | Fixed-T high-accuracy dew max error |
| --------------------------------- | ------------------------- | ----------------------------------- |
| beta                              | 1.2716225855370069e-11    | 3.9735992274358978e-12              |
| x                                 | 6.3446470299766133e-12    | 8.6319840164605921e-15              |
| y                                 | 2.2204460492503131e-16    | 1.1675105326958146e-12              |
| Z                                 | 1.4003243009597099e-12    | 1.3183898417423734e-12              |
| K                                 | 2.535194276731545e-11     | 5.5537796583848831e-12              |
| ln_phi                            | 3.2258640203508548e-12    | 1.5838441669302483e-12              |
| equilibrium log-fugacity residual | 9.5104479846952472e-12    | 7.2308825593836445e-13              |
| h_L                               | not a bubble caloric gate | 1.1095835361629725e-10              |
| h_V                               | not a bubble caloric gate | 5.133188096806407e-09               |
| H_eq                              | not a bubble caloric gate | 2.0801962818950415e-08              |

## Automated coverage and regression record

| Validation                                  | Result                                                                                                     |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| New M8.1 production tests                   | 32 passed                                                                                                  |
| Complete Python                             | 172 passed                                                                                                 |
| TypeScript                                  | 200 passed / 18 files                                                                                      |
| Browser                                     | 31 passed                                                                                                  |
| Pre-M8 independent                          | 7 passed                                                                                                   |
| M8 production comparison                    | 122 passed                                                                                                 |
| M9 equipment/process integration            | 7 passed                                                                                                   |
| Pre-M10 independent                         | 23 passed                                                                                                  |
| M10 production comparison                   | 1526 passed                                                                                                |
| Pre-M11 independent PH                      | 55 passed; not production M11                                                                              |
| Pre-M8.1 independent                        | 28 passed                                                                                                  |
| M8.1 production comparison                  | 325 passed; 12/12 bubble cases                                                                             |
| Contract parity / ESLint / TypeScript types | passed                                                                                                     |
| Python syntax / formatting / whitespace     | passed                                                                                                     |
| Production build                            | passed                                                                                                     |
| Production smoke                            | 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery passed |

Focused tests cover all 12 bubble states, runtime S*w/z, changed-feed propagation,
one retry/no retry loop, failed stability, failed/later RR, final stability
rejection, malformed trials, candidate ordering/orientation, zero inventory,
immutable controls, conflicts, historical standard beta/iteration count,
standard/high/standard isolation, repeatability, high-accuracy M10 comparison,
downstream margin and frozen reader integrity. M8/M10 tests are included in the
complete Python suite.

Initial validation issues were resolved without changing historical expected
values: the new failed-initialization message initially used a new status; the
historical RR failure status was preserved. HTTP tests required sandbox permission
for loopback sockets. A build run concurrently with browser tests removed their
nested `.next/e2e` directory and caused one browser timeout; the complete browser
suite was rerun after build completion. The first smoke run on port 3200 was
rejected by the configured origin policy; the matching SITE_URL runtime setting
resolved it. These were diagnostic/status or test-environment issues, not frozen
thermodynamic acceptance regressions.

Reproduction commands from the repository root:

```sh
(cd engine && .venv/bin/python -B -m unittest discover -s tests -v)
(cd engine && .venv/bin/python -B -m unittest discover -s tests -p 'test_pr_pt_boundary.py' -v)
(cd engine && .venv/bin/python -B -m unittest discover -s tests -p 'test_equilibrium_separator.py' -v)
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ph -p 'test_*.py' -v
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_boundary -p 'test_*.py' -v
npm test
npm run test:e2e
npm run contracts:check
npm run lint
npm run typecheck
npm run format:check
npm run build
# In a separate terminal after build; do not build while browser tests run:
SITE_URL=http://127.0.0.1:3200 RIOGINEER_LLM_PROVIDER='' npm run start -- --port 3200
SMOKE_URL=http://127.0.0.1:3200 npm run smoke
git diff --check
```

Python syntax was checked with `ast.parse` without writing bytecode. New Python
files were checked for trailing whitespace; the new Markdown report was checked
with repository Prettier. The untouched historical master document uses its
existing formatting rather than an unrelated whole-file rewrite.

## File inventory and isolation

| Category                 | File                                                            | Purpose                                                                                  |
| ------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Modified production      | engine/riogineer_engine/pr_flash.py                             | Single stability restart, immutable named controls, compact internal diagnostics         |
| Created production tests | engine/tests/test_pr_pt_boundary.py                             | 32 focused acceptance/safety regressions                                                 |
| Created comparison       | benchmarks/peng_robinson_pt_boundary/compare_production.py      | Hash-validated frozen reader, production comparison and local precision diagnostic       |
| Created evidence         | benchmarks/peng_robinson_pt_boundary/production_comparison.json | Full-precision production states, checks and diagnostics; distinct from frozen reference |
| Created documentation    | MILESTONE_8_1.md                                                | Production implementation and automated acceptance record                                |
| Modified documentation   | docs/RIOGINEER_MASTER_CONTEXT.md                                | Minimal M8.1 capability/status and M11 blocked status                                    |

Independent Pre-M8.1 was committed before implementation at `1e8efc5ab2ff88daed80c30403afc9c38e70e4be`. A pre-edit SHA-256 snapshot covered all 249 tracked files. The frozen boundary JSON remains SHA-256 `e5346c3a65c17e2f128e1a581d354e7404fc86fbf86e578fa9f4dc9798f20ad0`; the comparison reader checks these exact bytes and expected version/component/case identities. Historical benchmark scripts, references, reports and existing comparison evidence remain unchanged.

No changes to pre-M8, M8 frozen reference, M9 fixtures, pre-M10/M10 frozen or
comparison evidence, pre-M11 PH or pre-M8.1 independent files. Existing M8, M9
and M10 accepted numerical regressions pass unchanged. The intended new behavior
is successful equilibrium for previously failing bubble-side states.

Requirements/flowsheet/results contracts changed: **no / no / no**. No production
dependency added. Production imports none of Thermo, Chemicals, fluids, SciPy or
teqp. No process-equipment calculation changed (HEATER_1, COMPRESSOR_1, SEP_PR_1,
valves, mixer, pump or others); no process caller migrates to high accuracy.
No workspace, PFD, Stream Table, UI, frontend-contract or fixture change.
No live LLM/provider call, commit or push was made.

## Limitations and human validation

This qualifies the frozen methane/n_hexane zero-kij boundary matrix and dew
precision experiment. It does not establish universal behavior for arbitrary
mixtures/nonzero BIPs, water, VLLE, three phases, critical regions, retrograde
systems, opposite stability orientation or every near-boundary topology. The
positive-binary liquid-parent/vapor-trial mapping is the qualified restart scope.
Existing mechanical/root/normalization/stability failures remain explicit.

## Human-operated validation — 2026-09-29

The user reported successful manual execution and review of the bubble-center
and dew-precision commands on 2026-09-29. This human-operated acceptance is
recorded separately from the automated coverage above; it does not qualify
functionality outside the defined M8.1 scope.

### Bubble-center review

The user ran:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py --case bubble_center
```

The review confirmed:

- stability correctly identified an unstable state;
- raw Wilson initialization returned `liquid_tendency`, with no physical two-phase RR root;
- exactly one stability-derived restart produced a physical two-phase RR solution;
- the final phase was `vapor_liquid`, with beta approximately 0.002099473997475343;
- the maximum final log-fugacity residual was approximately 6.83e-12;
- the run completed with `PASS: 325 comparisons`.

### Dew-precision review

The user ran:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py --case dew_precision
```

The review confirmed:

- standard and `high_accuracy` targets were 1e-11 and 1e-12, respectively;
- standard required 59 iterations and `high_accuracy` required 65;
- the high-accuracy maximum final log-fugacity residual was approximately 7.23e-13;
- high-accuracy fields passed, with a production downstream H-conditioning margin of approximately 9.729×;
- standard/high/standard identical = `True`;
- repeated high-accuracy result identical = `True`;
- the run completed with `PASS: 325 comparisons`.

The displayed standard caloric diagnostic failure was expected and is not a
high-accuracy acceptance gate. The human review recognized it as evidence for
why the explicit high-accuracy profile is required.

Only the two commands above are recorded as manually reviewed. The full-matrix
and details commands below remain reproduction options, not additional claims
of human review. The comparison CLI's unchanged pending-validation footer is
historical automated-run wording; this dated documentation records the current
human-validation status. No comparison code or artifact changed in this update.

### Reproduction commands

Use these repository-root commands without `--write` (the display filter never
skips acceptance cases):

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py --case bubble_center
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py --case dew_precision
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py --details
```

No general PH diagnostic or PH matrix acceptance was added. The benchmark-only
local H-conditioning experiment measures the requested downstream error margin.
**M8.1 human-operated validation is recorded as successful. M11 remains NOT
IMPLEMENTED and blocked pending separate authorization.** M11 was not started
or resumed during this documentation update. No commit or push was made.
