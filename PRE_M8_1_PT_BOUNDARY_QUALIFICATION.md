# Pre-M8.1 — PT Boundary Robustness and Precision Qualification

## Status and scope

Independent acceptance evidence completed on 2026-09-29. **No production M8.1
correction is implemented. M11 remains blocked.** This freezes a small boundary
matrix and a precision study before changing the PT implementation. It does not
qualify a new production solver, resume M11 or introduce process integration.

Only this report and the new `benchmarks/peng_robinson_pt_boundary/` directory
were created. No existing file, tolerance, contract, fixture, dependency manifest,
production implementation or historical frozen reference changed. The repository
was clean at the start; a snapshot of all tracked-file hashes protects this boundary.

## Blocker origin and independent stack

The read-only M11 investigation found two distinct limitations. Near the bubble
boundary, production stability correctly detects instability, but raw Wilson K
has no physical RR root and PT stops before updating K. Near the dew boundary,
PT's current stopping accuracy leaves a small equilibrium-H offset. Inversion
compensates by moving T, making liquid enthalpy narrowly miss the inherited PH
comparison even though the final H residual is very small.

Thermo 0.6.0 owns this independent reference's PR EOS, fugacity, stability and
caloric properties. SciPy 1.15.3 supplies bracketed scalar roots. Chemicals 1.5.2,
fluids 1.3.1 and NumPy 2.2.6 are the same isolated pre-M8/pre-M10 stack. The local
requirements pins retain that complete stack (including unused teqp 0.23.1);
no dependency was installed or added to production. Reproduction uses Python
3.10.10 in `.local/pre-m8-venv` and requires no server or runtime network.

The new scripts reuse only independent benchmark helpers, never production
Python. Existing helper/reference hashes are frozen in metadata. `study.py`
contains an auditable independent successive-substitution experiment using
library fugacity evaluations and SciPy RR roots. It does not copy production
EOS or caloric equations and is not a replacement production flash framework.

All cases use methane/n_hexane in that order, z=[0.5,0.5], P=6000000 Pa absolute,
canonical PR coefficients 0.45724/0.07780 and R=8.31446261815324 J/(mol K).
Exact M7/M8 component constants, the explicit symmetric zero-kij matrix,
`methane_nhexane_explicit_zero@1.0` identity and mathematical-benchmark provenance
are preserved in JSON. Caloric properties retain the pre-M10 convention:
pure ideal-gas h=s=0 at 298.15 K / 101325 Pa, no formation terms. No Cp extrapolation.

## Bubble boundary and classification evidence

The new independently refined bubble temperature is **231.1175543513151 K**.

The unchanged independent P/VF=0 call first locates 231.11755435138735 K.
Its unrefined incipient composition leaves a maximum log-fugacity residual about
5.13e-9, which failed the new inherited 1e-9 equilibrium check. This is retained
as **raw diagnostic evidence**, not silently accepted. Refining the stationary
condition S(T)=1 shifts temperature by -7.2247985e-11 K.
The final maximum log-fugacity residual is
2.264855e-14. No old boundary value or reference
was rewritten; its temperature difference is negligible relative to inherited
qualification tolerances. The refinement gives the new incipient composition a
proper equilibrium check without loosening acceptance.

Exact saturation is stored as liquid plus **incipient** vapor evidence, not a
finite vapor stream or a compulsory classification at numerically exact beta=0.
Tests instead require stable liquid below and a real split above the boundary,
including ±0.0001 K and ±0.001 K neighborhoods.

