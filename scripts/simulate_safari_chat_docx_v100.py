from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import traceback
import zipfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.chat_delivery import (
    CHAT_PLACEMENT,
    DOCX_MIME,
    build_chat_delivery_manifest,
    content_disposition,
    dashboard_attachment_isolation_report,
)
from juriscribe.dashboard_v100 import render_session_dashboard
from juriscribe.delivery import ATTACH, delivery_gate, normalize_artifact_record
from juriscribe.modes import CONTINUATION, GREENFIELD, REVIEW, required_artifact_roles

SCHEMA = "juriscribe-safari-chat-docx-saturation/v1"
PRIMARY_M = 100
NO_NOVELTY_EXTENSION = 100

SAFARI_CONTEXTS = (
    "SAFARI_MACOS_STANDARD", "SAFARI_MACOS_PRIVATE", "SAFARI_IOS_STANDARD", "SAFARI_IOS_PRIVATE",
    "SAFARI_IPADOS_STANDARD", "SAFARI_IPADOS_SPLIT_VIEW", "SAFARI_DOWNLOADS_RESTRICTED",
    "SAFARI_UNICODE_LOCALE", "SAFARI_LOCAL_WORKBENCH", "SAFARI_JAVASCRIPT_DISABLED",
)
GENERIC_BROWSER_CONTEXTS = (
    "SAFARI_MACOS_STANDARD", "SAFARI_IOS_STANDARD", "SAFARI_IPADOS_STANDARD", "CHROMIUM_DESKTOP",
    "FIREFOX_DESKTOP", "EDGE_DESKTOP", "MOBILE_CHROMIUM", "GENERIC_WEBVIEW", "UNKNOWN_USER_AGENT",
    "JAVASCRIPT_DISABLED_BROWSER",
)
ASSISTANT_CONTEXTS = (
    "OPENAI_ASSISTANT", "GENERIC_AI_ASSISTANT", "LOCAL_MODEL_HOST", "ENTERPRISE_AGENT", "UNKNOWN_ASSISTANT_HOST",
)
FAMILIES = (
    ("VALID_BASELINE", True, "PASS_BASELINE"),
    ("VALID_UNICODE_FILENAME", True, "PASS_BASELINE"),
    ("VALID_NESTED_SPACE_PATH", True, "PASS_BASELINE"),
    ("SAFARI_JS_DISABLED", True, "PASS_BASELINE"),
    ("HTML_DOCX_LINK_LEAK", False, "HTML_DOCX_LINK"),
    ("HTML_DOWNLOAD_ANCHOR_LEAK", False, "HTML_DOWNLOAD_ANCHOR"),
    ("NON_DOCX_CHAT_ATTACHMENT", False, "DOCX_ONLY"),
    ("CHAT_MIME_MISMATCH", False, "DOCX_MIME"),
    ("DASHBOARD_FORCED_CHAT_ATTACHMENT", False, "SURFACE_SEPARATION"),
    ("FAKE_DOCX_BYTES", False, "OOXML_MATERIALIZATION"),
    ("READBACK_FAILURE", False, "READBACK"),
    ("MISSING_REQUIRED_CHAT_ATTACHMENT", False, "REQUIRED_ROLE"),
    ("NON_FINAL_FORCED_ATTACHMENT", False, "FINAL_ROLE_ONLY"),
    ("EXTERNAL_DOCX_PATH", False, "WORKSPACE_CONFINEMENT"),
    ("WRONG_DOC_EXTENSION", False, "DOCX_ONLY"),
)


def _write_docx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        f'<w:p><w:r><w:t xml:space="preserve">{xml_escape(text)}</w:t></w:r></w:p>'
        '</w:body></w:document>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        package.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
        package.writestr("word/document.xml", document)


def _state(root: Path, mode: str, assistant_context: str, browser_context: str, case_id: int) -> SimpleNamespace:
    setup = {}
    return SimpleNamespace(
        mode=mode, setup=setup,
        runtime={
            "capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE", "CHAT_ATTACHMENTS": "AVAILABLE"},
            "workspace_base": str(root.resolve()), "browser_context": browser_context, "assistant_context": assistant_context,
        },
        phase="VALIDATING", request={"raw": f"Safari DOCX edge {case_id}", "summary": f"Safari DOCX edge {case_id}"},
        mode_selection={}, mode_contract={"required_artifact_roles": sorted(required_artifact_roles(mode, setup)), "status": "READY"},
        editorial_standard={}, corpus=[], sources=[], bibliography={}, epistemic_units=[], relations=[], reticulum={},
        generation_contract={}, continuation={}, drafts=[], review={}, final_review={}, provenance={}, contradictions=[],
        mining={}, style_profile={}, source_intelligence={}, claim_ledger=[], artifact_evidence=[], quality={}, benchmark={},
        simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
        artifacts=[], completion={"eligible": False, "reason": "simulation"}, node_integrity={}, interaction={},
    )


