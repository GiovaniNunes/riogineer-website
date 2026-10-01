# Pre-M20 — Separator-liquid contract and local admissibility qualification

**Decision A: the contract and local guards are sufficient for a future production
implementation restricted to the explicitly qualified cases.** This is a study-only
result, not M20 implementation, current M19 support, a configurable operating domain
or installation approval. The two known 8 MPa PS failures remain unresolved and
excluded. No shared solver, model, schema, version, frontend or service was changed.

## Baseline and preserved evidence

Branch `main`, HEAD `2ca429d2e947c1c50219bfe65cd0d87f2a7cc7f0`, message
`Complete Milestone 19 variable-composition pump and record human acceptance`.
Index empty. Initial working changes were the first uncommitted Pre-M20 report,
its benchmark directory, its master-context entry and the unrelated modified
`next-env.d.ts` and `tsconfig.json`. This continuation did not require a remote
operation; the first study's live-remote verification remains historical evidence.

The extension captured hashes of tracked working files **and all existing untracked
study files** before writing study code. The entire existing master-context prefix
is protected by length/hash, permitting only this task's append. All prior evidence,
including the original report/plan/code/artifacts and both unrelated files, remains
byte-for-byte preserved. The first matrix was neither regenerated nor rerun.
Applicable AGENTS.md and targeted master-context, stream, separator, pump, stability,
EOS and inverse interfaces were inspected. No stage, commit, push, deployment or
service start/stop occurred.

## Existing interface problem and proposed minimal addition

`network_models.state_from_rates` already carries authoritative component mass
rates, total flow, mass fractions, T, absolute P and enthalpy flow. M17 adds molecular
properties to its serialized streams. These fields should be reused. M19's
`variable_pump_energy.inlet_specification` rejects any non-null Hdot and lacks a
way to distinguish upstream-derived energy from a competing independent input.

Propose one additive `state_context` object alongside the unchanged stream fields:

| Field | Proposed meaning |
| --- | --- |
| `specification_kind` | `independent_PT`, `independent_caloric`, or `upstream_derived`; this adapter handles only the last |
| `phase` | Material phase identity; `liquid` for the separator liquid port |
| `saturation` | `source_vle` if supported by source phase evidence; otherwise `unknown`, never automatically “subcooled” |
| `source` | Existing `run_id`, `input_sha256`, `requirements_sha256`, plus equipment ID, outlet port ID and material stream ID |
| `thermodynamics` | Existing `property_package`, `component_dataset`, `caloric_dataset`, `caloric_reference` and complete explicit `bip` specification |

These are proposed names, not a new production schema/version. The representation
reuses existing thermodynamic identifiers and result identities. Parent diagnostics,
phase compositions/Z/H/S, TPD trials, fugacity residuals, local witnesses and inverse
trials are **internal validation evidence**, not mandatory duplicated public fields.
Entropy is obtained from the resolved qualified source phase and fresh calorics;
an extra independent entropy specification is not admitted by this adapter.

Authoritative quantities remain component rates in kg/h, T in K, P in Pa absolute
and upstream Hdot in W. M7 derives molar flow (kmol/h, converted by /3.6 to mol/s),
molar fractions (mol/mol), mass fractions and molecular weight (kg/kmol). Total
mass and any serialized molecular properties must agree. No rates or composition
are normalized to a different state. The property and source-unit declarations
are checked; unknown added stream specifications reject rather than being ignored.

The three input kinds have distinct semantics:

- Independent PT: PT defines calorics; independent H/S are not additional free inputs.
- Independent caloric: requires its own qualified specification/solver contract;
  it is not accepted as an upstream-derived state merely by changing a label.
- Upstream derived: Hdot is a calculated conserved quantity with an identified
  source/model/reference. It is retained and checked against F·hphase and fresh
  thermodynamics. Agreement makes it corroborating information, not an inconsistent
  extra specification. Disagreement rejects; it is never discarded or replaced.

