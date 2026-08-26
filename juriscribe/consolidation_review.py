from __future__ import annotations

from typing import Any

from .consolidation import (
    CANDIDATE_ROLE,
    canonical_digest,
    validate_mutation_receipt,
    validate_saturation_receipt,
)
from .modes import COMPRESSION_CONSOLIDATION, normalize_mode

REVIEW_SCHEMA = "juriscribe-consolidation-peer-review-readiness/v1"
PROVENANCE_SCHEMA = "juriscribe-consolidation-provenance/v1"
FINAL_REVIEW_SCHEMA = "juriscribe-consolidation-final-review/v1"

REQUIRED_REVIEW_DIMENSIONS = {
    "scientific_consistency",
    "editorial_coherence",
    "argument_strength",
    "local_progression",
    "reticular_progression",
    "semantic_losslessness",
    "canonical_conditioning",
}


def _cc(state):
    return state.strategy.setdefault("consolidation", {})


def _dimension_pass(value: Any) -> bool:
    if value is True:
        return True
    return str(value or "").strip().upper() == "PASS"


def _current_candidate_sources(state) -> dict[str, dict[str, Any]]:
    return {
        str(c.get("source_id")): c
        for c in state.corpus
        if c.get("role") == CANDIDATE_ROLE and c.get("source_id")
    }


def _proof_chain_errors(state) -> list[str]:
    cc = _cc(state)
    errors: list[str] = []
    plan = cc.get("refactoring_contract") or {}
    reticulum_digest = str(state.reticulum.get("digest") or "")
    plan_digest = str(plan.get("digest") or "")
    if plan.get("status") != "READY":
        errors.append("current refactoring contract READY required")
    if state.reticulum.get("status") != "PASS":
        errors.append("current consolidation reticulum PASS required")
    mutation = cc.get("mutation_receipt") or {}
    mutation_ok, mutation_errors = validate_mutation_receipt(
        mutation,
        plan_digest=plan_digest,
        reticulum_digest=reticulum_digest,
    )
    if not mutation_ok:
        errors.extend(mutation_errors)
    saturation = cc.get("saturation") or {}
    saturation_ok, saturation_errors = validate_saturation_receipt(
        saturation,
        plan_digest=plan_digest,
    )
    if not saturation_ok:
        errors.extend(saturation_errors)
    candidates = _current_candidate_sources(state)
    sealed = cc.get("refined_candidates") or {}
    for source_id, source in candidates.items():
        record = sealed.get(source_id) or {}
        if record.get("status") != "SEALED":
            errors.append(f"refined candidate not sealed: {source_id}")
            continue
        if record.get("source_digest") != source.get("digest"):
            errors.append(f"refined candidate bound to stale source: {source_id}")
        if record.get("plan_digest") != plan_digest:
            errors.append(f"refined candidate bound to stale plan: {source_id}")
        if record.get("reticulum_digest") != reticulum_digest:
            errors.append(f"refined candidate bound to stale reticulum: {source_id}")
        if record.get("semantic_recall") != 1.0 or record.get("relation_recall") != 1.0:
            errors.append(f"refined candidate not semantically lossless: {source_id}")
    return list(dict.fromkeys(errors))


def record_peer_review_readiness(state, payload: dict[str, Any]):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("peer-review readiness is C&C-only")
    cc = _cc(state)
    errors = _proof_chain_errors(state)
    dimensions = dict(payload.get("dimensions") or {})
    missing = REQUIRED_REVIEW_DIMENSIONS - set(dimensions)
    if missing:
        errors.append("peer-review readiness dimensions missing: " + ", ".join(sorted(missing)))
    failed = sorted(
        key for key in REQUIRED_REVIEW_DIMENSIONS
        if key in dimensions and not _dimension_pass(dimensions.get(key))
    )
    if failed:
        errors.append("peer-review readiness dimensions not PASS: " + ", ".join(failed))
    blockers = list(payload.get("blockers") or [])
    if blockers:
        errors.append("peer-review readiness has open blockers")
    plan_digest = str((cc.get("refactoring_contract") or {}).get("digest") or "")
    reticulum_digest = str(state.reticulum.get("digest") or "")
    rec = {
        "schema": REVIEW_SCHEMA,
        "plan_digest": plan_digest,
        "reticulum_digest": reticulum_digest,
        "dimensions": dimensions,
        "blockers": blockers,
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
        "claim": "READY_FOR_PEER_REVIEW_NOT_PEER_REVIEWED",
    }
    rec["digest"] = canonical_digest(rec)
    cc["peer_review_readiness"] = rec
    state.review["status"] = "PEER_REVIEW_READY" if not errors else "REVIEW_REQUIRED"
    state.phase = "PEER_REVIEW_READY" if not errors else "SCIENTIFIC_EDITORIAL_REVIEW"
    return rec


