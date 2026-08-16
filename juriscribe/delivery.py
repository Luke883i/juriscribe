from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from typing import Any

from . import multimode as _multimode
from . import dashboard_v9 as _dashboard_v9

# Extend the canonical dashboard binding without duplicating the renderer. This is
# applied at module import before runtime rendering and keeps v0.9 UI semantics.
_DASHBOARD_CONTROL_KEYS = ("phase", "interaction", "completion", "node_integrity", "runtime")
_dashboard_v9.DASHBOARD_BINDING_KEYS = tuple(dict.fromkeys(_dashboard_v9.DASHBOARD_BINDING_KEYS + _DASHBOARD_CONTROL_KEYS))
dashboard_state_digest = _dashboard_v9.dashboard_state_digest
from .interaction import interaction_card
from .modes import required_artifact_roles

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
HTML_MIME = "text/html"
DELIVERY_SCHEMA = "juriscribe-final-delivery/v3"
ATTACH = "ATTACH"
INTERNAL = "INTERNAL"
DASHBOARD_DIGEST_RE = re.compile(r'<meta\s+name=["\']juriscribe-state-digest["\']\s+content=["\']([0-9a-f]{64})["\']', re.IGNORECASE)
DOCX_REQUIRED_MEMBERS = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
MAX_DOCX_FILE_BYTES = 64 * 1024 * 1024
MAX_DOCX_ENTRIES = 4096
MAX_DOCX_UNCOMPRESSED_BYTES = 192 * 1024 * 1024
MAX_DOCX_MEMBER_BYTES = 48 * 1024 * 1024
MAX_DOCUMENT_XML_BYTES = 24 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250

PRIMARY_ROLE_ORDER = [
    "final_chapter", "final_legal_text", "review_report", "revised_legal_text",
    "evidence_dossier", "review_findings_register", "source_register",
    "inference_register", "transformation_ledger", "session_dashboard",
]


def artifact_spec(role: str) -> dict[str, str]:
    if str(role or "") == "session_dashboard":
        return {"extension": ".html", "format": "HTML", "media_type": HTML_MIME}
    return {"extension": ".docx", "format": "DOCX", "media_type": DOCX_MIME}


def _required_roles(state) -> set[str]:
    mode = str(getattr(state, "mode", "") or "").strip()
    return {"session_dashboard"} if not mode else required_artifact_roles(mode, state.setup)


def _artifact_root(state) -> tuple[Path | None, list[str]]:
    workspace = str((getattr(state, "runtime", {}) or {}).get("workspace_base", "")).strip()
    if not workspace:
        return None, ["runtime workspace_base missing; final artifacts cannot be confined"]
    root = (Path(workspace) / "artifacts").resolve()
    return root, []


