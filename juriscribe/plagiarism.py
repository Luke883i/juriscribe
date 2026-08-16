from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

POLICY_ID = "JURISCRIBE_ANTI_PLAGIARISM_V1"
SCHEMA = "juriscribe-plagiarism-audit/v1"
FINGERPRINT_SCHEMA = "juriscribe-plagiarism-fingerprint/v1"
WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)
APPARATUS_MARKERS = ("Fonti verificate del capitolo", "Bibliografia", "Riferimenti bibliografici", "References")
EXACT_N = 12
SHINGLE_N = 5
NEAR_MIN_WORDS = 24
NEAR_THRESHOLD = 0.72


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _words(text: str) -> list[str]:
    return [word.casefold() for word in WORD_RE.findall(str(text or ""))]


def _hash_tokens(tokens: Iterable[str]) -> str:
    return hashlib.sha256(" ".join(tokens).encode("utf-8")).hexdigest()


def _body(text: str) -> str:
    raw = str(text or "")
    positions = [raw.find(marker) for marker in APPARATUS_MARKERS if raw.find(marker) >= 0]
    return raw[: min(positions)].rstrip() if positions else raw


def _segments(text: str) -> list[str]:
    body = _body(text)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
    return paragraphs or ([body.strip()] if body.strip() else [])


