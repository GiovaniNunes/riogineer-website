# Milestone 16 — production rigorous isenthalpic throttling valve

Automated acceptance: COMPLETE — 2026-09-30.

Human-operated M16 validation: COMPLETE — 2026-09-30.

The human reviewer executed and inspected `canonical`, `pressure`, `flow`, `phase`, `negative` and `summary --verify`. Human review confirmed canonical rigorous throttling behavior, pressure-series behavior, PRESSURE_FLASH_ONSET, flow invariance, phase/service-scope behavior, all 38 negative cases and summary verification: PASS. The final human-reviewed summary confirmed 17 positive cases, 38 negative cases, 572 numerical comparisons and eight byte-identical call-order checks.

This human-validation record is separate from automated acceptance. The five separate thermodynamic studies remain outside primary equipment-service qualification. All documented limitations and numerical acceptance evidence remain unchanged.

Baseline: `10e10d8bff617b2a9a44abd48c7fb699230d0b2c` (`main`, equal to local `origin/main`). No staging, commit or push was performed. No M17 work was started.

## Evidence and architecture

The production identity is `rigorous_isenthalpic_pr@1.0`, equipment type `throttling_valve`, network profile `throttling_valve_energy`. Separately authorized additive requirements 1.8, flowsheet 1.9 and results/process-result 1.10 branches preserve the historical branches. Engine version is 1.9.0. The error schema remains unchanged.

The independent acceptance oracle is the committed Pre-M16 JSON, not a production-generated expected value. Its SHA-256 remains `ef0141ec3b72740175553381f2e0431290a0fa8eb937bd03ad0259a9aa2dbead`. The comparator reads this artifact without importing its independent solver. It executes the public requirements/flowsheet/network/calculation/schema path for every primary case.

Actual inlet component mass flows supply M7 molar flow and composition; inlet stream pressure and temperature are authoritative. The sequence is high_accuracy inlet PT/M10 calorics → H target = inlet equilibrium H → shared M11 PH at specified outlet pressure → fresh final PT/caloric evaluation → service, phase reconstruction, material and energy acceptance → one overall outlet. It does not use PS, an ideal-gas shortcut or a valve-private PH algorithm. All mandatory stages must pass before an accepted result is published.

The registered material ports are `inlet` and `outlet`; execution uses the existing acyclic one-source → valve → sink architecture. No recycle solver or pressure-network solver is added. Explicit parameters are property package, BIP and outlet pressure. Flow, inlet pressure/temperature and composition are not duplicated equipment specifications.

A vapor-liquid outlet contains internal equilibrium phase diagnostics, not two material outlets. Overall flow and composition are conserved. M16 is not a separator. VL inlet service remains rejected.

The public result and dedicated UI show equilibrium H/S, beta, phases, pressure reduction, target enthalpy, PH diagnostics and closure residuals. Stale results are hidden after edits; a failed rerun publishes no accepted valve outlet. The PFD uses one valve and one outlet. Two separately authorized historical-duty guards prevent the new branch being rendered as a heater. No shaft power, valve efficiency or heat duty is calculated; `energy_residual_W = F*(Hout-Hin)` is a closure diagnostic, not power delivered or consumed.

Production comparison artifact SHA-256: `2279a7ef2f820647901c9e088a221cce485f3e3c6b7077e5ff1196972c331671`. A fresh-process `--case summary --verify` reproduces its bytes without rewriting it.

## Canonical production state

Units are Pa absolute, K, mol/s, J/mol, J/(mol K), and W. Report formatting does not reduce JSON precision.

| Quantity              | Production result      |
| --------------------- | ---------------------- |
| F                     | 100.0                  |
| z (methane, n_hexane) | [0.5, 0.5]             |
| Inlet pressure        | 30000000.0             |
| Outlet pressure       | 1000000.0              |
| Inlet temperature     | 300.0                  |
| Outlet temperature    | 291.742138656979       |
| Inlet phase           | single_liquid          |
| Outlet phase          | vapor_liquid           |
| Outlet beta           | 0.4794423112951449     |
| H in                  | -16303.948024671077    |
| H out                 | -16303.948024671097    |
| H target              | -16303.948024671077    |
| delta H               | -2.000888343900442e-11 |
| S in                  | -72.15880132373434     |
| S out                 | -57.29960279656648     |
| delta S               | 14.859198527167855     |
| Enthalpy residual     | -2.000888343900442e-11 |
| Energy residual       | -2.000888343900442e-09 |
| Energy allowance      | 9.999999999999999e-05  |
| PH residual           | -2.000888343900442e-11 |
| PH candidate count    | 1                      |
| PH evaluation count   | 171                    |
| PH root iterations    | 42                     |

