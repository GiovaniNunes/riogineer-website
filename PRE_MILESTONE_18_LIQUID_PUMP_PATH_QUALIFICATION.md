# Pre-M18 — Liquid PS/PH pump-path qualification

**Outcome: prerequisite study passes for a narrower, explicitly enumerated scope.**
Study performed 2026-10-01. No production pump exists and M18 is not complete.
No experimental validation or cavitation qualification is established.

## 1. Baseline and authorized changes

Branch `main`, HEAD `81d183d804755bcf6e995b1c126407a4404cf94a`
(`docs: record M17 visual acceptance`). Applicable `AGENTS.md` and the master
context were read. Initial status contained only the pre-existing `next-env.d.ts`
development-type-path modification. It is preserved byte-for-byte.

Authorized additions are confined to `benchmarks/pump_energy/`, this report and
a concise master-context update. Production engine, PT/caloric/PS/PH solvers,
contracts, schemas, application fixtures, frontend, PFD and historical benchmark
sources/artifacts/tolerances remain unchanged. A SHA-256 snapshot of all existing
tracked files was checked after the work, allowing only the intended master-context
edit. No stage, commit, push, deployment or application-server restart occurred.

## 2. Formulation, assumptions and reference independence

Inputs are T1 in K, P1/P2 in Pa absolute, normalized methane/n-hexane molar z,
positive F in mol/s and `0 < eta <= 1`. Require P2 >= P1. No heat transfer,
reaction, accumulation or kinetic/potential-energy change is modeled.

For P2 > P1:

```text
PT(T1,P1,z) -> h1,s1
PS(P2,s1,z) -> T2s,h2s
delta_h_s = h2s-h1
h_target = h1+delta_h_s/eta
PH(P2,h_target,z) -> T2,h2,s2
W_target = F*(h_target-h1)
W_recovered = F*(h2-h1)
```

Enthalpy is J/mol, entropy J/(mol K), power W. Efficiency is the isentropic
enthalpy rise divided by the actual enthalpy rise. Power enters the fluid; it is
not electrical demand. Density, head, motor efficiency, mechanical losses,
constant-Cp and incompressible pressure-work substitutions are absent.

Exact equal pressure is a benchmark identity branch: validate input and liquid
inlet, preserve its state, return zero work and unavailable reconstructed
efficiency. It emits no fictitious PS/PH diagnostics. Positive unresolved work
is never converted into this identity branch.

`reference.py` imports only the established independent benchmark helpers:
`peng_robinson_ps/{equilibrium,solver}.py`, `peng_robinson_ph/{equilibrium,solver}.py`
and `peng_robinson_caloric/{reference,equations}.py`. It calls no production
numerical implementation. The inherited caloric module contains an unused
data-check function; this generator does not invoke it. A runtime module guard
and focused import/source checks supplement this source audit.

Thermo's stability-first `FlashVL.flash_TP_stability_test` supplies PT roots and
phases; library calorics are checked against independent direct equations at
every evaluation. PS uses the inherited complete 64-point 200–500 K scan and
bisection; PH uses the inherited complete 128-point scan and Brent refinement.
Fresh final residuals and one candidate are required. Reference solvers reject
scan holes. No reference hole occurred in these candidate inversions. Additional
canonical/small-work checks use direct caloric residuals, tighter 1e-12 K PS
refinement and PH bisection, sharing the same independent PT library.

The frozen JSON records all scans, failures, inputs, units, component/Cp data,
source/data hashes, actual versions and solver diagnostics. The separate
`compare_production.py` reads that artifact and calls unchanged public production
`equilibrium_caloric_PT`, `flash_PS` and `flash_PH`. Its results cannot define the
independent reference. Both paths share only declared study inputs, comparison
policy and bookkeeping, not thermodynamic implementations.

