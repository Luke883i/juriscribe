from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

ENVIRONMENT_SCHEMA = "juriscribe-local-session-environment/v1"
ENVIRONMENT_PROFILE = "JURISCRIBE_LOCAL_SESSION_ENVIRONMENT_V1"
COGNITIVE_PROFILE = "JURISCRIBE_LOCAL_COGNITIVE_RUNTIME_V1"
ENVIRONMENT_AUTHORITY = "HOST_COMPOSITION_ONLY"
BOOT_PROMPT_MAX_CHARS = 8000

# Kept for ADMISSION v9 / compatibility. Only `root` carries current local policy;
# the other four nodes are aliases that MUST point back to root.
CONTRACT_NODE_KEYS = ("root", "execution", "state", "surface", "failure_recovery")
ACTIVATION = {
    "POST_ACCEPTANCE_BOOTSTRAP": ("root", "execution"),
    "ACTIVE_SESSION": ("root", "state", "surface"),
    "FAILURE_OR_RECOVERY": ("root", "state", "failure_recovery"),
    "REBIND_OR_TRANSPORT_FAILURE": ("root", "execution", "failure_recovery"),
}

EXECUTION_PROFILES = ("LEAN", "ATTESTED")
EXECUTION_PROFILE_SCHEMA = "juriscribe-execution-profile/v1"
METHOD_KERNEL_PROFILE = "JURISCRIBE_METHOD_KERNEL_V1"
LOCAL_SEARCH_SCHEMA = "juriscribe-local-bootstrap-search/v1"

METHOD_KERNEL = (
    "MANDATE_OR_MODE_INTENT",
    "INPUT_INVENTORY",
    "SEMANTIC_DECOMPOSITION_RETICULUM",
    "SETUP_EDITORIAL_STANDARD_DOD",
    "SOURCE_CLAIM_INFERENCE_DISCIPLINE",
    "MODE_SPECIFIC_WORK",
    "REVIEW_REGENERATION_SATURATION_WHEN_APPLICABLE",
    "PROVENANCE",
    "SEVERE_FINAL_REVIEW",
    "ARTIFACT_TARGET",
    "HUMAN_VALIDATION",
)

EXECUTION_DEBT = (
    "RUNTIME_UNATTESTED",
    "STATE_EPHEMERAL",
    "MATERIALIZATION_UNAVAILABLE",
    "DELIVERY_UNAVAILABLE",
    "RECOVERY_UNAVAILABLE",
)

EPISTEMIC_DEBT = (
    "SOURCE_UNAVAILABLE",
    "AUTHORITY_UNVERIFIED",
    "JURISDICTION_UNRESOLVED",
    "MATERIAL_EVIDENCE_MISSING",
    "CLAIM_UNSUPPORTED",
)

LOCAL_PATH_CLASSES = (
    "INSTALLED_BOUND_RUNTIME",
    "LOCAL_CANONICAL_SOURCE",
    "CONNECTED_REPOSITORY_SOURCE",
    "PUBLIC_REPOSITORY_SOURCE",
    "PROBE_SOURCE_TO_RUNTIME_BRIDGE",
    "CANONICAL_OPERATION_CLOSURE",
    "FULL_PINNED_RUNTIME_PACKAGE",
    "LEAN_METHOD_KERNEL",
)


def _policy(admission: Mapping[str, Any]) -> Mapping[str, Any]:
    policy = admission.get("local_session_environment")
    if not isinstance(policy, Mapping):
        raise ValueError("local_session_environment policy missing")
    return policy


