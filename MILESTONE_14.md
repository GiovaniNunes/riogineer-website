# Milestone 14 — Production rigorous Peng–Robinson compressor

Automated M14 acceptance: COMPLETE — 2026-09-30.

M14 human-operated validation: COMPLETE — 2026-09-30.

## Human-operated validation — 2026-09-30

The human reviewer reported successful execution and inspection of `canonical`, `efficiency`, `pressure`, `flow`, `ideal`, `service_scope`, `negative` and `summary`. All eight reviewed modes passed and were consistent with the automated qualification. This is a separate human validation record; the automated acceptance evidence below remains unchanged.

The canonical review confirmed `rigorous_isentropic_pr@1.0` with z = [0.9 methane, 0.1 n-hexane], T1 = 300 K, P1 = 100000 Pa, P2 = 300000 Pa, eta = 0.8 and 100 mol/s. The visible sequence was inlet PT/M10 -> H1,S1; flash_PS/M13 -> T2s,H2s; the efficiency equation -> H2_target; flash_PH/M11 -> actual outlet. Both nested solvers reported their respective capabilities, `pt_profile = high_accuracy` and `candidate_count = 1`.

Observed values were approximately T2s = 362.102637081 K, T2 = 376.432590149 K, H1 = 53.023122416 J/mol, H2s = 3055.289647116 J/mol and H2 = 3805.856278291 J/mol. Isentropic and actual fluid powers were approximately 300226.652470 W and 375283.315588 W; reconstructed eta and eta_power were approximately 0.8, with an energy residual of approximately 1.55e-11 W. The canonical case passed against frozen Pre-M14 evidence.

- Efficiency: eta = 0.60, 0.70, 0.75, 0.80, 0.85, 0.90 and 1.00 passed. T2s and H2s remained invariant; increasing efficiency decreased actual T2, H2 and fluid power.
- Pressure: ratios 1.5, 2, 3, 5 and 8 passed. T2s, H2s, T2, H2 and fluid power increased over the frozen regular-vapor matrix; the highest reviewed outlet temperature remained within 200–500 K.
- Flow: 1, 10, 100 and 200 mol/s passed the frozen scaling checks. Thermodynamic states remained invariant within recorded allowances and fluid power scaled linearly; the canonical 100/200 mol/s scaling error was 0.0 W.
- Ideal limit: eta = 1 reproduced T2 approximately equal to T2s, H2 approximately equal to H2s and S2 approximately equal to S1. Actual and isentropic fluid powers agreed, and both efficiency reconstructions were approximately 1. Nested PS/PH succeeded with high_accuracy PT and one candidate.
- Service scope: single vapor was accepted; single liquid and vapor-liquid compressor service were rejected without an accepted outlet. `VL_THERMODYNAMIC_ONLY` remained independently calculable thermodynamics and rejected compressor service.
- Negatives: all 43 cases passed without an accepted compressor outlet. Reviewed categories covered invalid flow, inlet/outlet pressure including P2 <= P1, efficiency, composition, water/components, nonzero BIP and temperature; liquid/VL service; unbracketed PS/PH; controlled PT/PS/PH failures; PS/PH coexistence gaps; PS ambiguity and property-evaluation holes.

The human-reviewed final summary reported **19 vapor positives, 43 negatives, one VL service rejection, 1,083 numerical comparisons and 18 byte-identical call-order checks**, with determinism/call order passed. Frozen reference SHA-256 remained `31972f6057f1c4191e25dc8fec317a0e21b20816d0a7c6513649fb7b630ed8cc`.

All reported maxima passed their frozen allowances, including outlet-H error 8.549250196665525e-11 J/mol and fluid-power error 8.60018189996481e-09 W (both `RATIO_1.5`), PS entropy residual 9.43245481721533e-12 J/(mol K) (`BOUNDARY_VAPOR`) and PH enthalpy residual 2.546585164964199e-11 J/mol (`PURE_HEXANE`). These are reviewed summary entries; separate execution of the `pure` and `boundary` human-review modes is not recorded.

