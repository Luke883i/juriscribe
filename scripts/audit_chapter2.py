from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.quality import audit_chapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a candidate chapter against an external reference chapter without storing corpus text in the repository.")
    parser.add_argument("--chapter", required=True, help="Path to the candidate chapter as extracted UTF-8 text")
    parser.add_argument("--reference", required=True, help="Path to the preceding/reference chapter as extracted UTF-8 text")
    parser.add_argument("--length-min", type=int, required=True)
    parser.add_argument("--length-max", type=int, required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    chapter = Path(args.chapter).read_text(encoding="utf-8")
    reference = Path(args.reference).read_text(encoding="utf-8")
    report = audit_chapter(
        chapter,
        reference_text=reference,
        accepted_setup={"accepted": {"length_words": [args.length_min, args.length_max]}},
    ).record()
    report["audit_subject"] = Path(args.chapter).name
    report["reference_subject"] = Path(args.reference).name
    report["corpus_retention"] = "input texts remain external to the repository"
    report["interpretation"] = {
        "corrected_false_positive": "A complete reader-visible source apparatus must not be classified as absent merely because source-list lines differ from prose locators.",
        "style_rule": "Prose/style metrics exclude bibliography and source apparatus; structural segmentation is evaluated separately.",
        "remaining_evidence_gap": "Claim-to-source-to-pinpoint traceability requires the session claim ledger and artifact-evidence locators; it cannot be inferred from bibliography presence alone.",
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
