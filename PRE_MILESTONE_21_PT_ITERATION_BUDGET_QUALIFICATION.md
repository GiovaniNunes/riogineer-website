# PRE-M21 — Extended PT iteration-budget qualification

## Decision

**A. `pr_high_accuracy_pt200@1` is qualified for the stated finite matrix and ready
for separately authorized implementation as an explicit opt-in numerical profile.**
Keep legacy defaults at 100. There is no 400-iteration fallback. This is numerical
qualification, not production equipment support or a continuous operating envelope.

Both actual 8 MPa separator-to-pump challenges complete the full isolated PS→PH
chain with 200 and 400. Both remain rejected by production M20 application scope.
All original 30 M20 combinations remain admitted. No production code, contracts,
requirements, frozen references, completed prerequisite study, or services changed.

The larger full-chain study reaches **199 equilibrium iterations**, at a PH scan
sample of 469.29133858267716 K and 8 MPa for both cold source compositions. Thus
200 has only **one iteration of observed headroom**. The preceding 152 maximum
was a smaller PS-focused diagnostic, not a bound. Arbitrary nearby inputs require
further qualification; this recommendation does not promise convergence there.

## Baseline and preservation

Branch `main`, HEAD `b256ee38e1dedc62872e18b5fc8832bf12bc5a2c`, empty index.
Task-start status contained the modified master context, modified `next-env.d.ts`
and `tsconfig.json`, and the untracked preceding report and study directory.
`baseline.json` freezes 513 existing paths, including that whole study and its
manifest. Its master prefix is 95,334 bytes. This task only appends to that prefix.

Current and task-start SHA-256 values:

| File | SHA-256 |
|---|---|
| next-env.d.ts | `0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc` |
| tsconfig.json | `e2a28ab5d02bb5b555a28523be8786d9dc3a400fe125f14602261e24a6288126` |
| Preceding study manifest | `b191affcd3540a74562449ade2877560fd503f62dea5297dae98439506b9de49` |

Both configuration files remain byte-identical. The new preservation verifier
checks all baseline files, master prefix, branch, HEAD and index; its manifest
also hashes this extension, report and exact new master appendix. The preceding
study's own read-only verifier remains valid. No staging, commit, push or deployment.

## Policy and isolated integration

| Control | Legacy | Candidate | Comparator |
|---|---|---|---|
| Numerical profile | pr_high_accuracy_pt100@1 | **pr_high_accuracy_pt200@1** | pr_high_accuracy_pt400@1 |
| PT equilibrium cap | 100 | **200** | 400 |
| Stability cap | 100 | 100 | 100 |
| Rachford–Rice cap | 200 | 200 | 200 |
| Fugacity tolerance | 1e-12 | 1e-12 | 1e-12 |
| Material tolerance | 1e-10 | 1e-10 | 1e-10 |
| Underlying settings profile | high_accuracy | high_accuracy | high_accuracy |
| Fallback | none | none | none |

All EOS, stability and caloric algorithms/data are unchanged. PS retains the
complete 64-point 200–500 K scan, rejection on any failed sample, one unambiguous
root bracket, 100 root iterations, 1e-10 K final width and 1e-8 J/(mol K) residual.
PH retains its complete 128-point scan, M16 connected-interval policy, existing
ambiguity rules, 100 root iterations, 1e-12 K width and 1e-6 J/mol residual.
Existing PH off-bracket PT failures remain governed by that original policy;
this study does not introduce interval bridging or permit PS holes.

PT already exposes immutable settings. PS, PH and `pump_energy.inverse` instead
hard-code `SolverSettings.high_accuracy()`. Merely passing 200 to standalone PT
cannot qualify their contracts. `profile.py` derives private functions from the
actual production AST, checks source hashes, adds one required keyword argument,
and replaces exactly one settings construction per function. The normalized AST
diffs and hashes are frozen in `production.json`. Their original algorithm/control
flow remains intact. Functions compile in separate namespaces; no production
function, module, default or result provenance is monkey-patched or rewritten.
This experiment is not a recommendation to deploy AST transformation.

The isolated guard expects the selected profile exactly and retains original
scan, candidate, failure, residual and payload checks. Additional assertions verify
final PT settings, pressure and composition association. A candidate result passes
its candidate guard and is deliberately rejected by the unchanged legacy guard.
It does not gain acceptance by pretending its nested PT used 100 iterations.

## Predeclared finite matrix

