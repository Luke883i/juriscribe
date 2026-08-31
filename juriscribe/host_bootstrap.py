from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from .admission import ACCEPT_PHRASE, contract_digest, issue_receipt, load_contract_text
from .bootstrap import bootstrap_card, issue_probe_receipt
from .portable_session import MemorySession, initialize_memory_session

HOST_BOOTSTRAP_SCHEMA = "juriscribe-host-bootstrap/v1"
TRANSPORT_SCHEMA = "juriscribe-host-runtime-transport/v1"
HOST_REACHABILITY_SCHEMA = "juriscribe-host-reachability/v1"
PUBLIC_BOOTSTRAP_INTENT_SCHEMA = "juriscribe-public-bootstrap-intent/v1"
CANONICAL_REPOSITORY_URL = "https://github.com/Luke883i/juriscribe"
CAPABILITY_STATES = frozenset({"AVAILABLE", "UNAVAILABLE", "UNVERIFIED"})
REACHABILITY_LEVELS = (
    "DISCOVERY_READY",
    "BOOTSTRAP_READY",
    "WORK_READY",
    "MATERIALIZATION_READY",
    "DELIVERY_READY",
    "RECOVERY_READY",
)
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_BOOTSTRAP_INTENT_RE = re.compile(
    r"^\s*(?:initialize|inizializza|avvia)\s+juriscribe(?:\s+(?P<url>https?://\S+))?\s*$",
    re.I,
)

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


def _cap_state(caps: Mapping[str, str], name: str) -> str:
    value = str(caps.get(name, "UNVERIFIED")).strip().upper()
    return value if value in CAPABILITY_STATES else "UNVERIFIED"


def _available(caps: Mapping[str, str], *names: str) -> bool:
    return all(_cap_state(caps, name) == "AVAILABLE" for name in names)


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


def normalize_repository_url(value: str | None) -> str:
    raw = str(value or CANONICAL_REPOSITORY_URL).strip().rstrip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    parsed = urlparse(raw)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme.lower() != "https" or parsed.netloc.lower() != "github.com":
        raise ValueError("Juriscribe bootstrap requires the canonical public GitHub repository URL")
    if len(parts) != 2 or tuple(part.lower() for part in parts) != ("luke883i", "juriscribe"):
        raise ValueError("repository URL is not the canonical Juriscribe repository")
    return CANONICAL_REPOSITORY_URL


def parse_bootstrap_intent(message: str) -> dict[str, Any]:
    match = _BOOTSTRAP_INTENT_RE.fullmatch(str(message or ""))
    if not match:
        raise ValueError("not a Juriscribe initialization intent")
    supplied = match.group("url")
    prefix = str(message).strip().split(maxsplit=1)[0].lower()
    return {
        "schema": PUBLIC_BOOTSTRAP_INTENT_SCHEMA,
        "intent": "INITIALIZE_JURISCRIBE",
        "repository": normalize_repository_url(supplied),
        "supplied_repository": bool(supplied),
        "language": "it" if prefix in {"inizializza", "avvia"} else "en",
        "authority": "HOST_UX_ALIAS_ONLY",
        "bypasses_acceptance": False,
    }


@dataclass(frozen=True)
class HostReachability:
    discovery_ready: bool
    bootstrap_ready: bool
    work_ready: bool
    materialization_ready: bool
    delivery_ready: bool
    recovery_ready: bool
    transport: str
    blockers: tuple[str, ...]
    facts: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        readiness = {
            "DISCOVERY_READY": self.discovery_ready,
            "BOOTSTRAP_READY": self.bootstrap_ready,
            "WORK_READY": self.work_ready,
            "MATERIALIZATION_READY": self.materialization_ready,
            "DELIVERY_READY": self.delivery_ready,
            "RECOVERY_READY": self.recovery_ready,
        }
        return {
            "schema": HOST_REACHABILITY_SCHEMA,
            "readiness": readiness,
            "highest_level": next((level for level in reversed(REACHABILITY_LEVELS) if readiness[level]), "BLOCKED"),
            "transport": self.transport,
            "blockers": list(self.blockers),
            "facts": dict(self.facts),
            "repository_connector_required": False,
            "platform_identity_affects_decision": False,
            "authority": "CAPABILITY_PROJECTION_ONLY",
        }


