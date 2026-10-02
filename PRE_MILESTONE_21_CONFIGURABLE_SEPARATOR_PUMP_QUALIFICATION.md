# PRE-M21 — Configurable separator-to-pump qualification

Study date: 2026-10-01, America/Sao_Paulo. **Decision D: extension including the
known 8 MPa paths requires separately qualified solver/admissibility changes.**
Current routines also support additional numerical exact candidates, but this
study does **not** qualify a continuous configurable domain. M20 remains accepted
for exactly its existing 30 combinations. **M21 is unimplemented.**

## 1. Verified baseline and preservation

Branch `main`; full HEAD, local `main`, `origin/main`, and live remote
`refs/heads/main` all matched:

`b256ee38e1dedc62872e18b5fc8832bf12bc5a2c`

The index was empty. Initial status was only:

```text
 M next-env.d.ts
 M tsconfig.json
```

Captured SHA-256 values:

| File | SHA-256 |
| --- | --- |
| next-env.d.ts | 0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc |
| tsconfig.json | e2a28ab5d02bb5b555a28523be8786d9dc3a400fe125f14602261e24a6288126 |

Their bytes were also copied to `/tmp/riogineer-pre-m21/`. The new
`benchmarks/configurable_separator_pump/baseline.json` hashes all **488** original
tracked working-tree files and records the master-context prefix length. Only an
append to that context is permitted. The initial sandboxed remote lookup could
not resolve GitHub; a permitted read-only retry confirmed the live hash. No fetch,
reset, stage, commit, push, deployment, application edit or service change occurred.

## 2. Constraints and dependencies

Reviewed AGENTS.md, current master context, M19/M20 reports, both Pre-M20 reports,
their ledgers/artifacts/reproduction code, M8.2 stability/PT evidence, M10 caloric
conventions, M11 PH and M13 PS qualification, and the relevant production modules
and integration tests. The M16 PH interval correction and M18 inverse guard were
read to resolve the different current PS/PH failure policies. No full-project
reaudit or new component/data qualification was undertaken. The installed Next
project-structure guide was consulted; no Next code was changed.

M20's input-only exact-combination restriction remains in
`engine/riogineer_engine/separator_pump_scope.py` and `separator_pump_cases.json`.
Actual source execution and graph resolution remain in `separator_pump_process.py`;
source/enthalpy/local checks in `separator_liquid_state.py`; pump orchestration in
`separator_liquid_pump.py`. Shared PT/PS/PH, calorics and M17–M19 remain unchanged.
Editable IDs do not establish execution provenance. No derived stream was admitted
by deleting upstream Hdot or relabelling it an independent feed.

Only methane/n-hexane and an explicit constant zero 2x2 kij are studied. The
200–500 K inverse domain is inherited, not a blanket thermodynamic envelope.
Water, new components, calibrated kij, critical-region qualification, hydraulics,
NPSH, cavitation safety, sizing and electrical power remain outside scope.

## 3. Actual 8 MPa chains and failure mechanism

Both sources were freshly executed through M17 from their **actual recorded
recipes**, rather than the similarly named earlier Pre-M13 states (whose rounded
or historical temperatures differ). Each feed is 100 mol/s, z=(0.5,0.5), Pin=7 MPa;
each separator is specified-temperature at 6 MPa. Exact recipes, material rates,
upstream Hdot, parent phase diagnostics and real run/input identities are retained
in `sources.json`.

| Quantity | PT_BUBBLE_BELOW_8MPA | PT_BUBBLE_ABOVE_8MPA |
| --- | ---: | ---: |
| Source feed Tin, K | 230.60146798619095 | 230.7220225690974 |
| Separator Tout / pump Tin, K | 231.06755435138734 | 231.16755435138973 |
| Parent equilibrium | single_liquid | vapor_liquid |
| Liquid methane mole fraction | 0.5 | 0.4997106092421193 |
| Liquid flow, mol/s | 100 | 99.94203100395112 |
| Retained upstream Hdot, W | -2540375.0361407287 | -2538803.192458195 |
| Pump Pout, Pa abs | 8000000 | 8000000 |
| Efficiency | 0.8 | 0.8 |
| Independent inlet H, J/mol | -25403.7503614073 | -25402.75764815932 |
| Independent inlet S, J/(mol K) | -98.87679248117604 | -98.84861756279591 |
| Independent PS T, K | 231.62864734074992 | 231.7288906905257 |
| Independent PS H, J/mol | -25239.20653043886 | -25238.146003891106 |
| Independent actual PH T, K | 232.00297744760923 | 232.10320007317674 |

