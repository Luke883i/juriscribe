from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path

from .admission import issue_receipt, load_contract_text, load_receipt, require_receipt, validate_receipt
from .dashboard import render_session_dashboard
from .orchestrator import (
    apply_setup,
    audit_candidate_chapter,
    record_artifact,
    build_research_plan,
    evaluate_completion,
    freeze_dods,
    ingest_and_mine,
    record_compression,
    record_continuation_coverage,
    record_regeneration,
    record_review_cycle,
    record_review_saturation,
    record_simulation,
    register_bibliography,
    register_continuation_plan,
    register_semantic_mining,
    seal_draft,
    validate_claim_ledger,
)
from .session import Workspace, stable_id


def probe_capabilities(*, admission_receipt=None, contract_text=None):
    contract_text = contract_text or load_contract_text()
    require_receipt(admission_receipt, contract_text)
    checks = {
        "SESSION_CONTEXT": "AVAILABLE",
        "LOCAL_SCRATCH_IO": "UNVERIFIED",
        "STRUCTURED_STORAGE": "AVAILABLE",
        "ATTACHMENT_READ": "UNVERIFIED",
        "DOCX_READ": "UNVERIFIED",
        "DOCX_WRITE": "UNVERIFIED",
        "DOCX_READBACK": "UNVERIFIED",
        "PDF_READ": "UNVERIFIED",
        "WEB_RESEARCH": "UNVERIFIED",
        "REPOSITORY_READ": "UNVERIFIED",
        "REPOSITORY_WRITE": "UNVERIFIED",
        "CLOCK": "AVAILABLE",
        "HASHING": "AVAILABLE",
    }
    try:
        probe = Path(".juriscribe-probe.tmp")
        probe.write_text("probe", encoding="utf-8")
        ok = probe.read_text(encoding="utf-8") == "probe"
        probe.unlink(missing_ok=True)
        checks["LOCAL_SCRATCH_IO"] = "AVAILABLE" if ok else "UNAVAILABLE"
    except OSError:
        checks["LOCAL_SCRATCH_IO"] = "UNAVAILABLE"
    return checks


def initialize(request, root=".juriscribe", session_id=None, host_capabilities=None, *, admission_receipt=None, contract_text=None):
    contract_text = contract_text or load_contract_text()
    receipt = require_receipt(admission_receipt, contract_text)
    session_id = session_id or stable_id("SES", request + os.getcwd())
    caps = probe_capabilities(admission_receipt=receipt, contract_text=contract_text)
    caps.update(host_capabilities or {})
    runtime = {
        "host": platform.platform(),
        "python": platform.python_version(),
        "capabilities": caps,
        "mode": "ACTIVE_FILE" if caps["LOCAL_SCRATCH_IO"] == "AVAILABLE" else "ACTIVE_EPHEMERAL",
    }
    ws = Workspace(root, session_id)
    state = ws.initialize(request, runtime, admission={"status": "ACCEPTED", "receipt": receipt})
    dash = ws.artifact_dir / "session-dashboard.html"
    render_session_dashboard(state.to_dict(), dash)
    state.artifacts.extend([
        {
            "id": "dashboard",
            "summary": "Fascicolo giuridico-scientifico-editoriale della sessione",
            "path": str(dash),
            "readback": "PASS",
            "required": True,
        },
        {
            "id": "node-h",
            "summary": "Header locale di integrità della sessione",
            "path": str(ws.node_path),
            "readback": "PASS",
            "required": True,
        },
    ])
    ws.save(state)
    return ws.base


def _ws(session_dir):
    path = Path(session_dir)
    return Workspace(path.parent, path.name)


def update_dashboard(session_dir):
    ws = _ws(session_dir)
    state = ws.load()
    out = ws.artifact_dir / "session-dashboard.html"
    return render_session_dashboard(state.to_dict(), out)


def _receipt(path):
    return load_receipt(path) if path else None


