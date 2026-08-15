from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "juriscribe-final-severe-review/v1"
CRITERIA = (
    "GLOBAL_NORMATIVE_FRAME",
    "SEED_CONSISTENCY",
    "LEGAL_AUTHORITY",
    "LOGICAL_CONSEQUENCES",
    "COUNTERAUTHORITY",
    "EDITORIAL_INTEGRITY",
    "INFERENCE_PROVENANCE",
    "TEMPORAL_JURISDICTION",
    "LOSSLESS_TRANSFORMATION",
)
ALLOWED_STATUS = {"PASS", "NOT_APPLICABLE"}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_final_review(
    *,
    candidate_digest: str,
    corpus_digest: str,
    normative_frame_digest: str,
    provenance_digest: str,
    evidence: list[dict[str, Any]],
    consequence_probes: list[dict[str, Any]],
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    by_criterion: dict[str, dict[str, Any]] = {}
    for idx, item in enumerate(evidence or []):
        criterion = str(item.get("criterion", ""))
        if criterion not in CRITERIA:
            errors.append(f"final review evidence {idx} criterion invalid")
            continue
        if criterion in by_criterion:
            errors.append(f"duplicate final review criterion {criterion}")
        by_criterion[criterion] = dict(item)
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"final review criterion {criterion} status invalid")
        if status == "PASS" and not str(item.get("locator", "")).strip():
            errors.append(f"final review criterion {criterion} has no evidence locator")
        if status == "NOT_APPLICABLE" and not str(item.get("rationale", "")).strip():
            errors.append(f"final review criterion {criterion} N/A lacks rationale")
    missing = [c for c in CRITERIA if c not in by_criterion]
    if missing:
        errors.append("final review evidence missing criteria: " + ", ".join(missing))

    normalized_probes: list[dict[str, Any]] = []
    for idx, raw in enumerate(consequence_probes or []):
        probe = dict(raw)
        if not str(probe.get("id", "")).strip():
            errors.append(f"consequence probe {idx} id missing")
        if not str(probe.get("proposition", "")).strip():
            errors.append(f"consequence probe {idx} proposition missing")
        if not str(probe.get("downstream_effect", "")).strip():
            errors.append(f"consequence probe {idx} downstream effect missing")
        if probe.get("status") not in {"PASS", "RESOLVED", "NOT_APPLICABLE"}:
            errors.append(f"consequence probe {idx} unresolved")
        if probe.get("status") != "NOT_APPLICABLE" and not str(probe.get("evidence_ref", "")).strip():
            errors.append(f"consequence probe {idx} evidence missing")
        normalized_probes.append(probe)
    if not normalized_probes:
        errors.append("at least one logical-consequence probe is required")

    normalized_findings = list(findings or [])
    open_material = [
        f for f in normalized_findings
        if f.get("severity") in {"BLOCKER", "MAJOR"} and f.get("status", "OPEN") not in {"RESOLVED", "ACCEPTED_RISK"}
    ]
    if open_material:
        errors.append("final severe review has unresolved BLOCKER/MAJOR findings")

    record = {
        "schema": SCHEMA,
        "candidate_digest": candidate_digest,
        "corpus_digest": corpus_digest,
        "normative_frame_digest": normative_frame_digest,
        "provenance_digest": provenance_digest,
        "evidence": [by_criterion[c] for c in CRITERIA if c in by_criterion],
        "consequence_probes": normalized_probes,
        "findings": normalized_findings,
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }
    record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    return record


def final_review_gate(
    record: dict[str, Any] | None,
    *,
    candidate_digest: str | None = None,
    corpus_digest: str | None = None,
    provenance_digest: str | None = None,
    normative_frame_digest: str | None = None,
) -> tuple[bool, list[str]]:
    if not record:
        return False, ["final severe review missing"]
    errors = list(record.get("errors", []))
    if record.get("schema") != SCHEMA:
        errors.append("final review schema mismatch")
    if record.get("status") != "PASS":
        errors.append("final severe review is not PASS")
    if candidate_digest is not None and record.get("candidate_digest") != candidate_digest:
        errors.append("final review bound to stale candidate")
    if corpus_digest is not None and record.get("corpus_digest") != corpus_digest:
        errors.append("final review bound to stale corpus")
    if provenance_digest is not None and record.get("provenance_digest") != provenance_digest:
        errors.append("final review bound to stale provenance")
    if normative_frame_digest is not None and record.get("normative_frame_digest") != normative_frame_digest:
        errors.append("final review bound to stale normative frame")
    expected = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    if record.get("digest") != expected:
        errors.append("final review digest mismatch")
    return not errors, list(dict.fromkeys(errors))