| State / phase | methane             | n_hexane            | Z                   | H                   | S                   |
| ------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| inlet/liquid  | 0.5                 | 0.5                 | 1.04595589143832    | -16303.948024671077 | -72.15880132373434  |
| outlet/liquid | 0.05718128748168017 | 0.9428187125183198  | 0.05116153871956797 | -30898.842876325474 | -92.04444980831724  |
| outlet/vapor  | 0.9807933719514703  | 0.01920662804852966 | 0.9725161211788265  | -457.4435508709597  | -19.575153308614254 |

## Qualified primary matrix

All 17 cases pass. These are the tested pressure/composition/pure-component combinations; the table does not authorize an arbitrary continuous pressure envelope. Outlet pressure is specified. L = single_liquid, V = single_vapor, VL = vapor_liquid.

| Case                  | F     | z          | Pin        | Pout       | Tin   | Tout               | Phases | beta out            | delta S                |
| --------------------- | ----- | ---------- | ---------- | ---------- | ----- | ------------------ | ------ | ------------------- | ---------------------- |
| CANONICAL             | 100.0 | [0.5, 0.5] | 30000000.0 | 1000000.0  | 300.0 | 291.742138656979   | L → VL | 0.4794423112951449  | 14.859198527167855     |
| PRESSURE_MILD         | 100.0 | [0.5, 0.5] | 30000000.0 | 29900000.0 | 300.0 | 300.0389692641584  | L → L  | 0.0                 | 0.028991271956215314   |
| PRESSURE_MODERATE     | 100.0 | [0.5, 0.5] | 30000000.0 | 20000000.0 | 300.0 | 303.5078121754573  | L → L  | 0.0                 | 2.9321996383599043     |
| PRESSURE_FLASH_ONSET  | 100.0 | [0.5, 0.5] | 30000000.0 | 10000000.0 | 300.0 | 304.2102681125253  | L → VL | 0.11065289435441628 | 6.006027491241198      |
| PRESSURE_INTERMEDIATE | 100.0 | [0.5, 0.5] | 30000000.0 | 6000000.0  | 300.0 | 300.2351719865334  | L → VL | 0.2992534811527605  | 7.859421004443689      |
| PRESSURE_SUBSTANTIAL  | 100.0 | [0.5, 0.5] | 30000000.0 | 3000000.0  | 300.0 | 296.08877191639135 | L → VL | 0.41056894713204883 | 10.473667862159346     |
| DOUBLE_FLOW           | 200.0 | [0.5, 0.5] | 30000000.0 | 1000000.0  | 300.0 | 291.742138656979   | L → VL | 0.4794423112951449  | 14.859198527167855     |
| LOW_FLOW              | 5.0   | [0.5, 0.5] | 30000000.0 | 1000000.0  | 300.0 | 291.742138656979   | L → VL | 0.4794423112951449  | 14.859198527167855     |
| VAPOR_SIMPLE          | 100.0 | [0.9, 0.1] | 6000000.0  | 1000000.0  | 400.0 | 381.63581455113086 | V → V  | 1.0                 | 14.206370670970813     |
| LIQUID_HEATING        | 100.0 | [0.5, 0.5] | 30000000.0 | 20000000.0 | 350.0 | 351.7917240382668  | L → L  | 0.0                 | 2.7715418337327193     |
| NEGLIGIBLE_DROP       | 100.0 | [0.5, 0.5] | 30000000.0 | 29999990.0 | 300.0 | 300.00000390025946 | L → L  | 0.0                 | 2.8988538076646364e-06 |
| HEXANE_RICH           | 100.0 | [0.1, 0.9] | 6000000.0  | 100000.0   | 300.0 | 296.0331464948125  | L → VL | 0.1183699905925053  | 4.203343660049555      |
| BALANCED_COLD         | 100.0 | [0.5, 0.5] | 30000000.0 | 1000000.0  | 250.0 | 241.4125803221007  | L → VL | 0.4503765951230889  | 14.216605685810947     |
| INLET_PRESSURE        | 100.0 | [0.5, 0.5] | 20000000.0 | 1000000.0  | 300.0 | 288.2461581862527  | L → VL | 0.4771923219083618  | 11.868855839328418     |
| PURE_METHANE          | 100.0 | [1.0, 0.0] | 6000000.0  | 100000.0   | 300.0 | 269.9814732896746  | V → V  | 1.0                 | 32.84700236078257      |
| PURE_HEXANE_VAPOR     | 100.0 | [0.0, 1.0] | 300000.0   | 100000.0   | 450.0 | 447.8327250189226  | V → V  | 1.0                 | 8.82379741561111       |
| PURE_HEXANE_LIQUID    | 100.0 | [0.0, 1.0] | 1000000.0  | 900000.0   | 300.0 | 300.04344444920156 | L → L  | 0.0                 | 0.04318946845000937    |

