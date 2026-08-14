from __future__ import annotations

import html
from pathlib import Path
from typing import Any

HUMAN_KIND = {
    "CLAIM": "tesi/affermazione", "RULE": "regola", "DEFINITION": "definizione",
    "EXCEPTION": "eccezione", "QUALIFICATION": "qualificazione", "ARGUMENT": "argomento",
    "COUNTERARGUMENT": "controargomento", "CONCLUSION": "conclusione",
    "OPEN_ISSUE": "questione aperta", "QUESTION": "questione", "INFERENCE": "inferenza", "CONCEPT": "concetto",
}
HUMAN_REL = {
    "SUPPORTS": "sostiene", "CONTRADICTS": "contraddice", "QUALIFIES": "qualifica",
    "DEPENDS_ON": "dipende da", "DEFINES": "definisce", "DISTINGUISHES": "distingue da",
    "ANTICIPATES": "prepara", "RECALLS": "richiama", "DEVELOPS": "sviluppa",
    "AVOIDS_DUPLICATION_OF": "non deve duplicare", "INFERRED_FROM": "deriva da",
}


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def status_class(value: Any) -> str:
    text = str(value).upper()
    if text in {"PASS", "DONE", "COMPLETE", "AVAILABLE", "READY", "ACCEPTED", "SATURATED", "PASS_CANDIDATE"} or value is True:
        return "ok"
    if text in {"FAIL", "GAPS_OPEN", "UNAVAILABLE", "RETICULUM_INVALID", "REGENERATE_REQUIRED", "BLOCKER"}:
        return "bad"
    return "wait"


def metric(label: str, value: Any, hint: str = "") -> str:
    return f'<div class="metric {status_class(value)}"><span>{esc(label)}</span><strong>{esc(value)}</strong>{f"<small>{esc(hint)}</small>" if hint else ""}</div>'


