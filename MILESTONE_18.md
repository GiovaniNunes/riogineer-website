# M18 — Guarded configurable liquid pump

Implementation date: 2026-10-01. Baseline: `main` at
`81d183d804755bcf6e995b1c126407a4404cf94a`.

Numerical implementation, automated qualification and user-reported human
acceptance are **complete within the bounded scope**. Giovani Nunes completed
browser acceptance on 2026-10-01 (America/Sao_Paulo) and authorized repository
closeout: commit the implementation and both prerequisite studies, then push
normally to origin/main. Deployment and M19 remain unauthorized. The pre-existing
`next-env.d.ts` modification remains separate and excluded from the commit.

## Capability and contracts

`rigorous_isentropic_pump_pr@1.0` adds one source → pump → sink, with one material
inlet and one material outlet. Requirements **1.10**, flowsheet **1.11**, results
and process result **1.12**, engine **1.11.0** are additive. Historical branches
retain their versions and numerical behavior. PR, caloric, PT, PS, PH, stability,
phase identification and M7 conversion routines are unchanged.

| Input                           | Accepted range                                               |
| ------------------------------- | ------------------------------------------------------------ |
| Composition                     | Fixed equimolar methane/n-hexane; explicit constant zero kij |
| Inlet temperature               | 300–350 K inclusive                                          |
| Inlet absolute pressure         | 20–25 MPa inclusive                                          |
| Discharge absolute pressure     | Exactly Pin, or Pin + 10,000 Pa through 30 MPa               |
| Specified isentropic efficiency | 0.6–1 inclusive                                              |
| Molar flow                      | 5–200 mol/s inclusive                                        |
| Each actual thermodynamic state | 300–370 K; 20–30 MPa absolute                                |

Limits reject; they never clamp. Off-grid inputs call the real property routines.
There is no allowlist, lookup table, interpolation, benchmark import or independent
reference target in production. Source mass rates are authoritative. Independently
specified inlet enthalpy or entropy is rejected. Equimolar does not mean equal
component mass rates.

M7 reconstructs component molar rates and composition without overwriting input
rates. A representation allowance of `64 * machine_epsilon` (approximately
1.42e-14 absolute mole fraction) permits binary64 division/summation roundoff.
Flow boundaries use that relative allowance at 5 and 200 mol/s; returned flow is
never snapped to the boundary. This is orders of magnitude below an engineering
recipe change. Tests cover legitimate mass-to-mole conversions and reject recipe
perturbations of 1e-10, equal mass rates, pure and hexane-rich recipes. Temperature,
pressure, efficiency and the positive-rise floor have no such widening.

## Equations and guards

For a positive rise, existing high-accuracy PT/calorics evaluates the actual inlet
at T1/P1/z; PS(P2,s1,z) determines h2s; then

```text
h_target = h1 + (h2s - h1)/eta_is
PH(P2,h_target,z) -> T2,h2,s2
W_target = F * (h_target - h1)
W_to_fluid = F * (h2 - h1)
Q = 0
```

Use J/mol, mol/s and W. Work is positive **into the fluid**; it is not electrical
consumption. Component rates and overall material flow are unchanged. Only the
actual outlet is a material stream. The isentropic state is an equipment diagnostic.

Each of the three states must have successful stable single-liquid equilibrium,
converged stability, PIP > 1, positive Z, matching finite phase/caloric payloads,
and matching T/P/composition. A **fresh high-accuracy PT/caloric witness** at the
same temperature/composition and **16 MPa** must independently pass the liquid
payload checks. The witness has its own fixed-pressure validation: it is outside
the actual-state pressure window by design. It is not a physical stream or pump
stage and does not establish cavitation safety.

Inverse acceptance retains immutable default 200–500 K domains, 64 PS scan points
and 128 PH scan points, one candidate, the selected/final brackets and exactly one
successful fresh final evaluation. The complete scan temperatures are checked.
PS property holes reject. PH retains its existing partitioned valid intervals;
no accepted bracket may bridge a hole. Final property, residual, temperature and
specification must match their reported payloads. Residual limits are 1e-8 J/(mol K)
for PS and 1e-6 J/mol for PH. No root forcing or shortened scans are used.

