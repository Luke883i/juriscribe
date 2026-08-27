"""v1 candidate public CLI/API surface with recovery-aware shell projection."""
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


def _argv(argv): return list(sys.argv[1:] if argv is None else argv)
def _clean_argv(argv): return [str(token) for token in _argv(argv) if str(token) != TECHNICAL_FLAG]
def _command(argv): return next((str(token) for token in _clean_argv(argv) if not str(token).startswith("-")), "")


def _session_dir(argv):
    args = _clean_argv(argv); command = _command(args)
    if command in BOOTSTRAP_VERBOSE_COMMANDS | {"initialize", "bootstrap-after-acceptance", "recovery-inspect", "recovery-resume"}:
        return None
    try: index = args.index(command)
    except ValueError: return None
    return next((str(token) for token in args[index + 1:] if not str(token).startswith("-")), None)


def _truncate(value: str, limit: int = MAX_PUBLIC_SUMMARY_CHARS) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: max(0, limit - 1)].rstrip() + "…"


def _session_from_output(command: str, raw: str, argv) -> str | None:
    if command in {"bootstrap-after-acceptance", "recovery-resume"}:
        try: return str(json.loads(raw).get("session_dir") or "") or None
        except Exception: return None
    if command == "initialize": return str(raw or "").strip() or None
    return _session_dir(argv)


def _render_persisted_shell(session_dir: str | None) -> str | None:
    if not session_dir: return None
    path = Path(session_dir); ws = _v9.Workspace(path.parent, path.name)
    if not ws.state_path.exists(): return None
    return render_chat_shell(ws.load())


def _record_hidden_failure(argv, exc: Exception) -> None:
    session_dir = _session_dir(argv)
    if not session_dir: return
    path = Path(session_dir); ws = _v9.Workspace(path.parent, path.name)
    if not ws.state_path.exists(): return
    try:
        state = ws.load(); command = _command(argv)
        record = {"kind":"RUNTIME_BLOCKER","status":"OPEN","command":command,"summary":"Errore tecnico interno; dettaglio disponibile solo nel ledger tecnico su richiesta esplicita.","error_type":type(exc).__name__}
        state.limits = [item for item in (state.limits or []) if not (str(item.get("kind", "")).upper()=="RUNTIME_BLOCKER" and item.get("command")==command)] + [record]
        ws.append_ledger("runtime-errors", {**record,"internal_message":str(exc),"traceback":traceback.format_exc(),"delivery_class":"INTERNAL"})
        _v9.persist_session(ws,state)
    except Exception: pass


def _technical_output_requested(argv) -> bool: return os.environ.get("JURISCRIBE_VERBOSE_JSON") == "1" and TECHNICAL_FLAG in _argv(argv)


def _legacy_public_fallback(command: str, raw: str, rc: int) -> str:
    if command == "recovery-inspect":
        try:
            data=json.loads(raw); where=data.get("where") or {}; nxt=data.get("next") or {}
            return _truncate(f"Recovery PASS · cp={data.get('checkpoint_id','')} · {where.get('phase','')} · NEXT: {nxt.get('summary','')}",600)
        except Exception: return "Bundle di recupero non leggibile."
    if command == "recovery-bundle": return "Snapshot di recupero materializzato; il file richiesto deve essere allegato dal host."
    if command == "gate": return "Consulta la dashboard."
    if command == "interaction-card": return _truncate(raw,600) or "Consulta la dashboard."
    if command == "bootstrap-after-acceptance": return _truncate(raw,600) or "Juriscribe inizializzato."
    if command in {"initialize", "dashboard"}: return _truncate(raw,600) or "OK."
    if rc == 0: return "OK. Contenuti aggiornati; consulta la dashboard e gli artefatti."
    return "Richiede attenzione. Consulta la dashboard."


def main(argv=None):
    clean=_clean_argv(argv)
    if _technical_output_requested(argv): return _v9.main(clean)
    command=_command(clean)
    if command in BOOTSTRAP_VERBOSE_COMMANDS: return _v9.main(clean)
    stdout=io.StringIO(); stderr=io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr): rc=_v9.main(clean)
    except Exception as exc:
        _record_hidden_failure(clean,exc); print("Operazione non completata. Consulta la dashboard."); return 2
    raw=stdout.getvalue().strip(); session_dir=_session_from_output(command,raw,clean)
    try: shell=_render_persisted_shell(session_dir)
    except Exception as exc: _record_hidden_failure(clean,exc); shell=None
    print(shell if shell else _legacy_public_fallback(command,raw,rc)); return rc


if __name__ == "__main__": raise SystemExit(main())
