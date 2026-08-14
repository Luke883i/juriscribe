from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .epistemic import ALLOWED_KINDS, ALLOWED_RELATIONS, MATERIAL_KINDS


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReticulumReport:
    status: str
    digest: str
    node_count: int
    relation_count: int
    material_count: int
    material_locator_coverage: float
    connected_material_coverage: float
    source_coverage: float
    cross_chapter_relations: int
    contradiction_relations: int
    errors: list[str]
    warnings: list[str]

    def record(self) -> dict[str, Any]:
        return asdict(self)


def validate_reticulum(units: list[dict[str, Any]], relations: list[dict[str, Any]], *, source_ids: set[str]) -> ReticulumReport:
    errors: list[str] = []
    warnings: list[str] = []
    ids = [u.get("id") for u in units]
    if len(ids) != len(set(ids)):
        errors.append("epistemic unit ids are not unique")
    if len(units) < 3:
        errors.append("reticulum requires at least three epistemic units")
    if not relations:
        errors.append("reticulum requires at least one typed relation")
    by_id = {u.get("id"): u for u in units if u.get("id")}
    material = []
    located = 0
    used_sources: set[str] = set()
    for u in units:
        kind = u.get("kind")
        if kind not in ALLOWED_KINDS:
            errors.append(f"unsupported epistemic kind: {kind}")
        sid = u.get("source_id")
        if sid not in source_ids:
            errors.append(f"unit {u.get('id')} references unknown source {sid}")
        else:
            used_sources.add(sid)
        is_material = bool(u.get("material", True)) and kind in MATERIAL_KINDS
        if is_material:
            material.append(u)
            if str(u.get("source_locator", "")).strip():
                located += 1
            else:
                errors.append(f"material unit {u.get('id')} has no source locator")
    incident: set[str] = set()
    cross = 0
    contradictions = 0
    for r in relations:
        pred = r.get("predicate")
        if pred not in ALLOWED_RELATIONS:
            errors.append(f"unsupported relation: {pred}")
        src, dst = r.get("source"), r.get("target")
        if src not in by_id or dst not in by_id:
            errors.append(f"relation endpoint missing: {src}->{dst}")
            continue
        incident.update((src, dst))
        if by_id[src].get("chapter") and by_id[dst].get("chapter") and by_id[src].get("chapter") != by_id[dst].get("chapter"):
            cross += 1
        if pred == "CONTRADICTS":
            contradictions += 1
    connected_material = sum(1 for u in material if u.get("id") in incident)
    if material and connected_material < len(material):
        warnings.append("one or more material epistemic units are isolated")
    locator_coverage = located / max(len(material), 1) if material else 0.0
    connected_coverage = connected_material / max(len(material), 1) if material else 0.0
    source_coverage = len(used_sources) / max(len(source_ids), 1) if source_ids else 0.0
    if material and connected_coverage < 0.70:
        errors.append("connected material coverage below 0.70")
    if material and locator_coverage < 1.0:
        errors.append("material source-locator coverage below 1.0")
    normalized = {
        "units": sorted(units, key=lambda x: str(x.get("id"))),
        "relations": sorted(relations, key=lambda x: (str(x.get("source")), str(x.get("predicate")), str(x.get("target")))),
    }
    digest = canonical_digest(normalized)
    status = "PASS" if not errors else "FAIL"
    return ReticulumReport(status, digest, len(units), len(relations), len(material), round(locator_coverage, 4), round(connected_coverage, 4), round(source_coverage, 4), cross, contradictions, errors, warnings)


def build_generation_contract(reticulum: dict[str, Any], setup: dict[str, Any], units: list[dict[str, Any]], relations: list[dict[str, Any]]) -> dict[str, Any]:
    if reticulum.get("status") != "PASS":
        raise ValueError("validated reticulum required")
    if setup.get("status") != "ACCEPTED":
        raise ValueError("accepted setup required")
    preserve = [u["id"] for u in units if u.get("kind") in {"DEFINITION", "RULE", "EXCEPTION", "QUALIFICATION"} or "preserve" in u.get("tags", [])]
    develop = [u["id"] for u in units if u.get("kind") in {"OPEN_ISSUE", "QUESTION"} or "develop" in u.get("tags", [])]
    avoid_duplicate = [u["id"] for u in units if u.get("kind") in {"CLAIM", "CONCLUSION"} and "repeat_ok" not in u.get("tags", [])]
    by_id = {u.get("id"): u for u in units}
    cross_relations = [r for r in relations if r.get("predicate") in {"ANTICIPATES", "RECALLS", "DEVELOPS", "DEPENDS_ON", "DISTINGUISHES"} and by_id.get(r.get("source"), {}).get("chapter") and by_id.get(r.get("target"), {}).get("chapter") and by_id[r["source"]].get("chapter") != by_id[r["target"]].get("chapter")]
    setup_digest = canonical_digest(setup.get("accepted", {}))
    payload = {
        "reticulum_digest": reticulum["digest"],
        "setup_digest": setup_digest,
        "preserve_unit_ids": sorted(set(preserve)),
        "develop_unit_ids": sorted(set(develop)),
        "avoid_duplicate_unit_ids": sorted(set(avoid_duplicate)),
        "cross_chapter_relations": cross_relations,
    }
    payload["contract_digest"] = canonical_digest(payload)
    payload["status"] = "READY"
    return payload


def generation_contract_valid(contract: dict[str, Any] | None, reticulum: dict[str, Any], setup: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not contract or contract.get("status") != "READY":
        return False, ["generation contract missing or not READY"]
    if contract.get("reticulum_digest") != reticulum.get("digest"):
        errors.append("generation contract bound to stale reticulum")
    if contract.get("setup_digest") != canonical_digest(setup.get("accepted", {})):
        errors.append("generation contract bound to stale setup")
    return not errors, errors
