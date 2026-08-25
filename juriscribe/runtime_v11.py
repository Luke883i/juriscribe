from __future__ import annotations

from typing import Any

from . import multimode as _legacy
from .consolidation import (
    CANONICAL_ROLE, CANDIDATE_ROLE,
    build_lossless_inventory, build_reference_method_profile, build_joint_reticulum,
    build_refactoring_contract, canonical_digest, record_user_calibration,
    text_digest, validate_mutation_receipt, validate_saturation_receipt,
)
from .interaction import interaction_card
from .modes import COMPRESSION_CONSOLIDATION, build_mode_contract, mode_selection_record, normalize_mode


def _cc(state) -> dict[str, Any]:
    return state.strategy.setdefault("consolidation", {})


def select_mode(state, mode: str):
    mode = normalize_mode(mode)
    if mode != COMPRESSION_CONSOLIDATION:
        return _legacy.select_mode(state, mode)
    if state.corpus or state.drafts:
        raise ValueError("mode must be selected before substantive corpus ingestion")
    state.mode = mode
    state.mode_selection = mode_selection_record(mode, request=state.request)
    state.mode_contract = {}
    state.editorial_standard = {}
    state.phase = "MODE_SELECTED"
    _cc(state).update({
        "inventories": {}, "source_texts": {}, "reference_profile": {},
        "refactoring_contract": {}, "mutation_receipt": {}, "saturation": {},
        "calibration": [], "refined_candidates": {}, "peer_review_readiness": {},
    })
    state.interaction = {**(state.interaction or {}), "card": interaction_card(
        "MODE_SELECTED",
        summary="Carica materiali CANONICAL e CANDIDATE; i canonici sono riferimenti immutabili, i candidati sono rifattorizzabili.",
        choices=["CARICA CANONICAL", "CARICA CANDIDATE", "ALTRO"],
    ), "status": "READY"}
    return state.mode_selection


def ingest_and_mine(state, text, *, source_id, chapter=None, source_record=None, role=None):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _legacy.ingest_and_mine(state, text, source_id=source_id, chapter=chapter, source_record=source_record, role=role)
    role = str(role or CANDIDATE_ROLE).strip().lower()
    if role not in {CANONICAL_ROLE, CANDIDATE_ROLE}:
        raise ValueError("C&C role must be canonical_material or candidate_material")
    inv = build_lossless_inventory(text, source_id=source_id, role=role)
    if inv.get("status") != "PASS":
        raise ValueError("lossless inventory failed")
    cc = _cc(state)
    cc["inventories"][source_id] = inv
    cc["source_texts"][source_id] = str(text)
    cc["reference_profile"] = build_reference_method_profile(list(cc["inventories"].values()))
    record = dict(source_record or {})
    record.update({
        "id": source_id,
        "title": record.get("title") or chapter or source_id,
        "source_type": "user_supplied_material",
        "role": role,
        "direct_read": True,
        "verified_at": record.get("verified_at") or state.updated_at,
    })
    state.sources = [s for s in state.sources if s.get("id") != source_id] + [record]
    state.corpus = [c for c in state.corpus if c.get("source_id") != source_id] + [{
        "source_id": source_id, "chapter": chapter, "role": role,
        "digest": text_digest(text), "word_count": len(str(text).split()),
        "inventory_digest": inv["digest"],
    }]
    state.mode_contract = {}
    state.phase = "CONSOLIDATION_INVENTORY"
    return state