This validation does not broaden the frozen methane/n-hexane, constant-zero-kij, bounded 200–500 K, vapor-only service qualification. All documented exclusions remain, including no electrical-power calculation or network compression optimization. The historical ideal-gas model remains distinct, and the additive requirements 1.6 / flowsheet 1.7 / results 1.8 contract history is unchanged.

## Baseline and authorization

The clean, synchronized baseline was `d78fef6ed001b0e3520d719def5f80ff7be3d4d8`, following M13 commit `94682d9d2bb499eea2d850d09831f553f694f01c`. Local and remote baseline agreement was verified before implementation. The original contract blocker was resolved by the separate explicit authorization for an additive rigorous compressor branch. Contract-only qualification passed before production implementation: 22 tests in the new compressor, historical compressor and M12 contract suites, plus generated-schema parity.

The historical `ideal_gas_isentropic_efficiency@1.0` model retains its Cp, heat-capacity-ratio, mechanical-efficiency, input, result and execution semantics. Historical tests were not edited. No historical documents require migration.

## Versioned process contracts

The previous latest requirements/flowsheet/results versions were 1.5/1.6/1.7. The new branch uses **requirements 1.6, flowsheet 1.7, results 1.8**, profile `compressor_energy`, engine version 1.7.0 and explicit equipment model `rigorous_isentropic_pr@1.0`. The validation envelope is unchanged; its embedded requirements union includes the new version. Existing six requirements, seven flowsheet and eleven results schema alternatives remain structurally identical. The schema generator and error schema are unchanged.

The required equipment parameters are `outlet_pressure_Pa_abs`, `isentropic_efficiency`, `property_package` and `bip`. They use PR `peng_robinson@1.0` and the existing explicit constant-zero methane/n-hexane BIP provenance structure. The inlet stream owns its component mass rates, temperature and absolute pressure. The new branch does not require Cp, k or mechanical efficiency. Pressure ratio is derived, and `0 < eta <= 1` and `P2 > P1 > 0` are enforced.

The structured result contains `inlet`, `isentropic_outlet` and `actual_outlet`. Each reuses the existing caloric state representation and adds `S_eq_J_mol_K` and phase `s_ig_J_mol_K`, `s_res_J_mol_K`, `s_J_mol_K`; M12 serialization remains unchanged. Existing state fields carry pressure, temperature, z, phase classification, beta, equilibrium H, phase composition/Z/H and PT evidence.

Exact compressor detail fields are `property_package`, `component_dataset`, `molecular_provider`, `caloric_dataset`, `caloric_reference`, `bip`, `F_mol_s`, the three states, `pressure_ratio`, `isentropic_efficiency`, `reconstructed_efficiency`, `eta_power`, `efficiency_allowance`, `H_out_target_J_mol`, `delta_H_is_J_mol`, `delta_H_actual_J_mol`, `isentropic_fluid_power_W`, `fluid_power_W`, `delta_S_actual_J_mol_K`, `energy_residual_W`, `energy_allowance_W`, `power_identity_residual_W`, `power_identity_allowance_W`, `ps` and `ph`.

Both inverse records include status, capability, high-accuracy PT profile, candidate count, selected/final brackets, root iterations and evaluation count. PS adds `entropy_residual_J_mol_K`; PH adds `enthalpy_residual_J_mol`. Complete scan arrays are not embedded. Equipment retains mass balance, zero duty and `work_W`; the process energy record labels fluid power and `positive_work = work_into_process`. Global stream and Stream Table contracts are unchanged.

## Runtime architecture and limits

The existing requirements builder, flowsheet validator, equipment registry and public calculation API dispatch the explicit rigorous model to the dedicated compressor module. The historical branch remains separate, with no fallback.

1. Recompute inlet PT/M10 from the stream with `SolverSettings.high_accuracy()` to obtain H1 and S1.
2. Call existing M13 `flash_PS(P2, S1, z)` to obtain the isentropic state and H2s.
3. Form `H2_target = H1 + (H2s - H1) / eta`.
4. Call existing M11 `flash_PH(P2, H2_target, z)` for the actual outlet.
5. Use M7 `MolecularCompositionProvider` to convert the material flow from kg/h through kmol/h to mol/s: `F = molar_flow_kmol_h * 1000 / 3600`.
6. Report actual fluid power `F * (H2 - H1)` and isentropic fluid power `F * (H2s - H1)`, positive into the material stream.

