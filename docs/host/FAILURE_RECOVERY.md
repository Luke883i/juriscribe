# Juriscribe Host Failure & Recovery Contract v1.1

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

Failure order:

`OBSERVE → CANONICAL PATH → SAFE LOCAL REPAIR → FINITE DISTINCT-PATH SEARCH → BOUNDED TRANSIENT RETRY → EXECUTION-PROFILE RESOLUTION → TRUTHFUL DEGRADATION → BLOCK / ADMIN`.

Classify observed failures as `USER_REQUIRED | LOCAL_REPAIRABLE | LOCAL_CONFIGURATION | HOST_CAPABILITY_LIMIT | TRANSIENT | REPOSITORY_OR_RUNTIME | METHOD_LIMIT | UNKNOWN`.

Repair autonomously only when local, safe, scoped, reversible, non-privileged and verifiable. A blocker requires an exhaustion witness for all currently eligible runtime path classes. `UNVERIFIED` is not evidence of impossibility.

If runtime infrastructure is exhausted but `METHOD_ACCESS` is valid, apply execution policy: `ATTESTED_REQUIRED` may block; otherwise LEAN may continue without lowering method or epistemic obligations. Record only the exact infrastructure-dependent attestations/surfaces lost.

Repository/runtime inconsistencies remain fail-closed for the affected operation; prepare evidence-based escalation and never shadow-patch canonical authority.

Recovery is a cross-mode control. Historical probe evidence never becomes current host authority. Memory-only work is not durable recovery. Failure to recover an old session does not automatically prevent a new bound session or LEAN method trajectory from continuing a still-valid human mandate, provided no old runtime authority is reconstructed from prose.