Positive work requires both h2s-h1 and h2-h1 > 0, recovered h2 matching target,
s2-s1 >= -2e-8 J/(mol K), and reconstructed efficiency within
`eta*1e-6/abs(h2-h1) + 64*machine_epsilon`. At eta=1, temperatures agree within
1e-7 K and entropy agrees within 2e-8 J/(mol K). There is no general vapor-style
outlet temperature ordering rule.

```text
B(h) = 1e-6 + 1e-11*abs(h)
arithmetic = 64*machine_epsilon*max(1,abs(h1),abs(h2s),abs(h2))/eta
E = (B(h1)+B(h2s))/eta + B(h1)+B(h2) + 370*1e-8/eta + 1e-6 + arithmetic
E/abs(h2-h1) <= 1e-4
```

E is an engineering numerical screening allowance, **not a certified uncertainty
bound or experimental accuracy claim**. Extensive values must be finite.
`W_to_fluid-W_target` is limited by `F*1e-6` plus extensive rounding allowance;
`Hdot_out-Hdot_in-W_to_fluid` is limited by
`64*machine_epsilon*max(1,abs(F*h1),abs(F*h2),abs(W_to_fluid))`.
The energy balance is algebraic consistency because work uses the same enthalpy
difference. Independent comparisons provide separate accuracy evidence.

Exact P2=P1 validates only the inlet and its witness, preserves state/rates,
returns W=Q=0, null isentropic reference and reconstructed efficiency, and
`not_applicable` PS/PH diagnostics. A tiny positive rise cannot become identity.
Failure is atomic: stage/status diagnostics are returned as controlled errors;
no partial accepted pump outlet is published.

## Integration and user interface

The bounded adapter validates ports, topology, actual source state and cross-field
pressure/recipe/flow restrictions. Shared strict Zod schemas generate the Python
JSON schemas; numerical and graph restrictions are enforced by the authoritative
Python validator before calculation.

Both streams use M17's corrected molecular serialization: kmol/h, kg/kmol and
mol/mol. `1 mol/s = 3.6 kmol/h`. Density and volumetric properties remain unavailable,
not fake zeroes. The equipment panel, general table and downloadable result share
the actual adapter output. The PFD has a pump symbol, directed flow and stable
stream numbers 1 and 2. The dedicated panel appears only for current results;
edits invalidate calculation/PFD readiness and disable result downloads. Detailed
witness/inverse diagnostics are expandable. Natural-language interpretation scope
is unchanged; load/edit the deterministic reference in Engineering data / Advanced.

## Independent equipment qualification

`benchmarks/pump_energy/m18/compare_equipment.py` calls both the **actual production
pump** and the **actual process adapter** against the unchanged independent frozen
references. It covers all configurable study rows (corners, interiors, off-grid
holdouts, identities, minimum admitted rises and below-floor rejects), canonical
operation, flow scaling and excluded first-study recipes/pressure conditions.
Identity aliases exist only inside the comparison normalizer so historical state
comparison code can be reused; the actual callable/adapter must publish null.
Independent witness comparisons are available for the configurable study; canonical
first-study/flow rows have production witness guards but no fabricated independent
witness data. Existing field tolerances are reused unchanged.

New output is `benchmarks/pump_energy/m18/equipment_comparison.json`.
`engine/tests/test_pump_energy.py` separately labels synthetic failure injection:
phase/stability/payload failures, missing/ambiguous/inconsistent inverse diagnostics,
PS holes and PH valid intervals, all witness stages, atomic inverse failures,
work resolution, entropy and ideal-efficiency failures. These are not represented
as physically calculated independent reference cases.

## Demonstrations and human checklist

From the repository root:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone18 --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone18 --mode identity --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone18 --mode off_grid --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone18 --mode flow --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone18 --mode floor --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone18 --mode sub_floor --calculate
```

Omit `--calculate` to print requirements. `sub_floor` must fail with
`positive_rise_below_floor`; it is a deliberate negative demo. The canonical UI
fixture is `contracts/examples/milestone-18-pump-requirements.json` and is tested
against the CLI-generated requirements.

In `/digital-engineer`, expand **Engineering data / Advanced**, click **Load
Milestone 18 pump reference**, then **Validate requirements**, **Generate PFD**,
and **Run engineering calculation**. Start a fresh engine process so it loads M18. The existing user services on
3000/8101 were left running. To avoid interrupting them, use two terminals:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8118
```

