from __future__ import annotations
import argparse, json, os, platform
from pathlib import Path
from .dashboard import render_session_dashboard
from .session import Workspace, stable_id

def probe_capabilities() -> dict[str, str]:
    checks = {"SESSION_CONTEXT":"AVAILABLE","LOCAL_SCRATCH_IO":"UNVERIFIED","STRUCTURED_STORAGE":"AVAILABLE","ATTACHMENT_READ":"UNVERIFIED","DOCX_READ":"UNVERIFIED","DOCX_WRITE":"UNVERIFIED","DOCX_READBACK":"UNVERIFIED","PDF_READ":"UNVERIFIED","WEB_RESEARCH":"UNVERIFIED","REPOSITORY_READ":"UNVERIFIED","REPOSITORY_WRITE":"UNVERIFIED","CLOCK":"AVAILABLE","HASHING":"AVAILABLE"}
    try:
        test = Path(".juriscribe-probe.tmp"); test.write_text("probe", encoding="utf-8"); ok = test.read_text(encoding="utf-8") == "probe"; test.unlink(missing_ok=True); checks["LOCAL_SCRATCH_IO"] = "AVAILABLE" if ok else "UNAVAILABLE"
    except OSError:
        checks["LOCAL_SCRATCH_IO"] = "UNAVAILABLE"
    return checks

def initialize(request: str, root: str = ".juriscribe", session_id: str | None = None) -> Path:
    session_id = session_id or stable_id("SES", request + os.getcwd()); capabilities = probe_capabilities()
    runtime = {"host": platform.platform(), "python": platform.python_version(), "capabilities": capabilities, "mode": "ACTIVE_FILE" if capabilities["LOCAL_SCRATCH_IO"] == "AVAILABLE" else "ACTIVE_EPHEMERAL"}
    ws = Workspace(root, session_id); state = ws.initialize(request, runtime); dashboard = ws.artifact_dir / "session-dashboard.html"; render_session_dashboard(state.to_dict(), dashboard)
    state.artifacts.append({"id":"dashboard","summary":"Dashboard HTML specifica della sessione","path":str(dashboard),"readback":"PASS"}); ws.save(state); return ws.base

def update_dashboard(session_dir: str | Path) -> Path:
    session_dir = Path(session_dir); ws = Workspace(session_dir.parent, session_dir.name); state = ws.load(); output = ws.artifact_dir / "session-dashboard.html"; return render_session_dashboard(state.to_dict(), output)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="juriscribe", description="iSeneca session kernel"); sub = parser.add_subparsers(dest="command", required=True); sub.add_parser("probe")
    p_init = sub.add_parser("initialize"); p_init.add_argument("--request", required=True); p_init.add_argument("--root", default=".juriscribe"); p_init.add_argument("--session-id")
    p_dash = sub.add_parser("dashboard"); p_dash.add_argument("session_dir"); args = parser.parse_args(argv)
    if args.command == "probe": print(json.dumps(probe_capabilities(), indent=2)); return 0
    if args.command == "initialize": print(initialize(args.request, args.root, args.session_id)); return 0
    if args.command == "dashboard": print(update_dashboard(args.session_dir)); return 0
    return 1