The observed transitions qualify L → L, L → VL and V → V. LIQUID_HEATING demonstrates heating during isenthalpic pressure reduction; other states cool or flash. Throttling is not universally cooling and is not isentropic. Entropy is reported as a thermodynamic diagnostic, not an efficiency. Pure methane and pure n-hexane qualification is limited to the listed states; unsupported pure coexistence gaps remain rejected.

## Flow and material closure

Every primary case conserves component mass flow, total molar flow and overall z. VL composition and phase enthalpy reconstruction pass separately. Stream enthalpy-flow subtraction is also checked against F times delta H within floating-point summation allowance.

| Case        | Intensive states byte-identical | Flow scaling error W | Allowance W |
| ----------- | ------------------------------- | -------------------- | ----------- |
| DOUBLE_FLOW | True                            | 0.0                  | 0.0         |
| LOW_FLOW    | True                            | 0.0                  | 0.0         |

## Separate thermodynamic studies

The five studies provide 130 additional field comparisons, separately from 572 primary comparisons. They do not enlarge primary valve service. The actual VL-inlet case is also sent through equipment validation and rejected without an accepted outlet.

| Case            | Inlet phase   | Outlet phase  | beta out              | Equipment interpretation                                   |
| --------------- | ------------- | ------------- | --------------------- | ---------------------------------------------------------- |
| TWO_PHASE_INLET | vapor_liquid  | vapor_liquid  | 0.47928294243271097   | rejected: VL inlet                                         |
| BUBBLE_BELOW    | single_liquid | single_liquid | 0.0                   | Separate boundary study; not primary service qualification |
| BUBBLE_ABOVE    | single_liquid | vapor_liquid  | 0.0005796899606593797 | Separate boundary study; not primary service qualification |
| DEW_BELOW       | single_vapor  | vapor_liquid  | 0.9986669447022223    | Separate boundary study; not primary service qualification |
| DEW_ABOVE       | single_vapor  | single_vapor  | 1.0                   | Separate boundary study; not primary service qualification |

## Negative matrix and atomic failure

All 38 negative cases pass. Controlled PT, PH, property-hole, ambiguity, unbracketed-target and fresh-final failures publish no accepted outlet. Internal diagnostic provenance is retained; the public error contains compact stage/status/reason rather than the full scan trace. Negative component mass flows map to production `invalid_flow`, while the independent mole-fraction input describes invalid composition; an incomplete binary basis maps to `unsupported_component`. These representation-specific categories preserve rejection and do not turn failures into accepted states.