`PLAN.md` and `common.py` define 70 physical PT inputs, each run under all three
profiles: 48 points combine both actual liquid compositions with 7, 7.5, 7.8 and
8 MPa, the two known failed temperatures (461.9047619047619 and 466.6666666666667 K),
and offsets −0.05, 0 and +0.05 K. Six separately chosen off-grid holdouts vary T,
P and composition. Sixteen additional inputs cover liquid/vapor/VL, bubble/dew,
actual source boundaries and vapor-parent restart controls. All use methane/n-hexane,
explicit zero kij and existing property data. The extrema do not define an envelope.

Six independent forward-defined PS/PH inverse anchors cover liquid, VL and vapor.
Twelve chains per profile cover both cold sources at the four stated discharges,
PH_FLASH, PT_VL_HEATING, PT_DEW_BELOW and the cold identity case. Total: 264 profile
runs (210 PT, 18 inverse, 36 chains), plus separate source and synthetic-policy checks.
Synthetic nonconvergence, ambiguity, nonfinite data and residual failures are not
counted as physical-fluid qualification points.

## Independent numerical evidence

The independent reference reuses the established Thermo 0.6.0 infrastructure,
canonical PR coefficients 0.45724/0.07780, Soave alpha, quadratic a/linear b mixing,
explicit zero kij and Poling ideal-gas heat capacities. H/S reference convention,
mixing entropy, component/data hashes and library source hashes are retained.
Reference generation asserts that no production engine module was imported.
Agreement is with the same physical model, not experimental validation.

Predeclared absolute/relative tolerances: T 1e-7 K; phase fractions and composition
2e-9; Z 2e-10 + 1e-9|Z|; H 1e-6 + 1e-11|H| J/mol; S 1e-8 + 1e-11|S| J/(mol K).
Phase ln(phi) comparison is 2e-9; independent fugacity equality is 1e-9, while
production acceptance still requires 1e-12. Initial/final stability and restart
records are retained; independent and production algorithm iteration counts are
not presumed comparable. The inherited work uncertainty ratio limit remains 1e-4,
including the 500 K PS-residual propagation bound.

### Reference phase identity: retained initial failure and resolution

The original named-reference comparison produced **195 failed checks** and the
initial 13-test study run had one failure. These outcomes remain in the original
`production.json`, `candidate_ledger.json` and test log. They were not overwritten,
suppressed or resolved by changing numerical tolerances.

Six PT inputs returned exchanged liquid/vapor names from the independent flash:
five cold-source 8 MPa points around the first historical temperature and HOLDOUT_0.
The unordered phase properties and aggregate H/S agreed, while the named phase
records and beta were complementary. A supplementary, explicitly documented audit
uses independent PIP, molar volume, mass density and fresh phase-root reproduction.
It requires unique PIP classifications, smaller liquid volume, larger liquid density,
and nontrivial Z/composition gaps before mapping whole phase records and fractions.
No production phase label or numerical value drives that mapping.

For example at 461.9047619047619 K, 8 MPa, z(CH4)=0.5, the reference's named liquid
has Z=0.695293865723343 and PIP=0.6721634497715105 (vapor-like); its named vapor has
Z=0.40697276721224523 and PIP=4.030940461389737 (liquid-like). Independent volumes
are 0.00033378363151978296 and 0.0001953718490360009 m³/mol, with densities about
138.68 and 327.37 kg/m³. Mapping the entire phase records and their fractions
resolves the discrepancy without modifying their properties. Fugacity-residual
orientation follows the same phase exchange. All 70 independent identities are
verified, exactly six are exchanged, and ambiguous mapping would remain a failure.

`phase_identity_reference.json` and `phase_identity_comparison.json` preserve this
separate evidence. The final `qualified_ledger.json` contains **7,895 checks,
5,857 scalar comparisons and zero unresolved comparison failures**; it also records
the 195 raw named-reference failures. Every count is reproducible from frozen data.

| Profile cap | Qualified PT | Qualified inverse anchors | Completed prototype chains |
|---|---:|---:|---:|
| 100 | 41/70 | 6/6 | 6/12 |
| 200 | 70/70 | 6/6 | 12/12 |
| 400 | 70/70 | 6/6 | 12/12 |

The 29 legacy PT failures are controlled `flash_not_converged` results, without
accepted phase/caloric payload. Six legacy chains stop at PS (both cold sources
at 7.5, 7.8 and 8 MPa). Initial stability convergence does not establish final
fugacity equilibrium. The two original 8 MPa holes and their failure mechanism
are reproduced; 200/400 recover them without skipping scan points.

