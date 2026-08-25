from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

from .admission import load_contract_text, require_receipt
from .bootstrap import bootstrap_card, require_probe_receipt
from .interaction import interaction_card
from .session import SessionState, new_session_id, stable_id

_CLAIM_LOCK = Lock()
_MEMORY_PROBE_CLAIMS: dict[str, str] = {}


def _claim_probe_in_memory(probe_receipt: dict[str, Any], session_id: str) -> None:
    receipt_id = str(probe_receipt.get("receipt_id") or "")
    if not receipt_id.startswith("PRB-"):
        raise PermissionError("cannot consume invalid probe receipt")
    with _CLAIM_LOCK:
        owner = _MEMORY_PROBE_CLAIMS.get(receipt_id)
        if owner:
            raise PermissionError(f"probe receipt already consumed by session {owner}")
        _MEMORY_PROBE_CLAIMS[receipt_id] = str(session_id)


@dataclass
class MemorySession:
    """True no-filesystem session carrier for hosts that can retain Python/session state.

    It deliberately does not claim durable recovery. The host must retain this object.
    Artifact delivery remains gated by real capabilities later in the pipeline.
    """

    state: SessionState

    @property
    def session_id(self) -> str:
        return self.state.session_id

    def snapshot(self) -> dict[str, Any]:
        return self.state.to_dict()


def initialize_memory_session(
    request: str,
    *,
    admission_receipt: dict[str, Any],
    probe_receipt: dict[str, Any],
    contract_text: str | None = None,
    session_id: str | None = None,
) -> MemorySession:
    contract_text = contract_text or load_contract_text()
    receipt = require_receipt(admission_receipt, contract_text)
    probe = require_probe_receipt(probe_receipt, receipt, contract_text)
    caps = dict(probe.get("capabilities") or {})
    if caps.get("SESSION_CONTEXT") != "AVAILABLE":
        raise PermissionError("memory session requires SESSION_CONTEXT=AVAILABLE")
    session_id = session_id or new_session_id()
    _claim_probe_in_memory(probe, session_id)
    runtime = {
        "host": probe.get("host") or "memory-host",
        "capabilities": caps,
        "mode": "ACTIVE_EPHEMERAL",
        "storage_backend": "MEMORY",
        "durable_recovery": False,
        "workspace_base": "",
    }
    admission = {
        "status": "ACCEPTED",
        "receipt": receipt,
        "probe_receipt": probe,
        "bootstrap": bootstrap_card(
            "MODE_SELECTION_REQUIRED",
            contract_version=receipt.get("contract_version", ""),
            detail="T&C accepted; probe sealed and consumed in memory; explicit mode selection required.",
        ),
    }
    state = SessionState(
        session_id=session_id,
        request={
            "raw": request,
            "request_id": stable_id("REQ", request),
            "summary": request.strip()[:500],
            "atoms": [],
        },
        runtime=runtime,
        admission=admission,
        phase="MODE_SELECTION_REQUIRED",
    )
    state.interaction = {
        "card": interaction_card(
            "MODE_SELECTION_REQUIRED",
            summary="Scegli una modalità Juriscribe prima dei materiali sostanziali.",
        ),
        "history": [],
        "status": "READY",
    }
    return MemorySession(state)


def memory_session_gate(session: MemorySession) -> tuple[bool, list[str]]:
    errors: list[str] = []
    runtime = session.state.runtime or {}
    if runtime.get("storage_backend") != "MEMORY":
        errors.append("memory session storage backend mismatch")
    if runtime.get("durable_recovery") is not False:
        errors.append("memory session must not claim durable recovery")
    if not session.state.admission.get("probe_receipt"):
        errors.append("probe receipt missing")
    return not errors, errors