def _confined_path(state, raw_path: str | Path) -> tuple[Path | None, list[str]]:
    root, errors = _artifact_root(state)
    if root is None:
        return None, errors
    raw = Path(raw_path)
    absolute = raw if raw.is_absolute() else (Path.cwd() / raw)
    absolute = absolute.absolute()
    try:
        relative = absolute.relative_to(root)
    except ValueError:
        try:
            absolute.resolve(strict=False).relative_to(root)
        except ValueError:
            return None, ["artifact path escapes the session artifacts directory"]
        relative = absolute.resolve(strict=False).relative_to(root)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None, ["artifact path uses a symlink; symlinked deliverables are forbidden"]
    resolved = absolute.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, ["artifact path resolves outside the session artifacts directory"]
    return resolved, []


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_docx(path: Path) -> list[str]:
    errors: list[str] = []
    size = path.stat().st_size
    if size > MAX_DOCX_FILE_BYTES:
        return ["DOCX exceeds maximum allowed package size"]
    if not zipfile.is_zipfile(path):
        return ["file is not a valid DOCX/OOXML zip package"]
    try:
        with zipfile.ZipFile(path) as package:
            infos = package.infolist()
            if len(infos) > MAX_DOCX_ENTRIES:
                errors.append("DOCX package contains too many members")
            names = {info.filename for info in infos}
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                errors.append("DOCX package contains unsafe member paths")
            if any(info.flag_bits & 0x1 for info in infos):
                errors.append("encrypted DOCX members are not allowed")
            if "word/vbaProject.bin" in names:
                errors.append("macro-bearing OOXML content is not allowed in DOCX deliverables")
            total = sum(max(0, info.file_size) for info in infos)
            if total > MAX_DOCX_UNCOMPRESSED_BYTES:
                errors.append("DOCX uncompressed payload exceeds safety limit")
            for info in infos:
                if info.file_size > MAX_DOCX_MEMBER_BYTES:
                    errors.append(f"DOCX member exceeds safety limit: {info.filename}")
                    break
                if info.file_size > 1024 * 1024:
                    ratio = info.file_size / max(1, info.compress_size)
                    if ratio > MAX_COMPRESSION_RATIO:
                        errors.append(f"DOCX member compression ratio is unsafe: {info.filename}")
                        break
            missing = sorted(DOCX_REQUIRED_MEMBERS - names)
            if missing:
                errors.append("DOCX package is missing required members: " + ", ".join(missing))
            if "word/document.xml" in names and not errors:
                info = package.getinfo("word/document.xml")
                if info.file_size > MAX_DOCUMENT_XML_BYTES:
                    errors.append("DOCX word/document.xml exceeds readback safety limit")
                else:
                    with package.open(info) as handle:
                        body = handle.read(MAX_DOCUMENT_XML_BYTES + 1)
                    if len(body) > MAX_DOCUMENT_XML_BYTES:
                        errors.append("DOCX word/document.xml readback exceeded safety limit")
                    if b"<w:document" not in body and b":document" not in body:
                        errors.append("DOCX word/document.xml is not recognizable as a WordprocessingML document")
                    if b"<w:t" not in body and b":t" not in body:
                        errors.append("DOCX contains no readable text nodes")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        errors.append(f"DOCX readback failed: {type(exc).__name__}")
    return errors


def _verify_dashboard(state, path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"dashboard readback failed: {type(exc).__name__}"]
    errors: list[str] = []
    lowered = text.lower()
    if "<html" not in lowered or "juriscribe" not in lowered:
        errors.append("dashboard is not recognizable as Juriscribe HTML")
    match = DASHBOARD_DIGEST_RE.search(text)
    if not match:
        errors.append("dashboard state-digest binding is missing")
    elif match.group(1).lower() != dashboard_state_digest(state):
        errors.append("dashboard is stale relative to current substantive session state")
    return errors


