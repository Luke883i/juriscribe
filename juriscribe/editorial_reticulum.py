from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from .consolidation import (
    ALLOWED_OPERATIONS,
    CANDIDATE_ROLE,
    build_lossless_inventory,
    canonical_digest,
    text_digest,
)

SCHEMA = "juriscribe-editorial-execution-reticulum/v1"
REFINEMENT_SCHEMA = "juriscribe-editorial-refinement-proof/v1"
PROFILE = "JURISCRIBE_A_LEVEL_SCIENTIFIC_EDITORIAL_RETICULUM_V1"
CLAIM_SCOPE = (
    "EDITORIAL_ARGUMENT_AND_COMPRESSION_DISCIPLINE_"
    "NOT_SCIENTIFIC_TRUTH_OR_JOURNAL_ACCEPTANCE"
)
QUALITY_TARGET = "A_LEVEL_SCIENTIFIC_EDITORIAL"

ALLOWED_FUNCTIONS = {
    "ARGUMENT", "CLAIM", "EVIDENCE", "WARRANT", "METHOD", "RESULT",
    "QUALIFIER", "LIMITATION", "DEFINITION", "CONTEXT", "TRANSITION", "IMPLICATION",
}
KIND_TO_FUNCTION = {
    "ARGUMENT": "ARGUMENT",
    "CLAIM": "CLAIM",
    "THESIS": "CLAIM",
    "PROPOSITION": "CLAIM",
    "FACT": "EVIDENCE",
    "EVIDENCE": "EVIDENCE",
    "SOURCE": "EVIDENCE",
    "WARRANT": "WARRANT",
    "REASON": "WARRANT",
    "ANALYSIS": "WARRANT",
    "METHOD": "METHOD",
    "METHODOLOGY": "METHOD",
    "RESULT": "RESULT",
    "FINDING": "RESULT",
    "QUALIFIER": "QUALIFIER",
    "QUALIFICATION": "QUALIFIER",
    "LIMITATION": "LIMITATION",
    "CAVEAT": "LIMITATION",
    "DEFINITION": "DEFINITION",
    "BACKGROUND": "CONTEXT",
    "CONTEXT": "CONTEXT",
    "TRANSITION": "TRANSITION",
    "BRIDGE": "TRANSITION",
    "IMPLICATION": "IMPLICATION",
    "CONCLUSION": "IMPLICATION",
}
SUPPORT_PREDICATES = {
    "SUPPORTS", "EVIDENCES", "WARRANTS", "ESTABLISHES", "RESULT_SUPPORTS",
    "SUPPORTED_BY", "EVIDENCED_BY", "JUSTIFIES",
}
REORDER_OPERATIONS = {"MOVE", "REORDER"}
EXPANSION_OPERATIONS = {"CLARIFY", "QUALIFY", "BRIDGE", "SPLIT", "LOCAL_REWRITE"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}


def _material(value: dict[str, Any]) -> bool:
    return value.get("material", True) is not False


def _norm(text: Any) -> str:
    return " ".join(str(text or "").split())


def _words(text: Any) -> int:
    return len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'’-]+\b", str(text or ""), flags=re.UNICODE))


def _function(unit: dict[str, Any]) -> tuple[str, str | None]:
    explicit = str(unit.get("editorial_function") or unit.get("function") or "").strip().upper()
    if explicit:
        if explicit not in ALLOWED_FUNCTIONS:
            return "", f"unsupported editorial function: {explicit}"
        return explicit, None
    kind = str(unit.get("kind") or "ARGUMENT").strip().upper()
    return KIND_TO_FUNCTION.get(kind, "ARGUMENT"), None


def _cc(state: Any) -> dict[str, Any]:
    return (state.strategy or {}).get("consolidation") or {}


def _candidate_inventory_map(state: Any) -> dict[str, dict[str, Any]]:
    return {
        str(source_id): dict(inv)
        for source_id, inv in (_cc(state).get("inventories") or {}).items()
        if str((inv or {}).get("role") or "") == CANDIDATE_ROLE
    }


def _object_order(state: Any) -> dict[str, tuple[str, int]]:
    out: dict[str, tuple[str, int]] = {}
    for source_id, inv in _candidate_inventory_map(state).items():
        for obj in inv.get("objects") or []:
            oid = str(obj.get("id") or "")
            if oid:
                out[oid] = (source_id, int(obj.get("ordinal") or 0))
    return out