def validate_environment_policy(admission: Mapping[str, Any]) -> Mapping[str, Any]:
    policy = _policy(admission)
    expected_scalars = {
        "schema": ENVIRONMENT_SCHEMA,
        "profile": ENVIRONMENT_PROFILE,
        "authority": ENVIRONMENT_AUTHORITY,
        "scientific_authority": False,
        "runtime_authority_nodes_added": 0,
        "same_revision_required": True,
        "session_local_verified_cache_allowed": True,
        "live_main_rebind_forbidden": True,
        "runtime_state_synthesis_forbidden": True,
        "receipt_simulation_forbidden": True,
        "local_sufficiency_required_before_blocker": True,
    }
    for key, expected in expected_scalars.items():
        if policy.get(key) != expected:
            raise ValueError(f"local environment invariant mismatch: {key}")

    max_chars = int(policy.get("boot_prompt_max_chars", 0))
    if max_chars <= 0 or max_chars > BOOT_PROMPT_MAX_CHARS:
        raise ValueError("boot prompt maximum must be in 1..8000")

    nodes = policy.get("contract_nodes")
    if not isinstance(nodes, Mapping) or set(nodes.keys()) != set(CONTRACT_NODE_KEYS):
        raise ValueError("contract node keys/order mismatch")
    paths = [str(nodes[key]) for key in CONTRACT_NODE_KEYS]
    if len(set(paths)) != len(paths):
        raise ValueError("contract node paths must be unique")
    if any(not path.startswith("docs/host/") or not path.endswith(".md") for path in paths):
        raise ValueError("contract nodes must be Markdown files under docs/host")
    if str(policy.get("root")) != str(nodes["root"]):
        raise ValueError("root path differs from root contract node")

    prompt_path = str(policy.get("boot_prompt", ""))
    if not prompt_path.startswith("docs/host/") or not prompt_path.endswith(".md"):
        raise ValueError("boot prompt must be a Markdown file under docs/host")
    if prompt_path in paths:
        raise ValueError("boot prompt must not masquerade as a normative contract node")

    pre = tuple(str(item) for item in (admission.get("pre_admission_allowlist") or ()))
    if str(nodes["root"]) in pre or prompt_path in pre:
        raise ValueError("host environment files must not enter the pre-admission allowlist")

    activation = policy.get("activation")
    if not isinstance(activation, Mapping) or set(activation.keys()) != set(ACTIVATION.keys()):
        raise ValueError("activation trigger set/order mismatch")
    for trigger, expected in ACTIVATION.items():
        actual = tuple(str(item) for item in (activation.get(trigger) or ()))
        if actual != expected:
            raise ValueError(f"activation mismatch: {trigger}")
    return policy


def activation_plan(admission: Mapping[str, Any], trigger: str) -> dict[str, Any]:
    """Return the v1 compatibility activation plan.

    All paths remain valid for ADMISSION v9. The specialist Markdown files are now
    compatibility aliases; the root is the single current cognitive policy node.
    """
    policy = validate_environment_policy(admission)
    trigger = str(trigger).strip().upper()
    if trigger not in ACTIVATION:
        raise ValueError(f"unknown local environment trigger: {trigger}")
    nodes = policy["contract_nodes"]
    keys = tuple(policy["activation"][trigger])
    return {
        "schema": ENVIRONMENT_SCHEMA,
        "profile": ENVIRONMENT_PROFILE,
        "cognitive_profile": COGNITIVE_PROFILE,
        "trigger": trigger,
        "node_keys": list(keys),
        "paths": [str(nodes[key]) for key in keys],
        "normative_policy_path": str(nodes["root"]),
        "normative_policy_nodes": 1,
        "same_revision_required": True,
        "authority": ENVIRONMENT_AUTHORITY,
        "scientific_authority": False,
        "runtime_authority_nodes_added": 0,
    }


def execution_profile_choices() -> dict[str, Any]:
    return {
        "schema": EXECUTION_PROFILE_SCHEMA,
        "choices": [
            {
                "id": "LEAN",
                "label": "LEAN",
                "description": "Metodo Juriscribe completo; infrastruttura e attestazioni degradano esplicitamente quando non disponibili.",
            },
            {
                "id": "ATTESTED",
                "label": "ATTESTED",
                "description": "Runtime, receipt, persistence, proof e completion restano soggetti ai gate canonici forti.",
            },
        ],
        "scientific_mode": False,
        "authority": "HOST_EXECUTION_POLICY_ONLY",
        "auto_select_forbidden": True,
    }


