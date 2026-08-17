from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message: str):
    raise SystemExit("UNIVERSAL ARTIFACT AUTOPILOT CONTRACT FAIL: " + message)


def text(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        fail(f"missing {path}")
    return target.read_text(encoding="utf-8")


def main():
    manifest = json.loads(text("MANIFEST.json"))
    orchestrator = text("juriscribe/orchestrator.py")
    conversation = text("juriscribe/conversation_contract.py")
    autopilot = text("juriscribe/artifact_autopilot.py")
    runtime_autopilot = text("juriscribe/runtime_autopilot.py")
    delivery = text("juriscribe/delivery.py")
    chat_delivery = text("juriscribe/chat_delivery.py")
    governance = text("juriscribe/governance_delivery.py")
    atlas = text("juriscribe/artifact_atlas.py")
    dashboard = text("juriscribe/dashboard_v100.py")
    tests = text("tests/test_universal_artifact_autopilot_v10_0.py")
    simulation = text("scripts/simulate_universal_artifacts_v100.py")
    workflow = text(".github/workflows/runtime-regression.yml")
    spec = text("docs/UNIVERSAL_ARTIFACT_AUTOPILOT_V10.md")
    audit = text("docs/AUDIT_UNIVERSAL_ARTIFACT_AUTOPILOT_V10.md")

    for path in [
        "schemas/natural-language-pipeline-contract.schema.json",
        "schemas/standard-artifact-autopilot.schema.json",
        "schemas/chat-docx-delivery.schema.json",
    ]:
        if not (ROOT / path).exists():
            fail(f"missing schema {path}")

    for token in [
        "natural_language_pipeline_lock_required=True", "standard_artifact_autopilot_required=True",
        "final_chapter_inference_trace_required=True", "dashboard_summary_surface_only=True",
        "chat_tail_docx_attachments_required=True",
    ]:
        if token not in orchestrator:
            fail(f"orchestrator missing {token}")

    for token in [
        "JURISCRIBE_NATURAL_LANGUAGE_PIPELINE_LOCK_V1", "implicit_mode_change_forbidden",
        "disable_standard_artifacts", "replace_output_format", "NEW_SESSION_REQUIRED",
        "build_final_artifact_inference_trace", "final_chapter_inference_trace_gate",
    ]:
        if token not in conversation:
            fail(f"natural-language contract missing {token}")

    for token in [
        "JURISCRIBE_STANDARD_ARTIFACT_AUTOPILOT_V1", "materialize_standard_artifacts",
        "store_candidate_text", "render_dossier_text", "auto_materialized_by_runtime",
        "final severe review PASS required", "DOCX_WRITE", "DOCX_READBACK",
        "final_chapter", "build_final_artifact_inference_trace",
    ]:
        if token not in autopilot:
            fail(f"artifact autopilot missing {token}")

    for token in ["initialize_pipeline_lock", "refresh_pipeline_lock_artifact_set", "store_candidate_text"]:
        if token not in runtime_autopilot:
            fail(f"runtime wrapper missing {token}")

    for token in [
        "SESSION_CHAT_TAIL", "dashboard_links_to_docx", "downloadable_in_chat",
        "host_attachment_capability_required", "global_host_behavior_claim",
    ]:
        if token not in chat_delivery:
            fail(f"chat delivery missing {token}")

    for token in [
        "materialize_standard_artifacts", "standard_artifact_autopilot_gate", "pipeline_lock_gate",
        "final_chapter_inference_trace_gate", "chat_tail_docx_delivery",
    ]:
        if token not in governance:
            fail(f"completion governance missing {token}")

    for token in ["sealed_candidate_texts", "tracciabilita_inferenziale_del_prodotto", "standard_artifact_autopilot", "natural_language_pipeline"]:
        if token not in atlas:
            fail(f"artifact atlas missing {token}")

    for token in ["html-summary-docx-chat-tail-v1", "chat-tail-delivery-summary", "_strip_docx_links"]:
        if token not in dashboard:
            fail(f"dashboard summary-only boundary missing {token}")

    for token in [
        "runtime_autopilot_materializes_every_standard_docx_without_assistant_record_artifact_calls",
        "natural_language_cannot_implicitly_change_mode_artifact_or_pipeline",
        "final_chapter_trace_is_bound_to_request_reticulum_decisions_contract_and_candidate",
    ]:
        if token not in tests:
            fail(f"unit test missing {token}")

    for token in [
        "M = 100", "NO_NOVELTY_EXTENSION = 100", "SAFARI_CONTEXTS", "ASSISTANTS",
        "LANGUAGE_FAMILIES", "materialize_standard_artifacts", "dashboard_attachment_isolation_report",
        "no_novelty_after_M", "final_chapter", "record_natural_language_interpretation",
    ]:
        if token not in simulation:
            fail(f"100+100 saturation missing {token}")

    for token in [
        "python scripts/check_universal_artifact_autopilot_contract.py",
        "python scripts/simulate_universal_artifacts_v100.py --cases 100 --no-novelty 100",
        "universal-artifact-v100",
    ]:
        if token not in workflow:
            fail(f"CI missing universal artifact gate {token}")

    for token in ["runtime-owned", "linguaggio naturale", "SESSION_CHAT_TAIL", "final_chapter", "M+100", "Safari"]:
        if token.lower() not in spec.lower():
            fail(f"spec missing {token}")
    for token in ["DoD globale", "DoD locali", "deragliamento", "100 edge", "M+100", "trace", "fixed-point"]:
        if token.lower() not in audit.lower():
            fail(f"audit missing {token}")

    delivery_cfg = manifest.get("delivery") or {}
    if delivery_cfg.get("documents_format") != "DOCX":
        fail("historical manifest DOCX requirement regressed")
    if delivery_cfg.get("dashboard_format") != "HTML":
        fail("historical dashboard HTML requirement regressed")

    print("UNIVERSAL ARTIFACT AUTOPILOT CONTRACT PASS")


if __name__ == "__main__":
    main()
