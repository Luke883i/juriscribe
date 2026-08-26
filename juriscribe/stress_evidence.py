from __future__ import annotations

from typing import Any

from .consolidation import (
    SATURATION_SCHEMA,
    canonical_digest,
    validate_mutation_receipt,
)

MUTATION_COVERAGE_SCHEMA = "juriscribe-mutation-coverage-evidence/v1"
SATURATION_COVERAGE_SCHEMA = "juriscribe-saturation-coverage-evidence/v1"
INSTANCE_CLAIM_SCOPE = "SOAK_VOLUME_NOT_UNIQUE_SEMANTIC_CASES"
SATURATION_CLAIM_SCOPE = "SEARCH_CONVERGENCE_EVIDENCE_NOT_REFINED_CANDIDATE_SEMANTIC_RECALL"


def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _normalize_counts(value: Any, errors: list[str], *, kind: str) -> dict[str, int]:
    if not isinstance(value, dict):
        errors.append(f"{kind} coverage class counts malformed")
        return {}
    try:
        counts = {str(key): int(count) for key, count in value.items()}
    except (TypeError, ValueError, OverflowError):
        errors.append(f"{kind} coverage class counts malformed")
        return {}
    if any(count <= 0 for count in counts.values()):
        errors.append(f"{kind} coverage class counts must be positive")
    return counts


def build_mutation_coverage_evidence(
    *, cases: int, class_counts: dict[str, int], mismatches: int = 0
) -> dict[str, Any]:
    counts = {str(key): int(value) for key, value in sorted((class_counts or {}).items())}
    payload = {
        "schema": MUTATION_COVERAGE_SCHEMA,
        "instance_claim_scope": INSTANCE_CLAIM_SCOPE,
        "instances": int(cases),
        "equivalence_classes": len(counts),
        "class_counts": counts,
        "mismatches": int(mismatches),
    }
    payload["digest"] = canonical_digest(payload)
    return payload


def validate_mutation_evidence(
    receipt: dict[str, Any], *, plan_digest: str, reticulum_digest: str
) -> tuple[bool, list[str]]:
    legacy_ok, legacy_errors = validate_mutation_receipt(
        receipt, plan_digest=plan_digest, reticulum_digest=reticulum_digest
    )
    errors = list(legacy_errors)
    evidence = dict(receipt.get("coverage_evidence") or {})
    if evidence.get("schema") != MUTATION_COVERAGE_SCHEMA:
        errors.append("mutation coverage evidence schema mismatch")
    if evidence.get("instance_claim_scope") != INSTANCE_CLAIM_SCOPE:
        errors.append("mutation instance claim scope mismatch")
    counts = _normalize_counts(evidence.get("class_counts"), errors, kind="mutation")
    if len(counts) < 2:
        errors.append("mutation coverage requires at least two executed equivalence classes")
    instances = _safe_int(evidence.get("instances"))
    classes = _safe_int(evidence.get("equivalence_classes"))
    mismatches = _safe_int(evidence.get("mismatches"))
    receipt_cases = _safe_int(receipt.get("cases"))
    if instances is None or instances != receipt_cases:
        errors.append("mutation coverage instance count mismatch")
    if instances is None or sum(counts.values()) != instances:
        errors.append("mutation coverage class counts do not sum to instances")
    if classes is None or classes != len(counts):
        errors.append("mutation coverage equivalence class count mismatch")
    if mismatches != 0:
        errors.append("mutation coverage contains mismatches")
    expected = canonical_digest({key: value for key, value in evidence.items() if key != "digest"})
    if evidence.get("digest") != expected:
        errors.append("mutation coverage evidence digest mismatch")
    return legacy_ok and not errors, list(dict.fromkeys(errors))


def build_saturation_coverage_evidence(
    *, probes: int, class_counts: dict[str, int], mismatches: int = 0
) -> dict[str, Any]:
    counts = {str(key): int(value) for key, value in sorted((class_counts or {}).items())}
    payload = {
        "schema": SATURATION_COVERAGE_SCHEMA,
        "instance_claim_scope": INSTANCE_CLAIM_SCOPE,
        "probes": int(probes),
        "equivalence_classes": len(counts),
        "class_counts": counts,
        "mismatches": int(mismatches),
    }
    payload["digest"] = canonical_digest(payload)
    return payload


def validate_saturation_evidence(
    receipt: dict[str, Any], *, plan_digest: str
) -> tuple[bool, list[str]]:
    """Validate search-convergence evidence without accepting semantic recall claims.

    v0.11 put semantic/relation recall in this pre-materialization receipt. v0.12
    deliberately does not trust or require those caller fields; refined-candidate
    preservation is proven later from the actual materialized text and projection.
    """
    errors: list[str] = []
    if receipt.get("schema") != SATURATION_SCHEMA:
        errors.append("saturation schema mismatch")
    if receipt.get("plan_digest") != plan_digest:
        errors.append("saturation bound to stale plan")
    novelty = _safe_int(receipt.get("no_novelty_tail"))
    compression = _safe_int(receipt.get("no_better_compression_tail"))
    if novelty is None or novelty < 1000:
        errors.append("M+1000 genuine no-novelty tail required")
    if compression is None or compression < 1000:
        errors.append("N+1000 no-better-lossless-compression tail required")
    if receipt.get("canonical_unchanged") is not True:
        errors.append("canonical material must remain unchanged")
    if "semantic_recall" in receipt or "relation_recall" in receipt:
        errors.append("caller-supplied semantic/relation recall is forbidden in v0.12 saturation evidence")

    evidence = dict(receipt.get("coverage_evidence") or {})
    if evidence.get("schema") != SATURATION_COVERAGE_SCHEMA:
        errors.append("saturation coverage evidence schema mismatch")
    if evidence.get("instance_claim_scope") != INSTANCE_CLAIM_SCOPE:
        errors.append("saturation instance claim scope mismatch")
    counts = _normalize_counts(evidence.get("class_counts"), errors, kind="saturation")
    if len(counts) < 2:
        errors.append("saturation coverage requires at least two executed equivalence classes")
    probes = _safe_int(evidence.get("probes"))
    classes = _safe_int(evidence.get("equivalence_classes"))
    mismatches = _safe_int(evidence.get("mismatches"))
    if probes is None or sum(counts.values()) != probes:
        errors.append("saturation coverage class counts do not sum to probes")
    if classes is None or classes != len(counts):
        errors.append("saturation coverage equivalence class count mismatch")
    if mismatches != 0:
        errors.append("saturation coverage contains mismatches")
    if probes is None or novelty is None or compression is None or probes < max(novelty, compression):
        errors.append("saturation coverage probe count is below declared tail")
    expected = canonical_digest({key: value for key, value in evidence.items() if key != "digest"})
    if evidence.get("digest") != expected:
        errors.append("saturation coverage evidence digest mismatch")
    return not errors, list(dict.fromkeys(errors))
