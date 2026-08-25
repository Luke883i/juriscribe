"""Current artifact-first public CLI, backed by pipeline_v11."""
from __future__ import annotations
import contextlib, io, json, os, sys, traceback
from pathlib import Path
from . import pipeline_v11 as _v9
from .pipeline_v11 import *  # noqa: F401,F403
MAX_PUBLIC_SUMMARY_CHARS=280
BOOTSTRAP_VERBOSE_COMMANDS={"terms","accept","probe"}
TECHNICAL_FLAG="--technical-output"
def _argv(argv): return list(sys.argv[1:] if argv is None else argv)
def _clean_argv(argv): return [str(t) for t in _argv(argv) if str(t)!=TECHNICAL_FLAG]
def _command(argv): return next((str(t) for t in _clean_argv(argv) if not str(t).startswith("-")),"")
def _session_dir(argv):
    args=_clean_argv(argv); command=_command(args)
    if command in BOOTSTRAP_VERBOSE_COMMANDS|{"initialize","bootstrap-after-acceptance"}: return None
    try: index=args.index(command)
    except ValueError: return None
    return next((str(t) for t in args[index+1:] if not str(t).startswith("-")),None)
def _truncate(value,limit=MAX_PUBLIC_SUMMARY_CHARS):
    text=" ".join(str(value or "").split()); return text if len(text)<=limit else text[:limit-1].rstrip()+"…"
def _compact_interaction(text):
    try: p=json.loads(text)
    except Exception: return "Consulta la dashboard."
    summary=_truncate(p.get("summary") or ""); choices=[str(x) for x in p.get("choices",[])][:6]
    return (summary+"\n"+" | ".join(choices)).strip() if choices else summary or "Consulta la dashboard."
def _compact_gate(text):
    try: p=json.loads(text)
    except Exception: return "Consulta la dashboard."
    m=p.get("delivery_manifest") or {}; a=m.get("attachments") or []
    if p.get("eligible") and m.get("status")=="PASS": return f"Completato. {len(a)} artefatti autorizzati sono disponibili secondo il manifest di consegna."
    return "Non pronto. Consulta la dashboard; restano blocker di lavorazione."
def _compact_fast_bootstrap(text):
    try: p=json.loads(text)
    except Exception: return "Juriscribe inizializzato. Scegli una modalità canonica."
    return f"Juriscribe inizializzato: {_truncate(p.get('session_dir') or '',500)}\n{' | '.join(str(x) for x in (p.get('choices') or []))}".strip()
def _record_hidden_failure(argv,exc):
    session_dir=_session_dir(argv)
    if not session_dir: return
    path=Path(session_dir); ws=_v9.Workspace(path.parent,path.name)
    if not ws.state_path.exists(): return
    try:
        state=ws.load(); command=_command(argv); record={"kind":"RUNTIME_BLOCKER","status":"OPEN","command":command,"summary":"Errore tecnico interno; dettaglio disponibile solo nel ledger tecnico su richiesta esplicita.","error_type":type(exc).__name__}
        state.limits=[i for i in (state.limits or []) if not (str(i.get("kind","")).upper()=="RUNTIME_BLOCKER" and i.get("command")==command)]+[record]
        ws.append_ledger("runtime-errors",{**record,"internal_message":str(exc),"traceback":traceback.format_exc(),"delivery_class":"INTERNAL"}); _v9.persist_session(ws,state)
    except Exception: pass
def _technical_output_requested(argv): return os.environ.get("JURISCRIBE_VERBOSE_JSON")=="1" and TECHNICAL_FLAG in _argv(argv)
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
    raw=stdout.getvalue().strip()
    if command=="gate": print(_compact_gate(raw))
    elif command=="interaction-card": print(_compact_interaction(raw))
    elif command=="bootstrap-after-acceptance": print(_compact_fast_bootstrap(raw))
    elif command in {"initialize","dashboard"}: print(_truncate(raw,600) or "OK.")
    elif command=="consolidation-status": print(_truncate(raw,1200) or "OK.")
    elif rc==0: print("OK. Stato Juriscribe aggiornato; la release resta governata dai gate runtime e dal manifest di consegna.")
    else: print("Richiede attenzione. Consulta la dashboard.")
    return rc
if __name__=="__main__": raise SystemExit(main())
