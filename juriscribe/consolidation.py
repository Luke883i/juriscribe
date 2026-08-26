from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any

PROFILE = "JURISCRIBE_COMPRESSION_CONSOLIDATION_V1"
INVENTORY_SCHEMA = "juriscribe-lossless-object-inventory/v1"
RETICULUM_SCHEMA = "juriscribe-consolidation-reticulum/v1"
PLAN_SCHEMA = "juriscribe-refactoring-contract/v1"
MUTATION_SCHEMA = "juriscribe-consolidation-mutation-receipt/v1"
SATURATION_SCHEMA = "juriscribe-consolidation-saturation/v1"
CALIBRATION_SCHEMA = "juriscribe-user-calibration/v1"

CANONICAL_ROLE = "canonical_material"
CANDIDATE_ROLE = "candidate_material"
ALLOWED_ROLES = {CANONICAL_ROLE, CANDIDATE_ROLE}

ALLOWED_OPERATIONS = {
    "KEEP", "MOVE", "MERGE_REDUNDANCY", "SPLIT", "CLARIFY", "QUALIFY",
    "BRIDGE", "REORDER", "NORMALIZE_TERMINOLOGY", "LOCAL_REWRITE",
}

REQUIRED_MUTATION_FAMILIES = {
    "LOSSLESSNESS", "CANONICAL_IMMUTABILITY", "RETICULUM", "GAP_EVIDENCE",
    "ARGUMENT_STRENGTH", "LOCAL_PROGRESSION", "RETICULAR_PROGRESSION",
    "ANOMALY_EDGE", "MINIMALITY", "MATERIALIZATION_READINESS",
}


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def inventory_set_digest(inventories: list[dict[str, Any]]) -> str:
    """Bind downstream evidence to the exact set of inventoried source revisions."""
    rows = sorted(
        (
            str(inv.get("source_id") or ""),
            str(inv.get("role") or ""),
            str(inv.get("digest") or ""),
        )
        for inv in inventories
    )
    return canonical_digest(rows)


def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _paragraph_spans(text: str) -> list[tuple[int, int, str]]:
    """Return exact non-empty paragraph spans without normalizing source bytes."""
    src = str(text or "")
    if not src:
        return []
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for match in re.finditer(r"(?:\r?\n)[ \t]*(?:\r?\n)+", src):
        end = match.start()
        chunk = src[cursor:end]
        if chunk.strip():
            spans.append((cursor, end, chunk))
        cursor = match.end()
    tail = src[cursor:]
    if tail.strip():
        spans.append((cursor, len(src), tail))
    return spans


