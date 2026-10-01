# Predeclared extension plan

Defined before production comparison. Historical evidence and tolerances remain frozen.

- Fixed equimolar methane/n-hexane, explicit zero kij and existing PR/caloric data.
- Candidate inputs: 300–350 K, 20–25 MPa inlet, discharge up to 30 MPa,
  efficiency 0.6–1, flow 5–200 mol/s. Exact identity is separate.
- Candidate operational positive-rise floor: 10,000 Pa. Examine 10, 1,000 and
  10,000 Pa at four limiting T/P/efficiency combinations. Do not claim this is
  the smallest possible floor.
- Sixteen coupled corners (T, inlet P, eta, minimum/maximum rise), four identities,
  six interiors, eight independent off-grid holdouts and twelve conditioning
  entries; duplicate intensive inputs reuse explicitly identified evidence.
- Flow: 5, 17.3, 83.7, 137.2 and 200 mol/s, using accepted intensive states once.
- State-temperature guard candidate: 300–370 K for all three states. Independently
  examine bubble pressure over that full range, including outlet temperatures.
- Boundary evidence: 0.5 K grid, separate deterministic off-grid points, two-sided
  phase probes, pressure/temperature saturation round trips and derivative probes.
  Investigate 16 MPa as a conservative engineering ceiling, not the largest
  sampled value or a rigorous global bound. Require a fresh stable-liquid PT
  witness at the same temperature and 16 MPa for each actual state.
- Inherit first-study field comparison gates unchanged. Retain 0.01% work-budget
  criterion. Runtime screening adds full PS-residual capacity mapped through
  dh=T ds, eta amplification, PH-residual capacity and arithmetic roundoff to
  endpoint comparison allowances. This is an engineering acceptance policy,
  not a proven uncertainty bound. Test independent residual perturbations.
- Preserve complete default 200–500 K scans. Every failed candidate remains in
  the ledger. No production solver modification, reference interpolation as a
  calculation, or exact-input allowlist.