Each accepted state must be single vapor, finite and within 200–500 K. PS/PH must each have one qualified candidate, high-accuracy nested PT and a fresh final evaluation. Mass rates, total molar flow and overall composition are conserved; the actual outlet pressure is P2. Recovered H/S, efficiency, power, energy closure, temperature ordering and entropy generation are checked before any accepted outlet is returned. Nested failures remain failures, including at the public process boundary.

Scope is one source, one adiabatic compressor and one sink for the frozen methane/n-hexane matrix, explicit constant zero kij, including pure endpoints represented on the same component basis. Liquid and VL compressor service are rejected. The separately calculable VL thermodynamic study does not authorize VL equipment service. This is not universal compressor qualification. No water, arbitrary petroleum mixtures, arbitrary nonzero BIPs, VLLE, three-phase equilibrium, critical-region compressor behavior, coexistence interpolation, heat loss, mechanical/motor/driver efficiency or gearbox losses are qualified. No compressor maps, surge/choke, speed dependence, sizing, polytropic model, staging, intercooling, anti-surge recycle or network pressure solution is implemented. No pump, valve, turbine or later milestone was started. No new production dependency or PT/RR/stability/M10/PH/PS equation was introduced.

## Numerical authority and tolerances

The immutable independent authority is `benchmarks/compressor_energy/methane_nhexane_compressor_reference.json` with SHA-256:

`31972f6057f1c4191e25dc8fec317a0e21b20816d0a7c6513649fb7b630ed8cc`

The original independent reference, solver, tests and Pre-M14 report are unchanged. A fresh independent reference run reproduced the file byte-for-byte: 19 vapor positives, one separate VL study, 43 negatives, 918 independent numerical checks and 18 byte-identical call-order checks.

All production comparisons use frozen field allowances. Derived enthalpy/entropy differences use sums of their state allowances. Fresh PS entropy and PH enthalpy residual gates retain 1e-8 J/(mol K) and 1e-6 J/mol respectively. The production efficiency closure bound is `eta * 1e-6 / abs(H2-H1) + 64*epsilon`; this follows from the final PH residual divided by actual enthalpy rise. The energy roundoff bound is `64*epsilon*max(1, abs(power), abs(F*H1), abs(F*H2))`. The power-identity allowance adds `F*1e-6` to that roundoff bound. Entropy ordering permits the sum of two 1e-8 entropy residual bounds, and the eta=1 temperature check uses the existing 1e-7 K scale. These equipment checks do not change any upstream solver tolerance or frozen allowance.

Flow conversion comparisons allow 64 machine epsilons at the flow scale. Thermodynamic states across the flow series are compared to identical independent frozen states using their recorded field allowances; floating-point M7 mass-to-molar projection is not required to be byte-identical across different flows. No M7 normalization or thermodynamic implementation was changed.

## Production matrix

All 19 positives traverse normal requirements -> flowsheet -> registry -> public validated result. All 43 negative cases reject without an accepted outlet. The separate VL study is rejected as compressor service. The production artifact records **1,083 numerical comparisons**, phase/provenance checks, flow scaling and 18 byte-identical call-order checks.

Canonical inputs: P1 = 100000 Pa absolute, T1 = 300 K, P2 = 300000 Pa absolute, z = (0.9 methane, 0.1 n-hexane), eta = 0.8 and F = 100 mol/s.

| State             |         T (K) |     H (J/mol) | S (J/(mol K)) |
| ----------------- | ------------: | ------------: | ------------: |
| inlet             |           300 | 53.0231224156 | 3.02630436218 |
| isentropic_outlet | 362.102637081 | 3055.28964712 | 3.02630436218 |
| actual_outlet     | 376.432590149 | 3805.85627829 | 5.05899561958 |

