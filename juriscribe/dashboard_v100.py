from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from . import dashboard_v97 as base
from .browser_delivery import render_docx_download_anchor
from .evidence_traceability import build_user_artifact_index

DASHBOARD_DESIGN_PROFILE = "JURISCRIBE_EDITORIAL_WORKBENCH_V4"
DASHBOARD_TITLE = base.DASHBOARD_TITLE
DASHBOARD_SECTIONS = base.DASHBOARD_SECTIONS
dashboard_state_digest = base.dashboard_state_digest
DASHBOARD_BINDING_KEYS = base.DASHBOARD_BINDING_KEYS

EXTRA_CSS = r'''
.docx-download{background:#f4f8f5!important;border-color:#7f9b86!important;color:#23462e!important;font-weight:820!important}
.docx-download::before{content:"DOCX · ";font-size:.68em;letter-spacing:.04em}
'''


def _payload(state: dict[str, Any] | Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _upgrade_document_links(page: str, state: dict[str, Any] | Any) -> str:
    """Replace legacy document-open anchors with native same-session DOCX downloads.

    Earlier workbench layers remain intact and version-addressable. The v4 renderer
    upgrades only document recall actions whose runtime projection already resolves
    to a safe DOCX href; non-DOCX paths receive no downloadable action.
    """
    index = build_user_artifact_index(_payload(state))
    for record in index.get("records") or []:
        href = str(record.get("richiamo") or "")
        role = str(record.get("ruolo") or "artifact")
        if not href:
            continue
        escaped = html.escape(href, quote=True)
        replacements = (
            (f'<a href="{escaped}">Apri artefatto</a>', render_docx_download_anchor(href, role, "Scarica DOCX")),
            (f'<a href="{escaped}">Apri artefatto dichiarato</a>', render_docx_download_anchor(href, role, "Scarica DOCX dichiarato")),
        )
        for old, new in replacements:
            page = page.replace(old, new)
    return page


def render_session_dashboard(state: dict[str, Any] | Any, output: str | Path) -> Path:
    out = Path(output)
    base.render_session_dashboard(state, out)
    page = out.read_text(encoding="utf-8")
    page = page.replace("</style>", EXTRA_CSS + "</style>", 1)
    page = _upgrade_document_links(page, state)
    marker = '<meta name="juriscribe-download-contract" content="docx-only-browser-native-v1">'
    page = page.replace("</head>", marker + "</head>", 1)
    out.write_text(page, encoding="utf-8")
    return out
