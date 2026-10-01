# Pre-M19 variable-composition liquid pump qualification

Qualification supports a useful configurable extension: methane mole fraction
0.01–0.55, n-hexane balance, explicit constant zero kij. M19 implementation and
human acceptance are distinguished in [MILESTONE_19.md](MILESTONE_19.md).

## Baseline and independence

Started on `main` at `2a2f4cc9c3e827187af1d64be9f1773b23389618`, matching live
`origin/main`. Staging was empty; the only initial modification was `next-env.d.ts`,
whose bytes were captured for preservation. M18 production pump files and all
historical qualification artifacts remain unchanged.

Independent evidence is in `benchmarks/variable_composition_pump/`. The exploratory
phase map informed `PLAN.md`; the 64-case pump matrix and 824-point coexistence
matrix were fixed before production comparison. Frozen reference SHA-256:
`a3c2e7c3fce2734dd8e977b569d003e9ae42e612684654be660a490d61675ce4`.
The reference reproduced byte-for-byte. Its generator asserts that no
`riogineer_engine` module was imported. The separate verifier checks source,
installed library and actual Poling-data hashes.

Reference environment: Python 3.10.10; thermo 0.6.0, chemicals 1.5.2, fluids 1.3.1,
NumPy 2.2.6, SciPy 1.15.3, pandas 2.3.3. Full transitive versions and source hashes
are frozen in JSON. Independent Thermo PR/PRMIX PT evaluations and benchmark-only
PS/PH bracketing wrappers reuse the established independent methodology. The
coexistence-equation solve uses SciPy root separately from Thermo bubble solving,
but both share Thermo fugacity evaluation: it is a numerical cross-check, not a
second physical model. Production uses its unchanged in-house PR/PT/PS/PH code.

PR constants: a=0.45724, b=0.07780, R=8.31446261815324 J/mol/K; classical quadratic
mixing, explicit symmetric zero kij. Reference pure ideal H and S are zero at
298.15 K and 101325 Pa; ideal mixture entropy includes mixing and pressure terms,
with PR residual H/S. Component data and ideal Cp/R polynomials:

| Component | MW kg/kmol |    Tc K |             Pc Pa |              omega | Cp/R coefficients, ascending T powers               |
| --------- | ---------: | ------: | ----------------: | -----------------: | --------------------------------------------------- |
| methane   |    16.0428 | 190.564 |           4599200 |            0.01142 | 4.568, −0.008975, 3.631e−5, −3.407e−8, 1.091e−11    |
| n-hexane  |   86.17536 |  507.82 | 3044115.328359688 | 0.3003189315498438 | 8.831, −0.000166, 0.00014302, −1.8314e−7, 7.124e−11 |

Methane Cp range 50–1000 K; hexane 200–1000 K. Both cover the unchanged 200–500 K
inverse scans. Numerical agreement is not experimental validation.

## Proposed scope, evidence and phase rationale

Retained candidate limits: Tin 300–350 K; Pin 20–25 MPa absolute; Pout=Pin exactly
or Pin+10000 Pa ≤ Pout ≤30 MPa; eta 0.6–1; F 5–200 mol/s. All reached states must
be 300–370 K and 20–30 MPa. Pure endpoints are excluded, not implicitly qualified.
Mass rates determine composition and molar flow through the M7 molecular provider.

The 64-case pump matrix includes 32 coupled boundary corners, four identities,
four interior compositions, eight off-grid holdouts, equimolar compatibility,
a new z=0.25 demonstration, three flow cases, two sub-floor challenges, eight
excluded compositions/endpoints, and one non-liquid challenge. Independent policy:
53 accepted; 11 rejected. Rejections remain recorded even when a bare reference
calculation converges. `exploration.json` also retains phase/solver failures at
methane-rich and pure conditions.

Coexistence evidence covers z=0.01+0.02j (28 compositions), T=300+2.5j (29
temperatures), and 12 independent off-grid points: **824/824 accepted**. Each
requires a nontrivial bubble branch, log-fugacity residual ≤2e−10, direct/library
bubble-pressure agreement ≤1000 Pa, VL below / liquid above at pressure factors
0.999/1.001, and a liquid 16 MPa witness. Sampled vapor/liquid composition gap >0.30
and Z gap >0.24 screen branch degeneration in this candidate region.

Largest bubble pressure: **15,135,460.174570 Pa**. Central probes use ±0.01 K and
±1e−5 mole fraction; observed slopes stay within prospective allowances of
100000 Pa/K and 40000000 Pa per unit mole fraction. Nearest-node allowances are
125000+400000 Pa, plus 1000 Pa numerical reserve. Thus the 16 MPa witness retains
**338,539.825430 Pa** after the 526000 Pa screening allowance. These are empirical
engineering allowances, not proved derivative bounds over every interval.
Finite sampling cannot guarantee convergence or exclude every unsampled anomaly. Observed maxima were 61,098.545 Pa/K and 31,257,110.204 Pa per mole fraction; minimum sampled composition and Z gaps were 0.340698660 and 0.261620149.

