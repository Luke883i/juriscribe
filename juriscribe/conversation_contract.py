from __future__ import annotations

import hashlib
import json
from typing import Any

from .modes import mode_spec, required_artifact_roles

SCHEMA = "juriscribe-natural-language-pipeline-contract/v1"
PROFILE_ID = "JURISCRIBE_NATURAL_LANGUAGE_PIPELINE_LOCK_V1"
TRACE_SCHEMA = "juriscribe-final-artifact-inference-trace/v1"

CLASSIFICATIONS = {
    "STATUS_QUERY", "CONTENT_CONSTRAINT", "PARAMETER_MUTATION", "MATERIAL_DECISION",
    "MODE_CHANGE_REQUEST", "NEW_WORK_REQUEST", "OUT_OF_SCOPE", "AMBIGUOUS",
}
PIPELINE_EFFECTS = {
    "NONE", "CONTENT_CONSTRAINT", "PARAMETER_MUTATION", "HUMAN_DECISION",
    "NEW_SESSION_REQUIRED", "BLOCKED_PENDING_CLARIFICATION",
}
MATERIAL_CLASSIFICATIONS = {"CONTENT_CONSTRAINT", "PARAMETER_MUTATION", "MATERIAL_DECISION"}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _strategy(state: Any) -> dict[str, Any]:
    s = _payload(state)
    strategy = s.setdefault("strategy", {}) if isinstance(s, dict) else {}
    return strategy


def _contract(state: Any) -> dict[str, Any]:
    return dict((_strategy(state) or {}).get("natural_language_pipeline") or {})


def _set_contract(state: Any, contract: dict[str, Any]) -> None:
    if isinstance(state, dict):
        state.setdefault("strategy", {})["natural_language_pipeline"] = contract
    else:
        state.strategy.setdefault("natural_language_pipeline", {})
        state.strategy["natural_language_pipeline"] = contract


def initialize_pipeline_lock(state: Any) -> dict[str, Any]:
    s = _payload(state)
    mode = str(s.get("mode") or "").strip().upper()
    if not mode:
        raise ValueError("mode must be selected before natural-language pipeline lock")
    spec = mode_spec(mode, s.get("setup") or {})
    existing = _contract(state)
    history = list(existing.get("interpretations") or [])
    lock = {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "status": "LOCKED",
        "locked_mode": mode,
        "locked_primary_artifact_role": spec.get("primary_artifact_role"),
        "locked_required_artifact_roles": sorted(required_artifact_roles(mode, s.get("setup") or {})),
        "mode_selection_digest": str((s.get("mode_selection") or {}).get("digest") or ""),
        "request_id": str((s.get("request") or {}).get("request_id") or ""),
        "interpretations": history,
        "policy": {
            "free_natural_language_allowed": True,
            "implicit_mode_change_forbidden": True,
            "implicit_artifact_role_change_forbidden": True,
            "implicit_pipeline_skip_forbidden": True,
            "mode_change_requires_new_explicit_selection_or_new_session": True,
            "material_user_instruction_requires_trace_record": True,
            "standard_artifact_set_runtime_owned": True,
            "final_artifact_trace_required": mode == "CONTINUATION",
        },
    }
    lock["lock_digest"] = canonical_digest({k: v for k, v in lock.items() if k != "lock_digest"})
    _set_contract(state, lock)
    return lock


def refresh_pipeline_lock_artifact_set(state: Any) -> dict[str, Any]:
    """Refresh setup-dependent roles without permitting a mode or primary-role drift."""
    s = _payload(state)
    lock = _contract(state)
    if not lock:
        return initialize_pipeline_lock(state)
    expected = sorted(required_artifact_roles(str(s.get("mode") or ""), s.get("setup") or {}))
    primary = mode_spec(str(s.get("mode") or ""), s.get("setup") or {}).get("primary_artifact_role")
    if lock.get("locked_mode") != str(s.get("mode") or ""):
        raise ValueError("natural-language pipeline lock forbids implicit mode change")
    if lock.get("locked_primary_artifact_role") != primary:
        raise ValueError("natural-language pipeline lock forbids implicit primary artifact change")
    lock["locked_required_artifact_roles"] = expected
    lock["lock_digest"] = canonical_digest({k: v for k, v in lock.items() if k != "lock_digest"})
    _set_contract(state, lock)
    return lock


