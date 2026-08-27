from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from juriscribe import mode_runtime
from juriscribe.mode_runtime import (
    MATERIAL_INPUT_CHANGED,
    SEMANTIC_MODEL_CHANGED,
    assert_input_transition,
    invalidate_downstream,
    mode_runtime_profile,
    validate_mode_corpus,
)
from juriscribe.modes import COMPRESSION_AND_CONSOLIDATION, CONTINUATION, GREENFIELD, REVIEW


class ModeRuntimeV13Tests(unittest.TestCase):
    def _state(self, mode, corpus=None):
        return SimpleNamespace(
            mode=mode,
            corpus=list(corpus or []),
            epistemic_units=[{"id": "U-old"}], relations=[{"id": "R-old"}], reticulum={"status": "PASS"},
            setup={"status": "ACCEPTED"}, editorial_standard={"status": "READY"},
            generation_contract={"status": "READY"}, mode_contract={"status": "READY"},
            continuation={"plan": {"old": True}, "coverage": {"status": "PASS"}, "benchmark_gap": {}, "status": "PASS"},
            dod=[{"id": "D1", "status": "DONE"}], drafts=[{"digest": "old"}],
            review={"cycles": [{"status": "PASS"}], "regenerations": [{}], "saturation": {"status": "PASS"}, "delivery_saturation": {"status": "PASS"}, "status": "PASS"},
            final_review={"status": "PASS"}, provenance={"status": "PASS"}, quality={"status": "PASS"}, benchmark={"status": "PASS"},
            simulations={"status": "PASS"}, compression={"status": "PASS"}, claim_ledger=[{"id": "C1"}], artifact_evidence=[{"id": "E1"}],
            source_intelligence={"research_plan": [1], "dominance_assessments": [1], "coverage_status": "PASS", "plagiarism_references": [{"source_id": "keep"}]},
            metrics={"semantic_no_novelty_streak": 10, "strategy_no_improvement_streak": 10, "dod_no_novelty_streak": 10, "review_no_novelty_streak": 10, "review_no_improvement_streak": 10, "simulations_run": 10, "simulation_failures": 1},
            completion={"eligible": True}, interaction={}, contradictions=[{"id": "X"}], editorial_actions=[{"id": "A"}], reflection={"iterations": 10, "no_novelty_streak": 10, "target": 1000, "saturated": True},
        )

    def test_profiles_share_spine_but_keep_specific_engines(self):
        profiles = [mode_runtime_profile(mode) for mode in (CONTINUATION, GREENFIELD, REVIEW, COMPRESSION_AND_CONSOLIDATION)]
        self.assertEqual(len({tuple(item["common_stages"]) for item in profiles}), 1)
        self.assertEqual(len({item["engine_family"] for item in profiles}), 4)
        self.assertIn("CONTINUATION_FRONTIER", profiles[0]["specific_stages"])
        self.assertIn("DIAGNOSTIC_REVIEW", profiles[2]["specific_stages"])
        self.assertIn("MUTATION_EVIDENCE", profiles[3]["specific_stages"])

    def test_role_firewall_is_mode_specific(self):
        self.assertEqual(assert_input_transition(self._state(CONTINUATION), source_id="c1"), "preceding_chapter")
        with self.assertRaises(ValueError):
            assert_input_transition(self._state(CONTINUATION), source_id="c1", role="review_target")

    def test_greenfield_and_review_are_single_target_but_reingestable(self):
        green = self._state(GREENFIELD, [{"source_id": "g1", "role": "concept_source"}])
        self.assertEqual(assert_input_transition(green, source_id="g1"), "concept_source")
        with self.assertRaises(ValueError):
            assert_input_transition(green, source_id="g2")
        review = self._state(REVIEW, [{"source_id": "r1", "role": "review_target"}])
        self.assertEqual(assert_input_transition(review, source_id="r1"), "review_target")
        with self.assertRaises(ValueError):
            assert_input_transition(review, source_id="r2")

    def test_source_role_cannot_drift(self):
        state = self._state(COMPRESSION_AND_CONSOLIDATION, [{"source_id": "x", "role": "canonical_material"}])
        with self.assertRaises(ValueError):
            assert_input_transition(state, source_id="x", role="candidate_material")

    def test_cc_requires_both_reference_and_candidate_before_semantics(self):
        ok, errors = validate_mode_corpus(COMPRESSION_AND_CONSOLIDATION, [{"source_id": "cand", "role": "candidate_material"}], require_minimum=True)
        self.assertFalse(ok)
        self.assertTrue(any("canonical_material" in error for error in errors))
        ok, errors = validate_mode_corpus(COMPRESSION_AND_CONSOLIDATION, [
            {"source_id": "canon", "role": "canonical_material"},
            {"source_id": "cand", "role": "candidate_material"},
        ], require_minimum=True)
        self.assertTrue(ok, errors)

    def test_material_change_invalidates_full_downstream_cone(self):
        for mode in (CONTINUATION, GREENFIELD, REVIEW, COMPRESSION_AND_CONSOLIDATION):
            state = self._state(mode)
            invalidate_downstream(state, boundary=MATERIAL_INPUT_CHANGED, reason="changed")
            self.assertEqual(state.epistemic_units, [])
            self.assertEqual(state.reticulum, {})
            self.assertEqual(state.setup, {})
            self.assertEqual(state.drafts, [])
            self.assertEqual(state.provenance, {})
            self.assertFalse(state.completion["eligible"])
            self.assertEqual(state.source_intelligence["plagiarism_references"], [{"source_id": "keep"}])
            self.assertEqual(state.metrics["simulations_run"], 0)
            self.assertEqual(state.contradictions, [])
            self.assertEqual(state.editorial_actions, [])
            self.assertFalse(state.reflection["saturated"])

    def test_semantic_change_preserves_current_semantics_but_invalidates_proofs(self):
        state = self._state(GREENFIELD)
        invalidate_downstream(state, boundary=SEMANTIC_MODEL_CHANGED, reason="changed")
        self.assertEqual(state.epistemic_units, [{"id": "U-old"}])
        self.assertEqual(state.reticulum, {"status": "PASS"})
        self.assertEqual(state.setup, {})
        self.assertEqual(state.drafts, [])
        self.assertFalse(state.completion["eligible"])

    def test_duplicate_corpus_identity_fails_closed(self):
        ok, errors = validate_mode_corpus(CONTINUATION, [
            {"source_id": "dup", "role": "preceding_chapter"},
            {"source_id": "dup", "role": "preceding_chapter"},
        ])
        self.assertFalse(ok)
        self.assertTrue(any("duplicate corpus source_id" in error for error in errors))

    def test_unknown_invalidation_boundary_rejected(self):
        with self.assertRaises(ValueError):
            invalidate_downstream(self._state(GREENFIELD), boundary="UNKNOWN", reason="x")


