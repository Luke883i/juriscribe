"""Projection-only three-line control shell for Juriscribe chat hosts.

This module owns no admission, mode, proof, completion, or artifact authority. It
compresses already-materialized runtime state into a stable conversational control
surface and deliberately treats autonomous runtime phases as non-interrupting.
"""
from __future__ import annotations

import re
from typing import Any

from .interaction import FREE_CHOICE, SCHEMA as INTERACTION_SCHEMA, mode_entry_card, phase_choices
from .modes import normalize_mode

SCHEMA = "juriscribe-chat-shell/v1"
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


def _text(value: Any, limit: int = MAX_LINE_CHARS) -> str:
    raw = ANSI_RE.sub("", str(value or ""))
    safe = " ".join("".join(ch if ch.isprintable() else " " for ch in raw).split())
    if len(safe) <= limit:
        return safe
    return safe[: max(0, limit - 1)].rstrip() + "…"


def _get(state: Any, name: str, default=None):
    return state.get(name, default) if isinstance(state, dict) else getattr(state, name, default)


def _phase(state: Any) -> str:
    return _text(_get(state, "phase", "UNKNOWN"), 64).upper() or "UNKNOWN"


def _mode(state: Any) -> str:
    raw = _get(state, "mode", "")
    if not str(raw or "").strip():
        return ""
    try:
        return normalize_mode(raw)
    except ValueError:
        # Fail readable without granting validity to an unknown serialized mode.
        return _text(raw, 64).upper()


def _completion_eligible(state: Any) -> bool:
    completion = _get(state, "completion", {}) or {}
    return bool(completion.get("eligible")) if isinstance(completion, dict) else False


def _current_card(state: Any) -> dict[str, Any]:
    interaction = _get(state, "interaction", {}) or {}
    if not isinstance(interaction, dict):
        return {}
    return dict(interaction.get("card") or {})


def _phase_bound_dynamic_card(state: Any, phase: str) -> dict[str, Any]:
    """Accept dynamic copy only at the explicit human-decision boundary.

    Workspace integrity validates persisted state before public CLI reads it. The
    shell therefore checks only the projection boundary (schema/phase/free path)
    instead of creating a second semantic-proof or digest authority.
    """
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


def _status(state: Any, phase: str) -> str:
    if _completion_eligible(state) or phase == "COMPLETE":
        return "COMPLETE"
    if phase in INPUT_PHASES:
        return "INPUT"
    return "WORKING"


def _next_text(phase: str, card: dict[str, Any], status: str) -> str:
    if status == "COMPLETE":
        return "Lavoro completato. Apri gli artefatti oppure richiedi modifiche."
    if phase in {"MODE_SELECTED", "HUMAN_DECISION_REQUIRED"} and card.get("summary"):
        return _text(card["summary"], 170)
    defaults = {
        "TERMS_PRESENTED": "Leggi i termini e usa I ACCEPT solo se vuoi procedere.",
        "PROBE_REQUIRED": "Verifica le capability dell’host.",
        "PROBED": "Inizializza la sessione Juriscribe.",
        "INITIALIZE_REQUIRED": "Inizializza la sessione Juriscribe.",
        "MODE_SELECTION_REQUIRED": "Scegli una modalità Juriscribe.",
        "USER_SETUP_REQUIRED": "Accetta i parametri consigliati oppure modifica quelli necessari.",
        "HUMAN_DECISION_REQUIRED": "È richiesta una decisione umana non inferibile.",
    }
    return defaults.get(phase, "Lavorazione autonoma in corso; nessuna decisione umana richiesta.")


def _choices(card: dict[str, Any]) -> list[str]:
    selected = []
    for item in card.get("choices") or []:
        label = _text(item, 56)
        if label and label != FREE_CHOICE and label not in selected:
            selected.append(label)
    return selected[:4]


def project_chat_shell(state: Any) -> dict[str, Any]:
    phase = _phase(state)
    mode = _mode(state)
    card = _card(state, phase, mode)
    status = _status(state, phase)
    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "phase": phase,
        "mode": mode,
        "status": status,
        "next": _next_text(phase, card, status),
        "choices": _choices(card),
        "utilities": ["STATO", "ARTEFATTI", "AIUTO", FREE_CHOICE],
    }


def render_chat_shell(state: Any) -> str:
    projection = project_chat_shell(state)
    line1 = _text(
        f"JURISCRIBE> {projection['phase']} | MODE={projection['mode'] or '-'} | {projection['status']}"
    )
    line2 = _text(f"NEXT> {projection['next']}")
    options = [f"[{index}] {label}" for index, label in enumerate(projection["choices"], 1)]
    options.extend(["[S] STATO", "[A] ARTEFATTI", "[?] AIUTO", "[…] ALTRO"])
    line3 = _text("  ".join(options))
    return "\n".join((line1, line2, line3))


def validate_rendered_shell(text: str) -> tuple[bool, list[str]]:
    lines = str(text or "").splitlines()
    errors = []
    if len(lines) != MAX_LINES:
        errors.append("chat shell must render exactly three lines")
    if any(len(line) > MAX_LINE_CHARS for line in lines):
        errors.append("chat shell line too long")
    if not lines or not lines[0].startswith("JURISCRIBE> "):
        errors.append("chat shell prompt missing")
    if len(lines) < 2 or not lines[1].startswith("NEXT> "):
        errors.append("chat shell next line missing")
    if len(lines) < 3 or "[…] ALTRO" not in lines[2]:
        errors.append("chat shell free-input path missing")
    return not errors, errors
