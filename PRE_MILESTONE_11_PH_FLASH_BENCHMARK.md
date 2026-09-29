# Pre-Milestone 11 — Independent PH Flash Benchmark

Independent reference completed on 2026-09-29. **Human review remains pending.**
This is benchmark qualification, not production Milestone 11.

## Scope and repository boundary

Only this report and the new `benchmarks/peng_robinson_ph/` files were created.
No existing tracked file changed. In particular, production PR/caloric code,
PropertyPackage, requirements/flowsheet/results contracts, fixtures, M8/M10
frozen references, UI and process equipment remain unchanged. The initial tree
was clean. No live LLM/provider or runtime network call was made.

M8 supplies the independently qualified PR/PT identity; pre-M10 supplies the
independent caloric equations, Cp data and reference convention. M10 production
outputs are regression evidence only, never an input to this oracle. M9 remains
PT/material separation with rigorous energy and duty unavailable. No Stream
Table enrichment occurs.

## Thermodynamic identity, data and units

Canonical PR1976: Ωa = 0.45724, Ωb = 0.07780 and
R = 8.31446261815324 J/(mol K). The independent implementation configures these
coefficients explicitly in Thermo, preserving the M8 convention. The component
constants correspond to `riogineer_components@1.0`, without importing production.

| Component | MW (kg/kmol) | Tc (K)  | Pc (Pa absolute)  | ω                  |
| --------- | ------------ | ------- | ----------------- | ------------------ |
| methane   | 16.0428      | 190.564 | 4599200.0         | 0.01142            |
| n_hexane  | 86.17536     | 507.82  | 3044115.328359688 | 0.3003189315498438 |

Overall z, liquid x and vapor y are molar fractions. Beta is the vapor molar
fraction of total feed: zero for single liquid, one for single vapor. Absent
phases have no fabricated composition, root or caloric data. All primary binary
states use z = [0.5, 0.5]. BIPs are explicitly symmetric zero kij, inherited from
the M8 mathematical benchmark, **not fitted physical interaction data**.

Cp/R = A + B·T + C·T² + D·T³ + E·T⁴. The frozen coefficients are the Poling rows
from Chemicals 1.5.2, originally Poling et al., _The Properties of Gases and
Liquids_, fifth edition (2001). Existing pre-M10 provenance and licensing remain
unchanged; the PH-local notices retain attribution. No mutable online endpoint
is consulted.

| Component | A, B, C, D, E                                          | Valid T (K) |
| --------- | ------------------------------------------------------ | ----------- |
| methane   | [4.568, -0.008975, 3.631e-05, -3.407e-08, 1.091e-11]   | 50–1000     |
| n_hexane  | [8.831, -0.000166, 0.00014302, -1.8314e-07, 7.124e-11] | 200–1000    |

The common pure ideal-gas reference is h = s = 0 at 298.15 K and 101325 Pa.
Formation properties are excluded. Ideal h integrates Cp from that temperature;
ideal s integrates Cp/T, then adds −R ln(P/101325) and ideal mixing
−R Σqᵢ ln(qᵢ), with zero-component terms equal to zero. Each phase uses its own
composition. PR residual properties are relative to ideal gas at the same T/P/q.
With L = ln[(Z+(1+√2)B)/(Z+(1−√2)B)]:

- h_res = R·T·(Z−1) + (T·da/dT−a)·L/(2√2·b).
- s_res = R·ln(Z−B) + (da/dT)·L/(2√2·b).

The analytic alpha/mixing derivatives and exact formulas are reused from the
unchanged independent pre-M10 `equations.py`. Total phase h/s equal ideal plus
residual. The reference is shared by `riogineer_caloric@1.0`; target enthalpies
are **not universal absolute thermochemical enthalpies**.

T is K; P is Pa absolute; every H target, phase h and PH residual is J/mol.
Entropy is retained in J/(mol K) as diagnostic evidence only. No PS inversion,
mass-specific PH target or process energy calculation is implemented.

## Independent implementation and reproduction

`equilibrium.py` constructs the independent Thermo stack via the benchmark-only
pre-M10 helper. At **every** temperature it explicitly calls
`FlashVL.flash_TP_stability_test`, which performs Michelsen stability testing
before phase selection/splitting. It validates phase amounts, component material
reconstruction (1e-10 absolute) and two-phase log-fugacity residuals (1e-9).
Liquid caloric values use x and the liquid root; vapor values use y and the vapor
root. Library H/S are audited against direct benchmark equations at every trial,
using unchanged pre-M10 tolerances. No production module is imported.

