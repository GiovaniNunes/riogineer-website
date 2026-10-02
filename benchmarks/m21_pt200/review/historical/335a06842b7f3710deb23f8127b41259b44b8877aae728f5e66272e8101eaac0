# Pre-M20 — Low-pressure separator-liquid pump qualification

Study date: 2026-10-01. **Specific numerical tuples are supported; no production
extension or bounded configurable domain is qualified yet. M20 is not implemented.**
All new calculations are study-only. Production models, shared numerical routines,
contracts and historical evidence are unchanged.

## Baseline and preservation

Verified branch `main`, full HEAD and live remote `refs/heads/main`:
`2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0`, message
`Complete Milestone 19 variable-composition pump and record human acceptance`.
The first sandboxed remote query could not resolve GitHub; the permitted read-only
retry verified the live remote. Initial index was empty. Initial working changes
were only `next-env.d.ts` and `tsconfig.json`. Both were copied to
`/tmp/riogineer-pre-m20-preservation/` before numerical work. Their SHA-256 values:

- `next-env.d.ts`: `1f2e4a6d7f55de2de72375901050f2af22ed89992a781fce74d6e6a4d3fc94f0`.
- `tsconfig.json`: `e2a28ab5d02bb5b555a28523be8786d9dc3a400fe125f14602261e24a6288126`.

`benchmarks/low_pressure_separator_pump/preservation.json` records every initially
tracked file's actual working bytes. The only authorized existing-file change is
the concise master-context entry. Root AGENTS.md, current master-context/M17–M19
entries, prerequisite reports, interfaces, guards and reproduction code were read.
No service was started/stopped, browser used, stage, commit, push or deployment made.

## Actual inventory and interface findings

Inventory uses the first 24 actual M17 outputs already frozen by M19's production
separator compatibility study; its additional high-pressure case is excluded.
The original 24 M17 inputs establish PT/PH mode. Existing artifacts suffice:
there is no reason to rerun the separator or alter historical output bytes.
Every complete actual liquid stream, component mass rates, total/molar flow,
composition, phase H/S, parent phase result and rejection is in `production.json`.
Specific enthalpy is never assigned to an absent phase.

There are **19 present liquids and five absent liquids**. Fifteen liquids were
separated from parent VL equilibrium; they are saturated liquid phases, not a
bulk two-phase pump feed. Four parent results are single liquid: two at 30 MPa,
and PT/PH BUBBLE_BELOW at 6 MPa. Independent bubble margins corroborate positive
thermodynamic compression: approximately 19.8024/18.5118 MPa for the 30 MPa
states and 4,715.456 Pa for the two cold 6 MPa states. The latter are only 0.05 K
below their historical bubble point and are not a broad engineering reserve.

Every literal stream passed to the actual M19 callable rejects with
`independent_caloric_input`: the separator supplies non-null enthalpy flow, while
M19 accepts PT-defined input. Additional scalar failures are all retained in the
inventory. An explicitly separate PT/rates projection also records the first
production scope rejection; it is not claimed as supported direct use. None of
these calculations silently deletes the actual stored stream enthalpy.

The stream dictionary preserves T/P, component rates, enthalpy flow and molecular
properties, but has no explicit phase identity or saturation provenance. Parent
separator diagnostics preserve phase identity, EOS/caloric provenance and entropy;
those must currently be joined from equipment results. The PT projection alone
cannot express “this material is the extracted equilibrium liquid phase.”

All 19 actual liquid-composition PT evaluations at unchanged T/P succeed as
single liquid in both reference and production. Production high-accuracy H/S
reproduce the stored phase properties exactly except a 3.638e-12 J/mol H
roundoff in PH_DEW_BELOW. Both production precision profiles give single liquid
at the actual states. Thus no forced root, phase-specific fallback, temperature
reduction or pressure increase is needed for these exact inlet evaluations.
Independent phase-specific liquid H/S are separate diagnostics and agree with
the separator phase within the predeclared caloric allowances. They are justified
by parent phase provenance and independent local coexistence evidence, not by
assuming any liquid root is stable.

## Saturation and local admissibility

Independent fixed-T bubble solving is followed by two-component log-fugacity
equality refinement, initialized from the library solution. Nontrivial composition
and Z gaps plus equilibrium PT at 0.999/1.001 bubble pressure corroborate the local
branch. All 19 refined residuals pass 2e-10; maximum is 9.770e-14. Largest correction
from the library pressure is 2.422e-8 Pa. Raw results remain stored: two library
fugacity residuals (approximately 1.083e-9 and 9.115e-9) fail that stricter gate.
The direct refinement resolves this numerical precision issue without changing
any physical model or comparison tolerance. It shares Thermo fugacity evaluation
and is not a second independent EOS.

