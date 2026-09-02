# Juriscribe Local Session Environment v1

Authority: `HOST_COMPOSITION_ONLY` — no scientific, legal, mode, proof, materialization or completion authority.

This is the root contract for a conversational host. It is binding only when activated by `ADMISSION.json` from the same revision already pinned to the human acceptance context.

## Identity

The persisted scientific session remains the durable, transport-independent asset. On a compliant conversational host, Juriscribe instantiates and governs that session as a **revision-bound local environment inside the current chat session**. Chat, provider, connector, browser and filesystem are replaceable host surfaces; replaceability does not make the chat a mere remote control and does not make the host a second Juriscribe implementation.

The local environment is the composition of canonical binding, executable runtime, state carrier, Juriscribe session, interaction state, workbench/dashboard, user-facing artifacts and recovery surface. This composition projects existing authority; it creates none.

## Contract graph

The normative nodes are:

- [`EXECUTION.md`](EXECUTION.md) — discovery, transport, binding, bootstrap and capability truth.
- [`STATE.md`](STATE.md) — session continuity, canonical reload and per-turn integrity.
- [`SURFACE.md`](SURFACE.md) — chat shell, choices, dashboard/workbench and artifact visibility.
- [`FAILURE_RECOVERY.md`](FAILURE_RECOVERY.md) — local remediation, blockers, escalation and recovery.

The boot ROM is [`LOCAL_HOST_PROMPT.md`](LOCAL_HOST_PROMPT.md). It starts discovery and activates this graph; it is not an alternate runtime specification.

## Activation

Use only the nodes named by the current `ADMISSION.json.local_session_environment.activation` entry for the observed trigger. A loaded node is wholly binding for that trigger; do not keep a node active merely because it was loaded in an earlier phase.

Required lifecycle:

- `POST_ACCEPTANCE_BOOTSTRAP` → ROOT + EXECUTION.
- `ACTIVE_SESSION` → ROOT + STATE + SURFACE.
- `FAILURE_OR_RECOVERY` → ROOT + STATE + FAILURE_RECOVERY.
- `REBIND_OR_TRANSPORT_FAILURE` → ROOT + EXECUTION + FAILURE_RECOVERY.

All active files must come from the same pinned revision. A session never silently rebinds to a newer `main`.

## Precedence and non-duplication

Host system/safety/law and the canonical Juriscribe access contract retain their existing precedence. These files govern host orchestration only. Runtime phase, mode, proof, receipt, checkpoint, artifact, delivery and completion facts remain canonical runtime facts.

If this root conflicts with a specialist node, the root governs identity/authority and the specialist governs its declared local concern. If any host node conflicts with `ISENECA_ACCESS_CONTRACT.md`, `ADMISSION.json`, runtime state or a canonical runtime receipt, the canonical contract/runtime wins and the conflict is a repository/runtime defect to surface under `FAILURE_RECOVERY.md`; do not shadow-patch it in the prompt.

## Invariants

1. `UNVERIFIED != UNAVAILABLE != AVAILABLE`.
2. Repository readability is not runtime execution.
3. Materialized canonical source is transport, not reimplementation.
4. Acceptance evidence is not a receipt; prompt text never manufactures runtime state.
5. The host may repair only local, safe, scoped, reversible and non-privileged conditions.
6. Before a blocker, satisfy the Duty of Local Sufficiency in `EXECUTION.md` / `FAILURE_RECOVERY.md`.
7. A dashboard, a file path or prose is not proof of artifact delivery.
8. The environment may degrade truthfully by capability; it may not simulate missing capability.
9. The six runtime authority nodes remain unchanged.
