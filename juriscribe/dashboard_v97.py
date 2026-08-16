from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from . import dashboard_v96 as base

DASHBOARD_DESIGN_PROFILE = "JURISCRIBE_EDITORIAL_WORKBENCH_V3"
DASHBOARD_TITLE = base.DASHBOARD_TITLE
DASHBOARD_SECTIONS = base.DASHBOARD_SECTIONS
dashboard_state_digest = base.dashboard_state_digest
DASHBOARD_BINDING_KEYS = base.DASHBOARD_BINDING_KEYS

EXTRA_CSS = r'''
.governance-panel{margin-top:18px;padding:28px;border:1px solid var(--line);border-radius:16px;background:var(--paper);box-shadow:0 8px 24px #28221c0c;scroll-margin-top:18px}.governance-panel h2{margin:7px 0 9px;font:700 clamp(1.55rem,2.2vw,2.25rem)/1.12 var(--serif);letter-spacing:-.012em}.governance-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:18px}.governance-card{border:1px solid var(--line);border-radius:12px;padding:15px;background:#faf8f3}.governance-card b{display:block;color:var(--navy);font:800 .76rem var(--ui);letter-spacing:.04em;text-transform:uppercase}.governance-card p{margin:.55rem 0 0;line-height:1.5}.concept-list{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.concept-chip{border:1px solid var(--line);border-radius:999px;padding:5px 9px;background:#fff;font:760 .7rem var(--ui)}.proof-status{display:inline-block;border-radius:999px;padding:6px 10px;background:var(--soft);font:850 .7rem var(--ui);letter-spacing:.06em}.proof-status.pass{background:var(--positive);color:var(--positive-ink)}.cycle-grid{display:grid;gap:9px;margin-top:16px}.cycle-row{display:grid;grid-template-columns:70px 1fr 90px;gap:10px;align-items:center;border-top:1px solid var(--line);padding-top:9px}.cycle-row:first-child{border-top:0}.cycle-row span:last-child{font:800 .72rem var(--ui)}@media(max-width:760px){.governance-grid{grid-template-columns:1fr}.cycle-row{grid-template-columns:55px 1fr 72px}}@media print{.governance-panel{box-shadow:none;border-color:#bbb}}
'''


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _get(state: dict[str, Any] | Any, key: str, default=None):
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _configuration_section(state) -> str:
    setup = _get(state, "setup", {}) or {}
    accepted = setup.get("accepted", setup if setup.get("status") == "ACCEPTED" else {}) or {}
    quality = _get(state, "quality", {}) or {}
    check = quality.get("generation_configuration") or {}
    abstract = accepted.get("generation_abstract") or "Configurazione non ancora accettata."
    concepts = accepted.get("key_concepts") or []
    length = accepted.get("length_words") or []
    length_text = f"{length[0]}–{length[1]} parole" if isinstance(length, (list, tuple)) and len(length) == 2 else "da definire"
    status = str(check.get("status") or ("ACCETTATA" if accepted.get("generation_abstract") else "DA CONFIGURARE"))
    chips = "".join(f'<span class="concept-chip">{_esc(item)}</span>' for item in concepts)
    return (
        '<section class="governance-panel" id="generation-configuration" aria-labelledby="generation-configuration-title">'
        '<div class="kicker">Contratto editoriale prima della scrittura</div>'
        '<h2 id="generation-configuration-title">Configurazione di generazione</h2>'
        '<p class="purpose">La configurazione accettata dall’utente non è un suggerimento: vincola il candidato che può entrare nel runtime.</p>'
        '<div class="governance-grid">'
        f'<article class="governance-card"><b>Abstract</b><p>{_esc(abstract)}</p></article>'
        f'<article class="governance-card"><b>Lunghezza</b><p>{_esc(length_text)}</p><p>Conformità: {_esc(status)}</p></article>'
        f'<article class="governance-card"><b>Concetti chiave</b><div class="concept-list">{chips or "<span class=\"concept-chip\">da definire</span>"}</div></article>'
        '</div></section>'
    )