| Case                 | Independent category          | Production status             | Stage            | Accepted outlet |
| -------------------- | ----------------------------- | ----------------------------- | ---------------- | --------------- |
| F_0.0                | invalid_flow                  | invalid_flow                  | specification    | No              |
| F_-1.0               | invalid_flow                  | invalid_flow                  | specification    | No              |
| F_NaN                | invalid_flow                  | invalid_flow                  | specification    | No              |
| F_Infinity           | invalid_flow                  | invalid_flow                  | specification    | No              |
| F_-Infinity          | invalid_flow                  | invalid_flow                  | specification    | No              |
| Pin_0.0              | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pin_-1.0             | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pin_NaN              | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pin_Infinity         | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pin_-Infinity        | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pout_0.0             | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pout_-1.0            | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pout_NaN             | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pout_Infinity        | invalid_pressure              | invalid_pressure              | specification    | No              |
| Pout_-Infinity       | invalid_pressure              | invalid_pressure              | specification    | No              |
| EQUAL_PRESSURE       | invalid_pressure              | invalid_pressure              | specification    | No              |
| PRESSURE_GAIN        | invalid_pressure              | invalid_pressure              | specification    | No              |
| TIN_199.0            | temperature_domain_invalid    | temperature_domain_invalid    | specification    | No              |
| TIN_501.0            | temperature_domain_invalid    | temperature_domain_invalid    | specification    | No              |
| TIN_NaN              | temperature_domain_invalid    | temperature_domain_invalid    | specification    | No              |
| TIN_Infinity         | temperature_domain_invalid    | temperature_domain_invalid    | specification    | No              |
| TIN_-Infinity        | temperature_domain_invalid    | temperature_domain_invalid    | specification    | No              |
| Z_SUM                | invalid_composition           | invalid_composition           | specification    | No              |
| Z_NEGATIVE           | invalid_composition           | invalid_flow                  | specification    | No              |
| Z_NAN                | invalid_composition           | invalid_flow                  | specification    | No              |
| Z_INF                | invalid_composition           | invalid_flow                  | specification    | No              |
| Z_LENGTH             | invalid_composition           | unsupported_component         | specification    | No              |
| WATER                | unsupported_component         | unsupported_component         | specification    | No              |
| UNKNOWN              | unsupported_component         | unsupported_component         | specification    | No              |
| NONZERO_KIJ          | unsupported_bip               | unsupported_bip               | specification    | No              |
| VL_INLET_SERVICE     | inlet_service_scope           | inlet_service_scope           | service_scope    | No              |
| PT                   | pt_evaluation_failure         | pt_evaluation_failure         | inlet_PT         | No              |
| PH                   | controlled_ph_failure         | controlled_ph_failure         | outlet_PH        | No              |
| UNBRACKETED          | enthalpy_target_not_bracketed | enthalpy_target_not_bracketed | outlet_PH        | No              |
| AMBIGUOUS            | multiple_ph_roots             | multiple_ph_roots             | outlet_PH        | No              |
| HOLE                 | pt_evaluation_failure         | pt_evaluation_failure         | outlet_PH        | No              |
| FRESH_FINAL          | final_acceptance_failed       | final_acceptance_failed       | final_acceptance | No              |
| PURE_COEXISTENCE_GAP | ph_nonconvergence             | ph_nonconvergence             | outlet_PH        | No              |

## General PH property-hole correction and authorization

Production PH previously aborted globally on the first controlled PT scan failure. The separately authorized general correction scans the same 128 temperatures over 200–500 K, partitions successful points at recorded controlled failures, builds exact-hit/sign-change candidates only within each valid interval, and evaluates uniqueness across all intervals. More than one candidate remains ambiguity. It retains the established refinement method, fresh-final acceptance, tolerances, resolution and serialized diagnostic structure. Unexpected programming errors are not swallowed as property holes. Per-call state is local and deterministic. No parallel scanning or feature flag is introduced.

Only the explicitly authorized early-abort assertion in `engine/tests/test_pr_ph_flash.py::Controls.test_pt_failure_recorded_and_not_bridged` changed: `call_count == 1` became exact complete-grid coverage, recorded failures and no brackets. The historical negative still has no payload, the same failure category and preserved underlying diagnostic. No PH numerical expectation, fixture, tolerance or frozen comparator artifact changed. No other historical test changed.

The initial PRESSURE_FLASH_ONSET scan stopped at evaluation 104, T = 443.3070866141732 K and P = 10000000 Pa. Isolated fresh-process PT repetitions reproduced `flash_not_converged`, 100 iterations and maximum log-fugacity residual 1.4646062140855065e-12. A 41-point local investigation found a finite unavailable region, not call-order contamination; 41 nearby-root points were valid VL states. A diagnostic-only 280–350 K call recovered the root but was never embedded in valve logic.

The unchanged full scan records eight failed points from 443.3070866141732 through 459.84251968503935 K. Sampled valid intervals are [200, 440.9448818897638] and [462.20472440944883, 500] K. The single candidate [303.93700787401576, 306.2992125984252] K is in the first interval. Its fresh result is T = 304.2102681125253 K, beta = 0.11065289435441628 and PH residual = -2.000888343900442e-11 J/mol. The comparator preserves every failed scan point, intervals and candidate diagnostics. Finite scanning is not a proof of global mathematical uniqueness outside the qualified search semantics.

