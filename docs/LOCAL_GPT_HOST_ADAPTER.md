# Juriscribe — Local GPT-like Host Adapter compatibility pointer

This path is retained for compatibility and discovery. It is not an independent specification.

Current boot/cognitive policy:
- [`host/LOCAL_HOST_PROMPT.md`](host/LOCAL_HOST_PROMPT.md) — standalone <=8k `LOCAL_CHAT` boot ROM; repository pin → `I ACCEPT` → explicit `LEAN | ATTESTED` → canonical mode selection/work.

Current host contracts:
- [`host/LOCAL_SESSION_ENVIRONMENT.md`](host/LOCAL_SESSION_ENVIRONMENT.md) — normative root;
- [`host/EXECUTION.md`](host/EXECUTION.md), [`host/STATE.md`](host/STATE.md), [`host/SURFACE.md`](host/SURFACE.md), [`host/FAILURE_RECOVERY.md`](host/FAILURE_RECOVERY.md) — lifecycle-scoped normative nodes.

Historical compatibility:
- [`host/RUNTIME_LOCAL_HOST.md`](host/RUNTIME_LOCAL_HOST.md) — retained pointer only; not loaded by current `LOCAL_CHAT` bootstrap.

Canonical graded-method source:
- [`../METHOD_KERNEL.json`](../METHOD_KERNEL.json) — method discipline and mode-method projection used for `METHOD_ACCESS`; it is not runtime state or proof.

The host never manufactures admission, mode selection, receipts, proof, checkpoint, materialization, delivery or `COMPLETE`. LEAN and ATTESTED preserve identical method/epistemic duties and artifact targets; they differ only in runtime attestation. LEAN → ATTESTED requires canonical replay/revalidation.
