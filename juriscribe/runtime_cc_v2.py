from __future__ import annotations

from typing import Any

from . import runtime_v11 as _v11
from . import runtime_v12 as _v12
from .runtime_v12 import *  # noqa: F401,F403
from .consolidation import canonical_digest
from .editorial_reticulum import (
    PROFILE as EDITORIAL_RETICULUM_PROFILE,
    build_editorial_execution_reticulum,
    build_editorial_refinement_proof,
    verify_editorial_execution_reticulum,
    verify_editorial_refinement_proof,
)
from .editorial_stress import validate_editorial_mutation_evidence
from .modes import COMPRESSION_AND_CONSOLIDATION, normalize_mode
from .semantic_proof_v2 import build_structural_semantic_proof, verify_structural_semantic_proof
from .stress_evidence import validate_mutation_evidence, validate_saturation_evidence

RUNTIME_SEMANTIC_PROFILE = "JURISCRIBE_RUNTIME_SEMANTICS_V2"
A_LEVEL_QUALITY_BAND = "A_LEVEL_EDITORIAL_READY"
SATURATION_CLAIM_SCOPE = "CURRENT_RETICULUM_STRUCTURAL_COMPLETENESS_NOT_REFINED_CANDIDATE_RECALL"


def _cc(state) -> dict[str, Any]:
    return state.strategy.setdefault("consolidation", {})


def _clear_execution_reticulum(state) -> None:
    _cc(state)["execution_reticulum"] = {}


def select_mode(state, mode: str):
    result = _v12.select_mode(state, mode)
    if normalize_mode(state.mode) == COMPRESSION_AND_CONSOLIDATION:
        _clear_execution_reticulum(state)
    return result


def ingest_and_mine(state, *args, **kwargs):
    result = _v12.ingest_and_mine(state, *args, **kwargs)
    if normalize_mode(state.mode) == COMPRESSION_AND_CONSOLIDATION:
        _clear_execution_reticulum(state)
    return result


def register_semantic_mining(state, *args, **kwargs):
    result = _v12.register_semantic_mining(state, *args, **kwargs)
    if normalize_mode(state.mode) == COMPRESSION_AND_CONSOLIDATION:
        _clear_execution_reticulum(state)
    return result


def apply_setup(state, *args, **kwargs):
    result = _v12.apply_setup(state, *args, **kwargs)
    if normalize_mode(state.mode) == COMPRESSION_AND_CONSOLIDATION:
        _clear_execution_reticulum(state)
    return result


def freeze_dods(state, *args, **kwargs):
    result = _v12.freeze_dods(state, *args, **kwargs)
    if normalize_mode(state.mode) == COMPRESSION_AND_CONSOLIDATION:
        _clear_execution_reticulum(state)
    return result


def register_refactoring_plan(state, *, gaps, operations):
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        raise ValueError("refactoring plan is C&C-only")
    plan = _v12.register_refactoring_plan(state, gaps=gaps, operations=operations)
    execution = build_editorial_execution_reticulum(state)
    _cc(state)["execution_reticulum"] = execution
    if execution.get("status") != "PASS":
        state.phase = "EDITORIAL_RETICULUM_INVALID"
        raise ValueError("editorial execution reticulum failed: " + "; ".join(execution.get("errors") or []))
    state.phase = "CONSOLIDATION_MUTATION_REQUIRED"
    return plan


def calibrate_refactoring(state, decisions):
    result = _v12.calibrate_refactoring(state, decisions)
    if normalize_mode(state.mode) == COMPRESSION_AND_CONSOLIDATION and result.get("material_change"):
        _clear_execution_reticulum(state)
    return result


def record_simulation(state, receipt):
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        return _v12.record_simulation(state, receipt)
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    execution = cc.get("execution_reticulum") or {}
    execution_ok, execution_errors = verify_editorial_execution_reticulum(state, execution)
    if not execution_ok:
        raise ValueError("current editorial execution reticulum required: " + "; ".join(execution_errors))
    mutation_ok, mutation_errors = validate_mutation_evidence(
        receipt,
        plan_digest=str(plan.get("digest") or ""),
        reticulum_digest=str((state.reticulum or {}).get("digest") or ""),
    )
    editorial_ok, editorial_errors = validate_editorial_mutation_evidence(
        dict(receipt.get("editorial_coverage_evidence") or {}),
        plan_digest=str(plan.get("digest") or ""),
        reticulum_digest=str((state.reticulum or {}).get("digest") or ""),
        execution_reticulum_digest=str(execution.get("digest") or ""),
    )
    errors = [*mutation_errors, *editorial_errors]
    if not mutation_ok or not editorial_ok:
        raise ValueError("; ".join(dict.fromkeys(errors)))
    return _v11.record_simulation(state, receipt)