The first inlet passes the compressed-liquid witness. The second is the extracted
saturated liquid of a verified two-phase parent. Both actual separated streams
pass the unchanged source contract; neither is a bulk VL pump feed.

For **both** paths, unchanged production PS returns `property_evaluation_failed`.
Its trials identify `pt_evaluation_failure`, underlying `flash_not_converged`, at
**461.9047619047619 K and 466.6666666666667 K**, at 8 MPa and the respective actual
liquid composition. The complete 64-point scan still records a candidate bracket
**[228.57142857142858, 233.33333333333334] K**, but PS rejects before refinement.
Production does not reach its actual PH stage or publish an accepted pump outlet.
The intended chain is PS(P2, s1, x) → hs, then
PH(P2, h1+(hs−h1)/eta, x) → actual outlet, with fluid power F(h2−h1).
The inlet Hdot remains the separator's conserved value throughout the contract
and integrated-energy checks; a fresh matching h1 is corroborating evidence.

Direct fresh PT diagnostics locate the failure more precisely:

- Initial TPD stability **converges** and finds an unstable homogeneous parent,
  identifying a VL region. This is not a failed initial stability search.
- The equilibrium iteration reaches its **100-iteration limit**. For the first
  path, maximum log-fugacity residuals are approximately **7.637e-12** and
  **3.476e-9**, both above the unchanged high-accuracy **1e-12** requirement.
  The second path has essentially the same residuals. Mass/RR residuals are small.
- The failed production result has no accepted phase classification/caloric state;
  the final common-tangent stability result is unavailable. A converged initial
  instability test must not be misrepresented as a converged final equilibrium.
- Independent Thermo equilibrium resolves these points and the ±0.01/±0.1 K
  neighborhoods as VL. Entropy exceeds the actual inlet target by approximately
  **101.85–101.88** and **104.31–104.34 J/(mol K)** at the two central points.
  The production failures persist at all ten immediately surrounding probes per
  path, so they are not merely isolated unlucky floating-point coordinates.

This evidence separates **PT equilibrium nonconvergence** from the **PS scan-policy
rejection** it triggers. The required liquid root is far away and independently
established. The failed region is physically characterized at the sampled points;
it is not dismissed as irrelevant without evidence. Neither these neighborhoods
nor any finite scan proves that every unsampled state or root is known.

Independent PS scans at 64 and 256 points each find one candidate and no holes;
the 256-point minimum sampled entropy slopes are 0.3259109676888774 and
0.32610521809826 J/(mol K²). No competing physical root was observed. All reference
inlet/ideal/actual endpoints are single liquid. Five intermediate discharge
pressures (6.2, 6.5, 7.0, 7.5, 7.8 MPa) independently recover liquid PS/PH endpoints.
Default production succeeds at the first three and fails PS at 7.5 and 7.8 MPa
for both paths. These are sampled paths, not a continuous-path guarantee or a
qualified threshold at 7 MPa.

**PH diagnostics are relevant but cannot replace PS.** At the independently
calculated actual enthalpy target, production PH succeeds and recovers the actual
endpoint. PH also succeeds at a target calculated from the isolated production-PT
prototype PS endpoint. Both PH scans retain four PT holes, near 462.2047244,
464.5669291, 466.9291339 and 469.2913386 K. M16's existing PH implementation
partitions valid sampled intervals and accepts the one observed bracket without
bridging holes; the current pump guard explicitly permits such off-bracket PH
scan failures. PS still requires a hole-free scan. A PH success is therefore
neither surprising nor proof that production completed the full pump chain.

No observed failure establishes phase inadmissibility of the required 8 MPa
endpoints, an unsupported component/caloric domain, or multiple roots. What remains
unqualified is production inverse coverage/policy and any stronger configurable
or continuous-path assertion.

## 4. Independent methodology

The separate `benchmarks/configurable_separator_pump/` extension reuses unchanged
independent M17 source and M18 pump-reference infrastructure. Reference processes
assert that no production thermodynamic module is imported. Production streams
supply pump **inputs**, never expected endpoint properties or substituted answers.
Each source recipe is also calculated independently, with independent M17
propagated source/phase/flow/duty allowances, so downstream agreement cannot mask
an unqualified upstream recipe. Real captured UUIDs are retained; reproduction
compares source numerics and semantic hashes without inventing deterministic UUIDs.

