# Milestone 10 — Production Peng–Robinson Caloric Properties

## Scope and architecture

M10 adds opt-in **property-layer** caloric evaluation to `peng_robinson@1.0`. It qualifies methane/n_hexane ideal Cp, ideal H/S, residual H/S, total phase H/S, mass-specific conversions and equilibrium phase-weighted aggregates against the unchanged independent pre-M10 reference. It does not integrate energy calculations into equipment or the website.

M7 remains authoritative for MW/Tc/Pc/omega through `riogineer_components@1.0`. A separate immutable offline `riogineer_caloric@1.0` dataset owns Cp coefficients, units, ranges and provenance. M8 remains authoritative for EOS, roots, stability and PT equilibrium. M9 still calls `flash_PT`, whose result fields, arithmetic and semantics are unchanged. No equipment, network, fixture or process contract is modified.

Production uses standard-library Python only for this capability. It imports no Thermo, teqp, benchmark Python, frozen JSON or benchmark virtual environment. The independent reference remains an acceptance oracle read only by tests and the comparison tool. No expected values were regenerated from production.

Files:

- `engine/riogineer_engine/caloric_data.py`: offline dataset, reference metadata and analytic component Cp/H/S integrals.
- `engine/riogineer_engine/pr_caloric.py`: caloric results, validation, phase evaluation, equilibrium aggregation and conversions.
- `engine/riogineer_engine/pr_eos.py`: additive read-only properties expose the existing analytic alpha derivative and explicitly constant BIP semantics; the prior EOS arithmetic is unchanged.
- `engine/riogineer_engine/property_packages.py`: capability-specific protocol and opt-in provider methods.
- `engine/riogineer_engine/CALORIC_DATA_NOTICE.txt`: retained attribution/license notice for the two Cp records.
- `engine/tests/test_pr_caloric.py`: production acceptance and failure regressions.
- `benchmarks/peng_robinson_caloric/compare_production.py`: production-environment comparison command.
- `benchmarks/peng_robinson_caloric/production_comparison.json`: generated comparison evidence, distinct from the untouched independent expected-value JSON.
- `MILESTONE_10.md`: implementation/qualification record.
- `docs/RIOGINEER_MASTER_CONTEXT.md`: minimal current-state/next-step update.

## Cp dataset, units and reference convention

Exact source: Poling, _The Properties of Gases and Liquids_, fifth edition; Chemicals 1.5.2 `PolingDatabank.tsv`. Table SHA-256: `9c707a81eb8896afc32cae53222b5596dabf98f318f6f26d97193016fe8f436b`. The coefficients are copied as data from the already-qualified independent record, with the published distribution's notice retained. See `PRE_MILESTONE_10_PR_CALORIC_BENCHMARK.md` for source assessment and redistribution boundaries. No runtime lookup or dependency on Chemicals is introduced.

Correlation: `Cp_ig/R = Σ(j=0..4) c_j T^j`, where R=8.31446261815324 J/(mol K), T is K, and coefficient units are respectively 1, K^-1, K^-2, K^-3, K^-4.

| Component | CAS      |    c0 |        c1 |         c2 |          c3 |        c4 | Cp range K |
| --------- | -------- | ----: | --------: | ---------: | ----------: | --------: | ---------- |
| methane   | 74-82-8  | 4.568 | -0.008975 |  3.631e-05 |  -3.407e-08 | 1.091e-11 | 50–1000    |
| n_hexane  | 110-54-3 | 8.831 | -0.000166 | 0.00014302 | -1.8314e-07 | 7.124e-11 | 200–1000   |

Component evaluation validates its own documented range; a declared binary validates both records, including zero-inventory components, giving a joint 200–1000 K domain. No clamping or extrapolation is allowed. Numerical phase qualification is the frozen 280/300/350/400 K matrix, not a blanket experimental validation across every temperature/pressure in the correlation domain. Missing records, malformed/nonfinite coefficients and nonfinite results fail explicitly.

Reference ID: `ideal_gas_sensible_298.15K_101325Pa@1.0`. Pure-component ideal-gas h=0 and s=0 at Tref=298.15 K and Pref=101325 Pa. No formation enthalpy or third-law absolute entropy is included. Result provenance carries the provider, molecular/caloric datasets, Cp source/hash, reference temperatures/pressure, both reference conventions and constant-BIP derivative convention.

Analytic integrals:

`h_i,ig = R Σ(j=0..4) c_ij (T^(j+1)−Tref^(j+1))/(j+1)`.