Reference environment: `.local/pre-m8-venv`, Python 3.10.10, Thermo 0.6.0,
Chemicals 1.5.2, Fluids 1.3.1, NumPy 2.2.6, SciPy 1.15.3, Pandas 2.3.3 and
teqp 0.23.1. teqp does not calculate the oracle. All transitive pins in
`requirements.txt` were verified against the actual environment. No installation
or dependency change was necessary.

The EOS uses canonical coefficients 0.45724/0.07780, existing component constants,
explicit constant zero kij and the Poling ideal-gas Cp records. Pure ideal-gas
h=s=0 at 298.15 K/101325 Pa; ideal mixing entropy and PR departures are retained.
The 200–500 K inverse domain is not a generally qualified operating envelope.

## 3. Investigated matrix and candidate outcomes

Every investigated path is retained in `candidate_ledger.json`, including failures.
Unless shown otherwise, F=100 mol/s and eta=0.8. P below is MPa absolute. Liquid
classifications were independently evaluated, not assumed from the inputs.

| Case            | z methane |               T1 K | P1 → P2       | eta / F variation | Outcome with unchanged production                     |
| --------------- | --------: | -----------------: | ------------- | ----------------- | ----------------------------------------------------- |
| CANONICAL       |       0.5 |                300 | 20 → 30       | —                 | Accepted                                              |
| P22             |       0.5 |                300 | 20 → 22       | —                 | Accepted                                              |
| ETA1            |       0.5 |                300 | 20 → 30       | eta=1             | Accepted                                              |
| ETA06           |       0.5 |                300 | 20 → 30       | eta=0.6           | Accepted                                              |
| HEXANE_P2       |         0 |                300 | 1 → 2         | —                 | Accepted                                              |
| HEXANE_P6       |         0 |                300 | 1 → 6         | —                 | Accepted                                              |
| T350            |       0.5 |                350 | 20 → 30       | —                 | Accepted                                              |
| HEXANE_RICH     |       0.1 |                300 | 6 → 10        | —                 | Accepted                                              |
| BUBBLE_BELOW    |       0.5 | 230.61755435138735 | 6 → 8         | —                 | Independent liquid path; production PS scan rejection |
| BUBBLE_MINUS_01 |       0.5 | 231.01755435138736 | 6 → 8         | —                 | Independent liquid path; production PS scan rejection |
| BUBBLE_PLUS_01  |       0.5 | 231.21755435138735 | 6 → 8         | —                 | Both paths reject VL inlet                            |
| FLOW5           |       0.5 |                300 | 20 → 30       | F=5               | Accepted                                              |
| FLOW200         |       0.5 |                300 | 20 → 30       | F=200             | Accepted                                              |
| IDENTITY_BINARY |       0.5 |                300 | 20 → 20       | —                 | Accepted identity                                     |
| IDENTITY_HEXANE |         0 |                300 | 1 → 1         | —                 | Accepted identity                                     |
| VAPOR_REJECTION |       0.5 |                300 | 0.001 → 0.002 | —                 | Both paths reject vapor inlet                         |
| DP_1000.0       |       0.5 |                300 | 20 → 20.001   | —                 | Accepted resolved small work                          |
| DP_10.0         |       0.5 |                300 | ΔP=10 Pa      | —                 | Positive but unresolved under work-accuracy criterion |
| DP_0.1          |       0.5 |                300 | ΔP=0.1 Pa     | —                 | Positive but unresolved under work-accuracy criterion |
| DP_0.001        |       0.5 |                300 | ΔP=0.001 Pa   | —                 | Positive but unresolved under work-accuracy criterion |

Totals: **20 candidates**. Independent reference: 15 accepted, three unresolved-work,
two phase rejections. Production: **13 accepted, two controlled PS failures,
three unresolved-work, two phase rejections**. None was silently dropped.
The 13 accepted tuples include two identities and two extra flow scalings;
they are not 13 unrelated thermodynamic paths.

Canonical independent values: T2s=303.7542654332 K, T2=305.5815250342 K,
delta_h_actual=1106.228601133975 J/mol and W=110622.8601133975 W.
The reference's two PS-blocked boundary paths produce liquid discharge at
231.5503539288 and 231.9526852662 K. These are independent results, not accepted
production pump outlets.

