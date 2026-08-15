from __future__ import annotations

from .convergence import completion_gate
from .final_review import build_final_review, final_review_gate
from .interaction import interaction_card
from .orchestrator_base import record_artifact as _record_artifact
from .orchestrator_base import record_compression as _record_compression
from .orchestrator_base import seal_draft as _seal_draft
from .provenance import (
    REQUIRED_FINAL_ARTIFACT_ROLES,
    build_provenance_bundle,
    canonical_digest as provenance_digest,
    provenance_gate,
)


def _normative_frame_digest(state):
    return provenance_digest({
        "sources": state.sources,
        "claims": state.claim_ledger,
        "source_intelligence": state.source_intelligence,
        "contradictions": state.contradictions,
    })


def seal_draft(state, text: str, *, stage: str = "INITIAL"):
    record = _seal_draft(state, text, stage=stage)
    state.provenance = {}
    state.final_review = {}
    return record


def record_compression(state, record):
    result = _record_compression(state, record)
    state.provenance = {}
    state.final_review = {}
    return result


def record_provenance(state, payload):
    if not state.drafts or state.drafts[-1].get("stage") != "COMPRESSED_FINAL":
        raise ValueError("provenance requires sealed COMPRESSED_FINAL candidate")
    current_digest = str(state.drafts[-1].get("digest", ""))
    if state.quality.get("status") != "PASS" or state.quality.get("candidate_digest") != current_digest:
        raise ValueError("final quality PASS bound to current candidate required before provenance")
    if state.source_intelligence.get("coverage_status") not in {"PASS", "NOT_REQUIRED"}:
        raise ValueError("claim/source coverage must be closed before provenance")
    coverage = (state.continuation or {}).get("coverage") or {}
    if coverage.get("status") != "PASS" or coverage.get("candidate_digest") != current_digest:
        raise ValueError("final continuation coverage PASS required before provenance")
    bundle = build_provenance_bundle(
        payload.get("entries", []),
        candidate_digest=current_digest,
        corpus_digest=provenance_digest(state.corpus),
        epistemic_units=state.epistemic_units,
        claim_ledger=state.claim_ledger,
        interaction=state.interaction,
        regenerations=state.review.get("regenerations", []),
        compression=state.compression,
    )
    ok, errors = provenance_gate(
        bundle,
        candidate_digest=current_digest,
        corpus_digest=provenance_digest(state.corpus),
    )
    if not ok:
        raise ValueError("; ".join(errors))
    state.provenance = bundle
    state.final_review = {}
    state.phase = "PROVENANCE_COMPLETE"
    return bundle


def record_final_review(state, payload):
    if not state.provenance or state.provenance.get("status") != "PASS":
        raise ValueError("lossless provenance PASS required before final severe review")
    if not state.drafts:
        raise ValueError("final severe review requires sealed candidate")
    current_digest = str(state.drafts[-1].get("digest", ""))
    corpus_digest = provenance_digest(state.corpus)
    normative_digest = _normative_frame_digest(state)
    record = build_final_review(
        candidate_digest=current_digest,
        corpus_digest=corpus_digest,
        normative_frame_digest=normative_digest,
        provenance_digest=state.provenance.get("digest", ""),
        evidence=payload.get("evidence", []),
        consequence_probes=payload.get("consequence_probes", []),
        findings=payload.get("findings", []),
    )
    ok, errors = final_review_gate(
        record,
        candidate_digest=current_digest,
        corpus_digest=corpus_digest,
        provenance_digest=state.provenance.get("digest", ""),
        normative_frame_digest=normative_digest,
    )
    if not ok:
        raise ValueError("; ".join(errors))
    state.final_review = record
    state.phase = "FINAL_SEVERE_REVIEW_PASS"
    return record


def record_artifact(state, record):
    role = record.get("role")
    if role in REQUIRED_FINAL_ARTIFACT_ROLES - {"session_dashboard"}:
        if state.final_review.get("status") != "PASS":
            raise ValueError("final severe review PASS required before final artifact materialization")
    return _record_artifact(state, record)


def evaluate_completion(state):
    benchmark_required = any(
        d.get("kind") == "MONOGRAPHIC_EXTRAPOLATION" and d.get("blocking", True)
        for d in state.dod
    )
    state.completion = completion_gate(
        state.dod,
        state.metrics,
        state.contradictions,
        quality=state.quality or None,
        source_coverage=state.source_intelligence.get("coverage_status"),
        benchmark=state.benchmark or None,
        benchmark_required=benchmark_required,
        artifacts=state.artifacts,
        generation_required=True,
        reticulum=state.reticulum,
        generation_contract=state.generation_contract,
        simulation=state.simulations,
        compression=state.compression,
        setup=state.setup,
        admission=state.admission,
        drafts=state.drafts,
        review=state.review,
        bibliography=state.bibliography,
        continuation=state.continuation,
        continuation_required=True,
        provenance=state.provenance,
        final_review=state.final_review,
        corpus=state.corpus,
        normative_frame_digest=_normative_frame_digest(state),
        bootstrap_required=True,
        finalization_required=True,
    )
    if (state.node_integrity or {}).get("status") != "PASS":
        errors = (state.node_integrity or {}).get("errors") or ["node.h integrity not verified"]
        state.completion["eligible"] = False
        state.completion["reason"] = (
            state.completion.get("reason", "PASS") + "; " + "; ".join(errors)
        ).strip("; ")
    state.phase = "COMPLETE" if state.completion["eligible"] else "VALIDATING"
    state.interaction = {
        **(state.interaction or {}),
        "card": interaction_card(
            "COMPLETE" if state.completion["eligible"] else "HUMAN_DECISION_REQUIRED",
            summary=(
                "Lavorazione completa; scegli cosa fare dopo."
                if state.completion["eligible"]
                else "Restano blocker prima della consegna."
            ),
        ),
        "status": "READY",
    }
    return state
