from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit("RUNTIME V1 CHECK FAIL: " + message)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _quoted_constant(source: str, name: str) -> str:
    match = re.search(rf'^{re.escape(name)}\s*=\s*["\']([^"\']+)["\']', source, re.M)
    if not match:
        fail(f"constant {name} missing")
    return match.group(1)


def main() -> int:
    manifest = json.loads(_read("MANIFEST.json"))
    admission = json.loads(_read("ADMISSION.json"))
    runtime_contract = json.loads(_read("RUNTIME_V1_CONTRACT.json"))
    pyproject = _read("pyproject.toml")
    init = _read("juriscribe/__init__.py")
    contract = _read("ISENECA_ACCESS_CONTRACT.md")
    packaged = _read("juriscribe/resources/ISENECA_ACCESS_CONTRACT.md")
    continuity = _read("juriscribe/continuity.py")
    recovery = _read("juriscribe/recovery.py")
    shell = _read("juriscribe/chat_shell.py")
    chat_delivery = _read("juriscribe/chat_delivery.py")
    router = _read("juriscribe/runtime_router.py")
    orchestrator = _read("juriscribe/orchestrator.py")

    version = _quoted_constant(init, "__version__")
    if version != "1.0.0" or manifest.get("runtime_version") != version:
        fail("runtime/manifest version mismatch")
    if not re.search(r'^version = "1\.0\.0"$', pyproject, re.M):
        fail("pyproject version is not 1.0.0")
    if manifest.get("contract_version") != "2.0.0" or admission.get("contract_version") != "2.0.0":
        fail("v1 contract version mismatch")
    if "contract_version: 2.0.0" not in contract or packaged != contract:
        fail("canonical/bundled v2 contract mismatch")
    digest = hashlib.sha256(contract.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    if admission.get("contract_sha256") != digest:
        fail("ADMISSION contract digest stale")

    expected_contract = {
        "schema": "juriscribe-runtime-v1-contract/v1",
        "profile": "JURISCRIBE_RUNTIME_V1",
        "runtime_version": version,
        "contract_version": "2.0.0",
        "authority_partition_nodes": 6,
        "no_new_authority_node": True,
        "exact_runtime_input_archive": True,
        "scientific_checkpoint_host_independent": True,
        "recovery_bundle_schema": "juriscribe-recovery-bundle/v1",
        "fresh_host_probe_required": True,
        "recovery_export_on_demand": True,
        "recovery_capable_completion": True,
        "cross_mode_materialization_pending": True,
        "materialization_continue_phrase": "Continue until the end of artefact materialization",
        "stress_cases_min": 10000,
    }
    for key, value in expected_contract.items():
        if runtime_contract.get(key) != value:
            fail("runtime v1 contract invariant mismatch: " + key)
    if runtime_contract.get("iteration_contract") != ["WHERE", "DONE", "NEXT", "HOW", "DO"]:
        fail("iteration contract mismatch")
    if runtime_contract.get("authority_nodes") != [
        "MODE_REGISTRY",
        "EXPLICIT_ROUTER",
        "COMMON_STALENESS",
        "SPECIALIST_PROOF",
        "MATERIALIZATION",
        "PROJECTION",
    ]:
        fail("authority node order/identity mismatch")

    docx = runtime_contract.get("chat_session_docx_delivery") or {}
    required_docx = {
        "profile": "JURISCRIBE_CHAT_DOCX_DELIVERY_V1",
        "scope": "EVERY_RETAINED_MATERIALIZED_DOCX_INTERMEDIATE_AND_FINAL",
        "downloadable_in_session_chat": True,
        "final_delivery_class_independent": True,
        "dashboard_is_not_a_substitute": True,
        "projection_must_not_hide_intermediate_docx": True,
        "unregistered_workspace_docx_must_be_surfaced_and_flagged": True,
        "completion_fails_closed_on_chat_projection_error": True,
        "scientific_authority": False,
    }
    for key, value in required_docx.items():
        if docx.get(key) != value:
            fail("chat DOCX contract invariant mismatch: " + key)

    required_admission_docx = {
        "session_chat_every_materialized_docx_required": True,
        "session_chat_intermediate_docx_download_required": True,
        "session_chat_final_delivery_class_independent": True,
        "session_chat_dashboard_not_download_substitute": True,
        "session_chat_unregistered_docx_surfaced_and_fail_closed": True,
        "session_chat_docx_projection_gate_required_for_complete": True,
    }
    for key, value in required_admission_docx.items():
        if admission.get(key) != value:
            fail("ADMISSION chat DOCX invariant mismatch: " + key)
    for token in (
        "## 25. Materializzazione DOCX e disponibilità nella sessione-chat",
        "indipendentemente dal fatto che sia intermedio o finale",
        "marcato `UNREGISTERED`",
        "impedisce `COMPLETE`",
    ):
        if token not in contract:
            fail("canonical access contract omits session-chat DOCX rule: " + token)

    surface = set((manifest.get("active_surface") or {}).get("runtime") or [])
    for path in (
        "docs/RUNTIME_V1.md",
        "juriscribe/continuity.py",
        "juriscribe/recovery.py",
        "juriscribe/chat_shell.py",
        "juriscribe/runtime_router.py",
        "juriscribe/runtime_v13.py",
    ):
        if path not in surface:
            fail("current v1 surface omits " + path)

    for token in (
        'ITERATION_SCHEMA = "juriscribe-iteration-projection/v1"',
        'RECOVERY_ACTION = "RECOVERY BUNDLE"',
        'ITERATION_AUTHORITY = "PROJECTION_ONLY"',
        'MATERIALIZATION_PENDING = "MATERIALIZATION_PENDING"',
        'MATERIALIZATION_CONTINUE_PHRASE = "Continue until the end of artefact materialization"',
    ):
        if token not in continuity:
            fail("continuity contract token missing: " + token)
    for token in (
        'SCHEMA="juriscribe-recovery-bundle/v1"',
        'AUTHORITY="MATERIALIZATION_ONLY"',
        "fresh_host_probe_required_on_resume",
    ):
        if token not in recovery:
            fail("recovery contract token missing: " + token)
    if 'SCHEMA = "juriscribe-chat-shell/v2"' not in shell:
        fail("chat shell v2 schema missing")
    for token in ("WHERE", "DONE>", "NEXT>", "HOW>", "[R] RECUPERO", "[…] ALTRO"):
        if token not in shell:
            fail("chat shell control token missing: " + token)

    for token in (
        'SESSION_CHAT_DOWNLOAD = "SESSION_CHAT_DOWNLOAD"',
        "build_session_chat_docx_manifest",
        "session_chat_docx_gate",
        '"downloadable_in_chat": True',
        '"final_delivery_class_independent": True',
    ):
        if token not in chat_delivery:
            fail("chat DOCX session-delivery contract token missing: " + token)

    if '"create_recovery_bundle": ("recovery", "create_recovery_bundle")' not in router:
        fail("recovery export route missing")
    if 'create_recovery_bundle = resolve_operation("create_recovery_bundle")' not in orchestrator:
        fail("orchestrator recovery route missing")
    if "from .runtime_cc_v2 import" in orchestrator:
        fail("v1 reintroduced import-order authority")

    convergence = manifest.get("runtime_convergence") or {}
    if convergence.get("authority_partition_nodes") != 6 or convergence.get("import_order_authority_forbidden") is not True:
        fail("v13 convergence authority partition regressed")

    print(json.dumps({
        "status": "PASS",
        "runtime_version": version,
        "contract_version": "2.0.0",
        "runtime_contract_schema": runtime_contract.get("schema"),
        "shell_schema": "juriscribe-chat-shell/v2",
        "recovery_schema": "juriscribe-recovery-bundle/v1",
        "chat_docx_profile": docx.get("profile"),
        "authority_nodes": 6,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
