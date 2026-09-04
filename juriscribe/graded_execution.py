from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "juriscribe-graded-execution/v2"
METHOD_ACCESS_SCHEMA = "juriscribe-method-access/v1"
METHOD_MODE_INTENT_SCHEMA = "juriscribe-method-mode-intent/v1"
METHOD_KERNEL_PROFILE = "JURISCRIBE_METHOD_KERNEL_V1"
PROFILES = ("ATTESTED", "LEAN")
PREFERENCES = ("ATTESTED_PREFERRED", "ATTESTED_REQUIRED", "LEAN")
CAPABILITY_STATES = frozenset({"AVAILABLE", "UNAVAILABLE", "UNVERIFIED"})
PATH_CLASSES = (
    "INSTALLED_BOUND_RUNTIME",
    "LOCAL_EXISTING_CHECKOUT_OR_PACKAGE",
    "CONNECTED_REPOSITORY_READ_TO_LOCAL_IMPORT",
    "PUBLIC_PINNED_REPOSITORY_READ_TO_LOCAL_IMPORT",
    "PROBE_SOURCE_TO_RUNTIME_BRIDGE",
    "OPERATION_SPECIFIC_CANONICAL_CLOSURE",
    "FULL_PINNED_RUNTIME_PACKAGE",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MethodAccess:
    exact_human_acceptance: bool
    revision_pinned: bool
    contract_digest_match: bool
    method_kernel_digest_match: bool

    @property
    def ready(self) -> bool:
        return all((self.exact_human_acceptance, self.revision_pinned, self.contract_digest_match, self.method_kernel_digest_match))


@dataclass(frozen=True)
class PathAttempt:
    path_class: str
    observed_result: str
    required_capabilities: tuple[str, ...] = ()
    failure_signature: str = ""
    retry_consumed: bool = False
    evidence_id: str = ""


@dataclass(frozen=True)
class InfrastructureDebt:
    code: str
    capability_or_path: str
    effect: str
    evidence_id: str
    replay_or_remediation: str = ""

    def as_dict(self) -> dict[str, str]:
        values = {
            "code": self.code.strip(),
            "capability_or_path": self.capability_or_path.strip(),
            "effect": self.effect.strip(),
            "evidence_id": self.evidence_id.strip(),
            "replay_or_remediation": self.replay_or_remediation.strip(),
        }
        if not all(values[k] for k in ("code", "capability_or_path", "effect", "evidence_id")):
            raise ValueError("infrastructure debt requires code, capability/path, exact effect and evidence_id")
        return values


def load_method_kernel(path: str | Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if value.get("profile") != METHOD_KERNEL_PROFILE:
        raise ValueError("unexpected Method Kernel profile")
    return value


def validate_method_kernel(
    kernel: Mapping[str, Any],
    *,
    canonical_modes: Sequence[str],
    canonical_runtime_specs: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if kernel.get("profile") != METHOD_KERNEL_PROFILE:
        errors.append("profile mismatch")
    if kernel.get("method_degradation_allowed") is not False:
        errors.append("method degradation must be forbidden")
    if kernel.get("epistemic_degradation_allowed") is not False:
        errors.append("epistemic degradation must be forbidden")
    if kernel.get("human_validation_required") is not True:
        errors.append("human validation must be required")
    methods = kernel.get("mode_methods") or {}
    if tuple(methods.keys()) != tuple(canonical_modes):
        errors.append("mode key/order parity mismatch")
    for mode in canonical_modes:
        pipeline = list((methods.get(mode) or {}).get("pipeline") or [])
        if not pipeline or pipeline[-1] != "HUMAN_VALIDATION":
            errors.append(f"{mode}: incomplete method pipeline")
    bindings = kernel.get("runtime_registry_stage_bindings") or {}
    common_binding = list(bindings.get("common_stages") or [])
    specific_bindings = bindings.get("specific_stages") or {}
    if not common_binding:
        errors.append("runtime common-stage binding missing")
    if tuple(specific_bindings.keys()) != tuple(canonical_modes):
        errors.append("runtime specific-stage binding mode parity mismatch")
    if canonical_runtime_specs is not None:
        for mode in canonical_modes:
            spec = canonical_runtime_specs.get(mode) or {}
            if common_binding != list(spec.get("common_stages") or []):
                errors.append(f"{mode}: common runtime-stage binding mismatch")
            if list(specific_bindings.get(mode) or []) != list(spec.get("specific_stages") or []):
                errors.append(f"{mode}: specific runtime-stage binding mismatch")
    profile_policy = kernel.get("profile_policy") or {}
    if profile_policy.get("mandatory_profile_choice") is not False:
        errors.append("mandatory execution-profile roundtrip forbidden")
    if profile_policy.get("default_preference") != "ATTESTED_PREFERRED":
        errors.append("default must be ATTESTED_PREFERRED")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "digest": _canonical_digest(kernel)}


def _state(caps: Mapping[str, str], name: str) -> str:
    value = str(caps.get(name, "UNVERIFIED")).upper().strip()
    return value if value in CAPABILITY_STATES else "UNVERIFIED"


def _available(caps: Mapping[str, str], *names: str) -> bool:
    return all(_state(caps, name) == "AVAILABLE" for name in names)


def _not_unavailable(caps: Mapping[str, str], *names: str) -> bool:
    return all(_state(caps, name) != "UNAVAILABLE" for name in names)


def eligible_path_classes(caps: Mapping[str, str], *, installed_runtime_bound: bool, operation_closure_available: bool = False) -> tuple[str, ...]:
    """Return runtime-transport classes only. LEAN is intentionally not a path class."""
    out: list[str] = []
    if installed_runtime_bound and _available(caps, "RUNTIME_IMPORT"):
        out.append("INSTALLED_BOUND_RUNTIME")
    if _available(caps, "LOCAL_CHECKOUT", "PYTHON_EXECUTION"):
        out.append("LOCAL_EXISTING_CHECKOUT_OR_PACKAGE")
    if _available(caps, "CONNECTED_REPOSITORY_READ", "LOCAL_SCRATCH_IO", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"):
        out.append("CONNECTED_REPOSITORY_READ_TO_LOCAL_IMPORT")
    if _available(caps, "PUBLIC_REPOSITORY_READ", "LOCAL_SCRATCH_IO", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"):
        out.append("PUBLIC_PINNED_REPOSITORY_READ_TO_LOCAL_IMPORT")
    if _not_unavailable(caps, "REPOSITORY_READ", "LOCAL_SCRATCH_IO", "PYTHON_EXECUTION") and _state(caps, "SOURCE_TO_RUNTIME_BRIDGE") == "UNVERIFIED":
        out.append("PROBE_SOURCE_TO_RUNTIME_BRIDGE")
    if operation_closure_available and _available(caps, "REPOSITORY_READ", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"):
        out.append("OPERATION_SPECIFIC_CANONICAL_CLOSURE")
    if _available(caps, "REPOSITORY_READ", "LOCAL_SCRATCH_IO", "PYTHON_EXECUTION", "SOURCE_TO_RUNTIME_BRIDGE"):
        out.append("FULL_PINNED_RUNTIME_PACKAGE")
    return tuple(dict.fromkeys(out))


def search_exhausted(eligible: Iterable[str], attempts: Iterable[PathAttempt]) -> bool:
    eligible_set = set(eligible)
    attempted = {a.path_class for a in attempts if a.observed_result in {"SUCCESS", "FAILED", "IMPOSSIBLE"}}
    return eligible_set.issubset(attempted)


def next_runtime_path(eligible: Iterable[str], attempts: Iterable[PathAttempt]) -> str | None:
    attempted = {a.path_class for a in attempts if a.observed_result in {"SUCCESS", "FAILED", "IMPOSSIBLE"}}
    return next((p for p in eligible if p not in attempted), None)


def choose_execution_profile(method_access: MethodAccess, *, runtime_reachable: bool, infrastructure_search_exhausted: bool, capability_discovery_complete: bool = True, preference: str = "ATTESTED_PREFERRED") -> dict[str, Any]:
    preference = str(preference).upper().strip()
    if preference not in PREFERENCES:
        raise ValueError("invalid execution preference")
    base = {"schema": SCHEMA, "method_degraded": False, "epistemic_degraded": False, "canonical_complete": False}
    if not method_access.ready:
        return {**base, "state": "METHOD_ACCESS_BLOCKED", "profile": None, "runtime_attestation_allowed": False}
    if preference == "LEAN":
        return {**base, "state": "WORK_READY", "profile": "LEAN", "runtime_attestation_allowed": False, "promotion_requires_replay": True}
    if runtime_reachable:
        return {**base, "state": "WORK_READY", "profile": "ATTESTED", "runtime_attestation_allowed": True, "promotion_requires_replay": False}
    if not capability_discovery_complete:
        return {**base, "state": "CAPABILITY_DISCOVERY", "profile": None, "runtime_attestation_allowed": False}
    if not infrastructure_search_exhausted:
        return {**base, "state": "INFRASTRUCTURE_SEARCH", "profile": None, "runtime_attestation_allowed": False}
    if preference == "ATTESTED_REQUIRED":
        return {**base, "state": "ATTESTED_INFRASTRUCTURE_BLOCKED", "profile": None, "runtime_attestation_allowed": False, "lean_available": True}
    return {**base, "state": "WORK_READY", "profile": "LEAN", "runtime_attestation_allowed": False, "promotion_requires_replay": True}


def runtime_claim_projection(*, profile: str, runtime_reachable: bool, receipts_verified: bool = False, complete_verified: bool = False) -> dict[str, bool]:
    if profile not in PROFILES:
        raise ValueError("profile must be ATTESTED or LEAN")
    attested = profile == "ATTESTED" and runtime_reachable
    return {
        "runtime_attestation": attested,
        "runtime_receipts_may_be_claimed": attested and bool(receipts_verified),
        "runtime_complete_may_be_claimed": attested and bool(complete_verified),
    }


def method_mode_intent(mode: str, method_kernel: Mapping[str, Any]) -> dict[str, Any]:
    value = str(mode).strip().upper()
    methods = method_kernel.get("mode_methods") or {}
    if value not in methods:
        raise ValueError("method mode intent must match a canonical Method Kernel mode")
    payload = {"schema": METHOD_MODE_INTENT_SCHEMA,"mode": value,"authority": "METHOD_INTENT_ONLY","runtime_mode_selection": False,"runtime_receipt": False,"pipeline": list(methods[value].get("pipeline") or [])}
    payload["digest"] = _canonical_digest(payload)
    return payload


def artifact_projection(*, profile: str, content_ready: bool, host_write: bool, host_readback: bool, delivered: bool) -> dict[str, Any]:
    if profile not in PROFILES:
        raise ValueError("profile must be ATTESTED or LEAN")
    if delivered and not host_write:
        raise ValueError("delivery requires physical materialization")
    if host_readback and not host_write:
        raise ValueError("readback requires physical materialization")
    physical = "NOT_READY"
    if content_ready: physical = "CONTENT_READY"
    if host_write: physical = "HOST_MATERIALIZED"
    if host_readback: physical = "HOST_READBACK_VERIFIED"
    if delivered: physical = "DELIVERED"
    return {"physical_readiness": physical,"execution_attestation": "RUNTIME_VERIFIED" if profile == "ATTESTED" else "METHOD_GUIDED","canonical_complete": False,"candidate_material_only": profile == "LEAN"}


def infrastructure_note(items: Iterable[InfrastructureDebt], *, language: str = "it") -> str:
    records = [item.as_dict() for item in items]
    if not records:
        return ""
    refs = [r["evidence_id"] for r in records]
    effects = list(dict.fromkeys(r["effect"] for r in records))
    if language.lower().startswith("en"):
        return "Juriscribe method and source discipline remain unchanged. " + f"This session limits {'; '.join(effects)} [{', '.join(refs)}]; work continues without claiming the unavailable runtime attestations."
    return "Metodo Juriscribe e disciplina delle fonti restano invariati. " + f"In questa sessione è limitato: {'; '.join(effects)} [{', '.join(refs)}]; il lavoro continua senza attribuire a quei passaggi attestazioni runtime non disponibili."


def replay_required_for_promotion(current_profile: str, target_profile: str) -> bool:
    if current_profile not in PROFILES or target_profile not in PROFILES:
        raise ValueError("unknown profile")
    return current_profile == "LEAN" and target_profile == "ATTESTED"