def _operation_index(plan: dict[str, Any]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    for op in plan.get("operations") or []:
        uid = str(op.get("unit_id") or "")
        operation = str(op.get("operation") or "").upper()
        if uid and operation:
            index[uid].add(operation)
    return dict(index)


def build_editorial_execution_reticulum(state: Any) -> dict[str, Any]:
    errors: list[str] = []
    cc = _cc(state)
    source_reticulum = state.reticulum or {}
    plan = cc.get("refactoring_contract") or {}
    inventories = _candidate_inventory_map(state)
    order = _object_order(state)

    if source_reticulum.get("status") != "PASS":
        errors.append("current PASS source semantic reticulum required")
    if plan.get("status") != "READY":
        errors.append("current READY refactoring contract required")
    if not inventories:
        errors.append("at least one candidate inventory required")

    candidate_units: list[dict[str, Any]] = []
    seen_units: set[str] = set()
    for unit in state.epistemic_units or []:
        if str(unit.get("material_role") or "") != CANDIDATE_ROLE or not _material(unit):
            continue
        uid = str(unit.get("id") or "")
        if not uid or uid in seen_units:
            errors.append("candidate material semantic unit ids must be unique and non-empty")
        seen_units.add(uid)
        source_id = str(unit.get("source_id") or "")
        object_id = str(unit.get("object_id") or "")
        if source_id not in inventories:
            errors.append(f"candidate unit bound to unknown candidate source: {uid or '?'}")
        if object_id not in order or order.get(object_id, (None,))[0] != source_id:
            errors.append(f"candidate unit object/source binding invalid: {uid or '?'}")
        function, function_error = _function(unit)
        if function_error:
            errors.append(f"{uid or '?'}: {function_error}")
        candidate_units.append({
            "unit_id": uid,
            "source_id": source_id,
            "object_id": object_id,
            "ordinal": int(order.get(object_id, (source_id, 0))[1]),
            "function": function or "ARGUMENT",
            "kind": str(unit.get("kind") or "ARGUMENT").upper(),
            "text_digest": text_digest(str(unit.get("text") or "")),
        })

    if not candidate_units:
        errors.append("candidate material has no material semantic units")

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for step in candidate_units:
        by_source[step["source_id"]].append(step)
    local_edges: list[dict[str, Any]] = []
    for source_id, steps in sorted(by_source.items()):
        steps.sort(key=lambda item: (item["ordinal"], item["unit_id"]))
        for left, right in zip(steps, steps[1:]):
            local_edges.append({
                "source": left["unit_id"],
                "predicate": "LOCAL_PROGRESSION",
                "target": right["unit_id"],
                "source_id": source_id,
            })

    unit_ids = {step["unit_id"] for step in candidate_units}
    semantic_edges: list[dict[str, Any]] = []
    relation_degree = Counter()
    claim_support = Counter()
    for relation in state.relations or []:
        if not _material(relation):
            continue
        src = str(relation.get("source") or "")
        dst = str(relation.get("target") or "")
        if src not in unit_ids and dst not in unit_ids:
            continue
        edge = {
            "id": str(relation.get("id") or ""),
            "source": src,
            "predicate": str(relation.get("predicate") or "").upper(),
            "target": dst,
        }
        semantic_edges.append(edge)
        if src in unit_ids:
            relation_degree[src] += 1
        if dst in unit_ids:
            relation_degree[dst] += 1
        pred = edge["predicate"]
        if pred in SUPPORT_PREDICATES:
            if dst in unit_ids:
                claim_support[dst] += 1
            if src in unit_ids and pred in {"SUPPORTED_BY", "EVIDENCED_BY"}:
                claim_support[src] += 1

    relation_covered = {uid for uid in unit_ids if relation_degree[uid] > 0}
    relation_coverage = len(relation_covered) / max(len(unit_ids), 1)
    if unit_ids and relation_coverage < 1.0:
        errors.append("candidate semantic relation coverage below 1.0")

    explicit_claim_ids = {
        step["unit_id"] for step in candidate_units if step["function"] == "CLAIM"
    }
    supported_claim_ids = {uid for uid in explicit_claim_ids if claim_support[uid] > 0}
    claim_support_coverage = (
        len(supported_claim_ids) / max(len(explicit_claim_ids), 1)
        if explicit_claim_ids else 1.0
    )
    if explicit_claim_ids and claim_support_coverage < 1.0:
        errors.append("explicit claim support-path coverage below 1.0")

    gaps = {str(g.get("id") or ""): g for g in plan.get("gaps") or [] if g.get("id")}
    operation_nodes: list[dict[str, Any]] = []
    bound_gaps: set[str] = set()
    for op in plan.get("operations") or []:
        operation = str(op.get("operation") or "").upper()
        uid = str(op.get("unit_id") or "")
        gap_ids = [str(item) for item in (op.get("gap_ids") or []) if str(item)]
        if operation not in ALLOWED_OPERATIONS:
            errors.append(f"unsupported execution operation: {operation or '?'}")
        if uid not in unit_ids:
            errors.append(f"execution operation targets unknown candidate unit: {uid or '?'}")
        unknown = [gid for gid in gap_ids if gid not in gaps]
        if unknown:
            errors.append("execution operation references unknown gaps: " + ", ".join(sorted(unknown)))
        bound_gaps.update(gid for gid in gap_ids if gid in gaps)
        expected_benefit = str(op.get("expected_benefit") or "").strip()
        risk = str(op.get("degradation_risk") or "").strip().upper()
        rationale = str(op.get("rationale") or "").strip()
        if operation != "KEEP":
            if not rationale:
                errors.append(f"operation rationale missing: {uid or '?'}")
            if not expected_benefit:
                errors.append(f"operation expected benefit missing: {uid or '?'}")
            if risk not in RISK_LEVELS:
                errors.append(f"operation degradation risk missing/invalid: {uid or '?'}")
        operation_nodes.append({
            "id": str(op.get("id") or ""),
            "unit_id": uid,
            "operation": operation,
            "gap_ids": gap_ids,
            "rationale": rationale,
            "expected_benefit": expected_benefit,
            "degradation_risk": risk,
        })

    gap_coverage = len(bound_gaps) / max(len(gaps), 1) if gaps else 1.0
    if gaps and gap_coverage < 1.0:
        errors.append("material gap disposition coverage below 1.0")

    function_counts = Counter(step["function"] for step in candidate_units)
    stages = [
        {
            "stage": "SOURCE_SEMANTIC_RETICULUM",
            "digest": str(source_reticulum.get("digest") or ""),
            "unit_count": len(candidate_units),
            "relation_count": len(semantic_edges),
        },
        {
            "stage": "EDITORIAL_FUNCTION_RETICULUM",
            "digest": canonical_digest({"steps": candidate_units, "local_edges": local_edges, "semantic_edges": semantic_edges}),
            "function_counts": dict(sorted(function_counts.items())),
            "relation_coverage": round(relation_coverage, 6),
            "claim_support_coverage": round(claim_support_coverage, 6),
        },
        {
            "stage": "REFACTORING_SURGERY_RETICULUM",
            "digest": canonical_digest({"plan_digest": plan.get("digest"), "operations": operation_nodes}),
            "operation_count": len(operation_nodes),
            "gap_disposition_coverage": round(gap_coverage, 6),
        },
    ]
    payload = {
        "schema": SCHEMA,
        "profile": PROFILE,
        "claim_scope": CLAIM_SCOPE,
        "quality_target": QUALITY_TARGET,
        "scientific_truth_claim": False,
        "journal_acceptance_claim": False,
        "source_reticulum_digest": str(source_reticulum.get("digest") or ""),
        "plan_digest": str(plan.get("digest") or ""),
        "candidate_inventory_set_digest": canonical_digest(sorted((sid, inv.get("digest")) for sid, inv in inventories.items())),
        "candidate_unit_count": len(candidate_units),
        "candidate_relation_count": len(semantic_edges),
        "candidate_relation_coverage": round(relation_coverage, 6),
        "explicit_claim_count": len(explicit_claim_ids),
        "explicit_claim_support_coverage": round(claim_support_coverage, 6),
        "material_gap_disposition_coverage": round(gap_coverage, 6),
        "steps": candidate_units,
        "local_edges": local_edges,
        "semantic_edges": semantic_edges,
        "operations": operation_nodes,
        "stages": stages,
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def verify_editorial_execution_reticulum(state: Any, reticulum: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not reticulum:
        return False, ["editorial execution reticulum missing"]
    expected = build_editorial_execution_reticulum(state)
    errors: list[str] = []
    for key in (
        "schema", "profile", "claim_scope", "quality_target", "scientific_truth_claim",
        "journal_acceptance_claim", "source_reticulum_digest", "plan_digest",
        "candidate_inventory_set_digest", "candidate_unit_count", "candidate_relation_count",
        "candidate_relation_coverage", "explicit_claim_count", "explicit_claim_support_coverage",
        "material_gap_disposition_coverage", "steps", "local_edges", "semantic_edges", "operations",
        "stages", "status", "errors",
    ):
        if reticulum.get(key) != expected.get(key):
            errors.append(f"editorial execution reticulum {key} mismatch")
    digest = canonical_digest({k: v for k, v in reticulum.items() if k != "digest"})
    if reticulum.get("digest") != digest:
        errors.append("editorial execution reticulum digest mismatch")
    if expected.get("status") != "PASS":
        errors.extend(expected.get("errors") or ["editorial execution reticulum is not PASS"])
    return not errors, list(dict.fromkeys(errors))


def _object_refs(unit: dict[str, Any]) -> list[str]:
    refs = unit.get("object_ids")
    if isinstance(refs, list) and refs:
        return [str(item) for item in refs if str(item)]
    oid = str(unit.get("object_id") or "")
    return [oid] if oid else []


def build_editorial_refinement_proof(
    state: Any,
    *,
    source_id: str,
    refined_text: str,
    projection: dict[str, Any],
    structural_proof: dict[str, Any],
    execution_reticulum: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    ok, reticulum_errors = verify_editorial_execution_reticulum(state, execution_reticulum)
    if not ok:
        errors.extend(reticulum_errors)
    if structural_proof.get("status") != "PASS":
        errors.append("PASS structural semantic proof required")

    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    candidate_inv = (cc.get("inventories") or {}).get(source_id) or {}
    if str(candidate_inv.get("role") or "") != CANDIDATE_ROLE:
        errors.append("candidate inventory missing for refinement proof")
    original_objects = {str(obj.get("id") or ""): obj for obj in candidate_inv.get("objects") or []}
    original_text = "\n\n".join(str(obj.get("text") or "") for obj in candidate_inv.get("objects") or [])
    refined_inventory = build_lossless_inventory(refined_text, source_id=source_id, role=CANDIDATE_ROLE)
    output_objects = {str(obj.get("id") or ""): obj for obj in refined_inventory.get("objects") or []}
    output_order = {oid: int(obj.get("ordinal") or 0) for oid, obj in output_objects.items()}

    source_units = [
        unit for unit in (state.epistemic_units or [])
        if str(unit.get("source_id") or "") == source_id
        and str(unit.get("material_role") or "") == CANDIDATE_ROLE
        and _material(unit)
    ]
    original_order = {
        str(unit.get("id") or ""): int((original_objects.get(str(unit.get("object_id") or "")) or {}).get("ordinal") or 0)
        for unit in source_units
    }
    projected = [
        dict(unit) for unit in (projection or {}).get("units", [])
        if str(unit.get("source_id") or "") == source_id and _material(unit)
    ]
    projected_by_id = {str(unit.get("id") or ""): unit for unit in projected if unit.get("id")}
    op_index = _operation_index(plan)

    anchor: dict[str, int] = {}
    output_to_units: dict[str, set[str]] = defaultdict(set)
    split_units: set[str] = set()
    for uid, unit in projected_by_id.items():
        refs = _object_refs(unit)
        if not refs:
            errors.append(f"refined unit has no output object binding: {uid}")
            continue
        unknown = [oid for oid in refs if oid not in output_objects]
        if unknown:
            errors.append(f"refined unit references unknown output objects: {uid}")
            continue
        if len(set(refs)) != len(refs):
            errors.append(f"refined unit repeats output object binding: {uid}")
        if len(refs) > 1:
            split_units.add(uid)
            if "SPLIT" not in op_index.get(uid, set()):
                errors.append(f"unauthorized semantic split: {uid}")
        anchor[uid] = min(output_order[oid] for oid in refs)
        for oid in refs:
            output_to_units[oid].add(uid)

    merge_groups = [sorted(uids) for uids in output_to_units.values() if len(uids) > 1]
    for group in merge_groups:
        unauthorized = [uid for uid in group if "MERGE_REDUNDANCY" not in op_index.get(uid, set())]
        if unauthorized:
            errors.append("unauthorized semantic merge: " + ", ".join(unauthorized))

    original_sequence = [uid for uid, _ in sorted(original_order.items(), key=lambda item: (item[1], item[0]))]
    refined_sequence = [
        uid for uid in sorted(original_sequence, key=lambda item: (anchor.get(item, 10**9), original_order.get(item, 10**9), item))
        if uid in projected_by_id
    ]
    original_positions = {uid: index for index, uid in enumerate(original_sequence)}
    refined_positions = {uid: index for index, uid in enumerate(refined_sequence)}
    moved_units = sorted(
        uid for uid in original_sequence
        if uid in refined_positions and original_positions[uid] != refined_positions[uid]
    )
    unauthorized_moves = [uid for uid in moved_units if not (op_index.get(uid, set()) & REORDER_OPERATIONS)]
    if unauthorized_moves:
        errors.append("unauthorized semantic reorder: " + ", ".join(unauthorized_moves))

    source_words = _words(original_text)
    refined_words = _words(refined_text)
    ratio = refined_words / max(source_words, 1)
    if source_words and ratio < 0.40:
        errors.append("overcompression below 0.40 word-ratio floor")
    if source_words and ratio > 1.35:
        errors.append("editorial expansion above 1.35 word-ratio ceiling")
    source_ops = set().union(*(op_index.get(uid, set()) for uid in original_order)) if original_order else set()
    if source_words and ratio > 1.05 and not (source_ops & EXPANSION_OPERATIONS):
        errors.append("editorial expansion lacks causal expansion operation")

    normalized_outputs = [_norm(obj.get("text")) for obj in refined_inventory.get("objects") or []]
    duplicates = sorted(text for text, count in Counter(normalized_outputs).items() if text and count > 1)
    if duplicates:
        errors.append("exact redundant refined paragraphs remain")

    source_density = len(source_units) / max(source_words, 1)
    refined_density = len(projected_by_id) / max(refined_words, 1)
    stages = [
        *list(execution_reticulum.get("stages") or []),
        {
            "stage": "REFINED_PROJECTION_RETICULUM",
            "digest": canonical_digest({
                "source_id": source_id,
                "refined_digest": text_digest(refined_text),
                "projection": projection,
                "structural_proof_digest": structural_proof.get("digest"),
            }),
            "compression_ratio": round(ratio, 6),
            "merge_groups": merge_groups,
            "split_units": sorted(split_units),
            "moved_units": moved_units,
        },
    ]
    payload = {
        "schema": REFINEMENT_SCHEMA,
        "profile": PROFILE,
        "claim_scope": CLAIM_SCOPE,
        "quality_target": QUALITY_TARGET,
        "scientific_truth_claim": False,
        "journal_acceptance_claim": False,
        "source_id": str(source_id),
        "source_inventory_digest": str(candidate_inv.get("digest") or ""),
        "refined_digest": text_digest(refined_text),
        "refined_inventory_digest": str(refined_inventory.get("digest") or ""),
        "plan_digest": str(plan.get("digest") or ""),
        "execution_reticulum_digest": str(execution_reticulum.get("digest") or ""),
        "structural_proof_digest": str(structural_proof.get("digest") or ""),
        "projection": dict(projection or {}),
        "source_word_count": source_words,
        "refined_word_count": refined_words,
        "compression_ratio": round(ratio, 6),
        "compression_gain": round(1.0 - ratio, 6),
        "source_semantic_density": round(source_density, 6),
        "refined_semantic_density": round(refined_density, 6),
        "merge_groups": merge_groups,
        "split_units": sorted(split_units),
        "moved_units": moved_units,
        "duplicate_refined_paragraph_count": len(duplicates),
        "stages": stages,
        "quality_band": "A_LEVEL_EDITORIAL_READY" if not errors else "NOT_READY",
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def verify_editorial_refinement_proof(
    state: Any,
    *,
    source_id: str,
    refined_text: str,
    structural_proof: dict[str, Any],
    execution_reticulum: dict[str, Any],
    proof: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    if not proof:
        return False, ["editorial refinement proof missing"]
    expected = build_editorial_refinement_proof(
        state,
        source_id=source_id,
        refined_text=refined_text,
        projection=dict(proof.get("projection") or {}),
        structural_proof=structural_proof,
        execution_reticulum=execution_reticulum,
    )
    errors: list[str] = []
    for key in (
        "schema", "profile", "claim_scope", "quality_target", "scientific_truth_claim",
        "journal_acceptance_claim", "source_id", "source_inventory_digest", "refined_digest",
        "refined_inventory_digest", "plan_digest", "execution_reticulum_digest",
        "structural_proof_digest", "source_word_count", "refined_word_count", "compression_ratio",
        "compression_gain", "source_semantic_density", "refined_semantic_density", "merge_groups",
        "split_units", "moved_units", "duplicate_refined_paragraph_count", "stages", "quality_band",
        "status", "errors",
    ):
        if proof.get(key) != expected.get(key):
            errors.append(f"editorial refinement proof {key} mismatch")
    digest = canonical_digest({k: v for k, v in proof.items() if k != "digest"})
    if proof.get("digest") != digest:
        errors.append("editorial refinement proof digest mismatch")
    if expected.get("status") != "PASS":
        errors.extend(expected.get("errors") or ["editorial refinement proof is not PASS"])
    return not errors, list(dict.fromkeys(errors))
