from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable

STANDARD_ID = "JURISCRIBE_LEGAL_MONOGRAPH_V1"
REVIEW_SATURATION_TARGET = 10000

# A publisher-neutral core synthesized from convergent legal-academic publishing
# practices. Citation syntax itself remains configurable by the editorial project.
REVIEW_CRITERIA: dict[str, dict[str, Any]] = {
    "MONOGRAPHIC_CONTRIBUTION": {
        "label": "Contributo al progetto monografico",
        "question": "Il capitolo sviluppa una funzione necessaria dell'opera e distingue il proprio contributo da quanto già svolto?",
        "blocking": True,
    },
    "INTERCHAPTER_COHERENCE": {
        "label": "Coerenza fra capitoli",
        "question": "Tesi, definizioni, rinvii, dipendenze e anticipazioni sono coerenti con i capitoli precedenti?",
        "blocking": True,
    },
    "LEGAL_AUTHORITY": {
        "label": "Autorità giuridiche",
        "question": "I claim giuridici materiali sono sostenuti da autorità adeguate, lette e circostanziate?",
        "blocking": True,
    },
    "CITATION_TRACEABILITY": {
        "label": "Tracciabilità delle citazioni",
        "question": "Il lettore può risalire da ogni claim materiale a fonte, pinpoint e posizione nell'artefatto?",
        "blocking": True,
    },
    "COUNTERAUTHORITY": {
        "label": "Controautorità e obiezioni",
        "question": "Le autorità contrarie e le obiezioni materialmente rilevanti sono identificate, non occultate e trattate?",
        "blocking": True,
    },
    "TEMPORAL_JURISDICTION": {
        "label": "Perimetro temporale e giurisdizionale",
        "question": "Regole, casi e dottrina sono qualificati per tempo, giurisdizione e stato di vigenza quando necessario?",
        "blocking": True,
    },
    "INFERENCE_DISCIPLINE": {
        "label": "Disciplina inferenziale",
        "question": "Le inferenze forti sono distinte dai fatti attestati e hanno premesse, ponte e falsificatore?",
        "blocking": True,
    },
    "TERMINOLOGY": {
        "label": "Coerenza terminologica",
        "question": "Definizioni e termini tecnici restano stabili o le variazioni sono motivate?",
        "blocking": True,
    },
    "STRUCTURE": {
        "label": "Architettura e progressione",
        "question": "La struttura è proporzionata, non frammentata artificialmente e conduce dalle premesse alle conclusioni?",
        "blocking": False,
    },
    "EDITORIAL_STYLE": {
        "label": "Continuità editoriale",
        "question": "Registro, densità, ritmo, sintassi e livello di formalità sono coerenti con l'opera senza imitazione meccanica?",
        "blocking": False,
    },
    "BIBLIOGRAPHY_INTEGRITY": {
        "label": "Integrità bibliografica",
        "question": "Le opere citate sono inventariate, coerenti con i richiami e verificate quando usate come supporto materiale?",
        "blocking": True,
    },
    "LOSSLESS_PRESERVATION": {
        "label": "Preservazione epistemica",
        "question": "Tesi, regole, eccezioni, qualificazioni e dipendenze obbligatorie sono preservate o trasformate con tracciabilità?",
        "blocking": True,
    },
    "AUDIENCE_FIT": {
        "label": "Adeguatezza al lettore",
        "question": "Il capitolo è leggibile e utile per il pubblico giuridico/scientifico dichiarato?",
        "blocking": False,
    },
}

ALLOWED_SEVERITIES = {"BLOCKER", "MAJOR", "MINOR", "NOTE"}
ALLOWED_FINDING_STATUS = {"OPEN", "ADDRESSED", "ACCEPTED_RISK", "HUMAN_DECISION_REQUIRED"}


ALLOWED_REVIEW_EVIDENCE_TYPES = {"reticulum", "source", "artifact", "comparison", "bibliography", "inference", "editorial_metric", "human_decision"}

