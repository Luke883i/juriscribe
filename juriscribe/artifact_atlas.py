from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import artifact_atlas as _base

PROFILE_ID = "JURISCRIBE_ARTIFACT_ATLAS_V1"
SCHEMA = "juriscribe-artifact-atlas/v1"
SENSITIVE_PUBLIC_KEYS = {
    "plagiarism_references", "sealed_candidate_fingerprints", "generation_governance",
    "exact_ngram_hashes", "shingle_hashes", "document_digest", "fingerprint_digest", "segment_digest",
    "candidate_fingerprint_digest", "resolved_path", "sha256", "path", "size_bytes", "readback",
}


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            token = str(key)
            if token in SENSITIVE_PUBLIC_KEYS or token.endswith("_digest"):
                continue
            cleaned = _scrub(item)
            if cleaned not in (None, "", [], {}, ()):
                out[token] = cleaned
        return out
    if isinstance(value, list):
        return [cleaned for cleaned in (_scrub(item) for item in value) if cleaned not in (None, "", [], {}, ())]
    return value


def _artifact_by_role(state: Any) -> dict[str, dict[str, Any]]:
    payload = state if isinstance(state, dict) else state.__dict__
    return {str(item.get("role") or ""): item for item in payload.get("artifacts") or [] if item.get("role")}


def build_artifact_atlas(state: Any) -> dict[str, Any]:
    atlas = deepcopy(_base.build_artifact_atlas(state))
    payload = state if isinstance(state, dict) else state.__dict__
    by_role = _artifact_by_role(payload)
    for record in atlas.get("artefatti_materiali") or []:
        role = str(record.get("ruolo") or "")
        artifact = by_role.get(role) or {}
        proof = artifact.get("artifact_generation_governance")
        if proof:
            detail = dict(record.get("descrizione_completa") or {})
            detail["verifica_del_materializzato"] = _scrub(proof)
            record["descrizione_completa"] = detail
            status = str(proof.get("status") or "")
            record["sintesi_compressa"] = (str(record.get("sintesi_compressa") or "").rstrip() + f" Verifica del file materializzato: {status}.").strip()
    for record in atlas.get("artefatti_epistemici") or []:
        record["descrizione_completa"] = _scrub(record.get("descrizione_completa"))
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
    ok, errors = _base.artifact_dashboard_coverage_gate(state, view)
    payload = state if isinstance(state, dict) else state.__dict__
    if (payload.get("limits") or []) and not any(str(item.get("ruolo")) == "limits" for item in view.get("artefatti_epistemici") or []):
        errors.append("substantive limits are not represented in dashboard artifact atlas")
    return not errors, list(dict.fromkeys(errors))
