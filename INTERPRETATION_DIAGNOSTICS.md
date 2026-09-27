# Interpretation provenance investigation

## Evidence available for the reported failure

The reported browser message is emitted only by the interpretation service's provenance gate, after schema validation. At inspection time, `.next/dev/logs/next-development.log` contained only an empty server log entry and a browser React DevTools notice. There was no rejected fact, response body, or rule diagnostic. The service neither stored provider responses nor logged the failing predicate. No browser was connected from which to recover the original input.

Consequently, **the exact historical fact and reason are not recoverable from the available logs**. This change does not claim a captured live response or a successful live replay. The regression inputs are constructed reproductions of the rejection paths, clearly labelled as such. Repeating the original input on the development server will now identify the rejected field, fact index and rule if rejection recurs. Provider variability means a new response cannot establish the contents of an earlier response.

## What the implementation establishes

| Candidate                      | Could produce the reported error?                                                                                                                                                        |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `origin: derived`              | Yes, for any fact, including strings and metadata disguised as supported fields. The previous schema permitted this origin while the service rejected it.                                |
| Nonexact excerpt               | Yes. Case, whitespace, line breaks, punctuation, joined passages, or rewritten identifiers/units can fail substring matching on the cited page.                                          |
| `n-Hexane` → `n_hexane`        | Not by changing the value/component identifier alone: both are schema-valid. It can cause this error if the excerpt is rewritten or origin is marked derived.                            |
| Requested-output normalization | Not by changing the value alone. Rewritten evidence or derived origin can cause this error. Unsupported output values are separately blocked during review.                              |
| Unit normalization             | An invalid unit token produces `PROVIDER_MALFORMED`, not this error. Rewritten evidence or derived origin can produce this error. Numeric unit conversions belong to local approval.     |
| Model/capability metadata      | Unknown fields/properties produce `PROVIDER_MALFORMED`. Metadata presented as an otherwise valid fact can fail provenance, especially if quoted from the manifest instead of the source. |
| Other provenance rules         | Wrong source ID, source type, nonexistent/wrong page, or component supplied for a non-component field (or absent for a component field).                                                 |

The old prompt requested canonical equipment/topology values, consistent component IDs and a canonical product list. It did not explicitly prohibit `origin: derived` for those representation choices. That was an integration ambiguity; it is not proof of which predicate failed in the historical run.

## Behavior changes

- The prompt now explicitly separates source assertions from calculations, preserves source identifiers such as `n-Hexane`, requires one exact contiguous excerpt, and excludes application model/capability metadata from extracted facts.
- Equipment/topology wording is retained in signed facts. A small whole-phrase alias table in local review maps supported wording to the existing capability IDs. Unknown wording remains blocked for review; partial matching never discards additional equipment or connections.
- Product-list formatting and numerical unit conversions remain local. Original facts, values, units and exact evidence remain in the approval audit. Local text changes now carry `deterministic_text_normalization`; unit changes retain `deterministic_unit_conversion`.
- Component IDs already permitted by the contract are preserved, not renamed. Unrepresentable identifiers must be reported as ambiguity. No component mapping, composition inference, recovery inference, equipment expansion or calculation change was introduced.
- Every original provenance predicate remains enforced before any draft is signed. Provider-derived facts are never relabelled or repaired into accepted facts.

## Development diagnostics

With `NODE_ENV=development` (normal `npm run dev`), failures emit `[riogineer:interpretation-validation]` in the local server log. Evidence failures include an event ID, zero-based source/fact indices, allowlisted field and one or more reasons. All failing facts in that source response are reported before rejection:

```json
{
  "stage": "evidence",
  "failures": [
    {
      "source_index": 0,
      "fact_index": 2,
      "field": "components",
      "reason": "derived_origin_forbidden"
    }
  ]
}
```

Reasons are `source_id_mismatch`, `source_type_mismatch`, `page_not_found`, `excerpt_not_exact`, `component_scope_mismatch`, and `derived_origin_forbidden`. Schema failures instead report a sanitized schema path, allowlisted field when available, and Zod rule code. Unknown property names, Zod messages, provider/model names, source text, excerpts, values, credentials and response bodies are not logged. Diagnostics are disabled outside development. The browser receives the existing sanitized error envelope, without diagnostics or approval.

## Regression coverage

`tests/interpretation-provenance.test.ts` exercises every provenance predicate through the Chat Completions adapter, multiple simultaneous failures, exact excerpts and PDF pages, normalized identifiers inside evidence, schema errors including extra metadata, sanitized HTTP responses/logging, production silence, and preservation of original source values through local normalization and approval. The browser suite also checks equipment/topology wording and the resulting audit.

The existing Milestone 1 reference fixture, Python validator, calculation code and contracts are unchanged. Existing tests continue to verify all Bia stream/balance/duty values and byte-identical reference snapshots.

## Validation results

| Check                                           | Result                                                                                            |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Complete Vitest suite                           | 99 passed, including 20 new provenance/normalization cases                                        |
| Complete Python suite                           | 14 passed, including reference snapshots and HTTP tests                                           |
| Complete Playwright suite                       | 12 passed, including one new wording/audit case                                                   |
| Contract parity                                 | Passed                                                                                            |
| ESLint and TypeScript                           | Passed                                                                                            |
| Repository formatting and new report formatting | Passed                                                                                            |
| Production build                                | Passed                                                                                            |
| Production smoke                                | 17 pages, 17 PNG social cards, links, 404s, preview indexing and disabled contact delivery passed |
| Diff whitespace                                 | Passed                                                                                            |
| Live provider replay of the original failure    | Not performed: original input/response unavailable                                                |

The first Python run could not bind its HTTP test socket inside the sandbox; the full run with localhost access passed. The first browser run was interrupted after a concurrent production build removed its nested `.next/e2e` output. A complete isolated rerun passed. Run build and browser tests sequentially with the current output-directory configuration.

Files changed for this investigation:

- `src/lib/digital-engineer/interpretation/validation.ts` (new sanitized diagnostics and shared validation)
- `src/lib/digital-engineer/interpretation/provider.ts` (extraction prompt and schema diagnostics)
- `src/lib/digital-engineer/interpretation/service.ts` (shared validation before signing)
- `src/lib/digital-engineer/interpretation/review.ts` (local wording normalization and audit)
- `src/app/digital-engineer/specification.tsx` (display locally normalized text choices)
- `tests/interpretation-provenance.test.ts` (new regression suite)
- `tests/e2e/specification.spec.ts` (wording/audit browser regression)
- `INTERPRETATION_DIAGNOSTICS.md` (this report)
