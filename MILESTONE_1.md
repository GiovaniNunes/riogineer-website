# Milestone 1 implementation report

Implemented the deterministic three-phase separator foundation only. No LLM interpretation, graphical editing, additional equipment, recycle calculation, authentication, database or deployment was added. The original Bia and Flowsheet 03 folders were not modified.

## Architecture

Reference inputs → requirements.json → strict schema and Python engineering validation → flowsheet.json → read-only SVG PFD → unchanged Bia Python evaluator → results.json → web tables and checks.

The new Python service is a separate package/process under engine/. The Next.js website contains contracts, request/response validation, a local API proxy and presentation/state logic; it contains no engineering equations. Corporate pages remain available independently of the engine.

## Reference comparison

| Quantity                          | Saved Bia reference | New engine | Difference |
| --------------------------------- | ------------------: | ---------: | ---------: |
| FEED, kg/h                        |              110000 |     110000 |          0 |
| GAS, kg/h                         |               22000 |      22000 |          0 |
| OIL, kg/h                         |               77550 |      77550 |          0 |
| WATER, kg/h                       |               10450 |      10450 |          0 |
| Water carried in OIL, kg/h        |                 550 |        550 |          0 |
| Separator duty, W                 |                   0 |          0 |          0 |
| Component balance residuals, kg/h |                   0 |          0 |          0 |
| Energy residual, W                |                   0 |          0 |          0 |

All four streams reproduce T = 313.15 K and P = 2000000 Pa absolute. Automated tests compare every saved component rate, mass fraction, stream total, T/P, enthalpy flow, component residual and duty. Existing +20 K and 90% water-recovery teaching cases also pass. Fixture and original source SHA-256 checks passed. See engine/fixtures/treinamento-bia-110000/README.md for the 100000/110000 kg/h reconciliation.

## Endpoints

POST /api/digital-engineer/validate-requirements → Python POST /v1/validate-requirements

POST /api/digital-engineer/build-flowsheet → Python POST /v1/build-flowsheet

POST /api/digital-engineer/calculate → Python POST /v1/calculate

Python additionally provides GET /health and GET /v1/reference.

## Verification completed

- 14 Python tests passed, including numerical equivalence, validation, topology, fingerprint and HTTP checks.
- 47 Vitest tests passed, preserving the original website tests and adding contract/API/workflow coverage.
- 4 Chrome browser tests passed: complete reference calculation and recalculation, stale results, layout preservation, invalid recoveries, late responses, mobile layout and engine-unavailable handling.
- Desktop and mobile screenshots inspected; PFD and tables scroll within their containers on narrow screens.
- Contract parity, ESLint, TypeScript, Prettier and git diff whitespace checks passed.
- Production build passed.
- Production smoke checks passed: 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery. Temporary smoke server used SITE_URL=http://127.0.0.1:3102 to match its port.

## Known limitations

Prescribed recoveries and assumed constant Cp only. No rigorous phase equilibrium, phase-dependent enthalpy, latent heat, vessel sizing or predicted separator efficiency. Unavailable calculations have an explicit reason and no fabricated zero. Zero actual flow/duty remains a legitimate result of the available model.

Canonical units only; alternate units are rejected. The browser edits structured reference requirements, not technical prose. No persistence: reload loses unsaved work; use document downloads. No live engine-version polling while idle. Restart the engine after changing Python code or schema files; the service has no hot reload. Local-only development HTTP service.

Numerical and semantic changes invalidate result identity; presentation changes do not. UI request revisions prevent late responses from replacing edited inputs. Previous results are labeled stale and cannot be downloaded as current.

## Local commands

Terminal 1, from the repository root:

```sh
cd engine
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B -m riogineer_engine.server --port 8001
```

Terminal 2, from the repository root:

```sh
npm ci --cache .local/npm-cache
npm run dev
```

Open http://127.0.0.1:3000/digital-engineer (or the Next.js port printed). Full verification commands and alternative browser/interpreter configuration are in engine/README.md.

## Files created

- `contracts/README.md`
- `contracts/examples/requirements.json`
- `contracts/v1/error.schema.json`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `engine/README.md`
- `engine/fixtures/treinamento-bia-110000/README.md`
- `engine/fixtures/treinamento-bia-110000/manifest.json`
- `engine/fixtures/treinamento-bia-110000/recovery_model.py`
- `engine/fixtures/treinamento-bia-110000/separator_inputs.json`
- `engine/fixtures/treinamento-bia-110000/separator_results.json`
- `engine/requirements.txt`
- `engine/riogineer_engine/__init__.py`
- `engine/riogineer_engine/core.py`
- `engine/riogineer_engine/server.py`
- `engine/tests/test_engine.py`
- `playwright.config.ts`
- `scripts/generate-engine-contracts.mjs`
- `src/app/api/digital-engineer/[operation]/route.ts`
- `src/app/digital-engineer/page.tsx`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/workspace.module.css`
- `src/app/digital-engineer/workspace.tsx`
- `src/lib/digital-engineer/api.ts`
- `src/lib/digital-engineer/contracts.ts`
- `src/lib/digital-engineer/workflow.ts`
- `tests/e2e/digital-engineer.spec.ts`
- `tests/engine-fixture.ts`
- `tests/engineering-api.test.ts`
- `tests/engineering-contracts.test.ts`
- `tests/engineering-workflow.test.ts`
- `MILESTONE_1.md`

## Existing files updated

- `.gitignore`
- `.github/workflows/ci.yml`
- `README.md`
- `package.json`
- `package-lock.json`
- `scripts/smoke.mjs`
- `src/config/pages.ts`

Awaiting user review before any LLM interpretation work.
