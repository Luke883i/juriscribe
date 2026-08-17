from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape as xml_escape

from juriscribe.browser_delivery import (
    DOCX_MIME,
    build_browser_delivery_manifest,
    browser_docx_delivery_gate,
    content_disposition,
    dashboard_docx_links_report,
)
from juriscribe.dashboard_v100 import render_session_dashboard
from juriscribe.delivery import ATTACH, SURFACE, delivery_gate, normalize_artifact_record
from juriscribe.modes import CONTINUATION, GREENFIELD, REVIEW, required_artifact_roles

SCHEMA = "juriscribe-browser-docx-safari-saturation/v1"
PRIMARY_M = 100
NO_NOVELTY_EXTENSION = 100

SAFARI_CONTEXTS = (
    "SAFARI_MACOS_STANDARD",
    "SAFARI_MACOS_PRIVATE",
    "SAFARI_IOS_STANDARD",
    "SAFARI_IOS_PRIVATE",
    "SAFARI_IPADOS_STANDARD",
    "SAFARI_IPADOS_SPLIT_VIEW",
    "SAFARI_DOWNLOADS_FOLDER",
    "SAFARI_UNICODE_FILENAME",
    "SAFARI_LOCAL_WORKBENCH",
    "SAFARI_JS_DISABLED",
)
EXTENSION_BROWSER_CONTEXTS = (
    "SAFARI_MACOS_STANDARD", "SAFARI_IOS_STANDARD", "SAFARI_IPADOS_STANDARD",
    "CHROMIUM_DESKTOP", "FIREFOX_DESKTOP", "EDGE_DESKTOP", "MOBILE_CHROMIUM",
    "GENERIC_WEBVIEW", "UNKNOWN_USER_AGENT", "JAVASCRIPT_DISABLED_BROWSER",
)
ASSISTANT_CONTEXTS = (
    "OPENAI_ASSISTANT", "GENERIC_AI_ASSISTANT", "LOCAL_MODEL_HOST", "ENTERPRISE_AGENT", "UNKNOWN_ASSISTANT_HOST",
)
FAMILIES = (
    ("VALID_BASELINE", True, "PASS_BASELINE"),
    ("VALID_UNICODE_FILENAME", True, "PASS_BASELINE"),
    ("VALID_NESTED_SPACE_PATH", True, "PASS_BASELINE"),
    ("JAVASCRIPT_DISABLED", True, "PASS_BASELINE"),
    ("NON_DOCX_ATTACHMENT", False, "DOCX_ONLY"),
    ("RECORD_MIME_MISMATCH", False, "DOCX_MIME"),
    ("DASHBOARD_FORCED_ATTACHMENT", False, "SURFACE_SEPARATION"),
    ("MISSING_DOWNLOAD_ATTRIBUTE", False, "DOWNLOAD_ATTRIBUTE"),
    ("CROSS_ORIGIN_HREF", False, "LOCAL_DOCX_HREF"),
    ("DATA_URL_HREF", False, "LOCAL_DOCX_HREF"),
    ("QUERY_FRAGMENT_HREF", False, "LOCAL_DOCX_HREF"),
    ("ANCHOR_MIME_MISMATCH", False, "DOCX_MIME"),
    ("NEW_BROWSING_CONTEXT", False, "NO_NEW_CONTEXT"),
    ("FAKE_DOCX_BYTES", False, "OOXML_MATERIALIZATION"),
    ("READBACK_FAILURE", False, "READBACK"),
    ("NON_FINAL_FORCED_ATTACHMENT", False, "FINAL_ROLE_ONLY"),
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


def _state(root: Path, mode: str, assistant_context: str, case_id: int) -> SimpleNamespace:
    setup = {}
    return SimpleNamespace(
        mode=mode,
        setup=setup,
        runtime={"capabilities": {"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"}, "workspace_base": str(root.resolve())},
        phase="VALIDATING",
        request={"raw": f"Safari DOCX edge {case_id}", "summary": f"Safari DOCX edge {case_id}", "assistant_context": assistant_context},
        mode_selection={},
        mode_contract={"required_artifact_roles": sorted(required_artifact_roles(mode, setup)), "status": "READY"},
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


def _materialize_baseline(root: Path, mode: str, assistant_context: str, case_id: int, family: str):
    state = _state(root, mode, assistant_context, case_id)
    for role in sorted(required_artifact_roles(mode, state.setup)):
        if role == "session_dashboard":
            continue
        path = _doc_path(root, role, case_id, family)
        _write_docx(path, f"{role} — scenario {case_id} — contenuto DOCX materializzato")
        state.artifacts.append(normalize_artifact_record(state, {
            "id": f"{role}-{case_id}", "role": role, "summary": f"{role} scenario {case_id}",
            "path": str(path), "readback": "PASS",
        }))
    dashboard_path = root / "artifacts" / "session-dashboard.html"
    state.artifacts.append(normalize_artifact_record(state, {
        "id": f"dashboard-{case_id}", "role": "session_dashboard", "summary": "Workbench browser della sessione",
        "path": str(dashboard_path), "readback": "PASS",
    }))
    render_session_dashboard(state.__dict__, dashboard_path)
    page = dashboard_path.read_text(encoding="utf-8")
    delivery_ok, delivery_errors = delivery_gate(state)
    links = dashboard_docx_links_report(state, page)
    if not delivery_ok or links.get("status") != "PASS":
        raise AssertionError(f"valid baseline failed for case {case_id}: delivery={delivery_errors}; links={links.get('errors')}")
    manifest = build_browser_delivery_manifest(state)
    if manifest.get("status") != "PASS" or not manifest.get("downloadable_artifacts_only_docx"):
        raise AssertionError(f"baseline browser manifest failed for case {case_id}: {manifest}")
    for descriptor in manifest.get("records") or []:
        if not str(descriptor.get("href") or "").startswith("./") or not str(descriptor.get("href") or "").lower().endswith(".docx"):
            raise AssertionError(f"unsafe baseline href in case {case_id}: {descriptor}")
        if descriptor.get("media_type") != DOCX_MIME or not str(descriptor.get("content_disposition") or "").startswith("attachment;"):
            raise AssertionError(f"invalid DOCX response metadata in case {case_id}: {descriptor}")
    return state, dashboard_path, page


def _strip_scripts(page: str) -> str:
    return re.sub(r"<script\b[^>]*>.*?</script>", "", page, flags=re.IGNORECASE | re.DOTALL)


def _first_attach(state: SimpleNamespace) -> dict:
    return next(item for item in state.artifacts if item.get("delivery_class") == ATTACH)


def _evaluate_mutation(state: SimpleNamespace, page: str, family: str, root: Path) -> tuple[bool, list[str]]:
    if family in {"VALID_BASELINE", "VALID_UNICODE_FILENAME", "VALID_NESTED_SPACE_PATH"}:
        ok, errors = delivery_gate(state)
        report = dashboard_docx_links_report(state, page)
        return bool(ok and report.get("status") == "PASS"), list(errors) + list(report.get("errors") or [])
    if family == "JAVASCRIPT_DISABLED":
        report = dashboard_docx_links_report(state, _strip_scripts(page))
        return report.get("status") == "PASS", list(report.get("errors") or [])
    if family == "NON_DOCX_ATTACHMENT":
        item = _first_attach(state); item["path"] = str(Path(item["path"]).with_suffix(".pdf"))
        ok, errors = browser_docx_delivery_gate(state); return ok, errors
    if family == "RECORD_MIME_MISMATCH":
        _first_attach(state)["media_type"] = "application/pdf"
        ok, errors = browser_docx_delivery_gate(state); return ok, errors
    if family == "DASHBOARD_FORCED_ATTACHMENT":
        next(item for item in state.artifacts if item.get("role") == "session_dashboard")["delivery_class"] = ATTACH
        ok, errors = browser_docx_delivery_gate(state); return ok, errors
    if family == "MISSING_DOWNLOAD_ATTRIBUTE":
        damaged = page.replace(" download type=", " type=", 1)
        report = dashboard_docx_links_report(state, damaged); return report.get("status") == "PASS", list(report.get("errors") or [])
    if family in {"CROSS_ORIGIN_HREF", "DATA_URL_HREF", "QUERY_FRAGMENT_HREF"}:
        if family == "CROSS_ORIGIN_HREF": replacement = "https://example.invalid/artefatto.docx"
        elif family == "DATA_URL_HREF": replacement = "data:application/octet-stream;base64,AA=="
        else: replacement = "./artefatto.docx?download=1#frag"
        damaged = re.sub(r'(<a class="docx-download" href=")[^"]+', lambda match: match.group(1) + replacement, page, count=1)
        report = dashboard_docx_links_report(state, damaged); return report.get("status") == "PASS", list(report.get("errors") or [])
    if family == "ANCHOR_MIME_MISMATCH":
        damaged = page.replace(f'type="{DOCX_MIME}"', 'type="application/pdf"', 1)
        report = dashboard_docx_links_report(state, damaged); return report.get("status") == "PASS", list(report.get("errors") or [])
    if family == "NEW_BROWSING_CONTEXT":
        damaged = page.replace(" download type=", ' download target="_blank" type=', 1)
        report = dashboard_docx_links_report(state, damaged); return report.get("status") == "PASS", list(report.get("errors") or [])
    if family == "FAKE_DOCX_BYTES":
        Path(_first_attach(state)["path"]).write_text("not OOXML", encoding="utf-8")
        ok, errors = delivery_gate(state); return ok, errors
    if family == "READBACK_FAILURE":
        _first_attach(state)["readback"] = "FAIL"
        ok, errors = browser_docx_delivery_gate(state); return ok, errors
    if family == "NON_FINAL_FORCED_ATTACHMENT":
        path = root / "artifacts" / "debug-receipt.docx"; _write_docx(path, "internal receipt")
        state.artifacts.append({"id": "debug", "role": "simulation_receipt", "path": str(path), "readback": "PASS", "format": "DOCX", "media_type": DOCX_MIME, "delivery_class": ATTACH})
        ok, errors = browser_docx_delivery_gate(state); return ok, errors
    raise AssertionError(f"unknown family {family}")


def _classify(errors: list[str], passed: bool) -> set[str]:
    if passed:
        return {"PASS_BASELINE"}
    categories: set[str] = set()
    for error in errors:
        text = str(error).lower()
        if "non-docx attachment" in text or "must end in .docx" in text or "target is not docx" in text or "wrong format" in text:
            categories.add("DOCX_ONLY")
        if "media type" in text or "mime" in text:
            categories.add("DOCX_MIME")
        if "dashboard html" in text or "session dashboard" in text and "attachment" in text:
            categories.add("SURFACE_SEPARATION")
        if "download attribute" in text:
            categories.add("DOWNLOAD_ATTRIBUTE")
        if "same-session" in text or "relative" in text or "href differs" in text or "non-local" in text:
            categories.add("LOCAL_DOCX_HREF")
        if "new browsing context" in text:
            categories.add("NO_NEW_CONTEXT")
        if "valid docx" in text or "ooxml" in text or "wordprocessingml" in text:
            categories.add("OOXML_MATERIALIZATION")
        if "readback" in text:
            categories.add("READBACK")
        if "non-final role" in text:
            categories.add("FINAL_ROLE_ONLY")
    if not categories:
        categories.add("UNCLASSIFIED:" + (str(errors[0])[:80] if errors else "NO_ERROR"))
    return categories


def _scenario(root: Path, ordinal: int, *, extension: bool) -> dict:
    family, expected_pass, expected_category = FAMILIES[(ordinal - 1) % len(FAMILIES)]
    mode = (CONTINUATION, GREENFIELD, REVIEW)[(ordinal - 1) % 3]
    browser_contexts = EXTENSION_BROWSER_CONTEXTS if extension else SAFARI_CONTEXTS
    browser = browser_contexts[(ordinal - 1) % len(browser_contexts)]
    assistant = ASSISTANT_CONTEXTS[(ordinal - 1) % len(ASSISTANT_CONTEXTS)]
    case_root = root / ("extension" if extension else "primary") / f"case-{ordinal:03d}"
    state, dashboard_path, page = _materialize_baseline(case_root, mode, assistant, ordinal, family)
    passed, errors = _evaluate_mutation(state, page, family, case_root)
    categories = _classify(errors, passed)
    if expected_pass != passed:
        raise AssertionError(f"scenario {ordinal} {family} expected pass={expected_pass}, got {passed}: {errors}")
    if expected_category not in categories:
        raise AssertionError(f"scenario {ordinal} {family} missing expected category {expected_category}: {categories}; {errors}")
    if expected_pass:
        descriptor = content_disposition(_first_attach(state).get("path", "artifact.docx"))
        if not descriptor.startswith("attachment;"):
            raise AssertionError(f"scenario {ordinal} lacks attachment content disposition")
    return {
        "ordinal": ordinal,
        "phase": "M_PLUS_EXTENSION" if extension else "ONE_TO_M",
        "family": family,
        "expected_pass": expected_pass,
        "observed_pass": passed,
        "categories": sorted(categories),
        "mode": mode,
        "browser_context": browser,
        "assistant_context": assistant,
        "dashboard": str(dashboard_path),
        "error_count": len(errors),
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
        learned = set().union(*(set(item["categories"]) for item in primary))
        extension = [_scenario(root, cases + index, extension=True) for index in range(1, no_novelty + 1)]
        extension_categories = set().union(*(set(item["categories"]) for item in extension))
        novel = sorted(extension_categories - learned)
        if novel:
            raise AssertionError("M+100 produced novel delivery failure classes: " + ", ".join(novel))
        all_scenarios = primary + extension
        receipt = {
            "schema": SCHEMA,
            "status": "PASS",
            "M": cases,
            "one_to_M_cases": len(primary),
            "M_plus_100_cases": len(extension),
            "total_cases": len(all_scenarios),
            "safari_targeted_primary_cases": sum(1 for item in primary if item["browser_context"].startswith("SAFARI")),
            "no_novelty_after_M": len(novel) == 0,
            "novel_categories_after_M": novel,
            "learned_categories_at_M": sorted(learned),
            "family_counts": dict(sorted(Counter(item["family"] for item in all_scenarios).items())),
            "mode_counts": dict(sorted(Counter(item["mode"] for item in all_scenarios).items())),
            "browser_context_counts": dict(sorted(Counter(item["browser_context"] for item in all_scenarios).items())),
            "assistant_context_counts": dict(sorted(Counter(item["assistant_context"] for item in all_scenarios).items())),
            "downloadable_artifact_contract": "DOCX_ONLY",
            "browser_workbench_contract": "HTML_SURFACE_NOT_ATTACHMENT",
            "javascript_required_for_download": False,
            "global_browser_behavior_claim": False,
            "scenarios": all_scenarios,
        }
        return receipt
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
    result = run(args.cases, args.no_novelty, args.out_root)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(payload + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("schema", "status", "M", "one_to_M_cases", "M_plus_100_cases", "total_cases", "safari_targeted_primary_cases", "no_novelty_after_M", "learned_categories_at_M")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
