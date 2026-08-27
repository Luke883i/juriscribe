"""Explicit public runtime composition for Juriscribe v1 candidate.

Recovery export is routed as MATERIALIZATION. Resume/import remains a bootstrap and
persisted-session concern and therefore is not an ordinary orchestration route.
"""
from __future__ import annotations

import importlib
from typing import Callable

SCHEMA = "juriscribe-runtime-router/v1"

ROUTES: dict[str, tuple[str, str]] = {
    "apply_setup": ("runtime_cc_v2", "apply_setup"),
    "audit_candidate_chapter": ("generation_governance", "audit_candidate_chapter"),
    "audit_legal_text": ("generation_governance", "audit_legal_text"),
    "create_recovery_bundle": ("recovery", "create_recovery_bundle"),
    "evaluate_completion": ("consolidation_completion", "evaluate_completion"),
    "freeze_dods": ("runtime_v13", "freeze_dods"),
    "ingest_and_mine": ("runtime_v13", "ingest_and_mine"),
    "record_artifact": ("runtime_autopilot", "record_artifact"),
    "record_compression": ("multimode", "record_compression"),
    "record_continuation_coverage": ("multimode", "record_continuation_coverage"),
    "record_final_review": ("runtime_v11_review", "record_final_review"),
    "record_natural_language_interpretation": ("runtime_autopilot", "record_natural_language_interpretation"),
    "record_provenance": ("runtime_v11_review", "record_provenance"),
    "record_regeneration": ("multimode", "record_regeneration"),
    "record_review_cycle": ("runtime_v11_review", "record_review_cycle"),
    "record_review_saturation": ("multimode", "record_review_saturation"),
    "record_simulation": ("runtime_cc_v2", "record_simulation"),
    "register_continuation_plan": ("multimode", "register_continuation_plan"),
    "register_plagiarism_reference": ("generation_governance", "register_plagiarism_reference"),
    "register_semantic_mining": ("runtime_v13", "register_semantic_mining"),
    "resolve_natural_language_interpretation": ("runtime_autopilot", "resolve_natural_language_interpretation"),
    "seal_draft": ("runtime_autopilot", "seal_draft"),
    "select_mode": ("runtime_v13", "select_mode"),
    "calibrate_refactoring": ("runtime_cc_v2", "calibrate_refactoring"),
    "consolidation_gate": ("runtime_cc_v2", "consolidation_gate"),
    "record_consolidation_saturation": ("runtime_cc_v2", "record_consolidation_saturation"),
    "register_refactoring_plan": ("runtime_cc_v2", "register_refactoring_plan"),
    "seal_refined_candidate": ("runtime_cc_v2", "seal_refined_candidate"),
}


def route_owner(operation: str) -> str:
    try:
        module_name, attribute = ROUTES[str(operation)]
    except KeyError as exc:
        raise KeyError(f"unknown public runtime operation: {operation}") from exc
    return f"juriscribe.{module_name}.{attribute}"


def resolve_operation(operation: str) -> Callable:
    try:
        module_name, attribute = ROUTES[str(operation)]
    except KeyError as exc:
        raise KeyError(f"unknown public runtime operation: {operation}") from exc
    module = importlib.import_module(f".{module_name}", __package__)
    target = getattr(module, attribute, None)
    if not callable(target):
        raise RuntimeError(f"runtime route target is not callable: {route_owner(operation)}")
    return target


def routing_manifest() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "operations": {name: route_owner(name) for name in sorted(ROUTES)},
        "authority": "EXPLICIT_COMPOSITION_ONLY",
    }
