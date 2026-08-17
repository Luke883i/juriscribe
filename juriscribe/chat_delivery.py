from __future__ import annotations

import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from .delivery_compliance import build_delivery_compliance_inventory
from .modes import required_artifact_roles

PROFILE_ID = "JURISCRIBE_CHAT_DOCX_DELIVERY_V1"
SCHEMA = "juriscribe-chat-docx-delivery/v1"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ATTACH = "ATTACH"
SURFACE_ROLE = "session_dashboard"
CHAT_PLACEMENT = "SESSION_CHAT_TAIL"
_SAFE_ASCII = re.compile(r"[^A-Za-z0-9._-]+")


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def required_docx_roles(state: Any) -> set[str]:
    s = _payload(state)
    mode = str(s.get("mode") or "").strip()
    if not mode:
        return set()
    try:
        return set(required_artifact_roles(mode, s.get("setup") or {})) - {SURFACE_ROLE}
    except ValueError:
        return set()


def _ascii_filename(name: str) -> str:
    base = Path(str(name or "artifact.docx")).name
    normalized = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.replace("%", "_").replace("\\", "_").replace('"', "_")
    normalized = _SAFE_ASCII.sub("_", normalized).strip(" ._") or "artifact.docx"
    if not normalized.lower().endswith(".docx"):
        normalized = normalized.rsplit(".", 1)[0] + ".docx"
    stem = normalized[:-5][:120].rstrip("._-") or "artifact"
    return stem + ".docx"


def content_disposition(filename: str) -> str:
    raw = Path(str(filename or "artifact.docx")).name
    if not raw.lower().endswith(".docx"):
        raw = raw.rsplit(".", 1)[0] + ".docx"
    fallback = _ascii_filename(raw)
    encoded = quote(raw, safe="")
    return f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{encoded}'