`s_i,ig,T = R [c_i0 ln(T/Tref) + Σ(j=1..4) c_ij (T^j−Tref^j)/j]`.

For phase molar composition q:

`Cp_ig = Σ q_i Cp_i,ig`; `h_ig = Σ q_i h_i,ig`.

`s_ig = Σ q_i s_i,ig,T − R ln(P/Pref) − R Σ q_i ln(q_i)`.

Ideal enthalpy has no pressure contribution. Entropy temperature, pressure and ideal mixing contributions are returned separately. Zero mole fractions use the continuous `q ln(q)=0` limit, never an arbitrary floor. Negative H/S are permitted under this reference convention and are not treated as calculation failure.

## EOS reuse and analytic departures

The caloric layer constructs the existing `PengRobinsonEOS` and consumes its `EOSState` and `PureParameters`. It does not duplicate alpha, a_i, b_i, mixture rules, A/B or cubic-root equations. The EOS already supplied analytic `da_i/dT` and `da_mix/dT` for M8 phase identification. The added `dalpha_dT` property uses `(da_i/dT)*alpha_i/a_i`, which is exactly the same analytic derivative since `a_i=a0_i*alpha_i`; no finite differences occur in production.

The existing analytic EOS equations are:

`kappa_i = 0.37464 + 1.54226 omega_i − 0.26992 omega_i²`;
`g_i = 1 + kappa_i (1−sqrt(T/Tc_i))`; `alpha_i = g_i²`;
`dalpha_i/dT = −kappa_i*g_i/sqrt(T*Tc_i)`.

`a0_i = 0.45724 R² Tc_i²/Pc_i`; `a_i = a0_i alpha_i`;
`da_i/dT = a0_i dalpha_i/dT`.

For temperature-independent BIPs:

`da_mix/dT = Σ_i Σ_j q_i q_j sqrt(a_i a_j) (1−kij)/2 * [(da_i/dT)/a_i + (da_j/dT)/a_j]`.

These equations are documented here for audit; production caloric code consumes the existing EOS implementation and does not reimplement them. A future temperature-dependent BIP would require the additional derivative contribution from dkij/dT and separate qualification.

Canonical coefficients remain 0.45724/0.07780 and the M8 Soave kappa polynomial remains unchanged. Only the existing numeric `BinaryInteractions` representation, explicitly identified as constant, is accepted by M10. The caloric qualification additionally requires all kij=0. New subclasses/temperature-dependent models and nonzero BIPs return `unsupported_bip`; future temperature-dependent BIPs require an explicit derivative implementation and qualification rather than inheriting an implicit zero derivative.

At each qualified phase root, define:

`L = ln[(Z+(1+sqrt(2))B)/(Z+(1−sqrt(2))B)]`.

`h_res = RT(Z−1) + (T da_mix/dT−a_mix) L/(2 sqrt(2) b_mix)`.

`s_res = R ln(Z−B) + (da_mix/dT) L/(2 sqrt(2) b_mix)`.

These residual properties are real minus ideal gas at the same T/P/composition. `log1p` evaluates the small logarithmic terms accurately in dilute states. Explicit checks validate b, B, Z−B, the PR logarithm denominator, both representable log1p arguments and all analytic derivatives; invalid domains fail without epsilon substitution. The root passed from PT must be exactly a member of the recomputed existing EOS state’s roots, so recalculation cannot silently switch branches. Total phase values are `h=h_ig+h_res` and `s=s_ig+s_res`; all decomposed terms are available for comparison. Returned diagnostics retain the EOS state, pure parameters, `T da/dT−a`, L and ln(Z−B).

## Provider API and identity

`peng_robinson@1.0` adds capabilities `phase_caloric_TP` and `equilibrium_caloric_PT` to its prior capabilities. `CaloricPropertyPackage` extends the capability-scoped protocol without changing process JSON contracts.

- `phase_caloric_TP(state, bip, *, phase=None, root=None, settings=SolverSettings())` performs qualified PT stability/equilibrium and requires a single stable phase. Optional phase/root values are consistency assertions, never root-selection shortcuts. Incorrect labels, metastable/arbitrary roots and two-phase states fail explicitly.
- `equilibrium_caloric_PT(state, bip, settings=SolverSettings())` performs the existing PT calculation and evaluates each resulting phase. Case B uses actual runtime x/Z_L and y/Z_V, not overall z for both phases.
- The existing `flash_PT` method does not call caloric code or add caloric fields to PT/process results.