def _plagiarism_section(state) -> str:
    quality = _get(state, "quality", {}) or {}
    record = quality.get("plagiarism") or {}
    status = str(record.get("status") or "NON ESEGUITO")
    status_class = " pass" if status == "PASS" else ""
    proof = record.get("proof_statement") or "Il controllo verrà eseguito sul candidato finale contro il corpus testuale registrato nel runtime."
    covered = len(record.get("covered_source_ids") or [])
    missing = len(record.get("missing_source_ids") or [])
    findings = int(record.get("prohibited_findings", 0) or 0)
    return (
        '<section class="governance-panel" id="anti-plagiarism" aria-labelledby="anti-plagiarism-title">'
        '<div class="kicker">Originalità dimostrabile</div><h2 id="anti-plagiarism-title">Controllo anti-plagio</h2>'
        f'<span class="proof-status{status_class}">{_esc(status)}</span><p class="purpose">{_esc(proof)}</p>'
        '<div class="governance-grid">'
        f'<article class="governance-card"><b>Fonti coperte</b><p>{covered}</p></article>'
        f'<article class="governance-card"><b>Fonti mancanti</b><p>{missing}</p></article>'
        f'<article class="governance-card"><b>Sovrapposizioni vietate</b><p>{findings}</p></article>'
        '</div></section>'
    )


def _saturation_section(state) -> str:
    review = _get(state, "review", {}) or {}
    record = review.get("delivery_saturation") or {}
    status = str(record.get("status") or "NON ESEGUITA")
    status_class = " pass" if status == "PASS" else ""
    cycles = []
    for cycle in record.get("cycles") or []:
        cycles.append(
            '<div class="cycle-row">'
            f'<span>Ciclo {int(cycle.get("cycle", 0))}</span>'
            f'<span>{"nessun nuovo blocker" if not cycle.get("new_findings") else str(len(cycle.get("new_findings") or [])) + " nuovi blocker"}</span>'
            f'<span>{_esc(cycle.get("status") or "")}</span></div>'
        )
    return (
        '<section class="governance-panel" id="predelivery-saturation" aria-labelledby="predelivery-saturation-title">'
        '<div class="kicker">Fixed point prima della consegna</div><h2 id="predelivery-saturation-title">Saturazione e ri-controllo ciclico</h2>'
        f'<span class="proof-status{status_class}">{_esc(status)}</span>'
        '<p class="purpose">Il candidato è consegnabile solo quando configurazione, originalità, qualità, fonti, provenance, review severa, dossier, tracciabilità e readback restano verdi in ri-controlli ciclici indipendenti dall’ordine.</p>'
        f'<div class="cycle-grid">{"".join(cycles) if cycles else "<p>Nessun ciclo di saturazione ancora registrato.</p>"}</div></section>'
    )


def _inject_navigation(page: str) -> str:
    extra = (
        '<li><a href="#generation-configuration"><span>Configurazione</span><span class="n">C</span></a></li>'
        '<li><a href="#anti-plagiarism"><span>Anti-plagio</span><span class="n">P</span></a></li>'
        '<li><a href="#predelivery-saturation"><span>Saturazione</span><span class="n">S</span></a></li>'
    )
    return page.replace('</ul></nav>', extra + '</ul></nav>', 1)


def render_session_dashboard(state: dict[str, Any] | Any, output: str | Path) -> Path:
    out = Path(output)
    base.render_session_dashboard(state, out)
    page = out.read_text(encoding="utf-8")
    page = page.replace("</style>", EXTRA_CSS + "</style>", 1)
    page = _inject_navigation(page)
    sections = _configuration_section(state) + _plagiarism_section(state) + _saturation_section(state)
    marker = '<section class="evidence-map" id="overall-outcome"'
    if marker in page:
        page = page.replace(marker, sections + marker, 1)
    else:
        page = page.replace('<footer class="footer">', sections + '<footer class="footer">', 1)
    out.write_text(page, encoding="utf-8")
    return out
