from __future__ import annotations
import html
from pathlib import Path
from typing import Any

def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))

def badge(label: str, value: Any) -> str:
    return f'<div class="metric"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'

def list_items(items: list[Any], empty: str = "Nessun elemento registrato") -> str:
    if not items:
        return f"<li class='muted'>{esc(empty)}</li>"
    rendered = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("human_readable") or item.get("text") or item.get("summary") or item.get("id") or str(item)
        else:
            text = item
        rendered.append(f"<li>{esc(text)}</li>")
    return "".join(rendered)

def render_session_dashboard(state: dict[str, Any], output: str | Path) -> Path:
    request = state.get("request", {}); metrics = state.get("metrics", {}); strategy = state.get("strategy", {})
    contradictions = state.get("contradictions", []); dod = state.get("dod", []); editorial = state.get("editorial_actions", [])
    artifacts = state.get("artifacts", []); sources = state.get("sources", []); atoms = request.get("atoms", [])
    method_labels = strategy.get("methods", ["atomizzazione epistemica", "mappatura globale-locale-relazionale", "controllo di contraddizione", "convergenza semantica e strategica", "audit lossless"])
    page = f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Juriscribe - sessione {esc(state.get('session_id'))}</title><style>body{{font-family:Georgia,'Times New Roman',serif;margin:0;background:#f5f3ee;color:#24211d;line-height:1.45}}main{{max-width:1080px;margin:auto;padding:32px}}h1,h2{{font-family:Arial,sans-serif}}header{{border-bottom:3px solid #24211d;margin-bottom:24px}}.eyebrow{{font:700 12px Arial,sans-serif;text-transform:uppercase;letter-spacing:.12em}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}.card{{background:white;border:1px solid #d8d2c7;border-radius:8px;padding:18px;margin:12px 0}}.metric{{background:white;border-left:4px solid #24211d;padding:12px}}.metric span{{display:block;font:12px Arial,sans-serif;text-transform:uppercase}}.metric strong{{font-size:22px}}.muted{{color:#6f675e}}ul{{padding-left:20px}}code{{background:#ece8df;padding:2px 5px;border-radius:3px}}</style></head><body><main><header><div class="eyebrow">iSeneca / dashboard della sessione</div><h1>{esc(request.get('summary') or 'Richiesta corrente')}</h1><p>Questa pagina descrive esclusivamente il lavoro svolto nella sessione <code>{esc(state.get('session_id'))}</code>. Non e una dashboard generale di Juriscribe.</p></header><div class="grid">{badge('Fase', state.get('phase'))}{badge('Unita epistemiche', len(state.get('epistemic_units', [])))}{badge('Contraddizioni aperte', len(contradictions))}{badge('Simulazioni', metrics.get('simulations_run', 0))}</div><section class="card"><h2>1. Cosa e stato chiesto</h2><p>{esc(request.get('raw', ''))}</p><h3>Atomi della richiesta</h3><ul>{list_items(atoms)}</ul></section><section class="card"><h2>2. Contesto effettivamente acquisito</h2><ul>{list_items(sources, 'Nessun documento o fonte aggiuntiva registrata')}</ul></section><section class="card"><h2>3. Come e stato affrontato</h2><p>Tipi di metodo applicati, esposti a livello operativo e non come chain-of-thought:</p><ul>{list_items(method_labels)}</ul><p><strong>Funzione del testo:</strong> {esc(strategy.get('document_role', 'da definire'))}</p><p><strong>Strategia selezionata:</strong> {esc(strategy.get('summary', 'non ancora consolidata'))}</p></section><section class="card"><h2>4. Comprensione globale, locale e relazionale</h2><p><strong>Globale:</strong> {esc(strategy.get('global_view', 'non ancora registrata'))}</p><p><strong>Locale:</strong> {esc(strategy.get('local_view', 'non ancora registrata'))}</p><p><strong>Relazionale:</strong> {esc(strategy.get('relational_view', 'non ancora registrata'))}</p></section><section class="card"><h2>5. Contraddizioni e decisioni aperte</h2><ul>{list_items(contradictions, 'Nessuna contraddizione materiale aperta')}</ul></section><section class="card"><h2>6. Convergenza e validazione</h2><div class="grid">{badge('No-novelty semantica', metrics.get('semantic_no_novelty_streak', 0))}{badge('No-improvement strategica', metrics.get('strategy_no_improvement_streak', 0))}{badge('Failure simulazioni', metrics.get('simulation_failures', 0))}</div></section><section class="card"><h2>7. Definition of Done</h2><ul>{list_items(dod, 'DoD non ancora congelati')}</ul></section><section class="card"><h2>8. Riorganizzazione e scrittura</h2><ul>{list_items(editorial, 'Nessuna trasformazione editoriale materializzata')}</ul></section><section class="card"><h2>9. Artefatti della sessione</h2><ul>{list_items(artifacts, 'Nessun artefatto materializzato')}</ul></section></main></body></html>'''
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(page, encoding="utf-8"); return output
