from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "juriscribe-provenance-bundle/v1"
DISPOSITIONS = {"IN_FINAL", "SUPERSEDED", "REJECTED", "DEFERRED", "NOT_APPLICABLE"}
ENTRY_KINDS = {"INFERENCE", "CLAIM", "USER_DECISION", "TRANSFORMATION", "QUALIFICATION", "LIMIT"}
REQUIRED_FINAL_ARTIFACT_ROLES = {
    "final_chapter",
    "evidence_dossier",
    "source_register",
    "inference_register",
    "transformation_ledger",
    "session_dashboard",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def expected_provenance_ids(epistemic_units, claim_ledger, interaction, regenerations, compression):
    inference_ids = {str(u.get("id")) for u in epistemic_units if u.get("kind") == "INFERENCE" and bool(u.get("material", True)) and u.get("id")}
    inference_ids.update({str(c.get("id")) for c in claim_ledger if c.get("claim_type") == "strong_inference" and bool(c.get("material", True)) and c.get("id")})
    claim_ids = {str(c.get("id")) for c in claim_ledger if bool(c.get("material", True)) and c.get("claim_type") != "strong_inference" and c.get("id")}
    decisions = {str(h.get("id")) for h in (interaction or {}).get("history", []) if h.get("kind") == "USER_DECISION" and h.get("id")}
    transformations = {f"REGEN-{idx+1}" for idx, _ in enumerate(regenerations or [])}
    if compression:
        transformations.add("COMPRESSION-FINAL")
    return {"INFERENCE": inference_ids, "CLAIM": claim_ids, "USER_DECISION": decisions, "TRANSFORMATION": transformations}


def build_provenance_bundle(entries, *, candidate_digest, corpus_digest, epistemic_units, claim_ledger, interaction=None, regenerations=None, compression=None):
    expected = expected_provenance_ids(epistemic_units, claim_ledger, interaction, regenerations, compression)
    errors=[]; seen=set(); covered={k:set() for k in expected}; normalized=[]
    for idx, raw in enumerate(entries or []):
        item=dict(raw); eid=str(item.get("id","")).strip(); kind=str(item.get("kind","")).upper()
        if not eid: errors.append(f"provenance entry {idx} id missing"); continue
        if eid in seen: errors.append(f"duplicate provenance entry {eid}")
        seen.add(eid)
        if kind not in ENTRY_KINDS: errors.append(f"provenance entry {eid} kind invalid")
        disposition=item.get("disposition")
        if disposition not in DISPOSITIONS: errors.append(f"provenance entry {eid} disposition invalid")
        if not str(item.get("proposition","")).strip(): errors.append(f"provenance entry {eid} proposition missing")
        if not str(item.get("rationale","")).strip(): errors.append(f"provenance entry {eid} rationale missing")
        if disposition == "IN_FINAL" and not item.get("artifact_locators"): errors.append(f"provenance entry {eid} IN_FINAL has no artifact locator")
        if kind in {"INFERENCE","CLAIM"} and not item.get("evidence_refs"): errors.append(f"provenance entry {eid} has no evidence refs")
        if kind == "INFERENCE":
            if not item.get("premise_ids"): errors.append(f"provenance inference {eid} premises missing")
            if not str(item.get("inference_bridge","")).strip(): errors.append(f"provenance inference {eid} bridge missing")
            if not str(item.get("falsifier","")).strip(): errors.append(f"provenance inference {eid} falsifier missing")
        if kind in covered and eid in expected[kind]: covered[kind].add(eid)
        item["kind"]=kind; normalized.append(item)
    missing={}
    for kind, ids in expected.items():
        gap=sorted(ids-covered[kind])
        if gap: missing[kind]=gap; errors.append(f"provenance missing {kind.lower()} ids: "+", ".join(gap))
    total_expected=sum(len(v) for v in expected.values()); total_covered=sum(len(v) for v in covered.values())
    coverage=1.0 if total_expected==0 else round(total_covered/total_expected,4)
    bundle={"schema":SCHEMA,"candidate_digest":candidate_digest,"corpus_digest":corpus_digest,"entries":normalized,"expected_ids":{k:sorted(v) for k,v in expected.items()},"missing_ids":missing,"coverage":coverage,"required_artifact_roles":sorted(REQUIRED_FINAL_ARTIFACT_ROLES),"status":"PASS" if not errors and coverage==1.0 else "FAIL","errors":list(dict.fromkeys(errors))}
    bundle["digest"]=canonical_digest({k:v for k,v in bundle.items() if k!="digest"}); return bundle


def provenance_gate(bundle, *, candidate_digest=None, corpus_digest=None):
    if not bundle: return False,["provenance bundle missing"]
    errors=list(bundle.get("errors",[]))
    if bundle.get("schema")!=SCHEMA: errors.append("provenance schema mismatch")
    if bundle.get("status")!="PASS": errors.append("provenance status is not PASS")
    if float(bundle.get("coverage",0.0) or 0.0)!=1.0: errors.append("provenance coverage is not lossless")
    if candidate_digest is not None and bundle.get("candidate_digest")!=candidate_digest: errors.append("provenance bound to stale candidate")
    if corpus_digest is not None and bundle.get("corpus_digest")!=corpus_digest: errors.append("provenance bound to stale corpus")
    if bundle.get("digest")!=canonical_digest({k:v for k,v in bundle.items() if k!="digest"}): errors.append("provenance digest mismatch")
    return not errors,list(dict.fromkeys(errors))


def final_artifact_gate(artifacts):
    by_role={str(a.get("role")):a for a in (artifacts or []) if a.get("role")}; errors=[]
    for role in sorted(REQUIRED_FINAL_ARTIFACT_ROLES):
        record=by_role.get(role)
        if not record: errors.append(f"required final artifact role missing: {role}"); continue
        if record.get("readback")!="PASS": errors.append(f"required final artifact readback failed: {role}")
    return not errors,errors
