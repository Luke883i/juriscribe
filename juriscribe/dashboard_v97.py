from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from . import dashboard_v96 as base
from .artifact_atlas import build_artifact_atlas
from .dashboard_v9 import _render as _render_semantic

DASHBOARD_DESIGN_PROFILE = "JURISCRIBE_EDITORIAL_WORKBENCH_V3"
DASHBOARD_TITLE = base.DASHBOARD_TITLE
DASHBOARD_SECTIONS = base.DASHBOARD_SECTIONS
dashboard_state_digest = base.dashboard_state_digest
DASHBOARD_BINDING_KEYS = base.DASHBOARD_BINDING_KEYS

EXTRA_CSS = r'''
.governance-panel,.artifact-atlas{margin-top:18px;padding:28px;border:1px solid var(--line);border-radius:16px;background:var(--paper);box-shadow:0 8px 24px #28221c0c;scroll-margin-top:18px}.governance-panel h2,.artifact-atlas h2{margin:7px 0 9px;font:700 clamp(1.55rem,2.2vw,2.25rem)/1.12 var(--serif);letter-spacing:-.012em}#generation-configuration{border-top:4px solid var(--gold);background:linear-gradient(180deg,#fffdf8,#fffdfa)}#anti-plagiarism{border-top:4px solid var(--wine);background:linear-gradient(180deg,#fff9fa,#fffdfa)}#predelivery-saturation{border-top:4px solid var(--blue);background:linear-gradient(180deg,#f8fbfd,#fffdfa)}.artifact-atlas{border-top:4px solid #745688;background:linear-gradient(180deg,#fbf8ff,#fffdfa)}.governance-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:18px}.governance-card{border:1px solid var(--line);border-radius:12px;padding:15px;background:#faf8f3}.governance-card:nth-child(1){box-shadow:inset 4px 0 0 var(--gold)}.governance-card:nth-child(2){box-shadow:inset 4px 0 0 var(--blue)}.governance-card:nth-child(3){box-shadow:inset 4px 0 0 var(--wine)}.governance-card b{display:block;color:var(--navy);font:800 .76rem var(--ui);letter-spacing:.04em;text-transform:uppercase}.governance-card p{margin:.55rem 0 0;line-height:1.5}.concept-list{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.concept-chip{border:1px solid #cab98d;border-radius:999px;padding:5px 9px;background:#fff9e9;color:#5c4823;font:760 .7rem var(--ui)}.proof-status{display:inline-block;border-radius:999px;padding:6px 10px;background:var(--soft);font:850 .7rem var(--ui);letter-spacing:.06em}.proof-status.pass{background:var(--positive);color:var(--positive-ink)}.cycle-grid{display:grid;gap:9px;margin-top:16px}.cycle-row{display:grid;grid-template-columns:70px 1fr 90px;gap:10px;align-items:center;border-top:1px solid var(--line);padding-top:9px}.cycle-row:first-child{border-top:0}.cycle-row span:last-child{font:800 .72rem var(--ui)}.atlas-summary{margin:15px 0 0;padding-left:1.2rem}.atlas-summary li{margin:.45rem 0}.atlas-group{margin-top:24px}.atlas-group-head{display:flex;justify-content:space-between;align-items:end;gap:12px;border-bottom:1px solid var(--line);padding-bottom:10px}.atlas-group-head h3{margin:0;font:720 1.25rem var(--serif);color:var(--navy)}.atlas-group-head span{font:760 .7rem var(--ui);color:var(--muted)}.atlas-records{display:grid;gap:12px;margin-top:14px}.atlas-record{border:1px solid var(--line);border-left:4px solid var(--navy);border-radius:13px;background:#fff;overflow:hidden}.atlas-record:nth-child(4n+2){border-left-color:var(--wine)}.atlas-record:nth-child(4n+3){border-left-color:var(--gold)}.atlas-record:nth-child(4n+4){border-left-color:#745688}.atlas-record summary{cursor:pointer;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:start;padding:16px 18px;list-style:none}.atlas-record summary::-webkit-details-marker{display:none}.atlas-title{display:block;color:var(--navy);font:760 1rem var(--serif)}.atlas-summary-line{display:block;margin-top:5px;color:var(--muted);font:.78rem/1.45 var(--ui)}.atlas-badges{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.atlas-badge{border:1px solid var(--line);border-radius:999px;padding:4px 8px;background:var(--soft);font:800 .62rem var(--ui);letter-spacing:.04em}.atlas-body{border-top:1px solid var(--line);padding:17px 18px;background:#fcfbf8}.atlas-function{margin:0 0 12px;color:#4d5359}.atlas-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.atlas-actions a{display:inline-block;border:1px solid var(--strong);border-radius:8px;padding:7px 10px;background:#fff;text-decoration:none;font:780 .72rem var(--ui)}@media(max-width:760px){.governance-grid{grid-template-columns:1fr}.cycle-row{grid-template-columns:55px 1fr 72px}.atlas-record summary{grid-template-columns:1fr}.atlas-badges{justify-content:flex-start}}@media print{.governance-panel,.artifact-atlas{box-shadow:none;border-color:#bbb}.atlas-record{break-inside:avoid}.atlas-actions{display:none!important}}
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
    preview = setup.get("generation_preview") or {}
    abstract = accepted.get("generation_abstract") or preview.get("abstract") or "Configurazione non ancora proposta."
    concepts = accepted.get("key_concepts") or preview.get("key_concepts") or []
    length = accepted.get("length_words") or preview.get("length_words") or []
    length_text = f"{length[0]}–{length[1]} parole" if isinstance(length, (list, tuple)) and len(length) == 2 else "da definire"
    status = str(check.get("status") or ("ACCETTATA" if accepted.get("generation_abstract") else "DA CONFIGURARE"))
    chips = "".join(f'<span class="concept-chip">{_esc(item)}</span>' for item in concepts)
    concepts_html = chips or '<span class="concept-chip">da definire</span>'
    return (
        '<section class="governance-panel" id="generation-configuration" aria-labelledby="generation-configuration-title">'
        '<div class="kicker">Contratto editoriale prima della scrittura</div>'
        '<h2 id="generation-configuration-title">Configurazione di generazione</h2>'
        '<p class="purpose">La configurazione sottoposta all’utente non è un suggerimento: dopo l’accettazione diventa un vincolo meccanico del candidato e degli artefatti narrativi finali.</p>'
        '<div class="governance-grid">'
        f'<article class="governance-card"><b>Abstract</b><p>{_esc(abstract)}</p></article>'
        f'<article class="governance-card"><b>Lunghezza</b><p>{_esc(length_text)}</p><p>Conformità: {_esc(status)}</p></article>'
        f'<article class="governance-card"><b>Concetti chiave</b><div class="concept-list">{concepts_html}</div></article>'
        '</div></section>'
    )


def _plagiarism_section(state) -> str:
    quality = _get(state, "quality", {}) or {}
    record = quality.get("plagiarism") or {}
    status = str(record.get("status") or "NON ESEGUITO")
    status_class = " pass" if status == "PASS" else ""
    proof = record.get("proof_statement") or "Il controllo viene eseguito sul candidato e sugli artefatti narrativi rispetto al corpus di confronto registrato nel runtime."
    covered = len(record.get("covered_source_ids") or [])
    missing = len(record.get("missing_source_ids") or [])
    findings = int(record.get("prohibited_findings", 0) or 0)
    scope = record.get("scope_status") or "DA COMPLETARE"
    return (
        '<section class="governance-panel" id="anti-plagiarism" aria-labelledby="anti-plagiarism-title">'
        '<div class="kicker">Originalità dimostrabile</div><h2 id="anti-plagiarism-title">Controllo anti-plagio</h2>'
        f'<span class="proof-status{status_class}">{_esc(status)}</span><p class="purpose">{_esc(proof)}</p>'
        '<div class="governance-grid">'
        f'<article class="governance-card"><b>Perimetro della prova</b><p>{_esc(scope)}</p><p>La prova è deliberatamente circoscritta: Juriscribe non formula una falsa pretesa di unicità rispetto a testi non presenti nel corpus di confronto.</p></article>'
        f'<article class="governance-card"><b>Copertura</b><p>{covered} fonti coperte · {missing} mancanti</p></article>'
        f'<article class="governance-card"><b>Sovrapposizioni vietate</b><p>{findings}</p><p>Riusi testuali lunghi sono ammessi solo se esplicitamente autorizzati e associati a una collocazione di attribuzione.</p></article>'
        '</div></section>'
    )


def _saturation_section(state) -> str:
    review = _get(state, "review", {}) or {}
    record = review.get("delivery_saturation") or {}
    status = str(record.get("status") or "NON ESEGUITA")
    status_class = " pass" if status == "PASS" else ""
    cycles = []
    for cycle in record.get("cycles") or []:
        finding_text = "nessun nuovo blocker" if not cycle.get("new_findings") else str(len(cycle.get("new_findings") or [])) + " nuovi blocker"
        cycles.append(
            '<div class="cycle-row">'
            f'<span>Ciclo {int(cycle.get("cycle", 0))}</span>'
            f'<span>{_esc(finding_text)}</span>'
            f'<span>{_esc(cycle.get("status") or "")}</span></div>'
        )
    cycles_html = "".join(cycles) if cycles else "<p>Nessun ciclo di saturazione ancora registrato.</p>"
    return (
        '<section class="governance-panel" id="predelivery-saturation" aria-labelledby="predelivery-saturation-title">'
        '<div class="kicker">Fixed point prima della consegna</div><h2 id="predelivery-saturation-title">Saturazione e ri-controllo ciclico</h2>'
        f'<span class="proof-status{status_class}">{_esc(status)}</span>'
        '<p class="purpose">Il candidato è consegnabile solo quando configurazione, originalità, qualità, fonti, provenance, review severa, dossier, tracciabilità, completezza dell’atlante e verifica della materializzazione restano verdi in ri-controlli ciclici con ordine variato.</p>'
        f'<div class="cycle-grid">{cycles_html}</div></section>'
    )


def _atlas_record(record: dict[str, Any]) -> str:
    actions = []
    if record.get("richiamo_dashboard"):
        actions.append(f'<a href="{_esc(record.get("richiamo_dashboard"))}">Vai alla sezione correlata</a>')
    if record.get("richiamo_artefatto"):
        actions.append(f'<a href="{_esc(record.get("richiamo_artefatto"))}">Apri artefatto</a>')
    actions_html = "".join(actions)
    return (
        '<details class="atlas-record" open><summary>'
        '<span>'
        f'<span class="atlas-title">{_esc(record.get("titolo"))}</span>'
        f'<span class="atlas-summary-line">{_esc(record.get("sintesi_compressa"))}</span>'
        '</span>'
        '<span class="atlas-badges">'
        f'<span class="atlas-badge">{_esc(record.get("stato") or "REGISTRATO")}</span>'
        f'<span class="atlas-badge">{_esc(record.get("tipo") or "ARTEFATTO")}</span>'
        '</span></summary>'
        '<div class="atlas-body">'
        f'<p class="atlas-function">{_esc(record.get("funzione"))}</p>'
        f'{_render_semantic(record.get("descrizione_completa") or {})}'
        f'<div class="atlas-actions">{actions_html}</div>'
        '</div></details>'
    )


def _artifact_atlas_section(state) -> str:
    atlas = build_artifact_atlas(state)
    summary = "".join(f"<li>{_esc(item)}</li>" for item in atlas.get("sintesi_compressa") or [])
    material = atlas.get("artefatti_materiali") or []
    epistemic = atlas.get("artefatti_epistemici") or []
    material_html = "".join(_atlas_record(item) for item in material)
    epistemic_html = "".join(_atlas_record(item) for item in epistemic)
    return (
        '<section class="artifact-atlas" id="artifact-atlas" aria-labelledby="artifact-atlas-title">'
        '<div class="kicker">Completezza della sessione</div>'
        f'<h2 id="artifact-atlas-title">{_esc(atlas.get("titolo"))}</h2><p class="purpose">{_esc(atlas.get("finalita"))}</p>'
        f'<ul class="atlas-summary">{summary}</ul>'
        '<div class="atlas-group"><div class="atlas-group-head"><h3>Artefatti materiali</h3>'
        f'<span>{len(material)} descritti</span></div><div class="atlas-records">{material_html}</div></div>'
        '<div class="atlas-group" id="epistemic-artifacts"><div class="atlas-group-head"><h3>Artefatti epistemici</h3>'
        f'<span>{len(epistemic)} descritti</span></div><div class="atlas-records">{epistemic_html}</div></div>'
        '</section>'
    )


def _inject_navigation(page: str, state) -> str:
    atlas = build_artifact_atlas(state)
    material_count = len(atlas.get("artefatti_materiali") or [])
    epistemic_count = len(atlas.get("artefatti_epistemici") or [])
    extra = (
        '<li><a href="#generation-configuration"><span>Configurazione</span><span class="n">C</span></a></li>'
        '<li><a href="#anti-plagiarism"><span>Anti-plagio</span><span class="n">P</span></a></li>'
        '<li><a href="#predelivery-saturation"><span>Saturazione</span><span class="n">S</span></a></li>'
        f'<li><a href="#artifact-atlas"><span>Artefatti</span><span class="n">{material_count}</span></a></li>'
        f'<li><a href="#epistemic-artifacts"><span>Epistemici</span><span class="n">{epistemic_count}</span></a></li>'
    )
    return page.replace('</ul></nav>', extra + '</ul></nav>', 1)


def render_session_dashboard(state: dict[str, Any] | Any, output: str | Path) -> Path:
    out = Path(output)
    base.render_session_dashboard(state, out)
    page = out.read_text(encoding="utf-8")
    page = page.replace("</style>", EXTRA_CSS + "</style>", 1)
    page = _inject_navigation(page, state)
    sections = _configuration_section(state) + _plagiarism_section(state) + _saturation_section(state) + _artifact_atlas_section(state)
    marker = '<section class="evidence-map" id="overall-outcome"'
    if marker in page:
        page = page.replace(marker, sections + marker, 1)
    else:
        page = page.replace('<footer class="footer">', sections + '<footer class="footer">', 1)
    out.write_text(page, encoding="utf-8")
    return out
