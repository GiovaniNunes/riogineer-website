# M22 finite application integration plan

Baseline: main at 253b91472a5007e7bd4749a6751c4efbc5066e14; empty index.
Preserve task-start configuration bytes, historical evidence and the master prefix.

Admit only PT_BUBBLE_BELOW and PT_BUBBLE_ABOVE source recipes from the frozen
Pre-M21 sources, discharge 8000000 Pa absolute, efficiency 0.8, explicitly selected
pr_high_accuracy_pt200@1. Keep all 30 historical tuples and omitted defaults.
No interpolation, scaling, efficiency variation, fallback or named PT400.

Before broad integration, exercise the actual source and existing source guard,
then the additive pump selection using M21 APIs. Compare against frozen independent
Pre-M21 source and pump references. After admission/contracts are implemented, repeat
through validation, build, network execution and serialized results; source values
must come from execution, never the oracle. Record the preliminary and final paths
separately. Qualification is complete only for the final application path.

Inherited tolerances: T 1e-7 K; H 1e-6+1e-11|H| J/mol; S
1e-8+1e-11|S| J/(mol K); phase fractions/composition 2e-9; Z
2e-10+1e-9|Z|. Source comparison uses frozen M17 propagated allowances.
Keep exact inverse settings/specification guards, full scans, local liquid guards,
source Hdot, component and total mass, entropy, work E/dH <= 1e-4 including
the 500 K term, equipment and overall energy allowances. No tolerance changes.

Test unknown/conflicting/omitted selection, stale or forged source provenance,
unsupported neighboring physical inputs, controlled solver failure without retry,
calculation identity, UI stale/error behavior, labels, stream tables and exports.
Reuse the unchanged 30-case independent comparison adapter with a new output path.
Separate historical source identity from current source manifests and regression.
Stabilize focused tests before one ordinary full Python/frontend/browser run and
repository gates; use affected reruns for corrections and preserve original logs.
Run Next/build/browser services only in an isolated copy, preserving user services.
Human acceptance, staging, commit, push and deployment remain pending.
