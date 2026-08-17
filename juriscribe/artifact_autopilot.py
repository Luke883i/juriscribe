from __future__ import annotations

import os
import uuid
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from .artifact_governance import record_artifact
from .conversation_contract import build_final_artifact_inference_trace, pipeline_lock_gate
from .dossier_materialization import render_dossier_text
from .modes import required_artifact_roles, review_output

PROFILE_ID = "JURISCRIBE_STANDARD_ARTIFACT_AUTOPILOT_V1"
SCHEMA = "juriscribe-standard-artifact-autopilot/v1"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOSSIER_ROLES = {"evidence_dossier", "source_register", "inference_register", "transformation_ledger"}
NARRATIVE_ROLES = {"final_chapter", "final_legal_text", "revised_legal_text"}
REVIEW_ROLES = {"review_report", "review_findings_register"}


def _payload(state: Any) -> dict[str, Any]:
    return state if isinstance(state, dict) else state.__dict__


def _strategy(state: Any) -> dict[str, Any]:
    if isinstance(state, dict):
        return state.setdefault("strategy", {})
    return state.strategy


def store_candidate_text(state: Any, candidate_digest: str, text: str) -> None:
    digest = str(candidate_digest or "").strip()
    if not digest:
        raise ValueError("candidate digest required for runtime candidate store")
    strategy = _strategy(state)
    store = strategy.setdefault("sealed_candidate_texts", {})
    store[digest] = str(text or "")
    strategy["sealed_candidate_text_store_profile"] = PROFILE_ID


def _current_candidate(state: Any) -> tuple[str, str]:
    s = _payload(state)
    drafts = list(s.get("drafts") or [])
    if not drafts:
        return "", ""
    digest = str(drafts[-1].get("digest") or "")
    text = str((s.get("strategy") or {}).get("sealed_candidate_texts", {}).get(digest) or "")
    return digest, text


def _artifact_root(state: Any) -> Path:
    s = _payload(state)
    workspace = str((s.get("runtime") or {}).get("workspace_base") or "").strip()
    if not workspace:
        raise ValueError("runtime workspace_base missing; standard artifact autopilot unavailable")
    root = (Path(workspace) / "artifacts").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _word_document(paragraphs: list[str]) -> str:
    body = []
    for paragraph in paragraphs:
        text = str(paragraph or "")
        if not text.strip():
            body.append("<w:p/>")
            continue
        body.append(
            '<w:p><w:r><w:t xml:space="preserve">'
            + xml_escape(text)
            + "</w:t></w:r></w:p>"
        )
    if not body:
        body.append('<w:p><w:r><w:t xml:space="preserve">Documento Juriscribe</w:t></w:r></w:p>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>' + "".join(body) + '<w:sectPr/></w:body></w:document>'
    )


def _write_docx_atomic(path: Path, title: str, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    paragraphs = [str(title or "Documento Juriscribe")]
    paragraphs.extend(str(text or "").replace("\r\n", "\n").split("\n"))
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as package:
            package.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                '</Types>',
            )
            package.writestr(
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '</Relationships>',
            )
            package.writestr("word/document.xml", _word_document(paragraphs))
            package.writestr(
                "word/_rels/document.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>',
            )
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _review_findings_text(state: Any) -> str:
    s = _payload(state)
    lines: list[str] = []
    cycles = list((s.get("review") or {}).get("cycles") or [])
    for cycle in cycles:
        lines.append(f"Ciclo {cycle.get('cycle', '')} — stato {cycle.get('status', '')}")
        findings = list(cycle.get("findings") or [])
        if not findings:
            lines.append("Nessun finding registrato.")
        for index, finding in enumerate(findings, 1):
            identifier = finding.get("finding_id") or finding.get("id") or f"F{index}"
            problem = finding.get("problema_rilevato") or finding.get("problem") or finding.get("summary") or ""
            severity = finding.get("gravita") or finding.get("severity") or ""
            action = finding.get("intervento_proposto") or finding.get("action") or ""
            lines.append(f"{identifier} | gravità: {severity} | problema: {problem} | intervento: {action}")
    return "\n".join(lines).strip() or "Nessun finding registrato nella sessione."


