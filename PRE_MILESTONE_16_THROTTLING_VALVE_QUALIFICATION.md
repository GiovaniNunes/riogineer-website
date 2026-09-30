# Pre-Milestone 16 — Independent rigorous throttling valve qualification

Independent Pre-M16 automated qualification: **COMPLETE — 2026-09-30**.

Property-hole investigation: **Outcome A — interval qualification resolved; failed PT region remains unavailable**.

Human-operated Pre-M16 validation: **COMPLETE — 2026-09-30**.

Production M16 valve: **NOT IMPLEMENTED**.

## Human-operated validation record

The human reviewer reported successful execution and inspection on 2026-09-30 of `canonical`, `pressure`, `flow`, `phase`, `negative` and `summary`. All reviewed modes passed. Phase review also exposed the pure-component, liquid/vapor, boundary and two-phase-inlet evidence. This record is separate from automated qualification; no numerical qualification was rerun for this documentation update.

The canonical case confirmed F=100 mol/s, z=[0.5 methane, 0.5 n_hexane], liquid inlet at 300 K and 30 MPa, and a VL outlet at 1 MPa and 291.742138657 K with beta=0.4794423113. Hin and Hout were both −16303.948024671074 J/mol, with zero reported delta H and PH residual and one qualified candidate. Entropy increased from approximately −72.1588013237 to −57.2996027966 J/(mol K), giving delta S=+14.8591985272 J/(mol K). The methane-rich vapor and n-hexane-rich liquid remain equilibrium phases of **one overall outlet stream**, with z_out=z_in; x and y are not separate valve streams.

Pressure review confirmed the existing numerical table: a very small pressure reduction leaves T approximately unchanged or slightly increased; 30→20 MPa gives approximately 303.507812 K (liquid), 30→10 MPa gives 304.210268 K (VL, beta≈0.110653), 30→6 MPa gives 300.235172 K (VL, beta≈0.299253), 30→3 MPa gives 296.088772 K (VL, beta≈0.410569), and 30→1 MPa gives 291.742139 K (VL, beta≈0.479442). Reviewed cases preserved the isenthalpic identity and positive entropy change; throttling does not imply universal cooling.

`PRESSURE_FLASH_ONSET` was confirmed as a qualified primary case **only on the explicit connected 280–350 K interval**, recovering approximately 304.210268113 K and beta=0.1106528944 with one candidate. The previously identified property hole remains unavailable and was neither interpolated nor bridged. The investigation and scope restrictions below remain unchanged.

Flow review compared `LOW_FLOW` (5 mol/s), `CANONICAL` (100 mol/s) and `DOUBLE_FLOW` (200 mol/s). Intensive outlet states were byte-identical and energy-scaling error was zero. Phase review confirmed primary liquid→liquid, liquid→VL and vapor→vapor behavior, including robust interior flashing, and the qualified `PURE_METHANE`, `PURE_HEXANE_VAPOR` and `PURE_HEXANE_LIQUID` cases. Pure coexistence-gap protection remains in force. `TWO_PHASE_INLET` remained a calculable separate study; `BUBBLE_BELOW`, `BUBBLE_ABOVE`, `DEW_BELOW` and `DEW_ABOVE` passed as separate studies. Recommended initial M16 service remains single-liquid or single-vapor inlets, with qualified liquid, vapor or VL outlets; VL inlet service is not promoted.

All 38 negatives rejected with `accepted_outlet=False`, including invalid flow/P/T/z, equal pressure and pressure gain, unsupported components/BIP, VL inlet service, PT/PH failures, unbracketed targets, ambiguity, property holes, fresh-final failure and pure coexistence-gap nonconvergence. No failed case published an accepted outlet.

The reviewed summary confirmed **17 primary cases, 5 separate studies, 38 negatives, 1,633 numerical comparisons and 12 byte-identical call-order checks**. Governing enthalpy residual 1.866283128e−9 J/mol and PH residual 1.735315891e−8 J/mol remained below 1e−6 J/mol; energy residual 1.866283128e−7 W remained below 1e−4 W. Component material residuals and flow-scaling errors were zero; phase/composition reconstruction stayed within recorded allowances. Existing numerical tables, tolerances and automated evidence remain unchanged.

This documentation update changes only this report and the newly authorized Pre-M16 entry in Master Context. Frozen reference SHA-256 remains `ef0141ec3b72740175553381f2e0431290a0fa8eb937bd03ad0259a9aa2dbead`. Production M16 remains **NOT IMPLEMENTED**; all existing exclusions and future authorization gates remain in force.

## Baseline and independence

On 2026-09-30 the read-only gate verified clean `main`, with HEAD equal to local `origin/main` at `6d18908ad5ed55e589af735be271a0f6b26663d1`. No fetch was needed. All 330 tracked baseline files were hashed before changes. At closure of the separately authorized property-hole investigation, all 330 remained byte-identical. No historical file, production equation, test, contract or tolerance was changed to resolve the hole.

The independent model identity is `independent_throttling_valve@1.0`, distinct from the recommended future production identity `rigorous_isenthalpic_pr@1.0`. The solver uses unchanged independent benchmark helpers from M10/M11/M13, Thermo stability-first PT and SciPy PH inversion. It does not import RioGineer production thermodynamics. `compare_forward.py` is a separate read-only production PT/PH diagnostic and never generates expected values.

The existing `.local/pre-m8-venv` environment remains unchanged: Python 3.10.10, Thermo 0.6.0, SciPy 1.15.3, NumPy 2.2.6, Chemicals 1.5.2 and fluids 1.3.1. Requirements retain the established independent stack's exact pins; no production dependency was added. The reference records component constants, Cp coefficient rows, package versions and source hashes. Notices attribute the inherited coefficient data and libraries.

