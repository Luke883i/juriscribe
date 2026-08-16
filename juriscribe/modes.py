from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "juriscribe-mode-contract/v1"
CONTINUATION = "CONTINUATION"
GREENFIELD = "GREENFIELD"
REVIEW = "REVIEW"
MODES = (CONTINUATION, GREENFIELD, REVIEW)
REVIEW_OUTPUTS = {"REPORT_ONLY", "REPORT_AND_REVISED_TEXT"}

COMMON_FINAL_ARTIFACT_ROLES = {
    "evidence_dossier",
    "source_register",
    "inference_register",
    "transformation_ledger",
    "session_dashboard",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_mode(mode: str | None) -> str:
    value = str(mode or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "CONTINUE": CONTINUATION,
        "CONTINUAZIONE": CONTINUATION,
        "CHAPTER_CONTINUATION": CONTINUATION,
        "EX_NOVO": GREENFIELD,
        "NEW": GREENFIELD,
        "NUOVO": GREENFIELD,
        "GREEN_FIELD": GREENFIELD,
        "REVISION": REVIEW,
        "REVISIONE": REVIEW,
        "AUDIT": REVIEW,
    }
    value = aliases.get(value, value)
    if value not in MODES:
        raise ValueError("mode must be CONTINUATION, GREENFIELD or REVIEW")
    return value


def review_output(setup: dict[str, Any] | None) -> str:
    accepted = (setup or {}).get("accepted", setup or {})
    value = str(accepted.get("review_output", "REPORT_ONLY")).upper()
    return value if value in REVIEW_OUTPUTS else "REPORT_ONLY"


def mode_spec(mode: str, setup: dict[str, Any] | None = None) -> dict[str, Any]:
    mode = normalize_mode(mode)
    if mode == CONTINUATION:
        return {"mode": mode, "seed_required": True, "concept_required": False, "review_target_required": False, "generation_required": True, "continuation_required": True, "revision_required": True, "compression_required": True, "simulation_required": True, "quality_must_pass": True, "source_coverage_must_close": True, "primary_artifact_role": "final_chapter", "input_role": "preceding_chapter"}
    if mode == GREENFIELD:
        return {"mode": mode, "seed_required": False, "concept_required": True, "review_target_required": False, "generation_required": True, "continuation_required": False, "revision_required": True, "compression_required": True, "simulation_required": True, "quality_must_pass": True, "source_coverage_must_close": True, "primary_artifact_role": "final_legal_text", "input_role": "concept_source"}
    output = review_output(setup)
    revised = output == "REPORT_AND_REVISED_TEXT"
    return {"mode": REVIEW, "seed_required": False, "concept_required": False, "review_target_required": True, "generation_required": False, "continuation_required": False, "revision_required": revised, "compression_required": False, "simulation_required": False, "quality_must_pass": revised, "source_coverage_must_close": revised, "primary_artifact_role": "review_report", "secondary_artifact_role": "revised_legal_text" if revised else "", "input_role": "review_target", "review_output": output}


def required_artifact_roles(mode: str, setup: dict[str, Any] | None = None) -> set[str]:
    spec = mode_spec(mode, setup)
    roles = set(COMMON_FINAL_ARTIFACT_ROLES)
    roles.add(spec["primary_artifact_role"])
    if spec.get("secondary_artifact_role"):
        roles.add(str(spec["secondary_artifact_role"]))
    if spec["mode"] == REVIEW:
        roles.add("review_findings_register")
    return roles


def mode_selection_record(mode: str, *, request: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_mode(mode)
    payload = {"schema": "juriscribe-mode-selection/v1", "mode": normalized, "request_digest": canonical_digest(request or {}), "status": "SELECTED"}
    payload["digest"] = canonical_digest(payload)
    return payload


def _target_digest(mode: str, corpus: list[dict[str, Any]]) -> str:
    role = mode_spec(mode)["input_role"]
    matches = [str(c.get("digest", "")) for c in corpus if c.get("role") == role and c.get("digest")]
    if mode == CONTINUATION:
        return canonical_digest(matches)
    return matches[-1] if matches else ""


def build_mode_contract(mode: str, *, request: dict[str, Any], corpus: list[dict[str, Any]], reticulum: dict[str, Any], setup: dict[str, Any], editorial_standard: dict[str, Any], generation_contract: dict[str, Any] | None = None) -> dict[str, Any]:
    mode = normalize_mode(mode)
    spec = mode_spec(mode, setup)
    errors: list[str] = []
    if reticulum.get("status") != "PASS": errors.append("validated reticulum required")
    if setup.get("status") != "ACCEPTED": errors.append("accepted setup required")
    if editorial_standard.get("status") != "READY": errors.append("editorial standard must be READY")
    target = _target_digest(mode, corpus)
    if spec["seed_required"] and not any(c.get("role") == "preceding_chapter" for c in corpus): errors.append("continuation mode requires preceding chapters")
    if spec["concept_required"] and not any(c.get("role") == "concept_source" for c in corpus): errors.append("greenfield mode requires a concept/prompt source")
    if spec["review_target_required"] and not target: errors.append("review mode requires a supplied review target")
    if spec["generation_required"] and (generation_contract or {}).get("status") != "READY": errors.append("generation contract required for writing mode")
    payload = {"schema": SCHEMA, "mode": mode, "request_digest": canonical_digest(request), "corpus_digest": canonical_digest(corpus), "target_digest": target, "reticulum_digest": str(reticulum.get("digest", "")), "setup_digest": canonical_digest(setup.get("accepted", {})), "editorial_standard_digest": str(editorial_standard.get("digest", "")), "generation_contract_digest": str((generation_contract or {}).get("contract_digest", "")), "requirements": spec, "required_artifact_roles": sorted(required_artifact_roles(mode, setup)), "status": "READY" if not errors else "FAIL", "errors": errors}
    payload["digest"] = canonical_digest(payload)
    return payload


def validate_mode_contract(contract: dict[str, Any] | None, *, mode: str, request: dict[str, Any], corpus: list[dict[str, Any]], reticulum: dict[str, Any], setup: dict[str, Any], editorial_standard: dict[str, Any], generation_contract: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    if not contract: return False, ["mode contract missing"]
    expected = build_mode_contract(mode, request=request, corpus=corpus, reticulum=reticulum, setup=setup, editorial_standard=editorial_standard, generation_contract=generation_contract)
    errors = list(contract.get("errors", []))
    if contract.get("schema") != SCHEMA: errors.append("mode contract schema mismatch")
    if contract.get("status") != "READY": errors.append("mode contract not READY")
    for key in ("mode", "request_digest", "corpus_digest", "target_digest", "reticulum_digest", "setup_digest", "editorial_standard_digest", "generation_contract_digest", "requirements", "required_artifact_roles"):
        if contract.get(key) != expected.get(key): errors.append(f"mode contract {key} mismatch")
    digest = canonical_digest({k: v for k, v in contract.items() if k != "digest"})
    if contract.get("digest") != digest: errors.append("mode contract digest mismatch")
    return not errors, list(dict.fromkeys(errors))
