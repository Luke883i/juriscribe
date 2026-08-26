from __future__ import annotations
import hashlib,json,re,secrets
from dataclasses import asdict,dataclass
from datetime import datetime,timezone
from pathlib import Path

CONTRACT_VERSION="1.9.0"
LEGACY_ISSUE_VERSIONS={"1.8.0","1.7.0","1.6.0","1.5.0"}
ACCEPT_PHRASE="I ACCEPT"
REPOSITORY="Luke883i/juriscribe"
PRE_ADMISSION_ALLOWLIST=("AGENTS.md","ISENECA_ACCESS_CONTRACT.md","ADMISSION.json")
_VERSION_RE=re.compile(r"(?m)^contract_version:\s*([^\s]+)\s*$")
_NONCE_RE=re.compile(r"^[a-f0-9]{32}$")
def utc_now(): return datetime.now(timezone.utc).isoformat()
def contract_version(contract_text):
    m=_VERSION_RE.search(contract_text)
    if not m: raise ValueError("contract_version missing from contract")
    return m.group(1)
def contract_digest(contract_text): return hashlib.sha256(contract_text.replace("\r\n","\n").encode("utf-8")).hexdigest()
def _receipt_id(repository,version,csha,esha,accepted_at,receipt_nonce): return "ADM-"+hashlib.sha256(f"{repository}|{version}|{csha}|{esha}|{accepted_at}|{receipt_nonce}".encode()).hexdigest()[:16]
@dataclass(frozen=True)
class AdmissionReceipt:
    repository:str; contract_version:str; contract_sha256:str; accepted_phrase:str; actor_type:str; evidence_type:str; evidence_sha256:str; accepted_at:str; receipt_nonce:str; receipt_id:str
    def record(self): return asdict(self)
def issue_receipt(contract_text,*,phrase,actor_type,evidence_type,user_message,repository=REPOSITORY,accepted_at=None,receipt_nonce=None):
    version=contract_version(contract_text)
    if version!=CONTRACT_VERSION and version not in LEGACY_ISSUE_VERSIONS: raise ValueError(f"runtime expects contract {CONTRACT_VERSION}, got {version}")
    if phrase!=ACCEPT_PHRASE or user_message.strip()!=ACCEPT_PHRASE: raise PermissionError("exact acceptance phrase required")
    if actor_type!="human": raise PermissionError("acceptance must be attributed to the human user")
    if evidence_type!="explicit_user_message": raise PermissionError("acceptance requires explicit_user_message evidence")
    accepted_at=accepted_at or utc_now(); receipt_nonce=receipt_nonce or secrets.token_hex(16)
    if not _NONCE_RE.fullmatch(receipt_nonce): raise ValueError("admission receipt nonce must be 128-bit lowercase hex")
    csha=contract_digest(contract_text); esha=hashlib.sha256(user_message.encode("utf-8")).hexdigest(); rid=_receipt_id(repository,version,csha,esha,accepted_at,receipt_nonce)
    return AdmissionReceipt(repository,version,csha,phrase,actor_type,evidence_type,esha,accepted_at,receipt_nonce,rid).record()
def validate_receipt(receipt,contract_text,*,repository=REPOSITORY):
    if not receipt: return False,["admission receipt missing"]
    errors=[]; checks={"repository":repository,"contract_version":contract_version(contract_text),"contract_sha256":contract_digest(contract_text),"accepted_phrase":ACCEPT_PHRASE,"actor_type":"human","evidence_type":"explicit_user_message"}
    for key,expected in checks.items():
        if receipt.get(key)!=expected: errors.append(f"receipt {key} mismatch")
    esha=str(receipt.get("evidence_sha256","")); accepted_at=str(receipt.get("accepted_at","")); nonce=str(receipt.get("receipt_nonce",""))
    if not esha.strip(): errors.append("receipt acceptance evidence hash missing")
    if not accepted_at.strip(): errors.append("receipt accepted_at missing")
    if not _NONCE_RE.fullmatch(nonce): errors.append("receipt nonce invalid")
    if not errors:
        if receipt.get("receipt_id")!=_receipt_id(repository,checks["contract_version"],checks["contract_sha256"],esha,accepted_at,nonce): errors.append("receipt id/digest mismatch")
    elif not str(receipt.get("receipt_id","")).startswith("ADM-"): errors.append("receipt id invalid")
    return not errors,list(dict.fromkeys(errors))
def require_receipt(receipt,contract_text):
    ok,errors=validate_receipt(receipt,contract_text)
    if not ok: raise PermissionError("repository admission denied: "+"; ".join(errors))
    return receipt or {}
def load_contract_text(repo_root=None):
    if repo_root is not None:
        return (Path(repo_root)/"ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
    source=(Path(__file__).resolve().parents[1]/"ISENECA_ACCESS_CONTRACT.md")
    if source.exists():
        return source.read_text(encoding="utf-8")
    from importlib.resources import files
    return files("juriscribe.resources").joinpath("ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
def load_receipt(path): return json.loads(Path(path).read_text(encoding="utf-8"))