## Thermodynamic model and conventions

Methane/n-hexane, in that component order, uses Peng–Robinson with constants 0.45724/0.07780, classical quadratic mixing and explicit constant zero kij. Qualification is limited to the frozen composition/pressure matrix and 200–500 K; it is not a rectangular-domain guarantee. Pressure is Pa absolute, temperature K, flow mol/s, enthalpy J/mol, entropy J/(mol K), and energy-rate residual W.

The valve is steady-state and adiabatic with no shaft work, negligible kinetic/potential energy change and one material inlet/outlet. The molar relation is `H_out = H_in`. Inlet PT supplies equilibrium H; PH at the specified lower outlet pressure determines T and equilibrium phases. Outlet pressure is a specification, not a hydraulic prediction. Pressure ratio is `Pout/Pin`; pressure reduction is `Pin-Pout`. Equal pressure and pressure gain reject.

Enthalpy residual is `H_out-H_in`; energy residual is `F*(H_out-H_in)`. The latter is a closure diagnostic, not valve power. Entropy diagnostic is `S_out-S_in`, not an isentropic constraint. Ideal-gas sensible H is zero at 298.15 K; entropy uses 298.15 K and 101325 Pa with ideal mixing. Primary library caloric values are checked against direct independent PR departures and ideal-gas integration using the same convention.

Temperature may rise or fall because the constant-enthalpy endpoint changes with pressure and equilibrium phases. A liquid inlet can flash while the valve remains adiabatic. Overall composition and flow remain unchanged: phase compositions differ, but they reconstruct the single overall outlet through `z=(1-beta)*x+beta*y`. The valve does not become a separator. Pressure-sensitivity rows represent separate endpoint calculations, not an integrated reversible path.

Unlike M14, there is no isentropic reference, efficiency or compressor power. Unlike M15, there is only one material path and no second process stream or heat-transfer calculation.

## Property-hole investigation and resolution

The original primary candidate `PRESSURE_FLASH_ONSET` has Pin=30000000 Pa, Tin=300 K, Pout=10000000 Pa, F=100 mol/s, z=[0.5,0.5], zero kij, liquid inlet and target H=−16303.948024671074 J/mol. The initial 256-point 200–500 K scan failed at 461.1764705882353 K. The exact unchanged-method failure was reproduced before changing any setting, and again in a fresh oracle: `TrialFailure`, stage `pt`, caused by Thermo `UnconvergedError`, message `End of SS without convergence`.

Settings remained PT_SS_TOL=1e-26, PT_SS_MAXITER=1000, PT_SS_POLISH=True, PT_SS_POLISH_TOL=1e-25, PT_SS_POLISH_MAXITER=1000, PT_SS_POLISH_VF=1e-6, PT_STABILITY_MAXITER=1000 and PT_STABILITY_XTOL=1e-12. Read-only exception tracing observed iteration 999, error 6.2136215202614615e-12 and unaccepted vapor-fraction candidate 0.5964477118277425. Candidate x=[0.467539249765092,0.532460750234908], y=[0.5219627131990213,0.4780372868009786]; initial guesses were [0.4999817383071967,0.5000182616928033] and [0.5187564786263548,0.48124352137364523]. These are iteration diagnostics, not accepted phases.

Every local scan point, success/failure, H, S, beta, phase compositions, phase Z/H/S and PT diagnostics is retained in JSON under `property_hole_investigation.scans`. Each point uses a fresh independent oracle. Failed points are unavailable; there is no interpolation.

| Scan       | Points | Failures | Lowest failed T, K | Highest failed T, K |
| ---------- | ------ | -------- | ------------------ | ------------------- |
| offsets    | 25     | 17       | 460.1764705882353  | 461.3764705882353   |
| step_0.1   | 41     | 15       | 460.1764705882353  | 461.5764705882353   |
| step_0.02  | 101    | 73       | 460.1764705882353  | 461.6164705882353   |
| step_0.005 | 101    | 101      | 460.9264705882353  | 461.4264705882353   |

The offset scan uses 0 and ±0.0001, ±0.001, ±0.01, ±0.02, ±0.05, ±0.1, ±0.2, ±0.5, ±1, ±2, ±5 and ±10 K about 461.1764705882353 K. Uniform scans span center±2 K at 0.1 K, center±1 K at 0.02 K and center±0.25 K at 0.005 K. There are 268 recorded evaluations, including intentionally repeated points across resolutions.

**Hole topology: B, a finite numerical property hole**, not an isolated point. The same region persists under refinement. It is adjacent to a change in the library's phase classification, but an exact bubble/dew boundary is not established there. At 460.0764705882353 K the oracle gives VL, beta 0.5266502891882289, H=8743.892365357598 J/mol; at 461.6764705882353 K it gives single_liquid, beta=0, H=9092.33636294955 J/mol. This warrants a near-critical/phase-coalescence conditioning interpretation, not an interpolated boundary or a universal critical-state claim.

Independent VF boundary queries returned bubble T=277.28334095278404 K and a nominal VF=1 solution at 454.20005493812494 K. Fresh PT at the bubble ±0.05 K changes from liquid to VL (beta 0.0002836815573057054 above). Fresh PT on both sides of the nominal VF=1 solution remains VL, with beta approximately 0.43343–0.43430. Therefore that VF query is **not accepted as a dew boundary**; neither query establishes a boundary at the failed point.

The legitimate Thermo `hot_start` diagnostic was tried with seeds at center−2, −1, −0.5, +0.5, +1 and +2 K under unchanged tolerances. All six overall attempts failed with `UnconvergedError`. Thermo tries a two-phase warm initialization when the seed has both phases and otherwise falls back to its stability-first route. No alternate initialization was adopted as the primary method.

