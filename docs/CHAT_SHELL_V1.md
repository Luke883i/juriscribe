# Juriscribe Chat Shell v1 — audit, design and Definition of Done

## Scope

Chat Shell v1 is a **projection-only** control surface for an already authoritative Juriscribe runtime. It does not define admission, modes, reticula, proofs, completion, artifacts, receipts, or legal/scientific truth. Its job is narrower: compress the current persisted session into a stable three-line UI that a chat host can render without reimplementing Juriscribe.

Canonical grammar:

```text
JURISCRIBE> <PHASE> | MODE=<MODE|-> | <INPUT|WORKING|COMPLETE>
NEXT> <one concrete user-facing next step>
[1] <choice> ... [S] STATO  [A] ARTEFATTI  [?] AIUTO  […] ALTRO
```

`ALTRO` remains permanently available. Autonomous phases do not manufacture choices merely because a previous interaction card remains in state.

## Development trajectory: PR1–PR26

The 26 merged PRs form five coupled epochs rather than 26 independent features.

1. **Kernel and epistemic proof — PR1–PR8.** Session governance, mining, evidence, mandatory epistemic reticulum, review/regeneration fixed points, continuation coverage, provenance/finalization, and canonical session integrity progressively convert a writing assistant into an auditable state machine.
2. **Modes, delivery and runtime hardening — PR9–PR13.** Tri-mode generalization exposes a recurring product tension: semantic generality can regress delivery/UI invariants. PR10–PR12 restore and then constitutionally preserve artifact-first DOCX/dashboard behavior; PR13 hardens bootstrap identity, persistence, capabilities and fast-path execution.
3. **Human workbench and materialization — PR14–PR20.** Canonical dossiers, the legal-editorial workbench, lossless evidence traceability, generation governance, persistent dashboard, 100 real-text materialization sessions, and runtime-owned universal DOCX delivery make the human-facing artifacts increasingly complete while keeping technical records internal.
4. **Independent evaluation boundary — PR21.** Evaluation is deliberately placed outside the runtime so implementation cannot self-certify substantive correctness.
5. **Fourth mode and proof-carrying C&C — PR22–PR26.** `COMPRESSION & CONSOLIDATION`, host source transport, revision-bound semantic evidence, proof-carrying semantics, fast bootstrap, and executable editorial-reticulum stress increase runtime depth without adding another user mode after PR22.

### Recurring patterns

- **Conservative accretion:** new guarantees are normally layered on top of historical gates rather than replacing them.
- **Fail-closed evidence binding:** important transitions become digest/revision/candidate bound and stale evidence is rejected.
- **Executable claim scoping:** large simulation counts are explicitly scoped as validator/property/soak evidence, not as legal truth or LLM-session counts.
- **Artifact-first convergence:** complexity migrates away from ordinary chat and into verified DOCX/dashboard artifacts.
- **Human interruption minimization:** the intended host behavior increasingly becomes autonomous-until-blocking/non-inferable.

### Recurring anti-patterns

- **Overlay accretion:** correctness can depend on the newest facade intercepting an older implementation. Example: the legacy multimode entry map is tri-mode while later C&C overlays make the public path four-mode safe.
- **Projection drift:** old user-facing strings/cards can survive after mode taxonomy changes even when runtime routing is correct.
- **Duplicated entry copy:** mode-entry guidance has historically been assembled in more than one runtime layer.
- **Internal-phase leakage:** a rich state machine can expose too many implementation phases to a human unless a projection explicitly distinguishes `INPUT` from autonomous `WORKING`.
- **Regression-by-generalization:** several historical releases required follow-up hardening because a broader semantic surface weakened a previously implicit UX/delivery invariant.

Chat Shell v1 is intentionally an anti-corruption layer for these anti-patterns, not a rewrite of the historical runtime stack.

## Five holistic multi-abstraction audit methods

### M1 — Genealogical / temporal audit

Treat each PR as a state transition in product philosophy, not only a diff. For every epoch identify: invariant introduced, authority moved, user burden added/removed, proof claim added, and later PRs that repaired a regression. This distinguishes durable trajectory from temporary implementation shape.

### M2 — Authority-stack audit

Trace one request from host/hardware capability to admission, bootstrap, persisted state, mode contract, epistemic/runtime gates, artifact materialization, and finally chat rendering. At every layer ask: **what may this layer know, mutate, prove, and display?** A UI layer fails this audit if it can create a mode, completion status, semantic proof, receipt, or capability.

### M3 — State-machine / human-interruption audit

Model all runtime phases, then quotient them by the user's actual responsibility:

- `INPUT`: a real user decision/material is required;
- `WORKING`: runtime work is autonomous and old cards must not interrupt;
- `COMPLETE`: runtime completion is already proven.

This quotient is the minimum UI lattice. The full runtime state machine remains intact underneath it.

### M4 — Metamorphic / mutation / soak audit