def verify_materialized_artifact(state, record: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    role = str(record.get("role", ""))
    path, confinement_errors = _confined_path(state, str(record.get("path", "")))
    if path is None:
        return False, confinement_errors, {}
    errors = list(confinement_errors)
    metadata: dict[str, Any] = {}
    if not path.exists():
        return False, errors + [f"materialized artifact missing on disk: {role}"], metadata
    if not path.is_file():
        return False, errors + [f"artifact path is not a file: {role}"], metadata
    try:
        size = path.stat().st_size
    except OSError as exc:
        return False, errors + [f"artifact stat/readback failed for {role}: {type(exc).__name__}"], metadata
    if size <= 0:
        errors.append(f"materialized artifact is empty: {role}")
    spec = artifact_spec(role)
    if path.suffix.lower() != spec["extension"]:
        errors.append(f"materialized artifact has wrong extension: {role} must be {spec['extension']}")
    if not errors:
        errors.extend(_verify_dashboard(state, path) if role == "session_dashboard" else _verify_docx(path))
    if not errors:
        metadata = {
            "size_bytes": size, "sha256": _sha256_file(path), "materialized": True,
            "verified_format": spec["format"], "workspace_confined": True,
            "resolved_path": str(path),
        }
        recorded_sha = str(record.get("sha256", ""))
        if recorded_sha and recorded_sha != metadata["sha256"]:
            errors.append(f"artifact digest changed after registration: {role}")
    return not errors, list(dict.fromkeys(errors)), metadata


def normalize_artifact_record(state, record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    role = str(normalized.get("role", "")); path = str(normalized.get("path", ""))
    if not role: raise ValueError("artifact role required")
    if not path: raise ValueError("artifact path required")
    required = _required_roles(state)
    if role in required:
        spec = artifact_spec(role)
        if Path(path).suffix.lower() != spec["extension"]:
            raise ValueError(f"final artifact {role} must be {spec['format']} ({spec['extension']})")
        if normalized.get("readback") != "PASS":
            raise ValueError(f"required final artifact {role} requires readback PASS")
        normalized.update({"format": spec["format"], "media_type": spec["media_type"], "delivery_class": ATTACH, "required": True})
    else:
        if str(normalized.get("delivery_class", INTERNAL)).upper() == ATTACH:
            raise ValueError(f"internal/non-final artifact {role} cannot be attached in final delivery")
        normalized["delivery_class"] = INTERNAL; normalized["required"] = False
    return normalized


def _normalize_existing_artifacts(state) -> None:
    required = _required_roles(state); normalized = []
    for artifact in state.artifacts:
        role = str(artifact.get("role", ""))
        try:
            normalized.append(normalize_artifact_record(state, artifact))
        except ValueError:
            if role in required: normalized.append(dict(artifact))
            else:
                internal = dict(artifact); internal["delivery_class"] = INTERNAL; internal["required"] = False; normalized.append(internal)
    state.artifacts = normalized


def record_artifact(state, record: dict[str, Any]):
    normalized = normalize_artifact_record(state, record)
    if normalized.get("delivery_class") == ATTACH:
        ok, errors, metadata = verify_materialized_artifact(state, normalized)
        if not ok: raise ValueError("; ".join(errors))
        normalized.update(metadata)
        normalized["path"] = metadata.get("resolved_path", normalized["path"])
    return _multimode.record_artifact(state, normalized)


def refresh_dashboard_artifact(state, path: str | Path) -> dict[str, Any]:
    path = Path(path)
    record = next((a for a in state.artifacts if a.get("role") == "session_dashboard"), None)
    if record is None:
        record = {"id": "dashboard", "role": "session_dashboard", "summary": "Fascicolo leggibile della sessione", "path": str(path), "readback": "PASS"}
        state.artifacts.append(record)
    else:
        record["path"] = str(path); record["readback"] = "PASS"
        # Dashboard regeneration is an authorized replacement. Invalidate only its
        # prior materialization metadata before verifying and sealing the new bytes.
        # Other final artifacts still fail closed if their registered digest drifts.
        for key in ("sha256", "size_bytes", "materialized", "verified_format", "workspace_confined", "resolved_path"):
            record.pop(key, None)
    normalized = normalize_artifact_record(state, record)
    ok, errors, metadata = verify_materialized_artifact(state, normalized)
    if not ok: raise ValueError("; ".join(errors))
    normalized.update(metadata)
    normalized["path"] = metadata.get("resolved_path", normalized["path"])
    state.artifacts = [a for a in state.artifacts if a.get("role") != "session_dashboard"] + [normalized]
    return normalized


def delivery_gate(state) -> tuple[bool, list[str]]:
    _normalize_existing_artifacts(state); required = _required_roles(state); errors = []
    root, root_errors = _artifact_root(state); errors.extend(root_errors)
    by_role = {str(a.get("role", "")): a for a in state.artifacts if a.get("role")}
    document_roles = required - {"session_dashboard"}; capabilities = (state.runtime or {}).get("capabilities", {})
    if document_roles:
        if capabilities.get("DOCX_WRITE") != "AVAILABLE": errors.append("DOCX_WRITE capability must be AVAILABLE for final delivery")
        if capabilities.get("DOCX_READBACK") != "AVAILABLE": errors.append("DOCX_READBACK capability must be AVAILABLE for final delivery")
    for role in sorted(required):
        record = by_role.get(role)
        if not record: errors.append(f"required final artifact role missing: {role}"); continue
        spec = artifact_spec(role)
        if Path(str(record.get("path", ""))).suffix.lower() != spec["extension"]: errors.append(f"required final artifact has wrong format: {role} must be {spec['format']}")
        if record.get("readback") != "PASS": errors.append(f"required final artifact readback failed: {role}")
        if record.get("delivery_class") != ATTACH: errors.append(f"required final artifact is not marked for attachment: {role}")
        if record.get("media_type") not in {None, "", spec["media_type"]}: errors.append(f"required final artifact media type mismatch: {role}")
        materialized_ok, materialized_errors, _ = verify_materialized_artifact(state, record)
        if not materialized_ok: errors.extend(materialized_errors)
    return not errors, list(dict.fromkeys(errors))


def build_delivery_manifest(state) -> dict[str, Any]:
    ok, errors = delivery_gate(state); required = _required_roles(state)
    by_role = {str(a.get("role", "")): a for a in state.artifacts if a.get("role")}
    order = [role for role in PRIMARY_ROLE_ORDER if role in required]; order.extend(sorted(required - set(order)))
    attachments = []
    if ok:
        for role in order:
            artifact = by_role[role]; spec = artifact_spec(role); _, _, data = verify_materialized_artifact(state, artifact)
            attachments.append({"id": artifact.get("id"), "role": role, "path": artifact.get("path"), "format": spec["format"], "media_type": spec["media_type"], "readback": artifact.get("readback"), "size_bytes": data.get("size_bytes"), "sha256": data.get("sha256")})
    internal_count = sum(1 for a in state.artifacts if a.get("delivery_class") == INTERNAL)
    return {"schema": DELIVERY_SCHEMA, "status": "PASS" if ok else "FAIL", "attachments": attachments, "errors": errors, "internal_records_excluded": internal_count, "chat_policy": "BRIEF_ARTIFACT_FIRST_ALL_POST_BOOTSTRAP", "dashboard_required": True, "dashboard_bound_to_current_state": ok, "documents_format": "DOCX", "materialization_verified": ok, "workspace_confinement_verified": ok}


def brief_delivery_text(state) -> str:
    manifest = build_delivery_manifest(state)
    if state.completion.get("eligible") and manifest.get("status") == "PASS": return f"Completato. Consulta gli artefatti allegati ({len(manifest['attachments'])} file)."
    return "Non pronto. Consulta la dashboard; restano blocker di lavorazione."


def evaluate_completion(state):
    _normalize_existing_artifacts(state); _multimode.evaluate_completion(state)
    ok, errors = delivery_gate(state); manifest = build_delivery_manifest(state)
    state.completion["delivery_gate"] = {"eligible": ok, "errors": errors}; state.completion["delivery_manifest"] = manifest
    if not ok:
        state.completion["eligible"] = False; existing = str(state.completion.get("reason", "")); extra = "; ".join(errors); state.completion["reason"] = (existing + "; " + extra).strip("; "); state.phase = "VALIDATING"
    else: state.phase = "COMPLETE" if state.completion.get("eligible") else "VALIDATING"
    complete = bool(state.completion.get("eligible"))
    state.interaction = {**(state.interaction or {}), "card": interaction_card("COMPLETE" if complete else "HUMAN_DECISION_REQUIRED", summary=("Completato. Consulta gli artefatti allegati." if complete else "Restano blocker. Consulta la dashboard."), choices=["APRI ARTEFATTI", "RICHIEDI MODIFICHE", "ALTRO"] if complete else None), "status": "READY"}
    return state
