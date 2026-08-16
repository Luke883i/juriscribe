from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable

from .editorial_artifacts import build_editorial_artifact_views
from .evidence_traceability import build_evidence_traceability, build_user_artifact_index
from .modes import required_artifact_roles

PROFILE_ID = "JURISCRIBE_ARTIFACT_ATLAS_V1"
SCHEMA = "juriscribe-artifact-atlas/v1"
INTERNAL = "INTERNAL"

TECHNICAL_KEYS = {
    "digest", "record_digest", "contract_digest", "setup_digest", "reticulum_digest", "candidate_digest",
    "corpus_digest", "normative_frame_digest", "provenance_digest", "mode_contract_digest", "editorial_standard_digest",
    "generation_contract_digest", "configuration_digest", "candidate_fingerprint_digest", "fingerprint_digest",
    "document_digest", "segment_digest", "exact_ngram_hashes", "shingle_hashes", "state_digest", "sha256", "path",
    "absolute_path", "resolved_path", "readback", "size_bytes", "materialized", "verified_format", "workspace_confined",
    "capability", "capabilities", "runtime", "integrity", "node_integrity", "traceback", "internal_message",
    "resource_limits", "probe_seeds", "seed", "seeds",
}

ROLE_META = {
    "final_chapter": ("Capitolo finale", "Testo finale generato in continuità con il corpus precedente."),
    "final_legal_text": ("Testo giuridico finale", "Prodotto giuridico generato ex novo secondo il mandato accettato."),
    "review_report": ("Relazione di revisione", "Esito argomentato della revisione scientifica, contenutistica, logica ed editoriale."),
    "review_findings_register": ("Registro dei rilievi", "Inventario completo di finding, severità, azioni e stato della revisione."),
    "revised_legal_text": ("Testo giuridico revisionato", "Testo revisionato risultante da finding, rigenerazione e ri-controllo."),
    "evidence_dossier": ("Evidence dossier", "Architettura probatoria completa delle proposizioni materiali."),
    "source_register": ("Source register", "Geografia delle fonti, della loro autorità e del loro uso effettivo."),
    "inference_register": ("Inference register", "Premesse, ponti, falsificatori e conclusioni delle inferenze materiali."),
    "transformation_ledger": ("Transformation ledger", "Storia causale delle trasformazioni, revisioni e preservazioni."),
    "session_dashboard": ("Dashboard di sessione", "Workbench umano che sintetizza e rende richiamabili tutti gli artefatti della sessione."),
}

ROLE_ANCHORS = {
    "final_chapter": "#artifact-atlas",
    "final_legal_text": "#artifact-atlas",
    "review_report": "#artifact-atlas",
    "review_findings_register": "#artifact-atlas",
    "revised_legal_text": "#artifact-atlas",
    "evidence_dossier": "#evidence-dossier",
    "source_register": "#source-register",
    "inference_register": "#inference-register",
    "transformation_ledger": "#transformation-ledger",
    "session_dashboard": "#top",
}


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _public(value: Any) -> Any:
    if isinstance(value, dict):
        out = OrderedDict()
        for key, item in value.items():
            token = str(key)
            lowered = token.lower()
            if lowered in TECHNICAL_KEYS or lowered.endswith("_digest") or lowered.endswith("_sha"):
                continue
            cleaned = _public(item)
            if cleaned not in (None, "", [], {}, ()):
                out[token] = cleaned
        return dict(out)
    if isinstance(value, (list, tuple, set)):
        cleaned = [_public(item) for item in value]
        return [item for item in cleaned if item not in (None, "", [], {}, ())]
    return value


def _has(value: Any) -> bool:
    return value not in (None, "", [], {}, ())


def _status(record: Any, default: str = "REGISTRATO") -> str:
    if isinstance(record, dict):
        for key in ("status", "stato", "coverage_status"):
            if str(record.get(key) or "").strip():
                return str(record.get(key))
    return default


def _expected_roles(s: dict[str, Any]) -> set[str]:
    mode = str(s.get("mode") or "").strip()
    if not mode:
        return {"session_dashboard"}
    try:
        return set(required_artifact_roles(mode, s.get("setup") or {}))
    except ValueError:
        return {"session_dashboard"}


def _human_artifacts(s: dict[str, Any]) -> list[dict[str, Any]]:
    expected = _expected_roles(s)
    return [
        dict(item) for item in (s.get("artifacts") or [])
        if str(item.get("role") or "") in expected or str(item.get("delivery_class") or "").upper() != INTERNAL
    ]


