from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import traceback
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.artifact_autopilot import materialize_standard_artifacts, standard_artifact_autopilot_gate, store_candidate_text
from juriscribe.chat_delivery import build_chat_delivery_manifest, dashboard_attachment_isolation_report
from juriscribe.conversation_contract import initialize_pipeline_lock, pipeline_lock_gate, record_natural_language_interpretation, resolve_natural_language_interpretation
from juriscribe.dashboard_v100 import render_session_dashboard
from juriscribe.delivery_compliance import build_delivery_compliance_inventory
from juriscribe.modes import CONTINUATION, GREENFIELD, REVIEW, required_artifact_roles

SCHEMA = "juriscribe-universal-artifact-saturation/v1"
M = 100
NO_NOVELTY_EXTENSION = 100

SAFARI_CONTEXTS = (
    "SAFARI_MACOS_STANDARD", "SAFARI_MACOS_PRIVATE", "SAFARI_IOS_STANDARD", "SAFARI_IOS_PRIVATE",
    "SAFARI_IPADOS_STANDARD", "SAFARI_IPADOS_SPLIT_VIEW", "SAFARI_UNICODE_LOCALE", "SAFARI_LOCAL_WORKBENCH",
    "SAFARI_JAVASCRIPT_DISABLED", "SAFARI_DOWNLOADS_RESTRICTED",
)
EXTENSION_BROWSERS = (
    "SAFARI_MACOS_STANDARD", "SAFARI_IOS_STANDARD", "SAFARI_IPADOS_STANDARD", "CHROMIUM_DESKTOP",
    "FIREFOX_DESKTOP", "EDGE_DESKTOP", "MOBILE_CHROMIUM", "GENERIC_WEBVIEW", "UNKNOWN_BROWSER",
    "JAVASCRIPT_DISABLED_BROWSER",
)
ASSISTANTS = ("OPENAI_ASSISTANT", "GENERIC_AI_ASSISTANT", "ENTERPRISE_AGENT", "LOCAL_MODEL_HOST", "UNKNOWN_ASSISTANT_HOST")
LANGUAGE_FAMILIES = (
    "BENIGN_CONTENT_CONSTRAINT", "SOFT_MODE_CHANGE", "SKIP_PIPELINE_REQUEST", "AMBIGUOUS_SHORTCUT", "STATUS_QUERY",
    "OUTPUT_FORMAT_DERAIL", "DISABLE_STANDARD_ARTIFACTS", "NEW_WORK_REQUEST", "MATERIAL_DECISION", "OUT_OF_SCOPE",
)