def _doc_path(root: Path, role: str, case_id: int, family: str) -> Path:
    artifact_root = root / "artifacts"
    if family == "VALID_UNICODE_FILENAME":
        return artifact_root / f"{role}-garanzia-à-§-{case_id}.docx"
    if family == "VALID_NESTED_SPACE_PATH":
        return artifact_root / "cartella con spazi" / f"{role} fascicolo {case_id}.docx"
    return artifact_root / f"{role}-{case_id}.docx"


def _baseline(root: Path, mode: str, assistant: str, browser: str, case_id: int, family: str):
    state = _state(root, mode, assistant, browser, case_id)
    for role in sorted(required_artifact_roles(mode, state.setup)):
        if role == "session_dashboard":
            continue
        path = _doc_path(root, role, case_id, family)
        _write_docx(path, f"{role} — scenario {case_id} — contenuto DOCX materializzato")
        state.artifacts.append(normalize_artifact_record(state, {
            "id": f"{role}-{case_id}", "role": role, "summary": f"Sintesi {role} scenario {case_id}",
            "path": str(path), "readback": "PASS",
        }))
    dashboard_path = root / "artifacts" / "session-dashboard.html"
    state.artifacts.append(normalize_artifact_record(state, {
        "id": f"dashboard-{case_id}", "role": "session_dashboard", "summary": "Workbench sintetico della sessione",
        "path": str(dashboard_path), "readback": "PASS",
    }))
    render_session_dashboard(state.__dict__, dashboard_path)
    page = dashboard_path.read_text(encoding="utf-8")
    delivery_ok, delivery_errors = delivery_gate(state)
    chat = build_chat_delivery_manifest(state)
    isolation = dashboard_attachment_isolation_report(page)
    if not delivery_ok or chat.get("status") != "PASS" or isolation.get("status") != "PASS":
        raise AssertionError(f"baseline failed {case_id}: delivery={delivery_errors}; chat={chat.get('errors')}; html={isolation.get('errors')}")
    if chat.get("placement") != CHAT_PLACEMENT:
        raise AssertionError("chat-tail placement drift")
    if not all(item.get("downloadable_in_chat") and str(item.get("filename") or "").lower().endswith(".docx") for item in chat.get("attachments") or []):
        raise AssertionError("baseline chat attachments are not downloadable DOCX")
    if 'id="chat-tail-delivery-summary"' not in page:
        raise AssertionError("dashboard lacks synthetic document summary")
    return state, dashboard_path, page


def _first_attach(state: SimpleNamespace) -> dict:
    return next(item for item in state.artifacts if item.get("delivery_class") == ATTACH)


