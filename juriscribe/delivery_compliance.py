from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .conversation_contract import final_chapter_inference_trace_gate, get_pipeline_lock, pipeline_lock_gate
from .modes import CONTINUATION, GREENFIELD, REVIEW, required_artifact_roles, review_output

SCHEMA = "juriscribe-delivery-compliance-inventory/v1"
PROFILE_ID = "JURISCRIBE_MECHANICAL_DELIVERY_COMPLIANCE_V1"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOSSIER_ROLES = {"evidence_dossier", "source_register", "inference_register", "transformation_ledger"}
NARRATIVE_ROLES = {"final_chapter", "final_legal_text", "revised_legal_text", "review_report"}


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _present(value: Any) -> bool:
    return value not in (None, "", [], {}, ())


def _status_ok(value: Any, accepted: set[str]) -> bool:
    return isinstance(value, dict) and str(value.get("status") or "").upper() in accepted


def _node(identifier: str, title: str, purpose: str, *, blocking: bool, applicable: bool, satisfied: bool, evidence: Any = None) -> dict[str, Any]:
    status = "NOT_APPLICABLE" if not applicable else ("PASS" if satisfied else ("FAIL" if blocking else "OPTIONAL_MISSING"))
    record = {"id": identifier, "title": title, "purpose": purpose, "blocking": bool(blocking), "applicable": bool(applicable), "status": status}
    if isinstance(evidence, dict):
        for key in ("status", "coverage_status", "standard_id", "policy_id", "profile", "schema"):
            if evidence.get(key) not in (None, ""):
                record[f"evidence_{key}"] = evidence.get(key)
    elif isinstance(evidence, list):
        record["evidence_count"] = len(evidence)
    elif evidence not in (None, ""):
        record["evidence_present"] = True
    return record


