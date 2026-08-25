"""v0.11 CLI overlay for Compression & Consolidation.

All historical commands delegate unchanged to pipeline_v9. New C&C commands mutate
only the isolated consolidation state and persist through the same Workspace path.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from . import pipeline_v9 as _v9
from .pipeline_v9 import *  # noqa: F401,F403
from .runtime_v11 import (
    calibrate_refactoring,
    record_consolidation_saturation,
    register_refactoring_plan,
    seal_refined_candidate,
    consolidation_gate,
)

CC_COMMANDS = {
    "consolidation-plan", "consolidation-saturation", "consolidation-calibrate",
    "consolidation-seal-refined", "consolidation-status",
}


def _workspace(session_dir: str):
    p=Path(session_dir); return Workspace(p.parent,p.name)


def _payload(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cc_main(argv):
    parser=argparse.ArgumentParser(prog="juriscribe")
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("consolidation-plan"); p.add_argument("session_dir"); p.add_argument("--json-file",required=True)
    p=sub.add_parser("consolidation-saturation"); p.add_argument("session_dir"); p.add_argument("--json-file",required=True)
    p=sub.add_parser("consolidation-calibrate"); p.add_argument("session_dir"); p.add_argument("--json-file",required=True)
    p=sub.add_parser("consolidation-seal-refined"); p.add_argument("session_dir"); p.add_argument("--source-id",required=True); p.add_argument("--text-file",required=True); p.add_argument("--semantic-recall",type=float,default=1.0); p.add_argument("--relation-recall",type=float,default=1.0)
    p=sub.add_parser("consolidation-status"); p.add_argument("session_dir")
    args=parser.parse_args(argv); ws=_workspace(args.session_dir); state=ws.load()
    if args.command=="consolidation-plan":
        data=_payload(args.json_file); out=register_refactoring_plan(state,gaps=data.get("gaps",[]),operations=data.get("operations",[]))
    elif args.command=="consolidation-saturation": out=record_consolidation_saturation(state,_payload(args.json_file))
    elif args.command=="consolidation-calibrate":
        data=_payload(args.json_file); out=calibrate_refactoring(state,data.get("decisions",data if isinstance(data,list) else []))
    elif args.command=="consolidation-seal-refined":
        out=seal_refined_candidate(state,source_id=args.source_id,text=Path(args.text_file).read_text(encoding="utf-8"),semantic_recall=args.semantic_recall,relation_recall=args.relation_recall)
    else:
        ok,errors=consolidation_gate(state); out={"status":"PASS" if ok else "FAIL","errors":errors,"phase":state.phase}
    if args.command!="consolidation-status": persist_session(ws,state,trigger=args.command)
    print(json.dumps(out if isinstance(out,dict) else {"status":"PASS"},ensure_ascii=False,indent=2)); return 0


def main(argv=None):
    args=list(argv or [])
    command=next((str(x) for x in args if not str(x).startswith("-")),"")
    if command in CC_COMMANDS: return _cc_main(args)
    return _v9.main(args)
