# PRE-M21 configurable separator/pump qualification

Study-only evidence; M21 remains unimplemented. Read the root
`PRE_MILESTONE_21_CONFIGURABLE_SEPARATOR_PUMP_QUALIFICATION.md` for the decision,
counts, failure analysis and limitations. No servers or browser are required.

From the repository root, reproduce without overwriting artifacts:

```sh
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/capture_sources.py
.local/pre-m8-venv/bin/python -B benchmarks/configurable_separator_pump/reference.py
.local/pre-m8-venv/bin/python -B benchmarks/configurable_separator_pump/phase_reference.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/compare.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/phase_compare.py
engine/.venv/bin/python -B -m unittest discover -s benchmarks/configurable_separator_pump -p 'test_*.py' -v
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/verify.py
```

`capture_sources.py` repeats actual M17 execution and compares numerical results,
semantic input/requirements hashes, units and status while retaining the original
captured UUIDs. The remaining calculation commands compare byte-for-byte; tests
only read artifacts. Reproduction is separate from the comparison assertions.
`verify.py` checks all original tracked bytes, the unchanged master-context prefix,
HEAD/index, and the study manifest. It does not query the remote.

For first creation in an empty extension only, use `--capture` for sources and
`--write` for the generators, in dependency order as above. Each refuses to
overwrite its own artifact. The baseline is a one-time capture, not regenerated.
Manifest creation (`verify.py --write`) follows report completion. Never pass
write flags to inherited benchmark modules. Environments already exist; no
package installation, service changes, application build or deployment is needed.

Independent environment pins and notices:
`../pump_energy/configurable_scope/requirements.txt` and `THIRD_PARTY_NOTICES.txt`.
Reference generation checks installed versions, Thermo source hashes and Poling
Cp-data hash against the historical reference. Thermo 0.6.0 is configured to PR
0.45724/0.07780; quadratic a mixing with (1-kij), linear b mixing, Soave alpha,
constant explicit zero 2x2 kij. Component constants and Poling ideal Cp coefficients
are stored in `reference.json`. Pure ideal H and S are zero at 298.15 K and
101325 Pa; ideal mixture entropy includes -R sum(z ln z). H and S are sensible
relative values, without formation offsets or third-law entropy. Each equilibrium
phase has its own composition and root. Independent direct equations cross-check
library calorics. This is independent implementation agreement for a shared PR
model and property-data basis, not experimental accuracy or a second physical EOS.

Inputs: T K, P Pa absolute, z mol/mol, phase F mol/s; mass kg/h = F*z*MW*3.6
with MW kg/kmol; mol/s = kmol/h /3.6. H J/mol, S J/(mol K), Hdot/power W = F*H.
Reference source recipes are independently calculated with M17 reference helpers.
Pump inputs use actual production liquid T/P/z/F to isolate downstream solver
agreement; this does not transfer separator qualification from pump results.
Reference processes assert that no `riogineer_engine` module is imported.
Production experiments never use reference endpoint values as solver answers.
Only the explicitly labelled standalone PH diagnostic uses a reference target;
it cannot repair or replace the failed production PS prerequisite.

`PLAN.md` fixes tolerances and dispositions. `common.py` defines 64 candidate
entries, including repeated identity/10 kPa controls. `sources.json` retains
24 actual separator executions. `reference.json` and `production.json` hold full
state/scan/root/source/provenance diagnostics. `candidate_ledger.json` separates
application admission, raw numerical stage, guarded callable, independent result
and prototype. The phase artifacts add independent lower-pressure witnesses.
The prototype preserves failed samples and refuses brackets spanning them,
competing sampled candidates, root failures and failed fresh residuals. Even a
resolved local root retains incomplete coverage and never claims global uniqueness.

Inherited integration tests can be run with:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m unittest engine.tests.test_separator_pump_integration -v
```

The historical preservation assertion compares `next-env.d.ts` to the older
M20-implementation baseline. It fails for the unrelated configuration already
present at study start; do not restore that file or rewrite the historical test.
The new baseline verifies the current authorized bytes instead. The report records
the actual full-suite outcome, including this assertion failure.

Additional read-only diagnostics, after the primary comparison artifact exists:

```sh
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/iteration_diagnostic.py
engine/.venv/bin/python -B benchmarks/configurable_separator_pump/integration_checks.py
```

Their initial creation used `--write`, also refusing overwrite. The iteration
study exercises 200/400 iteration caps via public settings in the benchmark only,
with unchanged tolerances and a default-PT final guard. It is not a changed
production default. `integration_checks.json` records full inlet-contract results
and prototype energy closure against the retained upstream Hdot, including the
separator duty and vapor stream. Generate these diagnostics before running the
complete new tests. All computation reproduction commands are independent of
manifest verification, so the initial-baseline verifier need not be rewritten
when running this evidence in a later checkout.

Primary production comparisons use four independent worker processes; ordered
collection keeps the frozen artifact deterministic. They invoke read-only engine
functions and do not operate servers. The ledger separates 64 entries from
62 distinct input combinations; the repeated identity/10 kPa controls explain
32 admitted entries representing only 30 distinct existing M20 combinations.
