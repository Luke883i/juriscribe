from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

REQUIRED_EDGE_FAMILIES = {
    "omission", "contradiction", "source_loss", "qualification_loss",
    "cross_chapter_duplication", "terminology_drift", "unsupported_inference",
    "temporal_conflict", "style_drift", "compression_loss",
}
REQUIRED_SIMULATION_CATEGORIES = {
    "adversarial", "favorable", "stress", "editorial_review", "logical_semantic_review"
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256((text or "").replace("\r\n", "\n").encode("utf-8")).hexdigest()


def seal_candidate(text: str, *, generation_contract: dict[str, Any], stage: str, sequence: int) -> dict[str, Any]:
    if generation_contract.get("status") != "READY":
        raise ValueError("generation contract not READY")
    if stage not in {"INITIAL", "REGENERATED", "COMPRESSED_FINAL"}:
        raise ValueError("unsupported candidate stage")
    digest = text_digest(text)
    words = len((text or "").split())
    payload = {
        "sequence": int(sequence),
        "stage": stage,
        "digest": digest,
        "word_count": words,
        "generation_contract_digest": generation_contract.get("contract_digest", ""),
        "reticulum_digest": generation_contract.get("reticulum_digest", ""),
        "status": "SEALED",
    }
    payload["record_digest"] = canonical_digest(payload)
    return payload


@dataclass(frozen=True)
class SimulationReceipt:
    cases: int
    seeds: list[int]
    families: list[str]
    failures: int
    escapes: int
    status: str
    categories: dict[str, int] | None = None
    candidate_digest: str = ""
    generation_contract_digest: str = ""
    scenario_digest: str = ""
    killed_mutants: int = 0
    accepted_controls: int = 0
    false_positives: int = 0
    notes: str = ""

    def record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompressionRecord:
    before_words: int
    after_words: int
    required_unit_ids: list[str]
    preserved_unit_ids: list[str]
    added_material_unit_ids: list[str]
    lost_required_unit_ids: list[str]
    status: str
    before_digest: str = ""
    after_digest: str = ""
    generation_contract_digest: str = ""
    inventory_digest: str = ""
    post_compression_recheck: str = "NOT_RUN"

    def record(self) -> dict[str, Any]:
        return asdict(self)


def validate_simulation_receipt(
    receipt: dict[str, Any] | None,
    *,
    candidate_digest: str | None = None,
    generation_contract_digest: str | None = None,
    require_categories: bool = False,
) -> tuple[bool, list[str]]:
    if not receipt:
        return False, ["simulation receipt missing"]
    errors: list[str] = []
    if int(receipt.get("cases", 0)) <= 0:
        errors.append("simulation case count must be positive")
    if not receipt.get("seeds"):
        errors.append("simulation seeds missing")
    families = set(receipt.get("families", []))
    missing = sorted(REQUIRED_EDGE_FAMILIES - families)
    if missing:
        errors.append("simulation edge families missing: " + ", ".join(missing))
    if require_categories:
        category_counts = receipt.get("categories", {}) or {}
        missing_categories = sorted(c for c in REQUIRED_SIMULATION_CATEGORIES if int(category_counts.get(c, 0)) <= 0)
        if missing_categories:
            errors.append("simulation categories missing: " + ", ".join(missing_categories))
    if int(receipt.get("failures", 0)) != 0:
        errors.append("simulation failures are non-zero")
    if int(receipt.get("escapes", 0)) != 0:
        errors.append("simulation escapes are non-zero")
    if int(receipt.get("false_positives", 0)) != 0:
        errors.append("simulation false positives are non-zero")
    if receipt.get("status") != "PASS":
        errors.append("simulation status is not PASS")
    if candidate_digest is not None:
        if receipt.get("candidate_digest") != candidate_digest:
            errors.append("simulation receipt bound to stale candidate")
        if not str(receipt.get("scenario_digest", "")).strip():
            errors.append("simulation scenario digest missing")
    if generation_contract_digest is not None and receipt.get("generation_contract_digest") != generation_contract_digest:
        errors.append("simulation receipt bound to stale generation contract")
    return not errors, list(dict.fromkeys(errors))


def audit_compression(
    *,
    before_words: int,
    after_words: int,
    required_unit_ids: list[str],
    preserved_unit_ids: list[str],
    added_material_unit_ids: list[str] | None = None,
    before_digest: str = "",
    after_digest: str = "",
    generation_contract_digest: str = "",
    post_compression_recheck: str = "NOT_RUN",
) -> dict[str, Any]:
    req = set(required_unit_ids)
    preserved = set(preserved_unit_ids)
    lost = sorted(req - preserved)
    added = sorted(set(added_material_unit_ids or []))
    errors: list[str] = []
    if lost:
        errors.append("required semantic units lost in compression")
    if after_words > before_words:
        errors.append("final compression expanded the candidate")
    if added:
        errors.append("compression introduced new material units requiring re-audit")
    if before_digest and after_digest and before_digest == after_digest and after_words != before_words:
        errors.append("compression digest unchanged despite word-count change")
    record = CompressionRecord(
        before_words=before_words,
        after_words=after_words,
        required_unit_ids=sorted(req),
        preserved_unit_ids=sorted(preserved),
        added_material_unit_ids=added,
        lost_required_unit_ids=lost,
        status="PASS" if not errors else "FAIL",
        before_digest=before_digest,
        after_digest=after_digest,
        generation_contract_digest=generation_contract_digest,
        inventory_digest=canonical_digest(sorted(req)),
        post_compression_recheck=post_compression_recheck,
    ).record()
    record["errors"] = errors
    record["record_digest"] = canonical_digest(record)
    return record


def compression_valid(
    record: dict[str, Any] | None,
    *,
    expected_before_digest: str | None = None,
    expected_after_digest: str | None = None,
    generation_contract_digest: str | None = None,
    strict: bool = False,
) -> tuple[bool, list[str]]:
    if not record:
        return False, ["compression record missing"]
    errors = list(record.get("errors", []))
    if record.get("status") != "PASS":
        errors.append("compression status is not PASS")
    if record.get("lost_required_unit_ids"):
        errors.append("compression lost required semantic units")
    if record.get("added_material_unit_ids"):
        errors.append("compression introduced new material units")
    if expected_before_digest is not None and record.get("before_digest") != expected_before_digest:
        errors.append("compression bound to stale pre-compression candidate")
    if expected_after_digest is not None and record.get("after_digest") != expected_after_digest:
        errors.append("compression bound to stale final candidate")
    if generation_contract_digest is not None and record.get("generation_contract_digest") != generation_contract_digest:
        errors.append("compression bound to stale generation contract")
    if strict and record.get("post_compression_recheck") != "PASS":
        errors.append("post-compression recheck is not PASS")
    return not errors, list(dict.fromkeys(errors))