```sh
RIOGINEER_ENGINE_URL=http://127.0.0.1:8118 RIOGINEER_E2E=1 npm run dev -- --port 3118
```

Then open `http://127.0.0.1:3118/digital-engineer`. The existing test-mode build
setting isolates this frontend in `.next/e2e`. Stop these two temporary services
when finished. Browser automation used these ports without replacing user services.

- Canonical: Tin=300 K, Pin=20 MPa, Pout=30 MPa, eta=0.8, F=100 mol/s.
  Independent T2s=303.7542654332 K, T2=305.5815250342 K,
  W=110622.8601133975 W. Production agrees within frozen allowances.
- Confirm both streams have 360 kmol/h, 18399.2688 kg/h, MW=51.10908 kg/kmol,
  mole fractions 0.5/0.5 and rates methane=2887.704, n-hexane=15511.5648 kg/h.
- Off-grid: set Tin=306.85 K, Pin=23655000 Pa, Pout=26313555 Pa and eta=0.7132
  (`HOLDOUT_0` in the frozen configurable reference). Independent T2s=307.88816551281514 K,
  T2=308.6652483796721 K, W=33292.4881201654 W.
- Flow scaling: halve both component rates. F=50 mol/s, 180 kmol/h, same intensive
  states and approximately 55311.430056699 W. Verify table/panel/download agreement.
- Identity: canonical inputs with only outlet pressure changed to 20000000 Pa.
  Tout=300 K, Pout=20 MPa, W=Q=0; reference/efficiency unavailable and no inversions.
- Sub-floor: canonical Pout=20001000 Pa must fail before an accepted result/PFD.
  Pout=20010000 Pa is the admitted floor and must calculate if guards pass.
- Stale behavior: edit a validated/calculated input and confirm stale heading,
  hidden pump panel, disabled download and required revalidation/rebuild.

The separate user-reported human acceptance record follows. The exact-floor
case above remains automated-only evidence; browser automation itself does not
constitute human acceptance.

## Limitations

No new fluids, water, nonzero BIPs, general recipe variation, global phase or
convergence guarantee, experimental validation, sizing, head, curves, speed, NPSH,
cavitation prediction, mechanical losses, electrical model, mixed rigorous networks,
recycles or phase-changing heat exchangers. No new saturation solver. The 16 MPa
witness policy is a qualified bounded admissibility check, not a general theorem.

## Human acceptance — complete, 2026-10-01

Operator: **Giovani Nunes**. Date: **2026-10-01, America/Sao_Paulo**.
This is user-reported acceptance from a user-operated browser session whose
screenshots and exported JSON were reviewed in ChatGPT. The closeout agent did
not personally operate or independently observe that session. The supplied
acceptance report is the evidence for this record; no claim is made that the
screenshots or exported JSON are stored in this repository. No replacement
evidence was manufactured or searched for on the user's filesystem.

Services used: engine `http://127.0.0.1:8118`; frontend
`http://127.0.0.1:3118/digital-engineer`.

### A. Canonical reference

Equimolar methane/n-hexane, explicit zero kij; Tin=300 K,
Pin=20,000,000 Pa absolute, Pout=30,000,000 Pa absolute, eta=0.8,
F=100 mol/s=360 kmol/h. The user confirmed the source → pump → sink PFD and
pump symbol, populated inlet/outlet tables, and current results. Observed
Tout=305.581525034 K, power transferred to fluid=110622.860113396 W,
T2s=303.754265433 K and reconstructed efficiency=0.8. Both streams had
18399.2688 kg/h; composition and component flows were preserved. Mass and
energy checks passed.

### B. Equal-pressure identity

Only Pout changed to 20,000,000 Pa absolute. Observed Tout=300 K,
fluid power=0 W and imposed heat duty=0 W. Inlet/outlet composition, flow and
enthalpy flow were preserved; mass and energy residuals were zero. The
isentropic reference temperature was unavailable for equal-pressure identity,
and reconstructed efficiency was unavailable for zero work.