def classify_host_reachability(
    capabilities: Mapping[str, str] | None,
    *,
    revision_pinned: bool,
    contract_pinned: bool,
    installed_runtime_bound: bool = False,
    host_kind: str = "UNKNOWN",
    provider: str = "UNKNOWN",
    browser: str = "UNKNOWN",
    os_name: str = "UNKNOWN",
) -> HostReachability:
    """Project observed capability facts into lifecycle reachability.

    Provider/browser/OS names are diagnostic only and cannot promote a capability.
    UNVERIFIED remains non-available. An installed runtime counts only when the host
    both observed RUNTIME_IMPORT and verified the runtime revision binding.
    """
    caps = normalize_host_capabilities(dict(capabilities or {}))
    blockers: list[str] = []

    discovery_ready = bool(revision_pinned and contract_pinned)
    if not revision_pinned:
        blockers.append("REVISION_NOT_PINNED")
    if not contract_pinned:
        blockers.append("CONTRACT_NOT_PINNED")

    source_transport = _available(caps, "REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE")
    verified_installed_runtime = bool(installed_runtime_bound and _available(caps, "RUNTIME_IMPORT"))
    if verified_installed_runtime:
        transport = "INSTALLED_BOUND"
    elif source_transport:
        transport = "PINNED_SOURCE"
    else:
        transport = "NONE"
        if installed_runtime_bound and not _available(caps, "RUNTIME_IMPORT"):
            blockers.append("RUNTIME_IMPORT_UNAVAILABLE")
        if _cap_state(caps, "REPOSITORY_READ") != "AVAILABLE":
            blockers.append("REPOSITORY_READ_UNAVAILABLE")
        if _cap_state(caps, "PYTHON_EXECUTION") != "AVAILABLE":
            blockers.append("PYTHON_EXECUTION_UNAVAILABLE")
        if _cap_state(caps, "SOURCE_TO_RUNTIME_BRIDGE") != "AVAILABLE":
            blockers.append("SOURCE_TO_RUNTIME_BRIDGE_UNAVAILABLE")

    memory_carrier = _cap_state(caps, "SESSION_CONTEXT") == "AVAILABLE"
    filesystem_carrier = _cap_state(caps, "LOCAL_SCRATCH_IO") == "AVAILABLE"
    state_carrier = memory_carrier or filesystem_carrier
    if not state_carrier:
        blockers.append("STATE_CARRIER_UNAVAILABLE")

    bootstrap_ready = discovery_ready and transport != "NONE" and state_carrier
    work_ready = bootstrap_ready

    materialization_ready = work_ready and filesystem_carrier and _available(caps, "DOCX_WRITE", "DOCX_READBACK")
    if work_ready and not filesystem_carrier:
        blockers.append("LOCAL_SCRATCH_IO_UNAVAILABLE_FOR_MATERIALIZATION")
    if work_ready and _cap_state(caps, "DOCX_WRITE") != "AVAILABLE":
        blockers.append("DOCX_WRITE_UNAVAILABLE")
    if work_ready and _cap_state(caps, "DOCX_READBACK") != "AVAILABLE":
        blockers.append("DOCX_READBACK_UNAVAILABLE")

    delivery_surface = _cap_state(caps, "CHAT_ATTACHMENT_WRITE") == "AVAILABLE" or _cap_state(caps, "LOCAL_FILE_DELIVERY") == "AVAILABLE"
    delivery_ready = materialization_ready and delivery_surface
    if materialization_ready and not delivery_surface:
        blockers.append("DELIVERY_SURFACE_UNAVAILABLE")

    recovery_ready = work_ready and filesystem_carrier and delivery_surface
    if work_ready and not recovery_ready:
        blockers.append("DURABLE_RECOVERY_UNAVAILABLE")

    return HostReachability(
        discovery_ready=discovery_ready,
        bootstrap_ready=bootstrap_ready,
        work_ready=work_ready,
        materialization_ready=materialization_ready,
        delivery_ready=delivery_ready,
        recovery_ready=recovery_ready,
        transport=transport,
        blockers=tuple(dict.fromkeys(blockers)),
        facts={
            "host_kind": str(host_kind),
            "provider": str(provider),
            "browser": str(browser),
            "os": str(os_name),
            "installed_runtime_bound": verified_installed_runtime,
            "installed_runtime_binding_requested": bool(installed_runtime_bound),
            "memory_state_carrier": memory_carrier,
            "filesystem_state_carrier": filesystem_carrier,
        },
    )