**Disposition: Outcome A.** The valve root is qualified only within the explicitly declared connected sampled interval **280–350 K** for `PRESSURE_FLASH_ONSET`. It remains a primary pressure-sensitivity case: its purpose is moderate flashing in the same-inlet pressure series, not investigation of the distant high-temperature hole. It was not deleted or relabeled to avoid failure. The 350–500 K region is outside this case's inverse qualification; the hole itself remains unresolved and unavailable.

The benchmark-local solver accepts an explicit bounded interval, validates that it lies in 200–500 K and checks the final root lies inside it. All other cases retain 200–500 K. Historical PH remains unchanged and still rejects any sampled failure inside the supplied interval. This is explicit scoped qualification, not global PH uniqueness. Every sampled state in the four connected-interval refinements is VL with increasing H; each scan finds one candidate, root refinement stays inside valid endpoints and fresh-final enthalpy closes. No failed point is used as a bracket endpoint or interior evaluation.

| Points | Root method | Root T, K          | H residual, J/mol       | Candidates |
| ------ | ----------- | ------------------ | ----------------------- | ---------- |
| 128    | brentq      | 304.2102681125352  | -1.8189894035458565e-12 | 1          |
| 256    | brentq      | 304.2102681125348  | -4.547473508864641e-11  | 1          |
| 512    | bisect      | 304.21026811252466 | -1.3878889149054885e-09 | 1          |
| 1024   | brentq      | 304.21026811253455 | -7.639755494892597e-11  | 1          |

The original 128-point full-domain result had Tout=304.2102681125351 K and beta=0.11065289435382315. Restricting the interval changed Tout by 5.684341886080802e-14 K, H by −1.8189894035458565e-12 J/mol, S by 4.263256414560601e-14 J/(mol K), and beta by −9.71445146547012e-17. All other 21 drafted positive/study results were byte-identical. The full existing negative matrix was rerun after the change. An added guard rejects even a successful injected PH result outside the declared interval.

Robust primary flashing is independently present in `CANONICAL` at 1 MPa, far from this hole. Its full 200–500 K scans at 128/256/512 points, Brent/bisection/direct-caloric recovery, fresh-final phase/material/enthalpy checks and deterministic/call-order checks pass. Beta≈0.47944 is comfortably interior. The pressure-series resolution does not depend on silently replacing the primary canonical example.

## Canonical result

| Quantity           | Result              |
| ------------------ | ------------------- |
| Flow, mol/s        | 100                 |
| Overall z          | [0.5, 0.5]          |
| Pin, Pa absolute   | 30000000.0          |
| Pout, Pa absolute  | 1000000.0           |
| Tin, K             | 300.0               |
| Tout, K            | 291.7421386569806   |
| Inlet phase        | single_liquid       |
| Outlet phase       | vapor_liquid        |
| Outlet beta        | 0.479442311295126   |
| Hin, J/mol         | -16303.948024671074 |
| Hout, J/mol        | -16303.948024671074 |
| H residual, J/mol  | 0.0                 |
| Sin, J/(mol K)     | -72.15880132373437  |
| Sout, J/(mol K)    | -57.29960279656633  |
| Delta S, J/(mol K) | 14.859198527168033  |
| Energy residual, W | 0.0                 |
| PH candidates      | 1                   |

| Outlet phase | Composition                                | Z                   | H, J/mol            | S, J/(mol K)        |
| ------------ | ------------------------------------------ | ------------------- | ------------------- | ------------------- |
| liquid       | [0.05718128748170936, 0.9428187125182906]  | 0.05116153871956692 | -30898.84287632438  | -92.04444980831451  |
| vapor        | [0.9807933719514688, 0.019206628048531193] | 0.9725161211788266  | -457.44355087090264 | -19.575153308614045 |

## Positive matrix, pressure, flow and composition behavior

