# Juriscribe Host Failure & Recovery Contract

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

## Failure order

For a failed host/runtime operation use:

`OBSERVE → CANONICAL PATH → SAFE LOCAL REPAIR → ONE EQUIVALENT FALLBACK → BOUNDED TRANSIENT RETRY → TRUTHFUL DEGRADATION → BLOCK / ADMIN`.

Do not jump from the first failed tool call to user handoff or “change host”. Apply the Duty of Local Sufficiency from [`EXECUTION.md`](EXECUTION.md).

## Classification

Classify observed failures as one of:

`USER_REQUIRED | LOCAL_REPAIRABLE | LOCAL_CONFIGURATION | HOST_CAPABILITY_LIMIT | TRANSIENT | REPOSITORY_OR_RUNTIME | UNKNOWN`.

Repair autonomously only when local, safe, scoped, reversible, non-privileged and verifiable. Retry only genuinely transient failures and keep retries bounded. A fallback must preserve the same required outcome and contract; it must not become a shadow implementation.

A blocker is admissible only when the requirement is necessary now, the direct path was attempted or proved impossible, the host cannot safely repair it, no practical equivalent path remains, the fact is not merely untested/`UNVERIFIED`, and truthful degradation cannot continue the requested operation.

## Repository/runtime defect

If a same-revision contract, runtime, manifest, host node or canonical state remains internally inconsistent after local verification, fail closed for the affected operation. Do not patch authority in the prompt. Prepare an `ADMIN_ESCALATION` record with revision, contract digest, operation/phase, relevant observed capabilities, expected behavior, observed behavior, attempted remediation, minimal reproduction and `confirmed|suspected`. Exclude secrets. Report escalation only if actually sent through an authorized channel; otherwise give the record to the user.

## Recovery

Recovery is a cross-mode session control, not a scientific mode. Create/import/resume bundles only through canonical runtime operations. A receiving host performs the required fresh capability probe; historical probe evidence never becomes current host authority. Preserve scientific checkpoint semantics across pure transport/rebind operations. Memory-only work must not be advertised as durable recovery.

If recovery itself is impossible, explain the precise missing carrier/capability and the smallest safe next action; do not reconstruct the session from prose.