def _state(root: Path, mode: str, case_id: int, browser: str, assistant: str) -> SimpleNamespace:
    setup = {"accepted": {"review_output": "REPORT_ONLY"}} if mode == REVIEW else {}
    drafts = []
    generation_contract = {"status": "NOT_REQUIRED"}
    continuation = {"plan": {}, "coverage": {}, "status": "NOT_APPLICABLE"}
    review = {
        "cycles": [{
            "cycle": 1, "status": "PASS",
            "findings": [{"finding_id": f"F-{case_id:03d}", "gravita": "MINOR", "problema_rilevato": "Controllo editoriale sintetico", "intervento_proposto": "Verifica completata"}],
        }],
        "regenerations": [], "saturation": {"status": "PASS"}, "status": "SATURATED",
    }
    simulations = {}
    compression = {}
    if mode in {CONTINUATION, GREENFIELD}:
        drafts = [{"digest": f"CAND-{case_id:03d}", "stage": "COMPRESSED_FINAL", "status": "SEALED"}]
        generation_contract = {"status": "READY", "contract_digest": f"GC-{case_id:03d}"}
        simulations = {"status": "PASS", "cases": 10000, "failures": 0}
        compression = {"status": "PASS", "lossless": True}
    if mode == CONTINUATION:
        continuation = {
            "plan": {"status": "PASS", "develop_unit_ids": ["U1"]},
            "coverage": {"status": "PASS", "covered_unit_ids": ["U1"]},
            "status": "PASS",
        }
    if mode == REVIEW:
        drafts = [{"digest": f"REVIEW-SOURCE-{case_id:03d}", "stage": "REVIEW_SOURCE", "status": "SEALED"}]
        review["status"] = "DIAGNOSTIC_SATURATED"
    state = SimpleNamespace(
        mode=mode, setup=setup,
        runtime={
            "workspace_base": str(root.resolve()),
            "capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"},
            "browser_context": browser, "assistant_context": assistant,
        },
        request={"raw": f"Mandato naturale scenario {case_id}", "summary": f"Mandato naturale scenario {case_id}", "request_id": f"REQ-{case_id:03d}"},
        mode_selection={"digest": f"MODE-{case_id:03d}"},
        mode_contract={"status": "READY"},
        editorial_standard={"status": "READY", "standard_id": "JURISCRIBE_LEGAL_EDITORIAL_CORE_V2"},
        corpus=[],
        sources=[{
            "id": "S1", "title": f"Fonte normativa scenario {case_id}", "source_type": "primary_law",
            "direct_read": True, "verified_at": "2026-08-17", "jurisdiction": "IT", "date": "2026-01-01",
        }],
        bibliography={"available": False, "entries": [], "status": "NOT_AVAILABLE"},
        epistemic_units=[{
            "id": "U1", "kind": "RULE", "text": f"Regola materiale scenario {case_id}",
            "source_id": "S1", "material": True, "status": "VERIFIED",
        }],
        relations=[], reticulum={"status": "PASS"}, generation_contract=generation_contract, continuation=continuation,
        drafts=drafts, review=review, final_review={"status": "PASS"},
        provenance={"status": "PASS", "entries": [{"id": "C1", "kind": "CLAIM", "proposition": f"Claim materiale scenario {case_id}", "evidence_refs": ["S1"], "artifact_locators": ["§ 1"]}]},
        contradictions=[], mining={}, style_profile={}, source_intelligence={"coverage_status": "PASS"},
        claim_ledger=[{
            "id": "C1", "text": f"Claim materiale scenario {case_id}", "claim_type": "claim", "material": True,
            "status": "VERIFIED", "support_source_ids": ["S1"],
            "source_evidence": [{"source_id": "S1", "pinpoint": "art. 1", "proposition": f"Regola attestata scenario {case_id}"}],
        }],
        artifact_evidence=[{
            "evidence_id": "E1", "claim_id": "C1", "source_ids": ["S1"], "artifact_role": "final_chapter" if mode == CONTINUATION else ("final_legal_text" if mode == GREENFIELD else "review_report"),
            "artifact_locator": "§ 1", "status": "VERIFIED",
        }],
        quality={"status": "PASS"}, benchmark={}, simulations=simulations, compression=compression, limits=[], strategy={},
        dod=[], editorial_actions=[], reflection={}, metrics={}, artifacts=[], completion={"eligible": False}, node_integrity={}, interaction={},
    )
    initialize_pipeline_lock(state)
    if mode in {CONTINUATION, GREENFIELD}:
        store_candidate_text(state, drafts[-1]["digest"], f"Testo definitivo scenario {case_id}; browser {browser}; assistant {assistant}. Regola materiale scenario {case_id}.")
    return state