def validate_review_evidence(evidence: list[dict[str, Any]] | None) -> tuple[bool, list[str]]:
    evidence = list(evidence or [])
    errors: list[str] = []
    covered: set[str] = set()
    for idx, item in enumerate(evidence):
        criterion = item.get("criterion")
        if criterion not in REVIEW_CRITERIA:
            errors.append(f"review evidence {idx} has unknown criterion")
            continue
        etype = item.get("evidence_type")
        if etype not in ALLOWED_REVIEW_EVIDENCE_TYPES:
            errors.append(f"review evidence {idx} has invalid evidence_type")
        status = item.get("status", "VERIFIED")
        if status not in {"VERIFIED", "NOT_APPLICABLE"}:
            errors.append(f"review evidence {idx} has invalid status")
        locator = str(item.get("locator", "")).strip()
        rationale = str(item.get("rationale", "")).strip()
        if status == "VERIFIED" and not locator:
            errors.append(f"review evidence {idx} has no locator")
        if status == "NOT_APPLICABLE" and not rationale:
            errors.append(f"review evidence {idx} marks NOT_APPLICABLE without rationale")
        covered.add(str(criterion))
    missing = [criterion for criterion in REVIEW_CRITERIA if criterion not in covered]
    if missing:
        errors.append("review evidence missing criteria: " + ", ".join(missing))
    return not errors, errors


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def review_standard_profile(*, citation_style: str = "PROJECT_DEFINED") -> dict[str, Any]:
    criteria = [
        {"id": key, **value}
        for key, value in REVIEW_CRITERIA.items()
    ]
    profile = {
        "standard_id": STANDARD_ID,
        "citation_style": citation_style,
        "criteria": criteria,
        "minimum_score": 0.80,
        "blocking_score": 0.90,
        "policy": "blocking criteria must have no unresolved BLOCKER/MAJOR findings; style syntax is project-defined but evidence integrity is invariant",
    }
    profile["digest"] = canonical_digest(profile)
    return profile


def _finding_signature(finding: dict[str, Any]) -> str:
    return canonical_digest({
        "criterion": finding.get("criterion"),
        "severity": finding.get("severity"),
        "kind": finding.get("kind"),
        "artifact_locator": finding.get("artifact_locator"),
        "epistemic_unit_ids": sorted(finding.get("epistemic_unit_ids", [])),
        "source_ids": sorted(finding.get("source_ids", [])),
    })