| Case                  | F, mol/s | z          | Pin, Pa    | Pout, Pa   | Tin, K | Tout, K            | Inlet → outlet                | beta                | Delta S, J/(mol K)     |
| --------------------- | -------- | ---------- | ---------- | ---------- | ------ | ------------------ | ----------------------------- | ------------------- | ---------------------- |
| CANONICAL             | 100.0    | [0.5, 0.5] | 30000000.0 | 1000000.0  | 300.0  | 291.7421386569806  | single_liquid → vapor_liquid  | 0.479442311295126   | 14.859198527168033     |
| PRESSURE_MILD         | 100.0    | [0.5, 0.5] | 30000000.0 | 29900000.0 | 300.0  | 300.0389692641587  | single_liquid → single_liquid | 0.0                 | 0.028991271956343212   |
| PRESSURE_MODERATE     | 100.0    | [0.5, 0.5] | 30000000.0 | 20000000.0 | 300.0  | 303.5078121754574  | single_liquid → single_liquid | 0.0                 | 2.9321996383599327     |
| PRESSURE_FLASH_ONSET  | 100.0    | [0.5, 0.5] | 30000000.0 | 10000000.0 | 300.0  | 304.2102681125352  | single_liquid → vapor_liquid  | 0.11065289435382306 | 6.006027491241369      |
| PRESSURE_INTERMEDIATE | 100.0    | [0.5, 0.5] | 30000000.0 | 6000000.0  | 300.0  | 300.2351719865419  | single_liquid → vapor_liquid  | 0.29925348115241773 | 7.859421004443732      |
| PRESSURE_SUBSTANTIAL  | 100.0    | [0.5, 0.5] | 30000000.0 | 3000000.0  | 300.0  | 296.0887719163945  | single_liquid → vapor_liquid  | 0.41056894713197395 | 10.473667862159445     |
| DOUBLE_FLOW           | 200.0    | [0.5, 0.5] | 30000000.0 | 1000000.0  | 300.0  | 291.7421386569806  | single_liquid → vapor_liquid  | 0.479442311295126   | 14.859198527168033     |
| LOW_FLOW              | 5.0      | [0.5, 0.5] | 30000000.0 | 1000000.0  | 300.0  | 291.7421386569806  | single_liquid → vapor_liquid  | 0.479442311295126   | 14.859198527168033     |
| VAPOR_SIMPLE          | 100.0    | [0.9, 0.1] | 6000000.0  | 1000000.0  | 400.0  | 381.63581455113086 | single_vapor → single_vapor   | 1.0                 | 14.20637067097077      |
| LIQUID_HEATING        | 100.0    | [0.5, 0.5] | 30000000.0 | 20000000.0 | 350.0  | 351.791724038267   | single_liquid → single_liquid | 0.0                 | 2.7715418337328046     |
| NEGLIGIBLE_DROP       | 100.0    | [0.5, 0.5] | 30000000.0 | 29999990.0 | 300.0  | 300.00000390025934 | single_liquid → single_liquid | 0.0                 | 2.8988537650320723e-06 |
| HEXANE_RICH           | 100.0    | [0.1, 0.9] | 6000000.0  | 100000.0   | 300.0  | 296.0331464948052  | single_liquid → vapor_liquid  | 0.11836999059248718 | 4.203343660043956      |
| BALANCED_COLD         | 100.0    | [0.5, 0.5] | 30000000.0 | 1000000.0  | 250.0  | 241.41258032209993 | single_liquid → vapor_liquid  | 0.45037659512309136 | 14.216605685811047     |
| INLET_PRESSURE        | 100.0    | [0.5, 0.5] | 20000000.0 | 1000000.0  | 300.0  | 288.24615818625244 | single_liquid → vapor_liquid  | 0.4771923219083493  | 11.868855839328312     |
| PURE_METHANE          | 100.0    | [1.0, 0.0] | 6000000.0  | 100000.0   | 300.0  | 269.98147328967485 | single_vapor → single_vapor   | 1.0                 | 32.84700236078259      |
| PURE_HEXANE_VAPOR     | 100.0    | [0.0, 1.0] | 300000.0   | 100000.0   | 450.0  | 447.8327250189228  | single_vapor → single_vapor   | 1.0                 | 8.823797415611168      |
| PURE_HEXANE_LIQUID    | 100.0    | [0.0, 1.0] | 1000000.0  | 900000.0   | 300.0  | 300.0434444492014  | single_liquid → single_liquid | 0.0                 | 0.04318946845000937    |

The 17 primary cases cover liquid and vapor inlets and liquid, vapor and VL outlets. Balanced and hexane-rich liquid feeds flash; the methane-rich vapor case remains vapor. Pure methane, pure n-hexane vapor and pure n-hexane liquid cases qualify separately. No primary vapor-to-VL case was established by this matrix; liquid-to-VL is the robust demonstrated phase-generation behavior.

The same-inlet pressure series first warms and then cools as pressure decreases; this is observed behavior of the chosen states, not universal temperature or beta monotonicity. `NEGLIGIBLE_DROP` changes T by about 3.90e-6 K for a positive 10 Pa pressure reduction, not exactly zero drop. Materially positive entropy changes occur throughout the matrix, including heating cases. No entropy-equality constraint or universal cooling rule was applied.

Canonical flow 100 mol/s, doubled flow 200 mol/s and low flow 5 mol/s produce byte-identical inlet/outlet thermodynamic states, including phase properties. Both explicit flow-scaling residual errors are zero. Overall/component material residuals are zero. No shaft-power quantity exists.

## Separate phase and inlet-service studies

| Case            | Inlet phase   | Outlet phase  | Tout, K            | beta out              | Primary? |
| --------------- | ------------- | ------------- | ------------------ | --------------------- | -------- |
| TWO_PHASE_INLET | vapor_liquid  | vapor_liquid  | 291.50166153068517 | 0.4792829424326885    | No       |
| BUBBLE_BELOW    | single_liquid | single_liquid | 231.06755435138734 | 0.0                   | No       |
| BUBBLE_ABOVE    | single_liquid | vapor_liquid  | 231.16755435138973 | 0.0005796899611142366 | No       |
| DEW_BELOW       | single_vapor  | vapor_liquid  | 468.2158895316327  | 0.9986669447044427    | No       |
| DEW_ABOVE       | single_vapor  | single_vapor  | 468.31588953163265 | 1.0                   | No       |

Five separate studies include one VL inlet and four bubble/dew perturbations at 6 MPa. These are distinct from the problematic 10 MPa region. At 6 MPa the ±0.05 K outlet perturbations produce liquid/VL across the bubble and VL/vapor across the dew. Refined roots, reconstruction and classification agree.

Recommendation: initially accept **single-phase inlets**, including qualified liquid and vapor, with liquid/vapor/VL outlets within this frozen matrix. Keep VL inlet service separate. The one VL-inlet example is independently calculable, deterministic, uniquely recovered on its scanned interval and supported by production PT/PH diagnostics and existing state serialization. That single study is insufficient evidence for a broader inlet-service envelope, especially near coalescence/coexistence regions. Exclusion is a conservative equipment-service choice, not a claim that VL PT/PH is impossible. No automatic downstream phase separation is implied.

## Failure matrix and fresh acceptance

All 38 negative cases reject without publishing an outlet. Nonfinite inputs are encoded as strings in JSON, decoded only for controlled tests. The unbracketed, ambiguity and property-hole tests inject deterministic evaluator behavior into the unchanged independent PH method; controlled PT/PH and fresh-final corruption are explicitly labeled. The pure coexistence case uses the real independent model and rejects with fresh-residual nonconvergence rather than interpolating the gap.