All 41 PT inputs already successful at 100 have identical numerical payloads,
diagnostics and executed equilibrium-iteration sequences at both larger budgets:
82 exact comparisons after excluding only the declared cap from result hashing.
All 70 PT cases also match exactly between 200 and 400. Passive tracing records
K, beta, fugacity/material residuals, RR work and restart state without mutation.
All six isolated legacy inverse anchors exactly equal their public production
counterparts. This does not assert identical entire inverse diagnostics for every
legacy-successful chain: at 7 MPa a legacy PH off-bracket hole is recovered by the
larger budget, legitimately changing its scan-failure diagnostics.

## Actual source-to-pump chains

Five fresh M17 source results were captured. The prototype registers each actual
result in a private execution context and resolves its real liquid connection
through existing source-resolution rules. The original admitted M20 graph supplies
the resolution context; the studied discharge is used only in the isolated chain.
No application admission rule is widened. Source UUIDs, specification hashes,
actual liquid component rates and authoritative upstream Hdot are retained.

The sequence is candidate inlet PT, PS at inlet entropy/discharge P, isentropic H,
efficiency-derived actual H target, PH, fresh candidate endpoints/local witnesses,
phase/work guards, mass and integrated energy balances. No reference endpoint or
root is injected. Separate forward-defined inverse anchors are explicitly diagnostic
anchors, not replacements for the pump's PS prerequisite. Identity preserves its
stream; positive-rise output does not falsely retain upstream producer context.

| Actual source, 8 MPa | Cap 100 | Cap 200 and 400 | Isentropic T (K) | Actual T (K) | Fluid power (W) | Production |
|---|---|---|---:|---:|---:|---|
| PT_BUBBLE_BELOW | fails PS | full chain passes | 231.62864734074992 | 232.0029774476092 | 20567.978871054584 | excluded |
| PT_BUBBLE_ABOVE | fails PS | full chain passes | 231.7288906905257 | 232.1032000731769 | 20564.527568835445 | excluded |

Both endpoints remain single liquid. Efficiency reconstructs to 0.8 within the
inherited tolerance. For the above-bubble challenge, reconstructed efficiency is
0.7999999999998656; pump energy residual is −1.4551915228366852e-10 W and integrated
residual 1.1510792319313623e-11 W, against allowances 0.00012540222005517012 and
0.00022547438420692683 W. Full states, residuals and budgets for both challenges
are in `summary.json` and `production.json`, including independent comparisons.

Every nonidentity successful chain has all 64 PS and 128 PH scan points, one
selected root candidate per solve, original refinement controls and fresh final
validation. Candidate inlet/endpoints and lower-pressure witnesses explicitly use
the selected settings. Legacy source verification, existing `local` checks and
separate fresh legacy endpoint probes are recorded as legacy100, not relabeled.
Those endpoint probes pass: the slow two-phase scan region is distant from the
liquid roots. An unchanged exact-settings inverse guard still rejects a candidate
inverse result, even when a separate legacy endpoint PT converges.

## Cost and bounded failures

Deterministic work is primary; wall time is supplementary. Across all 12 chains:

| Cap | PS/PH PT evaluations | Summed equilibrium iterations | Failed PT calls | Peak per-call iterations |
|---|---:|---:|---:|---:|
| 100 | 1,744 | 17,325 | 10 | 100 |
| 200 | 2,992 | 35,955 | 0 | 199 |
| 400 | 2,992 | 35,955 | 0 | 199 |

These totals cover inverse evaluator calls; timing additionally includes source
context, inlet, fresh endpoint/local and balance guards. They are not equal-work
speed comparisons: six legacy chains stop before PH. Each successful nonidentity
chain has 272 inverse PT calls; the identity has zero. The standalone 70-state PT
matrix peaks at 171 iterations (an off-grid holdout), while the full-chain peak is
199. Stability/RR limits and per-call counters remain independently recorded.

Serial timing used no tracing, one warmup and three repetitions per case/profile,
rotated profile order and `perf_counter`. Each repeat asserted identical numerical
result hashes and work counts. All raw samples, medians and host/Python/timer
metadata are in `performance.json`. Existing services were left running; ordinary
host scheduling variation is possible. Selected median seconds:

