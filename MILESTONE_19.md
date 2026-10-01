# M19 — guarded variable-composition liquid pump

Implemented and independently qualified. **Human acceptance was reported by
Giovani Nunes on 2026-10-01, America/Sao_Paulo.** The dated acceptance and repository
closeout entry below supersedes the historical pending status. No deployment,
equipment sizing or production mixed-network integration is included.

Starting branch `main`; full HEAD and remote `origin/main`:
`2a2f4cc9c3e827187af1d64be9f1773b23389618`. Initial staging empty, with only the
user's `next-env.d.ts` modification. Exact initial bytes were saved and preserved.
The [qualification report](PRE_MILESTONE_19_VARIABLE_COMPOSITION_PUMP_QUALIFICATION.md)
distinguishes evidence, runtime scope and remaining separator compatibility gaps.

## Implemented scope and versions

| Item                                      | M19                                                  |
| ----------------------------------------- | ---------------------------------------------------- |
| Model                                     | `rigorous_isentropic_pump_pr@2.0`                    |
| Profile                                   | `variable_pump_energy`                               |
| Requirements                              | 1.11                                                 |
| Flowsheet                                 | 1.12                                                 |
| Results / process result                  | 1.13                                                 |
| Engine provenance version for this branch | 1.12.0                                               |
| Components                                | methane, n_hexane; explicit constant zero kij        |
| Methane mole fraction                     | 0.01–0.55 inclusive; n_hexane balance                |
| Inlet T / P                               | 300–350 K / 20–25 MPa absolute                       |
| Discharge                                 | exactly Pin, or Pin+10000 Pa through 30 MPa absolute |
| Isentropic efficiency                     | 0.6–1                                                |
| Molar flow                                | 5–200 mol/s (18–720 kmol/h)                          |
| All reached states                        | 300–370 K, 20–30 MPa; fresh 16 MPa liquid witnesses  |
| Topology                                  | one source → pump → sink                             |

Component mass rates are authoritative. The unchanged molecular provider converts
kg/h to molar composition, molecular mass and molar flow. Only 64 machine epsilon
representation noise is admitted at composition/flow bounds; no rates or
composition are snapped, clipped or replaced. Pure components and out-of-range
compositions return `composition_scope`. Other diagnostics distinguish input
range, sub-floor rise, phase/stability/witness failure, inverse failure and
unresolved work. A scalar-domain admission is not a guarantee that every runtime
calculation will converge or pass guards.

Version 1.0 and its M18 requirements 1.10, flowsheet 1.11, results 1.12 retain fixed
equimolar semantics. Their pump module, adapter, CLI and evidence remain unchanged.
Version 2.0 uses a separate equipment module and adapter, sharing unchanged M18
phase/inverse guards. The short physical calculation orchestration is retained
in the separate versioned module to avoid refactoring the frozen M18 execution
path. New dispatch and contract branches are additive. Overall engine/schema fingerprints naturally change with the additive implementation; historical numerical semantics and model versions remain preserved, not whole-run UUIDs or current-source fingerprints. Shared EOS/PT/PS/PH,
stability, caloric data and molecular routines are unchanged.

Production imports no benchmark module, frozen data, Thermo, SciPy or independent
reference runtime. Actual H/S → PS → efficiency target → PH → fluid power remains
the only pressure-rise calculation. Identity has zero power, unchanged state,
one witness and null isentropic/reconstructed-efficiency fields. UI and downloads
retain real molar units, composition, molecular mass, fluid power and phase/solver
provenance; unavailable density and sizing remain unavailable.

The isolated-test `RIOGINEER_E2E_DIST_DIR` option prevents M19 tests/builds from
colliding with the existing M18 acceptance server's `.next/e2e` directory. Normal
Next and existing E2E defaults are unchanged.

## Independent evidence and limitations

- 64 predeclared pump cases: 53 independently admitted, 11 rejected.
- Actual equipment callable **and** process adapter: **13,607 comparisons passed**.
- 824/824 composition/temperature coexistence checks passed, including 12 holdouts.
- Largest bubble pressure 15.135460174570 MPa; after empirical interpolation and
  numerical allowances, witness reserve 0.338539825430 MPa below 16 MPa.
