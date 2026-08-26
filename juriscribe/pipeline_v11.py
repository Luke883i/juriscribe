"""Current CLI overlay for Compression & Consolidation.

Historical commands delegate to pipeline_v9 without import-time mutation. The overlay
adds mode-specific commands while runtime_v12 supplies proof-carrying semantics.
Dynamic mode discovery remains scoped to fast bootstrap invocation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import pipeline_v9 as _v9
from .pipeline_v9 import *  # noqa: F401,F403
from .modes import mode_choices
from .runtime_v12 import calibrate_refactoring, consolidation_gate, record_consolidation_saturation, register_refactoring_plan, seal_refined_candidate

CC_COMMANDS = {"consolidation-plan", "consolidation-saturation", "consolidation-calibrate", "consolidation-seal-refined", "consolidation-status"}


def _workspace(session_dir):
    path = Path(session_dir)
    return Workspace(path.parent, path.name)


def _payload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _dynamic_fast_bootstrap(original, *args, **kwargs):
    result = original(*args, **kwargs)
    result["choices"] = [*mode_choices(), "ALTRO"]
    return result


def _legacy_main(args):
    command = next((str(x) for x in args if not str(x).startswith("-")), "")
    if command != "bootstrap-after-acceptance":
        return _v9.main(args)
    original = _v9.bootstrap_after_acceptance
    _v9.bootstrap_after_acceptance = lambda *a, **kw: _dynamic_fast_bootstrap(original, *a, **kw)
    try:
        return _v9.main(args)
    finally:
        _v9.bootstrap_after_acceptance = original


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
