from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "1.5.0"
ACCEPT_PHRASE = "I ACCEPT"
REPOSITORY = "Luke883i/juriscribe"
PRE_ADMISSION_ALLOWLIST = ("AGENTS.md", "ISENECA_ACCESS_CONTRACT.md", "ADMISSION.json")
_VERSION_RE = re.compile(r"(?m)^contract_version:\s*([^\s]+)\s*$")

def utc_now() -> str: return datetime.now(timezone.utc).isoformat()
def contract_version(contract_text: str) -> str:
    match=_VERSION_RE.search(contract_text)
    if not match: raise ValueError("contract_version missing from contract")
    return match.group(1)
def contract_digest(contract_text: str) -> str: return hashlib.sha256(contract_text.replace("\r\n","\n").encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class AdmissionReceipt:
    repository: str; contract_version: str; contract_sha256: str; accepted_phrase: str; actor_type: str; evidence_type: str; evidence_sha256: str; accepted_at: str; receipt_id: str
    def record(self) -> dict[str, Any]: return asdict(self)

def issue_receipt(contract_text: str, *, phrase: str, actor_type: str, evidence_type: str, user_message: str, repository: str=REPOSITORY, accepted_at: str|None=None) -> dict[str,Any]:
    version=contract_version(contract_text)
    if version!=CONTRACT_VERSION: raise ValueError(f"runtime expects contract {CONTRACT_VERSION}, got {version}")
    if phrase!=ACCEPT_PHRASE or user_message.strip()!=ACCEPT_PHRASE: raise PermissionError("exact acceptance phrase required")
    if actor_type!="human": raise PermissionError("acceptance must be attributed to the human user")
    if evidence_type!="explicit_user_message": raise PermissionError("acceptance requires explicit_user_message evidence")
    accepted_at=accepted_at or utc_now(); csha=contract_digest(contract_text); esha=hashlib.sha256(user_message.encode("utf-8")).hexdigest(); rid_payload=f"{repository}|{version}|{csha}|{esha}|{accepted_at}"; rid="ADM-"+hashlib.sha256(rid_payload.encode("utf-8")).hexdigest()[:16]
    return AdmissionReceipt(repository,version,csha,phrase,actor_type,evidence_type,esha,accepted_at,rid).record()

def validate_receipt(receipt: dict[str,Any]|None, contract_text: str, *, repository: str=REPOSITORY) -> tuple[bool,list[str]]:
    errors=[]
    if not receipt: return False,["admission receipt missing"]
    checks={"repository":repository,"contract_version":contract_version(contract_text),"contract_sha256":contract_digest(contract_text),"accepted_phrase":ACCEPT_PHRASE,"actor_type":"human","evidence_type":"explicit_user_message"}
    for key,expected in checks.items():
        if receipt.get(key)!=expected: errors.append(f"receipt {key} mismatch")
    if not str(receipt.get("evidence_sha256","")).strip(): errors.append("receipt acceptance evidence hash missing")
    if not str(receipt.get("accepted_at","")).strip(): errors.append("receipt accepted_at missing")
    if not str(receipt.get("receipt_id","")).startswith("ADM-"): errors.append("receipt id invalid")
    return not errors,errors

def require_receipt(receipt: dict[str,Any]|None, contract_text: str) -> dict[str,Any]:
    ok,errors=validate_receipt(receipt,contract_text)
    if not ok: raise PermissionError("repository admission denied: "+"; ".join(errors))
    return receipt or {}
def load_contract_text(repo_root: str|Path|None=None) -> str:
    root=Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]; return (root/"ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
def load_receipt(path: str|Path) -> dict[str,Any]: return json.loads(Path(path).read_text(encoding="utf-8"))
