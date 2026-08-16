from __future__ import annotations

from . import delivery as _delivery
from .editorial_artifacts import DOSSIER_ROLES, PROFILE_ID, semantic_projection_digest
from .evidence_traceability import evidence_traceability_gate
from .interaction import interaction_card


def _semantic_record(state, record):
    normalized = dict(record)
    role = str(normalized.get("role", ""))
    if role in DOSSIER_ROLES:
        current = semantic_projection_digest(state, role)
        stored = str(normalized.get("semantic_projection_digest", "")).strip()
        if stored and stored != current:
            raise ValueError(f"semantic projection for {role} is stale before artifact registration")
        normalized["semantic_profile"] = PROFILE_ID
        normalized["semantic_projection_digest"] = current
    return normalized


def record_artifact(state, record):
    """Attach the current humanistic/editorial projection to final dossier records."""
    return _delivery.record_artifact(state, _semantic_record(state, record))


def semantic_dossier_gate(state):
    """Fail closed on semantic drift for dossiers registered by v0.9.4+."""
    by_role = {str(item.get("role", "")): item for item in state.artifacts if item.get("role")}
    errors = []
    for role in DOSSIER_ROLES:
        record = by_role.get(role)
        if not record:
            continue
        stored = str(record.get("semantic_projection_digest", "")).strip()
        if not stored:
            continue
        current = semantic_projection_digest(state, role)
        if stored != current:
            errors.append(f"{role} is stale relative to the current legal-humanistic editorial projection")
    return not errors, errors


def evaluate_completion(state):
    _delivery.evaluate_completion(state)
    dossier_ok, dossier_errors = semantic_dossier_gate(state)
    evidence_ok, evidence_errors = evidence_traceability_gate(state)
    state.completion["semantic_dossier_gate"] = {"eligible": dossier_ok, "errors": dossier_errors}
    state.completion["evidence_traceability_gate"] = {"eligible": evidence_ok, "errors": evidence_errors}
    errors = dossier_errors + evidence_errors
    if errors:
        state.completion["eligible"] = False
        existing = str(state.completion.get("reason", ""))
        extra = "; ".join(errors)
        state.completion["reason"] = (existing + "; " + extra).strip("; ")
        state.phase = "VALIDATING"
        state.interaction = {
            **(state.interaction or {}),
            "card": interaction_card(
                "HUMAN_DECISION_REQUIRED",
                summary="I dossier o la tracciabilita delle evidenze devono essere riallineati. Consulta la dashboard.",
            ),
            "status": "READY",
        }
    return state
