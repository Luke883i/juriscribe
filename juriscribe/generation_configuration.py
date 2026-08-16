from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any

PROFILE_ID = "JURISCRIBE_GENERATION_CONFIGURATION_V1"
SCHEMA = "juriscribe-generation-configuration/v1"
WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)
STOPWORDS = {
    "anche", "che", "con", "come", "dalla", "dalle", "dello", "della", "delle", "degli", "dei", "del", "di", "e", "ed", "gli",
    "il", "in", "la", "le", "lo", "nei", "nel", "nella", "nelle", "non", "o", "per", "piu", "più", "sul", "sulla", "tra", "un", "una",
    "uno", "the", "and", "for", "from", "into", "that", "this", "with", "without", "within", "which", "will", "would",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _words(text: str) -> list[str]:
    return [word.casefold() for word in WORD_RE.findall(str(text or ""))]


def _significant_terms(text: str, *, minimum: int = 4) -> list[str]:
    return [word for word in _words(text) if len(word) >= minimum and word not in STOPWORDS and not word.isdigit()]


def _derive_key_concepts(units: list[dict[str, Any]], mining: dict[str, Any], request: dict[str, Any], *, limit: int = 6) -> list[str]:
    candidates: list[str] = []
    recurrent = ((mining or {}).get("surface") or {}).get("recurrent_terms") or []
    candidates.extend(str(item).strip().casefold() for item in recurrent if str(item).strip())
    counter: Counter[str] = Counter()
    for unit in units or []:
        if not bool(unit.get("material", True)):
            continue
        counter.update(_significant_terms(str(unit.get("text") or "")))
    counter.update(_significant_terms(str((request or {}).get("summary") or (request or {}).get("raw") or "")))
    candidates.extend(term for term, _ in counter.most_common(24))
    out: list[str] = []
    for item in candidates:
        normalized = " ".join(_words(item))
        if len(normalized) < 4 or normalized in STOPWORDS or normalized in out:
            continue
        out.append(normalized)
        if len(out) >= limit:
            break
    if not out:
        out = ["inquadramento giuridico", "fonti", "inferenza"]
    return out


def _derive_abstract(request: dict[str, Any], units: list[dict[str, Any]], key_concepts: list[str], mode: str) -> str:
    request_summary = " ".join(str((request or {}).get("summary") or (request or {}).get("raw") or "").split())
    material = [" ".join(str(unit.get("text") or "").split()) for unit in units or [] if bool(unit.get("material", True)) and str(unit.get("text") or "").strip()]
    spine = "; ".join(item[:180].rstrip(" .;:") for item in material[:2])
    concepts = ", ".join(key_concepts[:5])
    if str(mode).upper() == "REVIEW":
        prefix = "La revisione esaminerà scientificamente, logicamente ed editorialmente il testo fornito"
    elif str(mode).upper() == "CONTINUATION":
        prefix = "Il nuovo capitolo svilupperà il fronte argomentativo aperto dai capitoli precedenti"
    else:
        prefix = "Il testo svilupperà il mandato in una tesi giuridica verificabile e documentata"
    parts = [prefix]
    if request_summary:
        parts.append(f"rispetto al mandato: {request_summary[:220].rstrip(' .;:')}")
    if concepts:
        parts.append(f"con particolare attenzione a {concepts}")
    if spine:
        parts.append(f"e alla seguente dorsale epistemica: {spine}")
    return ". ".join(parts).rstrip(" .") + "."


def _review_length(mining: dict[str, Any]) -> list[int]:
    words = int(((mining or {}).get("surface") or {}).get("word_count", 0) or 0)
    if words:
        return [max(800, int(words * 0.75)), max(1400, int(words * 1.25))]
    return [1500, 4000]


def enrich_setup_proposal(
    proposal: dict[str, Any],
    *,
    request: dict[str, Any],
    units: list[dict[str, Any]],
    mining: dict[str, Any],
) -> dict[str, Any]:
    if proposal.get("status") != "USER_SETUP_REQUIRED":
        raise ValueError("generation configuration can only enrich USER_SETUP_REQUIRED proposals")
    out = dict(proposal)
    recommended = dict(out.get("recommended") or {})
    parameters = [dict(item) for item in (out.get("parameters") or [])]
    mode = str(out.get("mode") or "")
    concepts = _derive_key_concepts(units, mining, request)
    abstract = _derive_abstract(request, units, concepts, mode)
    if "length_words" not in recommended:
        recommended["length_words"] = _review_length(mining)
        parameters.append({
            "key": "length_words",
            "label": "Lunghezza",
            "recommended": recommended["length_words"],
            "rationale": "Range vincolante del prodotto generato; il runtime rifiuta candidati fuori intervallo.",
            "choices": [recommended["length_words"], [1200, 1800], [2500, 3500], [4000, 9000]],
        })
    preview_params = [
        {
            "key": "generation_abstract",
            "label": "Abstract di generazione",
            "recommended": abstract,
            "rationale": "Anticipa la tesi/funzione del prodotto e diventa parte del contratto meccanico di generazione.",
            "choices": [abstract],
        },
        {
            "key": "key_concepts",
            "label": "Concetti chiave",
            "recommended": concepts,
            "rationale": "I concetti accettati diventano obblighi di copertura verificati sul candidato finale.",
            "choices": [concepts],
        },
    ]
    existing = {str(item.get("key")) for item in parameters}
    for item in preview_params:
        recommended[item["key"]] = item["recommended"]
        if item["key"] not in existing:
            parameters.append(item)
    out["recommended"] = recommended
    out["parameters"] = parameters
    out["generation_preview"] = {
        "schema": SCHEMA,
        "abstract": abstract,
        "key_concepts": concepts,
        "length_words": recommended.get("length_words"),
        "binding": "ACCEPTANCE_CREATES_MECHANICAL_GENERATION_CONTRACT",
    }
    return out


def build_generation_configuration_contract(setup: dict[str, Any]) -> dict[str, Any]:
    accepted = dict((setup or {}).get("accepted") or {})
    abstract = " ".join(str(accepted.get("generation_abstract") or "").split())
    concepts = [" ".join(str(item).split()) for item in (accepted.get("key_concepts") or []) if str(item).strip()]
    length = accepted.get("length_words")
    errors: list[str] = []
    if not abstract:
        errors.append("accepted generation abstract is missing")
    if len(concepts) < 1:
        errors.append("at least one accepted key concept is required")
    if not (isinstance(length, (list, tuple)) and len(length) == 2):
        errors.append("accepted generation length must be a two-value range")
        lower, upper = 0, 0
    else:
        lower, upper = int(length[0]), int(length[1])
        if lower <= 0 or upper < lower:
            errors.append("accepted generation length range is invalid")
    payload = {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "abstract": abstract,
        "key_concepts": concepts,
        "length_words": [lower, upper],
        "abstract_term_coverage_min": 0.30,
        "key_concept_policy": "ALL_REQUIRED",
        "status": "READY" if not errors else "FAIL",
        "errors": errors,
    }
    payload["digest"] = canonical_digest({k: v for k, v in payload.items() if k != "digest"})
    return payload


def generation_conformance(text: str, contract: dict[str, Any] | None) -> dict[str, Any]:
    if not contract or contract.get("status") != "READY":
        return {"schema": "juriscribe-generation-conformance/v1", "status": "FAIL", "errors": ["generation configuration contract missing or not READY"]}
    words = _words(text)
    word_set = set(words)
    lower, upper = [int(x) for x in contract.get("length_words", [0, 0])]
    length_ok = lower <= len(words) <= upper
    missing: list[str] = []
    concept_evidence: dict[str, list[str]] = {}
    for concept in contract.get("key_concepts") or []:
        tokens = [token for token in _significant_terms(str(concept), minimum=3)]
        required = max(1, min(2, len(tokens)))
        present = [token for token in tokens if token in word_set]
        if len(present) < required:
            missing.append(str(concept))
        concept_evidence[str(concept)] = present
    abstract_terms = sorted(set(_significant_terms(str(contract.get("abstract") or ""))))
    matched_abstract = [term for term in abstract_terms if term in word_set]
    abstract_coverage = len(matched_abstract) / max(len(abstract_terms), 1) if abstract_terms else 1.0
    abstract_ok = abstract_coverage >= float(contract.get("abstract_term_coverage_min", 0.30))
    errors = []
    if not length_ok:
        errors.append(f"candidate length {len(words)} outside accepted range {lower}-{upper}")
    if missing:
        errors.append("accepted key concepts missing: " + ", ".join(missing))
    if not abstract_ok:
        errors.append("candidate does not satisfy minimum lexical coverage of accepted abstract")
    record = {
        "schema": "juriscribe-generation-conformance/v1",
        "configuration_digest": contract.get("digest", ""),
        "word_count": len(words),
        "accepted_length_words": [lower, upper],
        "length_status": "PASS" if length_ok else "FAIL",
        "key_concepts": concept_evidence,
        "missing_key_concepts": missing,
        "abstract_term_coverage": round(abstract_coverage, 4),
        "abstract_status": "PASS" if abstract_ok else "FAIL",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    return record


def format_generation_preview(proposal: dict[str, Any]) -> str:
    preview = proposal.get("generation_preview") or {}
    concepts = ", ".join(str(item) for item in preview.get("key_concepts") or [])
    length = preview.get("length_words") or []
    length_text = f"{length[0]}–{length[1]} parole" if isinstance(length, (list, tuple)) and len(length) == 2 else "lunghezza da definire"
    abstract = " ".join(str(preview.get("abstract") or "").split())
    return f"Abstract: {abstract} Concetti chiave: {concepts}. Lunghezza: {length_text}."