class ModeRuntimeOverlayV13Tests(unittest.TestCase):
    def _state(self, mode, corpus=None):
        return ModeRuntimeV13Tests()._state(mode, corpus)
    def test_overlay_rejects_wrong_role_before_specialist_engine(self):
        from juriscribe import runtime_v13
        state = self._state(CONTINUATION)
        with patch.object(runtime_v13._runtime, "ingest_and_mine") as delegate:
            with self.assertRaises(ValueError):
                runtime_v13.ingest_and_mine(state, "x", source_id="s1", role="review_target")
        delegate.assert_not_called()

    def test_overlay_invalidates_old_proofs_after_valid_ingestion(self):
        from juriscribe import runtime_v13
        state = self._state(GREENFIELD)
        def fake_ingest(target, text, **kwargs):
            target.corpus = [{"source_id": kwargs["source_id"], "role": kwargs["role"]}]
            return target
        with patch.object(runtime_v13._runtime, "ingest_and_mine", side_effect=fake_ingest) as delegate:
            runtime_v13.ingest_and_mine(state, "concept", source_id="g1")
        self.assertEqual(delegate.call_args.kwargs["role"], "concept_source")
        self.assertEqual(state.corpus, [{"source_id": "g1", "role": "concept_source"}])
        self.assertEqual(state.setup, {})
        self.assertEqual(state.drafts, [])
        self.assertFalse(state.completion["eligible"])

    def test_overlay_blocks_semantics_until_mode_input_minimum_is_satisfied(self):
        from juriscribe import runtime_v13
        state = self._state(COMPRESSION_AND_CONSOLIDATION, [{"source_id": "cand", "role": "candidate_material"}])
        with patch.object(runtime_v13._runtime, "register_semantic_mining") as delegate:
            with self.assertRaises(ValueError):
                runtime_v13.register_semantic_mining(state, [], [])
        delegate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
