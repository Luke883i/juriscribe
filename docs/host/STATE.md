# Juriscribe Host State Contract

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

## Canonical state

Runtime state is the sole authority for phase, mode, interaction, checkpoint, proof, materialization and completion. Host memory is a carrier/cache, never a competing state machine. A memory session may be valid work state without durable recovery; scratch I/O is not user delivery.

Retain only observed/bound host facts needed for continuity: pinned revision/contract, acceptance context, runtime/session identifiers, sealed capabilities and the current canonical interaction projection. Do not silently bind an active session to a newer repository revision.

## Per-turn environment tick

For every active-session turn, apply the minimum cycle:

`VERIFY BINDING → ACTIVATE CURRENT HOST NODES → RELOAD CANONICAL STATE → VERIFY INTEGRITY → REFRESH INTERACTION + ARTIFACT PROJECTION → EXECUTE ALLOWED ACTION → RELOAD CANONICAL STATE`.

If no runtime mutation is needed, the final reload may be the same verified state. Never answer from a stale interaction card after a material mutation.

## Continuity rules

- Preserve the initial human intent as pending input until Juriscribe can consume it; do not reinterpret it as acceptance or mode selection.
- Do not repeat admission/probe/initialize once the valid session has passed those transitions.
- Material user decisions, new inputs and runtime mutations must flow through canonical runtime operations and their staleness rules.
- Completion is read from canonical completion state, never inferred from prose or apparent artifact presence.
- If context is lost, use supported recovery. Do not reconstruct authoritative runtime state from remembered chat text.

When state cannot be verified, activate [`FAILURE_RECOVERY.md`](FAILURE_RECOVERY.md); mark the affected fact `UNVERIFIED` and fail closed only to the extent required by the missing verification.
