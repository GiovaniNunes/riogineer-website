# Milestone 3 — First Live End-to-End Digital Engineer Validation

## Validation basis

The user reports manually completing the first successful live end-to-end RIOGINEER Digital Engineer workflow through the web interface. This report records those manual observations; they were not rerun by the coding agent. The case is Treinamento Bia — three-phase separator, reference case `THREE_PHASE_SEPARATOR_DEV_001`.

The inputs are **synthetic development assumptions, not I-ET or client data**. This milestone validates the integrated reference workflow with the registered **Prescribed Component Recoveries — Development Model** (`prescribed_component_recoveries@1.0`). It does not establish rigorous phase equilibrium or general process-simulation capability.

## Manually validated workflow

Natural-language specification → live LLM interpretation → deterministic evidence anchoring → structured requirements → human review → explicit approval of development-model assumptions → mandatory deterministic requirements validation → structured flowsheet → generated read-only PFD → Python Engineering Engine → deterministic mass/energy calculations → checks and results.

The user observed no missing information, ambiguities, conflicts or false unsupported-capability warnings during interpretation. Approval returned HTTP 200 from `/api/digital-engineer/approve-requirements`. The generated PFD correctly represented the structured connections:

```text
FEED → SEP_1
         ├── GAS   → GAS_SINK
         ├── OIL   → OIL_SINK
         └── WATER → WATER_SINK
```

The structured flowsheet remains the engineering source of truth; the PFD is a read-only representation. Generation and calculation are separate actions following approval and deterministic validation.

## Reference inputs and observed results

Feed and separator temperature: **313.15 K**. Feed and separator pressure: **2,000,000 Pa absolute**. Caloric reference temperature: **273.15 K**. Total feed: **110,000 kg/h**.

| Component | Feed (kg/h) | Constant Cp (J/(kg K)) | Gas recovery | Oil recovery | Water recovery |
| --------- | ----------: | ---------------------: | -----------: | -----------: | -------------: |
| methane   |      22,000 |                  2,200 |          1.0 |          0.0 |            0.0 |
| n_hexane  |      77,000 |                  2,200 |          0.0 |          1.0 |            0.0 |
| water     |      11,000 |                  4,180 |          0.0 |         0.05 |           0.95 |

| Quantity                    | Manually observed result |
| --------------------------- | -----------------------: |
| FEED                        |             110,000 kg/h |
| GAS                         |              22,000 kg/h |
| OIL                         |              77,550 kg/h |
| WATER                       |              10,450 kg/h |
| Separator heat duty         |                      0 W |
| Total mass-balance residual |                        0 |
| Energy-balance residual     |                      0 W |

The UI reported that component mass-balance checks and the energy-balance check passed. These observations agree with the existing deterministic reference basis. The zero duty is specific to this reference case and its model assumptions; it is not a general separator prediction.

## Responsibility, review and traceability

The LLM extracts and organizes source assertions; it does not calculate phase equilibrium, engineering balances or simulation results. Missing data and unresolved assumptions must remain explicit. The human reviews the interpreted requirements and explicitly accepts the development-model assumptions. Mandatory deterministic validation follows that approval before the downstream workflow is enabled.

The Python engine distributes components using prescribed recovery fractions, calculates the available constant-Cp energy accounting, and evaluates mass/energy checks. No engineering equations were moved into the frontend.

Evidence anchoring treats provider excerpts as locators, requires unique deterministic matches and stores exact original-source substrings. Original source pages are retained; relocated evidence preserves the provider candidate separately. Ambiguous matches and meaning-changing edits are rejected. See [EVIDENCE_ANCHORING.md](EVIDENCE_ANCHORING.md).

Topology normalization recognizes the supported one-feed / one-three-phase-separator / gas-oil-water configuration, including equivalent connection wording with separately stated outlets. Additional feeds, equipment, recycles and unsupported outlets remain blocked. Original source evidence is not rewritten. See [TOPOLOGY_NORMALIZATION.md](TOPOLOGY_NORMALIZATION.md).

## Approval feedback correction

The reported confusing feedback was a presentation defect: the PFD empty state always said “Approve the requirements, then generate the PFD.” even after workflow validation succeeded. The existing approval confirmation appeared above the review form, away from the action; the disabled approval button retained its imperative label.

