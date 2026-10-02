# PT equilibrium iteration budget — predeclared qualification

Study only. Preserve all 513 baseline paths, including the entire preceding study.
Compare fixed high_accuracy PT equilibrium caps 100, 200, 400. Stability cap 100,
RR cap 200, fugacity 1e-12, material 1e-10 and all caloric settings stay unchanged.
No adaptive retry or fallback. Candidate name: pr_high_accuracy_pt200@1 (or a
separately justified narrower outcome if it fails). Legacy defaults stay intact.

Physical PT matrix: both actual cold liquid compositions; P=7,7.5,7.8,8 MPa;
the two historical failed temperatures 200+300*55/63 and 200+300*56/63, each
with offsets -0.05,0,+0.05 K (48 states). Six off-grid T/P/z holdouts selected
before evaluation: (460.37,7.61MPa,.4937), (464.23,7.83,.5063),
(468.19,7.97,.5017), (470.11,7.69,.4873), (462.77,8.03,.4981),
(466.13,7.37,.5129). Add liquid/vapor/VL controls and existing bubble/dew and
vapor-parent restart states from frozen qualification inputs. No rectangle claim.

Full chains: both actual cold sources at Pout=7,7.5,7.8,8 MPa, eta=.8; plus
M20 PH_FLASH 2 MPa, PT_VL_HEATING 1.3 MPa, PT_DEW_BELOW 7 MPa, and cold identity.
Capture fresh M17 sources, preserve actual liquid rates and Hdot, resolve the
source through a private current execution context, then candidate-profile inlet
PT -> complete PS -> efficiency-derived H target -> PH -> candidate and legacy
fresh final/local phase checks -> equipment and integrated balances. No oracle
value drives the pump chain. Application admission remains the original 30 tuples.

Independent inverse anchors: forward liquid (300K,30MPa), VL (350K,1MPa), vapor
(317.3K,1kPa), z=.5, each independently inverted with PS and PH. These standalone
forward-defined targets are not substituted for a pump prerequisite.

Inherited comparisons: T 1e-7K; beta/x 2e-9; Z 2e-10+1e-9|Z|;
H 1e-6+1e-11|H| J/mol; S 1e-8+1e-11|S| J/(mol K).
PS residual <=1e-8, PH <=1e-6; respective widths 1e-10/1e-12 K;
64/128 full 200–500K scans; 100 scalar-root iterations; original ambiguity,
PS holes and PH connected-interval policies. Final PT fugacity/material and
stability gates remain unchanged. Independent fugacity equality <=1e-9;
phase log-fugacity coefficients compare within 2e-9. Stability methods/counts
are implementation-specific: compare phase/stability conclusions and retain
initial and final diagnostics, not algorithmically incomparable iteration counts.
Pump work E/dH <=1e-4 including existing 500K PS residual propagation. Original
mass/energy/phase/association guards unchanged except explicitly selected settings.

No production monkey-patching. Public immutable PT settings are used directly.
Because inverse functions hard-code nested settings, isolate an AST-derived copy
with exactly one added keyword argument and one replacement per function. Reuse
all original control-flow and guard code. Compile in a separate namespace; never
replace a production function, module, default or provenance. The inverse guard
gets the same additive expected-profile argument, and checks final PT settings
explicitly. Record source hashes and exact transformation. This is a parameter
injection experiment, not a copied EOS or new inverse algorithm.

Compatibility: trace PT loop observations without mutating locals; compare full
numeric payload/diagnostics after removing only the declared settings metadata,
and hash executed iteration sequences. Successful <=100-iteration cases should
match exactly. Inspect any discrepancy. Synthetic tests separately cover capped
exhaustion, wrong profile, ambiguity, holes, nonfinite inputs, residual failures,
phase and payload rejection. Real low-budget controls use cap=1, never fallback.

Cost: deterministic PT calls and summed equilibrium iterations are primary. For
timing use one warmup then three timed repetitions per selected ordinary, slow
and failing case, rotate profile order, perf_counter, serial execution without
tracing. Store all samples and median; no hard timing ratio acceptance threshold.
400 doubles the permitted equilibrium loop bound of 200, not necessarily actual
work; no finite matrix proves a universal convergence bound.

Acceptance: smallest fixed candidate that completes declared positive finite
cases with all independent comparisons and retained guards; controlled negatives
must return no accepted payload. Failures retained, not reclassified as successes.
Default artifact verification is read-only; timing measurements are separate from
byte-deterministic numerical reproduction. Report actual failures, including the
historical M20 next-env.d.ts snapshot assertion, without editing or excluding it.

## Supplementary reference phase-identity audit

Raw comparisons exposed six independent reference states with the two named
phases exchanged; aggregate H/S and unordered phase properties agree, but 195
named-field comparisons fail across profiles. Preserve those raw artifacts and
failures. Before supplementary classification, require independent Thermo PIP>1
for one phase and PIP<1 for the other, the former having smaller molar volume,
larger mass density, and a nontrivial Z/composition gap (>0.01). Fresh independent
phase objects must reproduce their recorded Z within 1e-10. Map complete phase
records and their fractions only when these identity checks pass. Never alter
phase numbers, tolerances, EOS or production labels to force agreement. Ambiguous
identity remains unresolved. Record raw versus physically identified reference
separately, and retain the original failed unit/comparison result in the report.
This audit concerns independent reference phase naming, not a new inverse policy.
