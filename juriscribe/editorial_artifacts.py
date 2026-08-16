from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any

from .review import REVIEW_CRITERIA

SEMANTIC_SCHEMA = "juriscribe-legal-humanistic-artifacts/v1"
PROFILE_ID = "JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1"
DOSSIER_ROLES = (
    "evidence_dossier",
    "source_register",
    "inference_register",
    "transformation_ledger",
)
SEMANTIC_ARTIFACT_ROLES = frozenset((*DOSSIER_ROLES, "session_dashboard"))

_AUTHORITY_LABELS = {
    "primary_law": "fonte normativa primaria",
    "constitutional_court": "giurisprudenza costituzionale",
    "supreme_court": "giurisprudenza di legittimita",
    "eu_court": "giurisprudenza dell'Unione europea",
    "echr": "giurisprudenza convenzionale CEDU",
    "administrative_supreme_court": "giurisprudenza amministrativa apicale",
    "official_institutional": "fonte istituzionale ufficiale",
    "peer_reviewed_doctrine": "dottrina scientifica peer-reviewed",
    "leading_treatise": "trattazione dottrinale di riferimento",
    "specialist_commentary": "commento specialistico",
    "corpus_chapter": "testo autoriale del corpus",
    "user_supplied_material": "materiale fornito dall'autore",
    "other": "fonte ulteriore",
}

_RELATION_LABELS = {
    "SUPPORTS": "sostiene",
    "CONTRADICTS": "contraddice",
    "QUALIFIES": "qualifica",
    "DEPENDS_ON": "dipende da",
    "DEFINES": "definisce",
    "APPLIES_TO": "si applica a",
    "DISTINGUISHES": "distingue",
    "SUPERSEDES": "supera",
    "INTRODUCED_IN": "e introdotto in",
    "RESOLVED_IN": "e risolto in",
    "ANTICIPATES": "anticipa",
    "RECALLS": "richiama",
    "REQUIRES_SOURCE": "richiede fonte",
    "INFERRED_FROM": "e inferito da",
    "DEVELOPS": "sviluppa",
    "AVOIDS_DUPLICATION_OF": "evita duplicazione di",
}


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _clean(value: Any) -> Any:
    """Keep only human-facing semantic content; drop empty containers and values."""
    if isinstance(value, dict):
        cleaned = OrderedDict()
        for key, item in value.items():
            item = _clean(item)
            if item not in (None, "", [], {}, ()): cleaned[str(key)] = item
        return dict(cleaned)
    if isinstance(value, (list, tuple, set)):
        cleaned = [_clean(item) for item in value]
        return [item for item in cleaned if item not in (None, "", [], {}, ())]
    return value


def _by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in items or [] if item.get("id")}


def _provenance_entries(state: dict[str, Any], kind: str | None = None) -> list[dict[str, Any]]:
    entries = list((state.get("provenance") or {}).get("entries") or [])
    if kind is None: return entries
    return [item for item in entries if str(item.get("kind", "")).upper() == kind]


def _authority_character(source: dict[str, Any]) -> str:
    source_type = str(source.get("source_type", "other"))
    return _AUTHORITY_LABELS.get(source_type, source_type.replace("_", " "))


