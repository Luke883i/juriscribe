from __future__ import annotations

from typing import Any

from . import generation_governance as _generation
from . import multimode as _multimode
from . import runtime_autopilot as _autopilot
from .consolidation import (
    CANONICAL_ROLE,
    CANDIDATE_ROLE,
    build_joint_reticulum,
    build_lossless_inventory,
    build_reference_method_profile,
    build_refactoring_contract,
    canonical_digest,
    inventory_set_digest,
    record_user_calibration,
    text_digest,
    validate_lossless_inventory,
    validate_mutation_receipt,
    validate_saturation_receipt,
)
from .interaction import interaction_card
from .modes import (
    COMPRESSION_CONSOLIDATION,
    build_mode_contract,
    mode_selection_record,
    normalize_mode,
    validate_mode_contract,
)

CC_ARTIFACT_PROFILE = "JURISCRIBE_CONSOLIDATION_ARTIFACT_AUTOPILOT_V1"


def _cc(state) -> dict[str, Any]:
    return state.strategy.setdefault("consolidation", {})


def _reset_completion(state, reason: str) -> None:
    state.completion = {"eligible": False, "reason": reason}


def _reset_review_surfaces(state) -> None:
    state.review = {
        **(state.review or {}),
        "cycles": [],
        "regenerations": [],
        "saturation": {},
        "status": "NOT_STARTED",
    }
    state.provenance = {}
    state.final_review = {}


def _clear_cc_proofs(state, *, clear_plan: bool = True, reason: str) -> None:
    cc = _cc(state)
    if clear_plan:
        cc["refactoring_contract"] = {}
    cc["mutation_receipt"] = {}
    cc["saturation"] = {}
    cc["refined_candidates"] = {}
    cc["peer_review_readiness"] = {}
    cc["provenance"] = {}
    cc["final_review"] = {}
    cc["artifact_autopilot"] = {}
    state.simulations = {}
    state.compression = {}
    state.metrics["simulations_run"] = 0
    state.metrics["simulation_failures"] = 0
    _reset_review_surfaces(state)
    state.artifacts = [
        item
        for item in (state.artifacts or [])
        if str(item.get("autopilot_profile") or "") != CC_ARTIFACT_PROFILE
    ]
    _reset_completion(state, reason)


def _invalidate_after_inventory_change(state) -> None:
    _clear_cc_proofs(
        state,
        clear_plan=True,
        reason="C&C material inventory changed; semantic mining and downstream evidence must be regenerated",
    )
    state.epistemic_units = []
    state.relations = []
    state.reticulum = {}
    state.setup = {}
    state.editorial_standard = {}
    state.generation_contract = {}
    state.mode_contract = {}


def _invalidate_after_reticulum_change(state) -> None:
    _clear_cc_proofs(
        state,
        clear_plan=True,
        reason="C&C semantic reticulum changed; setup, plan and downstream evidence must be regenerated",
    )
    state.setup = {}
    state.editorial_standard = {}
    state.generation_contract = {}
    state.mode_contract = {}


def select_mode(state, mode: str):
    mode = normalize_mode(mode)
    if mode != COMPRESSION_CONSOLIDATION:
        return _autopilot.select_mode(state, mode)
    if state.corpus or state.drafts:
        raise ValueError("mode must be selected before substantive corpus ingestion")
    state.mode = mode
    state.mode_selection = mode_selection_record(mode, request=state.request)
    state.mode_contract = {}
    state.editorial_standard = {}
    state.phase = "MODE_SELECTED"
    _cc(state).update({
        "inventories": {},
        "source_texts": {},
        "reference_profile": {},
        "refactoring_contract": {},
        "mutation_receipt": {},
        "saturation": {},
        "calibration": [],
        "refined_candidates": {},
        "peer_review_readiness": {},
        "provenance": {},
        "final_review": {},
        "artifact_autopilot": {},
    })
    state.interaction = {
        **(state.interaction or {}),
        "card": interaction_card(
            "MODE_SELECTED",
            summary="Carica materiali CANONICAL e CANDIDATE; i canonici sono riferimenti immutabili, i candidati sono rifattorizzabili.",
            choices=["CARICA CANONICAL", "CARICA CANDIDATE", "ALTRO"],
        ),
        "status": "READY",
    }
    return state.mode_selection