A `CaloricResult` owns status, message, caloric provenance, the original `PTResult`, a tuple of `PhaseCaloricProperties` and an optional aggregate. Each caloric payload joins to the original phase by `phase_identifier`; it does not duplicate phase composition/identity structures. T/P are in `equilibrium.overall_state`; phase composition, Z and fraction remain in `equilibrium.phases`. A successful single phase has exactly one caloric payload, with no fabricated absent-phase H/S.

All input validation occurs before publication: T/P must be positive finite values, canonical component IDs unique, composition nonnegative and normalized under the existing 1e−12 roundoff rule, provider/BIP identities consistent, BIPs explicit, data present and in range. Water and unknown components are rejected even at zero fraction; unsupported species are never dropped. Cp and all arithmetic outputs must be finite. The state remains immutable.

On failure, `phases=()` and `aggregate=None`. Thermodynamic statuses such as `flash_not_converged` and `stability_not_converged` propagate with their PT diagnostics. Other statuses distinguish `invalid_input`, `unsupported_components`, `unsupported_bip`, `missing_caloric_data`, `invalid_caloric_data`, `caloric_out_of_range`, `phase_mismatch` and `numerical_domain_error`. A successful PT diagnostic retained inside a failed caloric result does not mean the caloric calculation succeeded; consumers must check the outer status.

## Aggregation and unit helpers

`h_eq = Σ phase_fraction*h_phase` and `s_eq = Σ phase_fraction*s_phase` use molar phase fractions from PT. No extra phase-mixing entropy is added: each phase already contains its own ideal compositional mixing entropy, and the phases are macroscopically separate. Two-phase results also expose h_V−h_L and s_V−s_L, described as mixture phase-property differences, not pure-component latent heats. Single-phase differences remain unavailable (`None`).

Mixture MW uses the existing M7 constants and the appropriate phase molar composition. `molar_to_mass(value, MW_kg_kmol)` explicitly divides MW by 1000 before dividing J/mol or J/(mol K), giving J/kg or J/(kg K). Aggregate mass-specific properties use feed MW, not an unweighted average of phase MWs.

`enthalpy_flow_W(mass_flow_kg_h, h_J_kg)` returns `mass_flow_kg_h/3600*h_J_kg`, validates its arguments/results and allows physically reference-dependent negative enthalpy. It is a property-layer helper only. No heat duty or work is inferred from an absolute enthalpy flow.

A common additive component enthalpy reference C cancels from phase H differences. Component-dependent offsets need not cancel from h_V−h_L when x differs from y, but cancel from component-balanced inlet/outlet enthalpy flows. Tests demonstrate both distinctions using the common declared reference. Standard formation terms are unnecessary for these nonreactive differences. Reaction thermodynamics remains outside scope.

## Numerical acceptance

Independent oracle: `pre_m10_methane_nhexane_pr_caloric@1.0`; frozen JSON SHA-256: `1743a177aa7057a66f5e3e6362e33451e4a002a171d46e91f4cd4260a2be0e6e`.

The read-only comparison passes **1526 comparisons**. It covers all 12 binary equilibrium states, all 40 individual phase records (including 12 pure-component and 12 dilute-gas records), and all 10 pure Cp/integral reference points. States span the frozen 280/300/350/400 K samples.

For caloric quantities, comparisons use the exact frozen `atol + rtol*|reference|` gates. Mass-specific absolute tolerances are converted by dividing the molar tolerance by frozen MW_kg/mol. MW uses 1e−10 kg/kmol absolute plus 1e−12 relative; equilibrium composition/fraction comparisons use the existing 1e−9 comparison scale. No independent reference or M8 tolerance was altered.

EOS intermediate/derivative comparisons use identical frozen phase composition inputs, as required to apply their tight same-state tolerances. Runtime flash phases are separately compared for phase composition, beta, Z, Cp and decomposed/total H/S. Tiny permitted flash composition differences must not be confused with EOS derivative errors at identical input. This separation retains all frozen caloric and derivative acceptance gates.

Primary frozen reference values below are shown with display rounding; tests use full JSON precision:

