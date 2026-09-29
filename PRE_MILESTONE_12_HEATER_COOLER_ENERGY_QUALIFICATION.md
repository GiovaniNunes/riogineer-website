# Pre-Milestone 12 — Independent Heater/Cooler Energy-Balance Qualification

Independent automated qualification completed on 2026-09-29. Production M12 has not been implemented. This record does not claim human-operated Pre-M12 validation.

## Purpose and independence

Reference identity: `independent_methane_nhexane_heater_cooler@1.0`.

This benchmark qualifies the relation **inlet equilibrium state + outlet specification → outlet equilibrium state + heat duty** for the selected methane/n-hexane states. It does not qualify production Heater/Cooler code, flowsheet integration, Draw.io integration, UI behavior or sizing. All existing tracked files are protected and unchanged, including the current equipment models and M8/M8.1/M8.2/M10/M11 implementations.

The new experiment imports only the existing independent Pre-M11 PT/caloric oracle and independent PH solver. Thermo 0.6.0 supplies stability-first PT equilibrium and phase caloric values. The unchanged independent Pre-M10 equations audit library caloric values at each evaluation. SciPy 1.15.3 supplies Brent's root solver. Production thermodynamic results are never inputs to reference generation, and neither production PH nor production Heater/Cooler code is imported.

Dependencies remain isolated in `.local/pre-m8-venv`. The new `requirements.txt` repeats the exact qualified stack pins: thermo 0.6.0, chemicals 1.5.2, fluids 1.3.1, numpy 2.2.6, scipy 1.15.3, pandas 2.3.3, python-dateutil 2.9.0.post0, pytz 2026.4, six 1.17.0, teqp 0.23.1 and tzdata 2026.4. The retained teqp dependency is not called by this experiment. No production dependency or runtime online lookup is introduced.

## Thermodynamic provenance

Canonical PR1976 uses R = 8.31446261815324 J/(mol K), omega_a = 0.45724 and omega_b = 0.07780. Component constants match the independent M8 reference and `riogineer_components@1.0`:

| Component | MW kg/kmol |    Tc K |    Pc Pa absolute |    Acentric factor |
| --------- | ---------: | ------: | ----------------: | -----------------: |
| methane   |    16.0428 | 190.564 |           4599200 |            0.01142 |
| n_hexane  |   86.17536 |  507.82 | 3044115.328359688 | 0.3003189315498438 |

The entire BIP matrix is explicitly zero. This is the historical independent zero-kij benchmark convention, not fitted physical interaction data. Every positive case has overall molar composition `[0.5, 0.5]` in methane/n_hexane order.

Cp/R = a + bT + cT² + dT³ + eT⁴ uses the unchanged Poling coefficients distributed in Chemicals 1.5.2:

| Component / CAS     |     a |         b |          c |          d |         e | Source range K |
| ------------------- | ----: | --------: | ---------: | ---------: | --------: | -------------: |
| methane / 74-82-8   | 4.568 | -0.008975 |   3.631e-5 |  -3.407e-8 | 1.091e-11 |        50–1000 |
| n_hexane / 110-54-3 | 8.831 | -0.000166 | 0.00014302 | -1.8314e-7 | 7.124e-11 |       200–1000 |

The reference state is 298.15 K, 101325 Pa absolute, with pure ideal-gas h and s each zero there. Ideal h integrates Cp from the reference temperature, mixture h weights component ideal contributions by phase composition, and PR departure h is added at the corresponding phase root. Entropy follows the same inherited sensible, pressure and ideal mixing convention. No formation terms are used. Two-phase equilibrium H is `(1-beta)*h_L + beta*h_V`; no manual latent-heat interpolation is introduced.

The experiment restricts both endpoint temperatures and PH search to 200–500 K, the existing independent PH qualification interval, although the shared Cp correlations extend to 1000 K. All accepted states lie within both ranges. Exact constants, Cp coefficients, BIP, reference convention, package versions and source SHA-256 values are retained in the new JSON. Its nested historical Pre-M11 provenance is copied verbatim; historical scope statements there describe that independent reference, not the current implementation status of production M11.

Attribution and licenses are in `benchmarks/heater_cooler_energy/THIRD_PARTY_NOTICES.txt`. Only the already qualified two coefficient rows are repeated as metadata; no proprietary database or third-party implementation is redistributed.

## Energy conventions and algorithms

F is mol/s, H is J/mol, Q is J/s = W, P is Pa absolute, T is K. Beta and all compositions are molar. These calculations do not mix molar enthalpy with mass-specific properties.

Mode A independently evaluates the inlet at `(T_in, P_in, z)` and outlet at `(T_out, P_out, z)`, then computes:

```text
delta_H = H_out - H_in
Q = F * delta_H
R_Q = Q - F*(H_out - H_in)
```

Mode B reevaluates the inlet, forms `H_out,target = H_in + Q/F`, and calls the independent PH solver with P_out, z and that target. Mode B receives no forward outlet temperature or warm start. Every PH trial invokes stability-first PT and the existing independent caloric oracle. A deterministic 128-point 200–500 K scan identifies candidate brackets; Brent refinement uses xtol = 1e-10 K, rtol = 1e-14 and at most 100 iterations. A fresh final state must satisfy the enthalpy residual gate; multiple admissible roots, failed thermodynamic trials and unresolved targets fail explicitly.

Positive Q adds heat; negative Q removes heat. No shaft work, kinetic or potential energy change is included. P_out is a specified input, including one 6 MPa → 3 MPa case. This is not a hydraulic pressure-drop calculation. F_out = F_in and z_out = z_in; phase redistribution does not remove material.

## Accepted case matrix

L = single_liquid; VL = vapor_liquid; V = single_vapor. Display values are rounded only in this report; JSON retains full double precision and the complete forward/inverse phase payloads and PH diagnostics.

| Case                      | F mol/s | Pin → Pout Pa   | Tin → Tout K                  | Phase change |     H_in J/mol |    H_out J/mol |  delta_H J/mol |            Q W |
| ------------------------- | ------: | --------------- | ----------------------------- | ------------ | -------------: | -------------: | -------------: | -------------: |
| VAPOR_HEATING             |     100 | 1000 → 1000     | 300 → 350                     | V → V        |  164.368643728 |  4910.98206552 |  4746.61342179 |  474661.342179 |
| VAPOR_COOLING             |     100 | 1000 → 1000     | 350 → 300                     | V → V        |  4910.98206552 |  164.368643728 | -4746.61342179 | -474661.342179 |
| LIQUID_HEATING            |     100 | 3e+07 → 3e+07   | 280 → 350                     | L → L        | -18660.8082789 | -10017.8202563 |  8642.98802262 |  864298.802262 |
| LIQUID_COOLING            |     100 | 3e+07 → 3e+07   | 350 → 280                     | L → L        | -10017.8202563 | -18660.8082789 | -8642.98802262 | -864298.802262 |
| LIQUID_TO_TWO_PHASE       |     100 | 6e+06 → 6e+06   | 220 → 300                     | L → VL       | -26609.6886597 | -16333.9553084 |  10275.7333513 |  1027573.33513 |
| TWO_PHASE_TO_VAPOR        |     100 | 6e+06 → 6e+06   | 300 → 480                     | VL → V       | -16333.9553084 |  15162.9271949 |  31496.8825033 |  3149688.25033 |
| VAPOR_TO_TWO_PHASE        |     100 | 6e+06 → 6e+06   | 480 → 300                     | V → VL       |  15162.9271949 | -16333.9553084 | -31496.8825033 | -3149688.25033 |
| TWO_PHASE_TO_LIQUID       |     100 | 6e+06 → 6e+06   | 300 → 220                     | VL → L       | -16333.9553084 | -26609.6886597 | -10275.7333513 | -1027573.33513 |
| TWO_PHASE_TO_TWO_PHASE    |     100 | 6e+06 → 6e+06   | 300 → 350                     | VL → VL      | -16333.9553084 | -9627.95627204 |  6705.99903639 |  670599.903639 |
| SPECIFIED_OUTLET_PRESSURE |     100 | 6e+06 → 3e+06   | 300 → 350                     | VL → VL      | -16333.9553084 | -9028.92621389 |  7305.02909454 |  730502.909454 |
| VAPOR_HEATING_DOUBLE_FLOW |     200 | 1000 → 1000     | 300 → 350                     | V → V        |  164.368643728 |  4910.98206552 |  4746.61342179 |  949322.684357 |
| ZERO_DUTY                 |     100 | 300000 → 300000 | 300 → 300                     | VL → VL      | -14232.3399985 | -14232.3399985 |              0 |              0 |
| BUBBLE_ADJACENT_HEATING   |     100 | 6e+06 → 6e+06   | 230.617554351 → 231.617554351 | L → VL       | -25453.3357857 | -25321.1064842 |   132.22930151 |   13222.930151 |
| DEW_ADJACENT_COOLING      |     100 | 6e+06 → 6e+06   | 468.765889532 → 467.765889532 | V → VL       |  13402.9489954 |  13176.5020618 | -226.446933546 | -22644.6933546 |

The four required cross-phase directions all pass, as do VL → VL, vapor and liquid heating/cooling, and the specified-pressure-change case. The adjacent cases reuse the independent Pre-M11 bubble/dew endpoint temperatures at 6 MPa without replacing their frozen values. No critical or retrograde behavior is inferred.