| Case                 | T K             | Independent phase | beta                | Wilson F(0)          | Wilson F(1)      | Wilson interior root |
| -------------------- | --------------- | ----------------- | ------------------- | -------------------- | ---------------- | -------------------- |
| BUBBLE_STABLE_231_10 | 231.1           | single_liquid     | 0                   | -0.0057367748465861  | -4234.5076926292 | no                   |
| BUBBLE_MINUS_1MK     | 231.11655435132 | single_liquid     | 0                   | -0.0054175445776529  | -4229.8528377154 | no                   |
| BUBBLE_MINUS_0_1MK   | 231.11745435132 | single_liquid     | 0                   | -0.0054001875590892  | -4229.5999359249 | no                   |
| BUBBLE_PLUS_0_1MK    | 231.11765435132 | vapor_liquid      | 1.1607702196447e-06 | -0.0053963304210605  | -4229.5437378466 | no                   |
| BUBBLE_PLUS_1MK      | 231.11855435132 | vapor_liquid      | 1.1607451921589e-05 | -0.0053789731973722  | -4229.2908569407 | no                   |
| BUBBLE_231_15        | 231.15          | vapor_liquid      | 0.00037632691268736 | -0.0047724132057797  | -4220.4660151209 | no                   |
| BUBBLE_231_199       | 231.19921259843 | vapor_liquid      | 0.00094601040972387 | -0.0038227325649591  | -4206.6968275862 | no                   |
| BUBBLE_231_25        | 231.25          | vapor_liquid      | 0.0015325152906187  | -0.0028421360536341  | -4192.5402297021 | no                   |
| BUBBLE_CENTER        | 231.29921259843 | vapor_liquid      | 0.0020994740065363  | -0.0018914358931438  | -4178.8739372272 | no                   |
| BUBBLE_231_349       | 231.34921259843 | vapor_liquid      | 0.0026741381030192  | -0.00092501074478568 | -4165.0405212774 | no                   |
| BUBBLE_231_399       | 231.39921259843 | vapor_liquid      | 0.0032474302768553  | 4.193223113147e-05   | -4151.2588373063 | yes                  |
| BUBBLE_231_45        | 231.45          | vapor_liquid      | 0.0038283511948792  | 0.0010246327426466   | -4137.3128587055 | yes                  |

Three cases are stable single liquid; nine are two phase. Seven two-phase cases
have no physical Wilson RR root. Below the boundary the reference has beta=0,
no vapor phase payload, no fabricated y and no equilibrium K vector.

## Wilson limitation and why RR itself is correct

RR uses F(beta)=Σ z_i(K_i−1)/(1+beta(K_i−1)), with physical beta in [0,1].
Positive K keeps denominators positive throughout that interval. F(0)≤0 is a
liquid tendency; F(1)≥0 is a vapor tendency. Neither establishes phase stability.
Only F(0)>0 and F(1)<0 brackets an interior RR root. Equality is an endpoint,
not permission to fabricate a finite second phase.

At this pressure/composition, the independent bubble occurs at 231.1175543513151 K, while Wilson F(0) changes sign at **231.39704486494975 K**. The sampled intervening split region has negative Wilson F(0)/F(1), so no physical root exists for those guesses. The independent stability result and equilibrium split remain valid. This is an initialization mismatch, not an RR tolerance or bisection defect.

## Center-state independent reference

| Quantity                         | Value                                            |
| -------------------------------- | ------------------------------------------------ |
| T K                              | 231.29921259842519                               |
| beta                             | 0.002099474006536296                             |
| x                                | [0.4989503226083061, 0.5010496773916939]         |
| y                                | [0.9989219290325518, 0.0010780709674481168]      |
| Z L                              | 0.2574260608079645                               |
| Z V                              | 0.6970184843619537                               |
| Final K                          | [2.0020468647271352, 0.002151624910847589]       |
| phi L                            | [1.4890043030078843, 0.00011255787622721597]     |
| phi V                            | [0.7437409829118979, 0.052312963871978334]       |
| Log-fugacity residual vector     | [2.7644553313166398e-14, -2.353672812205332e-14] |
| Material reconstruction residual | [-5.551115123125783e-17, 0.0]                    |
| Stationary vapor-trial TPD/RT    | -0.0015658454268388793                           |

## Stability-derived initialization theory and experiment

For a liquid parent at feed composition z, let w be a nontrivial stationary
vapor trial and define:

```text
W_i = z_i * phi_i(parent,z) / phi_i(trial,w)
S = sum(W_i)
w_i = W_i / S
K_i,seed = W_i / z_i = S*w_i/z_i
TPD(w)/(R*T) = -ln(S)                 [at stationarity]
```

Negative TPD means S>1. Keeping S preserves the instability driving force.
Using only normalized w_i/z_i discards it: F(0)=Σw_i−1≈0, so the initial guess
is artificially placed at an endpoint. The fugacity-ratio and S·w/z mappings
are checked numerically against the independently converged Michelsen trial.
The trial refinement uses a squared-correction tolerance 1e-24 in the independent
library; that is **not** a proposed production log-fugacity tolerance.

This mapping is specifically for the qualified liquid-parent/vapor-trial,
positive binary-composition bubble cases. Opposite-parent orientation, zero
fractions and other mixtures need explicit treatment before broader use.
A nontrivial negative-TPD trial is an initialization source, not final beta/x/y.