| State | phase  |      h_ig J/mol |      h_res J/mol |          h J/mol |   s_ig J/(mol K) |     s_res J/(mol K) |      s J/(mol K) |
| ----- | ------ | --------------: | ---------------: | ---------------: | ---------------: | ------------------: | ---------------: |
| A     | liquid | 165.75492421744 | -16469.702948889 | -16303.948024671 | -40.997070836573 |    -31.161730487162 | -72.158801323734 |
| B     | liquid | 262.14522290762 | -30837.964045623 | -30575.818822715 | -7.4794006804449 |     -81.97328966884 | -89.452690349285 |
| B     | vapor  | 81.855970094879 | -88.689888592917 | -6.8339184980385 | -6.4662293404348 |   -0.20000674413449 | -6.6662360845693 |
| C     | vapor  | 165.75492421744 | -1.3862804890528 |  164.36864372839 |  44.716330692666 | -0.0029304741236806 |  44.713400218542 |

Case B beta=0.5346425102237959; h_eq=-14232.3399985311 J/mol; s_eq=-45.1915326286698 J/(mol K); h_V−h_L=30568.9849042169 J/mol; s_V−s_L=82.7864542647153 J/(mol K). The 1000 kmol/h benchmark enthalpy-flow sum is -3953427.77736975 W under this reference, not an M9 duty.

Production-versus-frozen totals (full decomposition and mass-specific checks are in the comparison command/report):

| Case/phase |  h production J/mol |      h frozen J/mol | s production J/(mol K) |  s frozen J/(mol K) | Gate |
| ---------- | ------------------: | ------------------: | ---------------------: | ------------------: | ---- |
| A/liquid   | -16303.948024671077 | -16303.948024671074 |    -72.158801323734338 | -72.158801323734366 | PASS |
| B/liquid   | -30575.818822714948 | -30575.818822714955 |    -89.452690349284524 | -89.452690349284637 | PASS |
| B/vapor    |  -6.833918498044028 | -6.8339184980384893 |    -6.6662360845689106 | -6.6662360845693094 | PASS |
| C/vapor    |  164.36864372839059 |  164.36864372839091 |     44.713400218541949 |  44.713400218541921 | PASS |

| Case B aggregate           |          Production |              Frozen | Gate |
| -------------------------- | ------------------: | ------------------: | ---- |
| h_eq_J_mol                 | -14232.339998530839 | -14232.339998531099 | PASS |
| s_eq_J_mol_K               | -45.191532628668789 | -45.191532628669755 | PASS |
| phase_difference_h_J_mol   |  30568.984904216904 |  30568.984904216915 | PASS |
| phase_difference_s_J_mol_K |  82.786454264715616 |  82.786454264715331 | PASS |

Observed maximum errors (absolute errors use the quantity’s SI units; relative errors are dimensionless and exclude exactly zero reference values):

| Quantity     | Maximum absolute error | Maximum relative error |
| ------------ | ---------------------: | ---------------------: |
| Cp           |      1.32700961331e-10 |      1.85679052203e-12 |
| MW           |      6.63789023747e-11 |      2.10939976635e-12 |
| Z            |      4.48974191158e-13 |      4.95483782647e-13 |
| a            |       3.5527136788e-15 |       7.6818370515e-16 |
| alpha        |      6.66133814775e-16 |      5.14252232565e-16 |
| b            |      2.71050543121e-20 |      2.72457450008e-16 |
| composition  |      9.46687173098e-13 |      4.30343088181e-12 |
| da_dT        |      3.46944695195e-18 |      6.57672647484e-16 |
| dalpha_dT    |      8.67361737988e-19 |      4.40271806078e-16 |
| fraction     |      8.17790279939e-13 |      1.97446598334e-12 |
| h_ig         |       1.1933479982e-08 |      1.79398990949e-12 |
| h_res        |      4.77371031593e-09 |      3.02139672386e-10 |
| h_total      |      1.54332155944e-08 |      9.23967468486e-11 |
| h_total_mass |      1.42899807543e-07 |      8.13838869382e-13 |
| s_ig         |      4.41691128117e-11 |       9.4306614095e-12 |
| s_res        |      8.25162160822e-12 |       9.6562634238e-10 |
| s_total      |      3.86091159044e-11 |      5.36007783178e-12 |
| s_total_mass |      1.59059254656e-09 |      7.46965576119e-12 |

Case C and the 1000/100/10/1 Pa series retain small, nonzero departures tending to zero; no values are forced to zero. Dataset accuracy and PR model accuracy are distinct from numerical agreement; zero kij is still a mathematical benchmark, not calibrated mixture thermodynamics.

## Reproduction and checks