Canonical isentropic fluid power is 300226.65247 W; actual fluid power is 375283.315588 W. The energy residual is 1.54614099301e-11 W. All three states are single vapor.

Lower eta increases actual H2, temperature and fluid power while preserving the isentropic state. Increasing pressure ratio increases required work over the qualified series. Eta=1 reproduces the isentropic state. Pure methane, pure n-hexane and the boundary-vapor case pass and remain vapor throughout.

| Case           |  eta | P2/P1 | F (mol/s) |        T2 (K) | Fluid power (W) |
| -------------- | ---: | ----: | --------: | ------------: | --------------: |
| CANONICAL      |  0.8 |   3.0 |       100 | 376.432590149 |   375283.315588 |
| ETA_0.6        |  0.6 |   3.0 |       100 | 399.632816387 |   500377.754117 |
| ETA_0.7        |  0.7 |   3.0 |       100 |  386.47734471 |   428895.217814 |
| ETA_0.75       | 0.75 |   3.0 |       100 | 381.139544208 |   400302.203293 |
| ETA_0.85       | 0.85 |   3.0 |       100 | 372.250760463 |   353207.826435 |
| ETA_0.9        |  0.9 |   3.0 |       100 |   368.5107388 |   333585.169411 |
| ETA_1.0        |  1.0 |   3.0 |       100 | 362.102637081 |    300226.65247 |
| RATIO_1.5      |  0.8 |   1.5 |       100 | 327.584953778 |   130445.247766 |
| RATIO_2.0      |  0.8 |   2.0 |       100 | 347.616538345 |   228657.491291 |
| RATIO_5.0      |  0.8 |   5.0 |       100 | 413.617182619 |   574046.662737 |
| RATIO_8.0      |  0.8 |   8.0 |       100 | 448.630499171 |    771141.39576 |
| FLOW_1.0       |  0.8 |   3.0 |         1 | 376.432590149 |   3752.83315588 |
| FLOW_10.0      |  0.8 |   3.0 |        10 | 376.432590149 |   37528.3315588 |
| FLOW_200.0     |  0.8 |   3.0 |       200 | 376.432590149 |   750566.631175 |
| BALANCED       |  0.8 |   2.0 |       100 | 375.673654665 |   255052.897826 |
| HEXANE_RICH    |  0.8 |   2.0 |       100 |  380.89135614 |   258277.021619 |
| PURE_METHANE   |  0.8 |   3.0 |       100 | 401.962737251 |     387717.0799 |
| PURE_HEXANE    |  0.8 |   2.0 |       100 | 315.062005125 |   220299.287523 |
| BOUNDARY_VAPOR |  0.8 |   1.5 |       100 | 337.165696334 |   135668.638552 |

Flow scaling uses the canonical 100 mol/s case. The 200 mol/s power is exactly doubled.

| Case       | Absolute scaling error (W) | Frozen allowance (W) |
| ---------- | -------------------------: | -------------------: |
| FLOW_1.0   |          4.54747350886e-13 |    5.40844706377e-11 |
| FLOW_10.0  |          7.27595761418e-12 |    5.40844706377e-10 |
| CANONICAL  |                          0 |    5.40844706377e-09 |
| FLOW_200.0 |                          0 |    1.08168941275e-08 |

## Negative mappings and failure propagation

Production inputs are mass streams. Negative/nonfinite mole fractions map to negative/nonfinite component mass rates and are rejected as invalid flow; inconsistent sums remain invalid composition. The immutable independent category is retained in the artifact. Liquid/VL independent `compressor_state_invalid` cases map to explicit equipment `compressor_service_scope` rejection.

Controlled PT/PS/PH failure injections test equipment propagation. Coexistence-gap cases invoke the real production inverse solvers with protected historical gap targets; ambiguity/property-hole cases invoke real PS with a controlled caloric evaluator. They are labeled synthetic mappings rather than natural compressor trajectories. Real unbracketed PS/PH cases use normal production input states. Additional tests corrupt nominally successful nested states/diagnostics and verify rejection. Public process tests confirm failure returns no accepted result.

