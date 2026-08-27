from __future__ import annotations

from typing import Any

from .consolidation import canonical_digest

SCHEMA = "juriscribe-editorial-mutation-evidence/v1"
PROFILE = "JURISCRIBE_A_LEVEL_EDITORIAL_MUTATION_STRESS_V1"
INSTANCE_CLAIM_SCOPE = "SEEDED_SCENARIO_SOAK_NOT_UNIQUE_TEXT_CASES"
MIN_INSTANCES = 10_000_000
MIN_SEEDS = 8
MIN_DEEP_CHECKS = 1_000

DEFAULT_SEEDS = (
    0x13A11E01, 0x13A11E17, 0x13A11E2D, 0x13A11E43,
    0x13A11E59, 0x13A11E6F, 0x13A11E85, 0x13A11E9B,
    0x13A11EB1, 0x13A11EC7, 0x13A11EDD, 0x13A11EF3,
    0x13A11F09, 0x13A11F1F, 0x13A11F35, 0x13A11F4B,
)

REQUIRED_SCENARIO_FAMILIES = {
    "SEMANTIC_PRESERVATION",
    "RELATION_INTEGRITY",
    "GAP_OPERATION_CAUSALITY",
    "ORDER_DISCIPLINE",
    "MERGE_SPLIT_DISCIPLINE",
    "COMPRESSION_BOUNDS",
    "REDUNDANCY",
    "STALE_BINDING",
    "HUMAN_CALIBRATION",
    "HUMAN_IDEMPOTENCY",
    "UNICODE_LAYOUT_EDGE",
    "LONG_FORM_SCALE",
}

REQUIRED_KILLED_CLASSES = {
    "lost_unit", "new_unit", "relation_rewire", "false_witness",
    "unknown_output_object", "unbound_gap", "unjustified_operation",
    "unauthorized_reorder", "unauthorized_merge", "unauthorized_split",
    "overcompression", "overexpansion", "unjustified_expansion",
    "duplicate_output", "stale_binding", "human_material_recalibration",
    "human_divergent_repeat",
}

# Lightweight executable invariant vector. It is intentionally separate from the
# full text/projection proof: the 10M campaign stresses combinatorial control-plane
# invariants, while deep checks execute the full reticulum/proof builders.
FLAG_UNIT_LOSS = 1 << 0
FLAG_NEW_UNIT = 1 << 1
FLAG_RELATION_REWIRE = 1 << 2
FLAG_FALSE_WITNESS = 1 << 3
FLAG_UNKNOWN_OBJECT = 1 << 4
FLAG_UNBOUND_GAP = 1 << 5
FLAG_UNJUSTIFIED_OPERATION = 1 << 6
FLAG_UNAUTHORIZED_REORDER = 1 << 7
FLAG_UNAUTHORIZED_MERGE = 1 << 8
FLAG_UNAUTHORIZED_SPLIT = 1 << 9
FLAG_DUPLICATE_OUTPUT = 1 << 10
FLAG_STALE_BINDING = 1 << 11
FLAG_HUMAN_MATERIAL_RECALIBRATION = 1 << 12
FLAG_HUMAN_DIVERGENT_REPEAT = 1 << 13
FLAG_EXPANSION_WITHOUT_CAUSE = 1 << 14
BLOCKING_FLAGS = (1 << 15) - 1


def validate_case_vector(flags: int, compression_permille: int) -> bool:
    """Fast invariant kernel used for high-volume seeded mutation campaigns."""
    if int(flags) & BLOCKING_FLAGS:
        return False
    ratio = int(compression_permille)
    if ratio < 400 or ratio > 1350:
        return False
    return True


def campaign_spec_digest(*, seeds: list[int] | tuple[int, ...], scenario_names: list[str] | tuple[str, ...]) -> str:
    return canonical_digest({
        "profile": PROFILE,
        "seeds": [int(item) for item in seeds],
        "scenario_names": sorted(str(item) for item in scenario_names),
        "required_families": sorted(REQUIRED_SCENARIO_FAMILIES),
        "required_killed_classes": sorted(REQUIRED_KILLED_CLASSES),
    })


def build_editorial_mutation_evidence(
    *,
    instances: int,
    plan_digest: str,
    reticulum_digest: str,
    execution_reticulum_digest: str,
    seed_counts: dict[str, int],
    scenario_counts: dict[str, int],
    family_counts: dict[str, int],
    killed_mutation_classes: list[str],
    deep_checks: int,
    survivors: int = 0,
    mismatches: int = 0,
    seeds: list[int] | tuple[int, ...] = DEFAULT_SEEDS,
) -> dict[str, Any]:
    scenario_names = sorted(str(item) for item in scenario_counts)
    payload = {
        "schema": SCHEMA,
        "profile": PROFILE,
        "instance_claim_scope": INSTANCE_CLAIM_SCOPE,
        "instances": int(instances),
        "plan_digest": str(plan_digest),
        "reticulum_digest": str(reticulum_digest),
        "execution_reticulum_digest": str(execution_reticulum_digest),
        "seeds": [int(item) for item in seeds],
        "seed_counts": {str(k): int(v) for k, v in sorted(seed_counts.items())},
        "scenario_counts": {str(k): int(v) for k, v in sorted(scenario_counts.items())},
        "family_counts": {str(k): int(v) for k, v in sorted(family_counts.items())},
        "killed_mutation_classes": sorted(str(item) for item in killed_mutation_classes),
        "deep_checks": int(deep_checks),
        "survivors": int(survivors),
        "mismatches": int(mismatches),
        "campaign_spec_digest": campaign_spec_digest(seeds=seeds, scenario_names=scenario_names),
    }
    payload["digest"] = canonical_digest(payload)
    return payload


