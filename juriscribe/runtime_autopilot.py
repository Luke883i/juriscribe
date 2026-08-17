from __future__ import annotations

from . import artifact_governance as _artifact
from . import multimode as _multimode
from .artifact_autopilot import store_candidate_text
from .conversation_contract import (
    initialize_pipeline_lock,
    record_natural_language_interpretation,
    refresh_pipeline_lock_artifact_set,
    resolve_natural_language_interpretation,
)


def select_mode(state, mode: str):
    result = _multimode.select_mode(state, mode)
    initialize_pipeline_lock(state)
    return result


def apply_setup(state, overrides=None):
    result = _artifact.apply_setup(state, overrides)
    refresh_pipeline_lock_artifact_set(state)
    return result


def freeze_dods(state, additional_dods=None):
    result = _artifact.freeze_dods(state, additional_dods)
    refresh_pipeline_lock_artifact_set(state)
    return result


def seal_draft(state, text: str, *, stage: str = "INITIAL"):
    record = _artifact.seal_draft(state, text, stage=stage)
    store_candidate_text(state, str(record.get("digest") or ""), text)
    return record


def record_artifact(state, record):
    return _artifact.record_artifact(state, record)


__all__ = [
    "select_mode",
    "apply_setup",
    "freeze_dods",
    "seal_draft",
    "record_artifact",
    "record_natural_language_interpretation",
    "resolve_natural_language_interpretation",
]