| Frozen case    | Production stage | Production status             | Controlled mapping |
| -------------- | ---------------- | ----------------------------- | ------------------ |
| FLOW_0.0       | specification    | invalid_flow                  | no                 |
| FLOW_-1.0      | specification    | invalid_flow                  | no                 |
| FLOW_NaN       | specification    | invalid_flow                  | no                 |
| FLOW_Infinity  | specification    | invalid_flow                  | no                 |
| FLOW_-Infinity | specification    | invalid_flow                  | no                 |
| P1_0.0         | specification    | invalid_pressure              | no                 |
| P1_-1.0        | specification    | invalid_pressure              | no                 |
| P1_NaN         | specification    | invalid_pressure              | no                 |
| P1_Infinity    | specification    | invalid_pressure              | no                 |
| P1_-Infinity   | specification    | invalid_pressure              | no                 |
| P2_0.0         | specification    | invalid_pressure              | no                 |
| P2_-1.0        | specification    | invalid_pressure              | no                 |
| P2_NaN         | specification    | invalid_pressure              | no                 |
| P2_Infinity    | specification    | invalid_pressure              | no                 |
| P2_-Infinity   | specification    | invalid_pressure              | no                 |
| P2_100000.0    | specification    | invalid_pressure              | no                 |
| P2_50000.0     | specification    | invalid_pressure              | no                 |
| ETA_0.0        | specification    | invalid_efficiency            | no                 |
| ETA_-0.1       | specification    | invalid_efficiency            | no                 |
| ETA_1.01       | specification    | invalid_efficiency            | no                 |
| ETA_NaN        | specification    | invalid_efficiency            | no                 |
| ETA_Infinity   | specification    | invalid_efficiency            | no                 |
| ETA_-Infinity  | specification    | invalid_efficiency            | no                 |
| BAD_SUM        | specification    | invalid_composition           | no                 |
| NEGATIVE_Z     | specification    | invalid_flow                  | no                 |
| NONFINITE_Z    | specification    | invalid_flow                  | no                 |
| WATER          | specification    | unsupported_component         | no                 |
| UNKNOWN        | specification    | unsupported_component         | no                 |
| NONZERO_KIJ    | specification    | unsupported_bip               | no                 |
| T_LOW          | specification    | temperature_domain_invalid    | no                 |
| T_HIGH         | specification    | temperature_domain_invalid    | no                 |
| T_NAN          | specification    | temperature_domain_invalid    | no                 |
| LIQUID_SERVICE | inlet_PT         | compressor_service_scope      | no                 |
| VL_SERVICE     | inlet_PT         | compressor_service_scope      | no                 |
| PS_UNBRACKETED | isentropic_PS    | entropy_target_not_bracketed  | no                 |
| PH_UNBRACKETED | actual_PH        | enthalpy_target_not_bracketed | no                 |
| PT_INJECTED    | inlet_PT         | controlled_pt_failure         | yes                |
| PS_INJECTED    | isentropic_PS    | controlled_solver_failure     | yes                |
| PH_INJECTED    | actual_PH        | controlled_solver_failure     | yes                |
| PS_GAP         | isentropic_PS    | ps_nonconvergence             | yes                |
| PH_GAP         | actual_PH        | ph_nonconvergence             | yes                |
| PS_AMBIGUOUS   | isentropic_PS    | ambiguous_ps_root             | yes                |
| PS_HOLE        | isentropic_PS    | property_evaluation_failed    | yes                |

## Maximum numerical errors

All entries passed. Allowances shown belong to the governing case. Residual and identity rows compare against zero or the specified identity; other rows compare production with independent values. The complete per-case comparisons are in the production artifact.