An absent phase has zero component/total/molar flow and Hdot, with unavailable
composition/specific H/S. Its outlet identity may still exist, but it is not a
pumpable material feed. The adapter checks absent-phase energy semantics and
returns `absent_liquid`, without inventing intensive properties.

## Source identity and consistency adapter

The old compatibility extraction did not retain original calculation UUIDs. This
study therefore captures **12 actual fresh M17 results**: the eight selected source
recipes, an absent-liquid control and three explicitly scaled PH_FLASH recipes.
Each retains its real run ID, semantic input hash, requirements hash, source equipment
and port mapping. No historical run ID is invented. The full immutable captures are
in `sources.json`. Their numerical results reproduce exactly while newly generated
UUIDs are intentionally not substituted into the frozen capture.

`adapter.representation` copies the complete actual stream and adds only context.
`adapter.verify` receives that stream, a separately resolved source result and the
expected current calculation identity. The caller must obtain that identity from
the current result/execution registry; self-asserted IDs in an incoming stream are
insufficient. A source lookup and current-revision check are integration duties,
not a cryptographic authenticity claim about editable JSON.

The adapter verifies source/run/input/requirements identity; completed separator
model and liquid port; explicit component/EOS/kij/caloric compatibility; source and
phase T/P; component/total/molar inventories and composition; phase fraction versus
parent feed flow; phase H and Hdot; property units; and fresh liquid and parent
PT/caloric agreement. Fresh calls use the received coordinates after strict source
agreement, so serialization roundoff does not trigger coordinate snapping. Matching
provenance alone cannot override thermodynamic contradiction: a coherently forged
upstream H and Hdot still fails fresh caloric verification.

Predeclared tolerances (absolute plus the stated relative term):

| Comparison | Allowance |
| --- | --- |
| Source T | 1e-8 K + 1e-12·|T| |
| Source P | 1e-5 Pa + 1e-12·|P| |
| Component/total mass | 1e-8 kg/h + 1e-12·|rate| |
| Molar flow | 1e-10 mol/s + 1e-12·|F| |
| Source mole/mass fractions | 1e-12 absolute |
| H | B(H)=1e-6 + 1e-11·|H| J/mol |
| S | 1e-8 + 1e-11·|S| J/(mol K) |
| Hdot | F·B(H) + 64 epsilon·max(1 W, |Hdot|) |
| Independent state comparison | Inherited T 1e-7 K, composition/beta 2e-9, Z 2e-10+1e-9·|Z|, and H/S above |

Native JSON round trips and 15-significant-digit serialization of T/P, component
rates, total flow and Hdot pass representative saturated, compressed and small-flow
cases without modifying the received values. Deliberate process changes exceed
these allowances and reject. These are numerical consistency allowances, not a
permission to condition a stream. Missing context/source identifiers/H or parent
evidence returns `missing_evidence`; stale or incompatible/inconsistent evidence
returns `contradictory_evidence`; phase absence/non-liquid returns `rejected`;
unresolved numerical evidence returns `unresolved`. No failed call returns an
accepted pump outlet.

## Local liquid-admissibility policy

Every admitted state requires a fresh successful high-accuracy equilibrium PT,
liquid phase identity, beta exactly zero, converged stable TPD, PIP>1 and valid
phase/caloric payload. Neither a tiny beta nor an ambiguous label is corrected.

**Saturated source liquid:** additionally reproduce the actual parent equilibrium
at the same received T/P and parent overall composition. Verify converged stable common-tangent TPD, both positive
parent phase fractions, source liquid composition/calorics and a nontrivial
vapor–liquid branch. Use the roots returned by fresh parent PT in the unchanged EOS
fugacity evaluator; require log-fugacity equality residual ≤2e-10 and composition
and Z gaps >0.01. The maximum measured residual is approximately 7.01e-13.

For the separated liquid composition x, the verified parent pair (x,y) at T/P is
local bubble-state evidence at that same T/composition. It is not necessary to
solve a new bubble pressure just to rediscover a known equilibrium parent. No
liquid root is forced, and source provenance is never used to bypass fresh phase
or consistency checks. This admits verified saturated liquid despite zero positive
subcooling and distinguishes it from bulk VL entering a pump.