Installed versions and module/data hashes are verified against preserved evidence:
Thermo 0.6.0, Chemicals 1.5.2, Fluids 1.3.1, NumPy 2.2.6, SciPy 1.15.3 and the
other pinned packages recorded in `reference.json`. Pins and notices remain in
`benchmarks/pump_energy/configurable_scope/`. No packages were installed.

The model is canonical PR (a coefficient 0.45724, b coefficient 0.07780), Soave
alpha, quadratic a mixing with (1-kij), linear b mixing, explicit zero kij.
Component critical constants/acentric factors and Poling ideal-Cp coefficients are
recorded in the reference artifact. R=8.31446261815324 J/(mol K); pure ideal H=S=0
at 298.15 K and 101325 Pa, with ideal composition-mixing entropy. No formation
enthalpy or third-law entropy offsets are added. Library phase calorics are
cross-checked against independent direct equations; phase-weighted equilibrium
properties retain actual phase compositions. Thermo stability/roots/calorics are
independent implementations, but share the stipulated physical model/data basis.
This is numerical model agreement, not experimental validation.

Units: K, Pa absolute, mol/mol, H J/mol, S J/(mol K), molar flow mol/s, Hdot and
fluid power W. kg/h=F*z*MW*3.6 for MW in kg/kmol; mol/s=kmol/h÷3.6; Hdot=F*H.

`PLAN.md` fixes criteria before classification: T 1e-7 K; H 1e-6+1e-11|H|;
S 1e-8+1e-11|S|; beta/composition 2e-9; Z 2e-10+1e-9|Z|; PS entropy residual
1e-8; PH enthalpy residual 1e-6. The M20 propagated work budget retains its 500 K
entropy-residual term and E/Δh≤1e-4. No tolerance was relaxed to admit a failure.

## 5. Candidate families and outcomes

The matrix has **64 entries**, representing **62 distinct source/Pout/eta
combinations**: 30 accepted M20 anchors, two unresolved 8 MPa challenges, ten
pressure/efficiency interior and off-grid variations, twelve source variations,
six identity/small-work controls and four deliberately invalid cases. Identity
and 10 kPa controls repeat two anchor combinations. There are **24 independently
checked separator recipes**, including the two recipes with absent liquid.

| Source family | Deliberate investigation | Interpretation |
| --- | --- | --- |
| Low-pressure specified-T VL | 345/350/355 K at 0.3 MPa; 348.3 K at 0.337 MPa; feed z=0.45 versus 0.5 | 355 K has no liquid. At fixed 350 K/0.3 MPa, changing overall feed z changes the split but preserves tie-line liquid composition. No rectangular source envelope. |
| Adiabatic PH | Established 30 MPa/300 K→1 MPa recipe; separately 28 MPa Pin, 303.7 K Tin, 1.173 MPa separator P, feed z=0.47 | Outlet temperature/composition are solved, not independently configurable pump inputs. Independent source energy qualification is mandatory. |
| Cold 6 MPa | Actual below/above-bubble sources, plus -0.1/+0.1 K source perturbations | Compressed and saturated sources need different local evidence. 8 MPa endpoints are thermodynamically supported locally, but default PS fails. |
| Warm near-dew 6 MPa | 468.2158895316327 K anchor and 468.11588953163266 K holdout | Small actual liquid flows are retained, approximately 0.1333 and 0.3985 mol/s. Do not substitute total separator-feed flow or assume cooling proves a margin. |
| Flow and pump specification | Existing 5/17.3/200 mol/s liquid anchors; 137 mol/s PH source-feed holdout; pressure rises 173456/500000/731000 Pa; eta 0.7/0.873/0.83 | Intensive-state and extensive-flow checks are separate; source-feed scaling is an actual new recipe. |

Actual nonzero liquid methane fractions span approximately 0.00471227–0.5 across
these finite entries, not a proposed composition interval. Source temperatures
span approximately 230.9676–468.2159 K and source pressures 0.1–6 MPa; their extrema
must not be combined into an envelope. No independent liquid composition knob is
introduced downstream of the separator.

Results:

- **55 accepted numerical entries**, comprising the 30 anchors, 23 additional
  distinct exact candidates and two repeated controls. These pass independent
  source/path comparisons and the unchanged actual M20 source/pump callable guards.
