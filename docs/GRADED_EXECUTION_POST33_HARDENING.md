# Juriscribe post-PR33 semantic hardening — audit PR1→33

Base audited: `main@9f0391f2ec7e77dba55130040d7f8b7fbd2862ec` (merged PR #33).

## Trajectory

The 33-PR history converges through six phases:

1. **PR1–4 — constitutional/epistemic foundation:** admission, session kernel, mining, typed reticulum, evidence and fail-closed completion.
2. **PR5–8 — scientific fixed points and continuity:** review/regeneration saturation, continuation coverage, provenance/final review, canonical session integrity.
3. **PR9–13 — multimode + delivery hardening:** explicit modes, DOCX/dashboard boundary, lossless contract preservation, identity/persistence/capability seals and safe fast bootstrap.
4. **PR14–20 — humanistic evidence/artifact runtime:** semantic dossiers, workbench, traceability, generation governance, persistent dashboard and runtime-owned atomic delivery.
5. **PR21–28 — independence and explicit authority:** external evaluation boundary, C&C, host transport bridge, proof-carrying semantics, projection-only shell and six-node authority lattice.
6. **PR29–33 — portable product/host:** scientific checkpoint/recovery, responsible-use governance, capability-derived physical host, revision-bound Local Session Environment and graded execution.

The stable design law across the trajectory is: **new usability must not create shadow authority; compression must preserve historical scientific detail; mechanical evidence never becomes substantive truth.**

## PR33 audit findings

### P0 — constitutional binding gap
PR33 introduces graded execution in `RUNTIME_V1_CONTRACT.json` and host policy but leaves access contract 2.2 and `ADMISSION.json` unchanged. `METHOD_ACCESS` therefore lacks the same constitutional/hash binding used historically for material access-policy changes.

### P0 — explicit LEAN retrocertification
Merged `graded_execution_plan()` checks `runtime_ready` before requested profile. Explicit LEAN therefore becomes `RUN_ATTESTED` whenever runtime is reachable; receipt/attestation and replay flags follow that promotion.

### P0 — `COMPLETE` eligibility too broad
The merged planner exposes `runtime_complete_may_be_claimed = runtime_ready`, but `COMPLETE` historically requires the complete section-19 gate, not runtime reachability.

### P1 — Method Kernel not independently bound
The merged kernel is a generic tuple inside host code. A LEAN claim of “full canonical method” needs a same-revision declarative Method Kernel with canonical mode parity and epistemic invariants.

### P1 — profile/search conflation
`LEAN_METHOD_KERNEL` is included as a bootstrap search class although LEAN is an execution profile/method trajectory, not runtime transport. This creates duplicate fallback semantics and weakens the explicit profile boundary.

### P1 — host-policy compression regression
PR32 proved five lifecycle activation signatures; PR33 collapses policy into one normative root and converts specialist nodes into aliases. This removes activation isolation without an equivalent historical-detail preservation proof. The post-33 shape restores five normative lifecycle nodes and keeps one non-authoritative cognitive companion.

### P1 — pre-acceptance cognitive authority ambiguity
The PR33 prompt loads the cognitive capsule at cold start even though host docs remain outside the pre-admission allowlist. The hardened design keeps the boot ROM minimal and activates/binds the cognitive companion only after valid acceptance.

### P1 — evidence harness self-reference
PR33 `stress_graded_execution.py` reimplements a simplified oracle instead of exercising the candidate runtime functions. The new stress gate imports and executes `juriscribe.graded_execution` directly.

### P2 — public-surface drift
README/MANIFEST remain broadly compatible but do not fully describe the post-33 method-access split. This PR keeps the semantic patch minimal and updates the Local GPT compatibility pointer; full README/MANIFEST editorial consolidation remains non-blocking documentation debt because neither file currently grants contradictory runtime authority.

### Contract-version strategy
This hardening deliberately retains `contract_version=2.2.0` and changes the canonical contract digest. The existing admission protocol already binds acceptance to that digest, so prior receipts become stale without a cross-repository release-version migration. `contract_semantic_revision=POST_PR33_GRADED_METHOD_ACCESS_HARDENING_V1` makes the hash-bound revision explicit.

## Converged architecture

`I ACCEPT + pinned revision + contract digest + verified METHOD_KERNEL.json → METHOD_ACCESS`.

`METHOD_ACCESS` authorizes canonical method discipline only. `RUNTIME_AUTHORITY` remains a separate real-runtime gate.

Execution preference defaults to `ATTESTED_PREFERRED`; no new mandatory round trip is added. Explicit `ATTESTED_REQUIRED` and explicit `LEAN` remain supported. LEAN is honored even if runtime capability exists and always requires replay for later ATTESTED claims.

The Local Host shape is:

`LOCAL_HOST_PROMPT.md → five lifecycle normative host nodes + post-acceptance RUNTIME_LOCAL_HOST.md companion → METHOD_KERNEL.json / canonical runtime`.

## Executed evidence

- PR33 behavior replay: 100,000 randomized cases, seed `7231180890413976942`; 145,494 mismatch-events across four concrete defect classes (30,821 explicit-LEAN overrides; 30,821 LEAN receipt retro-certification events; 29,584 lost replay requirements; 54,268 premature COMPLETE-eligibility events).
- Candidate mutation campaign: 100,000 mutations, seed `121015742168035242`; 100,000 killed; 0 survivors; digest `271ee087a885433677a18043d921059b477fed4d942aecc3d61253112ab10796`.
- Holistic PR1→33 campaign: 1,000,000 mutations across ten random 63-bit seeds; 1,000,000 killed; 0 survivors; aggregate digest `b4c4a5704cd127dd87286d4e58a992bd8dd8c1e3d228bed246d50fbc83155528`.
- Candidate direct runtime-policy stress: 100,000 traces importing the actual candidate module; 0 oracle mismatches; digest `28b8b603698a8ae6c5c2776849f8a19c91a056834bf769406e91acf79ef7f31b`.
- Focused direct tests: 31/31 PASS locally (14 graded-execution + 7 lifecycle-host + 10 post-PR33 integration).

Evidence is synthetic/property validation of architecture and runtime policy. It is not a count of physical hosts, legal matters, documents or LLM conversations and does not prove legal/factual truth.

## Definition of Done

### Global
- access contract/admission/runtime contract bind Method Access and Method Kernel coherently;
- four scientific modes and six runtime authority nodes unchanged;
- no method or epistemic degradation in LEAN;
- `COMPLETE` remains the historical canonical gate;
- five lifecycle-scoped host normative concerns remain isolated;
- cognitive companion adds zero runtime/scientific authority;
- human validation remains mandatory.

### Intermediate
- explicit LEAN is never auto-promoted by runtime availability;
- runtime reachability alone never authorizes receipts or `COMPLETE`;
- LEAN is not a runtime path class;
- Method Kernel key parity covers all canonical modes;
- `METHOD_MODE_INTENT != MODE_SELECTED`;
- pre-acceptance cognitive companion is inert;
- LEAN→ATTESTED always replay/revalidation based.

### Local
- boot prompt <= 8,000 characters and contains no copied scientific mode taxonomy;
- cognitive companion is same-revision/hash-bound after acceptance;
- infrastructure notes carry evidence id, exact effect and calm/non-alarmist wording;
- `UNVERIFIED != UNAVAILABLE`, scratch != delivery, dashboard != delivery;
- CI imports candidate runtime policy rather than a parallel behavioral model.