def fingerprint_text(text: str, *, source_id: str, locator_prefix: str = "P") -> dict[str, Any]:
    records = []
    normalized_document_words: list[str] = []
    for index, segment in enumerate(_segments(text), 1):
        words = _words(segment)
        normalized_document_words.extend(words)
        if not words:
            continue
        exact = sorted({_hash_tokens(words[i:i + EXACT_N]) for i in range(max(0, len(words) - EXACT_N + 1))})
        shingles = sorted({_hash_tokens(words[i:i + SHINGLE_N]) for i in range(max(0, len(words) - SHINGLE_N + 1))})
        records.append({
            "source_id": str(source_id),
            "locator": f"{locator_prefix}{index}",
            "word_count": len(words),
            "segment_digest": _hash_tokens(words),
            "exact_ngram_hashes": exact,
            "shingle_hashes": shingles,
        })
    payload = {
        "schema": FINGERPRINT_SCHEMA,
        "source_id": str(source_id),
        "word_count": len(normalized_document_words),
        "document_digest": _hash_tokens(normalized_document_words),
        "exact_n": EXACT_N,
        "shingle_n": SHINGLE_N,
        "segments": records,
        "status": "READY",
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def fingerprint_evidence_passages(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for claim in claims or []:
        for evidence in claim.get("source_evidence") or []:
            source_id = str(evidence.get("source_id") or "").strip()
            text = str(evidence.get("verbatim") or evidence.get("quote") or evidence.get("proposition") or "").strip()
            if source_id and text:
                grouped.setdefault(source_id, []).append(text)
    return [fingerprint_text("\n\n".join(parts), source_id=source_id, locator_prefix="E") for source_id, parts in sorted(grouped.items())]


def default_policy() -> dict[str, Any]:
    payload = {
        "policy_id": POLICY_ID,
        "exact_sequence_words": EXACT_N,
        "near_match_shingle_words": SHINGLE_N,
        "near_match_min_words": NEAR_MIN_WORDS,
        "near_match_threshold": NEAR_THRESHOLD,
        "authorized_reuse_requires_attribution": True,
        "runtime_visible_reference_coverage_required": True,
        "unattributed_verbatim_reuse": "FORBIDDEN",
        "unattributed_near_verbatim_reuse": "FORBIDDEN",
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def _authorized_maps(authorized_reuse: list[dict[str, Any]] | None) -> tuple[dict[str, set[str]], list[dict[str, Any]], list[str]]:
    exact_by_source: dict[str, set[str]] = {}
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, raw in enumerate(authorized_reuse or [], 1):
        source_id = str(raw.get("source_id") or "").strip()
        text = str(raw.get("text") or "").strip()
        attribution = str(raw.get("attribution_locator") or "").strip()
        if not source_id or not text or not attribution:
            errors.append(f"authorized reuse {index} requires source_id, text and attribution_locator")
            continue
        fp = fingerprint_text(text, source_id=source_id, locator_prefix="A")
        hashes = {item for segment in fp["segments"] for item in segment.get("exact_ngram_hashes", [])}
        exact_by_source.setdefault(source_id, set()).update(hashes)
        records.append({
            "source_id": source_id,
            "authorized_text_digest": fp["document_digest"],
            "attribution_locator": attribution,
            "kind": str(raw.get("kind") or "QUOTATION"),
            "rationale": str(raw.get("rationale") or "explicit attributed reuse"),
        })
    return exact_by_source, records, errors


def audit_plagiarism(
    text: str,
    *,
    references: list[dict[str, Any]],
    required_source_ids: set[str] | None = None,
    authorized_reuse: list[dict[str, Any]] | None = None,
    sealed_candidate_digest: str = "",
) -> dict[str, Any]:
    policy = default_policy()
    candidate = fingerprint_text(text, source_id="CANDIDATE", locator_prefix="C")
    reference_map: dict[str, dict[str, Any]] = {}
    for raw in references or []:
        if raw.get("schema") == FINGERPRINT_SCHEMA:
            fp = dict(raw)
        else:
            source_id = str(raw.get("source_id") or raw.get("id") or "").strip()
            fp = fingerprint_text(str(raw.get("text") or ""), source_id=source_id, locator_prefix=str(raw.get("locator_prefix") or "R"))
        source_id = str(fp.get("source_id") or "").strip()
        if source_id:
            reference_map[source_id] = fp
    required = {str(item) for item in (required_source_ids or set()) if str(item)}
    available = set(reference_map)
    missing = sorted(required - available)
    authorized_exact, authorized_records, authorization_errors = _authorized_maps(authorized_reuse)

    findings: list[dict[str, Any]] = []
    exact_index: dict[str, list[tuple[str, str]]] = {}
    reference_segments: list[tuple[str, dict[str, Any]]] = []
    for source_id, fp in reference_map.items():
        for segment in fp.get("segments") or []:
            reference_segments.append((source_id, segment))
            for digest in segment.get("exact_ngram_hashes") or []:
                exact_index.setdefault(digest, []).append((source_id, str(segment.get("locator") or "")))

    pair_counts: dict[tuple[str, str, str], dict[str, Any]] = {}
    for segment in candidate.get("segments") or []:
        candidate_locator = str(segment.get("locator") or "")
        for digest in segment.get("exact_ngram_hashes") or []:
            for source_id, source_locator in exact_index.get(digest, []):
                authorized = digest in authorized_exact.get(source_id, set())
                key = (candidate_locator, source_id, source_locator)
                bucket = pair_counts.setdefault(key, {"matched_exact_ngrams": 0, "authorized_exact_ngrams": 0})
                bucket["matched_exact_ngrams"] += 1
                if authorized:
                    bucket["authorized_exact_ngrams"] += 1
    fully_authorized_pairs: set[tuple[str, str, str]] = set()
    for (candidate_locator, source_id, source_locator), counts in sorted(pair_counts.items()):
        unauthorized = counts["matched_exact_ngrams"] - counts["authorized_exact_ngrams"]
        if counts["matched_exact_ngrams"] > 0 and unauthorized == 0:
            fully_authorized_pairs.add((candidate_locator, source_id, source_locator))
        if unauthorized > 0:
            findings.append({
                "kind": "UNATTRIBUTED_EXACT_OVERLAP",
                "candidate_locator": candidate_locator,
                "source_id": source_id,
                "source_locator": source_locator,
                "matched_exact_ngrams": counts["matched_exact_ngrams"],
                "authorized_exact_ngrams": counts["authorized_exact_ngrams"],
                "status": "BLOCKER",
            })

    exact_pairs = {(item["candidate_locator"], item["source_id"], item["source_locator"]) for item in findings}
    for candidate_segment in candidate.get("segments") or []:
        c_shingles = set(candidate_segment.get("shingle_hashes") or [])
        if int(candidate_segment.get("word_count", 0)) < NEAR_MIN_WORDS or not c_shingles:
            continue
        for source_id, source_segment in reference_segments:
            if int(source_segment.get("word_count", 0)) < NEAR_MIN_WORDS:
                continue
            key = (str(candidate_segment.get("locator") or ""), source_id, str(source_segment.get("locator") or ""))
            if key in exact_pairs or key in fully_authorized_pairs:
                continue
            s_shingles = set(source_segment.get("shingle_hashes") or [])
            if not s_shingles:
                continue
            similarity = len(c_shingles & s_shingles) / max(len(c_shingles | s_shingles), 1)
            if similarity >= NEAR_THRESHOLD:
                findings.append({
                    "kind": "UNATTRIBUTED_NEAR_VERBATIM_OVERLAP",
                    "candidate_locator": key[0],
                    "source_id": source_id,
                    "source_locator": key[2],
                    "similarity": round(similarity, 4),
                    "status": "BLOCKER",
                })

    errors = list(authorization_errors)
    if missing:
        errors.append("plagiarism comparison scope missing source ids: " + ", ".join(missing))
    if findings:
        errors.append("unattributed verbatim or near-verbatim overlap detected")
    manifest = [
        {"source_id": source_id, "document_digest": fp.get("document_digest", ""), "word_count": fp.get("word_count", 0), "fingerprint_digest": fp.get("digest", "")}
        for source_id, fp in sorted(reference_map.items())
    ]
    record = {
        "schema": SCHEMA,
        "policy": policy,
        "candidate_digest": candidate.get("document_digest", ""),
        "sealed_candidate_digest": sealed_candidate_digest,
        "candidate_fingerprint_digest": candidate.get("digest", ""),
        "reference_manifest": manifest,
        "required_source_ids": sorted(required),
        "covered_source_ids": sorted(available & required if required else available),
        "missing_source_ids": missing,
        "authorized_reuse": authorized_records,
        "findings": findings,
        "prohibited_findings": len(findings),
        "scope_status": "COMPLETE_FOR_RUNTIME_VISIBLE_CORPUS" if not missing else "INCOMPLETE",
        "proof_statement": "No prohibited verbatim or near-verbatim overlap was detected within the registered runtime-visible comparison corpus." if not findings and not missing else "Anti-plagiarism proof not established for this candidate.",
        "global_uniqueness_claim": False,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    return record


def plagiarism_gate(record: dict[str, Any] | None, *, sealed_candidate_digest: str | None = None, policy_digest: str | None = None) -> tuple[bool, list[str]]:
    if not record:
        return False, ["plagiarism audit receipt missing"]
    errors = list(record.get("errors") or [])
    if record.get("schema") != SCHEMA:
        errors.append("plagiarism audit schema mismatch")
    if record.get("status") != "PASS":
        errors.append("plagiarism audit is not PASS")
    if record.get("scope_status") != "COMPLETE_FOR_RUNTIME_VISIBLE_CORPUS":
        errors.append("plagiarism comparison scope is incomplete")
    if int(record.get("prohibited_findings", 0)) != 0:
        errors.append("plagiarism audit contains prohibited overlaps")
    if sealed_candidate_digest is not None and record.get("sealed_candidate_digest") != sealed_candidate_digest:
        errors.append("plagiarism audit bound to stale sealed candidate")
    if policy_digest is not None and (record.get("policy") or {}).get("digest") != policy_digest:
        errors.append("plagiarism audit policy mismatch")
    expected = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    if record.get("digest") != expected:
        errors.append("plagiarism audit digest mismatch")
    return not errors, list(dict.fromkeys(errors))