def validate_findings(findings: Iterable[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        fid = str(finding.get("id", "")).strip()
        if not fid:
            errors.append("review finding id missing")
            continue
        if fid in seen:
            errors.append(f"duplicate review finding id {fid}")
        seen.add(fid)
        if finding.get("criterion") not in REVIEW_CRITERIA:
            errors.append(f"review finding {fid} uses unknown criterion")
        if finding.get("severity") not in ALLOWED_SEVERITIES:
            errors.append(f"review finding {fid} uses invalid severity")
        if finding.get("status", "OPEN") not in ALLOWED_FINDING_STATUS:
            errors.append(f"review finding {fid} uses invalid status")
        if finding.get("severity") in {"BLOCKER", "MAJOR"} and not str(finding.get("artifact_locator", "")).strip():
            errors.append(f"review finding {fid} has no artifact locator")
        if finding.get("severity") in {"BLOCKER", "MAJOR"} and not str(finding.get("proposed_action", "")).strip():
            errors.append(f"review finding {fid} has no proposed action")
    return not errors, errors


def validate_scorecard(scorecard: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    missing = [criterion for criterion in REVIEW_CRITERIA if criterion not in scorecard]
    if missing:
        errors.append("review scorecard missing criteria: " + ", ".join(missing))
    for key, raw in scorecard.items():
        if key not in REVIEW_CRITERIA:
            errors.append(f"review scorecard has unknown criterion {key}")
            continue
        try:
            score = float(raw)
        except (TypeError, ValueError):
            errors.append(f"review score {key} is not numeric")
            continue
        if not 0.0 <= score <= 1.0:
            errors.append(f"review score {key} outside 0..1")
    return not errors, errors


@dataclass(frozen=True)
class ReviewCycleRecord:
    cycle: int
    candidate_digest: str
    standard_id: str
    standard_digest: str
    findings: list[dict[str, Any]]
    scorecard: dict[str, float]
    evidence_digest: str
    evidence_count: int
    citation_style: str
    open_blockers: int
    open_majors: int
    status: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


def build_review_cycle(
    *,
    cycle: int,
    candidate_digest: str,
    findings: list[dict[str, Any]],
    scorecard: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
    citation_style: str = "PROJECT_DEFINED",
) -> dict[str, Any]:
    if cycle <= 0:
        raise ValueError("review cycle must be positive")
    if not candidate_digest:
        raise ValueError("candidate digest required")
    ok_findings, finding_errors = validate_findings(findings)
    ok_scores, score_errors = validate_scorecard(scorecard)
    ok_evidence, evidence_errors = validate_review_evidence(evidence)
    if not ok_findings or not ok_scores or not ok_evidence:
        raise ValueError("; ".join(finding_errors + score_errors + evidence_errors))
    profile = review_standard_profile(citation_style=citation_style)
    unresolved = [f for f in findings if f.get("status", "OPEN") in {"OPEN", "HUMAN_DECISION_REQUIRED"}]
    blockers = sum(1 for f in unresolved if f.get("severity") == "BLOCKER")
    majors = sum(1 for f in unresolved if f.get("severity") == "MAJOR")
    blocking_score_failures = [
        key for key, meta in REVIEW_CRITERIA.items()
        if meta.get("blocking") and float(scorecard.get(key, 0.0)) < float(profile["blocking_score"])
    ]
    nonblocking_score_failures = [
        key for key, meta in REVIEW_CRITERIA.items()
        if not meta.get("blocking") and float(scorecard.get(key, 0.0)) < float(profile["minimum_score"])
    ]
    if blockers or majors or blocking_score_failures:
        status = "REGENERATE_REQUIRED"
    elif nonblocking_score_failures:
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS_CANDIDATE"
    evidence_digest = canonical_digest(evidence or [])
    return ReviewCycleRecord(
        cycle=cycle,
        candidate_digest=candidate_digest,
        standard_id=STANDARD_ID,
        standard_digest=profile["digest"],
        findings=[dict(f, signature=_finding_signature(f)) for f in findings],
        scorecard={k: round(float(v), 4) for k, v in scorecard.items()},
        evidence_digest=evidence_digest,
        evidence_count=len(evidence or []),
        citation_style=citation_style,
        open_blockers=blockers,
        open_majors=majors,
        status=status,
    ).record()


def validate_review_cycle(record: dict[str, Any] | None, *, expected_candidate_digest: str | None = None) -> tuple[bool, list[str]]:
    if not record:
        return False, ["review cycle missing"]
    errors: list[str] = []
    if record.get("standard_id") != STANDARD_ID:
        errors.append("review cycle standard mismatch")
    if expected_candidate_digest and record.get("candidate_digest") != expected_candidate_digest:
        errors.append("review cycle bound to stale candidate")
    ok_findings, finding_errors = validate_findings(record.get("findings", []))
    ok_scores, score_errors = validate_scorecard(record.get("scorecard", {}))
    errors.extend(finding_errors + score_errors)
    profile = review_standard_profile(citation_style=str(record.get("citation_style", "PROJECT_DEFINED")))
    if record.get("standard_digest") != profile["digest"]:
        errors.append("review cycle standard digest mismatch")
    if int(record.get("evidence_count", 0)) < len(REVIEW_CRITERIA):
        errors.append("review cycle evidence does not cover the complete standard")
    if record.get("status") not in {"REGENERATE_REQUIRED", "REVIEW_REQUIRED", "PASS_CANDIDATE"}:
        errors.append("review cycle status invalid")
    if not ok_findings or not ok_scores:
        pass
    return not errors, errors


def regeneration_record(
    *,
    cycle: int,
    from_digest: str,
    to_digest: str,
    addressed_finding_ids: list[str],
    preserved_required_unit_ids: list[str],
    required_unit_ids: list[str],
    introduced_material_unit_ids: list[str] | None = None,
    degradation_flags: list[str] | None = None,
) -> dict[str, Any]:
    introduced = sorted(set(introduced_material_unit_ids or []))
    degradation = sorted(set(degradation_flags or []))
    required = set(required_unit_ids)
    preserved = set(preserved_required_unit_ids)
    lost = sorted(required - preserved)
    errors: list[str] = []
    if not addressed_finding_ids:
        errors.append("regeneration must address at least one review finding")
    if not from_digest or not to_digest:
        errors.append("regeneration digests missing")
    if from_digest == to_digest and addressed_finding_ids:
        errors.append("regeneration did not change candidate despite addressed findings")
    if lost:
        errors.append("regeneration lost required epistemic units")
    if introduced:
        errors.append("regeneration introduced new material units requiring re-audit")
    if degradation:
        errors.append("regeneration introduced degradation flags")
    payload = {
        "cycle": cycle,
        "from_digest": from_digest,
        "to_digest": to_digest,
        "addressed_finding_ids": sorted(set(addressed_finding_ids)),
        "required_unit_ids": sorted(required),
        "preserved_required_unit_ids": sorted(preserved),
        "lost_required_unit_ids": lost,
        "introduced_material_unit_ids": introduced,
        "degradation_flags": degradation,
        "status": "PASS" if not errors else "REAUDIT_REQUIRED",
        "errors": errors,
    }
    payload["digest"] = canonical_digest(payload)
    return payload


def validate_regeneration(record: dict[str, Any] | None, *, expected_from_digest: str | None = None, expected_to_digest: str | None = None) -> tuple[bool, list[str]]:
    if not record:
        return False, ["regeneration record missing"]
    errors = list(record.get("errors", []))
    if record.get("status") != "PASS":
        errors.append("regeneration status is not PASS")
    if expected_from_digest and record.get("from_digest") != expected_from_digest:
        errors.append("regeneration source digest mismatch")
    if expected_to_digest and record.get("to_digest") != expected_to_digest:
        errors.append("regeneration target digest mismatch")
    if record.get("lost_required_unit_ids"):
        errors.append("regeneration lost required epistemic units")
    if record.get("introduced_material_unit_ids"):
        errors.append("regeneration introduced new material units")
    if record.get("degradation_flags"):
        errors.append("regeneration has degradation flags")
    return not errors, list(dict.fromkeys(errors))


@dataclass
class ReviewSaturationMonitor:
    signatures: set[str]
    no_novelty_streak: int = 0
    no_improvement_without_degradation_streak: int = 0
    probes: int = 0

    @classmethod
    def create(cls) -> "ReviewSaturationMonitor":
        return cls(signatures=set())

    @property
    def P(self) -> int:
        return len(self.signatures)

    def probe(self, *, signature: str, new_finding: bool, material_improvement: bool, degradation: bool) -> bool:
        self.probes += 1
        novelty = signature not in self.signatures
        if novelty:
            self.signatures.add(signature)
        self.no_novelty_streak = 0 if novelty or new_finding else self.no_novelty_streak + 1
        useful_improvement = bool(material_improvement and not degradation)
        self.no_improvement_without_degradation_streak = 0 if useful_improvement else self.no_improvement_without_degradation_streak + 1
        return (
            self.no_novelty_streak >= REVIEW_SATURATION_TARGET
            and self.no_improvement_without_degradation_streak >= REVIEW_SATURATION_TARGET
        )

    def receipt(self, *, candidate_digest: str, open_blockers: int = 0, open_majors: int = 0, degradation_escapes: int = 0) -> dict[str, Any]:
        status = "PASS" if (
            self.no_novelty_streak >= REVIEW_SATURATION_TARGET
            and self.no_improvement_without_degradation_streak >= REVIEW_SATURATION_TARGET
            and open_blockers == 0 and open_majors == 0 and degradation_escapes == 0
        ) else "INCOMPLETE"
        return {
            "candidate_digest": candidate_digest,
            "P": self.P,
            "probes": self.probes,
            "no_novelty_streak": self.no_novelty_streak,
            "no_improvement_without_degradation_streak": self.no_improvement_without_degradation_streak,
            "target": REVIEW_SATURATION_TARGET,
            "open_blockers": open_blockers,
            "open_majors": open_majors,
            "degradation_escapes": degradation_escapes,
            "status": status,
            "interpretation": "computational/challenge saturation evidence; not 10,000 hidden chain-of-thought traces",
        }


def review_gate(review: dict[str, Any] | None, *, expected_candidate_digest: str | None = None, require_regeneration: bool = False) -> tuple[bool, list[str]]:
    if not review:
        return False, ["scientific-editorial review missing"]
    errors: list[str] = []
    cycles = list(review.get("cycles", []))
    if not cycles:
        errors.append("scientific-editorial review has no cycles")
    else:
        last = cycles[-1]
        ok_cycle, cycle_errors = validate_review_cycle(last, expected_candidate_digest=expected_candidate_digest)
        errors.extend(cycle_errors)
        if last.get("status") != "PASS_CANDIDATE":
            errors.append("latest scientific-editorial review is not PASS_CANDIDATE")
    if require_regeneration:
        regenerations = list(review.get("regenerations", []))
        if not regenerations:
            errors.append("scientific-editorial review requires at least one documented regeneration")
        else:
            by_cycle = {int(c.get("cycle", 0)): c for c in cycles}
            for regeneration in regenerations:
                rcycle = int(regeneration.get("cycle", 0))
                source_cycle = by_cycle.get(rcycle)
                if regeneration.get("status") != "PASS":
                    errors.append(f"regeneration {rcycle} is not PASS")
                if not source_cycle:
                    errors.append(f"regeneration {rcycle} has no source review cycle")
                    continue
                if source_cycle.get("candidate_digest") != regeneration.get("from_digest"):
                    errors.append(f"regeneration {rcycle} source digest is not bound to its review cycle")
                finding_ids = {str(f.get("id")) for f in source_cycle.get("findings", [])}
                addressed = set(map(str, regeneration.get("addressed_finding_ids", [])))
                if not addressed or not addressed.issubset(finding_ids):
                    errors.append(f"regeneration {rcycle} does not address findings from its source review cycle")
            last_regeneration = regenerations[-1]
            if expected_candidate_digest and last_regeneration.get("to_digest") != expected_candidate_digest:
                errors.append("latest regeneration target is not the saturated candidate")
            if cycles and int(cycles[-1].get("cycle", 0)) <= int(last_regeneration.get("cycle", 0)):
                errors.append("regenerated candidate has no subsequent review cycle")
    saturation = review.get("saturation") or {}
    if expected_candidate_digest and saturation.get("candidate_digest") != expected_candidate_digest:
        errors.append("review saturation bound to stale candidate")
    if int(saturation.get("P", 0)) <= 0:
        errors.append("review saturation P must be positive")
    if int(saturation.get("probes", 0)) < int(saturation.get("P", 0)) + REVIEW_SATURATION_TARGET:
        errors.append("review saturation probes do not prove P+10000")
    if saturation.get("status") != "PASS":
        errors.append("review saturation status is not PASS")
    if int(saturation.get("no_novelty_streak", 0)) < REVIEW_SATURATION_TARGET:
        errors.append("P+10000 no-novelty review saturation not reached")
    if int(saturation.get("no_improvement_without_degradation_streak", 0)) < REVIEW_SATURATION_TARGET:
        errors.append("P+10000 no-improvement-without-degradation saturation not reached")
    if int(saturation.get("open_blockers", 0)) or int(saturation.get("open_majors", 0)):
        errors.append("review saturation has unresolved blocking/major findings")
    if int(saturation.get("degradation_escapes", 0)):
        errors.append("review saturation has degradation escapes")
    return not errors, list(dict.fromkeys(errors))
