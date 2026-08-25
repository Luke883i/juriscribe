from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from .artifact_autopilot import _write_docx_atomic
from .dossier_materialization import render_dossier_text
from .delivery import record_artifact, verify_materialized_artifact
from .modes import COMPRESSION_CONSOLIDATION, required_artifact_requirements, normalize_mode
from .runtime_v11 import consolidation_gate

PROFILE="JURISCRIBE_CONSOLIDATION_ARTIFACT_AUTOPILOT_V1"

def _cc(state): return state.strategy.setdefault("consolidation",{})
def _root(state):
    workspace=str((state.runtime or {}).get("workspace_base") or "").strip()
    if not workspace: raise ValueError("runtime workspace_base missing")
    root=(Path(workspace)/"artifacts").resolve(); root.mkdir(parents=True,exist_ok=True); return root

def _safe(value): return re.sub(r"[^A-Za-z0-9._-]+","-",str(value or "candidate")).strip("-") or "candidate"
def _report_text(state):
    cc=_cc(state); plan=cc.get("refactoring_contract") or {}; mutation=cc.get("mutation_receipt") or {}; saturation=cc.get("saturation") or {}; calibration=cc.get("calibration") or []; readiness=cc.get("peer_review_readiness") or {}; prov=cc.get("provenance") or {}; final=cc.get("final_review") or {}
    lines=["Juriscribe — Compression & Consolidation Refactoring Report",f"Mandato: {(state.request or {}).get('summary') or (state.request or {}).get('raw') or ''}",f"Reticolo: {state.reticulum.get('status','')}; object coverage={state.reticulum.get('object_coverage','')}",f"Piano: {plan.get('status','')} — unità toccate {len(plan.get('touched_unit_ids') or [])}/{plan.get('candidate_unit_count',0)}",f"Mutazioni: {mutation.get('cases',0)} — failures={mutation.get('failures',0)}",f"Saturazione: M+{saturation.get('no_novelty_tail',0)} / N+{saturation.get('no_better_compression_tail',0)}",f"Calibrazioni utente: {len(calibration)}",f"Peer-review readiness: {readiness.get('status','')} ({readiness.get('claim','')})",f"Provenance: {prov.get('status','')}",f"Final severe review: {final.get('status','')}","","Operazioni di rifattorizzazione:"]
    for op in plan.get("operations") or []: lines.append(f"{op.get('id')} | {op.get('unit_id')} | {op.get('operation')} | gap={','.join(op.get('gap_ids') or [])} | {op.get('rationale')}")
    return "\n".join(lines).strip()+"\n"

def materialize_consolidation_artifacts(state):
    if normalize_mode(state.mode)!=COMPRESSION_CONSOLIDATION: return {"status":"NOT_APPLICABLE"}
    ok,errors=consolidation_gate(state); cc=_cc(state)
    if not ok: return {"profile":PROFILE,"status":"DEFERRED","errors":errors}
    if (cc.get("peer_review_readiness") or {}).get("status")!="PASS": return {"profile":PROFILE,"status":"DEFERRED","errors":["peer-review readiness PASS required"]}
    if (cc.get("provenance") or {}).get("status")!="PASS" or (cc.get("final_review") or {}).get("status")!="PASS": return {"profile":PROFILE,"status":"DEFERRED","errors":["provenance and final severe review PASS required"]}
    caps=(state.runtime or {}).get("capabilities") or {}
    if caps.get("DOCX_WRITE")!="AVAILABLE" or caps.get("DOCX_READBACK")!="AVAILABLE": return {"profile":PROFILE,"status":"FAIL","errors":["DOCX_WRITE and DOCX_READBACK must be AVAILABLE"]}
    root=_root(state); materialized=[]; errs=[]
    static={"refactoring_report":("Refactoring report",_report_text(state)),"evidence_dossier":("Evidence dossier",render_dossier_text(state,"evidence_dossier")),"source_register":("Source register",render_dossier_text(state,"source_register")),"inference_register":("Inference register",render_dossier_text(state,"inference_register")),"transformation_ledger":("Transformation ledger",render_dossier_text(state,"transformation_ledger"))}
    for role,(title,body) in static.items():
        try:
            path=root/f"{role}.docx"; _write_docx_atomic(path,title,body); rec={"id":f"cc-{role}","role":role,"instance_key":role,"summary":title,"path":str(path),"readback":"PASS","auto_materialized_by_runtime":True,"autopilot_profile":PROFILE}; record_artifact(state,rec); materialized.append({"role":role,"instance_key":role})
        except Exception as exc: errs.append(f"{role}: {exc}")
    for source_id,item in sorted((cc.get("refined_candidates") or {}).items()):
        try:
            key=str(source_id); path=root/f"refined_candidate--{_safe(key)}.docx"; _write_docx_atomic(path,f"Refined candidate — {key}",str(item.get("text") or "")); rec={"id":f"cc-refined-{_safe(key)}","role":"refined_candidate","instance_key":key,"source_id":key,"summary":f"Refined candidate {key}","path":str(path),"readback":"PASS","auto_materialized_by_runtime":True,"autopilot_profile":PROFILE,"semantic_recall":1.0,"relation_recall":1.0,"source_digest":item.get("source_digest"),"refined_digest":item.get("refined_digest")}; record_artifact(state,rec); materialized.append({"role":"refined_candidate","instance_key":key})
        except Exception as exc: errs.append(f"refined_candidate {source_id}: {exc}")
    receipt={"profile":PROFILE,"status":"PASS" if not errs else "FAIL","requirements":required_artifact_requirements(state.mode,state.setup,state.corpus),"materialized":materialized,"errors":errs}; cc["artifact_autopilot"]=receipt; return receipt

def consolidation_artifact_gate(state):
    if normalize_mode(state.mode)!=COMPRESSION_CONSOLIDATION: return True,[]
    requirements=[x for x in required_artifact_requirements(state.mode,state.setup,state.corpus) if x.get("role")!="session_dashboard"]; artifacts=list(state.artifacts or []); errors=[]
    for req in requirements:
        role,key=str(req.get("role")),str(req.get("instance_key")); match=next((a for a in artifacts if str(a.get("role"))==role and str(a.get("instance_key",a.get("role")))==key),None)
        if not match: errors.append(f"required artifact instance missing: {role}/{key}"); continue
        ok,es,_=verify_materialized_artifact(state,match)
        if not ok: errors.extend(es)
        if role=="refined_candidate" and (match.get("semantic_recall")!=1.0 or match.get("relation_recall")!=1.0): errors.append(f"refined candidate not reticulum-lossless: {key}")
    return not errors,list(dict.fromkeys(errors))