The minimal correction adds visible confirmation beside the approval action, labels the disabled button “Requirements approved,” and changes the PFD empty state after validation to direct the user to Generate PFD. Source/review edits still invalidate approval. Failures retain the error alert and cannot enable PFD generation. No validation contract, calculation, model, topology normalization or evidence-anchoring behavior changed.

## Automated coverage — distinct from the manual run

The automated suites independently cover contract validation, deterministic reference results and checks, provenance, evidence anchoring, topology rejection/normalization, review and approval controls, invalidation/stale responses, PDF extraction and browser workflows. Controlled provider responses in browser tests are not live LLM runs.

The new browser success regression starts from a controlled interpreted draft, accepts the development assumptions, submits approval through the actual local approval route and Python validator, checks HTTP 200, visible approval confirmation and an enabled Generate PFD action, then confirms that editing the review invalidates success. It stops before generating a PFD. A separate controlled HTTP failure regression checks that success is never displayed and PFD generation remains disabled.

Validation executed for this documentation and UX change:

| Check                                                 | Result                                                                                                     |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| TypeScript unit/integration suite                     | 173 tests passed in 12 files                                                                               |
| Python suite                                          | 14 tests passed, including HTTP and reference snapshots                                                    |
| Browser suite                                         | 16 tests passed, including both new approval-feedback regressions                                          |
| Contract parity                                       | Passed                                                                                                     |
| ESLint                                                | Passed                                                                                                     |
| TypeScript                                            | Passed                                                                                                     |
| Repository formatting and milestone report formatting | Passed                                                                                                     |
| Production build                                      | Passed                                                                                                     |
| Production smoke                                      | 17 pages, 17 PNG social cards, internal links, 404s, preview indexing and disabled contact delivery passed |
| Diff whitespace                                       | Passed                                                                                                     |
| New live-provider requests                            | 0                                                                                                          |

Python HTTP and browser/smoke checks used temporary localhost servers with the required sandbox access. Hash comparison confirmed that the engineering engine, reference fixtures, requirements contracts and interpretation library (including evidence anchoring and topology normalization) remained byte-identical to their pre-task state.

Created: `MILESTONE_3.md`. Modified: `docs/RIOGINEER_MASTER_CONTEXT.md` (sections 27, 54–57, 61–62 only), `src/app/digital-engineer/specification.tsx`, `src/app/digital-engineer/workspace.tsx`, and `tests/e2e/specification.spec.ts`.

## Reproducibility and limits of the record

Run the website at `http://127.0.0.1:3000/digital-engineer` and the Python engine at `http://127.0.0.1:8001`, using the setup in [MILESTONE_2.md](MILESTONE_2.md) and [engine/README.md](engine/README.md). Live interpretation requires server-side provider configuration; credentials must remain outside version control and browser output. The reference contracts are in `contracts/examples/`, and saved deterministic reference artifacts are under `engine/fixtures/treinamento-bia-110000/`. The natural-language regression fixture is `tests/natural-specification-fixture.ts`.

For a manual reproduction, submit the specification with all inputs above, review its evidence and model assumptions, approve and validate requirements, generate the PFD, then calculate and compare the reported stream flows, duty and balances. Do not bypass human review or substitute defaults for missing facts. Preserve the source, reviewed requirements, flowsheet, results and available version metadata for a future run record.

The manual report supplies the case basis and observed UI results, not a captured provider response, exported run bundle, exact provider/model version or engine run identifier. The reference case ID should not be confused with an interpreted draft's generated `SPEC_...` case ID. Deterministic results are reproducible from the same model and inputs; provider wording may vary. The coding agent made no new live-provider call for this milestone update.

## Current limitations and recommended next steps

There is no rigorous vapor-oil-water equilibrium, separator sizing, geometry-based separation-efficiency prediction, graphical PFD editing or broader web-integrated equipment support. Recoveries are prescribed; constant Cp accounting does not model latent heat or rigorous phase-dependent thermodynamics. PDF interpretation is text-based without OCR. Evidence and capability normalization are conservative and may require review of unrecognized wording. This local prototype validation does not establish production readiness or validate client/field data.

Preserve the demonstrated reference and its regression tests, retain reproducible run artifacts, and collect engineering-user feedback. Next, define qualification criteria and benchmark cases for a suitable thermodynamic separator model before implementation. Additional equipment, process networks/recycles, graphical editing and Field Design integration remain future development subject to explicit scope and validation. None is introduced by this milestone.
