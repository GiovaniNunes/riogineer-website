# Pre-Milestone 10 — Independent Peng–Robinson Caloric Benchmark

## Scope and selected matrix (defined before freezing)

This benchmark-only study uses coefficient-configured Thermo 0.6.0 and an independent direct-equation implementation. It does not implement production caloric properties, PH/PS flash or equipment integration. All production files and the frozen M8 reference remain unchanged.

The selected binary is methane/n_hexane with z=[0.5,0.5] and temperature-independent kij=0. The exact M7 constants and canonical PR coefficients 0.45724/0.07780 are mandatory. The pre-existing isolated `.local/pre-m8-venv` is reused without package changes; dependency pins are copied into the new benchmark directory.

The selected reference convention is pure-component ideal-gas h=s=0 at 298.15 K and 101325 Pa. H/S are relative sensible properties, not formation-based or third-law absolute values. Mixture ideal entropy includes the pressure and ideal mixing terms. PR departures compare real and ideal gas at the same T/P/composition; total real-phase properties need not vanish at the reference conditions.

The following matrix was selected and documented before freezing:

- M8 A/B/C exactly: 300 K; 30000000 / 300000 / 1000 Pa. Caloric phase calculations use the frozen phase compositions and selected Z values are checked against M8.
- Additional binary temperatures: 280, 350 and 400 K. At each, 1000 Pa vapor and 30000000 Pa liquid; two-phase pressures 300000 Pa at 280 K, 1000000 Pa at 350 K, 3000000 Pa at 400 K. Library PT classification and ±2 K / ±5% P neighborhoods must retain these phase regimes before freezing.
- Pure methane: 280/300/350/400 K, 100000 Pa vapor. Pure n_hexane: the same temperatures, 1000 Pa vapor and 30000000 Pa liquid. Check minimum-Gibbs stable root selection, not root count.
- Dilute vapor: equimolar mixture and both pure components at 300 K and 1000/100/10/1 Pa. Departures should decrease toward zero; finite-pressure values are not set to zero.

Cp selection: explicitly select the Poling polynomial from Chemicals 1.5.2 through Thermo's `POLING_POLY` method. Methane validity is 50–1000 K; n_hexane 200–1000 K. No extrapolation, automatic method selection, formation constants or M5/M6 constant-Cp assumptions are used. The practical caloric matrix is 280–400 K; the broader correlation range is not blanket PR/process qualification.

## Evidence, independence and reproducibility

Qualified on 2026-09-29 as an independent numerical reference, not as production M10 functionality. M7 supplies exact molecular/critical constants; M8 supplies frozen A/B/C equilibrium; M9 supplies the prospective 1000 kmol/h flow basis only. M9's manually accepted energy-unavailable semantics remain correct.

Thermo 0.6.0 is suitable after inspection of its installed `PR`, `PRMIX`, `CEOSGas`, `CEOSLiquid` and `Phase` source: analytic attraction derivatives feed the generic cubic departure equations; phase H/S add Cp integrals, pressure and mixing contributions. Its default PR constants are not silently accepted. The benchmark subclasses override only coefficient configuration (including optimized coefficient products) to 0.45724/0.07780. Library EOS, roots, derivatives, departure functions and caloric methods are inherited unchanged. `equations.py` separately evaluates the canonical formulas using Python's standard library. It neither calls Thermo nor imports production equations.

The reference generator imports only the existing production **component data file** for an exact-constant assertion. It reads the frozen M8 JSON; no production equilibrium/caloric function supplies expected values. Library values are frozen only after direct-equation, numerical-quadrature and physical-limit checks pass. There were no material disagreements to resolve. A Gibbs/fugacity identity is auxiliary corroboration, not the definition of residual entropy.

`methane_nhexane_pr_caloric_reference.json` freezes inputs, units, coefficient data, reference convention, dependency versions, Python version, source SHA-256 hashes, quantity-specific tolerances and all phase records. Per-phase records include analytic alpha/derivatives, a/b/A/B/Z, entropy contributions, departure intermediates, independent comparisons, identities and mass-specific values. `cases`, `pure_states`, `low_pressure_states`, `cp_integration_checks` and `reference_shift_checks` separate the evidence. Double precision is retained through JSON serialization without decimal rounding. Human-readable tables below are formatted from that JSON.

The pre-existing isolated environment was reused without installation or mutation. Exact pins are in `benchmarks/peng_robinson_caloric/requirements.txt`; no production dependency changed. Python version at freeze: **3.10.10**. Thermo 0.6.0, Chemicals 1.5.2, Fluids 1.3.1, NumPy 2.2.6, SciPy 1.15.3, Pandas 2.3.3 and teqp 0.23.1 are pinned; teqp is retained for compatibility with the existing pre-M8 environment and does not calculate these caloric results. Remaining transitive pins are recorded in the requirements file.