def _apply_language_case(state: SimpleNamespace, family: str) -> tuple[str, bool]:
    if family == "BENIGN_CONTENT_CONSTRAINT":
        record = record_natural_language_interpretation(state, "Approfondisci questo punto, senza cambiare il capitolo", {
            "classification": "CONTENT_CONSTRAINT", "pipeline_effect": "CONTENT_CONSTRAINT", "interpretation": "Vincolo interno al prodotto già selezionato", "affected_unit_ids": ["U1"],
        }); return "CONTENT_CONSTRAINT_APPLIED", record["status"] == "APPLIED"
    if family == "SOFT_MODE_CHANGE":
        record = record_natural_language_interpretation(state, "Forse invece fammi un parere nuovo e lascia stare questo lavoro", {
            "classification": "MODE_CHANGE_REQUEST", "pipeline_effect": "NONE", "interpretation": "Cambio di lavoro implicito", "replace_mode": "GREENFIELD",
        }); resolve_natural_language_interpretation(state, record["id"], "Nuova sessione necessaria; pipeline corrente invariata"); return "MODE_CHANGE_BLOCKED", record["status"] == "BLOCKED"
    if family == "SKIP_PIPELINE_REQUEST":
        record = record_natural_language_interpretation(state, "Vai direttamente al file, niente review né provenance", {
            "classification": "CONTENT_CONSTRAINT", "pipeline_effect": "CONTENT_CONSTRAINT", "interpretation": "Tentativo di saltare gate", "skip_pipeline_steps": ["review", "provenance"],
        }); resolve_natural_language_interpretation(state, record["id"], "Gate obbligatori preservati"); return "PIPELINE_SKIP_BLOCKED", record["status"] == "BLOCKED"
    if family == "AMBIGUOUS_SHORTCUT":
        record = record_natural_language_interpretation(state, "Fallo come prima ma diverso", {
            "classification": "AMBIGUOUS", "pipeline_effect": "NONE", "interpretation": "Istruzione materialmente ambigua",
        }); resolve_natural_language_interpretation(state, record["id"], "Nessuna mutazione materiale applicata"); return "AMBIGUITY_BLOCKED", record["status"] == "AMBIGUOUS"
    if family == "STATUS_QUERY":
        record = record_natural_language_interpretation(state, "A che punto siamo?", {"classification": "STATUS_QUERY", "pipeline_effect": "NONE", "interpretation": "Richiesta di stato"}); return "STATUS_QUERY_ISOLATED", record["pipeline_effect"] == "NONE"
    if family == "OUTPUT_FORMAT_DERAIL":
        record = record_natural_language_interpretation(state, "Non fare DOCX, incollami solo una pagina web", {
            "classification": "CONTENT_CONSTRAINT", "pipeline_effect": "CONTENT_CONSTRAINT", "interpretation": "Tentativo di sostituire formato finale", "replace_output_format": "HTML",
        }); resolve_natural_language_interpretation(state, record["id"], "Formato standard DOCX preservato"); return "OUTPUT_FORMAT_DERAIL_BLOCKED", record["status"] == "BLOCKED"
    if family == "DISABLE_STANDARD_ARTIFACTS":
        record = record_natural_language_interpretation(state, "Dammi solo il capitolo, niente registri o dossier", {
            "classification": "CONTENT_CONSTRAINT", "pipeline_effect": "CONTENT_CONSTRAINT", "interpretation": "Tentativo di sopprimere artefatti standard", "disable_standard_artifacts": True,
        }); resolve_natural_language_interpretation(state, record["id"], "Set standard preservato"); return "STANDARD_ARTIFACT_SUPPRESSION_BLOCKED", record["status"] == "BLOCKED"
    if family == "NEW_WORK_REQUEST":
        record = record_natural_language_interpretation(state, "Apri anche un secondo lavoro completamente diverso", {
            "classification": "NEW_WORK_REQUEST", "pipeline_effect": "NONE", "interpretation": "Nuovo lavoro distinto",
        }); resolve_natural_language_interpretation(state, record["id"], "Nuova sessione separata necessaria"); return "NEW_WORK_ISOLATED", record["status"] == "BLOCKED"
    if family == "MATERIAL_DECISION":
        record = record_natural_language_interpretation(state, "Mantieni questa tesi come asse principale", {
            "classification": "MATERIAL_DECISION", "pipeline_effect": "HUMAN_DECISION", "interpretation": "Decisione materiale interna", "affected_unit_ids": ["U1"], "affected_claim_ids": ["C1"],
        }); return "MATERIAL_DECISION_TRACED", record["status"] == "APPLIED"
    record = record_natural_language_interpretation(state, "A proposito, che tempo fa?", {"classification": "OUT_OF_SCOPE", "pipeline_effect": "NONE", "interpretation": "Richiesta estranea al lavoro"})
    return "OUT_OF_SCOPE_ISOLATED", record["pipeline_effect"] == "NONE"


