# Juriscribe 1.0 — scientific continuity runtime

## Product definition

Juriscribe 1.0 is a proof-carrying legal/scientific/editorial runtime whose durable product is the persisted scientific session. Chat is a replaceable control adapter. A session is usable only when the user can always determine **WHERE** they are, what is **DONE**, what happens **NEXT**, **HOW** to advance it, and which actions they can **DO**.

The v0.13 convergence remains the architectural base. v1 adds continuity without adding authority.

## Minimal authority lattice

`MODE_REGISTRY | EXPLICIT_ROUTER | COMMON_STALENESS | SPECIALIST_PROOF | MATERIALIZATION | PROJECTION`

There are exactly six authority partitions. Recovery export belongs to MATERIALIZATION. Resume reuses admission/bootstrap and session persistence. The chat/iteration view belongs to PROJECTION. Neither checkpointing nor recovery is a seventh proof authority.

## Unified user-intent contract

| Intent | Runtime invariant | User surface | Proof |
| --- | --- | --- | --- |
| Know where I am | state-derived phase/mode/stage/checkpoint | `WHERE` | iteration projection tests |
| Know what happened | evidence-derived milestone summary | `DONE` | projection is read-only |
| Know what will happen | deterministic next gate | `NEXT` | phase/mode mapping tests |
| Know how to make it happen | bounded concrete action or autonomous statement | `HOW` | long-copy anti-truncation tests |
| Always retain agency | `RECUPERO`, `STATO`, `ALTRO` cannot be truncated | `DO` | three-line UI contract |
| Resume in another chat | exact runtime input + state + proof/artifact workspace | recovery ZIP | round-trip E2E |
| Resume scientifically, not cosmetically | transport rebind cannot alter `CP-*` | same checkpoint | fresh-host E2E |
| Never reuse old host authority | new receiving host is freshly probed | resume boundary | fresh probe test |
| Do not silently lose source material | every corpus source has an exact runtime-ingested UTF-8 witness | recovery-capable gate | continuity validator |
| Do not overclaim | bundle proves internal integrity/replayability, not legal truth or adversarial authenticity | manifest claim scope | contract/manifest check |
| Preserve v13 convergence | one registry, router, staleness owner, specialist engines | invisible architecture | v13 regression suite + v1 checker |

This table is normative for the v1 implementation: all rows are blocking release criteria.

## Scientific checkpoint

`CP-*` identifies substantive scientific/workflow progress. It intentionally excludes host/path, current probe, chat copy, current phase label, dashboard generation, attachment paths, completion/materialization telemetry and recovery lineage. It includes request, selected mode/contracts, corpus digests, semantic reticulum, setup/DoD, source/claim work, drafts, review, provenance, final review, simulations/compression and continuity material hashes.

Therefore a pure export/import/fresh-probe/path rebind preserves the checkpoint. A substantive material, semantic, proof or human-decision change changes the checkpoint or triggers the existing staleness cone.

## Runtime-input continuity

For every corpus source, Juriscribe stores the exact UTF-8 text representation it actually ingested, bound to source id, runtime role and SHA-256. This is not called an original-file archive: when a host extracted text from PDF/DOCX before ingest, the witness proves replay of what Juriscribe read, not byte identity with the upstream attachment.

The continuity store is INTERNAL. It is not projected into the editorial dashboard/atlas merely because it exists.

## Recovery bundle

The canonical recovery carrier is a bounded standard ZIP:

```text
manifest.json
README.md
snapshot/state.json
snapshot/iteration.json
snapshot/material-index.json
workspace/session.integrity.json       # when available
workspace/ledger/**                    # when available
workspace/artifacts/**                 # when available
```

Export is on-demand and must not mutate scientific state. A session with substantive corpus may reach COMPLETE only if it is recovery-capable; the user is not required to actually export a bundle.

Import validates safe paths, duplicates, symlinks, resource limits, checksums, state/checkpoint bindings, material archive and runtime compatibility. Resume then validates current admission, performs a fresh receiving-host probe, rebinds host/path, persists the session, and regenerates host-bound projection/materialization when necessary. The historical probe inside the snapshot is evidence only and cannot become current authority.

## UI/UX contract

Ordinary post-bootstrap output is exactly three bounded lines:

```text
JURISCRIBE> WHERE phase=<...> | mode=<...> | stage=<...> | <INPUT|WORKING|MATERIALIZATION_PENDING|COMPLETE> | cp=<...>
DONE> <...> | NEXT> <...> | HOW> <...>
DO> [R] RECUPERO [S] STATO [A] ARTEFATTI [?] AIUTO […] ALTRO <phase choices...>
```

`DONE`, `NEXT` and `HOW` have independent character budgets so a long summary can never erase the next-action instruction. Core controls are rendered before optional phase choices so recovery/state/free-input remain visible under all bounded-copy mutations.

## Cross-mode materialization continuation

When substantive/final-review work for an iteration is closed but one or more user-facing artifacts required by the canonical mode registry are not yet materialized with readback PASS, Juriscribe exposes `MATERIALIZATION_PENDING`. It instructs the user to send exactly:

`Continue until the end of artefact materialization`

A conforming chat host maps that phrase to the existing completion/materialization gate (`continue-materialization <session_dir>`). This is a transport-turn continuation, not a new scientific decision, proof engine, mode, or authority node. It applies to every canonical mode.

## Release evidence

The v1-specific release gate is additive to historical/v13 regressions: compile/check current surface; continuity/recovery/UI/E2E tests; v13 convergence tests; deterministic 10,000-instance v1 mutation soak; 44 mutation families × 4 modes = 176 deep signatures; zero deep failures, survivors or soak mismatches; six-node authority partition unchanged; all 21 one-node deletion/pair-merge candidates degrade an invariant; M+1176 no-novelty tail.

The stress receipt is architecture/recovery validation volume, not legal decisions, unique legal documents or LLM sessions.