### C. Invalidation before validation

After editing discharge pressure and before pressing Validate, the interface
showed “Previous results are stale”, “Engineering results — STALE”, and a warning
that values belonged to a previous calculation. Download results was disabled;
the PFD and dedicated pump panel were hidden; Generate PFD and Run engineering
calculation were disabled. **Previous general results and balance statuses
remained visible under the stale warning. Results were retained as stale, not
entirely deleted.**

### D. Controlled sub-floor rejection

With Pin=20,000,000 Pa and Pout=20,001,000 Pa absolute, the 1,000 Pa rise is below
the qualified 10,000 Pa minimum. After Validate, the interface displayed
`/: specification: positive_rise_below_floor;`. PFD generation and calculation
remained blocked; previous results stayed stale and download remained disabled.
No new accepted result was published. A separate manual test of the exact
10,000 Pa floor is **not claimed**; that case remains covered by automated evidence.

### E. Flow scaling

Canonical conditions were restored and both rates halved: methane=1443.852 kg/h,
n-hexane=7755.7824 kg/h. Observed total=9199.6344 kg/h=180 kmol/h,
Tout=305.581525034 K unchanged, fluid power=55311.430056698 W (half canonical),
and reconstructed efficiency=0.8. Composition was preserved, mass/energy checks
passed, and results were current.

### F. Off-grid operation

Canonical component flows were restored. Inputs: Tin=306.85 K,
Pin=23,655,000 Pa absolute, Pout=26,313,555 Pa absolute, eta=0.7132,
F=100 mol/s. Observed Tout=308.66524838 K, fluid power=33292.488120163 W,
T2s=307.888165513 K, reconstructed efficiency=0.7132, and
360 kmol/h=18399.2688 kg/h. Composition was preserved, mass/energy checks passed,
and results were current.

### G. Download agreement

The user downloaded the off-grid `results.json` and supplied it to ChatGPT.
Its values agreed with the display, allowing for display rounding:

- Schema and process-result versions: `1.12`; engine: `1.11.0`; status: `completed`.
- Equipment: `rigorous_isentropic_pump_pr@1.0`.
- Tout=308.665248379672 K; fluid power=33292.48812016267 W;
  reconstructed efficiency=0.7131999999999931.
- Energy residual=-4.3655745685100555e-11 W;
  tolerance=2.2379900405281102e-8 W.
- Mass and energy statuses passed; PS and PH diagnostics succeeded.
- Density and phase volumetric flows remained null/not_calculated.
- Qualification limitations and thermodynamic provenance were included.

Export run ID: `e8084a35-c661-45ba-a827-247baa2032d6`.

Export input SHA-256:
`d77f0eb947d1f99a25a552fa537fce9add9d5a85fa8cb6bb6ebf5451adaacae3`.

Human acceptance is **complete within the documented guarded scope**. It does not
expand composition, pressure, temperature, efficiency or flow ranges, and does
not establish experimental accuracy, sizing, head, NPSH, cavitation safety,
electrical power or mixed-network qualification. Automated evidence and its
initial failures/corrections/reruns below remain unchanged.

## Repository closeout

The user explicitly authorized recording acceptance, committing the implementation
and both prerequisite studies, and pushing normally to `origin/main`. The verified
inventory is **57 files: 26 M18 paths and 31 prerequisite paths**, listed below;
shared master-context documentation is counted once. `next-env.d.ts` is excluded
and its bytes at closeout entry are preserved. No production or solver code was
changed during closeout. No deployment, M19 work, history rewrite or force push
is authorized. Running user services are left untouched.

The historical preservation artifact records `.next/dev` imports in
`next-env.d.ts`; closeout began with `.next/e2e/dev` imports instead. The initial
read-only historical hash check identified this expected unrelated-file mismatch.
The current bytes were not changed or restored. Their closeout-entry SHA-256 is
`4d8f0e0ec749110e5c127c129b9992713962fca2147e10fe1203b42a14704fd3`.
All 154 applicable implementation/reference/protected-file/policy checks pass;
a separate check confirms this file matches its closeout-entry hash. The original
155-check implementation evidence and its artifact remain untouched.

