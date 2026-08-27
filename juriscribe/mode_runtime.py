"""Common execution invariants for all canonical Juriscribe modes.

The module does not replace mode-specific engines. It defines the smallest common
runtime spine that every mode must satisfy before its specialist pipeline runs:
input-role/cardinality integrity and deterministic invalidation of downstream
evidence when material or semantic foundations change.
"""
from __future__ import annotations

from typing import Any

from .modes import (
    COMPRESSION_AND_CONSOLIDATION,
    CONTINUATION,
    GREENFIELD,
    REVIEW,
    normalize_mode,
)

PROFILE = "JURISCRIBE_COMMON_MODE_RUNTIME_V1"
MATERIAL_INPUT_CHANGED = "MATERIAL_INPUT_CHANGED"
SEMANTIC_MODEL_CHANGED = "SEMANTIC_MODEL_CHANGED"

_POLICIES: dict[str, dict[str, Any]] = {
    CONTINUATION: {
        "engine_family": "CONTINUATION_GENERATION",
        "default_role": "preceding_chapter",
        "roles": {"preceding_chapter": {"min": 1, "max": None}},
        "specific_stages": ("CONTINUATION_FRONTIER", "GENERATION", "REVIEW_REGENERATION", "SIMULATION", "COMPRESSION"),
    },
    GREENFIELD: {
        "engine_family": "GREENFIELD_GENERATION",
        "default_role": "concept_source",
        "roles": {"concept_source": {"min": 1, "max": 1}},
        "specific_stages": ("GENERATION", "REVIEW_REGENERATION", "SIMULATION", "COMPRESSION"),
    },
    REVIEW: {
        "engine_family": "DIAGNOSTIC_OR_REVISION_REVIEW",
        "default_role": "review_target",
        "roles": {"review_target": {"min": 1, "max": 1}},
        "specific_stages": ("DIAGNOSTIC_REVIEW", "OPTIONAL_REVISION", "RE_REVIEW"),
    },
    COMPRESSION_AND_CONSOLIDATION: {
        "engine_family": "PROOF_CARRYING_REFACTORING",
        "default_role": "candidate_material",
        "roles": {
            "canonical_material": {"min": 1, "max": None},
            "candidate_material": {"min": 1, "max": None},
        },
        "specific_stages": (
            "LOSSLESS_INVENTORY", "JOINT_RETICULUM", "REFACTORING_PLAN",
            "MUTATION_EVIDENCE", "DUAL_SATURATION", "REFINED_CANDIDATES",
            "PEER_REVIEW_READINESS",
        ),
    },
}

_COMMON_STAGES = (
    "INPUT_BINDING",
    "SEMANTIC_RETICULUM",
    "USER_CONFIGURATION",
    "DOD_CONTRACT",
    "PROVENANCE",
    "FINAL_REVIEW",
    "MATERIALIZATION",
)


def _get(state: Any, name: str, default=None):
    return state.get(name, default) if isinstance(state, dict) else getattr(state, name, default)


def _set(state: Any, name: str, value: Any) -> None:
    if isinstance(state, dict):
        state[name] = value
    else:
        setattr(state, name, value)


def mode_runtime_profile(mode: str) -> dict[str, Any]:
    normalized = normalize_mode(mode)
    policy = _POLICIES[normalized]
    return {
        "profile": PROFILE,
        "mode": normalized,
        "engine_family": policy["engine_family"],
        "common_stages": list(_COMMON_STAGES),
        "specific_stages": list(policy["specific_stages"]),
        "default_role": policy["default_role"],
        "roles": {key: dict(value) for key, value in policy["roles"].items()},
    }


def resolve_input_role(mode: str, role: str | None = None) -> str:
    profile = mode_runtime_profile(mode)
    selected = str(role or profile["default_role"]).strip().lower()
    if selected not in profile["roles"]:
        allowed = ", ".join(profile["roles"])
        raise ValueError(f"input role {selected or '<empty>'} is not allowed for {profile['mode']}; allowed: {allowed}")
    return selected


def validate_mode_corpus(mode: str, corpus: list[dict[str, Any]] | None, *, require_minimum: bool = False) -> tuple[bool, list[str]]:
    profile = mode_runtime_profile(mode)
    entries = list(corpus or [])
    errors: list[str] = []
    seen_source_ids: set[str] = set()
    counts = {role: 0 for role in profile["roles"]}
    for index, item in enumerate(entries):
        source_id = str(item.get("source_id") or "").strip()
        role = str(item.get("role") or "").strip().lower()
        if not source_id:
            errors.append(f"corpus entry {index} source_id missing")
        elif source_id in seen_source_ids:
            errors.append(f"duplicate corpus source_id: {source_id}")
        else:
            seen_source_ids.add(source_id)
        if role not in profile["roles"]:
            errors.append(f"corpus role {role or '<empty>'} is not allowed for {profile['mode']}")
            continue
        counts[role] += 1
    for role, rule in profile["roles"].items():
        maximum = rule.get("max")
        if maximum is not None and counts[role] > int(maximum):
            errors.append(f"{profile['mode']} allows at most {maximum} {role} input(s)")
        if require_minimum and counts[role] < int(rule.get("min", 0)):
            errors.append(f"{profile['mode']} requires at least {rule.get('min', 0)} {role} input(s)")
    return not errors, list(dict.fromkeys(errors))


