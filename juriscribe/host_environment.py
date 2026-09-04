from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from . import graded_execution as ge
except ImportError:
    import importlib.util
    import sys
    _p = Path(__file__).with_name("graded_execution.py")
    _spec = importlib.util.spec_from_file_location("juriscribe_graded_execution_standalone", _p)
    if _spec is None or _spec.loader is None:
        raise
    ge = importlib.util.module_from_spec(_spec)
    sys.modules[_spec.name] = ge
    _spec.loader.exec_module(ge)

ENVIRONMENT_SCHEMA = "juriscribe-local-session-environment/v1"
ENVIRONMENT_PROFILE = "JURISCRIBE_LOCAL_SESSION_ENVIRONMENT_V1"
COGNITIVE_PROFILE = "JURISCRIBE_RUNTIME_LOCAL_HOST_V1"
ENVIRONMENT_AUTHORITY = "HOST_COMPOSITION_ONLY"
COGNITIVE_AUTHORITY = "HOST_ORCHESTRATION_AND_PROJECTION_ONLY"
BOOT_PROMPT_MAX_CHARS = 8000
CONTRACT_NODE_KEYS = ("root", "execution", "state", "surface", "failure_recovery")
ACTIVATION = {
    "POST_ACCEPTANCE_BOOTSTRAP": ("root", "execution"),
    "ACTIVE_SESSION": ("root", "state", "surface"),
    "FAILURE_OR_RECOVERY": ("root", "state", "failure_recovery"),
    "REBIND_OR_TRANSPORT_FAILURE": ("root", "execution", "failure_recovery"),
}
EXECUTION_PROFILES = ("LEAN", "ATTESTED")
EXECUTION_PROFILE_SCHEMA = "juriscribe-execution-profile/v1"
METHOD_KERNEL_PROFILE = ge.METHOD_KERNEL_PROFILE
LOCAL_SEARCH_SCHEMA = "juriscribe-local-bootstrap-search/v2"
LOCAL_PATH_CLASSES = ge.PATH_CLASSES


def _policy(admission: Mapping[str, Any]) -> Mapping[str, Any]:
    policy = admission.get("local_session_environment")
    if not isinstance(policy, Mapping):
        raise ValueError("local_session_environment policy missing")
    return policy


def _cognitive_policy(admission: Mapping[str, Any]) -> Mapping[str, Any]:
    policy = admission.get("local_cognitive_system")
    if not isinstance(policy, Mapping):
        raise ValueError("local_cognitive_system policy missing")
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
    if not isinstance(nodes, Mapping) or tuple(nodes.keys()) != CONTRACT_NODE_KEYS:
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
    if any(path in pre for path in [*paths, prompt_path]):
        raise ValueError("post-admission host files must not enter the pre-admission allowlist")
    activation = policy.get("activation")
    if not isinstance(activation, Mapping) or tuple(activation.keys()) != tuple(ACTIVATION.keys()):
        raise ValueError("activation trigger set/order mismatch")
    for trigger, expected in ACTIVATION.items():
        actual = tuple(str(item) for item in (activation.get(trigger) or ()))
        if actual != expected:
            raise ValueError(f"activation mismatch: {trigger}")
    cognitive = _cognitive_policy(admission)
    expected_cognitive = {
        "schema": "juriscribe-runtime-local-host/v1",
        "profile": COGNITIVE_PROFILE,
        "authority": COGNITIVE_AUTHORITY,
        "scientific_authority": False,
        "runtime_authority_nodes_added": 0,
        "same_revision_required": True,
        "normative_host_nodes_replaced": False,
        "load_before_acceptance": False,
    }
    for key, expected in expected_cognitive.items():
        if cognitive.get(key) != expected:
            raise ValueError(f"local cognitive invariant mismatch: {key}")
    cpath = str(cognitive.get("cognitive_policy", ""))
    if not cpath.startswith("docs/host/") or not cpath.endswith(".md") or cpath in paths:
        raise ValueError("cognitive companion path must be a distinct docs/host Markdown file")
    if cpath in pre:
        raise ValueError("cognitive companion must remain post-admission")
    if str(cognitive.get("boot_prompt")) != prompt_path:
        raise ValueError("cognitive system boot prompt differs from environment boot prompt")
    return policy


