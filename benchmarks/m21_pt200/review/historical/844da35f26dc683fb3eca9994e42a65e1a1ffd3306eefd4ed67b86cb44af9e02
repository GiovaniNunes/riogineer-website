# Pre-M20 study policy fixed before numerical comparison

Study only. Preserve all 24 actual M17 liquid streams from the frozen M19
compatibility artifact, including absent phases and below-0.01 methane fractions.
Screen unchanged liquid-composition PT in both implementations. Record every
M19 scalar mismatch and actual wrapper rejection with enthalpy retained.

Select PT_VL_HEATING, PT_VL_INLET_EQUAL, PT_VAPOR_INLET_COOLING, PH_FLASH,
PH_HEXANE_RICH, PT_BUBBLE_BELOW, PT_BUBBLE_ABOVE and PT_DEW_BELOW.
Each gets +10000 Pa and +1 MPa at eta 0.8 with actual historical flow.
These cover minimum prior work floor and moderate transfer pressure increase;
no 30 MPa discharge extrapolation. Add identities for each, eta 0.6/1 at
PH_FLASH +1 MPa, and PH_FLASH rises 10/100/1000 Pa. Explicit scaled copies
of PH_FLASH +1 MPa use 5/17.3/200 mol/s. Absent-liquid, bulk VL, vapor,
eta 0/0.59/1.01 and pressure decrease are controlled negatives.
No configurable domain is proposed, therefore no domain holdout claim.

Inherited endpoint tolerances: T 1e-7 K, H 1e-6+1e-11|H| J/mol,
S 1e-8+1e-11|S| J/mol/K, Z 2e-10+1e-9|Z|, z/beta 2e-9.
PS/PH residuals 1e-8 J/mol/K and 1e-6 J/mol. Work engineering allowance
uses full 500 K inverse domain (not M19's 370 K) in the entropy propagation;
require E/dh <=1e-4. eta 0.6–1 only. Inverses and endpoint phase gates must
pass. No tolerance relaxation or tiny-beta normalization is authorized.

Independent local bubble pressure: retain library solve, nontrivial phase gap,
fugacity residual and PT sides at factors 0.999/1.001. Pressure tolerance for
saturation diagnosis is 1 Pa; it is not a pressure correction. Screen phase
label sensitivity separately at relative pressure offsets ±1e-3, ±1e-6,
±1e-9, zero, and both production precision profiles at zero. Diagnostic probes
never substitute for an actual stream. Saturated provenance remains distinct
from subcooling even when bulk PT reports single liquid.

Accept only numerical tuples with all comparisons, liquid endpoint and work
checks passing; saturated inlet semantics unresolved means no production
extension yet. A failed equilibrium PT representation does not prove the
separated phase is a genuine two-phase feed. Retain all failures and diagnostics.

## Targeted refinement after the first screen

Retain the raw library boundary residuals and solve the two coexistence fugacity
equations with SciPy root at each inventory state, initialized from the library
bubble branch. Require residual <=2e-10, pressure agreement <=1 Pa, nontrivial
composition/Z gaps and stable PT sides. This resolves the specific excessive raw
residuals at PT_VAPOR_INLET_COOLING and PH_HEXANE_RICH; no tolerance is loosened.
Add the two selected cold bubble inlets at 8 MPa discharge to test the specific
PS scan limitation previously recorded in Pre-M18. They remain in the ledger
whether successful or not. No wider pressure sweep follows from this probe.
