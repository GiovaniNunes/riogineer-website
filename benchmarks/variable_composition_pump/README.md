# M19 variable-composition pump evidence

See [qualification](../../PRE_MILESTONE_19_VARIABLE_COMPOSITION_PUMP_QUALIFICATION.md)
and [implementation / acceptance](../../MILESTONE_19.md).

`PLAN.md`, `cases.py` and `reference.py` were fixed before production comparison.
`reference.json` was frozen before production changes and subsequently reproduced
byte-for-byte. `exploration.json` retains the broader phase challenges.
`verify_reference.py` verifies actual installed reference-library and Cp hashes,
including metadata inherited from the unchanged M18 independent environment.
`compare_equipment.py` invokes both the real equipment callable and process adapter;
`separator_compatibility.py` invokes actual M17 outputs without changing their T/P/rates.

Reproduce from repository root:

```sh
.local/pre-m8-venv/bin/python -B benchmarks/variable_composition_pump/explore.py
.local/pre-m8-venv/bin/python -B benchmarks/variable_composition_pump/verify_reference.py
.local/pre-m8-venv/bin/python -B benchmarks/variable_composition_pump/reference.py
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/variable_composition_pump/compare_equipment.py
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/variable_composition_pump/separator_compatibility.py
```

Only `reference.py --write` replaces the independent frozen reference. Ordinary
reference reproduction asserts byte equality. Production comparators regenerate
their own evidence. Keep all source stable during source-hash-sensitive runs.
Dependencies are pinned in `reference.json`; the existing independent environment
uses `benchmarks/pump_energy/configurable_scope/requirements.txt`. Third-party
notices in that directory apply unchanged. No reference dependency is imported by
production. Agreement validates numerical implementation of this specified model,
not experimental accuracy or a global guarantee of convergence.
