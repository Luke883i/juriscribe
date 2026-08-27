from __future__ import annotations

from . import governance_delivery as _legacy
from .chat_delivery import build_session_chat_docx_manifest, session_chat_docx_gate
from .consolidation_delivery import consolidation_artifact_gate, materialize_consolidation_artifacts
from .continuity import archive_material, continuity_state, validate_material_archive
from .modes import COMPRESSION_CONSOLIDATION, normalize_mode
from .runtime_cc_v2 import consolidation_gate


def _manifest(state):
    attachments = []
    for item in state.artifacts or []:
        if str(item.get("role") or "") == "session_dashboard":
            continue
        if str(item.get("delivery_class") or "").upper() != "ATTACH":
            continue
        attachments.append({
            "id": item.get("id"),
            "role": item.get("role"),
            "instance_key": item.get("instance_key", item.get("role")),
            "source_id": item.get("source_id"),
            "path": item.get("path"),
            "format": "DOCX",
            "media_type": item.get("media_type"),
            "size_bytes": item.get("size_bytes"),
            "sha256": item.get("sha256"),
            "readback": item.get("readback"),
        })
    return {
        "status": "PASS",
        "attachment_placement": "SESSION_CHAT_TAIL",
        "attachments": attachments,
        "atomic": True,
    }


def _repair_legacy_cc_continuity(state) -> None:
    """Migrate legacy C&C sessions only when their exact source texts survive.

    runtime_v11 historically retained exact C&C text in
    strategy.consolidation.source_texts. Reusing that exact representation is a
    lossless migration bridge, not a reconstruction from hashes or proof data.
    """
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION or not state.corpus:
        return
    strategy = state.strategy or {}
    source_texts = (strategy.get("consolidation") or {}).get("source_texts") or {}
    archived = (continuity_state(state).get("materials") or {})
    for item in state.corpus:
        source_id = str(item.get("source_id") or "").strip()
        if not source_id or source_id in archived or source_id not in source_texts:
            continue
        archive_material(
            state,
            str(source_texts[source_id]),
            source_id=source_id,
            role=str(item.get("role") or "candidate_material"),
            chapter=item.get("chapter"),
        )
        archived = continuity_state(state).get("materials") or {}


def _continuity_completion_gate(state) -> tuple[bool, list[str]]:
    """Common v1 recoverability gate; adds no proof authority."""
    _repair_legacy_cc_continuity(state)
    ok, errors = validate_material_archive(state)
    if state.corpus and not ok:
        return False, ["scientific recovery continuity is incomplete", *errors]
    return True, []


def _chat_docx_completion_gate(state) -> tuple[bool, list[str], dict]:
    """Every retained materialized DOCX must be projectable as a chat download."""
    manifest = build_session_chat_docx_manifest(state)
    ok, errors = session_chat_docx_gate(state)
    if not ok:
        return False, ["session-chat DOCX delivery projection is incomplete", *errors], manifest
    return True, [], manifest


def _apply_common_v1_gates(state):
    continuity_ok, continuity_errors = _continuity_completion_gate(state)
    chat_ok, chat_errors, chat_manifest = _chat_docx_completion_gate(state)
    state.completion["recovery_continuity_gate"] = {
        "eligible": continuity_ok,
        "errors": continuity_errors,
    }
    state.completion["session_chat_docx_gate"] = {
        "eligible": chat_ok,
        "errors": chat_errors,
        "manifest": chat_manifest,
    }
    if not continuity_ok or not chat_ok:
        state.completion["eligible"] = False
        existing = str(state.completion.get("reason") or "")
        extra = "; ".join([*continuity_errors, *chat_errors])
        state.completion["reason"] = (existing + "; " + extra).strip("; ")
        state.phase = "VALIDATING"
    return state


def evaluate_completion(state):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        _legacy.evaluate_completion(state)
        return _apply_common_v1_gates(state)

    errors = []
    core_ok, core_errors = consolidation_gate(state)
    errors.extend(core_errors)
    cc = (state.strategy or {}).get("consolidation") or {}
    if (cc.get("peer_review_readiness") or {}).get("status") != "PASS":
        errors.append("peer-review readiness PASS required")
    if (cc.get("provenance") or {}).get("status") != "PASS":
        errors.append("C&C provenance PASS required")
    if (cc.get("final_review") or {}).get("status") != "PASS":
        errors.append("C&C final severe review PASS required")

    autopilot = {"status": "DEFERRED", "errors": errors}
    if core_ok and not errors:
        autopilot = materialize_consolidation_artifacts(state)
    if autopilot.get("status") != "PASS":
        errors.extend(autopilot.get("errors") or ["C&C artifact autopilot not PASS"])

    art_ok, art_errors = consolidation_artifact_gate(state)
    errors.extend(art_errors)
    continuity_ok, continuity_errors = _continuity_completion_gate(state)
    errors.extend(continuity_errors)
    chat_ok, chat_errors, chat_manifest = _chat_docx_completion_gate(state)
    errors.extend(chat_errors)

    eligible = core_ok and art_ok and continuity_ok and chat_ok and not errors
    state.completion = {
        **(state.completion or {}),
        "eligible": eligible,
        "reason": "" if eligible else "; ".join(dict.fromkeys(errors)),
        "consolidation_gate": {"eligible": core_ok, "errors": core_errors},
        "consolidation_artifact_autopilot": autopilot,
        "consolidation_artifact_gate": {"eligible": art_ok, "errors": art_errors},
        "recovery_continuity_gate": {"eligible": continuity_ok, "errors": continuity_errors},
        "session_chat_docx_gate": {
            "eligible": chat_ok,
            "errors": chat_errors,
            "manifest": chat_manifest,
        },
        "delivery_manifest": _manifest(state) if eligible else {
            "status": "WITHHELD",
            "attachments": [],
            "atomic": True,
        },
    }
    state.phase = "COMPLETE" if eligible else "VALIDATING"
    return state