def _artifact_href_map(s: dict[str, Any]) -> dict[str, str]:
    index = build_user_artifact_index(s)
    out = {str(item.get("ruolo")): str(item.get("richiamo")) for item in index.get("records") or [] if item.get("ruolo") and item.get("richiamo")}
    return out


def _artifact_evidence_for_role(s: dict[str, Any], role: str, artifact_id: str = "") -> list[dict[str, Any]]:
    rows = []
    for item in s.get("artifact_evidence") or []:
        if str(item.get("artifact_role") or "") == role or (artifact_id and str(item.get("artifact_id") or "") == artifact_id):
            rows.append(_public(item))
    return rows


def _generated_text_description(s: dict[str, Any], role: str, artifact: dict[str, Any] | None) -> dict[str, Any]:
    setup = s.get("setup") or {}
    accepted = setup.get("accepted", setup if setup.get("status") == "ACCEPTED" else {}) or {}
    quality = s.get("quality") or {}
    review = s.get("review") or {}
    return _public({
        "mandato": (s.get("request") or {}).get("summary") or (s.get("request") or {}).get("raw"),
        "modalita": s.get("mode"),
        "abstract_accettato": accepted.get("generation_abstract"),
        "concetti_chiave_accettati": accepted.get("key_concepts"),
        "lunghezza_accettata": accepted.get("length_words"),
        "conformita_configurazione": quality.get("generation_configuration"),
        "qualita_finale": {k: v for k, v in quality.items() if k not in {"plagiarism", "generation_configuration"}},
        "originalita": quality.get("plagiarism"),
        "copertura_fonti": (s.get("source_intelligence") or {}).get("coverage_status"),
        "review": {"status": review.get("status"), "cycles": review.get("cycles"), "saturation": review.get("saturation")},
        "provenance": s.get("provenance"),
        "review_finale_severa": s.get("final_review"),
        "saturazione_pre_consegna": review.get("delivery_saturation"),
        "evidenze_collocate": _artifact_evidence_for_role(s, role, str((artifact or {}).get("id") or "")),
    })


def _review_description(s: dict[str, Any], role: str, artifact: dict[str, Any] | None) -> dict[str, Any]:
    review = s.get("review") or {}
    return _public({
        "mandato": (s.get("request") or {}).get("summary") or (s.get("request") or {}).get("raw"),
        "perimetro_accettato": ((s.get("setup") or {}).get("accepted") or {}).get("review_scope"),
        "esito_richiesto": ((s.get("setup") or {}).get("accepted") or {}).get("review_output"),
        "cicli_review": review.get("cycles"),
        "rigenerazioni": review.get("regenerations"),
        "saturazione_review": review.get("saturation"),
        "audit_qualita": s.get("quality"),
        "provenance": s.get("provenance"),
        "review_finale_severa": s.get("final_review"),
        "saturazione_pre_consegna": review.get("delivery_saturation"),
        "evidenze_collocate": _artifact_evidence_for_role(s, role, str((artifact or {}).get("id") or "")),
    })


def _material_artifact_records(s: dict[str, Any], dossier_views: dict[str, Any]) -> list[dict[str, Any]]:
    expected = _expected_roles(s)
    actual = _human_artifacts(s)
    by_role = {str(item.get("role") or ""): item for item in actual if item.get("role")}
    roles = sorted(expected | set(by_role), key=lambda item: (list(ROLE_META).index(item) if item in ROLE_META else 999, item))
    hrefs = _artifact_href_map(s)
    records = []
    for role in roles:
        artifact = by_role.get(role)
        title, purpose = ROLE_META.get(role, (role.replace("_", " ").title(), "Artefatto umano della sessione Juriscribe."))
        if role in dossier_views:
            detail = dossier_views[role]
            summary = f"{len(detail.get('records') or [])} record semantici; contenuto proiettato integralmente nella dashboard."
        elif role in {"final_chapter", "final_legal_text", "revised_legal_text"}:
            detail = _generated_text_description(s, role, artifact)
            summary = "Testo narrativo finale descritto mediante configurazione accettata, qualità, originalità, provenance, review e collocazioni probatorie."
        elif role in {"review_report", "review_findings_register"}:
            detail = _review_description(s, role, artifact)
            finding_count = sum(len(cycle.get("findings") or []) for cycle in ((s.get("review") or {}).get("cycles") or []))
            summary = f"Artefatto di review collegato a {finding_count} finding registrati e al relativo percorso di saturazione."
        elif role == "session_dashboard":
            detail = {
                "funzione": "superficie di lettura complessiva della sessione",
                "copre_artefatti_materiali": len(roles),
                "copre_artefatti_epistemici": "vedi Mappa completa degli artefatti epistemici",
                "esito_sessione": (s.get("completion") or {}).get("eligible"),
            }
            summary = "Dashboard corrente: sintesi compressa, descrizione completa e richiamo di tutti gli artefatti umani ed epistemici." 
        else:
            detail = _public(artifact or {})
            summary = str((artifact or {}).get("summary") or purpose)
        status = "DISPONIBILE" if artifact else "ATTESO"
        if artifact and str(artifact.get("delivery_class") or "").upper() == INTERNAL:
            continue
        records.append({
            "id": f"material:{role}",
            "tipo": "ARTEFATTO_MATERIALE",
            "ruolo": role,
            "titolo": title,
            "funzione": purpose,
            "stato": status,
            "sintesi_compressa": summary,
            "descrizione_completa": _public(detail),
            "richiamo_dashboard": ROLE_ANCHORS.get(role, "#artifact-atlas"),
            "richiamo_artefatto": hrefs.get(role),
        })
    return records