def build_epistemic_inventory(state: Any) -> list[dict[str, Any]]:
    s = _payload(state)
    mode = str(s.get("mode") or "").upper()
    setup = s.get("setup") or {}
    strategy = s.get("strategy") or {}
    quality = s.get("quality") or {}
    review = s.get("review") or {}
    continuation = s.get("continuation") or {}
    source_intel = s.get("source_intelligence") or {}
    generation = s.get("generation_contract") or {}
    language = get_pipeline_lock(s)
    governed_v100 = bool(language)
    narrative = mode in {CONTINUATION, GREENFIELD} or (mode == REVIEW and review_output(setup) == "REPORT_AND_REVISED_TEXT")
    has_claims = bool(s.get("claim_ledger") or [])
    source_coverage = str(source_intel.get("coverage_status") or "").upper()
    bibliography = s.get("bibliography") or {}
    plagiarism = quality.get("plagiarism") or {}
    generation_config = generation.get("generation_configuration") or setup.get("generation_configuration") or {}
    compression = s.get("compression") or {}
    simulations = s.get("simulations") or {}
    provenance = s.get("provenance") or {}
    expected_doc_roles = sorted(set(required_artifact_roles(mode, setup)) - {"session_dashboard"}) if mode else []
    autopilot = strategy.get("standard_artifact_autopilot") or {}
    auto_ok = (
        str(autopilot.get("status") or "").upper() == "PASS"
        and autopilot.get("runtime_owned") is True
        and sorted(autopilot.get("required_roles") or []) == expected_doc_roles
        and sorted(autopilot.get("materialized_roles") or []) == expected_doc_roles
    )
    lock_ok = True
    if governed_v100:
        lock_ok, _ = pipeline_lock_gate(s)

    rows = [
        _node("mode_contract", "Contratto di modalità", "Blocca modalità, output primario e requisiti del lavoro.", blocking=True, applicable=bool(mode), satisfied=_status_ok(s.get("mode_contract") or {}, {"READY", "PASS"}), evidence=s.get("mode_contract") or {}),
        _node("editorial_standard", "Standard editoriale", "Definisce i criteri giuridico-editoriali applicabili al prodotto.", blocking=True, applicable=bool(mode), satisfied=_status_ok(s.get("editorial_standard") or {}, {"READY", "PASS"}), evidence=s.get("editorial_standard") or {}),
        _node("atomic_mining", "Mining atomico", "Materializza le unità epistemiche e i concetti su cui opera la generazione/review.", blocking=True, applicable=bool(mode), satisfied=bool(s.get("epistemic_units") or []), evidence=s.get("epistemic_units") or []),
        _node("epistemic_reticulum", "Reticolo epistemico", "Vincola connessioni, dipendenze, locator e struttura semantica.", blocking=True, applicable=bool(mode), satisfied=_status_ok(s.get("reticulum") or {}, {"PASS"}), evidence=s.get("reticulum") or {}),
        _node("claim_ledger", "Claim ledger", "Inventaria le proposizioni materiali da supportare, qualificare o confutare.", blocking=True, applicable=bool(mode), satisfied=has_claims, evidence=s.get("claim_ledger") or []),
        _node("artifact_evidence", "Registro delle evidenze", "Lega claim, fonti, locator e artefatti finali.", blocking=has_claims, applicable=has_claims, satisfied=bool(s.get("artifact_evidence") or []), evidence=s.get("artifact_evidence") or []),
        _node("source_register_logic", "Fonti e source intelligence", "Dimostra copertura, autorità e uso effettivo delle fonti.", blocking=True, applicable=bool(mode), satisfied=bool(s.get("sources") or []) or source_coverage == "NOT_REQUIRED", evidence={"coverage_status": source_coverage}),
        _node("bibliography", "Bibliografia", "Registra la componente bibliografica quando disponibile o necessaria.", blocking=False, applicable=True, satisfied=bool(bibliography.get("available") is False or bibliography.get("entries") or bibliography.get("status") in {"PASS", "NOT_AVAILABLE", "NOT_REQUIRED"}), evidence=bibliography),
        _node("inference_structure", "Struttura inferenziale", "Rende verificabili premesse, ponti inferenziali, conclusioni e falsificatori.", blocking=has_claims, applicable=has_claims, satisfied=has_claims and bool(s.get("reticulum") or {}), evidence=s.get("claim_ledger") or []),
        _node("generation_contract", "Contratto di generazione", "Lega configurazione accettata, reticolo e candidato finale.", blocking=narrative, applicable=narrative, satisfied=_status_ok(generation, {"READY", "PASS"}), evidence=generation),
        _node("generation_configuration", "Configurazione accettata", "Vincola abstract, concetti chiave e lunghezza del testo generato.", blocking=narrative and bool(generation.get("governance_profile")), applicable=narrative and bool(generation.get("governance_profile")), satisfied=_status_ok(generation_config, {"READY", "PASS"}), evidence=generation_config),
        _node("continuation_plan", "Piano di continuazione", "Identifica la frontiera da sviluppare e ciò che deve essere preservato.", blocking=mode == CONTINUATION, applicable=mode == CONTINUATION, satisfied=_status_ok(continuation.get("plan") or {}, {"PASS"}), evidence=continuation.get("plan") or {}),
        _node("continuation_coverage", "Copertura di continuazione", "Dimostra copertura del piano e controllo di duplicazioni/lacune.", blocking=mode == CONTINUATION, applicable=mode == CONTINUATION, satisfied=_status_ok(continuation.get("coverage") or {}, {"PASS"}) or str(continuation.get("status") or "").upper() == "PASS", evidence=continuation.get("coverage") or {}),
        _node("scientific_editorial_review", "Review scientifica ed editoriale", "Registra finding, rigenerazioni e saturazione prima della consegna.", blocking=True, applicable=bool(mode), satisfied=bool(review.get("cycles") or []) and str(review.get("status") or "").upper() not in {"", "NOT_STARTED", "FAIL", "SATURATION_INCOMPLETE"}, evidence=review),
        _node("quality_audit", "Audit di qualità", "Verifica contenuto, fonti, logica, forma e conformità del candidato corrente.", blocking=True, applicable=bool(mode), satisfied=str(quality.get("status") or "").upper() == "PASS", evidence=quality),
        _node("anti_plagiarism", "Controllo anti-plagio", "Dimostra assenza di overlap proibito nel corpus runtime-visible dichiarato.", blocking=narrative and bool(generation.get("governance_profile")), applicable=narrative and bool(generation.get("governance_profile")), satisfied=str(plagiarism.get("status") or "").upper() == "PASS", evidence=plagiarism),
        _node("simulations", "Simulazioni avverse/favorevoli", "Testa edge case e failure modes sul candidato prima della consegna.", blocking=mode in {CONTINUATION, GREENFIELD}, applicable=mode in {CONTINUATION, GREENFIELD}, satisfied=_present(simulations) and str(simulations.get("status") or "PASS").upper() != "FAIL", evidence=simulations),
        _node("compression", "Compressione finale", "Dimostra la compressione lossless e il binding al candidato finale.", blocking=mode in {CONTINUATION, GREENFIELD}, applicable=mode in {CONTINUATION, GREENFIELD}, satisfied=_present(compression) and str(compression.get("status") or "PASS").upper() != "FAIL", evidence=compression),
        _node("provenance", "Provenance", "Ricostruisce fonti, trasformazioni, decisioni e derivazione del prodotto.", blocking=True, applicable=bool(mode), satisfied=_present(provenance), evidence=provenance),
        _node("final_severe_review", "Review finale severa", "Ultimo controllo circostanziato prima della materializzazione e release.", blocking=True, applicable=bool(mode), satisfied=_status_ok(s.get("final_review") or {}, {"PASS"}), evidence=s.get("final_review") or {}),
        _node("natural_language_pipeline", "Contratto conversazionale", "Impedisce che locuzioni naturali cambino implicitamente modalità, pipeline o set artefatti.", blocking=governed_v100, applicable=governed_v100, satisfied=lock_ok, evidence=language),
        _node("standard_artifact_autopilot", "Autopilot artefatti standard", "Dimostra che il runtime ha materializzato esattamente il set canonico senza dipendere dal browser/assistant.", blocking=governed_v100, applicable=governed_v100, satisfied=auto_ok, evidence=autopilot),
    ]
    return rows