- **Seven rejected entries:** absent liquid at the 355 K perturbation and the
  original vapor control; eta=0.599 and 1.001; pressure decrease; 10 and 100 Pa rises.
  For the last two the actual callable first reports `boundary_unresolved`, and
  the separate raw thermodynamic paths also fail the predeclared work-resolution
  screen (E/Δh≈0.00847 and 0.000847). They are excluded for unresolved numerical
  service, not asserted physically impossible.
- **Two unresolved production entries:** the actual 8 MPa challenges above. Their
  independent and prototype successes do not change this disposition.
- The application admits 32 entries because two are repeated anchor controls;
  these represent exactly the existing **30 distinct production combinations**.
  Every genuinely new combination remains rejected by the production scope guard.
- The 999 and 1001 Pa PH cases pass their tested numerical/local guards, with
  E/Δh≈8.480e-5 and 8.463e-5. This neither defines a universal minimum ΔP nor expands
  the M20 single 1000 Pa exception or the M18/M19 general floor.

Comparison counts are distinct from candidates:

| Evidence | Applicable checks | Numerical scalar checks | Failed checks |
| --- | ---: | ---: | ---: |
| Sources and primary paths | 5138 (1017 source + 4121 path) | 3997 | 0 |
| 115 independent lower-pressure witness states | 2001 | 1495 | 0 |
| Two local prototype paths | 130 | 94 | 0 |
| 200/400-iteration sensitivity scans | 256 joint entropy/phase records | 256 entropy comparisons | 0 |

There are **7525 applicable comparison records**, including **5842 numerical
scalar comparisons** under the table's counting convention. The remaining primary,
witness and prototype records are categorical/guard checks; iteration records
also include phase equality. This is not 7525 distinct candidates. Separately,
**27 provenance/enthalpy contradiction scenarios** reject in their expected
categories, including coherent forged upstream enthalpy, stale identity, wrong
port/basis, missing H and independent-feed relabelling.

Of the 115 independent lower-pressure witnesses, 92 are single liquid and 23 VL.
The latter are expected at saturated/very-small-rise states; no witness failure is
changed into a liquid result. Saturated-source admission uses independently
corroborated parent coexistence, not that failed compressed-state screen.

## 6. Isolated prototypes and proposed solver work

`prototype.py` samples the whole standard domain, retains failed points, constructs
brackets only between adjacent successful samples, and refuses competing observed
candidates. It bisects the sole observed bracket, fails on any encountered root
hole, and performs fresh final PT/caloric evaluation. PS width is 1e-10 K; PH width
is 1e-12 K; residual tolerances remain unchanged. Final ideal/actual states undergo
fresh default-production PT/stability and compressed-liquid witnesses. Neither
reference temperatures nor independent PS enthalpy drive this prototype.

Both challenges yield local liquid path candidates agreeing with the independent
reference. Their default-PT PS and PH scans remain **incomplete**. The result is
explicitly a local candidate, not global uniqueness or production acceptance.
`integration_checks.json` separately verifies each captured inlet contract and
prototype energy closure using the **retained original upstream Hdot**, separator
heat duty and actual vapor outlet. Hdot is not stripped or replaced.

A second, targeted diagnostic was declared after observing iteration exhaustion:
public immutable PT settings with 200 and 400 equilibrium iterations, all tolerances
unchanged. Both complete 64-point PS scans have no sampled holes and recover the
same local liquid roots; the largest observed equilibrium count is **152**. Fresh
final checks still use the default production PT/phase guards. This establishes
iteration-budget sensitivity for these samples, not an authorized changed default,
a universal convergence bound, or repaired coverage at every possible input.

A separately authorized implementation should first choose and qualify one policy:
retain conservative complete-scan PS semantics with a justified PT iteration budget,
or introduce a declared connected-interval PS policy with explicit incomplete-domain
and competing-root handling. The first option has direct supporting evidence here
and avoids needing to infer relevance of unknown intervals. Neither option is
implemented. Simply skipping failed samples, narrowing bounds around an oracle
answer or changing tolerances is not an acceptable correction.

