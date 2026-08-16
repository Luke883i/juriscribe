import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import juriscribe.pipeline as pipeline


class ArtifactFirstSurfaceV92Tests(unittest.TestCase):
    def test_interaction_surface_is_compact_even_for_large_payload(self):
        raw = json.dumps({"summary": "x" * 2000, "choices": ["A", "B", "C", "D", "E"]})
        text = pipeline._compact_interaction(raw)
        self.assertLessEqual(len(text.splitlines()), 2)
        self.assertLess(len(text), 400)
        self.assertNotIn("E", text.splitlines()[-1])

    def test_default_success_hides_machine_payload(self):
        def fake_main(argv=None):
            print(json.dumps({"SECRET_INTERNAL": "finding ledger provenance receipt"}))
            return 0
        out = io.StringIO()
        with patch.object(pipeline._v9, "main", fake_main), redirect_stdout(out):
            rc = pipeline.main(["research-plan", "/path/without/state"])
        self.assertEqual(rc, 0)
        text = out.getvalue()
        self.assertNotIn("SECRET_INTERNAL", text)
        self.assertEqual(len([line for line in text.splitlines() if line.strip()]), 1)

    def test_exception_and_stderr_are_redacted_from_public_surface(self):
        def fail(argv=None):
            raise ValueError("SECRET_TRACE_DETAIL")
        out = io.StringIO()
        with patch.object(pipeline._v9, "main", fail), patch.object(pipeline, "_record_hidden_failure"), redirect_stdout(out):
            rc = pipeline.main(["gate", "/path/without/state"])
        self.assertEqual(rc, 2)
        text = out.getvalue()
        self.assertNotIn("SECRET_TRACE_DETAIL", text)
        self.assertNotIn("Traceback", text)
        self.assertEqual(len([line for line in text.splitlines() if line.strip()]), 1)

    def test_verbose_json_requires_explicit_dual_opt_in(self):
        def fake_main(argv=None):
            print("RAW_MACHINE_DETAIL")
            return 0

        env_only = io.StringIO()
        with patch.object(pipeline._v9, "main", fake_main), patch.dict(os.environ, {"JURISCRIBE_VERBOSE_JSON": "1"}), redirect_stdout(env_only):
            rc = pipeline.main(["gate", "/path/without/state"])
        self.assertEqual(rc, 0)
        self.assertNotIn("RAW_MACHINE_DETAIL", env_only.getvalue())

        explicit = io.StringIO()
        with patch.object(pipeline._v9, "main", fake_main), patch.dict(os.environ, {"JURISCRIBE_VERBOSE_JSON": "1"}), redirect_stdout(explicit):
            rc = pipeline.main(["--technical-output", "gate", "/path/without/state"])
        self.assertEqual(rc, 0)
        self.assertIn("RAW_MACHINE_DETAIL", explicit.getvalue())


if __name__ == "__main__": unittest.main()
