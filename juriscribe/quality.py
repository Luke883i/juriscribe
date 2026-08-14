from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict
from typing import Any

from .mining import ARGUMENT_MARKERS, WORD_RE, SENTENCE_RE
from .sources import validate_claim

APPARATUS_MARKERS = (
    "Fonti verificate del capitolo",
    "Bibliografia",
    "Riferimenti bibliografici",
    "References",
)
HEADING_RE = re.compile(r"^(?:CAPITOLO\s+\d+|\d+(?:\.\d+)+\s+)", re.IGNORECASE)
NOTE_LINE_RE = re.compile(r"^(\d{1,3})\.\s+(.+)$")
TRAILING_NOTE_RE = re.compile(r"(?<=[.!?])\s+(\d{1,3})(?=\s|$)")


def split_document_regions(text: str) -> tuple[str, str, str | None]:
    """Split substantive body from bibliography/source apparatus.

    Style metrics MUST be computed on the substantive body only. This avoids the
    false drift observed when source lists were counted as short prose sentences.
    """
    best: tuple[int, str] | None = None
    for marker in APPARATUS_MARKERS:
        idx = text.find(marker)
        if idx >= 0 and (best is None or idx < best[0]):
            best = (idx, marker)
    if best is None:
        return text, "", None
    idx, marker = best
    return text[:idx].rstrip(), text[idx:].lstrip(), marker


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text or "")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_RE.split((text or "").strip()) if s.strip()]


def _headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if HEADING_RE.match(line.strip())]


def _density(count: int, word_count: int) -> float:
    return count * 1000.0 / max(word_count, 1)


def _relative_delta(current: float, reference: float, floor: float = 1.0) -> float:
    return abs(current - reference) / max(abs(reference), floor)


def _connector_set(text: str) -> set[str]:
    lower = text.lower()
    result: set[str] = set()
    for markers in ARGUMENT_MARKERS.values():
        for marker in markers:
            if marker in lower:
                result.add(marker)
    return result


def _jaccard_distance(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return 1.0 - len(a & b) / max(len(a | b), 1)


def style_profile(text: str) -> dict[str, Any]:
    body, _, _ = split_document_regions(text)
    words = _words(body)
    sentences = _sentences(body)
    lengths = [len(_words(s)) for s in sentences]
    ordered = sorted(lengths)
    p90 = float(ordered[min(len(ordered) - 1, max(0, math.ceil(0.9 * len(ordered)) - 1))]) if ordered else 0.0
    headings = _headings(body)
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "heading_count": len(headings),
        "avg_sentence_words": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
        "p90_sentence_words": p90,
        "heading_density_per_1000_words": round(_density(len(headings), len(words)), 3),
        "semicolon_density_per_1000_words": round(_density(body.count(";"), len(words)), 3),
        "colon_density_per_1000_words": round(_density(body.count(":"), len(words)), 3),
        "connectors": sorted(_connector_set(body)),
        "headings": headings,
    }


def compare_editorial_style(reference_text: str, candidate_text: str) -> dict[str, Any]:
    ref = style_profile(reference_text)
    cur = style_profile(candidate_text)
    deltas = {
        "avg_sentence_words": round(_relative_delta(cur["avg_sentence_words"], ref["avg_sentence_words"]), 4),
        "p90_sentence_words": round(_relative_delta(cur["p90_sentence_words"], ref["p90_sentence_words"]), 4),
        "heading_density": round(_relative_delta(cur["heading_density_per_1000_words"], ref["heading_density_per_1000_words"], 0.25), 4),
        "semicolon_density": round(_relative_delta(cur["semicolon_density_per_1000_words"], ref["semicolon_density_per_1000_words"], 0.5), 4),
        "colon_density": round(_relative_delta(cur["colon_density_per_1000_words"], ref["colon_density_per_1000_words"], 0.5), 4),
        "connector_distance": round(_jaccard_distance(set(ref["connectors"]), set(cur["connectors"])), 4),
    }
    weights = {
        "avg_sentence_words": 0.25,
        "p90_sentence_words": 0.15,
        "heading_density": 0.25,
        "semicolon_density": 0.10,
        "colon_density": 0.10,
        "connector_distance": 0.15,
    }
    weighted = sum(min(deltas[k], 2.0) * weights[k] for k in weights)
    # Sentence rhythm may vary by topic. Structural segmentation is treated more
    # strictly because excessive sectioning is a common AI editorial drift.
    checks = [
        {"id": "STYLE-SENTENCE-MEAN", "status": "PASS" if deltas["avg_sentence_words"] <= 0.25 else "REVIEW", "value": deltas["avg_sentence_words"]},
        {"id": "STYLE-SENTENCE-P90", "status": "PASS" if deltas["p90_sentence_words"] <= 0.30 else "REVIEW", "value": deltas["p90_sentence_words"]},
        {"id": "STYLE-SECTIONING", "status": "PASS" if deltas["heading_density"] <= 0.75 else "REVIEW", "value": deltas["heading_density"]},
        {"id": "STYLE-CONNECTORS", "status": "PASS" if deltas["connector_distance"] <= 0.65 else "REVIEW", "value": deltas["connector_distance"]},
    ]
    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "REVIEW_REQUIRED"
    return {"reference": ref, "candidate": cur, "deltas": deltas, "weighted_distance": round(weighted, 4), "checks": checks, "status": status}