| Case                 | Expected / observed failure   | Stage            | Accepted outlet |
| -------------------- | ----------------------------- | ---------------- | --------------- |
| F_0.0                | invalid_flow                  | specification    | No              |
| F_-1.0               | invalid_flow                  | specification    | No              |
| F_NaN                | invalid_flow                  | specification    | No              |
| F_Infinity           | invalid_flow                  | specification    | No              |
| F_-Infinity          | invalid_flow                  | specification    | No              |
| Pin_0.0              | invalid_pressure              | specification    | No              |
| Pin_-1.0             | invalid_pressure              | specification    | No              |
| Pin_NaN              | invalid_pressure              | specification    | No              |
| Pin_Infinity         | invalid_pressure              | specification    | No              |
| Pin_-Infinity        | invalid_pressure              | specification    | No              |
| Pout_0.0             | invalid_pressure              | specification    | No              |
| Pout_-1.0            | invalid_pressure              | specification    | No              |
| Pout_NaN             | invalid_pressure              | specification    | No              |
| Pout_Infinity        | invalid_pressure              | specification    | No              |
| Pout_-Infinity       | invalid_pressure              | specification    | No              |
| EQUAL_PRESSURE       | invalid_pressure              | specification    | No              |
| PRESSURE_GAIN        | invalid_pressure              | specification    | No              |
| TIN_199.0            | temperature_domain_invalid    | specification    | No              |
| TIN_501.0            | temperature_domain_invalid    | specification    | No              |
| TIN_NaN              | temperature_domain_invalid    | specification    | No              |
| TIN_Infinity         | temperature_domain_invalid    | specification    | No              |
| TIN_-Infinity        | temperature_domain_invalid    | specification    | No              |
| Z_SUM                | invalid_composition           | specification    | No              |
| Z_NEGATIVE           | invalid_composition           | specification    | No              |
| Z_NAN                | invalid_composition           | specification    | No              |
| Z_INF                | invalid_composition           | specification    | No              |
| Z_LENGTH             | invalid_composition           | specification    | No              |
| WATER                | unsupported_component         | specification    | No              |
| UNKNOWN              | unsupported_component         | specification    | No              |
| NONZERO_KIJ          | unsupported_bip               | specification    | No              |
| VL_INLET_SERVICE     | inlet_service_scope           | service_scope    | No              |
| PT                   | pt_evaluation_failure         | inlet_PT         | No              |
| PH                   | controlled_ph_failure         | outlet_PH        | No              |
| UNBRACKETED          | enthalpy_target_not_bracketed | outlet_PH        | No              |
| AMBIGUOUS            | multiple_ph_roots             | outlet_PH        | No              |
| HOLE                 | pt_evaluation_failure         | outlet_PH        | No              |
| FRESH_FINAL          | final_acceptance_failed       | final_acceptance | No              |
| PURE_COEXISTENCE_GAP | ph_nonconvergence             | outlet_PH        | No              |

Fresh-final acceptance checks finite physical state, exact P/z provenance, interval membership, physical beta/phase compositions, material and phase-enthalpy reconstruction, one candidate and H residual ≤1e-6 J/mol. Negative atomicity is tested after successful calculation with the same oracle and followed by successful canonical recovery. The exact historical hole remains a failure, and the 256-point full-domain case still rejects; successful restricted-interval recovery does not mask that behavior.

## Numerical controls, allowances and governing errors

Default PH scan uses 128 points; independent refinements use 256-point Brent, 512-point bisection and 128-point direct-caloric inversion. Root controls are xtol=1e-10 K, rtol=1e-14 and maxiter=100. The accepted fresh H residual remains 1e-6 J/mol. The connected-interval investigation adds a 1024-point check. Scan/root-trial hashes, counts, brackets, iterations, final evaluations, phase transitions and candidate counts are frozen. The inherited independent Brent wrapper does not expose a terminal bracket, so it is not fabricated; production diagnostics retain their final bracket.

Allowances inherit M10/M11/M13/Pre-M15 absolute-plus-relative rules: H=1e-6+1e-11|H| J/mol, S=1e-8+1e-11|S| J/(mol K), T=1e-7 K, beta/composition=2e-9 and Z=2e-10+1e-9|Z|. Recovered quantities add local absolute slope times the propagated inlet-H/PH temperature budget `1e-7 + 4*(inlet H allowance + 1e-6)/dH_dT`. Slopes use ±0.001 K and require unchanged phase classification. Phase material reconstruction uses 1e-10; phase H reconstruction uses 1e-6 J/mol. Energy residual allowance is F*1e-6 W. Values were inherited/propagated before comparisons, not fitted to observed error. All per-case allowances and comparisons reside in JSON.

There are 1,633 independent numerical checks, counted from the per-case checks plus two flow-scaling comparisons. The supplementary hole scans and four interval-refinement diagnostics are not inflated into that count. The following table records every governing quantity; repeated PH refinements contribute their actual errors.