**Compressed-liquid witness:** where no saturated parent is applicable, require a
fresh stable single-liquid PT/caloric witness at the same T and composition and
0.9999 times the actual pressure, in addition to the actual-state checks. This
provides local sampled evidence below the operating pressure for the finite
qualified cases. It does **not** measure bubble pressure, prove monotonicity between
points, establish a universal phase envelope or provide a hydraulic reserve.
Independent branch evidence corroborates the actual tested states. No fixed
16 MPa witness is used.

**Unresolved:** an apparently single-liquid state without verified saturated-source
evidence and without a successful liquid witness is unresolved. A PT/stability or
fugacity/branch failure is also unresolved. A genuine VL state, vapor or absent
liquid rejects. These rules are deliberately incomplete outside the qualified
cases; a small genuinely positive margin may remain unresolved.

The first study's 1 Pa boundary diagnostic band is not a runtime admission reserve.
This adapter does not use a bubble-pressure tolerance to shift a stream. It uses
source-association tolerances, fresh equilibrium, fugacity/branch criteria and local
witnesses. No NPSH, static head, suction losses, cooler, cavitation safety, pump
sizing or continuous pressure-path feasibility is inferred.

## Production-callable versus reference-only capabilities

Unchanged production callables used:

- M7 molecular enrichment and existing result/input identities.
- `PengRobinsonProvider.equilibrium_caloric_PT`, with high-accuracy settings.
- Existing PT stability/PIP diagnostics and EOS `mixture`/`fugacity` using the
  roots already selected by fresh parent equilibrium.
- Public PS/PH calls and the existing pump inverse-diagnostic validator.

There is no production bubble-pressure provider capability. For this **restricted
case set**, parent equilibrium supplies saturated branch evidence and local PT
witnesses supply the compressed-state screen, so a new boundary solver is not a
prerequisite. The direct boundary root refinement and library bubble-pressure
calculations remain independent qualification tools only. Neither runtime proposal
module imports Thermo/SciPy, reads frozen artifacts or uses reference values.

A request for arbitrary streams, quantified subcooling, tighter-margin admission,
critical-region discrimination or a configurable domain could require an additional
qualified boundary/state capability. Decision A must not be extended to those tasks.

## Matrix, independent evidence and results

`PLAN.md` fixes the contract, numerical allowances and compact matrix before
comparison. The first study's **30 accepted tuples** are reused as independent
expectations; all receive adapter checks and fresh local inlet/ideal/actual endpoint
checks. Their exact source input fingerprints, discharge pressure and efficiency
are listed in the new ledger. This includes sub-0.01 methane, the historical
small-flow outlet and explicitly separate scaled source cases.

Eight fresh pump runs exercise four representative source recipes at identity and
+1 MPa: PT_VL_HEATING, PH_FLASH, PT_BUBBLE_BELOW and PT_DEW_BELOW. The last retains
its actual approximately 0.13330553 mol/s liquid. The positive-rise runs retain
PT H/S → PS → efficiency target H → PH, without a phase-specific fallback. Full
inverse scans, fresh-final acceptance, material conservation, target recovery,
entropy, reconstructed efficiency and E/dH work checks remain mandatory. E retains
the first study's 500 K residual propagation term and 1e-4 relative screen.

Fluid power remains F(H2−H1), with independently checked H1 matching the retained
upstream Hdot/F. The energy check uses the **actual upstream Hdot**, not a silently
recomputed replacement; its allowance includes the upstream consistency budget.
Exact identity returns the complete received stream, zero power, null reconstructed
efficiency and no PS/PH calls. Positive-rise output contains calculated material
properties; it does not falsely retain a separator-source context as a pump-output
producer identity. A future process adapter must create its own valid output context.

