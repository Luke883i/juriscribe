from __future__ import annotations

from typing import Any

from . import finalization as legacy_final
from . import orchestrator_base as base
from .benchmark import benchmark_gate
from .bibliography import bibliography_gate
from .bootstrap import bootstrap_gate
from .continuation import continuation_gate, derive_continuation_plan
from .convergence import all_dods_done
from .editorial import editorial_conformance, resolve_editorial_standard, validate_editorial_standard
from .final_review import final_review_gate
from .generation import canonical_digest as generation_digest, compression_valid, seal_candidate, text_digest, validate_simulation_receipt
from .interaction import interaction_card
from .mining import deep_mine
from .modes import CONTINUATION, GREENFIELD, REVIEW, build_mode_contract, mode_selection_record, mode_spec, normalize_mode, required_artifact_roles, review_output, validate_mode_contract
from .provenance import build_provenance_bundle, canonical_digest as provenance_digest, provenance_gate
from .quality import audit_chapter
from .reticulum import build_generation_contract, canonical_digest as reticulum_digest, generation_contract_valid, validate_reticulum
from .review import review_gate, validate_review_cycle
from .setup import accept_setup, parameter_dods, propose_setup


def select_mode(state, mode: str):
    if state.corpus or state.drafts:
        raise ValueError("mode must be selected before substantive corpus ingestion")
    state.mode = normalize_mode(mode)
    state.mode_selection = mode_selection_record(state.mode, request=state.request)
    state.mode_contract = {}
    state.editorial_standard = {}
    state.phase = "MODE_SELECTED"
    choices = {CONTINUATION: ["CARICA CAPITOLI PRECEDENTI", "ALTRO"], GREENFIELD: ["FORNISCI CONCEPT", "ALTRO"], REVIEW: ["CARICA TESTO DA REVISIONARE", "ALTRO"]}[state.mode]
    state.interaction = {**(state.interaction or {}), "card": interaction_card("MODE_SELECTED", summary=f"Modalità {state.mode} selezionata.", choices=choices), "status": "READY"}
    return state.mode_selection


def _require_mode(state) -> str:
    if not state.mode:
        raise ValueError("select Juriscribe mode before substantive work")
    return normalize_mode(state.mode)


def ingest_and_mine(state, text, *, source_id, chapter=None, source_record=None, role=None):
    mode = _require_mode(state)
    role = str(role or mode_spec(mode, state.setup)["input_role"])
    state.mining = deep_mine(text, source_id=source_id, chapter=chapter)
    state.style_profile = dict(state.mining.get("style", {}))
    record = dict(source_record or {})
    record.update({"id": source_id, "title": record.get("title") or chapter or source_id, "source_type": record.get("source_type") or ("corpus_chapter" if role == "preceding_chapter" else "user_supplied_material"), "role": record.get("role") or role, "direct_read": True, "verified_at": record.get("verified_at") or state.updated_at})
    state.sources = [s for s in state.sources if s.get("id") != source_id] + [record]
    state.corpus = [c for c in state.corpus if c.get("source_id") != source_id] + [{"source_id": source_id, "chapter": chapter, "role": role, "digest": text_digest(text), "word_count": state.mining.get("surface", {}).get("word_count", 0)}]
    state.mode_contract = {}
    state.phase = "SEMANTIC_MINING_REQUIRED"
    return state


def register_semantic_mining(state, units: list[dict[str, Any]], relations: list[dict[str, Any]]):
    mode = _require_mode(state)
    source_ids = {s.get("id") for s in state.sources if s.get("id")}
    report = validate_reticulum(units, relations, source_ids=source_ids)
    state.epistemic_units = list(units)
    state.relations = list(relations)
    state.reticulum = report.record()
    state.mode_contract = {}
    if report.status != "PASS":
        state.phase = "RETICULUM_INVALID"
        return state.reticulum
    state.setup = propose_setup(state.mining, state.request, reticulum=state.reticulum, mode=mode)
    state.phase = "USER_SETUP_REQUIRED"
    return state.reticulum


