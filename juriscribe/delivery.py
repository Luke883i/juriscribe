from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from typing import Any

from . import multimode as _multimode
from .dashboard_v9 import dashboard_state_digest
from .interaction import interaction_card
from .modes import required_artifact_roles

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
HTML_MIME = "text/html"
DELIVERY_SCHEMA = "juriscribe-final-delivery/v2"
ATTACH = "ATTACH"
INTERNAL = "INTERNAL"
DASHBOARD_DIGEST_RE = re.compile(
    r'<meta\s+name=["\']juriscribe-state-digest["\']\s+content=["\']([0-9a-f]{64})["\']',
    re.IGNORECASE,
)
DOCX_REQUIRED_MEMBERS = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}

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
    mode = str(getattr(state, "mode", "") or "").strip()
    if not mode:
        # The dashboard exists from initialize onward, before a substantive mode is selected.
        return {"session_dashboard"}
    return required_artifact_roles(mode, state.setup)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_docx(path: Path) -> list[str]:
    errors: list[str] = []
    if not zipfile.is_zipfile(path):
        return ["file is not a valid DOCX/OOXML zip package"]
    try:
        with zipfile.ZipFile(path) as package:
            names = set(package.namelist())
            missing = sorted(DOCX_REQUIRED_MEMBERS - names)
            if missing:
                errors.append("DOCX package is missing required members: " + ", ".join(missing))
            if "word/document.xml" in names:
                body = package.read("word/document.xml")
                if b"<w:document" not in body and b":document" not in body:
                    errors.append("DOCX word/document.xml is not recognizable as a WordprocessingML document")
                if b"<w:t" not in body and b":t" not in body:
                    errors.append("DOCX contains no readable text nodes")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        errors.append(f"DOCX readback failed: {exc}")
    return errors


def _verify_dashboard(state, path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"dashboard readback failed: {exc}"]
    lowered = text.lower()
    if "<html" not in lowered or "juriscribe" not in lowered:
        errors.append("dashboard is not recognizable as Juriscribe HTML")
    match = DASHBOARD_DIGEST_RE.search(text)
    if not match:
        errors.append("dashboard state-digest binding is missing")
    else:
        expected = dashboard_state_digest(state)
        if match.group(1).lower() != expected:
            errors.append("dashboard is stale relative to current substantive session state")
    return errors


def verify_materialized_artifact(state, record: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    role = str(record.get("role", ""))
    path = Path(str(record.get("path", "")))
    errors: list[str] = []
    metadata: dict[str, Any] = {}
    if not path.exists():
        return False, [f"materialized artifact missing on disk: {role}"], metadata
    if not path.is_file():
        return False, [f"artifact path is not a file: {role}"], metadata
    try:
        size = path.stat().st_size
    except OSError as exc:
        return False, [f"artifact stat/readback failed for {role}: {exc}"], metadata
    if size <= 0:
        errors.append(f"materialized artifact is empty: {role}")
    spec = artifact_spec(role)
    if path.suffix.lower() != spec["extension"]:
        errors.append(f"materialized artifact has wrong extension: {role} must be {spec['extension']}")
    if not errors:
        if role == "session_dashboard":
            errors.extend(_verify_dashboard(state, path))
        else:
            errors.extend(_verify_docx(path))
    if not errors:
        metadata = {
            "size_bytes": size,
            "sha256": _sha256_file(path),
            "materialized": True,
            "verified_format": spec["format"],
        }
        recorded_sha = str(record.get("sha256", ""))
        if recorded_sha and recorded_sha != metadata["sha256"]:
            errors.append(f"artifact digest changed after registration: {role}")
    return not errors, list(dict.fromkeys(errors)), metadata


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
            raise ValueError(f"final artifact {role} must be {spec['format']} ({spec['extension']})")
        if normalized.get("readback") != "PASS":
            raise ValueError(f"required final artifact {role} requires readback PASS")
        normalized["format"] = spec["format"]
        normalized["media_type"] = spec["media_type"]
        normalized["delivery_class"] = ATTACH
        normalized["required"] = True
    else:
        if str(normalized.get("delivery_class", INTERNAL)).upper() == ATTACH:
            raise ValueError(f"internal/non-final artifact {role} cannot be attached in final delivery")
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
    if normalized.get("delivery_class") == ATTACH:
        ok, errors, metadata = verify_materialized_artifact(state, normalized)
        if not ok:
            raise ValueError("; ".join(errors))
        normalized.update(metadata)
    return _multimode.record_artifact(state, normalized)


def refresh_dashboard_artifact(state, path: str | Path) -> dict[str, Any]:
    path = Path(path)
    record = next((a for a in state.artifacts if a.get("role") == "session_dashboard"), None)
    if record is None:
        record = {
            "id": "dashboard",
            "role": "session_dashboard",
            "summary": "Fascicolo leggibile della sessione",
            "path": str(path),
            "readback": "PASS",
        }
        state.artifacts.append(record)
    else:
        record["path"] = str(path)
        record["readback"] = "PASS"
    normalized = normalize_artifact_record(state, record)
    ok, errors, metadata = verify_materialized_artifact(state, normalized)
    if not ok:
        raise ValueError("; ".join(errors))
    normalized.update(metadata)
    state.artifacts = [a for a in state.artifacts if a.get("role") != "session_dashboard"] + [normalized]
    return normalized


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
        materialized_ok, materialized_errors, _ = verify_materialized_artifact(state, record)
        if not materialized_ok:
            errors.extend(materialized_errors)

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
            _, _, data = verify_materialized_artifact(state, artifact)
            attachments.append({
                "id": artifact.get("id"),
                "role": role,
                "path": artifact.get("path"),
                "format": spec["format"],
                "media_type": spec["media_type"],
                "readback": artifact.get("readback"),
                "size_bytes": data.get("size_bytes"),
                "sha256": data.get("sha256"),
            })
    internal_count = sum(1 for a in state.artifacts if a.get("delivery_class") == INTERNAL)
    return {
        "schema": DELIVERY_SCHEMA,
        "status": "PASS" if ok else "FAIL",
        "attachments": attachments,
        "errors": errors,
        "internal_records_excluded": internal_count,
        "chat_policy": "BRIEF_ARTIFACT_FIRST_ALL_POST_BOOTSTRAP",
        "dashboard_required": True,
        "dashboard_bound_to_current_state": ok,
        "documents_format": "DOCX",
        "materialization_verified": ok,
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
            summary=("Completato. Consulta gli artefatti allegati." if complete else "Restano blocker. Consulta la dashboard."),
            choices=["APRI ARTEFATTI", "RICHIEDI MODIFICHE", "ALTRO"] if complete else None,
        ),
        "status": "READY",
    }
    return state
