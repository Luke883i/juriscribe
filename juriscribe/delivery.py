from __future__ import annotations

from pathlib import Path
from typing import Any

from . import multimode as _multimode
from .interaction import interaction_card
from .modes import required_artifact_roles

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
HTML_MIME = "text/html"
DELIVERY_SCHEMA = "juriscribe-final-delivery/v1"
ATTACH = "ATTACH"
INTERNAL = "INTERNAL"

PRIMARY_ROLE_ORDER = [
    "final_chapter",
    "final_legal_text",
    "review_report",
    "revised_legal_text",
    "evidence_dossier",
    "review_findings_register",
    "source_register",
    "inference_register",
    "transformation_ledger",
    "session_dashboard",
]


def artifact_spec(role: str) -> dict[str, str]:
    role = str(role or "")
    if role == "session_dashboard":
        return {"extension": ".html", "format": "HTML", "media_type": HTML_MIME}
    return {"extension": ".docx", "format": "DOCX", "media_type": DOCX_MIME}


def _required_roles(state) -> set[str]:
    return required_artifact_roles(state.mode, state.setup)


def normalize_artifact_record(state, record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    role = str(normalized.get("role", ""))
    path = str(normalized.get("path", ""))
    if not role:
        raise ValueError("artifact role required")
    if not path:
        raise ValueError("artifact path required")

    required = _required_roles(state)
    if role in required:
        spec = artifact_spec(role)
        if Path(path).suffix.lower() != spec["extension"]:
            raise ValueError(
                f"final artifact {role} must be {spec['format']} ({spec['extension']})"
            )
        if normalized.get("readback") != "PASS":
            raise ValueError(f"required final artifact {role} requires readback PASS")
        normalized["format"] = spec["format"]
        normalized["media_type"] = spec["media_type"]
        normalized["delivery_class"] = ATTACH
        normalized["required"] = True
    else:
        if str(normalized.get("delivery_class", INTERNAL)).upper() == ATTACH:
            raise ValueError(
                f"internal/non-final artifact {role} cannot be attached in final delivery"
            )
        normalized["delivery_class"] = INTERNAL
        normalized["required"] = False
    return normalized


def _normalize_existing_artifacts(state) -> None:
    required = _required_roles(state)
    normalized: list[dict[str, Any]] = []
    for artifact in state.artifacts:
        role = str(artifact.get("role", ""))
        try:
            normalized.append(normalize_artifact_record(state, artifact))
        except ValueError:
            # Preserve malformed required artifacts so the delivery gate can report the
            # exact failure instead of silently discarding evidence of the regression.
            if role in required:
                normalized.append(dict(artifact))
            else:
                internal = dict(artifact)
                internal["delivery_class"] = INTERNAL
                internal["required"] = False
                normalized.append(internal)
    state.artifacts = normalized


def record_artifact(state, record: dict[str, Any]):
    normalized = normalize_artifact_record(state, record)
    return _multimode.record_artifact(state, normalized)


def delivery_gate(state) -> tuple[bool, list[str]]:
    _normalize_existing_artifacts(state)
    required = _required_roles(state)
    errors: list[str] = []
    by_role = {str(a.get("role", "")): a for a in state.artifacts if a.get("role")}

    document_roles = required - {"session_dashboard"}
    capabilities = (state.runtime or {}).get("capabilities", {})
    if document_roles:
        if capabilities.get("DOCX_WRITE") != "AVAILABLE":
            errors.append("DOCX_WRITE capability must be AVAILABLE for final delivery")
        if capabilities.get("DOCX_READBACK") != "AVAILABLE":
            errors.append("DOCX_READBACK capability must be AVAILABLE for final delivery")

    for role in sorted(required):
        record = by_role.get(role)
        if not record:
            errors.append(f"required final artifact role missing: {role}")
            continue
        spec = artifact_spec(role)
        if Path(str(record.get("path", ""))).suffix.lower() != spec["extension"]:
            errors.append(f"required final artifact has wrong format: {role} must be {spec['format']}")
        if record.get("readback") != "PASS":
            errors.append(f"required final artifact readback failed: {role}")
        if record.get("delivery_class") != ATTACH:
            errors.append(f"required final artifact is not marked for attachment: {role}")
        if record.get("media_type") not in {None, "", spec["media_type"]}:
            errors.append(f"required final artifact media type mismatch: {role}")

    return not errors, list(dict.fromkeys(errors))


def build_delivery_manifest(state) -> dict[str, Any]:
    ok, errors = delivery_gate(state)
    required = _required_roles(state)
    by_role = {str(a.get("role", "")): a for a in state.artifacts if a.get("role")}
    order = [role for role in PRIMARY_ROLE_ORDER if role in required]
    order.extend(sorted(required - set(order)))
    attachments = []
    if ok:
        for role in order:
            artifact = by_role[role]
            spec = artifact_spec(role)
            attachments.append(
                {
                    "id": artifact.get("id"),
                    "role": role,
                    "path": artifact.get("path"),
                    "format": spec["format"],
                    "media_type": spec["media_type"],
                    "readback": artifact.get("readback"),
                }
            )
    internal_count = sum(1 for a in state.artifacts if a.get("delivery_class") == INTERNAL)
    return {
        "schema": DELIVERY_SCHEMA,
        "status": "PASS" if ok else "FAIL",
        "attachments": attachments,
        "errors": errors,
        "internal_records_excluded": internal_count,
        "chat_policy": "BRIEF_ARTIFACT_FIRST",
        "dashboard_required": True,
        "documents_format": "DOCX",
    }


def brief_delivery_text(state) -> str:
    manifest = build_delivery_manifest(state)
    if state.completion.get("eligible") and manifest.get("status") == "PASS":
        return f"Completato. Consulta gli artefatti allegati ({len(manifest['attachments'])} file)."
    return "Non pronto. Consulta la dashboard; restano blocker di lavorazione."


def evaluate_completion(state):
    _normalize_existing_artifacts(state)
    _multimode.evaluate_completion(state)
    ok, errors = delivery_gate(state)
    manifest = build_delivery_manifest(state)
    state.completion["delivery_gate"] = {"eligible": ok, "errors": errors}
    state.completion["delivery_manifest"] = manifest
    if not ok:
        state.completion["eligible"] = False
        existing = str(state.completion.get("reason", ""))
        extra = "; ".join(errors)
        state.completion["reason"] = (existing + "; " + extra).strip("; ")
        state.phase = "VALIDATING"
    else:
        state.phase = "COMPLETE" if state.completion.get("eligible") else "VALIDATING"

    complete = bool(state.completion.get("eligible"))
    state.interaction = {
        **(state.interaction or {}),
        "card": interaction_card(
            "COMPLETE" if complete else "HUMAN_DECISION_REQUIRED",
            summary=(
                "Completato. Consulta gli artefatti allegati."
                if complete
                else "Restano blocker. Consulta la dashboard."
            ),
            choices=["APRI ARTEFATTI", "RICHIEDI MODIFICHE", "ALTRO"] if complete else None,
        ),
        "status": "READY",
    }
    return state