def _scenario(root: Path, ordinal: int, *, extension: bool) -> dict:
    mode = (CONTINUATION, GREENFIELD, REVIEW)[(ordinal - 1) % 3]
    browser_pool = EXTENSION_BROWSERS if extension else SAFARI_CONTEXTS
    browser = browser_pool[(ordinal - 1) % len(browser_pool)]
    assistant = ASSISTANTS[(ordinal - 1) % len(ASSISTANTS)]
    family = LANGUAGE_FAMILIES[(ordinal - 1) % len(LANGUAGE_FAMILIES)]
    case_root = root / ("extension" if extension else "primary") / f"case-{ordinal:03d}"
    state = _state(case_root, mode, ordinal, browser, assistant)
    category, language_ok = _apply_language_case(state, family)
    if not language_ok: raise AssertionError(f"natural-language contract failed in scenario {ordinal}: {family}")
    lock_ok, lock_errors = pipeline_lock_gate(state)
    if not lock_ok: raise AssertionError(f"pipeline lock not converged in scenario {ordinal}: {lock_errors}")
    receipt = materialize_standard_artifacts(state)
    if receipt.get("status") != "PASS": raise AssertionError(f"artifact autopilot failed in scenario {ordinal}: {receipt}")
    auto_ok, auto_errors = standard_artifact_autopilot_gate(state)
    if not auto_ok: raise AssertionError(f"artifact autopilot gate failed in scenario {ordinal}: {auto_errors}")
    expected_docs = sorted(required_artifact_roles(mode, state.setup) - {"session_dashboard"})
    if receipt.get("materialized_roles") != expected_docs: raise AssertionError(f"standard artifact set drift in scenario {ordinal}: {receipt}")
    docs = [item for item in state.artifacts if item.get("role") != "session_dashboard"]
    if not all(str(item.get("path") or "").lower().endswith(".docx") and item.get("auto_materialized_by_runtime") for item in docs):
        raise AssertionError(f"non-DOCX or non-runtime-owned artifact in scenario {ordinal}")

    dashboard = case_root / "artifacts" / "session-dashboard.html"
    state.artifacts.append({
        "id": f"dashboard-{ordinal}", "role": "session_dashboard", "summary": "Riepilogo sintetico della sessione",
        "path": str(dashboard), "readback": "PASS", "format": "HTML", "media_type": "text/html", "delivery_class": "SURFACE",
    })
    render_session_dashboard(state.__dict__, dashboard)
    page = dashboard.read_text(encoding="utf-8")
    isolation = dashboard_attachment_isolation_report(page)
    if isolation.get("status") != "PASS": raise AssertionError(f"dashboard leaked document downloads in scenario {ordinal}: {isolation}")
    if 'id="chat-tail-delivery-summary"' not in page: raise AssertionError(f"dashboard lacks synthetic artifact summary in scenario {ordinal}")

    compliance = build_delivery_compliance_inventory(state)
    if compliance.get("status") != "PASS" or compliance.get("release_authorized") is not True:
        raise AssertionError(f"mechanical delivery compliance failed in scenario {ordinal}: {compliance}")
    chat = build_chat_delivery_manifest(state)
    if chat.get("status") != "PASS" or chat.get("placement") != "SESSION_CHAT_TAIL": raise AssertionError(f"chat-tail manifest failed in scenario {ordinal}: {chat}")
    if len(chat.get("attachments") or []) != len(expected_docs): raise AssertionError(f"chat-tail release count mismatch in scenario {ordinal}")
    if chat.get("withheld_attachments"): raise AssertionError(f"unexpected withheld attachment in scenario {ordinal}: {chat['withheld_attachments']}")
    if mode == CONTINUATION:
        chapter = next(item for item in state.artifacts if item.get("role") == "final_chapter")
        if (chapter.get("inference_trace") or {}).get("status") != "PASS": raise AssertionError(f"final_chapter trace failed in scenario {ordinal}")
    return {
        "ordinal": ordinal, "phase": "M_PLUS_100" if extension else "ONE_TO_M", "mode": mode,
        "browser_context": browser, "assistant_context": assistant, "language_family": family,
        "learned_category": category, "artifact_count": len(expected_docs), "status": "PASS",
    }


