from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .node_header import validate_node_header, write_node_header
from .session_integrity import CANONICAL_FILENAME, LEGACY_FILENAME, validate_session_integrity, write_session_integrity


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


@dataclass
class SessionState:
    session_id: str
    request: dict[str, Any]
    phase: str = "INITIALIZED"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    runtime: dict[str, Any] = field(default_factory=dict)
    admission: dict[str, Any] = field(default_factory=dict)
    interaction: dict[str, Any] = field(default_factory=lambda: {"card": {}, "history": [], "status": "NOT_STARTED"})
    corpus: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    bibliography: dict[str, Any] = field(default_factory=lambda: {"available": False, "entries": [], "status": "NOT_AVAILABLE"})
    epistemic_units: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    reticulum: dict[str, Any] = field(default_factory=dict)
    generation_contract: dict[str, Any] = field(default_factory=dict)
    continuation: dict[str, Any] = field(default_factory=lambda: {"plan": {}, "coverage": {}, "benchmark_gap": {}, "status": "NOT_STARTED"})
    drafts: list[dict[str, Any]] = field(default_factory=list)
    review: dict[str, Any] = field(default_factory=lambda: {"standard_id": "JURISCRIBE_LEGAL_MONOGRAPH_V1", "cycles": [], "regenerations": [], "saturation": {}, "status": "NOT_STARTED"})
    final_review: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    mining: dict[str, Any] = field(default_factory=dict)
    style_profile: dict[str, Any] = field(default_factory=dict)
    setup: dict[str, Any] = field(default_factory=dict)
    source_intelligence: dict[str, Any] = field(default_factory=lambda: {"research_plan": [], "dominance_assessments": [], "coverage_status": "NOT_STARTED"})
    claim_ledger: list[dict[str, Any]] = field(default_factory=list)
    artifact_evidence: list[dict[str, Any]] = field(default_factory=list)
    quality: dict[str, Any] = field(default_factory=dict)
    benchmark: dict[str, Any] = field(default_factory=dict)
    simulations: dict[str, Any] = field(default_factory=dict)
    compression: dict[str, Any] = field(default_factory=dict)
    limits: list[dict[str, Any]] = field(default_factory=list)
    strategy: dict[str, Any] = field(default_factory=dict)
    dod: list[dict[str, Any]] = field(default_factory=list)
    editorial_actions: list[dict[str, Any]] = field(default_factory=list)
    reflection: dict[str, Any] = field(default_factory=lambda: {"iterations": 0, "no_novelty_streak": 0, "target": 1000, "saturated": False})
    metrics: dict[str, Any] = field(default_factory=lambda: {
        "semantic_no_novelty_streak": 0,
        "strategy_no_improvement_streak": 0,
        "dod_no_novelty_streak": 0,
        "review_no_novelty_streak": 0,
        "review_no_improvement_streak": 0,
        "simulations_run": 0,
        "simulation_failures": 0,
    })
    completion: dict[str, Any] = field(default_factory=lambda: {"eligible": False, "reason": "DoD, review, provenance and final review not yet proven"})
    node_integrity: dict[str, Any] = field(default_factory=lambda: {"status": "NOT_CHECKED", "errors": []})
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        self.touch()
        return asdict(self)


class Workspace:
    def __init__(self, root: str | Path, session_id: str):
        self.base = Path(root) / session_id
        self.state_path = self.base / "state.json"
        self.integrity_path = self.base / CANONICAL_FILENAME
        # Contract 1.5 still names node.h: keep it as a checked compatibility projection.
        self.node_path = self.base / LEGACY_FILENAME
        self.ledger_dir = self.base / "ledger"
        self.artifact_dir = self.base / "artifacts"

    def initialize(self, request_text: str, runtime: dict[str, Any] | None = None, admission: dict[str, Any] | None = None) -> SessionState:
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        state = SessionState(
            session_id=self.base.name,
            request={
                "raw": request_text,
                "request_id": stable_id("REQ", request_text),
                "summary": request_text.strip()[:500],
                "atoms": [],
            },
            runtime=runtime or {},
            admission=admission or {},
        )
        self.save(state)
        return state

    def save(self, state: SessionState) -> None:
        self.base.mkdir(parents=True, exist_ok=True)
        data = state.to_dict()
        self.state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        write_session_integrity(data, self.integrity_path)
        write_node_header(data, self.node_path)

    def load(self) -> SessionState:
        state = SessionState(**json.loads(self.state_path.read_text(encoding="utf-8")))
        # One-way migration for pre-v0.8 workspaces: synthesize the canonical
        # manifest only when the legacy projection still validates against state.
        if not self.integrity_path.exists() and self.node_path.exists():
            data = asdict(state)
            legacy_ok, _ = validate_node_header(data, self.node_path.read_text(encoding="utf-8"))
            if legacy_ok:
                write_session_integrity(data, self.integrity_path)
        return state

    def validate_integrity(self, state: SessionState) -> tuple[bool, list[str]]:
        data = asdict(state)
        errors: list[str] = []
        if not self.integrity_path.exists():
            errors.append(f"{CANONICAL_FILENAME} missing")
        else:
            ok, manifest_errors = validate_session_integrity(data, self.integrity_path.read_text(encoding="utf-8"))
            if not ok:
                errors.extend(manifest_errors)
        if not self.node_path.exists():
            errors.append(f"legacy {LEGACY_FILENAME} missing")
        else:
            ok, legacy_errors = validate_node_header(data, self.node_path.read_text(encoding="utf-8"))
            if not ok:
                errors.extend(legacy_errors)
        return not errors, errors

    def validate_node(self, state: SessionState) -> tuple[bool, list[str]]:
        """Deprecated compatibility alias; use validate_integrity()."""
        return self.validate_integrity(state)

    def append_ledger(self, name: str, record: dict[str, Any]) -> None:
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        path = self.ledger_dir / f"{name}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