def build_chat_attachment_descriptor(record: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    item = dict(record or {})
    role = str(item.get("role") or "").strip()
    path = str(item.get("path") or "").strip()
    errors: list[str] = []
    if not role: errors.append("chat attachment role missing")
    if role == SURFACE_ROLE: errors.append("session dashboard HTML is a browser surface and cannot be a chat attachment")
    if str(item.get("delivery_class") or "").upper() != ATTACH: errors.append(f"chat artifact is not marked ATTACH: {role or 'unknown'}")
    if not path or Path(path).suffix.lower() != ".docx": errors.append(f"chat attachment must be DOCX: {role or 'unknown'}")
    if item.get("readback") != "PASS": errors.append(f"chat attachment readback is not PASS: {role or 'unknown'}")
    if str(item.get("format") or "DOCX").upper() != "DOCX": errors.append(f"chat attachment format is not DOCX: {role or 'unknown'}")
    media_type = str(item.get("media_type") or DOCX_MIME)
    if media_type != DOCX_MIME: errors.append(f"chat attachment media type mismatch: {role or 'unknown'}")
    if item.get("verified_format") not in (None, "", "DOCX"): errors.append(f"chat attachment is not materially verified as DOCX: {role or 'unknown'}")
    if "materialized" in item and item.get("materialized") is not True: errors.append(f"chat attachment is not materially sealed: {role or 'unknown'}")
    if path and Path(path).name in {"", ".", ".."}: errors.append(f"chat attachment filename is invalid: {role or 'unknown'}")
    filename = Path(path).name if path else "artifact.docx"
    descriptor = {
        "schema": SCHEMA, "profile": PROFILE_ID, "role": role, "path": path, "filename": filename,
        "media_type": DOCX_MIME, "content_disposition": content_disposition(filename), "delivery_class": ATTACH,
        "placement": CHAT_PLACEMENT, "downloadable_in_chat": True, "dashboard_link_allowed": False,
        "assistant_agnostic_contract": True, "browser_agnostic_contract": True,
        "host_attachment_capability_required": True, "global_host_behavior_claim": False,
        "status": "PASS" if not errors else "FAIL",
    }
    return descriptor, list(dict.fromkeys(errors))


def build_chat_delivery_manifest(state: Any, *, require_all: bool = True) -> dict[str, Any]:
    s = _payload(state)
    expected = required_docx_roles(s)
    artifacts = [dict(item) for item in s.get("artifacts") or []]
    by_role = {str(item.get("role") or ""): item for item in artifacts if item.get("role")}
    errors: list[str] = []
    candidates: list[dict[str, Any]] = []

    if require_all:
        for role in sorted(expected):
            if role not in by_role:
                errors.append(f"required chat-tail DOCX artifact missing: {role}")

    candidate_roles = set(expected if require_all else ())
    candidate_roles.update(str(item.get("role") or "") for item in artifacts if str(item.get("delivery_class") or "").upper() == ATTACH and item.get("role"))
    for role in sorted(candidate_roles):
        item = by_role.get(role)
        if not item: continue
        descriptor, descriptor_errors = build_chat_attachment_descriptor(item)
        candidates.append(descriptor)
        errors.extend(descriptor_errors)
        if require_all and role not in expected: errors.append(f"non-final role entered chat attachment set: {role}")

    dashboard = by_role.get(SURFACE_ROLE)
    if dashboard and str(dashboard.get("delivery_class") or "").upper() == ATTACH:
        errors.append("session dashboard HTML may not enter the session-chat attachment tail")
    for item in artifacts:
        if str(item.get("delivery_class") or "").upper() == ATTACH and Path(str(item.get("path") or "")).suffix.lower() != ".docx":
            errors.append(f"non-DOCX chat attachment is forbidden: {item.get('role')}")

    compliance = build_delivery_compliance_inventory(s)
    if compliance.get("status") == "FAIL" or compliance.get("release_authorized") is False:
        errors.extend(compliance.get("blocking_errors") or ["mechanical delivery compliance inventory did not authorize atomic release"])
    errors = list(dict.fromkeys(errors))
    release_authorized = not errors and compliance.get("release_authorized", True) is True
    released = candidates if release_authorized else []
    withheld = [] if release_authorized else sorted({str(item.get("role") or "") for item in candidates if item.get("role")})
    return {
        "schema": SCHEMA, "profile": PROFILE_ID, "status": "PASS" if release_authorized else "FAIL",
        "required_docx_roles": sorted(expected), "attachments": released, "withheld_attachments": withheld,
        "candidate_attachment_count": len(candidates), "released_attachment_count": len(released), "errors": errors,
        "placement": CHAT_PLACEMENT, "atomic_release": True, "mechanical_delivery_compliance": compliance,
        "downloadable_artifacts_only_docx": not any(Path(str(item.get("path") or "")).suffix.lower() != ".docx" for item in artifacts if str(item.get("delivery_class") or "").upper() == ATTACH),
        "dashboard_is_summary_surface_not_attachment": not bool(dashboard and str(dashboard.get("delivery_class") or "").upper() == ATTACH),
        "dashboard_links_to_docx": False, "assistant_agnostic_contract": True, "browser_agnostic_contract": True,
        "host_attachment_capability_required": True, "global_host_behavior_claim": False,
    }


def chat_docx_delivery_gate(state: Any) -> tuple[bool, list[str]]:
    manifest = build_chat_delivery_manifest(state, require_all=True)
    return manifest.get("status") == "PASS", list(manifest.get("errors") or [])


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True); self.anchors: list[dict[str, str | None]] = []
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a": self.anchors.append({str(key).lower(): value for key, value in attrs})


def dashboard_attachment_isolation_report(page: str) -> dict[str, Any]:
    parser = _AnchorParser(); parser.feed(str(page or ""))
    errors: list[str] = []; docx_links = []; download_links = []
    for anchor in parser.anchors:
        href = str(anchor.get("href") or ""); parsed = urlsplit(href); decoded_path = unquote(parsed.path or "")
        if decoded_path.lower().endswith(".docx"):
            docx_links.append(href); errors.append("dashboard must summarize DOCX artifacts without linking them")
        if "download" in anchor:
            download_links.append(href); errors.append("dashboard must not expose browser download anchors for final artifacts")
    errors = list(dict.fromkeys(errors))
    return {
        "schema": SCHEMA, "profile": PROFILE_ID, "status": "PASS" if not errors else "FAIL",
        "docx_link_count": len(docx_links), "download_anchor_count": len(download_links), "errors": errors,
        "policy": "HTML_SUMMARY_ONLY_DOCX_IN_SESSION_CHAT_TAIL",
    }


def dashboard_attachment_isolation_gate(page: str) -> tuple[bool, list[str]]:
    report = dashboard_attachment_isolation_report(page)
    return report.get("status") == "PASS", list(report.get("errors") or [])
