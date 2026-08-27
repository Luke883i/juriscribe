# Common Mode Runtime v13 — engine audit and DoD

## Scope

This change extends PR #27 from a projection-only UI improvement into a bounded runtime hardening of the four canonical Juriscribe modes. It does not create a fifth mode, replace existing specialist engines, alter admission, weaken historical proof gates, or change serialized mode-contract semantics.

The common runtime kernel enforces only invariants that are genuinely shared. Mode-specific epistemic work remains delegated to the historical engines.

## Reticular model

Every mode is represented as:

`common spine + mode-specific delta`

Common spine:

1. input binding;
2. semantic reticulum;
3. user configuration;
4. DoD contract;
5. provenance;
6. final severe review;
7. materialization.

Mode deltas:

- **CONTINUATION** — multiple preceding chapters; continuation frontier/coverage; generation; causal review/regeneration; simulation and compression.
- **GREENFIELD** — one replaceable concept/mandate source; generation; review/regeneration; simulation and compression.
- **REVIEW** — one replaceable review target; diagnostic review and optional revision/re-review according to accepted output policy.
- **COMPRESSION & CONSOLIDATION** — one-or-more immutable canonical references plus one-or-more candidate materials; lossless inventory; joint reticulum; causal refactoring plan; mutation evidence; dual saturation; refined candidates; peer-review readiness; proof-carrying C&C semantics remain delegated to the existing v0.12/C&C v2 stack.

## Three runtime methods introduced

### 1. Role/Cardinality Firewall

The mode controls which material roles may enter its corpus. Source identity is stable: a `source_id` cannot silently switch roles. GREENFIELD and REVIEW have singleton target semantics but permit replacement by re-ingesting the same `source_id`. CONTINUATION remains multi-input. C&C requires both canonical and candidate classes before semantic mining can start.

This closes a historical asymmetry: C&C already rejected illegal material roles, while legacy modes accepted a caller-supplied `role` more permissively.

### 2. Evidence Staleness Cone

A material change invalidates every proof derived below the material boundary: semantic units/relations/reticulum, setup, editorial standard, generation/mode contracts, continuation evidence, DoDs, drafts, review/regeneration/saturation, provenance, final review, quality, benchmark, simulations, compression, claim/artifact evidence, contradictions, editorial actions, convergence counters and completion.

A semantic-model change preserves the current semantic representation until the specialist engine replaces it, but invalidates setup and every downstream proof.

The cone deliberately preserves authority that did not change: admission, selected mode, request, corpus/source records, explicit bibliography, host/runtime state and C&C source inventories. Specialist engines may clear additional proof stores.

### 3. Reticular Mode Quotient

The runtime exposes one common lifecycle vocabulary without pretending that the four engines are semantically identical. This is the same abstraction principle used by the chat shell: quotient only what is behaviorally equivalent; preserve distinctions where proof obligations differ.

## Audit methods

Five established methods and three repository-specific methods were combined:

1. **state-transition audit** — verify legal predecessor/successor states and fail closed on invalid transitions;
2. **dependency-DAG invalidation** — propagate staleness from a changed root to every derived witness;
3. **equivalence partition + boundary-value analysis** — singleton/multi-input, missing/duplicate IDs, valid/invalid roles, complete/incomplete C&C input sets;
4. **metamorphic testing** — same-source replacement must remain valid while source-role mutation must fail;
5. **mutation/soak testing** — execute validators repeatedly across balanced control and adversarial families;
6. **Evidence Staleness Cone** — repository-specific causal reset model derived from the stronger C&C invalidation design;
7. **Role/Cardinality Firewall** — repository-specific mode boundary that prevents caller-driven semantic role drift;
8. **Cross-mode isomorphism audit** — compare the four engines at each lifecycle layer and unify only invariant-preserving structure.

## 10M executable stress gate

`scripts/simulate_mode_runtime_v13.py` executes exactly one real kernel validator/profile transition per case. The default release campaign is **10,000,000 actual invocations** across 16 balanced families.

Families include valid profiles/default roles, CONTINUATION multi-input, same-source GREENFIELD/REVIEW replacement, complete C&C minimum input, illegal role, GREENFIELD/REVIEW singleton overflow, source-role drift, duplicate source identity, missing source identity, and missing canonical/candidate C&C classes.

Local pre-commit campaign:

- actual validator invocations: 10,000,000;
- accepted controls: 5,000,000;
- killed edge/mutant cases: 5,000,000;
- failures/mismatches: 0;
- family size: 625,000 each;
- scenario digest: `9d94931649f047bbc76576dd9737d959aa5bb8062992a4808c9db7ed4c55a04f`.

Claim scope is explicitly `EXECUTED_MODE_RUNTIME_VALIDATOR_INVOCATIONS_NOT_UNIQUE_LEGAL_OR_LLM_CASES`. The count is real execution volume, not ten million legal judgments, unique semantic texts, or LLM sessions.

## Definition of Done

### Global

- the four canonical modes and their labels remain unchanged;
- current C&C structural/editorial proof gates remain authoritative and are not reimplemented;
- historical mode-contract/fixed-point receipts are not rewritten to accommodate the new layer;
- material or semantic changes cannot retain downstream evidence as if it were current;
- the public chat shell continues to derive from persisted integrity-checked state and keeps the v0.9.2 redacted fallback.

### Intermediate

- all mode input roles are mechanically bounded;
- source role cannot drift under a stable identity;
- GREENFIELD/REVIEW cannot silently accumulate competing primary targets;
- C&C cannot begin semantic mining without both canonical reference and candidate material;
- common invalidation resets contradictions, editorial actions and convergence witnesses as well as final artifacts/proofs;
- specialist pipelines remain reachable through the existing orchestrator facade.

### Local

- focused mode-runtime tests pass;
- 10M executable campaign passes with zero mismatch;
- Python 3.10/3.12 historical runtime suite remains green;
- contract/dashboard/delivery/evaluation and all historical saturation/fixed-point gates remain green;
- no threshold in an existing workflow is reduced.

## Residual boundary

This hardening intentionally does not flatten the historical module overlay stack. A future compatibility refactor may collapse old implementation layers only after proving byte/state/receipt equivalence. v13 instead introduces a minimal anti-corruption kernel above the current specialist engines, giving the product one invariant runtime spine without relocating substantive legal or editorial authority.
