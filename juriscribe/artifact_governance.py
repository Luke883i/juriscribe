from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from . import delivery as _delivery
from . import generation_governance as _base
from . import multimode as _multimode
from .generation_configuration import build_generation_configuration_contract, generation_conformance
from .modes import required_artifact_roles
from .plagiarism import audit_plagiarism, fingerprint_text

NARRATIVE_ARTIFACT_ROLES = frozenset({"final_chapter", "final_legal_text", "revised_legal_text", "review_report"})
ARTIFACT_GOVERNANCE_SCHEMA = "juriscribe-artifact-generation-governance/v1"


def _configuration(state) -> dict[str, Any]:
    from_contract = (state.generation_contract or {}).get("generation_configuration") or {}
    if from_contract.get("status") == "READY":
        return from_contract
    stored = (state.setup or {}).get("generation_configuration") or {}
    if stored.get("status") == "READY":
        return stored
    if (state.setup or {}).get("status") == "ACCEPTED" and ((state.setup or {}).get("accepted") or {}).get("generation_abstract"):
        derived = build_generation_configuration_contract(state.setup)
        return derived if derived.get("status") == "READY" else {}
    return {}


def apply_setup(state, overrides=None):
    """Preserve migration compatibility while governing every newly enriched setup."""
    if (state.setup or {}).get("generation_preview"):
        return _base.apply_setup(state, overrides)
    return _multimode.apply_setup(state, overrides)


def freeze_dods(state, additional_dods=None):
    if (state.setup or {}).get("generation_configuration"):
        return _base.freeze_dods(state, additional_dods)
    return _multimode.freeze_dods(state, additional_dods)


def seal_draft(state, text: str, *, stage: str = "INITIAL"):
    record = _base.seal_draft(state, text, stage=stage)
    configuration = _configuration(state)
    if configuration and str(record.get("digest") or ""):
        governance = state.strategy.setdefault("generation_governance", {})
        fingerprints = governance.setdefault("sealed_candidate_fingerprints", {})
        fingerprints[str(record["digest"])] = fingerprint_text(text, source_id=f"SEALED_{record.get('sequence', 0)}", locator_prefix="C")
    return record


def _extract_docx_text(state, record: dict[str, Any]) -> str:
    ok, errors, metadata = _delivery.verify_materialized_artifact(state, record)
    if not ok:
        raise ValueError("; ".join(errors))
    path = Path(str(metadata.get("resolved_path") or record.get("path") or ""))
    with zipfile.ZipFile(path) as package:
        info = package.getinfo("word/document.xml")
        if info.file_size > _delivery.MAX_DOCUMENT_XML_BYTES:
            raise ValueError("DOCX word/document.xml exceeds generation-governance readback limit")
        with package.open(info) as handle:
            raw = handle.read(_delivery.MAX_DOCUMENT_XML_BYTES + 1)
    if len(raw) > _delivery.MAX_DOCUMENT_XML_BYTES:
        raise ValueError("DOCX generation-governance readback exceeded safety limit")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("DOCX text extraction failed: invalid WordprocessingML") from exc
    parts: list[str] = []
    for element in root.iter():
        if str(element.tag).rsplit("}", 1)[-1] == "t" and element.text:
            parts.append(element.text)
    text = " ".join(part.strip() for part in parts if part and part.strip()).strip()
    if not text:
        raise ValueError("DOCX narrative artifact contains no extractable text")
    return text


def _candidate_binding(state, role: str, artifact_fingerprint: dict[str, Any]) -> dict[str, Any]:
    if role == "review_report":
        return {"required": False, "status": "NOT_APPLICABLE", "reason": "review report is governed directly at materialized-artifact level"}
    if not state.drafts:
        return {"required": True, "status": "FAIL", "reason": "sealed narrative candidate missing"}
    current = str(state.drafts[-1].get("digest") or "")
    expected = (((state.strategy or {}).get("generation_governance") or {}).get("sealed_candidate_fingerprints") or {}).get(current)
    if not expected:
        return {"required": True, "status": "FAIL", "reason": "sealed candidate fingerprint missing", "candidate_reference": current}
    match = str(expected.get("document_digest") or "") == str(artifact_fingerprint.get("document_digest") or "")
    return {
        "required": True,
        "status": "PASS" if match else "FAIL",
        "reason": "materialized narrative text matches sealed candidate" if match else "materialized narrative text differs from sealed candidate",
        "candidate_reference": current,
    }


