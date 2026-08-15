from __future__ import annotations
from typing import Any

from .bibliography import assess_bibliography
from .continuation import (
    audit_continuation_coverage,
    canonical_digest as continuation_digest,
    derive_continuation_plan,
    validate_continuation_plan,
)
from .convergence import completion_gate
from .generation import compression_valid, seal_candidate, text_digest, validate_simulation_receipt
from .mining import deep_mine
from .quality import audit_chapter
from .reticulum import build_generation_contract, validate_reticulum
from .review import review_gate, validate_regeneration, validate_review_cycle
from .setup import accept_setup, parameter_dods, propose_setup
from .sources import research_plan, validate_claim, validate_inference_graph


def ingest_and_mine(state, text, *, source_id, chapter=None, source_record=None):
    state.mining = deep_mine(text, source_id=source_id, chapter=chapter)
    state.style_profile = dict(state.mining.get("style", {}))
    if source_record:
        state.sources = [s for s in state.sources if s.get("id") != source_id] + [dict(source_record)]
    elif not any(s.get("id") == source_id for s in state.sources):
        state.sources.append({
            "id": source_id,
            "title": chapter or source_id,
            "source_type": "corpus_chapter",
            "role": "preceding_chapter",
            "direct_read": True,
            "verified_at": state.updated_at,
        })
    state.corpus = [c for c in state.corpus if c.get("source_id") != source_id] + [{
        "source_id": source_id,
        "chapter": chapter,
        "role": "preceding_chapter",
        "word_count": state.mining.get("surface", {}).get("word_count", 0),
    }]
    state.phase = "SEMANTIC_MINING_REQUIRED"
    return state


def register_semantic_mining(state, units: list[dict[str, Any]], relations: list[dict[str, Any]]):
    source_ids = {s.get("id") for s in state.sources if s.get("id")}
    report = validate_reticulum(units, relations, source_ids=source_ids)
    state.epistemic_units = list(units)
    state.relations = list(relations)
    state.reticulum = report.record()
    if report.status != "PASS":
        state.phase = "RETICULUM_INVALID"
        return state.reticulum
    state.setup = propose_setup(state.mining, state.request, reticulum=state.reticulum)
    state.phase = "USER_SETUP_REQUIRED"
    return state.reticulum


def mine_and_prepare(state, text, *, source_id, chapter=None, semantic_annotations=None):
    """Compatibility wrapper: semantic annotations must contain units+relations to reach setup."""
    ingest_and_mine(state, text, source_id=source_id, chapter=chapter)
    if semantic_annotations:
        register_semantic_mining(state, semantic_annotations.get("units", []), semantic_annotations.get("relations", []))
    return state


def apply_setup(state, overrides=None):
    if state.setup.get("status") != "USER_SETUP_REQUIRED":
        raise ValueError("setup proposal is not ready; validated reticulum required first")
    state.setup = accept_setup(state.setup, overrides)
    existing = [d for d in state.dod if d.get("kind") != "USER_PARAMETER"]
    state.dod = existing + parameter_dods(state.setup)
    state.phase = "DOD_DEFINITION"
    return state


def freeze_dods(state, additional_dods=None):
    if state.setup.get("status") != "ACCEPTED":
        raise ValueError("user setup must be accepted before DoD freeze")
    for dod in additional_dods or []:
        if not dod.get("id"):
            raise ValueError("DoD requires id")
        dod.setdefault("status", "OPEN")
        dod.setdefault("blocking", True)
        dod.setdefault("evidence", [])
        state.dod.append(dod)
    state.generation_contract = build_generation_contract(state.reticulum, state.setup, state.epistemic_units, state.relations)
    plan = derive_continuation_plan(state.generation_contract, state.epistemic_units, state.relations)
    state.continuation = {"plan": plan, "coverage": {}, "benchmark_gap": {}, "status": "PLANNED" if plan.get("status") == "PASS" else "INVALID"}
    state.phase = "DOD_FROZEN"
    return state


def register_continuation_plan(state, plan: dict[str, Any]):
    if state.generation_contract.get("status") != "READY":
        raise ValueError("generation contract not READY")
    ok, errors = validate_continuation_plan(plan, state.generation_contract, state.epistemic_units)
    if not ok:
        raise ValueError("; ".join(errors))
    normalized = dict(plan)
    normalized["status"] = "PASS"
    normalized["errors"] = []
    normalized["digest"] = continuation_digest({k: v for k, v in normalized.items() if k != "digest"})
    state.continuation = {
        **(state.continuation or {}),
        "plan": normalized,
        "coverage": {},
        "status": "PLANNED",
    }
    state.phase = "CONTINUATION_PLANNED"
    return normalized