def ingest_and_mine(state, text, *, source_id, chapter=None, source_record=None, role=None):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _generation.ingest_and_mine(
            state,
            text,
            source_id=source_id,
            chapter=chapter,
            source_record=source_record,
            role=role,
        )
    source_id = str(source_id or "").strip()
    if not source_id:
        raise ValueError("C&C source_id must be non-empty")
    role = str(role or CANDIDATE_ROLE).strip().lower()
    if role not in {CANONICAL_ROLE, CANDIDATE_ROLE}:
        raise ValueError("C&C role must be canonical_material or candidate_material")
    inv = build_lossless_inventory(text, source_id=source_id, role=role)
    if inv.get("status") != "PASS":
        raise ValueError("lossless inventory failed")
    cc = _cc(state)
    cc.setdefault("inventories", {})[source_id] = inv
    cc.setdefault("source_texts", {})[source_id] = str(text)
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
        "source_id": source_id,
        "chapter": chapter,
        "role": role,
        "digest": text_digest(text),
        "word_count": len(str(text).split()),
        "inventory_digest": inv["digest"],
    }]
    _invalidate_after_inventory_change(state)
    state.phase = "CONSOLIDATION_INVENTORY"
    return state


def register_semantic_mining(state, units: list[dict[str, Any]], relations: list[dict[str, Any]]):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _generation.register_semantic_mining(state, units, relations)
    cc = _cc(state)
    inventories = list((cc.get("inventories") or {}).values())
    report = build_joint_reticulum(inventories, units, relations)
    state.epistemic_units = list(units)
    state.relations = list(relations)
    state.reticulum = report
    _invalidate_after_reticulum_change(state)
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
        return _autopilot.apply_setup(state, overrides)
    if state.setup.get("status") != "USER_SETUP_REQUIRED":
        raise ValueError("setup proposal is not ready")
    accepted = dict(state.setup.get("recommended") or {})
    accepted.update(overrides or {})
    _clear_cc_proofs(
        state,
        clear_plan=True,
        reason="C&C setup changed; refactoring evidence must be regenerated",
    )
    state.mode_contract = {}
    state.generation_contract = {}
    state.setup = {
        "status": "ACCEPTED",
        "mode": COMPRESSION_CONSOLIDATION,
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
            "formal_register": True,
            "stable_terminology": True,
            "claim_source_traceability": True,
            "no_fabricated_authority": True,
            "minimal_refactoring": True,
            "semantic_losslessness": True,
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
        return _autopilot.freeze_dods(state, additional_dods)
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
        request=state.request,
        corpus=state.corpus,
        reticulum=state.reticulum,
        setup=state.setup,
        editorial_standard=state.editorial_standard,
        generation_contract=state.generation_contract,
    )
    if state.mode_contract.get("status") != "READY":
        raise ValueError("; ".join(state.mode_contract.get("errors") or []))
    _clear_cc_proofs(
        state,
        clear_plan=True,
        reason="C&C DoD frozen; a fresh refactoring plan and downstream proof are required",
    )
    state.phase = "REFACTORING_PLAN_REQUIRED"
    return state


def register_refactoring_plan(state, *, gaps, operations):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("refactoring plan is C&C-only")
    if state.mode_contract.get("status") != "READY":
        raise ValueError("current READY mode contract required before refactoring plan")
    candidate_units = [u for u in state.epistemic_units if u.get("material_role") == CANDIDATE_ROLE]
    plan = build_refactoring_contract(
        reticulum=state.reticulum,
        candidate_units=candidate_units,
        gaps=list(gaps or []),
        operations=list(operations or []),
    )
    if plan.get("status") != "READY":
        raise ValueError("; ".join(plan.get("errors") or []))
    _clear_cc_proofs(
        state,
        clear_plan=True,
        reason="C&C refactoring plan changed; mutation, saturation and review evidence must be regenerated",
    )
    cc = _cc(state)
    cc["refactoring_contract"] = plan
    state.phase = "CONSOLIDATION_MUTATION_REQUIRED"
    return plan


def record_simulation(state, receipt):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return _multimode.record_simulation(state, receipt)
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    if plan.get("status") != "READY":
        raise ValueError("current READY refactoring plan required before mutation receipt")
    ok, errors = validate_mutation_receipt(
        receipt,
        plan_digest=plan.get("digest", ""),
        reticulum_digest=state.reticulum.get("digest", ""),
    )
    if not ok:
        raise ValueError("; ".join(errors))
    cc["mutation_receipt"] = dict(receipt)
    cc["saturation"] = {}
    cc["refined_candidates"] = {}
    cc["peer_review_readiness"] = {}
    cc["provenance"] = {}
    cc["final_review"] = {}
    state.simulations = dict(receipt)
    state.compression = {}
    state.metrics["simulations_run"] = int(receipt.get("cases", 0))
    state.phase = "CONSOLIDATION_MUTATED"
    _reset_completion(state, "C&C mutation recorded; saturation and downstream evidence remain required")
    return state


