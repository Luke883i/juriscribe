from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "juriscribe-mode-contract/v1"
CONTINUATION = "CONTINUATION"
GREENFIELD = "GREENFIELD"
REVIEW = "REVIEW"
COMPRESSION_AND_CONSOLIDATION = "COMPRESSION & CONSOLIDATION"
# Python compatibility symbol only. Serialized/user-visible mode values use the label above.
COMPRESSION_CONSOLIDATION = COMPRESSION_AND_CONSOLIDATION
LEGACY_MODES = (CONTINUATION, GREENFIELD, REVIEW)
MODES = (*LEGACY_MODES, COMPRESSION_AND_CONSOLIDATION)
REVIEW_OUTPUTS = {"REPORT_ONLY", "REPORT_AND_REVISED_TEXT"}

COMMON_RUNTIME_STAGES = (
    "INPUT_BINDING",
    "SEMANTIC_RETICULUM",
    "USER_CONFIGURATION",
    "DOD_CONTRACT",
    "PROVENANCE",
    "FINAL_REVIEW",
    "MATERIALIZATION",
)

# One canonical registry for every mode-level invariant that must be shared by
# runtime admission of material, specialist routing and conversational projection.
# Substantive proof semantics remain in their specialist engines.
MODE_REGISTRY: dict[str, dict[str, Any]] = {
    CONTINUATION: {
        "engine_family": "CONTINUATION_GENERATION",
        "default_role": "preceding_chapter",
        "roles": {"preceding_chapter": {"min": 1, "max": None}},
        "specific_stages": (
            "CONTINUATION_FRONTIER",
            "GENERATION",
            "REVIEW_REGENERATION",
            "SIMULATION",
            "COMPRESSION",
        ),
        "entry": {
            "summary": "Modalità CONTINUATION selezionata. Carica i capitoli precedenti.",
            "choices": ["CARICA CAPITOLI PRECEDENTI", "ALTRO"],
        },
    },
    GREENFIELD: {
        "engine_family": "GREENFIELD_GENERATION",
        "default_role": "concept_source",
        "roles": {"concept_source": {"min": 1, "max": 1}},
        "specific_stages": (
            "GENERATION",
            "REVIEW_REGENERATION",
            "SIMULATION",
            "COMPRESSION",
        ),
        "entry": {
            "summary": "Modalità GREENFIELD selezionata. Fornisci il concept o mandato di partenza.",
            "choices": ["FORNISCI CONCEPT", "ALTRO"],
        },
    },
    REVIEW: {
        "engine_family": "DIAGNOSTIC_OR_REVISION_REVIEW",
        "default_role": "review_target",
        "roles": {"review_target": {"min": 1, "max": 1}},
        "specific_stages": (
            "DIAGNOSTIC_REVIEW",
            "OPTIONAL_REVISION",
            "RE_REVIEW",
        ),
        "entry": {
            "summary": "Modalità REVIEW selezionata. Carica il testo da revisionare.",
            "choices": ["CARICA TESTO DA REVISIONARE", "ALTRO"],
        },
    },
    COMPRESSION_AND_CONSOLIDATION: {
        "engine_family": "PROOF_CARRYING_REFACTORING",
        "default_role": "candidate_material",
        "roles": {
            "canonical_material": {"min": 1, "max": None},
            "candidate_material": {"min": 1, "max": None},
        },
        "specific_stages": (
            "LOSSLESS_INVENTORY",
            "JOINT_RETICULUM",
            "REFACTORING_PLAN",
            "MUTATION_EVIDENCE",
            "DUAL_SATURATION",
            "REFINED_CANDIDATES",
            "PEER_REVIEW_READINESS",
        ),
        "entry": {
            "summary": (
                "Modalità COMPRESSION & CONSOLIDATION selezionata. Carica materiali "
                "CANONICAL immutabili e CANDIDATE rifattorizzabili."
            ),
            "choices": ["CARICA CANONICAL", "CARICA CANDIDATE", "ALTRO"],
        },
    },
}

