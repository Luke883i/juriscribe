from __future__ import annotations
from typing import Any

from . import runtime_v11 as _legacy
from .runtime_v11 import *  # noqa: F401,F403
from .consolidation import canonical_digest
from .modes import COMPRESSION_AND_CONSOLIDATION, normalize_mode
from .semantic_proof import build_structural_semantic_proof, verify_structural_semantic_proof
from .stress_evidence import validate_mutation_evidence, validate_saturation_evidence

RUNTIME_SEMANTIC_PROFILE = "JURISCRIBE_RUNTIME_SEMANTICS_V1"


def record_simulation(state, receipt):
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        return _legacy.record_simulation(state, receipt)
    cc = state.strategy.setdefault("consolidation", {})
    plan = cc.get("refactoring_contract") or {}
    ok, errors = validate_mutation_evidence(
        receipt,
        plan_digest=str(plan.get("digest") or ""),
        reticulum_digest=str((state.reticulum or {}).get("digest") or ""),
    )
    if not ok:
        raise ValueError("; ".join(errors))
    return _legacy.record_simulation(state, receipt)


def record_consolidation_saturation(state, receipt):
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        raise ValueError("C&C saturation only")
    cc = state.strategy.setdefault("consolidation", {})
    plan = cc.get("refactoring_contract") or {}
    ok, errors = validate_saturation_evidence(receipt, plan_digest=str(plan.get("digest") or ""))
    if not ok:
        raise ValueError("; ".join(errors))
    normalized = dict(receipt)
    normalized["semantic_recall"] = 1.0
    normalized["relation_recall"] = 1.0
    normalized["recall_claim_scope"] = (
        "CURRENT_RETICULUM_STRUCTURAL_COMPLETENESS_NOT_REFINED_CANDIDATE_RECALL"
    )
    return _legacy.record_consolidation_saturation(state, normalized)


def seal_refined_candidate(
    state,
    *,
    source_id: str,
    text: str,
    semantic_projection: dict[str, Any],
):
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        raise ValueError("refined candidate is C&C-only")
    proof = build_structural_semantic_proof(
        state,
        source_id=source_id,
        refined_text=text,
        projection=dict(semantic_projection or {}),
    )
    if proof.get("status") != "PASS":
        raise ValueError("structural semantic proof failed: " + "; ".join(proof.get("errors") or []))
    record = _legacy.seal_refined_candidate(
        state,
        source_id=source_id,
        text=text,
        semantic_recall=1.0,
        relation_recall=1.0,
    )
    record["semantic_proof"] = proof
    record["semantic_proof_digest"] = proof["digest"]
    record["semantic_claim_scope"] = proof["claim_scope"]
    record["structural_unit_recall"] = proof["structural_unit_recall"]
    record["structural_relation_recall"] = proof["structural_relation_recall"]
    record["semantic_recall"] = proof["structural_unit_recall"]
    record["relation_recall"] = proof["structural_relation_recall"]
    record["runtime_semantic_profile"] = RUNTIME_SEMANTIC_PROFILE
    record["digest"] = canonical_digest({key: value for key, value in record.items() if key != "digest"})
    return record


def consolidation_gate(state) -> tuple[bool, list[str]]:
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        return _legacy.consolidation_gate(state)
    legacy_ok, legacy_errors = _legacy.consolidation_gate(state)
    cc = state.strategy.setdefault("consolidation", {})
    strict_semantics = bool((cc.get("mutation_receipt") or {}).get("coverage_evidence")) or any(
        bool((record or {}).get("semantic_proof"))
        for record in (cc.get("refined_candidates") or {}).values()
    )
    if not strict_semantics:
        return legacy_ok, list(legacy_errors)
    errors = list(legacy_errors)
    plan = cc.get("refactoring_contract") or {}
    mutation_ok, mutation_errors = validate_mutation_evidence(
        cc.get("mutation_receipt") or {},
        plan_digest=str(plan.get("digest") or ""),
        reticulum_digest=str((state.reticulum or {}).get("digest") or ""),
    )
    if not mutation_ok:
        errors.extend(mutation_errors)
    stored_saturation = dict(cc.get("saturation") or {})
    saturation_evidence = dict(stored_saturation)
    saturation_evidence.pop("semantic_recall", None)
    saturation_evidence.pop("relation_recall", None)
    saturation_evidence.pop("recall_claim_scope", None)
    saturation_ok, saturation_errors = validate_saturation_evidence(
        saturation_evidence,
        plan_digest=str(plan.get("digest") or ""),
    )
    if stored_saturation.get("recall_claim_scope") != (
        "CURRENT_RETICULUM_STRUCTURAL_COMPLETENESS_NOT_REFINED_CANDIDATE_RECALL"
    ):
        saturation_errors.append("stored saturation recall claim scope mismatch")
        saturation_ok = False
    if not saturation_ok:
        errors.extend(saturation_errors)
    for source_id, record in sorted((cc.get("refined_candidates") or {}).items()):
        proof = record.get("semantic_proof") or {}
        proof_ok, proof_errors = verify_structural_semantic_proof(
            state,
            source_id=str(source_id),
            refined_text=str(record.get("text") or ""),
            proof=proof,
        )
        if not proof_ok:
            errors.extend(f"{source_id}: {message}" for message in proof_errors)
        if record.get("semantic_proof_digest") != proof.get("digest"):
            errors.append(f"refined candidate semantic proof digest mismatch: {source_id}")
        if record.get("semantic_claim_scope") != proof.get("claim_scope"):
            errors.append(f"refined candidate semantic claim scope mismatch: {source_id}")
        if record.get("structural_unit_recall") != 1.0 or record.get("structural_relation_recall") != 1.0:
            errors.append(f"refined candidate structural preservation not lossless: {source_id}")
        expected_digest = canonical_digest({key: value for key, value in record.items() if key != "digest"})
        if record.get("digest") != expected_digest:
            errors.append(f"refined candidate digest mismatch after semantic proof: {source_id}")
    return legacy_ok and mutation_ok and saturation_ok and not errors, list(dict.fromkeys(errors))
