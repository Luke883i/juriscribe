# Juriscribe Host State Contract v1.2

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

Canonical runtime state is the sole authority for phase, selected mode, interaction, checkpoint, proof, materialization, delivery and completion. The standalone `LOCAL_HOST_PROMPT.md` state map is a host continuity aid only.

Retain only observed host facts required for continuity: pinned revision/contract, Method Kernel digest, exact human acceptance evidence, selected execution profile, runtime/session identifiers when real, capability observations relevant to the selected profile, infrastructure debt, pending human intent and current canonical interaction projection.

`METHOD_MODE_INTENT` is host-local method intent only and must never be projected as runtime `MODE_SELECTED`.

Per ATTESTED turn: `VERIFY BINDING → ACTIVATE CURRENT NODES → RELOAD CANONICAL STATE → VERIFY INTEGRITY → REFRESH INTERACTION/ARTIFACTS → EXECUTE → RELOAD STATE`.

For LEAN: verify revision/contract/Method Kernel, keep the method trajectory and infrastructure-debt evidence, and preserve inputs/material human decisions required for later replay. Never reconstruct canonical runtime state from remembered chat text.

A material runtime mutation invalidates stale host projections. Recovery resume always follows canonical recovery semantics and fresh host probe requirements.