## 4. Liquid/phase-boundary admissibility policy

Independent endpoint evidence includes **31 distinct liquid endpoint T/P/z
states**, each with a same-temperature bubble-pressure calculation and PT probes
at 0.999 and 1.001 times that bubble pressure. All actual liquid endpoints lie on
the higher-pressure side. Each lower probe is non-liquid and each upper probe is
single liquid. These are local phase-boundary corroborations, not a critical-locus
solver or a proof over an interpolated region.

There are also **12 temperature boundary probes**: offsets -0.5, -0.1, -0.001,
0, +0.001 and +0.1 K around the binary bubble point at 6 MPa and pure n-hexane
saturation at 1 MPa. Independent and production labels agree on these probes.
The binary bubble temperature is 231.11755435138735 K; the pure n-hexane value is
437.9632531107387 K. The exact binary bubble point is labelled single liquid;
the exact pure saturation point is labelled single vapor. Thus a phase label
alone does not implement an exact-saturation exclusion.

A separate counterexample uses pure methane at 300 K/30 MPa. It exceeds its own
Tc=190.564 K and Pc=4599200 Pa, but **both implementations label it single liquid**.
Production reports converged stable phase evidence and PIP>1. This demonstrates
that stability+PIP is not a general supercritical exclusion. No pure-component
critical criterion is substituted for a mixture critical locus.

**Practical initial policy:** admit only the exact 13 accepted input tuples listed
in `candidate_ledger.json`; reject other T/P/z/eta/flow tuples. Require successful
stable liquid inlet, isentropic and actual states and all residual/work gates.
`scope.py::admissible` demonstrates this enforceable benchmark policy and rejects
unlisted neighboring states and the supercritical methane counterexample. It is
not installed as a production guard.

This deliberately restricted option needs neither an unqualified critical detector
nor a new runtime saturation solver. It supports controlled demonstrations and
equipment qualification at those cases. Arbitrary user-entered liquid operating
conditions, interpolation between accepted cases and continuous envelope claims
remain unqualified. A broader useful operating window requires a separately
qualified boundary/admissibility policy. No NPSH or cavitation safety follows.

## 5. Numerical comparisons and tolerances

Tolerances were defined in `common.py` before the first production evaluation.
No tolerance was changed to accept a production result.

| Quantity                           | Fixed comparison/acceptance gate         |
| ---------------------------------- | ---------------------------------------- |
| T                                  | 1e-7 K absolute                          |
| H, phase and aggregate             | 1e-6 + 1e-11 abs(H_reference), J/mol     |
| S, phase and aggregate             | 1e-8 + 1e-11 abs(S_reference), J/(mol K) |
| Z                                  | 2e-10 + 1e-9 abs(Z_reference)            |
| z and phase fractions/compositions | 2e-9 absolute                            |
| Fresh PS residual                  | 1e-8 J/(mol K) absolute                  |
| Fresh PH residual                  | 1e-6 J/mol absolute                      |
| Work differences                   | Sum of applicable endpoint H budgets     |
| Power differences                  | Work budget multiplied by F              |

Target-power allowance propagates inlet/isentropic H budgets through division by
eta; recovered-power allowance uses inlet/actual H budgets. Reconstructed-efficiency
comparison propagates numerator and denominator uncertainties, with a positive
resolved denominator. Identity has zero power and unavailable efficiency.

**1,215 applicable field/policy checks passed: 827 numerical and 388 structural,
phase or acceptance checks; zero failed comparisons.** This includes partial
inlet comparison for rejected/PS-failed paths, not a claim that those full paths
passed. Separate tests inspect the standalone PH diagnostics and boundary evidence.

Observed main-comparison maxima:

| Quantity        | Maximum absolute error | Case                                   |
| --------------- | ---------------------: | -------------------------------------- |
| State T         |           2.8422e-13 K | DP_10.0 actual outlet                  |
| Aggregate H     |        4.7185e-9 J/mol | BUBBLE_PLUS_01 inlet, rejected service |
| Aggregate S     |   2.0407e-11 J/(mol K) | BUBBLE_PLUS_01 inlet, rejected service |
| Actual delta_h  |       3.6380e-11 J/mol | P22; tied pure-liquid cases            |
| Recovered power |            3.6380e-9 W | P22; tied pure-liquid cases            |

All comparable states retain T/P/z/H/S/Z, phase identity and phase composition
checks. Successful production PS/PH records expose full default-domain scans,
one candidate and fresh final residuals. Stable-liquid states additionally check
converged stability, stable=true and liquid-like PIP. Flow scaling, component and
mass conservation, M7 reconstruction, ideal efficiency and entropy generation are
checked. No vapor-compressor temperature-ordering rule was imposed.

The material stream is only a benchmark construction here; no equipment adapter
or Stream Table implementation has been qualified. The focused M7 check confirms
that the case mass-rate inputs reconstruct the intended molar flow/composition.

Energy closure using W defined from the same H difference is explicitly an
**algebraic consistency check**. The independent state/work/power comparisons,
target-versus-recovered H residual and cross-method study provide separate
numerical accuracy evidence. None is experimental validation.

## 6. Small-work conditioning findings

Define B(h)=1e-6+1e-11 abs(h) J/mol. The prospective relative work-error budget is
`[B(h1)+B(h2)]/abs(delta_h_actual)`, conditional on both state-H comparisons passing.
The preselected resolved-work requirement is <=1e-4 (0.01%). It is a numerical
qualification criterion, not an experimental pump-accuracy specification.

| ΔP Pa | Independent delta_h J/mol | Relative budget | Policy     |
| ----- | ------------------------: | --------------: | ---------- |
| 1000  |           0.1120223665712 |       2.0842e-5 | Resolved   |
| 10    |           0.0011202198948 |       0.0020842 | Unresolved |
| 0.1   |             1.11983536e-5 |         0.20849 | Unresolved |
| 0.001 |             1.12602720e-7 |          20.734 | Unresolved |

Agreement between production and primary reference is much tighter than these
conservative budgets, but that alone cannot justify a smaller guaranteed work
threshold. PS entropy uncertainty maps into recovered enthalpy through the local
thermodynamic response; subtracting large referenced enthalpies and subsequent PH
inversion further condition the tiny difference. Absolute residual gates do not
guarantee small relative work or efficiency error.

The tighter independent direct-caloric/bisection cross-check changes delta_h by
approximately 1.09e-10 J/mol for CANONICAL, -4.24e-9 for DP_1000.0 and -8.22e-10
for DP_0.001. The last is approximately **0.736% relative** to the tighter result,
despite excellent absolute-H agreement. It supports retaining the unresolved
classification and unavailable reconstructed efficiency.

The smallest **tested** resolved rise is 1000 Pa at this inlet/composition/eta.
No universal minimum pressure rise is established, nor is the untested interval
between 10 and 1000 Pa qualified. Future production should reject unresolved
positive work explicitly rather than return identity or report precise efficiency.

## 7. Production PS/PH limitations or defects

Both boundary paths use discharge pressure 8 MPa. Their unchanged production PS
scans finish all 64 points and find one candidate, but two PT evaluations fail:

- 461.9047619047619 K: `flash_not_converged`.
- 466.6666666666667 K: `flash_not_converged`.

PS returns `property_evaluation_failed`, no fresh final and no accepted isentropic
or actual outlet. This is a reproducible limitation of the current full-scan
acceptance policy combined with PT nonconvergence, not evidence that the cold
liquid pump path is physically impossible. The independent full scans succeed.

A **separate** diagnostic calls production PH with the frozen independent outlet
H target. Both cases succeed with one candidate in
[230.70866141732284, 233.07086614173227] K. Their 128-point scans retain four PT
failures at 462.20472440944883, 464.56692913385825, 466.92913385826773 and
469.29133858267716 K. The bracket does not cross a hole, and fresh PH residuals
pass. This demonstrates the already-qualified M16 PH valid-interval policy.
It does not bypass PS or rescue a production pump result.

