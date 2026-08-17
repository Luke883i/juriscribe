from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import artifact_atlas_core as _base

PROFILE_ID = "JURISCRIBE_ARTIFACT_ATLAS_V1"
SCHEMA = "juriscribe-artifact-atlas/v1"
SENSITIVE_PUBLIC_KEYS = {
    "plagiarism_references", "sealed_candidate_fingerprints", "generation_governance",
    "exact_ngram_hashes", "shingle_hashes", "document_digest", "fingerprint_digest", "segment_digest",
    "candidate_fingerprint_digest", "resolved_path", "sha256", "path", "size_bytes", "readback",
}
MANDATORY_EPISTEMIC_ROLES = {
    "evidence_dossier", "source_register", "inference_register", "transformation_ledger", "artifact_evidence_traceability",
}
EMPTY_PUBLIC_VALUES = (None, "", [], {}, ())


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            token = str(key)
            if token in SENSITIVE_PUBLIC_KEYS or token.endswith("_digest"):
                continue
            cleaned = _scrub(item)
            if cleaned not in EMPTY_PUBLIC_VALUES:
                out[token] = cleaned
        return out
    if isinstance(value, list):
        return [cleaned for cleaned in (_scrub(item) for item in value) if cleaned not in EMPTY_PUBLIC_VALUES]
    return value


def _artifact_by_role(state: Any) -> dict[str, dict[str, Any]]:
    payload = state if isinstance(state, dict) else state.__dict__
    return {str(item.get("role") or ""): item for item in payload.get("artifacts") or [] if item.get("role")}


def _public_registration(artifact: dict[str, Any]) -> dict[str, Any]:
    return _scrub({
        "id": artifact.get("id"),
        "role": artifact.get("role"),
        "summary": artifact.get("summary"),
        "artifact_generation_governance": artifact.get("artifact_generation_governance"),
        "semantic_materialization": artifact.get("semantic_materialization"),
    })


def build_artifact_atlas(state: Any) -> dict[str, Any]:
    atlas = deepcopy(_base.build_artifact_atlas(state))
    payload = state if isinstance(state, dict) else state.__dict__
    by_role = _artifact_by_role(payload)
    for record in atlas.get("artefatti_materiali") or []:
        role = str(record.get("ruolo") or "")
        artifact = by_role.get(role) or {}
        detail = dict(record.get("descrizione_completa") or {})
        registration = _public_registration(artifact)
        if registration:
            detail["registrazione_artefatto"] = registration
        proof = artifact.get("artifact_generation_governance")
        if proof:
            detail["verifica_del_materializzato"] = _scrub(proof)
            status = str(proof.get("status") or "")
            record["sintesi_compressa"] = (str(record.get("sintesi_compressa") or "").rstrip() + f" Verifica del file materializzato: {status}.").strip()
        semantic_proof = artifact.get("semantic_materialization")
        if semantic_proof:
            detail["completezza_semantica_del_dossier"] = _scrub(semantic_proof)
            status = str(semantic_proof.get("status") or "")
            record["sintesi_compressa"] = (str(record.get("sintesi_compressa") or "").rstrip() + f" Materializzazione semantica del dossier: {status}.").strip()
        if detail:
            record["descrizione_completa"] = detail

    # The core atlas historically constructed a few optional records from wrapper
    # dictionaries such as {cycles: [], regenerations: []}. After public scrubbing
    # those records have no semantic content. Do not publish a false "active"
    # artifact card with an empty drill-down; mandatory canonical dossiers remain.
    epistemic_records = []
    for record in atlas.get("artefatti_epistemici") or []:
        cleaned = _scrub(record.get("descrizione_completa"))
        role = str(record.get("ruolo") or "")
        if cleaned in EMPTY_PUBLIC_VALUES and role not in MANDATORY_EPISTEMIC_ROLES:
            continue
        record["descrizione_completa"] = cleaned
        epistemic_records.append(record)
    atlas["artefatti_epistemici"] = epistemic_records

    limits = payload.get("limits") or []
    if limits:
        atlas.setdefault("artefatti_epistemici", []).append({
            "id": "epistemic:limits",
            "tipo": "ARTEFATTO_EPISTEMICO",
            "ruolo": "limits",
            "titolo": "Limiti e riserve",
            "funzione": "Rende espliciti limiti sostanziali, riserve e condizioni che incidono sull'affidabilità o sul perimetro del prodotto.",
            "stato": "REGISTRATO",
            "sintesi_compressa": f"{len(limits)} limite/i o riserva/e materialmente registrati.",
            "descrizione_completa": _scrub(limits),
            "richiamo_dashboard": "#epistemic-artifacts",
        })
    atlas["copertura"]["epistemici_descritti"] = len(atlas.get("artefatti_epistemici") or [])
    atlas["sintesi_compressa"] = [
        item if not str(item).startswith("Gli artefatti INTERNAL") else "Gli artefatti INTERNAL, i fingerprint e la telemetria tecnica sono esclusi; ogni contenuto giuridico, probatorio, inferenziale ed editoriale materialmente rilevante resta descritto."
        for item in atlas.get("sintesi_compressa") or []
    ]
    return atlas


def artifact_dashboard_coverage_gate(state: Any, atlas: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    view = atlas or build_artifact_atlas(state)
    _, errors = _base.artifact_dashboard_coverage_gate(state, view)
    payload = state if isinstance(state, dict) else state.__dict__
    if (payload.get("limits") or []) and not any(str(item.get("ruolo")) == "limits" for item in view.get("artefatti_epistemici") or []):
        errors.append("substantive limits are not represented in dashboard artifact atlas")
    by_role = _artifact_by_role(payload)
    atlas_by_role = {str(item.get("ruolo") or ""): item for item in view.get("artefatti_materiali") or [] if item.get("ruolo")}
    for role, artifact in by_role.items():
        if str(artifact.get("delivery_class") or "").upper() == "INTERNAL":
            continue
        atlas_record = atlas_by_role.get(role)
        if not atlas_record:
            errors.append(f"public material artifact is absent from dashboard atlas: {role}")
            continue
        summary = str(artifact.get("summary") or "").strip()
        if summary:
            registration = ((atlas_record.get("descrizione_completa") or {}).get("registrazione_artefatto") or {})
            if str(registration.get("summary") or "") != summary:
                errors.append(f"public artifact summary is not represented in dashboard atlas: {role}")
    return not errors, list(dict.fromkeys(errors))