`solver.py` receives only P, z, target molar H and numerical controls. It cannot
receive the forward reference temperature. Its residual is
F(T) = H_eq(T,P,z) − H_target. Single-phase H_eq is that phase's h; for VLE,
H_eq = (1−beta)·h_L + beta·h_V. `reference.py` first creates independent forward
states, then invokes this inverse solver without their temperature. Existing
canonical H targets are read at full precision from the frozen pre-M10 reference;
forward phase state/caloric comparisons must pass before inversion.

The already isolated `.local/pre-m8-venv` was reused (Python 3.10.10).

| Package   | Version |
| --------- | ------- |
| chemicals | 1.5.2   |
| fluids    | 1.3.1   |
| numpy     | 2.2.6   |
| scipy     | 1.15.3  |
| thermo    | 0.6.0   |

The local `requirements.txt` retains the complete prior independent stack pins,
including transitive packages and teqp 0.23.1; teqp is not called by PH inversion.
There are no production dependency changes. Existing reference JSON and helper
SHA-256 hashes are stored under `metadata.source_sha256`.

From the repository root:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_ph/reference.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ph -p 'test_*.py' -v
```

Ordinary execution recomputes and compares; it never rewrites the frozen file.
The explicit maintainer `--write` flag generates the new PH artifact. No server,
Node process or internet connection is required. Human review of the benchmark
must occur before production M11 authorization.

## Domain, brackets and solver policy

Every acceptance case searches **200–500 K**, inside the shared 200–1000 K Cp
range. The binary needs the intersection of both component ranges; the pure
vectors conservatively use that same domain. No extrapolation occurs. The
interface rejects bounds outside 200–1000 K, but this benchmark qualifies only
the selected cases/domains, not all possible states up to 1000 K.

A deterministic 128-point inclusive uniform grid evaluates stable equilibrium
at every point. It does not contain 300 K, 280 K, 350 K or 400 K. All adjacent
valid sign changes are investigated; there is no case-specific initial guess or
frozen answer shortcut. An exactly zero grid residual can be a root only after
fresh final evaluation. Near-zero nonzero values remain bracket evidence, not
accepted grid approximations. Any failed grid point makes uniqueness unresolved
and fails the solve: the algorithm never bridges an invalid thermodynamic hole.

SciPy Brent (`brentq`) solves each bracket with xtol = 1e-10 K,
rtol = 1e-14 and at most 100 iterations. A new independent forward evaluation
at the returned temperature supplies the published result. Final absolute
|H_eq−H_target| must be ≤ 1e-6 J/mol regardless of internal convergence.
The normalized signed residual uses max(|H_target|, 1 J/mol) as denominator.
Multiple residual-qualified roots return `multiple_ph_roots`, without selecting
one. Scan/root/final evaluation counts, root trials, brackets, F endpoints,
iterations and monotonicity evidence are frozen separately.

The scan is evidence for the sampled domain, not a proof that no narrow or
tangential root exists between arbitrary grid points. Critical/retrograde/global
phase-envelope claims are explicitly excluded.

## Frozen identity and schema

`independent_methane_nhexane_pr_ph@1.0` is stored at
`benchmarks/peng_robinson_ph/methane_nhexane_pr_ph_reference.json`.
It contains metadata, quantity tolerances, 29 positive cases with separate input,
forward and inverse sections, complete scans, sensitivity investigations,
continuity refinements, an excluded pure-saturation gap and eight negative
specifications. Each present phase retains composition, Z, MW, ideal/residual/total
H and S, and direct-equation audit values. Failed results have no successful
`solution`; partial values stay explicitly in diagnostics. No timestamps enter
numerical serialization. Two full fresh builds must match frozen bytes exactly.

## Acceptance tolerances and evidence

Comparisons use atol + rtol·|reference|; recovered T and final H residual have
absolute limits. Tighter solver controls than comparison tolerances avoid
round-trip amplification. Values near zero retain meaningful absolute limits.

| Quantity    | atol  | rtol  |
| ----------- | ----- | ----- |
| H_residual  | 1e-06 | 0     |
| T           | 1e-07 | 0     |
| Z           | 1e-10 | 1e-09 |
| beta        | 1e-09 | 1e-09 |
| composition | 1e-09 | 1e-09 |
| h           | 1e-07 | 1e-11 |

The tolerance study uses xtol 1e-6, 1e-8, 1e-10 and 1e-12 K on A/B/C. At
1e-6 K, B internally converges but leaves +3.85434614e-5 J/mol, so the independent
final residual gate rejects it. At 1e-10 K all canonical cases pass; tightening
to 1e-12 changes no classification and gives B an exactly zero computed residual.
The final limits follow this independent evidence, not future production output.

| Maximum across 29 primary Brent round trips | Absolute error    |
| ------------------------------------------- | ----------------- |
| T                                           | 1.50635059981e-11 |
| beta                                        | 6.52993284445e-14 |
| composition                                 | 5.45952172359e-14 |
| Z                                           | 1.6320278462e-14  |
| h                                           | 2.77941580862e-09 |
| H residual (J/mol)                          | 2.56113708019e-09 |

## Round-trip temperature matrix

H is J/mol; P is Pa absolute; T and ΔT are K. All rows pass.

| Case                             | P        | H target       | T ref         | T PH          | ΔT           | Phase         | H residual   |
| -------------------------------- | -------- | -------------- | ------------- | ------------- | ------------ | ------------- | ------------ |
| PH_A_SINGLE_LIQUID               | 30000000 | -16303.9480247 | 300           | 300           | +5.68434e-14 | single_liquid | +7.27596e-12 |
| PH_B_VAPOR_LIQUID                | 300000   | -14232.3399985 | 300           | 300           | -1.50635e-11 | vapor_liquid  | -2.56114e-09 |
| PH_C_SINGLE_VAPOR                | 1000     | 164.368643728  | 300           | 300           | +0           | single_vapor  | +0           |
| PH_T280_L                        | 30000000 | -18660.8082789 | 280           | 280           | -5.68434e-14 | single_liquid | +0           |
| PH_T280_VL                       | 300000   | -17232.3717045 | 280           | 280           | +0           | vapor_liquid  | +0           |
| PH_T280_V                        | 1000     | -1591.31676    | 280           | 280           | +0           | single_vapor  | +0           |
| PH_T350_L                        | 30000000 | -10017.8202563 | 350           | 350           | -5.68434e-14 | single_liquid | +5.45697e-12 |
| PH_T350_VL                       | 1000000  | -7277.0837901  | 350           | 350           | -1.25624e-11 | vapor_liquid  | -2.55113e-09 |
| PH_T350_V                        | 1000     | 4910.98206552  | 350           | 350           | +0           | single_vapor  | +0           |
| PH_T400_L                        | 30000000 | -3155.14014951 | 400           | 400           | +0           | single_liquid | +0           |
| PH_T400_VL                       | 3000000  | -167.032023537 | 400           | 400           | +5.68434e-13 | vapor_liquid  | +1.15961e-10 |
| PH_T400_V                        | 1000     | 10182.6432602  | 400           | 400           | +0           | single_vapor  | +0           |
| PH_PURE_METHANE_280K_100000PA    | 100000   | -663.088822474 | 280           | 280           | -5.68434e-14 | single_vapor  | -1.81899e-12 |
| PH_PURE_METHANE_300K_100000PA    | 100000   | 48.2859223994  | 300           | 300           | +0           | single_vapor  | +0           |
| PH_PURE_METHANE_350K_100000PA    | 100000   | 1898.37875997  | 350           | 350           | +0           | single_vapor  | +0           |
| PH_PURE_METHANE_400K_100000PA    | 100000   | 3867.28619282  | 400           | 400           | -5.68434e-14 | single_vapor  | -3.18323e-12 |
| PH_PURE_N_HEXANE_280K_1000PA     | 1000     | -2540.61430877 | 280           | 280           | +5.68434e-14 | single_vapor  | +7.27596e-12 |
| PH_PURE_N_HEXANE_280K_30000000PA | 30000000 | -31906.849836  | 280           | 280           | +0           | single_liquid | +0           |
| PH_PURE_N_HEXANE_300K_1000PA     | 1000     | 261.530577736  | 300           | 300           | +0           | single_vapor  | +0           |
| PH_PURE_N_HEXANE_300K_30000000PA | 30000000 | -28324.9107896 | 300           | 300           | -5.68434e-14 | single_liquid | -7.27596e-12 |
| PH_PURE_N_HEXANE_350K_1000PA     | 1000     | 7908.86889062  | 350           | 350           | -5.68434e-14 | single_vapor  | -7.27596e-12 |
| PH_PURE_N_HEXANE_350K_30000000PA | 30000000 | -18746.9125474 | 350           | 350           | -1.13687e-13 | single_liquid | -1.09139e-11 |
| PH_PURE_N_HEXANE_400K_1000PA     | 1000     | 16486.3425456  | 400           | 400           | -5.68434e-14 | single_vapor  | +0           |
| PH_PURE_N_HEXANE_400K_30000000PA | 30000000 | -8243.45942111 | 400           | 400           | +0           | single_liquid | +0           |
| PH_BUBBLE_BELOW                  | 6000000  | -25453.3357857 | 230.617554351 | 230.617554351 | -2.84217e-14 | single_liquid | +0           |
| PH_BUBBLE_ABOVE                  | 6000000  | -25321.1064842 | 231.617554351 | 231.617554351 | +1.42109e-13 | vapor_liquid  | -2.43745e-10 |
| PH_DEW_BELOW                     | 6000000  | 13176.5020618  | 467.765889532 | 467.765889532 | +1.7053e-13  | vapor_liquid  | +3.63798e-12 |
| PH_DEW_ABOVE                     | 6000000  | 13402.9489954  | 468.765889532 | 468.765889532 | +5.45697e-12 | single_vapor  | +8.62201e-10 |
| PH_NEAR_ZERO_H                   | 1000     | 0.389734586687 | 298.17        | 298.17        | +0           | single_vapor  | +0           |

The nine additional binary states reuse the pre-M10 280/350/400 K liquid,
vapor and two-phase references. Pure methane covers all four 280/300/350/400 K
states at 100000 Pa; pure n-hexane covers those temperatures in vapor at 1000 Pa
and liquid at 30 MPa. The near-zero target is +0.389734586687 J/mol at 298.17 K.
All recover the independent forward phase and phase caloric state.

## Phase recovery

Composition errors are maximum absolute component molar-fraction differences;
Z errors are absolute. Full single-phase forward/inverse data are in JSON.

| Case              | beta ref         | beta PH          | max x error       | max y error       | ZL error          | ZV error          |
| ----------------- | ---------------- | ---------------- | ----------------- | ----------------- | ----------------- | ----------------- |
| PH_B_VAPOR_LIQUID | 0.534642510224   | 0.534642510224   | 2.1302404285e-15  | 4.8960835386e-14  | 4.63171168086e-16 | 1.66533453694e-15 |
| PH_T280_VL        | 0.506800542426   | 0.506800542426   | 0                 | 0                 | 0                 | 0                 |
| PH_T350_VL        | 0.569012139921   | 0.569012139921   | 3.5527136788e-15  | 5.45952172359e-14 | 5.27355936697e-16 | 6.2172489379e-15  |
| PH_T400_VL        | 0.58581698199    | 0.58581698199    | 3.33066907388e-16 | 2.33146835171e-15 | 1.66533453694e-16 | 7.77156117238e-16 |
| PH_BUBBLE_ABOVE   | 0.00573494724846 | 0.00573494724839 | 3.29736238314e-14 | 9.97465998687e-18 | 7.38298311376e-15 | 9.99200722163e-16 |
| PH_DEW_BELOW      | 0.986874454196   | 0.986874454196   | 8.881784197e-16   | 1.22124532709e-15 | 7.21644966006e-16 | 1.55431223448e-15 |

| Single-phase case                | Expected = recovered | Z error           |
| -------------------------------- | -------------------- | ----------------- |
| PH_A_SINGLE_LIQUID               | single_liquid        | 0                 |
| PH_C_SINGLE_VAPOR                | single_vapor         | 0                 |
| PH_T280_L                        | single_liquid        | 2.22044604925e-16 |
| PH_T280_V                        | single_vapor         | 0                 |
| PH_T350_L                        | single_liquid        | 4.4408920985e-16  |
| PH_T350_V                        | single_vapor         | 0                 |
| PH_T400_L                        | single_liquid        | 0                 |
| PH_T400_V                        | single_vapor         | 0                 |
| PH_PURE_METHANE_280K_100000PA    | single_vapor         | 0                 |
| PH_PURE_METHANE_300K_100000PA    | single_vapor         | 0                 |
| PH_PURE_METHANE_350K_100000PA    | single_vapor         | 0                 |
| PH_PURE_METHANE_400K_100000PA    | single_vapor         | 1.11022302463e-16 |
| PH_PURE_N_HEXANE_280K_1000PA     | single_vapor         | 0                 |
| PH_PURE_N_HEXANE_280K_30000000PA | single_liquid        | 0                 |
| PH_PURE_N_HEXANE_300K_1000PA     | single_vapor         | 0                 |
| PH_PURE_N_HEXANE_300K_30000000PA | single_liquid        | 2.22044604925e-16 |
| PH_PURE_N_HEXANE_350K_1000PA     | single_vapor         | 0                 |
| PH_PURE_N_HEXANE_350K_30000000PA | single_liquid        | 2.22044604925e-16 |
| PH_PURE_N_HEXANE_400K_1000PA     | single_vapor         | 0                 |
| PH_PURE_N_HEXANE_400K_30000000PA | single_liquid        | 0                 |
| PH_BUBBLE_BELOW                  | single_liquid        | 5.55111512313e-17 |
| PH_DEW_ABOVE                     | single_vapor         | 1.6320278462e-14  |
| PH_NEAR_ZERO_H                   | single_vapor         | 0                 |

## Enthalpy recovery

All quantities below are J/mol. Acceptance is |residual| ≤ 1e-6.

| Case                             | Target         | Fresh H eq     | Signed residual | Absolute residual | h L            | h V            | Pass |
| -------------------------------- | -------------- | -------------- | --------------- | ----------------- | -------------- | -------------- | ---- |
| PH_A_SINGLE_LIQUID               | -16303.9480247 | -16303.9480247 | +7.27596e-12    | 7.27595761418e-12 | -16303.9480247 | —              | PASS |
| PH_B_VAPOR_LIQUID                | -14232.3399985 | -14232.3399985 | -2.56114e-09    | 2.56113708019e-09 | -30575.8188227 | -6.8339184987  | PASS |
| PH_C_SINGLE_VAPOR                | 164.368643728  | 164.368643728  | +0              | 0                 | —              | 164.368643728  | PASS |
| PH_T280_L                        | -18660.8082789 | -18660.8082789 | +0              | 0                 | -18660.8082789 | —              | PASS |
| PH_T280_VL                       | -17232.3717045 | -17232.3717045 | +0              | 0                 | -34140.9330612 | -777.588034534 | PASS |
| PH_T280_V                        | -1591.31676    | -1591.31676    | +0              | 0                 | —              | -1591.31676    | PASS |
| PH_T350_L                        | -10017.8202563 | -10017.8202563 | +5.45697e-12    | 5.45696821064e-12 | -10017.8202563 | —              | PASS |
| PH_T350_VL                       | -7277.0837901  | -7277.08379011 | -2.55113e-09    | 2.55113263847e-09 | -20156.2201518 | 2477.98298395  | PASS |
| PH_T350_V                        | 4910.98206552  | 4910.98206552  | +0              | 0                 | —              | 4910.98206552  | PASS |
| PH_T400_L                        | -3155.14014951 | -3155.14014951 | +0              | 0                 | -3155.14014951 | —              | PASS |
| PH_T400_VL                       | -167.032023537 | -167.032023537 | +1.15961e-10    | 1.15960574476e-10 | -8218.37204403 | 5525.40846766  | PASS |
| PH_T400_V                        | 10182.6432602  | 10182.6432602  | +0              | 0                 | —              | 10182.6432602  | PASS |
| PH_PURE_METHANE_280K_100000PA    | -663.088822474 | -663.088822474 | -1.81899e-12    | 1.81898940355e-12 | —              | -663.088822474 | PASS |
| PH_PURE_METHANE_300K_100000PA    | 48.2859223994  | 48.2859223994  | +0              | 0                 | —              | 48.2859223994  | PASS |
| PH_PURE_METHANE_350K_100000PA    | 1898.37875997  | 1898.37875997  | +0              | 0                 | —              | 1898.37875997  | PASS |
| PH_PURE_METHANE_400K_100000PA    | 3867.28619282  | 3867.28619282  | -3.18323e-12    | 3.18323145621e-12 | —              | 3867.28619282  | PASS |
| PH_PURE_N_HEXANE_280K_1000PA     | -2540.61430877 | -2540.61430877 | +7.27596e-12    | 7.27595761418e-12 | —              | -2540.61430877 | PASS |
| PH_PURE_N_HEXANE_280K_30000000PA | -31906.849836  | -31906.849836  | +0              | 0                 | -31906.849836  | —              | PASS |
| PH_PURE_N_HEXANE_300K_1000PA     | 261.530577736  | 261.530577736  | +0              | 0                 | —              | 261.530577736  | PASS |
| PH_PURE_N_HEXANE_300K_30000000PA | -28324.9107896 | -28324.9107896 | -7.27596e-12    | 7.27595761418e-12 | -28324.9107896 | —              | PASS |
| PH_PURE_N_HEXANE_350K_1000PA     | 7908.86889062  | 7908.86889062  | -7.27596e-12    | 7.27595761418e-12 | —              | 7908.86889062  | PASS |
| PH_PURE_N_HEXANE_350K_30000000PA | -18746.9125474 | -18746.9125474 | -1.09139e-11    | 1.09139364213e-11 | -18746.9125474 | —              | PASS |
| PH_PURE_N_HEXANE_400K_1000PA     | 16486.3425456  | 16486.3425456  | +0              | 0                 | —              | 16486.3425456  | PASS |
| PH_PURE_N_HEXANE_400K_30000000PA | -8243.45942111 | -8243.45942111 | +0              | 0                 | -8243.45942111 | —              | PASS |
| PH_BUBBLE_BELOW                  | -25453.3357857 | -25453.3357857 | +0              | 0                 | -25453.3357857 | —              | PASS |
| PH_BUBBLE_ABOVE                  | -25321.1064842 | -25321.1064842 | -2.43745e-10    | 2.43744580075e-10 | -25442.7101406 | -4238.7389189  | PASS |
| PH_DEW_BELOW                     | 13176.5020618  | 13176.5020618  | +3.63798e-12    | 3.63797880709e-12 | 9268.87369562  | 13228.4739767  | PASS |
| PH_DEW_ABOVE                     | 13402.9489954  | 13402.9489954  | +8.62201e-10    | 8.62200977281e-10 | —              | 13402.9489954  | PASS |
| PH_NEAR_ZERO_H                   | 0.389734586687 | 0.389734586687 | +0              | 0                 | —              | 0.389734586687 | PASS |

## Canonical brackets and H(T) investigation

### PH_A_SINGLE_LIQUID

Bracket [299.2125984252, 301.57480314961] K; F endpoints [-94.449526820106, +189.31285959145] J/mol. Scan: **increasing**; one sign bracket and one accepted root.

| T (K)         | Phase         | beta | H eq (J/mol)   | F (J/mol)      |
| ------------- | ------------- | ---- | -------------- | -------------- |
| 296.850393701 | single_liquid | 0    | -16680.920834  | -376.972809317 |
| 299.212598425 | single_liquid | 0    | -16398.3975515 | -94.4495268201 |
| 301.57480315  | single_liquid | 0    | -16114.6351651 | 189.312859591  |
| 303.937007874 | single_liquid | 0    | -15829.628559  | 474.319465657  |

Evaluations: scan 128, root 6, fresh final 1, total 135; root iterations 5.

### PH_B_VAPOR_LIQUID

Bracket [299.2125984252, 301.57480314961] K; F endpoints [-133.12810339261, +270.93386833057] J/mol. Scan: **increasing**; one sign bracket and one accepted root.

| T (K)         | Phase        | beta           | H eq (J/mol)   | F (J/mol)      |
| ------------- | ------------ | -------------- | -------------- | -------------- |
| 296.850393701 | vapor_liquid | 0.528687812148 | -14756.0068648 | -523.666866271 |
| 299.212598425 | vapor_liquid | 0.533083529524 | -14365.4681019 | -133.128103393 |
| 301.57480315  | vapor_liquid | 0.537910494776 | -13961.4061302 | 270.933868331  |
| 303.937007874 | vapor_liquid | 0.543213096801 | -13542.6200371 | 689.719961477  |

Evaluations: scan 128, root 6, fresh final 1, total 135; root iterations 5.

### PH_C_SINGLE_VAPOR

Bracket [299.2125984252, 301.57480314961] K; F endpoints [-70.638843640941, +141.65414728727] J/mol. Scan: **increasing**; one sign bracket and one accepted root.

| T (K)         | Phase        | beta | H eq (J/mol)   | F (J/mol)      |
| ------------- | ------------ | ---- | -------------- | -------------- |
| 296.850393701 | single_vapor | 1    | -117.435197723 | -281.803841452 |
| 299.212598425 | single_vapor | 1    | 93.7298000874  | -70.6388436409 |
| 301.57480315  | single_vapor | 1    | 306.022791016  | 141.654147287  |
| 303.937007874 | single_vapor | 1    | 519.446857139  | 355.078213411  |

Evaluations: scan 128, root 5, fresh final 1, total 134; root iterations 4.

Across 200–500 K, A stays liquid; B and C cross from VLE to vapor. All three
canonical scans are increasing. No multiple roots were found for any selected
positive case. An explicit synthetic nonmonotonic test checks refusal to choose
between two roots; it is a solver-policy test, not a physical benchmark.

A 191-point alternative grid (also avoiding 300 K) and bisection using direct-equation enthalpy both
recover canonical roots within the same tolerances. ±10 J/mol perturbations
move recovered T in the expected local direction in all three cases. The
additional binary matrix verifies inversion away from 300 K and changing
beta/x/y/phase enthalpies at multiple two-phase temperatures.

## Boundary and continuity evidence

At 6 MPa, independent PVF boundary location gives the bubble and dew temperatures
below. Four forward cases lie ±0.5 K from these boundaries, avoiding exact
saturation and critical degeneracy. The bubble-above and dew-below root brackets
actually contain two phase classifications, as do their recorded root trials.
These are local transition checks, not general envelope qualification.

| Boundary        | P (Pa)  | T (K)         | H span at ±1 K | H span at ±0.00001 K |
| --------------- | ------- | ------------- | -------------- | -------------------- |
| bubble          | 6000000 | 231.117554351 | 263.940116986  | 0.00264987478295     |
| dew             | 6000000 | 468.265889532 | 451.925145993  | 0.00454006821019     |
| dew_at_1000Pa   | 1000    | 233.234113056 | 2491.92614266  | 0.0274365390069      |
| dew_at_300000Pa | 300000  | 353.643911183 | 970.111707049  | 0.00998281409647     |

The binary refinements use offsets 1, 0.1, 0.01, 0.001, 0.0001 and 0.00001 K.
Enthalpy spans shrink with the interval; successful stability/PT and caloric
checks support numerical continuity at this resolution. Canonical B/C dew
crossings were also refined. The 1000 Pa crossing has a steeper enthalpy slope: the initial ±0.0001 K span
was 0.27436 J/mol, above the diagnostic test limit of 0.1 J/mol. Refining to
±0.00001 K brought it below that unchanged limit; no thermodynamic tolerance
was weakened. There is no unexplained binary discontinuity.

Pure n-hexane at 1000 Pa instead has a **physical latent-heat discontinuity** in
a single-valued stable PT branch at 242.8283318534392 K. At ±0.0001 K the enthalpy
span is about 33798.083685 J/mol and does not vanish under refinement. At exact
saturation, P/T alone cannot choose the phase amount. A PH target inside this
latent gap needs a pure-coexistence lever rule; a scalar single-valued PT residual
cannot supply it. The midpoint-gap experiment fails the final residual gate
(`ph_nonconvergence`), publishing no normal state. It is explicitly excluded
from qualification. The selected pure-phase positive cases lie outside the gap.

## Failure taxonomy and negative evidence

No failure is converted to a zero enthalpy or valid-looking state.

| Frozen negative case | Expected = observed           |
| -------------------- | ----------------------------- |
| PH_BELOW_RANGE       | enthalpy_target_not_bracketed |
| PH_ABOVE_RANGE       | enthalpy_target_not_bracketed |
| PH_INVALID_P         | invalid_input                 |
| PH_INVALID_Z         | invalid_input                 |
| PH_UNSUPPORTED_WATER | unsupported_component         |
| PH_INVALID_BOUNDS    | temperature_domain_invalid    |
| PH_CP_EXTRAPOLATION  | temperature_domain_invalid    |
| PH_MAXITER           | ph_nonconvergence             |

Additional executed tests cover nonfinite H/P, invalid composition/controls,
unknown components, equal/reversed/nonfinite bounds, missing thermodynamic
scan points, PT failure inside a valid bracket, caloric failure on the fresh
final evaluation, multiple synthetic roots, and the pure latent gap.

The statuses are `invalid_input`, `unsupported_component`,
`temperature_domain_invalid`, `enthalpy_target_not_bracketed`,
`pt_evaluation_failure`, `caloric_evaluation_failure`, `multiple_ph_roots`, and
`ph_nonconvergence`. Scan invalidity is conservative: no unique root is certified
through a failed region. Diagnostic partial information is not a successful state.

## Automated checks and repository integrity

- New pre-M11 independent benchmark: **55 tests passed, 0 failed**.
- Determinism: two freshly recomputed complete references equal frozen bytes.
- Pre-M8 independent benchmark: **7 tests passed**.
- Pre-M10 independent caloric benchmark: **23 tests passed**.
- M8 production comparison: **122 comparisons passed**.
- M9 equilibrium separator integration: **7 tests passed**.
- M10 production caloric comparison: **1526 comparisons passed**.

The first M9 command from the repository root lacked the engine import path and
failed module discovery; rerunning from `engine/` passed all seven tests. This
was an invocation error, not a production assertion failure; no file was changed
to resolve it. The existing M10 comparison prints an outdated manual-pending
message; the already committed M10 documentation correctly records its human
validation. Neither existing file was edited in this benchmark task.

Regression commands, from the repository root unless indicated:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
```

