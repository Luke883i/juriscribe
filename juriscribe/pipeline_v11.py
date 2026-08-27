"""v1 candidate CLI composition: specialist C&C plus recovery transport.

This file keeps historical commands delegated to pipeline_v9 and uses the explicit
runtime router for substantive/public operations. Recovery resume remains bootstrap/
session materialization rather than an orchestration route.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import platform
from pathlib import Path

from . import pipeline_v9 as _v9
from .pipeline_v9 import *  # noqa: F401,F403
from .modes import mode_choices
from .recovery import inspect_recovery_bundle, resume_recovery_bundle
from .runtime_router import resolve_operation

calibrate_refactoring = resolve_operation("calibrate_refactoring")
consolidation_gate = resolve_operation("consolidation_gate")
record_consolidation_saturation = resolve_operation("record_consolidation_saturation")
register_refactoring_plan = resolve_operation("register_refactoring_plan")
seal_refined_candidate = resolve_operation("seal_refined_candidate")
create_recovery_bundle = resolve_operation("create_recovery_bundle")

CC_COMMANDS = {"consolidation-plan", "consolidation-saturation", "consolidation-calibrate", "consolidation-seal-refined", "consolidation-status"}
RECOVERY_COMMANDS = {"recovery-bundle", "recovery-inspect", "recovery-resume"}
MATERIALIZATION_CONTINUE_COMMAND = "continue-materialization"


def _workspace(session_dir):
    path = Path(session_dir)
    return Workspace(path.parent, path.name)


def _payload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _legacy_main(args):
    command = next((str(x) for x in args if not str(x).startswith("-")), "")
    if command == MATERIALIZATION_CONTINUE_COMMAND:
        index = list(args).index(command); tail = list(args)[index + 1:]
        if not tail or str(tail[0]).startswith("-"):
            raise ValueError("continue-materialization requires session_dir")
        return _v9.main(["gate", str(tail[0])])
    if command != "bootstrap-after-acceptance":
        return _v9.main(args)
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        rc = _v9.main(args)
    raw = stdout.getvalue().strip()
    try:
        result = json.loads(raw); result["choices"] = [*mode_choices(), "ALTRO"]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception:
        print(raw)
    return rc


def _cc_main(argv):
    parser = argparse.ArgumentParser(prog="juriscribe"); sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("consolidation-plan"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-saturation"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-calibrate"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-seal-refined"); p.add_argument("session_dir"); p.add_argument("--source-id", required=True); p.add_argument("--text-file", required=True); p.add_argument("--projection-json", required=True)
    p = sub.add_parser("consolidation-status"); p.add_argument("session_dir")
    args = parser.parse_args(argv); ws = _workspace(args.session_dir); state = ws.load()
    if args.command == "consolidation-plan":
        data = _payload(args.json_file); out = register_refactoring_plan(state, gaps=data.get("gaps", []), operations=data.get("operations", []))
    elif args.command == "consolidation-saturation": out = record_consolidation_saturation(state, _payload(args.json_file))
    elif args.command == "consolidation-calibrate":
        data = _payload(args.json_file); out = calibrate_refactoring(state, data.get("decisions", data if isinstance(data, list) else []))
    elif args.command == "consolidation-seal-refined":
        out = seal_refined_candidate(state, source_id=args.source_id, text=Path(args.text_file).read_text(encoding="utf-8"), semantic_projection=_payload(args.projection_json))
    else:
        ok, errors = consolidation_gate(state); out = {"status": "PASS" if ok else "FAIL", "errors": errors, "phase": state.phase}
    if args.command != "consolidation-status": persist_session(ws, state, trigger=args.command)
    print(json.dumps(out if isinstance(out, dict) else {"status": "PASS"}, ensure_ascii=False, indent=2)); return 0


def _recovery_main(argv):
    parser = argparse.ArgumentParser(prog="juriscribe"); sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("recovery-bundle"); p.add_argument("session_dir"); p.add_argument("--out", required=True)
    p = sub.add_parser("recovery-inspect"); p.add_argument("bundle")
    p = sub.add_parser("recovery-resume"); p.add_argument("bundle"); p.add_argument("--root", default=".juriscribe")
    args = parser.parse_args(argv)
    if args.command == "recovery-bundle":
        ws = _workspace(args.session_dir); state = ws.load()
        checkpoint = __import__("juriscribe.continuity", fromlist=["checkpoint_id"]).checkpoint_id
        before = checkpoint(state); out = create_recovery_bundle(state, args.out, workspace_base=ws.base, require_resumable=True)
        report = inspect_recovery_bundle(out)
        if report.get("status") != "PASS": raise ValueError("generated recovery bundle failed readback: " + "; ".join(report.get("errors") or []))
        if checkpoint(state) != before: raise RuntimeError("recovery export mutated scientific checkpoint")
        print(json.dumps({"status":"PASS","bundle":str(out),"checkpoint_id":before,"attach_to_user":True}, ensure_ascii=False, indent=2)); return 0
    report = inspect_recovery_bundle(args.bundle)
    if report.get("status") != "PASS":
        print(json.dumps({"status":"FAIL","errors":report.get("errors") or []}, ensure_ascii=False, indent=2)); return 2
    if args.command == "recovery-inspect":
        iteration = report.get("iteration") or {}
        print(json.dumps({"status":"PASS","session_id":(report.get("state") or {}).get("session_id"),"checkpoint_id":(report.get("manifest") or {}).get("checkpoint_id"),"where":iteration.get("where"),"next":iteration.get("next"),"material_count":(report.get("manifest") or {}).get("material_count")}, ensure_ascii=False, indent=2)); return 0
    contract = load_contract_text(); receipt = ((report.get("state") or {}).get("admission") or {}).get("receipt")
    caps = _v9.probe_capabilities(admission_receipt=receipt, contract_text=contract)
    base = resume_recovery_bundle(args.bundle, args.root, host_capabilities=caps, host=platform.platform(), contract_text=contract)
    print(json.dumps({"status":"PASS","session_dir":str(base),"checkpoint_id":(report.get("manifest") or {}).get("checkpoint_id")}, ensure_ascii=False, indent=2)); return 0


def main(argv=None):
    args = list(argv or []); command = next((str(x) for x in args if not str(x).startswith("-")), "")
    if command in RECOVERY_COMMANDS: return _recovery_main(args)
    if command in CC_COMMANDS: return _cc_main(args)
    return _legacy_main(args)
