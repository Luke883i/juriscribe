from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SESSION_INTEGRITY_SCHEMA = "juriscribe-session-integrity/v1"
CANONICAL_FILENAME = "session.integrity.json"
LEGACY_FILENAME = "node.h"


def _digest(value: Any) -> str:
    """Return the canonical SHA-256 used by session integrity bindings."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def integrity_bindings(state: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic, corpus-free bindings for the current session state."""
    drafts = state.get("drafts", [])
    current = drafts[-1].get("digest", "") if drafts else ""
    bibliography = state.get("bibliography", {})
    reticulum = state.get("reticulum", {})
    generation = state.get("generation_contract", {})
    admission = state.get("admission", {})
    return {
        "session_id": str(state.get("session_id", "")),
        "phase": str(state.get("phase", "")),
        "ready": bool((state.get("completion") or {}).get("eligible")),
        "corpus_sha256": _digest(state.get("corpus", [])),
        "sources_sha256": _digest(state.get("sources", [])),
        "claims_sha256": _digest(state.get("claim_ledger", [])),
        "source_intelligence_sha256": _digest(state.get("source_intelligence", {})),
        "reticulum_sha256": str(reticulum.get("digest", "")),
        "setup_sha256": _digest((state.get("setup") or {}).get("accepted", {})),
        "dod_sha256": _digest(state.get("dod", [])),
        "generation_contract_sha256": str(generation.get("contract_digest", "")),
        "continuation_sha256": _digest(state.get("continuation", {})),
        "current_candidate_sha256": str(current),
        "review_sha256": _digest(state.get("review", {})),
        "final_review_sha256": _digest(state.get("final_review", {})),
        "provenance_sha256": _digest(state.get("provenance", {})),
        "interaction_sha256": _digest(state.get("interaction", {})),
        "bootstrap_sha256": _digest(admission.get("bootstrap", {})),
        "bibliography_sha256": str(bibliography.get("digest", _digest([]))),
        "simulation_sha256": _digest(state.get("simulations", {})),
        "compression_sha256": _digest(state.get("compression", {})),
        "quality_sha256": _digest(state.get("quality", {})),
        "benchmark_sha256": _digest(state.get("benchmark", {})),
        "artifacts_sha256": _digest(state.get("artifacts", [])),
    }


def integrity_record(state: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical JSON manifest.

    The manifest stores only metadata, booleans, paths and digests. It never
    serializes legal corpus text or hidden model reasoning.
    """
    return {
        "schema": SESSION_INTEGRITY_SCHEMA,
        "kind": "session_integrity_manifest",
        "bindings": integrity_bindings(state),
        "paths": {"state": "state.json", "ledger": "ledger", "artifacts": "artifacts"},
        "legacy_projection": {
            "path": LEGACY_FILENAME,
            "format": "c-preprocessor-header",
            "status": "DEPRECATED_COMPATIBILITY",
            "note": "node.h is a compatibility projection, not Node.js and not node.s",
        },
    }


def render_session_integrity(state: dict[str, Any]) -> str:
    return json.dumps(integrity_record(state), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_session_integrity(state: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_session_integrity(state), encoding="utf-8")
    return out


def parse_session_integrity(text: str) -> dict[str, Any]:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("session integrity manifest must be a JSON object")
    return value


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    out: dict[str, Any] = {}
    for key in sorted(value):
        path = f"{prefix}.{key}" if prefix else key
        item = value[key]
        if isinstance(item, dict):
            out.update(_flatten(item, path))
        else:
            out[path] = item
    return out


def validate_session_integrity(state: dict[str, Any], text: str) -> tuple[bool, list[str]]:
    try:
        parsed = parse_session_integrity(text)
    except (json.JSONDecodeError, ValueError) as exc:
        return False, [f"{CANONICAL_FILENAME} invalid JSON: {exc}"]
    expected = integrity_record(state)
    actual_flat = _flatten(parsed)
    expected_flat = _flatten(expected)
    errors: list[str] = []
    for key in sorted(expected_flat):
        if key not in actual_flat:
            errors.append(f"{CANONICAL_FILENAME} missing field: {key}")
        elif actual_flat[key] != expected_flat[key]:
            errors.append(f"{CANONICAL_FILENAME} {key} mismatch")
    unexpected = sorted(set(actual_flat) - set(expected_flat))
    if unexpected:
        errors.append(f"{CANONICAL_FILENAME} unexpected fields: " + ", ".join(unexpected))
    return not errors, errors
