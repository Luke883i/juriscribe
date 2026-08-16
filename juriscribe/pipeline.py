"""Current CLI/API pipeline with an artifact-first public surface.

The v0.9 implementation remains in :mod:`pipeline_v9`. v0.9.2 makes the
post-bootstrap human/agent surface intentionally small for *every* substantive
step, not only final delivery. Machine JSON and tracebacks remain available only
through the explicit ``JURISCRIBE_VERBOSE_JSON=1`` technical path.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path

from . import pipeline_v9 as _v9
from .delivery import refresh_dashboard_artifact
from .pipeline_v9 import *  # noqa: F401,F403

MAX_PUBLIC_SUMMARY_CHARS = 280
BOOTSTRAP_VERBOSE_COMMANDS = {"terms", "accept", "probe"}


def _command(argv):
    args = list(sys.argv[1:] if argv is None else argv)
    for token in args:
        if not str(token).startswith("-"):
            return str(token)
    return ""


def _argv(argv):
    return list(sys.argv[1:] if argv is None else argv)


def _session_dir(argv):
    args = _argv(argv)
    command = _command(args)
    if command in BOOTSTRAP_VERBOSE_COMMANDS | {"initialize"}:
        return None
    try:
        index = args.index(command)
    except ValueError:
        return None
    for token in args[index + 1 :]:
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
        suffix = " | ".join(choices)
        return f"{summary}\n{suffix}".strip()
    return summary or "Consulta la dashboard."


def _compact_gate(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return "Consulta la dashboard."
    manifest = payload.get("delivery_manifest") or {}
    if payload.get("eligible") and manifest.get("status") == "PASS":
        return f"Completato. Consulta gli artefatti allegati ({len(manifest.get('attachments', []))} file)."
    return "Non pronto. Consulta la dashboard; restano blocker di lavorazione."


def _refresh_dashboard(session_dir: str | None) -> str | None:
    if not session_dir:
        return None
    path = Path(session_dir)
    ws = _v9.Workspace(path.parent, path.name)
    if not ws.state_path.exists():
        return None
    state = ws.load()
    out = ws.artifact_dir / "session-dashboard.html"
    _v9.render_session_dashboard(state.to_dict(), out)
    refresh_dashboard_artifact(state, out)
    ws.save(state)
    return str(out)


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
            "summary": _truncate(f"{type(exc).__name__}: {exc}", 800),
        }
        state.limits = [
            item
            for item in (state.limits or [])
            if not (
                str(item.get("kind", "")).upper() == "RUNTIME_BLOCKER"
                and item.get("command") == command
            )
        ] + [record]
        ws.append_ledger(
            "runtime-errors",
            {
                **record,
                "traceback": traceback.format_exc(),
                "delivery_class": "INTERNAL",
            },
        )
        ws.save(state)
        _refresh_dashboard(session_dir)
    except Exception:
        # Public output must remain terse even if internal failure recording fails.
        pass


def main(argv=None):
    if os.environ.get("JURISCRIBE_VERBOSE_JSON") == "1":
        return _v9.main(argv)

    command = _command(argv)
    if command in BOOTSTRAP_VERBOSE_COMMANDS:
        # Terms and explicit acceptance/probe surfaces must remain visible to the human.
        return _v9.main(argv)

    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = _v9.main(argv)
    except Exception as exc:
        _record_hidden_failure(argv, exc)
        print("Operazione non completata. Consulta la dashboard.")
        return 2

    raw = stdout.getvalue().strip()
    session_dir = _session_dir(argv)
    if command == "initialize" and raw:
        # initialize prints the newly-created workspace path; immediately re-render
        # and bind the first dashboard to the current state before exposing it.
        session_dir = raw.splitlines()[-1].strip()
    if session_dir:
        try:
            _refresh_dashboard(session_dir)
        except Exception as exc:
            _record_hidden_failure(argv, exc)
            print("Operazione non completata. Consulta la dashboard.")
            return 2

    if command == "gate":
        print(_compact_gate(raw))
    elif command == "interaction-card":
        print(_compact_interaction(raw))
    elif command in {"initialize", "dashboard"}:
        print(_truncate(raw, 600) or "OK.")
    elif rc == 0:
        print("OK. Dettagli aggiornati negli artefatti e nella dashboard.")
    else:
        print("Richiede attenzione. Consulta la dashboard.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
