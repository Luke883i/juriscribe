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


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


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
    if inventory.get("schema") != INVENTORY_SCHEMA: errors.append("inventory schema mismatch")
    if inventory.get("source_sha256") != text_digest(src): errors.append("inventory source digest mismatch")
    if int(inventory.get("source_length", -1)) != len(src): errors.append("inventory source length mismatch")
    objects = list(inventory.get("objects") or [])
    if int(inventory.get("object_count", -1)) != len(objects): errors.append("inventory object count mismatch")
    for obj in objects:
        start, end = int(obj.get("start", -1)), int(obj.get("end", -1))
        if start < 0 or end < start or end > len(src):
            errors.append(f"inventory bounds invalid: {obj.get('id')}")
            continue
        exact = src[start:end]
        if obj.get("text") != exact: errors.append(f"inventory text mismatch: {obj.get('id')}")
        if obj.get("sha256") != text_digest(exact): errors.append(f"inventory hash mismatch: {obj.get('id')}")
    expected = canonical_digest({k: v for k, v in inventory.items() if k != "digest"})
    if inventory.get("digest") != expected: errors.append("inventory digest mismatch")
    return not errors, list(dict.fromkeys(errors))


def build_reference_method_profile(inventories: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = [i for i in inventories if i.get("role") == CANONICAL_ROLE]
    objects = [o for i in canonical for o in i.get("objects", [])]
    texts = [str(o.get("text") or "") for o in objects]
    words = re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'’-]+\b", "\n".join(texts), flags=re.UNICODE)
    connectors = Counter(
        token.lower() for token in re.findall(r"\b(?:tuttavia|pertanto|dunque|inoltre|peraltro|nondimeno|infatti|in sintesi|in conclusione)\b", "\n".join(texts), re.I)
    )
    paragraph_lengths = [len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'’-]+\b", t, flags=re.UNICODE)) for t in texts]
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
    object_ids = {str(o.get("id")) for inv in inventories for o in inv.get("objects", []) if o.get("id")}
    source_roles = {str(inv.get("source_id")): str(inv.get("role")) for inv in inventories}
    errors: list[str] = []
    covered: set[str] = set()
    unit_ids: set[str] = set()
    for unit in semantic_units:
        uid = str(unit.get("id") or "")
        if not uid or uid in unit_ids: errors.append("semantic unit ids must be unique and non-empty")
        unit_ids.add(uid)
        oid = str(unit.get("object_id") or "")
        if oid not in object_ids: errors.append(f"semantic unit {uid or '?'} references unknown object")
        else: covered.add(oid)
        source_id = str(unit.get("source_id") or "")
        expected_role = source_roles.get(source_id)
        if expected_role and str(unit.get("material_role") or "") != expected_role:
            errors.append(f"semantic unit {uid or '?'} material role mismatch")
    cross_role = 0
    by_id = {str(u.get("id")): u for u in semantic_units if u.get("id")}
    for relation in relations:
        src, dst = str(relation.get("source") or ""), str(relation.get("target") or "")
        if src not in by_id or dst not in by_id: errors.append(f"relation endpoint missing: {src}->{dst}")
        elif by_id[src].get("material_role") != by_id[dst].get("material_role"): cross_role += 1
    coverage = len(covered) / max(len(object_ids), 1)
    if object_ids and coverage < 1.0: errors.append("lossless object coverage below 1.0")
    canonical_sources = {sid for sid, role in source_roles.items() if role == CANONICAL_ROLE}
    candidate_sources = {sid for sid, role in source_roles.items() if role == CANDIDATE_ROLE}
    if not candidate_sources: errors.append("at least one candidate material is required")
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
    if reticulum.get("status") != "PASS": errors.append("validated consolidation reticulum required")
    unit_ids = {str(u.get("id")) for u in candidate_units if u.get("id")}
    gap_by_id = {str(g.get("id")): g for g in gaps if g.get("id")}
    normalized: list[dict[str, Any]] = []
    touched: set[str] = set()
    for index, op in enumerate(operations, 1):
        operation = str(op.get("operation") or "").upper()
        unit_id = str(op.get("unit_id") or "")
        gap_ids = sorted({str(x) for x in op.get("gap_ids") or [] if str(x)})
        rationale = str(op.get("rationale") or "").strip()
        if operation not in ALLOWED_OPERATIONS: errors.append(f"unsupported operation: {operation}")
        if unit_id not in unit_ids: errors.append(f"operation targets unknown candidate unit: {unit_id}")
        if operation != "KEEP" and not gap_ids: errors.append(f"operation {index} lacks causal gap binding")
        if any(gid not in gap_by_id for gid in gap_ids): errors.append(f"operation {index} references unknown gap")
        if operation != "KEEP" and not rationale: errors.append(f"operation {index} lacks rationale")
        if operation != "KEEP": touched.add(unit_id)
        normalized.append({
            "id": str(op.get("id") or f"OP-{index:04d}"),
            "unit_id": unit_id,
            "operation": operation,
            "gap_ids": gap_ids,
            "rationale": rationale,
            "expected_benefit": str(op.get("expected_benefit") or "").strip(),
            "degradation_risk": str(op.get("degradation_risk") or "").strip(),
        })
    payload = {
        "schema": PLAN_SCHEMA,
        "profile": PROFILE,
        "reticulum_digest": str(reticulum.get("digest") or ""),
        "candidate_unit_count": len(unit_ids),
        "gap_count": len(gaps),
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


def validate_mutation_receipt(receipt: dict[str, Any], *, plan_digest: str, reticulum_digest: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if receipt.get("schema") != MUTATION_SCHEMA: errors.append("mutation receipt schema mismatch")
    if receipt.get("plan_digest") != plan_digest: errors.append("mutation receipt bound to stale plan")
    if receipt.get("reticulum_digest") != reticulum_digest: errors.append("mutation receipt bound to stale reticulum")
    if int(receipt.get("cases", 0)) < 10_000_000: errors.append("at least 10,000,000 mutation instances required")
    families = set(map(str, receipt.get("families") or []))
    required = {
        "LOSSLESSNESS", "CANONICAL_IMMUTABILITY", "RETICULUM", "GAP_EVIDENCE",
        "ARGUMENT_STRENGTH", "LOCAL_PROGRESSION", "RETICULAR_PROGRESSION",
        "ANOMALY_EDGE", "MINIMALITY", "MATERIALIZATION_READINESS",
    }
    if not required.issubset(families): errors.append("mutation family coverage incomplete")
    if int(receipt.get("failures", 0)) != 0: errors.append("mutation receipt contains unresolved failures")
    return not errors, list(dict.fromkeys(errors))


def validate_saturation_receipt(receipt: dict[str, Any], *, plan_digest: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if receipt.get("schema") != SATURATION_SCHEMA: errors.append("saturation schema mismatch")
    if receipt.get("plan_digest") != plan_digest: errors.append("saturation bound to stale plan")
    if int(receipt.get("no_novelty_tail", 0)) < 1000: errors.append("M+1000 genuine no-novelty tail required")
    if int(receipt.get("no_better_compression_tail", 0)) < 1000: errors.append("N+1000 no-better-lossless-compression tail required")
    if receipt.get("semantic_recall") != 1.0: errors.append("semantic recall must be 1.0")
    if receipt.get("relation_recall") != 1.0: errors.append("relation recall must be 1.0")
    if receipt.get("canonical_unchanged") is not True: errors.append("canonical material must remain unchanged")
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
    if set(before_unit_ids) - set(after_unit_ids): errors.append("material semantic units lost")
    if set(before_relation_ids) - set(after_relation_ids): errors.append("required semantic relations lost")
    return not errors, errors
