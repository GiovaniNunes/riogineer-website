# Single-separator topology classification

The reported warning originated in the local review gate, not the engineering engine. `normalize` accepted only a small whole-phrase alias list. The sentence “The process shall comprise one feed stream entering one three-phase separator.” matched none of those aliases, even when a separate cited outputs fact supplied gas, oil and water. The UI used the same context-free normalization and displayed the raw sentence as unsupported.

A bounded, complete-input grammar now recognizes the existing one-feed / one-separator connection and exactly three distinct gas/oil/water outlets. It accepts singular count wording, feed-to-separator verbs, arrow/list notation, and reordered outlet lists. A connection sentence without outlets requires an explicit outputs fact from the current review values; missing outlets are not inferred. Full topology descriptions remain self-contained. The existing canonical identifier and Portuguese alias remain compatible.

The UI, capability gate, conflict comparison and normalization audit all use the same outputs context. Original facts and evidence remain unchanged. Every clause must be consumed: extra feeds, separators, recycles, outlets, equipment, negation and unknown clauses remain blocked. Unrecognized wording remains blocked conservatively; this is not unrestricted natural-language understanding. Existing provider unsupported issues and contradictory facts are not suppressed.

Regression tests cover the exact reported sentence, equivalent connected descriptions, each requested unsupported case, missing/duplicate outlets, reversed direction, equipment scope, preservation of evidence, and the unapproved UI state. No case name or reference number participates in classification.

## Validation

All checks passed: 173 Vitest tests, 14 Python tests, 14 Playwright tests, contract parity, ESLint, TypeScript, formatting, production build and diff whitespace. Production smoke passed for 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery. The live input uses the existing full natural-language reference data with its topology line replaced by the exact quoted sentence; its separate gas/oil/water product statement is retained. The complete latest UI input was not supplied separately.

The live test ends at interpretation/review. Automated regression suites retain their existing synthetic approval and calculation scenarios.

## Live result

Exactly one provider request passed. The topology mapped to the supported identifier and there were zero unsupported-capability warnings. All 24 facts passed provenance and all 20 explicit numerical fields matched their reference values and units. All 15 component fields populated. The provider returned three scope exclusions and zero unsupported requests. The only remaining blocker was explicit development-model acceptance.

No requirements were approved, no PFD was generated and no engineering calculation was run for the live case. The sanitized result is saved in ignored `.local/live-topology-summary.json`.