Affected regressions include PT convergence/stability/restart branches and failure
budgets; PS/PH complete diagnostics, controlled holes inside/outside brackets,
ambiguity and discontinuities; fresh-final residual and payload association; and
M11–M20 callers (heater, compressor, exchanger, valve, separator and all pump
versions). `pump_energy.inverse` also verifies exact settings and requires no PS
failures: a benchmark PT-budget override alone does not satisfy that production
contract. Frozen reference artifacts and old model semantics must remain preserved.
No universal iteration cap or relaxed guard is qualified by four successful scans.

## 7. Guards required for any future configurable proposal

1. Resolve the source through the validated current graph and private completed
   execution registry. Validate current run/input/requirements and producer/port;
   editable stream provenance is corroboration, never authority. Preserve atomic
   failure and invalidation of downstream results after source edits.
2. Keep authoritative component rates, units, actual liquid flow/composition and
   upstream Hdot. Independently verify F·h against retained Hdot, source phase and
   fresh calorics; preserve incompatible/missing/stale-evidence diagnostics.
3. Separate source recipes/modes from pump-path inputs. A successful isolated pump
   state is not an independent source qualification. Absent liquid remains absent.
4. Require stable converged liquid PT, beta exactly zero, appropriate PIP, finite
   valid phase/caloric payload and association at inlet/ideal/actual endpoints.
   A `single_liquid` label by itself is insufficient.
5. For saturated source liquid, reproduce the same-T/P parent VL equilibrium,
   positive phase inventories, common-tangent stability, nontrivial composition/Z
   gaps and fugacity equality ≤2e-10. For compressed states, retain fresh same-T/z
   liquid evidence at 0.9999P. Failure means unresolved or rejected service; do not
   clip beta, force roots, snap coordinates or manufacture subcooling.
6. Require exact inverse specification/control association, declared scan policy,
   one observed candidate, fresh final state and PS/PH residuals ≤1e-8/1e-6. Preserve
   failure intervals and distinguish missing coverage from established ambiguity.
7. Preserve component/total mass, separator and pump energy closure, integrated
   vapor+liquid+heat+fluid-work closure against original upstream Hdot, positive
   ideal/actual work for ΔP>0, efficiency reconstruction and entropy checks.
8. Retain the propagated small-work screen, not merely positive work. Equal pressure
   must preserve the entire received material stream, zero work, null reconstructed
   efficiency and no inverse solves. Check finite values before publication.

Endpoint checks, lower-pressure witnesses and five sampled intermediate pressures
are different levels of evidence. None proves every intermediate state, a complete
phase envelope, or convergence for every continuous input. The numerical guards
make no claim about suction losses, NPSH margin, cavitation, hydraulic sizing or
electrical power.

## 8. Recommended separately authorized M21 scope

Do not replace the M20 exact list with a box assembled from sampled extrema.
Decision D applies to extending into the investigated 8 MPa region. The evidence
supports a focused solver qualification first, while additional exact candidates
could be considered separately using existing routines and unchanged guards.

A later configurable proposal should name separate low-pressure PT, adiabatic PH,
cold compressed/saturated and warm near-dew source families; qualify their boundary
and exclusion rules; then qualify pressure/efficiency/flow behavior and integrated
provenance independently. This study supplies holdouts and counterexamples, but
not sufficient source-boundary/critical/topology coverage to designate a continuous
runtime envelope. No new schema, UI acceptance, production solver or adapter is
implemented or authorized by this report.

## 9. Executed verification and reproduction

All 24 captured source executions reproduce their numerical streams/equipment,
units, status and semantic input/requirements hashes; fresh UUIDs are intentionally
not substituted into the capture. Independent reference, witness reference,
primary production/ledger, witness comparison, iteration sensitivity and upstream
integration artifacts reproduce **byte-for-byte in fresh processes**. Primary
production results also retain deterministic ordering with four isolated workers.
This is separate from the read-only comparison/unit assertions.

**13 new study tests pass**, including competing roots, unbridgeable scan holes,
root-time failures, discontinuities, nonfinite inputs, incomplete-domain labels,
source/phase checks, scope preservation, identity/conservation and prototype
upstream energy. Six of these are synthetic prototype-policy tests, not physical
fluid cases. The existing M20 integration suite was also executed: **11 tests,
ten passing and one failing**. The failure is solely its historical
`test_preservation [next-env.d.ts]` assertion against the older hash
`1f2e4a6d7f55de2de72375901050f2af22ed89992a781fce74d6e6a4d3fc94f0`.
The current file instead matches the explicitly preserved study-start hash
`0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc`.
Neither the file nor that historical test/baseline was changed to make the suite
pass. This is a recorded nonzero test command, not an all-green regression claim.