def _payload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="juriscribe")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("terms")

    accept = sub.add_parser("accept")
    accept.add_argument("--phrase", required=True)
    accept.add_argument("--actor-type", required=True)
    accept.add_argument("--evidence-type", required=True)
    accept.add_argument("--user-message", required=True)
    accept.add_argument("--out", required=True)

    probe = sub.add_parser("probe")
    probe.add_argument("--receipt", required=True)

    init = sub.add_parser("initialize")
    init.add_argument("--request", required=True)
    init.add_argument("--root", default=".juriscribe")
    init.add_argument("--session-id")
    init.add_argument("--receipt", required=True)

    mine = sub.add_parser("mine")
    mine.add_argument("session_dir")
    mine.add_argument("--text-file", required=True)
    mine.add_argument("--source-id", required=True)
    mine.add_argument("--chapter")

    semantic = sub.add_parser("semantic-mining")
    semantic.add_argument("session_dir")
    semantic.add_argument("--json-file", required=True)

    bibliography = sub.add_parser("bibliography")
    bibliography.add_argument("session_dir")
    bibliography.add_argument("--json-file", required=True)

    setup = sub.add_parser("accept-setup")
    setup.add_argument("session_dir")
    setup.add_argument("--overrides-json")

    freeze = sub.add_parser("freeze-dods")
    freeze.add_argument("session_dir")
    freeze.add_argument("--additional-json")

    continuation_plan = sub.add_parser("continuation-plan")
    continuation_plan.add_argument("session_dir")
    continuation_plan.add_argument("--json-file", required=True)

    continuation_coverage = sub.add_parser("continuation-coverage")
    continuation_coverage.add_argument("session_dir")
    continuation_coverage.add_argument("--json-file", required=True)

    research = sub.add_parser("research-plan")
    research.add_argument("session_dir")
    claims = sub.add_parser("validate-claims")
    claims.add_argument("session_dir")

    draft = sub.add_parser("seal-draft")
    draft.add_argument("session_dir")
    draft.add_argument("--text-file", required=True)
    draft.add_argument("--stage", choices=["INITIAL", "REGENERATED", "COMPRESSED_FINAL"], default="INITIAL")

    review = sub.add_parser("review-cycle")
    review.add_argument("session_dir")
    review.add_argument("--json-file", required=True)

    regen = sub.add_parser("record-regeneration")
    regen.add_argument("session_dir")
    regen.add_argument("--json-file", required=True)

    saturation = sub.add_parser("review-saturation")
    saturation.add_argument("session_dir")
    saturation.add_argument("--json-file", required=True)

    simulation = sub.add_parser("record-simulation")
    simulation.add_argument("session_dir")
    simulation.add_argument("--json-file", required=True)

    compression = sub.add_parser("record-compression")
    compression.add_argument("session_dir")
    compression.add_argument("--json-file", required=True)

    audit = sub.add_parser("audit-chapter")
    audit.add_argument("session_dir")
    audit.add_argument("--text-file", required=True)
    audit.add_argument("--reference-file")
    audit.add_argument("--prior-file", action="append", default=[])
    audit.add_argument("--artifact-evidence-json")

    artifact = sub.add_parser("record-artifact")
    artifact.add_argument("session_dir")
    artifact.add_argument("--json-file", required=True)

    gate = sub.add_parser("gate")
    gate.add_argument("session_dir")
    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("session_dir")
    node = sub.add_parser("node-header")
    node.add_argument("session_dir")

    args = parser.parse_args(argv)
    contract = load_contract_text()

    if args.command == "terms":
        print(contract)
        return 0
    if args.command == "accept":
        receipt = issue_receipt(
            contract,
            phrase=args.phrase,
            actor_type=args.actor_type,
            evidence_type=args.evidence_type,
            user_message=args.user_message,
        )
        Path(args.out).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(args.out)
        return 0
    if args.command == "probe":
        print(json.dumps(probe_capabilities(admission_receipt=_receipt(args.receipt), contract_text=contract), indent=2))
        return 0
    if args.command == "initialize":
        print(initialize(args.request, args.root, args.session_id, admission_receipt=_receipt(args.receipt), contract_text=contract))
        return 0

    ws = _ws(args.session_dir)
    state = ws.load()
    ok, _ = validate_receipt((state.admission or {}).get("receipt"), contract)
    if not ok:
        raise PermissionError("session admission receipt is missing or stale")

    if args.command == "mine":
        ingest_and_mine(state, Path(args.text_file).read_text(encoding="utf-8"), source_id=args.source_id, chapter=args.chapter)
    elif args.command == "semantic-mining":
        payload = _payload(args.json_file)
        report = register_semantic_mining(state, payload.get("units", []), payload.get("relations", []))
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("status") == "PASS" else 2
    elif args.command == "bibliography":
        payload = _payload(args.json_file)
        entries = payload if isinstance(payload, list) else payload.get("entries", [])
        report = register_bibliography(state, entries)
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("status") in {"PASS", "NOT_AVAILABLE"} else 2
    elif args.command == "accept-setup":
        apply_setup(state, json.loads(args.overrides_json) if args.overrides_json else None)
    elif args.command == "freeze-dods":
        freeze_dods(state, json.loads(args.additional_json) if args.additional_json else None)
    elif args.command == "continuation-plan":
        report = register_continuation_plan(state, _payload(args.json_file))
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    elif args.command == "continuation-coverage":
        report = record_continuation_coverage(state, _payload(args.json_file))
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("status") == "PASS" else 2
    elif args.command == "research-plan":
        build_research_plan(state)
        ws.save(state)
        print(json.dumps(state.source_intelligence["research_plan"], ensure_ascii=False, indent=2))
        return 0
    elif args.command == "validate-claims":
        errors = validate_claim_ledger(state)
        ws.save(state)
        print(json.dumps(errors, ensure_ascii=False, indent=2))
        return 1 if errors else 0
    elif args.command == "seal-draft":
        record = seal_draft(state, Path(args.text_file).read_text(encoding="utf-8"), stage=args.stage)
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    elif args.command == "review-cycle":
        record_review_cycle(state, _payload(args.json_file))
    elif args.command == "record-regeneration":
        record_regeneration(state, _payload(args.json_file))
    elif args.command == "review-saturation":
        result = record_review_saturation(state, _payload(args.json_file))
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "PASS" else 2
    elif args.command == "record-simulation":
        record_simulation(state, _payload(args.json_file))
    elif args.command == "record-compression":
        record_compression(state, _payload(args.json_file))
    elif args.command == "record-artifact":
        record_artifact(state, _payload(args.json_file))
    elif args.command == "audit-chapter":
        text = Path(args.text_file).read_text(encoding="utf-8")
        reference = Path(args.reference_file).read_text(encoding="utf-8") if args.reference_file else None
        priors = [Path(path).read_text(encoding="utf-8") for path in args.prior_file]
        evidence = _payload(args.artifact_evidence_json) if args.artifact_evidence_json else None
        report = audit_candidate_chapter(state, text, reference_text=reference, prior_texts=priors, artifact_evidence=evidence)
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report.get("status") != "PASS" else 0
    elif args.command == "gate":
        node_ok, node_errors = ws.validate_node(state)
        state.node_integrity = {"status": "PASS" if node_ok else "FAIL", "errors": node_errors}
        evaluate_completion(state)
        ws.save(state)
        update_dashboard(ws.base)
        print(json.dumps(state.completion, ensure_ascii=False, indent=2))
        return 0 if state.completion["eligible"] else 2
    elif args.command == "dashboard":
        print(update_dashboard(ws.base))
        return 0
    elif args.command == "node-header":
        node_ok, node_errors = ws.validate_node(state)
        print(json.dumps({"status": "PASS" if node_ok else "FAIL", "errors": node_errors, "path": str(ws.node_path)}, ensure_ascii=False, indent=2))
        return 0 if node_ok else 2
    else:
        return 1

    ws.save(state)
    update_dashboard(ws.base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