| Field                    | Maximum absolute error | Governing case |         Allowance |
| ------------------------ | ---------------------: | -------------- | ----------------: |
| H_out_target_J_mol       |      4.54747350886e-12 | BOUNDARY_VAPOR | 4.94536655998e-05 |
| delta_H_actual_J_mol     |      8.59472493175e-11 | RATIO_1.5      | 0.000178306946141 |
| delta_H_is_J_mol         |      6.36646291241e-12 | HEXANE_RICH    | 4.61217486107e-05 |
| delta_S_actual_J_mol_K   |      2.43804976208e-13 | RATIO_1.5      | 5.58227708645e-07 |
| energy_residual          |      7.36690708436e-11 | RATIO_5.0      | 8.23304411282e-09 |
| eta_identity             |      9.32587340685e-15 | PURE_HEXANE    | 3.63156556432e-10 |
| eta_power                |      5.39568389968e-14 | RATIO_1.5      | 1.34405368893e-07 |
| eta_power_identity       |      9.21485110439e-15 | PURE_HEXANE    | 3.63156556432e-10 |
| eta_specified            |                      0 | CANONICAL      |                 0 |
| fluid_power_W            |      8.60018189996e-09 | RATIO_1.5      |   0.0178306965432 |
| inlet.H                  |      6.36646291241e-12 | HEXANE_RICH    | 1.07205213009e-06 |
| inlet.P                  |                      0 | CANONICAL      |                 0 |
| inlet.S                  |       3.5527136788e-14 | BALANCED       | 1.02083050783e-08 |
| inlet.T                  |                      0 | CANONICAL      |             1e-07 |
| inlet.beta               |                      0 | CANONICAL      |             2e-09 |
| inlet.vapor.H            |      6.36646291241e-12 | HEXANE_RICH    | 1.07205213009e-06 |
| inlet.vapor.S            |       3.5527136788e-14 | BALANCED       | 1.02083050783e-08 |
| inlet.vapor.Z            |      1.11022302463e-16 | CANONICAL      | 1.19562900038e-09 |
| inlet.vapor.q0           |                      0 | CANONICAL      |             2e-09 |
| inlet.vapor.q1           |      1.38777878078e-17 | FLOW_10.0      |             2e-09 |
| inlet.z.methane          |      1.11022302463e-16 | FLOW_10.0      |             2e-09 |
| inlet.z.n_hexane         |                      0 | CANONICAL      |             2e-09 |
| isentropic.H             |      3.18323145621e-12 | BOUNDARY_VAPOR | 3.77249671332e-05 |
| isentropic.P             |                      0 | CANONICAL      |                 0 |
| isentropic.S             |      7.81597009336e-14 | HEXANE_RICH    | 1.26855672067e-07 |
| isentropic.T             |                      0 | CANONICAL      | 7.60084903559e-07 |
| isentropic.beta          |                      0 | CANONICAL      |             2e-09 |
| isentropic.vapor.H       |      3.18323145621e-12 | BOUNDARY_VAPOR | 3.77249671332e-05 |
| isentropic.vapor.S       |      7.81597009336e-14 | HEXANE_RICH    | 1.26855672067e-07 |
| isentropic.vapor.Z       |      2.22044604925e-16 | CANONICAL      | 1.23761606766e-09 |
| isentropic.vapor.q0      |                      0 | CANONICAL      |             2e-09 |
| isentropic.vapor.q1      |      1.38777878078e-17 | FLOW_10.0      |             2e-09 |
| isentropic.z.methane     |      1.11022302463e-16 | FLOW_10.0      |             2e-09 |
| isentropic.z.n_hexane    |                      0 | CANONICAL      |             2e-09 |
| isentropic_fluid_power_W |      6.40284270048e-10 | HEXANE_RICH    |  0.00461217486107 |
| mass_residual            |                      0 | CANONICAL      |                 0 |
| molar_flow               |                      0 | CANONICAL      | 1.42108547152e-12 |
| out_composition.methane  |      1.11022302463e-16 | FLOW_10.0      |             2e-09 |
| out_composition.n_hexane |                      0 | CANONICAL      |             2e-09 |
| out_molar_flow           |                      0 | CANONICAL      | 1.42108547152e-12 |
| outlet.H                 |      8.54925019667e-11 | RATIO_1.5      |  0.00017730641591 |
| outlet.P                 |                      0 | CANONICAL      |                 0 |
| outlet.S                 |      2.22488694135e-13 | RATIO_1.5      | 5.48197445601e-07 |
| outlet.T                 |      1.76214598469e-12 | RATIO_1.5      | 3.70412215095e-06 |
| outlet.beta              |                      0 | CANONICAL      |             2e-09 |
| outlet.vapor.H           |      8.54925019667e-11 | RATIO_1.5      |  0.00017730641591 |
| outlet.vapor.S           |      2.22488694135e-13 | RATIO_1.5      | 5.48197445601e-07 |
| outlet.vapor.Z           |      3.33066907388e-16 | HEXANE_RICH    | 1.66996453963e-09 |
| outlet.vapor.q0          |                      0 | CANONICAL      |             2e-09 |
| outlet.vapor.q1          |      1.38777878078e-17 | FLOW_10.0      |             2e-09 |
| outlet.z.methane         |      1.11022302463e-16 | FLOW_10.0      |             2e-09 |
| outlet.z.n_hexane        |                      0 | CANONICAL      |             2e-09 |
| ph.residual              |      2.54658516496e-11 | PURE_HEXANE    |             1e-06 |
| power_identity           |      2.56113708019e-09 | PURE_HEXANE    | 0.000100003502298 |
| pressure_ratio           |                      0 | CANONICAL      |                 0 |
| ps.residual              |      9.43245481722e-12 | BOUNDARY_VAPOR |             1e-08 |
| reconstructed_efficiency |      5.39568389968e-14 | RATIO_1.5      | 1.34405368893e-07 |