Doubling F from 100 to 200 mol/s leaves both full thermodynamic states and delta_H exactly identical and doubles Q from 474661.34217868675 to 949322.6843573735 W. Reversed endpoint cases have exactly opposite duties. The zero-duty case has identical forward endpoints and Q = 0 W; independent PH recovers 299.99999999998494 K.

## Round-trip acceptance and numerical policy

Every case follows PT outlet → H_out → Q → target H → independent PH → recovered outlet state. Acceptance checks inlet and outlet H, delta_H, Q, phase classification, T, beta, each phase composition, Z and ideal/residual/total phase h. A 60-digit Decimal calculation from exact binary-float endpoint inputs independently checks energy arithmetic in the tests.

The following tolerances come from the independently qualified Pre-M11 state comparison, not production settings. They remain appropriate because the same independent stability-first PT/caloric stack, 200–500 K inversion interval, phase-sensitive states and reference convention are used. The required energy arithmetic introduces no new thermodynamic approximation. Phase classification must match exactly.

| Quantity                              | Absolute allowance | Relative allowance |
| ------------------------------------- | -----------------: | -----------------: |
| Recovered T                           |             1e-7 K |                  0 |
| Final H residual                      |         1e-6 J/mol |                  0 |
| Beta and each phase mole fraction     |               1e-9 |               1e-9 |
| Z                                     |              1e-10 |               1e-9 |
| H_eq and ideal/residual/total phase h |         1e-7 J/mol |              1e-11 |

The combined state allowance is `atol + rtol*abs(reference)`. Zero quantities use absolute allowance. A conservative arithmetic budget is `A_Q = 64*epsilon*max(1, abs(Q), abs(F*H_in), abs(F*H_out)) W`, with double-precision epsilon = 2.220446049250313e-16. Scaling by endpoint enthalpy flows accounts for subtraction cancellation; the factor 64 provides headroom for the short multiplication/division/subtraction chain, without widening thermodynamic acceptance. Decimal arithmetic independently checks that budget.

Forward closure requires `abs(R_Q) <= A_Q`; target-H reconstruction requires error ≤ A_Q/F. Inverse closure requires `abs(R_H) <= 1e-6 J/mol` and `abs(R_Q,inverse) <= F*1e-6 + A_Q W`. Thus the energy allowance is propagated from the independent PH residual rather than chosen as a percentage of duty. It remains meaningful for Q = 0.

| Maximum absolute error        |         Observed value | Case                    |
| ----------------------------- | ---------------------: | ----------------------- |
| T                             | 1.5063505998114124e-11 | ZERO_DUTY               |
| beta                          | 6.5299328444456961e-14 | BUBBLE_ADJACENT_HEATING |
| composition                   | 4.8960835385969403e-14 | ZERO_DUTY               |
| Z                             |  7.382983113757291e-15 | BUBBLE_ADJACENT_HEATING |
| h                             | 2.7794158086180687e-09 | ZERO_DUTY               |
| forward_R_Q_W                 |                      0 | VAPOR_HEATING           |
| inverse_R_Q_W                 | 2.5611370801925659e-07 | ZERO_DUTY               |
| inverse_R_H_J_mol             | 2.5611370801925659e-09 | ZERO_DUTY               |
| H_target_reconstruction_J_mol | 4.5474735088646412e-13 | VAPOR_COOLING           |

The h maximum covers phase ideal, residual and total enthalpy comparisons. Full equilibrium-H recovery is additionally controlled by the final R_H and target reconstruction gates. All round-trip allowances passed; no tolerance was changed.

## Negative specifications

Each rejected specification publishes only a failure status/message, with no accepted outlet. Nonfinite inputs are encoded as `nan`/`inf` strings in JSON and converted to floats only when evaluating the controlled test.

| Case                    | Expected and observed status  |
| ----------------------- | ----------------------------- |
| ZERO_FLOW               | invalid_flow                  |
| NEGATIVE_FLOW           | invalid_flow                  |
| NAN_FLOW                | invalid_flow                  |
| INFINITE_FLOW           | invalid_flow                  |
| INVALID_INLET_PRESSURE  | invalid_pressure              |
| INVALID_OUTLET_PRESSURE | invalid_pressure              |
| INVALID_COMPOSITION     | invalid_composition           |
| UNSUPPORTED_WATER       | unsupported_component         |
| INLET_CP_EXTRAPOLATION  | temperature_domain_invalid    |
| UNBRACKETED_HIGH_TARGET | enthalpy_target_not_bracketed |
| UNBRACKETED_LOW_TARGET  | enthalpy_target_not_bracketed |
| NAN_DUTY                | invalid_duty                  |
| INFINITE_DUTY           | invalid_duty                  |
| OUTLET_CP_EXTRAPOLATION | temperature_domain_invalid    |
| PURE_COEXISTENCE_GAP    | ph_nonconvergence             |