def record_continuation_coverage(state, payload: dict[str, Any]):
    if not state.drafts:
        raise ValueError("continuation coverage requires a sealed candidate")
    plan = (state.continuation or {}).get("plan") or {}
    current_digest = str(state.drafts[-1].get("digest", ""))
    records = payload.get("coverage", []) if isinstance(payload, dict) else []
    report = audit_continuation_coverage(
        plan,
        records,
        introduced_material_unit_ids=payload.get("introduced_material_unit_ids", []),
        introduced_material_bindings=payload.get("introduced_material_bindings", []),
        candidate_digest=current_digest,
    )
    state.continuation = {
        **(state.continuation or {}),
        "coverage": report,
        "status": "PASS" if report.get("status") == "PASS" else "GAPS_OPEN",
    }
    state.phase = "CONTINUATION_COVERAGE" if report.get("status") == "PASS" else "CONTINUATION_REVIEW_REQUIRED"
    return report


def register_bibliography(state, entries: list[dict[str, Any]] | None):
    state.bibliography = assess_bibliography(entries, state.sources, state.claim_ledger)
    state.phase = "BIBLIOGRAPHY_REGISTERED"
    return state.bibliography


def build_research_plan(state):
    state.source_intelligence["research_plan"] = research_plan(state.claim_ledger)
    state.source_intelligence["coverage_status"] = "PLANNED" if state.source_intelligence["research_plan"] else "NOT_REQUIRED"
    return state


def validate_claim_ledger(state):
    errors = {}
    graph_ok, graph_errors = validate_inference_graph(state.claim_ledger)
    if not graph_ok:
        errors["INFERENCE_GRAPH"] = graph_errors
    for claim in state.claim_ledger:
        ok, es = validate_claim(claim, state.sources, state.claim_ledger, strict=True)
        if not ok:
            errors[claim.get("id", "UNKNOWN")] = es
    state.source_intelligence["coverage_status"] = "PASS" if not errors else "GAPS_OPEN"
    if state.bibliography.get("available"):
        state.bibliography = assess_bibliography(state.bibliography.get("entries", []), state.sources, state.claim_ledger)
    return errors


def seal_draft(state, text: str, *, stage: str = "INITIAL"):
    if state.generation_contract.get("status") != "READY":
        raise ValueError("generation contract not READY")
    if (state.continuation or {}).get("plan", {}).get("status") != "PASS":
        raise ValueError("validated continuation plan required before drafting")
    if stage == "INITIAL" and state.drafts:
        raise ValueError("initial draft already sealed")
    if stage == "REGENERATED" and not state.review.get("cycles"):
        raise ValueError("regeneration requires a prior scientific-editorial review cycle")
    if stage == "COMPRESSED_FINAL" and (state.review.get("saturation") or {}).get("status") != "PASS":
        raise ValueError("final compression requires review saturation PASS")
    record = seal_candidate(text, generation_contract=state.generation_contract, stage=stage, sequence=len(state.drafts) + 1)
    if stage == "REGENERATED":
        regenerations = state.review.get("regenerations", [])
        if not regenerations or regenerations[-1].get("to_digest") != record.get("digest"):
            raise ValueError("regenerated draft digest does not match latest regeneration record")
    state.drafts.append(record)
    if (state.continuation or {}).get("coverage"):
        state.continuation["coverage"] = {}
        state.continuation["status"] = "PLANNED"
    state.phase = "DRAFT_SEALED" if stage == "INITIAL" else ("REGENERATED_DRAFT_SEALED" if stage == "REGENERATED" else "FINAL_COMPRESSED_DRAFT_SEALED")
    return record


def record_review_cycle(state, record: dict[str, Any]):
    if not state.drafts:
        raise ValueError("review requires a sealed candidate")
    current = state.drafts[-1].get("digest")
    ok, errors = validate_review_cycle(record, expected_candidate_digest=current)
    if not ok:
        raise ValueError("; ".join(errors))
    cycles = list(state.review.get("cycles", []))
    expected_cycle = len(cycles) + 1
    if int(record.get("cycle", 0)) != expected_cycle:
        raise ValueError(f"review cycle must be {expected_cycle}")
    cycles.append(dict(record))
    state.review["cycles"] = cycles
    state.review["status"] = record.get("status", "NOT_STARTED")
    state.phase = "SCIENTIFIC_EDITORIAL_REVIEW"
    return record


def record_regeneration(state, record: dict[str, Any]):
    if not state.drafts:
        raise ValueError("regeneration requires a sealed source candidate")
    if not state.review.get("cycles"):
        raise ValueError("regeneration requires review findings")
    expected_from = state.drafts[-1].get("digest")
    latest_cycle = state.review.get("cycles", [])[-1]
    ok, errors = validate_regeneration(record, expected_from_digest=expected_from)
    if int(record.get("cycle", 0)) != int(latest_cycle.get("cycle", 0)):
        errors.append("regeneration cycle must match latest review cycle")
    if latest_cycle.get("candidate_digest") != expected_from:
        errors.append("latest review cycle is not bound to current candidate")
    finding_ids = {str(f.get("id")) for f in latest_cycle.get("findings", [])}
    addressed = set(map(str, record.get("addressed_finding_ids", [])))
    if not addressed or not addressed.issubset(finding_ids):
        errors.append("regeneration must address findings from latest review cycle")
    if not ok or errors:
        raise ValueError("; ".join(dict.fromkeys(errors)))
    state.review.setdefault("regenerations", []).append(dict(record))
    state.phase = "REGENERATION_RECORDED"
    return record


