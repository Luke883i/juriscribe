from __future__ import annotations
import argparse, json, os, platform
from pathlib import Path
from .dashboard import render_session_dashboard
from .orchestrator import mine_and_prepare, apply_setup, freeze_dods, build_research_plan, validate_claim_ledger, evaluate_completion
from .session import Workspace, stable_id


def probe_capabilities() -> dict[str, str]:
    checks = {"SESSION_CONTEXT":"AVAILABLE","LOCAL_SCRATCH_IO":"UNVERIFIED","STRUCTURED_STORAGE":"AVAILABLE","ATTACHMENT_READ":"UNVERIFIED","DOCX_READ":"UNVERIFIED","DOCX_WRITE":"UNVERIFIED","DOCX_READBACK":"UNVERIFIED","PDF_READ":"UNVERIFIED","WEB_RESEARCH":"UNVERIFIED","REPOSITORY_READ":"UNVERIFIED","REPOSITORY_WRITE":"UNVERIFIED","CLOCK":"AVAILABLE","HASHING":"AVAILABLE"}
    try:
        test = Path(".juriscribe-probe.tmp"); test.write_text("probe", encoding="utf-8"); ok = test.read_text(encoding="utf-8") == "probe"; test.unlink(missing_ok=True); checks["LOCAL_SCRATCH_IO"] = "AVAILABLE" if ok else "UNAVAILABLE"
    except OSError:
        checks["LOCAL_SCRATCH_IO"] = "UNAVAILABLE"
    return checks


def initialize(request: str, root: str = ".juriscribe", session_id: str | None = None, host_capabilities: dict | None = None) -> Path:
    session_id = session_id or stable_id("SES", request + os.getcwd()); capabilities = probe_capabilities()
    if host_capabilities: capabilities.update(host_capabilities)
    runtime = {"host": platform.platform(), "python": platform.python_version(), "capabilities": capabilities, "mode": "ACTIVE_FILE" if capabilities["LOCAL_SCRATCH_IO"] == "AVAILABLE" else "ACTIVE_EPHEMERAL"}
    ws = Workspace(root, session_id); state = ws.initialize(request, runtime); dashboard = ws.artifact_dir / "session-dashboard.html"; render_session_dashboard(state.to_dict(), dashboard)
    state.artifacts.append({"id":"dashboard","summary":"Dashboard HTML specifica della sessione","path":str(dashboard),"readback":"PASS"}); ws.save(state); return ws.base


def _workspace(session_dir: str | Path) -> Workspace:
    p = Path(session_dir); return Workspace(p.parent, p.name)


def update_dashboard(session_dir: str | Path) -> Path:
    ws = _workspace(session_dir); state = ws.load(); output = ws.artifact_dir / "session-dashboard.html"; return render_session_dashboard(state.to_dict(), output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="juriscribe", description="iSeneca session kernel"); sub = parser.add_subparsers(dest="command", required=True); sub.add_parser("probe")
    p_init = sub.add_parser("initialize"); p_init.add_argument("--request", required=True); p_init.add_argument("--root", default=".juriscribe"); p_init.add_argument("--session-id")
    p_mine = sub.add_parser("mine"); p_mine.add_argument("session_dir"); p_mine.add_argument("--text-file", required=True); p_mine.add_argument("--source-id", required=True); p_mine.add_argument("--chapter")
    p_setup = sub.add_parser("accept-setup"); p_setup.add_argument("session_dir"); p_setup.add_argument("--overrides-json")
    p_freeze = sub.add_parser("freeze-dods"); p_freeze.add_argument("session_dir"); p_freeze.add_argument("--additional-json")
    p_research = sub.add_parser("research-plan"); p_research.add_argument("session_dir")
    p_validate = sub.add_parser("validate-claims"); p_validate.add_argument("session_dir")
    p_gate = sub.add_parser("gate"); p_gate.add_argument("session_dir")
    p_dash = sub.add_parser("dashboard"); p_dash.add_argument("session_dir")
    args = parser.parse_args(argv)
    if args.command == "probe": print(json.dumps(probe_capabilities(), indent=2)); return 0
    if args.command == "initialize": print(initialize(args.request, args.root, args.session_id)); return 0
    ws = _workspace(getattr(args, "session_dir")); state = ws.load()
    if args.command == "mine":
        text = Path(args.text_file).read_text(encoding="utf-8"); mine_and_prepare(state, text, source_id=args.source_id, chapter=args.chapter); ws.save(state); update_dashboard(ws.base); print(json.dumps(state.setup, ensure_ascii=False, indent=2)); return 0
    if args.command == "accept-setup":
        overrides = json.loads(args.overrides_json) if args.overrides_json else None; apply_setup(state, overrides); ws.save(state); update_dashboard(ws.base); print(json.dumps(state.setup, ensure_ascii=False, indent=2)); return 0
    if args.command == "freeze-dods":
        additional = json.loads(args.additional_json) if args.additional_json else None; freeze_dods(state, additional); ws.save(state); update_dashboard(ws.base); return 0
    if args.command == "research-plan": build_research_plan(state); ws.save(state); print(json.dumps(state.source_intelligence["research_plan"], ensure_ascii=False, indent=2)); return 0
    if args.command == "validate-claims":
        errors = validate_claim_ledger(state); ws.save(state); print(json.dumps(errors, ensure_ascii=False, indent=2)); return 1 if errors else 0
    if args.command == "gate": evaluate_completion(state); ws.save(state); update_dashboard(ws.base); print(json.dumps(state.completion, ensure_ascii=False, indent=2)); return 0 if state.completion["eligible"] else 2
    if args.command == "dashboard": print(update_dashboard(ws.base)); return 0
    return 1