def _govern_materialized_narrative(state, record: dict[str, Any], authorized_reuse=None) -> dict[str, Any]:
    role = str(record.get("role") or "")
    configuration = _configuration(state)
    if role not in NARRATIVE_ARTIFACT_ROLES or not configuration:
        return {"schema": ARTIFACT_GOVERNANCE_SCHEMA, "role": role, "status": "NOT_APPLICABLE"}
    text = _extract_docx_text(state, record)
    artifact_fingerprint = fingerprint_text(text, source_id=f"ARTIFACT_{role}", locator_prefix="A")
    conformance = generation_conformance(text, configuration)
    plagiarism = audit_plagiarism(
        text,
        references=_base._plagiarism_references(state),
        required_source_ids=_base._required_plagiarism_sources(state),
        authorized_reuse=authorized_reuse,
        sealed_candidate_digest=str(artifact_fingerprint.get("document_digest") or ""),
    )
    binding = _candidate_binding(state, role, artifact_fingerprint)
    errors: list[str] = []
    if conformance.get("status") != "PASS":
        errors.extend(conformance.get("errors") or ["materialized artifact violates generation configuration"])
    if plagiarism.get("status") != "PASS":
        errors.extend(plagiarism.get("errors") or ["materialized artifact has no anti-plagiarism proof"])
    if binding.get("status") == "FAIL":
        errors.append(str(binding.get("reason") or "materialized artifact does not match sealed candidate"))
    return {
        "schema": ARTIFACT_GOVERNANCE_SCHEMA,
        "role": role,
        "configuration_conformance": conformance,
        "plagiarism": plagiarism,
        "sealed_candidate_binding": binding,
        "word_count": int(artifact_fingerprint.get("word_count", 0) or 0),
        "status": "PASS" if not errors else "FAIL",
        "errors": list(dict.fromkeys(errors)),
    }


def record_artifact(state, record):
    prepared = dict(record)
    authorized_reuse = prepared.pop("authorized_reuse", None)
    proof = _govern_materialized_narrative(state, prepared, authorized_reuse=authorized_reuse)
    if proof.get("status") == "FAIL":
        raise ValueError("materialized artifact generation governance failed: " + "; ".join(proof.get("errors") or []))
    if proof.get("status") == "PASS":
        prepared["artifact_generation_governance"] = proof
    return _base.record_artifact(state, prepared)


def artifact_generation_governance_gate(state) -> tuple[bool, list[str]]:
    configuration = _configuration(state)
    if not configuration:
        return True, []
    expected = set(required_artifact_roles(state.mode, state.setup)) & set(NARRATIVE_ARTIFACT_ROLES)
    by_role = {str(item.get("role") or ""): item for item in state.artifacts if item.get("role")}
    errors: list[str] = []
    for role in sorted(expected):
        artifact = by_role.get(role)
        if not artifact:
            errors.append(f"narrative artifact missing generation-governance proof: {role}")
            continue
        proof = artifact.get("artifact_generation_governance") or {}
        if proof.get("status") != "PASS":
            errors.append(f"narrative artifact generation-governance proof is not PASS: {role}")
        if (proof.get("configuration_conformance") or {}).get("status") != "PASS":
            errors.append(f"materialized narrative configuration conformance is not PASS: {role}")
        if (proof.get("plagiarism") or {}).get("status") != "PASS":
            errors.append(f"materialized narrative anti-plagiarism proof is not PASS: {role}")
        binding = proof.get("sealed_candidate_binding") or {}
        if binding.get("required") and binding.get("status") != "PASS":
            errors.append(f"materialized narrative is not bound to sealed candidate: {role}")
    return not errors, list(dict.fromkeys(errors))
