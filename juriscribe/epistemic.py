from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

ALLOWED_KINDS = {"CONCEPT", "CLAIM", "DEFINITION", "RULE", "SOURCE", "CASE", "DOCTRINE", "ARGUMENT", "COUNTERARGUMENT", "EXCEPTION", "QUALIFICATION", "CONCLUSION", "QUESTION", "CONSTRAINT", "DECISION", "OPEN_ISSUE"}
ALLOWED_RELATIONS = {"SUPPORTS", "CONTRADICTS", "QUALIFIES", "DEPENDS_ON", "DEFINES", "APPLIES_TO", "DISTINGUISHES", "SUPERSEDES", "INTRODUCED_IN", "RESOLVED_IN", "ANTICIPATES", "RECALLS", "REQUIRES_SOURCE"}

@dataclass(frozen=True)
class EpistemicUnit:
    id: str
    kind: str
    text: str
    source_id: str
    status: str = "UNKNOWN"
    chapter: str | None = None
    confidence: float | None = None
    tags: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.kind not in ALLOWED_KINDS:
            raise ValueError(f"Unsupported epistemic kind: {self.kind}")
        if not self.text.strip():
            raise ValueError("Epistemic unit text cannot be empty")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

    def record(self) -> dict:
        self.validate()
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

@dataclass(frozen=True)
class Relation:
    source: str
    predicate: str
    target: str
    rationale: str = ""

    def validate(self) -> None:
        if self.predicate not in ALLOWED_RELATIONS:
            raise ValueError(f"Unsupported relation: {self.predicate}")
        if self.source == self.target and self.predicate in {"CONTRADICTS", "DEPENDS_ON"}:
            raise ValueError("Invalid self relation")

    def record(self) -> dict:
        self.validate()
        return asdict(self)

def contradiction_pairs(relations: Iterable[dict]) -> list[tuple[str, str]]:
    pairs, seen = [], set()
    for relation in relations:
        if relation.get("predicate") != "CONTRADICTS":
            continue
        pair = tuple(sorted((relation["source"], relation["target"])))
        if pair not in seen:
            seen.add(pair)
            pairs.append(pair)
    return pairs
