# Pre-M18 — Configurable liquid-pump scope qualification

**Conclusion: a configurable bounded scope is supported, with a positive-rise
floor and mandatory runtime diagnostic guards.** This is numerical qualification
of the proposed scope, not a production pump implementation or completion of M18.
Study date: 2026-10-01. Human acceptance is not claimed.

## 1. Proposed versus supported ranges

Baseline: `main` at `81d183d804755bcf6e995b1c126407a4404cf94a`. The first Pre-M18
study was uncommitted; it was preserved. The unrelated `next-env.d.ts` change
was also preserved. Applicable AGENTS instructions, master context and prior
study/report/code/ledger were read before the extension.

| Variable              | Proposed                   | Supported by this numerical study                          |
| --------------------- | -------------------------- | ---------------------------------------------------------- |
| Inlet temperature     | 300–350 K                  | 300–350 K, inclusive                                       |
| Inlet pressure        | 20–25 MPa absolute         | 20–25 MPa absolute, inclusive                              |
| Discharge pressure    | Pin through 30 MPa         | Exact Pout=Pin identity, or Pin+10,000 Pa <= Pout <=30 MPa |
| Isentropic efficiency | 0.6–1                      | 0.6–1, inclusive                                           |
| Molar flow            | 5–200 mol/s                | Continuous interval 5–200 mol/s                            |
| Composition           | Equimolar methane/n-hexane | Fixed z=[0.5,0.5] only                                     |

Every accepted inlet, isentropic reference and actual discharge must also remain
within **300–370 K and 20–30 MPa**, pass stable-liquid and phase-witness checks,
and pass the inverse/work criteria below. These are rejection guards, not clamps.
The highest sampled temperature was 360.4202640897 K. Unsampled states that fail
a guard or a solver are rejected without an accepted pump outlet.

This replaces an exact-input allowlist with ranges and calculated-state checks.
It does not guarantee convergence at every unsampled point. A reference-table
lookup or interpolation is never used to calculate the pump outlet.

## 2. Fixed composition, model and independent authority

Retain canonical PR coefficients 0.45724/0.07780, existing molecular/critical
constants, explicit constant zero kij, existing Poling Cp data and the sensible
ideal-gas reference h=s=0 at 298.15 K/101325 Pa. Mixture ideal entropy and PR
departures remain included. Water, other compositions and the prior pure-hexane
and hexane-rich cases are outside this configurable scope.

Use the unchanged inlet PT/caloric -> discharge PS -> efficiency equation ->
actual discharge PH formulation. `h_target=h1+(h2s-h1)/eta`; power is
`F*(h2-h1)` in W for mol/s and J/mol, positive into the fluid. No heat transfer,
kinetic/potential-energy change, head, constant-density work, mechanical losses
or motor/electrical power is introduced.

The extension reference imports established benchmark-only Thermo PT/caloric and
independent inverse helpers. It never imports production numerical routines.
`reference.json` was frozen before production comparison. Production comparison
uses the unchanged public provider interfaces through the separately inspected
first-study adapter. Full 200–500 K inverse scans and tolerances are unchanged.

The actual reference environment remains Python 3.10.10, Thermo 0.6.0, Chemicals
1.5.2, Fluids 1.3.1, NumPy 2.2.6, SciPy 1.15.3 and Pandas 2.3.3; teqp 0.23.1 is
pinned but not used numerically. Dependency pins, component/Cp data, convention,
installed-library/data hashes and relevant source hashes are recorded. Production
source hashes are separate. No package installation was needed.

Prior source-compatible evidence is reused only at exact matching inputs and
matching hashes. Of 42 distinct intensive input tuples, three reuse prior
reference/production calculations; 39 receive new calculations. Four further
ledger rows reuse extension corner calculations as explicit conditioning entries.
Flow scaling reuses calculated intensive states legitimately; it does not cache or
skip any required fresh-final evaluation within a new inverse calculation.

## 3. Sampling plan, holdouts and coverage limits

`benchmarks/pump_energy/configurable_scope/PLAN.md` and `policy.py::cases` fixed
the plan and acceptance gates before production comparison:

- 16 coupled corners: two inlet temperatures, two inlet pressures, two
  efficiencies and minimum/maximum positive pressure rise.
- Four exact-pressure identities at inlet T/P corners.
- Six interior/coupled development cases varying pressure fraction, temperature
  and efficiency together.
- Eight deterministic off-grid holdouts, separate from guard development.
- Twelve conditioning entries: 10, 1,000 and 10,000 Pa rises at four limiting
  T/P/efficiency combinations. Four 10,000 Pa entries duplicate corner inputs.

