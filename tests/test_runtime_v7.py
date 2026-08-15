import unittest

from juriscribe.bootstrap import bootstrap_card, issue_probe_receipt, validate_probe_receipt
from juriscribe.final_review import CRITERIA, build_final_review, final_review_gate
from juriscribe.interaction import interaction_card, validate_interaction_card
from juriscribe.provenance import build_provenance_bundle, final_artifact_gate, provenance_gate
from juriscribe.admission import issue_receipt

CONTRACT = """---\ncontract_version: 1.5.0\n---\ncontract body\n"""

def admission(): return issue_receipt(CONTRACT, phrase="I ACCEPT", actor_type="human", evidence_type="explicit_user_message", user_message="I ACCEPT", accepted_at="2026-01-01T00:00:00+00:00")

class BootstrapV7Tests(unittest.TestCase):
    def test_probe_receipt_is_separate_and_contract_bound(self):
        adm=admission(); probe=issue_probe_receipt(adm,CONTRACT,{"WEB_RESEARCH":"AVAILABLE","LOCAL_SCRATCH_IO":"AVAILABLE"},host="test",probed_at="2026-01-01T00:01:00+00:00")
        self.assertTrue(validate_probe_receipt(probe,adm,CONTRACT)[0]); stale=dict(probe,contract_sha256="0"*64); self.assertFalse(validate_probe_receipt(stale,adm,CONTRACT)[0])
    def test_bootstrap_card_keeps_user_visible_next_action(self):
        card=bootstrap_card("PROBE_REQUIRED",contract_version="1.5.0"); self.assertEqual(card["choices"][0],"PROBE JURISCRIBE"); self.assertIn("ALTRO",card["choices"])

class InteractionV7Tests(unittest.TestCase):
    def test_every_standard_card_has_free_path(self):
        for phase in ["TERMS_PRESENTED","PROBE_REQUIRED","INITIALIZE_REQUIRED","ACTIVE","USER_SETUP_REQUIRED","COMPLETE"]:
            card=interaction_card(phase); self.assertTrue(validate_interaction_card(card)[0],phase); self.assertIn("ALTRO",card["choices"]); self.assertTrue(card["free_input_allowed"])
    def test_card_digest_detects_tampering(self):
        card=interaction_card("COMPLETE"); card["choices"]=["APRI ARTEFATTI"]; self.assertFalse(validate_interaction_card(card)[0])

class ProvenanceV7Tests(unittest.TestCase):
    def _bundle(self):
        units=[{"id":"I1","kind":"INFERENCE","material":True}]; claims=[{"id":"C1","material":True,"claim_type":"direct"},{"id":"I2","material":True,"claim_type":"strong_inference"}]; interaction={"history":[{"id":"D1","kind":"USER_DECISION","value":"accetta"}]}
        entries=[
            {"id":"I1","kind":"INFERENCE","proposition":"inferenza 1","disposition":"IN_FINAL","rationale":"necessaria","artifact_locators":["§2"],"evidence_refs":["S1"],"premise_ids":["P1"],"inference_bridge":"ponte","falsifier":"F1"},
            {"id":"I2","kind":"INFERENCE","proposition":"inferenza 2","disposition":"SUPERSEDED","rationale":"sostituita","artifact_locators":[],"evidence_refs":["S2"],"premise_ids":["C1"],"inference_bridge":"ponte","falsifier":"F2"},
            {"id":"C1","kind":"CLAIM","proposition":"claim","disposition":"IN_FINAL","rationale":"supportato","artifact_locators":["§3"],"evidence_refs":["S3"]},
            {"id":"D1","kind":"USER_DECISION","proposition":"decisione utente","disposition":"IN_FINAL","rationale":"parametro accettato","artifact_locators":["setup"]},
            {"id":"REGEN-1","kind":"TRANSFORMATION","proposition":"rigenerazione","disposition":"IN_FINAL","rationale":"finding risolto","artifact_locators":["ledger"]},
            {"id":"COMPRESSION-FINAL","kind":"TRANSFORMATION","proposition":"compressione","disposition":"IN_FINAL","rationale":"lossless","artifact_locators":["ledger"]},]
        return build_provenance_bundle(entries,candidate_digest="a"*64,corpus_digest="b"*64,epistemic_units=units,claim_ledger=claims,interaction=interaction,regenerations=[{"x":1}],compression={"status":"PASS"})
    def test_lossless_provenance_covers_inferences_decisions_transformations(self):
        bundle=self._bundle(); self.assertEqual(bundle["status"],"PASS",bundle["errors"]); self.assertEqual(bundle["coverage"],1.0); self.assertTrue(provenance_gate(bundle,candidate_digest="a"*64,corpus_digest="b"*64)[0])
    def test_missing_inference_fails(self):
        bundle=self._bundle(); bundle["entries"]=[e for e in bundle["entries"] if e["id"]!="I2"]; self.assertFalse(provenance_gate(bundle,candidate_digest="a"*64,corpus_digest="b"*64)[0])
    def test_final_artifact_roles_are_complete(self):
        roles=["final_chapter","evidence_dossier","source_register","inference_register","transformation_ledger","session_dashboard"]; artifacts=[{"role":r,"readback":"PASS"} for r in roles]; self.assertTrue(final_artifact_gate(artifacts)[0]); self.assertFalse(final_artifact_gate(artifacts[:-1])[0])

class FinalReviewV7Tests(unittest.TestCase):
    def _record(self):
        evidence=[{"criterion":c,"status":"PASS","locator":f"evidence:{c}","rationale":"checked"} for c in CRITERIA]; probes=[{"id":"CP1","proposition":"tesi","downstream_effect":"effetto","status":"PASS","evidence_ref":"E1"}]
        return build_final_review(candidate_digest="a"*64,corpus_digest="b"*64,normative_frame_digest="c"*64,provenance_digest="d"*64,evidence=evidence,consequence_probes=probes,findings=[])
    def test_final_review_is_bound_to_candidate_corpus_provenance_and_normative_frame(self):
        rec=self._record(); self.assertEqual(rec["status"],"PASS",rec["errors"]); self.assertTrue(final_review_gate(rec,candidate_digest="a"*64,corpus_digest="b"*64,normative_frame_digest="c"*64,provenance_digest="d"*64)[0]); self.assertFalse(final_review_gate(rec,candidate_digest="x"*64,corpus_digest="b"*64,normative_frame_digest="c"*64,provenance_digest="d"*64)[0])
    def test_unresolved_consequence_or_major_finding_blocks(self):
        evidence=[{"criterion":c,"status":"PASS","locator":f"e:{c}"} for c in CRITERIA]; rec=build_final_review(candidate_digest="a",corpus_digest="b",normative_frame_digest="c",provenance_digest="d",evidence=evidence,consequence_probes=[{"id":"CP","proposition":"p","downstream_effect":"e","status":"OPEN"}],findings=[{"severity":"MAJOR","status":"OPEN"}]); self.assertEqual(rec["status"],"FAIL")

if __name__ == "__main__": unittest.main()