## Determinism and regression gates

A fresh `--verify` run reproduced the production artifact byte-for-byte. The only removed public-result field is the intentionally random `run_id`; implementation and input hashes remain included. No timestamp or machine-specific absolute path is serialized. Eighteen comparisons repeat canonical, pure methane and boundary-vapor cases after historical compression, another positive, eta=1, invalid input, PS failure and PH failure.

The following table records automated acceptance, when human review was still pending; the separate completed human validation is recorded above. Initial new-harness issues were corrected: a synthetic ambiguity fixture now supplies required high-accuracy PT provenance, and flow comparisons use frozen field allowances rather than an unjustified cross-flow byte-equality assertion. The browser check exposed the missing new-version PFD dispatch and the minimal version guard was added. No historical tolerance/test or thermodynamic code was changed for those fixes.

| Gate                                                  | Result                                                                                                        |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Historical production `compression`                   | 7 tests passed, unchanged                                                                                     |
| Historical production `pr_flash`                      | 26 tests passed, unchanged                                                                                    |
| Historical production `pr_caloric`                    | 35 tests passed, unchanged                                                                                    |
| Historical production `pr_ph_flash`                   | 53 tests passed, unchanged                                                                                    |
| Historical production `heater_cooler_energy`          | 36 tests passed, unchanged                                                                                    |
| Historical production `pr_ps_flash`                   | 55 tests passed, unchanged                                                                                    |
| Independent `peng_robinson`                           | 7 tests passed, unchanged                                                                                     |
| Independent `peng_robinson_pt_boundary`               | 28 tests passed, unchanged                                                                                    |
| Independent `peng_robinson_pt_vapor_parent`           | 25 tests passed, unchanged                                                                                    |
| Independent `peng_robinson_caloric`                   | 23 tests passed, unchanged                                                                                    |
| Independent `peng_robinson_ph`                        | 55 tests passed, unchanged                                                                                    |
| Independent `heater_cooler_energy`                    | 36 tests passed, unchanged                                                                                    |
| Independent `peng_robinson_ps`                        | 46 tests passed, unchanged                                                                                    |
| Independent `compressor_energy`                       | 66 tests passed, unchanged                                                                                    |
| Focused M14 Python                                    | 75 tests passed                                                                                               |
| Complete Python suite                                 | 414 tests passed                                                                                              |
| Historical production comparators                     | All seven PT/boundary/vapor-parent/M10/M11/M12/M13 comparators passed                                         |
| TypeScript                                            | 219 tests in 20 files passed                                                                                  |
| Browser                                               | 32 tests passed                                                                                               |
| Contract-only gate before implementation              | 22 tests in three suites passed                                                                               |
| Schema parity / lint / type checks                    | Passed                                                                                                        |
| Repository formatting / Python syntax and indentation | Passed                                                                                                        |
| Production build                                      | Passed                                                                                                        |
| Production smoke                                      | 17 pages, 17 PNG cards, links, 404s, preview indexing and disabled contact delivery passed                    |
| All ten human-review CLI modes                        | Executed successfully as automated checks; human review still pending                                         |
| Changed-line whitespace / git diff --check            | Passed                                                                                                        |
| Protected-file integrity                              | All historical tests, independent evidence, thermodynamics, dependencies and unauthorized contracts unchanged |

