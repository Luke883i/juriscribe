from __future__ import annotations
import copy, hashlib, json
from dataclasses import asdict, is_dataclass
from typing import Any
SCHEMA="juriscribe-continuity/v1"; MATERIAL_SCHEMA="juriscribe-continuity-material/v1"; ITERATION_SCHEMA="juriscribe-iteration-projection/v1"
ITERATION_AUTHORITY="PROJECTION_ONLY"; ARCHIVE_AUTHORITY="NO_INDEPENDENT_AUTHORITY"; AUTHORITY=ITERATION_AUTHORITY
RECOVERY_ACTION="RECOVERY BUNDLE"; MATERIALIZATION_CONTINUE_PHRASE="Continue until the end of artefact materialization"; MATERIALIZATION_PENDING="MATERIALIZATION_PENDING"
def canonical_digest(v:Any)->str:return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def _state(s):
    if isinstance(s,dict): return s
    if is_dataclass(s): return asdict(s)
    return dict(getattr(s,"__dict__",{}))
def _strategy(s,create=False):
    if isinstance(s,dict): v=s.setdefault("strategy",{}) if create else (s.get("strategy") or {})
    else:
        v=getattr(s,"strategy",None)
        if v is None and create:v={};setattr(s,"strategy",v)
        v=v or {}
    if not isinstance(v,dict):raise TypeError("state.strategy must be a mapping")
    return v
def continuity_state(s,create=False):
    st=_strategy(s,create)
    if not create:return st.get("continuity") or {}
    v=st.setdefault("continuity",{"schema":SCHEMA,"materials":{},"status":"READY"})
    if not isinstance(v,dict):raise TypeError("state.strategy.continuity must be a mapping")
    return v
def archive_material(s,text,*,source_id,role,chapter=None):
    source_id=str(source_id or "").strip();role=str(role or "").strip().lower();text=str(text or "")
    if not source_id or not role:raise ValueError("continuity source_id and role required")
    raw=text.encode();sha=hashlib.sha256(raw).hexdigest(); corpus=next((x for x in (_state(s).get("corpus") or []) if str(x.get("source_id") or "")==source_id),None)
    if corpus:
        if str(corpus.get("role") or "").lower() not in {"",role}:raise ValueError("continuity material role differs from corpus role")
        if str(corpus.get("digest") or "") not in {"",sha}:raise ValueError("continuity material text differs from corpus digest")
    r={"schema":MATERIAL_SCHEMA,"source_id":source_id,"role":role,"chapter":chapter,"representation":"RUNTIME_INGESTED_UTF8_TEXT","encoding":"utf-8","text_sha256":sha,"byte_length":len(raw),"character_count":len(text),"text":text};r["digest"]=canonical_digest(r)
    c=continuity_state(s,True);c.setdefault("materials",{})[source_id]=r;c["materials_digest"]=canonical_digest({k:v.get("digest","") for k,v in sorted(c["materials"].items())});c["status"]="READY";return dict(r)
def material_index(s):
    return [{**{k:v for k,v in dict(r).items() if k!="text"},"source_id":str(r.get("source_id") or sid)} for sid,r in sorted((continuity_state(s).get("materials") or {}).items())]
