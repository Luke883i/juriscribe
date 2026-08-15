from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

BOOTSTRAP_SCHEMA = "juriscribe-bootstrap/v1"
PROBE_SCHEMA = "juriscribe-probe-receipt/v1"
BOOTSTRAP_ORDER = (
    "TERMS_PRESENTED",
    "TERMS_ACCEPTED",
    "PROBE_REQUIRED",
    "PROBED",
    "INITIALIZE_REQUIRED",
    "INITIALIZING",
    "ACTIVE",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bootstrap_card(state: str, *, contract_version: str = "", detail: str = "") -> dict[str, Any]:
    state = str(state).upper()
    cards = {
        "TERMS_PRESENTED": ("Termini da accettare", ["I ACCEPT", "I DECLINE", "ALTRO"]),
        "PROBE_REQUIRED": ("Verifica capacità dell'host", ["PROBE JURISCRIBE", "ALTRO"]),
        "PROBED": ("Probe completato", ["INITIALIZE JURISCRIBE", "ALTRO"]),
        "INITIALIZE_REQUIRED": ("Inizializzazione richiesta", ["INITIALIZE JURISCRIBE", "ALTRO"]),
        "ACTIVE": ("Juriscribe attivo", ["CARICA CAPITOLI", "STATO SESSIONE", "ALTRO"]),
    }
    title, choices = cards.get(state, (state.replace("_", " ").title(), ["ALTRO"]))
    payload = {
        "schema": BOOTSTRAP_SCHEMA,
        "state": state,
        "headline": title,
        "contract_version": contract_version,
        "detail": detail,
        "choices": choices,
        "free_input_allowed": True,
        "blocking": state != "ACTIVE",
    }
    payload["digest"] = canonical_digest(payload)
    return payload


def issue_probe_receipt(
    admission_receipt: dict[str, Any],
    contract_text: str,
    capabilities: dict[str, str],
    *,
    host: str,
    probed_at: str | None = None,
) -> dict[str, Any]:
    from .admission import contract_digest, contract_version, validate_receipt

    ok, errors = validate_receipt(admission_receipt, contract_text)
    if not ok:
        raise PermissionError("probe denied: " + "; ".join(errors))
    if not capabilities:
        raise ValueError("probe capabilities missing")
    normalized = {str(k): str(v) for k, v in sorted(capabilities.items())}
    probed_at = probed_at or utc_now()
    payload = {
        "schema": PROBE_SCHEMA,
        "status": "PROBED",
        "admission_receipt_id": admission_receipt.get("receipt_id", ""),
        "contract_version": contract_version(contract_text),
        "contract_sha256": contract_digest(contract_text),
        "host": str(host),
        "capabilities": normalized,
        "capabilities_digest": canonical_digest(normalized),
        "probed_at": probed_at,
    }
    payload["receipt_id"] = "PRB-" + canonical_digest(payload)[:16]
    return payload


def validate_probe_receipt(
    probe_receipt: dict[str, Any] | None,
    admission_receipt: dict[str, Any] | None,
    contract_text: str,
) -> tuple[bool, list[str]]:
    from .admission import contract_digest, contract_version, validate_receipt

    errors: list[str] = []
    ok, admission_errors = validate_receipt(admission_receipt, contract_text)
    if not ok:
        errors.extend(admission_errors)
    if not probe_receipt:
        return False, list(dict.fromkeys(errors + ["probe receipt missing"]))
    if probe_receipt.get("schema") != PROBE_SCHEMA:
        errors.append("probe receipt schema mismatch")
    if probe_receipt.get("status") != "PROBED":
        errors.append("probe receipt status is not PROBED")
    if probe_receipt.get("admission_receipt_id") != (admission_receipt or {}).get("receipt_id"):
        errors.append("probe receipt bound to different admission receipt")
    if probe_receipt.get("contract_version") != contract_version(contract_text):
        errors.append("probe receipt contract version mismatch")
    if probe_receipt.get("contract_sha256") != contract_digest(contract_text):
        errors.append("probe receipt contract hash mismatch")
    caps = probe_receipt.get("capabilities") or {}
    if not caps:
        errors.append("probe receipt capabilities missing")
    elif probe_receipt.get("capabilities_digest") != canonical_digest({str(k): str(v) for k, v in sorted(caps.items())}):
        errors.append("probe receipt capabilities digest mismatch")
    if not str(probe_receipt.get("host", "")).strip():
        errors.append("probe receipt host missing")
    if not str(probe_receipt.get("probed_at", "")).strip():
        errors.append("probe receipt timestamp missing")
    if not str(probe_receipt.get("receipt_id", "")).startswith("PRB-"):
        errors.append("probe receipt id invalid")
    return not errors, list(dict.fromkeys(errors))


def require_probe_receipt(
    probe_receipt: dict[str, Any] | None,
    admission_receipt: dict[str, Any] | None,
    contract_text: str,
) -> dict[str, Any]:
    ok, errors = validate_probe_receipt(probe_receipt, admission_receipt, contract_text)
    if not ok:
        raise PermissionError("initialization denied: " + "; ".join(errors))
    return probe_receipt or {}


def bootstrap_gate(admission: dict[str, Any] | None) -> tuple[bool, list[str]]:
    admission = admission or {}
    errors: list[str] = []
    if admission.get("status") != "ACCEPTED":
        errors.append("human T&C acceptance is not active")
    if not admission.get("receipt"):
        errors.append("admission receipt missing")
    if not admission.get("probe_receipt"):
        errors.append("probe receipt missing")
    bootstrap = admission.get("bootstrap") or {}
    if bootstrap.get("state") != "ACTIVE":
        errors.append("bootstrap is not ACTIVE")
    return not errors, errors