def _evaluate(state: SimpleNamespace, page: str, family: str, root: Path) -> tuple[bool, list[str]]:
    if family in {"VALID_BASELINE", "VALID_UNICODE_FILENAME", "VALID_NESTED_SPACE_PATH"}:
        ok, errors = delivery_gate(state)
        chat = build_chat_delivery_manifest(state); iso = dashboard_attachment_isolation_report(page)
        if ok and chat.get("status") == "PASS" and iso.get("status") == "PASS":
            header = content_disposition(_first_attach(state).get("path") or "artifact.docx")
            if not header.startswith("attachment;") or ".docx" not in header:
                return False, ["content disposition is not DOCX attachment"]
            return True, []
        return False, list(errors) + list(chat.get("errors") or []) + list(iso.get("errors") or [])
    if family == "SAFARI_JS_DISABLED":
        stripped = re.sub(r"<script\b[^>]*>.*?</script>", "", page, flags=re.IGNORECASE | re.DOTALL)
        chat = build_chat_delivery_manifest(state); iso = dashboard_attachment_isolation_report(stripped)
        return bool(chat.get("status") == "PASS" and iso.get("status") == "PASS"), list(chat.get("errors") or []) + list(iso.get("errors") or [])
    if family == "HTML_DOCX_LINK_LEAK":
        damaged = page.replace("</body>", '<a href="./leak.docx">leak</a></body>', 1)
        iso = dashboard_attachment_isolation_report(damaged); return iso.get("status") == "PASS", list(iso.get("errors") or [])
    if family == "HTML_DOWNLOAD_ANCHOR_LEAK":
        damaged = page.replace("</body>", '<a href="./leak.txt" download>leak</a></body>', 1)
        iso = dashboard_attachment_isolation_report(damaged); return iso.get("status") == "PASS", list(iso.get("errors") or [])
    if family == "NON_DOCX_CHAT_ATTACHMENT":
        item = _first_attach(state); item["path"] = str(Path(item["path"]).with_suffix(".pdf"))
        chat = build_chat_delivery_manifest(state); return chat.get("status") == "PASS", list(chat.get("errors") or [])
    if family == "CHAT_MIME_MISMATCH":
        _first_attach(state)["media_type"] = "application/pdf"
        chat = build_chat_delivery_manifest(state); return chat.get("status") == "PASS", list(chat.get("errors") or [])
    if family == "DASHBOARD_FORCED_CHAT_ATTACHMENT":
        next(item for item in state.artifacts if item.get("role") == "session_dashboard")["delivery_class"] = ATTACH
        chat = build_chat_delivery_manifest(state); return chat.get("status") == "PASS", list(chat.get("errors") or [])
    if family == "FAKE_DOCX_BYTES":
        Path(_first_attach(state)["path"]).write_text("not OOXML", encoding="utf-8")
        return delivery_gate(state)
    if family == "READBACK_FAILURE":
        _first_attach(state)["readback"] = "FAIL"
        chat = build_chat_delivery_manifest(state); return chat.get("status") == "PASS", list(chat.get("errors") or [])
    if family == "MISSING_REQUIRED_CHAT_ATTACHMENT":
        victim = _first_attach(state); state.artifacts = [item for item in state.artifacts if item is not victim]
        chat = build_chat_delivery_manifest(state); return chat.get("status") == "PASS", list(chat.get("errors") or [])
    if family == "NON_FINAL_FORCED_ATTACHMENT":
        path = root / "artifacts" / "debug-receipt.docx"; _write_docx(path, "internal receipt")
        state.artifacts.append({"id": "debug", "role": "simulation_receipt", "path": str(path), "readback": "PASS", "format": "DOCX", "media_type": DOCX_MIME, "delivery_class": ATTACH})
        chat = build_chat_delivery_manifest(state); return chat.get("status") == "PASS", list(chat.get("errors") or [])
    if family == "EXTERNAL_DOCX_PATH":
        outside = root.parent / f"outside-{root.name}.docx"; _write_docx(outside, "outside")
        _first_attach(state)["path"] = str(outside)
        return delivery_gate(state)
    if family == "WRONG_DOC_EXTENSION":
        item = _first_attach(state); item["path"] = str(Path(item["path"]).with_suffix(".doc"))
        chat = build_chat_delivery_manifest(state); return chat.get("status") == "PASS", list(chat.get("errors") or [])
    raise AssertionError(f"unknown family {family}")


def _categories(errors: list[str], passed: bool) -> set[str]:
    if passed:
        return {"PASS_BASELINE"}
    out: set[str] = set()
    for error in errors:
        text = str(error).lower()
        if "summarize docx" in text: out.add("HTML_DOCX_LINK")
        if "download anchors" in text: out.add("HTML_DOWNLOAD_ANCHOR")
        if "must be docx" in text or "non-docx" in text or "wrong format" in text: out.add("DOCX_ONLY")
        if "media type" in text: out.add("DOCX_MIME")
        if "dashboard" in text and "attachment" in text: out.add("SURFACE_SEPARATION")
        if "valid docx" in text or "ooxml" in text or "wordprocessingml" in text: out.add("OOXML_MATERIALIZATION")
        if "readback" in text: out.add("READBACK")
        if "required chat-tail docx artifact missing" in text: out.add("REQUIRED_ROLE")
        if "non-final role" in text: out.add("FINAL_ROLE_ONLY")
        if "outside" in text or "escapes" in text: out.add("WORKSPACE_CONFINEMENT")
    if not out:
        out.add("UNCLASSIFIED:" + (str(errors[0])[:90] if errors else "NO_ERROR"))
    return out