def _review_report_text(state: Any) -> str:
    s = _payload(state)
    request = s.get("request") or {}
    review = s.get("review") or {}
    quality = s.get("quality") or {}
    final_review = s.get("final_review") or {}
    lines = [
        f"Mandato: {request.get('summary') or request.get('raw') or ''}",
        f"Modalità: {s.get('mode') or ''}",
        f"Esito review: {review.get('status') or ''}",
        f"Esito audit qualità: {quality.get('status') or ''}",
        f"Review finale severa: {final_review.get('status') or ''}",
        "",
        "Registro dei rilievi:",
        _review_findings_text(state),
    ]
    return "\n".join(lines).strip() + "\n"


def _role_text(state: Any, role: str) -> tuple[str, str, str]:
    s = _payload(state)
    digest, candidate_text = _current_candidate(state)
    titles = {
        "final_chapter": "Nuovo capitolo",
        "final_legal_text": "Testo giuridico finale",
        "revised_legal_text": "Testo giuridico revisionato",
        "review_report": "Relazione di revisione",
        "review_findings_register": "Registro dei rilievi",
        "evidence_dossier": "Evidence dossier",
        "source_register": "Source register",
        "inference_register": "Inference register",
        "transformation_ledger": "Transformation ledger",
    }
    if role in DOSSIER_ROLES:
        return titles[role], render_dossier_text(state, role), "CANONICAL_SEMANTIC_PROJECTION"
    if role in NARRATIVE_ROLES:
        if not digest or not candidate_text:
            raise ValueError(f"sealed candidate text unavailable for automatic {role} materialization")
        expected_stage = "COMPRESSED_FINAL" if str(s.get("mode") or "") in {"CONTINUATION", "GREENFIELD"} else "REVISED_FINAL"
        if str((s.get("drafts") or [{}])[-1].get("stage") or "") != expected_stage:
            raise ValueError(f"automatic {role} materialization requires current {expected_stage} candidate")
        return titles[role], candidate_text, "SEALED_FINAL_CANDIDATE"
    if role == "review_report":
        return titles[role], _review_report_text(state), "REVIEW_STATE_PROJECTION"
    if role == "review_findings_register":
        return titles[role], _review_findings_text(state), "REVIEW_FINDINGS_PROJECTION"
    raise ValueError(f"unsupported standard artifact role: {role}")


def _upsert_record(state: Any, role: str, path: Path, source_kind: str, candidate_digest: str) -> dict[str, Any]:
    s = _payload(state)
    if isinstance(state, dict):
        artifacts = state.setdefault("artifacts", [])
    else:
        artifacts = state.artifacts
    artifacts[:] = [item for item in artifacts if str(item.get("role") or "") != role]
    record: dict[str, Any] = {
        "id": f"auto-{role}",
        "role": role,
        "summary": f"Artefatto standard {role} materializzato automaticamente dal runtime Juriscribe.",
        "path": str(path),
        "readback": "PASS",
        "auto_materialized_by_runtime": True,
        "autopilot_profile": PROFILE_ID,
        "source_kind": source_kind,
    }
    if role == "final_chapter":
        trace = build_final_artifact_inference_trace(state, role, candidate_digest)
        if trace.get("status") != "PASS":
            raise ValueError("final_chapter inference trace failed: " + "; ".join(trace.get("errors") or []))
        record["inference_trace"] = trace
    return record_artifact(state, record)


