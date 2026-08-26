from __future__ import annotations

from typing import Any

from .consolidation import CANDIDATE_ROLE, build_lossless_inventory, canonical_digest, text_digest
from .semantic_proof import (
    SCHEMA as V1_SCHEMA,
    CLAIM_SCOPE,
    _candidate_before,
    _canonical_inventory_digest,
    _material,
    _norm,
    _relation_key,
    _required_relations,
    build_structural_semantic_proof as build_v1,
    verify_structural_semantic_proof as verify_v1,
)

SCHEMA = "juriscribe-structural-semantic-proof/v2"
PROFILE = "JURISCRIBE_PROOF_CARRYING_SEMANTICS_V2"


def _refs(unit: dict[str, Any]) -> list[str]:
    object_ids = unit.get("object_ids")
    if isinstance(object_ids, list) and object_ids:
        return [str(item) for item in object_ids if str(item)]
    object_id = str(unit.get("object_id") or "")
    return [object_id] if object_id else []


def _uses_multi_object(projection: dict[str, Any]) -> bool:
    return any(len(_refs(dict(unit))) > 1 for unit in (projection or {}).get("units", []))


def build_structural_semantic_proof(
    state: Any,
    *,
    source_id: str,
    refined_text: str,
    projection: dict[str, Any],
) -> dict[str, Any]:
    """v2 only widens output binding from one object to one-or-many objects.

    All non-split projections reuse v1 byte-for-byte semantics. This keeps the new
    surface minimal while making the already-allowed SPLIT refactoring operation
    representable without inventing new semantic unit ids.
    """
    if not _uses_multi_object(projection):
        return build_v1(
            state,
            source_id=source_id,
            refined_text=refined_text,
            projection=projection,
        )

    source_id = str(source_id or "").strip()
    refined_text = str(refined_text or "")
    errors: list[str] = []
    cc = (state.strategy or {}).get("consolidation") or {}
    plan = cc.get("refactoring_contract") or {}
    source = next(
        (
            item for item in (state.corpus or [])
            if str(item.get("source_id") or "") == source_id
            and str(item.get("role") or "") == CANDIDATE_ROLE
        ),
        None,
    )
    source_inventory = (cc.get("inventories") or {}).get(source_id) or {}
    if not source:
        errors.append("candidate source not found")
    if source_inventory.get("role") != CANDIDATE_ROLE:
        errors.append("candidate source inventory missing")
    if plan.get("status") != "READY":
        errors.append("current READY refactoring plan required")
    if (state.reticulum or {}).get("status") != "PASS":
        errors.append("current PASS reticulum required")

    before_units = _candidate_before(state, source_id)
    before_ids = {str(unit.get("id") or "") for unit in before_units if unit.get("id")}
    if not before_ids:
        errors.append("candidate has no material semantic units")
    if len(before_ids) != len(before_units):
        errors.append("candidate material semantic unit ids must be unique and non-empty")

    before_relations = _required_relations(state, before_ids)
    before_relation_map = {_relation_key(item): item for item in before_relations}
    if len(before_relation_map) != len(before_relations):
        errors.append("required relation ids/keys must be unique")

    refined_inventory = build_lossless_inventory(
        refined_text,
        source_id=source_id,
        role=CANDIDATE_ROLE,
    )
    if refined_inventory.get("status") != "PASS":
        errors.append("refined text has no inventoryable material")
    output_objects = {
        str(obj.get("id") or ""): obj
        for obj in (refined_inventory.get("objects") or [])
        if obj.get("id")
    }

    projected_units = [dict(unit) for unit in (projection or {}).get("units", [])]
    projected_relations = [dict(rel) for rel in (projection or {}).get("relations", [])]
    after_material = [unit for unit in projected_units if _material(unit)]
    after_ids = [str(unit.get("id") or "") for unit in after_material]
    if any(not uid for uid in after_ids) or len(set(after_ids)) != len(after_ids):
        errors.append("projected material semantic unit ids must be unique and non-empty")
    after_id_set = set(after_ids)

    lost_units = sorted(before_ids - after_id_set)
    new_units = sorted(after_id_set - before_ids)
    if lost_units:
        errors.append("material semantic units lost: " + ", ".join(lost_units))
    if new_units:
        errors.append("unsupported new material semantic units: " + ", ".join(new_units))

    before_by_id = {str(unit.get("id")): unit for unit in before_units if unit.get("id")}
    covered_objects: set[str] = set()
    multi_object_units: list[str] = []
    all_state_unit_ids = {str(unit.get("id") or "") for unit in (state.epistemic_units or []) if unit.get("id")}
    for unit in after_material:
        uid = str(unit.get("id") or "")
        if str(unit.get("source_id") or "") != source_id:
            errors.append(f"projected unit source mismatch: {uid or '?'}")
        if str(unit.get("material_role") or "") != CANDIDATE_ROLE:
            errors.append(f"projected unit role mismatch: {uid or '?'}")
        before = before_by_id.get(uid)
        if before and before.get("kind") and unit.get("kind") and unit.get("kind") != before.get("kind"):
            errors.append(f"projected unit kind changed: {uid}")
        refs = _refs(unit)
        if not refs:
            errors.append(f"projected unit output object binding missing: {uid or '?'}")
            continue
        if len(refs) != len(set(refs)):
            errors.append(f"projected unit output object bindings duplicated: {uid or '?'}")
        if len(refs) > 1:
            multi_object_units.append(uid)
        unknown = [oid for oid in refs if oid not in output_objects]
        if unknown:
            errors.append(f"projected unit references unknown refined object: {uid or '?'}")
            continue
        covered_objects.update(refs)
        witness = _norm(unit.get("text"))
        object_text = _norm(" ".join(str(output_objects[oid].get("text") or "") for oid in refs))
        if not witness:
            errors.append(f"projected unit text witness missing: {uid or '?'}")
        elif witness not in object_text and object_text not in witness:
            errors.append(f"projected unit text is not bound to refined object set: {uid or '?'}")

    object_coverage = len(covered_objects) / max(len(output_objects), 1)
    if output_objects and object_coverage < 1.0:
        errors.append("refined output object coverage below 1.0")

    after_relation_map: dict[str, dict[str, Any]] = {}
    for relation in projected_relations:
        if not _material(relation):
            continue
        key = _relation_key(relation)
        if key in after_relation_map:
            errors.append("projected material relation ids/keys must be unique")
        after_relation_map[key] = relation
        src = str(relation.get("source") or "")
        dst = str(relation.get("target") or "")
        if src not in (all_state_unit_ids | after_id_set) or dst not in (all_state_unit_ids | after_id_set):
            errors.append(f"projected relation endpoint missing: {src}->{dst}")

    before_relation_keys = set(before_relation_map)
    after_relation_keys = set(after_relation_map)
    lost_relations = sorted(before_relation_keys - after_relation_keys)
    new_relations = sorted(after_relation_keys - before_relation_keys)
    if lost_relations:
        errors.append("required semantic relations lost: " + ", ".join(lost_relations))
    if new_relations:
        errors.append("unsupported new material semantic relations: " + ", ".join(new_relations))

    unit_recall = len(before_ids & after_id_set) / max(len(before_ids), 1)
    relation_recall = len(before_relation_keys & after_relation_keys) / max(len(before_relation_keys), 1) if before_relation_keys else 1.0
    payload = {
        "schema": SCHEMA,
        "profile": PROFILE,
        "claim_scope": CLAIM_SCOPE,
        "semantic_truth_claim": False,
        "legal_entailment_claim": False,
        "source_id": source_id,
        "source_digest": str((source or {}).get("digest") or ""),
        "source_inventory_digest": str(source_inventory.get("digest") or ""),
        "refined_digest": text_digest(refined_text),
        "refined_inventory_digest": str(refined_inventory.get("digest") or ""),
        "plan_digest": str(plan.get("digest") or ""),
        "reticulum_digest": str((state.reticulum or {}).get("digest") or ""),
        "canonical_inventory_set_digest": _canonical_inventory_digest(state),
        "projection": {"units": projected_units, "relations": projected_relations},
        "projection_digest": canonical_digest({"units": projected_units, "relations": projected_relations}),
        "object_binding_mode": "ONE_OR_MANY",
        "multi_object_unit_ids": sorted(multi_object_units),
        "before_material_unit_count": len(before_ids),
        "after_material_unit_count": len(after_id_set),
        "required_relation_count": len(before_relation_keys),
        "after_material_relation_count": len(after_relation_keys),
        "output_object_count": len(output_objects),
        "output_object_coverage": round(object_coverage, 6),
        "structural_unit_recall": round(unit_recall, 6),
        "structural_relation_recall": round(relation_recall, 6),
        "lost_material_unit_ids": lost_units,
        "unsupported_new_material_unit_ids": new_units,
        "lost_required_relation_keys": lost_relations,
        "unsupported_new_relation_keys": new_relations,
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    payload["digest"] = canonical_digest({key: value for key, value in payload.items() if key != "digest"})
    return payload


def verify_structural_semantic_proof(
    state: Any,
    *,
    source_id: str,
    refined_text: str,
    proof: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    if not proof:
        return False, ["structural semantic proof missing"]
    if proof.get("schema") == V1_SCHEMA:
        return verify_v1(
            state,
            source_id=source_id,
            refined_text=refined_text,
            proof=proof,
        )
    if proof.get("schema") != SCHEMA:
        return False, ["structural semantic proof schema mismatch"]
    expected = build_structural_semantic_proof(
        state,
        source_id=source_id,
        refined_text=refined_text,
        projection=dict(proof.get("projection") or {}),
    )
    errors: list[str] = []
    for key in (
        "schema", "profile", "claim_scope", "semantic_truth_claim", "legal_entailment_claim",
        "source_id", "source_digest", "source_inventory_digest", "refined_digest",
        "refined_inventory_digest", "plan_digest", "reticulum_digest",
        "canonical_inventory_set_digest", "projection_digest", "object_binding_mode",
        "multi_object_unit_ids", "before_material_unit_count", "after_material_unit_count",
        "required_relation_count", "after_material_relation_count", "output_object_count",
        "output_object_coverage", "structural_unit_recall", "structural_relation_recall",
        "lost_material_unit_ids", "unsupported_new_material_unit_ids",
        "lost_required_relation_keys", "unsupported_new_relation_keys", "status", "errors",
    ):
        if proof.get(key) != expected.get(key):
            errors.append(f"structural semantic proof {key} mismatch")
    digest = canonical_digest({key: value for key, value in proof.items() if key != "digest"})
    if proof.get("digest") != digest:
        errors.append("structural semantic proof digest mismatch")
    if expected.get("status") != "PASS":
        errors.extend(expected.get("errors") or ["structural semantic proof is not PASS"])
    return not errors, list(dict.fromkeys(errors))