def activation_plan(admission: Mapping[str, Any], trigger: str) -> dict[str, Any]:
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
        "normative_policy_nodes": len(CONTRACT_NODE_KEYS),
        "cognitive_companion_nodes": 1,
        "same_revision_required": True,
        "authority": ENVIRONMENT_AUTHORITY,
        "scientific_authority": False,
        "runtime_authority_nodes_added": 0,
    }


def execution_profile_choices() -> dict[str, Any]:
    return {
        "schema": EXECUTION_PROFILE_SCHEMA,
        "choices": ["LEAN", "ATTESTED"],
        "scientific_mode": False,
        "mandatory_selection": False,
        "default_preference": "ATTESTED_PREFERRED",
        "auto_select_forbidden": False,
        "authority": "HOST_EXECUTION_POLICY_ONLY",
    }


def normalize_execution_profile(value: str) -> str:
    profile = str(value or "").strip().upper()
    if profile not in EXECUTION_PROFILES:
        raise ValueError("execution profile must be LEAN or ATTESTED")
    return profile


def method_kernel_contract() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    kernel = ge.load_method_kernel(root / "METHOD_KERNEL.json")
    return {
        "profile": kernel["profile"],
        "method_degradation_allowed": kernel["method_degradation_allowed"],
        "epistemic_degradation_allowed": kernel["epistemic_degradation_allowed"],
        "human_validation_required": kernel["human_validation_required"],
        "mode_methods": kernel["mode_methods"],
        "runtime_authority": False,
        "claim_scope": "CANONICAL_METHOD_NOT_RUNTIME_ATTESTATION",
    }


def graded_execution_plan(profile: str, *, method_available: bool, runtime_ready: bool, persistence_ready: bool = False, materialization_ready: bool = False, delivery_ready: bool = False, recovery_ready: bool = False) -> dict[str, Any]:
    profile = normalize_execution_profile(profile)
    access = ge.MethodAccess(method_available, method_available, method_available, method_available)
    decision = ge.choose_execution_profile(access, runtime_reachable=runtime_ready, infrastructure_search_exhausted=True, capability_discovery_complete=True, preference="LEAN" if profile == "LEAN" else "ATTESTED_REQUIRED")
    debt: list[str] = []
    if not runtime_ready: debt.append("RUNTIME_UNATTESTED")
    if runtime_ready and not persistence_ready: debt.append("STATE_EPHEMERAL")
    if not materialization_ready: debt.append("MATERIALIZATION_UNAVAILABLE")
    if not delivery_ready: debt.append("DELIVERY_UNAVAILABLE")
    if not recovery_ready: debt.append("RECOVERY_UNAVAILABLE")
    resolved = decision.get("profile")
    action = {
        ("LEAN", "WORK_READY"): "RUN_LEAN_METHOD",
        ("ATTESTED", "WORK_READY"): "RUN_ATTESTED",
        (None, "ATTESTED_INFRASTRUCTURE_BLOCKED"): "OFFER_LEAN",
        (None, "METHOD_ACCESS_BLOCKED"): "BLOCK_METHOD_UNAVAILABLE",
    }.get((resolved, decision.get("state")), decision.get("state"))
    claims = ge.runtime_claim_projection(profile=resolved or "LEAN", runtime_reachable=runtime_ready, receipts_verified=False, complete_verified=False) if resolved else {"runtime_attestation": False, "runtime_receipts_may_be_claimed": False, "runtime_complete_may_be_claimed": False}
    return {
        "schema": EXECUTION_PROFILE_SCHEMA,
        "requested_profile": profile,
        "action": action,
        "method_available": bool(method_available),
        "runtime_ready": bool(runtime_ready),
        "attestation": "RUNTIME_REACHABLE" if claims["runtime_attestation"] else "METHOD_GUIDED" if resolved == "LEAN" else "UNAVAILABLE",
        "execution_debt": debt,
        **claims,
        "promotion_requires_replay": resolved == "LEAN" and method_available,
        "method_kernel": METHOD_KERNEL_PROFILE if method_available else None,
    }