def pipeline_lock_gate(state: Any) -> tuple[bool, list[str]]:
    s = _payload(state)
    mode = str(s.get("mode") or "").strip()
    if not mode:
        return True, []
    lock = _contract(state)
    errors: list[str] = []
    if lock.get("schema") != SCHEMA or lock.get("profile") != PROFILE_ID:
        return False, ["natural-language pipeline contract missing"]
    if lock.get("status") != "LOCKED":
        errors.append("natural-language pipeline contract is not LOCKED")
    expected_primary = mode_spec(mode, s.get("setup") or {}).get("primary_artifact_role")
    expected_roles = sorted(required_artifact_roles(mode, s.get("setup") or {}))
    if lock.get("locked_mode") != mode:
        errors.append("natural-language pipeline lock drift: mode")
    if lock.get("locked_primary_artifact_role") != expected_primary:
        errors.append("natural-language pipeline lock drift: primary artifact")
    if lock.get("locked_required_artifact_roles") != expected_roles:
        errors.append("natural-language pipeline lock drift: standard artifact set")
    if lock.get("mode_selection_digest") != str((s.get("mode_selection") or {}).get("digest") or ""):
        errors.append("natural-language pipeline lock drift: mode selection")
    if lock.get("lock_digest") != canonical_digest({k: v for k, v in lock.items() if k != "lock_digest"}):
        errors.append("natural-language pipeline lock digest mismatch")
    for item in lock.get("interpretations") or []:
        if item.get("status") in {"AMBIGUOUS", "BLOCKED"} and item.get("resolution_status") != "RESOLVED":
            errors.append(f"unresolved natural-language interpretation: {item.get('id')}")
        if item.get("pipeline_effect") not in PIPELINE_EFFECTS:
            errors.append(f"invalid pipeline effect in natural-language interpretation: {item.get('id')}")
        if item.get("classification") not in CLASSIFICATIONS:
            errors.append(f"invalid natural-language classification: {item.get('id')}")
    return not errors, list(dict.fromkeys(errors))


def record_natural_language_interpretation(state: Any, utterance: str, interpretation: dict[str, Any]) -> dict[str, Any]:
    s = _payload(state)
    if not _contract(state):
        initialize_pipeline_lock(state)
    lock = _contract(state)
    classification = str(interpretation.get("classification") or "").strip().upper()
    if classification not in CLASSIFICATIONS:
        raise ValueError("natural-language interpretation classification invalid")
    proposed_effect = str(interpretation.get("pipeline_effect") or "NONE").strip().upper()
    if proposed_effect not in PIPELINE_EFFECTS:
        raise ValueError("natural-language interpretation pipeline_effect invalid")

    forbidden_requested = any(
        interpretation.get(key) not in (None, "", [], {}, False)
        for key in ("replace_mode", "replace_primary_artifact_role", "skip_pipeline_steps", "disable_standard_artifacts", "replace_output_format")
    )
    status = "APPLIED"
    effect = proposed_effect
    errors: list[str] = []
    if classification in {"MODE_CHANGE_REQUEST", "NEW_WORK_REQUEST"}:
        effect = "NEW_SESSION_REQUIRED"
        status = "BLOCKED"
        errors.append("mode/new-work change cannot mutate the active pipeline implicitly")
    elif classification == "AMBIGUOUS":
        effect = "BLOCKED_PENDING_CLARIFICATION"
        status = "AMBIGUOUS"
        errors.append("ambiguous material language requires clarification before state mutation")
    elif forbidden_requested:
        effect = "BLOCKED_PENDING_CLARIFICATION"
        status = "BLOCKED"
        errors.append("natural language cannot replace mode, primary artifact, standard artifacts, output format or pipeline steps")
    elif classification in {"STATUS_QUERY", "OUT_OF_SCOPE"}:
        effect = "NONE"

    interpretations = list(lock.get("interpretations") or [])
    ordinal = len(interpretations) + 1
    record = {
        "id": f"NL-{ordinal:04d}",
        "utterance_digest": hashlib.sha256(str(utterance or "").encode("utf-8")).hexdigest(),
        "utterance_excerpt": " ".join(str(utterance or "").split())[:500],
        "classification": classification,
        "pipeline_effect": effect,
        "interpretation": str(interpretation.get("interpretation") or "").strip()[:1000],
        "material_effects": list(interpretation.get("material_effects") or []),
        "affected_unit_ids": sorted({str(x) for x in interpretation.get("affected_unit_ids") or [] if str(x)}),
        "affected_claim_ids": sorted({str(x) for x in interpretation.get("affected_claim_ids") or [] if str(x)}),
        "mode_snapshot": str(s.get("mode") or ""),
        "primary_artifact_snapshot": lock.get("locked_primary_artifact_role"),
        "status": status,
        "resolution_status": "NOT_REQUIRED" if status == "APPLIED" else "OPEN",
        "errors": errors,
    }
    record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    interpretations.append(record)
    lock["interpretations"] = interpretations
    lock["lock_digest"] = canonical_digest({k: v for k, v in lock.items() if k != "lock_digest"})
    _set_contract(state, lock)
    return record


