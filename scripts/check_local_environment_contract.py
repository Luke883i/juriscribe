from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from juriscribe.host_environment import (
    ACTIVATION, BOOT_PROMPT_MAX_CHARS, CONTRACT_NODE_KEYS,
    ENVIRONMENT_AUTHORITY, ENVIRONMENT_PROFILE, ENVIRONMENT_SCHEMA,
    COGNITIVE_PROFILE, COGNITIVE_AUTHORITY,
    validate_environment_files, validate_environment_policy,
)
from juriscribe.graded_execution import validate_method_kernel
from juriscribe.modes import MODES, mode_runtime_spec


def fail(message: str) -> None: raise SystemExit("LOCAL SESSION ENVIRONMENT CHECK FAIL: " + message)
def read(path: str) -> str: return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    admission=json.loads(read("ADMISSION.json")); manifest=json.loads(read("MANIFEST.json")); runtime=json.loads(read("RUNTIME_V1_CONTRACT.json"))
    contract=read("ISENECA_ACCESS_CONTRACT.md"); packaged=read("juriscribe/resources/ISENECA_ACCESS_CONTRACT.md"); adapter=read("docs/LOCAL_GPT_HOST_ADAPTER.md")
    if admission.get("contract_version")!="2.2.0" or manifest.get("contract_version")!="2.2.0" or runtime.get("contract_version")!="2.2.0": fail("contract 2.2.0 coherence drift")
    if "contract_version: 2.2.0" not in contract or packaged!=contract: fail("canonical and packaged access contract are not byte-equivalent 2.2.0")
    digest=hashlib.sha256(contract.replace("\r\n","\n").encode()).hexdigest()
    if admission.get("contract_sha256")!=digest: fail("ADMISSION contract digest stale")
    try:
        policy=validate_environment_policy(admission); graph=validate_environment_files(ROOT,admission)
    except Exception as exc: fail(str(exc))
    if tuple(policy["contract_nodes"].keys()) != CONTRACT_NODE_KEYS: fail("five-node normative reticulum drift")
    if {k:tuple(v) for k,v in policy["activation"].items()} != ACTIVATION: fail("activation graph drift")
    if graph.get("normative_policy_nodes")!=5 or graph.get("cognitive_companion_nodes")!=1: fail("normative/cognitive partition drift")
    if policy.get("boot_prompt_max_chars")!=BOOT_PROMPT_MAX_CHARS or graph.get("prompt_chars",99999)>BOOT_PROMPT_MAX_CHARS: fail("boot prompt bound drift")
    lse=manifest.get("local_session_environment") or {}
    expected_manifest={"schema":ENVIRONMENT_SCHEMA,"profile":ENVIRONMENT_PROFILE,"authority":ENVIRONMENT_AUTHORITY,"scientific_authority":False,"runtime_authority_nodes_added":0,"root":policy["root"],"boot_prompt":policy["boot_prompt"],"resolver":"juriscribe.host_environment.activation_plan","validator":"juriscribe.host_environment.validate_environment_files"}
    for key,value in expected_manifest.items():
        if lse.get(key)!=value: fail("manifest local environment drift: "+key)
    host_surface=set((manifest.get("active_surface") or {}).get("host_environment") or [])
    required={"juriscribe/host_environment.py",*policy["contract_nodes"].values(),policy["boot_prompt"]}
    if not required.issubset(host_surface): fail("active surface omits lifecycle host files")
    env_runtime=runtime.get("local_session_environment") or {}
    for key,value in {"profile":ENVIRONMENT_PROFILE,"schema":ENVIRONMENT_SCHEMA,"authority":ENVIRONMENT_AUTHORITY,"scientific_authority":False,"runtime_authority_nodes_added":0,"durable_scientific_state_host_independent":True,"chat_environment_revision_bound":True,"contract_graph_activation_required":True,"normative_policy_nodes":5,"cognitive_companion_nodes":1,"boot_prompt_max_chars":8000}.items():
        if env_runtime.get(key)!=value: fail("runtime local environment invariant mismatch: "+key)
    cognitive=admission.get("local_cognitive_system") or {}
    for key,value in {"profile":COGNITIVE_PROFILE,"authority":COGNITIVE_AUTHORITY,"scientific_authority":False,"runtime_authority_nodes_added":0,"same_revision_required":True,"normative_host_nodes_replaced":False,"load_before_acceptance":False}.items():
        if cognitive.get(key)!=value: fail("local cognitive binding drift: "+key)
    method=admission.get("method_access") or {}; kernel=json.loads(read(str(method.get("kernel_path"))))
    kresult=validate_method_kernel(kernel,canonical_modes=MODES,canonical_runtime_specs={m:mode_runtime_spec(m) for m in MODES})
    if kresult["status"]!="PASS": fail("Method Kernel invalid: "+"; ".join(kresult["errors"]))
    ksha=hashlib.sha256((ROOT/str(method.get("kernel_path"))).read_bytes()).hexdigest()
    if method.get("kernel_sha256")!=ksha: fail("Method Kernel binding stale")
    if (ROOT/str(method.get("kernel_resource_path"))).read_bytes() != (ROOT/str(method.get("kernel_path"))).read_bytes(): fail("root/package Method Kernel parity failed")
    for token in ("## 26. Ambiente locale di sessione e contratto host","## 27. Accesso al metodo ed esecuzione graduata","METHOD_ACCESS","ATTESTED_PREFERRED","METHOD_MODE_INTENT","INFRASTRUCTURE_DEBT"):
        if token not in contract: fail("access contract omits post-33 binding: "+token)
    for token in ("LOCAL_HOST_PROMPT.md","LOCAL_SESSION_ENVIRONMENT.md","RUNTIME_LOCAL_HOST.md","METHOD_KERNEL.json"):
        if token not in adapter: fail("host adapter omits current surface: "+token)
    expected_nodes=["MODE_REGISTRY","EXPLICIT_ROUTER","COMMON_STALENESS","SPECIALIST_PROOF","MATERIALIZATION","PROJECTION"]
    if runtime.get("authority_nodes")!=expected_nodes or runtime.get("authority_partition_nodes")!=6: fail("runtime authority topology changed")
    graded=runtime.get("graded_execution") or {}
    for key,value in {"mandatory_profile_choice":False,"default_preference":"ATTESTED_PREFERRED","explicit_lean_honored_when_runtime_reachable":True,"runtime_reachability_does_not_imply_receipt_or_complete":True,"lean_is_runtime_transport_class":False,"method_kernel_mode_parity_required":True}.items():
        if graded.get(key)!=value: fail("graded execution hardening drift: "+key)
    print(json.dumps({"status":"PASS","contract_version":"2.2.0","contract_semantic_revision":admission.get("contract_semantic_revision"),"profile":ENVIRONMENT_PROFILE,"cognitive_profile":COGNITIVE_PROFILE,"normative_nodes":5,"cognitive_companion_nodes":1,"prompt_chars":graph["prompt_chars"],"runtime_authority_nodes":6,"graph_sha256":graph["graph_sha256"],"method_kernel_sha256":ksha},ensure_ascii=False,indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
