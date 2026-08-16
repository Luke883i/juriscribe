from __future__ import annotations

import hashlib
import json
import random
from typing import Any

PROFILE_ID = "JURISCRIBE_PREDELIVERY_SATURATION_V1"
SCHEMA = "juriscribe-predelivery-saturation/v1"
DEFAULT_SEEDS = (101, 211, 307)


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_gate_results(gate_results: dict[str, Any]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for name, raw in sorted((gate_results or {}).items()):
        if isinstance(raw, tuple) and len(raw) == 2:
            eligible, errors = raw
            normalized[str(name)] = {"eligible": bool(eligible), "errors": list(errors or [])}
        elif isinstance(raw, dict):
            normalized[str(name)] = {"eligible": bool(raw.get("eligible")), "errors": list(raw.get("errors") or [])}
        else:
            normalized[str(name)] = {"eligible": bool(raw), "errors": [] if raw else [f"{name} failed"]}
    return normalized


def build_predelivery_saturation(
    *,
    candidate_digest: str,
    generation_contract_digest: str,
    gate_results: dict[str, Any],
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
) -> dict[str, Any]:
    normalized = _normalize_gate_results(gate_results)
    gate_names = list(normalized)
    if not gate_names:
        raise ValueError("predelivery saturation requires at least one gate")
    cycles: list[dict[str, Any]] = []
    seen_findings: set[str] = set()
    state_digests: list[str] = []
    no_novelty_streak = 0
    for cycle_index, seed in enumerate(seeds, 1):
        order = list(gate_names)
        random.Random(seed).shuffle(order)
        findings: list[str] = []
        ordered_results = []
        for name in order:
            result = normalized[name]
            ordered_results.append({"gate": name, "eligible": result["eligible"], "errors": result["errors"]})
            findings.extend(f"{name}: {error}" for error in result["errors"])
            if not result["eligible"] and not result["errors"]:
                findings.append(f"{name}: gate failed without detail")
        new_findings = [item for item in findings if item not in seen_findings]
        seen_findings.update(findings)
        if new_findings:
            no_novelty_streak = 0
        else:
            no_novelty_streak += 1
        semantic_state = {
            "candidate_digest": candidate_digest,
            "generation_contract_digest": generation_contract_digest,
            "gates": normalized,
        }
        state_digest = canonical_digest(semantic_state)
        state_digests.append(state_digest)
        cycles.append({
            "cycle": cycle_index,
            "seed": seed,
            "probe_order": order,
            "gate_results": ordered_results,
            "findings": findings,
            "new_findings": new_findings,
            "state_digest": state_digest,
            "status": "PASS" if not findings else "FAIL",
        })
    all_green = all(item["eligible"] for item in normalized.values())
    fixed_point = len(set(state_digests)) == 1
    no_new_on_rechecks = len(cycles) >= 3 and all(not cycle["new_findings"] for cycle in cycles[1:])
    errors: list[str] = []
    if not all_green:
        errors.append("one or more predelivery gates are not PASS")
    if not fixed_point:
        errors.append("predelivery gate vector did not reach a stable fixed point")
    if not no_new_on_rechecks:
        errors.append("predelivery re-checks introduced new findings")
    record = {
        "schema": SCHEMA,
        "profile": PROFILE_ID,
        "candidate_digest": candidate_digest,
        "generation_contract_digest": generation_contract_digest,
        "probe_seeds": list(seeds),
        "cycles": cycles,
        "no_novelty_streak": no_novelty_streak,
        "fixed_point": fixed_point,
        "all_gates_green": all_green,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    return record


def predelivery_saturation_gate(
    record: dict[str, Any] | None,
    *,
    candidate_digest: str | None = None,
    generation_contract_digest: str | None = None,
) -> tuple[bool, list[str]]:
    if not record:
        return False, ["predelivery saturation receipt missing"]
    errors = list(record.get("errors") or [])
    if record.get("schema") != SCHEMA:
        errors.append("predelivery saturation schema mismatch")
    if record.get("status") != "PASS":
        errors.append("predelivery saturation is not PASS")
    if record.get("fixed_point") is not True:
        errors.append("predelivery saturation fixed point not reached")
    if record.get("all_gates_green") is not True:
        errors.append("predelivery saturation contains a failing gate")
    if len(record.get("cycles") or []) < 3:
        errors.append("predelivery saturation requires at least three cyclic re-checks")
    if candidate_digest is not None and record.get("candidate_digest") != candidate_digest:
        errors.append("predelivery saturation bound to stale candidate")
    if generation_contract_digest is not None and record.get("generation_contract_digest") != generation_contract_digest:
        errors.append("predelivery saturation bound to stale generation contract")
    expected = canonical_digest({k: v for k, v in record.items() if k != "digest"})
    if record.get("digest") != expected:
        errors.append("predelivery saturation digest mismatch")
    return not errors, list(dict.fromkeys(errors))