| Case | 100 | 200 | 400 | Deterministic interpretation |
|---|---:|---:|---:|---|
| Normal liquid PT | 0.010152 | 0.010251 | 0.010135 | 0 equilibrium iterations; stability still runs |
| Normal VL PT | 0.024920 | 0.024803 | 0.024918 | 7 iterations for all |
| Historical 461.9048 K PT | 0.023374 | 0.036117 | 0.035692 | fails at 100; converges at 109 |
| Historical 466.6667 K PT | 0.023140 | 0.040591 | 0.040530 | fails at 100; converges at 152 |
| HOLDOUT_2 PT | 0.022928 | 0.043138 | 0.042910 | fails at 100; converges at 171 |
| PH_FLASH full chain | 3.747262 | 3.748330 | 3.741089 | 272 PT calls / 654 equilibrium iterations for all |
| Above-bubble 8 MPa chain | 1.473514 | 5.297254 | 5.329177 | 64/1462 legacy failure vs 272/4736 completed chain |

Normal-case actual work does not increase merely because the cap rises. 400 doubles
the permitted equilibrium-loop work relative to 200 but executes the same work in
this matrix and adds no recovered physical cases. This is the basis for preferring
200, not a claim that 400 is always equally cheap or that 200 has robust headroom.

The natural 100-iteration failures stop exactly at their cap and publish no accepted
payload. A real cap=1 VL control also fails at exactly one iteration with no payload.
Invalid pressure remains `invalid_input` for all three profiles (about 35 microseconds;
zero PT equilibrium evaluations). Synthetic tests enforce failed-sample rejection,
ambiguous roots, nonfinite targets/properties, discontinuities/fresh residual failures,
wrong settings, phase rejection and payload association. No profile retries at 400.
There is no naturally nonconvergent 200/400 physical case in this finite matrix;
the study does not invent one or infer a universal bound from their absence.

## Compatibility and separately authorized implementation

Implement an additive immutable opt-in profile; do not change the shared
`high_accuracy()` default or silently switch existing equipment. The explicit
profile name identifies numerical policy, while full settings still truthfully
record `high_accuracy` with cap=200. Retain legacy100 when selection is omitted.
Do not copy the EOS, stability or inverse solver to create the profile.

Potential production integration points, not edits made here:

1. Add a keyword-only nested PT settings/profile parameter to provider `flash_PS`
   and `flash_PH` in `property_packages.py`, including the provider protocol, and
   thread it through `pr_ps_flash.flash_ps` and `pr_ph_flash.flash_ph`. The same
   selected controls must reach every scan/refinement/final PT call and its exact
   provenance check. Default behavior must remain byte/numerically compatible.
2. Add an explicitly expected profile to `pump_energy.inverse`; retain all existing
   inverse controls and require final PT provenance/pressure/composition association.
   Never replace exact matching with accepting arbitrary larger iteration caps.
3. Only a separately authorized equipment caller may select the new profile for
   its PS, actual PH and candidate fresh checks. Existing `pump_energy._pump` and
   separator-pump callers must retain their historical selection by default.
   Source verification and endpoint witnesses need explicit documented selection;
   the experiment's recorded legacy witnesses must not be silently relabeled.
4. Record the versioned numerical profile identifier, full nested PT settings,
   inverse controls, actual cap/iterations, complete-scan coverage, failed trials,
   root candidates, residuals and final-validation profile. Physical property-package
   identity remains `peng_robinson@1.0`; a budget change is not new physical data.

An internal additive solver API alone does not require public requirements/schema
or physical package version changes. Current M20 thermodynamic diagnostics already
permit structured diagnostic fields, but top-level thermodynamics is closed to
undeclared keys. Put future numerical provenance in the supported diagnostics or
make an explicit versioned contract change if a new public field is desired.
A future user-selectable policy/new equipment model or broader admission requires
its own contract/model-version and qualification review. No M17–M20 historical
model behavior or the existing 30-case admission set may change implicitly.

Required implementation regressions: unchanged omitted-profile legacy behavior;
all PT/PS/PH callers and provider signatures; exact nested/final settings and
wrong-profile association rejection; full scans/ambiguity/nonfinite/residual and
bounded exhaustion controls; the full finite physical matrix and both actual pump
chains; authoritative source Hdot/rates and integrated balances; explicit admission
and historical model-version tests. Retain the independent phase-identity audit.
Additional nearby cases are needed before any expansion beyond this finite scope.

## Historical configuration assertion