The pure n-hexane coexistence target is exactly the excluded independent Pre-M11 target at 1000 Pa, converted to Q from its independently evaluated inlet H. The inherited solver returns `ph_nonconvergence`; this is a controlled qualification boundary, not permission to interpolate through the latent-heat gap. The pressure, flow, composition, unsupported-water, out-of-domain, nonfinite-duty and unbracketed-target guards all pass.

## Automated checks and determinism

The first fresh interpreter run generated the new JSON. A second fresh interpreter independently rebuilt it and required byte-for-byte equality without rewriting the artifact. The independent test run rebuilt it again. All three runs passed. No random state, production result, network lookup or timestamp enters the frozen content.

There are 36 new tests: 14 individually named positive cases, 15 individually named negative specifications, and seven tests for byte-identical reproduction, zero duty, flow scaling, reverse heating/cooling, required transitions, pressure change and an inverse interface without forward Tout or loaded production modules.

| Gate run in this task                             | Result                                                                                                                   |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Pre-M12 independent tests                         | 36 passed                                                                                                                |
| Independent second-process reference reproduction | Byte-for-byte identical                                                                                                  |
| Pre-M8 independent tests                          | 7 passed                                                                                                                 |
| M8 production comparison                          | 122 comparisons passed                                                                                                   |
| Pre-M8.1 independent tests                        | 28 passed                                                                                                                |
| M8.1 production comparison                        | 325 comparisons passed                                                                                                   |
| Pre-M8.2 independent tests                        | 25 passed                                                                                                                |
| M8.2 production comparison                        | 749 comparisons passed                                                                                                   |
| M8.2 nine-grid high-accuracy scan                 | 1152/1152 successful; zero unexpected failures; four vapor-parent/liquid-trial and one liquid-parent/vapor-trial restart |
| M9 equipment integration tests                    | 7 passed                                                                                                                 |
| Pre-M10 independent tests                         | 23 passed                                                                                                                |
| M10 production comparison                         | 1526 comparisons passed                                                                                                  |
| Pre-M11 independent tests                         | 55 passed                                                                                                                |
| M11 production comparison                         | 29 positive, nine negative/gap, 401 positive field comparisons passed                                                    |
| Focused M11 production tests                      | 53 passed                                                                                                                |

All comparator runs omitted write/output options. Some unchanged historical comparators print milestone-era pending-status text; that output is not a reversal of the human validation already recorded in the current milestone documents. No historical documentation was changed here. Website, browser and production-build suites were not rerun: this task adds independent reference artifacts only and the requested thermodynamic regression gates all passed.

Final checks cover Markdown formatting, canonical JSON serialization, Python AST syntax and indentation, new-file trailing whitespace/terminal newlines, `git diff --check`, Git status, and SHA-256 verification of every pre-existing tracked file against the clean-tree snapshot taken before creating these files. No existing tracked file changed. No staging, commit or push occurred.

## Reproduction

From the repository root, using the existing isolated environment:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/heater_cooler_energy/reference.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/heater_cooler_energy -p 'test_*.py' -v
```

The first command recomputes and compares the complete frozen JSON without writing. Initial generation used the same command with `--write`; routine review should omit that flag. On a clean machine, provision an isolated environment from the new `requirements.txt` before reproduction; no production dependency installation is required. Reproduction itself is offline.

Historical commands executed, without reference regeneration:

```sh
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_boundary -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_boundary/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_pt_vapor_parent -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_pt_vapor_parent/compare_production.py --case all
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_equilibrium_separator.py' -v
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_caloric -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_caloric/compare_production.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/peng_robinson_ph -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/peng_robinson_ph/compare_production.py --case summary
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -p 'test_pr_ph_flash.py' -v
```

## Scope and next action

Qualification is limited to the selected steady-state methane/n-hexane explicit-zero-kij energy balances and controlled failures. Finite PH scanning does not establish global uniqueness for arbitrary thermodynamic states. No water, VLLE, three-phase, arbitrary petroleum mixture, nonzero-kij, critical-region, retrograde or pure coexistence interpolation capability is added. No exchanger area, U, LMTD, pinch, geometry, hydraulic correlation, utilities, fouling, mechanical design, holdup, thermal inertia or dynamics is qualified.

The frozen evidence is ready for human review and a separately authorized production M12 integration. Such integration must consume the established production PT/PH/caloric capabilities and independently pass these energy and state-recovery gates. This task implements none of that integration. Existing process equipment and Stream Table behavior remain unchanged.
