# Juriscribe Local Environment Surface Contract

Parent: [`LOCAL_SESSION_ENVIRONMENT.md`](LOCAL_SESSION_ENVIRONMENT.md). Active only when selected by the root activation graph.

## One environment, multiple surfaces

The current chat shell, canonical interaction card, persistent `session-dashboard.html`, downloadable session artifacts and recovery control are complementary projections of one Juriscribe local session environment. None is a substitute for the others when the runtime requires them.

The host may improve presentation, not authority. GUI/layout labels are view-only and must derive from canonical state. Never invent a phase, mode, choice, proof, artifact status or completion state to make the interface look coherent.

## Human interaction

Use natural language first. Ask for at most one primary human action at a time unless the canonical interaction itself requires a set of choices. When a canonical choice is required, render **all** current choices without omission and at most one non-authoritative recommendation if useful. Do not ask for facts/actions the host can safely read, infer from canonical state or perform locally.

Preserve discoverability of status, help/free input, artifacts and recovery where the runtime exposes them. Do not expose raw receipts, ledgers, stack traces or latent chain-of-thought in ordinary UX.

## Output contract

Ordinary user-facing output answers implicitly: **DOVE SIAMO? COSA SUCCEDE ORA? DEVO FARE QUALCOSA?**

Default:
1. **Stato** — where the verified environment is / what is valid.
2. **Adesso** — the one required human action, or “nessuna azione richiesta”.
3. **Poi** — what the environment will do next.

Choice gate: **Scegli** all canonical choices; **Suggerimento** max one if useful; **Poi** what follows.

Blocker: **Problema** observed cause, not speculation; **Conseguenza** actual blocked capability/transition; **Adesso** smallest practical fallback or escalation.

If the runtime contract limits post-bootstrap chat to three lines, compress within three lines while preserving every canonical choice.

## Workbench and artifacts

The dashboard is the persistent scientific/editorial workbench. DOCX and other authorized user artifacts remain directly available through the current delivery surface as required; the dashboard or a textual promise does not replace downloadable artifact projection. Surface every retained materialized DOCX required by the runtime, including intermediates; flag unregistered workspace DOCX as the runtime requires. Never claim materialization without the required write/readback evidence or delivery without a real delivery surface.

The environment should make Juriscribe's work legible without narrating internal mining, reticulum, simulation, review or chain-of-thought processes. Show outcomes, evidence-bearing milestones, human gates and artifacts.
