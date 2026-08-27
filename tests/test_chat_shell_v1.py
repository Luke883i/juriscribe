from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace

from juriscribe.chat_shell import project_chat_shell, render_chat_shell, validate_rendered_shell
from juriscribe.interaction import interaction_card, mode_entry_card
from juriscribe.modes import MODES


def state(phase, mode="", card=None, *, eligible=False):
    return SimpleNamespace(
        phase=phase,
        mode=mode,
        interaction={"card": card or {}, "history": [], "status": "READY"},
        completion={"eligible": eligible},
        artifacts=[],
    )


class ChatShellV1Tests(unittest.TestCase):
    def test_all_modes_have_one_standard_entry_projection(self):
        expected = {
            "CONTINUATION": "CARICA CAPITOLI PRECEDENTI",
            "GREENFIELD": "FORNISCI CONCEPT",
            "REVIEW": "CARICA TESTO DA REVISIONARE",
            "COMPRESSION & CONSOLIDATION": "CARICA CANONICAL",
        }
        for mode in MODES:
            with self.subTest(mode=mode):
                text = render_chat_shell(state("MODE_SELECTED", mode, mode_entry_card(mode)))
                self.assertIn(expected[mode], text)
                self.assertIn("[…] ALTRO", text)
                ok, errors = validate_rendered_shell(text)
                self.assertTrue(ok, errors)

    def test_stale_mode_card_never_interrupts_autonomous_phase(self):
        stale = mode_entry_card("COMPRESSION & CONSOLIDATION")
        text = render_chat_shell(state("DOD_FROZEN", "COMPRESSION & CONSOLIDATION", stale))
        self.assertIn("| WORKING", text)
        self.assertIn("nessuna decisione umana richiesta", text)
        self.assertNotIn("CARICA CANONICAL", text)

    def test_dynamic_human_decision_is_phase_bound_and_sanitized(self):
        card = interaction_card(
            "HUMAN_DECISION_REQUIRED",
            summary="\x1b[31mScegli\x1b[0m\nora",
            choices=["OPZIONE\x00 1", "ALTRO"],
        )
        text = render_chat_shell(state("HUMAN_DECISION_REQUIRED", "REVIEW", card))
        self.assertNotIn("\x1b", text)
        self.assertNotIn("\x00", text)
        self.assertIn("Scegli ora", text)
        self.assertIn("OPZIONE 1", text)

    def test_projection_is_read_only_and_non_authoritative(self):
        item = state("USER_SETUP_REQUIRED", "GREENFIELD")
        before = copy.deepcopy(item.__dict__)
        projection = project_chat_shell(item)
        self.assertEqual("PROJECTION_ONLY", projection["authority"])
        self.assertEqual(before, item.__dict__)

    def test_shell_is_always_three_bounded_lines(self):
        card = interaction_card("HUMAN_DECISION_REQUIRED", summary="x" * 3000, choices=["y" * 3000, "ALTRO"])
        text = render_chat_shell(state("HUMAN_DECISION_REQUIRED", "REVIEW", card))
        lines = text.splitlines()
        self.assertEqual(3, len(lines))
        self.assertTrue(all(len(line) <= 220 for line in lines))
        self.assertIn("[S] STATO", lines[2])
        self.assertIn("[A] ARTEFATTI", lines[2])
        self.assertIn("[?] AIUTO", lines[2])
        self.assertIn("[…] ALTRO", lines[2])

    def test_completion_does_not_depend_on_stale_interaction_card(self):
        stale = mode_entry_card("GREENFIELD")
        text = render_chat_shell(state("FINAL_REVIEW", "GREENFIELD", stale, eligible=True))
        self.assertIn("| COMPLETE", text)
        self.assertIn("Lavoro completato", text)
        self.assertNotIn("FORNISCI CONCEPT", text)


if __name__ == "__main__":
    unittest.main()