def _positive_counts(value: Any, *, label: str, errors: list[str]) -> dict[str, int]:
    if not isinstance(value, dict):
        errors.append(f"{label} counts malformed")
        return {}
    try:
        counts = {str(k): int(v) for k, v in value.items()}
    except (TypeError, ValueError, OverflowError):
        errors.append(f"{label} counts malformed")
        return {}
    if any(v <= 0 for v in counts.values()):
        errors.append(f"{label} counts must be positive")
    return counts


def validate_editorial_mutation_evidence(
    evidence: dict[str, Any],
    *,
    plan_digest: str,
    reticulum_digest: str,
    execution_reticulum_digest: str,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if evidence.get("schema") != SCHEMA:
        errors.append("editorial mutation evidence schema mismatch")
    if evidence.get("profile") != PROFILE:
        errors.append("editorial mutation evidence profile mismatch")
    if evidence.get("instance_claim_scope") != INSTANCE_CLAIM_SCOPE:
        errors.append("editorial mutation instance claim scope mismatch")
    if evidence.get("plan_digest") != plan_digest:
        errors.append("editorial mutation evidence bound to stale plan")
    if evidence.get("reticulum_digest") != reticulum_digest:
        errors.append("editorial mutation evidence bound to stale source reticulum")
    if evidence.get("execution_reticulum_digest") != execution_reticulum_digest:
        errors.append("editorial mutation evidence bound to stale execution reticulum")
    try:
        instances = int(evidence.get("instances"))
    except (TypeError, ValueError, OverflowError):
        instances = -1
    if instances < MIN_INSTANCES:
        errors.append("at least 10,000,000 editorial mutation instances required")

    seeds = evidence.get("seeds")
    if not isinstance(seeds, list):
        errors.append("editorial mutation seeds malformed")
        normalized_seeds: list[int] = []
    else:
        try:
            normalized_seeds = [int(item) for item in seeds]
        except (TypeError, ValueError, OverflowError):
            normalized_seeds = []
            errors.append("editorial mutation seeds malformed")
    if len(set(normalized_seeds)) < MIN_SEEDS:
        errors.append("editorial mutation campaign requires at least eight distinct seeds")

    seed_counts = _positive_counts(evidence.get("seed_counts"), label="seed", errors=errors)
    scenario_counts = _positive_counts(evidence.get("scenario_counts"), label="scenario", errors=errors)
    family_counts = _positive_counts(evidence.get("family_counts"), label="family", errors=errors)
    if sum(seed_counts.values()) != instances:
        errors.append("editorial mutation seed counts do not sum to instances")
    if sum(scenario_counts.values()) != instances:
        errors.append("editorial mutation scenario counts do not sum to instances")
    missing_families = REQUIRED_SCENARIO_FAMILIES - set(family_counts)
    if missing_families:
        errors.append("editorial mutation families missing: " + ", ".join(sorted(missing_families)))
    if sum(family_counts.values()) != instances:
        errors.append("editorial mutation family counts do not sum to instances")

    killed = {str(item) for item in (evidence.get("killed_mutation_classes") or [])}
    missing_kills = REQUIRED_KILLED_CLASSES - killed
    if missing_kills:
        errors.append("required editorial mutation classes survived/unexecuted: " + ", ".join(sorted(missing_kills)))
    try:
        deep_checks = int(evidence.get("deep_checks"))
        survivors = int(evidence.get("survivors"))
        mismatches = int(evidence.get("mismatches"))
    except (TypeError, ValueError, OverflowError):
        deep_checks, survivors, mismatches = -1, -1, -1
        errors.append("editorial mutation result counts malformed")
    if deep_checks < MIN_DEEP_CHECKS:
        errors.append("editorial mutation deep checks below minimum")
    if survivors != 0:
        errors.append("editorial mutation survivors remain")
    if mismatches != 0:
        errors.append("editorial mutation oracle mismatches remain")

    expected_spec = campaign_spec_digest(seeds=normalized_seeds, scenario_names=sorted(scenario_counts)) if normalized_seeds else ""
    if evidence.get("campaign_spec_digest") != expected_spec:
        errors.append("editorial mutation campaign specification digest mismatch")
    expected_digest = canonical_digest({k: v for k, v in evidence.items() if k != "digest"})
    if evidence.get("digest") != expected_digest:
        errors.append("editorial mutation evidence digest mismatch")
    return not errors, list(dict.fromkeys(errors))