def apply_setup(state, overrides=None):
    mode = _require_mode(state)
    if state.setup.get("status") != "USER_SETUP_REQUIRED":
        raise ValueError("setup proposal is not ready; validated reticulum required first")
    state.setup = accept_setup(state.setup, overrides)
    state.editorial_standard = resolve_editorial_standard(mode, state.setup, request=state.request, mining=state.mining)
    existing = [d for d in state.dod if d.get("kind") != "USER_PARAMETER"]
    state.dod = existing + parameter_dods(state.setup)
    state.mode_contract = {}
    state.phase = "DOD_DEFINITION"
    return state


def _revision_contract(state) -> dict[str, Any]:
    preserve = sorted(str(u.get("id")) for u in state.epistemic_units if u.get("id") and bool(u.get("material", True)))
    payload = {"reticulum_digest": state.reticulum.get("digest", ""), "setup_digest": reticulum_digest(state.setup.get("accepted", {})), "preserve_unit_ids": preserve, "develop_unit_ids": [], "avoid_duplicate_unit_ids": [], "cross_chapter_relations": [], "mode": REVIEW, "purpose": "REVISION_OF_SUPPLIED_TEXT"}
    payload["contract_digest"] = reticulum_digest(payload)
    payload["status"] = "READY"
    return payload


def freeze_dods(state, additional_dods=None):
    mode = _require_mode(state)
    if state.setup.get("status") != "ACCEPTED":
        raise ValueError("user setup must be accepted before DoD freeze")
    ok_ed, ed_errors = validate_editorial_standard(state.editorial_standard, mode=mode)
    if not ok_ed:
        raise ValueError("; ".join(ed_errors))
    for dod in additional_dods or []:
        if not dod.get("id"):
            raise ValueError("DoD requires id")
        item = dict(dod); item.setdefault("status", "OPEN"); item.setdefault("blocking", True); item.setdefault("evidence", []); state.dod.append(item)
    if mode in {CONTINUATION, GREENFIELD}:
        state.generation_contract = build_generation_contract(state.reticulum, state.setup, state.epistemic_units, state.relations)
    elif review_output(state.setup) == "REPORT_AND_REVISED_TEXT":
        state.generation_contract = _revision_contract(state)
    else:
        state.generation_contract = {"status": "NOT_REQUIRED", "mode": REVIEW}
    if mode == CONTINUATION:
        plan = derive_continuation_plan(state.generation_contract, state.epistemic_units, state.relations)
        state.continuation = {"plan": plan, "coverage": {}, "benchmark_gap": {}, "status": "PLANNED" if plan.get("status") == "PASS" else "INVALID"}
    else:
        state.continuation = {"plan": {}, "coverage": {}, "benchmark_gap": {}, "status": "NOT_APPLICABLE"}
    state.mode_contract = build_mode_contract(mode, request=state.request, corpus=state.corpus, reticulum=state.reticulum, setup=state.setup, editorial_standard=state.editorial_standard, generation_contract=state.generation_contract)
    if state.mode_contract.get("status") != "READY":
        raise ValueError("; ".join(state.mode_contract.get("errors", [])))
    state.phase = "DOD_FROZEN"
    return state


def register_continuation_plan(state, plan: dict[str, Any]):
    if _require_mode(state) != CONTINUATION:
        raise ValueError("continuation plan is only applicable in CONTINUATION mode")
    return base.register_continuation_plan(state, plan)


def record_continuation_coverage(state, payload: dict[str, Any]):
    if _require_mode(state) != CONTINUATION:
        raise ValueError("continuation coverage is only applicable in CONTINUATION mode")
    return base.record_continuation_coverage(state, payload)


def _append_generation_draft(state, text: str, stage: str):
    if state.generation_contract.get("status") != "READY": raise ValueError("generation contract not READY")
    if stage not in {"INITIAL", "REGENERATED", "COMPRESSED_FINAL"}: raise ValueError("writing modes support INITIAL, REGENERATED and COMPRESSED_FINAL stages")
    if stage == "INITIAL" and state.drafts: raise ValueError("initial draft already sealed")
    if stage == "REGENERATED" and not state.review.get("cycles"): raise ValueError("regeneration requires a prior scientific-editorial review cycle")
    if stage == "COMPRESSED_FINAL" and (state.review.get("saturation") or {}).get("status") != "PASS": raise ValueError("final compression requires review saturation PASS")
    record = seal_candidate(text, generation_contract=state.generation_contract, stage=stage, sequence=len(state.drafts) + 1)
    if stage == "REGENERATED":
        regenerations = state.review.get("regenerations", [])
        if not regenerations or regenerations[-1].get("to_digest") != record.get("digest"): raise ValueError("regenerated draft digest does not match latest regeneration record")
    state.drafts.append(record); state.provenance = {}; state.final_review = {}
    state.phase = "DRAFT_SEALED" if stage == "INITIAL" else ("REGENERATED_DRAFT_SEALED" if stage == "REGENERATED" else "FINAL_COMPRESSED_DRAFT_SEALED")
    return record