Run from repository root, using only the production Python environment for production acceptance:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_pr_caloric.py' -v
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
```

Each comparison record identifies its field and reports reference, production, absolute error, relative error (undefined for an exactly zero reference), atol, rtol and pass/fail. Maximum absolute and relative errors are reported by quantity class. The comparison defaults to read-only. Its explicit `--write` option writes only `production_comparison.json`; it never updates the independent reference. This is the appropriate property-level inspection workflow; no new browser button or browser caloric claim exists.

Independent reference regressions remain isolated:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
```

Automated evidence from this implementation run:

- New M10 production suite: **35 tests passed**, including the 1526-comparison matrix, pure/reordered components, low-pressure behavior, units/flow, opt-in capability boundary, reference shifts, invalid inputs, Cp range/data failures, unsupported water/BIPs, phase/root mismatches, nonconvergence propagation, finite/logarithm/denominator safeguards, no partial caloric publication, deterministic call order, manual-output formatting, relative-error reporting and offline import independence. Focused Cp, ideal H/S, derivative, residual/total H/S and temperature-sensitivity tests supplement the complete matrix comparison.
- Complete Python suite: **140 tests passed**, including all existing M3–M9 numerical/identity regressions and M9 zero-flow/energy-unavailable semantics.
- Complete TypeScript suite: **200 tests passed in 18 files**.
- Independent caloric reference suite: **23 tests passed**.
- M8 independent benchmark: **7 tests passed**; M8 production comparison: **122 comparisons passed**.
- Complete browser suite: **31 tests passed** against the real local engine.
- Contract parity, ESLint, TypeScript type checking, repository formatting, production build and production smoke checks: passed.
- New Markdown/JSON formatting, Python syntax, new-file whitespace and `git diff --check`: passed.

The sandbox initially blocked the Python HTTP fixture's localhost bind. The unchanged suite passed after rerunning with local-server permission. No engineering behavior was changed in response.

## Compatibility and deferred work

Requirements 1.4, flowsheet 1.5 and results 1.6 remain unchanged, as do their schemas and older readers. This is an additive Python property capability, not a reinterpretation of a process contract. `riogineer_components@1.0` is untouched. Existing M8 EOS, stability, RR and flash arithmetic and frozen references are untouched. Existing heater/compressor duties and prescribed separators remain unchanged. M9 does not acquire stream enthalpy, heat duty, shaft work, density or volumetric flow; these remain unavailable according to its accepted scope.

Excluded: PH/PS/UV/TV solvers, rigorous equipment energy balances, water/VLLE, reactions/formation terms, density/volumetric process integration, transport properties, sizing and natural-language interpretation expansion. No live LLM/provider call is needed or made. No production dependency is added.

## PH readiness and conditional next milestone

The property provider is ready to supply equilibrium enthalpy at a trial T/P/z within its validated scope. `equilibrium_caloric_PT` performs stability/PT flash at every trial and handles both one-phase and phase-weighted two-phase H. Callers receive reference metadata and explicit failures, so unsupported/out-of-range/nonconverged evaluations can be distinguished from valid enthalpy residuals. This is a prerequisite, not PH solver qualification.

A future solver must keep its temperature bounds and every trial inside the intersection of declared Cp and provider validity domains. The present empirical Cp ranges do not establish global PT/caloric validity or monotonicity. A bracket must be found deliberately; do not assume h_eq is globally monotonic or that a temperature interval has only one solution. Bubble/dew crossings can change derivatives and phase classification, which must be recomputed at each trial. Targets and trial values must share the same H basis, component order and reference convention. PT/caloric failures must propagate rather than becoming numeric residuals. A future implementation needs explicit bracketing policy, root finder, maximum iterations, H/T tolerances, phase-boundary handling and PH nonconvergence statuses.

**Following the automated acceptance gates and the successful human-operated validation recorded below**, recommend separately scoping **Milestone 11 — Standalone PH Flash Qualification**. It must begin with an independent frozen PH benchmark for single vapor, single liquid and two-phase states. Each benchmark would specify P/z/target H and independently known T, phase classification and H residual; the two-phase case must additionally freeze beta/x/y and phase H values. Conceptually: bracket T → PT equilibrium → M10 h_eq → solve `h_eq−h_target=0` → verify final thermodynamic and enthalpy residuals. This is documentation only; no PH solver or PH benchmark is implemented in M10.

Process heater/cooler/separator integration must remain a later, separately approved milestone even after standalone PH qualification. A rigorous compressor also needs entropy/PS qualification. No unresolved numerical acceptance failures remain; wider empirical accuracy, near-critical/general-state validity, temperature-dependent or calibrated BIPs, and inversion robustness remain deliberately unqualified. Water/VLLE is not the automatic next milestone.

