from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from . import dashboard_v9 as base
from .editorial_artifacts import build_dashboard_inference_view
from .evidence_traceability import build_dashboard_evidence_coverage

DASHBOARD_DESIGN_PROFILE = "JURISCRIBE_EDITORIAL_WORKBENCH_V2"
DASHBOARD_TITLE = base.DASHBOARD_TITLE
DASHBOARD_SECTIONS = base.DASHBOARD_SECTIONS
dashboard_state_digest = base.dashboard_state_digest
DASHBOARD_BINDING_KEYS = base.DASHBOARD_BINDING_KEYS

EXTRA_CSS = r'''
.evidence-map{margin-top:18px;padding:28px;border:1px solid var(--line);border-radius:16px;background:var(--paper);box-shadow:0 8px 24px #28221c0c;scroll-margin-top:18px}.evidence-map h2{margin:7px 0 9px;font:700 clamp(1.55rem,2.2vw,2.25rem)/1.12 var(--serif);letter-spacing:-.012em}.outcome-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.outcome-state{border:1px solid var(--line);border-radius:999px;padding:7px 11px;background:var(--soft);font:850 .72rem var(--ui);letter-spacing:.07em}.outcome-state.ready{background:var(--positive);color:var(--positive-ink)}.compressed{margin:17px 0 0;padding-left:1.25rem}.compressed li{margin:.45rem 0}.coverage-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:18px}.coverage-cell{border:1px solid var(--line);border-radius:11px;padding:13px;background:#faf8f3}.coverage-cell b{display:block;color:var(--navy);font:780 1.45rem/1 var(--ui)}.coverage-cell span{display:block;margin-top:6px;color:var(--muted);font:720 .72rem var(--ui)}.artifact-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:18px}.artifact-card{border:1px solid var(--line);border-radius:13px;padding:17px;background:linear-gradient(180deg,#fff,#faf8f3)}.artifact-card h3{margin:0;color:var(--navy);font:750 1.05rem var(--serif)}.artifact-card p{margin:7px 0;color:#555b61}.artifact-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:13px}.artifact-actions a{display:inline-block;border:1px solid var(--strong);border-radius:8px;padding:7px 10px;background:#fff;text-decoration:none;font:780 .72rem var(--ui)}.artifact-status{display:inline-block;margin-top:9px;border-radius:999px;padding:4px 8px;background:var(--soft);color:var(--muted);font:800 .64rem var(--ui);letter-spacing:.06em}.artifact-status.available{background:var(--positive);color:var(--positive-ink)}.trace-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding-bottom:16px;border-bottom:1px solid var(--line)}.trace-records{display:grid;gap:14px;margin-top:18px}.trace-meta{margin-top:12px;color:var(--muted);font:.74rem var(--ui)}@media(max-width:760px){.coverage-grid,.artifact-grid{grid-template-columns:1fr}.outcome-head,.trace-head{display:block}.outcome-state{display:inline-block;margin-top:8px}}@media print{.evidence-map{box-shadow:none;border-color:#bbb}.artifact-actions{display:none!important}}
'''


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _outcome_section(coverage: dict[str, Any]) -> str:
    outcome = coverage["esito_complessivo"]
    counts = outcome.get("conteggi_dossier") or {}
    state = str(outcome.get("stato") or "NON PRONTO")
    cells = (
        (counts.get("evidence_dossier", 0), "elementi probatori"),
        (counts.get("source_register", 0), "fonti"),
        (counts.get("inference_register", 0), "inferenze"),
        (counts.get("transformation_ledger", 0), "trasformazioni"),
    )
    grid = "".join(f'<div class="coverage-cell"><b>{int(value)}</b><span>{_esc(label)}</span></div>' for value, label in cells)
    summary = "".join(f"<li>{_esc(item)}</li>" for item in outcome.get("sintesi_compressa") or [])
    ready = " ready" if state == "PRONTO" else ""
    return (
        '<section class="evidence-map" id="overall-outcome" aria-labelledby="overall-outcome-title">'
        '<div class="outcome-head"><div><div class="kicker">Esito complessivo</div>'
        f'<h2 id="overall-outcome-title">{_esc(outcome.get("titolo"))}</h2></div>'
        f'<span class="outcome-state{ready}">{_esc(state)}</span></div>'
        f'<ul class="compressed">{summary}</ul><div class="coverage-grid">{grid}</div></section>'
    )