The holes remain unavailable. No interpolation or bracket crosses them, and root-relevant holes remain failures. M16 does not repair the independent library property hole or change production PT/EOS/stability. PH production logic contains no benchmark identifier, hard-coded hole boundary, composition or root.

The PH gate passed before valve implementation resumed: 16 focused interval tests; historical M11 53, M12 36, M14 75 and M15 118 tests; 548 unique complete Python tests (initial sandbox run plus unchanged permitted localhost rerun); unchanged M11 comparator 29 positives / 9 negatives or gaps / 401 comparisons; unchanged Pre-M16 forward comparator 571 comparisons. Two fresh readiness processes and reversed call order were byte-identical. HOLE, AMBIGUOUS, PURE_COEXISTENCE_GAP, UNBRACKETED and FRESH_FINAL all retained controlled rejection. Historical M11 comparison artifact SHA-256 remains `c561353ff82fe6ebaddc384b03b2242ead1ddbc4483074180b21967a387195d2`.

## Governing numerical errors

Each allowance is the unchanged field-specific allowance for its governing case; it is not a newly fitted global tolerance. All rows PASS. H/S units follow the canonical table, fractions/Z are dimensionless, and energy residual is W.

| Quantity                         | Maximum absolute error | Allowance              | Governing case        | Result |
| -------------------------------- | ---------------------- | ---------------------- | --------------------- | ------ |
| F                                | 0.0                    | 1.4210854715202004e-12 | CANONICAL             | PASS   |
| PH_residual                      | 7.275957614183426e-11  | 1e-06                  | BALANCED_COLD         | PASS   |
| delta_S                          | 5.5990767577895895e-12 | 1.233240513076079e-07  | HEXANE_RICH           | PASS   |
| energy_residual                  | 7.275957614183426e-09  | 9.999999999999999e-05  | BALANCED_COLD         | PASS   |
| enthalpy_residual                | 7.275957614183426e-11  | 1e-06                  | BALANCED_COLD         | PASS   |
| inlet.H                          | 9.094947017729282e-12  | 1.1001782025629118e-06 | LIQUID_HEATING        | PASS   |
| inlet.P                          | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| inlet.S                          | 6.394884621840902e-14  | 1.052801281625649e-08  | LIQUID_HEATING        | PASS   |
| inlet.T                          | 0.0                    | 1e-07                  | CANONICAL             | PASS   |
| inlet.beta                       | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| inlet.liquid.H                   | 9.094947017729282e-12  | 1.1001782025629118e-06 | LIQUID_HEATING        | PASS   |
| inlet.liquid.S                   | 6.394884621840902e-14  | 1.052801281625649e-08  | LIQUID_HEATING        | PASS   |
| inlet.liquid.Z                   | 2.220446049250313e-16  | 1.1762340414300265e-09 | LIQUID_HEATING        | PASS   |
| inlet.liquid.q0                  | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| inlet.liquid.q1                  | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| inlet.vapor.H                    | 4.547473508864641e-13  | 1.0392474567954585e-06 | VAPOR_SIMPLE          | PASS   |
| inlet.vapor.S                    | 1.4210854715202004e-14 | 1.0596795457668544e-08 | PURE_HEXANE_VAPOR     | PASS   |
| inlet.vapor.Z                    | 2.220446049250313e-16  | 1.0853976940652931e-09 | PURE_METHANE          | PASS   |
| inlet.vapor.q0                   | 0.0                    | 2e-09                  | VAPOR_SIMPLE          | PASS   |
| inlet.vapor.q1                   | 0.0                    | 2e-09                  | VAPOR_SIMPLE          | PASS   |
| inlet.z0                         | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| inlet.z1                         | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| outlet.H                         | 1.811713445931673e-09  | 3.1372608990667116e-05 | HEXANE_RICH           | PASS   |
| outlet.P                         | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| outlet.S                         | 5.6132876125047915e-12 | 1.1246906457702944e-07 | HEXANE_RICH           | PASS   |
| outlet.T                         | 9.890754881780595e-12  | 2.650485013592297e-07  | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.beta                      | 5.932199176328368e-13  | 2.4892863587551814e-09 | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.liquid.H                  | 1.0863004717975855e-08 | 1.594445258683243e-05  | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.liquid.S                  | 1.9269918993813917e-11 | 8.540802202084387e-08  | PRESSURE_INTERMEDIATE | PASS   |
| outlet.liquid.Z                  | 8.554268404736831e-14  | 5.907098880147545e-10  | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.liquid.q0                 | 3.6048941609578833e-13 | 2.2874990290999616e-09 | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.liquid.q1                 | 3.6048941609578833e-13 | 2.2874990290999616e-09 | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.vapor.H                   | 4.4929038267582655e-10 | 8.52981314639925e-06   | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.vapor.S                   | 2.55262477821816e-12   | 5.0104949082406656e-08 | HEXANE_RICH           | PASS   |
| outlet.vapor.Z                   | 1.587618925213974e-14  | 1.278766274121767e-09  | PRESSURE_FLASH_ONSET  | PASS   |
| outlet.vapor.q0                  | 1.0469403122215226e-13 | 3.1856114387291246e-09 | HEXANE_RICH           | PASS   |
| outlet.vapor.q1                  | 1.0477729794899915e-13 | 3.185611438725143e-09  | HEXANE_RICH           | PASS   |
| outlet.z0                        | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| outlet.z1                        | 0.0                    | 2e-09                  | CANONICAL             | PASS   |
| pressure_ratio                   | 0.0                    | 0.0                    | CANONICAL             | PASS   |
| target_H                         | 9.094947017729282e-12  | 1.1001782025629118e-06 | LIQUID_HEATING        | PASS   |
| phase enthalpy reconstruction    | 0.0                    | 1e-06                  | CANONICAL             | PASS   |
| phase composition reconstruction | 4.218847493575595e-15  | 1e-10                  | BALANCED_COLD         | PASS   |
| phase composition normalization  | 1.1102230246251565e-16 | 1e-10                  | PRESSURE_INTERMEDIATE | PASS   |
| delta_H / isenthalpic closure    | 7.275957614183426e-11  | 1e-06                  | BALANCED_COLD         | PASS   |