def _claim_source_evidence(claim: dict[str, Any], sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    evidence_by_source = {
        str(item.get("source_id")): item
        for item in claim.get("source_evidence", []) or [] if item.get("source_id")
    }
    rows = []
    for source_id in claim.get("support_source_ids", []) or []:
        source_id = str(source_id)
        source = sources.get(source_id, {})
        evidence = evidence_by_source.get(source_id, {})
        rows.append(_clean({
            "riferimento_fonte": source_id,
            "fonte": source.get("title") or source_id,
            "carattere_autorita": _authority_character(source),
            "giurisdizione": source.get("jurisdiction"),
            "collocazione_temporale": source.get("date"),
            "pinpoint": evidence.get("pinpoint"),
            "proposizione_attestata": evidence.get("proposition"),
            "funzione": source.get("role"),
        }))
    return rows


def _relation_context(reference: str, relations: list[dict[str, Any]], units: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for relation in relations or []:
        src, dst = str(relation.get("source", "")), str(relation.get("target", ""))
        if reference not in {src, dst}: continue
        other = dst if src == reference else src
        rows.append(_clean({
            "relazione": _RELATION_LABELS.get(str(relation.get("predicate", "")), str(relation.get("predicate", "")).lower()),
            "verso": other,
            "contenuto_correlato": (units.get(other) or {}).get("text"),
            "ragione": relation.get("rationale"),
        }))
    return rows


def _artifact_locators(state: dict[str, Any], reference: str) -> list[str]:
    out = []
    for item in state.get("artifact_evidence") or []:
        if str(item.get("claim_id", "")) == reference and str(item.get("artifact_locator", "")).strip():
            out.append(str(item.get("artifact_locator")))
    return list(dict.fromkeys(out))


def _legal_function(kind: str, claim_type: str = "") -> str:
    token = str(claim_type or kind or "").lower()
    mapping = {
        "rule": "regola normativa o criterio giuridico",
        "definition": "definizione operativa",
        "claim": "proposizione giuridica materiale",
        "strong_inference": "inferenza giuridica forte",
        "inference": "passaggio inferenziale esplicito",
        "qualification": "qualificazione o limite",
        "exception": "eccezione alla regola",
        "counterargument": "controargomento",
        "conclusion": "conclusione argomentativa",
        "interpretive_proposal": "proposta interpretativa",
        "editorial": "scelta editoriale motivata",
    }
    return mapping.get(token, token.replace("_", " ") or "elemento del ragionamento")


def build_evidence_dossier(state: Any) -> dict[str, Any]:
    s = _payload(state)
    sources = _by_id(s.get("sources") or [])
    claims = _by_id(s.get("claim_ledger") or [])
    units = _by_id(s.get("epistemic_units") or [])
    provenance = {str(item.get("id")): item for item in _provenance_entries(s) if item.get("id")}
    records = []
    references = []
    references.extend(str(c.get("id")) for c in s.get("claim_ledger") or [] if c.get("id") and c.get("material", True))
    references.extend(str(u.get("id")) for u in s.get("epistemic_units") or [] if u.get("id") and u.get("material", True) and u.get("kind") in {"RULE", "DEFINITION", "ARGUMENT", "COUNTERARGUMENT", "EXCEPTION", "QUALIFICATION", "CONCLUSION", "INFERENCE"})
    for reference in dict.fromkeys(references):
        claim = claims.get(reference, {})
        unit = units.get(reference, {})
        prov = provenance.get(reference, {})
        evidence = _claim_source_evidence(claim, sources)
        if not evidence:
            for source_id in prov.get("evidence_refs", []) or []:
                source = sources.get(str(source_id), {})
                evidence.append(_clean({
                    "riferimento_fonte": source_id,
                    "fonte": source.get("title") or source_id,
                    "carattere_autorita": _authority_character(source),
                    "giurisdizione": source.get("jurisdiction"),
                    "collocazione_temporale": source.get("date"),
                }))
        locators = list(prov.get("artifact_locators") or []) + _artifact_locators(s, reference)
        records.append(_clean({
            "riferimento": reference,
            "proposizione": prov.get("proposition") or claim.get("text") or unit.get("text"),
            "funzione_giuridica": _legal_function(str(unit.get("kind", "")), str(claim.get("claim_type", ""))),
            "ambito": claim.get("scope"),
            "stato_epistemico": claim.get("status") or unit.get("status"),
            "evidenze": evidence,
            "premesse": claim.get("premise_claim_ids") or prov.get("premise_ids"),
            "ponte_inferenziale": claim.get("inference_bridge") or prov.get("inference_bridge"),
            "condizione_di_confutazione": claim.get("falsifier") or prov.get("falsifier"),
            "contesto_relazionale": _relation_context(reference, s.get("relations") or [], units),
            "ragione_editoriale_o_probatoria": prov.get("rationale"),
            "disposizione_finale": prov.get("disposition"),
            "collocazione_nel_testo": list(dict.fromkeys(str(x) for x in locators if str(x).strip())),
        }))
    return {
        "titolo": "Evidence dossier — architettura probatoria del testo",
        "finalita": "Rendere leggibile, per ciascuna proposizione materiale, il passaggio da fonte o premessa alla formulazione giuridica e alla sua collocazione nel testo.",
        "records": records,
    }


def build_source_register(state: Any) -> dict[str, Any]:
    s = _payload(state)
    claims = s.get("claim_ledger") or []
    records = []
    for source in s.get("sources") or []:
        sid = str(source.get("id", ""))
        supported = [claim for claim in claims if sid in {str(x) for x in claim.get("support_source_ids", []) or []}]
        source_evidence = []
        for claim in supported:
            for ev in claim.get("source_evidence", []) or []:
                if str(ev.get("source_id", "")) == sid:
                    source_evidence.append(_clean({
                        "proposizione": claim.get("text"),
                        "pinpoint": ev.get("pinpoint"),
                        "contenuto_attestato": ev.get("proposition"),
                    }))
        notes = str(source.get("notes", ""))
        records.append(_clean({
            "riferimento": sid,
            "fonte": source.get("title") or sid,
            "carattere_autorita": _authority_character(source),
            "autore_o_organo": source.get("court_or_author"),
            "giurisdizione": source.get("jurisdiction"),
            "collocazione_temporale": source.get("date"),
            "ruolo_nel_lavoro": source.get("role"),
            "uso_nel_ragionamento": [claim.get("text") for claim in supported if claim.get("text")],
            "evidenza_circostanziata": source_evidence,
            "controautorita_o_riserva": notes if "counter" in notes.lower() or "contr" in notes.lower() else None,
            "nota_critica": notes or None,
            "verifica": "lettura diretta verificata" if source.get("direct_read") and source.get("verified_at") else ("lettura diretta" if source.get("direct_read") else "da verificare"),
            "data_verifica": source.get("verified_at"),
            "voce_bibliografica": source.get("bibliography_entry"),
            "collegamento": source.get("url"),
        }))
    return {
        "titolo": "Source register — geografia delle autorita e delle fonti",
        "finalita": "Esplicitare peso, perimetro, funzione e uso effettivo delle fonti, distinguendo autorita, dottrina, corpus autoriale e controautorita.",
        "records": records,
    }


def build_inference_register(state: Any) -> dict[str, Any]:
    s = _payload(state)
    claims = _by_id(s.get("claim_ledger") or [])
    units = _by_id(s.get("epistemic_units") or [])
    sources = _by_id(s.get("sources") or [])
    provenance = {str(item.get("id")): item for item in _provenance_entries(s, "INFERENCE") if item.get("id")}
    references = []
    references.extend(str(item.get("id")) for item in s.get("claim_ledger") or [] if item.get("id") and item.get("claim_type") == "strong_inference" and item.get("material", True))
    references.extend(str(item.get("id")) for item in s.get("epistemic_units") or [] if item.get("id") and item.get("kind") == "INFERENCE" and item.get("material", True))
    references.extend(provenance)
    records = []
    lookup = {**units, **claims}
    for reference in dict.fromkeys(references):
        claim = claims.get(reference, {})
        unit = units.get(reference, {})
        prov = provenance.get(reference, {})
        premise_ids = list(prov.get("premise_ids") or claim.get("premise_claim_ids") or [])
        premise_rows = []
        for premise_id in premise_ids:
            premise = lookup.get(str(premise_id), {})
            premise_rows.append(_clean({
                "riferimento": premise_id,
                "contenuto": premise.get("text"),
                "stato": premise.get("status"),
            }))
        evidence_refs = list(prov.get("evidence_refs") or claim.get("support_source_ids") or [])
        evidence = []
        for source_id in evidence_refs:
            source = sources.get(str(source_id), {})
            evidence.append(_clean({
                "riferimento_fonte": source_id,
                "fonte": source.get("title") or source_id,
                "carattere_autorita": _authority_character(source),
            }))
        relations = _relation_context(reference, s.get("relations") or [], units)
        records.append(_clean({
            "riferimento": reference,
            "conclusione_inferenziale": prov.get("proposition") or claim.get("text") or unit.get("text"),
            "premesse": premise_rows,
            "ponte_inferenziale": prov.get("inference_bridge") or claim.get("inference_bridge"),
            "condizione_di_confutazione": prov.get("falsifier") or claim.get("falsifier"),
            "autorita_o_evidenze": evidence,
            "qualificazioni_obiezioni_e_contrasti": relations,
            "ragione_dell_inferenza": prov.get("rationale"),
            "disposizione_finale": prov.get("disposition"),
            "collocazione_nel_testo": prov.get("artifact_locators"),
        }))
    return {
        "titolo": "Inference register — anatomia delle inferenze giuridiche",
        "finalita": "Separare il dato attestato dal passaggio interpretativo: premesse, ponte, possibilità di confutazione, qualificazioni, controargomenti e destinazione finale.",
        "records": records,
    }


def _criterion_label(criterion: str) -> str:
    return str((REVIEW_CRITERIA.get(str(criterion)) or {}).get("label") or criterion).replace("_", " ")


def build_transformation_ledger(state: Any) -> dict[str, Any]:
    s = _payload(state)
    records: list[dict[str, Any]] = []
    cycles = list((s.get("review") or {}).get("cycles") or [])
    for cycle in cycles:
        for finding in cycle.get("findings", []) or []:
            records.append(_clean({
                "fase": f"review {cycle.get('cycle', '')}".strip(),
                "natura": "rilievo scientifico-editoriale",
                "ragione": _criterion_label(str(finding.get("criterion", ""))),
                "problema_rilevato": finding.get("message") or finding.get("kind"),
                "gravita": finding.get("severity"),
                "intervento_proposto": finding.get("proposed_action"),
                "riferimenti_epistemici": finding.get("epistemic_unit_ids"),
                "fonti_coinvolte": finding.get("source_ids"),
                "collocazione": finding.get("artifact_locator"),
                "esito": finding.get("status", "OPEN"),
            }))
    for regen in (s.get("review") or {}).get("regenerations", []) or []:
        lost = list(regen.get("lost_required_unit_ids") or [])
        introduced = list(regen.get("introduced_material_unit_ids") or [])
        records.append(_clean({
            "fase": f"rigenerazione {regen.get('cycle', '')}".strip(),
            "natura": "trasformazione causale del testo",
            "ragione": "correzione dei finding della review senza perdita del patrimonio epistemico",
            "finding_affrontati": regen.get("addressed_finding_ids"),
            "contenuti_preservati": regen.get("preserved_required_unit_ids"),
            "contenuti_persi": lost,
            "nuovo_materiale": introduced,
            "degradazioni": regen.get("degradation_flags"),
            "esito": "preservazione confermata" if not lost and not introduced and not regen.get("degradation_flags") else regen.get("status"),
        }))
    compression = s.get("compression") or {}
    if compression:
        records.append(_clean({
            "fase": "compressione finale",
            "natura": "compressione editoriale lossless",
            "ragione": "ridurre ridondanza senza modificare il contenuto giuridicamente necessario",
            "estensione_prima": compression.get("before_words"),
            "estensione_dopo": compression.get("after_words"),
            "contenuti_preservati": compression.get("preserved_unit_ids"),
            "contenuti_persi": compression.get("lost_required_unit_ids"),
            "nuovo_materiale": compression.get("added_material_unit_ids"),
            "riesame_successivo": compression.get("post_compression_recheck"),
            "esito": compression.get("status"),
        }))
    for item in _provenance_entries(s, "TRANSFORMATION"):
        records.append(_clean({
            "fase": "provenance della trasformazione",
            "natura": "trasformazione materialmente rilevante",
            "riferimento": item.get("id"),
            "oggetto": item.get("proposition"),
            "ragione": item.get("rationale"),
            "disposizione_finale": item.get("disposition"),
            "collocazione_nel_testo": item.get("artifact_locators"),
        }))
    for action in s.get("editorial_actions") or []:
        records.append(_clean({
            "fase": "intervento editoriale",
            "natura": action.get("kind") or action.get("type") or "azione editoriale",
            "oggetto": action.get("summary") or action.get("message") or action.get("action"),
            "ragione": action.get("rationale") or action.get("reason"),
            "esito": action.get("status"),
        }))
    final_review = s.get("final_review") or {}
    for evidence in final_review.get("evidence", []) or []:
        records.append(_clean({
            "fase": "review finale severa",
            "natura": "controllo conclusivo",
            "ragione": str(evidence.get("criterion", "")).replace("_", " ").lower(),
            "evidenza": evidence.get("rationale") or evidence.get("summary") or evidence.get("locator"),
            "esito": evidence.get("status"),
        }))
    for probe in final_review.get("consequence_probes", []) or []:
        records.append(_clean({
            "fase": "review finale severa",
            "natura": "prova delle conseguenze logiche",
            "proposizione": probe.get("proposition"),
            "conseguenza_esaminata": probe.get("downstream_effect"),
            "evidenza": probe.get("evidence_ref"),
            "esito": probe.get("status"),
        }))
    return {
        "titolo": "Transformation ledger — storia ragionata delle trasformazioni",
        "finalita": "Mostrare perche il testo e cambiato, quali significati sono stati preservati, quali problemi sono stati corretti e quali conseguenze sono state riesaminate.",
        "records": records,
    }


def build_editorial_artifact_views(state: Any) -> dict[str, dict[str, Any]]:
    return {
        "evidence_dossier": build_evidence_dossier(state),
        "source_register": build_source_register(state),
        "inference_register": build_inference_register(state),
        "transformation_ledger": build_transformation_ledger(state),
    }


def build_dashboard_inference_view(state: Any) -> dict[str, Any]:
    s = _payload(state)
    editorial = s.get("editorial_standard") or {}
    setup = s.get("setup") or {}
    accepted = setup.get("accepted", setup) if isinstance(setup, dict) else {}
    views = build_editorial_artifact_views(s)
    return _clean({
        "titolo": "Dossier inferenziale giuridico-umanistico-editoriale",
        "mandato": (s.get("request") or {}).get("summary") or (s.get("request") or {}).get("raw"),
        "cornice_editoriale": {
            "modalita": s.get("mode"),
            "genere_giuridico": editorial.get("document_type") or accepted.get("document_type"),
            "destinatari": editorial.get("audience") or accepted.get("audience"),
            "orientamento": editorial.get("mode_adjustments"),
            "principi_applicati": [str(k).replace("_", " ") for k, value in (editorial.get("rules") or {}).items() if value is True],
        },
        "evidence_dossier": views["evidence_dossier"],
        "source_register": views["source_register"],
        "inference_register": views["inference_register"],
        "transformation_ledger": views["transformation_ledger"],
    })


def semantic_projection_digest(state: Any, role: str) -> str:
    role = str(role)
    if role == "session_dashboard":
        value = build_dashboard_inference_view(state)
    else:
        views = build_editorial_artifact_views(state)
        if role not in views:
            raise ValueError(f"role {role} has no legal-humanistic semantic projection")
        value = views[role]
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