def _epistemic_record(identifier: str, title: str, purpose: str, value: Any, anchor: str, *, status: str | None = None, source: str = "stato canonico") -> dict[str, Any]:
    public = _public(value)
    if isinstance(public, dict):
        measure = len(public.get("records") or public.get("entries") or public.get("cycles") or public.get("findings") or [])
    elif isinstance(public, list):
        measure = len(public)
    else:
        measure = 1 if _has(public) else 0
    return {
        "id": f"epistemic:{identifier}",
        "tipo": "ARTEFATTO_EPISTEMICO",
        "ruolo": identifier,
        "titolo": title,
        "funzione": purpose,
        "stato": status or _status(value),
        "sorgente": source,
        "sintesi_compressa": f"{title}: {measure} elemento/i semanticamente materializzati; dettaglio completo disponibile qui sotto.",
        "descrizione_completa": public,
        "richiamo_dashboard": anchor,
    }


def _epistemic_records(s: dict[str, Any], dossier_views: dict[str, Any]) -> list[dict[str, Any]]:
    setup = s.get("setup") or {}
    generation_contract = s.get("generation_contract") or {}
    continuation = s.get("continuation") or {}
    review = s.get("review") or {}
    quality = s.get("quality") or {}
    source_intelligence = s.get("source_intelligence") or {}
    records: list[dict[str, Any]] = []

    specs: list[tuple[str, str, str, Any, str]] = [
        ("epistemic_inventory", "Inventario epistemico", "Unità atomiche e relazioni tipizzate che costituiscono il patrimonio semantico di base.", {"unita": s.get("epistemic_units") or [], "relazioni": s.get("relations") or []}, "#epistemic-artifacts"),
        ("reticulum", "Validazione del reticolo epistemico", "Attesta connessione, locator, copertura delle fonti e coerenza del reticolo.", s.get("reticulum"), "#epistemic-artifacts"),
        ("claim_ledger", "Claim ledger", "Inventario delle proposizioni materiali, supporti, inferenze e stati epistemici.", s.get("claim_ledger") or [], "#evidence-dossier"),
        ("contradictions", "Registro delle contraddizioni", "Contraddizioni materiali, stato di risoluzione e funzione nel controllo logico.", s.get("contradictions") or [], "#epistemic-artifacts"),
        ("mode_contract", "Contratto di modalità", "Vincola il lavoro alla modalità selezionata, ai requisiti e agli artefatti finali attesi.", s.get("mode_contract"), "#epistemic-artifacts"),
        ("editorial_standard", "Standard editoriale", "Regole giuridico-editoriali applicate al prodotto.", s.get("editorial_standard"), "#epistemic-artifacts"),
        ("generation_configuration", "Configurazione di generazione", "Abstract, concetti chiave e lunghezza sottoposti all'utente e poi congelati.", setup.get("generation_configuration") or setup.get("generation_preview"), "#generation-configuration"),
        ("generation_contract", "Contratto meccanico di generazione", "Lega configurazione, reticolo e obblighi di preservazione/sviluppo al candidato.", generation_contract, "#generation-configuration"),
        ("continuation_plan", "Piano di continuazione", "Fronte argomentativo da sviluppare rispetto al corpus pregresso.", continuation.get("plan"), "#epistemic-artifacts"),
        ("continuation_coverage", "Copertura di continuazione", "Dimostra la copertura del piano e l'assenza di duplicazioni/lacune materiali.", continuation.get("coverage"), "#epistemic-artifacts"),
        ("bibliography", "Valutazione bibliografica", "Disponibilità, copertura e qualità della bibliografia usata.", s.get("bibliography"), "#source-register"),
        ("source_intelligence", "Intelligence delle fonti", "Piano di ricerca, copertura claim-fonte e valutazioni di dominanza.", source_intelligence, "#source-register"),
        ("quality_audit", "Audit di qualità", "Verifica lunghezza, stile, apparato, tracciabilità e conformità editoriale.", {k: v for k, v in quality.items() if k not in {"plagiarism", "generation_configuration"}}, "#epistemic-artifacts"),
        ("plagiarism_audit", "Receipt anti-plagio", "Prova scoped dell'assenza di sovrapposizioni vietate nel corpus di confronto registrato.", quality.get("plagiarism"), "#anti-plagiarism"),
        ("benchmark", "Benchmark cieco", "Confronto strutturale richiesto per extrapolazioni monografiche quando applicabile.", s.get("benchmark"), "#epistemic-artifacts"),
        ("review_cycles", "Cicli di review scientifico-editoriale", "Finding, severità, azioni e ri-esami causali del candidato.", {"cycles": review.get("cycles") or [], "regenerations": review.get("regenerations") or []}, "#transformation-ledger"),
        ("review_saturation", "Saturazione della review", "Fixed point della revisione scientifico-editoriale prima della fase finale.", review.get("saturation"), "#transformation-ledger"),
        ("simulation_receipt", "Receipt di simulazione", "Esito delle simulazioni avverse, favorevoli, stress, editoriali e logico-semantiche.", s.get("simulations"), "#epistemic-artifacts"),
        ("compression_record", "Record di compressione", "Dimostra preservazione delle unità richieste e assenza di nuovo materiale nella compressione finale.", s.get("compression"), "#transformation-ledger"),
        ("provenance_bundle", "Bundle di provenance", "Ricostruisce evidenze, decisioni, trasformazioni e collocazioni finali senza esporre ragionamento latente.", s.get("provenance"), "#epistemic-artifacts"),
        ("final_severe_review", "Review finale severa", "Riesame conclusivo della cornice normativa, autorità, inferenze, conseguenze e trasformazioni.", s.get("final_review"), "#transformation-ledger"),
        ("dod_ledger", "Definition of Done", "Obblighi globali/locali e relativo stato di chiusura.", s.get("dod") or [], "#epistemic-artifacts"),
    ]
    for identifier, title, purpose, value, anchor in specs:
        if _has(value):
            records.append(_epistemic_record(identifier, title, purpose, value, anchor))

    dossier_meta = {
        "evidence_dossier": ("Evidence dossier", "Architettura probatoria completa del testo.", "#evidence-dossier"),
        "source_register": ("Source register", "Geografia delle fonti e del loro uso effettivo.", "#source-register"),
        "inference_register": ("Inference register", "Premesse, ponti e falsificatori delle inferenze materiali.", "#inference-register"),
        "transformation_ledger": ("Transformation ledger", "Storia causale di review, rigenerazioni e trasformazioni.", "#transformation-ledger"),
    }
    for identifier, (title, purpose, anchor) in dossier_meta.items():
        value = dossier_views[identifier]
        records.append(_epistemic_record(identifier, title, purpose, value, anchor, status="POPOLATO" if value.get("records") else "VUOTO", source="proiezione semantica canonica"))

    trace = build_evidence_traceability(s)
    records.append(_epistemic_record("artifact_evidence_traceability", "Tracciabilità delle evidenze negli artefatti", "Lega claim, fonti/pinpoint e collocazioni nel prodotto consegnato.", trace, "#evidence-traceability", status=_status(trace, "DA_COMPLETARE"), source="proiezione lossless artifact_evidence"))
    if _has(review.get("delivery_saturation")):
        records.append(_epistemic_record("predelivery_saturation", "Saturazione pre-consegna", "Riesegue ciclicamente i gate finali fino a un fixed point senza nuovi blocker.", review.get("delivery_saturation"), "#predelivery-saturation"))
    return records


