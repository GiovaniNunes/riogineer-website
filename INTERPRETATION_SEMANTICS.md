# Component identity and scope interpretation follow-up

## Confirmed cause and live evidence

An authorized live call used the configured provider with the exact component-flow, constant-Cp, recovery-row and exclusion wording supplied by the user. The test surrounds that wording with explicit reference-case conditions and the declared component basis `methane, n_hexane, water`; it is not a capture of the earlier browser session.

The live provider returned **all 15 component facts**, marked `specified`, with valid source evidence:

| Source component | Registered ID | Flow fact index | Cp fact index | Recovery fact indices (gas, oil, water) |
| ---------------- | ------------- | --------------- | ------------- | --------------------------------------- |
| Methane          | methane       | 9               | 12            | 15, 16, 17                              |
| n-Hexane         | n_hexane      | 10              | 13            | 18, 19, 20                              |
| Water            | water         | 11              | 14            | 21, 22, 23                              |

Indices are zero-based within that response's 24 facts. Every original fact survived provenance validation. Replaying the **old exact-string lookup against this same live response missed all 15 fields**. The corrected lookup populated all 15, with numerical values matching the unchanged reference. Thus the reproduced defect was neither provider omission nor rejection: the review model joined source-name facts against different canonical keys. Its evidence and conflict lookups had the same inconsistency.

The old prompt said to report equilibrium, sizing and efficiency as unsupported without distinguishing an affirmative request from an exclusion. The corrected prompt explicitly distinguishes them, handles section headings and zero recoveries, and treats explicitly supplied Cp/recoveries as specified rather than implicitly assumed. The live response returned **three cited scope exclusions, zero unsupported requests**. The successful development diagnostic event was `488a240d-be41-48e4-ab0e-9b2d6e5c087e`.

Initial live attempts encountered a transport connect timeout. DNS inspection showed IPv6 addresses first; preferring IPv4 for the diagnostic process allowed the verified run. No provider endpoint, credentials, environment file or production networking configuration was changed. Provider response bodies were not persisted; only a sanitized count/coverage summary was saved under ignored `.local/`.

## Local component identity

The engine accepts an explicit case component basis; it has no global substance/property database. That basis is the case's registry. The shared identity function normalizes valid identifiers by trimming, lowercasing and replacing hyphens with underscores. It is applied consistently to basis IDs, fact keys, review controls, evidence lookup, issue matching, conflicts, corrections and final requirements. It contains no component-specific list, reference values, defaults, or inferred engineering properties.

The signed source facts retain their original names and exact evidence. The audit records `original_component`, the source-name-to-registered-ID mapping, and the deterministic identity derivation separately. Canonical keys enter the existing Milestone 1 contract only after normal review and validation.

Unknown components remain orphan blockers. Duplicate IDs produced by normalization remain duplicate-basis blockers. Contradictory alias facts still require an explicit correction and resolution note. There is no fuzzy chemical matching: `methane`, `methanol` and `CH4` are not treated as synonyms. Missing numerical values stay missing, and explicitly proposed assumptions still require acceptance.

## Scope statements

`scope_exclusion` is an interpretation-layer issue kind with mandatory exact source evidence. A local whole-sentence check recognizes the explicit negative scope construction used in the supplied text. Source ID, source type, page and exact excerpt are checked before signing. Affirmative, negated-negative, mixed request/exclusion, or fabricated statements cannot pass as an exclusion.

The UI presents these statements under **Source scope exclusions**, without an unsupported warning or resolution-note requirement. The audit retains them. Unsupported requests remain unconditional approval blockers, even when a valid exclusion exists elsewhere or the user enters a dismissal note. The local code never removes an unsupported issue merely because its message contains a negative word or mentions an excluded capability. Other exclusion phrasing is not an affirmative request; uncertain interpretation still requires review.

## Development coverage diagnostics

`[riogineer:interpretation-review]` now reports successful extraction coverage in addition to the existing rejection diagnostics. Each registered component/field has its basis index, returned fact indices, an identity-mapping flag, and one of:

- `populated`
- `not_returned_for_component`
- `awaiting_assumption_review`

It also reports orphan fact indices and counts of exclusions and unsupported requests. Diagnostics log neither component names, source text, values, credentials nor provider bodies. They are disabled outside development. HTTP errors remain sanitized. This distinguishes omitted data, failed provenance, identity mismatch and pending assumption decisions without exposing the provider response.

## Regression coverage and validation

The natural-language fixture includes all three flows, all three heat capacities and all nine recoveries from the user-supplied structure. The regression proves the original 15 missing joins, exact source preservation, canonical requirements, unchanged engineering values, generic mapping for unrelated registered names and values, collision/orphan/conflict protection, correction and issue matching, omission and assumption behavior, exclusion evidence, actual unsupported requests, mixed/negative scope phrasing, and development/production logging.

The browser regression populates all 15 fields, displays the exclusions, and approves through the real Python validator with **no manual engineering entries or corrections**.

The Milestone 1 engine, contracts and reference snapshots are unchanged. No graphical editing or broader equipment support was added.

| Validation                     | Final result                                                                                                          |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Complete Vitest suite          | 118 passed (19 new semantic regression cases)                                                                         |
| Complete Python suite          | 14 passed, including byte-identical Bia reference snapshots and all calculated quantities                             |
| Complete browser suite         | 13 passed (one new all-fields/exclusions/approval case)                                                               |
| Authorized live provider check | 15 returned component facts, 15 populated fields, exact reference values, three exclusions, zero unsupported requests |
| Contract parity                | Passed                                                                                                                |
| ESLint                         | Passed without warnings                                                                                               |
| TypeScript                     | Passed                                                                                                                |
| Formatting and whitespace      | Passed                                                                                                                |
| Production build               | Passed                                                                                                                |
| Production smoke               | 17 pages, 17 PNG social cards, links, 404s, preview indexing and disabled contact delivery passed                     |

The first browser attempt stopped during test loading because the new JSON import needed an explicit import attribute. After correcting it, the full suite passed. Live transport retries are described above; the successful live assertions and the deterministic suite both passed. The live call verified extraction/review values; the browser test used a controlled interpretation response and the real Python approval validator. No credentials or provider bodies enter the browser diagnostics.

## Files changed

- `src/lib/digital-engineer/interpretation/components.ts` — generic component identity helpers (new).
- `src/lib/digital-engineer/interpretation/scope.ts` — strict source-exclusion recognition (new).
- `src/lib/digital-engineer/interpretation/contracts.ts` — shared canonical fact keys and evidence-bearing scope statements.
- `src/lib/digital-engineer/interpretation/review.ts` — canonical basis, orphan/conflict checks, audit mapping and scope handling.
- `src/lib/digital-engineer/interpretation/provider.ts` — complete row extraction and request/exclusion prompt rules.
- `src/lib/digital-engineer/interpretation/validation.ts` — issue evidence validation and successful-review diagnostics.
- `src/lib/digital-engineer/interpretation/service.ts` — validate statements and log review coverage before returning.
- `src/app/digital-engineer/specification.tsx` — source-exclusion section; existing controls use the shared identity keys.
- `tests/natural-specification-fixture.ts` — exact natural-language component structure (new).
- `tests/interpretation-semantics.test.ts` — semantic regressions (new).
- `tests/interpretation-provenance.test.ts` — canonical export expectation while retaining source identity.
- `tests/e2e/specification.spec.ts` — all-fields/exclusions/approval browser regression.
- `INTERPRETATION_SEMANTICS.md` — this report.