def normalize_execution_profile(value: str) -> str:
    profile = str(value or "").strip().upper()
    if profile not in EXECUTION_PROFILES:
        raise ValueError("execution profile must be LEAN or ATTESTED")
    return profile


def method_kernel_contract() -> dict[str, Any]:
    return {
        "profile": METHOD_KERNEL_PROFILE,
        "steps": list(METHOD_KERNEL),
        "epistemic_discipline_degradable": False,
        "human_validation_required": True,
        "runtime_receipts_required": False,
        "runtime_authority": False,
        "claim_scope": "CANONICAL_METHOD_NOT_RUNTIME_ATTESTATION",
    }


def graded_execution_plan(
    profile: str,
    *,
    method_available: bool,
    runtime_ready: bool,
    persistence_ready: bool = False,
    materialization_ready: bool = False,
    delivery_ready: bool = False,
    recovery_ready: bool = False,
) -> dict[str, Any]:
    """Project capability truth into a graded execution decision.

    LEAN may continue the canonical method without runtime attestation. ATTESTED
    never silently degrades: when the method remains available it offers LEAN.
    """
    profile = normalize_execution_profile(profile)
    if runtime_ready:
        action = "RUN_ATTESTED"
        attestation = "RUNTIME_VERIFIED"
    elif method_available and profile == "LEAN":
        action = "RUN_LEAN_METHOD"
        attestation = "METHOD_GUIDED"
    elif method_available:
        action = "OFFER_LEAN"
        attestation = "UNAVAILABLE"
    else:
        action = "BLOCK_METHOD_UNAVAILABLE"
        attestation = "UNAVAILABLE"

    debt: list[str] = []
    if not runtime_ready:
        debt.append("RUNTIME_UNATTESTED")
    if runtime_ready and not persistence_ready:
        debt.append("STATE_EPHEMERAL")
    if not materialization_ready:
        debt.append("MATERIALIZATION_UNAVAILABLE")
    if not delivery_ready:
        debt.append("DELIVERY_UNAVAILABLE")
    if not recovery_ready:
        debt.append("RECOVERY_UNAVAILABLE")

    return {
        "schema": EXECUTION_PROFILE_SCHEMA,
        "requested_profile": profile,
        "action": action,
        "method_available": bool(method_available),
        "runtime_ready": bool(runtime_ready),
        "attestation": attestation,
        "execution_debt": debt,
        "runtime_receipts_may_be_claimed": bool(runtime_ready),
        "runtime_complete_may_be_claimed": bool(runtime_ready),
        "promotion_requires_replay": not runtime_ready and bool(method_available),
        "method_kernel": METHOD_KERNEL_PROFILE if method_available else None,
    }


def artifact_trajectory(
    *,
    content_ready: bool,
    materialized: bool,
    delivered: bool,
    runtime_attested: bool,
    complete: bool = False,
) -> dict[str, Any]:
    if delivered and not materialized:
        raise ValueError("delivered artifact must be materialized")
    if materialized and not content_ready:
        raise ValueError("materialized artifact must have content ready")
    if complete and not runtime_attested:
        raise PermissionError("COMPLETE cannot be claimed by METHOD_GUIDED output")
    physical = "DELIVERED" if delivered else "MATERIALIZED" if materialized else "CONTENT_READY" if content_ready else "PENDING"
    return {
        "physical": physical,
        "attestation": "RUNTIME_VERIFIED" if runtime_attested else "METHOD_GUIDED",
        "complete": bool(complete),
        "human_validation_required": True,
    }


def promotion_plan(*, method_work_exists: bool, runtime_ready: bool) -> dict[str, Any]:
    if not method_work_exists:
        return {"action": "NO_PROMOTION_NEEDED", "steps": []}
    if not runtime_ready:
        return {"action": "WAIT_FOR_RUNTIME", "steps": []}
    return {
        "action": "REPLAY_REQUIRED",
        "steps": [
            "REAL_ADMISSION_PROBE_INITIALIZE_AS_APPLICABLE",
            "REAL_MODE_SELECTION",
            "CANONICAL_INPUT_REPLAY",
            "RECOMPUTE_APPLICABLE_PROOF_AND_GATES",
            "FRESH_MATERIALIZATION_AND_READBACK",
        ],
        "prior_method_work_is_proof": False,
    }


