from __future__ import annotations
from typing import Any
from .consolidation import canonical_digest, CANDIDATE_ROLE
from .modes import COMPRESSION_CONSOLIDATION, normalize_mode

REVIEW_SCHEMA="juriscribe-consolidation-peer-review-readiness/v1"
PROVENANCE_SCHEMA="juriscribe-consolidation-provenance/v1"
FINAL_REVIEW_SCHEMA="juriscribe-consolidation-final-review/v1"


def _cc(state): return state.strategy.setdefault("consolidation",{})

def record_peer_review_readiness(state, payload: dict[str,Any]):
    if normalize_mode(state.mode)!=COMPRESSION_CONSOLIDATION: raise ValueError("peer-review readiness is C&C-only")
    cc=_cc(state); candidates=[c for c in state.corpus if c.get("role")==CANDIDATE_ROLE]; sealed=cc.get("refined_candidates") or {}; errors=[]
    if any(c.get("source_id") not in sealed for c in candidates): errors.append("all candidate materials must be sealed before readiness review")
    if not cc.get("mutation_receipt") or not cc.get("saturation"): errors.append("mutation and dual saturation required")
    dimensions=dict(payload.get("dimensions") or {})
    required={"scientific_consistency","editorial_coherence","argument_strength","local_progression","reticular_progression","semantic_losslessness","canonical_conditioning"}
    missing=required-set(dimensions)
    if missing: errors.append("peer-review readiness dimensions missing: "+", ".join(sorted(missing)))
    blockers=list(payload.get("blockers") or [])
    if blockers: errors.append("peer-review readiness has open blockers")
    rec={"schema":REVIEW_SCHEMA,"plan_digest":str((cc.get("refactoring_contract") or {}).get("digest") or ""),"reticulum_digest":str(state.reticulum.get("digest") or ""),"dimensions":dimensions,"blockers":blockers,"status":"PASS" if not errors else "FAIL","errors":errors,"claim":"READY_FOR_PEER_REVIEW_NOT_PEER_REVIEWED"}
    rec["digest"]=canonical_digest(rec); cc["peer_review_readiness"]=rec; state.review["status"]="PEER_REVIEW_READY" if not errors else "REVIEW_REQUIRED"; state.phase="PEER_REVIEW_READY" if not errors else "SCIENTIFIC_EDITORIAL_REVIEW"; return rec

def record_consolidation_provenance(state,payload: dict[str,Any]):
    if normalize_mode(state.mode)!=COMPRESSION_CONSOLIDATION: raise ValueError("C&C provenance only")
    cc=_cc(state); plan=cc.get("refactoring_contract") or {}; errors=[]; dispositions=list(payload.get("dispositions") or [])
    ids={str(x.get("id")) for x in dispositions if x.get("id")}; required_ops={str(x.get("id")) for x in plan.get("operations",[]) if x.get("operation")!="KEEP"}; required_sources={str(c.get("source_id")) for c in state.corpus if c.get("role")==CANDIDATE_ROLE}
    covered_ops={str(x.get("operation_id")) for x in dispositions if x.get("operation_id")}; covered_sources={str(x.get("source_id")) for x in dispositions if x.get("source_id")}
    if required_ops-covered_ops: errors.append("provenance missing transformed operations")
    if required_sources-covered_sources: errors.append("provenance missing candidate source disposition")
    if not ids: errors.append("provenance dispositions missing stable ids")
    rec={"schema":PROVENANCE_SCHEMA,"plan_digest":str(plan.get("digest") or ""),"reticulum_digest":str(state.reticulum.get("digest") or ""),"dispositions":dispositions,"status":"PASS" if not errors else "FAIL","errors":errors}; rec["digest"]=canonical_digest(rec); cc["provenance"]=rec; state.provenance=rec; state.phase="PROVENANCE"; return rec

def record_consolidation_final_review(state,payload: dict[str,Any]):
    if normalize_mode(state.mode)!=COMPRESSION_CONSOLIDATION: raise ValueError("C&C final review only")
    cc=_cc(state); errors=[]
    if (cc.get("peer_review_readiness") or {}).get("status")!="PASS": errors.append("peer-review readiness PASS required")
    if (cc.get("provenance") or {}).get("status")!="PASS": errors.append("provenance PASS required")
    if str(payload.get("status") or "").upper()!="PASS": errors.append("final severe review must PASS")
    if payload.get("plan_digest")!=str((cc.get("refactoring_contract") or {}).get("digest") or ""): errors.append("final review bound to stale plan")
    if payload.get("reticulum_digest")!=str(state.reticulum.get("digest") or ""): errors.append("final review bound to stale reticulum")
    rec={"schema":FINAL_REVIEW_SCHEMA,"plan_digest":payload.get("plan_digest"),"reticulum_digest":payload.get("reticulum_digest"),"findings":list(payload.get("findings") or []),"status":"PASS" if not errors else "FAIL","errors":errors}; rec["digest"]=canonical_digest(rec); cc["final_review"]=rec; state.final_review=rec; state.phase="FINAL_REVIEWED" if not errors else "FINAL_REVIEW_REQUIRED"; return rec