**46 ledger entries, 42 distinct intensive tuples.** Final range policy accepts
38 entries / 34 distinct tuples, including all eight holdouts, and rejects eight
below-floor entries. The accepted entries include four identities and four reused
conditioning rows. No failed point was omitted.

The coupled corners test maximum work/heating and smallest admitted work; interiors
and holdouts probe pressures that change the full PS scan. This is structured
coverage rather than a full Cartesian product or proof of a continuous solution
surface. Runtime failure propagation remains necessary between samples.

## 4. Phase-boundary evidence and enforceable guards

Independent bubble-pressure evidence covers the full **300–370 K reached-state
guard**, not only inlet temperatures: 141 points at 0.5 K spacing plus eight
separate off-grid temperatures. All 149 have a bubble-pressure result, a VL PT
probe at 0.999 times that pressure, a liquid PT probe at 1.001 times that pressure,
and a stable-liquid independent PT witness at 16 MPa.

The largest sampled bubble pressure is **13.6860229102 MPa**. Observed central
derivatives, evaluated with +/-0.01 K probes, span approximately 5,945.58 to
57,167.04 Pa/K. All sampled derivatives are positive, but global monotonicity is
not assumed. The two-phase composition gap exceeds 0.4015 and the Z gap exceeds
0.3189 throughout the sampled branch; no sampled phase coalescence is observed.
These are branch-separation diagnostics, not a mixture critical-locus calculation.

The proposed **16 MPa engineering ceiling** is deliberately separated from the
sampled maximum. Its screening derivation uses a conservative 100,000 Pa/K slope
allowance over the nearest-node distance of 0.25 K (25,000 Pa) plus 1,000 Pa
numerical allowance. The remaining reserve is:

```text
16,000,000 - 13,686,022.9102 - 25,000 - 1,000
= 2,287,977.0898 Pa
```

The slope allowance is empirically supported by the finer grid and holdouts;
it is **not a rigorously proven derivative bound**. Therefore this is a conservative
engineering enclosure supported by independent numerical evidence, not a theorem
that 16 MPa globally bounds every mathematical branch. No interpolated saturation
table is needed in the runtime calculation. Undetected behavior between samples
remains residual numerical uncertainty.

To avoid relying on that empirical enclosure alone, the runtime proposal requires
a **fresh high-accuracy stable-liquid PT/caloric witness at the same temperature
and fixed z, at 16 MPa, for each of the three states**, in addition to successful
stable-liquid checks at their actual 20–30 MPa pressures. Witness failure,
non-liquid classification, indeterminate PIP, mismatched state, or nonfinite
properties rejects the calculation. The actual pressure is at least 4 MPa above
the engineering ceiling. This is a thermodynamic scope margin, not NPSH or a
cavitation-safety margin.

### Saturation precision and alternate-branch findings

The first boundary artifact is retained unchanged. Four unrestricted library
P/VF -> T round trips at 361.5, 362, 362.5 and 363 K return alternate temperatures
of about 394.4034, 393.9193, 393.4346 and 392.9494 K. They are recorded in the ledger
as alternate-branch returns, not silently treated as successful same-state round
trips. They lie outside the proposed 370 K state guard.

`boundary_refinement.json` separately records tighter library boundary controls
at all 149 temperatures and targeted local branch recovery at those four points.
The local fixed-T-bubble-pressure inversion uses T +/-0.25 K brackets and recovers
the intended branch within 1.91e-11 K. This does not claim global uniqueness.

Tightening the wrapper settings alone leaves some phase fugacity residuals near
1.2e-7, so `boundary_equations.json` adds a separate local coexistence-equation
check at every temperature. It solves the two component log-fugacity equalities
for log(P) and vapor composition, then requires the nontrivial branch and
independent stable PT states on both sides. Maximum final log-fugacity residual
is 4.89e-15; maximum pressure difference from the original boundary is 5.59e-8 Pa,
well within the predeclared 1,000 Pa numerical allowance. Pump states are always
obtained from stable PT equilibrium; this boundary check never forces a pump root.

The runtime uses **no new saturation routine or critical-locus dependency**.
The existing PT/caloric provider performs the witness checks. Fixed composition,
temperature/pressure restrictions, numerical branch evidence and runtime witnesses
act together. The known supercritical pure-methane counterexample is rejected by
composition/range policy; pure critical constants are not used for mixtures.

## 5. Small-work criterion and numerical justification

Exact Pout=Pin is a separate identity: validate all inputs and phase guards,
preserve the inlet, zero work, unavailable reconstructed efficiency and no PS/PH
diagnostics. No pressure epsilon converts small positive rise into equality.

For positive rise require **Pout-Pin >=10,000 Pa**, then independently require
positive isentropic/actual enthalpy increments and the runtime screening ratio
`E/abs(delta_h_actual) <= 1e-4` (the unchanged 0.01% criterion).

