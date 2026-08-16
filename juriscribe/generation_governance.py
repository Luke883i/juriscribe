from __future__ import annotations

from typing import Any

from . import multimode as _multimode
from . import semantic_delivery as _semantic_delivery
from .continuation import derive_continuation_plan
from .evidence_traceability import evidence_traceability_gate
from .final_review import final_review_gate
from .generation import canonical_digest as generation_digest, text_digest
from .generation_configuration import (
    PROFILE_ID as CONFIG_PROFILE_ID,
    build_generation_configuration_contract,
    enrich_setup_proposal,
    format_generation_preview,
    generation_conformance,
)
from .interaction import interaction_card
from .modes import CONTINUATION, GREENFIELD, REVIEW, build_mode_contract, mode_spec, required_artifact_roles, review_output
from .plagiarism import (
    POLICY_ID as PLAGIARISM_POLICY_ID,
    audit_plagiarism,
    default_policy,
    fingerprint_evidence_passages,
    fingerprint_text,
    plagiarism_gate,
)
from .provenance import canonical_digest as provenance_digest, provenance_gate
from .saturation import build_predelivery_saturation, predelivery_saturation_gate

GOVERNANCE_PROFILE = "JURISCRIBE_GENERATION_GOVERNANCE_V1"


def _generated_stage(state, stage: str) -> bool:
    mode = str(getattr(state, "mode", "") or "").upper()
    if mode in {CONTINUATION, GREENFIELD}:
        return stage in {"INITIAL", "REGENERATED", "COMPRESSED_FINAL"}
    return mode == REVIEW and stage == "REVISED_FINAL" and review_output(state.setup) == "REPORT_AND_REVISED_TEXT"


def _attach_generation_governance(state) -> None:
    contract = dict(state.generation_contract or {})
    if contract.get("status") != "READY":
        return
    configuration = build_generation_configuration_contract(state.setup)
    if configuration.get("status") != "READY":
        raise ValueError("; ".join(configuration.get("errors") or ["generation configuration invalid"]))
    policy = default_policy()
    contract.update({
        "governance_profile": GOVERNANCE_PROFILE,
        "generation_configuration": configuration,
        "plagiarism_policy": policy,
    })
    contract.pop("contract_digest", None)
    contract["contract_digest"] = generation_digest(contract)
    state.generation_contract = contract
    mode = str(state.mode).upper()
    if mode == CONTINUATION:
        plan = derive_continuation_plan(contract, state.epistemic_units, state.relations)
        state.continuation = {
            **(state.continuation or {}),
            "plan": plan,
            "coverage": {},
            "status": "PLANNED" if plan.get("status") == "PASS" else "INVALID",
        }
    state.mode_contract = build_mode_contract(
        mode,
        request=state.request,
        corpus=state.corpus,
        reticulum=state.reticulum,
        setup=state.setup,
        editorial_standard=state.editorial_standard,
        generation_contract=state.generation_contract,
    )
    if state.mode_contract.get("status") != "READY":
        raise ValueError("; ".join(state.mode_contract.get("errors") or ["mode contract invalid after generation governance binding"]))


def ingest_and_mine(state, text, *, source_id, chapter=None, source_record=None, role=None):
    result = _multimode.ingest_and_mine(state, text, source_id=source_id, chapter=chapter, source_record=source_record, role=role)
    fingerprint = fingerprint_text(text, source_id=str(source_id), locator_prefix="P")
    for record in state.corpus:
        if record.get("source_id") == source_id:
            record["plagiarism_fingerprint"] = fingerprint
    return result


def register_semantic_mining(state, units: list[dict[str, Any]], relations: list[dict[str, Any]]):
    result = _multimode.register_semantic_mining(state, units, relations)
    if state.reticulum.get("status") == "PASS" and state.setup.get("status") == "USER_SETUP_REQUIRED":
        state.setup = enrich_setup_proposal(state.setup, request=state.request, units=state.epistemic_units, mining=state.mining)
        state.interaction = {
            **(state.interaction or {}),
            "card": interaction_card(
                "USER_SETUP_REQUIRED",
                headline="Configurazione di generazione",
                summary=format_generation_preview(state.setup),
                choices=["ACCETTA CONSIGLIATI", "MODIFICA", "ALTRO"],
                blocking=True,
            ),
            "status": "READY",
        }
    return result


def apply_setup(state, overrides=None):
    result = _multimode.apply_setup(state, overrides)
    configuration = build_generation_configuration_contract(state.setup)
    if configuration.get("status") != "READY":
        raise ValueError("; ".join(configuration.get("errors") or ["generation configuration invalid"]))
    state.setup["generation_configuration"] = configuration
    return result


def freeze_dods(state, additional_dods=None):
    result = _multimode.freeze_dods(state, additional_dods)
    if state.generation_contract.get("status") == "READY":
        _attach_generation_governance(state)
    return result