No production numerical change is required for the 13 admitted tuples. Supporting
the two boundary paths requires a separately scoped follow-up: independently
qualify recovery of the two failing PT states, or independently assess a PS
valid-interval policy with ambiguity, holes, gaps and fresh-final protections.
This study establishes neither remedy and implements neither. Silently narrowing
the 200–500 K scan or copying PH's policy into PS would be unjustified.

## 8. Scope supportable by the evidence

Supported: the 13 exact ledger tuples, explicit-zero-kij methane/n-hexane including
the studied pure n-hexane states, liquid inlet/reference/discharge, fluid work,
the tested flow scaling and two equal-pressure identities. The eight principal
non-boundary requested paths all pass. One additional small-rise case passes.

Excluded: the two 8 MPa PS-blocked paths, non-liquid inlets, unresolved positive
work, exact saturation, unlisted or supercritical service, arbitrary compositions
or ranges, water, VLLE, mixed equipment networks/recycles, head, curves, NPSH,
hydraulics, sizing, motor/electrical power and phase-changing HX support.

The restriction is a finite qualification matrix, not a generally qualified
liquid-pump operating envelope. The label limitation is addressed by restricted
admissibility, not claimed solved by PIP.

## 9. Tests actually run and reproducibility

- Independent reference generated and then rebuilt in a fresh process: exact
  byte-for-byte reproduction, including cross-method and boundary evidence.
- Full separate production comparison generated and reproduced in a fresh
  process: exact byte-for-byte reproduction, including controlled failures.
- **18 focused unittest methods passed**: ten reference/evidence checks and eight
  production/evidence checks. Input-guard coverage includes 13 invalid prototype
  specifications; these are not claimed as production pump validation.
- Candidate-ledger reproduction, Python syntax, documentation formatting,
  whitespace and historical-file SHA-256 preservation checks passed.
- No complete Python, TypeScript, browser or application-build suite was run.
  No application server was started or restarted.

The focused tests consume captured evidence and check source hashes; actual
thermodynamic re-execution is the separate generator/comparator reproduction
gate. An altered-H test confirms the comparator detects corrupted values.
Numerical artifacts omit volatile runtime/timing metadata.

From repository root, read-only verification commands:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/reference.py
engine/.venv/bin/python -B benchmarks/pump_energy/compare_production.py
engine/.venv/bin/python -B benchmarks/pump_energy/scope.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/pump_energy -p 'test_*.py' -v
```

Only explicit `--write` regenerates the respective new artifact; defaults verify.
Do not regenerate historical reference files. Full scans are preserved in the
JSON rather than dumped to terminal output.

Frozen independent SHA-256:
`6c0f7b33d9b4aea4ecd6b3f09bab70b22d46fa711a725bbfeab0cd3e63ad8f07`.
The production artifact records this hash; `candidate_ledger.json` records both
reference and production artifact hashes. Source hashes bind numerical evidence
to the generating and compared implementations.

## 10. Recommendation for the next implementation step

Proceed, under a separate implementation request, with a **restricted source →
pump → sink equipment qualification** consuming these independent accepted cases.
Retain exact-input admissibility, stable-liquid checks at all three states,
resolved-work checks, explicit identity and fluid-power semantics. Preserve the
two PS failures as controlled rejection regressions.

If the intended product must accept freely entered liquid states rather than
this finite supported set, further admissibility/envelope qualification is a
prerequisite. Inclusion of the bubble-adjacent 8 MPa paths additionally needs the
bounded PS/PT follow-up described above. That is the material scope decision;
no solver change is necessary merely to implement the narrower qualified cases.

**Pre-M18 prerequisite study complete for the stated narrower scope. Pump
implementation and M18 remain unstarted. Human-operated acceptance of this study
has not been claimed.**