def artifact_trajectory(*, content_ready: bool, materialized: bool, delivered: bool, runtime_attested: bool, complete: bool = False) -> dict[str, Any]:
    if delivered and not materialized:
        raise ValueError("delivered artifact must be materialized")
    if materialized and not content_ready:
        raise ValueError("materialized artifact must have content ready")
    if complete and not runtime_attested:
        raise PermissionError("COMPLETE cannot be claimed by METHOD_GUIDED output")
    physical = "DELIVERED" if delivered else "MATERIALIZED" if materialized else "CONTENT_READY" if content_ready else "PENDING"
    return {"physical": physical, "attestation": "RUNTIME_VERIFIED" if runtime_attested else "METHOD_GUIDED", "complete": bool(complete), "human_validation_required": True}


def promotion_plan(*, method_work_exists: bool, runtime_ready: bool) -> dict[str, Any]:
    if not method_work_exists:
        return {"action": "NO_PROMOTION_NEEDED", "steps": []}
    if not runtime_ready:
        return {"action": "WAIT_FOR_RUNTIME", "steps": []}
    return {"action": "REPLAY_REQUIRED", "steps": ["REAL_ADMISSION_PROBE_INITIALIZE_AS_APPLICABLE", "REAL_MODE_SELECTION", "CANONICAL_INPUT_REPLAY", "RECOMPUTE_APPLICABLE_PROOF_AND_GATES", "FRESH_MATERIALIZATION_AND_READBACK"], "prior_method_work_is_proof": False}