def validate_material_archive(s):
    d=_state(s);c=continuity_state(s);m=c.get("materials") or {};e=[]
    if c and c.get("schema")!=SCHEMA:e.append("continuity schema mismatch")
    for sid,raw in m.items():
        r=dict(raw or {});t=str(r.get("text") or "");b=t.encode()
        if r.get("schema")!=MATERIAL_SCHEMA:e.append(f"continuity material schema mismatch: {sid}")
        if str(r.get("source_id") or "")!=str(sid):e.append(f"continuity material source binding mismatch: {sid}")
        if r.get("text_sha256")!=hashlib.sha256(b).hexdigest():e.append(f"continuity material text digest mismatch: {sid}")
        if int(r.get("byte_length",-1))!=len(b) or int(r.get("character_count",-1))!=len(t):e.append(f"continuity material length mismatch: {sid}")
        if r.get("digest")!=canonical_digest({k:v for k,v in r.items() if k!="digest"}):e.append(f"continuity material record digest mismatch: {sid}")
    for x in d.get("corpus") or []:
        sid=str(x.get("source_id") or "").strip();r=m.get(sid)
        if not sid:e.append("corpus source_id missing");continue
        if not r:e.append(f"runtime input representation missing from continuity archive: {sid}");continue
        if str(x.get("role") or "").lower() not in {"",str(r.get("role") or "").lower()}:e.append(f"continuity material role mismatch: {sid}")
        if str(x.get("digest") or "") not in {"",str(r.get("text_sha256") or "")}:e.append(f"continuity material/corpus digest mismatch: {sid}")
    expected=canonical_digest({k:v.get("digest","") for k,v in sorted(m.items())})
    if m and c.get("materials_digest")!=expected:e.append("continuity materials aggregate digest mismatch")
    return not e,list(dict.fromkeys(e))
def _checkpoint_payload(s):
    d=copy.deepcopy(_state(s))
    for k in ("updated_at","runtime","phase","interaction","completion","dashboard_persistence","node_integrity","artifacts"):d.pop(k,None)
    a=d.get("admission") or {}
    if isinstance(a,dict):a.pop("probe_receipt",None);a.pop("bootstrap",None)
    st=d.get("strategy") or {};c=st.get("continuity") or {} if isinstance(st,dict) else {}
    if isinstance(c,dict):
        q={k:copy.deepcopy(v) for k,v in c.items() if k not in {"recovery_lineage","export_history"}};q["materials"]={sid:{k:v for k,v in dict(r).items() if k!="text"} for sid,r in sorted((c.get("materials") or {}).items())};st["continuity"]=q
    return d
def checkpoint_id(s):return "CP-"+canonical_digest(_checkpoint_payload(s))[:20]
def _materialization_requirements(s):
    d=_state(s);mode=str(d.get("mode") or "").strip()
    if not mode:return []
    try:
        from .modes import required_artifact_requirements
        return list(required_artifact_requirements(mode,d.get("setup") or {},d.get("corpus") or []))
    except (ImportError,ValueError,TypeError):return []
def _artifact_satisfies(req,a):
    if str(a.get("role") or "")!=str(req.get("role") or ""):return False
    src=str(req.get("source_id") or "").strip(); inst=str(req.get("instance_key") or "").strip(); actual=str(a.get("instance_key") or a.get("role") or "").strip()
    if src and str(a.get("source_id") or "").strip()!=src:return False
    if inst and "*" not in inst and actual!=inst:return False
    return bool(str(a.get("path") or "").strip()) and str(a.get("readback") or "").upper()=="PASS" and not a.get("materialization_stale")
def materialization_status(s):
    d=_state(s);arts=list(d.get("artifacts") or []);complete=bool((d.get("completion") or {}).get("eligible"));st=d.get("strategy") or {};cc=st.get("consolidation") or {} if isinstance(st,dict) else {};mode=str(d.get("mode") or "");phase=str(d.get("phase") or "").upper()
    if mode=="COMPRESSION & CONSOLIDATION":finalized=(cc.get("peer_review_readiness") or {}).get("status")=="PASS" and (cc.get("provenance") or {}).get("status")=="PASS" and (cc.get("final_review") or {}).get("status")=="PASS"
    else:finalized=(d.get("provenance") or {}).get("status")=="PASS" and (d.get("final_review") or {}).get("status")=="PASS"
    finalized=bool(finalized and phase in {"FINAL_SEVERE_REVIEW_PASS","FINAL_REVIEWED","VALIDATING","ARTIFACT_REGISTERED","MATERIALIZING"})
    reqs=_materialization_requirements(s);missing=[str(r.get("instance_key") or r.get("role") or "artifact") for r in reqs if not any(_artifact_satisfies(r,a) for a in arts)];stale=[str(a.get("id") or a.get("role") or "artifact") for a in arts if a.get("materialization_stale") or a.get("readback")=="STALE_RECOVERY"]
    pending=bool(finalized and not complete and (missing or stale));return {"pending":pending,"status":MATERIALIZATION_PENDING if pending else ("COMPLETE" if complete else "NOT_PENDING"),"finalization_ready":finalized,"required_count":len(reqs),"missing":missing,"stale_artifact_ids":stale,"complete":complete and not pending,"continue_phrase":MATERIALIZATION_CONTINUE_PHRASE if pending else ""}
