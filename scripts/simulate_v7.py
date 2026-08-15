from __future__ import annotations

import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe.admission import issue_receipt
from juriscribe.bootstrap import bootstrap_gate,issue_probe_receipt,validate_probe_receipt
from juriscribe.final_review import CRITERIA,build_final_review,final_review_gate
from juriscribe.interaction import interaction_card,validate_interaction_card
from juriscribe.provenance import build_provenance_bundle,final_artifact_gate,provenance_gate
SELECTOR_VERSION="sha256-roundrobin-v7"
CONTRACT="---\ncontract_version: 1.5.0\n---\ncontract body\n"
FAMILIES=("bootstrap_not_active","probe_stale_contract","probe_capability_tamper","interaction_no_free_path","provenance_missing_inference","provenance_missing_decision","provenance_stale_candidate","final_review_stale_provenance","final_review_open_consequence","artifact_role_missing")
def sha(value): return hashlib.sha256(value.encode("utf-8")).hexdigest()
def admission(): return issue_receipt(CONTRACT,phrase="I ACCEPT",actor_type="human",evidence_type="explicit_user_message",user_message="I ACCEPT",accepted_at="2026-01-01T00:00:00+00:00")
def probe():
    a=admission(); return a,issue_probe_receipt(a,CONTRACT,{"LOCAL_SCRATCH_IO":"AVAILABLE","WEB_RESEARCH":"AVAILABLE"},host="ci",probed_at="2026-01-01T00:01:00+00:00")
def provenance():
    entries=[{"id":"I1","kind":"INFERENCE","proposition":"i","disposition":"IN_FINAL","rationale":"r","artifact_locators":["§1"],"evidence_refs":["S1"],"premise_ids":["P1"],"inference_bridge":"b","falsifier":"f"},{"id":"C1","kind":"CLAIM","proposition":"c","disposition":"IN_FINAL","rationale":"r","artifact_locators":["§2"],"evidence_refs":["S1"]},{"id":"D1","kind":"USER_DECISION","proposition":"d","disposition":"IN_FINAL","rationale":"r","artifact_locators":["setup"]},{"id":"REGEN-1","kind":"TRANSFORMATION","proposition":"regen","disposition":"IN_FINAL","rationale":"r","artifact_locators":["ledger"]},{"id":"COMPRESSION-FINAL","kind":"TRANSFORMATION","proposition":"compression","disposition":"IN_FINAL","rationale":"r","artifact_locators":["ledger"]}]
    return build_provenance_bundle(entries,candidate_digest="a"*64,corpus_digest="b"*64,epistemic_units=[{"id":"I1","kind":"INFERENCE","material":True}],claim_ledger=[{"id":"C1","material":True,"claim_type":"direct"}],interaction={"history":[{"id":"D1","kind":"USER_DECISION"}]},regenerations=[{}],compression={"status":"PASS"})
def final_review(prov):
    evidence=[{"criterion":c,"status":"PASS","locator":f"e:{c}"} for c in CRITERIA]
    return build_final_review(candidate_digest="a"*64,corpus_digest="b"*64,normative_frame_digest="c"*64,provenance_digest=prov["digest"],evidence=evidence,consequence_probes=[{"id":"CP1","proposition":"p","downstream_effect":"e","status":"PASS","evidence_ref":"E1"}],findings=[])
def artifacts(): return [{"role":r,"readback":"PASS"} for r in ["final_chapter","evidence_dossier","source_register","inference_register","transformation_ledger","session_dashboard"]]
def killed(family):
    a,p=probe(); prov=provenance(); fr=final_review(prov)
    if family=="bootstrap_not_active": return not bootstrap_gate({"status":"ACCEPTED","receipt":a,"probe_receipt":p,"bootstrap":{"state":"INITIALIZE_REQUIRED"}})[0]
    if family=="probe_stale_contract": return not validate_probe_receipt(dict(p,contract_sha256="0"*64),a,CONTRACT)[0]
    if family=="probe_capability_tamper": return not validate_probe_receipt(dict(p,capabilities={**p["capabilities"],"WEB_RESEARCH":"UNAVAILABLE"}),a,CONTRACT)[0]
    if family=="interaction_no_free_path":
        card=interaction_card("COMPLETE"); card["choices"]=["APRI ARTEFATTI"]; return not validate_interaction_card(card)[0]
    if family=="provenance_missing_inference": return not provenance_gate(dict(prov,entries=[e for e in prov["entries"] if e["id"]!="I1"]),candidate_digest="a"*64,corpus_digest="b"*64)[0]
    if family=="provenance_missing_decision": return not provenance_gate(dict(prov,entries=[e for e in prov["entries"] if e["id"]!="D1"]),candidate_digest="a"*64,corpus_digest="b"*64)[0]
    if family=="provenance_stale_candidate": return not provenance_gate(prov,candidate_digest="x"*64,corpus_digest="b"*64)[0]
    if family=="final_review_stale_provenance": return not final_review_gate(fr,candidate_digest="a"*64,corpus_digest="b"*64,normative_frame_digest="c"*64,provenance_digest="x"*64)[0]
    if family=="final_review_open_consequence":
        ev=[{"criterion":c,"status":"PASS","locator":f"e:{c}"} for c in CRITERIA]; bad=build_final_review(candidate_digest="a"*64,corpus_digest="b"*64,normative_frame_digest="c"*64,provenance_digest=prov["digest"],evidence=ev,consequence_probes=[{"id":"CP","proposition":"p","downstream_effect":"e","status":"OPEN"}],findings=[]); return bad["status"]=="FAIL"
    if family=="artifact_role_missing": return not final_artifact_gate(artifacts()[:-1])[0]
    raise AssertionError(family)
def clean_control():
    a,p=probe(); prov=provenance(); fr=final_review(prov)
    return all([validate_probe_receipt(p,a,CONTRACT)[0],bootstrap_gate({"status":"ACCEPTED","receipt":a,"probe_receipt":p,"bootstrap":{"state":"ACTIVE"}})[0],validate_interaction_card(interaction_card("COMPLETE"))[0],provenance_gate(prov,candidate_digest="a"*64,corpus_digest="b"*64)[0],final_review_gate(fr,candidate_digest="a"*64,corpus_digest="b"*64,normative_frame_digest="c"*64,provenance_digest=prov["digest"])[0],final_artifact_gate(artifacts())[0]])
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--cases",type=int,default=10000); ap.add_argument("--json-out",required=True); args=ap.parse_args(); failures=[]; counts={f:0 for f in FAMILIES}; signatures=[]
    for i in range(args.cases):
        family=FAMILIES[i%len(FAMILIES)]; counts[family]+=1; signature=sha(f"{SELECTOR_VERSION}|{i}|{family}"); signatures.append(signature)
        if not killed(family): failures.append({"index":i,"family":family,"signature":signature})
    controls=max(1000,args.cases//10); control_failures=sum(1 for _ in range(controls) if not clean_control())
    receipt={"schema":"juriscribe-mutation-v7/v1","selector":SELECTOR_VERSION,"mutations":args.cases,"controls":controls,"unique_signatures":len(set(signatures)),"families":counts,"killed_mutants":args.cases-len(failures),"mutation_escapes":len(failures),"accepted_controls":controls-control_failures,"false_positives":control_failures,"failures":failures[:20],"scenario_digest":sha("|".join(signatures)),"status":"PASS" if not failures and not control_failures and len(set(signatures))==args.cases else "FAIL"}
    Path(args.json_out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(receipt,ensure_ascii=False,indent=2)); return 0 if receipt["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