def record_consolidation_provenance(state, payload: dict[str, Any]):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("C&C provenance only")
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    plan_digest = str(plan.get("digest") or "")
    reticulum_digest = str(state.reticulum.get("digest") or "")
    errors: list[str] = []
    readiness = cc.get("peer_review_readiness") or {}
    if readiness.get("status") != "PASS":
        errors.append("peer-review readiness PASS required before provenance")
    if readiness.get("plan_digest") != plan_digest:
        errors.append("peer-review readiness bound to stale plan")
    if readiness.get("reticulum_digest") != reticulum_digest:
        errors.append("peer-review readiness bound to stale reticulum")

    dispositions = list(payload.get("dispositions") or [])
    disposition_ids = [str(x.get("id") or "").strip() for x in dispositions]
    if not dispositions:
        errors.append("provenance dispositions missing")
    if any(not value for value in disposition_ids):
        errors.append("every provenance disposition requires a stable id")
    nonempty_ids = [value for value in disposition_ids if value]
    if len(nonempty_ids) != len(set(nonempty_ids)):
        errors.append("provenance disposition ids must be unique")

    all_ops = {str(x.get("id")) for x in plan.get("operations", []) if x.get("id")}
    required_ops = {
        str(x.get("id"))
        for x in plan.get("operations", [])
        if x.get("operation") != "KEEP" and x.get("id")
    }
    required_sources = set(_current_candidate_sources(state))
    covered_ops: set[str] = set()
    covered_sources: set[str] = set()
    for item in dispositions:
        operation_id = str(item.get("operation_id") or "").strip()
        source_id = str(item.get("source_id") or "").strip()
        if operation_id:
            if operation_id not in all_ops:
                errors.append(f"provenance references unknown operation: {operation_id}")
            else:
                covered_ops.add(operation_id)
        if source_id:
            if source_id not in required_sources:
                errors.append(f"provenance references unknown candidate source: {source_id}")
            else:
                covered_sources.add(source_id)
    if required_ops - covered_ops:
        errors.append("provenance missing transformed operations")
    if required_sources - covered_sources:
        errors.append("provenance missing candidate source disposition")

    rec = {
        "schema": PROVENANCE_SCHEMA,
        "plan_digest": plan_digest,
        "reticulum_digest": reticulum_digest,
        "readiness_digest": str(readiness.get("digest") or ""),
        "dispositions": dispositions,
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    rec["digest"] = canonical_digest(rec)
    cc["provenance"] = rec
    state.provenance = rec
    state.phase = "PROVENANCE" if not errors else "PROVENANCE_REQUIRED"
    return rec


def record_consolidation_final_review(state, payload: dict[str, Any]):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("C&C final review only")
    cc = _cc(state)
    errors: list[str] = []
    plan_digest = str((cc.get("refactoring_contract") or {}).get("digest") or "")
    reticulum_digest = str(state.reticulum.get("digest") or "")
    readiness = cc.get("peer_review_readiness") or {}
    provenance = cc.get("provenance") or {}
    if readiness.get("status") != "PASS":
        errors.append("peer-review readiness PASS required")
    if readiness.get("plan_digest") != plan_digest or readiness.get("reticulum_digest") != reticulum_digest:
        errors.append("peer-review readiness is stale")
    if provenance.get("status") != "PASS":
        errors.append("provenance PASS required")
    if provenance.get("plan_digest") != plan_digest or provenance.get("reticulum_digest") != reticulum_digest:
        errors.append("provenance is stale")
    if provenance.get("readiness_digest") != readiness.get("digest"):
        errors.append("provenance bound to stale peer-review readiness")
    if str(payload.get("status") or "").upper() != "PASS":
        errors.append("final severe review must PASS")
    if payload.get("plan_digest") != plan_digest:
        errors.append("final review bound to stale plan")
    if payload.get("reticulum_digest") != reticulum_digest:
        errors.append("final review bound to stale reticulum")
    if list(payload.get("blockers") or []):
        errors.append("final severe review has open blockers")
    rec = {
        "schema": FINAL_REVIEW_SCHEMA,
        "plan_digest": plan_digest,
        "reticulum_digest": reticulum_digest,
        "readiness_digest": str(readiness.get("digest") or ""),
        "provenance_digest": str(provenance.get("digest") or ""),
        "findings": list(payload.get("findings") or []),
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    rec["digest"] = canonical_digest(rec)
    cc["final_review"] = rec
    state.final_review = rec
    state.phase = "FINAL_REVIEWED" if not errors else "FINAL_REVIEW_REQUIRED"
    return rec