The fifteen saturated products have |P−Pbubble| below 5.5e-6 Pa, well inside the
predeclared 1 Pa diagnostic band. That band diagnoses numerical proximity; it does
not correct a stream, grant subcooling or authorize acceptance of entrained vapor.
Independent and production probes at relative pressure offsets ±1e-3, ±1e-6,
±1e-9 and zero are kept distinct from actual feeds. Production identifies the
saturated products as VL at −1e-6, with vapor fractions roughly 7.18e-9–1.11e-6,
but as single liquid at −1e-9. This resolves neither arbitrary trace-vapor
admission nor exact boundary classification in all cases. No beta is clipped.
A genuinely bulk VL negative at 300 K, 0.3 MPa, z=0.5 is separately rejected.

A future local criterion should combine actual equilibrium/phase evidence with
same-T/composition coexistence branch validation and a declared margin policy.
Saturated service needs an explicit branch of that policy, not a false positive
subcooling claim. Fixed 16 MPa witnesses cannot supply local inlet margin here.
Boundary probes and endpoint bubble checks are diagnostic evidence only; no
production saturation solver or runtime boundary guard was implemented.

Thermodynamic feasibility does not establish installation feasibility. NPSH,
suction losses, static head, cavitation safety, head/capacity sizing, mechanical
losses and electrical power remain outside scope. No cooler or suction head is
assumed, and no conditioned process case is substituted for an actual product.

## Independent reference and acceptance criteria

The independent process imports only established benchmark Thermo PR/PT/caloric
and independent PS/PH inversion helpers. It asserts that no `riogineer_engine`
module was imported. Historical production outlet T/P/composition/flow define
study inputs; independently evaluated properties define reference expectations.
Production calculations run separately after the reference is frozen.

Environment: Python 3.10.10, Thermo 0.6.0, chemicals 1.5.2, fluids 1.3.1,
NumPy 2.2.6, SciPy 1.15.3 and pandas 2.3.3. Full installed versions, inherited
source hashes, actual library/Cp hashes and conventions are frozen in reference
JSON and checked against M19's established environment. Dependency pins/notices
are reused read-only from `benchmarks/pump_energy/configurable_scope/`.

Component order is methane then n-hexane; explicit symmetric 2×2 zero kij,
canonical PR a=0.45724, b=0.07780 and R=8.31446261815324 J/mol/K; classical
quadratic mixing and the unchanged Poling ideal Cp polynomials. MWs are
16.0428/86.17536 kg/kmol; critical constants and all Cp coefficients are recorded
in JSON and match Pre-M19. Pure ideal H/S are zero at 298.15 K and 101325 Pa;
ideal mixing/pressure entropy and PR residuals are retained. No offset fitting,
water, additional components, changed EOS or fitted kij is introduced.
Numerical agreement for this physical model is not experimental validation.

`PLAN.md` fixes the matrix and inherited tolerances before comparison; its separate
addendum records only the targeted boundary refinement and 8 MPa challenge.
T: 1e-7 K; H: 1e-6+1e-11|H| J/mol; S: 1e-8+1e-11|S| J/mol/K;
Z: 2e-10+1e-9|Z|; composition/beta: 2e-9. Fresh PS/PH residuals are
1e-8 J/mol/K and 1e-6 J/mol. No tolerance was loosened after results.

Positive-rise paths use inlet PT H/S → PS(P2,S1) →
Htarget=H1+(H2s−H1)/eta → PH(P2,Htarget) and fluid power F(H2−H1).
Flows are mol/s, H J/mol, power W. Both inverse routines retain their full
200–500 K scans (64 PS, 128 PH), one candidate and fresh final evaluation.
Production scan failures remain failures and never receive substituted reference
values. Inlet, ideal outlet and actual outlet must each be admissible liquid;
phase crossings at those evaluated states reject. Successful endpoints do not
prove continuous-path admissibility at every intermediate pressure, and no
continuous-path or arbitrary pressure-range claim is made.