def materialize_standard_artifacts(state: Any, *, require_all: bool = True) -> dict[str, Any]:
    s = _payload(state)
    mode = str(s.get("mode") or "").strip()
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "mode": mode,
        "status": "NOT_APPLICABLE" if not mode else "PASS",
        "required_roles": [],
        "materialized_roles": [],
        "errors": [],
        "runtime_owned": True,
        "assistant_action_required": False,
        "browser_action_required": False,
    }
    if not mode:
        _strategy(state)["standard_artifact_autopilot"] = receipt
        return receipt
    if str((s.get("final_review") or {}).get("status") or "") != "PASS":
        receipt["status"] = "DEFERRED"
        receipt["errors"] = ["final severe review PASS required before automatic final artifact materialization"]
        _strategy(state)["standard_artifact_autopilot"] = receipt
        return receipt
    caps = (s.get("runtime") or {}).get("capabilities") or {}
    if caps.get("DOCX_WRITE") != "AVAILABLE" or caps.get("DOCX_READBACK") != "AVAILABLE":
        receipt["status"] = "FAIL"
        receipt["errors"] = ["DOCX_WRITE and DOCX_READBACK must be AVAILABLE for standard artifact autopilot"]
        _strategy(state)["standard_artifact_autopilot"] = receipt
        return receipt
    lock_ok, lock_errors = pipeline_lock_gate(state)
    if not lock_ok:
        receipt["status"] = "FAIL"
        receipt["errors"] = lock_errors
        _strategy(state)["standard_artifact_autopilot"] = receipt
        return receipt

    roles = sorted(set(required_artifact_roles(mode, s.get("setup") or {})) - {"session_dashboard"})
    receipt["required_roles"] = roles
    root = _artifact_root(state)
    candidate_digest, _ = _current_candidate(state)
    errors: list[str] = []
    materialized: list[str] = []
    for role in roles:
        try:
            title, body, source_kind = _role_text(state, role)
            path = root / f"{role}.docx"
            _write_docx_atomic(path, title, body)
            _upsert_record(state, role, path, source_kind, candidate_digest)
            materialized.append(role)
        except Exception as exc:
            errors.append(f"{role}: {exc}")
            if require_all:
                continue
    receipt["materialized_roles"] = sorted(materialized)
    missing = sorted(set(roles) - set(materialized))
    if missing:
        errors.append("standard artifact roles not materialized: " + ", ".join(missing))
    receipt["errors"] = list(dict.fromkeys(errors))
    receipt["status"] = "PASS" if not receipt["errors"] else "FAIL"
    _strategy(state)["standard_artifact_autopilot"] = receipt
    return receipt


def standard_artifact_autopilot_gate(state: Any) -> tuple[bool, list[str]]:
    s = _payload(state)
    if not str(s.get("mode") or "").strip():
        return True, []
    receipt = (s.get("strategy") or {}).get("standard_artifact_autopilot") or {}
    errors: list[str] = []
    if receipt.get("schema") != SCHEMA or receipt.get("profile") != PROFILE_ID:
        errors.append("standard artifact autopilot receipt missing")
    if receipt.get("status") != "PASS":
        errors.extend(receipt.get("errors") or ["standard artifact autopilot is not PASS"])
    expected = sorted(set(required_artifact_roles(str(s.get("mode") or ""), s.get("setup") or {})) - {"session_dashboard"})
    if sorted(receipt.get("required_roles") or []) != expected:
        errors.append("standard artifact autopilot required-role set is stale")
    if sorted(receipt.get("materialized_roles") or []) != expected:
        errors.append("standard artifact autopilot did not materialize the full standard DOCX set")
    by_role = {str(item.get("role") or ""): item for item in s.get("artifacts") or [] if item.get("role")}
    for role in expected:
        item = by_role.get(role)
        if not item:
            errors.append(f"autopilot materialized role missing from artifact registry: {role}")
        elif item.get("auto_materialized_by_runtime") is not True:
            errors.append(f"standard artifact is not runtime-owned: {role}")
        elif not str(item.get("path") or "").lower().endswith(".docx"):
            errors.append(f"standard artifact is not DOCX: {role}")
    return not errors, list(dict.fromkeys(errors))
