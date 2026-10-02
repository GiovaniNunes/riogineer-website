# Pre-M20 phase-aware separator-liquid contract study

Study only. No current pump-wrapper support or production schema change. See
`../../../PRE_MILESTONE_20_SEPARATOR_LIQUID_CONTRACT_QUALIFICATION.md` for the
contract, policy, decision, limitations and exact inventory.

From repository root:

```sh
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/capture_sources.py
.local/pre-m8-venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/reference.py
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/compare.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/low_pressure_separator_pump/phase_contract -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/low_pressure_separator_pump/phase_contract/verify.py
```

These commands verify without rewriting. The first reproduces 12 targeted
separator outputs numerically while retaining captured real run IDs; production
UUID generation is intentionally not byte deterministic. `sources.json` is an
immutable source-result capture. Its original creation used `--capture`, which
refuses to overwrite it. Source result streams, equipment, units and semantic
input hashes must reproduce exactly; new UUIDs are not substituted into evidence.
All other JSON artifacts reproduce byte-for-byte in fresh processes.

For initial extension artifact creation only, reference.py, compare.py and
verify.py accept `--write`, in that order. They write only their respective files
in this extension directory. Do not regenerate any parent study artifact.

Existing independent environment/pins/notices are reused from
`benchmarks/pump_energy/configurable_scope/` from repository root. New reference
checks installed versions, actual Thermo module hashes and Poling-data hash against
the preserved first study. Reference calculations never import production code.

`adapter.py` and `pump.py` import production routines only, with no independent
library, frozen table or file reads. Runtime callers supply resolved current
source results and expected current calculation identity. Both modules are
non-production proposals, and do not bypass the M19 wrapper to claim support.
The minimal representation reuses stream material/property fields and adds
`state_context`; internal parent/flash/fugacity evidence is not public schema.

`production.json` retains source adapter results, local endpoint checks for all
30 previously accepted tuples, 72 independent new witness/boundary probes,
contract negatives, eight fresh representative pump/identity paths and both
unchanged known PS failures explicitly reused from the first study.
`candidate_ledger.json` binds extension file hashes and lists proposed exact
source-input-fingerprint/P2/eta restrictions. Those are qualification restrictions,
not a property lookup or a general configurable operating envelope.

`preservation.json` includes tracked working files and all original untracked
study files. `baseline.json` records initial master-context length/hash so the
verifier protects its entire existing prefix while permitting a concise append.
All original study code/artifacts remain unchanged. No services are needed.
