"""Current CLI/API pipeline.

v0.9 implementation lives in pipeline_v9. v0.9.1 keeps machine-readable JSON available
through ``JURISCRIBE_VERBOSE_JSON=1`` but makes the default agent/human surface terse:
substantive details belong in the attached DOCX artifacts and HTML dashboard, not in chat.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

from . import pipeline_v9 as _v9
from .pipeline_v9 import *  # noqa: F401,F403


def _command(argv):
    args = list(sys.argv[1:] if argv is None else argv)
    for token in args:
        if not str(token).startswith("-"):
            return str(token)
    return ""


def _compact_interaction(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return "Consulta la dashboard."
    summary = str(payload.get("summary") or "").strip()
    choices = payload.get("choices") or []
    if choices:
        suffix = " | ".join(map(str, choices))
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


def main(argv=None):
    if os.environ.get("JURISCRIBE_VERBOSE_JSON") == "1":
        return _v9.main(argv)

    command = _command(argv)
    # Terms/bootstrap must remain fully visible: the human must actually see what is
    # being accepted. Initialize/dashboard already print only a path.
    if command in {"terms", "accept", "probe", "initialize", "dashboard"}:
        return _v9.main(argv)

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = _v9.main(argv)
    raw = buffer.getvalue().strip()

    if command == "gate":
        print(_compact_gate(raw))
    elif command == "interaction-card":
        print(_compact_interaction(raw))
    elif rc == 0:
        print("OK. Dettagli aggiornati negli artefatti e nella dashboard.")
    else:
        print("Richiede attenzione. Consulta la dashboard.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
