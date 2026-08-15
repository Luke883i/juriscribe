from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

PLAN_SCHEMA = "juriscribe-continuation-plan/v1"
COVERAGE_SCHEMA = "juriscribe-continuation-coverage/v1"
HORIZONS = {"NOW", "LATER", "OPTIONAL"}
PRIORITIES = {"CORE", "SUPPORTING", "OPTIONAL"}
MODES = {
    "ARGUMENT", "COUNTERARGUMENT", "CASE_FAMILY", "HISTORICAL",
    "DOCTRINAL", "DISTINCTION", "APPLICATION", "SYNTHESIS",
}
COVERAGE_STATUSES = {"DEVELOPED", "PARTIAL", "ABSENT", "DEFERRED"}
EVIDENCE_MODES = {"text", "source", "case", "comparison", "inference", "editorial"}
INTRODUCTION_BINDING_STATUSES = {"VERIFIED", "REAUDIT_REQUIRED"}
DEFAULT_CORE_DEPTH = 0.65
DEFAULT_MINIMUM_COVERAGE = 0.72


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _mode_for_unit(unit: dict[str, Any]) -> str:
    kind = str(unit.get("kind", ""))
    tags = {str(t).lower() for t in unit.get("tags", [])}
    if "case_family" in tags or kind == "CASE":
        return "CASE_FAMILY"
    if kind == "COUNTERARGUMENT" or "counterargument" in tags:
        return "COUNTERARGUMENT"
    if kind in {"QUESTION", "OPEN_ISSUE", "QUALIFICATION", "EXCEPTION"}:
        return "DISTINCTION"
    if kind == "DOCTRINE":
        return "DOCTRINAL"
    return "ARGUMENT"


