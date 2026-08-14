# Runtime v0.4 — epistemic reticulum and deterministic chapter-generation gates

## Why v0.4 exists

Repository history progressively added session governance (PR1), deep mining/setup/source controls (PR2), then scientific quality, artifact evidence and blind benchmark hardening (PR3). The remaining architectural gap was that epistemic nodes and relations existed as primitives but were not a mandatory lifecycle gate before chapter generation.

v0.4 makes the reticulum part of the executable contract.

## State transition

```text
ADMITTED
-> INITIALIZED
-> SEMANTIC_MINING_REQUIRED
-> RETICULUM_INVALID | USER_SETUP_REQUIRED
-> DOD_DEFINITION
-> DOD_FROZEN + GENERATION_CONTRACT_READY
-> RESEARCH / DRAFT / SIMULATION
-> QUALITY_AUDIT
-> COMPRESSION
-> VALIDATING
-> COMPLETE
```

## Boundary between runtime and host AI

The stdlib runtime can deterministically segment, anchor, hash, validate and gate structured state. It cannot by itself understand every legal proposition in arbitrary prose. The host AI therefore supplies semantic atoms and typed relations, while the runtime validates their source anchoring, referential integrity, connectivity and lifecycle position.

This division is intentional: semantic judgment remains model/human work; the repository makes that judgment inspectable and prevents the generation phase from silently skipping it.

## Reticulum invariants

- stable unique unit IDs;
- supported epistemic kinds and relation predicates;
- every material unit linked to a known corpus source;
- every material unit has a source locator;
- every relation endpoint exists;
- connected-material coverage >= 0.70;
- deterministic canonical digest;
- explicit count of cross-chapter and contradictory relations.

## Generation contract

The generation contract binds the accepted setup to the current reticulum. It records preserve/develop/avoid-duplication obligations and actual inter-chapter relations. If setup or reticulum changes, the contract becomes stale and completion fails.

## Scientific source controls

Strict validation adds claim-level source evidence. A material claim using an external source requires direct read, verification timestamp, scoped proposition and pinpoint. Artifact evidence must expose all supporting source IDs. Strong-inference graphs are cycle-checked.

## Simulation and compression gates

A generation completion requires simulation coverage for ten mandatory risk families and a compression audit showing no required semantic unit was lost and no new material proposition was introduced without re-audit.

## Admission enforcement limit

`AGENTS.md` is now a pre-admission sentinel, and runtime commands require a receipt tied to the current contract hash. This is enforceable inside the Juriscribe protocol/runtime. It cannot revoke raw GitHub access from a client that already has repository credentials; this limitation is explicit in the contract and README.
