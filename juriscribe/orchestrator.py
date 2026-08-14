from __future__ import annotations

from typing import Any

from .convergence import completion_gate
from .mining import deep_mine
from .setup import propose_setup, accept_setup, parameter_dods
from .sources import validate_claim, research_plan


def mine_and_prepare(state, text: str, *, source_id: str, chapter: str | None = None, semantic_annotations: dict[str, Any] | None = None):
    state.mining = deep_mine(text, source_id=source_id, chapter=chapter, semantic_annotations=semantic_annotations)
    state.style_profile = dict(state.mining.get("style", {}))
    state.setup = propose_setup(state.mining, state.request)
    state.phase = "USER_SETUP_REQUIRED"
    return state


def apply_setup(state, overrides: dict[str, Any] | None = None):
    if state.setup.get("status") != "USER_SETUP_REQUIRED":
        raise ValueError("setup proposal is not ready")
    state.setup = accept_setup(state.setup, overrides)
    existing_non_param = [d for d in state.dod if d.get("kind") != "USER_PARAMETER"]
    state.dod = existing_non_param + parameter_dods(state.setup)
    state.phase = "DOD_DEFINITION"
    return state


def freeze_dods(state, additional_dods: list[dict[str, Any]] | None = None):
    if state.setup.get("status") != "ACCEPTED":
        raise ValueError("user setup must be accepted before DoD freeze")
    for dod in additional_dods or []:
        if not dod.get("id"):
            raise ValueError("DoD requires id")
        dod.setdefault("status", "OPEN")
        dod.setdefault("blocking", True)
        dod.setdefault("evidence", [])
        state.dod.append(dod)
    state.phase = "DOD_FROZEN"
    return state


def build_research_plan(state):
    state.source_intelligence["research_plan"] = research_plan(state.claim_ledger)
    state.source_intelligence["coverage_status"] = "PLANNED" if state.source_intelligence["research_plan"] else "NOT_REQUIRED"
    return state


def validate_claim_ledger(state) -> dict[str, list[str]]:
    errors = {}
    for claim in state.claim_ledger:
        ok, claim_errors = validate_claim(claim, state.sources, state.claim_ledger)
        if not ok:
            errors[claim.get("id", "UNKNOWN")] = claim_errors
    state.source_intelligence["coverage_status"] = "PASS" if not errors else "GAPS_OPEN"
    return errors


def evaluate_completion(state):
    state.completion = completion_gate(state.dod, state.metrics, state.contradictions)
    state.phase = "COMPLETE" if state.completion["eligible"] else "VALIDATING"
    return state