def build_artifact_atlas(state: Any) -> dict[str, Any]:
    s = _payload(state)
    dossier_views = build_editorial_artifact_views(s)
    material = _material_artifact_records(s, dossier_views)
    epistemic = _epistemic_records(s, dossier_views)
    available = sum(1 for item in material if item.get("stato") == "DISPONIBILE")
    expected = len(material)
    summary = [
        f"{available}/{expected} artefatti materiali previsti o prodotti sono disponibili; ciascuno ha una descrizione completa e un richiamo contestuale.",
        f"{len(epistemic)} artefatti epistemici attivi sono proiettati con sintesi compressa e contenuto pubblico completo.",
        "Gli artefatti INTERNAL e la telemetria tecnica sono esclusi dalla superficie umana; il contenuto inferenziale, probatorio ed editoriale resta invece esplicito.",
    ]
    return {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "titolo": "Atlante completo degli artefatti",
        "finalita": "Descrivere in forma insieme completa e compressa ogni artefatto umano ed epistemico della sessione, consentendo drill-down e richiamo senza duplicare telemetria tecnica.",
        "sintesi_compressa": summary,
        "artefatti_materiali": material,
        "artefatti_epistemici": epistemic,
        "copertura": {
            "materiali_descritti": len(material),
            "epistemici_descritti": len(epistemic),
            "internal_esclusi": sum(1 for item in (s.get("artifacts") or []) if str(item.get("delivery_class") or "").upper() == INTERNAL),
        },
    }