- Independent reference reproduced byte-for-byte; installed library and Cp/source
  hashes verified. No shared solver tolerances were relaxed.
- Exact equimolar M18/M19 numerical details and stream outputs match in engine tests.

This is numerical evidence for the specified PR model, not experimental accuracy,
a certified uncertainty estimate, a continuous-domain proof or cavitation safety.
Runtime stable-liquid, PIP, fresh witness, payload association, residual, work,
entropy, efficiency and closure checks remain mandatory at actual composition.
See the qualification report for equations, constants, tolerances and rejection
rationale. Numerical ambiguity/nonconvergence guard tests are explicitly synthetic;
they are not misrepresented as naturally occurring in-domain observations.

## Separator compatibility

The study calculated all 24 frozen M17 cases using actual outlet component rates,
T/P/H and phase diagnostics. None can enter M19 directly: absent liquid, pressure,
temperature, flow or composition prevents admission. Examples: actual methane
fractions 0.015619720086 at 0.3 MPa and 0.057181287482 at 1 MPa overlap composition
but remain respectively 19.7 and 19 MPa below minimum inlet pressure. Canonical
PT liquid z=0.007744817176 is also below the composition limit.

One additional high-pressure full-liquid M17 case (z=0.25, 100 mol/s, 300 K,
20 MPa outlet) is directly thermodynamically compatible, with zero H-convention
residual. Its unchanged outlet matches the independently qualified new pump inlet.
It is not a fractionated low-pressure product. Lower-pressure/saturation-margin,
state-temperature and in some cases lower-composition/flow qualification remains
necessary. No separator outlet was moved to a convenient pressure or temperature,
and no production mixed-network connection was added.

## Startup and manual acceptance

Use separate terminals from repository root, with unused ports:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8119
```

```sh
RIOGINEER_ENGINE_URL=http://127.0.0.1:8119 RIOGINEER_E2E=1 RIOGINEER_E2E_DIST_DIR=.next/m19-e2e npm run dev -- --port 3119
```

Open http://127.0.0.1:3119/digital-engineer. Existing user services were not stopped.
Next may regenerate local TypeScript declarations/config for the selected output
directory during startup; the delivered `next-env.d.ts` retains the initial bytes.

1. Open **Engineering data / Advanced**, load **Milestone 19 variable pump
   reference**, validate, generate PFD and run. Confirm model 2.0, pump symbol,
   current results, passed mass/energy checks, and values below.
2. Verify inlet and outlet component rates match, composition is 0.25/0.75,
   molecular mass and molar flow use the displayed units, and density remains
   unavailable. Expand phase/witness diagnostics.
3. Download results and compare displayed numbers to JSON. Edit any rate or
   parameter: previous results remain visible with explicit STALE/previous-calculation
   warnings; the current pump panel disappears and export is disabled until
   revalidation/recalculation. This does not delete or clear all previous results.
4. Set discharge to 20000000 Pa: exact identity, zero power, unchanged temperature,
   unavailable ideal reference/reconstructed efficiency. Set it to 20001000 Pa:
   controlled `positive_rise_below_floor` rejection.
5. For a composition rejection at F=100 mol/s, use methane 3465.2448 kg/h and
   n_hexane 12409.25184 kg/h (z=0.6/0.4). Confirm `composition_scope`, no current
   results and disabled PFD generation. Pure endpoints are also unsupported.
6. Reload the M18 reference and confirm its unchanged equimolar results; editing
   that M18 recipe to non-equimolar remains rejected. M19 CLI `--mode equimolar`
   provides the separate version 2.0 equimolar demonstration.

| Quantity            |   M19 canonical z=0.25 | Equimolar compatibility |
| ------------------- | ---------------------: | ----------------------: |
| Inlet T / P         |         300 K / 20 MPa |          300 K / 20 MPa |
| Discharge / eta     |           30 MPa / 0.8 |            30 MPa / 0.8 |
| Molar flow          | 100 mol/s = 360 kmol/h |  100 mol/s = 360 kmol/h |
| Molecular mass      |       68.64222 kg/kmol |        51.10908 kg/kmol |
| Total mass flow     |        24711.1992 kg/h |         18399.2688 kg/h |
| Methane mass flow   |          1443.852 kg/h |           2887.704 kg/h |
| n_hexane mass flow  |        23267.3472 kg/h |         15511.5648 kg/h |
| Isentropic outlet T |     302.352192004522 K |        303.7542654332 K |
| Actual outlet T     |     304.097803732985 K |        305.5815250342 K |
| Fluid power         |     132548.174119273 W |     110622.8601133975 W |
| Heat duty           |                    0 W |                     0 W |

CLI commands:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone19 --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone19 --mode equimolar --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone19 --mode unsupported --calculate
```