def _seal_review_candidate(state, text: str, stage: str):
    output = review_output(state.setup)
    if stage not in {"REVIEW_SOURCE", "REVISED_FINAL"}: raise ValueError("REVIEW mode supports REVIEW_SOURCE and REVISED_FINAL stages")
    digest = text_digest(text)
    if stage == "REVIEW_SOURCE":
        if state.drafts: raise ValueError("review source already sealed")
        expected = str(state.mode_contract.get("target_digest", ""))
        if expected and digest != expected: raise ValueError("review source does not match supplied review target")
    else:
        if output != "REPORT_AND_REVISED_TEXT": raise ValueError("REVISED_FINAL requires review_output=REPORT_AND_REVISED_TEXT")
        if not state.review.get("regenerations"): raise ValueError("revised final requires a documented regeneration")
        if state.review["regenerations"][-1].get("to_digest") != digest: raise ValueError("revised final digest does not match latest regeneration record")
    payload = {"sequence": len(state.drafts) + 1, "stage": stage, "digest": digest, "word_count": len((text or "").split()), "mode": REVIEW, "mode_contract_digest": state.mode_contract.get("digest", ""), "generation_contract_digest": state.generation_contract.get("contract_digest", ""), "reticulum_digest": state.reticulum.get("digest", ""), "status": "SEALED"}
    payload["record_digest"] = generation_digest(payload)
    state.drafts.append(payload); state.provenance = {}; state.final_review = {}; state.phase = "REVIEW_SOURCE_SEALED" if stage == "REVIEW_SOURCE" else "REVISED_FINAL_SEALED"
    return payload


def seal_draft(state, text: str, *, stage: str = "INITIAL"):
    mode = _require_mode(state)
    if state.mode_contract.get("status") != "READY": raise ValueError("mode contract not READY")
    if mode == CONTINUATION: return legacy_final.seal_draft(state, text, stage=stage)
    if mode == GREENFIELD: return _append_generation_draft(state, text, stage)
    return _seal_review_candidate(state, text, stage)


def record_review_cycle(state, record: dict[str, Any]):
    if not state.drafts: raise ValueError("review requires a sealed candidate")
    current = state.drafts[-1].get("digest")
    ok, errors = validate_review_cycle(record, expected_candidate_digest=current)
    if not ok: raise ValueError("; ".join(errors))
    cycles = list(state.review.get("cycles", [])); expected_cycle = len(cycles) + 1
    if int(record.get("cycle", 0)) != expected_cycle: raise ValueError(f"review cycle must be {expected_cycle}")
    stored = dict(record); stored["mode"] = _require_mode(state); stored["editorial_standard_digest"] = state.editorial_standard.get("digest", ""); cycles.append(stored)
    state.review["cycles"] = cycles; state.review["status"] = stored.get("status", "NOT_STARTED"); state.phase = "SCIENTIFIC_EDITORIAL_REVIEW"
    return stored


def record_regeneration(state, record: dict[str, Any]): return base.record_regeneration(state, record)


def record_review_saturation(state, receipt: dict[str, Any]):
    mode = _require_mode(state)
    if mode == REVIEW and review_output(state.setup) == "REPORT_ONLY":
        if not state.drafts or state.drafts[-1].get("stage") != "REVIEW_SOURCE": raise ValueError("diagnostic saturation requires sealed REVIEW_SOURCE")
        current = state.drafts[-1].get("digest"); errors = []
        if receipt.get("candidate_digest") != current: errors.append("diagnostic saturation bound to stale review target")
        if int(receipt.get("no_novelty_streak", 0)) < 10000: errors.append("diagnostic review requires 10000 consecutive no-new-finding probes")
        if int(receipt.get("no_improvement_without_degradation_streak", 0)) < 10000: errors.append("diagnostic review requires 10000 consecutive no-further-audit-improvement probes")
        if not state.review.get("cycles"): errors.append("diagnostic review cycle missing")
        stored = dict(receipt); stored["diagnostic_complete"] = not errors; stored["status"] = "PASS" if not errors else "FAIL"; stored["errors"] = errors
        state.review["saturation"] = stored; state.review["status"] = "DIAGNOSTIC_SATURATED" if not errors else "SATURATION_INCOMPLETE"; state.phase = "REVIEW_SATURATED" if not errors else "SCIENTIFIC_EDITORIAL_REVIEW"
        return {"status": stored["status"], "errors": errors}
    return base.record_review_saturation(state, receipt)


