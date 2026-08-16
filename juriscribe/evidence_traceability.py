from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .modes import required_artifact_roles

PROFILE_ID = "JURISCRIBE_EVIDENCE_TRACEABILITY_V1"
SCHEMA = "juriscribe-evidence-traceability/v1"
DOSSIER_ROLES = ("evidence_dossier", "source_register", "inference_register", "transformation_ledger")
ROLE_LABELS = {
    "final_chapter": "Capitolo finale",
    "final_legal_text": "Testo giuridico finale",
    "review_report": "Relazione di revisione",
    "review_findings_register": "Registro dei rilievi",
    "revised_legal_text": "Testo giuridico revisionato",
    "evidence_dossier": "Evidence dossier",
    "source_register": "Source register",
    "inference_register": "Inference register",
    "transformation_ledger": "Transformation ledger",
}
ROLE_PURPOSES = {
    "final_chapter": "testo finale generato in continuita con il corpus precedente",
    "final_legal_text": "testo giuridico finale generato ex novo",
    "review_report": "esito argomentato della revisione scientifico-editoriale",
    "review_findings_register": "rilievi, severita, azioni e stato della revisione",
    "revised_legal_text": "testo revisionato risultante dalla review",
    "evidence_dossier": "architettura probatoria delle proposizioni materiali",
    "source_register": "geografia, autorita e uso effettivo delle fonti",
    "inference_register": "premesse, ponti, falsificatori e conclusioni inferenziali",
    "transformation_ledger": "storia causale delle trasformazioni editoriali",
}
ROLE_ANCHORS = {
    "evidence_dossier": "#evidence-dossier",
    "source_register": "#source-register",
    "inference_register": "#inference-register",
    "transformation_ledger": "#transformation-ledger",
}
KNOWN_EVIDENCE_FIELDS = {
    "evidence_id", "claim_id", "artifact_locator", "source_ids", "pinpoints", "status",
    "artifact_id", "artifact_role", "evidence_kind",
}


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            item = _clean(item)
            if item not in (None, "", [], {}, ()): out[str(key)] = item
        return out
    if isinstance(value, (list, tuple, set)):
        out = [_clean(item) for item in value]
        return [item for item in out if item not in (None, "", [], {}, ())]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _evidence_id(record: dict[str, Any]) -> str:
    explicit = str(record.get("evidence_id", "")).strip()
    if explicit:
        return explicit
    digest = hashlib.sha256(_canonical(record).encode("utf-8")).hexdigest()[:16]
    return f"EVID-{digest}"


def _lookups(state: dict[str, Any]):
    claims = {str(item.get("id")): item for item in state.get("claim_ledger") or [] if item.get("id")}
    units = {str(item.get("id")): item for item in state.get("epistemic_units") or [] if item.get("id")}
    provenance = {str(item.get("id")): item for item in (state.get("provenance") or {}).get("entries", []) or [] if item.get("id")}
    sources = {str(item.get("id")): item for item in state.get("sources") or [] if item.get("id")}
    artifacts = [dict(item) for item in state.get("artifacts") or []]
    return claims, units, provenance, sources, artifacts


def _claim_text(reference: str, claims, units, provenance) -> str | None:
    return (
        (claims.get(reference) or {}).get("text")
        or (units.get(reference) or {}).get("text")
        or (provenance.get(reference) or {}).get("proposition")
    )


