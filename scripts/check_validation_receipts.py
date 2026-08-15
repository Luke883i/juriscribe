from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_payload(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_payload(value)).hexdigest()


def differing_top_level_keys(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    keys = sorted(set(expected) | set(actual))
    return [key for key in keys if expected.get(key) != actual.get(key)]


def check(expected_path: Path, actual_path: Path) -> dict[str, Any]:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    expected_digest = digest(expected)
    actual_digest = digest(actual)
    result = {
        "expected": str(expected_path),
        "actual": str(actual_path),
        "expected_digest": expected_digest,
        "actual_digest": actual_digest,
        "semantic_fixed_point": expected_digest == actual_digest,
        "differing_top_level_keys": differing_top_level_keys(expected, actual) if isinstance(expected, dict) and isinstance(actual, dict) else [],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare validation receipts by canonical JSON semantics, not file formatting.")
    parser.add_argument("expected")
    parser.add_argument("actual")
    args = parser.parse_args()
    result = check(Path(args.expected), Path(args.actual))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["semantic_fixed_point"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
