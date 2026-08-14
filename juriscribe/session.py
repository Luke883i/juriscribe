from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


@dataclass
class SessionState:
    session_id: str
    request: dict[str, Any]
    phase: str = "INITIALIZED"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    runtime: dict[str, Any] = field(default_factory=dict)
    sources: list[dict[str, Any]] = field(default_factory=list)
    epistemic_units: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    strategy: dict[str, Any] = field(default_factory=dict)
    dod: list[dict[str, Any]] = field(default_factory=list)
    editorial_actions: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=lambda: {
        "semantic_no_novelty_streak": 0,
        "strategy_no_improvement_streak": 0,
        "simulations_run": 0,
        "simulation_failures": 0,
    })
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
        self.ledger_dir = self.base / "ledger"
        self.artifact_dir = self.base / "artifacts"

    def initialize(self, request_text: str, runtime: dict[str, Any] | None = None) -> SessionState:
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
        )
        self.save(state)
        return state

    def save(self, state: SessionState) -> None:
        self.base.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> SessionState:
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return SessionState(**data)

    def append_ledger(self, name: str, record: dict[str, Any]) -> None:
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        path = self.ledger_dir / f"{name}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