def resolve_natural_language_interpretation(state: Any, record_id: str, resolution: str) -> dict[str, Any]:
    lock = _contract(state)
    records = list(lock.get("interpretations") or [])
    target = next((item for item in records if str(item.get("id")) == str(record_id)), None)
    if not target:
        raise ValueError("natural-language interpretation record not found")
    target["resolution_status"] = "RESOLVED"
    target["resolution"] = " ".join(str(resolution or "").split())[:1000]
    target["digest"] = canonical_digest({k: v for k, v in target.items() if k != "digest"})
    lock["interpretations"] = records
    lock["lock_digest"] = canonical_digest({k: v for k, v in lock.items() if k != "lock_digest"})
    _set_contract(state, lock)
    return target


def build_final_artifact_inference_trace(state: Any, role: str, candidate_digest: str) -> dict[str, Any]:
    s = _payload(state)
    lock = _contract(state)
    material_interpretations = [
        item for item in lock.get("interpretations") or []
        if item.get("classification") in MATERIAL_CLASSIFICATIONS and item.get("status") == "APPLIED"
    ]
    unit_ids = sorted({str(item.get("id")) for item in s.get("epistemic_units") or [] if item.get("id") and bool(item.get("material", True))})
    claim_ids = sorted({str(item.get("id")) for item in s.get("claim_ledger") or [] if item.get("id") and bool(item.get("material", True))})
    trace = {
        "schema": TRACE_SCHEMA,
        "profile": PROFILE_ID,
        "status": "PASS",
        "artifact_role": str(role),
        "request_id": str((s.get("request") or {}).get("request_id") or ""),
        "mode": str(s.get("mode") or ""),
        "locked_primary_artifact_role": lock.get("locked_primary_artifact_role"),
        "natural_language_interpretation_ids": [str(item.get("id")) for item in material_interpretations],
        "material_epistemic_unit_ids": unit_ids,
        "material_claim_ids": claim_ids,
        "generation_contract_digest": str((s.get("generation_contract") or {}).get("contract_digest") or ""),
        "continuation_plan_status": str(((s.get("continuation") or {}).get("plan") or {}).get("status") or ""),
        "candidate_digest": str(candidate_digest or ""),
        "required_artifact_roles": list(lock.get("locked_required_artifact_roles") or []),
    }
    errors: list[str] = []
    ok_lock, lock_errors = pipeline_lock_gate(s)
    if not ok_lock:
        errors.extend(lock_errors)
    if str(role) == "final_chapter":
        if str(s.get("mode") or "") != "CONTINUATION": errors.append("final_chapter trace requires CONTINUATION mode")
        if lock.get("locked_primary_artifact_role") != "final_chapter": errors.append("final_chapter is not the locked primary artifact")
        if not unit_ids: errors.append("final_chapter trace requires material epistemic units")
        if not str((s.get("generation_contract") or {}).get("contract_digest") or ""): errors.append("final_chapter trace requires generation contract")
        if ((s.get("continuation") or {}).get("plan") or {}).get("status") != "PASS": errors.append("final_chapter trace requires validated continuation plan")
    if not str(candidate_digest or ""):
        errors.append("final artifact inference trace requires candidate digest")
    trace["status"] = "PASS" if not errors else "FAIL"
    trace["errors"] = list(dict.fromkeys(errors))
    trace["digest"] = canonical_digest({k: v for k, v in trace.items() if k != "digest"})
    return trace


def final_chapter_inference_trace_gate(state: Any) -> tuple[bool, list[str]]:
    s = _payload(state)
    if str(s.get("mode") or "") != "CONTINUATION":
        return True, []
    artifact = next((item for item in s.get("artifacts") or [] if item.get("role") == "final_chapter"), None)
    if not artifact:
        return False, ["final_chapter artifact missing inference trace"]
    trace = artifact.get("inference_trace") or {}
    errors: list[str] = []
    if trace.get("schema") != TRACE_SCHEMA or trace.get("profile") != PROFILE_ID:
        errors.append("final_chapter inference trace schema/profile mismatch")
    if trace.get("status") != "PASS":
        errors.extend(trace.get("errors") or ["final_chapter inference trace is not PASS"])
    current_candidate = str((s.get("drafts") or [{}])[-1].get("digest") or "") if s.get("drafts") else ""
    if trace.get("candidate_digest") != current_candidate:
        errors.append("final_chapter inference trace is bound to stale candidate")
    if trace.get("generation_contract_digest") != str((s.get("generation_contract") or {}).get("contract_digest") or ""):
        errors.append("final_chapter inference trace is bound to stale generation contract")
    if trace.get("digest") != canonical_digest({k: v for k, v in trace.items() if k != "digest"}):
        errors.append("final_chapter inference trace digest mismatch")
    return not errors, list(dict.fromkeys(errors))