def _milestones(s):
    d=_state(s);st=d.get("strategy") or {};cc=st.get("consolidation") or {} if isinstance(st,dict) else {};r=d.get("review") or {}
    return [("BOOTSTRAP","bootstrap validato",(d.get("admission") or {}).get("status")=="ACCEPTED"),("MODE","modalità selezionata",bool(d.get("mode"))),("INPUT","materiali acquisiti",bool(d.get("corpus"))),("RETICULUM","reticolo epistemico validato",(d.get("reticulum") or {}).get("status")=="PASS"),("SETUP","configurazione utente fissata",(d.get("setup") or {}).get("status")=="ACCEPTED"),("CONTRACT","contratti di lavoro pronti",(d.get("mode_contract") or {}).get("status")=="READY" or (d.get("generation_contract") or {}).get("status")=="READY"),("DOD","DoD materializzati",bool(d.get("dod"))),("WORK_PRODUCT","prodotto di lavoro sigillato",bool(d.get("drafts")) or bool(cc.get("refined_candidates"))),("REVIEW","review avviata o completata",bool(r.get("cycles")) or str(r.get("status") or "") not in {"","NOT_STARTED"}),("FINALIZATION","finalizzazione/provenance avviata",(d.get("final_review") or {}).get("status")=="PASS" or (d.get("provenance") or {}).get("status")=="PASS" or bool(d.get("artifacts"))),("COMPLETE","consegna completa",bool((d.get("completion") or {}).get("eligible")))]
def _card(s):
    i=_state(s).get("interaction") or {};return dict(i.get("card") or {}) if isinstance(i,dict) else {}
def _default_next(phase,missing,complete):
    if complete:return "Lavoro completato; apri gli artefatti, chiedi modifiche o crea un bundle di recupero."
    bp={"TERMS_PRESENTED":"Leggi i termini e accetta solo con messaggio umano esplicito.","PROBE_REQUIRED":"Verifica le capability dell'host.","PROBED":"Inizializza la sessione.","INITIALIZE_REQUIRED":"Inizializza la sessione.","MODE_SELECTION_REQUIRED":"Seleziona una modalità canonica.","MODE_SELECTED":"Fornisci i materiali richiesti dalla modalità.","USER_SETUP_REQUIRED":"Accetta o modifica la configurazione proposta.","HUMAN_DECISION_REQUIRED":"Fornisci la decisione umana materialmente necessaria."};bm={"BOOTSTRAP":"Completa bootstrap e binding dell'host.","MODE":"Seleziona una modalità canonica.","INPUT":"Fornisci i materiali richiesti dalla modalità.","RETICULUM":"Il sistema completerà mining e reticolo epistemico.","SETUP":"Conferma la configurazione utente proposta.","CONTRACT":"Il sistema congelerà i contratti di lavoro.","DOD":"Il sistema materializzerà e congelerà i DoD.","WORK_PRODUCT":"Il sistema produrrà o rifattorizzerà il candidato.","REVIEW":"Il sistema eseguirà review e saturazione.","FINALIZATION":"Il sistema completerà provenance, review finale e materializzazione.","COMPLETE":"Il sistema verificherà completion e consegna."};return bp.get(phase,bm.get(missing,"Il sistema proseguirà autonomamente fino al prossimo gate umano o alla consegna."))
