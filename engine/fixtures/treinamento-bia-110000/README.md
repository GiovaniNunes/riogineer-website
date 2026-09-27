# Treinamento Bia reference: 110,000 kg/h

Captured before Milestone 1 implementation. These input, saved-result and evaluator files are byte-for-byte snapshots; manifest.json records their original paths and SHA-256 hashes. The originals remain untouched.

## Documentation reconciliation

The source README_CODEX.md describes the older 100,000 kg/h case (20,000 methane, 70,000 n-hexane, 10,000 water). That basis belongs to its original/ archive and is NOT the current numerical reference.

The current separator_inputs.json, separator_results.json and teaching specification use 110,000 kg/h (22,000 methane, 77,000 n-hexane, 11,000 water). Expected outlets are GAS 22,000; OIL 77,550 (including 550 water); WATER 10,450 kg/h. At 313.15 K and 2,000,000 Pa absolute, calculated surrogate duty is 0 W. This note supersedes the older README basis for this implementation without editing the reference folder.

The saved results omit newer engine/model metadata. They remain the numerical comparison fixture, not the new API contract. The evaluator snapshot is imported by the new Python engine without changing its equations. It is the shared evaluator used by the active Bia runner, not the archived standalone runner.

All property and recovery inputs are synthetic development assumptions. Passing bookkeeping checks does not validate phase equilibrium or equipment performance.