The complete existing regression command was run without excluding preservation:
**274 tests, 273 passed, one failure** in M20 `test_preservation`, for `next-env.d.ts`.
The historical expected hash is
`1f2e4a6d7f55de2de72375901050f2af22ed89992a781fce74d6e6a4d3fc94f0`;
current bytes hash to `0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc`,
matching both prerequisite-study start and this task start. This is not a solver
regression or a current-task configuration change. The assertion remains a failure.

Current `next-env.d.ts` imports `.next/dev/types/routes.d.ts` and
`.next/dev/types/root-params.d.ts`; the HEAD version imports `.next/types/...`.
HEAD's file hash is `1862ac4bbbc5192d4bf562161df66ea547ed3e67173100656ab606ae9797db2b`,
also different from the historical assertion. Therefore checking out HEAD is not
an evidence-based reconstruction of that historical snapshot. No configuration,
frozen baseline, test assertion or previous manifest was modified to pass it.

For a later authorized maintenance change, separate (a) verification of immutable
historical artifacts against their actual archived snapshot, (b) session preservation
against captured current bytes, and (c) numerical/production-source regression checks.
If historical config bytes were not archived, report that missing evidence rather
than inventing it from HEAD. Retain commit and production-source hashes; do not
blanket-exclude config/source files or replace historical expected hashes with current
values merely to get green results. This study performs (b), preserves (a)'s failure,
and reports numerical checks independently.

## Verification and reproducibility

Commands and exact artifact roles are in `benchmarks/pt_iteration_budget/README.md`.
The final new suite passes **14 tests**. The initial 13-test run failed on the 195
raw comparisons; the subsequent independent phase audit and additional preservation
assertions account for the final result. A separate nine-policy-test run passed.
Logs retain the initial failure, final result and the existing regression failure.
A timing-helper scaffold initially assumed invalid input always had equilibrium
diagnostics; it was corrected to record the controlled no-equilibrium result before
any timing artifact was frozen. No production change or acceptance relaxation resulted.

Fresh-process read-only reproduction checked source numerical results, independent
reference bytes, production/ledger bytes, supplemental phase-identity evidence and
qualified ledger. Timing verification separately replays deterministic counts and
result hashes; it does not pretend elapsed seconds are byte-reproducible. Summary
and preservation checks are also read-only. No unrelated frontend/browser/build
suite was run for this study-only extension.

## Deliverable inventory and working tree

New root file: `PRE_MILESTONE_21_PT_ITERATION_BUDGET_QUALIFICATION.md`.
Only existing file intentionally changed by this task: appended status in
`docs/RIOGINEER_MASTER_CONTEXT.md`.

New directory `benchmarks/pt_iteration_budget/` contains:
`PLAN.md`, `README.md`, `baseline.json`, `common.py`, `profile.py`,
`capture_sources.py`, `sources.json`, `reference.py`, `reference.json`,
`harness.py`, `compare.py`, `production.json`, `candidate_ledger.json`,
`phase_identity_reference.py`, `phase_identity_reference.json`,
`phase_identity_compare.py`, `phase_identity_comparison.json`, `qualified_ledger.json`,
`test_budget.py`, `performance.py`, `performance.json`, `summarize.py`, `summary.json`,
`verify.py`, `manifest.json`; and logs `regressions.log`, `study-tests.log`,
`policy-tests.log`, `final-study-tests.log`, `production-reproduction.log`,
`reference-reproduction.log`, `performance.log`, `performance-reproduction.log`,
`final-verification.log` under `logs/`.

Final expected status (verified at completion):

```text
 M docs/RIOGINEER_MASTER_CONTEXT.md
 M next-env.d.ts
 M tsconfig.json
?? PRE_MILESTONE_21_CONFIGURABLE_SEPARATOR_PUMP_QUALIFICATION.md
?? PRE_MILESTONE_21_PT_ITERATION_BUDGET_QUALIFICATION.md
?? benchmarks/configurable_separator_pump/
?? benchmarks/pt_iteration_budget/
```

The two config modifications and prerequisite study entries predate this task.
Index and HEAD remain unchanged. For implementation planning upload this report,
`summary.json`, `profile.py` and `PLAN.md`; provide the entire study directory and
repository/prerequisite references for a reproducible numerical review.

## Final conclusion

**A — qualify `pr_high_accuracy_pt200@1` only for the declared finite scope.**
Both formerly failing 8 MPa challenges pass the full candidate chain and both remain
excluded from production. Preserve legacy100 and all existing conservative policies.
The observed 199-iteration peak, retained raw reference failures and historical config
assertion limit the claims explicitly; none is hidden by changing defaults or evidence.