def record_consolidation_saturation(state, receipt):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("C&C saturation only")
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    mutation = cc.get("mutation_receipt") or {}
    if plan.get("status") != "READY":
        raise ValueError("current READY refactoring plan required before saturation")
    mutation_ok, mutation_errors = validate_mutation_receipt(
        mutation,
        plan_digest=plan.get("digest", ""),
        reticulum_digest=state.reticulum.get("digest", ""),
    )
    if not mutation_ok:
        raise ValueError("current 10M mutation receipt required before saturation: " + "; ".join(mutation_errors))
    ok, errors = validate_saturation_receipt(receipt, plan_digest=plan.get("digest", ""))
    if not ok:
        raise ValueError("; ".join(errors))
    cc["saturation"] = dict(receipt)
    cc["refined_candidates"] = {}
    cc["peer_review_readiness"] = {}
    cc["provenance"] = {}
    cc["final_review"] = {}
    state.compression = dict(receipt)
    state.phase = "CONSOLIDATION_SATURATED"
    _reset_completion(state, "C&C saturated; refined candidates and review evidence remain required")
    return receipt


def calibrate_refactoring(state, decisions):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("user calibration is C&C-only")
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    rec = record_user_calibration(plan, list(decisions or []))
    cc.setdefault("calibration", []).append(rec)
    if rec.get("material_change"):
        _clear_cc_proofs(
            state,
            clear_plan=True,
            reason="material user calibration changed C&C intent; refactoring plan and downstream evidence are stale",
        )
        state.phase = "REFACTORING_PLAN_REQUIRED"
    return rec


def seal_refined_candidate(
    state,
    *,
    source_id: str,
    text: str,
    semantic_recall: float,
    relation_recall: float,
):
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        raise ValueError("refined candidate is C&C-only")
    cc = _cc(state)
    plan = cc.get("refactoring_contract") or {}
    mutation_ok, mutation_errors = validate_mutation_receipt(
        cc.get("mutation_receipt") or {},
        plan_digest=plan.get("digest", ""),
        reticulum_digest=state.reticulum.get("digest", ""),
    )
    saturation_ok, saturation_errors = validate_saturation_receipt(
        cc.get("saturation") or {},
        plan_digest=plan.get("digest", ""),
    )
    if not mutation_ok or not saturation_ok:
        raise ValueError(
            "current mutation and saturation PASS required before materialization: "
            + "; ".join(mutation_errors + saturation_errors)
        )
    source = next(
        (
            c
            for c in state.corpus
            if c.get("source_id") == source_id and c.get("role") == CANDIDATE_ROLE
        ),
        None,
    )
    if not source:
        raise ValueError("candidate source not found")
    if float(semantic_recall) != 1.0 or float(relation_recall) != 1.0:
        raise ValueError("refined candidate must be lossless against semantic reticulum")
    inventory = (cc.get("inventories") or {}).get(source_id) or {}
    record = {
        "source_id": source_id,
        "source_digest": source.get("digest"),
        "inventory_digest": inventory.get("digest"),
        "refined_digest": text_digest(text),
        "text": str(text),
        "semantic_recall": 1.0,
        "relation_recall": 1.0,
        "plan_digest": plan.get("digest"),
        "reticulum_digest": state.reticulum.get("digest"),
        "status": "SEALED",
    }
    record["digest"] = canonical_digest(record)
    cc.setdefault("refined_candidates", {})[source_id] = record
    cc["peer_review_readiness"] = {}
    cc["provenance"] = {}
    cc["final_review"] = {}
    state.phase = "REFINED_CANDIDATE_SEALED"
    _reset_completion(state, "C&C refined candidate set changed; review and provenance must be regenerated")
    return record