def analyze_reference_apparatus(text: str) -> dict[str, Any]:
    body, apparatus, marker = split_document_regions(text)
    declared: dict[int, str] = {}
    for line in apparatus.splitlines():
        m = NOTE_LINE_RE.match(line.strip())
        if m:
            declared[int(m.group(1))] = m.group(2).strip()
    used: list[int] = []
    for line in body.splitlines():
        for raw in TRAILING_NOTE_RE.findall(line):
            n = int(raw)
            if n in declared:
                used.append(n)
    unique_used = sorted(set(used))
    unused = sorted(set(declared) - set(unique_used))
    missing = sorted(set(unique_used) - set(declared))
    return {
        "marker": marker,
        "declared_source_count": len(declared),
        "used_source_count": len(unique_used),
        "callout_count": len(used),
        "coverage": round(len(unique_used) / max(len(declared), 1), 4) if declared else 0.0,
        "declared_source_numbers": sorted(declared),
        "used_source_numbers": unique_used,
        "unused_source_numbers": unused,
        "missing_source_numbers": missing,
        "status": "PASS" if declared and not unused and not missing else "REVIEW_REQUIRED",
    }


def claim_traceability(claims: list[dict[str, Any]], sources: list[dict[str, Any]], artifact_evidence: list[dict[str, Any]]) -> dict[str, Any]:
    source_ids = {s.get("id") for s in sources}
    by_claim = {e.get("claim_id"): e for e in artifact_evidence if e.get("claim_id")}
    material = [c for c in claims if c.get("material", True)]
    errors: dict[str, list[str]] = {}
    visible = 0
    for claim in material:
        cid = claim.get("id", "UNKNOWN")
        ok, claim_errors = validate_claim(claim, sources, claims)
        ev = by_claim.get(cid)
        if not ev:
            claim_errors.append("material claim has no artifact locator")
        else:
            locator = str(ev.get("artifact_locator", "")).strip()
            if not locator:
                claim_errors.append("artifact locator is empty")
            ev_sources = set(ev.get("source_ids", []))
            if any(sid not in source_ids for sid in ev_sources):
                claim_errors.append("artifact evidence references unknown source")
            if locator and not claim_errors:
                visible += 1
        if not ok or claim_errors:
            errors[cid] = claim_errors
    return {
        "material_claims": len(material),
        "fully_traceable_claims": visible,
        "coverage": round(visible / max(len(material), 1), 4) if material else 1.0,
        "errors": errors,
        "status": "PASS" if not errors else "GAPS_OPEN",
    }


@dataclass(frozen=True)
class ChapterQualityReport:
    status: str
    blocking_failures: list[str]
    review_items: list[str]
    body_word_count: int
    apparatus_word_count: int
    length_status: str
    style: dict[str, Any]
    reference_apparatus: dict[str, Any]
    claim_traceability: dict[str, Any]
    notes: list[str]

    def record(self) -> dict[str, Any]:
        return asdict(self)


def audit_chapter(
    text: str,
    *,
    reference_text: str | None = None,
    accepted_setup: dict[str, Any] | None = None,
    claims: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
    artifact_evidence: list[dict[str, Any]] | None = None,
) -> ChapterQualityReport:
    body, apparatus, _ = split_document_regions(text)
    body_words = len(_words(body))
    apparatus_words = len(_words(apparatus))
    setup = (accepted_setup or {}).get("accepted", accepted_setup or {})
    expected_length = setup.get("length_words")
    length_status = "NOT_CONSTRAINED"
    blocking: list[str] = []
    review: list[str] = []
    notes: list[str] = []
    if isinstance(expected_length, (list, tuple)) and len(expected_length) == 2:
        lo, hi = int(expected_length[0]), int(expected_length[1])
        length_status = "PASS" if lo <= body_words <= hi else "FAIL"
        if length_status == "FAIL":
            blocking.append(f"body length {body_words} outside accepted range {lo}-{hi}")
    style = compare_editorial_style(reference_text, body) if reference_text else {"status": "NOT_EVALUATED", "checks": []}
    if style.get("status") == "REVIEW_REQUIRED":
        review.append("style continuity requires editorial review")
    apparatus_report = analyze_reference_apparatus(text)
    # A source appendix with all declared references used is valid evidence of
    # reader-visible grounding. It is not equivalent to claim-level pinpointing.
    if apparatus_report["status"] == "PASS":
        notes.append("source apparatus is visible and internally referenced")
    elif apparatus_report["declared_source_count"]:
        review.append("source apparatus has unused or unresolved references")
    trace = claim_traceability(claims or [], sources or [], artifact_evidence or []) if claims is not None else {"status": "NOT_EVALUATED", "coverage": None, "errors": {}}
    if trace.get("status") == "GAPS_OPEN":
        blocking.append("material claim-to-source-to-artifact traceability is incomplete")
    status = "FAIL" if blocking else ("REVIEW_REQUIRED" if review else "PASS")
    return ChapterQualityReport(status, blocking, review, body_words, apparatus_words, length_status, style, apparatus_report, trace, notes)
