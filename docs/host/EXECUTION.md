# Juriscribe Host Execution Contract

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

## Goal

Make the exact pinned Juriscribe revision executable with the smallest truthful local path. Do not turn transport mechanics into user work when the host can perform them.

## Discovery and acceptance binding

Before human acceptance, read only the pre-admission allowlist declared by `ADMISSION.json`. Resolve and retain the full repository revision and presented contract digest. Acceptance must be the exact human evidence required by the current contract. A cold-start `I ACCEPT` received before terms and binding were presented is not valid acceptance.

After acceptance, activate this contract from the same pinned revision. Never fetch a newer host contract into the active session merely because `main` advanced.

## Execution ladder

1. Use an installed runtime only when `RUNTIME_IMPORT=AVAILABLE` and its revision is verified against the pinned revision.
2. Otherwise follow `host_runtime_transport` and try exact pinned canonical source transport.
3. When the current policy allows a minimal bootstrap closure, materialize only that closure first; expand lazily when substantive runtime code is needed.
4. Treat `SOURCE_TO_RUNTIME_BRIDGE` as an observed result. A practical bridge may be direct download→execution workspace, repository fetch→local write→readback→import, or another byte-equivalent local path. Tool names do not define equivalence; verified outcome does.
5. Verify source/readback/binding before calling a transport `AVAILABLE`.
6. Execute real admission/probe/initialize transitions. Never synthesize receipt, nonce, digest, mode choice or phase from source text.

## Duty of Local Sufficiency

Before `USER_REQUIRED`, `HOST_CAPABILITY_LIMIT` or a blocker:

- **HAI FATTO ABBASTANZA?** Attempt the shortest canonical path or establish why it is impossible.
- **LO PUOI FARE TU?** If the missing step is local, safe, scoped, reversible and non-privileged, perform it autonomously.
- **CI SONO ALTRI METODI?** If the first path fails, attempt at most one best-next functionally equivalent local path when practical.

Not attempted means `UNVERIFIED`, not `UNAVAILABLE`. “Change host” is admissible only after the limitation is shown to belong to the host rather than to the first failed method.

## Stop condition

Stop discovery/transport as soon as a revision-bound canonical runtime is executable with a real state carrier. Continue through the canonical fast path when allowed, preserving distinct probe and initialize receipts. End bootstrap in canonical mode selection or an admissible blocker; do not stop merely at “acceptance stored”.