The protected inventory covers all 304 baseline tracked files. Only the explicitly authorized existing files below differ; all other baseline hashes are unchanged. No historical test exception was needed. Nothing is staged, committed or pushed. Generated incidental files were not retained.

## Exact changed files

| Path                                                        | Change and purpose                                                            |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `src/lib/digital-engineer/contracts.ts`                     | Modified: additive versioned rigorous input, flowsheet and result branches.   |
| `contracts/v1/requirements.schema.json`                     | Modified: generated requirements 1.6 branch.                                  |
| `contracts/v1/flowsheet.schema.json`                        | Modified: generated flowsheet 1.7 branch.                                     |
| `contracts/v1/results.schema.json`                          | Modified: generated results 1.8 branch.                                       |
| `contracts/v1/validation.schema.json`                       | Modified: generated embedded requirements union.                              |
| `engine/riogineer_engine/core.py`                           | Modified: route new versions through the public process API.                  |
| `engine/riogineer_engine/network.py`                        | Modified: new profile build/validation and dedicated calculation dispatch.    |
| `engine/riogineer_engine/network_models.py`                 | Modified: explicit rigorous model dispatch; historical calculation unchanged. |
| `engine/riogineer_engine/compressor_energy.py`              | New: PT/PS/PH composition, service checks and equipment closure.              |
| `engine/riogineer_engine/compressor_process.py`             | New: narrow process execution and versioned result serialization.             |
| `engine/tests/test_compressor_energy.py`                    | New: 75 frozen-matrix, integration and failure tests.                         |
| `benchmarks/compressor_energy/compare_production.py`        | New: immutable-reference comparator and human-review modes.                   |
| `benchmarks/compressor_energy/production_comparison.json`   | New: deterministic production evidence, separate from independent truth.      |
| `src/app/digital-engineer/rigorous-compression-results.tsx` | New: minimal three-state and fluid-power results view.                        |
| `src/app/digital-engineer/workspace.tsx`                    | Modified: render rigorous result and accurate PR energy identity.             |
| `src/app/digital-engineer/pfd.tsx`                          | Modified: dispatch flowsheet 1.7 to existing graph/compressor symbol.         |
| `tests/compressor-energy-contracts.test.ts`                 | New: rigorous/historical contract separation and serialization checks.        |
| `tests/e2e/compressor-energy.spec.ts`                       | New: normal workspace calculation, result identity, power and PFD check.      |
| `MILESTONE_14.md`                                           | New: automated qualification, scope, evidence and human-review instructions.  |
| `docs/RIOGINEER_MASTER_CONTEXT.md`                          | Modified: minimal M14 automated status and limitations.                       |

## Human-operated validation commands

Run from the repository root. All commands were exercised successfully by automation; this does not constitute human-operated validation. Each mode recomputes the qualified matrix.

```sh
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case canonical
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case efficiency
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case pressure
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case flow
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case ideal
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case pure
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case boundary
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case service_scope
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case negative
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --case summary
```

For fresh artifact verification:

```sh
engine/.venv/bin/python -B benchmarks/compressor_energy/compare_production.py --verify --case summary
```

M14 human-operated validation: COMPLETE — 2026-09-30. No subsequent milestone is authorized by this acceptance record.
