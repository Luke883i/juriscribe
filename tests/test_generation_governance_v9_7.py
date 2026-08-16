import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from juriscribe.artifact_atlas import artifact_dashboard_coverage_gate, build_artifact_atlas
from juriscribe.artifact_governance import _govern_materialized_narrative
from juriscribe.dashboard_v97 import render_session_dashboard
from juriscribe.generation_configuration import (
    build_generation_configuration_contract,
    enrich_setup_proposal,
    generation_conformance,
)
from juriscribe.plagiarism import audit_plagiarism, fingerprint_text
from juriscribe.saturation import build_predelivery_saturation, predelivery_saturation_gate


class GenerationGovernanceV97Tests(unittest.TestCase):
    def test_generation_preview_becomes_mechanical_contract(self):
        proposal = {
            "status": "USER_SETUP_REQUIRED",
            "mode": "GREENFIELD",
            "recommended": {"length_words": [80, 140]},
            "parameters": [],
        }
        enriched = enrich_setup_proposal(
            proposal,
            request={"summary": "Analisi della proporzionalità nel diritto amministrativo"},
            units=[
                {"id": "U1", "kind": "RULE", "text": "La proporzionalità richiede adeguatezza necessità e bilanciamento.", "material": True},
                {"id": "U2", "kind": "QUALIFICATION", "text": "Il sindacato varia in relazione al margine amministrativo.", "material": True},
            ],
            mining={"surface": {"recurrent_terms": ["proporzionalità", "necessità"]}},
        )
        self.assertIn("generation_preview", enriched)
        self.assertTrue(enriched["generation_preview"]["abstract"])
        self.assertTrue(enriched["generation_preview"]["key_concepts"])
        self.assertEqual(enriched["generation_preview"]["length_words"], [80, 140])
        setup = {"status": "ACCEPTED", "accepted": dict(enriched["recommended"])}
        contract = build_generation_configuration_contract(setup)
        self.assertEqual(contract["status"], "READY")
        concepts = " ".join(contract["key_concepts"])
        abstract_terms = " ".join(contract["abstract"].split()[:12])
        candidate = (concepts + " " + abstract_terms + " argomentazione fonte interpretazione giuridica " * 30).strip()
        result = generation_conformance(candidate, contract)
        self.assertEqual(result["status"], "PASS", result)
        short = generation_conformance("proporzionalità necessità", contract)
        self.assertEqual(short["status"], "FAIL")

    def test_plagiarism_blocks_exact_and_incomplete_scope_but_allows_attributed_reuse(self):
        source = " ".join(f"termine{i}" for i in range(1, 46))
        reference = fingerprint_text(source, source_id="S1")
        blocked = audit_plagiarism(source, references=[reference], required_source_ids={"S1"}, sealed_candidate_digest="C")
        self.assertEqual(blocked["status"], "FAIL")
        self.assertGreater(blocked["prohibited_findings"], 0)
        missing = audit_plagiarism("testo autonomo sufficientemente distinto", references=[], required_source_ids={"S1"}, sealed_candidate_digest="C")
        self.assertEqual(missing["scope_status"], "INCOMPLETE")
        self.assertEqual(missing["status"], "FAIL")
        attributed = audit_plagiarism(
            source,
            references=[reference],
            required_source_ids={"S1"},
            sealed_candidate_digest="C",
            authorized_reuse=[{"source_id": "S1", "text": source, "attribution_locator": "nota 12"}],
        )
        self.assertEqual(attributed["status"], "PASS", attributed)
        self.assertFalse(attributed["global_uniqueness_claim"])

    def test_predelivery_saturation_requires_stable_rechecks(self):
        good = build_predelivery_saturation(
            candidate_digest="CAND",
            generation_contract_digest="GEN",
            gate_results={"quality": (True, []), "anti_plagiarism": (True, []), "dashboard": (True, [])},
            seeds=(11, 29, 47),
        )
        self.assertEqual(good["status"], "PASS")
        self.assertEqual(len(good["cycles"]), 3)
        self.assertTrue(predelivery_saturation_gate(good, candidate_digest="CAND", generation_contract_digest="GEN")[0])
        bad = build_predelivery_saturation(
            candidate_digest="CAND",
            generation_contract_digest="GEN",
            gate_results={"quality": (True, []), "anti_plagiarism": (False, ["overlap"])},
            seeds=(11, 29, 47),
        )
        self.assertEqual(bad["status"], "FAIL")
        self.assertFalse(predelivery_saturation_gate(bad)[0])

    def _state(self):
        return {
            "request": {"raw": "Mandato distintivo atlante", "summary": "Mandato distintivo atlante"},
            "phase": "VALIDATING",
            "mode": "GREENFIELD",
            "mode_selection": {},
            "mode_contract": {"status": "READY", "requirements": {"generation_required": True}},
            "editorial_standard": {"document_type": "LEGAL_ARTICLE", "audience": "giuristi", "rules": {"formal_register": True}},
            "corpus": [],
            "sources": [{"id": "S1", "title": "Fonte distintiva dashboard", "source_type": "primary_law", "direct_read": True, "verified_at": "2026-08-16"}],
            "bibliography": {"available": True, "entries": ["Voce bibliografica distintiva"], "status": "PASS"},
            "epistemic_units": [{"id": "C1", "kind": "RULE", "text": "Proposizione epistemica distintiva", "source_id": "S1", "source_locator": "art. 1", "status": "VERIFIED", "material": True}],
            "relations": [],
            "reticulum": {"status": "PASS", "errors": []},
            "generation_contract": {"status": "READY", "governance_profile": "JURISCRIBE_GENERATION_GOVERNANCE_V1", "generation_configuration": {"status": "READY", "abstract": "Abstract distintivo dashboard", "key_concepts": ["concetto distintivo"], "length_words": [100, 200]}},
            "continuation": {},
            "drafts": [{"stage": "COMPRESSED_FINAL", "word_count": 150}],
            "review": {"cycles": [{"cycle": 1, "findings": [{"id": "F1", "message": "Finding distintivo dashboard", "severity": "MINOR"}]}], "regenerations": [], "saturation": {"status": "PASS"}, "delivery_saturation": {"status": "PASS", "cycles": [{"cycle": 1, "status": "PASS", "new_findings": []}, {"cycle": 2, "status": "PASS", "new_findings": []}, {"cycle": 3, "status": "PASS", "new_findings": []}]}},
            "final_review": {"status": "PASS", "evidence": [{"criterion": "LEGAL_AUTHORITY", "rationale": "Review finale distintiva"}]},
            "provenance": {"entries": [{"id": "C1", "kind": "CLAIM", "proposition": "Provenance distintiva", "rationale": "ragione", "artifact_locators": ["§1"]}]},
            "contradictions": [],
            "mining": {},
            "style_profile": {},
            "setup": {"status": "ACCEPTED", "accepted": {"document_type": "LEGAL_ARTICLE", "audience": "giuristi", "generation_abstract": "Abstract distintivo dashboard", "key_concepts": ["concetto distintivo"], "length_words": [100, 200]}, "generation_configuration": {"status": "READY", "abstract": "Abstract distintivo dashboard", "key_concepts": ["concetto distintivo"], "length_words": [100, 200]}},
            "source_intelligence": {"coverage_status": "PASS", "research_plan": [{"question": "Questione distintiva fonti"}], "plagiarism_references": [{"source_id": "SECRET", "exact_ngram_hashes": ["NON_VISIBILE"]}]},
            "claim_ledger": [{"id": "C1", "text": "Claim distintivo dashboard", "claim_type": "rule", "scope": "scope", "support_source_ids": ["S1"], "status": "VERIFIED", "material": True}],
            "artifact_evidence": [{"evidence_id": "E1", "claim_id": "C1", "artifact_locator": "§1", "source_ids": ["S1"], "status": "PASS"}],
            "quality": {"status": "PASS", "candidate_digest": "hidden", "generation_configuration": {"status": "PASS", "word_count": 150}, "plagiarism": {"status": "PASS", "scope_status": "COMPLETE_FOR_RUNTIME_VISIBLE_CORPUS", "prohibited_findings": 0, "proof_statement": "Prova originalità distintiva", "covered_source_ids": ["S1"], "missing_source_ids": [], "exact_ngram_hashes": ["NON_VISIBILE"]}},
            "benchmark": {"status": "PASS", "summary": "Benchmark distintivo"},
            "simulations": {"status": "PASS", "cases": 10000, "notes": "Simulazione distintiva"},
            "compression": {"status": "PASS", "before_words": 180, "after_words": 150, "post_compression_recheck": "PASS"},
            "limits": [{"kind": "scope", "summary": "Limite distintivo dashboard"}],
            "strategy": {},
            "dod": [{"id": "DOD-X", "status": "DONE", "expected": "DoD distintivo"}],
            "editorial_actions": [],
            "reflection": {},
            "metrics": {},
            "completion": {"eligible": False},
            "interaction": {},
            "node_integrity": {},
            "runtime": {"workspace_base": "/tmp/secret-dashboard-path"},
            "artifacts": [
                {"id": "final", "role": "final_legal_text", "summary": "Artefatto finale distintivo", "delivery_class": "ATTACH"},
                {"id": "ev", "role": "evidence_dossier", "delivery_class": "ATTACH"},
                {"id": "src", "role": "source_register", "delivery_class": "ATTACH"},
                {"id": "inf", "role": "inference_register", "delivery_class": "ATTACH"},
                {"id": "tr", "role": "transformation_ledger", "delivery_class": "ATTACH"},
                {"id": "dash", "role": "session_dashboard", "delivery_class": "ATTACH"},
            ],
        }

    def test_artifact_information_is_materialized_in_dashboard(self):
        state = self._state()
        atlas = build_artifact_atlas(state)
        ok, errors = artifact_dashboard_coverage_gate(state, atlas)
        self.assertTrue(ok, errors)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dashboard.html"
            render_session_dashboard(state, path)
            page = path.read_text(encoding="utf-8")
        body = page.split("<body>", 1)[1].split("</body>", 1)[0]
        for token in [
            "Abstract distintivo dashboard", "concetto distintivo", "Fonte distintiva dashboard",
            "Finding distintivo dashboard", "Review finale distintiva", "Provenance distintiva",
            "Prova originalità distintiva", "Simulazione distintiva", "Limite distintivo dashboard",
            "Atlante completo degli artefatti", "Artefatti materiali", "Artefatti epistemici",
        ]:
            self.assertIn(token, body, token)
        for forbidden in ["/tmp/secret-dashboard-path", "NON_VISIBILE", "exact_ngram_hashes", "plagiarism_references", "sha256", "readback"]:
            self.assertNotIn(forbidden, body, forbidden)
        self.assertIn("#18344c", page)
        self.assertIn("#713641", page)
        self.assertIn("#9c7a3b", page)

    def _write_docx(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body></w:document>'
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"></Types>")
            zf.writestr("_rels/.rels", "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"></Relationships>")
            zf.writestr("word/document.xml", document)

    def test_materialized_narrative_is_rechecked_and_bound_to_sealed_candidate(self):
        text = ("proporzionalità necessità bilanciamento fonte argomentazione giuridica " * 20).strip()
        fp = fingerprint_text(text, source_id="SEALED")
        config = {"schema": "juriscribe-generation-configuration/v1", "profile": "JURISCRIBE_GENERATION_CONFIGURATION_V1", "abstract": "proporzionalità necessità bilanciamento", "key_concepts": ["proporzionalità", "necessità"], "length_words": [80, 180], "abstract_term_coverage_min": 0.3, "key_concept_policy": "ALL_REQUIRED", "status": "READY", "errors": [], "digest": "cfg"}
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = base / "artifacts" / "final.docx"
            self._write_docx(path, text)
            state = SimpleNamespace(
                runtime={"workspace_base": str(base)}, setup={"status": "ACCEPTED", "generation_configuration": config, "accepted": {"generation_abstract": config["abstract"], "key_concepts": config["key_concepts"], "length_words": config["length_words"]}},
                generation_contract={"status": "READY", "generation_configuration": config},
                strategy={"generation_governance": {"sealed_candidate_fingerprints": {"CAND": fp}}},
                drafts=[{"digest": "CAND"}], corpus=[], claim_ledger=[], source_intelligence={}, artifacts=[], mode="GREENFIELD",
            )
            proof = _govern_materialized_narrative(state, {"role": "final_legal_text", "path": str(path), "readback": "PASS"})
            self.assertEqual(proof["status"], "PASS", proof)
            self.assertEqual(proof["sealed_candidate_binding"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