def _artifact_section(coverage: dict[str, Any]) -> str:
    index = coverage["artifact_index"]
    cards = []
    for record in index.get("records") or []:
        status = str(record.get("stato") or "ATTESO")
        available = " available" if status == "DISPONIBILE" else ""
        actions = []
        if record.get("ancora_dashboard"):
            actions.append(f'<a href="{_esc(record["ancora_dashboard"])}">Vai al contenuto</a>')
        if record.get("richiamo"):
            actions.append(f'<a href="{_esc(record["richiamo"])}">Apri artefatto</a>')
        cards.append(
            '<article class="artifact-card">'
            f'<h3>{_esc(record.get("titolo"))}</h3><p>{_esc(record.get("funzione"))}</p>'
            f'<span class="artifact-status{available}">{_esc(status)}</span>'
            f'<div class="artifact-actions">{"".join(actions)}</div></article>'
        )
    content = "".join(cards) if cards else '<div class="empty"><b>00</b><p><strong>Nessun artefatto finale ancora atteso.</strong><br>L’indice si popola dopo la selezione della modalità.</p></div>'
    return (
        '<section class="evidence-map" id="artifact-index" aria-labelledby="artifact-index-title">'
        '<div class="kicker">Consegna richiamabile</div>'
        f'<h2 id="artifact-index-title">{_esc(index.get("titolo"))}</h2><p class="purpose">{_esc(index.get("finalita"))}</p>'
        f'<div class="artifact-grid">{content}</div></section>'
    )


def _trace_section(coverage: dict[str, Any]) -> str:
    trace = coverage["evidence_traceability"]
    records = trace.get("records") or []
    rows = []
    for index, record in enumerate(records, 1):
        title = record.get("proposizione") or record.get("claim_id") or record.get("riferimento_evidenza")
        locator = record.get("collocazione_nell_artefatto") or "collocazione non dichiarata"
        body_record = dict(record)
        declared = dict(body_record.get("artefatto_dichiarato") or {})
        href = declared.pop("richiamo", None)
        if declared:
            body_record["artefatto_dichiarato"] = declared
        elif "artefatto_dichiarato" in body_record:
            body_record.pop("artefatto_dichiarato", None)
        action = f'<div class="artifact-actions"><a href="{_esc(href)}">Apri artefatto dichiarato</a></div>' if href else ""
        rows.append(
            '<details class="record evidence-record" open><summary>'
            f'<span class="idx">{index:02d}</span><span><span class="title">{_esc(title)}</span><span class="ref">{_esc(locator)}</span></span>'
            f'<span class="badges"><span class="badge">{_esc(record.get("stato") or "EVIDENZA")}</span></span></summary>'
            f'<div class="record-body">{base._render(body_record)}{action}</div></details>'
        )
    if rows:
        body = f'<div class="trace-records">{"".join(rows)}</div>'
    else:
        body = '<div class="empty"><b>00</b><p><strong>Nessuna evidenza di artefatto registrata.</strong><br>Il registro resta vuoto finché non viene dichiarata una collocazione probatoria nel prodotto.</p></div>'
    cov = trace.get("copertura") or {}
    meta = f'{cov.get("evidenze_proiettate", 0)}/{cov.get("evidenze_registrate", 0)} evidenze proiettate · copertura {_esc(cov.get("stato", "DA_COMPLETARE"))}'
    return (
        '<section class="evidence-map" id="evidence-traceability" aria-labelledby="evidence-traceability-title">'
        '<div class="trace-head"><div><div class="kicker">Tracciabilita lossless</div>'
        f'<h2 id="evidence-traceability-title">{_esc(trace.get("titolo"))}</h2><p class="purpose">{_esc(trace.get("finalita"))}</p></div>'
        f'<span class="count">{len(records)} evidenze</span></div>{body}<p class="trace-meta">{meta}</p></section>'
    )


def _inject_navigation(page: str, coverage: dict[str, Any]) -> str:
    trace_count = len((coverage.get("evidence_traceability") or {}).get("records") or [])
    artifact_count = len((coverage.get("artifact_index") or {}).get("records") or [])
    extra = (
        '<li><a href="#overall-outcome"><span>Esito complessivo</span><span class="n">Σ</span></a></li>'
        f'<li><a href="#artifact-index"><span>Artefatti</span><span class="n">{artifact_count}</span></a></li>'
        f'<li><a href="#evidence-traceability"><span>Tracciabilita</span><span class="n">{trace_count}</span></a></li>'
    )
    return page.replace('</ul></nav>', extra + '</ul></nav>', 1)


def render_session_dashboard(state: dict[str, Any] | Any, output: str | Path) -> Path:
    out = Path(output)
    base.render_session_dashboard(state, out)
    aggregate = build_dashboard_inference_view(state)
    coverage = build_dashboard_evidence_coverage(state, aggregate)
    page = out.read_text(encoding="utf-8")
    page = page.replace("</style>", EXTRA_CSS + "</style>", 1)
    page = _inject_navigation(page, coverage)
    sections = _outcome_section(coverage) + _artifact_section(coverage) + _trace_section(coverage)
    marker = '<section class="dossier" id="evidence-dossier"'
    if marker in page:
        page = page.replace(marker, sections + marker, 1)
    else:
        page = page.replace('<footer class="footer">', sections + '<footer class="footer">', 1)
    out.write_text(page, encoding="utf-8")
    return out