New independent calculations are limited to **72 genuinely new witness/probe
states**: 44 distinct lower-pressure witnesses and 28 boundary perturbations for
four sources. Boundary pressure comes from the unchanged first study's independent
refinement. At fixed T, pressure probes span relative −0.001, −1e-6, 0, +1e-6,
+0.001; temperature probes are ±0.01 K at the independent bubble pressure. These
are diagnostic states, not altered source products. The old inverse matrix is not
rerun. The explicit zero-kij methane/n-hexane PR model, component data, ideal Cp,
H/S references, units and independent environment remain those of the first study;
installed versions and Thermo/Cp hashes are verified against that frozen evidence.

Results:

- All 30 original accepted tuples pass fresh adapter/local endpoint qualification.
- Eleven present captured source outlets pass; the absent-liquid capture rejects.
- All eight fresh pump/identity cases pass their independent comparisons.
- **2,543 applicable numerical/phase comparisons pass**, with no loosened tolerance.
- Twenty-seven frozen contract negatives reject in their expected category.
- Of the 72 standalone probes without saturated source evidence, 43 pass the
  compressed witness, 19 reject as VL and ten remain boundary-unresolved.
- Both historical 8 MPa PS failures remain explicitly unresolved, copied with
  diagnostics and hashes from preserved evidence, not rerun or relabelled.

At the four independently located bubble centers, standalone local checks correctly
remain unresolved without source-phase evidence; the corresponding actual verified
saturated outlets can be accepted through the separate parent-evidence branch.
All −0.001 pressure probes are VL/rejected and all +0.001 pressure probes pass the
compressed witness. Tiny positive pressure offsets may remain unresolved. In the
warm PT_DEW_BELOW case, T−0.01 K is VL while T+0.01 K is single liquid but fails the
margin witness. This observed local temperature behavior is retained; the policy
never assumes that cooling invariably establishes liquid service.

The 1000 Pa tuple retains its limited first-study work margin, approximately
E/dH=8.47e-5. It is one qualified tuple, not a replacement general floor. The two
8 MPa states still have full-scan PT holes at approximately 461.905/466.667 K;
no scan narrowing, bridging, reference substitution or solver patch is introduced.
No successful endpoint collection proves an entire continuous compression path.
Numerical model agreement remains distinct from experimental validation.

## Exact future production implications and remaining work

A separately authorized narrow M20 implementation could admit only the explicit
source-input-fingerprint/P2/eta combinations in `candidate_ledger.json`, with the
new provenance/consistency and local guards mandatory. The numerical states must
still be calculated, not looked up. Fresh run identities can change; source semantic
input identity, model basis and validated material state must remain qualified.
A narrower selection may retain the existing general 10000 Pa floor and omit the
single 1000 Pa exception. No interpolation between listed cases is qualified.

Affected interfaces, proposed only:

1. `network_models.state_from_rates` / stream serialization conventions: preserve
   existing fields and add producer-derived state context without changing legacy
   independent-PT semantics.
2. `separator_energy_process.calculate`: emit source liquid phase/context using
   actual run/input identity and existing thermodynamics; preserve absent phases.
3. A future separately scoped pump adapter, alongside
   `variable_pump_energy.inlet_specification`: accept verified upstream-derived
   calorics through an explicit path; do not remove M18/M19 guards or reinterpret
   their existing versions. Reuse PS/PH and inverse validation unchanged.
4. The execution/result resolver must supply current source calculation identities
   and resolved parent evidence, invalidate stale dependencies and identify the
   actual producer of pump outputs. Current bounded separator/pump topologies do
   not implement this mixed-equipment propagation.
5. `src/lib/digital-engineer/contracts.ts` and generated requirements/flowsheet/results
   schemas would need an explicitly versioned additive proposal and compatibility
   tests in that implementation request. None changed in this study.

Production registration, atomic error serialization, schema/version work, source
freshness resolution, mixed-network scheduling, UI exposure and implementation
regression/human acceptance remain future work. A new broad thermodynamic boundary
solver is not required for the tested restricted policy. No current M19 wrapper
acceptance or production integration is claimed by this study-only orchestration.

## Verification, artifact integrity and reproduction

