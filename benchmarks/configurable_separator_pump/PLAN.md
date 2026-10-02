# Predeclared PRE-M21 qualification policy

Study only; no production edits. Baseline captured before experiments.

Reuse all 30 M20 anchors, both recorded 8 MPa paths, and deliberately selected
one-factor/interior/holdout variations around the existing PT, PH, cold 6 MPa
and warm near-dew families. Do not infer a rectangle from their extrema.
New source recipes require separate independent separator comparisons; pump
comparisons use the actual retained production liquid coordinates as inputs.
A pump success alone never qualifies the separator recipe or integrated adapter.

Acceptance gates fixed before generation: inherited pump T 1e-7 K, H
1e-6+1e-11|H| J/mol, S 1e-8+1e-11|S| J/(mol K), composition/beta 2e-9,
Z 2e-10+1e-9|Z|; PS residual 1e-8, PH residual 1e-6. Source comparisons
use the independent M17 propagated allowances at the actual source recipe.
Require all comparisons, M20 source/local/energy/work guards, and finite outputs.
The 500 K entropy-residual propagation and E/dH <=1e-4 remain unchanged.
Identity preserves the received stream and zero work. eta in [0.6,1].
Reject pressure decrease, absent liquid and unresolved small work. Preserve failures.

Prototype: inspect the complete standard scan; only refine adjacent valid sign
brackets, never join across a failed sample. Refuse competing sampled roots.
Bisection must fail on any encountered hole and use unchanged tolerances with a
fresh final PT/caloric/stability and compressed witness. Missing scan coverage
remains explicitly incomplete: a local candidate is not a globally unique solution
or production acceptance. Use no oracle target to drive prototype PS/PH.
Independently inspect failed-point neighborhoods at offsets -0.1,-0.01,0,0.01,0.1 K.
Record independent phase, entropy residual and sampled monotonicity; no finite
sampling proof of absence of other roots. Probe five intermediate pressures for
each challenge as sampled path evidence only.

Candidates: accepted means a supported numerical exact candidate with independent
source/path and unchanged callable guards, NOT application admission. Rejected
means an explicit contract/physical/numerical-resolution guard. Unresolved means
missing reference/comparison/solver evidence. Only integrated M20 anchors can be
called production-supported. Prototype successes cannot change that disposition.

## Targeted iteration-budget diagnostic (declared after observing the root cause)

The 8 MPa failures reach the existing 100-iteration PT cap with converged initial
stability and unmet 1e-12 fugacity tolerance. Separately evaluate complete 64-point
PS scans and local roots at PT budgets 200 and 400 through public immutable
SolverSettings, only in the new benchmark. Keep all tolerances and physics fixed.
Compare sampled S/phase to the independent scan, retain failures, and recheck the
root with default production PT/local guards. This is sensitivity evidence, not a
new production default or a qualification of all states between samples. It does
not change the primary matrix, acceptance criteria or frozen failure outcomes.