Component/mass conservation, target H recovery, energy identity, entropy
nondecrease (−2e-8 allowance), reconstructed efficiency and eta=1 consistency
are checked. Endpoint/work/power comparison is independent of algebraic energy
closure. The work screen uses B(H)=1e-6+1e-11|H| and
E=[B(H1)+B(H2s)]/eta+B(H1)+B(H2)+500e-8/eta+1e-6+roundoff.
Require positive ideal/actual rises and E/(H2−H1)≤1e-4. The 500 K term covers the
full scan domain and warm dew-side product, instead of transplanting M19's 370 K
bound. E is an engineering screen, not a certified error interval.

Exact identity preserves the inlet, uses no inverses, zero fluid work and null
reconstructed efficiency. The artifact also retains the complete unchanged actual
separator stream for identity. Positive unresolved work is never made identity.

## Matrix and interpretation

Eight selected actual low-pressure liquids cover PT/PH, methane below 0.01,
0.1/0.3/1/6 MPa, saturated and compressed inlet states and cold/warm boundary
products. Each has identity, +10000 Pa and +1 MPa cases at eta=0.8 and its actual
historical flow. These are moderate transfer-pressure rises and a previous
minimum-work floor, not an assumed capability through 30 MPa. PT_DEW_BELOW retains
its actual 0.1333 mol/s flow; that historical tuple is explicitly outside the
5–200 mol/s scaled-case interval and is never silently enlarged.

PH_FLASH adds eta=0.6 and 1, +10/+100/+1000 Pa, and separate flow-scaled 5/17.3/200
mol/s cases. Two cold bubble products at 8 MPa discharge investigate the specific
historical PS scan limitation. Seven controlled negatives cover actual absent
liquid, genuine bulk VL, vapor, efficiencies 0/0.59/1.01 and pressure decrease.
All 41 candidates remain in the ledger. There is no Cartesian sweep or proposed
configurable domain, hence no off-grid-domain qualification claim. Boundary
perturbations are included but do not replace independent domain holdouts if a
future bounded domain is proposed.

## Future production dependencies

1. Decide an explicit saturated-liquid stream contract: phase identity, source
   separator/state provenance, H/S convention and consistency with rates/T/P.
   Reject genuine two-phase material and ambiguous provenance. Do not claim that
   stripping H from the current stream provides production compatibility.
2. Qualify local phase/margin guards at inlet, ideal and actual outlet; preserve
   saturation semantics and reject unresolved boundary branches. Installation
   NPSH/cavitation assessment remains separate.
3. Select scope from the accepted tuples or perform a separate bounded-domain
   study with boundary corners and independent off-grid holdouts. Temperature,
   pressure, composition (including below 0.01) and flow changes require explicit
   qualification; finite samples do not prove universal convergence.
4. Retain failure-atomic PS/PH handling, full scans, stability/PIP, caloric,
   conservation, entropy, efficiency and work-resolution checks. The 1000 Pa
   example is evidence for one tuple, not a general replacement floor.
5. Qualify adapters/contracts and mixed-equipment propagation under a separately
   authorized implementation request. No version, frontend/PFD or production
   pump/separator behavior is changed by this study.

## Results and limitations

**41 ledger entries: 30 accepted numerical tuples, nine rejected, two unresolved
pump paths. All 2,337 applicable production/reference checks pass.** Eight accepted
entries are identities; 22 are positive-rise calculations. Accepted numerical
results do not mean the current pump wrapper supports these inputs.

Accepted scope is exactly the eight selected source tuples at identity, +10000 Pa
and +1 MPa; PH_FLASH +1 MPa at eta=0.6/1; PH_FLASH +1000 Pa at eta=0.8; and the
three explicitly scaled PH_FLASH +1 MPa cases. All other settings remain exactly
those in the ledger. No continuous T/P/composition/efficiency domain is inferred.
For example PH_FLASH at its actual 291.742138657 K, 1 MPa, zCH4≈0.057181287482,
F≈52.0557688705 mol/s, discharged to 2 MPa at eta=0.8 transfers approximately
8,068.18515750 W into the fluid. PT_DEW_BELOW at actual 0.133305529960 mol/s
and 6→7 MPa transfers approximately 33.31282982 W. No motor-power claim follows.

Seven input/phase negatives reject as planned. The 10 Pa and 100 Pa PH_FLASH
rises have positive calculated work but E/dH≈0.00847116 and 0.000847113, so are
rejected for inadequate numerical work resolution. The 1000 Pa case has
E/dH≈8.47114e-5, only about 1.18 times headroom to the 1e-4 threshold; it passes
this tuple's test but is not a robust general lower floor. All selected 10000 Pa
paths pass. No positive rise is relabelled identity.

