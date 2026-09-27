# Deterministic evidence anchoring

Provider evidence is a locator. Before signing a draft, facts and cited issues must resolve to one contiguous substring on the cited original source page. The locator preserves word case and identity, numeric spelling (including decimal/grouping punctuation and scientific notation), signs, and unit operators. It tolerates whitespace, line breaks, line-leading bullets before words, Unicode dash variants, and bounded separator/sentence punctuation differences. It performs no fuzzy matching, synonym substitution, unit conversion, identity normalization, reordering, or joining of separate passages.

Both exact and presentation-equivalent occurrences participate in the uniqueness check. Multiple matches reject the response with sanitized `excerpt_ambiguous` diagnostics; no match retains `excerpt_not_exact`. Source/page identity, component scope and derived-origin restrictions remain enforced. Unit expressions cannot be truncated at a slash or exponent boundary.

The signed draft retains the untouched original source pages alongside their existing hashes. For relocated evidence, `excerpt` is the exact original substring, `provider_excerpt` retains the candidate, and `source_start`/`source_end` are JavaScript UTF-16 offsets on the cited page. These local metadata fields are forbidden in provider responses. Existing drafts without source pages or locator metadata remain schema-compatible. Full source retention increases audit size; the existing approval size limit remains enforced.

The regression at source index 0, fact index 2, field `components` is a constructed formatting reproduction, not a recovered historical provider response. Tests also cover altered values, units, component/equipment/outlet identities, signs, decimals, pressure basis, exponents, omitted components, ambiguous exact and normalized matches, issue evidence, and preservation of the source and provider candidate.

Milestone 1 calculations, engineering contracts, and reference fixtures remain byte-identical to their pre-task state. No engineering equations or Treinamento Bia reference values changed.

## Validation

- Vitest: 144 tests passed.
- Python: 14 tests passed, including HTTP tests and reference snapshots. The HTTP tests required localhost access beyond the sandbox.
- Playwright: 13 tests passed.
- Contract parity, lint, TypeScript, repository formatting and diff whitespace checks passed.
- Final production build passed.
- Production smoke passed: 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery.

The automated suites exercise their existing synthetic approval/calculation regressions. The live test is restricted to interpretation and the unapproved review model.

## Single live interpretation result

One configured-provider request used the existing `naturalSpecification` fixture via `naturalFixture()`. All 24 returned facts passed provenance; all 20 explicit numerical fields populated the unapproved review model with matching reference values and units. All 15 component fields populated, with zero orphan facts. The source pages were preserved exactly. Three scope exclusions and zero unsupported requests were returned. The only review blocker was acceptance of the development model and its limitations.

This particular response returned exact excerpts, so zero facts required presentation-tolerant relocation. The fallback is verified by deterministic regressions; this run does not claim to reproduce the historical provider wording. The sanitized summary is in ignored `.local/live-anchoring-summary.json`; no credentials or raw provider response were saved. No retry, approval, PFD generation or engineering calculation was performed for the live case.
