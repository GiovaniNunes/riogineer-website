# RIOGINEER Engine — Milestone 1

Separate Python HTTP service for one prescribed-recovery separator. Python 3.10+.
No LLM, database, authentication, cloud deployment, additional equipment, recycle
solver, draw.io integration or new thermodynamics is included.

## Run locally

From the website repository, in terminal 1:

```sh
cd engine
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B -m riogineer_engine.server --port 8001
```

In terminal 2, from the website repository:

```sh
npm ci --cache .local/npm-cache
npm run dev
```

Open http://127.0.0.1:3000/digital-engineer (or the actual Next.js port printed).
The engine binds only to 127.0.0.1. The server-side environment variable
`RIOGINEER_ENGINE_URL` defaults to `http://127.0.0.1:8001` and may only select a
local HTTP service. Do not prefix it with NEXT_PUBLIC_. No environment file is
needed for the default ports. Both processes must remain running.

## Architecture and ownership

Browser requirements → Next.js request validation/proxy → Python schema and
engineering validation → flowsheet → read-only SVG → Python evaluator → results.

`riogineer_engine/core.py` adapts generic IDs, ports and connections to the Bia
evaluator. It preserves checks formerly applied by the fixed Bia adapter (such
as no separator pressure increase). It imports the immutable evaluator snapshot
from `fixtures/treinamento-bia-110000/recovery_model.py`; no equations are copied
into TypeScript or changed in the snapshot. Startup verifies its SHA-256 hash.
The original Bia and Flowsheet 03 directories are never dependencies at runtime
and are not modified.

`server.py` supplies a local HTTP boundary. It does not write case files or retain
case state. The browser holds the working documents; downloads are explicit.
Refreshing the page reloads the reference and loses unsaved work. This server is
for local development and is not a production hosting design.

## Endpoints

| Website (POST) | Python (POST) | Input → output |
| --- | --- | --- |
| `/api/digital-engineer/validate-requirements` | `/v1/validate-requirements` | requirements → validated requirements and warnings |
| `/api/digital-engineer/build-flowsheet` | `/v1/build-flowsheet` | requirements → flowsheet |
| `/api/digital-engineer/calculate` | `/v1/calculate` | flowsheet → results |

Python also provides `GET /health` and `GET /v1/reference`. The browser calls only
the Next.js API. Unknown operations, additional fields, incompatible units,
unsupported versions, nonfinite values, duplicate JSON keys at the Python
boundary, invalid recoveries and unsupported topology are rejected. Errors are
structured; no substitute calculated result is returned. Request limit: 128 KiB;
Next-to-engine deadline: 15 seconds.

## Contracts and freshness

See `../contracts/README.md`. `requirements.json` identifies the feed and one
separator. `flowsheet.json` explicitly contains one source, one separator, three
sinks, four streams and four directed connections. Ports are `inlet`, `gas`,
`oil`, `water` on the separator. Layout is a separate presentation object.

Calculation identity hashes the canonical flowsheet (excluding presentation,
calculation status and validation display metadata), the engine implementation,
schema files, evaluator and selected model. Object key and graph-array ordering
are canonicalized. Numerical, component, model, operating-condition and semantic
connection changes alter the fingerprint. Layout-only changes do not.

The browser invalidates previous results immediately when requirements change,
even before validation. Results remain visible with STALE labeling; stale result
download is disabled. Request revisions prevent late responses from replacing
an edited model. A failed run also invalidates current status. An engine change
requires validation/PFD generation again before results can be accepted. There
is no live engine-version polling while a page is idle.

## Reference and physical limits

The fixture README reconciles the older 100,000 kg/h documentation with the
current 110,000 kg/h reference. Snapshots and manifest were captured before
implementation. The old README in the original folder remains untouched.

Expected totals: FEED 110,000; GAS 22,000; OIL 77,550; WATER 10,450 kg/h.
OIL contains 550 kg/h of carried-over water. At feed and separator T = 313.15 K
and P = 2,000,000 Pa absolute, calculated duty and residuals are zero. The
existing +20 K teaching case gives 1,465,444.444444444 W duty with unchanged mass
flows. Tests compare every saved stream quantity, component residual and duty.

Recoveries and Cp are specified assumptions. No phase equilibrium, latent heat,
pressure-dependent enthalpy, geometry, sizing or predicted efficiency is
calculated. OIL is a stream service, not an equilibrium phase claim. Unavailable
calculations explicitly use `status: "not calculated"` and a reason, never a
numeric zero. Genuine absent streams and calculated zero duty retain zero.

## Verification

From `engine/`:

```sh
.venv/bin/python -B -m unittest discover -s tests -v
```

From the website root (Python dependencies must already be installed):

```sh
npm run contracts:check
npm test
npm run lint
npm run typecheck
npm run build
npm run test:e2e
```

E2E tests start isolated services on ports 8101 and 3100 and stop them afterward.
They use installed Google Chrome by default. For bundled Chromium instead:

```sh
npx playwright install chromium
PLAYWRIGHT_CHANNEL=chromium npm run test:e2e
```

`ENGINE_PYTHON` can select an alternate interpreter with the pinned dependencies.
Tests default to `engine/.venv/bin/python`, falling back to `python3` when absent.
Browser screenshots and test outputs are under ignored `.local/`.