Both targeted 8 MPa cold bubble cases have independently admissible liquid
reference paths but **production PS rejects its complete scan**. At discharge
8 MPa, T=461.9047619047619 and 466.6666666666667 K, PT returns
`flash_not_converged`, recorded as `pt_evaluation_failure`; PS returns
`property_evaluation_failed` with “Complete scan contains property holes”.
The two compositions are exactly those in PT_BUBBLE_BELOW and PT_BUBBLE_ABOVE.
These remote scan failures are numerical limitations, not evidence that the
actual cold inlet is two phase or that the independent pump path is physically
impossible. No PH is called after failed PS, no hole is bridged and no reference
outlet is substituted. The historical M18 limitation remains reproducible.
The nearby 7 MPa successes do not justify a pressure interval through 8 MPa.

Maximum applicable absolute discrepancies:

| Quantity | Maximum error |
| --- | ---: |
| T | 1.2961e-11 K |
| Equilibrium H | 2.2956e-9 J/mol |
| Equilibrium S | 7.8444e-12 J/(mol K) |
| Actual enthalpy rise | 2.2993e-9 J/mol |
| Fluid power | 4.5985e-7 W |

The code retains partial diagnostic comparisons on failures; they cannot promote
a failed inverse to acceptance. Actual equal-pressure identities preserve the
original stream. All selected successful inlet/ideal/actual states are liquid;
no endpoint phase crossing is observed. Endpoint coexistence checks are retained
in the independent artifact. Intermediate-path/global branch proof is absent.

The evidence therefore supports **specific accepted tuples only, with no
production extension yet**. Saturated inlet contract semantics, local phase guards,
PS scan limitations, a justified configurable envelope and future integration
remain dependencies. Numerical feasibility of these tuples is a narrower result
than M20 implementation or safe physical pump service.

## Inventory summary

Full precision and component/mass/energy records are in `production.json`;
rounded display below never defines inputs. “Saturated” means parent VL plus
independent local boundary corroboration, not bulk two-phase pump material.

| Source | Mode | T K | P MPa | Liquid zCH4 | Liquid mol/s | Kind | M19 scalar reasons |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| PT_VL_HEATING | PT | 350.000000000 | 0.3 | 0.007744817176 | 9.1269233862 | saturated | composition_scope, pressure_scope |
| PT_LIQUID_COOLING | PT | 280.000000000 | 30 | 0.500000000000 | 100.0000000000 | compressed | temperature_scope, pressure_scope |
| PT_VAPOR | PT | 400.000000000 | 0.001 | — | 0 | absent | absent_liquid |
| PT_VL_INLET_EQUAL | PT | 300.000000000 | 0.3 | 0.015619720086 | 46.5357489776 | saturated | pressure_scope |
| PT_VAPOR_INLET_COOLING | PT | 280.000000000 | 1 | 0.062495158908 | 9.5798124667 | saturated | temperature_scope, pressure_scope |
| PT_DOUBLE_FLOW | PT | 350.000000000 | 0.3 | 0.007744817176 | 18.2538467724 | saturated | composition_scope, pressure_scope |
| PT_LOW_FLOW | PT | 350.000000000 | 0.3 | 0.007744817176 | 0.4563461693 | saturated | composition_scope, pressure_scope, flow_scope |
| PH_FLASH | PH | 291.742138657 | 1 | 0.057181287482 | 52.0557688705 | saturated | temperature_scope, pressure_scope |
| PH_LIQUID_EQUAL | PH | 300.000000000 | 30 | 0.500000000000 | 100.0000000000 | compressed | temperature_scope, pressure_scope |
| PH_VAPOR | PH | 381.635814551 | 1 | — | 0 | absent | absent_liquid |
| PH_VAPOR_EQUAL | PH | 300.000000000 | 0.001 | — | 0 | absent | absent_liquid |
| PH_VL_EQUAL | PH | 300.000000000 | 0.3 | 0.015619720086 | 46.5357489776 | saturated | temperature_scope, pressure_scope |
| PH_VL_REDUCTION | PH | 291.501661531 | 1 | 0.057280447626 | 52.0717057567 | saturated | temperature_scope, pressure_scope |
| PH_DOUBLE_FLOW | PH | 291.742138657 | 1 | 0.057181287482 | 104.1115377410 | saturated | temperature_scope, pressure_scope |
| PH_LOW_FLOW | PH | 291.742138657 | 1 | 0.057181287482 | 2.6027884435 | saturated | temperature_scope, pressure_scope, flow_scope |
| PH_HEXANE_RICH | PH | 296.033146495 | 0.1 | 0.004712273406 | 88.1630009407 | saturated | composition_scope, temperature_scope, pressure_scope |
| PH_BUBBLE_BELOW | PH | 231.067554351 | 6 | 0.500000000000 | 100.0000000000 | compressed | temperature_scope, pressure_scope |
| PT_BUBBLE_BELOW | PT | 231.067554351 | 6 | 0.500000000000 | 100.0000000000 | compressed | temperature_scope, pressure_scope |
| PH_BUBBLE_ABOVE | PH | 231.167554351 | 6 | 0.499710609242 | 99.9420310039 | saturated | temperature_scope, pressure_scope |
| PT_BUBBLE_ABOVE | PT | 231.167554351 | 6 | 0.499710609242 | 99.9420310040 | saturated | temperature_scope, pressure_scope |
| PH_DEW_BELOW | PH | 468.215889532 | 6 | 0.214047610417 | 0.1333055298 | saturated | temperature_scope, pressure_scope, flow_scope |
| PT_DEW_BELOW | PT | 468.215889532 | 6 | 0.214047610417 | 0.1333055300 | saturated | temperature_scope, pressure_scope, flow_scope |
| PH_DEW_ABOVE | PH | 468.315889532 | 6 | — | 0 | absent | absent_liquid |
| PT_DEW_ABOVE | PT | 468.315889532 | 6 | — | 0 | absent | absent_liquid |

