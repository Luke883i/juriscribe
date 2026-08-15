from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\wÀ-ÿ]+", " ", (value or "").lower())).strip()


def assess_bibliography(entries: list[dict[str, Any]] | None, sources: list[dict[str, Any]], claims: list[dict[str, Any]]) -> dict[str, Any]:
    entries = list(entries or [])
    if not entries:
        return {
            "available": False,
            "entries": [],
            "entry_count": 0,
            "used_source_count": 0,
            "mapped_used_source_count": 0,
            "coverage": 1.0,
            "duplicates": [],
            "unresolved_used_source_ids": [],
            "status": "NOT_AVAILABLE",
            "digest": canonical_digest([]),
        }
    ids = [str(e.get("id", "")).strip() for e in entries]
    duplicates: list[str] = []
    seen_ids: set[str] = set()
    for eid in ids:
        if not eid:
            duplicates.append("<missing-id>")
        elif eid in seen_ids:
            duplicates.append(eid)
        seen_ids.add(eid)
    normalized: dict[str, list[str]] = {}
    for e in entries:
        key = _norm(str(e.get("citation", "")))
        if key:
            normalized.setdefault(key, []).append(str(e.get("id", "")))
    duplicates.extend("/".join(v) for v in normalized.values() if len(v) > 1)
    by_source = {str(e.get("source_id")): e for e in entries if e.get("source_id")}
    used_source_ids = sorted({sid for claim in claims if claim.get("material", True) for sid in claim.get("support_source_ids", [])})
    mapped = [sid for sid in used_source_ids if sid in by_source]
    unresolved = [sid for sid in used_source_ids if sid not in by_source]
    source_map = {s.get("id"): s for s in sources}
    unverified_used = [sid for sid in mapped if not source_map.get(sid, {}).get("direct_read") or not source_map.get(sid, {}).get("verified_at")]
    errors: list[str] = []
    if duplicates:
        errors.append("bibliography contains duplicate or missing identifiers")
    if unresolved:
        errors.append("bibliography does not map all sources used by material claims")
    if unverified_used:
        errors.append("bibliography maps material claim sources that are not verified")
    for e in entries:
        if not str(e.get("citation", "")).strip():
            errors.append(f"bibliography entry {e.get('id', 'UNKNOWN')} has empty citation")
    coverage = len(mapped) / max(len(used_source_ids), 1) if used_source_ids else 1.0
    payload = {
        "available": True,
        "entries": entries,
        "entry_count": len(entries),
        "used_source_count": len(used_source_ids),
        "mapped_used_source_count": len(mapped),
        "coverage": round(coverage, 4),
        "duplicates": sorted(set(duplicates)),
        "unresolved_used_source_ids": unresolved,
        "unverified_used_source_ids": unverified_used,
        "status": "PASS" if not errors else "GAPS_OPEN",
        "errors": errors,
    }
    payload["digest"] = canonical_digest(payload)
    return payload


def bibliography_gate(record: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not record or record.get("status") == "NOT_AVAILABLE":
        return True, []
    errors = list(record.get("errors", []))
    if record.get("status") != "PASS":
        errors.append("bibliography status is not PASS")
    if float(record.get("coverage", 0.0)) < 1.0:
        errors.append("bibliography does not cover every source used by material claims")
    return not errors, list(dict.fromkeys(errors))
