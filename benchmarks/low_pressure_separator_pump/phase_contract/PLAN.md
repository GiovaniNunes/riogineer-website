# Phase-aware contract study: policy fixed before comparison

Preserve the first study and reuse its 30 accepted tuples as numerical expectations.
No configurable envelope. Capture fresh full separator results for the eight
selected historical sources, one absent-liquid control and three explicitly
scaled PH_FLASH source calculations; retain actual run_id/input hashes. Never
invent a historical run ID missing from the earlier extracted artifacts.

Proposed public addition is state_context: specification_kind, phase identity,
saturation evidence status, source calculation/equipment/port/stream identifiers,
and existing thermodynamic provenance. Existing stream rates/T/P/Hdot remain
unchanged. Internal evidence is the resolved source result, phase H/S/Z/composition,
fresh parent and liquid PT, stability/fugacity diagnostics and local PT witnesses.

Adapter tolerances declared in SI: T 1e-8 K +1e-12 relative; P 1e-5 Pa +1e-12
relative; component/total mass 1e-8 kg/h +1e-12 relative; F 1e-10 mol/s +1e-12
relative; mole/mass fractions 1e-12 absolute. H 1e-6+1e-11|H| J/mol;
S 1e-8+1e-11|S| J/mol/K; Hdot F*B(H)+64 epsilon*max(1,|Hdot|) W.
These permit serialization roundoff, not process conditioning. Reject material
changes. Units and model/provenance identifiers require exact agreement.

Local production-only proposal: require fresh high-accuracy equilibrium PT,
converged stable liquid, PIP>1, zero beta and consistent payload. For saturated
liquid require verified source parent VL at the same T/P, source liquid composition,
fresh parent phase caloric agreement, both positive parent phase fractions,
nontrivial vapor/liquid composition and Z gaps >0.01 and log-fugacity equality
<=2e-10. Phase roots must come from the fresh parent PT result, never be forced.
This directly identifies a bubble state for the separated liquid composition;
no library bubble pressure or reference lookup enters the adapter.

For compressed states require an additional same-T/z production PT liquid witness
at 0.9999*P, with the same stability/PIP gates. This is a sampled lower-pressure
witness, not a quantified saturation pressure, hydraulic reserve or proof of
monotonicity. Independently corroborate its local branch at the finite qualified
states. Without saturated source evidence or a liquid witness return unresolved;
bulk VL/vapor/absent reject. No tiny-beta clipping and no 16 MPa witness.

Apply the local policy freshly to every distinct endpoint of the 30 old accepted
tuples; reuse frozen independent endpoint/boundary expectations without rerunning
all inverse paths. Fresh complete pump paths: PT_VL_HEATING +1 MPa (z<.01),
PH_FLASH +1 MPa, PT_BUBBLE_BELOW +1 MPa, PT_DEW_BELOW +1 MPa (small flow),
and their four identities. Retain both old 8 MPa failures explicitly as unresolved
frozen evidence; do not rerun the old entire matrix or replace them.

New independent states: same-T lower-pressure witnesses for distinct endpoints;
for PT_VL_HEATING, PH_FLASH, PT_BUBBLE_BELOW and PT_DEW_BELOW use each independently
frozen bubble pressure and probes P*(1±1e-3), P*(1±1e-6), center, and T±0.01 K
at that pressure. These are diagnostics, never edited source streams. Standard
inherited comparison allowances apply; classification mismatch is retained,
not normalized. Missing/stale/wrong source, T/P/z/rates/total/Hdot/units/model,
phase/boundary and caloric-reference mutations receive explicit negative tests.
