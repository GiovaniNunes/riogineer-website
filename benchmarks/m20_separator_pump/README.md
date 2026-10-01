# M20 implementation evidence

`baseline.json` records the branch, full local/live-remote HEAD, original file hashes,
and master-context prefix before implementation. `implementation.json` contains fresh
production results and explicit comparisons against the frozen independent reference.
`verify.py` also reconstructs the exact input-only scope from the original sources and
accepted ledger. Historical UUIDs and hashes are evidence, never production authorization.

Run from the repository root after production changes are complete:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m20_separator_pump/verify.py
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_separator_pump_integration -v
npx vitest run tests/separator-pump.test.ts
PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m20_separator_pump/regression.py
```

Do not regenerate the independent reference or update the prerequisite preservation
baselines. The implementation-era test protects all original engine modules except
the explicitly changed dispatch/hash adapters, all prerequisite files, the original
master-context prefix, and the unrelated Next/TypeScript configuration bytes.

The result hashes depend on production source and schema bytes. Regenerate fresh
implementation evidence after changing those bytes. Source recipe recognition allows
only 64 machine-epsilon serialization noise; received numbers are retained. Exact
pressure and efficiency combinations remain mandatory. PR inverse association checks
compare the retained input specification exactly and evaluated mole fractions within
the qualified 1e-12 composition tolerance (the existing PR routine normalizes at roundoff).
