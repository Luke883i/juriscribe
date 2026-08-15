from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _status(value: Any) -> str:
    text = str(value).upper()
    if text in {"PASS", "DONE", "READY", "COMPLETE", "ACCEPTED", "SATURATED", "PASS_CANDIDATE", "AVAILABLE"} or value is True:
        return "ok"
    if text in {"FAIL", "GAPS_OPEN", "BLOCKER", "REGENERATE_REQUIRED", "INVALID"} or value is False:
        return "bad"
    return "wait"


def metric(label: str, value: Any, hint: str = "") -> str:
    return f'<div class="metric {_status(value)}"><span>{esc(label)}</span><b>{esc(value)}</b>{f"<small>{esc(hint)}</small>" if hint else ""}</div>'


def table(items: list[dict[str, Any]], cols: list[tuple[str, Any]], empty: str = "Nessun elemento registrato") -> str:
    if not items:
        return f'<p class="muted">{esc(empty)}</p>'
    head = "".join(f"<th>{esc(label)}</th>" for label, _ in cols)
    body = []
    for item in items:
        cells = []
        for _, accessor in cols:
            value = accessor(item) if callable(accessor) else item.get(accessor, "")
            if isinstance(value, (list, tuple, set)):
                value = ", ".join(map(str, value))
            cells.append(f"<td>{esc(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def _blockers(state: dict[str, Any]) -> list[str]:
    reason = (state.get("completion") or {}).get("reason", "")
    if not reason or reason == "PASS":
        return []
    return [x.strip() for x in str(reason).split(";") if x.strip()]


def _next_action(state: dict[str, Any]) -> str:
    card = (state.get("interaction") or {}).get("card") or {}
    choices = card.get("choices") or []
    return str(choices[0]) if choices else "Consulta i blocker e completa il passaggio successivo"


def render_session_dashboard(state: dict[str, Any], output: str | Path) -> Path:
    req = state.get("request") or {}
    completion = state.get("completion") or {}
    ret = state.get("reticulum") or {}
    continuation = state.get("continuation") or {}
    coverage = continuation.get("coverage") or {}
    review = state.get("review") or {}
    final_review = state.get("final_review") or {}
    provenance = state.get("provenance") or {}
    quality = state.get("quality") or {}
    source_intel = state.get("source_intelligence") or {}
    bibliography = state.get("bibliography") or {}
    simulation = state.get("simulations") or {}
    compression = state.get("compression") or {}
    node = state.get("node_integrity") or {}
    admission = state.get("admission") or {}
    units = state.get("epistemic_units") or []
    claims = state.get("claim_ledger") or []
    sources = state.get("sources") or []
    artifacts = state.get("artifacts") or []
    cycles = review.get("cycles") or []
    regenerations = review.get("regenerations") or []
    latest_cycle = cycles[-1] if cycles else {}
    findings = latest_cycle.get("findings") or []
    prov_entries = provenance.get("entries") or []
    final_findings = final_review.get("findings") or []
    final_evidence = final_review.get("evidence") or []
    consequence_probes = final_review.get("consequence_probes") or []
    blockers = _blockers(state)
    ready = bool(completion.get("eligible"))

    material_claims = [c for c in claims if c.get("material", True)]
    inferences = [c for c in claims if c.get("claim_type") == "strong_inference"] + [u for u in units if u.get("kind") == "INFERENCE"]
    setup = state.get("setup") or {}
    accepted = setup.get("accepted") or {}
    interaction = state.get("interaction") or {}

    claim_cols = [
        ("ID", "id"),
        ("Proposizione", lambda x: x.get("text") or x.get("proposition")),
        ("Stato", "status"),
        ("Fonti", lambda x: x.get("support_source_ids", [])),
        ("Perimetro", lambda x: x.get("scope") or x.get("jurisdiction") or ""),
    ]
    source_cols = [
        ("ID", "id"), ("Fonte", "title"), ("Tipo", "source_type"),
        ("Lettura diretta", "direct_read"), ("Verifica", "verified_at"),
    ]
    prov_cols = [
        ("ID", "id"), ("Tipo", "kind"), ("Proposizione", "proposition"),
        ("Esito finale", "disposition"), ("Evidenze", lambda x: x.get("evidence_refs", [])),
        ("Dove nel finale", lambda x: x.get("artifact_locators", [])),
    ]
    finding_cols = [
        ("Criterio", "criterion"), ("Gravità", "severity"), ("Problema", lambda x: x.get("message") or x.get("kind")),
        ("Posizione", "artifact_locator"), ("Stato", "status"), ("Intervento", "proposed_action"),
    ]
    artifact_cols = [("Ruolo", "role"), ("Artefatto", "summary"), ("Percorso", "path"), ("Readback", "readback")]

    html_page = f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Juriscribe — fascicolo di sessione</title>
<style>
:root{{--bg:#f6f3ec;--paper:#fffdfa;--ink:#252825;--muted:#6b6f69;--line:#ddd6c8;--ok:#236443;--bad:#973d36;--wait:#92701c;--accent:#365f77}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Georgia,'Times New Roman',serif}}
main{{max-width:1180px;margin:auto;padding:22px}} header,section{{background:var(--paper);border:1px solid var(--line);border-radius:12px;margin:12px 0;padding:20px}}
h1,h2,h3,.eyebrow,.metric,.pill,th,.next{{font-family:Arial,sans-serif}} h1{{margin:.2rem 0 .5rem;font-size:2rem}} h2{{font-size:1.25rem;margin-top:0}}
.eyebrow{{font-size:.73rem;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);font-weight:800}}
.verdict{{font:800 1.55rem Arial,sans-serif;margin:.5rem 0}} .ok{{color:var(--ok)}} .bad{{color:var(--bad)}} .wait{{color:var(--wait)}}
.next{{padding:12px 14px;background:#eef3f5;border-left:5px solid var(--accent);border-radius:7px}} .blockers{{padding:12px 16px;background:#fff0ee;border-left:5px solid var(--bad)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:9px}} .metric{{padding:10px;border:1px solid var(--line);border-radius:8px;background:#fff}}
.metric span{{display:block;font-size:.7rem;text-transform:uppercase;color:var(--muted)}} .metric b{{display:block;font-size:1.05rem}} .metric small{{display:block;color:var(--muted)}}
.checks{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:9px}} .check{{padding:12px;border:1px solid var(--line);border-radius:8px}} .check strong{{font-family:Arial,sans-serif}}
.table-wrap{{overflow:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}} th,td{{border-bottom:1px solid #ebe5d9;text-align:left;padding:8px;vertical-align:top}} th{{font-size:.72rem;text-transform:uppercase;letter-spacing:.03em}}
details{{margin:.65rem 0}} summary{{cursor:pointer;font-family:Arial,sans-serif;font-weight:700}} .muted{{color:var(--muted)}} code{{background:#f0ece3;padding:2px 5px;border-radius:4px}}
.pill{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;margin:2px;font-size:.78rem}}
@media(max-width:700px){{main{{padding:8px}} header,section{{padding:14px}}}}
</style></head><body><main>
<header>
<div class="eyebrow">Juriscribe · fascicolo di lavorazione per umanisti, giuristi e redazioni</div>
<h1>{esc(req.get('summary') or req.get('raw') or 'Sessione Juriscribe')}</h1>
<div class="verdict {'ok' if ready else 'bad'}">{'PRONTO PER CONSEGNA' if ready else 'NON PRONTO'}</div>
<p class="muted">Sessione <code>{esc(state.get('session_id'))}</code>. Qui trovi stati ed evidenze verificabili, non chain-of-thought.</p>
<div class="next"><strong>Prossima azione:</strong> {esc(_next_action(state))}</div>
{('<div class="blockers"><strong>Cosa blocca la consegna</strong><ul>'+''.join(f'<li>{esc(x)}</li>' for x in blockers)+'</ul></div>') if blockers else '<p class="ok"><strong>Nessun blocker aperto.</strong></p>'}
</header>

<section><h2>1. Dove siamo</h2>
<div class="grid">
{metric('Fase',state.get('phase'))}{metric('Bootstrap',(admission.get('bootstrap') or {}).get('state','NON ATTIVO'))}{metric('Reticolo',ret.get('status','NON ESEGUITO'))}{metric('Continuazione',coverage.get('status','NON ESEGUITA'))}{metric('Review',review.get('status','NON ESEGUITA'))}{metric('Provenance',provenance.get('status','NON ESEGUITA'))}{metric('Review finale',final_review.get('status','NON ESEGUITA'))}{metric('Qualità',quality.get('status','NON ESEGUITA'))}
</div>
<h3>Mandato e parametri accettati</h3><p>{esc(req.get('raw',''))}</p>
{table([{'k':k,'v':v} for k,v in accepted.items()],[('Parametro','k'),('Valore','v')], 'Nessun parametro ancora accettato')}
<p><strong>Scelte disponibili ora:</strong> {''.join(f'<span class="pill">{esc(x)}</span>' for x in ((interaction.get('card') or {}).get('choices') or ['ALTRO']))}</p>
</section>

<section><h2>2. Cosa è stato controllato</h2>
<div class="checks">
<div class="check"><strong>Mining e Mappa scientifica</strong><p>{esc(ret.get('node_count',len(units)))} unità · {esc(ret.get('relation_count',0))} relazioni · locator materiali {esc(ret.get('material_locator_coverage','n/a'))}</p></div>
<div class="check"><strong>Continuità del capitolo</strong><p>coverage {esc(coverage.get('coverage_score','n/a'))} · core aperti {esc(len(coverage.get('unresolved_core',[]) or []))}</p></div>
<div class="check"><strong>Fonti e bibliografia</strong><p>{esc(source_intel.get('coverage_status','NON ESEGUITO'))} · bibliografia {esc(bibliography.get('status','NON DISPONIBILE'))}</p></div>
<div class="check"><strong>Review scientifico-editoriale</strong><p>{esc(len(cycles))} cicli · {esc(len(regenerations))} rigenerazioni · stato {esc(review.get('status','NON ESEGUITA'))}</p></div>
<div class="check"><strong>Simulazioni, saturazione e compressione</strong><p>{esc(simulation.get('cases',0))} casi · P+ {esc((review.get('saturation') or {}).get('no_novelty_streak',0))} · compressione {esc(compression.get('status','NON ESEGUITA'))}</p></div>
<div class="check"><strong>Review finale giuridico-consequenziale</strong><p>{esc(final_review.get('status','NON ESEGUITA'))} · consequence probes {esc(len(consequence_probes))}</p></div>
</div></section>

<section><h2>3. Evidenze circostanziate</h2>
<p class="muted">Questa sezione è pensata per il controllo redazionale: ogni elemento dovrebbe essere riconducibile a una fonte, a un'inferenza dichiarata o a una posizione nell'artefatto finale.</p>
<details open><summary>Claim materiali ({len(material_claims)})</summary>{table(material_claims,claim_cols)}</details>
<details><summary>Fonti ({len(sources)})</summary>{table(sources,source_cols)}</details>
<details><summary>Inferenze forti / epistemiche ({len(inferences)})</summary>{table(inferences,[('ID','id'),('Proposizione',lambda x:x.get('text') or x.get('proposition')),('Premesse',lambda x:x.get('premise_claim_ids') or x.get('premise_ids') or []),('Ponte',lambda x:x.get('inference_bridge') or ''),('Falsificatore','falsifier')])}</details>
<details open><summary>Provenance finale ({len(prov_entries)})</summary>{table(prov_entries,prov_cols,'Provenance non ancora materializzata')}</details>
</section>

<section><h2>4. Storia delle revisioni</h2>
<h3>Review scientifico-editoriale</h3>{table(findings,finding_cols,'Nessun finding nell’ultimo ciclo')}
<h3>Rigenerazioni</h3>{table(regenerations,[('Ciclo','cycle'),('Da','from_digest'),('A','to_digest'),('Finding affrontati',lambda x:x.get('addressed_finding_ids',[])),('Stato','status')],'Nessuna rigenerazione registrata')}
<h3>Review finale severa</h3>{table(final_evidence,[('Criterio','criterion'),('Stato','status'),('Evidenza','locator'),('Nota','rationale')],'Review finale non ancora eseguita')}
<h3>Conseguenze testate</h3>{table(consequence_probes,[('ID','id'),('Proposizione','proposition'),('Conseguenza','downstream_effect'),('Stato','status'),('Evidenza','evidence_ref')],'Nessun consequence probe registrato')}
{table(final_findings,[('Criterio','criterion'),('Gravità','severity'),('Problema',lambda x:x.get('message') or x.get('kind')),('Stato','status')],'Nessun finding finale')}
</section>

<section><h2>5. Artefatti finali</h2>{table(artifacts,artifact_cols,'Nessun artefatto registrato')}</section>

<section><h2>6. Integrità tecnica</h2><p class="muted">Sezione secondaria: utile per audit e debugging, non necessaria per leggere il merito scientifico.</p>
<details><summary>Apri dettagli tecnici</summary><div class="grid">{metric('node.h',node.get('status','NON VERIFICATO'))}{metric('Provenance coverage',provenance.get('coverage','n/a'))}{metric('Candidate digest',(state.get('drafts') or [{}])[-1].get('digest','') if state.get('drafts') else '')}{metric('Final review digest',final_review.get('digest',''))}</div></details>
</section>
</main></body></html>'''
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html_page, encoding="utf-8"); return out
