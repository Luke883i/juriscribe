from __future__ import annotations
import hashlib,json,re
from dataclasses import asdict,dataclass
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
CONTRACT_VERSION="1.7.0"; LEGACY_ISSUE_VERSIONS={"1.6.0","1.5.0"}; ACCEPT_PHRASE="I ACCEPT"; REPOSITORY="Luke883i/juriscribe"; PRE_ADMISSION_ALLOWLIST=("AGENTS.md","ISENECA_ACCESS_CONTRACT.md","ADMISSION.json"); _VERSION_RE=re.compile(r"(?m)^contract_version:\s*([^\s]+)\s*$")
def utc_now(): return datetime.now(timezone.utc).isoformat()
def contract_version(contract_text):
    match=_VERSION_RE.search(contract_text)
    if not match: raise ValueError("contract_version missing from contract")
    return match.group(1)
def contract_digest(contract_text): return hashlib.sha256(contract_text.replace("\r\n","\n").encode("utf-8")).hexdigest()
@dataclass(frozen=True)
class AdmissionReceipt:
    repository:str; contract_version:str; contract_sha256:str; accepted_phrase:str; actor_type:str; evidence_type:str; evidence_sha256:str; accepted_at:str; receipt_id:str
    def record(self): return asdict(self)
def issue_receipt(contract_text,*,phrase,actor_type,evidence_type,user_message,repository=REPOSITORY,accepted_at=None):
    version=contract_version(contract_text)
    if version!=CONTRACT_VERSION and version not in LEGACY_ISSUE_VERSIONS: raise ValueError(f"runtime expects contract {CONTRACT_VERSION}, got {version}")
    if phrase!=ACCEPT_PHRASE or user_message.strip()!=ACCEPT_PHRASE: raise PermissionError("exact acceptance phrase required")
    if actor_type!="human": raise PermissionError("acceptance must be attributed to the human user")
    if evidence_type!="explicit_user_message": raise PermissionError("acceptance requires explicit_user_message evidence")
    accepted_at=accepted_at or utc_now(); csha=contract_digest(contract_text); esha=hashlib.sha256(user_message.encode("utf-8")).hexdigest(); rid="ADM-"+hashlib.sha256(f"{repository}|{version}|{csha}|{esha}|{accepted_at}".encode("utf-8")).hexdigest()[:16]; return AdmissionReceipt(repository,version,csha,phrase,actor_type,evidence_type,esha,accepted_at,rid).record()
def validate_receipt(receipt,contract_text,*,repository=REPOSITORY):
    if not receipt: return False,["admission receipt missing"]
    errors=[]; checks={"repository":repository,"contract_version":contract_version(contract_text),"contract_sha256":contract_digest(contract_text),"accepted_phrase":ACCEPT_PHRASE,"actor_type":"human","evidence_type":"explicit_user_message"}
    for key,expected in checks.items():
        if receipt.get(key)!=expected: errors.append(f"receipt {key} mismatch")
    if not str(receipt.get("evidence_sha256","")).strip(): errors.append("receipt acceptance evidence hash missing")
    if not str(receipt.get("accepted_at","")).strip(): errors.append("receipt accepted_at missing")
    if not str(receipt.get("receipt_id","")).startswith("ADM-"): errors.append("receipt id invalid")
    return not errors,errors
def require_receipt(receipt,contract_text):
    ok,errors=validate_receipt(receipt,contract_text)
    if not ok: raise PermissionError("repository admission denied: "+"; ".join(errors))
    return receipt or {}
def load_contract_text(repo_root=None):
    root=Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]; return (root/"ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
def load_receipt(path): return json.loads(Path(path).read_text(encoding="utf-8"))
