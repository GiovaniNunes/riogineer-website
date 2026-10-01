# M19 qualification plan (before production comparison)

Baseline: 2a2f4cc9c3e827187af1d64be9f1773b23389618.
Exploration is retained in exploration.json. Candidate methane mole fraction:
0.01–0.55 inclusive, hexane balance; pure endpoints excluded. Initial exploration
finds 16 MPa witnesses become VL at z=0.60 and warm states, and methane-rich
single_liquid labels are not trustworthy service admission by themselves.

Retain M18 operating/state/work/inverse limits provisionally. Independently examine
all reached-state temperatures 300–370 K across composition, rather than only
pump inlet temperatures. Boundary grid: z=0.01+0.02*j, j=0..27; T=300+2.5*j,
j=0..28. Twelve deterministic composition/temperature holdouts. Each point:
nontrivial bubble branch, independent coexistence-equation residual <=2e-10,
pressure agreement <=1000 Pa, VL/liquid PT sides at .999/1.001 bubble pressure,
16 MPa liquid witness, composition gap >0.30 and Z gap >0.24. These branch-gap
thresholds screen the sampled candidate region, not general critical criteria.
Central derivative probes: +/-0.01 K, +/-1e-5 mole fraction. Prospective engineering
slope allowances: 100000 Pa/K and 40000000 Pa per unit mole fraction. Nearest-node
allowance =125000+400000 Pa, plus 1000 Pa numerical allowance. Require sampled
maximum +526000 Pa <16 MPa. This is an empirical screening reserve, not a global
bound; fresh high_accuracy actual-state and witness guards remain mandatory.

Pump matrix: 32 full coupled composition/operating corners (z endpoints, T/P
endpoints, eta .6/1, floor/max rise), eight independent off-grid holdouts, four
interior recipes, four identities, equimolar compatibility, flow 5/17.3/200,
sub-floor cases and excluded composition/endpoints. All outcomes retained.
Record inverse/property/phase failures without relaxing tolerances. Independent
PS/PH reuse full default domains and prior frozen field allowances unchanged.
Boundary/non-liquid challenges supplement in-domain cases; synthetic ambiguity,
missing-fresh-final and nonconvergence tests must be labelled synthetic.

Run actual M17 PT/PH separator cases from the existing frozen matrix. Preserve
actual liquid output mass rates, T/P/H and phase convention when assessing direct
compatibility; quantify each pressure/temperature/flow/composition mismatch.
No production mixed network. Reference generation imports no production code.
Freeze independent evidence before production-model implementation/comparison.