def run(cases: int = M, no_novelty: int = NO_NOVELTY_EXTENSION, out_root: str | None = None) -> dict:
    if cases != M: raise ValueError(f"release saturation requires M={M}")
    if no_novelty != NO_NOVELTY_EXTENSION: raise ValueError(f"release saturation requires M+{NO_NOVELTY_EXTENSION}")
    owned = None
    if out_root:
        root = Path(out_root).resolve(); shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True, exist_ok=True)
    else:
        owned = tempfile.TemporaryDirectory(); root = Path(owned.name)
    try:
        primary = [_scenario(root, i, extension=False) for i in range(1, cases + 1)]
        if any(not row["browser_context"].startswith("SAFARI") for row in primary): raise AssertionError("all 100 primary scenarios must be Safari-targeted")
        learned = {row["learned_category"] for row in primary}
        extension = [_scenario(root, cases + i, extension=True) for i in range(1, no_novelty + 1)]
        novel = sorted({row["learned_category"] for row in extension} - learned)
        if novel: raise AssertionError("M+100 produced novel pipeline/artifact categories: " + ", ".join(novel))
        rows = primary + extension
        return {
            "schema": SCHEMA, "status": "PASS", "M": cases, "one_to_M_cases": len(primary), "M_plus_100_cases": len(extension),
            "total_cases": len(rows), "safari_primary_cases": len(primary), "no_novelty_after_M": not novel,
            "novel_categories_after_M": novel, "learned_categories_at_M": sorted(learned),
            "mode_counts": dict(sorted(Counter(row["mode"] for row in rows).items())),
            "assistant_counts": dict(sorted(Counter(row["assistant_context"] for row in rows).items())),
            "browser_counts": dict(sorted(Counter(row["browser_context"] for row in rows).items())),
            "language_family_counts": dict(sorted(Counter(row["language_family"] for row in rows).items())),
            "invariants": {
                "standard_artifacts_runtime_owned": True,
                "all_standard_documents_docx": True,
                "dashboard_summary_only_no_docx_links": True,
                "chat_tail_attachment_manifest": True,
                "mechanical_material_epistemic_inventory": True,
                "atomic_release_all_or_nothing": True,
                "natural_language_cannot_implicitly_change_pipeline": True,
                "final_chapter_inference_trace_required": True,
                "global_external_host_behavior_claim": False,
            },
            "scenarios": rows,
        }
    finally:
        if owned is not None: owned.cleanup()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--cases", type=int, default=M); parser.add_argument("--no-novelty", type=int, default=NO_NOVELTY_EXTENSION); parser.add_argument("--out-root"); parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    try:
        result = run(args.cases, args.no_novelty, args.out_root)
    except Exception as exc:
        detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-6000:]
        safe = detail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Universal artifact saturation::{safe}")
        raise
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if args.json_out: Path(args.json_out).write_text(payload + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("schema", "status", "M", "one_to_M_cases", "M_plus_100_cases", "total_cases", "safari_primary_cases", "no_novelty_after_M", "learned_categories_at_M")}, ensure_ascii=False, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())