Using computed h1, h2s, h2 and specified eta:

```text
B(h) = 1e-6 + 1e-11*abs(h) J/mol
E = [B(h1)+B(h2s)]/eta + B(h1)+B(h2)
    + 370 K * 1e-8 J/(mol K) / eta
    + 1e-6 J/mol + arithmetic allowance
```

The arithmetic term is `64*machine_epsilon*max(1,abs(h1),abs(h2s),abs(h2))/eta`.
This is computable from runtime inputs/states; it uses no unknown reference value.
`B(h)` remains a **comparison allowance**, not a proven pointwise property-error
bound. E is a conservative engineering screening policy informed by independent
comparison and perturbation evidence, not a guaranteed uncertainty interval.

The PS term uses the single-phase constant-P/z identity dh=T ds and the full
allowed PS entropy residual, amplified by efficiency. The PH term separately
allows full target-recovery residual. Underlying forward-property discrepancies
are assessed through independent endpoint comparisons; they are not eliminated
by a small inverse residual. Subtraction roundoff and efficiency amplification
are retained explicitly.

At four limiting 10,000 Pa paths, independent tighter direct-caloric inversions
perturb entropy targets by +/-1e-8 J/(mol K) and enthalpy targets by +/-1e-6 J/mol.
Recovered isentropic-H changes are approximately 3.00e-6–3.51e-6 J/mol, below
the 3.70e-6 capacity; PH changes remain within approximately 1.001e-6 J/mol.
These perturbations test sensitivity rather than redefine comparison tolerances.

The largest accepted sampled E/delta_h is approximately **1.062e-5**, providing
about 9.4 times headroom to 1e-4. Independent actual-work differences are at most
4.73e-11 J/mol. The 10 Pa cases fail the old work-resolution criterion; 1,000 Pa
cases may satisfy it but are deliberately excluded by the new conservative floor.
No optimal minimum rise is claimed. The floor plus dynamic work screen provides
a simple useful region without qualifying arbitrarily small differences.

Input normalization must precede these SI comparisons and retain provenance.
For example, 200 bar absolute converts explicitly to 20,000,000 Pa. The next
representable pressure above Pin is a positive-rise rejection, not identity.
The next representable value below the rise floor is conservatively rejected.
No units, gauge reference or intended equality are guessed from numerical proximity.

## 6. Flow-scaling evidence and supported interval

For each accepted intensive calculation, scaling checks use F=5, 17.3, 83.7,
137.2 and 200 mol/s: **190 scaling records**, without repeated inversions.
M7 independently reconstructs molar flow/composition from component mass rates.
Checks cover component rates, total mass, molar closure, both enthalpy flows and
power. The prototype also accepts an additional unlisted F=91.234 mol/s in tests.

The formula depends linearly on F; intensive-state calculations have no flow
argument beyond independent material bookkeeping. Thus the supported interval
is continuous 5–200 mol/s, not the tested five flow values. Finite arithmetic and
closure checks remain mandatory. No pump capacity, hydraulic or sizing claim follows.

## 7. Comparisons, failures and remaining dependencies

All unchanged first-study comparison gates are retained: T 1e-7 K; H
1e-6+1e-11 abs(H); S 1e-8+1e-11 abs(S); Z 2e-10+1e-9 abs(Z);
composition/beta 2e-9; fresh PS residual 1e-8 J/(mol K); fresh PH residual
1e-6 J/mol. Work/power comparison allowances propagate the endpoint H gates.

**5,522 applicable checks pass: 4,392 numerical and 1,130 structural/policy checks.**
These counts include flow scaling and the eight intentionally rejected sub-floor
cases' independently comparable states. Rejection is not a numerical failure.

| Quantity                     | Maximum main-comparison absolute error |
| ---------------------------- | -------------------------------------: |
| State T                      |                            3.411e-13 K |
| Aggregate H                  |                        4.366e-11 J/mol |
| Aggregate S                  |                    1.422e-13 J/(mol K) |
| Actual delta_h               |                        4.730e-11 J/mol |
| Recovered power at 100 mol/s |                             4.730e-9 W |

No pump-path reference unavailability, production PS/PH failure or property scan
hole occurred in this extension matrix. Every non-identity PS uses the full
64-point 200–500 K scan; PH uses all 128 points; each accepts one candidate and
a fresh final state. This is sampled evidence, not guaranteed future convergence.
Synthetic tests verify controlled rejection of inverse failures, ambiguity,
missing fresh finals and altered domains rather than weakening the solvers.

All prior bubble-adjacent 8 MPa failures remain outside this region, and their
evidence remains unchanged. No PS interval-policy transplant, shortened scan,
PT change, caloric change or production saturation dependency is required here.
Any later expansion beyond this composition/region needs separate evidence.

