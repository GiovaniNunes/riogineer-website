# Engineering contracts v1.0

Authoritative schema definitions: `src/lib/digital-engineer/contracts.ts`.
Committed JSON Schema Draft 2020-12 files under `v1/` are generated from Zod and
consumed by Python's pinned jsonschema validator. Schema parity is tested.
No engineering equations live in these definitions.

```sh
npm run contracts:generate
npm run contracts:check
```

All objects reject unknown properties. Finite numeric values, bounds, explicit
unit literals and supported versions are required. Python additionally validates
component-key consistency, positive feed, recovery sums, pressure constraints,
unique IDs, owned port directions and exact supported source/separator/sink
topology. A schema-valid document is not necessarily engineering-valid.

| Document | Purpose |
| --- | --- |
| `requirements.json` | Reference engineering data, units, component basis, source provenance, model/version and parameters |
| `flowsheet.json` | Explicit nodes, ports, streams, directed connections, solver profile, validation and calculation status; independent presentation |
| `results.json` | Immutable run values and provenance, source/model fingerprints, mass/energy checks, tolerances, warnings and unavailable calculations |

`examples/requirements.json` is the 110,000 kg/h reference transformed into this
contract. Download flowsheet/results examples from the running workspace.

Version 1.0 deliberately permits only `single_separator_development` and
`prescribed_component_recoveries@1.0`. Its explicit owner/port/connection structure
can evolve through versioned contracts; this is not a claim that additional
equipment, models or recycles are enabled. Feed and equipment IDs are not fixed
to Bia's IDs. Component names must match across feed, recoveries and Cp; listing
a component alone does not establish physical-property support.

Canonical units: K, Pa absolute, kg/h, J/(kg K), W, mass-fraction recoveries.
This milestone rejects alternate units instead of silently interpreting or
converting them. Feed values are specified; products are calculated and cannot
carry independent specified states. Heat is positive into the separator.
Energy results name their caloric model and reference temperature. Unknown
engineering behavior is represented as `not calculated` plus a reason.

The browser's JSON editor is a deterministic requirements editor, not a technical
specification interpreter. PFD layout is read-only apart from a display-width
toggle. No drawing-to-model importer exists.

## Milestone 3.1: flowsheet/results 1.1

Requirements and the registered calculation model remain unchanged. Newly built
flowsheets use `schema_version: "1.1"` and require `engineering_number` on each
material stream. Results 1.1 add typed `properties` to each stream result;
unavailable quantities use null / `not_calculated`, with explicit units.
The major-version schemas in `v1/` now accept both original 1.0 and new 1.1
branches. Old strict clients must upgrade to read new 1.1 responses; legacy
flowsheets remain accepted and legacy results remain readable. Stream numbering
is assigned by the engine, never inferred by a frontend migration. Regenerate a
legacy flowsheet to obtain numbers. See `MILESTONE_3_1.md` for the numbering rule,
property semantics, fingerprint effects and compatibility limits.
