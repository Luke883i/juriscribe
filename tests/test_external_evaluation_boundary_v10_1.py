import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evaluation"
ORACLE_PATH = EVAL_DIR / "reference_oracle.py"
DATASET_PATH = EVAL_DIR / "cases_v101.json"


def load_oracle():
    spec = importlib.util.spec_from_file_location("juriscribe_external_reference_oracle", ORACLE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ExternalEvaluationBoundaryV101Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = load_oracle()
        cls.dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    def test_evaluation_sidecar_cannot_import_runtime(self):
        for path in EVAL_DIR.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imported = [node.module or ""]
                else:
                    continue
                self.assertFalse(
                    any(name == "juriscribe" or name.startswith("juriscribe.") for name in imported),
                    f"evaluation sidecar must not import runtime code: {path}: {imported}",
                )

    def test_seed_dataset_is_valid_and_has_reserved_cases(self):
        errors = self.oracle.validate_dataset(self.dataset)
        self.assertEqual(errors, [], errors)
        receipt = self.oracle.dataset_receipt(self.dataset)
        self.assertEqual(receipt["status"], "PASS")
        self.assertGreaterEqual(receipt["train_count"], 1)
        self.assertGreaterEqual(receipt["reserved_count"], 2)
        self.assertEqual(receipt["training_eligible_count"], receipt["train_count"])

    def test_training_export_excludes_eval_and_holdout(self):
        records = self.oracle.build_training_records(self.dataset)
        exported = {record["case_id"] for record in records}
        train = {case["case_id"] for case in self.dataset["cases"] if case["split"] == "train"}
        reserved = {case["case_id"] for case in self.dataset["cases"] if case["split"] in {"eval", "holdout"}}
        self.assertEqual(exported, train)
        self.assertTrue(exported.isdisjoint(reserved))

    def test_runtime_generated_gold_is_rejected(self):
        poisoned = json.loads(json.dumps(self.dataset))
        target = next(case for case in poisoned["cases"] if case["split"] == "train")
        target["annotation"]["runtime_generated_ideal_output"] = True
        self.assertFalse(self.oracle.training_eligible(target))
        with self.assertRaises(ValueError):
            self.oracle.build_training_records(poisoned)

    def test_single_reviewer_gold_is_rejected(self):
        poisoned = json.loads(json.dumps(self.dataset))
        target = next(case for case in poisoned["cases"] if case["split"] == "train")
        target["annotation"]["reviewer_count"] = 1
        self.assertFalse(self.oracle.training_eligible(target))
        with self.assertRaises(ValueError):
            self.oracle.build_training_records(poisoned)

    def test_case_order_is_metamorphically_invariant(self):
        reversed_dataset = dict(self.dataset)
        reversed_dataset["cases"] = list(reversed(self.dataset["cases"]))
        original = self.oracle.dataset_receipt(self.dataset)
        transformed = self.oracle.dataset_receipt(reversed_dataset)
        for field in ["status", "case_count", "train_count", "reserved_count", "training_eligible_count", "errors"]:
            self.assertEqual(original[field], transformed[field])

    def test_cli_materializes_only_training_seed(self):
        records = self.oracle.build_training_records(self.dataset)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "seed.jsonl"
            out.write_text(
                "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            parsed = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(parsed), 2)
        self.assertTrue(all(item["case_id"].startswith("train-") for item in parsed))


if __name__ == "__main__":
    unittest.main()
