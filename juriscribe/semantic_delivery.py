from __future__ import annotations

from . import delivery as _delivery
from .dossier_materialization import PROFILE as MATERIALIZATION_PROFILE, dossier_semantic_materialization_gate, verify_dossier_semantic_materialization
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


def _has_runtime_workspace(state) -> bool:
    runtime = state.get("runtime", {}) if isinstance(state, dict) else getattr(state, "runtime", {})
    return bool(str((runtime or {}).get("workspace_base") or "").strip())


def record_artifact(state, record):
    """Bind runtime-materialized canonical dossier files to the projection used by the dashboard.

    Pure in-memory semantic sealing remains available for compatibility and unit-level
    projection tests; any real initialized runtime session has workspace_base and must
    pass the content materialization proof before a new canonical dossier is registered.
    """
    prepared = _semantic_record(state, record)
    role = str(prepared.get("role", ""))
    if role in DOSSIER_ROLES and _has_runtime_workspace(state):
        normalized = _delivery.normalize_artifact_record(state, prepared)
        proof = verify_dossier_semantic_materialization(state, normalized)
        if proof.get("status") != "PASS":
            raise ValueError("canonical dossier semantic materialization failed: " + "; ".join(proof.get("errors") or []))
        prepared["semantic_materialization_profile"] = MATERIALIZATION_PROFILE
        prepared["semantic_materialization"] = proof
    return _delivery.record_artifact(state, prepared)


def semantic_dossier_gate(state):
    """Fail closed on semantic drift or dossier-file semantic incompleteness."""
    by_role = {str(item.get("role", "")): item for item in state.artifacts if item.get("role")}
    errors = []
    for role in DOSSIER_ROLES:
        record = by_role.get(role)
        if not record:
            continue
        stored = str(record.get("semantic_projection_digest", "")).strip()
        if stored:
            current = semantic_projection_digest(state, role)
            if stored != current:
                errors.append(f"{role} is stale relative to the current legal-humanistic editorial projection")
    materialized_ok, materialized_errors = dossier_semantic_materialization_gate(state)
    if not materialized_ok:
        errors.extend(materialized_errors)
    return not errors, list(dict.fromkeys(errors))


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
