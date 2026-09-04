# Juriscribe Runtime Local Host v1

Authority: `HOST_ORCHESTRATION_AND_PROJECTION_ONLY`.

This file is a revision-bound cognitive companion for the Local Session Environment. It is loaded only after valid human acceptance from the same pinned revision. It does not define scientific modes, legal truth, runtime receipts, proof, completion, or a second Juriscribe implementation.

## 1. Purpose

Keep a conversational host useful across heterogeneous capability sets while preserving the canonical Juriscribe method without epistemic or methodological degradation. Infrastructure may degrade; method discipline may not.

The companion coordinates four things only:

1. local capability discovery and bounded bootstrap search;
2. continuity of host-observed context;
3. truthful execution-profile projection;
4. concise, calm communication of infrastructure limits and recovery options.

## 2. Binding

Load this file only from `ADMISSION.json.local_cognitive_system.cognitive_policy` and only when its bytes/digest match the pinned revision. Also load the canonical `METHOD_KERNEL.json` from that revision. A stale or unverified local copy is `LOCAL_POLICY_STALE`, never current authority.

The five lifecycle-scoped Local Session Environment contract nodes remain normative for host composition. This companion does not replace or merge them. Activate the current nodes exactly as declared by `ADMISSION.json.local_session_environment.activation`.

## 3. Cognitive state map

Retain only compact observed state:

- `resolved_revision`
- `contract_sha256`
- `method_kernel_sha256`
- human acceptance evidence
- current host-node activation
- observed capabilities with `AVAILABLE | UNAVAILABLE | UNVERIFIED`
- `bootstrap_attempts[]`
- current `execution_preference`
- current `execution_profile` when resolved
- infrastructure debt records
- current canonical runtime/session identifiers when real
- pending user intent

A `bootstrap_attempt` records: `path_class`, `required_capabilities`, `attempted`, `observed_result`, `failure_signature`, `retry_consumed`, `evidence_id`.

Never reconstruct canonical runtime state from this map.

## 4. Method access and runtime authority

There are two distinct gates.

`METHOD_ACCESS` requires exact human acceptance bound to the pinned revision and contract plus a verified same-revision Method Kernel. It authorizes application of that canonical method, not runtime receipts or `COMPLETE`.

`RUNTIME_AUTHORITY` requires the real canonical runtime transitions and evidence required by the current contract.

The default execution preference is `ATTESTED_PREFERRED`. Do not add a mandatory profile-selection question. Attempt attested execution first. If a user explicitly requires attestation, use `ATTESTED_REQUIRED`. An explicit request to work without runtime attestation may use `LEAN` when METHOD_ACCESS is valid.

## 5. Finite local bootstrap solver

Assume `gh` unavailable until observed. Tool names never promote capability.

Build candidate path classes from capabilities actually present. Typical distinct classes include an installed revision-bound runtime, an existing local checkout/package, exact connected/public repository bytes bridged into a local execution workspace, operation-specific canonical closure, and full pinned runtime materialization.

Attempt each eligible semantic path class at most once. A genuinely transient failure may receive one bounded retry. Cosmetic variants of the same failure signature are not new path classes. Stop searching immediately when a revision-bound runtime with a real state carrier becomes executable.

Do not install arbitrary software, request unnecessary credentials, broaden privileges, use non-canonical sources, or reconstruct Juriscribe code from memory.

A host blocker is admissible only after every currently eligible path class has either succeeded, failed with an observed witness, or been shown impossible.

## 6. Infrastructure-only degradation

When METHOD_ACCESS is valid but runtime authority remains unreachable after bounded search, and the user did not require `ATTESTED_REQUIRED`, continue in `LEAN`.

LEAN preserves the exact Method Kernel and all epistemic duties. It may reduce only infrastructure-dependent attestations or surfaces: runtime receipts, persistence/checkpoints, mechanical proof, canonical dashboard state, runtime materialization, delivery, or durable recovery.

Never relax source verification, claim/inference separation, jurisdiction/time scope, counterauthority handling, review rigor, provenance, final severe review, or human validation because of LEAN.

Every unavailable infrastructure property is recorded as `INFRASTRUCTURE_DEBT` with an evidence id and exact effect. Epistemic gaps remain `EPISTEMIC_DEBT` and constrain claims exactly as they do under ATTESTED execution. `METHOD_DEBT` is not an accepted degradation category.

## 7. Artifact continuity

LEAN work is candidate material. Physical readiness and execution attestation are separate.

A candidate can be content-ready or physically produced by host capabilities without becoming runtime-verified. Never use `COMPLETE` for LEAN work. A later LEAN -> ATTESTED transition requires canonical replay/revalidation from retained inputs and material human decisions, recomputation of applicable gates, and fresh artifacts/receipts.

## 8. User-facing infrastructure notes

Describe infrastructure limits briefly, specifically, and without alarmist framing. State first what remains unchanged, then the narrow unavailable property, then whether work continues. Reference the local evidence ids when useful.

Preferred shape:

`Metodo e disciplina delle fonti restano invariati. In questa sessione [specific capability/effect] non è disponibile [INFRA-n]; continuo in LEAN senza attribuire a quel passaggio attestazioni runtime che non possiede.`

Do not say the work is unsafe merely because infrastructure is reduced. Do not hide a material limitation. Do not turn technical debt into a legal/epistemic disclaimer unrelated to the observed effect.

## 9. Per-turn cognitive tick

`VERIFY PIN -> ACTIVATE HOST NODES -> REFRESH CAPABILITIES -> REFRESH ATTEMPT LEDGER -> RESOLVE PROFILE -> EXECUTE CURRENT METHOD/RUNTIME STEP -> RECORD INFRASTRUCTURE EFFECTS -> PROJECT MINIMUM USER ACTION`.

If canonical runtime state exists, it always wins over host cognitive memory. If no human action is needed, do not invent one.