Energy closure from power defined by the same H difference remains an algebraic
consistency check. Independent endpoint/work/power comparisons, entropy checks,
target recovery and perturbations provide separate numerical evidence. There is
no experimental, hydraulic, NPSH or cavitation validation.

## 8. Verification, artifacts and reproduction

**13 focused unittest methods passed**, including real captured off-grid cases,
source/hash preservation, full scans, phase-boundary evidence, small-work sensitivity,
M7/flow checks, identities, range/representation edges and clearly labelled
synthetic invalid-state/inverse failures. The actual thermodynamic reruns are the
separate reference/comparison reproduction gates, not simulated by those tests.

One final fresh-process byte-for-byte reproduction was performed for each new
numerical artifact. Ledger verification, syntax, formatting, whitespace and
preservation checks passed. No full application/Python/browser suites, servers,
commits or deployments were invoked.

From repository root:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/configurable_scope/reference.py
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/configurable_scope/boundary_refinement.py
.local/pre-m8-venv/bin/python -B benchmarks/pump_energy/configurable_scope/boundary_equations.py
engine/.venv/bin/python -B benchmarks/pump_energy/configurable_scope/compare_production.py
engine/.venv/bin/python -B benchmarks/pump_energy/configurable_scope/ledger.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/pump_energy/configurable_scope -p 'test_*.py' -v
```

Defaults verify; explicit `--write` creates only the corresponding extension
artifact. Existing study files must not be regenerated. Numerical JSON excludes
volatile logs/timing. `candidate_ledger.json` binds all artifact hashes and the
final runtime-prototype source hash.

| Artifact                 | SHA-256                                                            |
| ------------------------ | ------------------------------------------------------------------ |
| reference.json           | `282a43569321acdb3efacdff6e0caa19f7903fa0a1bbde94dd78b4e90ae6c048` |
| production.json          | `e9d4452b4bcef8c0d201f4b3eb05429aa6833dab9a36783c455f9ccc35d2d2b9` |
| boundary_refinement.json | `6172a20e733cc1b7dea37904cb310b51b9529c31115ebc59f6be29a5d2e2dbf6` |
| boundary_equations.json  | `c9d5823231763f3c96c489d5ab5a4cb7145bce3cd50a41be084f0f3afee0ba9d` |
| candidate_ledger.json    | `f38d78e39e68dfe77fc9dc2a65ce46a5a389ae162f7b6ededf50081befaaf0e7` |

## 9. Exact runtime policy recommended for M18

`runtime.py::admissibility` is the benchmark-only executable proposal. It reads
no frozen output table and no allowlist. A future adapter should:

1. Validate finite SI inputs, fixed equimolar recipe, explicit zero kij and the
   input ranges in section 1. Reject pressure reduction and sub-floor positive rise.
2. Evaluate inlet high-accuracy PT/calorics and the same-T 16 MPa witness. Reject
   unsupported states, failed stability, mismatched or nonfinite phase payloads.
3. For exact identity, preserve the inlet and return zero power without inverses.
4. Otherwise execute unchanged default PS, efficiency equation and PH. Require
   one candidate, full domains, high-accuracy PT and fresh final residuals. Never
   bridge a property hole or publish a failed/partial path as accepted.
5. Apply the 300–370 K / 20–30 MPa state window and the 16 MPa witness independently
   to the isentropic reference and actual discharge. Require stable single liquid
   and the unchanged overall/phase composition at all three states.
6. Require positive work, E/delta_h <=1e-4, target/recovered H and power agreement,
   reconstructed efficiency, entropy generation and eta=1 consistency. Validate
   finite extensive outputs and material closure using the actual flow.
7. Propagate any failure as controlled rejection. Never clamp, interpolate reference
   outputs, apply a constant-density substitute or reinterpret positive rise as identity.

The witness adds existing PT calls, not a new thermodynamic solver. Production
implementation must preserve this policy or separately qualify any simplification.

## 10. Next implementation step and change boundary

**Production pump implementation can now proceed under a separate request for
this configurable, guarded scope.** Numerical support extends beyond exact test
tuples while retaining explicit rejection and uncertainty limits. No mathematical
global phase/convergence guarantee or general mixture-critical detector is claimed.

Created code/artifacts/docs are confined to `benchmarks/pump_energy/configurable_scope/`
and this report. Only concise links/status notes were added to the parent benchmark
README and master context; the first study's conclusions remain intact as historical
evidence. All prior frozen references, comparisons, ledgers, production sources,
contracts, schemas, frontend/PFD and `next-env.d.ts` were preserved byte-for-byte.

No production pump, registration, contract or interface has been implemented.
All changes remain unstaged. M18 is not complete.