Before final evidence freeze, the new harness integrated-energy roundoff term was
aligned with the existing M20 formula, and its prototype PH bracket-width stop
was tightened to production's 1e-12 K. Final artifacts were freshly recalculated
and independently reproduced; candidate dispositions did not change. No benchmark
answer replaced a calculation and no historical artifact was regenerated.

Python AST parsing, strict JSON parsing, study whitespace checks, `git diff --check`,
source/evidence hash preservation and actual byte comparisons of both configuration
copies pass. The study changes and appended context were reviewed. All 488 original
tracked paths retain their captured bytes, except the authorized master-context
append whose complete prior prefix remains unchanged. HEAD/local main/origin-main
remain at the baseline, and the index remains empty. No full application suite,
browser, build, deployment or service operations were performed. Historical
verification counts and exclusions in M19/M20 remain historical.

Exact read-only reproduction commands, from repository root:

```sh
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/capture_sources.py
.local/pre-m8-venv/bin/python -B benchmarks/configurable_separator_pump/reference.py
.local/pre-m8-venv/bin/python -B benchmarks/configurable_separator_pump/phase_reference.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/compare.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/phase_compare.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/iteration_diagnostic.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/integration_checks.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/configurable_separator_pump -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/verify.py
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_separator_pump_integration -v
git diff --check
git status --short
git diff --cached --stat
```

The inherited integration command intentionally retains the historical hash
failure described above. `verification.txt` records executed test outputs and
reproduction hashes. `manifest.json` binds the report and all extension files;
`verify.py` defaults to read-only validation. Initial creation flags and dependency
pins are documented in the benchmark README; write flags refuse overwrite. The
baseline verifier is specific to this checkout state and must not be rewritten to
conceal later differences.

## 10. Exact delivered inventory and final status

Two documentation paths:

- `PRE_MILESTONE_21_CONFIGURABLE_SEPARATOR_PUMP_QUALIFICATION.md` (new report).
- `docs/RIOGINEER_MASTER_CONTEXT.md` (27 appended lines; old prefix preserved).

New benchmark directory, 24 files:

```text
benchmarks/configurable_separator_pump/PLAN.md
benchmarks/configurable_separator_pump/README.md
benchmarks/configurable_separator_pump/baseline.json
benchmarks/configurable_separator_pump/candidate_ledger.json
benchmarks/configurable_separator_pump/capture_sources.py
benchmarks/configurable_separator_pump/common.py
benchmarks/configurable_separator_pump/compare.py
benchmarks/configurable_separator_pump/integration_checks.json
benchmarks/configurable_separator_pump/integration_checks.py
benchmarks/configurable_separator_pump/iteration_diagnostic.json
benchmarks/configurable_separator_pump/iteration_diagnostic.py
benchmarks/configurable_separator_pump/manifest.json
benchmarks/configurable_separator_pump/phase_compare.py
benchmarks/configurable_separator_pump/phase_comparison.json
benchmarks/configurable_separator_pump/phase_reference.json
benchmarks/configurable_separator_pump/phase_reference.py
benchmarks/configurable_separator_pump/production.json
benchmarks/configurable_separator_pump/prototype.py
benchmarks/configurable_separator_pump/reference.json
benchmarks/configurable_separator_pump/reference.py
benchmarks/configurable_separator_pump/sources.json
benchmarks/configurable_separator_pump/test_study.py
benchmarks/configurable_separator_pump/verification.txt
benchmarks/configurable_separator_pump/verify.py
```

Final exact `git status --short`:

```text
 M docs/RIOGINEER_MASTER_CONTEXT.md
 M next-env.d.ts
 M tsconfig.json
?? PRE_MILESTONE_21_CONFIGURABLE_SEPARATOR_PUMP_QUALIFICATION.md
?? benchmarks/configurable_separator_pump/
```

The two configuration modifications predate the study and remain byte-identical.
No production/frozen historical evidence changes, staging, commit, push, deployment
or service changes. **M21 remains unimplemented.**

Minimum uploads for the next design discussion: this report and
`benchmarks/configurable_separator_pump/candidate_ledger.json`. Add `sources.json`
and `iteration_diagnostic.json` for source-recipe/solver-detail review; use the
complete benchmark directory plus the baseline repository for reproducibility.
