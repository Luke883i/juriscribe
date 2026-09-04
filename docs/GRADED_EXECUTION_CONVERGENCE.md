# Juriscribe graded execution convergence — PR33 historical evidence

Status: **historical convergence record for merged PR #33; not the current semantic specification**.

PR #33 introduced the first `LEAN | ATTESTED` graded-execution model and the Local Cognitive Host. Its synthetic/property receipts remain useful evidence for that merge candidate, but post-merge audit found several semantic gaps that are hardened by the current post-PR33 surface.

Current sources of truth for graded execution are:

- `ISENECA_ACCESS_CONTRACT.md` — Method Access / Runtime Authority constitutional boundary;
- `ADMISSION.json.method_access` — machine-readable Method Access binding;
- `METHOD_KERNEL.json` — canonical non-degrading method obligations and mode/stage parity;
- `juriscribe/graded_execution.py` — executable graded-execution policy;
- `docs/host/LOCAL_SESSION_ENVIRONMENT.md` plus lifecycle nodes — normative host composition;
- `docs/host/RUNTIME_LOCAL_HOST.md` — post-acceptance cognitive companion;
- `docs/GRADED_EXECUTION_POST33_HARDENING.md` — PR1→33 audit, defects, DoD and current mutation evidence.

The following PR33 conclusions are **superseded**:

- execution-profile choice is no longer a mandatory new human round trip; default is `ATTESTED_PREFERRED`, with explicit `ATTESTED_REQUIRED` and `LEAN` supported;
- `LEAN` is not a runtime bootstrap path class;
- a reachable runtime never by itself proves receipts or `COMPLETE`;
- explicit LEAN remains method-guided even when runtime capability exists and later promotion requires replay;
- the five lifecycle host concerns remain normative and activation-scoped; `RUNTIME_LOCAL_HOST.md` is one additional non-authoritative cognitive companion, not their replacement.

The original PR33 evidence receipt under `docs/evidence/graded-execution-stress-20260903.json` is retained as historical candidate evidence with its original claim scope. It must not be used as proof of the post-PR33 hardened semantics.
