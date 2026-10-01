# M18 actual equipment evidence

This directory is separate from both frozen Pre-M18 studies. Production imports
none of these files. The comparator invokes the registered pump callable and
public requirements → flowsheet → calculation adapter, using unchanged independent
reference states and unchanged field allowances.

```sh
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/pump_energy/m18/compare_equipment.py
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/pump_energy/m18/verify_evidence.py
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_pump_energy -v
```

`equipment_comparison.json` records source/reference hashes, 59 cases (43 accepted,
16 rejected), and 10,477 checks. Coverage includes all 46 configurable-study rows,
the first canonical case, four additional flow rates and eight excluded first-study
recipes/pressure conditions. Both actual execution paths run for every case.
There are no production result caches or reference targets in these calculations.

Positive-rise cases use three fresh 16 MPa witnesses; identities use one and must
publish a null isentropic reference. Historical comparison normalization aliases
the inlet only inside this benchmark for identity comparisons. Independent witness
comparisons use the configurable reference where present; no witness evidence is
invented for first-study canonical/flow cases.

`preservation.json` records baseline/final hashes for 42 protected files: both
prerequisite studies, their code/artifacts, the thermodynamic foundation and the
pre-existing `next-env.d.ts`. The baseline includes prior uncommitted work.

Synthetic guard failures are separately labeled in `engine/tests/test_pump_energy.py`.
They do not count as physical independent reference cases. See `MILESTONE_18.md`
for equations, qualification limits, executed gates, retries, exact file inventory
and the pending human acceptance checklist.

`evidence_verification.json` checks current production/reference/protected hashes
and exact equivalence of the actual positive-rise screening allowance and ratio
to the qualified benchmark policy. This verification imports benchmark policy
only in the benchmark layer.
