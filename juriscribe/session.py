from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .node_header import validate_node_header
from .session_integrity import (
    CANONICAL_FILENAME,
    LEGACY_FILENAME,
    render_session_integrity,
    validate_session_integrity,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix, value):
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


def new_session_id() -> str:
    """Return a non-deterministic session id to prevent accidental workspace reuse."""
    return "SES-" + uuid.uuid4().hex[:16]


def _atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


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
    mode: str = ""
    mode_selection: dict[str, Any] = field(default_factory=dict)
    mode_contract: dict[str, Any] = field(default_factory=dict)
    editorial_standard: dict[str, Any] = field(default_factory=dict)
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
    metrics: dict[str, Any] = field(default_factory=lambda: {"semantic_no_novelty_streak": 0, "strategy_no_improvement_streak": 0, "dod_no_novelty_streak": 0, "review_no_novelty_streak": 0, "review_no_improvement_streak": 0, "simulations_run": 0, "simulation_failures": 0})
    completion: dict[str, Any] = field(default_factory=lambda: {"eligible": False, "reason": "Mode, DoD, review, provenance and final review not yet proven"})
    node_integrity: dict[str, Any] = field(default_factory=lambda: {"status": "NOT_CHECKED", "errors": []})
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    def touch(self):
        self.updated_at = utc_now()

    def to_dict(self):
        self.touch()
        return asdict(self)


class Workspace:
    def __init__(self, root, session_id):
        self.root = Path(root)
        self.base = self.root / session_id
        self.state_path = self.base / "state.json"
        self.integrity_path = self.base / CANONICAL_FILENAME
        self.node_path = self.base / LEGACY_FILENAME
        self.ledger_dir = self.base / "ledger"
        self.artifact_dir = self.base / "artifacts"

    def assert_initializable(self) -> None:
        if not self.base.exists():
            return
        try:
            occupied = any(self.base.iterdir())
        except OSError as exc:
            raise PermissionError(f"cannot inspect existing session workspace: {exc}") from exc
        if occupied:
            raise FileExistsError(f"session workspace already exists: {self.base}")

    def initialize(self, request_text, runtime=None, admission=None, *, persist: bool = True):
        self.assert_initializable()
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
        if persist:
            self.ledger_dir.mkdir(parents=True, exist_ok=True)
            self.artifact_dir.mkdir(parents=True, exist_ok=True)
            self.save(state)
        return state

    def save(self, state):
        self.base.mkdir(parents=True, exist_ok=True)
        data = state.to_dict()
        state_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        integrity_text = render_session_integrity(data)
        # Each file is atomically replaced. If a crash occurs between replacements,
        # load() detects the generation mismatch and fails closed.
        _atomic_text_write(self.state_path, state_text)
        _atomic_text_write(self.integrity_path, integrity_text)

    def load(self, *, validate: bool = True):
        state = SessionState(**json.loads(self.state_path.read_text(encoding="utf-8")))
        if not self.integrity_path.exists() and self.node_path.exists():
            data = asdict(state)
            legacy_ok, _ = validate_node_header(data, self.node_path.read_text(encoding="utf-8"))
            if legacy_ok:
                _atomic_text_write(self.integrity_path, render_session_integrity(data))
        if validate:
            ok, errors = self.validate_integrity(state)
            if not ok:
                raise PermissionError("session integrity validation failed: " + "; ".join(errors))
        return state

    def validate_integrity(self, state):
        data = asdict(state)
        errors = []
        if not self.integrity_path.exists():
            errors.append(f"{CANONICAL_FILENAME} missing")
        else:
            ok, manifest_errors = validate_session_integrity(
                data, self.integrity_path.read_text(encoding="utf-8")
            )
            if not ok:
                errors.extend(manifest_errors)
        return not errors, errors

    def validate_node(self, state):
        return self.validate_integrity(state)

    def append_ledger(self, name, record):
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        path = self.ledger_dir / f"{name}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