Exercise invariants rather than ideal transcripts. The v1 harness uses 1,000 generated human-like journeys and 1,000,000 projection edge cases. Mutation-style probes target shadow authority, state mutation, stale-card reuse, mode drift, ANSI/control leakage, layout overflow, free-input removal, and false interruption of autonomous phases. Counts are **generated projection soak**, not unique legal decisions or LLM conversations.

### M5 — Reticular onto-epistemic convergence audit

Build a graph whose nodes are request, state, mode, interaction card, proof/gate, artifact and UI projection; edges are `authorizes`, `binds`, `derives`, `materializes`, or `projects`. Remove any UI node/edge that duplicates authority already present below. Convergence is reached when the remaining UI can answer only four human questions: **where am I, what happens next, what can I choose, where are the artifacts/help?**

## End-to-end interaction by mode

All four modes share the same outer method:

`accept -> probe -> initialize -> choose mode -> supply mode input -> mine/reticulum -> setup -> mode-specific work -> evidence/review/saturation -> final review -> materialize -> complete`

The shell does not expose every internal arrow. It projects only the current responsibility.

| Mode | Human entry | Mode-specific core | Standard shell behavior |
| --- | --- | --- | --- |
| CONTINUATION | preceding chapters | continuation frontier/coverage + generation/review | request chapters once, then `WORKING` until a real decision/blocker |
| GREENFIELD | concept/mandate | greenfield generation/research/review | request concept once, then same outer shell |
| REVIEW | text to review | report-only or report+revised lifecycle | request target once; later human decision only if runtime requires one |
| COMPRESSION & CONSOLIDATION | canonical + candidate materials | immutable canonical method, lossless inventory, refactoring plan, stress/proofs | expose canonical/candidate upload choices; proof complexity remains hidden below `WORKING` |

The common user method is therefore stable even when the internal proof graph differs substantially.

## Why the DOS/ISPF-like projection

The design borrows interaction primitives, not authority or semantics:

- **DOS-like prompt:** one persistent recognizable prompt establishes location and command context.
- **IBM ISPF-like option panel:** numbered current choices are separate from the status/next-step line.
- **Norton Commander-like utility strip:** fixed utilities stay in the same visual position instead of being rediscovered per mode.
- **SQLite-shell-like meta layer:** shell controls are distinct from the underlying domain engine; the shell is not another implementation of Juriscribe.

The result deliberately avoids menus within menus, verbose process narration, and mode-specific chrome.

## Safety and projection invariants

1. `authority == PROJECTION_ONLY`.
2. Rendering never mutates session state.
3. Completion is read from canonical completion state, never inferred from prose.
4. Mode names are normalized through the canonical mode module.
5. Dynamic human-decision copy is used only when its card is phase-bound and preserves `ALTRO`.
6. Stale mode/setup cards cannot turn autonomous phases into user interruptions.
7. ANSI/control characters are removed and lines are bounded.
8. Ordinary output is exactly three lines; technical JSON remains behind the historical dual opt-in.
9. Unknown phases/modes fail readable but acquire no validity or authority.
10. No chain-of-thought, raw receipt, ledger, provenance, path or proof telemetry is added to the shell.

## Definition of Done

### Global

- [ ] All four canonical modes remain semantically unchanged.
- [ ] No admission, proof, completion, artifact or capability authority moves into the shell.
- [ ] Every ordinary post-bootstrap CLI mutation can render from persisted integrity-checked state.
- [ ] Ordinary shell output is bounded to three lines with a permanent free-input path.
- [ ] Historical artifact-first, DOCX/dashboard, autonomy and technical-output invariants remain green.
- [ ] Full repository CI remains green on Python 3.10/3.12 and existing saturation workflows.

### Intermediate

- [ ] One shared mode-entry projection covers all four modes.
- [ ] `INPUT / WORKING / COMPLETE` is derived only from phase + canonical completion eligibility.
- [ ] Phase-stale interaction cards are suppressed.
- [ ] Persisted state is reloaded after mutations before public projection.
- [ ] Control-sequence and layout adversaries cannot escape the renderer.

### Local / measurable

- [x] 6 focused unit tests pass in the prototype environment.
- [x] 1,000 generated journeys pass.
- [x] 6,000 journey checkpoints pass.
- [x] 1,000,000 generated projection edge cases pass.
- [x] 8/8 semantic/projection mutants killed; 0 survivors.
- [x] 0 state mutations observed from rendering.
- [x] Maximum 3 lines, 220 characters per line.
- [ ] GitHub Actions must reproduce targeted tests + one-million-case receipt on the PR head.

## Residual boundaries

Chat Shell v1 does not solve every historical layering issue. In particular, older runtime overlays may still contain duplicated mode-entry code that is unreachable or intercepted on the current public path. Removing those layers is a separate compatibility refactor and would expand the semantic blast radius without improving the v1 user contract. The v1 convergence criterion is therefore **one canonical external projection over current authoritative state**, followed by later internal simplification only when equivalence is mechanically demonstrated.
