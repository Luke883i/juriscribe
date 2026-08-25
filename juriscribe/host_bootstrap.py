from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .admission import ACCEPT_PHRASE, issue_receipt, load_contract_text
from .bootstrap import bootstrap_card, issue_probe_receipt
from .portable_session import MemorySession, initialize_memory_session

HOST_BOOTSTRAP_SCHEMA = "juriscribe-host-bootstrap/v1"
TRANSPORT_SCHEMA = "juriscribe-host-runtime-transport/v1"
CAPABILITY_STATES = frozenset({"AVAILABLE", "UNAVAILABLE", "UNVERIFIED"})


def normalize_host_capabilities(capabilities: dict[str, str] | None) -> dict[str, str]:
    """Normalize only representation, never availability.

    The host must supply observed capability states. Unknown or malformed states are
    rejected rather than promoted or guessed.
    """
    if not capabilities:
        raise ValueError("host capabilities missing")
    normalized: dict[str, str] = {}
    for key, value in sorted(capabilities.items()):
        name = str(key).strip().upper()
        state = str(value).strip().upper()
        if not name:
            raise ValueError("host capability name missing")
        if state not in CAPABILITY_STATES:
            raise ValueError(f"invalid host capability state for {name}: {state}")
        normalized[name] = state
    return normalized


def plan_runtime_transport(capabilities: dict[str, str] | None) -> dict[str, Any]:
    """Return the fail-closed host transport decision before runtime bootstrap.

    Repository readability is deliberately insufficient. Source materialization is
    allowed only when the host has separately observed a bridge from pinned source
    bytes into its Python execution environment.
    """
    caps = normalize_host_capabilities(capabilities)
    if caps.get("RUNTIME_IMPORT") == "AVAILABLE":
        decision = "USE_INSTALLED_RUNTIME"
        missing: list[str] = []
    else:
        required = ("REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE")
        missing = [name for name in required if caps.get(name) != "AVAILABLE"]
        decision = "MATERIALIZE_PINNED_RUNTIME_SOURCE" if not missing else "BLOCKED"
    return {
        "schema": TRANSPORT_SCHEMA,
        "decision": decision,
        "missing": missing,
        "revision_binding_required": True,
        "receipt_simulation_allowed": False,
    }


def issue_probe_from_acceptance(
    *,
    user_message: str,
    host_capabilities: dict[str, str],
    host: str,
    contract_text: str | None = None,
) -> dict[str, Any]:
    """Resume canonical bootstrap from retained exact human acceptance evidence.

    This is intentionally not a second acceptance predicate. The canonical
    admission runtime validates the retained human message and issues the receipt;
    the probe receipt is then created from the observed, non-amplified capability
    map. No filesystem is required.
    """
    contract_text = contract_text or load_contract_text()
    caps = normalize_host_capabilities(host_capabilities)
    receipt = issue_receipt(
        contract_text,
        phrase=ACCEPT_PHRASE,
        actor_type="human",
        evidence_type="explicit_user_message",
        user_message=user_message,
    )
    probe = issue_probe_receipt(receipt, contract_text, caps, host=str(host))
    return {
        "schema": HOST_BOOTSTRAP_SCHEMA,
        "state": "INITIALIZE_REQUIRED",
        "admission_receipt": receipt,
        "probe_receipt": probe,
        "next": bootstrap_card(
            "INITIALIZE_REQUIRED",
            contract_version=receipt.get("contract_version", ""),
            detail="Exact human acceptance evidence was validated by the runtime; admission and probe receipts are real.",
        ),
    }


@dataclass(frozen=True)
class MemoryBootstrap:
    session: MemorySession
    admission_receipt: dict[str, Any]
    probe_receipt: dict[str, Any]

    def public_status(self) -> dict[str, Any]:
        card = dict(((self.session.state.interaction or {}).get("card") or {}))
        return {
            "schema": HOST_BOOTSTRAP_SCHEMA,
            "state": self.session.state.phase,
            "backend": "MEMORY",
            "session_id": self.session.session_id,
            "durable_recovery": False,
            "choices": [str(item) for item in card.get("choices", [])],
        }


def bootstrap_memory_from_acceptance(
    request: str,
    *,
    user_message: str,
    host_capabilities: dict[str, str],
    host: str,
    contract_text: str | None = None,
    session_id: str | None = None,
) -> MemoryBootstrap:
    """Canonical no-filesystem fast path for session-context-capable local hosts."""
    contract_text = contract_text or load_contract_text()
    handshake = issue_probe_from_acceptance(
        user_message=user_message,
        host_capabilities=host_capabilities,
        host=host,
        contract_text=contract_text,
    )
    session = initialize_memory_session(
        request,
        admission_receipt=handshake["admission_receipt"],
        probe_receipt=handshake["probe_receipt"],
        contract_text=contract_text,
        session_id=session_id,
    )
    return MemoryBootstrap(
        session=session,
        admission_receipt=handshake["admission_receipt"],
        probe_receipt=handshake["probe_receipt"],
    )
