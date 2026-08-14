from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

REQUIRED_EDGE_FAMILIES = {
    "omission", "contradiction", "source_loss", "qualification_loss",
    "cross_chapter_duplication", "terminology_drift", "unsupported_inference",
    "temporal_conflict", "style_drift", "compression_loss",
}

@dataclass(frozen=True)
class SimulationReceipt:
    cases: int
    seeds: list[int]
    families: list[str]
    failures: int
    escapes: int
    status: str
    notes: str = ""
    def record(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class CompressionRecord:
    before_words: int
    after_words: int
    required_unit_ids: list[str]
    preserved_unit_ids: list[str]
    added_material_unit_ids: list[str]
    lost_required_unit_ids: list[str]
    status: str
    def record(self) -> dict[str, Any]: return asdict(self)

def validate_simulation_receipt(receipt: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not receipt:
        return False, ["simulation receipt missing"]
    errors=[]
    if int(receipt.get("cases",0)) <= 0: errors.append("simulation case count must be positive")
    if not receipt.get("seeds"): errors.append("simulation seeds missing")
    families=set(receipt.get("families",[])); missing=sorted(REQUIRED_EDGE_FAMILIES-families)
    if missing: errors.append("simulation edge families missing: "+", ".join(missing))
    if int(receipt.get("failures",0)) != 0: errors.append("simulation failures are non-zero")
    if int(receipt.get("escapes",0)) != 0: errors.append("simulation escapes are non-zero")
    if receipt.get("status") != "PASS": errors.append("simulation status is not PASS")
    return not errors,errors

def audit_compression(*,before_words:int,after_words:int,required_unit_ids:list[str],preserved_unit_ids:list[str],added_material_unit_ids:list[str]|None=None)->dict[str,Any]:
    req=set(required_unit_ids); preserved=set(preserved_unit_ids); lost=sorted(req-preserved); added=sorted(set(added_material_unit_ids or [])); errors=[]
    if lost: errors.append("required semantic units lost in compression")
    if after_words>before_words: errors.append("final compression expanded the candidate")
    if added: errors.append("compression introduced new material units requiring re-audit")
    return CompressionRecord(before_words,after_words,sorted(req),sorted(preserved),added,lost,"PASS" if not errors else "FAIL").record() | {"errors":errors}

def compression_valid(record: dict[str,Any] | None)->tuple[bool,list[str]]:
    if not record:return False,["compression record missing"]
    errors=list(record.get("errors",[]))
    if record.get("status")!="PASS": errors.append("compression status is not PASS")
    if record.get("lost_required_unit_ids"): errors.append("compression lost required semantic units")
    return not errors,errors