From `engine/`:

```sh
.venv/bin/python -B -m unittest discover -s tests -p 'test_equilibrium_separator.py' -v
```

Documentation formatting, Python syntax and whitespace checks are separate from
thermodynamic gates. Git diff/integrity inspection confirms no existing tracked
file changed and no prior benchmark was regenerated. Full website/browser/build
validation is not needed for these isolated benchmark-only additions.

## Acceptance gates

| Gate           | Evidence / result                                                   |
| -------------- | ------------------------------------------------------------------- |
| Independence   | PASS: benchmark-only Thermo/direct equations; no production import  |
| Forward state  | PASS: independent PT/caloric forward states; old frozen comparisons |
| Round trip     | PASS: all 29 recovered T values                                     |
| Enthalpy       | PASS: fresh absolute residual checks                                |
| Phase          | PASS: every expected classification                                 |
| Two phase      | PASS: beta/x/y/Z/h independently compared                           |
| Single phase   | PASS: correct root, enthalpy and absent-phase semantics             |
| Pure component | PASS: four methane and eight n-hexane selected states               |
| Boundary       | PASS: four ±0.5 K states                                            |
| Phase change   | PASS: mixed-phase root brackets and trial histories                 |
| Bracketing     | PASS: all canonical F endpoints recorded                            |
| Multiple roots | PASS: unique on investigated grids; synthetic ambiguity rejected    |
| Domain         | PASS: no Cp extrapolation; invalid domains rejected                 |
| Failure        | PASS: explicit failures without successful state                    |
| Determinism    | PASS: two byte-identical reproductions                              |
| Regression     | PASS: prior references unchanged; selected prior checks pass        |

