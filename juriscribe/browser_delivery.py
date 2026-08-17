from __future__ import annotations

import html
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from .modes import required_artifact_roles

PROFILE_ID = "JURISCRIBE_BROWSER_DOCX_DELIVERY_V1"
SCHEMA = "juriscribe-browser-docx-delivery/v1"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ATTACH = "ATTACH"
SURFACE_ROLE = "session_dashboard"
DOWNLOAD_ATTR = "data-juriscribe-download-role"
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


def _artifact_root(state: Any) -> Path | None:
    s = _payload(state)
    workspace = str((s.get("runtime") or {}).get("workspace_base") or "").strip()
    if not workspace:
        return None
    return (Path(workspace) / "artifacts").resolve(strict=False)


def relative_docx_href(state: Any, record: dict[str, Any] | None) -> str | None:
    if not record:
        return None
    root = _artifact_root(state)
    raw_path = str(record.get("path") or "").strip()
    if root is None or not raw_path:
        return None
    raw = Path(raw_path)
    absolute = raw if raw.is_absolute() else (Path.cwd() / raw)
    resolved = absolute.resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    if relative.suffix.lower() != ".docx":
        return None
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None
    return "./" + quote(relative.as_posix(), safe="/._-@")


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


def build_download_descriptor(state: Any, record: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    item = dict(record or {})
    role = str(item.get("role") or "").strip()
    errors: list[str] = []
    if not role:
        errors.append("downloadable artifact role missing")
    if role == SURFACE_ROLE:
        errors.append("browser workbench HTML is a surface, not a downloadable artifact")
    if str(item.get("delivery_class") or "").upper() != ATTACH:
        errors.append(f"downloadable artifact is not ATTACH: {role or 'unknown'}")
    path = str(item.get("path") or "").strip()
    if not path or Path(path).suffix.lower() != ".docx":
        errors.append(f"downloadable artifact must end in .docx: {role or 'unknown'}")
    if item.get("readback") != "PASS":
        errors.append(f"downloadable artifact readback is not PASS: {role or 'unknown'}")
    if str(item.get("format") or "DOCX").upper() != "DOCX":
        errors.append(f"downloadable artifact format is not DOCX: {role or 'unknown'}")
    media_type = str(item.get("media_type") or DOCX_MIME)
    if media_type != DOCX_MIME:
        errors.append(f"downloadable artifact media type mismatch: {role or 'unknown'}")
    if item.get("verified_format") not in (None, "", "DOCX"):
        errors.append(f"materialized downloadable artifact is not verified as DOCX: {role or 'unknown'}")
    if "materialized" in item and item.get("materialized") is not True:
        errors.append(f"downloadable artifact is not materially sealed: {role or 'unknown'}")

    href = relative_docx_href(state, item)
    if not href:
        errors.append(f"downloadable artifact has no safe same-session DOCX href: {role or 'unknown'}")
    else:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not href.startswith("./"):
            errors.append(f"download href is not a plain same-session relative URL: {role or 'unknown'}")
        decoded = unquote(parsed.path)
        if not decoded.lower().endswith(".docx"):
            errors.append(f"download href does not resolve to DOCX: {role or 'unknown'}")

    filename = Path(path).name if path else "artifact.docx"
    descriptor = {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "role": role,
        "href": href,
        "download_filename": filename,
        "media_type": DOCX_MIME,
        "content_disposition": content_disposition(filename),
        "same_session_relative": bool(href and href.startswith("./")),
        "browser_native_anchor": True,
        "javascript_required": False,
        "global_browser_claim": False,
        "status": "PASS" if not errors else "FAIL",
    }
    return descriptor, list(dict.fromkeys(errors))


def build_browser_delivery_manifest(state: Any, *, require_all: bool = True) -> dict[str, Any]:
    s = _payload(state)
    expected = required_docx_roles(s)
    artifacts = [dict(item) for item in s.get("artifacts") or []]
    by_role = {str(item.get("role") or ""): item for item in artifacts if item.get("role")}
    errors: list[str] = []
    records: list[dict[str, Any]] = []

    if require_all:
        for role in sorted(expected):
            if role not in by_role:
                errors.append(f"required downloadable DOCX artifact missing: {role}")

    candidate_roles = set(expected if require_all else ())
    candidate_roles.update(
        str(item.get("role") or "")
        for item in artifacts
        if str(item.get("delivery_class") or "").upper() == ATTACH and item.get("role")
    )
    for role in sorted(candidate_roles):
        item = by_role.get(role)
        if not item:
            continue
        descriptor, descriptor_errors = build_download_descriptor(s, item)
        records.append(descriptor)
        errors.extend(descriptor_errors)
        if require_all and role not in expected:
            errors.append(f"non-final role entered downloadable attachment set: {role}")

    dashboard = by_role.get(SURFACE_ROLE)
    if dashboard and str(dashboard.get("delivery_class") or "").upper() == ATTACH:
        errors.append("session dashboard HTML may not enter downloadable attachment set")

    for item in artifacts:
        if str(item.get("delivery_class") or "").upper() != ATTACH:
            continue
        if Path(str(item.get("path") or "")).suffix.lower() != ".docx":
            errors.append(f"non-DOCX attachment is forbidden: {item.get('role')}")

    errors = list(dict.fromkeys(errors))
    return {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "status": "PASS" if not errors else "FAIL",
        "required_docx_roles": sorted(expected),
        "records": records,
        "errors": errors,
        "downloadable_artifacts_only_docx": not any(Path(str(item.get("path") or "")).suffix.lower() != ".docx" for item in artifacts if str(item.get("delivery_class") or "").upper() == ATTACH),
        "dashboard_is_browser_surface_not_attachment": not bool(dashboard and str(dashboard.get("delivery_class") or "").upper() == ATTACH),
        "assistant_agnostic": True,
        "user_agent_agnostic_runtime_contract": True,
        "browser_native_download_links": True,
        "http_attachment_headers_declared": True,
        "global_browser_behavior_claim": False,
    }


def browser_docx_delivery_gate(state: Any) -> tuple[bool, list[str]]:
    manifest = build_browser_delivery_manifest(state, require_all=True)
    return manifest.get("status") == "PASS", list(manifest.get("errors") or [])


def render_docx_download_anchor(href: str, role: str, label: str = "Scarica DOCX") -> str:
    parsed = urlsplit(str(href or ""))
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not str(href).startswith("./"):
        raise ValueError("DOCX download anchor requires a same-session relative href")
    if not unquote(parsed.path).lower().endswith(".docx"):
        raise ValueError("DOCX download anchor requires a .docx target")
    return (
        f'<a class="docx-download" href="{html.escape(str(href), quote=True)}" '
        f'download type="{DOCX_MIME}" {DOWNLOAD_ATTR}="{html.escape(str(role), quote=True)}" '
        f'aria-label="{html.escape(str(label), quote=True)} — DOCX">{html.escape(str(label))}</a>'
    )


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.anchors.append({str(key).lower(): value for key, value in attrs})


def dashboard_docx_links_report(state: Any, page: str) -> dict[str, Any]:
    s = _payload(state)
    parser = _AnchorParser()
    parser.feed(str(page or ""))
    anchors = parser.anchors
    artifacts = [dict(item) for item in s.get("artifacts") or []]
    expected_records = [item for item in artifacts if str(item.get("delivery_class") or "").upper() == ATTACH]
    expected: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for item in expected_records:
        role = str(item.get("role") or "")
        descriptor, descriptor_errors = build_download_descriptor(s, item)
        expected[role] = descriptor
        errors.extend(descriptor_errors)

    marked = [item for item in anchors if DOWNLOAD_ATTR in item]
    linked_roles = {str(item.get(DOWNLOAD_ATTR) or "") for item in marked}
    for role, descriptor in expected.items():
        matches = [item for item in marked if str(item.get(DOWNLOAD_ATTR) or "") == role]
        if not matches:
            errors.append(f"dashboard lacks browser-native DOCX download link: {role}")
            continue
        for anchor in matches:
            href = str(anchor.get("href") or "")
            if href != str(descriptor.get("href") or ""):
                errors.append(f"dashboard DOCX href differs from sealed same-session href: {role}")
            if "download" not in anchor:
                errors.append(f"dashboard DOCX link lacks download attribute: {role}")
            if str(anchor.get("type") or "") != DOCX_MIME:
                errors.append(f"dashboard DOCX link lacks canonical MIME annotation: {role}")
            if "target" in anchor:
                errors.append(f"dashboard DOCX link must not depend on a new browsing context: {role}")
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not href.startswith("./"):
                errors.append(f"dashboard DOCX link is not same-session relative: {role}")
            if not unquote(parsed.path).lower().endswith(".docx"):
                errors.append(f"dashboard download target is not DOCX: {role}")

    for anchor in anchors:
        if "download" not in anchor:
            continue
        href = str(anchor.get("href") or "")
        parsed = urlsplit(href)
        if not href.startswith("./") or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not unquote(parsed.path).lower().endswith(".docx"):
            errors.append("dashboard contains a download attribute on a non-DOCX or non-local target")

    errors = list(dict.fromkeys(errors))
    return {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "status": "PASS" if not errors else "FAIL",
        "expected_download_roles": sorted(expected),
        "linked_download_roles": sorted(role for role in linked_roles if role),
        "marked_download_link_count": len(marked),
        "errors": errors,
        "javascript_required": False,
        "download_attribute_required": True,
        "same_session_relative_required": True,
        "docx_only_required": True,
    }


def dashboard_docx_links_gate(state: Any, page: str) -> tuple[bool, list[str]]:
    report = dashboard_docx_links_report(state, page)
    return report.get("status") == "PASS", list(report.get("errors") or [])