def plan_local_bootstrap_search(capabilities: Mapping[str, str], *, installed_runtime_bound: bool = False, operation_closure_available: bool = False, method_available: bool = True) -> dict[str, Any]:
    classes = ge.eligible_path_classes(capabilities, installed_runtime_bound=installed_runtime_bound, operation_closure_available=operation_closure_available)
    return {
        "schema": LOCAL_SEARCH_SCHEMA,
        "candidates": [{"class": c, "action": "TRY"} for c in classes],
        "candidate_classes": list(classes),
        "method_access_available": bool(method_available),
        "lean_is_runtime_transport_class": False,
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


def local_blocker_status(search_plan: Mapping[str, Any], attempts: Sequence[Mapping[str, Any]], *, requested_profile: str) -> dict[str, Any]:
    profile = normalize_execution_profile(requested_profile)
    nxt = next_local_path(search_plan, attempts)
    if nxt is not None:
        return {"blocker_allowed": False, "action": "TRY_NEXT_LOCAL_PATH", "next": nxt}
    method = bool(search_plan.get("method_access_available"))
    if method and profile == "LEAN":
        return {"blocker_allowed": False, "action": "RUN_LEAN_METHOD", "next": None}
    if method:
        return {"blocker_allowed": False, "action": "OFFER_LEAN", "next": None}
    return {"blocker_allowed": True, "action": "BLOCK", "next": None}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def validate_environment_files(repo_root: str | Path, admission: Mapping[str, Any]) -> dict[str, Any]:
    policy = validate_environment_policy(admission)
    root = Path(repo_root)
    nodes = policy["contract_nodes"]
    paths = {key: root / str(nodes[key]) for key in CONTRACT_NODE_KEYS}
    prompt_path = root / str(policy["boot_prompt"])
    cognitive = _cognitive_policy(admission)
    cognitive_path = root / str(cognitive["cognitive_policy"])
    kernel_policy = admission.get("method_access") or {}
    kernel_path = root / str(kernel_policy.get("kernel_path", "METHOD_KERNEL.json"))
    for path in [*paths.values(), prompt_path, cognitive_path, kernel_path]:
        if not path.is_file():
            raise FileNotFoundError(f"local environment file missing: {path}")
    texts = {key: path.read_text(encoding="utf-8") for key, path in paths.items()}
    prompt = prompt_path.read_text(encoding="utf-8")
    cognitive_text = cognitive_path.read_text(encoding="utf-8")
    prompt_chars = len(prompt)
    if prompt_chars > int(policy["boot_prompt_max_chars"]):
        raise ValueError(f"boot prompt exceeds declared character limit: {prompt_chars}")
    root_text = texts["root"]
    for key in CONTRACT_NODE_KEYS[1:]:
        name = Path(str(nodes[key])).name
        if name not in root_text:
            raise ValueError(f"root does not cross-reference {name}")
    for required in (prompt_path.name, cognitive_path.name, kernel_path.name):
        if required not in root_text and required != kernel_path.name:
            raise ValueError(f"root does not cross-reference {required}")
    root_name = Path(str(nodes["root"])).name
    for key in CONTRACT_NODE_KEYS[1:]:
        if root_name not in texts[key]:
            raise ValueError(f"{key} does not cross-reference root")
    for token in ("pre_admission_allowlist", "resolved_revision", "RUNTIME_LOCAL_HOST.md", "METHOD_KERNEL.json", "UNVERIFIED", "ATTESTED_PREFERRED", "LEAN"):
        if token not in prompt:
            raise ValueError(f"boot prompt missing anchor: {token}")
    if "COMPRESSION & CONSOLIDATION" in prompt:
        raise ValueError("boot prompt duplicates canonical scientific mode taxonomy")
    for token in ("METHOD_ACCESS", "ATTESTED_PREFERRED", "INFRASTRUCTURE_DEBT", "EPISTEMIC_DEBT", "LEAN -> ATTESTED"):
        if token not in cognitive_text:
            raise ValueError(f"cognitive companion missing invariant: {token}")
    if _sha256(cognitive_text) != str(cognitive.get("cognitive_policy_sha256")):
        raise ValueError("cognitive companion digest mismatch")
    if _sha256(prompt) != str(cognitive.get("boot_prompt_sha256")):
        raise ValueError("boot prompt digest mismatch")
    kernel_bytes = kernel_path.read_bytes()
    kernel_sha = hashlib.sha256(kernel_bytes).hexdigest()
    if kernel_sha != str(kernel_policy.get("kernel_sha256")):
        raise ValueError("Method Kernel digest mismatch")
    payload = {
        "schema": ENVIRONMENT_SCHEMA,
        "profile": ENVIRONMENT_PROFILE,
        "cognitive_profile": COGNITIVE_PROFILE,
        "authority": ENVIRONMENT_AUTHORITY,
        "prompt_chars": prompt_chars,
        "prompt_limit": int(policy["boot_prompt_max_chars"]),
        "normative_policy_nodes": len(CONTRACT_NODE_KEYS),
        "cognitive_companion_nodes": 1,
        "nodes": {key: {"path": str(nodes[key]), "sha256": _sha256(texts[key])} for key in CONTRACT_NODE_KEYS},
        "boot_prompt": {"path": str(policy["boot_prompt"]), "sha256": _sha256(prompt)},
        "cognitive_companion": {"path": str(cognitive["cognitive_policy"]), "sha256": _sha256(cognitive_text)},
        "method_kernel": {"path": str(kernel_policy.get("kernel_path")), "sha256": kernel_sha},
        "activation": {key: list(value) for key, value in ACTIVATION.items()},
        "runtime_authority_nodes_added": 0,
    }
    payload["graph_sha256"] = _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return payload