## Evidence-based recommendations for future M11

Recommend deterministic bracket discovery with exposed bounds, grid points,
phase transitions, F endpoints, iterations and evaluation counts. Start with
explicit user/qualification bounds intersected with active Cp validity; 200–500 K
is defensible for this matrix, not a universal default for all fluids. A future
solver should not silently extrapolate or assume the initial phase persists.

Brent is a suitable primary method, with bisection as a robust fallback policy;
this reference's two methods agree. A 128-point discovery scan, 100 iterations per
bracket, xtol 1e-10 K, rtol 1e-14, final |RH| ≤ 1e-6 J/mol and validation |ΔT| ≤
1e-7 K are supported here. For a unique bracket, a future evaluation budget can
reserve 128 scan + up to 102 solver calls + one final call (231); cap the global
budget explicitly and fail if exhausted. Multiple-bracket investigation needs a
separate total budget and must never select a root arbitrarily. Numerical limits
must remain configurable and tested, not inferred from hard-coded case identity.

Exact-grid roots require a fresh residual check. Near-zero H needs absolute
acceptance. A target outside the scanned stable H range should return an explicit
unbracketed status. Multiple brackets require all roots to be investigated; grid
refinement/domain qualification is needed before stronger uniqueness claims.
Any failed PT/caloric evaluation inside a candidate region must propagate its
stage and diagnostic rather than permit interpolation through the failure.

