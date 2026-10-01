# Pre-Milestone 17 — Two-phase separator energy qualification

Independent numerical qualification completed on 2026-10-01. This report establishes
reference equipment evidence; production integration and regression acceptance are
recorded separately in `MILESTONE_17.md`. No human-operated acceptance is claimed.

## Baseline and independence

Starting production baseline: `c0f03ca6d5fc022f97aac2b2df4115b0a38e3b4f` (completed M16).
The independent reference was generated and reproduced before production integration
was compared against it. Expected values never call a production separator, PR
flash or caloric routine. The new directory is `benchmarks/two_phase_separator_energy/`.

`reference.py` reuses the independent Thermo-based `EntropyPT` oracle and SciPy PH
inversion from prior benchmark directories, plus the independently established M16
boundary experiments. External versions: Thermo 0.6.0, Chemicals 1.5.2, NumPy 2.2.6,
SciPy 1.15.3. Exact inherited dependency pins and third-party notices accompany it.
These remain isolated in `.local/pre-m8-venv`; no production dependency was added.
The frozen JSON records reference source hashes and package versions.

EOS conventions are canonical Peng–Robinson coefficients 0.45724/0.07780, the
existing methane/n-hexane component constants, explicit symmetric constant zero
kij, and the M10 ideal-Cp plus PR-departure caloric basis. Pure ideal-gas H and S are
zero at 298.15 K and 101325 Pa. The independent caloric oracle explicitly reconciles
that reference with library direct calorics before comparison; no unexplained
enthalpy-reference offset is fitted to production. Zero kij is a mathematical
benchmark, not fitted physical interaction data.

Frozen artifact: `methane_nhexane_separator_energy_reference.json`.
SHA-256: `f6dfea8e4dad2729cef6ee33096a3f8c9fe76abfe8059e0dd8f18a6258242122`.
`production_comparison.json` is separate evidence, never reference truth.

## Equipment reconstruction and units

Inputs are molar flow F in mol/s, molar overall z, actual inlet Pin/Tin and specified
separator Pout. PT additionally specifies Tout; adiabatic PH does not.

For vapor fraction beta, the vapor/liquid molar rates are F beta and F (1-beta).
For each phase, component mass rate in kg/h is `F_phase * q_i * MW_i * 3.6`, using
MW in kg/kmol (16.0428 for methane; 86.17536 for n-hexane).
Phase enthalpy flow in W is `F_phase * h_phase[J/mol]`.

`Q = Hdot_vapor + Hdot_liquid - Hdot_inlet`, positive into the equipment.
PT calculates Q; PH imposes Q=0 and solves at Pout for Htarget=Hin. Component and
energy inventories are reconstructed independently from the external phase states.
Absent phases retain zero material and enthalpy flows, with null composition and
specific enthalpy. Positive feed only; no water, shaft work or kinetic/potential terms.

## Matrix and qualification results

All **24 cases** reproduce exactly from the independent tool. Both modes cover
liquid, vapor and VL outlets, equal pressure and pressure reduction. The matrix
establishes L/V/VL inlet categories for this separator; M16's single-phase valve
service restriction is not transplanted into separator service.

- Seven base PT cases: VL heating, liquid cooling, vaporization, VL inlet at equal
  conditions, vapor-inlet cooling, double flow and low flow.
- Nine base PH cases: liquid-to-VL pressure reduction, equal-pressure liquid,
  vapor reduction/equal pressure, VL equal/reduced pressure, double/low flow and
  hexane-rich composition.
- Eight boundary cases: PT and PH at 0.05 K below/above independently determined
  bubble and dew temperatures at 6 MPa, equimolar feed. These retain their prior
  independent provenance and are explicitly tested as M17 equipment cases.

Flow rates: 5, 100 and 200 mol/s. Composition examples include 0.1, 0.5 and 0.9
methane mole fraction. Evaluations remain within 200–500 K; pressures span the
listed frozen states from 1000 Pa to 30 MPa. This is a case matrix, not blanket
qualification of a rectangular operating envelope or arbitrary compositions.
Pure coexistence gaps remain unsupported; no pure-fluid lever-rule solver is added.

Examples from independent evidence:

| Case              | Outlet |        T (K) |          Q (W) |
| ----------------- | ------ | -----------: | -------------: |
| PT_VL_HEATING     | VL     |          350 | 1832535.619763 |
| PT_LIQUID_COOLING | liquid |          280 | -235686.025424 |
| PT_VAPOR          | vapor  |          400 | 2648659.128483 |
| PH_FLASH          | VL     | 291.74213866 |      0 imposed |
| PH_VL_REDUCTION   | VL     | 291.50166153 |      0 imposed |

Each PH case is independently repeated with a 256-point scan and bisection instead
of the primary 128-point scan and Brent solver. Reference expected values are not
initialized with production temperatures. The external inverse conservatively
rejects scan holes; none of these accepted cases requires narrowing its 200–500 K
interval. Production retains M16's more capable valid-interval policy unchanged.

## Tolerances and failures

Inherited base comparison allowances: temperature 1e-7 K; H 1e-6 J/mol plus
1e-11 relative; S 1e-8 J/(mol K) plus 1e-11 relative; beta and composition 2e-9;
Z 2e-10 plus 1e-9 relative. PH root residual is 1e-6 J/mol.
For PH, local independent ±0.001 K derivatives propagate inlet-H/PH uncertainty
to outlet temperature and properties, using the existing Pre-M16 conditioning
method without weakening it. Both perturbations must retain phase classification.

Phase-flow allowances propagate beta and composition errors through the explicit
molar-to-mass equations. Phase enthalpy-flow allowances propagate beta and phase-H
uncertainty; duty allowance adds both phase-flow energy allowances and inlet-H
uncertainty. These dimensioned allowances are frozen per case. No tolerance is
selected from production disagreement.

Independent tests cover exact reproduction, all phase categories, signed PT duty,
material/energy identities and null absent phases. Parameterized specification
negatives cover missing/contradictory fields, zero/negative/nonfinite flow, invalid
pressure/T/composition and unsupported fields. Independent inverse tests distinguish
synthetic unbracketed targets, ambiguous roots and property holes from a real
pure-n-hexane coexistence gap. Synthetic failures test policy, not physical cases.
Production-specific topology/ports, zero-inventory water, failure publication and
schema checks are recorded in M17.

Six independent test methods pass. Production agreement is **969 numerical checks
across 24 cases**, covering inlet H, outlet T/phase composition/fractions, phase H,
phase/component/total flows, enthalpy flows, duty and adiabatic closure. PT closure
alone is an accounting identity; independently compared phase H and duty provide
the additional numerical evidence.

## Reproduction

```sh
.local/pre-m8-venv/bin/python -B benchmarks/two_phase_separator_energy/reference.py
.local/pre-m8-venv/bin/python -B -m unittest discover -s benchmarks/two_phase_separator_energy -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/two_phase_separator_energy/compare_production.py --verify
```

Default reference execution verifies frozen bytes. `--write` is an explicit
artifact-generation operation, not part of normal verification. The production
comparator likewise separates `--write` from `--verify`.
