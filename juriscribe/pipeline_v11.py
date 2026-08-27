"""Current CLI composition for specialist C&C commands and historical commands.

Historical commands delegate to pipeline_v9. C&C specialist commands resolve via
the same explicit runtime router used by the public orchestrator. Fast-bootstrap
mode choices are normalized at the transport boundary without monkey-patching the
legacy module.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path

from . import pipeline_v9 as _v9
from .pipeline_v9 import *  # noqa: F401,F403
from .modes import mode_choices
from .runtime_router import resolve_operation

calibrate_refactoring = resolve_operation("calibrate_refactoring")
consolidation_gate = resolve_operation("consolidation_gate")
record_consolidation_saturation = resolve_operation("record_consolidation_saturation")
register_refactoring_plan = resolve_operation("register_refactoring_plan")
seal_refined_candidate = resolve_operation("seal_refined_candidate")

CC_COMMANDS = {"consolidation-plan", "consolidation-saturation", "consolidation-calibrate", "consolidation-seal-refined", "consolidation-status"}


def _workspace(session_dir):
    path = Path(session_dir)
    return Workspace(path.parent, path.name)


def _payload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _legacy_main(args):
    command = next((str(x) for x in args if not str(x).startswith("-")), "")
    if command != "bootstrap-after-acceptance":
        return _v9.main(args)
    # pipeline_v9 is compatibility code and still serializes a historical tri-mode
    # choice list. Normalize only the returned transport payload from the canonical
    # registry; do not mutate the legacy module or invent a second mode source.
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        rc = _v9.main(args)
    raw = stdout.getvalue().strip()
    try:
        result = json.loads(raw)
        result["choices"] = [*mode_choices(), "ALTRO"]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception:
        print(raw)
    return rc


def _cc_main(argv):
    parser = argparse.ArgumentParser(prog="juriscribe")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("consolidation-plan"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-saturation"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-calibrate"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-seal-refined"); p.add_argument("session_dir"); p.add_argument("--source-id", required=True); p.add_argument("--text-file", required=True); p.add_argument("--projection-json", required=True)
    p = sub.add_parser("consolidation-status"); p.add_argument("session_dir")
    args = parser.parse_args(argv)
    ws = _workspace(args.session_dir)
    state = ws.load()
    if args.command == "consolidation-plan":
        data = _payload(args.json_file); out = register_refactoring_plan(state, gaps=data.get("gaps", []), operations=data.get("operations", []))
    elif args.command == "consolidation-saturation":
        out = record_consolidation_saturation(state, _payload(args.json_file))
    elif args.command == "consolidation-calibrate":
        data = _payload(args.json_file); out = calibrate_refactoring(state, data.get("decisions", data if isinstance(data, list) else []))
    elif args.command == "consolidation-seal-refined":
        out = seal_refined_candidate(
            state,
            source_id=args.source_id,
            text=Path(args.text_file).read_text(encoding="utf-8"),
            semantic_projection=_payload(args.projection_json),
        )
    else:
        ok, errors = consolidation_gate(state); out = {"status": "PASS" if ok else "FAIL", "errors": errors, "phase": state.phase}
    if args.command != "consolidation-status":
        persist_session(ws, state, trigger=args.command)
    print(json.dumps(out if isinstance(out, dict) else {"status": "PASS"}, ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    args = list(argv or [])
    command = next((str(x) for x in args if not str(x).startswith("-")), "")
    if command in CC_COMMANDS:
        return _cc_main(args)
    return _legacy_main(args)