The last command intentionally exits with a controlled unsupported-composition
error. `identity`, `off_grid`, `flow`, `floor` and `sub_floor` modes are also
available. The canonical requirements exactly match the checked-in UI fixture.

## Verification record

Focused development checks passed: 18 new engine tests, three TypeScript tests,
and one real-browser calculation/table/PFD/export/identity/stale/rejection test.
The first reference CLI attempt used the independent environment without jsonschema;
it was corrected to the production engine environment. The initial separator
study used the wrong port spelling and was corrected to M17's actual `liquid`
port. The first temporary browser launch lacked an explicit repository working
directory; it was corrected before the focused browser test ran. None required
solver changes or tolerance relaxation.

Post-stabilization gates already verified:

- TypeScript: **271 tests passed** in 25 files.
- Browser: **39 tests passed**, including M18 and M19, on isolated 3119/8119 services.
- Generated schema parity, lint, Next type generation plus TypeScript, production
  build, formatting and whitespace checks passed. TypeScript was checked again
  after restoring generated local declaration/config changes.
- Smoke: **17 pages and 17 PNG social cards**, links, 404s, preview indexing and
  disabled contact delivery passed on the isolated production build at port 3219.
- Historical preservation manifest: **141 files unchanged**. Actual equipment
  evidence matches all **36 production source hashes**.
- Python: **658 tests of cumulative post-stabilization coverage passed**. The full
  command ran **656 tests in 734.546 s**, all passing, but exited nonzero because
  `test_engine.HttpTests.setUpClass` could not bind a localhost socket inside the
  sandbox (`PermissionError: [Errno 1] Operation not permitted`). Only that class
  was rerun with localhost permission: **2/2 passed in 0.536 s**. This is a
  recovered regression gate, not a claim that the original full command exited
  zero. The 18 focused development tests are overlapping coverage, not 18 further
  unique tests. No thermodynamic failures or source corrections were required.