def audit_legal_text(state, text, *, reference_text=None, prior_texts=None, artifact_evidence=None):
    if not state.drafts: raise ValueError("candidate must be sealed before quality audit")
    if text_digest(text) != state.drafts[-1].get("digest"): raise ValueError("quality audit text does not match current sealed candidate")
    if artifact_evidence is not None: state.artifact_evidence = list(artifact_evidence)
    report = audit_chapter(text, reference_text=reference_text, prior_texts=prior_texts, accepted_setup=state.setup, claims=state.claim_ledger, sources=state.sources, artifact_evidence=state.artifact_evidence).record()
    report["mode"] = _require_mode(state); report["editorial_conformance"] = editorial_conformance(text, state.editorial_standard)
    if report["editorial_conformance"].get("status") == "FAIL": report["status"] = "FAIL"
    elif report["editorial_conformance"].get("status") == "REVIEW_REQUIRED" and report.get("status") == "PASS": report["status"] = "REVIEW_REQUIRED"
    state.quality = report; state.phase = "QUALITY_AUDIT"; return state.quality


def audit_candidate_chapter(state, text, *, reference_text=None, prior_texts=None, artifact_evidence=None): return audit_legal_text(state, text, reference_text=reference_text, prior_texts=prior_texts, artifact_evidence=artifact_evidence)

def record_simulation(state, receipt):
    if mode_spec(_require_mode(state), state.setup)["simulation_required"] is not True: raise ValueError("simulation receipt is not required for this mode")
    return base.record_simulation(state, receipt)
def record_compression(state, record):
    if mode_spec(_require_mode(state), state.setup)["compression_required"] is not True: raise ValueError("compression record is not required for this mode")
    result = base.record_compression(state, record); state.provenance = {}; state.final_review = {}; return result


def record_provenance(state, payload):
    mode = _require_mode(state); spec = mode_spec(mode, state.setup)
    if not state.drafts: raise ValueError("provenance requires a sealed work target")
    current = state.drafts[-1]; current_digest = str(current.get("digest", "")); expected_stage = "COMPRESSED_FINAL" if mode in {CONTINUATION, GREENFIELD} else ("REVISED_FINAL" if spec["revision_required"] else "REVIEW_SOURCE")
    if current.get("stage") != expected_stage: raise ValueError(f"provenance requires current stage {expected_stage}")
    if mode in {CONTINUATION, GREENFIELD} or spec["revision_required"]:
        if state.quality.get("status") != "PASS" or state.quality.get("candidate_digest") != current_digest: raise ValueError("final quality PASS bound to current candidate required before provenance")
    elif state.quality.get("candidate_digest") != current_digest: raise ValueError("diagnostic quality audit bound to review target required before provenance")
    if spec["source_coverage_must_close"] and state.source_intelligence.get("coverage_status") not in {"PASS", "NOT_REQUIRED"}: raise ValueError("claim/source coverage must be closed before provenance")
    if mode == CONTINUATION:
        coverage = (state.continuation or {}).get("coverage") or {}
        if coverage.get("status") != "PASS" or coverage.get("candidate_digest") != current_digest: raise ValueError("final continuation coverage PASS required before provenance")
    bundle = build_provenance_bundle(payload.get("entries", []), candidate_digest=current_digest, corpus_digest=provenance_digest(state.corpus), epistemic_units=state.epistemic_units, claim_ledger=state.claim_ledger, interaction=state.interaction, regenerations=state.review.get("regenerations", []), compression=state.compression if spec["compression_required"] else None)
    bundle["mode"] = mode; bundle["mode_contract_digest"] = state.mode_contract.get("digest", ""); bundle["editorial_standard_digest"] = state.editorial_standard.get("digest", ""); bundle["required_artifact_roles"] = sorted(required_artifact_roles(mode, state.setup)); bundle["digest"] = provenance_digest({k: v for k, v in bundle.items() if k != "digest"})
    ok, errors = provenance_gate(bundle, candidate_digest=current_digest, corpus_digest=provenance_digest(state.corpus))
    if not ok: raise ValueError("; ".join(errors))
    state.provenance = bundle; state.final_review = {}; state.phase = "PROVENANCE_COMPLETE"; return bundle


