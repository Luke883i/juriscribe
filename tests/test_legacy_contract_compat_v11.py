from __future__ import annotations

import unittest

from juriscribe.modes import CONTINUATION, GREENFIELD, REVIEW, build_mode_contract, mode_spec


class LegacyContractCompatibilityV11Tests(unittest.TestCase):
    def test_legacy_mode_specs_do_not_gain_cc_fields(self):
        continuation = mode_spec(CONTINUATION)
        greenfield = mode_spec(GREENFIELD)
        review = mode_spec(REVIEW)
        for spec in (continuation, greenfield, review):
            self.assertNotIn("input_roles", spec)
            self.assertNotIn("canonical_material_immutable", spec)
            self.assertNotIn("candidate_material_required", spec)
            self.assertNotIn("mutation_cases_min", spec)

    def test_legacy_v1_contract_shape_has_no_cc_cardinality_field(self):
        common = {
            "request": {"raw": "x"},
            "reticulum": {"status": "PASS", "digest": "RET"},
            "setup": {"status": "ACCEPTED", "accepted": {}},
            "editorial_standard": {"status": "READY", "digest": "ED"},
        }
        fixtures = [
            (CONTINUATION, [{"role": "preceding_chapter", "digest": "A"}], {"status": "READY", "contract_digest": "GEN"}),
            (GREENFIELD, [{"role": "concept_source", "digest": "B"}], {"status": "READY", "contract_digest": "GEN"}),
            (REVIEW, [{"role": "review_target", "digest": "C"}], None),
        ]
        for mode, corpus, generation in fixtures:
            contract = build_mode_contract(mode, corpus=corpus, generation_contract=generation, **common)
            self.assertEqual(contract["schema"], "juriscribe-mode-contract/v1")
            self.assertNotIn("artifact_requirements", contract)
            self.assertNotIn("input_roles", contract["requirements"])


if __name__ == "__main__":
    unittest.main()