def register_semantic_mining(state, units: list[dict[str, Any]], relations: list[dict[str, Any]]):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _legacy.register_semantic_mining(state, units, relations)
    cc = _cc(state)
    inventories = list((cc.get("inventories") or {}).values())
    report = build_joint_reticulum(inventories, units, relations)
    state.epistemic_units = list(units)
    state.relations = list(relations)
    state.reticulum = report
    state.mode_contract = {}
    if report.get("status") != "PASS":
        state.phase = "RETICULUM_INVALID"
        return report
    state.setup = {
        "status": "USER_SETUP_REQUIRED",
        "mode": COMPRESSION_CONSOLIDATION,
        "recommended": {
            "document_type": "GENERIC_LEGAL_TEXT",
            "audience": "giuristi, accademici e redazioni giuridiche",
            "citation_style": "PROJECT_DEFINED",
            "research_depth": "verifica mirata dei claim materiali",
            "refactoring_policy": "MINIMAL_SURGICAL_LOSSLESS",
            "canonical_policy": "IMMUTABLE_REFERENCE",
            "peer_review_target": "READY_FOR_PEER_REVIEW",
        },
        "simple_options": ["ACCETTA CONSIGLIATI", "MODIFICA", "ALTRO"],
        "reticulum_digest": report.get("digest"),
    }
    state.phase = "USER_SETUP_REQUIRED"
    return report


def apply_setup(state, overrides=None):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _legacy.apply_setup(state, overrides)
    if state.setup.get("status") != "USER_SETUP_REQUIRED":
        raise ValueError("setup proposal is not ready")
    accepted = dict(state.setup.get("recommended") or {})
    accepted.update(overrides or {})
    state.setup = {
        "status": "ACCEPTED", "mode": COMPRESSION_CONSOLIDATION,
        "accepted": accepted,
        "source": "recommended" if not overrides else "recommended_with_user_overrides",
        "reticulum_digest": state.reticulum.get("digest"),
    }
    state.editorial_standard = {
        "schema": "juriscribe-editorial-standard/v1",
        "standard_id": "JURISCRIBE_LEGAL_EDITORIAL_CORE_V2",
        "mode": COMPRESSION_CONSOLIDATION,
        "document_type": accepted.get("document_type", "GENERIC_LEGAL_TEXT"),
        "audience": accepted.get("audience", "giuristi, accademici e redazioni giuridiche"),
        "rules": {
            "formal_register": True, "stable_terminology": True,
            "claim_source_traceability": True, "no_fabricated_authority": True,
            "minimal_refactoring": True, "semantic_losslessness": True,
            "canonical_immutability": True,
        },
        "mode_adjustments": [
            "treat canonical material as immutable transformation reference",
            "change candidate material only on evidenced gap",
            "preserve semantic units and required relations",
            "prepare refined candidates for peer review without claiming peer review occurred",
        ],
        "source_style_profile": (_cc(state).get("reference_profile") or {}),
        "status": "READY",
    }
    state.editorial_standard["digest"] = canonical_digest(state.editorial_standard)
    state.phase = "DOD_DEFINITION"
    return state


def freeze_dods(state, additional_dods=None):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _legacy.freeze_dods(state, additional_dods)
    if state.setup.get("status") != "ACCEPTED":
        raise ValueError("user setup must be accepted before DoD freeze")
    state.generation_contract = {
        "status": "NOT_REQUIRED",
        "mode": COMPRESSION_CONSOLIDATION,
        "contract_digest": canonical_digest({
            "mode": COMPRESSION_CONSOLIDATION,
            "reticulum": state.reticulum.get("digest"),
        }),
    }
    state.mode_contract = build_mode_contract(
        COMPRESSION_CONSOLIDATION,
        request=state.request, corpus=state.corpus, reticulum=state.reticulum,
        setup=state.setup, editorial_standard=state.editorial_standard,
        generation_contract=state.generation_contract,
    )
    if state.mode_contract.get("status") != "READY":
        raise ValueError("; ".join(state.mode_contract.get("errors") or []))
    cc = _cc(state)
    cc["refactoring_contract"] = {}
    cc["mutation_receipt"] = {}
    cc["saturation"] = {}
    state.phase = "REFACTORING_PLAN_REQUIRED"
    return state


def register_refactoring_plan(state, *, gaps, operations):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("refactoring plan is C&C-only")
    candidate_units = [u for u in state.epistemic_units if u.get("material_role") == CANDIDATE_ROLE]
    plan = build_refactoring_contract(
        reticulum=state.reticulum,
        candidate_units=candidate_units,
        gaps=list(gaps or []),
        operations=list(operations or []),
    )
    if plan.get("status") != "READY":
        raise ValueError("; ".join(plan.get("errors") or []))
    cc = _cc(state)
    cc["refactoring_contract"] = plan
    cc["mutation_receipt"] = {}
    cc["saturation"] = {}
    cc["peer_review_readiness"] = {}
    state.phase = "CONSOLIDATION_MUTATION_REQUIRED"
    return plan


