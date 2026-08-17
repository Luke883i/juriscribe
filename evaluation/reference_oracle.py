from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "juriscribe-external-eval/v1"
ELIGIBLE_LABEL_ORIGINS = {"independent_human_gold", "external_reference"}
ADJUDICATED_STATUSES = {"AGREED", "ADJUDICATED"}
TRAIN_SPLIT = "train"
RESERVED_EVAL_SPLITS = {"eval", "holdout"}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _nonempty(case.get("case_id")):
        errors.append("case_id missing")
    split = case.get("split")
    if split not in {TRAIN_SPLIT, *RESERVED_EVAL_SPLITS}:
        errors.append("split must be train, eval or holdout")

    task = case.get("task") or {}
    if not _nonempty(task.get("instruction")):
        errors.append("task.instruction missing")
    if not _nonempty(task.get("ideal_output")):
        errors.append("task.ideal_output missing")

    annotation = case.get("annotation") or {}
    if annotation.get("label_origin") not in ELIGIBLE_LABEL_ORIGINS:
        errors.append("annotation.label_origin is not independent")
    if int(annotation.get("reviewer_count") or 0) < 2:
        errors.append("annotation.reviewer_count must be at least 2")
    if annotation.get("adjudication_status") not in ADJUDICATED_STATUSES:
        errors.append("annotation.adjudication_status is not adjudicated")
    if annotation.get("runtime_generated_ideal_output") is not False:
        errors.append("ideal_output must not be runtime-generated")

    provenance = case.get("provenance") or {}
    if not _nonempty(provenance.get("source_class")):
        errors.append("provenance.source_class missing")
    if not _nonempty(provenance.get("source_locator")):
        errors.append("provenance.source_locator missing")

    rubric = case.get("rubric") or {}
    dimensions = rubric.get("dimensions") or []
    if not dimensions or not all(_nonempty(item) for item in dimensions):
        errors.append("rubric.dimensions must contain non-empty entries")
    return errors


def training_eligible(case: dict[str, Any]) -> bool:
    return case.get("split") == TRAIN_SPLIT and not validate_case(case)


def validate_dataset(dataset: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if dataset.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    cases = dataset.get("cases") or []
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        return errors

    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case[{index}] must be an object")
            continue
        case_id = str(case.get("case_id") or "")
        if case_id in seen:
            errors.append(f"duplicate case_id {case_id}")
        seen.add(case_id)
        for error in validate_case(case):
            errors.append(f"{case_id or index}: {error}")

    splits = {case.get("split") for case in cases if isinstance(case, dict)}
    if TRAIN_SPLIT not in splits:
        errors.append("dataset requires at least one train case")
    if not (splits & RESERVED_EVAL_SPLITS):
        errors.append("dataset requires at least one reserved eval or holdout case")
    return errors


def build_training_records(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    errors = validate_dataset(dataset)
    if errors:
        raise ValueError("invalid external evaluation dataset: " + "; ".join(errors))

    records: list[dict[str, Any]] = []
    for case in dataset["cases"]:
        if case.get("split") in RESERVED_EVAL_SPLITS:
            continue
        if not training_eligible(case):
            raise ValueError(f"training case {case.get('case_id')} is not independently adjudicated")
        records.append(
            {
                "case_id": case["case_id"],
                "input": case["task"]["instruction"],
                "ideal_output": case["task"]["ideal_output"],
                "rubric_dimensions": list(case["rubric"]["dimensions"]),
                "label_origin": case["annotation"]["label_origin"],
                "source_class": case["provenance"]["source_class"],
            }
        )
    return records


def dataset_receipt(dataset: dict[str, Any]) -> dict[str, Any]:
    errors = validate_dataset(dataset)
    cases = dataset.get("cases") or []
    return {
        "schema": "juriscribe-external-eval-receipt/v1",
        "status": "PASS" if not errors else "FAIL",
        "dataset_digest": canonical_digest(dataset),
        "case_count": len(cases),
        "train_count": sum(1 for case in cases if case.get("split") == TRAIN_SPLIT),
        "reserved_count": sum(1 for case in cases if case.get("split") in RESERVED_EVAL_SPLITS),
        "training_eligible_count": sum(1 for case in cases if training_eligible(case)),
        "errors": errors,
        "interpretation": (
            "mechanical independence and contamination firewall only; "
            "does not prove substantive legal correctness"
        ),
    }


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent Juriscribe evaluation-sidecar oracle")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--training-jsonl", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    dataset = _load(args.dataset)
    receipt = dataset_receipt(dataset)
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    if receipt["status"] != "PASS":
        return 1

    if args.training_jsonl:
        records = build_training_records(dataset)
        payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
        args.training_jsonl.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