| Center initialization quantity | Value                                       |
| ------------------------------ | ------------------------------------------- |
| w                              | [0.9989253690728804, 0.001074630927119689]  |
| S                              | 1.0015670720029153                          |
| W                              | [1.0004907570517563, 0.0010763149511590709] |
| K seed                         | [2.0009815141035125, 0.0021526299023181417] |
| F(0) with seed                 | 0.0015670720029153373                       |
| F(1) with seed                 | -231.52389691397082                         |
| Initial RR beta                | 0.0015689126962169708                       |
| Normalized-only F(0)           | 1.1102230246251565e-16                      |
| Stationarity error             | 1.1102230246251565e-16                      |

Independent restart experiments converge from the stability-derived seeds for
all nine split states, taking 10–16 outer iterations at a 1e-12 log-fugacity
target. They reproduce the separately obtained independent equilibrium state
under inherited PH field tolerances. No equilibrium beta or final K is supplied
as an initial answer.

Future restart acceptance: if stability says unstable and Wilson cannot bracket
an interior RR root, attempt a justified stability-based seed, recheck RR
endpoints, and then iterate to equilibrium. On failure report the actual
initialization/convergence cause. Never reinterpret Wilson's endpoint tendency
as stable liquid, force a negative-beta root into [0,1], invent residual signs,
or create vapor in the independently stable liquid region. RR remains unchanged
conceptually. No production restart has been added in this task.

## Dew reference and same-state caloric agreement

Exact T from committed PH_DEW_BELOW: **467.7658895316326 K**, P=6000000 Pa, z=[0.5,0.5]. Classification: vapor_liquid; beta=0.986874454195794; H_eq=13176.502061845651 J/mol.

| Quantity    | Liquid                                    | Vapor                                     |
| ----------- | ----------------------------------------- | ----------------------------------------- |
| composition | [0.21387939963097552, 0.7861206003690245] | [0.5038054374897473, 0.49619456251025273] |
| Z           | 0.31392088454266426                       | 0.6965737829346879                        |
| phi         | [2.9131102599632492, 0.26825614451753255] | [1.2366962067026528, 0.42499796917153154] |
| h_ig_J_mol  | 24703.149353079923                        | 18085.68112155216                         |
| h_res_J_mol | -15434.275657464068                       | -4857.207144850776                        |
| h_J_mol     | 9268.873695615855                         | 13228.473976701385                        |

Log-fugacity residuals: [5.440092820663267e-14, -5.4511950509095186e-14].

The earlier read-only investigation found same-T liquid-h differences of only
~8.55e-11 J/mol at the recovered T and ~1.62e-10 J/mol at frozen T. At identical
T/composition the caloric remainder was ~2.36e-11 J/mol. Thus a M10 arithmetic
change is not justified. This new independent study also checks library caloric
values against unchanged pre-M10 direct equations for every recorded phase.

The upstream PT beta and vapor-composition offset changes equilibrium H. Matching
that biased H to a target shifts recovered temperature; liquid h then changes
with T. The diagnostic below isolates this mechanism without modifying production.

## PT precision sensitivity

The independent experiment uses raw Wilson K at the known dew-side VLE state,
undamped fugacity-ratio successive substitution and a SciPy bracketed RR root.
RR residual is verified ≤2e-14 and raw composition sums ≤1e-12 before roundoff
normalization. All states must pass component reconstruction ≤1e-10. No global
production setting or existing benchmark setting is changed.

Each stopping target is compared with the independent full-equilibrium reference.
This is production-like convergence logic evaluated through **independent**
Thermo arithmetic, not a bitwise reproduction of production iteration history.
The local enthalpy-matching experiment solves within T_ref±0.001 K, verifies
independent VLE classification at every evaluated temperature, and uses a fresh
final state. It is a conditioning/accuracy experiment, **not production PH or
resumed M11**.

Fixed-temperature absolute errors (H/h in J/mol):