def derive_continuation_plan(
    generation_contract: dict[str, Any],
    units: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a conservative development frontier from the validated reticulum.

    The plan deliberately does *not* predict an author's exact next outline. It turns
    reticular development candidates into auditable coverage obligations, plus
    non-binding alternatives. A host may enrich the plan before drafting, but exact
    section order can never become a completion requirement.
    """
    by_id = {str(u.get("id")): u for u in units if u.get("id")}
    develop_ids = [str(x) for x in generation_contract.get("develop_unit_ids", [])]
    develop_set = set(develop_ids)
    obligations: list[dict[str, Any]] = []
    for uid in develop_ids:
        unit = by_id.get(uid, {})
        obligations.append({
            "id": f"DEV-{uid}",
            "unit_ids": [uid],
            "mode": _mode_for_unit(unit),
            "priority": "CORE",
            "horizon": "NOW",
            "deferrable": False,
            "minimum_depth": DEFAULT_CORE_DEPTH,
            "rationale": f"Develop reticulum unit {uid} selected by generation contract",
        })

    existing_modes = {(o["mode"], tuple(o["unit_ids"])) for o in obligations}
    for relation in relations:
        src, dst = str(relation.get("source", "")), str(relation.get("target", ""))
        pred = relation.get("predicate")
        if not ({src, dst} & develop_set):
            continue
        other_id = dst if src in develop_set else src
        other = by_id.get(other_id, {})
        if pred == "CONTRADICTS":
            mode = "COUNTERARGUMENT"
        elif pred == "APPLIES_TO" or other.get("kind") == "CASE":
            mode = "CASE_FAMILY"
        else:
            continue
        key = (mode, (other_id,))
        if key in existing_modes:
            continue
        existing_modes.add(key)
        obligations.append({
            "id": f"DEV-{mode}-{other_id}",
            "unit_ids": [other_id],
            "mode": mode,
            "priority": "SUPPORTING",
            "horizon": "NOW",
            "deferrable": True,
            "minimum_depth": 0.50,
            "rationale": f"Reticulum relation {pred} makes {other_id} relevant to the continuation",
        })

    uncertainty_score = round(
        min(1.0, 0.12 * max(len(develop_ids) - 1, 0) + (0.15 if len(relations) < max(len(units), 1) else 0.0)),
        3,
    )
    obligation_ids = [o["id"] for o in obligations]
    alternatives = []
    if obligation_ids:
        alternatives.append({
            "id": "ALT-CORE",
            "obligation_ids": obligation_ids,
            "emphasis": "core-first",
            "binding_order": False,
        })
    if len(obligation_ids) >= 2:
        alternatives.append({
            "id": "ALT-EVIDENCE",
            "obligation_ids": list(reversed(obligation_ids)),
            "emphasis": "evidence-first",
            "binding_order": False,
        })
    plan = {
        "schema": PLAN_SCHEMA,
        "generation_contract_digest": generation_contract.get("contract_digest", ""),
        "obligations": obligations,
        "alternatives": alternatives,
        "uncertainty_score": uncertainty_score,
        "minimum_coverage_score": DEFAULT_MINIMUM_COVERAGE,
        "concrete_validation_required": any(o["mode"] in {"CASE_FAMILY", "APPLICATION"} for o in obligations),
        "sequence_is_binding": False,
        "status": "PASS",
    }
    ok, errors = validate_continuation_plan(plan, generation_contract, units)
    plan["status"] = "PASS" if ok else "FAIL"
    plan["errors"] = errors
    plan["digest"] = canonical_digest({k: v for k, v in plan.items() if k != "digest"})
    return plan


def validate_continuation_plan(
    plan: dict[str, Any] | None,
    generation_contract: dict[str, Any],
    units: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    if not plan:
        return False, ["continuation plan missing"]
    errors: list[str] = []
    if plan.get("schema") != PLAN_SCHEMA:
        errors.append("continuation plan schema mismatch")
    if plan.get("generation_contract_digest") != generation_contract.get("contract_digest"):
        errors.append("continuation plan bound to stale generation contract")
    if plan.get("sequence_is_binding") is not False:
        errors.append("continuation plan may not make exact section order a completion requirement")
    known_units = {str(u.get("id")) for u in units if u.get("id")}
    required = {str(x) for x in generation_contract.get("develop_unit_ids", [])}
    if not required:
        errors.append("generation contract has no auditable development frontier")
    obligation_ids: set[str] = set()
    covered_required: set[str] = set()
    for obligation in plan.get("obligations", []):
        oid = str(obligation.get("id", "")).strip()
        if not oid:
            errors.append("continuation obligation id missing")
            continue
        if oid in obligation_ids:
            errors.append(f"duplicate continuation obligation {oid}")
        obligation_ids.add(oid)
        if obligation.get("mode") not in MODES:
            errors.append(f"continuation obligation {oid} has invalid mode")
        if obligation.get("priority") not in PRIORITIES:
            errors.append(f"continuation obligation {oid} has invalid priority")
        if obligation.get("horizon") not in HORIZONS:
            errors.append(f"continuation obligation {oid} has invalid horizon")
        if not str(obligation.get("rationale", "")).strip():
            errors.append(f"continuation obligation {oid} lacks rationale")
        try:
            minimum_depth = float(obligation.get("minimum_depth", DEFAULT_CORE_DEPTH if obligation.get("priority") == "CORE" else 0.50))
        except (TypeError, ValueError):
            minimum_depth = -1.0
        if not 0.0 <= minimum_depth <= 1.0:
            errors.append(f"continuation obligation {oid} has invalid minimum_depth")
        unit_ids = {str(x) for x in obligation.get("unit_ids", [])}
        if not unit_ids:
            errors.append(f"continuation obligation {oid} has no unit ids")
        unknown = sorted(unit_ids - known_units)
        if unknown:
            errors.append(f"continuation obligation {oid} references unknown units: {', '.join(unknown)}")
        covered_required.update(unit_ids & required)
    missing = sorted(required - covered_required)
    if missing:
        errors.append("generation-contract development units missing from continuation plan: " + ", ".join(missing))
    try:
        uncertainty = float(plan.get("uncertainty_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        uncertainty = -1.0
    if not 0.0 <= uncertainty <= 1.0:
        errors.append("continuation uncertainty score outside 0..1")
    try:
        minimum_coverage = float(plan.get("minimum_coverage_score", DEFAULT_MINIMUM_COVERAGE))
    except (TypeError, ValueError):
        minimum_coverage = -1.0
    if not 0.50 <= minimum_coverage <= 1.0:
        errors.append("continuation minimum coverage score outside 0.50..1.0")
    alternatives = plan.get("alternatives", []) or []
    if uncertainty >= 0.60 and len(alternatives) < 2:
        errors.append("high-uncertainty continuation requires at least two alternatives")
    for alternative in alternatives:
        refs = {str(x) for x in alternative.get("obligation_ids", [])}
        if refs - obligation_ids:
            errors.append(f"continuation alternative {alternative.get('id')} references unknown obligations")
        if alternative.get("binding_order") is True:
            errors.append("continuation alternatives may not make exact section order a completion requirement")
    return not errors, list(dict.fromkeys(errors))


def audit_continuation_coverage(
    plan: dict[str, Any] | None,
    coverage: list[dict[str, Any]] | None,
    *,
    introduced_material_unit_ids: list[str] | None = None,
    introduced_material_bindings: list[dict[str, Any]] | None = None,
    candidate_digest: str = "",
) -> dict[str, Any]:
    errors: list[str] = []
    if not plan or plan.get("status") != "PASS":
        return {
            "schema": COVERAGE_SCHEMA,
            "status": "FAIL",
            "errors": ["valid continuation plan required"],
            "digest": canonical_digest({"status": "FAIL", "reason": "plan"}),
        }
    obligations = {str(o["id"]): o for o in plan.get("obligations", []) if o.get("id")}
    raw_records = [r for r in (coverage or []) if r.get("obligation_id")]
    records = {str(r.get("obligation_id")): r for r in raw_records}
    if len(records) != len(raw_records):
        errors.append("duplicate continuation coverage records")
    unknown_records = sorted(set(records) - set(obligations))
    if unknown_records:
        errors.append("coverage references unknown obligations: " + ", ".join(unknown_records))

    core_now = [o for o in obligations.values() if o.get("priority") == "CORE" and o.get("horizon") == "NOW"]
    core_ids = {str(o.get("id")) for o in core_now}
    unresolved_core: list[str] = []
    developed_later: list[str] = []
    mode_counts: Counter[str] = Counter()
    weighted_possible = 0.0
    weighted_earned = 0.0

    weights = {"CORE": 3.0, "SUPPORTING": 1.5, "OPTIONAL": 0.5}
    for oid, obligation in obligations.items():
        record = records.get(oid, {})
        status = record.get("status", "ABSENT")
        try:
            depth = float(record.get("depth_score", 0.0) or 0.0)
        except (TypeError, ValueError):
            depth = -1.0
        if status not in COVERAGE_STATUSES:
            errors.append(f"coverage {oid} has invalid status")
        if not 0.0 <= depth <= 1.0:
            errors.append(f"coverage {oid} depth outside 0..1")
        if status in {"DEVELOPED", "PARTIAL"} and not str(record.get("artifact_locator", "")).strip():
            errors.append(f"coverage {oid} lacks artifact locator")
        evidence = {str(x) for x in record.get("evidence_modes", [])}
        invalid_evidence = sorted(evidence - EVIDENCE_MODES)
        if invalid_evidence:
            errors.append(f"coverage {oid} has invalid evidence modes: {', '.join(invalid_evidence)}")
        minimum_depth = float(obligation.get("minimum_depth", DEFAULT_CORE_DEPTH if obligation.get("priority") == "CORE" else 0.50))
        if status == "DEVELOPED" and depth >= minimum_depth:
            mode_counts[str(obligation.get("mode"))] += 1
        weight = weights.get(str(obligation.get("priority")), 1.0)
        weighted_possible += weight
        earned_factor = max(depth, 0.0) if status in {"DEVELOPED", "PARTIAL"} else 0.0
        weighted_earned += weight * earned_factor

        if oid in core_ids and (status != "DEVELOPED" or depth < minimum_depth):
            unresolved_core.append(oid)
        if obligation.get("horizon") in {"LATER", "OPTIONAL"} and status == "DEVELOPED" and depth >= max(0.75, minimum_depth):
            developed_later.append(oid)
        if status == "DEFERRED" and not obligation.get("deferrable", False):
            errors.append(f"non-deferrable obligation {oid} was deferred")

    if unresolved_core:
        errors.append("core continuation obligations underdeveloped: " + ", ".join(sorted(unresolved_core)))
    if unresolved_core and developed_later:
        errors.append("premature anticipation: later/optional obligations deeply developed while core obligations remain open")
    if plan.get("concrete_validation_required") and not any(mode_counts[m] > 0 for m in ("CASE_FAMILY", "APPLICATION")):
        errors.append("continuation plan requires concrete case/application validation")

    introduced = sorted({str(x) for x in (introduced_material_unit_ids or []) if str(x)})
    bindings = list(introduced_material_bindings or [])
    bound_ids: set[str] = set()
    for idx, binding in enumerate(bindings):
        uid = str(binding.get("unit_id", "")).strip()
        oid = str(binding.get("obligation_id", "")).strip()
        if not uid:
            errors.append(f"introduced material binding {idx} has no unit_id")
            continue
        if uid not in introduced:
            errors.append(f"introduced material binding {uid} is not declared in introduced_material_unit_ids")
        if oid not in obligations:
            errors.append(f"introduced material binding {uid} references unknown continuation obligation")
        if binding.get("status") not in INTRODUCTION_BINDING_STATUSES:
            errors.append(f"introduced material binding {uid} has invalid status")
        if binding.get("status") == "REAUDIT_REQUIRED":
            errors.append(f"introduced material unit {uid} still requires re-audit")
        if not str(binding.get("rationale", "")).strip():
            errors.append(f"introduced material binding {uid} lacks rationale")
        if not str(binding.get("evidence_ref", "")).strip():
            errors.append(f"introduced material binding {uid} lacks source/inference evidence_ref")
        if binding.get("status") == "VERIFIED" and oid in obligations:
            bound_ids.add(uid)
    unbound = sorted(set(introduced) - bound_ids)
    if unbound:
        errors.append("candidate introduced material units outside the audited continuation frontier: " + ", ".join(unbound))

    coverage_score = round(weighted_earned / weighted_possible, 4) if weighted_possible else 0.0
    minimum_coverage_score = float(plan.get("minimum_coverage_score", DEFAULT_MINIMUM_COVERAGE))
    if coverage_score < minimum_coverage_score:
        errors.append(
            f"continuation weighted coverage {coverage_score:.4f} below minimum {minimum_coverage_score:.4f}"
        )
    result = {
        "schema": COVERAGE_SCHEMA,
        "plan_digest": plan.get("digest", ""),
        "candidate_digest": candidate_digest,
        "status": "PASS" if not errors else "FAIL",
        "coverage_score": coverage_score,
        "minimum_coverage_score": minimum_coverage_score,
        "obligations": len(obligations),
        "core_now": len(core_now),
        "unresolved_core": sorted(unresolved_core),
        "developed_later": sorted(developed_later),
        "mode_counts": dict(sorted(mode_counts.items())),
        "introduced_material_unit_ids": introduced,
        "bound_introduced_material_unit_ids": sorted(bound_ids),
        "unbound_introduced_material_unit_ids": unbound,
        "errors": list(dict.fromkeys(errors)),
    }
    result["digest"] = canonical_digest(result)
    return result


def benchmark_gap_report(
    reference_facets: list[dict[str, Any]],
    candidate_facets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Post-hoc benchmark focused on substantive coverage, not outline imitation."""
    reference = {str(x.get("id")): x for x in reference_facets if x.get("id")}
    candidate = {str(x.get("id")): x for x in candidate_facets if x.get("id")}
    total_weight = sum(float(x.get("weight", 1.0) or 1.0) for x in reference.values()) or 1.0
    covered_ids: set[str] = set()
    underdeveloped: list[str] = []
    hit_weight = 0.0
    for fid, facet in reference.items():
        cand = candidate.get(fid)
        if not cand:
            continue
        minimum_depth = float(facet.get("minimum_depth", 0.50) or 0.50)
        depth = float(cand.get("depth_score", 1.0) or 0.0)
        if depth >= minimum_depth:
            covered_ids.add(fid)
            hit_weight += float(facet.get("weight", 1.0) or 1.0)
        else:
            underdeveloped.append(fid)
    missing_core = sorted(k for k, v in reference.items() if v.get("core", False) and k not in covered_ids)
    surplus = sorted(set(candidate) - set(reference))
    by_category: dict[str, dict[str, int]] = {}
    for item in reference.values():
        cat = str(item.get("category", "other"))
        by_category.setdefault(cat, {"reference": 0, "covered": 0})["reference"] += 1
        if str(item.get("id")) in covered_ids:
            by_category[cat]["covered"] += 1
    report = {
        "schema": "juriscribe-blind-continuation-benchmark/v1",
        "weighted_coverage": round(hit_weight / total_weight, 4),
        "missing_core_facets": missing_core,
        "underdeveloped_facets": sorted(underdeveloped),
        "surplus_facets": surplus,
        "category_coverage": by_category,
        "sequence_scoring": "DISABLED",
        "interpretation": "Measures substantive coverage/depth/omission/surplus after reveal; exact section order is not a quality target.",
    }
    report["digest"] = canonical_digest(report)
    return report


def continuation_gate(
    continuation: dict[str, Any] | None,
    *,
    generation_contract_digest: str | None = None,
    candidate_digest: str | None = None,
) -> tuple[bool, list[str]]:
    """Validate persisted development-frontier and candidate-coverage bindings."""
    if not continuation:
        return False, ["continuation development state missing"]
    errors: list[str] = []
    plan = continuation.get("plan") or {}
    coverage = continuation.get("coverage") or {}
    if plan.get("status") != "PASS":
        errors.append("continuation plan is not PASS")
    if generation_contract_digest is not None and plan.get("generation_contract_digest") != generation_contract_digest:
        errors.append("continuation plan bound to stale generation contract")
    if coverage.get("status") != "PASS":
        errors.append("continuation coverage is not PASS")
    if coverage.get("plan_digest") != plan.get("digest"):
        errors.append("continuation coverage bound to stale plan")
    if candidate_digest is not None and coverage.get("candidate_digest") != candidate_digest:
        errors.append("continuation coverage bound to stale candidate")
    return not errors, list(dict.fromkeys(errors))
