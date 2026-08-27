"""Projection-only three-line control shell for Juriscribe v1.

Every render answers WHERE / DONE / NEXT / HOW / DO. The projection also carries
all session-chat downloadable DOCX descriptors for the host adapter; the text
surface remains bounded to three lines.
"""
from __future__ import annotations

import re
from typing import Any

from .chat_delivery import build_session_chat_docx_manifest
from .continuity import RECOVERY_ACTION, project_iteration
from .interaction import FREE_CHOICE, SCHEMA as INTERACTION_SCHEMA, mode_entry_card, phase_choices
from .modes import normalize_mode

SCHEMA = "juriscribe-chat-shell/v2"
AUTHORITY = "PROJECTION_ONLY"
MAX_LINES = 3
MAX_LINE_CHARS = 220
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
USER_PHASES = frozenset({
    "TERMS_PRESENTED",
    "PROBE_REQUIRED",
    "PROBED",
    "INITIALIZE_REQUIRED",
    "MODE_SELECTION_REQUIRED",
    "MODE_SELECTED",
    "USER_SETUP_REQUIRED",
    "HUMAN_DECISION_REQUIRED",
    "COMPLETE",
})
INPUT_PHASES = USER_PHASES - {"COMPLETE"}
DONE_BUDGET = 58
NEXT_BUDGET = 58
HOW_BUDGET = 72
CHOICE_BUDGET = 34


def _text(value: Any, limit: int = MAX_LINE_CHARS) -> str:
    raw = ANSI_RE.sub("", str(value or ""))
    safe = " ".join("".join(ch if ch.isprintable() else " " for ch in raw).split())
    if len(safe) <= limit:
        return safe
    return safe[: max(0, limit - 1)].rstrip() + "…"


def _get(state: Any, name: str, default=None):
    return state.get(name, default) if isinstance(state, dict) else getattr(state, name, default)


def _mode(state: Any) -> str:
    raw = _get(state, "mode", "")
    if not str(raw or "").strip():
        return ""
    try:
        return normalize_mode(raw)
    except ValueError:
        return _text(raw, 64).upper()


def _current_card(state: Any) -> dict[str, Any]:
    interaction = _get(state, "interaction", {}) or {}
    if not isinstance(interaction, dict):
        return {}
    return dict(interaction.get("card") or {})


def _phase_bound_dynamic_card(state: Any, phase: str) -> dict[str, Any]:
    card = _current_card(state)
    choices = [str(item) for item in card.get("choices") or []]
    if (
        card.get("schema") == INTERACTION_SCHEMA
        and str(card.get("phase") or "").upper() == phase
        and card.get("free_input_allowed") is True
        and FREE_CHOICE in choices
    ):
        return card
    return {}


def _card(state: Any, phase: str, mode: str) -> dict[str, Any]:
    if phase == "MODE_SELECTED" and mode:
        try:
            return mode_entry_card(mode)
        except ValueError:
            return {}
    if phase == "HUMAN_DECISION_REQUIRED":
        dynamic = _phase_bound_dynamic_card(state, phase)
        if dynamic:
            return dynamic
    if phase in USER_PHASES:
        return {
            "phase": phase,
            "summary": "",
            "choices": phase_choices(phase),
            "blocking": phase != "COMPLETE",
        }
    return {}


def _choices(card: dict[str, Any]) -> list[str]:
    selected: list[str] = []
    for item in card.get("choices") or []:
        label = _text(item, CHOICE_BUDGET)
        if label and label != FREE_CHOICE and label not in selected:
            selected.append(label)
    return selected[:3]


def project_chat_artifacts(state: Any) -> dict[str, Any]:
    """Projection-only host payload for all retained session DOCX downloads."""
    return build_session_chat_docx_manifest(state)


def project_chat_shell(state: Any) -> dict[str, Any]:
    iteration = project_iteration(state)
    where = iteration["where"]
    phase = where["phase"]
    mode = _mode(state)
    card = _card(state, phase, mode)
    artifact_manifest = project_chat_artifacts(state)
    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "phase": phase,
        "mode": mode,
        "stage": where["stage"],
        "status": where["status"],
        "checkpoint_id": iteration["checkpoint_id"],
        "done": iteration["done"]["summary"],
        "next": iteration["next"]["summary"],
        "how": iteration["next"]["how"],
        "choices": _choices(card),
        "utilities": [RECOVERY_ACTION, "STATO", "ARTEFATTI", "AIUTO", FREE_CHOICE],
        "recovery_ready": iteration["recovery"]["resume_ready"],
        "artifact_manifest_status": artifact_manifest.get("status"),
        "artifact_count": int(artifact_manifest.get("artifact_count") or 0),
        "downloadable_artifacts": list(artifact_manifest.get("artifacts") or []),
        "artifact_projection_errors": list(artifact_manifest.get("errors") or []),
    }


def render_chat_shell(state: Any) -> str:
    projection = project_chat_shell(state)
    line1 = _text(
        f"JURISCRIBE> WHERE phase={_text(projection['phase'], 42)} | mode={_text(projection['mode'] or '-', 34)} | "
        f"stage={_text(projection['stage'], 22)} | {projection['status']} | cp={projection['checkpoint_id'][3:11]}"
    )
    line2 = (
        f"DONE> {_text(projection['done'], DONE_BUDGET)} | "
        f"NEXT> {_text(projection['next'], NEXT_BUDGET)} | "
        f"HOW> {_text(projection['how'], HOW_BUDGET)}"
    )
    recovery = "[R] RECUPERO" if projection["recovery_ready"] else "[R] RECUPERO(!)"
    artifact_control = f"[A] ARTEFATTI({projection['artifact_count']})"
    core = f"DO> {recovery}  [S] STATO  {artifact_control}  [?] AIUTO  […] ALTRO"
    options = [f"[{index}] {label}" for index, label in enumerate(projection["choices"], 1)]
    line3 = core if not options else _text(core + "  |  " + "  ".join(options))
    return "\n".join((line1, line2, line3))


def validate_rendered_shell(text: str) -> tuple[bool, list[str]]:
    lines = str(text or "").splitlines()
    errors: list[str] = []
    if len(lines) != MAX_LINES:
        errors.append("chat shell must render exactly three lines")
    if any(len(line) > MAX_LINE_CHARS for line in lines):
        errors.append("chat shell line too long")
    if not lines or not lines[0].startswith("JURISCRIBE> WHERE "):
        errors.append("chat shell WHERE line missing")
    if len(lines) < 2 or not lines[1].startswith("DONE> "):
        errors.append("chat shell DONE line missing")
    if len(lines) < 2 or " | NEXT> " not in lines[1]:
        errors.append("chat shell NEXT segment missing")
    if len(lines) < 2 or " | HOW> " not in lines[1]:
        errors.append("chat shell HOW segment missing")
    if len(lines) < 3 or not lines[2].startswith("DO> "):
        errors.append("chat shell DO line missing")
    if len(lines) < 3 or "[R] RECUPERO" not in lines[2]:
        errors.append("chat shell recovery action missing")
    if len(lines) < 3 or "[S] STATO" not in lines[2]:
        errors.append("chat shell status action missing")
    if len(lines) < 3 or "[A] ARTEFATTI(" not in lines[2]:
        errors.append("chat shell downloadable-artifact control missing")
    if len(lines) < 3 or "[…] ALTRO" not in lines[2]:
        errors.append("chat shell free-input path missing")
    return not errors, errors