def record_simulation(state, receipt):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _legacy.record_simulation(state, receipt)
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    ok, errors = validate_mutation_receipt(
        receipt,
        plan_digest=plan.get("digest", ""),
        reticulum_digest=state.reticulum.get("digest", ""),
    )
    if not ok:
        raise ValueError("; ".join(errors))
    cc["mutation_receipt"] = dict(receipt)
    state.simulations = dict(receipt)
    state.metrics["simulations_run"] = int(receipt.get("cases", 0))
    state.phase = "CONSOLIDATION_MUTATED"
    return state


def record_consolidation_saturation(state, receipt):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("C&C saturation only")
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    if not cc.get("mutation_receipt"):
        raise ValueError("10M mutation receipt required before saturation")
    ok, errors = validate_saturation_receipt(receipt, plan_digest=plan.get("digest", ""))
    if not ok:
        raise ValueError("; ".join(errors))
    cc["saturation"] = dict(receipt)
    state.compression = dict(receipt)
    state.phase = "CONSOLIDATION_SATURATED"
    return receipt


def calibrate_refactoring(state, decisions):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("user calibration is C&C-only")
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    rec = record_user_calibration(plan, list(decisions or []))
    cc.setdefault("calibration", []).append(rec)
    if rec.get("material_change"):
        cc["mutation_receipt"] = {}
        cc["saturation"] = {}
        state.simulations = {}
        state.compression = {}
        state.phase = "REFACTORING_PLAN_REQUIRED"
    return rec


def seal_refined_candidate(state, *, source_id: str, text: str, semantic_recall: float, relation_recall: float):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("refined candidate is C&C-only")
    cc = _cc(state)
    if not cc.get("mutation_receipt") or not cc.get("saturation"):
        raise ValueError("mutation and saturation PASS required before materialization")
    source = next((c for c in state.corpus if c.get("source_id") == source_id and c.get("role") == CANDIDATE_ROLE), None)
    if not source:
        raise ValueError("candidate source not found")
    if float(semantic_recall) != 1.0 or float(relation_recall) != 1.0:
        raise ValueError("refined candidate must be lossless against semantic reticulum")
    record = {
        "source_id": source_id,
        "source_digest": source.get("digest"),
        "refined_digest": text_digest(text),
        "text": str(text),
        "semantic_recall": 1.0,
        "relation_recall": 1.0,
        "plan_digest": cc["refactoring_contract"].get("digest"),
        "status": "SEALED",
    }
    record["digest"] = canonical_digest(record)
    cc.setdefault("refined_candidates", {})[source_id] = record
    state.phase = "REFINED_CANDIDATE_SEALED"
    return record


def consolidation_gate(state) -> tuple[bool, list[str]]:
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return True, []
    cc = _cc(state)
    errors: list[str] = []
    candidates = [c for c in state.corpus if c.get("role") == CANDIDATE_ROLE]
    if state.reticulum.get("status") != "PASS" or state.reticulum.get("object_coverage") != 1.0:
        errors.append("joint reticulum is not lossless")
    if (cc.get("refactoring_contract") or {}).get("status") != "READY":
        errors.append("refactoring contract not READY")
    if not cc.get("mutation_receipt"):
        errors.append("10M mutation receipt missing")
    if not cc.get("saturation"):
        errors.append("dual saturation receipt missing")
    sealed = cc.get("refined_candidates") or {}
    missing = [c.get("source_id") for c in candidates if c.get("source_id") not in sealed]
    if missing:
        errors.append("refined candidates missing: " + ", ".join(map(str, missing)))
    canonical_ids = {c.get("source_id") for c in state.corpus if c.get("role") == CANONICAL_ROLE}
    if any(sid in sealed for sid in canonical_ids):
        errors.append("canonical material was incorrectly materialized as refined candidate")
    return not errors, errors
