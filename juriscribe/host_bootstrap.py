from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .admission import ACCEPT_PHRASE, contract_digest, issue_receipt, load_contract_text
from .bootstrap import bootstrap_card, issue_probe_receipt
from .portable_session import MemorySession, initialize_memory_session

HOST_BOOTSTRAP_SCHEMA = "juriscribe-host-bootstrap/v1"
TRANSPORT_SCHEMA = "juriscribe-host-runtime-transport/v1"
CAPABILITY_STATES = frozenset({"AVAILABLE", "UNAVAILABLE", "UNVERIFIED"})
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")

BOOTSTRAP_SOURCE_PATHS = (
    "juriscribe/__init__.py",
    "juriscribe/admission.py",
    "juriscribe/bootstrap.py",
    "juriscribe/host_bootstrap.py",
    "juriscribe/interaction.py",
    "juriscribe/modes.py",
    "juriscribe/node_header.py",
    "juriscribe/portable_session.py",
    "juriscribe/session.py",
    "juriscribe/session_integrity.py",
)


def normalize_host_capabilities(capabilities: dict[str, str] | None) -> dict[str, str]:
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


def validate_runtime_binding(resolved_revision: str, runtime_revision: str) -> str:
    expected = str(resolved_revision).strip()
    actual = str(runtime_revision).strip()
    if not _REVISION_RE.fullmatch(expected):
        raise ValueError("resolved revision must be a full lowercase 40-hex commit SHA")
    if not _REVISION_RE.fullmatch(actual):
        raise ValueError("runtime revision must be a full lowercase 40-hex commit SHA")
    if actual != expected:
        raise PermissionError(f"runtime revision mismatch: expected {expected}, got {actual}")
    return expected


def validate_acceptance_context(contract_text: str, presented_contract_sha256: str) -> str:
    expected = contract_digest(contract_text)
    observed = str(presented_contract_sha256).strip().lower()
    if observed != expected:
        raise PermissionError("presented contract hash does not match executing runtime contract")
    return expected


def plan_runtime_transport(
    capabilities: dict[str, str] | None,
    *,
    resolved_revision: str,
    runtime_revision: str | None = None,
) -> dict[str, Any]:
    """Choose the smallest revision-bound transport that can execute bootstrap."""
    caps = normalize_host_capabilities(capabilities)
    expected = str(resolved_revision).strip()
    if not _REVISION_RE.fullmatch(expected):
        raise ValueError("resolved revision must be a full lowercase 40-hex commit SHA")

    installed_bound = False
    installed_reason = "runtime import unavailable"
    if caps.get("RUNTIME_IMPORT") == "AVAILABLE":
        if runtime_revision is None:
            installed_reason = "runtime revision unverified"
        else:
            try:
                validate_runtime_binding(expected, runtime_revision)
            except (ValueError, PermissionError):
                installed_reason = "runtime revision mismatch or invalid"
            else:
                installed_bound = True
                installed_reason = "runtime revision verified"

    if installed_bound:
        decision = "USE_INSTALLED_RUNTIME"
        missing: list[str] = []
        scope = "INSTALLED_BOUND"
        source_paths: list[str] = []
        deferred_full_runtime = False
    else:
        required = ("REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE")
        missing = [name for name in required if caps.get(name) != "AVAILABLE"]
        decision = "MATERIALIZE_PINNED_RUNTIME_SOURCE" if not missing else "BLOCKED"
        use_minimal = not missing and caps.get("SESSION_CONTEXT") == "AVAILABLE"
        scope = "BOOTSTRAP_MINIMAL" if use_minimal else ("FULL_RUNTIME" if not missing else "NONE")
        source_paths = list(BOOTSTRAP_SOURCE_PATHS) if use_minimal else []
        deferred_full_runtime = bool(use_minimal)

    return {
        "schema": TRANSPORT_SCHEMA,
        "decision": decision,
        "missing": missing,
        "resolved_revision": expected,
        "installed_runtime_binding": installed_reason,
        "revision_binding_required": True,
        "receipt_simulation_allowed": False,
        "materialization_scope": scope,
        "required_source_paths": source_paths,
        "deferred_full_runtime": deferred_full_runtime,
        "bootstrap_round_trip_policy": "SINGLE_HOST_TURN_AFTER_ACCEPTANCE",
    }


def issue_probe_from_acceptance(
    *,
    user_message: str,
    host_capabilities: dict[str, str],
    host: str,
    resolved_revision: str,
    runtime_revision: str,
    presented_contract_sha256: str,
    contract_text: str | None = None,
) -> dict[str, Any]:
    contract_text = contract_text or load_contract_text()
    revision = validate_runtime_binding(resolved_revision, runtime_revision)
    csha = validate_acceptance_context(contract_text, presented_contract_sha256)
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
        "resolved_revision": revision,
        "contract_sha256": csha,
        "admission_receipt": receipt,
        "probe_receipt": probe,
        "next": bootstrap_card(
            "INITIALIZE_REQUIRED",
            contract_version=receipt.get("contract_version", ""),
            detail="Pinned human acceptance context was validated; admission and probe receipts are real.",
        ),
    }


@dataclass(frozen=True)
class MemoryBootstrap:
    session: MemorySession
    admission_receipt: dict[str, Any]
    probe_receipt: dict[str, Any]
    resolved_revision: str
    contract_sha256: str

    def public_status(self) -> dict[str, Any]:
        card = dict(((self.session.state.interaction or {}).get("card") or {}))
        return {
            "schema": HOST_BOOTSTRAP_SCHEMA,
            "state": self.session.state.phase,
            "backend": "MEMORY",
            "session_id": self.session.session_id,
            "resolved_revision": self.resolved_revision,
            "durable_recovery": False,
            "choices": [str(item) for item in card.get("choices", [])],
        }


def bootstrap_memory_from_acceptance(
    request: str,
    *,
    user_message: str,
    host_capabilities: dict[str, str],
    host: str,
    resolved_revision: str,
    runtime_revision: str,
    presented_contract_sha256: str,
    contract_text: str | None = None,
    session_id: str | None = None,
) -> MemoryBootstrap:
    contract_text = contract_text or load_contract_text()
    handshake = issue_probe_from_acceptance(
        user_message=user_message,
        host_capabilities=host_capabilities,
        host=host,
        resolved_revision=resolved_revision,
        runtime_revision=runtime_revision,
        presented_contract_sha256=presented_contract_sha256,
        contract_text=contract_text,
    )
    session = initialize_memory_session(
        request,
        admission_receipt=handshake["admission_receipt"],
        probe_receipt=handshake["probe_receipt"],
        contract_text=contract_text,
        session_id=session_id,
    )
    session.state.runtime["source_revision"] = handshake["resolved_revision"]
    session.state.runtime["contract_sha256"] = handshake["contract_sha256"]
    return MemoryBootstrap(
        session=session,
        admission_receipt=handshake["admission_receipt"],
        probe_receipt=handshake["probe_receipt"],
        resolved_revision=handshake["resolved_revision"],
        contract_sha256=handshake["contract_sha256"],
    )
