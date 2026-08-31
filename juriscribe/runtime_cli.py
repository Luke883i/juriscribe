"""Current Juriscribe CLI/runtime composition.

This module is the non-versioned current command surface. Historical pipeline_v9
and pipeline_v11 remain compatibility entrypoints only; the public pipeline no
longer executes through them.
"""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

from .admission import CONTRACT_VERSION, issue_receipt, load_contract_text, load_receipt, require_receipt, validate_receipt
from .bootstrap import activate_work, bootstrap_card, bootstrap_gate, claim_probe_receipt, issue_probe_receipt, require_probe_receipt
from .continuity import checkpoint_id
from .dashboard_persistence import persist_dashboard_generation
from .interaction import interaction_card
from .modes import MODES, mode_choices
from .orchestrator import (
    apply_setup,
    audit_legal_text,
    build_research_plan,
    calibrate_refactoring,
    consolidation_gate,
    evaluate_completion,
    freeze_dods,
    ingest_and_mine,
    record_artifact,
    record_compression,
    record_consolidation_saturation,
    record_continuation_coverage,
    record_final_review,
    record_provenance,
    record_regeneration,
    record_review_cycle,
    record_review_saturation,
    record_simulation,
    register_bibliography,
    register_continuation_plan,
    register_refactoring_plan,
    register_semantic_mining,
    seal_draft,
    seal_refined_candidate,
    select_mode,
    validate_claim_ledger,
)
from .recovery import inspect_recovery_bundle, resume_recovery_bundle
from .session import Workspace, new_session_id

MATERIALIZATION_CONTINUE_COMMAND = "continue-materialization"