| Quantity                      | Maximum absolute error | Allowance              | Governing case        | Result |
| ----------------------------- | ---------------------- | ---------------------- | --------------------- | ------ |
| PH_residual                   | 1.735315890982747e-08  | 1e-06                  | DEW_BELOW             | PASS   |
| boundary_T                    | 2.3590018827235326e-12 | 2.5830171941041014e-07 | BUBBLE_ABOVE          | PASS   |
| component_material0           | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| component_material1           | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| energy_residual               | 1.8662831280380487e-07 | 9.999999999999999e-05  | HEXANE_RICH           | PASS   |
| enthalpy_residual             | 1.8662831280380487e-09 | 1e-06                  | HEXANE_RICH           | PASS   |
| flow                          | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| inlet.H                       | 7.275957614183426e-12  | 1.253905036688311e-06  | BUBBLE_ABOVE          | PASS   |
| inlet.P                       | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| inlet.S                       | 4.263256414560601e-14  | 1.052801281625649e-08  | LIQUID_HEATING        | PASS   |
| inlet.liquid.H                | 7.275957614183426e-12  | 1.253905036688311e-06  | BUBBLE_ABOVE          | PASS   |
| inlet.liquid.S                | 4.263256414560601e-14  | 1.052801281625649e-08  | LIQUID_HEATING        | PASS   |
| inlet.liquid.sum              | 1.1102230246251565e-16 | 1e-10                  | TWO_PHASE_INLET       | PASS   |
| inlet.phase_H_reconstruction  | 0.0                    | 1e-06                  | CANONICAL             | PASS   |
| inlet.reconstruction0         | 5.551115123125783e-17  | 1e-10                  | TWO_PHASE_INLET       | PASS   |
| inlet.reconstruction1         | 0.0                    | 1e-10                  | CANONICAL             | PASS   |
| inlet.vapor.H                 | 5.4569682106375694e-12 | 1.133317465465046e-06  | DEW_ABOVE             | PASS   |
| inlet.vapor.S                 | 3.019806626980426e-14  | 1.010929360147591e-08  | DEW_ABOVE             | PASS   |
| inlet.vapor.sum               | 2.220446049250313e-16  | 1e-10                  | TWO_PHASE_INLET       | PASS   |
| inlet.z0                      | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| inlet.z1                      | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| outlet.H                      | 1.0913936421275139e-11 | 2.2126495390214647e-05 | PRESSURE_SUBSTANTIAL  | PASS   |
| outlet.P                      | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| outlet.S                      | 2.4158453015843406e-13 | 1.1246906457702944e-07 | HEXANE_RICH           | PASS   |
| outlet.liquid.H               | 1.4551915228366852e-11 | 2.957665119511406e-05  | CANONICAL             | PASS   |
| outlet.liquid.S               | 2.984279490192421e-13  | 1.0048282103860448e-07 | HEXANE_RICH           | PASS   |
| outlet.liquid.sum             | 2.220446049250313e-16  | 1e-10                  | INLET_PRESSURE        | PASS   |
| outlet.phase_H_reconstruction | 0.0                    | 1e-06                  | CANONICAL             | PASS   |
| outlet.reconstruction0        | 5.551115123125783e-17  | 1e-10                  | CANONICAL             | PASS   |
| outlet.reconstruction1        | 1.1102230246251565e-16 | 1e-10                  | PRESSURE_INTERMEDIATE | PASS   |
| outlet.vapor.H                | 3.637978807091713e-12  | 3.017889811462314e-05  | PURE_HEXANE_VAPOR     | PASS   |
| outlet.vapor.S                | 5.684341886080802e-14  | 7.5274735976482e-08    | PURE_HEXANE_VAPOR     | PASS   |
| outlet.vapor.sum              | 1.1102230246251565e-16 | 1e-10                  | BUBBLE_ABOVE          | PASS   |
| outlet.z0                     | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| outlet.z1                     | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| refined.H                     | 1.7336788005195558e-08 | 3.920305907733174e-05  | DEW_BELOW             | PASS   |
| refined.S                     | 3.699973660786782e-11  | 9.142615432704797e-08  | DEW_BELOW             | PASS   |
| refined.T                     | 6.275513442233205e-11  | 3.507449931085733e-07  | VAPOR_SIMPLE          | PASS   |
| refined.beta                  | 1.557309836641707e-12  | 5.430283848850604e-09  | DEW_BELOW             | PASS   |
| refined.liquid.H              | 1.6543708625249565e-08 | 3.7304967761797424e-05 | DEW_BELOW             | PASS   |
| refined.liquid.S              | 3.483080490696011e-11  | 8.64480328279679e-08   | DEW_BELOW             | PASS   |
| refined.liquid.Z              | 1.375566327510569e-13  | 8.159529739675667e-10  | DEW_BELOW             | PASS   |
| refined.liquid.q0             | 2.6029178812336795e-13 | 2.9156486606258947e-09 | BUBBLE_ABOVE          | PASS   |
| refined.liquid.q1             | 2.601252546696742e-13  | 2.9156486606302887e-09 | BUBBLE_ABOVE          | PASS   |
| refined.vapor.H               | 1.1226802598685026e-08 | 2.5743603968881635e-05 | DEW_BELOW             | PASS   |
| refined.vapor.S               | 3.282529803527723e-11  | 8.223239769929356e-08  | DEW_BELOW             | PASS   |
| refined.vapor.Z               | 3.3306690738754696e-13 | 1.6294518334723314e-09 | DEW_BELOW             | PASS   |
| refined.vapor.q0              | 4.466427228067005e-13  | 2.983584161285193e-09  | DEW_BELOW             | PASS   |
| refined.vapor.q1              | 4.464761893530067e-13  | 2.9835841612887702e-09 | DEW_BELOW             | PASS   |
| refined.z0                    | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| refined.z1                    | 0.0                    | 2e-09                  | CANONICAL             | PASS   |

## Frozen evidence, determinism and verification

Frozen artifact: `benchmarks/throttling_valve/methane_nhexane_throttling_valve_reference.json`.

SHA-256: `ef0141ec3b72740175553381f2e0431290a0fa8eb937bd03ad0259a9aa2dbead`.