def _source_rows(source_ids: list[str], sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for source_id in source_ids:
        source = sources.get(source_id, {})
        rows.append(_clean({
            "riferimento_fonte": source_id,
            "fonte": source.get("title") or source_id,
            "autore_o_organo": source.get("court_or_author"),
            "giurisdizione": source.get("jurisdiction"),
            "data": source.get("date"),
        }))
    return rows


def _expected_roles(state: dict[str, Any]) -> set[str]:
    mode = str(state.get("mode") or "").strip()
    if not mode:
        return set()
    try:
        return set(required_artifact_roles(mode, state.get("setup") or {})) - {"session_dashboard"}
    except ValueError:
        return set()


def _relative_artifact_href(state: dict[str, Any], record: dict[str, Any]) -> str | None:
    raw_path = str(record.get("path", "")).strip()
    workspace = str((state.get("runtime") or {}).get("workspace_base", "")).strip()
    if not raw_path or not workspace:
        return None
    root = (Path(workspace) / "artifacts").resolve(strict=False)
    raw = Path(raw_path)
    absolute = raw if raw.is_absolute() else (Path.cwd() / raw)
    resolved = absolute.resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    return "./" + quote(relative.as_posix(), safe="/._-@")


def build_user_artifact_index(state: Any) -> dict[str, Any]:
    s = _payload(state)
    expected = _expected_roles(s)
    _, _, _, _, artifacts = _lookups(s)
    actual_by_role = {str(item.get("role")): item for item in artifacts if str(item.get("role", "")) in expected}
    records = []
    for role in sorted(expected, key=lambda item: (list(ROLE_LABELS).index(item) if item in ROLE_LABELS else 999, item)):
        artifact = actual_by_role.get(role)
        available = bool(artifact and artifact.get("path") and artifact.get("readback") == "PASS")
        records.append(_clean({
            "riferimento_artefatto": (artifact or {}).get("id") or role,
            "ruolo": role,
            "titolo": ROLE_LABELS.get(role, role.replace("_", " ").title()),
            "funzione": ROLE_PURPOSES.get(role, "artefatto finale della sessione"),
            "stato": "DISPONIBILE" if available else ("REGISTRATO" if artifact else "ATTESO"),
            "contenuto_nella_dashboard": "INTEGRALE" if role in DOSSIER_ROLES else "RICHIAMATO TRAMITE ARTEFATTO",
            "richiamo": _relative_artifact_href(s, artifact) if artifact else None,
            "ancora_dashboard": ROLE_ANCHORS.get(role),
        }))
    return {
        "titolo": "Indice degli artefatti — richiamo della consegna",
        "finalita": "Rendere immediatamente raggiungibili gli artefatti finali senza esporre percorsi, digest o telemetria tecnica.",
        "records": records,
    }


def build_evidence_traceability(state: Any) -> dict[str, Any]:
    s = _payload(state)
    claims, units, provenance, sources, artifacts = _lookups(s)
    raw_records = [dict(item) for item in s.get("artifact_evidence") or []]
    artifact_by_id = {str(item.get("id")): item for item in artifacts if item.get("id")}
    artifact_by_role = {str(item.get("role")): item for item in artifacts if item.get("role")}
    records = []
    missing_claims: set[str] = set()
    missing_sources: set[str] = set()
    missing_artifacts: set[str] = set()
    missing_locators: list[str] = []
    evidence_ids: list[str] = []

    for raw in raw_records:
        evidence_id = _evidence_id(raw)
        evidence_ids.append(evidence_id)
        claim_id = str(raw.get("claim_id", "")).strip()
        locator = str(raw.get("artifact_locator", "")).strip()
        source_ids = [str(item) for item in raw.get("source_ids", []) or []]
        artifact_id = str(raw.get("artifact_id", "")).strip()
        artifact_role = str(raw.get("artifact_role", "")).strip()
        if claim_id and not _claim_text(claim_id, claims, units, provenance):
            missing_claims.add(claim_id)
        if not locator:
            missing_locators.append(evidence_id)
        for source_id in source_ids:
            if source_id not in sources:
                missing_sources.add(source_id)
        if artifact_id and artifact_id not in artifact_by_id:
            missing_artifacts.add(artifact_id)
        if artifact_role and artifact_role not in artifact_by_role:
            missing_artifacts.add(artifact_role)
        target = artifact_by_id.get(artifact_id) if artifact_id else artifact_by_role.get(artifact_role)
        extras = {key: value for key, value in raw.items() if key not in KNOWN_EVIDENCE_FIELDS}
        records.append(_clean({
            "riferimento_evidenza": evidence_id,
            "tipo_evidenza": raw.get("evidence_kind") or "collocazione probatoria nel prodotto",
            "claim_id": claim_id,
            "proposizione": _claim_text(claim_id, claims, units, provenance),
            "collocazione_nell_artefatto": locator,
            "fonti_richiamate": _source_rows(source_ids, sources),
            "pinpoint_registrati": list(raw.get("pinpoints", []) or []),
            "stato": raw.get("status"),
            "artefatto_dichiarato": {
                "riferimento": artifact_id or None,
                "ruolo": artifact_role or None,
                "titolo": ROLE_LABELS.get(artifact_role) if artifact_role else None,
                "richiamo": _relative_artifact_href(s, target) if target else None,
            } if artifact_id or artifact_role else None,
            "attributi_ulteriori": extras,
        }))

    duplicates = sorted(item for item, count in Counter(evidence_ids).items() if count > 1)
    complete = not (missing_claims or missing_sources or missing_artifacts or missing_locators or duplicates)
    coverage = {
        "evidenze_registrate": len(raw_records),
        "evidenze_proiettate": len(records),
        "riferimenti_claim_non_risolti": sorted(missing_claims),
        "riferimenti_fonte_non_risolti": sorted(missing_sources),
        "riferimenti_artefatto_non_risolti": sorted(missing_artifacts),
        "evidenze_senza_collocazione": missing_locators,
        "identificativi_evidenza_duplicati": duplicates,
        "stato": "COMPLETA" if complete and len(raw_records) == len(records) else "DA_COMPLETARE",
    }
    return {
        "schema": SCHEMA,
        "profilo": PROFILE_ID,
        "titolo": "Registro di tracciabilita delle evidenze di artefatto",
        "finalita": "Mostrare senza perdita ogni evidenza che collega una proposizione, le sue fonti e i pinpoint alla collocazione dichiarata nel prodotto.",
        "copertura": coverage,
        "records": records,
    }


def build_dashboard_evidence_coverage(state: Any, dossier_views: dict[str, Any] | None = None) -> dict[str, Any]:
    s = _payload(state)
    traceability = build_evidence_traceability(s)
    artifacts = build_user_artifact_index(s)
    dossier_views = dossier_views or {}
    dossier_counts = {
        role: len(((dossier_views.get(role) or {}).get("records") or []))
        for role in DOSSIER_ROLES
    }
    available = sum(1 for item in artifacts["records"] if item.get("stato") == "DISPONIBILE")
    expected = len(artifacts["records"])
    raw_evidence = traceability["copertura"]["evidenze_registrate"]
    projected = traceability["copertura"]["evidenze_proiettate"]
    gaps = sum(len(traceability["copertura"][key]) for key in (
        "riferimenti_claim_non_risolti", "riferimenti_fonte_non_risolti",
        "riferimenti_artefatto_non_risolti", "evidenze_senza_collocazione",
        "identificativi_evidenza_duplicati",
    ))
    status = "PRONTO" if bool((s.get("completion") or {}).get("eligible")) else "NON PRONTO"
    summary = [
        f"{dossier_counts['evidence_dossier']} elementi probatori, {dossier_counts['source_register']} fonti, {dossier_counts['inference_register']} inferenze e {dossier_counts['transformation_ledger']} trasformazioni sono esposte integralmente nei quattro dossier canonici.",
        f"{projected}/{raw_evidence} evidenze di artefatto sono proiettate senza omissioni; {available}/{expected} artefatti finali attesi sono richiamabili dalla dashboard.",
    ]
    if gaps:
        summary.append(f"La tracciabilita presenta {gaps} riferimento/i da completare; il dettaglio e riportato nel registro delle evidenze.")
    elif raw_evidence:
        summary.append("I riferimenti di evidenza registrati risultano risolti rispetto a claim, fonti e artefatti esplicitamente dichiarati.")
    return {
        "esito_complessivo": {
            "titolo": "Esito complessivo — quadro compresso e completo",
            "stato": status,
            "sintesi_compressa": summary,
            "conteggi_dossier": dossier_counts,
            "copertura_evidenziale": traceability["copertura"],
            "artefatti_attesi": expected,
            "artefatti_richiamabili": available,
        },
        "artifact_index": artifacts,
        "evidence_traceability": traceability,
    }


def evidence_traceability_gate(state: Any) -> tuple[bool, list[str]]:
    view = build_evidence_traceability(state)
    coverage = view["copertura"]
    errors: list[str] = []
    if coverage["evidenze_registrate"] != coverage["evidenze_proiettate"]:
        errors.append("artifact evidence projection is not lossless")
    for key, label in (
        ("riferimenti_claim_non_risolti", "unresolved artifact-evidence claim reference"),
        ("riferimenti_fonte_non_risolti", "unresolved artifact-evidence source reference"),
        ("riferimenti_artefatto_non_risolti", "unresolved explicit artifact reference"),
        ("evidenze_senza_collocazione", "artifact evidence without locator"),
        ("identificativi_evidenza_duplicati", "duplicate artifact-evidence identity"),
    ):
        if coverage[key]:
            errors.append(f"{label}: {', '.join(coverage[key])}")
    return not errors, errors