## Constants, Cp source and redistribution

Component order everywhere is methane, n_hexane. Pressures are absolute.

| Component | CAS      | MW kg/kmol |    Tc K |             Pc Pa |              omega |
| --------- | -------- | ---------: | ------: | ----------------: | -----------------: |
| methane   | 74-82-8  |    16.0428 | 190.564 |         4599200.0 |            0.01142 |
| n_hexane  | 110-54-3 |   86.17536 |  507.82 | 3044115.328359688 | 0.3003189315498438 |

Cp source: B. E. Poling, J. M. Prausnitz and J. P. O'Connell, _The Properties of Gases and Liquids_, fifth edition (2001), polynomial values as distributed by **Chemicals 1.5.2** in `Heat Capacity/PolingDatabank.tsv`. Retrieved from that pinned offline distribution on 2026-09-29; the entire table's SHA-256 is recorded in JSON. Component CAS numbers, original coefficient values and ranges are frozen and checked against the distribution on every reproduction. The polynomial's unit normalization is Cp/R, not Cp itself; Thermo converts its coefficients to dimensional polynomial coefficients by multiplying by R. This transformation is independently checked. [Chemicals heat-capacity documentation](https://chemicals.readthedocs.io/chemicals.heat_capacity.html) describes the correlations and bundled sources; installed source hashes identify the exact implementation used rather than a mutable latest documentation version.

