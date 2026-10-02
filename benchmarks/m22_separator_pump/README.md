# M22 integration qualification report

Finite integration of two explicitly selected PT200 pump workflows. See
`../../MILESTONE_22.md` for exact recipes, versioning, commands and manual acceptance.
Human acceptance, stage/commit/push/deployment remain pending.

## Evidence ownership

- `PLAN.md`: predeclared scope, inherited tolerances and integration risks.
- `baseline.json`: task-start tracked bytes, configuration hashes, Git identity and
  master-prefix length. Capture status separately records the newly created directory.
- `preliminary.json`: fresh M17 application source followed by selected production
  pump core, before broad contract/admission edits; 207 checks, no failures.
- `integration.json`: both complete new application workflows, requirements,
  flowsheets, result payloads and 221 independent/guard/provenance comparisons.
- `historical.json`: fresh 30-case M20 regression against independent references,
  plus exact equality of complete result payloads except run/input/implementation
  identities. Requirements and all numeric/material/energy/diagnostic fields remain.
- `verify.py`: fresh final-path comparison by default; `--preliminary` selects the
  separately labeled preliminary route. `--output` creates a new file, never overwrites.
- `historical.py`: uses the unchanged M21 current-M20 comparison adapter, checks all
  30 current identities and exact numerical payload compatibility; create-only output.
- `integrity.py`: exact current manifest, committed M21 source identity and task-start
  preservation. Exact authorized changed files are enumerated; no directory exclusion.
- `contracts.py` / `contract_compatibility.json`: literal structural equality of all
  historical schema branches and shared definitions, with one additive branch each.
- `screenshots/`: automated PFD/stream-table captures; above-reference PFD visually
  inspected, with normal horizontal table scrolling. No human acceptance implied.
- `finalize.py`: writes final gate metadata/inventory only after the full suite passes;
  never stages or commits.
- `source_manifest.json`: current production Python, schemas and both input-only lists.
- `verification.json`, `inventory.json`, `manifest.json`: final commands/counts,
  exact task file list and hashes; configuration edits are separately excluded.
- `logs/`: original focused failures, corrections and repository gate outputs.

No independent expected artifact was generated or changed. The independent source
and pump oracle is the accepted Pre-M21 `pt_iteration_budget/reference.json`, reusing
independent Thermo/SciPy calculations under canonical PR, explicit zero kij and the
same Poling caloric basis. Source comparisons reuse frozen M17 propagated allowances;
pump tolerances are inherited verbatim. Agreement is numerical model agreement,
not experimental validation. Frozen reference dependencies and notices remain in
previous benchmark directories.

## New versus archived identity

M22 changes application source and additive schemas, so implementation-dependent
semantic hashes change. Old M21 source pins continue to identify its committed source,
verified from Git at the M22 baseline. Current-source verification uses the new M22
manifest. Existing active historical tests retain archived M19/M20 expectations and
fresh numerical comparisons, with their current preservation calls pointed explicitly
to M22. All M21 review records, originals and acceptance records are byte-preserved.
The 199-iteration peak is retained accepted M21 evidence, not a new full M21 study.

## Reproduction

From repository root:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m22_separator_pump/verify.py
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m22_separator_pump/historical.py
engine/.venv/bin/python -B benchmarks/m22_separator_pump/integrity.py
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_m22_separator_pump -v
PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest discover -s engine/tests -v
npm run contracts:check
npm test
npm run lint
npm run format:check
git diff --check
```

Next commands are run in `.local/m22-validation`, copied with `.git`, `.local`,
`.next`, `node_modules`, `.venv`, caches and tsbuildinfo excluded, with dependencies
symlinked to the original checkout. Only the copied Playwright config changes
3100/8101 to 3122/8122. No original configuration is regenerated.

```sh
npm run typecheck
npx playwright test tests/e2e/m22-separator-pump.spec.ts
npx playwright test
RIOGINEER_E2E_DIST_DIR=.next/m22-build NEXT_TELEMETRY_DISABLED=1 npm run build
```

Gate counts are single-run counts. Focused and full-suite counts overlap; they must
not be summed as unique tests. Intermediate failures remain in their original logs.
Final results and any environment limitations are recorded in `verification.json`.

## Final results

Full Python: **693 passed in 871.395 s**, one ordinary unfiltered run. Full frontend:
**280 passed / 28 files**. Full browser: **42 passed**, one run. Separate focused
Python runs passed 9 and 29 tests; focused frontend 7 and browser 2 passed. Counts
overlap and are not summed. New final integration: 221 checks / two cases; historical
regression: 1,680 checks / 30 cases with exact numerical payload equality. The
207 preliminary comparisons are separately labeled and overlap final checks.

Contracts, TypeScript, lint, isolated production build, smoke and preservation pass.
Only repository formatting of pre-existing protected tsconfig.json remains nonzero.
Initial focused failures were test setup corrections (unchanged 0.5 mutation and
unsupported test filename), retained in original logs; no production tolerance or
physical guard was relaxed. Current source and frozen references are separately
hashed. No engineering blocker remains for the exact two new cases. Human acceptance,
commit/push and deployment are pending. See verification.json for exact commands.