def _role_dependencies(mode: str, role: str, setup: dict[str, Any]) -> list[str]:
    common = ["mode_contract", "editorial_standard", "atomic_mining", "epistemic_reticulum", "claim_ledger", "source_register_logic", "provenance", "final_severe_review"]
    dossier = {
        "evidence_dossier": common + ["artifact_evidence", "inference_structure"],
        "source_register": common + ["source_register_logic"],
        "inference_register": common + ["inference_structure"],
        "transformation_ledger": common + ["scientific_editorial_review"],
    }
    if role in dossier: return list(dict.fromkeys(dossier[role]))
    if role == "final_chapter": return list(dict.fromkeys(common + ["artifact_evidence", "inference_structure", "generation_contract", "generation_configuration", "continuation_plan", "continuation_coverage", "scientific_editorial_review", "quality_audit", "anti_plagiarism", "simulations", "compression", "natural_language_pipeline", "standard_artifact_autopilot"]))
    if role == "final_legal_text": return list(dict.fromkeys(common + ["artifact_evidence", "inference_structure", "generation_contract", "generation_configuration", "scientific_editorial_review", "quality_audit", "anti_plagiarism", "simulations", "compression", "natural_language_pipeline", "standard_artifact_autopilot"]))
    if role == "revised_legal_text": return list(dict.fromkeys(common + ["artifact_evidence", "inference_structure", "generation_contract", "generation_configuration", "scientific_editorial_review", "quality_audit", "anti_plagiarism", "natural_language_pipeline", "standard_artifact_autopilot"]))
    if role in {"review_report", "review_findings_register"}: return list(dict.fromkeys(common + ["artifact_evidence", "inference_structure", "scientific_editorial_review", "quality_audit", "natural_language_pipeline", "standard_artifact_autopilot"]))
    if role == "session_dashboard": return list(dict.fromkeys(common + ["scientific_editorial_review"]))
    return common