def record_review_saturation(state, receipt: dict[str, Any]):
    if not state.drafts:
        raise ValueError("review saturation requires a sealed candidate")
    current = state.drafts[-1].get("digest")
    state.review["saturation"] = dict(receipt)
    ok, errors = review_gate(state.review, expected_candidate_digest=current, require_regeneration=True)
    state.review["status"] = "SATURATED" if ok else "SATURATION_INCOMPLETE"
    state.metrics["review_no_novelty_streak"] = int(receipt.get("no_novelty_streak", 0))
    state.metrics["review_no_improvement_streak"] = int(receipt.get("no_improvement_without_degradation_streak", 0))
    state.phase = "REVIEW_SATURATED" if ok else "SCIENTIFIC_EDITORIAL_REVIEW"
    return {"status": "PASS" if ok else "FAIL", "errors": errors}


def record_simulation(state, receipt):
    if not state.drafts:
        raise ValueError("simulation requires a sealed final candidate")
    current = state.drafts[-1].get("digest")
    contract_digest = state.generation_contract.get("contract_digest")
    ok, errors = validate_simulation_receipt(
        receipt,
        candidate_digest=current,
        generation_contract_digest=contract_digest,
        require_categories=True,
    )
    if not ok:
        raise ValueError("; ".join(errors))
    state.simulations = dict(receipt)
    state.metrics["simulations_run"] = int(receipt.get("cases", 0))
    state.metrics["simulation_failures"] = int(receipt.get("failures", 0))
    state.phase = "SIMULATED"
    return state


def record_compression(state, record):
    if not state.drafts or state.drafts[-1].get("stage") != "COMPRESSED_FINAL":
        raise ValueError("compression record requires a sealed COMPRESSED_FINAL candidate")
    saturation_candidate = (state.review.get("saturation") or {}).get("candidate_digest")
    final_candidate = state.drafts[-1].get("digest")
    ok, errors = compression_valid(
        record,
        expected_before_digest=saturation_candidate,
        expected_after_digest=final_candidate,
        generation_contract_digest=state.generation_contract.get("contract_digest"),
        strict=True,
    )
    if not ok:
        raise ValueError("; ".join(errors))
    state.compression = dict(record)
    state.phase = "COMPRESSED"
    return state


def record_artifact(state, record: dict[str, Any]):
    if not str(record.get("id", "")).strip():
        raise ValueError("artifact id required")
    if not str(record.get("path", "")).strip():
        raise ValueError("artifact path required")
    if record.get("role") == "final_chapter" and record.get("readback") != "PASS":
        raise ValueError("final chapter artifact requires readback PASS")
    state.artifacts = [a for a in state.artifacts if a.get("id") != record.get("id")] + [dict(record)]
    state.phase = "ARTIFACT_REGISTERED"
    return record


def audit_candidate_chapter(state, text, *, reference_text=None, prior_texts=None, artifact_evidence=None):
    if state.generation_contract.get("status") != "READY":
        raise ValueError("generation contract not READY")
    if not state.drafts:
        raise ValueError("candidate must be sealed before quality audit")
    if text_digest(text) != state.drafts[-1].get("digest"):
        raise ValueError("quality audit text does not match current sealed candidate")
    if artifact_evidence is not None:
        state.artifact_evidence = list(artifact_evidence)
    report = audit_chapter(
        text,
        reference_text=reference_text,
        prior_texts=prior_texts,
        accepted_setup=state.setup,
        claims=state.claim_ledger,
        sources=state.sources,
        artifact_evidence=state.artifact_evidence,
    )
    state.quality = report.record()
    state.phase = "QUALITY_AUDIT"
    return state.quality


def evaluate_completion(state):
    benchmark_required = any(d.get("kind") == "MONOGRAPHIC_EXTRAPOLATION" and d.get("blocking", True) for d in state.dod)
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
    )
    if (state.node_integrity or {}).get("status") != "PASS":
        reason = (state.node_integrity or {}).get("errors") or ["node.h integrity not verified"]
        state.completion["eligible"] = False
        state.completion["reason"] = (state.completion.get("reason", "PASS") + "; " + "; ".join(reason)).strip("; ")
    state.phase = "COMPLETE" if state.completion["eligible"] else "VALIDATING"
    return state
