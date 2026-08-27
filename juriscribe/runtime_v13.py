"""Common multimode runtime kernel layered over the current specialist engines.

The v13 overlay adds only cross-mode invariants: mode-specific input firewalls,
shared downstream staleness invalidation and canonical mode-entry interaction.
All substantive generation/review/C&C proof semantics continue to delegate to the
current runtime_cc_v2 stack.
"""
from __future__ import annotations

from typing import Any

from . import runtime_cc_v2 as _runtime
from .runtime_cc_v2 import *  # noqa: F401,F403
from .interaction import mode_entry_card
from .mode_runtime import (
    MATERIAL_INPUT_CHANGED,
    SEMANTIC_MODEL_CHANGED,
    assert_input_transition,
    invalidate_downstream,
    validate_mode_corpus,
)
from .modes import normalize_mode

RUNTIME_PROFILE = "JURISCRIBE_COMMON_MODE_RUNTIME_V1"


def _require_valid_corpus(state, *, require_minimum: bool) -> None:
    mode = normalize_mode(state.mode)
    ok, errors = validate_mode_corpus(mode, state.corpus, require_minimum=require_minimum)
    if not ok:
        raise ValueError("mode input contract failed: " + "; ".join(errors))


def select_mode(state, mode: str):
    result = _runtime.select_mode(state, mode)
    state.interaction = {
        **(state.interaction or {}),
        "card": mode_entry_card(state.mode),
        "status": "READY",
    }
    return result


def ingest_and_mine(state, text, *, source_id, chapter=None, source_record=None, role=None):
    selected_role = assert_input_transition(state, source_id=source_id, role=role)
    result = _runtime.ingest_and_mine(
        state,
        text,
        source_id=source_id,
        chapter=chapter,
        source_record=source_record,
        role=selected_role,
    )
    invalidate_downstream(
        state,
        boundary=MATERIAL_INPUT_CHANGED,
        reason=f"{normalize_mode(state.mode)} material input changed; semantic and downstream evidence must be regenerated",
    )
    return result


def register_semantic_mining(state, units: list[dict[str, Any]], relations: list[dict[str, Any]]):
    _require_valid_corpus(state, require_minimum=True)
    invalidate_downstream(
        state,
        boundary=SEMANTIC_MODEL_CHANGED,
        reason=f"{normalize_mode(state.mode)} semantic model changed; setup and downstream evidence must be regenerated",
    )
    return _runtime.register_semantic_mining(state, units, relations)


def freeze_dods(state, additional_dods=None):
    _require_valid_corpus(state, require_minimum=True)
    return _runtime.freeze_dods(state, additional_dods)