Closeout verification is limited to inventory/documentation review, read-only
source/reference/preservation hashes and recorded policy checks, and working-tree
and staged whitespace checks. Full numerical, browser and build suites are not
repeated for this documentation-only closeout; their earlier evidence is retained
as cumulative coverage, not relabelled as a clean uninterrupted full-suite run.

## Exact file inventory

M18 additions/modifications (master context also retains prior study additions):

```text
MILESTONE_18.md
benchmarks/pump_energy/m18/README.md
benchmarks/pump_energy/m18/compare_equipment.py
benchmarks/pump_energy/m18/equipment_comparison.json
benchmarks/pump_energy/m18/evidence_verification.json
benchmarks/pump_energy/m18/preservation.json
benchmarks/pump_energy/m18/verify_evidence.py
contracts/examples/milestone-18-pump-requirements.json
contracts/v1/flowsheet.schema.json
contracts/v1/requirements.schema.json
contracts/v1/results.schema.json
contracts/v1/validation.schema.json
docs/RIOGINEER_MASTER_CONTEXT.md
engine/riogineer_engine/core.py
engine/riogineer_engine/milestone18.py
engine/riogineer_engine/network.py
engine/riogineer_engine/network_models.py
engine/riogineer_engine/pump_energy.py
engine/riogineer_engine/pump_process.py
engine/tests/test_pump_energy.py
src/app/digital-engineer/pfd.tsx
src/app/digital-engineer/pump-results.tsx
src/app/digital-engineer/workspace.tsx
src/lib/digital-engineer/contracts.ts
tests/e2e/pump.spec.ts
tests/pump.test.ts
```

Preserved prerequisite work, already uncommitted at entry:

```text
PRE_MILESTONE_18_CONFIGURABLE_PUMP_SCOPE_QUALIFICATION.md
PRE_MILESTONE_18_LIQUID_PUMP_PATH_QUALIFICATION.md
benchmarks/pump_energy/README.md
benchmarks/pump_energy/THIRD_PARTY_NOTICES.txt
benchmarks/pump_energy/candidate_ledger.json
benchmarks/pump_energy/common.py
benchmarks/pump_energy/compare_production.py
benchmarks/pump_energy/configurable_scope/PLAN.md
benchmarks/pump_energy/configurable_scope/README.md
benchmarks/pump_energy/configurable_scope/THIRD_PARTY_NOTICES.txt
benchmarks/pump_energy/configurable_scope/boundary_equations.json
benchmarks/pump_energy/configurable_scope/boundary_equations.py
benchmarks/pump_energy/configurable_scope/boundary_refinement.json
benchmarks/pump_energy/configurable_scope/boundary_refinement.py
benchmarks/pump_energy/configurable_scope/candidate_ledger.json
benchmarks/pump_energy/configurable_scope/compare_production.py
benchmarks/pump_energy/configurable_scope/ledger.py
benchmarks/pump_energy/configurable_scope/policy.py
benchmarks/pump_energy/configurable_scope/production.json
benchmarks/pump_energy/configurable_scope/reference.json
benchmarks/pump_energy/configurable_scope/reference.py
benchmarks/pump_energy/configurable_scope/requirements.txt
benchmarks/pump_energy/configurable_scope/runtime.py
benchmarks/pump_energy/configurable_scope/test_scope.py
benchmarks/pump_energy/liquid_pump_path_reference.json
benchmarks/pump_energy/production_comparison.json
benchmarks/pump_energy/reference.py
benchmarks/pump_energy/requirements.txt
benchmarks/pump_energy/scope.py
benchmarks/pump_energy/test_production.py
benchmarks/pump_energy/test_reference.py
```

Separate pre-existing unrelated modification: `next-env.d.ts`. Next tooling
rewrites its imports while generating test/build types; its original incoming
bytes were restored and checked against the captured baseline hash during
implementation. At that earlier handoff no changes were staged, committed or
pushed. During this separately authorized closeout its current bytes are left
untouched and excluded; deployment remains unauthorized.

## Executed verification and retries

The final actual-equipment comparison passed **59 cases: 43 accepted and 16
controlled rejections**, with **10,477 checks**. The final source manifest matches
the tested production files. Evidence verification passed **155 checks**, including
78 exact screening-budget/ratio comparisons with the qualified policy, 33
production source hashes, two independent reference hashes and 42 protected-file
hashes. No independent reference or boundary-generation job was repeated.