def assert_input_transition(state: Any, *, source_id: str, role: str | None = None) -> str:
    mode = normalize_mode(_get(state, "mode", ""))
    source_id = str(source_id or "").strip()
    if not source_id:
        raise ValueError("source_id must be non-empty")
    selected_role = resolve_input_role(mode, role)
    corpus = list(_get(state, "corpus", []) or [])
    ok, errors = validate_mode_corpus(mode, corpus, require_minimum=False)
    if not ok:
        raise ValueError("invalid current mode corpus: " + "; ".join(errors))
    profile = mode_runtime_profile(mode)
    for item in corpus:
        if str(item.get("source_id") or "").strip() != source_id:
            continue
        existing_role = str(item.get("role") or "").strip().lower()
        if existing_role != selected_role:
            raise ValueError(f"source {source_id} cannot change role from {existing_role} to {selected_role}")
        return selected_role
    maximum = profile["roles"][selected_role].get("max")
    if maximum is not None:
        count = sum(1 for item in corpus if str(item.get("role") or "").strip().lower() == selected_role)
        if count >= int(maximum):
            raise ValueError(f"{mode} allows at most {maximum} {selected_role} input(s); re-ingest the existing source_id to replace it")
    return selected_role


def _reset_source_coverage(state: Any) -> None:
    source_intelligence = dict(_get(state, "source_intelligence", {}) or {})
    if not source_intelligence:
        return
    source_intelligence["research_plan"] = []
    source_intelligence["dominance_assessments"] = []
    source_intelligence["coverage_status"] = "NOT_STARTED"
    _set(state, "source_intelligence", source_intelligence)


def _reset_metrics(state: Any) -> None:
    metrics = dict(_get(state, "metrics", {}) or {})
    for key in (
        "semantic_no_novelty_streak", "strategy_no_improvement_streak",
        "dod_no_novelty_streak", "review_no_novelty_streak",
        "review_no_improvement_streak", "simulations_run", "simulation_failures",
    ):
        if key in metrics:
            metrics[key] = 0
    _set(state, "metrics", metrics)


def invalidate_downstream(state: Any, *, boundary: str, reason: str) -> Any:
    """Invalidate evidence below a changed material/semantic foundation.

    This is an evidence-staleness operation, not a mode reset. Request, mode,
    admission, corpus/source records, explicit bibliography and C&C source
    inventories stay intact. Specialist engines may additionally clear their own
    proof stores.
    """
    if boundary not in {MATERIAL_INPUT_CHANGED, SEMANTIC_MODEL_CHANGED}:
        raise ValueError("unknown invalidation boundary")
    if boundary == MATERIAL_INPUT_CHANGED:
        _set(state, "epistemic_units", [])
        _set(state, "relations", [])
        _set(state, "reticulum", {})
    _set(state, "setup", {})
    _set(state, "editorial_standard", {})
    _set(state, "generation_contract", {})
    _set(state, "mode_contract", {})
    _set(state, "continuation", {"plan": {}, "coverage": {}, "benchmark_gap": {}, "status": "NOT_STARTED"})
    _set(state, "dod", [])
    _set(state, "drafts", [])
    review = dict(_get(state, "review", {}) or {})
    review.update({"cycles": [], "regenerations": [], "saturation": {}, "status": "NOT_STARTED"})
    review.pop("delivery_saturation", None)
    _set(state, "review", review)
    _set(state, "final_review", {})
    _set(state, "provenance", {})
    _set(state, "quality", {})
    _set(state, "benchmark", {})
    _set(state, "simulations", {})
    _set(state, "compression", {})
    _set(state, "claim_ledger", [])
    _set(state, "artifact_evidence", [])
    _set(state, "contradictions", [])
    _set(state, "editorial_actions", [])
    reflection = dict(_get(state, "reflection", {}) or {})
    if reflection:
        reflection.update({"iterations": 0, "no_novelty_streak": 0, "saturated": False})
        _set(state, "reflection", reflection)
    _reset_source_coverage(state)
    _reset_metrics(state)
    _set(state, "completion", {"eligible": False, "reason": str(reason)})
    return state
