import unittest
from juriscribe.editorial import resolve_editorial_standard,validate_editorial_standard
from juriscribe.modes import CONTINUATION,GREENFIELD,REVIEW,build_mode_contract,required_artifact_roles
from juriscribe.setup import accept_setup,propose_setup
class ModeArchitectureTests(unittest.TestCase):
    def setUp(self): self.reticulum={"status":"PASS","digest":"r"*64}; self.mining={"surface":{"word_count":1000},"style":{"register":"formal"}}
    def _contract(self,mode,request,role,generation=True,overrides=None):
        proposal=propose_setup(self.mining,request,reticulum=self.reticulum,mode=mode); setup=accept_setup(proposal,overrides); editorial=resolve_editorial_standard(mode,setup,request=request,mining=self.mining); gc={"status":"READY","contract_digest":"g"*64} if generation else {"status":"NOT_REQUIRED"}; contract=build_mode_contract(mode,request=request,corpus=[{"role":role,"digest":"a"*64}],reticulum=self.reticulum,setup=setup,editorial_standard=editorial,generation_contract=gc); return setup,editorial,contract
    def test_continuation_requires_final_chapter_and_continuation(self):
        setup,editorial,contract=self._contract(CONTINUATION,{"raw":"capitolo successivo"},"preceding_chapter"); self.assertEqual(contract["status"],"READY"); self.assertTrue(contract["requirements"]["continuation_required"]); self.assertIn("final_chapter",required_artifact_roles(CONTINUATION,setup)); self.assertTrue(validate_editorial_standard(editorial,mode=CONTINUATION)[0])
    def test_greenfield_needs_no_preceding_chapter(self):
        setup,_,contract=self._contract(GREENFIELD,{"raw":"monografia ex novo"},"concept_source"); self.assertEqual(contract["status"],"READY"); self.assertFalse(contract["requirements"]["continuation_required"]); self.assertIn("final_legal_text",required_artifact_roles(GREENFIELD,setup))
    def test_review_report_only_treats_findings_as_output(self):
        setup,_,contract=self._contract(REVIEW,{"raw":"revisione completa"},"review_target",generation=False); self.assertEqual(contract["status"],"READY"); self.assertFalse(contract["requirements"]["revision_required"]); roles=required_artifact_roles(REVIEW,setup); self.assertIn("review_report",roles); self.assertIn("review_findings_register",roles); self.assertNotIn("revised_legal_text",roles)
    def test_review_can_require_revised_text(self):
        setup,_,contract=self._contract(REVIEW,{"raw":"revisione e riscrittura"},"review_target",generation=False,overrides={"review_output":"REPORT_AND_REVISED_TEXT"}); self.assertTrue(contract["requirements"]["revision_required"]); self.assertIn("revised_legal_text",required_artifact_roles(REVIEW,setup))
if __name__=="__main__": unittest.main()