def _state(capabilities: Mapping[str, str], name: str) -> str:
    value = str(capabilities.get(name, "UNVERIFIED")).strip().upper()
    return value if value in {"AVAILABLE", "UNAVAILABLE", "UNVERIFIED"} else "UNVERIFIED"


def _not_unavailable(capabilities: Mapping[str, str], name: str) -> bool:
    return _state(capabilities, name) != "UNAVAILABLE"


def _available(capabilities: Mapping[str, str], name: str) -> bool:
    return _state(capabilities, name) == "AVAILABLE"


def plan_local_bootstrap_search(
    capabilities: Mapping[str, str],
    *,
    installed_runtime_bound: bool = False,
    operation_closure_available: bool = False,
    method_available: bool = True,
) -> dict[str, Any]:
    """Enumerate materially distinct, safe local paths before a blocker.

    `gh` is deliberately absent: the host assumes it unavailable until observed and
    never makes it a bootstrap dependency. UNVERIFIED capabilities may justify a
    probe path; only explicit UNAVAILABLE removes that path.
    """
    candidates: list[dict[str, Any]] = []

    if installed_runtime_bound and _available(capabilities, "RUNTIME_IMPORT"):
        candidates.append({"class": "INSTALLED_BOUND_RUNTIME", "action": "USE", "priority": 10})

    python_possible = _not_unavailable(capabilities, "PYTHON_EXECUTION")
    scratch_possible = _not_unavailable(capabilities, "LOCAL_SCRATCH_IO")
    generic_repo = _not_unavailable(capabilities, "REPOSITORY_READ")

    if python_possible and scratch_possible and _not_unavailable(capabilities, "LOCAL_REPOSITORY_READ"):
        candidates.append({"class": "LOCAL_CANONICAL_SOURCE", "action": "TRY", "priority": 20})
    if python_possible and scratch_possible and (_not_unavailable(capabilities, "CONNECTED_REPOSITORY_READ") or generic_repo):
        candidates.append({"class": "CONNECTED_REPOSITORY_SOURCE", "action": "TRY", "priority": 30})
    if python_possible and scratch_possible and _not_unavailable(capabilities, "PUBLIC_REPOSITORY_READ"):
        candidates.append({"class": "PUBLIC_REPOSITORY_SOURCE", "action": "TRY", "priority": 40})

    if python_possible and scratch_possible and generic_repo and _state(capabilities, "SOURCE_TO_RUNTIME_BRIDGE") == "UNVERIFIED":
        candidates.append({"class": "PROBE_SOURCE_TO_RUNTIME_BRIDGE", "action": "PROBE", "priority": 50})

    if operation_closure_available and python_possible and scratch_possible and generic_repo:
        candidates.append({"class": "CANONICAL_OPERATION_CLOSURE", "action": "TRY", "priority": 60})

    if python_possible and scratch_possible and generic_repo:
        candidates.append({"class": "FULL_PINNED_RUNTIME_PACKAGE", "action": "TRY", "priority": 70})

    if method_available:
        candidates.append({"class": "LEAN_METHOD_KERNEL", "action": "DEGRADE_WITH_DISCLOSURE", "priority": 90})

    unique: dict[str, dict[str, Any]] = {}
    for item in sorted(candidates, key=lambda x: int(x["priority"])):
        unique.setdefault(str(item["class"]), item)
    ordered = list(unique.values())
    return {
        "schema": LOCAL_SEARCH_SCHEMA,
        "candidates": ordered,
        "candidate_classes": [item["class"] for item in ordered],
        "gh_cli_required": False,
        "privilege_escalation_allowed": False,
        "arbitrary_software_install_allowed": False,
        "unverified_is_unavailable": False,
        "authority": "HOST_SEARCH_POLICY_ONLY",
    }


