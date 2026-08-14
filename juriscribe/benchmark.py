from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tokens(text: str) -> set[str]:
    stop = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "as"}
    return {t.lower() for t in WORD_RE.findall(text or "") if t.lower() not in stop}


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / max(len(ta | tb), 1)


def _match_headings(actual: list[str], generated: list[str], threshold: float = 0.45) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    remaining = set(range(len(generated)))
    matches: list[dict[str, Any]] = []
    missing: list[str] = []
    for a in actual:
        best_i = None
        best_score = 0.0
        for i in remaining:
            score = _similarity(a, generated[i])
            if score > best_score:
                best_score, best_i = score, i
        if best_i is not None and best_score >= threshold:
            matches.append({"actual": a, "generated": generated[best_i], "similarity": round(best_score, 4)})
            remaining.remove(best_i)
        else:
            missing.append(a)
    extra = [generated[i] for i in sorted(remaining)]
    return matches, missing, extra


@dataclass(frozen=True)
class BenchmarkChapter:
    id: str
    title: str
    role: str
    headings: list[str]
    summary: str = ""

    def record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BlindBenchmarkEnvelope:
    benchmark_id: str
    monograph: str
    author: str
    domain: str
    context_digest: str
    hidden_reference_commitment: str
    generated: dict[str, Any]
    generated_digest: str
    generated_sealed_at: str
    protocol: str = "hidden reference content unavailable to generator; only SHA-256 commitment may be present before generation"
    actual: dict[str, Any] | None = None
    revealed_at: str | None = None
    commitment_verified: bool | None = None
    score: dict[str, Any] | None = None

    @classmethod
    def seal_generation(
        cls,
        *,
        monograph: str,
        author: str,
        domain: str,
        prior_context: list[dict[str, Any]],
        hidden_reference_commitment: str,
        generated: BenchmarkChapter,
    ) -> "BlindBenchmarkEnvelope":
        context_digest = canonical_digest(prior_context)
        generated_record = generated.record()
        benchmark_id = hashlib.sha256((monograph + context_digest + hidden_reference_commitment).encode("utf-8")).hexdigest()[:16]
        return cls(
            benchmark_id=benchmark_id,
            monograph=monograph,
            author=author,
            domain=domain,
            context_digest=context_digest,
            hidden_reference_commitment=hidden_reference_commitment,
            generated=generated_record,
            generated_digest=canonical_digest(generated_record),
            generated_sealed_at=_now(),
        )

    def reveal(self, actual: BenchmarkChapter) -> dict[str, Any]:
        actual_record = actual.record()
        actual_digest = canonical_digest(actual_record)
        self.commitment_verified = actual_digest == self.hidden_reference_commitment
        self.actual = actual_record
        self.revealed_at = _now()
        matches, missing, extra = _match_headings(actual.headings, self.generated.get("headings", []))
        recall = len(matches) / max(len(actual.headings), 1)
        precision = len(matches) / max(len(self.generated.get("headings", [])), 1)
        self.score = {
            "heading_recall_soft": round(recall, 4),
            "heading_precision_soft": round(precision, 4),
            "matched": matches,
            "missing_from_generation": missing,
            "extra_generated": extra,
            "blind_integrity": "PASS" if self.commitment_verified else "FAIL",
            "interpretation": "structural benchmark only; does not prove legal correctness or model ignorance beyond the external commitment protocol",
        }
        return self.record()

    def record(self) -> dict[str, Any]:
        return asdict(self)


def benchmark_gate(record: dict[str, Any] | None, *, required: bool = False) -> dict[str, Any]:
    if not required:
        return {"required": False, "status": "NOT_REQUIRED", "eligible": True}
    if not record:
        return {"required": True, "status": "MISSING", "eligible": False}
    score = record.get("score") or {}
    integrity = score.get("blind_integrity") == "PASS"
    recall = float(score.get("heading_recall_soft", 0.0) or 0.0)
    # Benchmark quality is not a legal-truth gate. We only require integrity and
    # a minimum structural signal when Juriscribe claims monographic extrapolation.
    eligible = integrity and recall >= 0.50
    return {"required": True, "status": "PASS" if eligible else "FAIL", "eligible": eligible, "integrity": integrity, "recall": recall}
