import unittest

from juriscribe.benchmark import BenchmarkChapter, BlindBenchmarkEnvelope, benchmark_gate, canonical_digest
from juriscribe.convergence import completion_gate
from juriscribe.quality import analyze_reference_apparatus, audit_chapter, claim_traceability, compare_editorial_style
from juriscribe.sources import ClaimRecord, SourceRecord

REFERENCE = """CAPITOLO 1\n1.1 Quadro generale\n""" + ("Anzitutto il problema richiede una ricostruzione ordinata; tuttavia la regola deve essere qualificata nel suo contesto. " * 80)

CANDIDATE_OVERSECTIONED = "CAPITOLO 2\n" + "\n".join(
    f"2.{i} Sezione {i}\n" + ("Anzitutto il problema richiede una ricostruzione ordinata; tuttavia la regola deve essere qualificata nel suo contesto. " * 8)
    for i in range(1, 14)
)

SOURCE_APPARATUS = (
    "CAPITOLO 2\n2.1 Regole\n" +
    " ".join(f"La proposizione {i} è circostanziata. {i}" for i in range(1, 14)) +
    "\nFonti verificate del capitolo\n" +
    "\n".join(f"{i}. Fonte istituzionale {i}." for i in range(1, 14))
)


class RuntimeV3AuditTests(unittest.TestCase):
    def test_style_excludes_source_appendix(self):
        candidate = REFERENCE + "\nFonti verificate del capitolo\n1. Fonte.\n2. Fonte molto breve."
        comparison = compare_editorial_style(REFERENCE, candidate)
        self.assertLess(comparison["deltas"]["avg_sentence_words"], 0.05)

    def test_complete_source_apparatus_is_not_misclassified_as_invisible(self):
        result = analyze_reference_apparatus(SOURCE_APPARATUS)
        self.assertEqual(result["declared_source_count"], 13)
        self.assertEqual(result["used_source_count"], 13)
        self.assertEqual(result["status"], "PASS")

    def test_style_flags_oversectioning_separately_from_sentence_rhythm(self):
        style = compare_editorial_style(REFERENCE, CANDIDATE_OVERSECTIONED)
        self.assertLessEqual(style["deltas"]["avg_sentence_words"], 0.25)
        self.assertGreater(style["deltas"]["heading_density"], 0.75)
        self.assertEqual(style["status"], "REVIEW_REQUIRED")

    def test_claim_traceability_requires_artifact_locator(self):
        source = SourceRecord("S1", "Norma", "u", "primary_law", direct_read=True).record()
        claim = ClaimRecord("C1", "Regola", "direct", "scope", support_source_ids=("S1",), status="SUPPORTED").record()
        result = claim_traceability([claim], [source], [])
        self.assertEqual(result["status"], "GAPS_OPEN")
        result = claim_traceability([claim], [source], [{"claim_id": "C1", "artifact_locator": "§2.1 ¶3 n.1", "source_ids": ["S1"]}])
        self.assertEqual(result["status"], "PASS")

    def test_quality_blocks_missing_claim_locator_but_not_valid_source_appendix(self):
        source = SourceRecord("S1", "Norma", "u", "primary_law", direct_read=True).record()
        claim = ClaimRecord("C1", "Regola", "direct", "scope", support_source_ids=("S1",), status="SUPPORTED").record()
        text = "CAPITOLO 2\n2.1 A\nLa regola è questa. 1\nFonti verificate del capitolo\n1. Norma."
        quality = audit_chapter(text, accepted_setup={"accepted": {"length_words": [1, 100]}}, claims=[claim], sources=[source], artifact_evidence=[])
        self.assertEqual(quality.reference_apparatus["status"], "PASS")
        self.assertEqual(quality.status, "FAIL")

    def test_blind_benchmark_requires_external_commitment(self):
        actual = BenchmarkChapter("A", "Actual", "N+1", ["Alpha rule", "Beta exception"])
        commitment = canonical_digest(actual.record())
        generated = BenchmarkChapter("G", "Generated", "N+1", ["Alpha rule", "Beta exception"])
        envelope = BlindBenchmarkEnvelope.seal_generation(
            monograph="M", author="A", domain="law", prior_context=[{"title": "N"}],
            hidden_reference_commitment=commitment, generated=generated,
        )
        record = envelope.reveal(actual)
        self.assertEqual(record["score"]["blind_integrity"], "PASS")
        self.assertTrue(benchmark_gate(record, required=True)["eligible"])

    def test_benchmark_bad_commitment_fails(self):
        actual = BenchmarkChapter("A", "Actual", "N+1", ["Alpha"])
        generated = BenchmarkChapter("G", "Generated", "N+1", ["Alpha"])
        envelope = BlindBenchmarkEnvelope.seal_generation(
            monograph="M", author="A", domain="law", prior_context=[],
            hidden_reference_commitment="0" * 64, generated=generated,
        )
        record = envelope.reveal(actual)
        self.assertFalse(benchmark_gate(record, required=True)["eligible"])

    def test_completion_mutations_really_block(self):
        dod = [{"id": "D", "status": "DONE", "blocking": True}]
        metrics = {"dod_no_novelty_streak": 10000}
        base = completion_gate(dod, metrics, [], quality={"status": "PASS"}, source_coverage="PASS", artifacts=[{"readback": "PASS", "required": True}])
        self.assertTrue(base["eligible"])
        self.assertFalse(completion_gate(dod, metrics, [], quality={"status": "FAIL"}, source_coverage="PASS")["eligible"])
        self.assertFalse(completion_gate(dod, metrics, [], quality={"status": "PASS"}, source_coverage="GAPS_OPEN")["eligible"])
        self.assertFalse(completion_gate(dod, metrics, [{"status": "OPEN", "blocking": True}], quality={"status": "PASS"}, source_coverage="PASS")["eligible"])


if __name__ == "__main__":
    unittest.main()
