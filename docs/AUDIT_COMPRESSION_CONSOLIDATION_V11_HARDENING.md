# Compression & Consolidation v0.11 — semantic hardening audit

## Scope

This audit hardens the v0.11 `COMPRESSION_CONSOLIDATION` overlay without changing the public mode taxonomy or legacy CONTINUATION/GREENFIELD/REVIEW behavior. The governing design rule is simple: **a downstream proof is valid only for the exact semantic revision that produced it**.

The audit covers inventory, joint reticulum, gap/operation planning, mutation receipt validation, dual saturation, user calibration, refined candidates, peer-review readiness, provenance, final review and DOCX artifact materialization. The existing historical regression workflows remain unchanged; a dedicated additive C&C stress workflow is added.

## Native C&C pipeline

1. `canonical_material` and `candidate_material` are inventoried as exact paragraph spans with SHA-256 and object digests.
2. Canonical material is profiled for reference method/style signals; it is not treated as legal or factual authority merely because it is canonical.
3. Semantic units and relations are joined into a canonical/candidate reticulum with 1.0 object coverage.
4. Candidate gaps are converted into a minimal refactoring contract. Non-KEEP operations must be causally bound to evidenced gaps.
5. A mutation receipt must cover at least 10,000,000 instances and all ten required families with zero unresolved failures.
6. Saturation requires both M+1000 no-novelty and N+1000 no-better-lossless-compression tails, semantic and relation recall 1.0, and unchanged canonical material.
7. Material user calibration invalidates plan-bound convergence.
8. Exactly one refined candidate is sealed per candidate source; canonical material is never emitted as a refined candidate.
9. Peer-review readiness, provenance and final severe review precede artifact materialization.
10. Final delivery is atomic and produces real DOCX artifacts; readiness means ready for peer review, not peer reviewed.

## Findings and killed mutations

### Reticulum equivalence collision

Before hardening, reticulum digests were largely count/coverage based. Two semantic states with the same counts and source ids could share the same reticulum digest even if unit text or relation content changed. The reticulum digest now binds the exact inventory-set digest, semantic-unit digest and relation digest. The completion gate reconstructs the expected reticulum from current state and compares digests.

### Object/source role spoofing

A semantic unit could reference a known object while declaring a mismatched source identity. Reticulum construction now requires exact object/source and object/role identity and detects duplicate source/object/unit identifiers.

### Weak inventory self-validation

Inventory validation now checks status, role, object cardinality, unique object ids, monotonic/non-overlapping spans, object source/role identity, exact text, hashes, per-object digests and whole-inventory digest. Malformed numeric fields fail closed rather than raising accidental conversion exceptions.

### Gap-to-operation causal drift

The prior refactoring contract accepted gap identifiers without proving non-empty evidence, unique stable ids, same-unit causality, complete gap disposition or unique operation ids. The contract now normalizes and digests gaps, binds the candidate-unit snapshot, rejects cross-unit gap use, and fails when a material gap has no disposition.

### Stale proof reuse

Re-ingestion, semantic re-mining, plan replacement and material calibration could leave downstream receipts or sealed outputs alive. The runtime now invalidates all logically downstream state at each semantic boundary: mutation, saturation, refined candidates, peer-review readiness, provenance, final review, C&C auto-materialized artifacts and completion eligibility.

At the final gate the runtime reconstructs the reticulum and refactoring contract and re-validates the mode contract, 10M mutation receipt and saturation receipt against current digests. Refined candidates are bound to source digest, inventory digest, plan digest and reticulum digest.

### False PASS in readiness and provenance

Peer-review readiness formerly required dimension names but not PASS values. Every required dimension must now be `PASS` (or boolean true), with no blockers and a current proof chain. Provenance now requires stable unique disposition ids, current readiness binding, complete transformed-operation coverage, complete candidate-source coverage and no unknown operation/source references. Final review binds both readiness and provenance digests to the current plan and reticulum.

### Artifact staleness

Refined-candidate DOCX records now carry source, inventory, refined-text, plan, reticulum and seal digests. The artifact gate compares these bindings with the current sealed candidate, so a stale physical artifact cannot satisfy a new semantic revision.

## Stress and held-out editorial fixture

`scripts/simulate_compression_consolidation_v11.py` is a deterministic, stdlib-only stress harness. It contains a repository-authored four-chapter fixture. Chapters 1–2 are the canonical method sample. The synthesis function generates ten versions for each of held-out chapters 3–4 using only the learned reference profile plus chapter-level concept prompts; the held-out target text is not read during synthesis. After generation, synthetic outputs are compared with the held-out targets using bounded token-overlap and length-ratio signals. These scores are diagnostics, not claims of semantic or literary equivalence.

The same fixture is reticularized losslessly, all candidate paragraphs receive evidenced local operations, and the resulting plan feeds three executable campaigns:

- 10,000,000 mutation-receipt validations across valid and killed equivalence classes;
- 1,000,000 saturation-receipt validations across convergence and stale/malformed classes;
- 1,000,000 dynamic mode-routing validations spanning all four canonical modes plus invalid input.

The 10M campaign is therefore **ten million actual validator invocations**, not a receipt that merely claims ten million transformations. It deliberately does not claim ten million LLM-written chapters or ten million full DOCX E2E sessions. Expensive physical artifact/readback behavior remains covered by the repository's existing dedicated E2E and Safari/universal-delivery suites.

## DoD closure

### Global

- legacy mode taxonomy and historical paths remain additive and untouched;
- C&C cannot complete on stale semantic evidence;
- CI contains a reproducible 10M C&C executable gate;
- final user artifacts remain atomic DOCX outputs and canonical materials remain immutable references.

### Intermediate

- inventory -> reticulum -> mode contract -> plan -> mutation -> saturation -> seal -> readiness -> provenance -> final review is digest-bound end to end;
- every semantic boundary invalidates only downstream proofs;
- malformed receipts fail closed;
- all evidenced gaps have same-unit dispositions.

### Local

- duplicate ids, source spoofing, cross-unit gap binding, missing evidence, malformed numeric thresholds, stale receipts, failing review dimensions and stale seals are regression-tested;
- refined artifact metadata must match the current seal.

### Reticular

- reticulum digest changes when semantic-unit or relation content changes even if counts remain identical;
- object coverage remains 1.0;
- candidate-unit snapshot is bound into the plan;
- final evidence chain is tied to one exact reticulum revision.

## Residual boundary

Juriscribe can mechanically prove that receipts, mappings and declared recall are internally consistent and bound to the current revision. It cannot independently prove that arbitrary natural-language rewrites are semantically equivalent without a supplied semantic mapping/evaluation. `semantic_recall=1.0` and `relation_recall=1.0` remain evidence asserted by the semantic evaluation layer; this hardening prevents that evidence from being stale, malformed or silently rebound, but does not pretend to replace semantic judgment with hashing.