def rows(items: list[dict[str, Any]], columns: list[tuple[str, Any]], empty: str = "Nessun elemento registrato") -> str:
    if not items:
        return f'<tr><td colspan="{len(columns)}" class="muted">{esc(empty)}</td></tr>'
    out: list[str] = []
    for item in items:
        cells = []
        for _, accessor in columns:
            value = accessor(item) if callable(accessor) else item.get(accessor, "")
            cells.append(f"<td>{esc(value)}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(out)


def header(columns: list[tuple[str, Any]]) -> str:
    return "".join(f"<th>{esc(label)}</th>" for label, _ in columns)


def blockers(state: dict[str, Any]) -> list[str]:
    reason = (state.get("completion") or {}).get("reason", "")
    if not reason or reason == "PASS":
        return []
    return [part.strip() for part in reason.split(";") if part.strip()]


def _cross_chapter(units: list[dict[str, Any]], relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {u.get("id"): u for u in units}
    out: list[dict[str, Any]] = []
    for relation in relations:
        left = by_id.get(relation.get("source"), {})
        right = by_id.get(relation.get("target"), {})
        if left.get("chapter") and right.get("chapter") and left.get("chapter") != right.get("chapter"):
            out.append({
                "from": left.get("chapter"),
                "relation": HUMAN_REL.get(relation.get("predicate"), relation.get("predicate")),
                "to": right.get("chapter"),
                "subject": left.get("text"),
                "target": right.get("text"),
            })
    return out


def render_session_dashboard(state: dict[str, Any], output: str | Path) -> Path:
    req = state.get("request", {})
    ret = state.get("reticulum", {})
    units = state.get("epistemic_units", [])
    relations = state.get("relations", [])
    sources = state.get("sources", [])
    bibliography = state.get("bibliography", {})
    setup = state.get("setup", {})
    dod = state.get("dod", [])
    claims = state.get("claim_ledger", [])
    quality = state.get("quality", {})
    metrics = state.get("metrics", {})
    simulation = state.get("simulations", {})
    compression = state.get("compression", {})
    completion = state.get("completion", {})
    artifacts = state.get("artifacts", [])
    evidence = state.get("artifact_evidence", [])
    contradictions = state.get("contradictions", [])
    generation = state.get("generation_contract", {})
    admission = state.get("admission", {})
    source_intel = state.get("source_intelligence", {})
    benchmark = state.get("benchmark", {})
    limits = state.get("limits", [])
    drafts = state.get("drafts", [])
    review = state.get("review", {})
    cycles = review.get("cycles", [])
    regenerations = review.get("regenerations", [])
    saturation = review.get("saturation", {})
    node = state.get("node_integrity", {})

    done = sum(1 for item in dod if item.get("status") == "DONE")
    release = "PRONTO PER CONSEGNA" if completion.get("eligible") else "NON PRONTO"
    block = blockers(state)
    cross = _cross_chapter(units, relations)
    strong_inferences = [claim for claim in claims if claim.get("claim_type") == "strong_inference"]
    latest_cycle = cycles[-1] if cycles else {}
    open_findings = [
        finding for finding in latest_cycle.get("findings", [])
        if finding.get("status", "OPEN") in {"OPEN", "HUMAN_DECISION_REQUIRED"}
    ]
    human_decisions = [c for c in contradictions if c.get("status") == "HUMAN_DECISION_REQUIRED"] + [f for f in open_findings if f.get("status") == "HUMAN_DECISION_REQUIRED"]
    current_draft = drafts[-1] if drafts else {}
    review_scores = latest_cycle.get("scorecard", {})

    unit_cols = [
        ("ID", "id"),
        ("Funzione", lambda x: HUMAN_KIND.get(x.get("kind"), x.get("kind"))),
        ("Proposizione", "text"),
        ("Capitolo", "chapter"),
        ("Passo sorgente", "source_locator"),
    ]
    source_cols = [
        ("Fonte", "title"), ("Tipo", "source_type"), ("Ruolo", "role"),
        ("Lettura", "direct_read"), ("Verificata", "verified_at"), ("Voce bibliografica", "bibliography_entry"),
    ]
    finding_cols = [
        ("Criterio", "criterion"), ("Gravità", "severity"), ("Problema", "message"),
        ("Posizione", "artifact_locator"), ("Stato", "status"), ("Intervento", "proposed_action"),
    ]
    dod_cols = [("DoD", "id"), ("Tipo", "kind"), ("Atteso", "expected"), ("Stato", "status")]
    artifact_cols = [("Artefatto", "summary"), ("Percorso", "path"), ("Readback", "readback")]

    score_rows = "".join(
        f"<tr><td>{esc(key)}</td><td>{esc(value)}</td></tr>" for key, value in review_scores.items()
    ) or '<tr><td colspan="2" class="muted">Review non ancora eseguita</td></tr>'

    page = f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Juriscribe — fascicolo editoriale</title><style>
:root{{--ink:#202321;--paper:#f3f0e8;--card:#fffdfa;--line:#d7cfbf;--green:#265e45;--amber:#8a681b;--red:#8e3434;--blue:#385f78;--muted:#686861}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.52 Georgia,'Times New Roman',serif}}main{{max-width:1280px;margin:auto;padding:28px}}h1,h2,h3,th,.kicker,.metric span,.verdict,.nav{{font-family:Arial,sans-serif}}header,section{{background:var(--card);border:1px solid var(--line);border-radius:8px}}header{{padding:24px;border-top:7px solid var(--ink)}}.kicker{{font-size:12px;text-transform:uppercase;letter-spacing:.12em;font-weight:800;color:var(--blue)}}.verdict{{font-size:30px;font-weight:800;margin:.5rem 0}}.verdict.ok{{color:var(--green)}}.verdict.wait,.verdict.bad{{color:var(--red)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:14px 0}}.metric{{background:#fff;padding:11px;border-left:5px solid var(--blue);border-radius:4px}}.metric.ok{{border-left-color:var(--green)}}.metric.wait{{border-left-color:var(--amber)}}.metric.bad{{border-left-color:var(--red)}}.metric span{{display:block;color:var(--muted);font-size:11px;text-transform:uppercase}}.metric strong{{font-size:19px}}.metric small{{display:block;color:var(--muted);font-size:12px;margin-top:3px}}section{{padding:20px;margin:14px 0}}.explain{{background:#f5f7f5;border-left:4px solid var(--blue);padding:10px 13px}}.block{{background:#fff2f0;border-left:4px solid var(--red);padding:10px 14px}}.good{{background:#eff7f1;border-left:4px solid var(--green);padding:10px 14px}}.decision{{background:#fff8e8;border-left:4px solid var(--amber);padding:10px 14px}}table{{width:100%;border-collapse:collapse;font-size:.91rem}}th,td{{border-bottom:1px solid #e5dfd4;padding:8px;text-align:left;vertical-align:top}}th{{font-size:.73rem;text-transform:uppercase;letter-spacing:.04em}}details{{margin:.6rem 0}}code{{background:#eee8dc;padding:2px 5px;border-radius:3px}}.muted{{color:var(--muted)}}.steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px;list-style:none;padding:0}}.steps li{{border:1px solid var(--line);padding:8px;background:#fff}}@media(max-width:720px){{main{{padding:10px}}table{{display:block;overflow:auto}}}}
</style></head><body><main>
<header><div class="kicker">Juriscribe · fascicolo per autore, responsabile scientifico e redazione</div><h1>{esc(req.get('summary') or 'Lavorazione corrente')}</h1><div class="verdict {status_class(completion.get('eligible'))}">{release}</div><p>Sessione <code>{esc(state.get('session_id'))}</code>. La dashboard mostra evidenze e decisioni editoriali; non espone chain-of-thought.</p>{('<div class="block"><strong>Perché non è pronto</strong><ul>'+''.join(f'<li>{esc(item)}</li>' for item in block)+'</ul></div>') if block else '<div class="good"><strong>Tutti i gate di consegna risultano chiusi.</strong></div>'}{('<div class="decision"><strong>Decisioni umane aperte:</strong> '+esc(len(human_decisions))+'</div>') if human_decisions else ''}</header>
<div class="grid">{metric('Fase',state.get('phase'))}{metric('Reticolo',ret.get('status','NON ESEGUITO'))}{metric('Bozze sigillate',len(drafts))}{metric('Cicli review',len(cycles))}{metric('Rigenerazioni',len(regenerations))}{metric('Review',review.get('status','NOT_STARTED'))}{metric('P review',saturation.get('P',0))}{metric('P+10.000',saturation.get('no_novelty_streak',0))}{metric('Fonti',source_intel.get('coverage_status','NOT_STARTED'))}{metric('Bibliografia',bibliography.get('status','NOT_AVAILABLE'))}{metric('Qualità finale',quality.get('status','NOT_RUN'))}{metric('node.h',node.get('status','NOT_CHECKED'))}</div>
<section><h2>1. Mandato e percorso di lavorazione</h2><p><strong>Richiesta:</strong> {esc(req.get('raw',''))}</p><p class="explain">Il capitolo viene costruito dai capitoli precedenti: prima mappa tesi/regole/eccezioni e relazioni, poi genera una bozza, la sottopone a review severa, rigenera e chiude solo quando non emergono nuove criticità o miglioramenti materiali senza degradazione.</p><ul class="steps"><li>Mining atomico</li><li>Reticolo</li><li>Setup</li><li>Bozza</li><li>Review scientifica</li><li>Rigenerazione</li><li>Saturazione</li><li>Compressione</li><li>Controllo finale</li></ul><h3>Parametri accettati</h3><table><tbody>{''.join(f'<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>' for k,v in setup.get('accepted',{}).items()) or '<tr><td class="muted">Setup non ancora accettato</td></tr>'}</tbody></table></section>
<section><h2>2. Mappa scientifica dei capitoli precedenti</h2><div class="grid">{metric('Unità epistemiche',ret.get('node_count',len(units)))}{metric('Relazioni',ret.get('relation_count',len(relations)))}{metric('Locator materiali',ret.get('material_locator_coverage','n/a'))}{metric('Unità connesse',ret.get('connected_material_coverage','n/a'))}{metric('Legami inter-capitolo',ret.get('cross_chapter_relations',len(cross)))}{metric('Contraddizioni',ret.get('contradiction_relations',0))}</div><details><summary><strong>Apri inventario epistemico</strong></summary><table><thead><tr>{header(unit_cols)}</tr></thead><tbody>{rows(units,unit_cols)}</tbody></table></details><details><summary><strong>Apri legami fra capitoli</strong></summary><table><thead><tr><th>Da</th><th>Relazione</th><th>A</th><th>Elemento</th><th>Elemento collegato</th></tr></thead><tbody>{''.join(f'<tr><td>{esc(item["from"])}</td><td>{esc(item["relation"])}</td><td>{esc(item["to"])}</td><td>{esc(item["subject"])}</td><td>{esc(item["target"])}</td></tr>' for item in cross) or '<tr><td colspan="5" class="muted">Nessun legame inter-capitolo registrato</td></tr>'}</tbody></table></details></section>
<section><h2>3. Review scientifico-editoriale e rigenerazione</h2><p class="explain">La review usa un nucleo comune: contributo monografico, coerenza inter-capitolo, autorità giuridiche, citazioni/pinpoint, controautorità, tempo/giurisdizione, inferenze, terminologia, struttura, stile, bibliografia, preservazione lossless e adeguatezza al lettore. Lo stile citazionale specifico resta quello scelto dal progetto editoriale.</p><div class="grid">{metric('Candidato corrente',current_draft.get('stage','NON PRESENTE'))}{metric('Review ultimo ciclo',latest_cycle.get('status','NOT_RUN'))}{metric('Standard',latest_cycle.get('standard_id','NOT_RUN'))}{metric('Evidenze review',latest_cycle.get('evidence_count',0))}{metric('Blocker aperti',latest_cycle.get('open_blockers',0))}{metric('Major aperti',latest_cycle.get('open_majors',0))}{metric('No novelty review',saturation.get('no_novelty_streak',0))}{metric('No improvement',saturation.get('no_improvement_without_degradation_streak',0))}</div><h3>Esito per criterio — ultimo ciclo</h3><table><thead><tr><th>Criterio</th><th>Punteggio 0–1</th></tr></thead><tbody>{score_rows}</tbody></table><h3>Rilievi ancora aperti</h3><table><thead><tr>{header(finding_cols)}</tr></thead><tbody>{rows(open_findings,finding_cols,'Nessun rilievo aperto')}</tbody></table><details><summary><strong>Cronologia dei cicli</strong></summary><table><thead><tr><th>Ciclo</th><th>Digest candidato</th><th>Esito</th><th>Blocker</th><th>Major</th></tr></thead><tbody>{''.join(f'<tr><td>{esc(c.get("cycle"))}</td><td><code>{esc(str(c.get("candidate_digest",""))[:12])}</code></td><td>{esc(c.get("status"))}</td><td>{esc(c.get("open_blockers"))}</td><td>{esc(c.get("open_majors"))}</td></tr>' for c in cycles) or '<tr><td colspan="5" class="muted">Nessun ciclo</td></tr>'}</tbody></table></details></section>
<section><h2>4. Fonti, bibliografia e inferenze</h2><p class="explain">Una bibliografia disponibile orienta la ricerca, ma non prova da sola un claim. Per i claim materiali servono fonti lette, verificate e circostanziate; la dashboard distingue inoltre le inferenze forti dai fatti attestati.</p><div class="grid">{metric('Claim materiali',sum(1 for c in claims if c.get('material',True)))}{metric('Evidence locator',len(evidence))}{metric('Copertura bibliografia',bibliography.get('coverage','n/a'))}{metric('Inferenze forti',len(strong_inferences))}</div><table><thead><tr>{header(source_cols)}</tr></thead><tbody>{rows(sources,source_cols,'Nessuna fonte registrata')}</tbody></table><details><summary><strong>Inferenze forti</strong></summary><table><thead><tr><th>Claim</th><th>Premesse</th><th>Ponte</th><th>Falsificatore</th><th>Stato</th></tr></thead><tbody>{''.join(f'<tr><td>{esc(c.get("text"))}</td><td>{esc(c.get("premise_claim_ids",[]))}</td><td>{esc(c.get("inference_bridge"))}</td><td>{esc(c.get("falsifier"))}</td><td>{esc(c.get("status"))}</td></tr>' for c in strong_inferences) or '<tr><td colspan="5" class="muted">Nessuna inferenza forte</td></tr>'}</tbody></table></details></section>
<section><h2>5. DoD e controllo editoriale finale</h2><div class="grid">{metric('DoD chiusi',f'{done}/{len(dod)}')}{metric('Parole corpo',quality.get('body_word_count','n/a'))}{metric('Lunghezza',quality.get('length_status','NOT_RUN'))}{metric('Stile', (quality.get('style') or {}).get('status','NOT_RUN'))}{metric('Duplicazioni', (quality.get('cross_chapter_duplication') or {}).get('status','NOT_RUN'))}{metric('Tracciabilità claim', (quality.get('claim_traceability') or {}).get('status','NOT_RUN'))}</div><table><thead><tr>{header(dod_cols)}</tr></thead><tbody>{rows(dod,dod_cols,'DoD non ancora congelati')}</tbody></table></section>
<section><h2>6. Simulazioni, saturazione e compressione</h2><div class="grid">{metric('Casi simulati',simulation.get('cases',0))}{metric('Seed',len(simulation.get('seeds',[])))}{metric('Failure',simulation.get('failures','n/a'))}{metric('Escape',simulation.get('escapes','n/a'))}{metric('Falsi positivi',simulation.get('false_positives','n/a'))}{metric('M+10.000 DoD',metrics.get('dod_no_novelty_streak',0))}{metric('P review',saturation.get('P',0))}{metric('P+10.000 novelty',saturation.get('no_novelty_streak',0))}{metric('P+10.000 improvement',saturation.get('no_improvement_without_degradation_streak',0))}{metric('Compressione',compression.get('status','NOT_RUN'))}{metric('Recheck post-compressione',compression.get('post_compression_recheck','NOT_RUN'))}</div><p><strong>Classi simulate:</strong> {esc(simulation.get('categories',{}))}.</p><p><strong>Unità obbligatorie perse:</strong> {esc(compression.get('lost_required_unit_ids',[]))}. <strong>Nuovo materiale introdotto:</strong> {esc(compression.get('added_material_unit_ids',[]))}.</p></section>
<section><h2>7. Limiti, benchmark e integrità locale</h2><p><strong>Contraddizioni aperte:</strong> {esc(len([c for c in contradictions if c.get('status','OPEN')!='RESOLVED']))}. <strong>Benchmark monografico:</strong> {esc(benchmark.get('monograph','non richiesto/non eseguito'))}.</p><table><thead><tr><th>Limite</th><th>Impatto</th><th>Mitigazione</th></tr></thead><tbody>{rows(limits,[('Limite','id'),('Impatto','impact'),('Mitigazione','mitigation')],'Nessun limite registrato')}</tbody></table><p><strong>node.h:</strong> {esc(node.get('status','NOT_CHECKED'))}. È un header locale di soli metadati/digest che collega stato, reticolo, setup, DoD, candidato, review, bibliografia, simulazione e compressione.</p></section>
<section><h2>8. Artefatti e decisione</h2><table><thead><tr>{header(artifact_cols)}</tr></thead><tbody>{rows(artifacts,artifact_cols,'Nessun artefatto')}</tbody></table><p><strong>Decisione:</strong> {release}. <strong>Motivo:</strong> {esc(completion.get('reason','non ancora valutato'))}.</p></section>
<footer class="muted"><p>Gli indicatori documentano il processo e le evidenze disponibili. Non sostituiscono il giudizio giuridico del responsabile scientifico né trasformano simulazioni computazionali in decisioni legali.</p></footer>
</main></body></html>'''
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out