Flow invariance is additionally byte-exact and flow-scaling error is zero in both rows above, against zero allowance. Component mass-balance residuals are zero throughout the primary matrix.

## Determinism and regression gates

The production artifact passes fresh-process byte reproduction with `--verify`. Normal review never writes it. Run IDs are omitted from deterministic evidence; implementation and input hashes remain. All eight calculation histories below reproduce the same target bytes.

| Target               | Previous calculation | Byte-identical |
| -------------------- | -------------------- | -------------- |
| CANONICAL            | PRESSURE_FLASH_ONSET | True           |
| LIQUID_HEATING       | VAPOR_SIMPLE         | True           |
| VAPOR_SIMPLE         | HEXANE_RICH          | True           |
| CANONICAL            | PH                   | True           |
| CANONICAL            | PURE_METHANE         | True           |
| PRESSURE_FLASH_ONSET | HOLE                 | True           |
| PURE_HEXANE_LIQUID   | AMBIGUOUS            | True           |
| CANONICAL            | FRESH_FINAL          | True           |

Final automated gates:

| Gate                                      | Observed result                                                                              |
| ----------------------------------------- | -------------------------------------------------------------------------------------------- |
| Complete Python, fixed final source tree  | 609 tests PASS                                                                               |
| Focused valve                             | 61 tests PASS (17 positive, 38 negative, six integration)                                    |
| General PH intervals                      | 16 tests PASS                                                                                |
| Historical M11 / M12 / M14 / M15          | 53 / 36 / 75 / 118 tests PASS; included in full regression                                   |
| Independent Pre-M16 suite                 | 54 tests PASS; frozen-reference reproduction unchanged                                       |
| Primary production comparator             | 17 positive, 38 negative, 572 comparisons PASS                                               |
| Separate production thermodynamic studies | Five studies, 130 comparisons PASS                                                           |
| M11 production comparator                 | 29 positive, nine negative/gap, 401 comparisons; historical bytes unchanged                  |
| Pre-M16 read-only forward comparator      | 571 comparisons PASS                                                                         |
| TypeScript/Vitest                         | 260 tests in 22 files PASS                                                                   |
| Valve plus historical contracts           | 29 new + 39 historical = 68 PASS; 78 including workflow                                      |
| Complete browser suite                    | 34 tests PASS                                                                                |
| Schema generation parity                  | `npm run contracts:check` PASS; historical branches unchanged                                |
| Lint / types / formatting                 | `npm run lint`, `npm run typecheck`, `npm run format:check` PASS                             |
| Build                                     | `npm run build` PASS; 41 pages                                                               |
| Production smoke                          | 17 pages, 17 PNG cards, internal links, 404s, preview indexing and disabled delivery PASS    |
| New Python syntax / indentation           | AST, compile to temporary location and tabnanny PASS                                         |
| Documentation / JSON / whitespace         | New report Markdown, deterministic JSON, changed-line whitespace and `git diff --check` PASS |