COMMON_FINAL_ARTIFACT_ROLES = {
    "evidence_dossier",
    "source_register",
    "inference_register",
    "transformation_ledger",
    "session_dashboard",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_mode(mode: str | None) -> str:
    raw = str(mode or "").strip().upper()
    if raw == COMPRESSION_AND_CONSOLIDATION:
        return COMPRESSION_AND_CONSOLIDATION
    value = raw.replace("&", "AND").replace("-", "_").replace(" ", "_")
    while "__" in value:
        value = value.replace("__", "_")
    legacy_serialized = "COMPRESSION" + "_" + "CONSOLIDATION"
    aliases = {
        "CONTINUE": CONTINUATION,
        "CONTINUAZIONE": CONTINUATION,
        "CHAPTER_CONTINUATION": CONTINUATION,
        "EX_NOVO": GREENFIELD,
        "NEW": GREENFIELD,
        "NUOVO": GREENFIELD,
        "GREEN_FIELD": GREENFIELD,
        "REVISION": REVIEW,
        "REVISIONE": REVIEW,
        "AUDIT": REVIEW,
        "COMPRESSION_AND_CONSOLIDATION": COMPRESSION_AND_CONSOLIDATION,
        legacy_serialized: COMPRESSION_AND_CONSOLIDATION,
        "CONSOLIDATION": COMPRESSION_AND_CONSOLIDATION,
        "CONSOLIDAMENTO": COMPRESSION_AND_CONSOLIDATION,
    }
    value = aliases.get(value, value)
    if value not in MODES:
        raise ValueError("mode must be one of: " + ", ".join(MODES))
    return value


def mode_choices() -> list[str]:
    return list(MODES)


def mode_runtime_spec(mode: str) -> dict[str, Any]:
    normalized = normalize_mode(mode)
    policy = MODE_REGISTRY[normalized]
    return {
        "mode": normalized,
        "engine_family": policy["engine_family"],
        "common_stages": list(COMMON_RUNTIME_STAGES),
        "specific_stages": list(policy["specific_stages"]),
        "default_role": policy["default_role"],
        "roles": {key: dict(value) for key, value in policy["roles"].items()},
    }


def mode_entry_projection(mode: str) -> dict[str, Any]:
    normalized = normalize_mode(mode)
    entry = MODE_REGISTRY[normalized]["entry"]
    return {
        "mode": normalized,
        "summary": str(entry["summary"]),
        "choices": list(entry["choices"]),
    }


def review_output(setup: dict[str, Any] | None) -> str:
    accepted = (setup or {}).get("accepted", setup or {})
    value = str(accepted.get("review_output", "REPORT_ONLY")).upper()
    return value if value in REVIEW_OUTPUTS else "REPORT_ONLY"


def mode_spec(mode: str, setup: dict[str, Any] | None = None) -> dict[str, Any]:
    mode = normalize_mode(mode)
    runtime = mode_runtime_spec(mode)
    if mode == CONTINUATION:
        return {"mode": mode, "seed_required": True, "concept_required": False, "review_target_required": False, "generation_required": True, "continuation_required": True, "revision_required": True, "compression_required": True, "simulation_required": True, "quality_must_pass": True, "source_coverage_must_close": True, "primary_artifact_role": "final_chapter", "input_role": runtime["default_role"]}
    if mode == GREENFIELD:
        return {"mode": mode, "seed_required": False, "concept_required": True, "review_target_required": False, "generation_required": True, "continuation_required": False, "revision_required": True, "compression_required": True, "simulation_required": True, "quality_must_pass": True, "source_coverage_must_close": True, "primary_artifact_role": "final_legal_text", "input_role": runtime["default_role"]}
    if mode == COMPRESSION_AND_CONSOLIDATION:
        return {"mode": mode, "seed_required": False, "concept_required": False, "review_target_required": False, "generation_required": False, "continuation_required": False, "revision_required": True, "compression_required": True, "simulation_required": True, "quality_must_pass": True, "source_coverage_must_close": True, "primary_artifact_role": "refactoring_report", "input_role": runtime["default_role"], "input_roles": list(runtime["roles"]), "canonical_material_immutable": True, "candidate_material_required": True, "mutation_cases_min": 10_000_000, "no_novelty_tail_min": 1000, "no_better_compression_tail_min": 1000}
    output = review_output(setup)
    revised = output == "REPORT_AND_REVISED_TEXT"
    return {"mode": REVIEW, "seed_required": False, "concept_required": False, "review_target_required": True, "generation_required": False, "continuation_required": False, "revision_required": revised, "compression_required": False, "simulation_required": False, "quality_must_pass": revised, "source_coverage_must_close": revised, "primary_artifact_role": "review_report", "secondary_artifact_role": "revised_legal_text" if revised else "", "input_role": runtime["default_role"], "review_output": output}


def required_artifact_roles(mode: str, setup: dict[str, Any] | None = None) -> set[str]:
    spec = mode_spec(mode, setup)
    roles = set(COMMON_FINAL_ARTIFACT_ROLES)
    roles.add(spec["primary_artifact_role"])
    if spec.get("secondary_artifact_role"):
        roles.add(str(spec["secondary_artifact_role"]))
    if spec["mode"] == REVIEW:
        roles.add("review_findings_register")
    if spec["mode"] == COMPRESSION_AND_CONSOLIDATION:
        roles.add("refined_candidate")
    return roles


def required_artifact_requirements(mode: str, setup: dict[str, Any] | None = None, corpus: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    mode = normalize_mode(mode)
    requirements = [{"role": role, "instance_key": role, "required": True} for role in sorted(required_artifact_roles(mode, setup)) if role != "refined_candidate"]
    if mode == COMPRESSION_AND_CONSOLIDATION:
        candidates = [c for c in (corpus or []) if c.get("role") == "candidate_material"]
        if candidates:
            requirements.extend({"role": "refined_candidate", "instance_key": str(c.get("source_id") or c.get("digest") or "candidate"), "source_id": str(c.get("source_id") or ""), "required": True} for c in candidates)
        else:
            requirements.append({"role": "refined_candidate", "instance_key": "candidate_material:*", "required": True, "cardinality": "ONE_PER_CANDIDATE"})
    return requirements


def mode_selection_record(mode: str, *, request: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_mode(mode)
    payload = {"schema": "juriscribe-mode-selection/v1", "mode": normalized, "request_digest": canonical_digest(request or {}), "status": "SELECTED"}
    payload["digest"] = canonical_digest(payload)
    return payload


def _target_digest(mode: str, corpus: list[dict[str, Any]]) -> str:
    mode = normalize_mode(mode)
    if mode == COMPRESSION_AND_CONSOLIDATION:
        candidates = sorted(str(c.get("digest", "")) for c in corpus if c.get("role") == "candidate_material" and c.get("digest"))
        return canonical_digest(candidates) if candidates else ""
    role = mode_spec(mode)["input_role"]
    matches = [str(c.get("digest", "")) for c in corpus if c.get("role") == role and c.get("digest")]
    if mode == CONTINUATION:
        return canonical_digest(matches)
    return matches[-1] if matches else ""


def build_mode_contract(mode: str, *, request: dict[str, Any], corpus: list[dict[str, Any]], reticulum: dict[str, Any], setup: dict[str, Any], editorial_standard: dict[str, Any], generation_contract: dict[str, Any] | None = None) -> dict[str, Any]:
    mode = normalize_mode(mode)
    spec = mode_spec(mode, setup)
    errors: list[str] = []
    if reticulum.get("status") != "PASS": errors.append("validated reticulum required")
    if setup.get("status") != "ACCEPTED": errors.append("accepted setup required")
    if editorial_standard.get("status") != "READY": errors.append("editorial standard must be READY")
    target = _target_digest(mode, corpus)
    if spec["seed_required"] and not any(c.get("role") == "preceding_chapter" for c in corpus): errors.append("continuation mode requires preceding chapters")
    if spec["concept_required"] and not any(c.get("role") == "concept_source" for c in corpus): errors.append("greenfield mode requires a concept/prompt source")
    if spec["review_target_required"] and not target: errors.append("review mode requires a supplied review target")
    if mode == COMPRESSION_AND_CONSOLIDATION and not any(c.get("role") == "candidate_material" for c in corpus): errors.append("compression/consolidation requires at least one candidate material")
    if spec["generation_required"] and (generation_contract or {}).get("status") != "READY": errors.append("generation contract required for writing mode")
    payload = {"schema": SCHEMA, "mode": mode, "request_digest": canonical_digest(request), "corpus_digest": canonical_digest(corpus), "target_digest": target, "reticulum_digest": str(reticulum.get("digest", "")), "setup_digest": canonical_digest(setup.get("accepted", {})), "editorial_standard_digest": str(editorial_standard.get("digest", "")), "generation_contract_digest": str((generation_contract or {}).get("contract_digest", "")), "requirements": spec, "required_artifact_roles": sorted(required_artifact_roles(mode, setup)), "status": "READY" if not errors else "FAIL", "errors": errors}
    if mode == COMPRESSION_AND_CONSOLIDATION:
        payload["artifact_requirements"] = required_artifact_requirements(mode, setup, corpus)
    payload["digest"] = canonical_digest(payload)
    return payload


def validate_mode_contract(contract: dict[str, Any] | None, *, mode: str, request: dict[str, Any], corpus: list[dict[str, Any]], reticulum: dict[str, Any], setup: dict[str, Any], editorial_standard: dict[str, Any], generation_contract: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    if not contract: return False, ["mode contract missing"]
    mode = normalize_mode(mode)
    expected = build_mode_contract(mode, request=request, corpus=corpus, reticulum=reticulum, setup=setup, editorial_standard=editorial_standard, generation_contract=generation_contract)
    errors = list(contract.get("errors", []))
    if contract.get("schema") != SCHEMA: errors.append("mode contract schema mismatch")
    if contract.get("status") != "READY": errors.append("mode contract not READY")
    keys = ["mode", "request_digest", "corpus_digest", "target_digest", "reticulum_digest", "setup_digest", "editorial_standard_digest", "generation_contract_digest", "requirements", "required_artifact_roles"]
    if mode == COMPRESSION_AND_CONSOLIDATION:
        keys.append("artifact_requirements")
    for key in keys:
        if contract.get(key) != expected.get(key): errors.append(f"mode contract {key} mismatch")
    digest = canonical_digest({k: v for k, v in contract.items() if k != "digest"})
    if contract.get("digest") != digest: errors.append("mode contract digest mismatch")
    return not errors, list(dict.fromkeys(errors))
