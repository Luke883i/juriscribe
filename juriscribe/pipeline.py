from __future__ import annotations
import argparse,json,os,platform
from pathlib import Path
from .admission import issue_receipt,load_contract_text,load_receipt,require_receipt,validate_receipt
from .dashboard import render_session_dashboard
from .orchestrator import ingest_and_mine,register_semantic_mining,apply_setup,freeze_dods,build_research_plan,validate_claim_ledger,audit_candidate_chapter,record_simulation,record_compression,evaluate_completion
from .session import Workspace,stable_id

def probe_capabilities(*,admission_receipt=None,contract_text=None):
    contract_text=contract_text or load_contract_text()
    require_receipt(admission_receipt,contract_text)
    checks={"SESSION_CONTEXT":"AVAILABLE","LOCAL_SCRATCH_IO":"UNVERIFIED","STRUCTURED_STORAGE":"AVAILABLE","ATTACHMENT_READ":"UNVERIFIED","DOCX_READ":"UNVERIFIED","DOCX_WRITE":"UNVERIFIED","DOCX_READBACK":"UNVERIFIED","PDF_READ":"UNVERIFIED","WEB_RESEARCH":"UNVERIFIED","REPOSITORY_READ":"UNVERIFIED","REPOSITORY_WRITE":"UNVERIFIED","CLOCK":"AVAILABLE","HASHING":"AVAILABLE"}
    try:
        t=Path('.juriscribe-probe.tmp'); t.write_text('probe',encoding='utf-8'); ok=t.read_text(encoding='utf-8')=='probe'; t.unlink(missing_ok=True); checks['LOCAL_SCRATCH_IO']='AVAILABLE' if ok else 'UNAVAILABLE'
    except OSError: checks['LOCAL_SCRATCH_IO']='UNAVAILABLE'
    return checks

def initialize(request,root='.juriscribe',session_id=None,host_capabilities=None,*,admission_receipt=None,contract_text=None):
    contract_text=contract_text or load_contract_text(); receipt=require_receipt(admission_receipt,contract_text); session_id=session_id or stable_id('SES',request+os.getcwd()); caps=probe_capabilities(admission_receipt=receipt,contract_text=contract_text); caps.update(host_capabilities or {}); runtime={'host':platform.platform(),'python':platform.python_version(),'capabilities':caps,'mode':'ACTIVE_FILE' if caps['LOCAL_SCRATCH_IO']=='AVAILABLE' else 'ACTIVE_EPHEMERAL'}; ws=Workspace(root,session_id); state=ws.initialize(request,runtime,admission={'status':'ACCEPTED','receipt':receipt}); dash=ws.artifact_dir/'session-dashboard.html'; render_session_dashboard(state.to_dict(),dash); state.artifacts.append({'id':'dashboard','summary':'Dashboard giuridico-scientifico-editoriale della sessione','path':str(dash),'readback':'PASS','required':True}); ws.save(state); return ws.base

def _ws(session_dir): p=Path(session_dir); return Workspace(p.parent,p.name)
def update_dashboard(session_dir): ws=_ws(session_dir); state=ws.load(); out=ws.artifact_dir/'session-dashboard.html'; return render_session_dashboard(state.to_dict(),out)
def _receipt(path): return load_receipt(path) if path else None

