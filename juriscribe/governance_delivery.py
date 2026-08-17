from __future__ import annotations

from . import generation_governance as _base
from .artifact_atlas import artifact_dashboard_coverage_gate
from .artifact_governance import artifact_generation_governance_gate
from .chat_delivery import chat_docx_delivery_gate
from .interaction import interaction_card
from .saturation import build_predelivery_saturation, predelivery_saturation_gate


def evaluate_completion(state):
    """Final delivery boundary: evidence, artifacts and chat-tail DOCX delivery must converge."""
    _base._semantic_delivery.evaluate_completion(state)
    current_digest = str(state.drafts[-1].get("digest") or "") if state.drafts else ""
    contract_digest = str((state.generation_contract or {}).get("contract_digest") or "")
    gate_results = _base._gate_vector(state, current_digest)
    atlas_ok, atlas_errors = artifact_dashboard_coverage_gate(state)
    artifact_gov_ok, artifact_gov_errors = artifact_generation_governance_gate(state)
    chat_ok, chat_errors = chat_docx_delivery_gate(state)
    gate_results["dashboard_artifact_completeness"] = (atlas_ok, atlas_errors)
    gate_results["materialized_narrative_governance"] = (artifact_gov_ok, artifact_gov_errors)
    gate_results["chat_tail_docx_delivery"] = (chat_ok, chat_errors)
    saturation = build_predelivery_saturation(
        candidate_digest=current_digest,
        generation_contract_digest=contract_digest,
        gate_results=gate_results,
    )
    state.review["delivery_saturation"] = saturation
    sat_ok, sat_errors = predelivery_saturation_gate(
        saturation,
        candidate_digest=current_digest,
        generation_contract_digest=contract_digest,
    )
    state.completion["artifact_dashboard_coverage_gate"] = {"eligible": atlas_ok, "errors": atlas_errors}
    state.completion["artifact_generation_governance_gate"] = {"eligible": artifact_gov_ok, "errors": artifact_gov_errors}
    state.completion["chat_docx_delivery_gate"] = {"eligible": chat_ok, "errors": chat_errors}
    state.completion["predelivery_saturation_gate"] = {"eligible": sat_ok, "errors": sat_errors}
    if not sat_ok:
        state.completion["eligible"] = False
        existing = str(state.completion.get("reason") or "")
        extra = "; ".join(sat_errors)
        state.completion["reason"] = (existing + "; " + extra).strip("; ")
        state.phase = "VALIDATING"
        state.interaction = {
            **(state.interaction or {}),
            "card": interaction_card(
                "HUMAN_DECISION_REQUIRED",
                headline="Saturazione pre-consegna incompleta",
                summary="Configurazione, originalità, contenuto materializzato, controlli scientifici, copertura degli artefatti e allegati DOCX in coda chat devono convergere allo stesso fixed point prima della consegna.",
                blocking=True,
            ),
            "status": "READY",
        }
    return state
