from __future__ import annotations
from . import governance_delivery as _legacy
from .consolidation_delivery import materialize_consolidation_artifacts, consolidation_artifact_gate
from .modes import COMPRESSION_CONSOLIDATION, normalize_mode
from .runtime_v12 import consolidation_gate

def _manifest(state):
    attachments=[]
    for item in state.artifacts or []:
        if str(item.get("role") or "")=="session_dashboard": continue
        if str(item.get("delivery_class") or "").upper()!="ATTACH": continue
        attachments.append({"id":item.get("id"),"role":item.get("role"),"instance_key":item.get("instance_key",item.get("role")),"source_id":item.get("source_id"),"path":item.get("path"),"format":"DOCX","media_type":item.get("media_type"),"size_bytes":item.get("size_bytes"),"sha256":item.get("sha256"),"readback":item.get("readback")})
    return {"status":"PASS","attachment_placement":"SESSION_CHAT_TAIL","attachments":attachments,"atomic":True}

def evaluate_completion(state):
    if normalize_mode(state.mode)!=COMPRESSION_CONSOLIDATION:
        return _legacy.evaluate_completion(state)
    errors=[]; core_ok,core_errors=consolidation_gate(state); errors.extend(core_errors)
    cc=(state.strategy or {}).get("consolidation") or {}
    if (cc.get("peer_review_readiness") or {}).get("status")!="PASS": errors.append("peer-review readiness PASS required")
    if (cc.get("provenance") or {}).get("status")!="PASS": errors.append("C&C provenance PASS required")
    if (cc.get("final_review") or {}).get("status")!="PASS": errors.append("C&C final severe review PASS required")
    autopilot={"status":"DEFERRED","errors":errors}
    if core_ok and not errors: autopilot=materialize_consolidation_artifacts(state)
    if autopilot.get("status")!="PASS": errors.extend(autopilot.get("errors") or ["C&C artifact autopilot not PASS"])
    art_ok,art_errors=consolidation_artifact_gate(state); errors.extend(art_errors)
    eligible=core_ok and art_ok and not errors
    state.completion={**(state.completion or {}),"eligible":eligible,"reason":"" if eligible else "; ".join(dict.fromkeys(errors)),"consolidation_gate":{"eligible":core_ok,"errors":core_errors},"consolidation_artifact_autopilot":autopilot,"consolidation_artifact_gate":{"eligible":art_ok,"errors":art_errors},"delivery_manifest":_manifest(state) if eligible else {"status":"WITHHELD","attachments":[],"atomic":True}}
    state.phase="COMPLETE" if eligible else "VALIDATING"
    return state
