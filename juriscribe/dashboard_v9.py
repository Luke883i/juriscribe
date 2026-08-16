from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

from .editorial_artifacts import build_dashboard_inference_view

DASHBOARD_BINDING_KEYS = (
    "request", "mode", "mode_selection", "mode_contract", "editorial_standard",
    "corpus", "sources", "bibliography", "epistemic_units", "relations", "reticulum",
    "generation_contract", "continuation", "drafts", "review", "final_review", "provenance",
    "contradictions", "mining", "style_profile", "setup", "source_intelligence", "claim_ledger",
    "artifact_evidence", "quality", "benchmark", "simulations", "compression", "limits", "strategy",
    "dod", "editorial_actions", "reflection", "metrics",
)


def _artifact_binding(artifacts):
    return sorted(
        [{"id": str(item.get("id", "")), "role": str(item.get("role", "")), "path": str(item.get("path", "")), "readback": str(item.get("readback", ""))} for item in artifacts or []],
        key=lambda item: (item["role"], item["id"], item["path"]),
    )


def dashboard_state_digest(state: dict[str, Any] | Any) -> str:
    payload = state if isinstance(state, dict) else state.__dict__
    bound = {key: payload.get(key) for key in DASHBOARD_BINDING_KEYS}
    bound["artifacts"] = _artifact_binding(payload.get("artifacts") or []) if str(payload.get("mode") or "").strip() else []
    encoded = json.dumps(bound, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _label(key: str) -> str:
    labels = {
        "riferimento": "Riferimento", "proposizione": "Proposizione", "funzione_giuridica": "Funzione giuridica",
        "ambito": "Ambito", "stato_epistemico": "Stato epistemico", "evidenze": "Evidenze", "premesse": "Premesse",
        "ponte_inferenziale": "Ponte inferenziale", "condizione_di_confutazione": "Condizione di confutazione",
        "contesto_relazionale": "Relazioni, qualificazioni e contrasti", "ragione_editoriale_o_probatoria": "Ragione editoriale o probatoria",
        "disposizione_finale": "Disposizione finale", "collocazione_nel_testo": "Collocazione nel testo", "fonte": "Fonte",
        "carattere_autorita": "Carattere dell'autorita", "autore_o_organo": "Autore o organo", "giurisdizione": "Giurisdizione",
        "collocazione_temporale": "Collocazione temporale", "ruolo_nel_lavoro": "Ruolo nel lavoro", "uso_nel_ragionamento": "Uso nel ragionamento",
        "evidenza_circostanziata": "Evidenza circostanziata", "controautorita_o_riserva": "Controautorita o riserva",
        "nota_critica": "Nota critica", "verifica": "Verifica della fonte", "data_verifica": "Data della verifica",
        "voce_bibliografica": "Voce bibliografica", "collegamento": "Collegamento", "conclusione_inferenziale": "Conclusione inferenziale",
        "autorita_o_evidenze": "Autorita o evidenze", "qualificazioni_obiezioni_e_contrasti": "Qualificazioni, obiezioni e contrasti",
        "ragione_dell_inferenza": "Ragione dell'inferenza", "fase": "Fase", "natura": "Natura della trasformazione", "ragione": "Ragione",
        "problema_rilevato": "Problema rilevato", "gravita": "Gravita", "intervento_proposto": "Intervento proposto",
        "riferimenti_epistemici": "Riferimenti epistemici", "fonti_coinvolte": "Fonti coinvolte", "collocazione": "Collocazione", "esito": "Esito",
        "finding_affrontati": "Finding affrontati", "contenuti_preservati": "Contenuti preservati", "contenuti_persi": "Contenuti persi",
        "nuovo_materiale": "Nuovo materiale", "degradazioni": "Degradazioni", "estensione_prima": "Estensione prima della trasformazione",
        "estensione_dopo": "Estensione dopo la trasformazione", "riesame_successivo": "Riesame successivo", "oggetto": "Oggetto",
        "evidenza": "Evidenza", "conseguenza_esaminata": "Conseguenza esaminata", "modalita": "Modalita",
        "genere_giuridico": "Genere giuridico", "destinatari": "Destinatari", "orientamento": "Orientamento editoriale",
        "principi_applicati": "Principi applicati",
    }
    return labels.get(key, str(key).replace("_", " ").strip().capitalize())


def _render_value(value: Any, *, depth: int = 0) -> str:
    if isinstance(value, dict):
        if not value: return '<p class="muted">Nessun elemento materializzato.</p>'
        rows = [f'<div class="field"><dt>{esc(_label(str(key)))}</dt><dd>{_render_value(item, depth=depth + 1)}</dd></div>' for key, item in value.items()]
        return '<dl class="fields">' + ''.join(rows) + '</dl>'
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        if not items: return '<span class="muted">Nessun elemento materializzato.</span>'
        if all(isinstance(item, dict) for item in items):
            return '<div class="record-list">' + ''.join(f'<article class="record">{_render_value(item, depth=depth + 1)}</article>' for item in items) + '</div>'
        return '<ul>' + ''.join(f'<li>{_render_value(item, depth=depth + 1)}</li>' for item in items) + '</ul>'
    if isinstance(value, bool): return "si" if value else "no"
    return f'<span>{esc(value)}</span>'


def _render_dossier(view: dict[str, Any], number: int) -> str:
    title = str(view.get("titolo") or "Dossier"); purpose = str(view.get("finalita") or ""); records = list(view.get("records") or [])
    return f'<section><div class="eyebrow">Parte {number}</div><h2>{esc(title)}</h2><p class="purpose">{esc(purpose)}</p><p class="count">{len(records)} elementi materializzati</p>{_render_value(records)}</section>'


def render_session_dashboard(state: dict[str, Any] | Any, output: str | Path) -> Path:
    payload = state if isinstance(state, dict) else state.__dict__
    inference = build_dashboard_inference_view(payload)
    state_digest = dashboard_state_digest(payload)
    frame = inference.get("cornice_editoriale") or {}
    ready = bool((payload.get("completion") or {}).get("eligible"))
    editorial_state = "PRONTO" if ready else "NON PRONTO"
    body = ''.join([
        _render_dossier(inference.get("evidence_dossier") or {}, 1),
        _render_dossier(inference.get("source_register") or {}, 2),
        _render_dossier(inference.get("inference_register") or {}, 3),
        _render_dossier(inference.get("transformation_ledger") or {}, 4),
    ])
    page = f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="juriscribe-state-digest" content="{state_digest}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Juriscribe — dossier inferenziale</title>
<style>
:root{{--bg:#f5f1e8;--paper:#fffdf8;--ink:#242722;--muted:#686c64;--line:#d9d1c2;--accent:#395b67;--soft:#f0ece3}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.62 Georgia,'Times New Roman',serif}}main{{max-width:1120px;margin:auto;padding:24px}}header,section{{background:var(--paper);border:1px solid var(--line);border-radius:12px;margin:14px 0;padding:24px}}h1,h2,h3,.eyebrow,.count,dt{{font-family:Arial,sans-serif}}h1{{font-size:2.05rem;line-height:1.15;margin:.25rem 0 .75rem}}h2{{font-size:1.35rem;margin:.25rem 0 .5rem}}h3{{font-size:1rem}}.eyebrow{{font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--accent)}}.mandate{{font-size:1.08rem}}.purpose{{max-width:900px;color:#414740}}.count{{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}.frame{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-top:18px}}.frame article{{background:var(--soft);border-radius:8px;padding:12px}}.frame h3{{margin:0 0 5px;color:var(--accent)}}.record-list{{display:grid;gap:12px}}.record{{border:1px solid var(--line);border-radius:10px;padding:14px;background:#fff}}.fields{{margin:0}}.field{{display:grid;grid-template-columns:minmax(155px,220px) 1fr;gap:14px;padding:8px 0;border-bottom:1px solid #ece6da}}.field:last-child{{border-bottom:0}}dt{{font-size:.77rem;font-weight:800;text-transform:uppercase;letter-spacing:.025em;color:var(--accent)}}dd{{margin:0;min-width:0}}ul{{margin:.2rem 0 .2rem 1.2rem;padding:0}}li{{margin:.16rem 0}}.muted{{color:var(--muted)}}@media(max-width:720px){{main{{padding:8px}}header,section{{padding:16px}}.field{{grid-template-columns:1fr;gap:3px}}}}
</style>
</head>
<body><main>
<header>
<div class="eyebrow">Juriscribe · dossier inferenziale giuridico-umanistico-editoriale · {editorial_state}</div>
<h1>{esc(inference.get('titolo') or 'Dossier inferenziale')}</h1>
<p class="mandate"><strong>Mandato:</strong> {esc(inference.get('mandato') or 'Non ancora definito')}</p>
<h2>Standard redazionali applicati</h2>
<div class="frame">
<article><h3>Modalità:</h3>{_render_value(frame.get('modalita') or 'Non selezionata')}</article>
<article><h3>Genere giuridico</h3>{_render_value(frame.get('genere_giuridico') or 'Da definire')}</article>
<article><h3>Destinatari</h3>{_render_value(frame.get('destinatari') or 'Da definire')}</article>
</div>
{('<h3>Orientamento editoriale</h3>'+_render_value(frame.get('orientamento'))) if frame.get('orientamento') else ''}
{('<h3>Principi applicati</h3>'+_render_value(frame.get('principi_applicati'))) if frame.get('principi_applicati') else ''}
<div class="eyebrow">Evidenze e merito</div>
</header>
{body}
</main></body></html>'''
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(page, encoding="utf-8"); return out