def plan_runtime_transport(
    capabilities: dict[str, str] | None,
    *,
    resolved_revision: str,
    runtime_revision: str | None = None,
) -> dict[str, Any]:
    """Choose the smallest revision-bound transport with a real state carrier."""
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

    reachability = classify_host_reachability(
        caps,
        revision_pinned=True,
        contract_pinned=True,
        installed_runtime_bound=installed_bound,
    )
    profile = reachability.as_dict()
    if reachability.bootstrap_ready and installed_bound:
        decision = "USE_INSTALLED_RUNTIME"
        missing: list[str] = []
        scope = "INSTALLED_BOUND"
        source_paths: list[str] = []
        deferred_full_runtime = False
    elif reachability.bootstrap_ready and reachability.transport == "PINNED_SOURCE":
        decision = "MATERIALIZE_PINNED_RUNTIME_SOURCE"
        use_minimal = caps.get("SESSION_CONTEXT") == "AVAILABLE"
        scope = "BOOTSTRAP_MINIMAL" if use_minimal else "FULL_RUNTIME"
        source_paths = list(BOOTSTRAP_SOURCE_PATHS) if use_minimal else []
        deferred_full_runtime = bool(use_minimal)
        missing = []
    else:
        decision = "BLOCKED"
        scope = "NONE"
        source_paths = []
        deferred_full_runtime = False
        blocker_map = {
            "RUNTIME_IMPORT_UNAVAILABLE": "RUNTIME_IMPORT",
            "REPOSITORY_READ_UNAVAILABLE": "REPOSITORY_READ",
            "PYTHON_EXECUTION_UNAVAILABLE": "PYTHON_EXECUTION",
            "SOURCE_TO_RUNTIME_BRIDGE_UNAVAILABLE": "SOURCE_TO_RUNTIME_BRIDGE",
            "STATE_CARRIER_UNAVAILABLE": "SESSION_CONTEXT_OR_LOCAL_SCRATCH_IO",
        }
        missing = [blocker_map[b] for b in reachability.blockers if b in blocker_map]
        if caps.get("RUNTIME_IMPORT") == "AVAILABLE" and not installed_bound:
            missing = ["RUNTIME_REVISION_BINDING", *missing]
        missing = list(dict.fromkeys(missing))

    return {
        "schema": TRANSPORT_SCHEMA,
        "decision": decision,
        "missing": missing,
        "resolved_revision": expected,
        "installed_runtime_binding": installed_reason,
        "revision_binding_required": True,
        "receipt_simulation_allowed": False,
        "repository_connector_required": False,
        "materialization_scope": scope,
        "required_source_paths": source_paths,
        "deferred_full_runtime": deferred_full_runtime,
        "bootstrap_round_trip_policy": "SINGLE_HOST_TURN_AFTER_ACCEPTANCE",
        "reachability": profile,
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
    caps = normalize_host_capabilities(host_capabilities)
    if caps.get("SESSION_CONTEXT") != "AVAILABLE":
        raise PermissionError("memory bootstrap requires SESSION_CONTEXT=AVAILABLE")
    contract_text = contract_text or load_contract_text()
    handshake = issue_probe_from_acceptance(
        user_message=user_message,
        host_capabilities=caps,
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