The final public-error serialization change was covered by its focused atomic-failure test, a further passing M16 browser run, and the final complete Python run. Browser coverage includes canonical flashing, stale-result invalidation, a fresh changed-pressure result, VL-inlet failure with no accepted result, and the one-outlet PFD.

Environment and execution qualifications: the earlier HTTP suite needed the already permitted localhost rerun. An initial browser run overlapped a build that removed its Next development output; all 34 tests passed on an unchanged complete rerun with the build finished. Smoke initially used mismatched SITE_URL/port settings and passed with the task server and SITE_URL both on port 3200. A complete Python attempt overlapped the final error-message source edit, so a historical M15 byte comparison observed different implementation hashes; the entire suite was rerun with source held fixed. No historical test or numerical allowance was altered for these execution issues. Task-owned servers were stopped and generated next-env.d.ts changes restored.

## Qualification limits

Qualification is bounded to the frozen methane/n-hexane matrix, explicit constant zero kij, existing 200–500 K domain and pressures listed above. Accepted inlet service is single liquid or single vapor; qualified outlets may be L, V or VL. VL inlets and boundary perturbations remain separate studies. Pure-component coexistence-gap, ambiguity, unbracketed-target and property-hole rejection remain active.

No water, arbitrary petroleum/general mixture, arbitrary nonzero BIP, VLLE, three-phase equilibrium, near-critical generality or non-equilibrium flashing is qualified. The adiabatic model neglects kinetic and potential energy. There is no heat-transfer model, shaft-work model, valve efficiency, flow prediction, Cv/Kv, choking/choked-flow sizing, cavitation, erosion, noise, mechanical valve design, control dynamics or automatic downstream phase separation. No compressor, pump, turbine, expander or M17 feature is added by this milestone.

## Integrity and exact file inventory

All 338 baseline tracked files were compared against baseline bytes. The 13 authorized modifications below leave 325 baseline files unchanged. All eight committed Pre-M16 files, all prior frozen artifacts and qualification reports, dependencies, PT/EOS/stability/PS, and error.schema.json remain byte-identical. Historical tests are protected except the single authorized early-abort expectation. Numerical values/tolerances in historical evidence are unchanged. New comparison values are observations, not replacement independent truth.

The authorization history is explicit: minimal versioned valve contract extension; two workspace duty guards; general property-hole-aware PH investigation/correction; and the single M11 early-abort semantic update. No additional historical assertion needed modification. All changes remain unstaged.

Modified baseline files:

- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `docs/RIOGINEER_MASTER_CONTEXT.md`
- `engine/riogineer_engine/core.py`
- `engine/riogineer_engine/network.py`
- `engine/riogineer_engine/network_models.py`
- `engine/riogineer_engine/pr_ph_flash.py`
- `engine/tests/test_pr_ph_flash.py`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/workspace.tsx`
- `src/lib/digital-engineer/contracts.ts`

New files:

- `MILESTONE_16.md`
- `benchmarks/throttling_valve/compare_production.py`
- `benchmarks/throttling_valve/production_comparison.json`
- `engine/riogineer_engine/throttling_valve_energy.py`
- `engine/riogineer_engine/throttling_valve_process.py`
- `engine/tests/test_pr_ph_intervals.py`
- `engine/tests/test_throttling_valve_energy.py`
- `src/app/digital-engineer/throttling-valve-results.tsx`
- `tests/e2e/throttling-valve.spec.ts`
- `tests/throttling-valve-contracts.test.ts`

## Tested human-review commands

Run from the repository root. Each mode below was executed successfully. The human-operated modes and completion record are listed above; this command list also retains the previously tested automated review modes. The frozen independent JSON and production comparison are not rewritten by these commands.

```bash
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case canonical
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case pressure
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case flow
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case composition
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case phase
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case pure
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case negative
engine/.venv/bin/python -B benchmarks/throttling_valve/compare_production.py --case summary --verify
```

`--write` is reserved for explicit generation of the new production comparison artifact. It does not regenerate independent truth. Automated acceptance and human-operated validation remain separate records. Human-operated M16 validation is complete as recorded above.