def build_delivery_compliance_inventory(state: Any) -> dict[str, Any]:
    s = _payload(state)
    mode = str(s.get("mode") or "").upper()
    language = get_pipeline_lock(s)
    governed_v100 = bool(language)
    expected = sorted(required_artifact_roles(mode, s.get("setup") or {})) if mode else []
    by_role = {str(item.get("role") or ""): item for item in s.get("artifacts") or [] if item.get("role")}
    epistemic = build_epistemic_inventory(s)
    epi_by_id = {row["id"]: row for row in epistemic}
    material: list[dict[str, Any]] = []
    blocking_errors: list[str] = []
    generation_governed = bool((s.get("generation_contract") or {}).get("governance_profile"))
    trace_ok, trace_errors = final_chapter_inference_trace_gate(s)

    for role in expected:
        artifact = by_role.get(role) or {}
        is_dashboard = role == "session_dashboard"
        deps = _role_dependencies(mode, role, s.get("setup") or {})
        dep_failures = [dep for dep in deps if epi_by_id.get(dep, {}).get("blocking") and epi_by_id.get(dep, {}).get("applicable") and epi_by_id.get(dep, {}).get("status") != "PASS"]
        artifact_ok = bool(artifact)
        if artifact_ok:
            if is_dashboard:
                artifact_ok = str(artifact.get("delivery_class") or "").upper() == "SURFACE" and Path(str(artifact.get("path") or "")).suffix.lower() == ".html"
            else:
                artifact_ok = (
                    str(artifact.get("delivery_class") or "").upper() == "ATTACH"
                    and Path(str(artifact.get("path") or "")).suffix.lower() == ".docx"
                    and str(artifact.get("media_type") or DOCX_MIME) == DOCX_MIME
                    and artifact.get("readback") == "PASS"
                )
                if governed_v100: artifact_ok = artifact_ok and artifact.get("auto_materialized_by_runtime") is True
        if role in NARRATIVE_ROLES and artifact and generation_governed:
            proof = artifact.get("artifact_generation_governance") or {}
            if proof.get("status") != "PASS": artifact_ok = False
        if role in DOSSIER_ROLES and artifact and governed_v100:
            semantic_proof = artifact.get("semantic_materialization") or {}
            if semantic_proof.get("status") != "PASS": artifact_ok = False
        if role == "final_chapter" and governed_v100 and not trace_ok:
            artifact_ok = False
            dep_failures.extend(["final_chapter_inference_trace"] + list(trace_errors))
        eligible = artifact_ok and not dep_failures
        row = {
            "role": role, "kind": "HTML_SURFACE" if is_dashboard else "DOCX_ATTACHMENT",
            "artifact_present": bool(artifact), "artifact_contract_pass": bool(artifact_ok),
            "dependency_ids": deps, "failed_dependency_ids": sorted(set(dep_failures)),
            "eligible_for_delivery": bool(eligible),
            "release_placement": "SESSION_DASHBOARD_SURFACE" if is_dashboard else "SESSION_CHAT_TAIL",
        }
        material.append(row)
        if not eligible:
            blocking_errors.append(f"delivery compliance failed for {role}: " + (", ".join(row["failed_dependency_ids"]) if row["failed_dependency_ids"] else "artifact contract"))

    epistemic_failures = [row["id"] for row in epistemic if row["blocking"] and row["applicable"] and row["status"] != "PASS"]
    blocking_errors.extend(f"blocking epistemic dependency not compliant: {identifier}" for identifier in epistemic_failures)
    blocking_errors = list(dict.fromkeys(blocking_errors))
    atomic_release = not blocking_errors
    inventory = {
        "schema": SCHEMA, "profile": PROFILE_ID, "mode": mode,
        "status": "LEGACY_NOT_APPLICABLE" if mode and not governed_v100 else ("PASS" if atomic_release else "FAIL"),
        "runtime_governed": governed_v100, "atomic_release": True,
        "release_authorized": bool(atomic_release) if governed_v100 else True,
        "expected_material_roles": expected, "material_artifacts": material, "epistemic_artifacts": epistemic,
        "blocking_errors": blocking_errors if governed_v100 else [],
        "withheld_roles": [] if (atomic_release or not governed_v100) else [row["role"] for row in material if not row["eligible_for_delivery"]],
        "logic": "No final attachment is released unless the complete applicable material+epistemic dependency graph is compliant.",
        "global_external_host_behavior_claim": False,
    }
    inventory["inventory_digest"] = _digest({k: v for k, v in inventory.items() if k != "inventory_digest"})
    return inventory


def delivery_compliance_gate(state: Any) -> tuple[bool, list[str]]:
    inventory = build_delivery_compliance_inventory(state)
    if inventory.get("status") == "LEGACY_NOT_APPLICABLE": return True, []
    return inventory.get("status") == "PASS" and inventory.get("release_authorized") is True, list(inventory.get("blocking_errors") or [])