def build_lossless_inventory(text: str, *, source_id: str, role: str) -> dict[str, Any]:
    role = str(role or "").strip().lower()
    if role not in ALLOWED_ROLES:
        raise ValueError("consolidation material role must be canonical_material or candidate_material")
    src = str(text or "")
    objects: list[dict[str, Any]] = []
    for index, (start, end, exact) in enumerate(_paragraph_spans(src), 1):
        obj = {
            "id": f"OBJ-{source_id}-P{index:04d}",
            "source_id": str(source_id),
            "role": role,
            "kind": "PARAGRAPH",
            "ordinal": index,
            "locator": f"P{index}",
            "start": start,
            "end": end,
            "sha256": text_digest(exact),
            "text": exact,
        }
        obj["digest"] = canonical_digest({k: v for k, v in obj.items() if k != "digest"})
        objects.append(obj)
    payload = {
        "schema": INVENTORY_SCHEMA,
        "profile": PROFILE,
        "source_id": str(source_id),
        "role": role,
        "source_sha256": text_digest(src),
        "source_length": len(src),
        "object_count": len(objects),
        "objects": objects,
        "status": "PASS" if objects else "FAIL",
        "errors": [] if objects else ["material contains no inventoryable paragraph"],
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def validate_lossless_inventory(inventory: dict[str, Any], source_text: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    src = str(source_text or "")
    if inventory.get("schema") != INVENTORY_SCHEMA:
        errors.append("inventory schema mismatch")
    if inventory.get("status") != "PASS":
        errors.append("inventory status not PASS")
    if inventory.get("role") not in ALLOWED_ROLES:
        errors.append("inventory role invalid")
    if inventory.get("source_sha256") != text_digest(src):
        errors.append("inventory source digest mismatch")
    source_length = _safe_int(inventory.get("source_length", -1))
    if source_length != len(src):
        errors.append("inventory source length mismatch")
    objects = list(inventory.get("objects") or [])
    object_count = _safe_int(inventory.get("object_count", -1))
    if object_count != len(objects):
        errors.append("inventory object count mismatch")
    if not objects:
        errors.append("inventory contains no objects")
    seen_ids: set[str] = set()
    last_end = -1
    for obj in objects:
        oid = str(obj.get("id") or "")
        if not oid or oid in seen_ids:
            errors.append("inventory object ids must be unique and non-empty")
        seen_ids.add(oid)
        if str(obj.get("source_id") or "") != str(inventory.get("source_id") or ""):
            errors.append(f"inventory object source mismatch: {oid or '?'}")
        if str(obj.get("role") or "") != str(inventory.get("role") or ""):
            errors.append(f"inventory object role mismatch: {oid or '?'}")
        start = _safe_int(obj.get("start", -1))
        end = _safe_int(obj.get("end", -1))
        if start is None or end is None or start < 0 or end < start or end > len(src):
            errors.append(f"inventory bounds invalid: {oid or '?'}")
            continue
        if start < last_end:
            errors.append(f"inventory object spans overlap or regress: {oid or '?'}")
        last_end = end
        exact = src[start:end]
        if obj.get("text") != exact:
            errors.append(f"inventory text mismatch: {oid or '?'}")
        if obj.get("sha256") != text_digest(exact):
            errors.append(f"inventory hash mismatch: {oid or '?'}")
        expected_obj = canonical_digest({k: v for k, v in obj.items() if k != "digest"})
        if obj.get("digest") != expected_obj:
            errors.append(f"inventory object digest mismatch: {oid or '?'}")
    expected = canonical_digest({k: v for k, v in inventory.items() if k != "digest"})
    if inventory.get("digest") != expected:
        errors.append("inventory digest mismatch")
    return not errors, list(dict.fromkeys(errors))


def build_reference_method_profile(inventories: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = [i for i in inventories if i.get("role") == CANONICAL_ROLE]
    objects = [o for i in canonical for o in i.get("objects", [])]
    texts = [str(o.get("text") or "") for o in objects]
    words = re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'’-]+\b", "\n".join(texts), flags=re.UNICODE)
    connectors = Counter(
        token.lower()
        for token in re.findall(
            r"\b(?:tuttavia|pertanto|dunque|inoltre|peraltro|nondimeno|infatti|in sintesi|in conclusione)\b",
            "\n".join(texts),
            re.I,
        )
    )
    paragraph_lengths = [
        len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'’-]+\b", t, flags=re.UNICODE))
        for t in texts
    ]
    return {
        "profile": PROFILE,
        "canonical_source_count": len(canonical),
        "canonical_object_count": len(objects),
        "average_paragraph_words": round(sum(paragraph_lengths) / max(len(paragraph_lengths), 1), 3),
        "dominant_connectors": [x for x, _ in connectors.most_common(12)],
        "lexical_size": len(set(w.lower() for w in words)),
        "authority_claim": False,
        "status": "READY" if canonical else "NOT_AVAILABLE",
    }


def build_joint_reticulum(
    inventories: list[dict[str, Any]],
    semantic_units: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    source_roles: dict[str, str] = {}
    object_by_id: dict[str, dict[str, Any]] = {}
    for inv in inventories:
        source_id = str(inv.get("source_id") or "")
        role = str(inv.get("role") or "")
        if not source_id:
            errors.append("inventory source ids must be non-empty")
        elif source_id in source_roles:
            errors.append(f"duplicate inventory source id: {source_id}")
        else:
            source_roles[source_id] = role
        for obj in inv.get("objects", []) or []:
            oid = str(obj.get("id") or "")
            if not oid:
                errors.append("inventory object ids must be non-empty")
                continue
            if oid in object_by_id:
                errors.append(f"duplicate inventory object id: {oid}")
            else:
                object_by_id[oid] = obj

    object_ids = set(object_by_id)
    covered: set[str] = set()
    unit_ids: set[str] = set()
    for unit in semantic_units:
        uid = str(unit.get("id") or "")
        if not uid or uid in unit_ids:
            errors.append("semantic unit ids must be unique and non-empty")
        unit_ids.add(uid)
        oid = str(unit.get("object_id") or "")
        obj = object_by_id.get(oid)
        if obj is None:
            errors.append(f"semantic unit {uid or '?'} references unknown object")
        else:
            covered.add(oid)
        source_id = str(unit.get("source_id") or "")
        if source_id not in source_roles:
            errors.append(f"semantic unit {uid or '?'} references unknown source")
            expected_role = None
        else:
            expected_role = source_roles[source_id]
        material_role = str(unit.get("material_role") or "")
        if expected_role is not None and material_role != expected_role:
            errors.append(f"semantic unit {uid or '?'} material role mismatch")
        if obj is not None:
            if str(obj.get("source_id") or "") != source_id:
                errors.append(f"semantic unit {uid or '?'} object/source binding mismatch")
            if str(obj.get("role") or "") != material_role:
                errors.append(f"semantic unit {uid or '?'} object/role binding mismatch")

    cross_role = 0
    by_id = {str(u.get("id")): u for u in semantic_units if u.get("id")}
    for relation in relations:
        src, dst = str(relation.get("source") or ""), str(relation.get("target") or "")
        if src not in by_id or dst not in by_id:
            errors.append(f"relation endpoint missing: {src}->{dst}")
        elif by_id[src].get("material_role") != by_id[dst].get("material_role"):
            cross_role += 1

    coverage = len(covered) / max(len(object_ids), 1)
    if object_ids and coverage < 1.0:
        errors.append("lossless object coverage below 1.0")
    canonical_sources = {sid for sid, role in source_roles.items() if role == CANONICAL_ROLE}
    candidate_sources = {sid for sid, role in source_roles.items() if role == CANDIDATE_ROLE}
    if not candidate_sources:
        errors.append("at least one candidate material is required")
    payload = {
        "schema": RETICULUM_SCHEMA,
        "profile": PROFILE,
        "object_count": len(object_ids),
        "semantic_unit_count": len(semantic_units),
        "relation_count": len(relations),
        "object_coverage": round(coverage, 6),
        "cross_role_relations": cross_role,
        "canonical_source_ids": sorted(canonical_sources),
        "candidate_source_ids": sorted(candidate_sources),
        "inventories_digest": inventory_set_digest(inventories),
        "semantic_units_digest": canonical_digest(semantic_units),
        "relations_digest": canonical_digest(relations),
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def build_gap_map(
    candidate_units: list[dict[str, Any]],
    *,
    reference_profile: dict[str, Any],
    findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    supplied = list(findings or [])
    gaps: list[dict[str, Any]] = []
    for index, finding in enumerate(supplied, 1):
        gap = {
            "id": str(finding.get("id") or f"GAP-{index:04d}"),
            "unit_id": str(finding.get("unit_id") or ""),
            "kind": str(finding.get("kind") or "EDITORIAL").upper(),
            "severity": str(finding.get("severity") or "MATERIAL").upper(),
            "evidence": str(finding.get("evidence") or "").strip(),
            "reference": str(finding.get("reference") or reference_profile.get("profile") or PROFILE),
        }
        if gap["unit_id"] and any(str(u.get("id")) == gap["unit_id"] for u in candidate_units):
            gaps.append(gap)
    return gaps


def build_refactoring_contract(
    *,
    reticulum: dict[str, Any],
    candidate_units: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    if reticulum.get("status") != "PASS":
        errors.append("validated consolidation reticulum required")
    unit_ids = {str(u.get("id")) for u in candidate_units if u.get("id")}

    normalized_gaps: list[dict[str, Any]] = []
    gap_by_id: dict[str, dict[str, Any]] = {}
    for index, gap in enumerate(gaps, 1):
        gid = str(gap.get("id") or "")
        unit_id = str(gap.get("unit_id") or "")
        evidence = str(gap.get("evidence") or "").strip()
        normalized = {
            "id": gid,
            "unit_id": unit_id,
            "kind": str(gap.get("kind") or "EDITORIAL").upper(),
            "severity": str(gap.get("severity") or "MATERIAL").upper(),
            "evidence": evidence,
            "reference": str(gap.get("reference") or PROFILE),
        }
        if not gid:
            errors.append(f"gap {index} lacks stable id")
        elif gid in gap_by_id:
            errors.append(f"duplicate gap id: {gid}")
        else:
            gap_by_id[gid] = normalized
        if unit_id not in unit_ids:
            errors.append(f"gap {gid or index} targets unknown candidate unit: {unit_id}")
        if not evidence:
            errors.append(f"gap {gid or index} lacks evidence")
        normalized_gaps.append(normalized)

    normalized: list[dict[str, Any]] = []
    touched: set[str] = set()
    operation_ids: set[str] = set()
    bound_gap_ids: set[str] = set()
    for index, op in enumerate(operations, 1):
        operation_id = str(op.get("id") or "")
        operation = str(op.get("operation") or "").upper()
        unit_id = str(op.get("unit_id") or "")
        gap_ids = sorted({str(x) for x in op.get("gap_ids") or [] if str(x)})
        rationale = str(op.get("rationale") or "").strip()
        if not operation_id:
            errors.append(f"operation {index} lacks stable id")
        elif operation_id in operation_ids:
            errors.append(f"duplicate operation id: {operation_id}")
        operation_ids.add(operation_id)
        if operation not in ALLOWED_OPERATIONS:
            errors.append(f"unsupported operation: {operation}")
        if unit_id not in unit_ids:
            errors.append(f"operation targets unknown candidate unit: {unit_id}")
        if operation != "KEEP" and not gap_ids:
            errors.append(f"operation {index} lacks causal gap binding")
        if gap_ids and not rationale:
            errors.append(f"operation {index} with gap binding lacks rationale")
        for gid in gap_ids:
            gap = gap_by_id.get(gid)
            if gap is None:
                errors.append(f"operation {index} references unknown gap")
                continue
            bound_gap_ids.add(gid)
            if str(gap.get("unit_id") or "") != unit_id:
                errors.append(f"operation {index} is bound to a gap on a different unit")
        if operation != "KEEP":
            touched.add(unit_id)
        normalized.append({
            "id": operation_id,
            "unit_id": unit_id,
            "operation": operation,
            "gap_ids": gap_ids,
            "rationale": rationale,
            "expected_benefit": str(op.get("expected_benefit") or "").strip(),
            "degradation_risk": str(op.get("degradation_risk") or "").strip(),
        })

    unbound = set(gap_by_id) - bound_gap_ids
    if unbound:
        errors.append("gaps lack disposition: " + ", ".join(sorted(unbound)))

    payload = {
        "schema": PLAN_SCHEMA,
        "profile": PROFILE,
        "reticulum_digest": str(reticulum.get("digest") or ""),
        "candidate_unit_count": len(unit_ids),
        "candidate_units_digest": canonical_digest(candidate_units),
        "gap_count": len(normalized_gaps),
        "gaps": normalized_gaps,
        "gaps_digest": canonical_digest(normalized_gaps),
        "operations": normalized,
        "touched_unit_ids": sorted(touched),
        "touch_ratio": round(len(touched) / max(len(unit_ids), 1), 6),
        "minimality_policy": [
            "canonical_immutability", "semantic_recall_1.0", "relation_recall_1.0",
            "no_unsupported_novelty", "close_material_gaps", "minimize_touched_units",
            "minimize_transform_distance", "minimize_restructure",
        ],
        "status": "READY" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def validate_mutation_receipt(
    receipt: dict[str, Any], *, plan_digest: str, reticulum_digest: str
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if receipt.get("schema") != MUTATION_SCHEMA:
        errors.append("mutation receipt schema mismatch")
    if receipt.get("plan_digest") != plan_digest:
        errors.append("mutation receipt bound to stale plan")
    if receipt.get("reticulum_digest") != reticulum_digest:
        errors.append("mutation receipt bound to stale reticulum")
    cases = _safe_int(receipt.get("cases", 0))
    if cases is None or cases < 10_000_000:
        errors.append("at least 10,000,000 mutation instances required")
    families = set(map(str, receipt.get("families") or []))
    if not REQUIRED_MUTATION_FAMILIES.issubset(families):
        errors.append("mutation family coverage incomplete")
    failures = _safe_int(receipt.get("failures", 0))
    if failures is None or failures != 0:
        errors.append("mutation receipt contains unresolved failures")
    return not errors, list(dict.fromkeys(errors))


def validate_saturation_receipt(receipt: dict[str, Any], *, plan_digest: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if receipt.get("schema") != SATURATION_SCHEMA:
        errors.append("saturation schema mismatch")
    if receipt.get("plan_digest") != plan_digest:
        errors.append("saturation bound to stale plan")
    novelty = _safe_int(receipt.get("no_novelty_tail", 0))
    compression = _safe_int(receipt.get("no_better_compression_tail", 0))
    if novelty is None or novelty < 1000:
        errors.append("M+1000 genuine no-novelty tail required")
    if compression is None or compression < 1000:
        errors.append("N+1000 no-better-lossless-compression tail required")
    if receipt.get("semantic_recall") != 1.0:
        errors.append("semantic recall must be 1.0")
    if receipt.get("relation_recall") != 1.0:
        errors.append("relation recall must be 1.0")
    if receipt.get("canonical_unchanged") is not True:
        errors.append("canonical material must remain unchanged")
    return not errors, list(dict.fromkeys(errors))


def record_user_calibration(plan: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {
        "schema": CALIBRATION_SCHEMA,
        "profile": PROFILE,
        "plan_digest_before": str(plan.get("digest") or ""),
        "decisions": list(decisions or []),
        "material_change": any(bool(d.get("material", True)) for d in decisions or []),
    }
    payload["digest"] = canonical_digest(payload)
    return payload


def semantic_lossless_gate(
    *,
    before_unit_ids: list[str],
    after_unit_ids: list[str],
    before_relation_ids: list[str],
    after_relation_ids: list[str],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if len(set(before_unit_ids)) != len(before_unit_ids):
        errors.append("before semantic unit ids are not unique")
    if len(set(after_unit_ids)) != len(after_unit_ids):
        errors.append("after semantic unit ids are not unique")
    if len(set(before_relation_ids)) != len(before_relation_ids):
        errors.append("before relation ids are not unique")
    if len(set(after_relation_ids)) != len(after_relation_ids):
        errors.append("after relation ids are not unique")
    if set(before_unit_ids) - set(after_unit_ids):
        errors.append("material semantic units lost")
    if set(before_relation_ids) - set(after_relation_ids):
        errors.append("required semantic relations lost")
    return not errors, list(dict.fromkeys(errors))
