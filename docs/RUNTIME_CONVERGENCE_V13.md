# Juriscribe runtime convergence v0.13 — explicit authority, saturation and DoD

## Product move

v0.13 is a compatibility refactor after PR #27. It does **not** add a mode, proof claim, completion rule, artifact class, admission power, or new legal/scientific authority. It removes accidental authority created by module layering and makes the current runtime topology explicit.

The target lattice is:

`host capability -> admission/bootstrap -> persisted session -> canonical mode registry -> common runtime invariants -> specialist proof engine -> completion/delivery -> projection`

Each edge has one owner. The chat shell remains `PROJECTION_ONLY`; specialist proof engines remain authoritative for mode-specific semantics.

## Priority findings closed

1. **Current-surface drift.** Runtime version becomes `0.13.0`; `MANIFEST.json` names `modes.py`, `mode_runtime.py`, `runtime_v13.py`, `runtime_router.py` and `chat_shell.py` as current runtime surface.
2. **Import-order authority.** `runtime_router.ROUTES` declares the owner of every public orchestrator operation. `orchestrator.py` no longer relies on repeated same-name imports where the last import silently wins.
3. **Bootstrap/mode projection drift.** The canonical four-mode registry owns both mode runtime policy and mode-entry projection. The C&C compatibility pipeline normalizes the legacy fast-bootstrap transport response without monkey-patching `pipeline_v9`.
4. **Split CLI routing.** C&C specialist CLI operations resolve through the same explicit router as public orchestration.
5. **Shared staleness ownership.** `mode_runtime.invalidate_downstream` remains the single owner of common evidence invalidation. Specialist engines may only add specialist proof invalidation.
6. **Stress scope.** The release gate separates exhaustive deep signature checks from high-volume mutation soak rather than representing one as the other.
7. **Current contract validation.** `check_runtime_convergence_v13.py` validates current topology while historical v0.12 semantic guards become future-additive instead of pinning the whole product to `0.12.0`.

## Canonical mode registry

`juriscribe.modes.MODE_REGISTRY` is the sole current source for canonical mode order, common engine-family label, legal input roles/cardinality, mode-specific stage delta, and user-entry summary/choices. Substantive mode contracts and proof semantics are unchanged.

## Explicit router

`juriscribe.runtime_router.ROUTES` maps a public operation to one current implementation owner. It is deliberately lazy and declarative. The router does not become a proof engine; it only removes import-order ambiguity. C&C remains the strongest specialist engine and still owns inventory, proof-carrying semantic preservation, editorial execution reticulum, mutation evidence, dual saturation, refined candidates and consolidation gate.

## Multi-abstraction mutation campaign

The final pre-PR campaign used a random 63-bit seed and eight abstraction layers: host capability model, admission/bootstrap, session persistence model, mode registry, common runtime, specialist routing, evidence/delivery model, and UI/UX projection.

Sixteen mutation families cover capability promotion, bootstrap mode drift, persistence regression, wrong input role, singleton overflow, source-role drift, duplicate source identity, incomplete C&C role classes, registry-entry drift, router-owner drift, unknown route, material/semantic staleness escape, stale-card interruption, control/layout escape and projection authority escalation.

Final pre-PR receipt:

- random seed: `7227976535808407722`;
- actual validator invocations: **10,000,000**;
- deep cross-product signature checks: **64/64 PASS**;
- mismatches: **0**;
- scenario digest: `db9e543bd033d3588ce01d896d492cc50aa6b4c9b292195648f603339c0a7446`.

The dedicated CI reruns another deterministic 10M campaign with seed `1363003010493296010` and expected scenario digest `de894953f9b24fe4d72671eb72bd22a1b04372fa4bf2dab3bd1f4e32bd1063f1`.

Claim scope is `EXECUTED_CROSS_LAYER_ARCHITECTURE_VALIDATIONS_NOT_PHYSICAL_HOST_LEGAL_OR_LLM_SESSIONS`. Neither campaign claims ten million physical hosts, legal judgments, unique texts or LLM sessions.

## Dual saturation

### M — no novelty

The finite mutation signature space is `16 families x 4 modes = M=64`. Every signature is deep-checked once. A further **M+1000** randomized probes must discover zero new signatures.

### N — no greater compression without degradation

The minimal authority partition has six nodes:

`MODE_REGISTRY | EXPLICIT_ROUTER | COMMON_STALENESS | SPECIALIST_PROOF | MATERIALIZATION | PROJECTION`

All one-node deletions and pairwise merges are evaluated: `N = C(6,1) + C(6,2) = 21`. Each candidate degrades at least one authority/separation invariant. A further **N+1000** attempts must yield no smaller partition without degradation. This is architectural compression, not semantic-text compression.

## Global DoD

- four canonical modes and serialized labels unchanged;
- specialist proof semantics unchanged and still authoritative;
- no import-order authority in the public orchestrator;
- one canonical mode registry feeds runtime policy and UI entry projection;
- one common staleness owner, with specialist-only additive invalidation permitted;
- C&C CLI and generic CLI share explicit composition authority;
- chat shell remains projection-only, bounded and state-derived;
- runtime/manifest/package current surface is version-coherent;
- historical test, fixed-point, delivery, semantic-proof and C&C workflows remain green;
- 10M cross-layer mutation soak, M+1000 novelty saturation and N+1000 compression saturation remain green.

## Residual boundary

Historical implementation modules remain for compatibility. v0.13 removes their *implicit composition authority* but does not delete them. Physical removal should happen only after a later equivalence proof demonstrates that no public state, receipt, artifact, migration or historical import relies on them.