def _scenario(root: Path, ordinal: int, *, extension: bool) -> dict:
    family, expected_pass, expected_category = FAMILIES[(ordinal - 1) % len(FAMILIES)]
    mode = (CONTINUATION, GREENFIELD, REVIEW)[(ordinal - 1) % 3]
    browser_pool = GENERIC_BROWSER_CONTEXTS if extension else SAFARI_CONTEXTS
    browser = browser_pool[(ordinal - 1) % len(browser_pool)]
    assistant = ASSISTANT_CONTEXTS[(ordinal - 1) % len(ASSISTANT_CONTEXTS)]
    case_root = root / ("extension" if extension else "primary") / f"case-{ordinal:03d}"
    state, dashboard_path, page = _baseline(case_root, mode, assistant, browser, ordinal, family)
    passed, errors = _evaluate(state, page, family, case_root)
    categories = _categories(errors, passed)
    if expected_pass != passed:
        raise AssertionError(f"scenario {ordinal} {family} expected pass={expected_pass}, got {passed}: {errors}")
    if expected_category not in categories:
        raise AssertionError(f"scenario {ordinal} {family} missing {expected_category}: {categories}; {errors}")
    return {
        "ordinal": ordinal, "phase": "M_PLUS_100" if extension else "ONE_TO_M", "family": family,
        "expected_pass": expected_pass, "observed_pass": passed, "categories": sorted(categories), "mode": mode,
        "browser_context": browser, "assistant_context": assistant, "dashboard": str(dashboard_path), "error_count": len(errors),
    }


def run(cases: int = PRIMARY_M, no_novelty: int = NO_NOVELTY_EXTENSION, out_root: str | None = None) -> dict:
    if cases != PRIMARY_M:
        raise ValueError(f"release saturation requires M={PRIMARY_M}")
    if no_novelty != NO_NOVELTY_EXTENSION:
        raise ValueError(f"release no-novelty extension requires M+{NO_NOVELTY_EXTENSION}")
    owned_tmp = None
    if out_root:
        root = Path(out_root).resolve(); shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True, exist_ok=True)
    else:
        owned_tmp = tempfile.TemporaryDirectory(); root = Path(owned_tmp.name)
    try:
        primary = [_scenario(root, index, extension=False) for index in range(1, cases + 1)]
        if any(not item["browser_context"].startswith("SAFARI") for item in primary):
            raise AssertionError("all 100 primary edge cases must be Safari-targeted")
        learned = set().union(*(set(item["categories"]) for item in primary))
        extension = [_scenario(root, cases + index, extension=True) for index in range(1, no_novelty + 1)]
        extension_categories = set().union(*(set(item["categories"]) for item in extension))
        novel = sorted(extension_categories - learned)
        if novel:
            raise AssertionError("M+100 produced novel delivery classes: " + ", ".join(novel))
        all_scenarios = primary + extension
        return {
            "schema": SCHEMA, "status": "PASS", "M": cases, "one_to_M_cases": len(primary),
            "M_plus_100_cases": len(extension), "total_cases": len(all_scenarios), "safari_primary_cases": len(primary),
            "no_novelty_after_M": len(novel) == 0, "novel_categories_after_M": novel,
            "learned_categories_at_M": sorted(learned),
            "family_counts": dict(sorted(Counter(item["family"] for item in all_scenarios).items())),
            "mode_counts": dict(sorted(Counter(item["mode"] for item in all_scenarios).items())),
            "browser_context_counts": dict(sorted(Counter(item["browser_context"] for item in all_scenarios).items())),
            "assistant_context_counts": dict(sorted(Counter(item["assistant_context"] for item in all_scenarios).items())),
            "downloadable_artifact_contract": "DOCX_ONLY_SESSION_CHAT_TAIL",
            "dashboard_contract": "HTML_SYNTHETIC_SUMMARY_NO_DOCX_LINKS",
            "host_attachment_capability_required": True,
            "global_browser_or_assistant_behavior_claim": False,
            "scenarios": all_scenarios,
        }
    finally:
        if owned_tmp is not None:
            owned_tmp.cleanup()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=PRIMARY_M)
    parser.add_argument("--no-novelty", type=int, default=NO_NOVELTY_EXTENSION)
    parser.add_argument("--out-root")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    try:
        result = run(args.cases, args.no_novelty, args.out_root)
    except Exception as exc:
        detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-6000:]
        safe = detail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Safari chat-tail DOCX saturation::{safe}")
        raise
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(payload + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("schema", "status", "M", "one_to_M_cases", "M_plus_100_cases", "total_cases", "safari_primary_cases", "no_novelty_after_M", "learned_categories_at_M")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())