def probe_capabilities(*, admission_receipt=None, contract_text=None):
    contract_text = contract_text or load_contract_text()
    require_receipt(admission_receipt, contract_text)
    checks = {
        "SESSION_CONTEXT": "AVAILABLE",
        "LOCAL_SCRATCH_IO": "UNVERIFIED",
        "STRUCTURED_STORAGE": "AVAILABLE",
        "ATTACHMENT_READ": "UNVERIFIED",
        "CHAT_ATTACHMENT_WRITE": "UNVERIFIED",
        "LOCAL_FILE_DELIVERY": "UNVERIFIED",
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
        checks["LOCAL_FILE_DELIVERY"] = "AVAILABLE" if ok else "UNAVAILABLE"
    except OSError:
        checks["LOCAL_SCRATCH_IO"] = "UNAVAILABLE"
        checks["LOCAL_FILE_DELIVERY"] = "UNAVAILABLE"
    return checks


def perform_probe(*, admission_receipt, contract_text=None, host_capabilities=None, host=None, probed_at=None):
    contract_text = contract_text or load_contract_text()
    caps = probe_capabilities(admission_receipt=admission_receipt, contract_text=contract_text)
    caps.update(host_capabilities or {})
    return issue_probe_receipt(
        admission_receipt,
        contract_text,
        caps,
        host=host or platform.platform(),
        probed_at=probed_at,
    )


def _sealed_capabilities(probe, host_capabilities=None):
    caps = dict(probe.get("capabilities") or {})
    for key, value in (host_capabilities or {}).items():
        if key not in caps:
            raise PermissionError(f"host capability {key} was not present in sealed probe receipt")
        if str(caps[key]) != str(value):
            raise PermissionError(f"host capability {key} differs from sealed probe receipt")
    return caps


def persist_session(ws: Workspace, state, *, trigger: str = "runtime-mutation") -> Path:
    return persist_dashboard_generation(ws, state, trigger=trigger)


def initialize(
    request,
    root=".juriscribe",
    session_id=None,
    host_capabilities=None,
    *,
    admission_receipt=None,
    probe_receipt=None,
    contract_text=None,
):
    contract_text = contract_text or load_contract_text()
    receipt = require_receipt(admission_receipt, contract_text)
    probe = require_probe_receipt(probe_receipt, receipt, contract_text)
    session_id = session_id or new_session_id()
    ws = Workspace(root, session_id)
    ws.assert_initializable()
    caps = _sealed_capabilities(probe, host_capabilities)
    claim_probe_receipt(root, probe, session_id)
    runtime = {
        "host": probe.get("host") or platform.platform(),
        "python": platform.python_version(),
        "capabilities": caps,
        "mode": "ACTIVE_FILE" if caps.get("LOCAL_SCRATCH_IO") == "AVAILABLE" else "ACTIVE_EPHEMERAL",
        "workspace_base": str(ws.base.resolve()),
    }
    mode_card = bootstrap_card(
        "MODE_SELECTION_REQUIRED",
        contract_version=receipt.get("contract_version", ""),
        detail="T&C accepted; probe sealed and consumed; workspace initialized; explicit mode selection required.",
    )
    admission = {"status": "ACCEPTED", "receipt": receipt, "probe_receipt": probe, "bootstrap": mode_card}
    state = ws.initialize(request, runtime, admission=admission, persist=False)
    state.phase = "MODE_SELECTION_REQUIRED"
    state.interaction = {
        "card": interaction_card(
            "MODE_SELECTION_REQUIRED",
            summary="Scegli una modalità canonica prima di caricare i materiali sostanziali.",
        ),
        "history": [],
        "status": "READY",
    }
    state.artifacts.append({
        "id": "session-integrity",
        "role": "session_integrity",
        "summary": "Manifest canonico di integrità",
        "path": str(ws.integrity_path),
        "readback": "PASS",
        "required": False,
        "delivery_class": "INTERNAL",
    })
    persist_session(ws, state, trigger="initialize")
    return ws.base


def bootstrap_after_acceptance(
    request,
    *,
    phrase,
    actor_type,
    evidence_type,
    user_message,
    root=".juriscribe",
    session_id=None,
    host_capabilities=None,
    contract_text=None,
):
    contract_text = contract_text or load_contract_text()
    receipt = issue_receipt(
        contract_text,
        phrase=phrase,
        actor_type=actor_type,
        evidence_type=evidence_type,
        user_message=user_message,
    )
    probe = perform_probe(
        admission_receipt=receipt,
        contract_text=contract_text,
        host_capabilities=host_capabilities,
    )
    base = initialize(
        request,
        root=root,
        session_id=session_id,
        admission_receipt=receipt,
        probe_receipt=probe,
        contract_text=contract_text,
    )
    return {
        "session_dir": str(base),
        "state": "MODE_SELECTION_REQUIRED",
        "choices": [*mode_choices(), "ALTRO"],
    }


def _ws(session_dir):
    path = Path(session_dir)
    return Workspace(path.parent, path.name)


def update_dashboard(session_dir):
    ws = _ws(session_dir)
    state = ws.load()
    return persist_session(ws, state, trigger="dashboard")


def _receipt(path):
    return load_receipt(path) if path else None


def _payload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _add_common_commands(sub):
    terms = sub.add_parser("terms"); terms.add_argument("--brief", action="store_true")
    accept = sub.add_parser("accept"); accept.add_argument("--phrase", required=True); accept.add_argument("--actor-type", required=True); accept.add_argument("--evidence-type", required=True); accept.add_argument("--user-message", required=True); accept.add_argument("--out", required=True)
    probe = sub.add_parser("probe"); probe.add_argument("--receipt", required=True); probe.add_argument("--out", required=True)
    init = sub.add_parser("initialize"); init.add_argument("--request", required=True); init.add_argument("--root", default=".juriscribe"); init.add_argument("--session-id"); init.add_argument("--receipt", required=True); init.add_argument("--probe-receipt", required=True)
    fast = sub.add_parser("bootstrap-after-acceptance"); fast.add_argument("--request", required=True); fast.add_argument("--root", default=".juriscribe"); fast.add_argument("--session-id"); fast.add_argument("--phrase", required=True); fast.add_argument("--actor-type", required=True); fast.add_argument("--evidence-type", required=True); fast.add_argument("--user-message", required=True)
    choose = sub.add_parser("select-mode"); choose.add_argument("session_dir"); choose.add_argument("--mode", choices=list(MODES), required=True)
    mine = sub.add_parser("mine"); mine.add_argument("session_dir"); mine.add_argument("--text-file", required=True); mine.add_argument("--source-id", required=True); mine.add_argument("--chapter"); mine.add_argument("--role")
    semantic = sub.add_parser("semantic-mining"); semantic.add_argument("session_dir"); semantic.add_argument("--json-file", required=True)
    bibliography = sub.add_parser("bibliography"); bibliography.add_argument("session_dir"); bibliography.add_argument("--json-file", required=True)
    setup = sub.add_parser("accept-setup"); setup.add_argument("session_dir"); setup.add_argument("--overrides-json")
    freeze = sub.add_parser("freeze-dods"); freeze.add_argument("session_dir"); freeze.add_argument("--additional-json")
    continuation_plan = sub.add_parser("continuation-plan"); continuation_plan.add_argument("session_dir"); continuation_plan.add_argument("--json-file", required=True)
    continuation_coverage = sub.add_parser("continuation-coverage"); continuation_coverage.add_argument("session_dir"); continuation_coverage.add_argument("--json-file", required=True)
    sub.add_parser("research-plan").add_argument("session_dir")
    sub.add_parser("validate-claims").add_argument("session_dir")
    draft = sub.add_parser("seal-draft"); draft.add_argument("session_dir"); draft.add_argument("--text-file", required=True); draft.add_argument("--stage", choices=["INITIAL", "REGENERATED", "COMPRESSED_FINAL", "REVIEW_SOURCE", "REVISED_FINAL"], default="INITIAL")
    review = sub.add_parser("review-cycle"); review.add_argument("session_dir"); review.add_argument("--json-file", required=True)
    regen = sub.add_parser("record-regeneration"); regen.add_argument("session_dir"); regen.add_argument("--json-file", required=True)
    saturation = sub.add_parser("review-saturation"); saturation.add_argument("session_dir"); saturation.add_argument("--json-file", required=True)
    simulation = sub.add_parser("record-simulation"); simulation.add_argument("session_dir"); simulation.add_argument("--json-file", required=True)
    compression = sub.add_parser("record-compression"); compression.add_argument("session_dir"); compression.add_argument("--json-file", required=True)
    provenance = sub.add_parser("record-provenance"); provenance.add_argument("session_dir"); provenance.add_argument("--json-file", required=True)
    final_review = sub.add_parser("final-review"); final_review.add_argument("session_dir"); final_review.add_argument("--json-file", required=True)
    for name in ["audit-text", "audit-chapter"]:
        audit = sub.add_parser(name); audit.add_argument("session_dir"); audit.add_argument("--text-file", required=True); audit.add_argument("--reference-file"); audit.add_argument("--prior-file", action="append", default=[]); audit.add_argument("--artifact-evidence-json")
    artifact = sub.add_parser("record-artifact"); artifact.add_argument("session_dir"); artifact.add_argument("--json-file", required=True)
    sub.add_parser("gate").add_argument("session_dir")
    sub.add_parser("dashboard").add_argument("session_dir")
    sub.add_parser("interaction-card").add_argument("session_dir")
    sub.add_parser("integrity").add_argument("session_dir")
    sub.add_parser("node-header").add_argument("session_dir")
    sub.add_parser(MATERIALIZATION_CONTINUE_COMMAND).add_argument("session_dir")

    p = sub.add_parser("consolidation-plan"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-saturation"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-calibrate"); p.add_argument("session_dir"); p.add_argument("--json-file", required=True)
    p = sub.add_parser("consolidation-seal-refined"); p.add_argument("session_dir"); p.add_argument("--source-id", required=True); p.add_argument("--text-file", required=True); p.add_argument("--projection-json", required=True)
    sub.add_parser("consolidation-status").add_argument("session_dir")

    p = sub.add_parser("recovery-bundle"); p.add_argument("session_dir"); p.add_argument("--out", required=True)
    p = sub.add_parser("recovery-inspect"); p.add_argument("bundle")
    p = sub.add_parser("recovery-resume"); p.add_argument("bundle"); p.add_argument("--root", default=".juriscribe")


def _run_recovery(args, contract):
    if args.command == "recovery-bundle":
        ws = _ws(args.session_dir); state = ws.load(); before = checkpoint_id(state)
        from .orchestrator import create_recovery_bundle
        out = create_recovery_bundle(state, args.out, workspace_base=ws.base, require_resumable=True)
        report = inspect_recovery_bundle(out)
        if report.get("status") != "PASS":
            raise ValueError("generated recovery bundle failed readback: " + "; ".join(report.get("errors") or []))
        if checkpoint_id(state) != before:
            raise RuntimeError("recovery export mutated scientific checkpoint")
        print(json.dumps({"status": "PASS", "bundle": str(out), "checkpoint_id": before, "attach_to_user": True}, ensure_ascii=False, indent=2))
        return 0
    report = inspect_recovery_bundle(args.bundle)
    if report.get("status") != "PASS":
        print(json.dumps({"status": "FAIL", "errors": report.get("errors") or []}, ensure_ascii=False, indent=2)); return 2
    if args.command == "recovery-inspect":
        iteration = report.get("iteration") or {}
        print(json.dumps({
            "status": "PASS",
            "session_id": (report.get("state") or {}).get("session_id"),
            "checkpoint_id": (report.get("manifest") or {}).get("checkpoint_id"),
            "where": iteration.get("where"),
            "next": iteration.get("next"),
            "material_count": (report.get("manifest") or {}).get("material_count"),
        }, ensure_ascii=False, indent=2)); return 0
    receipt = ((report.get("state") or {}).get("admission") or {}).get("receipt")
    caps = probe_capabilities(admission_receipt=receipt, contract_text=contract)
    base = resume_recovery_bundle(args.bundle, args.root, host_capabilities=caps, host=platform.platform(), contract_text=contract)
    print(json.dumps({"status": "PASS", "session_dir": str(base), "checkpoint_id": (report.get("manifest") or {}).get("checkpoint_id")}, ensure_ascii=False, indent=2)); return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="juriscribe")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_common_commands(sub)
    args = parser.parse_args(argv)
    contract = load_contract_text()

    if args.command == "terms":
        if args.brief:
            print(json.dumps({
                "contract_version": CONTRACT_VERSION,
                "contract_sha256": __import__("hashlib").sha256(contract.replace("\r\n", "\n").encode("utf-8")).hexdigest(),
                "acceptance": "I ACCEPT must be an explicit human message",
                "full_terms_available": True,
            }, ensure_ascii=False, indent=2))
        else:
            print(contract)
            print(json.dumps(bootstrap_card("TERMS_PRESENTED", contract_version=CONTRACT_VERSION), ensure_ascii=False, indent=2))
        return 0
    if args.command == "accept":
        receipt = issue_receipt(contract, phrase=args.phrase, actor_type=args.actor_type, evidence_type=args.evidence_type, user_message=args.user_message)
        Path(args.out).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(bootstrap_card("PROBE_REQUIRED", contract_version=receipt["contract_version"]), ensure_ascii=False, indent=2)); return 0
    if args.command == "probe":
        receipt = _receipt(args.receipt); probe_receipt = perform_probe(admission_receipt=receipt, contract_text=contract)
        Path(args.out).write_text(json.dumps(probe_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"probe_receipt": args.out, "next": bootstrap_card("INITIALIZE_REQUIRED", contract_version=probe_receipt["contract_version"])}, ensure_ascii=False, indent=2)); return 0
    if args.command == "initialize":
        print(initialize(args.request, args.root, args.session_id, admission_receipt=_receipt(args.receipt), probe_receipt=_receipt(args.probe_receipt), contract_text=contract)); return 0
    if args.command == "bootstrap-after-acceptance":
        result = bootstrap_after_acceptance(args.request, phrase=args.phrase, actor_type=args.actor_type, evidence_type=args.evidence_type, user_message=args.user_message, root=args.root, session_id=args.session_id, contract_text=contract)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    if args.command in {"recovery-bundle", "recovery-inspect", "recovery-resume"}:
        return _run_recovery(args, contract)

    ws = _ws(args.session_dir)
    state = ws.load()
    ok, _ = validate_receipt((state.admission or {}).get("receipt"), contract)
    boot_ok, _ = bootstrap_gate(state.admission)
    if not ok or not boot_ok:
        raise PermissionError("session bootstrap is missing, stale or not ready")

    if args.command == "select-mode":
        result = select_mode(state, args.mode)
        activate_work(state.admission, contract_version=(state.admission.get("receipt") or {}).get("contract_version", CONTRACT_VERSION))
        persist_session(ws, state, trigger="select-mode")
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    if args.command == "dashboard":
        print(update_dashboard(ws.base)); return 0
    if args.command == "interaction-card":
        print(json.dumps((state.interaction or {}).get("card") or interaction_card(state.phase), ensure_ascii=False, indent=2)); return 0
    if args.command in {"integrity", "node-header"}:
        integrity_ok, integrity_errors = ws.validate_integrity(state)
        payload = {"status": "PASS" if integrity_ok else "FAIL", "errors": integrity_errors, "path": str(ws.integrity_path), "legacy_path": str(ws.node_path)}
        print(json.dumps(payload, ensure_ascii=False, indent=2)); return 0 if integrity_ok else 2
    if not state.mode:
        raise PermissionError("explicit mode selection required before substantive work")

    rc = 0
    output = None
    if args.command == "mine":
        ingest_and_mine(state, Path(args.text_file).read_text(encoding="utf-8"), source_id=args.source_id, chapter=args.chapter, role=args.role)
    elif args.command == "semantic-mining":
        payload = _payload(args.json_file); output = register_semantic_mining(state, payload.get("units", []), payload.get("relations", [])); rc = 0 if output.get("status") == "PASS" else 2
    elif args.command == "bibliography":
        payload = _payload(args.json_file); entries = payload if isinstance(payload, list) else payload.get("entries", []); output = register_bibliography(state, entries); rc = 0 if output.get("status") in {"PASS", "NOT_AVAILABLE"} else 2
    elif args.command == "accept-setup":
        apply_setup(state, json.loads(args.overrides_json) if args.overrides_json else None)
    elif args.command == "freeze-dods":
        freeze_dods(state, json.loads(args.additional_json) if args.additional_json else None)
    elif args.command == "continuation-plan":
        output = register_continuation_plan(state, _payload(args.json_file))
    elif args.command == "continuation-coverage":
        output = record_continuation_coverage(state, _payload(args.json_file)); rc = 0 if output.get("status") == "PASS" else 2
    elif args.command == "research-plan":
        build_research_plan(state); output = state.source_intelligence["research_plan"]
    elif args.command == "validate-claims":
        output = validate_claim_ledger(state); rc = 1 if output else 0
    elif args.command == "seal-draft":
        output = seal_draft(state, Path(args.text_file).read_text(encoding="utf-8"), stage=args.stage)
    elif args.command == "review-cycle":
        record_review_cycle(state, _payload(args.json_file))
    elif args.command == "record-regeneration":
        record_regeneration(state, _payload(args.json_file))
    elif args.command == "review-saturation":
        output = record_review_saturation(state, _payload(args.json_file)); rc = 0 if output.get("status") == "PASS" else 2
    elif args.command == "record-simulation":
        record_simulation(state, _payload(args.json_file))
    elif args.command == "record-compression":
        record_compression(state, _payload(args.json_file))
    elif args.command == "record-provenance":
        output = record_provenance(state, _payload(args.json_file))
    elif args.command == "final-review":
        output = record_final_review(state, _payload(args.json_file))
    elif args.command == "record-artifact":
        record_artifact(state, _payload(args.json_file))
    elif args.command in {"audit-text", "audit-chapter"}:
        text = Path(args.text_file).read_text(encoding="utf-8")
        reference = Path(args.reference_file).read_text(encoding="utf-8") if args.reference_file else None
        priors = [Path(p).read_text(encoding="utf-8") for p in args.prior_file]
        evidence = _payload(args.artifact_evidence_json) if args.artifact_evidence_json else None
        output = audit_legal_text(state, text, reference_text=reference, prior_texts=priors, artifact_evidence=evidence)
        rc = 0 if state.mode == "REVIEW" and ((state.setup or {}).get("accepted") or {}).get("review_output", "REPORT_ONLY") == "REPORT_ONLY" else (1 if output.get("status") != "PASS" else 0)
    elif args.command in {"gate", MATERIALIZATION_CONTINUE_COMMAND}:
        integrity_ok, integrity_errors = ws.validate_integrity(state); state.node_integrity = {"status": "PASS" if integrity_ok else "FAIL", "errors": integrity_errors}; evaluate_completion(state); output = state.completion; rc = 0 if state.completion["eligible"] else 2
    elif args.command == "consolidation-plan":
        payload = _payload(args.json_file); output = register_refactoring_plan(state, gaps=payload.get("gaps", []), operations=payload.get("operations", []))
    elif args.command == "consolidation-saturation":
        output = record_consolidation_saturation(state, _payload(args.json_file))
    elif args.command == "consolidation-calibrate":
        payload = _payload(args.json_file); output = calibrate_refactoring(state, payload.get("decisions", payload if isinstance(payload, list) else []))
    elif args.command == "consolidation-seal-refined":
        output = seal_refined_candidate(state, source_id=args.source_id, text=Path(args.text_file).read_text(encoding="utf-8"), semantic_projection=_payload(args.projection_json))
    elif args.command == "consolidation-status":
        gate_ok, errors = consolidation_gate(state); output = {"status": "PASS" if gate_ok else "FAIL", "errors": errors, "phase": state.phase}; rc = 0 if gate_ok else 2
    else:
        return 1

    if args.command != "consolidation-status":
        persist_session(ws, state, trigger=args.command)
    if output is not None:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