The published [Chemicals v1.5.2 license](https://raw.githubusercontent.com/CalebBell/chemicals/v1.5.2/LICENSE.txt) is MIT. This reference stores two numerical correlation records already distributed with that package, with source attribution and the package copyright/permission notice in `THIRD_PARTY_NOTICES.txt`. It does not copy the textbook or a proprietary commercial database. This is a reproducible open-source-distribution basis for these two records; it is not a claim that the original book or other Poling tables are freely redistributable. Thermo's distribution notice is retained as well.

For component i:

`Cp_i^ig(T) = R (c0 + c1*T + c2*T² + c3*T³ + c4*T⁴)`.

| Component |    c0 |   c1 K^-1 |    c2 K^-2 |     c3 K^-3 |   c4 K^-4 | Valid range K |
| --------- | ----: | --------: | ---------: | ----------: | --------: | ------------- |
| methane   | 4.568 | -0.008975 |  3.631e-05 |  -3.407e-08 | 1.091e-11 | 50–1000       |
| n_hexane  | 8.831 | -0.000166 | 0.00014302 | -1.8314e-07 | 7.124e-11 | 200–1000      |

Cp is in J/(mol K). The joint integration domain is 200–1000 K, including reference temperature 298.15 K. All acceptance states and their ±0.01 K derivative probes are inside it. Values outside the joint domain, nonfinite temperatures and out-of-domain integration reference temperatures are rejected; no extrapolation is enabled.

Alternatives assessed through the pinned package were TRC ideal-gas correlations (methane 50–5000 K, n_hexane 200–1500 K), NIST Shomate for methane (first interval begins at 298 K, so does not cover the requested 280 K point), and HEOS fits (methane 90.6941–625 K, n_hexane 177.83–600 K). These alternatives are not frozen or qualified here. The selected polynomial covers the full desired matrix without joining sources/reference conventions, has explicit offline coefficients and analytic integrals, and is transparent to audit. It is a documented engineering correlation rather than a new experimental validation. Its printed coefficient precision and lack of a quantified experimental uncertainty mean tight floating-point acceptance tolerances must not be interpreted as physical accuracy. Evaluate empirical accuracy separately before widening production scope. Within 280–400 K, direct evaluation and independent integration show no conditioning concern; no claim is made for extrapolation or near-critical accuracy.

## Reference state and ideal-gas equations

`T_h,ref = T_s,ref = 298.15 K`; `P_s,ref = 101325 Pa`. Each pure-component ideal gas has h=0 J/mol and s=0 J/(mol K) there. No standard formation enthalpies, third-law entropies, reaction data or library Hfs are added. This matches the inspected Thermo CEOS H/S methods and reference constants. Real-phase totals at the reference conditions generally are nonzero because of departures; an ideal mixture also has mixing entropy.

With coefficient index j=0..4:

`h_i^ig(T) = R Σ c_ij (T^(j+1) - Tref^(j+1))/(j+1)`

`s_i,T^ig(T) = R [c_i0 ln(T/Tref) + Σ(j=1..4) c_ij (T^j - Tref^j)/j]`

`h_ig(T,q) = Σ q_i h_i^ig(T)`

`s_ig(T,P,q) = Σ q_i s_i,T^ig(T) - R ln(P/Pref) - R Σ q_i ln(q_i)`.

Here q is z for a single phase, x for Case B liquid and y for Case B vapor. The pure-component standard-state constants are explicitly zero. The temperature, pressure and mixing entropy terms are frozen separately. The continuous limit `0 ln(0)=0` is used for pure-component checks. Ideal enthalpy contains no pressure term; tests verify composition weighting and pressure independence. Entropy pressure differences are checked against `-R ln(P2/P1)`. Cp integrals are compared against both library analytic integration and independent SciPy numerical quadrature, including reverse integration below 298.15 K.

## Canonical PR analytic derivatives and departures

Use R=8.31446261815324 J/(mol K), kappa_i=0.37464+1.54226 omega_i−0.26992 omega_i² and:

`g_i = 1 + kappa_i (1 - sqrt(T/Tc_i))`

`alpha_i = g_i²`; `dalpha_i/dT = -kappa_i*g_i/sqrt(T*Tc_i)`

`a0_i = 0.45724 R² Tc_i²/Pc_i`; `a_i(T) = a0_i alpha_i`

`da_i/dT = a0_i dalpha_i/dT`; `b_i = 0.07780 R Tc_i/Pc_i`

`a_mix = Σ_i Σ_j q_i q_j sqrt(a_i a_j) (1-kij)`; `b_mix = Σ_i q_i b_i`

`da_mix/dT = Σ_i Σ_j q_i q_j sqrt(a_i a_j) (1-kij)/2 * [(da_i/dT)/a_i + (da_j/dT)/a_j]`.

The full symmetric BIP matrix is zero, with zero diagonal, explicitly representing the M8 zero-kij mathematical benchmark rather than calibrated mixture data. BIPs are constant, so their temperature derivative is zero. A future temperature-dependent BIP would add `-Σ q_i q_j sqrt(a_i a_j) dkij/dT`; that capability is not qualified here.

`A = a_mix P/(RT)²`; `B = b_mix P/(RT)`; `Z = PV/(RT)`.

Define `L_PR = ln[(Z+(1+sqrt(2))B)/(Z+(1-sqrt(2))B)]`. Then:

`h_res = RT(Z-1) + (T da_mix/dT - a_mix)/(2 sqrt(2) b_mix) * L_PR`

`s_res = R ln(Z-B) + (da_mix/dT)/(2 sqrt(2) b_mix) * L_PR`

`h = h_ig + h_res`; `s = s_ig + s_res`.

Residual/departure here means real minus ideal gas **at the same T, P and molar composition**. Thermo's `H_dep`/`S_dep` are mapped to this definition and verified by the equations; the logarithmic Z term is essential to the entropy mapping. Direct evaluation uses `log1p` for dilute-gas numerical conditioning. Entropy is evaluated from its own equation, not inferred from a Gibbs expression.

The independent library analytically evaluates da/dT. Frozen diagnostic values include alpha, alpha derivative, pure a/da/b, mixed a/da/b, `T da/dT-a`, `L_PR` and `ln(Z-B)`. Auxiliary central differences with 0.01 K verify da/dT and the constant-P, fixed-composition identity `d(h_res)/dT = T d(s_res)/dT`. The fugacity-derived `RT Σ q_i ln(phi_i)` independently checks `h_res-T*s_res`. These checks do not replace analytic derivatives.

## Phase/root selection

The library repeats stability/PT equilibrium for all binary states. For A/B/C it must agree with the unchanged M8 classification, beta and phase compositions; caloric calculations then use the exact frozen M8 compositions. Selected Z must agree with the frozen phase Z. Case A uses the stable liquid root despite Z>1 at 30 MPa; a compressibility value alone is not a phase classifier. Case C uses the stable dilute vapor root. Case B evaluates `(T,P,x,Z_L)` and `(T,P,y,Z_V)` separately, never the overall z for both phase properties.

For every binary state, a 3×3 neighborhood at T±2 K and P×0.95/1/1.05 preserves its classification. These neighborhoods are local robustness checks, not a phase-envelope qualification. Pure-component checks compare PRMIX at a unit composition with the separate pure PR class and require the chosen root to have minimum residual Gibbs energy among available roots.

## Primary A/B/C numerical reference

All primary states are at 300 K. A: 30000000 Pa, B: 300000 Pa, C: 1000 Pa. Entries below are rounded display values; the JSON is authoritative.

| Case / phase | molar composition [CH4,nC6]               |                  Z |       MW kg/kmol |
| ------------ | ----------------------------------------- | -----------------: | ---------------: |
| A / liquid   | [0.5, 0.5]                                |   1.04595589143832 |         51.10908 |
| B / liquid   | [0.015619720085966004, 0.984380279914034] | 0.0154696638024269 | 85.0799090438878 |
| B / vapor    | [0.9216088074693791, 0.07839119253062085] |  0.988502784824013 | 21.5405750136253 |
| C / vapor    | [0.5, 0.5]                                |  0.999796670205194 |         51.10908 |

| Case / phase |       h_ig J/mol |       h_res J/mol |           h J/mol |    s_ig J/(mol K) |      s_res J/(mol K) |       s J/(mol K) |
| ------------ | ---------------: | ----------------: | ----------------: | ----------------: | -------------------: | ----------------: |
| A / liquid   | 165.754924217444 | -16469.7029488885 | -16303.9480246711 | -40.9970708365727 |    -31.1617304871616 | -72.1588013237344 |
| B / liquid   |  262.14522290762 | -30837.9640456226 |  -30575.818822715 | -7.47940068044494 |    -81.9732896688397 | -89.4526903492846 |
| B / vapor    | 81.8559700948787 | -88.6898885929172 | -6.83391849803849 | -6.46622934043482 |   -0.200006744134487 | -6.66623608456931 |
| C / vapor    | 165.754924217444 | -1.38628048905275 |  164.368643728391 |  44.7163306926656 | -0.00293047412368063 |  44.7134002185419 |

| Case / phase |  a_mix Pa m⁶/mol² | da_mix/dT Pa m⁶/(mol² K) |          T da/dT-a |                 L_PR |               ln(Z-B) |
| ------------ | ----------------: | -----------------------: | -----------------: | -------------------: | --------------------: |
| A / liquid   |  1.43289630014247 |     -0.00253169325874016 |  -2.19240427776452 |     1.44112048919448 |     -1.44457483298405 |
| B / liquid   |  3.69044019631824 |     -0.00647386819534053 |   -5.6326006549204 |     1.51990309866814 |     -5.93568124454168 |
| B / vapor    | 0.321315728653071 |    -0.000579664182181249 | -0.495214983307445 |   0.0113660465860105 |   -0.0156066546391984 |
| C / vapor    |  1.43289630014247 |     -0.00253169325874016 |  -2.19240427776452 | 7.63913318095234e-05 | -0.000230359977698584 |

### Case B aggregation and phase differences

Beta (vapor molar fraction) = **0.5346425102237959**; liquid molar fraction = **0.4653574897762041**.

- `overall_h_J_mol` = **-14232.3399985311 J/mol feed**.
- `overall_s_J_mol_K` = **-45.19153262866975 J/(mol feed K)**.
- `phase_difference_h_J_mol` = **30568.98490421692 J/mol**.
- `phase_difference_s_J_mol_K` = **82.78645426471533 J/(mol K)**.
- `benchmark_equilibrium_enthalpy_flow_W` = **-3953427.77736975 W**.

Use `h_eq=(1-beta)h_L+beta*h_V` and `s_eq=(1-beta)s_L+beta*s_V`; independent library equilibrium H/S agree with these sums. Entropy is extensive: summing entropy over phase amounts is sufficient. Each phase already includes its own compositional mixing entropy. No additional arbitrary phase-mixing entropy is added for macroscopically separate equilibrium phases. These mixture phase differences are not pure-component latent heats, and their ratio is not required to equal T.

The flow calculation uses only the M9 reference basis 1000 kmol/h. It is an equilibrium-state enthalpy flow under the stated reference convention, **not a separator duty**, since no inlet caloric state/difference has been specified for a process balance. It is not published into M9 results.

### Explicit mass-specific conversion

`MW_kg_per_mol = MW_kg_per_kmol / 1000`.

`h_J_per_kg = h_J_per_mol / MW_kg_per_mol`; likewise for s.

`Hdot_W = F_kmol_per_h * 1000 / 3600 * h_J_per_mol`.

Equivalently `Hdot_W = mdot_kg_per_h / 3600 * h_J_per_kg`. Dedicated functions and tests check both routes, including each Case B phase and the sum. Units must be converted dimensionally: 1 J/mol = 1000 J/kmol = 1 kJ/kmol, but no informal numeric equivalence is relied upon in code. Future MaterialStream design may choose J/kg for specific enthalpy and W for enthalpy flow; that design is not implemented here.

| Case B phase |            h J/kg |        s J/(kg K) | Hdot W at its phase share of 1000 kmol/h |
| ------------ | ----------------: | ----------------: | ---------------------------------------: |
| liquid       | -359377.662321461 | -1051.39616807937 |                        -3952412.85977518 |
| vapor        | -317.257941986959 | -309.473450933999 |                        -1014.91759457115 |

## Additional-temperature reference

All cases use overall z=[0.5,0.5]. Phase compositions, ideal/residual splits and diagnostic intermediates are retained at full precision in JSON.

| Case    | T K |   P Pa | phase  |           beta |               Z |        h J/mol |    s J/(mol K) |
| ------- | --: | -----: | ------ | -------------: | --------------: | -------------: | -------------: |
| T280_L  | 280 |  3e+07 | liquid |              0 |   1.08805474597 | -18660.8082789 | -80.2873995593 |
| T280_VL | 280 | 300000 | liquid | 0.506800542426 | 0.0161532680709 | -34140.9330612 | -101.826146895 |
| T280_VL | 280 | 300000 | vapor  | 0.506800542426 |  0.989616717648 | -777.588034534 | -10.4692101021 |
| T280_V  | 280 |   1000 | vapor  |              1 |  0.999754919172 |    -1591.31676 |  38.6584962591 |
| T350_L  | 350 |  3e+07 | liquid |              0 |   0.97623404143 | -10017.8202563 | -52.8012816256 |
| T350_VL | 350 |  1e+06 | liquid | 0.569012139921 | 0.0470355883909 | -20156.2201518 | -58.0980328399 |
| T350_VL | 350 |  1e+06 | vapor  | 0.569012139921 |  0.964367911024 |  2477.98298396 | -7.47870289673 |
| T350_V  | 350 |   1000 | vapor  |              1 |  0.999867999231 |  4910.98206552 |   59.326777938 |
| T400_L  | 400 |  3e+07 | liquid |              0 |  0.945991818659 | -3155.14014951 | -34.4906226726 |
| T400_VL | 400 |  3e+06 | liquid |  0.58581698199 |  0.134090854889 | -8218.37204403 | -28.1873115769 |
| T400_VL | 400 |  3e+06 | vapor  |  0.58581698199 |  0.906132969196 |  5525.40846766 | -6.70084432381 |
| T400_V  | 400 |   1000 | vapor  |              1 |  0.999911077338 |  10182.6432602 |    73.38967402 |

## Pure-component checks and ideal-gas limit

| Component | T K |   P Pa | phase  | Cp_ig J/(mol K) |     h_ig J/mol |   s_ig J/(mol K) |    h_res J/mol |   s_res J/(mol K) |
| --------- | --: | -----: | ------ | --------------: | -------------: | ---------------: | -------------: | ----------------: |
| methane   | 280 | 100000 | vapor  |    35.094168798 | -643.060098188 |   -2.11560756212 | -20.0287242856 |  -0.0489342376699 |
| methane   | 300 | 100000 | vapor  |   35.8509733884 |  66.2563456344 |   0.330981191506 |  -17.970423235 |  -0.0418276462309 |
| methane   | 350 | 100000 | vapor  |   38.0610484918 |  1912.32226276 |    6.01805299408 | -13.9435027898 |  -0.0293583367804 |
| methane   | 400 | 100000 | vapor  |   40.6279231687 |  3878.30029514 |    11.2646349794 | -11.0141023163 |  -0.0215091753957 |
| n_hexane  | 280 |   1000 | vapor  |   136.480903268 | -2536.51456618 |    29.6236414896 | -4.09974258241 | -0.00901700224021 |
| n_hexane  | 280 |  3e+07 | liquid |   136.480903268 | -2536.51456618 |   -56.0897600396 | -29370.3352698 |    -50.5477479416 |
| n_hexane  | 300 |   1000 | vapor  |   143.717681373 |    265.2535028 |    39.2858721889 |  -3.7229250648 | -0.00771599440705 |
| n_hexane  | 300 |  3e+07 | liquid |   143.717681373 |    265.2535028 |   -46.4275293403 | -28590.1642924 |    -47.8563052289 |
| n_hexane  | 350 |   1000 | vapor  |   162.213234646 |  7911.85306918 |    62.8238176437 | -2.98417855256 | -0.00542855325793 |
| n_hexane  | 350 |  3e+07 | liquid |   162.213234646 |  7911.85306918 |   -22.8895838855 | -26658.7656166 |    -41.9010804139 |
| n_hexane  | 400 |   1000 | vapor  |   180.844417591 |  16488.7881018 |    85.7019310843 | -2.44555614463 | -0.00398537544029 |
| n_hexane  | 400 |  3e+07 | liquid |   180.844417591 |  16488.7881018 | -0.0114704449047 | -24732.2475229 |    -36.7562441491 |

Pure entropy includes its pressure term; temperature-only increments are separately frozen in `cp_integration_checks`. Pure mixtures have exactly zero ideal mixing entropy.

| composition [CH4,nC6] | P Pa at 300 K |                Z−1 |       h_res J/mol |    s_res J/(mol K) |
| --------------------- | ------------: | -----------------: | ----------------: | -----------------: |
| [0.5, 0.5]            |          1000 | -0.000203329794806 |    -1.38628048905 |  -0.00293047412368 |
| [0.5, 0.5]            |           100 | -2.03304437537e-05 |   -0.138607772572 | -0.000292990364876 |
| [0.5, 0.5]            |            10 | -2.03301902646e-06 |  -0.0138605745615 | -2.92984662172e-05 |
| [0.5, 0.5]            |             1 | -2.03301649182e-07 | -0.00138605542952 | -2.92984091946e-06 |
| [1.0, 0.0]            |          1000 |  -2.1754483333e-05 |   -0.179652237918 | -0.000417962538441 |
| [1.0, 0.0]            |           100 | -2.17547899173e-06 |  -0.0179651760241 | -4.17959671662e-05 |
| [1.0, 0.0]            |            10 | -2.17548205783e-07 | -0.00179651712506 | -4.17959384933e-06 |
| [1.0, 0.0]            |             1 | -2.17548237202e-08 | -0.00017965170764 |  -4.1795935646e-07 |
| [0.0, 1.0]            |          1000 | -0.000564661294963 |     -3.7229250648 |  -0.00771599440705 |
| [0.0, 1.0]            |           100 | -5.64423338724e-05 |   -0.372124532085 | -0.000771138412444 |
| [0.0, 1.0]            |            10 | -5.64399567471e-06 |  -0.0372107751805 | -7.71092360078e-05 |
| [0.0, 1.0]            |             1 | -5.64397190428e-07 | -0.00372106073928 | -7.71087755258e-06 |

Case C already has small departures at 1000 Pa relative to typical liquid caloric scales, but is not exactly ideal. Reducing P to 1 Pa decreases absolute departures monotonically for the binary and both pure components; all satisfy |Z−1|<1e−6, |h_res|<0.01 J/mol and |s_res|<1e−4 J/(mol K). No finite-pressure value is forced to zero.

## Tolerances and observed numerical agreement

Acceptance is `|actual-reference| <= atol + rtol*|reference|`. Values below are numerical qualification tolerances, not Cp experimental uncertainties. They accommodate double-precision polynomial integration/subtraction, cubic root/departure evaluation and reproducibility, without reusing fugacity residual thresholds. Cp's printed coefficient precision defines the correlation being reproduced; it does not justify rounding or relaxing reproduction of that fixed polynomial.

| Quantity  | atol (quantity's SI units) |  rtol |
| --------- | -------------------------: | ----: |
| Cp        |                      1e-10 | 1e-12 |
| alpha     |                      1e-13 | 1e-12 |
| dalpha_dT |                      1e-15 | 1e-11 |
| a         |                      1e-13 | 1e-12 |
| da_dT     |                      1e-13 | 1e-10 |
| b         |                      1e-16 | 1e-12 |
| Z         |                      1e-10 | 1e-09 |
| h_ig      |                      1e-07 | 1e-11 |
| s_ig      |                      1e-09 | 1e-11 |
| h_res     |                      1e-07 | 1e-11 |
| s_res     |                      1e-09 | 1e-11 |
| h_total   |                      1e-07 | 1e-11 |
| s_total   |                      1e-09 | 1e-11 |

Observed maximum absolute library−direct-equation differences across all 40 phase evaluations:

| Quantity        | max absolute error |
| --------------- | -----------------: |
| Cp_ig_J_mol_K   |  2.84217094304e-14 |
| h_ig_J_mol      |  7.27595761418e-12 |
| s_ig_J_mol_K    |   3.5527136788e-14 |
| h_res_J_mol     |  1.81898940355e-11 |
| s_res_J_mol_K   |  2.55795384874e-13 |
| h_total_J_mol   |  2.54658516496e-11 |
| s_total_J_mol_K |  2.70006239589e-13 |

Maximum |dHres/dT−T dSres/dT| = 1.82694748219e-08 J/(mol K); threshold 2e−5 includes central-difference truncation and cancellation. Analytic da/dT versus its finite difference uses `1e−11 + 1e−8*|da/dT|`. Maximum Gibbs identity error = 1.1823431123e-11 J/mol.

The table's small absolute errors justify conservative numerical headroom (1e−7 J/mol enthalpy, 1e−9 J/(mol K) entropy), which remains far below correlation/model uncertainty. Default frozen numerical reproduction is tighter: absolute 1e−10 plus relative 1e−11. Metadata, coefficients and provenance match exactly; NaN and altered values are rejected. Frozen M8 Z agreement uses the listed Z tolerance and beta/compositions use 1e−9; M8 acceptance gates themselves are unchanged. Additional-state material closure is <1e−10. New caloric tolerances qualify this reference only; future production acceptance must retain the documented distinction between numerical and physical accuracy.

## Reference shifts and nonreactive energy accounting

Tests add a common C=12345 J/mol to every component's enthalpy reference. All phase molar enthalpies increase by C, so h_V−h_L and same-composition temperature differences are invariant. Total inlet/outlet enthalpy-flow shifts cancel when total molar flow closes.

For component-specific constants C_i, the phase shift is `Σ q_i C_i`. Because x≠y, h_V−h_L **need not** remain unchanged. A component-balanced process energy difference still cancels `Σ n_i C_i` between inlet and outlets. The benchmark demonstrates this with component shifts [10000,−3000] J/mol; this is an algebraic reference check, not a newly qualified separator duty.

The resulting phase-difference change is 11777.8581359844 J/mol, whereas the net inlet/outlet shift error at 1000 kmol/h is only 1.2631870858e-10 W.

A common entropy shift similarly leaves phase entropy differences unchanged. Component-dependent standard-state entropy choices alter phase differences when compositions differ; cross-library entropy comparisons require the same pure-component standards, pressure reference and mixing convention. Component-balanced total entropy-flow differences cancel consistent component reference shifts, but this does not grant interchangeability of arbitrary absolute entropy data or qualify entropy generation calculations.

For nonreactive heaters, coolers, compressors and separators, consistent sensible plus residual enthalpy differences are sufficient: formation terms cancel under component conservation. Adding formation enthalpies is unnecessary for that scope. Reactions, combustion, hydrogenation, heats of reaction, reaction equilibrium and formation Gibbs energies are explicitly unqualified.

## Recommended production architecture and PH/PS readiness

Recommend a separately versioned offline **caloric dataset** linked by stable component IDs to `riogineer_components@1.0`, with explicit units, Cp equation type, coefficients, ranges, source, reference convention and provenance. This preserves already-qualified M7 molecular constants and allows caloric revisions without silently relabeling them. Its identifier would be new and independently qualified; none is added to production now.

For the initial 280–400 K methane/n_hexane scope, recommend the explicit Cp/R polynomial qualified here, with analytic definite integrals and a hard range check. Wider ranges or accuracy requirements may warrant TRC/NASA/Shomate alternatives after separate qualification. Store coefficients offline rather than selecting a library's preferred method dynamically. Do not combine a different source's H/S offsets with these integrals without an explicit reference transformation.

The smallest future PropertyPackage extension is an optional, versioned phase-caloric capability, conceptually `phase_properties_TP`, accepting a qualified phase T/P/molar composition and phase/root identity and returning h/s with units, reference/dataset IDs, status and provenance. The provider owns both Cp and departure calculations; equipment must not contain caloric equations. PT stability/flash determines the actual phase(s) before enrichment, and failed/out-of-range caloric calls must not become numeric zero. No current interface, capability or contract is changed.

The equations and numerical references are sufficiently defined to start a separately authorized production **caloric implementation and comparison** milestone. They do not qualify a PH solver. Future PH requires:

1. Input P, overall z, target enthalpy on an explicit molar or mass basis, provider and matching reference convention.
2. At each trial T, run qualified stability/PT equilibrium and compute phase h at actual x/y, then h_eq by phase weighting.
3. Solve `f(T)=h_eq(T,P,z)-h_target=0` with bracketed root finding over the intersection of Cp/provider validity domains.
4. Permit phase classification to change. Bubble/dew boundaries can change the derivative; do not assume a single smooth phase equation or global monotonicity.
5. Detect invalid/no brackets, multiple candidate solutions, unstable roots, PT nonconvergence and out-of-range trials. Define separate enthalpy and temperature convergence tolerances and preserve diagnostics/reference consistency.

A PS solver would analogously use equilibrium entropy at each trial T with the same reference convention, domain and phase-boundary safeguards. It is not implemented. Near-critical, phase-boundary, target inversion and solver robustness matrices remain future work.

Future heater with specified outlet T: `Q=H_out−H_in`. With specified duty: `H_out=H_in+Q`, then a PH solution. HEATER_1 remains unchanged.

Future compressor: inlet entropy → PS isentropic outlet at P2 → enthalpy difference → isentropic efficiency → actual outlet enthalpy → PH outlet T. Replacing constant Cp alone is insufficient; the M6 compressor and its mechanical-efficiency semantics remain unchanged.

Future SEP_PR_1 could use `Q=H_vapor+H_liquid−H_in` for an isothermal flash only after inlet and outlet caloric states are qualified. Adiabatic temperature or specified-duty states require a PH-type solve. Current M9 heat duty, shaft work, enthalpy and rigorous phase-change energy balance remain unavailable, not zero. Density and volumetric process integration also remain unavailable.

## Reproduction and automated evidence

From repository root, with the existing isolated environment:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/peng_robinson_caloric/reference.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
```

The first command recomputes, compares against JSON and prints a human-readable summary. It does not write the artifact or access the network. `--write` is an explicit maintainer-only refreeze operation after all equation-level gates; ordinary tests never regenerate their expected JSON. Two successive reproduction runs match; no random initialization is used. All Cp inputs are in the pinned local distribution and frozen coefficients, not mutable runtime endpoints.

For a fresh isolated environment (installation requires package access, reproduction does not):

```sh
python3.10 -m venv .local/pre-m10-venv
.local/pre-m10-venv/bin/python -m pip install -r benchmarks/peng_robinson_caloric/requirements.txt
.local/pre-m10-venv/bin/python -B benchmarks/peng_robinson_caloric/reference.py
.local/pre-m10-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
```

Exact recorded Python version and source hashes are intentionally audited; changing interpreter/package source requires review rather than silently refreezing. This task exercised the existing environment, not a fresh install.

Required unchanged-production regressions:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_equilibrium_separator.py' -v
```

Results on 2026-09-29:

- New independent caloric suite: **23 tests passed**, covering exact constants, Cp/ranges/integration, entropy terms, analytic derivatives, residual/total H/S, A/B/C and both B phases, phase aggregation, pure EOS, ideal-gas limits, reference shifts, explicit unit/flow conversions, identities, extra-temperature neighborhoods, corruption rejection and read-only frozen reproduction.
- M8 frozen independent benchmark: **7 tests passed**.
- M8 production comparison: **122 comparisons passed**, unchanged acceptance criteria.
- M9 equilibrium-separator integration: **7 tests passed**, including runtime propagation, balance/round trip, absent-phase semantics and failure handling.
- Two consecutive default reproduction runs passed with identical human-readable output and an unchanged frozen-file SHA-256.
- Prettier checks passed for this report and the frozen JSON; Python AST syntax checks passed for all three new Python files; all new text files passed trailing-whitespace/final-newline checks; `git diff --check` passed.
- `git diff --exit-code` passed: no pre-existing tracked file was modified. Only the seven new benchmark/report files listed below were added. No broad UI/browser/build run is claimed for this benchmark-only change.

## Limits and next action

This is canonical PR plus a specified ideal-gas correlation, checked numerically against an independent implementation. Zero kij is a mathematical qualification assumption, not calibrated experimental validation. The empirical accuracy of Cp and PR mixture caloric predictions, particularly at high pressure, is not established by numerical agreement. Pure methane vapor and pure n_hexane vapor/liquid coverage is finite and does not qualify arbitrary components or states. Reproduction is intentionally tied to pinned source and reference conventions.

Excluded: production caloric properties; PH, PS, UV or TV flash; rigorous heaters/coolers/compressors/separator energy balances; water-containing caloric equilibrium or VLLE; reactions/chemical equilibrium; transport properties, viscosity, thermal conductivity, speed of sound; process density or volumetric-flow integration. No website, warning, Stream Table, equipment, production dependency, fixture, schema or contract version is changed. No live LLM/provider call was made. Development-only public-source research does not run during reproduction.

Recommended next action: review this reference and separately authorize a bounded M10 implementation of phase caloric properties with the offline dataset/reference convention and production-versus-frozen tests. Qualify that capability before separately implementing PH/PS inversion or process energy integration. Do not automatically proceed to water/VLLE. Remaining architectural work is explicit status/reference handling and robust phase-changing inversion, not a hidden implementation inside this benchmark.

## File inventory

Created:

- `PRE_MILESTONE_10_PR_CALORIC_BENCHMARK.md` — this report.
- `benchmarks/peng_robinson_caloric/reference.py` — independent-library generation, validation and human-readable output.
- `benchmarks/peng_robinson_caloric/equations.py` — direct benchmark-only equations.
- `benchmarks/peng_robinson_caloric/test_reference.py` — 23 reproduction/physics/unit tests.
- `benchmarks/peng_robinson_caloric/methane_nhexane_pr_caloric_reference.json` — frozen full-precision reference.
- `benchmarks/peng_robinson_caloric/requirements.txt` — isolated dependency pins.
- `benchmarks/peng_robinson_caloric/THIRD_PARTY_NOTICES.txt` — attribution and license notices.

Existing files modified: **none**. This report does not supersede M9's manual acceptance or expand its qualified scope.
