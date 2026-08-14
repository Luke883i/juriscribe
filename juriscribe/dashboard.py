from __future__ import annotations
import html
from pathlib import Path
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def badge(label: str, value: Any) -> str:
    return f'<div class="metric"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'


def list_items(items: list[Any], empty: str = "Nessun elemento registrato") -> str:
    if not items: return f"<li class='muted'>{esc(empty)}</li>"
    rendered = []
    for item in items:
        if isinstance(item, dict): text = item.get("human_readable") or item.get("text") or item.get("summary") or item.get("label") or item.get("id") or str(item)
        else: text = item
        rendered.append(f"<li>{esc(text)}</li>")
    return "".join(rendered)


def setup_html(setup: dict[str, Any]) -> str:
    if not setup: return "<p class='muted'>Setup non ancora proposto.</p>"
    accepted = setup.get("accepted")
    if accepted:
        rows = "".join(f"<li><strong>{esc(k)}</strong>: {esc(v)}</li>" for k, v in accepted.items())
        return f"<p><strong>Setup accettato.</strong></p><ul>{rows}</ul>"
    rows = "".join(f"<li><strong>{esc(p.get('label'))}</strong>: {esc(p.get('recommended'))}</li>" for p in setup.get("parameters", []))
    return f"<p><strong>Configurazione raccomandata, in attesa dell'utente.</strong></p><ul>{rows}</ul>"


def render_session_dashboard(state: dict[str, Any], output: str | Path) -> Path:
    request = state.get("request", {}); metrics = state.get("metrics", {}); strategy = state.get("strategy", {})
    contradictions = state.get("contradictions", []); dod = state.get("dod", []); editorial = state.get("editorial_actions", [])
    artifacts = state.get("artifacts", []); sources = state.get("sources", []); atoms = request.get("atoms", [])
    mining = state.get("mining", {}); style = state.get("style_profile", {}); source_intel = state.get("source_intelligence", {})
    claims = state.get("claim_ledger", []); setup = state.get("setup", {}); completion = state.get("completion", {})
    method_labels = strategy.get("methods", ["deep mining", "atomizzazione epistemica", "mappatura globale-locale-relazionale", "style fingerprint", "claim grounding", "convergenza vs DoD", "audit lossless"])
    done_dod = sum(1 for d in dod if d.get("status") == "DONE")
    page = f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Juriscribe - sessione {esc(state.get('session_id'))}</title><style>body{{font-family:Georgia,'Times New Roman',serif;margin:0;background:#f5f3ee;color:#24211d;line-height:1.45}}main{{max-width:1080px;margin:auto;padding:32px}}h1,h2{{font-family:Arial,sans-serif}}header{{border-bottom:3px solid #24211d;margin-bottom:24px}}.eyebrow{{font:700 12px Arial,sans-serif;text-transform:uppercase;letter-spacing:.12em}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}}.card{{background:white;border:1px solid #d8d2c7;border-radius:8px;padding:18px;margin:12px 0}}.metric{{background:white;border-left:4px solid #24211d;padding:12px}}.metric span{{display:block;font:12px Arial,sans-serif;text-transform:uppercase}}.metric strong{{font-size:20px}}.muted{{color:#6f675e}}ul{{padding-left:20px}}code{{background:#ece8df;padding:2px 5px;border-radius:3px}}</style></head><body><main><header><div class="eyebrow">iSeneca / dashboard della sessione</div><h1>{esc(request.get('summary') or 'Richiesta corrente')}</h1><p>Descrive esclusivamente la lavorazione <code>{esc(state.get('session_id'))}</code>, non Juriscribe in generale.</p></header><div class="grid">{badge('Fase', state.get('phase'))}{badge('DoD', f'{done_dod}/{len(dod)}')}{badge('No novelty vs DoD', metrics.get('dod_no_novelty_streak', 0))}{badge('Claim registrati', len(claims))}</div><section class="card"><h2>1. Richiesta e setup</h2><p>{esc(request.get('raw', ''))}</p><h3>Atomi</h3><ul>{list_items(atoms)}</ul>{setup_html(setup)}</section><section class="card"><h2>2. Mining profondo del contesto</h2><p><strong>Stato:</strong> {esc(mining.get('mining_status', 'non eseguito'))}</p><p><strong>Parole analizzate:</strong> {esc(mining.get('surface', {}).get('word_count', 0))}</p><p><strong>Registro:</strong> {esc(style.get('register', 'non rilevato'))}</p><p><strong>Periodo medio:</strong> {esc(style.get('avg_sentence_words', 0))} parole; <strong>paragrafo medio:</strong> {esc(style.get('avg_paragraph_words', 0))}.</p><p><strong>Connettori dominanti:</strong> {esc(', '.join(style.get('dominant_connectors', [])))}</p></section><section class="card"><h2>3. Contesto e fonti effettivamente acquisiti</h2><ul>{list_items(sources, 'Nessuna fonte esterna registrata')}</ul><p><strong>Copertura claim:</strong> {esc(source_intel.get('coverage_status', 'NOT_STARTED'))}</p><p><strong>Dominanza:</strong> {esc(source_intel.get('dominance_assessments', []))}</p></section><section class="card"><h2>4. Metodo e strategia</h2><ul>{list_items(method_labels)}</ul><p><strong>Funzione:</strong> {esc(strategy.get('document_role', 'da definire'))}</p><p><strong>Strategia:</strong> {esc(strategy.get('summary', 'non consolidata'))}</p><p><strong>Globale:</strong> {esc(strategy.get('global_view', 'non registrata'))}</p><p><strong>Locale:</strong> {esc(strategy.get('local_view', 'non registrata'))}</p><p><strong>Relazionale:</strong> {esc(strategy.get('relational_view', 'non registrata'))}</p></section><section class="card"><h2>5. Claim e controllo fonti</h2><ul>{list_items(claims, 'Nessun claim materializzato')}</ul></section><section class="card"><h2>6. Contraddizioni</h2><ul>{list_items(contradictions, 'Nessuna contraddizione materiale aperta')}</ul></section><section class="card"><h2>7. DoD e saturazione</h2><ul>{list_items(dod, 'DoD non congelati')}</ul><div class="grid">{badge('No novelty semantica', metrics.get('semantic_no_novelty_streak', 0))}{badge('No improvement strategica', metrics.get('strategy_no_improvement_streak', 0))}{badge('No novelty vs DoD', metrics.get('dod_no_novelty_streak', 0))}{badge('Simulazioni', metrics.get('simulations_run', 0))}</div><p><strong>Completion gate:</strong> {esc(completion.get('reason', 'non valutato'))}</p></section><section class="card"><h2>8. Riorganizzazione e scrittura</h2><ul>{list_items(editorial, 'Nessuna trasformazione editoriale materializzata')}</ul></section><section class="card"><h2>9. Artefatti</h2><ul>{list_items(artifacts, 'Nessun artefatto materializzato')}</ul></section></main></body></html>'''
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(page, encoding="utf-8"); return output
