from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .modes import CONTINUATION, GREENFIELD, REVIEW, normalize_mode

SCHEMA = "juriscribe-editorial-standard/v1"
STANDARD_ID = "JURISCRIBE_LEGAL_EDITORIAL_CORE_V2"
DOCUMENT_TYPES = {"LEGAL_CHAPTER", "LEGAL_MONOGRAPH", "LEGAL_ARTICLE", "LEGAL_ESSAY", "LEGAL_MEMORANDUM", "LEGAL_REPORT", "GENERIC_LEGAL_TEXT"}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def infer_document_type(request: dict[str, Any] | None, mode: str) -> str:
    text = str((request or {}).get("raw", "")).lower()
    if mode == CONTINUATION: return "LEGAL_CHAPTER"
    if "monograf" in text or "trattato" in text: return "LEGAL_MONOGRAPH"
    if "articolo" in text or "paper" in text or "saggio" in text: return "LEGAL_ARTICLE"
    if "memorandum" in text or "memo" in text or "parere" in text: return "LEGAL_MEMORANDUM"
    if "report" in text or "relazione" in text: return "LEGAL_REPORT"
    return "GENERIC_LEGAL_TEXT"


def _genre_rules(document_type: str) -> dict[str, Any]:
    base = {"formal_register": True, "stable_terminology": True, "proportional_heading_hierarchy": True, "claim_source_traceability": True, "authority_and_counterauthority": True, "temporal_jurisdiction_qualification": True, "inference_fact_separation": True, "citation_style": "PROJECT_DEFINED", "bibliography_consistency": True, "no_fabricated_authority": True, "reader_oriented_structure": True, "max_heading_density_per_1000_words": 8.0}
    if document_type == "LEGAL_MONOGRAPH": base.update({"max_heading_density_per_1000_words": 5.0, "macro_architecture_required": True, "chapter_logic_required": True})
    elif document_type == "LEGAL_CHAPTER": base.update({"max_heading_density_per_1000_words": 6.0, "interchapter_coherence_required": True})
    elif document_type == "LEGAL_ARTICLE": base.update({"abstract_policy": "PROJECT_DEFINED", "issue_thesis_conclusion_arc": True})
    elif document_type == "LEGAL_MEMORANDUM": base.update({"issue_rule_analysis_conclusion_or_equivalent": True, "executive_clarity": True})
    elif document_type == "LEGAL_REPORT": base.update({"executive_summary_policy": "PROJECT_DEFINED", "finding_recommendation_separation": True})
    return base


def resolve_editorial_standard(mode: str, setup: dict[str, Any], *, request: dict[str, Any] | None = None, mining: dict[str, Any] | None = None) -> dict[str, Any]:
    mode = normalize_mode(mode)
    accepted = setup.get("accepted", setup)
    document_type = str(accepted.get("document_type") or infer_document_type(request, mode)).upper()
    if document_type not in DOCUMENT_TYPES: document_type = "GENERIC_LEGAL_TEXT"
    rules = _genre_rules(document_type)
    rules["citation_style"] = str(accepted.get("citation_style", "PROJECT_DEFINED"))
    profile = {"schema": SCHEMA, "standard_id": STANDARD_ID, "mode": mode, "document_type": document_type, "audience": str(accepted.get("audience", "giuristi, accademici e redazioni giuridiche")), "rules": rules, "mode_adjustments": {CONTINUATION: ["preserve prior definitions and qualifications", "avoid unnecessary duplication", "maintain editorial continuity without mechanical imitation"], GREENFIELD: ["derive architecture from concept and research map", "make scope boundaries explicit", "avoid treating prompt assumptions as verified law"], REVIEW: ["distinguish diagnosis from proposed rewriting", "preserve authorial voice unless change is justified", "findings may remain open in report-only delivery"]}[mode], "source_style_profile": (mining or {}).get("style", {}), "status": "READY"}
    profile["digest"] = canonical_digest(profile)
    return profile


def validate_editorial_standard(profile: dict[str, Any] | None, *, mode: str | None = None) -> tuple[bool, list[str]]:
    if not profile: return False, ["editorial standard missing"]
    errors: list[str] = []
    if profile.get("schema") != SCHEMA: errors.append("editorial standard schema mismatch")
    if profile.get("standard_id") != STANDARD_ID: errors.append("editorial standard id mismatch")
    if profile.get("status") != "READY": errors.append("editorial standard not READY")
    if mode is not None and profile.get("mode") != normalize_mode(mode): errors.append("editorial standard mode mismatch")
    if profile.get("document_type") not in DOCUMENT_TYPES: errors.append("editorial document type invalid")
    if profile.get("digest") != canonical_digest({k: v for k, v in profile.items() if k != "digest"}): errors.append("editorial standard digest mismatch")
    return not errors, errors


def editorial_conformance(text: str, profile: dict[str, Any]) -> dict[str, Any]:
    ok, errors = validate_editorial_standard(profile)
    if not ok: return {"status": "FAIL", "errors": errors, "findings": [], "standard_digest": profile.get("digest", "")}
    words = re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'’-]+\b", text or "", flags=re.UNICODE)
    headings = [line.strip() for line in (text or "").splitlines() if re.match(r"^(?:#{1,6}\s+|\d+(?:\.\d+)*[.)]?\s+|CAPITOLO\b)", line.strip(), re.I)]
    density = len(headings) * 1000 / max(len(words), 1)
    findings: list[dict[str, Any]] = []
    if not words: findings.append({"id": "ED-NO-TEXT", "severity": "BLOCKER", "message": "testo vuoto"})
    max_density = float(profile.get("rules", {}).get("max_heading_density_per_1000_words", 8.0))
    if len(words) >= 800 and density > max_density: findings.append({"id": "ED-SECTIONING", "severity": "REVIEW", "message": "densità di heading potenzialmente eccessiva", "value": round(density, 3), "threshold": max_density})
    if len(words) >= 4000 and len(headings) == 0: findings.append({"id": "ED-STRUCTURE", "severity": "REVIEW", "message": "testo lungo privo di articolazione visibile; verificare se coerente con il genere"})
    status = "FAIL" if any(f["severity"] == "BLOCKER" for f in findings) else ("REVIEW_REQUIRED" if findings else "PASS")
    return {"status": status, "standard_id": profile["standard_id"], "standard_digest": profile["digest"], "mode": profile["mode"], "document_type": profile["document_type"], "word_count": len(words), "heading_count": len(headings), "heading_density_per_1000_words": round(density, 3), "findings": findings, "errors": []}
