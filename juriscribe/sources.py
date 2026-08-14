from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

AUTHORITY_RANK = {
    "primary_law":100,"constitutional_court":95,"supreme_court":92,"eu_court":92,"echr":90,
    "administrative_supreme_court":90,"official_institutional":85,"peer_reviewed_doctrine":75,
    "leading_treatise":72,"specialist_commentary":60,"other":30,
}
JURISPRUDENCE_TYPES={"constitutional_court","supreme_court","eu_court","echr","administrative_supreme_court"}
DOCTRINE_TYPES={"peer_reviewed_doctrine","leading_treatise","specialist_commentary"}

def now_iso()->str: return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class SourceRecord:
    id:str; title:str; url:str; source_type:str; jurisdiction:str|None=None; court_or_author:str|None=None; date:str|None=None; verified_at:str|None=None; direct_read:bool=False; primary:bool=False; notes:str=""; bibliography_entry:str=""; role:str="external_source"
    def record(self)->dict[str,Any]:
        data=asdict(self); data["authority_rank"]=AUTHORITY_RANK.get(self.source_type,AUTHORITY_RANK["other"]); data["verified_at"]=self.verified_at or (now_iso() if self.direct_read else None); return data

@dataclass(frozen=True)
class ClaimRecord:
    id:str; text:str; claim_type:str; scope:str; support_source_ids:tuple[str,...]=(); premise_claim_ids:tuple[str,...]=(); inference_bridge:str=""; falsifier:str=""; status:str="UNVERIFIED"; material:bool=True; source_evidence:tuple[dict[str,Any],...]=()
    def record(self)->dict[str,Any]:
        data=asdict(self); data["support_source_ids"]=list(self.support_source_ids); data["premise_claim_ids"]=list(self.premise_claim_ids); data["source_evidence"]=[dict(x) for x in self.source_evidence]; return data

def validate_claim(claim:dict[str,Any],sources:list[dict[str,Any]],claims:list[dict[str,Any]],*,strict:bool=False)->tuple[bool,list[str]]:
    errors=[]; by_source={s.get("id"):s for s in sources}; by_claim={c.get("id"):c for c in claims}; ctype=claim.get("claim_type"); support=claim.get("support_source_ids",[]); premises=claim.get("premise_claim_ids",[])
    if claim.get("material",True) and ctype not in {"interpretive_proposal","editorial"} and not support and not premises: errors.append("material claim has no source or premise support")
    if any(sid not in by_source for sid in support): errors.append("claim references unknown source")
    if any(cid not in by_claim for cid in premises): errors.append("claim references unknown premise")
    if ctype=="strong_inference":
        if not premises: errors.append("strong inference requires premises")
        if not claim.get("inference_bridge","").strip(): errors.append("strong inference requires an explicit bridge")
        if not claim.get("falsifier","").strip(): errors.append("strong inference requires a falsifier")
        for cid in premises:
            premise=by_claim.get(cid,{})
            if strict and premise.get("status") not in {"SUPPORTED","VERIFIED","INFERRED"}: errors.append(f"strong inference premise {cid} is not supported")
    if strict and claim.get("material",True):
        evidence={e.get("source_id"):e for e in claim.get("source_evidence",[]) if e.get("source_id")}
        for sid in support:
            source=by_source.get(sid,{})
            if not source.get("direct_read"): errors.append(f"source {sid} was not directly read")
            if not source.get("verified_at"): errors.append(f"source {sid} has no verification timestamp")
            ev=evidence.get(sid)
            if not ev: errors.append(f"source {sid} has no claim-level evidence record")
            elif not str(ev.get("pinpoint","")).strip(): errors.append(f"source {sid} evidence has no pinpoint")
            elif not str(ev.get("proposition","")).strip(): errors.append(f"source {sid} evidence has no scoped proposition")
    return not errors,errors

def validate_inference_graph(claims:list[dict[str,Any]])->tuple[bool,list[str]]:
    by_id={c.get("id"):c for c in claims}; graph={cid:list(c.get("premise_claim_ids",[])) for cid,c in by_id.items() if c.get("claim_type")=="strong_inference"}; errors=[]
    visiting=set(); visited=set()
    def dfs(node):
        if node in visiting: errors.append(f"cyclic inference dependency at {node}"); return
        if node in visited: return
        visiting.add(node)
        for dep in graph.get(node,[]):
            if dep in graph: dfs(dep)
        visiting.remove(node); visited.add(node)
    for node in graph: dfs(node)
    return not errors,errors

def assess_dominance(label:str,candidates:list[dict[str,Any]],*,minimum_independent_sources:int=3,kind:str="general")->dict[str,Any]:
    verified=[c for c in candidates if c.get("direct_read") and c.get("verified_at")]
    if kind=="jurisprudence": verified=[c for c in verified if c.get("source_type") in JURISPRUDENCE_TYPES]
    elif kind=="doctrine": verified=[c for c in verified if c.get("source_type") in DOCTRINE_TYPES]
    independent={(c.get("court_or_author") or c.get("id"),c.get("source_type")) for c in verified}; high=[c for c in verified if c.get("authority_rank",0)>=72]
    counter=[c for c in verified if "counter" in str(c.get("notes","")).lower()]
    sufficient=len(independent)>=minimum_independent_sources and len(high)>=minimum_independent_sources and not counter
    return {"label":label,"kind":kind,"status":"SUPPORTED_DOMINANT" if sufficient else "DOMINANCE_NOT_ESTABLISHED","verified_sources":len(verified),"independent_sources":len(independent),"high_authority_sources":len(high),"counter_authorities":len(counter),"rule":"search rank and repetition alone never establish dominance"}

def research_plan(claims:list[dict[str,Any]])->list[dict[str,Any]]:
    return [{"claim_id":c.get("id"),"query_goal":c.get("text","")[:240],"preferred_sources":["primary_law","constitutional_court","supreme_court","eu_court","echr","official_institutional","peer_reviewed_doctrine","leading_treatise"],"require_direct_read":True,"require_date_and_scope":True,"require_pinpoint":True} for c in claims if c.get("material",True)]
