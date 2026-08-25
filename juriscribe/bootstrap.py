from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BOOTSTRAP_SCHEMA = "juriscribe-bootstrap/v2"
PROBE_SCHEMA = "juriscribe-probe-receipt/v2"
BOOTSTRAP_ORDER = (
    "TERMS_PRESENTED", "TERMS_ACCEPTED", "PROBE_REQUIRED", "PROBED",
    "INITIALIZE_REQUIRED", "INITIALIZING", "MODE_SELECTION_REQUIRED", "ACTIVE_WORK",
)

def utc_now() -> str: return datetime.now(timezone.utc).isoformat()
def canonical_digest(value: Any) -> str:
    payload=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")); return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def bootstrap_card(state: str, *, contract_version: str = "", detail: str = "") -> dict[str, Any]:
    state=str(state).upper()
    from .modes import mode_choices
    cards={
        "TERMS_PRESENTED": ("Termini da accettare", ["I ACCEPT","I DECLINE","ALTRO"]),
        "PROBE_REQUIRED": ("Verifica capacità dell'host", ["PROBE JURISCRIBE","ALTRO"]),
        "PROBED": ("Probe completato", ["INITIALIZE JURISCRIBE","ALTRO"]),
        "INITIALIZE_REQUIRED": ("Inizializzazione richiesta", ["INITIALIZE JURISCRIBE","ALTRO"]),
        "MODE_SELECTION_REQUIRED": ("Scegli la modalità Juriscribe", [*mode_choices(),"ALTRO"]),
        "ACTIVE_WORK": ("Juriscribe attivo", ["STATO SESSIONE","ALTRO"]),
    }
    title,choices=cards.get(state,(state.replace("_"," ").title(),["ALTRO"]))
    payload={"schema":BOOTSTRAP_SCHEMA,"state":state,"headline":title,"contract_version":contract_version,"detail":detail,"choices":choices,"free_input_allowed":True,"blocking":state!="ACTIVE_WORK"}
    payload["digest"]=canonical_digest(payload); return payload

def issue_probe_receipt(admission_receipt: dict[str, Any], contract_text: str, capabilities: dict[str, str], *, host: str, probed_at: str | None = None, probe_nonce: str | None = None) -> dict[str, Any]:
    from .admission import contract_digest, contract_version, validate_receipt
    ok,errors=validate_receipt(admission_receipt,contract_text)
    if not ok: raise PermissionError("probe denied: "+"; ".join(errors))
    if not capabilities: raise ValueError("probe capabilities missing")
    normalized={str(k):str(v) for k,v in sorted(capabilities.items())}; probed_at=probed_at or utc_now(); probe_nonce=probe_nonce or secrets.token_hex(16)
    if len(probe_nonce)!=32 or any(ch not in "0123456789abcdef" for ch in probe_nonce): raise ValueError("probe nonce must be 128-bit lowercase hex")
    payload={"schema":PROBE_SCHEMA,"status":"PROBED","admission_receipt_id":admission_receipt.get("receipt_id",""),"admission_receipt_nonce":admission_receipt.get("receipt_nonce",""),"contract_version":contract_version(contract_text),"contract_sha256":contract_digest(contract_text),"host":str(host),"capabilities":normalized,"capabilities_digest":canonical_digest(normalized),"probed_at":probed_at,"probe_nonce":probe_nonce}
    payload["receipt_id"]="PRB-"+canonical_digest(payload)[:16]; return payload