| Target | Iterations | Final max log-f residual | beta error          | max x error         | max y error         | max Z error         | h L error           | h V error           | H eq error          |
| ------ | ---------- | ------------------------ | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| 1e-10  | 53         | 8.4266149613654e-11      | 4.3531256377349e-10 | 8.604228440845e-16  | 1.2788714531808e-10 | 1.4437362416686e-10 | 1.4551915228367e-11 | 5.6300996220671e-07 | 2.2792846721131e-06 |
| 1e-11  | 59         | 7.8184125840153e-12      | 4.0648706622903e-11 | 5.5511151231258e-16 | 1.1941836408624e-11 | 1.3481327165721e-11 | 2.3646862246096e-11 | 5.2570612751879e-08 | 2.1283449314069e-07 |
| 3e-12  | 62         | 2.3820945216357e-12      | 1.2579937092028e-11 | 2.2204460492503e-16 | 3.6958214266747e-12 | 4.1723291488438e-12 | 1.4551915228367e-11 | 1.6269041225314e-08 | 6.5869244281203e-08 |
| 1e-12  | 65         | 7.2608585810485e-13      | 4.0306646909016e-12 | 4.4408920985006e-16 | 1.1841638780652e-12 | 1.3368195439512e-12 | 1.0913936421275e-11 | 5.2114046411589e-09 | 2.1102096070535e-08 |
| 3e-13  | 68         | 2.2082335959794e-13      | 1.4240830736867e-12 | 1.6653345369377e-16 | 4.1844305798122e-13 | 4.7217785237308e-13 | 0                   | 1.8389982869849e-09 | 7.4560375651345e-09 |
| 1e-13  | 71         | 6.7057470687359e-14      | 6.3060667798709e-13 | 1.1102230246252e-16 | 1.8529622280994e-13 | 2.093880624443e-13  | 1.8189894035459e-12 | 8.1126927398145e-10 | 3.2978277886286e-09 |

Downstream comparison after local H matching uses the unchanged frozen PH values/tolerances:

| PT target | delta T K           | Liquid h error J/mol | Allowed J/mol       | H residual J/mol     | Minimum margin factor | All inherited checks |
| --------- | ------------------- | -------------------- | ------------------- | -------------------- | --------------------- | -------------------- |
| 1e-10     | 7.7590129876626e-09 | 2.1715877664974e-06  | 1.9268873695616e-07 | -1.4551915228367e-11 | 0.088731728889296     | FAIL (diagnostic)    |
| 1e-11     | 7.2458306021872e-10 | 2.0279549062252e-07  | 1.9268873695616e-07 | 2.0008883439004e-11  | 0.95016282839753      | FAIL (diagnostic)    |
| 3e-12     | 2.2430413082475e-10 | 6.2780600273982e-08  | 1.9268873695616e-07 | -1.6370904631913e-11 | 3.0692401174128       | PASS                 |
| 1e-12     | 7.1906924858922e-11 | 2.0123479771428e-08  | 1.9268873695616e-07 | 5.4569682106376e-12  | 9.5753189381166       | PASS                 |
| 3e-13     | 2.5465851649642e-11 | 7.1322574513033e-09  | 1.9268873695616e-07 | 0                    | 27.016514514762       | PASS                 |
| 1e-13     | 1.1311840353301e-11 | 3.1614035833627e-09  | 1.9268873695616e-07 | 5.4569682106376e-12  | 60.950375956492       | PASS                 |

The standard 1e-11 experiment deliberately retains the downstream liquid-h miss.
That diagnostic FAIL is expected evidence, not an omitted acceptance failure.
The 1e-10 experiment is also insufficient. Margins improve as convergence tightens;
liquid fixed-T differences already sit at roundoff, so they are not required to
be monotonically decreasing. The physically significant beta/vapor/H errors
and downstream margin show the consistent trend.

## Recommended accuracy and numerical margin

Recommend a future **high-accuracy maximum log-fugacity residual of 1e-12**.
Before choosing among the six candidates, this study uses a new design-margin
criterion of at least **5×** against every inherited downstream PH field check
(T, beta, x/y, Z, ideal/residual/total phase h and H_eq). This is a recommendation
criterion for the new study, not a modification of acceptance tolerances.

1e-12 is the loosest tested target meeting that margin. It takes **65 rather
than 59 iterations** at the reference state: six extra iterations, approximately
10.2% more outer updates. The minimum observed downstream margin is **9.5753×**;
liquid-h error is **2.01235e-8 J/mol** against **1.92688737e-7 J/mol** allowed.
At 3e-12 the margin is only 3.0692×; 3e-13 and 1e-13 give 27.0× and 61.0× but
require 68 and 71 iterations. They are not necessary for this scoped target.

No stronger RR requirement was needed. Retain the existing production 2e-14 RR
criterion unless future production qualification supplies contrary evidence.
The independent experiment caps outer iterations at 200, but every measured
precision case converges within the existing production limit of 100. No
production iteration-limit increase is currently justified.

The reference sensitivity slopes and measured local-inversion comparisons are
frozen in JSON. This is evidence for these particular states, not a guarantee
of the same cost or margin throughout the entire PH matrix.

## Future controls, provenance and historical defaults

Use explicit internal standard/high-accuracy profiles or equivalent immutable
solver controls. **Standard must preserve current 1e-11 convergence and historical
M8/M9 results.** Do not silently tighten a global default to make M11 pass.
The future inverse-calculation consumer should explicitly request high accuracy.