def main(argv=None):
    p=argparse.ArgumentParser(prog='juriscribe'); sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('terms')
    acc=sub.add_parser('accept'); acc.add_argument('--phrase',required=True); acc.add_argument('--actor-type',required=True); acc.add_argument('--evidence-type',required=True); acc.add_argument('--user-message',required=True); acc.add_argument('--out',required=True)
    pr=sub.add_parser('probe'); pr.add_argument('--receipt',required=True)
    i=sub.add_parser('initialize'); i.add_argument('--request',required=True); i.add_argument('--root',default='.juriscribe'); i.add_argument('--session-id'); i.add_argument('--receipt',required=True)
    m=sub.add_parser('mine'); m.add_argument('session_dir'); m.add_argument('--text-file',required=True); m.add_argument('--source-id',required=True); m.add_argument('--chapter')
    sm=sub.add_parser('semantic-mining'); sm.add_argument('session_dir'); sm.add_argument('--json-file',required=True)
    a=sub.add_parser('accept-setup'); a.add_argument('session_dir'); a.add_argument('--overrides-json')
    f=sub.add_parser('freeze-dods'); f.add_argument('session_dir'); f.add_argument('--additional-json')
    r=sub.add_parser('research-plan'); r.add_argument('session_dir')
    v=sub.add_parser('validate-claims'); v.add_argument('session_dir')
    sim=sub.add_parser('record-simulation'); sim.add_argument('session_dir'); sim.add_argument('--json-file',required=True)
    comp=sub.add_parser('record-compression'); comp.add_argument('session_dir'); comp.add_argument('--json-file',required=True)
    q=sub.add_parser('audit-chapter'); q.add_argument('session_dir'); q.add_argument('--text-file',required=True); q.add_argument('--reference-file'); q.add_argument('--prior-file',action='append',default=[]); q.add_argument('--artifact-evidence-json')
    g=sub.add_parser('gate'); g.add_argument('session_dir')
    d=sub.add_parser('dashboard'); d.add_argument('session_dir')
    args=p.parse_args(argv); contract=load_contract_text()
    if args.command=='terms': print(contract); return 0
    if args.command=='accept':
        receipt=issue_receipt(contract,phrase=args.phrase,actor_type=args.actor_type,evidence_type=args.evidence_type,user_message=args.user_message); Path(args.out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(args.out); return 0
    if args.command=='probe': print(json.dumps(probe_capabilities(admission_receipt=_receipt(args.receipt),contract_text=contract),indent=2)); return 0
    if args.command=='initialize': print(initialize(args.request,args.root,args.session_id,admission_receipt=_receipt(args.receipt),contract_text=contract)); return 0
    ws=_ws(args.session_dir); state=ws.load()
    ok,_=validate_receipt((state.admission or {}).get('receipt'),contract)
    if not ok: raise PermissionError('session admission receipt is missing or stale')
    if args.command=='mine': ingest_and_mine(state,Path(args.text_file).read_text(encoding='utf-8'),source_id=args.source_id,chapter=args.chapter); ws.save(state); update_dashboard(ws.base); print(state.phase); return 0
    if args.command=='semantic-mining':
        payload=json.loads(Path(args.json_file).read_text(encoding='utf-8')); report=register_semantic_mining(state,payload.get('units',[]),payload.get('relations',[])); ws.save(state); update_dashboard(ws.base); print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if report.get('status')=='PASS' else 2
    if args.command=='accept-setup': apply_setup(state,json.loads(args.overrides_json) if args.overrides_json else None); ws.save(state); update_dashboard(ws.base); print(json.dumps(state.setup,ensure_ascii=False,indent=2)); return 0
    if args.command=='freeze-dods': freeze_dods(state,json.loads(args.additional_json) if args.additional_json else None); ws.save(state); update_dashboard(ws.base); return 0
    if args.command=='research-plan': build_research_plan(state); ws.save(state); print(json.dumps(state.source_intelligence['research_plan'],ensure_ascii=False,indent=2)); return 0
    if args.command=='validate-claims': errs=validate_claim_ledger(state); ws.save(state); print(json.dumps(errs,ensure_ascii=False,indent=2)); return 1 if errs else 0
    if args.command=='record-simulation': record_simulation(state,json.loads(Path(args.json_file).read_text(encoding='utf-8'))); ws.save(state); update_dashboard(ws.base); return 0
    if args.command=='record-compression': record_compression(state,json.loads(Path(args.json_file).read_text(encoding='utf-8'))); ws.save(state); update_dashboard(ws.base); return 0
    if args.command=='audit-chapter':
        text=Path(args.text_file).read_text(encoding='utf-8'); ref=Path(args.reference_file).read_text(encoding='utf-8') if args.reference_file else None; priors=[Path(x).read_text(encoding='utf-8') for x in args.prior_file]; ev=json.loads(Path(args.artifact_evidence_json).read_text(encoding='utf-8')) if args.artifact_evidence_json else None; report=audit_candidate_chapter(state,text,reference_text=ref,prior_texts=priors,artifact_evidence=ev); ws.save(state); update_dashboard(ws.base); print(json.dumps(report,ensure_ascii=False,indent=2)); return 1 if report.get('status')!='PASS' else 0
    if args.command=='gate': evaluate_completion(state); ws.save(state); update_dashboard(ws.base); print(json.dumps(state.completion,ensure_ascii=False,indent=2)); return 0 if state.completion['eligible'] else 2
    if args.command=='dashboard': print(update_dashboard(ws.base)); return 0
    return 1