def seal_draft(state, text: str, *, stage: str = "INITIAL"):
    if _generated_stage(state, stage):
        configuration = (state.generation_contract or {}).get("generation_configuration")
        check = generation_conformance(text, configuration)
        if check.get("status") != "PASS":
            raise ValueError("generation configuration violation: " + "; ".join(check.get("errors") or []))
    record = _multimode.seal_draft(state, text, stage=stage)
    if isinstance(state.review, dict):
        state.review.pop("delivery_saturation", None)
    return record


def register_plagiarism_reference(state, *, source_id: str, text: str, locator_prefix: str = "R") -> dict[str, Any]:
    source_id = str(source_id or "").strip()
    if not source_id:
        raise ValueError("plagiarism reference source_id required")
    fingerprint = fingerprint_text(text, source_id=source_id, locator_prefix=locator_prefix)
    refs = [item for item in (state.source_intelligence.get("plagiarism_references") or []) if item.get("source_id") != source_id]
    refs.append(fingerprint)
    state.source_intelligence["plagiarism_references"] = refs
    state.source_intelligence["plagiarism_reference_status"] = "REGISTERED"
    return fingerprint


def _plagiarism_references(state, *, reference_text=None, prior_texts=None) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    references.extend(fingerprint_evidence_passages(state.claim_ledger))
    references.extend(dict(item) for item in (state.source_intelligence.get("plagiarism_references") or []))
    for record in state.corpus:
        fp = record.get("plagiarism_fingerprint")
        if fp:
            references.append(dict(fp))
    if reference_text:
        references.append(fingerprint_text(reference_text, source_id="REFERENCE_STYLE", locator_prefix="S"))
    for index, text in enumerate(prior_texts or [], 1):
        references.append(fingerprint_text(text, source_id=f"PRIOR_TEXT_{index}", locator_prefix="P"))
    return references


def _required_plagiarism_sources(state) -> set[str]:
    required = {str(item.get("source_id")) for item in state.corpus if item.get("source_id")}
    for claim in state.claim_ledger:
        if not bool(claim.get("material", True)):
            continue
        required.update(str(source_id) for source_id in claim.get("support_source_ids") or [] if str(source_id))
    return required


def audit_legal_text(
    state,
    text,
    *,
    reference_text=None,
    prior_texts=None,
    artifact_evidence=None,
    authorized_reuse=None,
):
    report = _multimode.audit_legal_text(
        state,
        text,
        reference_text=reference_text,
        prior_texts=prior_texts,
        artifact_evidence=artifact_evidence,
    )
    current_stage = str(state.drafts[-1].get("stage") or "") if state.drafts else ""
    generated = _generated_stage(state, current_stage)
    if generated:
        configuration = generation_conformance(text, (state.generation_contract or {}).get("generation_configuration"))
        configuration["sealed_candidate_digest"] = text_digest(text)
        configuration["digest"] = generation_digest({k: v for k, v in configuration.items() if k != "digest"})
        plagiarism = audit_plagiarism(
            text,
            references=_plagiarism_references(state, reference_text=reference_text, prior_texts=prior_texts),
            required_source_ids=_required_plagiarism_sources(state),
            authorized_reuse=authorized_reuse,
            sealed_candidate_digest=text_digest(text),
        )
    else:
        configuration = {"status": "NOT_APPLICABLE", "profile": CONFIG_PROFILE_ID, "sealed_candidate_digest": text_digest(text)}
        plagiarism = {"status": "NOT_APPLICABLE", "policy_id": PLAGIARISM_POLICY_ID, "sealed_candidate_digest": text_digest(text)}
    state.quality["generation_configuration"] = configuration
    state.quality["plagiarism"] = plagiarism
    if generated and (configuration.get("status") != "PASS" or plagiarism.get("status") != "PASS"):
        state.quality["status"] = "FAIL"
        blockers = list(state.quality.get("blocking_failures") or [])
        if configuration.get("status") != "PASS":
            blockers.append("accepted generation configuration is not satisfied")
        if plagiarism.get("status") != "PASS":
            blockers.append("anti-plagiarism proof is not established")
        state.quality["blocking_failures"] = list(dict.fromkeys(blockers))
    if isinstance(state.review, dict):
        state.review.pop("delivery_saturation", None)
    return state.quality


def audit_candidate_chapter(state, text, *, reference_text=None, prior_texts=None, artifact_evidence=None, authorized_reuse=None):
    return audit_legal_text(
        state,
        text,
        reference_text=reference_text,
        prior_texts=prior_texts,
        artifact_evidence=artifact_evidence,
        authorized_reuse=authorized_reuse,
    )


def record_provenance(state, payload):
    result = _multimode.record_provenance(state, payload)
    if isinstance(state.review, dict):
        state.review.pop("delivery_saturation", None)
    return result


def record_final_review(state, payload):
    result = _multimode.record_final_review(state, payload)
    if isinstance(state.review, dict):
        state.review.pop("delivery_saturation", None)
    return result