The smallest useful control set is a resolved fugacity target and a bounded
maximum outer iteration count, plus explicit restart policy/version. Keep RR
acceptance fixed for now; avoid exposing unqualified numerical knobs through
process contracts. A future boundary fallback should activate only after
instability is established and Wilson cannot seed a split; successful historical
paths must remain unchanged. Standard precision and robustness fallback are
separate design concerns.

Future provenance should retain requested profile, resolved numerical targets,
iteration limits, restart algorithm/version and whether it was used, alongside
provider, component/caloric datasets and BIP identity. A future nested PH result
should carry this PT policy and actual final PT result, allowing comparison of
trial/final accuracy. No production API names or provenance fields are implemented.

## Acceptance tolerances and frozen artifact

Reference ID: `independent_pr_pt_boundary@1.0`.
Artifact: `benchmarks/peng_robinson_pt_boundary/methane_nhexane_pt_boundary_reference.json`.

All historical tolerance dictionaries are copied verbatim as metadata and
checked against source references. External comparisons use atol+rtol·|reference|.
For phase fractions/compositions/Z and caloric properties, the inherited PH/M10
limits apply; no tolerance was relaxed. Log-phi comparisons use the M8 log-phi
limit; phi comparisons can be expressed in log space. Final K is y/x and its
allowance should follow the inherited component composition bounds, not a newly
invented loose K threshold. Material reconstruction is ≤1e-10. The exact boundary
refinement additionally demonstrates log-fugacity residual below 1e-11.

The precision experiment's requested stopping targets are diagnostic independent
inputs, clearly separate from frozen external acceptance and from unchanged
production settings. The JSON retains full useful float precision, deterministic
case IDs, source hashes, all 12 bubble references and initialization records,
raw/refined saturation evidence, dew reference, six precision histories and local
H-matching evidence. Ordinary reproduction never rewrites a reference; only the
explicit `--write` flag writes this new artifact.

## Tests, regressions and integrity

- New independent boundary suite: **28 tests passed**.
- Pre-M8 independent suite: **7 tests passed**.
- M8 production comparison: **122 comparisons passed**.
- Pre-M10 independent suite: **23 tests passed**.
- M10 production comparison: **1526 comparisons passed**.
- Pre-M11 independent PH suite: **55 tests passed**.
- Determinism: two complete fresh builds match frozen bytes.

The new saturation-phase test initially exposed the raw P/VF composition precision
issue described above; the new independent refinement resolves it without changing
historical files or tolerances. No prior regression failed.

Syntax, Markdown formatting, new-file whitespace, source hashes and Git integrity
were checked separately. No existing tracked file changed; the Master Context
and milestone reports remain untouched. No production M8.1 code, production PH,
equipment changes or live LLM/provider calls were introduced.

## File inventory and reproduction

Created:

- `PRE_M8_1_PT_BOUNDARY_QUALIFICATION.md` — this report.
- `benchmarks/peng_robinson_pt_boundary/study.py` — independent library evaluations and accuracy experiments.
- `benchmarks/peng_robinson_pt_boundary/reference.py` — deterministic assembly/reproduction.
- `benchmarks/peng_robinson_pt_boundary/methane_nhexane_pt_boundary_reference.json` — new frozen evidence.
- `benchmarks/peng_robinson_pt_boundary/test_reference.py` — 28 independent tests.
- `benchmarks/peng_robinson_pt_boundary/requirements.txt` — isolated dependency pins.
- `benchmarks/peng_robinson_pt_boundary/THIRD_PARTY_NOTICES.txt` — reused data/software attribution.

From the repository root:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_pt_boundary/reference.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_boundary -p 'test_*.py' -v
```

Historical regression commands:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ph -p 'test_*.py' -v
```

## Limitations and recommendation

Separately authorize M8.1 to implement and qualify the boundary fallback and an
explicit high-accuracy profile against this evidence while preserving historical
standard results. Then reassess M11; do not resume it automatically.

No unresolved discrepancy remains within this independent qualification matrix.
The production correction and its full-regression proof remain outstanding.
Seed mapping is limited to the qualified liquid-parent/vapor-trial orientation;
critical regions, arbitrary mixtures/BIPs, water/VLLE, pure coexistence and broad
phase-envelope behavior remain outside scope. No general PH/PS implementation or
process-energy integration is qualified here.

**Pre-M8.1 PT boundary qualification completed. M11 remains blocked pending
a separately authorized production M8.1 correction.**
