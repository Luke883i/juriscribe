from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

AUTHORITY_RANK = {
    "primary_law": 100, "constitutional_court": 95, "supreme_court": 92, "eu_court": 92,
    "echr": 90, "administrative_supreme_court": 90, "official_institutional": 85,
    "peer_reviewed_doctrine": 75, "leading_treatise": 72, "specialist_commentary": 60, "other": 30,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SourceRecord:
    id: str
    title: str
    url: str
    source_type: str
    jurisdiction: str | None = None
    court_or_author: str | None = None
    date: str | None = None
    verified_at: str | None = None
    direct_read: bool = False
    primary: bool = False
    notes: str = ""

    def record(self) -> dict[str, Any]:
        data = asdict(self)
        data["authority_rank"] = AUTHORITY_RANK.get(self.source_type, AUTHORITY_RANK["other"])
        data["verified_at"] = self.verified_at or now_iso()
        return data


@dataclass(frozen=True)
class ClaimRecord:
    id: str
    text: str
    claim_type: str
    scope: str
    support_source_ids: tuple[str, ...] = ()
    premise_claim_ids: tuple[str, ...] = ()
    inference_bridge: str = ""
    falsifier: str = ""
    status: str = "UNVERIFIED"
    material: bool = True

    def record(self) -> dict[str, Any]:
        data = asdict(self)
        data["support_source_ids"] = list(self.support_source_ids)
        data["premise_claim_ids"] = list(self.premise_claim_ids)
        return data


def validate_claim(claim: dict[str, Any], sources: list[dict[str, Any]], claims: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    source_ids = {s.get("id") for s in sources}
    claim_ids = {c.get("id") for c in claims}
    claim_type = claim.get("claim_type")
    support = claim.get("support_source_ids", [])
    premises = claim.get("premise_claim_ids", [])
    if claim.get("material", True) and claim_type not in {"interpretive_proposal", "editorial"} and not support and not premises:
        errors.append("material claim has no source or premise support")
    if any(sid not in source_ids for sid in support): errors.append("claim references unknown source")
    if any(cid not in claim_ids for cid in premises): errors.append("claim references unknown premise")
    if claim_type == "strong_inference":
        if not premises: errors.append("strong inference requires premises")
        if not claim.get("inference_bridge", "").strip(): errors.append("strong inference requires an explicit bridge")
        if not claim.get("falsifier", "").strip(): errors.append("strong inference requires a falsifier")
    return (not errors, errors)


def assess_dominance(label: str, candidates: list[dict[str, Any]], *, minimum_independent_sources: int = 3) -> dict[str, Any]:
    verified = [c for c in candidates if c.get("direct_read") and c.get("verified_at")]
    independent = {(c.get("court_or_author") or c.get("id"), c.get("source_type")) for c in verified}
    high_authority = [c for c in verified if c.get("authority_rank", 0) >= 72]
    sufficient = len(independent) >= minimum_independent_sources and len(high_authority) >= minimum_independent_sources
    return {
        "label": label,
        "status": "SUPPORTED_DOMINANT" if sufficient else "DOMINANCE_NOT_ESTABLISHED",
        "verified_sources": len(verified), "independent_sources": len(independent), "high_authority_sources": len(high_authority),
        "rule": "search rank and repetition alone never establish dominance",
    }


def research_plan(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan = []
    for claim in claims:
        if not claim.get("material", True): continue
        plan.append({
            "claim_id": claim.get("id"), "query_goal": claim.get("text", "")[:240],
            "preferred_sources": ["primary_law", "constitutional_court", "supreme_court", "eu_court", "echr", "official_institutional", "peer_reviewed_doctrine", "leading_treatise"],
            "require_direct_read": True, "require_date_and_scope": True,
        })
    return plan
