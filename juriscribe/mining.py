from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

SENTENCE_RE = re.compile(r"(?<=[.!?;:])\s+")
WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)
HEADING_RE = re.compile(r"(?m)^(?:CAPITOLO|Capitolo|§|\d+(?:\.\d+)*\s+)[^\n]{2,120}$")
CITATION_MARKERS = ("art.", "artt.", "Cass.", "Cons. Stato", "Corte cost.", "CGUE", "CEDU", "v.", "cfr.")
ARGUMENT_MARKERS = {
    "premise": ("anzitutto", "in primo luogo", "muovendo da", "premesso che"),
    "contrast": ("tuttavia", "peraltro", "nondimeno", "viceversa", "eppure"),
    "consequence": ("pertanto", "dunque", "ne consegue", "sicché", "cosicché"),
    "qualification": ("salvo", "purché", "nei limiti", "a condizione", "fermo restando"),
    "synthesis": ("in definitiva", "in conclusione", "in sintesi", "può dunque"),
}


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_RE.split(text.strip()) if s.strip()]


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _ratio(n: int, d: int) -> float:
    return round(n / d, 4) if d else 0.0


def _percentile(values: list[int], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil(p * len(ordered)) - 1))
    return float(ordered[idx])


@dataclass(frozen=True)
class StyleFingerprint:
    words: int
    sentences: int
    paragraphs: int
    headings: int
    avg_sentence_words: float
    p90_sentence_words: float
    avg_paragraph_words: float
    citation_density_per_1000_words: float
    semicolon_density_per_1000_words: float
    parenthetical_density_per_1000_words: float
    first_person_density_per_1000_words: float
    argument_markers: dict[str, int]
    dominant_connectors: list[str]
    register: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


def mine_style(text: str) -> StyleFingerprint:
    words = _words(text)
    sentences = _sentences(text)
    paragraphs = _paragraphs(text)
    sentence_lengths = [len(_words(s)) for s in sentences]
    paragraph_lengths = [len(_words(p)) for p in paragraphs]
    lower = text.lower()
    marker_counts = {kind: sum(lower.count(marker) for marker in markers) for kind, markers in ARGUMENT_MARKERS.items()}
    connector_counter = Counter()
    for markers in ARGUMENT_MARKERS.values():
        for marker in markers:
            count = lower.count(marker)
            if count:
                connector_counter[marker] = count
    citations = sum(text.count(marker) for marker in CITATION_MARKERS)
    first_person = len(re.findall(r"\b(?:ritengo|riteniamo|osservo|osserviamo|sostengo|sosteniamo)\b", lower))
    long_sentence_ratio = _ratio(sum(1 for n in sentence_lengths if n >= 35), len(sentence_lengths))
    register = "giuridico-denso" if citations or long_sentence_ratio >= 0.25 else "saggistico-argomentativo"
    return StyleFingerprint(
        words=len(words), sentences=len(sentences), paragraphs=len(paragraphs), headings=len(HEADING_RE.findall(text)),
        avg_sentence_words=round(sum(sentence_lengths) / len(sentence_lengths), 2) if sentence_lengths else 0.0,
        p90_sentence_words=_percentile(sentence_lengths, 0.9),
        avg_paragraph_words=round(sum(paragraph_lengths) / len(paragraph_lengths), 2) if paragraph_lengths else 0.0,
        citation_density_per_1000_words=round(_ratio(citations * 1000, len(words)), 2),
        semicolon_density_per_1000_words=round(_ratio(text.count(";") * 1000, len(words)), 2),
        parenthetical_density_per_1000_words=round(_ratio((text.count("(") + text.count("—")) * 1000, len(words)), 2),
        first_person_density_per_1000_words=round(_ratio(first_person * 1000, len(words)), 2),
        argument_markers=marker_counts, dominant_connectors=[k for k, _ in connector_counter.most_common(8)], register=register,
    )


def source_anchors(text: str) -> list[dict[str, Any]]:
    """Deterministic paragraph anchors used by host semantic atomization."""
    anchors = []
    for idx, paragraph in enumerate(_paragraphs(text), start=1):
        digest = __import__("hashlib").sha256(paragraph.encode("utf-8")).hexdigest()[:12]
        anchors.append({"locator": f"P{idx}", "sha256_12": digest, "word_count": len(_words(paragraph)), "preview": paragraph[:220]})
    return anchors


def deep_mine(text: str, *, source_id: str, chapter: str | None = None, semantic_annotations: dict[str, Any] | None = None) -> dict[str, Any]:
    style = mine_style(text)
    words = _words(text)
    lower = text.lower()
    legal_terms = Counter(w.lower() for w in words if len(w) >= 7)
    recurrent = [term for term, count in legal_terms.most_common(40) if count >= 2][:20]
    qualifications = [m for m in ("salvo", "nei limiti", "purché", "fermo restando", "tuttavia", "peraltro") if m in lower]
    questions = [s for s in _sentences(text) if "?" in s]
    return {
        "source_id": source_id,
        "chapter": chapter,
        "surface": {
            "word_count": style.words,
            "paragraph_count": style.paragraphs,
            "heading_count": style.headings,
            "recurrent_terms": recurrent,
            "qualification_markers": qualifications,
            "explicit_questions": questions[:20],
            "anchors": source_anchors(text),
        },
        "style": style.record(),
        "semantic": semantic_annotations or {},
        "mining_status": "DETERMINISTIC_PLUS_HOST_SEMANTIC" if semantic_annotations else "SEMANTIC_ATOMIZATION_REQUIRED",
    }


def compare_style(reference: dict[str, Any], candidate_text: str) -> dict[str, Any]:
    candidate = mine_style(candidate_text).record()
    numeric_keys = [
        "avg_sentence_words", "p90_sentence_words", "avg_paragraph_words",
        "citation_density_per_1000_words", "semicolon_density_per_1000_words",
        "parenthetical_density_per_1000_words", "first_person_density_per_1000_words",
    ]
    deviations = {}
    for key in numeric_keys:
        ref = float(reference.get(key, 0.0) or 0.0)
        cur = float(candidate.get(key, 0.0) or 0.0)
        deviations[key] = round(abs(cur - ref) / max(abs(ref), 1.0), 4)
    return {
        "candidate": candidate,
        "deviations": deviations,
        "mean_relative_deviation": round(sum(deviations.values()) / len(deviations), 4),
        "register_match": candidate.get("register") == reference.get("register"),
    }
