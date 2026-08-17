from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from . import dashboard_v97 as base
from .artifact_atlas import build_artifact_atlas

DASHBOARD_DESIGN_PROFILE = "JURISCRIBE_EDITORIAL_WORKBENCH_V4"
DASHBOARD_TITLE = base.DASHBOARD_TITLE
DASHBOARD_SECTIONS = base.DASHBOARD_SECTIONS
dashboard_state_digest = base.dashboard_state_digest
DASHBOARD_BINDING_KEYS = base.DASHBOARD_BINDING_KEYS

EXTRA_CSS = r'''
.chat-tail-note{margin-top:12px;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:#f7f5ef;color:#45494e;font:.78rem/1.5 var(--ui)}
.chat-tail-note b{color:var(--navy)}
'''
_DOCX_ANCHOR_RE = re.compile(r'<a\b(?P<attrs>[^>]*)href="(?P<href>[^"]+)"(?P<tail>[^>]*)>(?P<label>.*?)</a>', re.IGNORECASE | re.DOTALL)


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _strip_docx_links(page: str) -> str:
    def repl(match: re.Match[str]) -> str:
        href = unquote(html.unescape(match.group("href") or ""))
        if href.lower().split("?", 1)[0].split("#", 1)[0].endswith(".docx"):
            return '<span class="artifact-chat-tail">Disponibile come allegato DOCX in coda alla sessione-chat</span>'
        attrs = (match.group("attrs") or "") + (match.group("tail") or "")
        if re.search(r'\bdownload(?:\s|=|$)', attrs, re.IGNORECASE):
            return '<span class="artifact-chat-tail">Download disponibile nella sessione-chat</span>'
        return match.group(0)
    return _DOCX_ANCHOR_RE.sub(repl, page)


def _chat_tail_summary(state: dict[str, Any] | Any) -> str:
    atlas = build_artifact_atlas(state)
    material = [item for item in atlas.get("artefatti_materiali") or [] if str(item.get("ruolo") or "") != "session_dashboard"]
    ready = sum(1 for item in material if str(item.get("stato") or "").upper() in {"DISPONIBILE", "PASS", "REGISTRATO"})
    return (
        '<div class="chat-tail-note" id="chat-tail-delivery-summary">'
        '<b>Consegna documentale.</b> '
        f'{ready}/{len(material)} artefatti documentali risultano materializzati o registrati. '
        'La dashboard ne riepiloga sinteticamente contenuto, funzione e stato; i file finali sono allegati in formato DOCX in coda alla sessione-chat e non sono linkati da questa pagina.'
        '</div>'
    )


def render_session_dashboard(state: dict[str, Any] | Any, output: str | Path) -> Path:
    out = Path(output)
    base.render_session_dashboard(state, out)
    page = out.read_text(encoding="utf-8")
    page = page.replace("</style>", EXTRA_CSS + "</style>", 1)
    page = _strip_docx_links(page)
    marker = '<section class="evidence-map" id="artifact-index"'
    note = _chat_tail_summary(state)
    if marker in page:
        page = page.replace(marker, note + marker, 1)
    else:
        page = page.replace('<footer class="footer">', note + '<footer class="footer">', 1)
    page = page.replace("</head>", '<meta name="juriscribe-delivery-contract" content="html-summary-docx-chat-tail-v1"></head>', 1)
    out.write_text(page, encoding="utf-8")
    return out