def _active_epistemic_ids(s: dict[str, Any], atlas: dict[str, Any]) -> set[str]:
    return {str(item.get("ruolo")) for item in atlas.get("artefatti_epistemici") or [] if item.get("ruolo")}


def artifact_dashboard_coverage_gate(state: Any, atlas: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    s = _payload(state)
    view = atlas or build_artifact_atlas(s)
    errors: list[str] = []
    material = view.get("artefatti_materiali") or []
    epistemic = view.get("artefatti_epistemici") or []
    material_roles = [str(item.get("ruolo")) for item in material if item.get("ruolo")]
    expected = _expected_roles(s)
    missing_material = sorted(expected - set(material_roles))
    if missing_material:
        errors.append("dashboard artifact atlas missing expected material roles: " + ", ".join(missing_material))
    human_actual_roles = {str(item.get("role")) for item in _human_artifacts(s) if item.get("role")}
    missing_actual = sorted(human_actual_roles - set(material_roles))
    if missing_actual:
        errors.append("dashboard artifact atlas missing produced human artifacts: " + ", ".join(missing_actual))
    ids = [str(item.get("id")) for item in material + epistemic if item.get("id")]
    if len(ids) != len(set(ids)):
        errors.append("dashboard artifact atlas contains duplicate artifact identities")
    for item in material + epistemic:
        if not str(item.get("sintesi_compressa") or "").strip():
            errors.append(f"artifact {item.get('id')} lacks compressed description")
        if not _has(item.get("descrizione_completa")):
            errors.append(f"artifact {item.get('id')} lacks complete public description")
        if not str(item.get("richiamo_dashboard") or "").strip():
            errors.append(f"artifact {item.get('id')} lacks dashboard recall")
    active = _active_epistemic_ids(s, view)
    mandatory = {"evidence_dossier", "source_register", "inference_register", "transformation_ledger", "artifact_evidence_traceability"}
    missing_mandatory = sorted(mandatory - active)
    if missing_mandatory:
        errors.append("dashboard atlas missing canonical epistemic artifacts: " + ", ".join(missing_mandatory))
    conditional = {
        "generation_configuration": bool((s.get("setup") or {}).get("generation_preview") or (s.get("setup") or {}).get("generation_configuration")),
        "generation_contract": (s.get("generation_contract") or {}).get("status") == "READY",
        "plagiarism_audit": _has((s.get("quality") or {}).get("plagiarism")),
        "predelivery_saturation": _has((s.get("review") or {}).get("delivery_saturation")),
        "provenance_bundle": _has(s.get("provenance")),
        "final_severe_review": _has(s.get("final_review")),
        "simulation_receipt": _has(s.get("simulations")),
        "compression_record": _has(s.get("compression")),
        "claim_ledger": _has(s.get("claim_ledger")),
        "epistemic_inventory": _has(s.get("epistemic_units")) or _has(s.get("relations")),
    }
    for identifier, required in conditional.items():
        if required and identifier not in active:
            errors.append(f"active epistemic artifact is not represented in dashboard atlas: {identifier}")
    return not errors, list(dict.fromkeys(errors))