Stable sorted-key JSON preserves full floating-point precision and contains no absolute machine paths. Explicit `--write` generated the artifact. Normal execution freshly rebuilds and compares bytes without rewriting. Final verification uses the final solver source hash; an earlier verification run was superseded by the added interval-membership guard and deliberately regenerated before final acceptance. No numerical allowance changed.

Twelve byte-identical call-order checks cover canonical, simple vapor, pure liquid and VL-study targets after unrelated pure, boundary and controlled PH-failure histories. Flow comparisons also require byte-identical intensive state serialization. Nine fresh-process verifications passed; detailed results are recorded below.

## Production thermodynamic diagnostic and future readiness

The separate read-only comparator calls existing high_accuracy PT/M10 followed by PH/M11 using the production inlet H target. It uses the explicit 280–350 K interval only for `PRESSURE_FLASH_ONSET`, through existing PHSettings; all other cases retain 200–500 K. No fallback production solver or valve equipment is created. The diagnostic covers all 17 primary and five study states, including H, S, T, beta, phase classifications, phase Z/H/S/compositions, exact overall z, final residual and candidate provenance. All 571 numerical comparisons passed; detailed results are recorded below.

The independent hole does not establish a production thermodynamic defect. Existing PH supports the tested liquid/vapor/VL endpoints and existing caloric serialization exposes beta, liquid/vapor composition, Z, H and S. The explicit inverse-interval scope must be preserved in future acceptance; no global uniqueness or reliable independent characterization of the failed region is claimed.

Production diagnostic examples (independent allowances preserved):

| Quantity         | Maximum absolute error |              Allowance | Governing case       |
| ---------------- | ---------------------: | ---------------------: | -------------------- |
| inlet.H          | 1.0568328434601426e-09 |  1.163339553084298e-06 | TWO_PHASE_INLET      |
| inlet.S          |  3.623767952376511e-12 | 1.0643993654121932e-08 | TWO_PHASE_INLET      |
| outlet.T         |  7.077005648170598e-11 | 2.2888643804854688e-07 | DEW_BELOW            |
| outlet.H         |  1.811713445931673e-09 | 3.1372608990667116e-05 | HEXANE_RICH          |
| outlet.S         | 5.6132876125047915e-12 | 1.1246906457702944e-07 | HEXANE_RICH          |
| outlet.beta      |  2.220446049250313e-12 |  5.430283848850604e-09 | DEW_BELOW            |
| outlet.liquid.H  |  1.996158971451223e-08 | 3.7304967761797424e-05 | DEW_BELOW            |
| outlet.liquid.q0 | 3.6048941609578833e-13 | 2.2874990290999616e-09 | PRESSURE_FLASH_ONSET |
| outlet.vapor.q0  |  6.364908600176022e-13 |  2.983584161285193e-09 | DEW_BELOW            |

**Contract readiness: future M16 requires an additive contract extension.** Repository searches found no integrated valve/throttle calculation model, requirement branch or dispatch entry. Existing registry equipment includes heaters, compressors, separators, splitter, mixer and the four-port exchanger. A drawing/library mention of a valve is not an executable model.

Actual latest versions are requirements 1.7, flowsheet 1.8 and results/process-result 1.9. Recommend new additive requirements 1.8, flowsheet 1.9 and results/process-result 1.10 branches with explicit `rigorous_isenthalpic_pr@1.0`, specified Pout, property package and BIP provenance. Minimum future files include `src/lib/digital-engineer/contracts.ts` and the generated requirements/flowsheet/results schemas, plus validation schema compatibility if needed. Preserve every historical branch. Reuse existing H/S state structures and compact PH diagnostics instead of introducing duplicate phase structures.

Future result fields should include inlet/outlet states, flow/material conservation, pressure ratio/reduction, H target, delta H, delta S, enthalpy/energy closure residuals, and PH interval/bracket/final provenance. Do not introduce `valve_power`, efficiency, shaft-power recovery or a second outlet stream.

**Future production M16 must STOP before public contract modifications and obtain separate authorization unless its implementation request explicitly authorizes that exact extension.** No contract changes are authorized by this independent qualification.

**Network readiness:** the existing one-inlet/one-outlet port and stream-identity pattern can represent the future valve, without M15's four-port topology. A model registry entry and rigorous process dispatch/result integration are still needed later; present network energy execution is not a general rigorous mixed-equipment solver. Current code rejects cycles and explicitly excludes recycle convergence. A deterministic valve needs no special recycle equation, but recycle integration itself remains unqualified and must not be claimed available.

Recommended future sequence: validate specification → inlet PT/M10 → inlet-service check → H target=Hin → PH/M11 at specified Pout within qualified interval → fresh final outlet → enthalpy/material/phase/service checks → publish one accepted overall outlet. Failures at specification, inlet_PT, outlet_PH, service_scope or final_acceptance publish no accepted outlet and reuse the existing error envelope. Relevant inlet/Pout/provider/BIP/model changes invalidate prior output.

Recommend a separate future `compare_production.py` and `production_comparison.json` against the committed independent reference. Neither production acceptance artifact is created now. Later UI should show inlet/outlet P/T, phase transition, beta/phase properties, H, delta H/S and PH residual. A conventional one-inlet/one-outlet valve PFD is sufficient. This would be the first rigorous equipment milestone deliberately admitting pressure-generated VL service; it remains one overall stream that may later feed a separator.

## Qualification limitations

Qualification does not cover water, arbitrary petroleum mixtures, nonzero BIPs, temperatures outside 200–500 K, pressures/compositions outside the frozen matrix, VLLE, three phases, critical-region generalization, metastability, non-equilibrium flashing, slip, kinetic/potential effects, heat loss/gain, shaft work, valve efficiency, Cv/Kv or choked-flow sizing, capacity prediction, cavitation, flashing erosion, noise, vibration, trim sizing, material selection, mechanical design, dynamics, controls, actuator behavior or downstream separation. It qualifies endpoints, not internal valve paths, reversibility or mechanical/design suitability. Pure coexistence intervals remain rejected. No M16 or M17 implementation was performed.

