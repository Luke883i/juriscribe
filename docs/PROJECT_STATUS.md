# Juriscribe project status and assurance boundary

## Status

Juriscribe is **experimental open-source research software** for repository-governed, auditable legal/scientific/editorial workflows. The runtime is designed to make its process inspectable and to fail closed on defined internal invariants. It is not designed to make AI output self-validating.

The project originated as a repository-governed conversational/runtime experiment and evolved through admission control, persistent session state, explicit multimode routing, evidence/provenance boundaries, artifact-first materialization, proof-carrying structural semantics, and portable scientific continuity. Version 1.0 deliberately keeps six runtime authority partitions:

`MODE_REGISTRY | EXPLICIT_ROUTER | COMMON_STALENESS | SPECIALIST_PROOF | MATERIALIZATION | PROJECTION`

Project-status metadata does **not** add a seventh authority partition. It constrains how the repository describes itself and how a compliant host presents and interprets runtime claims.

## Minimal project-status reticulum

The repository-wide status contract consists of seven irreducible statements:

1. `OPEN_SOURCE_IDENTITY` — repository work is licensed under Apache-2.0.
2. `EXPERIMENTAL_STATUS` — the software is experimental and under active development.
3. `AI_FALLIBILITY` — AI-assisted outputs may contain substantive errors, hallucinations, omissions, stale material, or citation/inference defects.
4. `HUMAN_VALIDATION` — material outputs require competent human validation before consequential reliance.
5. `HUMAN_FINAL_RESPONSIBILITY` — adoption and use of the final artifact remain human decisions and responsibilities.
6. `NO_PROFESSIONAL_SUBSTITUTION` — runtime output is not itself professional advice, legal authority, peer review, or certification.
7. `NO_AUTHORITY_ESCALATION` — internal `PASS`, proof, receipt, stress, saturation, checksum, or readiness labels prove only their expressly scoped runtime property.

These statements are intentionally declarative. They do not alter the scientific checkpoint, the specialist proof engines, mode semantics, or the six-node runtime authority lattice.

## Cross-surface binding

The same status is projected into:

- `PROJECT_STATUS.json` as the canonical machine-readable status profile;
- `README.md` for human discovery;
- `LICENSE` for the open-source grant and warranty/liability terms;
- `RESPONSIBLE_USE.md` for the validation and reliance boundary;
- `AGENTS.md` and `ISENECA_ACCESS_CONTRACT.md` for AI/host admission;
- `ADMISSION.json` for machine-readable pre-admission binding;
- `pyproject.toml` for package/license metadata;
- `RUNTIME_V1_CONTRACT.json` for continuity of the v1 claim boundary;
- `MANIFEST.json` for the current access-contract version binding.

CI rejects contradictions across these surfaces. The canonical open-source license and the responsible-use statement remain separate: operational human-validation requirements are not encoded as field-of-use restrictions in the software license.

## Assurance boundary

Juriscribe can mechanically test properties such as current-state binding, structural preservation, evidence freshness, artifact readback, provenance completeness, deterministic routing, or recovery consistency when the relevant gate says so. It cannot, by those mechanisms alone, prove arbitrary legal correctness, factual truth, semantic entailment, professional fitness, or that an external source is current and authoritative.

Ten-million-case campaigns in this repository are executable validator/stress volume over declared mutation families. They are not ten million unique legal matters, documents, model conversations, or independent professional judgments.

## User responsibility boundary

Before relying on a Juriscribe artifact, a human reviewer should at minimum verify the actual source materials, citations and pinpoints, material factual premises, jurisdiction and date, consequential legal/scientific inferences, omissions and counter-authority, and the final text that will be signed, filed, submitted, published, or otherwise relied on.

See `RESPONSIBLE_USE.md` for the concise responsible-use statement and `ISENECA_ACCESS_CONTRACT.md` for the runtime admission/operating contract.