Commands executed from the repository root:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/pump_energy/m18/compare_equipment.py
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/pump_energy/m18/verify_evidence.py
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_pump_energy -v
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_compressor_energy.FrozenCompressorMatrix -v
npm test
npx vitest run tests/pump.test.ts
npx playwright test --config .local/m18.playwright.config.ts
npx playwright test --config .local/m18.playwright.config.ts tests/e2e/pump.spec.ts
npm run contracts:generate
npm run contracts:check
npm run typecheck
npx tsc --noEmit
npm run lint
npm run format:check
npx prettier --check MILESTONE_18.md benchmarks/pump_energy/m18/README.md
RIOGINEER_E2E=1 npm run build
SITE_URL=http://127.0.0.1:3200 RIOGINEER_E2E=1 RIOGINEER_LLM_PROVIDER='' npm run start -- --port 3200
SMOKE_URL=http://127.0.0.1:3200 npm run smoke
git diff --check
```

The temporary browser config is the existing Playwright config with frontend/engine
ports changed from 3100/8101 to 3118/8118, `testDir: '../tests/e2e'`, and both web
servers' `cwd: process.cwd()`. It lives in ignored `.local/`. The first launch
failed because the temporary config initially resolved PYTHONPATH relative to
`.local`; correcting the working directory resolved that environment issue.
Localhost browser/HTTP/build/smoke operations ran with approved sandbox escalation.
Existing services on 3000 and 8101 were preserved. Temporary test servers stopped.

Development corrections and affected-scope reruns:

- A new stability diagnostic initially contained Python tuples; explicit JSON
  serialization corrected result-schema validation without a numerical change.
- The first equipment-comparator attempt assumed the older canonical artifact
  contained witness data. It does not. Independent witness comparisons now use
  only available frozen data, while production witness validation remains mandatory.
  The complete final equipment comparison passed after all guard changes.
- Focused Python tests initially passed 14 methods. Payload checks were strengthened
  to cover every caloric payload field and matching final trial property, and two
  atomic-failure tests were added. The final **16 focused methods passed**.
- Full Vitest initially passed 266 and failed two new workflow tests because the
  test setup omitted the existing validation event. Correcting only the test setup
  produced **3/3 passing M18 tests**, covering both failed cases. Thus all **268
  TypeScript tests** have passing evidence; the 265 historical tests were unchanged.
- Full browser run passed **37 historical tests** and failed the new pump test:
  flowsheet 1.11 was missing from graph-PFD routing. The routing entry was added;
  the affected M18 test then passed. All **38 browser tests** have passing evidence.
- The initial smoke command omitted matching `SITE_URL` on the temporary server;
  the contact origin check correctly returned 403. Restarting only that temporary
  server with `SITE_URL=http://127.0.0.1:3200` passed the existing smoke: **17 pages,
  17 PNG social cards, internal links, 404s, preview indexing and disabled contact
  delivery**. No contact message was sent.
- Schema parity, full type checking, lint, formatting, build, final whitespace
  review and new Python syntax/trailing-whitespace checks passed. Next tooling
  rewrote `next-env.d.ts`; its original incoming bytes were restored and the final
  `tsc --noEmit` passed against those restored declarations.

The full Python suite was run **once**: **570 tests passed**, with one class-setup
error preventing the 65-test historical compressor matrix from running. The
failure was its byte-level call-order assertion (`historical`, `CANONICAL`): final
M18 guard edits during the run changed the dynamic implementation source hash.
No historical compressor or thermodynamic algorithm was edited. With source fixed,
the entire affected `FrozenCompressorMatrix` rerun passed **65/65**, including the
call-order assertion. The final M18-focused run passed **16/16** (14 present in the
full run plus two added atomic-failure tests). These full/focused runs cover all
**637 tests in the final Python inventory**. The full suite was not repeated.
This is a recovered gate, not a claim that the initial full command exited zero.

All six CLI modes were actually run: five successful calculations and the expected
sub-floor rejection. Human acceptance was pending at that automated handoff;
the subsequent user-reported acceptance is recorded separately above.
