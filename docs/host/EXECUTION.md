# Juriscribe Host Execution Contract v1.1

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

## Goal

Reach the exact pinned Juriscribe runtime through the smallest truthful local path without turning host transport into user work. If runtime authority remains unavailable, hand off to the separately authorized Method Access policy without degrading method or epistemic discipline.

## Discovery and binding

Before human acceptance, read only the current `pre_admission_allowlist`. Resolve and retain the full revision and presented contract digest. Host-local capability observation is allowed; post-admission host contracts, `RUNTIME_LOCAL_HOST.md` and `METHOD_KERNEL.json` are not authoritative before acceptance/binding.

After valid acceptance, load this node, the verified same-revision cognitive companion and `METHOD_KERNEL.json` exactly as declared by `ADMISSION.json`.

## Finite local runtime search

Enumerate materially distinct, safe, proportionate runtime-transport classes from observed capabilities. Prefer, in order where eligible: verified installed runtime; canonical local checkout/package/cache/mount; connected repository/API exact bytes to local import; public/read-only exact bytes to local import; verified source-to-runtime bridge; canonical operation-specific closure; full pinned runtime package.

`gh` is not a dependency and is `UNAVAILABLE` unless actually observed. Do not install arbitrary software, request unnecessary credentials, elevate privileges, use non-canonical sources or infer private dependency subsets.

Each semantic path class is attempted at most once per stable failure signature. A genuinely transient failure may receive one bounded retry. Record an evidence-bearing exhaustion witness. Stop search immediately when a revision-bound runtime with a real state carrier becomes executable.

**LEAN is not a runtime-search path.** Only after capability discovery and eligible runtime paths are exhausted may execution policy resolve to LEAN under the accepted Method Access contract.

## Execution profile

Default preference is `ATTESTED_PREFERRED`; do not add a mandatory profile question. An explicit user request may set `ATTESTED_REQUIRED` or `LEAN`.

- `ATTESTED`: execute real admission/probe/initialize, real mode selection and all current runtime gates. Runtime reachability alone does not certify receipts, proofs or `COMPLETE`.
- `LEAN`: require valid `METHOD_ACCESS`; honor LEAN even if runtime is technically reachable but intentionally not used as authority for that work. Use `METHOD_MODE_INTENT`, never synthesize runtime mode state or receipts.

Any LEAN → ATTESTED transition requires canonical replay/revalidation of inputs and material human decisions plus recomputation of applicable gates and fresh artifact evidence.

## Stop condition

End transport discovery at the first executable bound runtime, or after a complete exhaustion witness. A technical blocker is admissible only when the requested execution policy cannot proceed and no safe equivalent runtime path remains. Infrastructure-only limitations do not become epistemic limitations.
