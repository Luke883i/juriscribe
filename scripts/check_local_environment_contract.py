from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.host_environment import (
    ACTIVATION,
    BOOT_PROMPT_MAX_CHARS,
    CONTRACT_NODE_KEYS,
    ENVIRONMENT_AUTHORITY,
    ENVIRONMENT_PROFILE,
    ENVIRONMENT_SCHEMA,
    validate_environment_files,
    validate_environment_policy,
)


def fail(message: str) -> None:
    raise SystemExit("LOCAL SESSION ENVIRONMENT CHECK FAIL: " + message)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    admission = json.loads(read("ADMISSION.json"))
    manifest = json.loads(read("MANIFEST.json"))
    runtime = json.loads(read("RUNTIME_V1_CONTRACT.json"))
    contract = read("ISENECA_ACCESS_CONTRACT.md")
    packaged = read("juriscribe/resources/ISENECA_ACCESS_CONTRACT.md")
    adapter = read("docs/LOCAL_GPT_HOST_ADAPTER.md")

    if admission.get("contract_version") != "2.2.0" or manifest.get("contract_version") != "2.2.0" or runtime.get("contract_version") != "2.2.0":
        fail("contract 2.2.0 is not coherent across admission/manifest/runtime")
    if "contract_version: 2.2.0" not in contract or packaged != contract:
        fail("canonical and packaged access contract are not byte-equivalent v2.2.0")
    digest = hashlib.sha256(contract.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    if admission.get("contract_sha256") != digest:
        fail("ADMISSION contract digest stale")

    try:
        policy = validate_environment_policy(admission)
        graph = validate_environment_files(ROOT, admission)
    except Exception as exc:
        fail(str(exc))

    if set(policy["contract_nodes"].keys()) != set(CONTRACT_NODE_KEYS):
        fail("normative node reticulum drift")
    if {key: tuple(value) for key, value in policy["activation"].items()} != ACTIVATION:
        fail("activation graph drift")
    if policy.get("boot_prompt_max_chars") != BOOT_PROMPT_MAX_CHARS or graph.get("prompt_chars", 99999) > BOOT_PROMPT_MAX_CHARS:
        fail("boot prompt bound drift")

    lse = manifest.get("local_session_environment") or {}
    expected_manifest = {
        "schema": ENVIRONMENT_SCHEMA,
        "profile": ENVIRONMENT_PROFILE,
        "authority": ENVIRONMENT_AUTHORITY,
        "scientific_authority": False,
        "runtime_authority_nodes_added": 0,
        "root": policy["root"],
        "boot_prompt": policy["boot_prompt"],
        "resolver": "juriscribe.host_environment.activation_plan",
        "validator": "juriscribe.host_environment.validate_environment_files",
    }
    for key, value in expected_manifest.items():
        if lse.get(key) != value:
            fail("manifest local environment drift: " + key)

    public_composition = set((manifest.get("active_surface") or {}).get("public_composition") or [])
    if public_composition != {"juriscribe/pipeline.py", "juriscribe/runtime_cli.py"}:
        fail("physical public composition is not explicit")
    host_surface = set((manifest.get("active_surface") or {}).get("host_environment") or [])
    required_host = {"juriscribe/host_environment.py", *policy["contract_nodes"].values(), policy["boot_prompt"]}
    if not required_host.issubset(host_surface):
        fail("active surface omits local environment files")

    env_runtime = runtime.get("local_session_environment") or {}
    for key, value in {
        "profile": ENVIRONMENT_PROFILE,
        "schema": ENVIRONMENT_SCHEMA,
        "authority": ENVIRONMENT_AUTHORITY,
        "scientific_authority": False,
        "runtime_authority_nodes_added": 0,
        "durable_scientific_state_host_independent": True,
        "chat_environment_revision_bound": True,
        "contract_graph_activation_required": True,
        "boot_prompt_max_chars": 8000,
    }.items():
        if env_runtime.get(key) != value:
            fail("runtime local environment invariant mismatch: " + key)

    for token in (
        "## 26. Ambiente locale di sessione e contratto host",
        "ambiente locale revision-bound dentro la sessione-chat corrente",
        "non costituisce una settima authority",
        "Duty of Local Sufficiency",
    ):
        if token not in contract:
            fail("access contract omits local environment rule: " + token)
    if "LOCAL_HOST_PROMPT.md" not in adapter or "LOCAL_SESSION_ENVIRONMENT.md" not in adapter:
        fail("legacy host adapter is not a compatibility pointer")

    expected_nodes = ["MODE_REGISTRY", "EXPLICIT_ROUTER", "COMMON_STALENESS", "SPECIALIST_PROOF", "MATERIALIZATION", "PROJECTION"]
    if runtime.get("authority_nodes") != expected_nodes or runtime.get("authority_partition_nodes") != 6:
        fail("runtime authority topology changed")

    print(json.dumps({
        "status": "PASS",
        "contract_version": "2.2.0",
        "profile": ENVIRONMENT_PROFILE,
        "authority": ENVIRONMENT_AUTHORITY,
        "normative_nodes": len(CONTRACT_NODE_KEYS),
        "prompt_chars": graph["prompt_chars"],
        "activation_triggers": len(ACTIVATION),
        "runtime_authority_nodes": 6,
        "graph_sha256": graph["graph_sha256"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