## Completed human-operated manual validation — 2026-09-29

**Human-operated Milestone 10 validation was completed successfully on 2026-09-29, as reported by the user.** This manual acceptance record is separate from the automated validation evidence above; automated command execution and browser regression coverage do not constitute human review.

The human-operated review executed and inspected these five runs:

| Run                                    | Conditions and inspected scope                                                                                                                                               |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Case A (`--case A`)                    | 300 K, 30 MPa absolute; single liquid.                                                                                                                                       |
| Case B (`--case B`)                    | 300 K, 300000 Pa absolute; vapor-liquid equilibrium. Liquid and vapor caloric properties, beta, equilibrium enthalpy/entropy, h_V−h_L and s_V−s_L were inspected separately. |
| Case C (`--case C`)                    | 300 K, 1000 Pa absolute; single vapor. Z near unity and small but nonzero PR residual properties confirmed the expected low-pressure behavior.                               |
| Pure methane (`--case pure_methane`)   | Reference states at 280, 300, 350 and 400 K were inspected.                                                                                                                  |
| Pure n-hexane (`--case pure_n_hexane`) | The run was inspected from beginning to completion, including vapor and liquid reference states over the qualified cases.                                                    |

All five runs reported:

```text
PASS: 1526 comparisons; peng_robinson@1.0; riogineer_caloric@1.0
```

No FAIL result was observed. The human review confirmed the expected phase classifications and the reported Cp, Z, MW, ideal-gas enthalpy/entropy, residual enthalpy/entropy, total enthalpy/entropy, mass-specific properties, PR derivatives and, where applicable, two-phase aggregate properties. Case B specifically confirmed liquid/vapor caloric properties and equilibrium aggregation. The pure-component reviews confirmed temperature-dependent caloric behavior and successful frozen-reference comparisons.

This manual acceptance is limited to the defined M10 property-qualification scope. It does not qualify PH/PS flash, water caloric properties or process-equipment energy integration. No thermodynamic calculations or benchmark values were changed to record this review. Milestone 11 has not started.

Commands used for the reported review, from repository root:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --case A
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --case B
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --case C
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --case pure_methane
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --case pure_n_hexane
```

Additional reproduction commands below remain available; they are not claimed as separate human-reviewed runs in this record:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --case low_pressure
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --details
```

Additional-temperature display selectors are `T280_L`, `T280_VL`, `T280_V`, `T350_L`, `T350_VL`, `T350_V`, `T400_L`, `T400_VL`, `T400_V`; for example:

```sh
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --case T350_VL
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py --json
```

All 1526 acceptance comparisons execute regardless of the display selector. Default output shows the 12 binary cases and maximum errors; `--details` adds all pure/limit states and every comparison. `--json` prints complete machine-readable evidence without writing it. Each selected Case B phase shows component-labelled composition, Z, MW, h_ig/h_res/h_total, s_ig/s_res/s_total and J/kg/J/(kg K) values; its aggregate shows beta, liquid molar fraction, h_eq, s_eq and phase differences. The accompanying table includes frozen value, production value, absolute/relative errors, atol/rtol and pass/fail, including comparisons at exact frozen phase composition.

## Automated acceptance gates

| Gate        | Evidence                                                               | Status |
| ----------- | ---------------------------------------------------------------------- | ------ |
| Dataset     | Exact coefficients/ranges/source and unchanged M7 constants            | PASS   |
| Cp          | Both components at all 10 frozen Cp/integral points                    | PASS   |
| Ideal H     | Component integrals and mixture phase H across the frozen matrix       | PASS   |
| Ideal S     | Component integrals, pressure and explicit mixing/no-mixing regression | PASS   |
| Derivatives | Same-state alpha, pure a and mixture a analytic derivatives            | PASS   |
| Residual H  | All frozen phase departure values                                      | PASS   |
| Residual S  | All frozen phase departure values                                      | PASS   |
| Phase       | A, B liquid/vapor, C, additional temperatures and pure states          | PASS   |
| Aggregate   | Case B and other frozen two-phase equilibrium H/S/differences          | PASS   |
| Units       | Molar/mass-specific and enthalpy-flow round trips                      | PASS   |
| Regression  | M3–M9, all repository checks and independent benchmark suites          | PASS   |

M10 implementation and human-operated validation are complete within the specified property scope. The successful manual review on 2026-09-29 is recorded separately from automated coverage above. M11 has not started.