def _how(card,blocking,complete):
    if complete:return "Nessuna azione obbligatoria; usa RECOVERY BUNDLE per uno snapshot o richiedi modifiche."
    choices=[str(x).strip() for x in card.get("choices") or [] if str(x).strip() and str(x).strip()!="ALTRO"]
    if blocking:return ("Scegli "+" / ".join(choices[:3])+" oppure usa ALTRO.") if choices else "Rispondi alla decisione richiesta oppure usa ALTRO."
    return "Automatico: nessuna decisione umana richiesta; Juriscribe prosegue. Usa STATO o RECOVERY BUNDLE quando vuoi."
def project_iteration(s):
    d=_state(s);phase=str(d.get("phase") or "UNKNOWN").upper();ms=_milestones(s);done=[(k,l) for k,l,v in ms if v];missing=next((k for k,_l,v in ms if not v),None);card=_card(s);complete=bool((d.get("completion") or {}).get("eligible")) or phase=="COMPLETE";mat=materialization_status(s);pending=mat["pending"];blocking=bool(card.get("blocking"));n=str(card.get("summary") or "").strip() if blocking and card.get("summary") else _default_next(phase,missing,complete)
    if pending:n="Iterazione conclusa; la materializzazione prevista dalla modalità non è ancora completa."
    actions=[]
    for x in list(card.get("choices") or [])+["STATO",RECOVERY_ACTION,"ARTEFATTI","AIUTO","ALTRO"]:
        x=str(x).strip()
        if x and x not in actions:actions.append(x)
    ok,errs=validate_material_archive(s);ready=True if not d.get("corpus") else ok;status="COMPLETE" if complete else (MATERIALIZATION_PENDING if pending else ("INPUT" if blocking else "WORKING"))
    p={"schema":ITERATION_SCHEMA,"authority":ITERATION_AUTHORITY,"checkpoint_id":checkpoint_id(s),"where":{"phase":phase,"mode":str(d.get("mode") or ""),"stage":"MATERIALIZATION" if pending else (done[-1][0] if done else "START"),"status":status},"done":{"milestones":[k for k,_ in done],"summary":"; ".join(l for _,l in done[-3:]) if done else "nessun milestone sostanziale ancora completato"},"next":{"stage":"MATERIALIZATION" if pending else (missing or "COMPLETE"),"summary":n,"how":f'Indica esattamente: "{MATERIALIZATION_CONTINUE_PHRASE}"' if pending else _how(card,blocking,complete),"requires_user_input":pending or (blocking and not complete)},"actions":actions,"materialization":mat,"recovery":{"on_demand":True,"action":RECOVERY_ACTION,"resume_ready":ready,"errors":[] if ready else errs,"material_count":len(material_index(s))}};p["digest"]=canonical_digest(p);return p
def validate_iteration_projection(s,p):
    if not p:return False,["iteration projection missing"]
    e=[];w=p.get("where") or {};n=p.get("next") or {};a=[str(x) for x in p.get("actions") or []]
    if p.get("schema")!=ITERATION_SCHEMA:e.append("iteration projection schema mismatch")
    if p.get("authority")!=ITERATION_AUTHORITY:e.append("iteration projection authority escalation")
    if not all(k in w for k in ("phase","mode","stage","status")):e.append("iteration where state incomplete")
    if not isinstance(p.get("done"),dict) or not all(k in p["done"] for k in ("summary","milestones")):e.append("iteration done state incomplete")
    if not all(k in n for k in ("summary","how","stage","requires_user_input")):e.append("iteration next state incomplete")
    if RECOVERY_ACTION not in a or "ALTRO" not in a:e.append("iteration control actions incomplete")
    if (p.get("recovery") or {}).get("on_demand") is not True:e.append("iteration recovery must be on demand")
    if p!=project_iteration(s):e.append("iteration projection is stale or not state-derived")
    return not e,list(dict.fromkeys(e))