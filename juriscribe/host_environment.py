from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ENVIRONMENT_SCHEMA = "juriscribe-local-session-environment/v1"
ENVIRONMENT_PROFILE = "JURISCRIBE_LOCAL_SESSION_ENVIRONMENT_V1"
ENVIRONMENT_AUTHORITY = "HOST_COMPOSITION_ONLY"
BOOT_PROMPT_MAX_CHARS = 8000

CONTRACT_NODE_KEYS = ("root", "execution", "state", "surface", "failure_recovery")
ACTIVATION = {
    "POST_ACCEPTANCE_BOOTSTRAP": ("root", "execution"),
    "ACTIVE_SESSION": ("root", "state", "surface"),
    "FAILURE_OR_RECOVERY": ("root", "state", "failure_recovery"),
    "REBIND_OR_TRANSPORT_FAILURE": ("root", "execution", "failure_recovery"),
}


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
    policy = validate_environment_policy(admission)
    trigger = str(trigger).strip().upper()
    if trigger not in ACTIVATION:
        raise ValueError(f"unknown local environment trigger: {trigger}")
    nodes = policy["contract_nodes"]
    keys = tuple(policy["activation"][trigger])
    return {
        "schema": ENVIRONMENT_SCHEMA,
        "profile": ENVIRONMENT_PROFILE,
        "trigger": trigger,
        "node_keys": list(keys),
        "paths": [str(nodes[key]) for key in keys],
        "same_revision_required": True,
        "authority": ENVIRONMENT_AUTHORITY,
        "scientific_authority": False,
        "runtime_authority_nodes_added": 0,
    }


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
    for key in CONTRACT_NODE_KEYS[1:]:
        name = Path(str(nodes[key])).name
        if name not in root_text:
            raise ValueError(f"root does not cross-reference {name}")
    if Path(str(policy["boot_prompt"])).name not in root_text:
        raise ValueError("root does not cross-reference boot prompt")

    root_name = Path(str(nodes["root"])).name
    for key in CONTRACT_NODE_KEYS[1:]:
        if root_name not in texts[key]:
            raise ValueError(f"{key} does not cross-reference root")

    for token in ("pre_admission_allowlist", "resolved_revision", "local_session_environment", "`UNVERIFIED`", "`UNAVAILABLE`"):
        if token not in prompt:
            raise ValueError(f"boot prompt missing anchor: {token}")
    if "MODE_REGISTRY" in prompt or "COMPRESSION & CONSOLIDATION" in prompt:
        raise ValueError("boot prompt duplicates canonical runtime taxonomy")

    payload = {
        "schema": ENVIRONMENT_SCHEMA,
        "profile": ENVIRONMENT_PROFILE,
        "authority": ENVIRONMENT_AUTHORITY,
        "prompt_chars": prompt_chars,
        "prompt_limit": int(policy["boot_prompt_max_chars"]),
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