def next_local_path(search_plan: Mapping[str, Any], attempts: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    seen = {str(item.get("class")) for item in attempts if item.get("attempted") is True}
    for candidate in search_plan.get("candidates") or []:
        if str(candidate.get("class")) not in seen:
            return dict(candidate)
    return None


def local_blocker_status(
    search_plan: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    *,
    requested_profile: str,
) -> dict[str, Any]:
    profile = normalize_execution_profile(requested_profile)
    next_path = next_local_path(search_plan, attempts)
    if next_path is not None:
        return {"blocker_allowed": False, "action": "TRY_NEXT_LOCAL_PATH", "next": next_path}
    method_candidate = "LEAN_METHOD_KERNEL" in set(search_plan.get("candidate_classes") or [])
    if profile == "ATTESTED" and method_candidate:
        return {"blocker_allowed": False, "action": "OFFER_LEAN", "next": None}
    if profile == "LEAN" and method_candidate:
        return {"blocker_allowed": False, "action": "RUN_LEAN_METHOD", "next": None}
    return {"blocker_allowed": True, "action": "BLOCK", "next": None}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def validate_environment_files(repo_root: str | Path, admission: Mapping[str, Any]) -> dict[str, Any]:
    policy = validate_environment_policy(admission)
    root = Path(repo_root)
    nodes = policy["contract_nodes"]
    paths = {key: root / str(nodes[key]) for key in CONTRACT_NODE_KEYS}
    prompt_path = root / str(policy["boot_prompt"])
    for path in [*paths.values(), prompt_path]:
        if not path.is_file():
            raise FileNotFoundError(f"local environment file missing: {path}")

    texts = {key: path.read_text(encoding="utf-8") for key, path in paths.items()}
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_chars = len(prompt)
    if prompt_chars > int(policy["boot_prompt_max_chars"]):
        raise ValueError(f"boot prompt exceeds declared character limit: {prompt_chars}")

    root_text = texts["root"]
    for token in (
        COGNITIVE_PROFILE,
        "LEAN",
        "ATTESTED",
        "METHOD KERNEL",
        "LOCAL BOOTSTRAP SEARCH",
        "CHAT_CONTEXT_MAP",
        "COMPLETE",
    ):
        if token not in root_text:
            raise ValueError(f"cognitive root missing invariant: {token}")

    root_name = Path(str(nodes["root"])).name
    for key in CONTRACT_NODE_KEYS[1:]:
        alias = texts[key]
        if "COMPATIBILITY ALIAS" not in alias or root_name not in alias:
            raise ValueError(f"{key} is not a compatibility alias to cognitive root")

    for token in (
        "pre_admission_allowlist",
        "resolved_revision",
        "CHAT_CONTEXT_MAP",
        "`UNVERIFIED`",
        "`UNAVAILABLE`",
        "gh",
        "LEAN",
        "ATTESTED",
        root_name,
    ):
        if token not in prompt:
            raise ValueError(f"boot prompt missing anchor: {token}")
    if "COMPRESSION & CONSOLIDATION" in prompt:
        raise ValueError("boot prompt duplicates canonical scientific mode taxonomy")

    payload = {
        "schema": ENVIRONMENT_SCHEMA,
        "profile": ENVIRONMENT_PROFILE,
        "cognitive_profile": COGNITIVE_PROFILE,
        "authority": ENVIRONMENT_AUTHORITY,
        "prompt_chars": prompt_chars,
        "prompt_limit": int(policy["boot_prompt_max_chars"]),
        "normative_policy_nodes": 1,
        "compatibility_alias_nodes": len(CONTRACT_NODE_KEYS) - 1,
        "nodes": {
            key: {"path": str(nodes[key]), "sha256": _sha256(texts[key])}
            for key in CONTRACT_NODE_KEYS
        },
        "boot_prompt": {"path": str(policy["boot_prompt"]), "sha256": _sha256(prompt)},
        "activation": {key: list(value) for key, value in ACTIVATION.items()},
        "runtime_authority_nodes_added": 0,
    }
    payload["graph_sha256"] = _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return payload