def validate_probe_receipt(probe_receipt: dict[str, Any] | None, admission_receipt: dict[str, Any] | None, contract_text: str) -> tuple[bool,list[str]]:
    from .admission import contract_digest, contract_version, validate_receipt
    errors=[]; ok,admission_errors=validate_receipt(admission_receipt,contract_text)
    if not ok: errors.extend(admission_errors)
    if not probe_receipt: return False,list(dict.fromkeys(errors+["probe receipt missing"]))
    if probe_receipt.get("schema")!=PROBE_SCHEMA: errors.append("probe receipt schema mismatch")
    if probe_receipt.get("status")!="PROBED": errors.append("probe receipt status is not PROBED")
    if probe_receipt.get("admission_receipt_id")!=(admission_receipt or {}).get("receipt_id"): errors.append("probe receipt bound to different admission receipt")
    if probe_receipt.get("admission_receipt_nonce")!=(admission_receipt or {}).get("receipt_nonce"): errors.append("probe receipt admission nonce mismatch")
    if probe_receipt.get("contract_version")!=contract_version(contract_text): errors.append("probe receipt contract version mismatch")
    if probe_receipt.get("contract_sha256")!=contract_digest(contract_text): errors.append("probe receipt contract hash mismatch")
    caps=probe_receipt.get("capabilities") or {}
    if not caps: errors.append("probe receipt capabilities missing")
    elif probe_receipt.get("capabilities_digest")!=canonical_digest({str(k):str(v) for k,v in sorted(caps.items())}): errors.append("probe receipt capabilities digest mismatch")
    if not str(probe_receipt.get("host","")).strip(): errors.append("probe receipt host missing")
    if not str(probe_receipt.get("probed_at","")).strip(): errors.append("probe receipt timestamp missing")
    nonce=str(probe_receipt.get("probe_nonce",""))
    if len(nonce)!=32 or any(ch not in "0123456789abcdef" for ch in nonce): errors.append("probe receipt nonce invalid")
    expected=dict(probe_receipt); expected.pop("receipt_id",None)
    if probe_receipt.get("receipt_id")!="PRB-"+canonical_digest(expected)[:16]: errors.append("probe receipt id/digest mismatch")
    return not errors,list(dict.fromkeys(errors))

def require_probe_receipt(probe_receipt, admission_receipt, contract_text):
    ok,errors=validate_probe_receipt(probe_receipt,admission_receipt,contract_text)
    if not ok: raise PermissionError("initialization denied: "+"; ".join(errors))
    return probe_receipt or {}

def claim_probe_receipt(root: str | Path, probe_receipt: dict[str, Any], session_id: str) -> Path:
    receipt_id=str(probe_receipt.get("receipt_id",""))
    if not receipt_id.startswith("PRB-"): raise PermissionError("cannot consume invalid probe receipt")
    claims=Path(root)/".bootstrap-claims"; claims.mkdir(parents=True,exist_ok=True); marker=claims/f"{receipt_id}.json"
    payload=json.dumps({"probe_receipt_id":receipt_id,"probe_nonce":probe_receipt.get("probe_nonce",""),"session_id":str(session_id),"consumed_at":utc_now()},ensure_ascii=False,sort_keys=True)+"\n"
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    try: fd=os.open(marker,flags,0o600)
    except FileExistsError as exc:
        try: owner=json.loads(marker.read_text(encoding="utf-8")).get("session_id","unknown")
        except Exception: owner="unknown"
        raise PermissionError(f"probe receipt already consumed by session {owner}") from exc
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle: handle.write(payload); handle.flush(); os.fsync(handle.fileno())
    except Exception: marker.unlink(missing_ok=True); raise
    return marker

def activate_work(admission: dict[str, Any], *, contract_version: str) -> None:
    admission["bootstrap"]=bootstrap_card("ACTIVE_WORK",contract_version=contract_version,detail="Mode selected; substantive work is authorized under the mode contract.")

def bootstrap_gate(admission: dict[str, Any] | None) -> tuple[bool,list[str]]:
    admission=admission or {}; errors=[]
    if admission.get("status")!="ACCEPTED": errors.append("human T&C acceptance is not active")
    if not admission.get("receipt"): errors.append("admission receipt missing")
    if not admission.get("probe_receipt"): errors.append("probe receipt missing")
    state=(admission.get("bootstrap") or {}).get("state"); legacy=str((admission.get("receipt") or {}).get("contract_version","")) in {"1.5.0","1.6.0"}
    if state not in {"MODE_SELECTION_REQUIRED","ACTIVE_WORK"} and not (state=="ACTIVE" and legacy): errors.append("bootstrap is not ready for mode selection or active work")
    return not errors,errors