## Executed checks and integrity

Independent Pre-M16: **54 tests passed** (separate from production discovery), **17 primary**, **5 studies**, **38 negatives**, **1,633 independent numerical comparisons**, **12 byte-identical call-order checks**. The explicit --write path generated the final artifact; all eight human-review modes and default verification passed in **nine fresh processes** with byte-identical evidence and unchanged final SHA. All nine documented review/diagnostic commands were tested successfully. Human validation was pending at automated qualification; the separate completed human record is above.

Read-only production thermodynamics: **571 numerical field comparisons passed** across all 22 positive/study cases, with matching phases and qualified fresh PH diagnostics. No production M16 implementation or production acceptance artifact exists.

Historical complete Python discovery ran 530 tests successfully, but the HTTP class setup was blocked by sandbox localhost binding (`PermissionError: [Errno 1] Operation not permitted`). The unchanged permitted rerun of `test_engine.py` passed all 14 tests, including both HTTP tests; 12 were repeats. Thus **532 unique current production tests passed across the full discovery and targeted environment rerun**, with no unresolved failure or skipped test. This is not a claim that the initial sandbox run exited successfully. No thermodynamic regression was observed.

```sh
cd engine
.venv/bin/python -B -m unittest discover -s tests -v
# Same source, with localhost permission for the environment-only rerun:
.venv/bin/python -B -m unittest discover -s tests -p test_engine.py -v
```

Historical modules, with actual passing counts:

| Module                                    | Tests passed |
| ----------------------------------------- | -----------: |
| `test_compression`                        |            7 |
| `test_compressor_energy`                  |           75 |
| `test_engine`                             |           14 |
| `test_equilibrium_separator`              |            7 |
| `test_heater_cooler_energy`               |           36 |
| `test_network`                            |           18 |
| `test_pr_caloric`                         |           35 |
| `test_pr_comparison`                      |            1 |
| `test_pr_eos`                             |            7 |
| `test_pr_flash`                           |           26 |
| `test_pr_ph_flash`                        |           53 |
| `test_pr_ps_flash`                        |           55 |
| `test_pr_pt_boundary`                     |           32 |
| `test_pr_pt_vapor_parent`                 |           23 |
| `test_sequential`                         |            9 |
| `test_streams`                            |            6 |
| `test_thermodynamics`                     |           10 |
| `test_two_stream_heat_exchanger_energy`   |          113 |
| `test_two_stream_heat_exchanger_topology` |            5 |

TypeScript/browser/build were **not run because application/contracts remained byte-identical**. Historical benchmark CLI suites were not rerun separately; current production unittest discovery includes the existing numerical/comparator protections listed above. Historical references/reports were additionally protected by hashes.

Python syntax/compile and indentation checks passed for all four new Python files without writing bytecode. All 11 requirement pins match the unchanged independent environment. Markdown formatting/checks passed for the new report, deterministic JSON formatting/portable-path checks passed, all new-file whitespace checks and `git diff --check` passed. The exact investigation diff was inspected; all 21 unrelated positive/study results remain byte-identical after the final interval guard. All 38 negatives were rerun.

**At automated qualification close, 330/330 baseline tracked files remained byte-identical.** The eight specifically checked Pre-M14/M14/Pre-M15/M15 reports and independent/production reference JSON artifacts also match their baseline hashes. No historical numerical value, tolerance, model, contract, test or dependency changed. Master Context was intentionally unchanged under the investigation authorization's requirement to preserve all 330 baseline files; the later documentation-only authorization permits the Pre-M16 status entry recorded with human validation. No unrelated repository-local diagnostic, cache or scratch file remains.

## Human-review commands

Run from repository root. Each independent command freshly reproduces the frozen evidence and verifies bytes; none rewrites it. Human-operated validation is recorded separately above. The final command is a separate thermodynamic diagnostic, not production M16 acceptance.

```sh
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case canonical
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case pressure
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case flow
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case composition
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case phase
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case pure
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case negative
.local/pre-m8-venv/bin/python -B benchmarks/throttling_valve/reference.py --case summary
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_forward.py
```

All commands above completed successfully against the final unchanged artifact.

## Exact file inventory

New Pre-M16 files:

- `PRE_MILESTONE_16_THROTTLING_VALVE_QUALIFICATION.md`
- `benchmarks/throttling_valve/requirements.txt`
- `benchmarks/throttling_valve/THIRD_PARTY_NOTICES.txt`
- `benchmarks/throttling_valve/solver.py`
- `benchmarks/throttling_valve/reference.py`
- `benchmarks/throttling_valve/test_reference.py`
- `benchmarks/throttling_valve/methane_nhexane_throttling_valve_reference.json`
- `benchmarks/throttling_valve/compare_forward.py`

The investigation modified only the original three draft files and added the independent test file. After Outcome A, the resumed original qualification added requirements, notices, independent JSON and the read-only forward diagnostic. Temporary work remains outside the repository. No stage, commit or push occurred.

No existing tracked file was modified during automated qualification. Its closing `git status --short` was:

```text
?? PRE_MILESTONE_16_THROTTLING_VALVE_QUALIFICATION.md
?? benchmarks/throttling_valve/
```

All evidence remains unstaged for final inspection. Independent automated qualification is complete within the stated interval and service limitations. Human-operated Pre-M16 validation is separately complete — 2026-09-30.

**Independent Pre-Milestone 16 Rigorous Throttling Valve qualification completed. Production M16 valve has not been implemented.**