def seal_refined_candidate(
    state,
    *,
    source_id: str,
    text: str,
    semantic_projection: dict[str, Any],
):
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        raise ValueError("refined candidate is C&C-only")
    cc = _cc(state)
    execution = cc.get("execution_reticulum") or {}
    execution_ok, execution_errors = verify_editorial_execution_reticulum(state, execution)
    if not execution_ok:
        raise ValueError("current editorial execution reticulum required: " + "; ".join(execution_errors))
    structural = build_structural_semantic_proof(
        state,
        source_id=source_id,
        refined_text=text,
        projection=dict(semantic_projection or {}),
    )
    if structural.get("status") != "PASS":
        raise ValueError("structural semantic proof failed: " + "; ".join(structural.get("errors") or []))
    editorial = build_editorial_refinement_proof(
        state,
        source_id=source_id,
        refined_text=text,
        projection=dict(semantic_projection or {}),
        structural_proof=structural,
        execution_reticulum=execution,
    )
    if editorial.get("status") != "PASS" or editorial.get("quality_band") != A_LEVEL_QUALITY_BAND:
        raise ValueError("editorial refinement proof failed: " + "; ".join(editorial.get("errors") or []))
    record = _v11.seal_refined_candidate(
        state,
        source_id=source_id,
        text=text,
        semantic_recall=1.0,
        relation_recall=1.0,
    )
    record["semantic_proof"] = structural
    record["semantic_proof_digest"] = structural["digest"]
    record["semantic_claim_scope"] = structural["claim_scope"]
    record["structural_unit_recall"] = structural["structural_unit_recall"]
    record["structural_relation_recall"] = structural["structural_relation_recall"]
    record["semantic_recall"] = structural["structural_unit_recall"]
    record["relation_recall"] = structural["structural_relation_recall"]
    record["editorial_execution_reticulum_digest"] = execution["digest"]
    record["editorial_refinement_proof"] = editorial
    record["editorial_refinement_proof_digest"] = editorial["digest"]
    record["editorial_quality_band"] = editorial["quality_band"]
    record["editorial_reticulum_profile"] = EDITORIAL_RETICULUM_PROFILE
    record["runtime_semantic_profile"] = RUNTIME_SEMANTIC_PROFILE
    record["digest"] = canonical_digest({key: value for key, value in record.items() if key != "digest"})
    return record


def consolidation_gate(state) -> tuple[bool, list[str]]:
    if normalize_mode(state.mode) != COMPRESSION_AND_CONSOLIDATION:
        return _v12.consolidation_gate(state)
    cc = _cc(state)
    execution = cc.get("execution_reticulum") or {}
    strict_v2 = bool(execution) or any(
        bool((record or {}).get("editorial_refinement_proof"))
        for record in (cc.get("refined_candidates") or {}).values()
    )
    if not strict_v2:
        return _v12.consolidation_gate(state)

    legacy_ok, legacy_errors = _v11.consolidation_gate(state)
    errors = list(legacy_errors)
    execution_ok, execution_errors = verify_editorial_execution_reticulum(state, execution)
    if not execution_ok:
        errors.extend(execution_errors)

    plan = cc.get("refactoring_contract") or {}
    mutation = cc.get("mutation_receipt") or {}
    mutation_ok, mutation_errors = validate_mutation_evidence(
        mutation,
        plan_digest=str(plan.get("digest") or ""),
        reticulum_digest=str((state.reticulum or {}).get("digest") or ""),
    )
    if not mutation_ok:
        errors.extend(mutation_errors)
    editorial_mutation_ok, editorial_mutation_errors = validate_editorial_mutation_evidence(
        dict(mutation.get("editorial_coverage_evidence") or {}),
        plan_digest=str(plan.get("digest") or ""),
        reticulum_digest=str((state.reticulum or {}).get("digest") or ""),
        execution_reticulum_digest=str(execution.get("digest") or ""),
    )
    if not editorial_mutation_ok:
        errors.extend(editorial_mutation_errors)

    stored_saturation = dict(cc.get("saturation") or {})
    saturation_evidence = dict(stored_saturation)
    saturation_evidence.pop("semantic_recall", None)
    saturation_evidence.pop("relation_recall", None)
    saturation_evidence.pop("recall_claim_scope", None)
    saturation_ok, saturation_errors = validate_saturation_evidence(
        saturation_evidence,
        plan_digest=str(plan.get("digest") or ""),
    )
    if stored_saturation.get("recall_claim_scope") != SATURATION_CLAIM_SCOPE:
        saturation_errors.append("stored saturation recall claim scope mismatch")
        saturation_ok = False
    if not saturation_ok:
        errors.extend(saturation_errors)

    for source_id, record in sorted((cc.get("refined_candidates") or {}).items()):
        structural = record.get("semantic_proof") or {}
        structural_ok, structural_errors = verify_structural_semantic_proof(
            state,
            source_id=str(source_id),
            refined_text=str(record.get("text") or ""),
            proof=structural,
        )
        if not structural_ok:
            errors.extend(f"{source_id}: {message}" for message in structural_errors)
        editorial = record.get("editorial_refinement_proof") or {}
        editorial_ok, editorial_errors = verify_editorial_refinement_proof(
            state,
            source_id=str(source_id),
            refined_text=str(record.get("text") or ""),
            structural_proof=structural,
            execution_reticulum=execution,
            proof=editorial,
        )
        if not editorial_ok:
            errors.extend(f"{source_id}: {message}" for message in editorial_errors)
        if record.get("semantic_proof_digest") != structural.get("digest"):
            errors.append(f"refined candidate semantic proof digest mismatch: {source_id}")
        if record.get("editorial_refinement_proof_digest") != editorial.get("digest"):
            errors.append(f"refined candidate editorial proof digest mismatch: {source_id}")
        if record.get("editorial_execution_reticulum_digest") != execution.get("digest"):
            errors.append(f"refined candidate bound to stale editorial execution reticulum: {source_id}")
        if record.get("editorial_quality_band") != A_LEVEL_QUALITY_BAND:
            errors.append(f"refined candidate not A-level editorial ready: {source_id}")
        if record.get("structural_unit_recall") != 1.0 or record.get("structural_relation_recall") != 1.0:
            errors.append(f"refined candidate structural preservation not lossless: {source_id}")
        expected_digest = canonical_digest({key: value for key, value in record.items() if key != "digest"})
        if record.get("digest") != expected_digest:
            errors.append(f"refined candidate digest mismatch after editorial v2 proof chain: {source_id}")

    return (
        legacy_ok
        and execution_ok
        and mutation_ok
        and editorial_mutation_ok
        and saturation_ok
        and not errors,
        list(dict.fromkeys(errors)),
    )
