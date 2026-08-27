"""Current CLI/API pipeline with a hardened artifact-first public surface.

v0.11 delegates substantive work to :mod:`pipeline_v11`, while preserving the
historical public surface for pre-existing commands. Raw machine JSON still
requires the two-part technical opt-in. The ordinary post-bootstrap surface is a
projection-only three-line chat shell derived from persisted runtime state.

When no persisted session can be loaded (tests, bootstrap fallbacks, external
callers), the historical compact/redacted facade remains authoritative. The shell
therefore strengthens the public surface without weakening the v0.9.2 boundary.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path

from . import pipeline_v11 as _v9
from .chat_shell import render_chat_shell
from .pipeline_v11 import *  # noqa: F401,F403

MAX_PUBLIC_SUMMARY_CHARS = 280
BOOTSTRAP_VERBOSE_COMMANDS = {"terms", "accept", "probe"}
TECHNICAL_FLAG = "--technical-output"


def _argv(argv):
    return list(sys.argv[1:] if argv is None else argv)


def _clean_argv(argv):
    return [str(token) for token in _argv(argv) if str(token) != TECHNICAL_FLAG]


def _command(argv):
    for token in _clean_argv(argv):
        if not str(token).startswith("-"):
            return str(token)
    return ""


def _session_dir(argv):
    args = _clean_argv(argv)
    command = _command(args)
    if command in BOOTSTRAP_VERBOSE_COMMANDS | {"initialize", "bootstrap-after-acceptance"}:
        return None
    try:
        index = args.index(command)
    except ValueError:
        return None
    for token in args[index + 1:]:
        value = str(token)
        if not value.startswith("-"):
            return value
    return None


def _truncate(value: str, limit: int = MAX_PUBLIC_SUMMARY_CHARS) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _compact_interaction(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return "Consulta la dashboard."
    summary = _truncate(str(payload.get("summary") or ""))
    choices = [str(item) for item in (payload.get("choices") or [])][:4]
    if choices:
        return f"{summary}\n{' | '.join(choices)}".strip()
    return summary or "Consulta la dashboard."


def _compact_gate(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return "Consulta la dashboard."
    manifest = payload.get("delivery_manifest") or {}
    attachments = manifest.get("attachments") or []
    if payload.get("eligible") and manifest.get("status") == "PASS":
        if manifest.get("attachment_placement") == "SESSION_CHAT_TAIL" and all(item.get("format") == "DOCX" for item in attachments):
            return f"Completato. I {len(attachments)} artefatti DOCX scaricabili sono allegati in coda alla sessione-chat; la dashboard ne riepiloga i contenuti senza linkarli."
        return "Completato, ma il contratto pubblico di allegazione DOCX non risulta materializzato."
    return "Non pronto. Consulta la dashboard; restano blocker di lavorazione."


def _compact_fast_bootstrap(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return "Juriscribe inizializzato. Scegli una modalità canonica."
    session_dir = _truncate(str(payload.get("session_dir") or ""), 500)
    choices = " | ".join(str(x) for x in (payload.get("choices") or []))
    return f"Juriscribe inizializzato: {session_dir}\n{choices}".strip()


def _session_from_output(command: str, raw: str, argv) -> str | None:
    if command == "bootstrap-after-acceptance":
        try:
            return str(json.loads(raw).get("session_dir") or "") or None
        except Exception:
            return None
    if command == "initialize":
        return str(raw or "").strip() or None
    return _session_dir(argv)


def _render_persisted_shell(session_dir: str | None) -> str | None:
    if not session_dir:
        return None
    path = Path(session_dir)
    ws = _v9.Workspace(path.parent, path.name)
    if not ws.state_path.exists():
        return None
    state = ws.load()
    return render_chat_shell(state)


def _record_hidden_failure(argv, exc: Exception) -> None:
    session_dir = _session_dir(argv)
    if not session_dir:
        return
    path = Path(session_dir)
    ws = _v9.Workspace(path.parent, path.name)
    if not ws.state_path.exists():
        return
    try:
        state = ws.load()
        command = _command(argv)
        record = {
            "kind": "RUNTIME_BLOCKER",
            "status": "OPEN",
            "command": command,
            "summary": "Errore tecnico interno; dettaglio disponibile solo nel ledger tecnico su richiesta esplicita.",
            "error_type": type(exc).__name__,
        }
        state.limits = [
            item for item in (state.limits or [])
            if not (str(item.get("kind", "")).upper() == "RUNTIME_BLOCKER" and item.get("command") == command)
        ] + [record]
        ws.append_ledger("runtime-errors", {
            **record,
            "internal_message": str(exc),
            "traceback": traceback.format_exc(),
            "delivery_class": "INTERNAL",
        })
        _v9.persist_session(ws, state)
    except Exception:
        pass


def _technical_output_requested(argv) -> bool:
    return os.environ.get("JURISCRIBE_VERBOSE_JSON") == "1" and TECHNICAL_FLAG in _argv(argv)


def _legacy_public_fallback(command: str, raw: str, rc: int) -> str:
    """Preserve the hardened pre-shell surface when canonical state is unavailable."""
    if command == "gate":
        return _compact_gate(raw)
    if command == "interaction-card":
        return _compact_interaction(raw)
    if command == "bootstrap-after-acceptance":
        return _compact_fast_bootstrap(raw)
    if command in {"initialize", "dashboard"}:
        return _truncate(raw, 600) or "OK."
    if command == "consolidation-status":
        return _truncate(raw, 1200) or "OK."
    if rc == 0:
        return "OK. Contenuti aggiornati; i DOCX finali saranno allegati in coda alla sessione-chat e la dashboard resterà un riepilogo sintetico senza link documentali."
    return "Richiede attenzione. Consulta la dashboard."


def main(argv=None):
    clean = _clean_argv(argv)
    if _technical_output_requested(argv):
        return _v9.main(clean)
    command = _command(clean)
    if command in BOOTSTRAP_VERBOSE_COMMANDS:
        return _v9.main(clean)
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = _v9.main(clean)
    except Exception as exc:
        _record_hidden_failure(clean, exc)
        print("Operazione non completata. Consulta la dashboard.")
        return 2
    raw = stdout.getvalue().strip()
    session_dir = _session_from_output(command, raw, clean)
    try:
        shell = _render_persisted_shell(session_dir)
    except Exception as exc:
        _record_hidden_failure(clean, exc)
        shell = None
    print(shell if shell else _legacy_public_fallback(command, raw, rc))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