def record_artifact(state, record):
    result = _semantic_delivery.record_artifact(state, record)
    if isinstance(state.review, dict):
        state.review.pop("delivery_saturation", None)
    return result


def _artifact_gate(state) -> tuple[bool, list[str]]:
    by_role = {str(item.get("role") or ""): item for item in state.artifacts if item.get("role")}
    errors: list[str] = []
    for role in sorted(required_artifact_roles(state.mode, state.setup)):
        item = by_role.get(role)
        if not item:
            errors.append(f"required artifact missing during predelivery saturation: {role}")
        elif item.get("readback") != "PASS":
            errors.append(f"required artifact readback not PASS during predelivery saturation: {role}")
    return not errors, errors


def _configuration_gate(state, current_digest: str) -> tuple[bool, list[str]]:
    if not state.generation_contract or state.generation_contract.get("status") != "READY":
        return True, []
    record = (state.quality or {}).get("generation_configuration") or {}
    errors = []
    if record.get("status") != "PASS":
        errors.append("generation configuration conformance is not PASS")
    if record.get("sealed_candidate_digest") != current_digest:
        errors.append("generation configuration conformance bound to stale candidate")
    expected = ((state.generation_contract or {}).get("generation_configuration") or {}).get("digest")
    if expected and record.get("configuration_digest") != expected:
        errors.append("generation configuration conformance bound to stale configuration")
    return not errors, errors


def _plagiarism_gate(state, current_digest: str) -> tuple[bool, list[str]]:
    if not state.generation_contract or state.generation_contract.get("status") != "READY":
        return True, []
    policy = (state.generation_contract or {}).get("plagiarism_policy") or default_policy()
    return plagiarism_gate((state.quality or {}).get("plagiarism"), sealed_candidate_digest=current_digest, policy_digest=policy.get("digest"))


def _quality_gate(state, current_digest: str) -> tuple[bool, list[str]]:
    errors = []
    spec = mode_spec(state.mode, state.setup)
    if spec.get("quality_must_pass") and state.quality.get("status") != "PASS":
        errors.append("quality audit is not PASS")
    if state.quality.get("candidate_digest") != current_digest:
        errors.append("quality audit bound to stale candidate")
    return not errors, errors


def _source_gate(state) -> tuple[bool, list[str]]:
    status = state.source_intelligence.get("coverage_status")
    if status in {"PASS", "NOT_REQUIRED"}:
        return True, []
    mode = mode_spec(state.mode, state.setup)
    if not mode.get("source_coverage_must_close"):
        return True, []
    return False, ["claim/source coverage is not closed"]


def _provenance_gate(state, current_digest: str) -> tuple[bool, list[str]]:
    corpus_digest = provenance_digest(state.corpus)
    return provenance_gate(state.provenance, candidate_digest=current_digest or None, corpus_digest=corpus_digest)


def _final_review_gate(state, current_digest: str) -> tuple[bool, list[str]]:
    corpus_digest = provenance_digest(state.corpus)
    normative = provenance_digest({
        "sources": state.sources,
        "claims": state.claim_ledger,
        "source_intelligence": state.source_intelligence,
        "contradictions": state.contradictions,
    })
    return final_review_gate(
        state.final_review,
        candidate_digest=current_digest or None,
        corpus_digest=corpus_digest,
        provenance_digest=(state.provenance or {}).get("digest"),
        normative_frame_digest=normative,
    )


def _gate_vector(state, current_digest: str) -> dict[str, Any]:
    semantic_ok, semantic_errors = _semantic_delivery.semantic_dossier_gate(state)
    evidence_ok, evidence_errors = evidence_traceability_gate(state)
    return {
        "generation_configuration": _configuration_gate(state, current_digest),
        "anti_plagiarism": _plagiarism_gate(state, current_digest),
        "quality": _quality_gate(state, current_digest),
        "source_claim_coverage": _source_gate(state),
        "provenance": _provenance_gate(state, current_digest),
        "final_severe_review": _final_review_gate(state, current_digest),
        "semantic_dossier_freshness": (semantic_ok, semantic_errors),
        "evidence_traceability": (evidence_ok, evidence_errors),
        "artifact_materialization_readback": _artifact_gate(state),
    }


def evaluate_completion(state):
    _semantic_delivery.evaluate_completion(state)
    current_digest = str(state.drafts[-1].get("digest") or "") if state.drafts else ""
    contract_digest = str((state.generation_contract or {}).get("contract_digest") or "")
    saturation = build_predelivery_saturation(
        candidate_digest=current_digest,
        generation_contract_digest=contract_digest,
        gate_results=_gate_vector(state, current_digest),
    )
    state.review["delivery_saturation"] = saturation
    sat_ok, sat_errors = predelivery_saturation_gate(
        saturation,
        candidate_digest=current_digest,
        generation_contract_digest=contract_digest,
    )
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
                summary="Il fixed point pre-consegna non è raggiunto: rigenerare o riallineare i blocker e rieseguire i controlli.",
                blocking=True,
            ),
            "status": "READY",
        }
    return state