Future production should reuse the existing M8 PT property provider directly at
every T, then call M10 caloric evaluation **only after successful PT equilibrium**.
It should carry the final qualified PT state and phase caloric outputs together,
not reconstruct phase information separately. Preserve provider, component dataset,
caloric dataset/reference convention, BIP, input and solver-control provenance.
Keep P/z/molar-H input and success/failure results entirely in the property layer,
independent of equipment. The pure saturation latent gap needs a separately
specified coexistence policy; do not claim arbitrary pure-fluid PH coverage from
these selected pure-phase cases.

## Limitations and next step

This freezes selected methane/n-hexane zero-kij PH references under the existing
caloric convention. It does not qualify production PH, arbitrary mixtures,
physical nonzero BIPs, water/aqueous/VLLE/three-phase states, critical or near-critical
regions, general retrograde behavior, PS/UV/TV flash, reactive equilibrium,
formation enthalpy or rigorous equipment/network energy calculations.

A later isenthalpic valve would require qualified PH at the outlet pressure;
a duty-specified heater would require a consistent flow basis for H_out = H_in + Q.
Neither is implemented. A rigorous compressor also needs separately qualified
entropy/PS behavior; PH alone is insufficient. HEATER_1, COMPRESSOR_1 and SEP_PR_1
remain untouched, including the separator's energy-unavailable semantics.

If human review finds no discrepancy, recommend **Milestone 11 — Production
Standalone PH Flash Qualification**, tested against this frozen reference while
preserving M8 and M10. Process integration remains a later separately authorized
milestone. No production interface or PH/PS implementation was created here.

No unresolved discrepancy remains for the accepted reference matrix. The pure
latent gap and finite-grid uniqueness limitations are explicit scope exclusions.

**Independent pre-Milestone 11 PH benchmark completed. Human review of the
benchmark remains pending.**