All literal streams additionally fail the enthalpy-input contract. Strict scalar
comparisons retain PH values just below 300 K; no rounding silently admits them.

## Verification, frozen artifacts and reproduction

Completed fresh-process byte-for-byte reproduction of both independent reference
and production comparison, plus deterministic ledger reproduction. **Eight focused
unittest methods passed**, including exact inventory/identity preservation,
independent caloric agreement, local branch refinement, conservation/work gates,
flow scaling, controlled negatives, real retained PS holes and historical-file
integrity. Independent/production classifications agree at all 133 inventory
pressure probes; the reference contains 52 distinct endpoint boundary records
with no unavailable bubble calculation. These are finite diagnostic samples.

All initially tracked files match their captured working hashes except the
intended master-context addition. Both unrelated modified files also match their
saved copies byte-for-byte. HEAD is unchanged, staging empty; no commit, push or
deployment occurred. Python AST syntax, new-file whitespace and `git diff --check`
passed. No full application, browser or historical numerical suite was rerun.

Frozen SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| `reference.json` | `f8561da75590265a6060f69edfa3b8c0895670178cbd12bcacbd6b819d6d1858` |
| `production.json` | `28410bb61af23f5cce56bc187c477e26df324a103296150621c43c09420a02ea` |
| `candidate_ledger.json` | `2c4ed458054ea1c675db6a9bad71df570498a3f617bd8cc86886c5b82cb7cc58` |

Run from repository root (defaults verify, never overwrite):

```sh
.local/pre-m8-venv/bin/python -B benchmarks/low_pressure_separator_pump/reference.py
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/compare.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/low_pressure_separator_pump -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/verify.py
```

`--write` exists only for initial artifact creation. Reference, production and
ledger generations must occur in that order, with source frozen. See the study
README for environment pins, third-party notices and integrity behavior.

Exact task changed-file inventory (13 paths):

- `PRE_MILESTONE_20_LOW_PRESSURE_SEPARATOR_PUMP_QUALIFICATION.md` — new report.
- `docs/RIOGINEER_MASTER_CONTEXT.md` — concise appended study status only.
- `benchmarks/low_pressure_separator_pump/PLAN.md`.
- `benchmarks/low_pressure_separator_pump/README.md`.
- `benchmarks/low_pressure_separator_pump/common.py`.
- `benchmarks/low_pressure_separator_pump/reference.py`.
- `benchmarks/low_pressure_separator_pump/compare.py`.
- `benchmarks/low_pressure_separator_pump/verify.py`.
- `benchmarks/low_pressure_separator_pump/test_study.py`.
- `benchmarks/low_pressure_separator_pump/reference.json`.
- `benchmarks/low_pressure_separator_pump/production.json`.
- `benchmarks/low_pressure_separator_pump/candidate_ledger.json`.
- `benchmarks/low_pressure_separator_pump/preservation.json`.

Final Git status: modified master context; new report and study directory;
pre-existing modified `next-env.d.ts`/`tsconfig.json` retained unchanged.
Everything is unstaged. No production or historical benchmark file changed.