def record_final_review(state, payload): return legacy_final.record_final_review(state, payload)
def record_artifact(state, record):
    role = str(record.get("role", "")); required = required_artifact_roles(_require_mode(state), state.setup)
    if role in required:
        if state.final_review.get("status") != "PASS": raise ValueError("final severe review PASS required before final artifact materialization")
        if record.get("readback") != "PASS": raise ValueError(f"required final artifact {role} requires readback PASS")
    return base.record_artifact(state, record)

def _dynamic_artifact_gate(state):
    by_role = {str(a.get("role")): a for a in state.artifacts if a.get("role")}; errors=[]
    for role in sorted(required_artifact_roles(_require_mode(state), state.setup)):
        record=by_role.get(role)
        if not record: errors.append(f"required final artifact role missing: {role}")
        elif record.get("readback")!="PASS": errors.append(f"required final artifact readback failed: {role}")
    return not errors,errors

def _mode_contract_gate(state):
    return validate_mode_contract(state.mode_contract, mode=_require_mode(state), request=state.request, corpus=state.corpus, reticulum=state.reticulum, setup=state.setup, editorial_standard=state.editorial_standard, generation_contract=state.generation_contract)


def evaluate_completion(state):
    mode=_require_mode(state); reasons=[]; open_contra=[c for c in state.contradictions if c.get("blocking",True) and c.get("status","OPEN")!="RESOLVED"]
    if not all_dods_done(state.dod): reasons.append("not all blocking DoD are DONE")
    if int(state.metrics.get("dod_no_novelty_streak",0))<10000: reasons.append("M+10000 no-novelty evidence vs DoD not reached")
    if open_contra: reasons.append("blocking contradictions remain open")
    ok_boot,boot_errors=bootstrap_gate(state.admission); reasons.extend([] if ok_boot else boot_errors)
    if state.reticulum.get("status")!="PASS": reasons.append("validated epistemic reticulum is required")
    ok_ed,ed_errors=validate_editorial_standard(state.editorial_standard,mode=mode); reasons.extend([] if ok_ed else ed_errors)
    ok_mode,mode_errors=_mode_contract_gate(state); reasons.extend([] if ok_mode else mode_errors)
    ok_bib,bib_errors=bibliography_gate(state.bibliography); reasons.extend([] if ok_bib else bib_errors)
    bg=benchmark_gate(state.benchmark or None,required=any(d.get("kind")=="MONOGRAPHIC_EXTRAPOLATION" and d.get("blocking",True) for d in state.dod))
    if not bg["eligible"]: reasons.append("blind monograph benchmark integrity/coverage failed")
    current_digest=str(state.drafts[-1].get("digest","")) if state.drafts else ""
    if mode in {CONTINUATION,GREENFIELD}:
        ok_contract,contract_errors=generation_contract_valid(state.generation_contract,state.reticulum,state.setup); reasons.extend([] if ok_contract else contract_errors)
        stages={d.get("stage") for d in state.drafts}
        for needed in {"INITIAL","REGENERATED","COMPRESSED_FINAL"}:
            if needed not in stages: reasons.append(f"sealed {needed} draft is missing")
        if state.drafts and state.drafts[-1].get("stage")!="COMPRESSED_FINAL": reasons.append("current candidate is not COMPRESSED_FINAL")
        if mode==CONTINUATION:
            ok_cont,cont_errors=continuation_gate(state.continuation,generation_contract_digest=state.generation_contract.get("contract_digest"),candidate_digest=current_digest or None); reasons.extend([] if ok_cont else cont_errors)
        pre=str((state.review.get("saturation") or {}).get("candidate_digest","")); ok_rev,rev_errors=review_gate(state.review,expected_candidate_digest=pre or None,require_regeneration=True); reasons.extend([] if ok_rev else rev_errors)
        ok_comp,comp_errors=compression_valid(state.compression,expected_before_digest=pre or None,expected_after_digest=current_digest or None,generation_contract_digest=state.generation_contract.get("contract_digest"),strict=True); reasons.extend([] if ok_comp else comp_errors)
        ok_sim,sim_errors=validate_simulation_receipt(state.simulations,candidate_digest=current_digest or None,generation_contract_digest=state.generation_contract.get("contract_digest"),require_categories=True); reasons.extend([] if ok_sim else sim_errors)
        if state.quality.get("status")!="PASS" or state.quality.get("candidate_digest")!=current_digest: reasons.append("final quality PASS bound to current candidate required")
        if state.source_intelligence.get("coverage_status") not in {"PASS","NOT_REQUIRED"}: reasons.append("claim/source coverage is not closed")
    else:
        output=review_output(state.setup)
        if not state.drafts or state.drafts[0].get("stage")!="REVIEW_SOURCE": reasons.append("sealed REVIEW_SOURCE is required")
        if not state.review.get("cycles",[]): reasons.append("scientific/content/editorial review cycle is required")
        if output=="REPORT_ONLY":
            sat=state.review.get("saturation") or {}
            if sat.get("status")!="PASS" or sat.get("diagnostic_complete") is not True: reasons.append("diagnostic review saturation is incomplete")
            if state.quality.get("candidate_digest")!=current_digest: reasons.append("diagnostic quality audit bound to review target required")
        else:
            if not state.drafts or state.drafts[-1].get("stage")!="REVISED_FINAL": reasons.append("REVISED_FINAL is required by review_output")
            if not state.review.get("regenerations"): reasons.append("documented revision is required")
            pre=str((state.review.get("saturation") or {}).get("candidate_digest","")); ok_rev,rev_errors=review_gate(state.review,expected_candidate_digest=pre or current_digest or None,require_regeneration=True); reasons.extend([] if ok_rev else rev_errors)
            if state.quality.get("status")!="PASS" or state.quality.get("candidate_digest")!=current_digest: reasons.append("revised final quality PASS required")
            if state.source_intelligence.get("coverage_status") not in {"PASS","NOT_REQUIRED"}: reasons.append("claim/source coverage is not closed for revised final")
    corpus_digest=provenance_digest(state.corpus); ok_prov,prov_errors=provenance_gate(state.provenance,candidate_digest=current_digest or None,corpus_digest=corpus_digest); reasons.extend([] if ok_prov else prov_errors)
    normative=provenance_digest({"sources":state.sources,"claims":state.claim_ledger,"source_intelligence":state.source_intelligence,"contradictions":state.contradictions}); ok_final,final_errors=final_review_gate(state.final_review,candidate_digest=current_digest or None,corpus_digest=corpus_digest,provenance_digest=(state.provenance or {}).get("digest"),normative_frame_digest=normative); reasons.extend([] if ok_final else final_errors)
    ok_art,art_errors=_dynamic_artifact_gate(state); reasons.extend([] if ok_art else art_errors)
    if (state.node_integrity or {}).get("status")!="PASS": reasons.extend((state.node_integrity or {}).get("errors") or ["session integrity not verified"])
    state.completion={"eligible":not reasons,"reason":"PASS" if not reasons else "; ".join(dict.fromkeys(reasons)),"mode":mode,"mode_contract_gate":{"eligible":ok_mode,"errors":mode_errors},"editorial_standard_gate":{"eligible":ok_ed,"errors":ed_errors},"bootstrap_gate":{"eligible":ok_boot,"errors":boot_errors},"bibliography_gate":{"eligible":ok_bib,"errors":bib_errors},"final_artifact_gate":{"eligible":ok_art,"errors":art_errors}}
    state.phase="COMPLETE" if state.completion["eligible"] else "VALIDATING"; state.interaction={**(state.interaction or {}),"card":interaction_card("COMPLETE" if state.completion["eligible"] else "HUMAN_DECISION_REQUIRED",summary="Lavorazione completa; scegli cosa fare dopo." if state.completion["eligible"] else "Restano blocker prima della consegna.",choices=["APRI ARTEFATTI","RICHIEDI MODIFICHE","NUOVO LAVORO","ALTRO"] if state.completion["eligible"] else None),"status":"READY"}; return state