At z=0.60, warm-state bubble pressures exceed 16 MPa and the witness becomes VL.
At richer compositions the exploration includes near-critical/supercritical label
ambiguities and unavailable reference solutions. A single_liquid label alone is
insufficient. The chosen upper bound stops at 0.55 with tested witness reserve;
the lower 0.01 bound excludes unqualified pure/near-pure service. Neither is a
universal physical boundary. No clipping, recipe substitution or fallback is used.

## Runtime and numerical qualification

Every accepted inlet, isentropic outlet and actual outlet requires a fresh
high_accuracy PT calculation, associated state/composition/caloric payload,
converged stable TPD diagnostics and PIP>1. Each also requires a fresh stable-liquid
16 MPa witness at the same T and actual composition. Identity has one inlet
witness and no inverse calculations. Guard failure returns no partial outlet.

The physical model remains S1 from PT; PS(P2,S1); target h2=h1+(hs−h1)/eta;
PH(P2,target); fluid power F(h2−h1). PS retains 64-point complete scanning with no
holes; PH retains 128-point valid-interval scanning, never bridging a property
hole. Both use 200–500 K, one bracket and a fresh final-state evaluation. No shared
solver settings, defaults, algorithms or tolerances changed.

Independent comparison tolerances remain: T 1e−7 K; H 1e−6+1e−11|H| J/mol;
S 1e−8+1e−11|S| J/mol/K; Z 2e−10+1e−9|Z|; composition 2e−9. PS/PH runtime fresh
residual limits are 1e−8 J/mol/K and 1e−6 J/mol. These inherited fixed allowances
were set before M19 production comparison. Work differences use propagated
enthalpy allowances rather than an arbitrary relative power tolerance.

For B(h)=1e−6+1e−11|h|, the runtime work allowance is
E=(B(h1)+B(hs))/eta+B(h1)+B(h2)+370e−8/eta+1e−6+roundoff.
Require E/(h2−h1)≤1e−4 and strictly positive ideal and actual rises. Reconstructed
efficiency tolerance is eta·1e−6/(h2−h1)+64 epsilon; entropy generation ≥−2e−8.
Unity eta also requires |T2−Ts|≤1e−7 K and |S2−S1|≤2e−8. Extensive target power
residual ≤F·1e−6+roundoff; algebraic energy closure uses roundoff. Component mass
rates are copied exactly; total/molar mass consistency is checked. Equal-pressure
identity has exact zero power and null ideal state/reconstructed efficiency.

## Actual separator output compatibility

`separator_compatibility.json` records actual full M17 outlet streams and phase
diagnostics from all 24 frozen M17 cases, plus one additional high-pressure liquid
case. No T, P, mass rate or composition was overwritten. All 24 historical cases
are either absent-liquid or outside one or more M19 inlet limits.

| Actual M17 case       |      Liquid methane fraction | Actual pressure | Principal mismatch                                 |
| --------------------- | ---------------------------: | --------------: | -------------------------------------------------- |
| PT_VL_HEATING         |               0.007744817176 |         0.3 MPa | 19.7 MPa below minimum; composition below 0.01     |
| PT_VL_INLET_EQUAL     |               0.015619720086 |         0.3 MPa | 19.7 MPa below minimum despite composition overlap |
| PH_FLASH              |               0.057181287482 |           1 MPa | 19 MPa below minimum; T≈291.742 K below 300 K      |
| PH_HEXANE_RICH        |               0.004712273406 |         0.1 MPa | 19.9 MPa below minimum; composition below 0.01     |
| PH_LIQUID_EQUAL       |                          0.5 |          30 MPa | 5 MPa above maximum inlet pressure                 |
| Bubble/dew challenges | 0.214–0.5 when liquid exists |           6 MPa | 14 MPa below minimum; T/flow also fail in cases    |

The additional M19 compatibility case uses actual M17 PT separation from 30 MPa,
300 K, z=0.25, F=100 mol/s to 20 MPa and 300 K. Its full-liquid output directly
matches the independently qualified new pump inlet. Pump recomputation of actual
separator H has **zero extensive residual** under the same convention. The study
retains actual H in the artifact, then projects unchanged PT/rates into the pump's
PT-only input API and requires H agreement before claiming compatibility.
This is a single-liquid separator pass-through, not evidence of direct pumping
of representative fractionated low-pressure products, nor retroactive expansion
of the frozen M17 matrix. Production mixed networks remain unavailable.

Supporting those fractionated products requires new low-pressure liquid, saturation
margin/witness and inverse-path qualification (and often lower T, flow or methane
fraction). A 16 MPa auxiliary witness cannot simply be reused as a lower-pressure
liquid-service guarantee. M19 does not solve that integration gap.

Reproduction commands, exact artifact sources and implementation validation are
linked from the benchmark README and MILESTONE_19.md. Human acceptance was pending
at qualification handoff; Giovani Nunes subsequently reported acceptance on
2026-10-01, America/Sao_Paulo. See the dated acceptance entry in MILESTONE_19.md.
This status update does not change the qualification evidence or limits.