**Twelve focused test methods pass.** Coverage includes untouched actual streams,
27 contradictory/missing-evidence scenarios, 15-digit serialization without
snapping, identity with PS/PH calls forbidden, injected PT/witness failure without
accepted outlet, absent liquid, false saturation claims, actual vapor/bulk VL,
all frozen comparisons, boundary sides, explicit known PS failures and absence of
reference-library/file dependencies in the runtime proposal, and comparison ordering
across three Python hash seeds. Injected failures
are policy tests and are not presented as physical reference cases.

All 12 source calculations reproduce their streams, equipment, units, status and
semantic input/requirements hashes exactly; fresh UUIDs are expected to differ,
and captured originals remain unchanged. The independent reference, production
comparison and candidate ledger reproduce byte-for-byte in fresh processes.
An initial reproduction mismatch exposed unordered liquid/vapor comparison-record
iteration across Python hash seeds. Sorting that record order fixed the extension
serializer without changing thermodynamic values or tolerances; a regression test
checks seeds 0, 1 and 2. The original first-study matrix/artifacts were neither
rerun nor regenerated.
Python AST/whitespace and `git diff --check` pass. No full application, browser or
historical regression suite was run.

Frozen extension SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| `sources.json` | `711e821235fc75744274e8ca8fda36fb532c485ea736be1c94a8e8eb27cd8e2a` |
| `reference.json` | `c0c1492808e0bbe6fce1cc60e5d9de878b90a7efb79eb9877194f0fa0db9b161` |
| `production.json` | `ecb5a0b2ea83bd740cb1f7dd9cffdf18a0abf9e3bb275cb315ebe626bf9ff070` |
| `candidate_ledger.json` | `d616934cb7bdf53eab3d616be11011abaabb66ee9d74e53ababba89f0f79787d` |

From repository root, all defaults verify without overwriting:

```sh
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/capture_sources.py
.local/pre-m8-venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/reference.py
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/compare.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/low_pressure_separator_pump/phase_contract -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/verify.py
```

Source creation uses `--capture` once and refuses to overwrite its artifact.
Reference/comparison/ledger initial generation uses `--write` in that order, only
inside the new extension. See its README for environment and immutable-source
semantics. The ledger hashes every other extension file; preservation checks
protect all original tracked and untracked evidence and the existing master prefix.

Exact changed-file inventory for this continuation (19 paths):

- `PRE_MILESTONE_20_SEPARATOR_LIQUID_CONTRACT_QUALIFICATION.md` — new report.
- `docs/RIOGINEER_MASTER_CONTEXT.md` — concise appended entry, prior prefix intact.
- `benchmarks/low_pressure_separator_pump/phase_contract/PLAN.md`.
- `benchmarks/low_pressure_separator_pump/phase_contract/README.md`.
- `benchmarks/low_pressure_separator_pump/phase_contract/common.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/adapter.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/pump.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/capture_sources.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/reference.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/compare.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/negatives.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/test_contract.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/verify.py`.
- `benchmarks/low_pressure_separator_pump/phase_contract/baseline.json`.
- `benchmarks/low_pressure_separator_pump/phase_contract/preservation.json`.
- `benchmarks/low_pressure_separator_pump/phase_contract/sources.json`.
- `benchmarks/low_pressure_separator_pump/phase_contract/reference.json`.
- `benchmarks/low_pressure_separator_pump/phase_contract/production.json`.
- `benchmarks/low_pressure_separator_pump/phase_contract/candidate_ledger.json`.

Final status: branch/HEAD unchanged, index empty. Both Pre-M20 reports and the
benchmark directory remain untracked; the master context is modified. The initial
`next-env.d.ts` and `tsconfig.json` modifications remain byte-identical, with SHA-256
`1f2e4a6d7f55de2de72375901050f2af22ed89992a781fce74d6e6a4d3fc94f0` and
`e2a28ab5d02bb5b555a28523be8786d9dc3a400fe125f14602261e24a6288126` respectively.
No production/historical evidence changed; nothing was staged, committed, pushed
or deployed. All user services were left untouched.