Commands (from repository root):

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_engine.HttpTests -v
npm run contracts:check
npm test
npm run lint
RIOGINEER_E2E_DIST_DIR=.next/m19-build npm run typecheck
RIOGINEER_E2E_DIST_DIR=.next/m19-build SITE_URL=http://127.0.0.1:3219 npm run build
npx playwright test --config .local/m19.playwright.config.ts
SITE_URL=http://127.0.0.1:3219 RIOGINEER_E2E_DIST_DIR=.next/m19-build RIOGINEER_LLM_PROVIDER='' npm run start -- --port 3219
SMOKE_URL=http://127.0.0.1:3219 npm run smoke
npm run format:check
npx tsc --noEmit
git diff --check
```

The ignored temporary Playwright config copies the repository config, sets
`cwd: process.cwd()` for both web servers, uses ports 3119/8119, changes testDir
to `../tests/e2e` and sets `RIOGINEER_E2E_DIST_DIR=.next/m19-e2e`. It has the same
single-worker tests, browser and review settings. Temporary servers were stopped;
the pre-existing user services were left running. Independent evidence reproduction
commands are in the benchmark README. Full expensive matrices were not repeated
without cause; HTTP permissions were handled with the two-test scoped rerun.

## Exact changed-file inventory

The verified M19 commit inventory contains exactly 37 paths (14 modified tracked
files and 23 new files at closeout start). The separate local modifications to
`next-env.d.ts` and `tsconfig.json` are excluded and preserved byte-for-byte.

```text
MILESTONE_19.md
PRE_MILESTONE_19_VARIABLE_COMPOSITION_PUMP_QUALIFICATION.md
benchmarks/variable_composition_pump/PLAN.md
benchmarks/variable_composition_pump/README.md
benchmarks/variable_composition_pump/cases.py
benchmarks/variable_composition_pump/compare_equipment.py
benchmarks/variable_composition_pump/equipment_comparison.json
benchmarks/variable_composition_pump/exploration.json
benchmarks/variable_composition_pump/explore.py
benchmarks/variable_composition_pump/preservation.json
benchmarks/variable_composition_pump/reference.json
benchmarks/variable_composition_pump/reference.py
benchmarks/variable_composition_pump/separator_compatibility.json
benchmarks/variable_composition_pump/separator_compatibility.py
benchmarks/variable_composition_pump/verify_reference.py
contracts/README.md
contracts/examples/milestone-19-pump-requirements.json
contracts/v1/flowsheet.schema.json
contracts/v1/requirements.schema.json
contracts/v1/results.schema.json
contracts/v1/validation.schema.json
docs/RIOGINEER_MASTER_CONTEXT.md
engine/riogineer_engine/core.py
engine/riogineer_engine/milestone19.py
engine/riogineer_engine/network.py
engine/riogineer_engine/network_models.py
engine/riogineer_engine/variable_pump_energy.py
engine/riogineer_engine/variable_pump_process.py
engine/tests/test_variable_pump_energy.py
engine/tests/test_variable_pump_evidence.py
next.config.mjs
src/app/digital-engineer/pfd.tsx
src/app/digital-engineer/pump-results.tsx
src/app/digital-engineer/workspace.tsx
src/lib/digital-engineer/contracts.ts
tests/e2e/variable-pump.spec.ts
tests/variable-pump.test.ts
```

## Historical implementation handoff (before human acceptance)

Branch `main`, HEAD unchanged at
`2a2f4cc9c3e827187af1d64be9f1773b23389618`; starting live remote matched this commit.
No commit, push or deployment. Index empty. The inventory above contains 14 modified
tracked files and 23 new files for M19. The only additional tracked modification
is the user's original `next-env.d.ts`, preserved byte-for-byte. Next-generated
`tsconfig.json` changes were restored to its initially clean bytes. Historical
preservation and current equipment source hashes were checked again after the
full suite. Temporary test/build servers are stopped; user services remain intact.
Implementation and automated qualification are ready for review; human acceptance
is pending and M19 is not marked human-accepted.

## Human acceptance — 2026-10-01, America/Sao_Paulo

**Accepted by Giovani Nunes.** This is user-reported browser acceptance, based on
browser operation, screenshots and the exported canonical results JSON reviewed
in the accompanying ChatGPT conversation. It is distinct from the historical
automated evidence above. The closeout agent did not personally repeat these
human checks; the screenshots and exported acceptance JSON are not included in
this repository commit. Only the observations reported below are recorded as
manually observed; other items in the reproduction checklist are not implied.

### Canonical M19 calculation and export

Giovani reported model `rigorous_isentropic_pump_pr@2.0`, methane/n-hexane mole
fractions 0.25/0.75, inlet 300 K and 20,000,000 Pa absolute, discharge 30,000,000 Pa
absolute, and specified isentropic efficiency 0.8. Molar flow was 360 kmol/h
(100 mol/s), total mass flow 24,711.1992 kg/h and molecular mass 68.64222 kg/kmol.
The calculated outlet temperature was approximately 304.097803733 K and power
transferred to the fluid approximately 132,548.174119273 W; imposed heat duty
was 0 W. Mass and energy checks passed and results were marked current.
The exported JSON agreed with the displayed canonical values and identified
results schema 1.13 and engine 1.12.0. Density and phase volumetric flows remained
explicitly unavailable.

### Stale results and unsupported composition

Editing feed values invalidated the preceding calculation. Previous results
remained visible with explicit STALE/previous-calculation warnings and download
was disabled. This was not deletion or clearing of all previous results.

With methane 3465.2448 kg/h and n-hexane 12409.25184 kg/h, validation rejected the
0.60 methane mole fraction with `composition_scope`, stating the qualified
interval 0.01–0.55. Previous results remained stale and download disabled.

### Equal-pressure identity and below-minimum rise

After restoring the M19 reference, discharge was set to 20,000,000 Pa absolute,
exactly equal to inlet pressure. Outlet temperature was 300 K; fluid power and
heat duty were both 0 W. Inlet/outlet flows, composition and enthalpy flow were
unchanged. Mass and energy residuals were zero and checks passed. Results were
current and download enabled. Isentropic reference temperature displayed
unavailable for equal-pressure identity; reconstructed efficiency displayed
unavailable for zero work.

Changing discharge to 20,001,000 Pa absolute gave a positive rise of 1,000 Pa.
Validation returned `positive_rise_below_floor`. Generate PFD, Run engineering
calculation and Download results were disabled. Historical results remained
marked STALE.

### Historical M18 compatibility

Loading the historical M18 reference and running the workflow produced model
`rigorous_isentropic_pump_pr@1.0` with fixed equimolar methane/n-hexane, outlet
temperature approximately 305.581525034 K, fluid power approximately
110,622.860113396 W and reconstructed efficiency 0.8. Mass and energy checks
passed and results were current.

Keeping the M18 model while changing feed rates to methane 1443.852 kg/h and
n-hexane 23267.3472 kg/h produced the expected rejection:
`composition_scope; Fixed equimolar methane/n_hexane required`.
PFD generation, calculation and download were disabled, with previous results
marked STALE. These observations confirm that M19 did not silently broaden the
M18 contract.

### Accepted limits and repository closeout

Acceptance applies only to methane mole fraction 0.01–0.55, n-hexane balance,
explicit zero kij and all existing temperature, pressure, efficiency, flow,
phase, witness, inverse-solver, residual and work guards documented above.
Finite sampling does not guarantee convergence for every intermediate input;
numerical qualification is not experimental validation. Low-pressure fractionated
separator-product integration remains unresolved. No new mixed-network, sizing,
NPSH, cavitation or electrical-power capability is claimed.

Giovani authorized the 37-path implementation/qualification/documentation commit
and a normal push to existing remote main, with message:
`Complete Milestone 19 variable-composition pump and record human acceptance`.
The baseline was verified as main at
`2a2f4cc9c3e827187af1d64be9f1773b23389618`, matching live remote main, with an empty
index. The actual inventory matched the 37 documented M19 paths. An additional
local `tsconfig.json` change was found: generated `.next/m19-e2e` type includes
and formatting, consistent with the documented acceptance-server startup. Its
origin is inferred from the diff. Both that file and `next-env.d.ts` were separately
saved and excluded from staging; neither is overwritten or discarded.

Closeout checks are lightweight and separate from historical regression runs:
complete inventory/diff review, stored reference/source/evidence and historical
preservation integrity, generated-schema parity, documentation formatting,
working-tree and staged whitespace, and explicit staged-path/byte-preservation
checks. Production code, versions, shared solvers and frozen numerical artifacts
are unchanged during closeout. Full Python, TypeScript, browser and numerical
benchmark suites are not rerun for this documentation closeout. The historical
658-test cumulative Python record, including the successful two-test HTTP retry,
is preserved exactly above.

Closeout check results: inventory reconciled at 37 paths; all 141 historical
preservation hashes and all 36 production source hashes matched. The independent
reference verifier passed, including installed library/Cp hashes, and all three
read-only evidence tests passed (0.068 s). All 13,607 stored comparison pass flags
were verified without rerunning numerical calculations. Generated schema parity
passed, and all historical branches of the four changed schemas were preserved.
Prettier passed for the milestone/qualification reports and edited master-context
sections. A whole-file master-context check flagged legacy formatting also
present in the baseline; unrelated historical formatting was intentionally retained.
Working-tree whitespace passed. Only the three documentation files changed during
closeout; all implementation, tests and frozen artifacts retained their starting
bytes. Staged whitespace, exact path list and exclusion checks are required before
the authorized commit, followed by final byte-preservation/synchronization checks.

The closeout commit identifies this accepted state; the final delivery records its
full SHA and verifies local main, origin/main and live remote main agree after a
normal push. The two excluded local modifications mean the working tree is not
clean. Running user services are left untouched. Next-conversation handoff:
M19 is human-accepted within its guarded scope; await a separately authorized
next task. No deployment, M20 or thermodynamic scope expansion is included.
