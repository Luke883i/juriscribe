from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from juriscribe.chat_shell import project_chat_shell, render_chat_shell, validate_rendered_shell
from juriscribe.interaction import mode_entry_card, phase_choices
from juriscribe.mode_runtime import MATERIAL_INPUT_CHANGED, invalidate_downstream, mode_runtime_profile
from juriscribe.modes import (
    COMPRESSION_AND_CONSOLIDATION,
    CONTINUATION,
    GREENFIELD,
    MODE_REGISTRY,
    MODES,
    REVIEW,
    mode_choices,
    mode_entry_projection,
    mode_spec,
)
from juriscribe.runtime_router import ROUTES, route_owner, routing_manifest


class RuntimeConvergenceV13Tests(unittest.TestCase):
    def _state(self, mode):
        return SimpleNamespace(
            mode=mode, corpus=[], phase="ACTIVE_WORK", completion={"eligible": False}, interaction={},
            epistemic_units=[{"id": "U"}], relations=[{"id": "R"}], reticulum={"status": "PASS"},
            setup={"status": "ACCEPTED"}, editorial_standard={"status": "READY"}, generation_contract={"status": "READY"},
            mode_contract={"status": "READY"}, continuation={"status": "PASS"}, dod=[{"id": "D"}], drafts=[{"digest": "d"}],
            review={"cycles": [{}], "regenerations": [{}], "saturation": {}, "status": "PASS"}, final_review={"status": "PASS"},
            provenance={"status": "PASS"}, quality={}, benchmark={}, simulations={}, compression={}, claim_ledger=[], artifact_evidence=[],
            contradictions=[], editorial_actions=[], reflection={}, source_intelligence={}, metrics={},
        )

    def test_registry_is_single_four_mode_source_for_runtime_and_entry_projection(self):
        self.assertEqual(tuple(MODE_REGISTRY), MODES)
        for mode in MODES:
            runtime = mode_runtime_profile(mode)
            spec = mode_spec(mode)
            projection = mode_entry_projection(mode)
            card = mode_entry_card(mode)
            self.assertEqual(runtime["default_role"], spec["input_role"])
            self.assertEqual(card["summary"], projection["summary"])
            self.assertEqual(card["choices"], projection["choices"])
        self.assertEqual(phase_choices("MODE_SELECTION_REQUIRED"), [*mode_choices(), "ALTRO"])

    def test_router_makes_previous_effective_owners_explicit(self):
        expected = {
            "select_mode": "juriscribe.runtime_v13.select_mode",
            "ingest_and_mine": "juriscribe.runtime_v13.ingest_and_mine",
            "register_semantic_mining": "juriscribe.runtime_v13.register_semantic_mining",
            "freeze_dods": "juriscribe.runtime_v13.freeze_dods",
            "evaluate_completion": "juriscribe.consolidation_completion.evaluate_completion",
            "register_refactoring_plan": "juriscribe.runtime_cc_v2.register_refactoring_plan",
        }
        for operation, owner in expected.items():
            self.assertEqual(route_owner(operation), owner)
        manifest = routing_manifest()
        self.assertEqual(manifest["authority"], "EXPLICIT_COMPOSITION_ONLY")
        self.assertEqual(len(ROUTES), len(set(ROUTES)))

    def test_common_staleness_remains_owned_and_projection_stays_non_authoritative(self):
        state = self._state(CONTINUATION)
        invalidate_downstream(state, boundary=MATERIAL_INPUT_CHANGED, reason="changed")
        self.assertEqual(state.epistemic_units, [])
        self.assertEqual(state.setup, {})
        self.assertEqual(state.drafts, [])
        self.assertFalse(state.completion["eligible"])
        state.interaction = {"card": mode_entry_card(CONTINUATION)}
        projection = project_chat_shell(state)
        self.assertEqual(projection["status"], "WORKING")
        self.assertEqual(projection["choices"], [])

    def test_shell_is_bounded_for_every_mode_entry(self):
        for mode in (CONTINUATION, GREENFIELD, REVIEW, COMPRESSION_AND_CONSOLIDATION):
            state = self._state(mode)
            state.phase = "MODE_SELECTED"
            text = render_chat_shell(state)
            ok, errors = validate_rendered_shell(text)
            self.assertTrue(ok, errors)
            self.assertEqual(len(text.splitlines()), 3)
            self.assertIn("[…] ALTRO", text)

    def test_source_files_do_not_reintroduce_import_order_or_pipeline_monkey_patch(self):
        root = Path(__file__).resolve().parents[1]
        orchestrator = (root / "juriscribe/orchestrator.py").read_text(encoding="utf-8")
        pipeline = (root / "juriscribe/pipeline_v11.py").read_text(encoding="utf-8")
        self.assertNotIn("from .runtime_cc_v2 import", orchestrator)
        self.assertNotIn("_v9.bootstrap_after_acceptance =", pipeline)
        self.assertIn('resolve_operation("select_mode")', orchestrator)
        self.assertIn('resolve_operation("register_refactoring_plan")', pipeline)


if __name__ == "__main__":
    unittest.main()