def consolidation_gate(state) -> tuple[bool, list[str]]:
    if normalize_mode(state.mode) != COMPRESSION_CONSOLIDATION:
        return True, []
    cc = _cc(state)
    errors: list[str] = []
    inventories = cc.get("inventories") or {}
    source_texts = cc.get("source_texts") or {}
    corpus_materials = [
        c for c in state.corpus if c.get("role") in {CANONICAL_ROLE, CANDIDATE_ROLE}
    ]
    corpus_by_source = {str(c.get("source_id") or ""): c for c in corpus_materials}
    inventory_ids = set(map(str, inventories))
    corpus_ids = set(corpus_by_source)
    if inventory_ids != corpus_ids:
        errors.append("current corpus and lossless inventory source sets diverge")
    for source_id, inv in inventories.items():
        source_id = str(source_id)
        text = source_texts.get(source_id)
        if text is None:
            errors.append(f"source text missing for inventory: {source_id}")
            continue
        ok, inventory_errors = validate_lossless_inventory(inv, text)
        if not ok:
            errors.extend(f"{source_id}: {msg}" for msg in inventory_errors)
        corpus_item = corpus_by_source.get(source_id)
        if not corpus_item:
            continue
        if str(corpus_item.get("role") or "") != str(inv.get("role") or ""):
            errors.append(f"corpus/inventory role mismatch: {source_id}")
        if corpus_item.get("digest") != text_digest(text):
            errors.append(f"corpus/source digest mismatch: {source_id}")
        if corpus_item.get("inventory_digest") != inv.get("digest"):
            errors.append(f"corpus/inventory digest mismatch: {source_id}")

    reticulum = state.reticulum or {}
    expected_reticulum = build_joint_reticulum(
        list(inventories.values()),
        list(state.epistemic_units or []),
        list(state.relations or []),
    )
    if reticulum.get("status") != "PASS" or reticulum.get("object_coverage") != 1.0:
        errors.append("joint reticulum is not lossless")
    if reticulum.get("digest") != expected_reticulum.get("digest"):
        errors.append("joint reticulum does not match current semantic state")
    if reticulum.get("inventories_digest") != inventory_set_digest(list(inventories.values())):
        errors.append("joint reticulum is bound to stale inventories")
    if reticulum.get("semantic_units_digest") != canonical_digest(state.epistemic_units):
        errors.append("joint reticulum is bound to stale semantic units")
    if reticulum.get("relations_digest") != canonical_digest(state.relations):
        errors.append("joint reticulum is bound to stale relations")

    mode_contract = state.mode_contract or {}
    mode_ok, mode_errors = validate_mode_contract(
        mode_contract,
        mode=COMPRESSION_CONSOLIDATION,
        request=state.request,
        corpus=state.corpus,
        reticulum=reticulum,
        setup=state.setup,
        editorial_standard=state.editorial_standard,
        generation_contract=state.generation_contract,
    )
    if not mode_ok:
        errors.extend(mode_errors)

    plan = cc.get("refactoring_contract") or {}
    candidate_units = [
        unit for unit in state.epistemic_units
        if unit.get("material_role") == CANDIDATE_ROLE
    ]
    expected_plan = build_refactoring_contract(
        reticulum=reticulum,
        candidate_units=candidate_units,
        gaps=list(plan.get("gaps") or []),
        operations=list(plan.get("operations") or []),
    ) if plan else {}
    if plan.get("status") != "READY":
        errors.append("refactoring contract not READY")
    elif plan.get("digest") != expected_plan.get("digest"):
        errors.append("refactoring contract does not match current gaps, operations or candidate units")

    mutation = cc.get("mutation_receipt") or {}
    mutation_ok, mutation_errors = validate_mutation_receipt(
        mutation,
        plan_digest=plan.get("digest", ""),
        reticulum_digest=reticulum.get("digest", ""),
    )
    if not mutation_ok:
        errors.extend(mutation_errors)

    saturation = cc.get("saturation") or {}
    saturation_ok, saturation_errors = validate_saturation_receipt(
        saturation,
        plan_digest=plan.get("digest", ""),
    )
    if not saturation_ok:
        errors.extend(saturation_errors)

    candidates = [c for c in corpus_materials if c.get("role") == CANDIDATE_ROLE]
    sealed = cc.get("refined_candidates") or {}
    missing = [c.get("source_id") for c in candidates if c.get("source_id") not in sealed]
    if missing:
        errors.append("refined candidates missing: " + ", ".join(map(str, missing)))
    for candidate in candidates:
        source_id = str(candidate.get("source_id") or "")
        rec = sealed.get(source_id)
        if not rec:
            continue
        if rec.get("status") != "SEALED":
            errors.append(f"refined candidate not SEALED: {source_id}")
        if rec.get("source_digest") != candidate.get("digest"):
            errors.append(f"refined candidate bound to stale source: {source_id}")
        inventory = inventories.get(source_id) or {}
        if rec.get("inventory_digest") != inventory.get("digest"):
            errors.append(f"refined candidate bound to stale inventory: {source_id}")
        if rec.get("plan_digest") != plan.get("digest"):
            errors.append(f"refined candidate bound to stale plan: {source_id}")
        if rec.get("reticulum_digest") != reticulum.get("digest"):
            errors.append(f"refined candidate bound to stale reticulum: {source_id}")
        if rec.get("semantic_recall") != 1.0 or rec.get("relation_recall") != 1.0:
            errors.append(f"refined candidate not reticulum-lossless: {source_id}")
        expected_digest = canonical_digest({k: v for k, v in rec.items() if k != "digest"})
        if rec.get("digest") != expected_digest:
            errors.append(f"refined candidate digest mismatch: {source_id}")

    canonical_ids = {
        c.get("source_id") for c in corpus_materials if c.get("role") == CANONICAL_ROLE
    }
    if any(sid in sealed for sid in canonical_ids):
        errors.append("canonical material was incorrectly materialized as refined candidate")
    return not errors, list(dict.fromkeys(errors))
