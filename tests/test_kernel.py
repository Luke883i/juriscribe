import json,tempfile,unittest
from pathlib import Path
from juriscribe.admission import issue_receipt
from juriscribe.convergence import ConvergenceMonitor
from juriscribe.dashboard import render_session_dashboard
from juriscribe.epistemic import EpistemicUnit,Relation,contradiction_pairs
from juriscribe.pipeline import initialize,perform_probe
ROOT=Path(__file__).resolve().parents[1]; CONTRACT=(ROOT/'ISENECA_ACCESS_CONTRACT.md').read_text(encoding='utf-8')
def receipt(): return issue_receipt(CONTRACT,phrase='I ACCEPT',actor_type='human',evidence_type='explicit_user_message',user_message='I ACCEPT',accepted_at='2026-01-01T00:00:00+00:00')
def probe_receipt(r): return perform_probe(admission_receipt=r,contract_text=CONTRACT,host='test',probed_at='2026-01-01T00:01:00+00:00')
class KernelTests(unittest.TestCase):
    def test_semantic_saturation_requires_1000_clean_probes(self):
        m=ConvergenceMonitor()
        for _ in range(999): self.assertFalse(m.semantic_probe(False,False))
        self.assertTrue(m.semantic_probe(False,False)); self.assertFalse(m.semantic_probe(True,False))
    def test_epistemic_unit_validation(self): self.assertEqual(EpistemicUnit('EU-1','CLAIM','Una proposizione','SRC-1').record()['kind'],'CLAIM')
    def test_contradiction_deduplicated(self): self.assertEqual(contradiction_pairs([Relation('A','CONTRADICTS','B').record(),Relation('B','CONTRADICTS','A').record()]),[('A','B')])
    def test_dashboard_is_session_and_mode_specific(self):
        state={'session_id':'SES-test','phase':'VALIDATING','mode':'CONTINUATION','request':{'raw':'Scrivi il capitolo 3','summary':'Scrivi il capitolo 3'},'admission':{'status':'ACCEPTED'},'mode_contract':{'status':'READY','required_artifact_roles':['final_chapter']},'editorial_standard':{'status':'READY','standard_id':'JURISCRIBE_LEGAL_EDITORIAL_CORE_V2','document_type':'LEGAL_CHAPTER','audience':'giuristi','rules':{}},'reticulum':{},'continuation':{},'review':{},'provenance':{},'final_review':{},'sources':[{'title':'Capitolo 1'}],'setup':{},'claim_ledger':[],'quality':{},'completion':{},'artifacts':[],'source_intelligence':{},'bibliography':{},'node_integrity':{}}
        with tempfile.TemporaryDirectory() as tmp:
            text=render_session_dashboard(state,Path(tmp)/'dash.html').read_text(encoding='utf-8'); self.assertIn('Scrivi il capitolo 3',text); self.assertIn('Modalità:',text); self.assertIn('Standard redazionali applicati',text)
    def test_initialize_requires_admission_probe_and_materializes_mode_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError): initialize('Riorganizza',root=tmp,session_id='BAD',contract_text=CONTRACT)
            r=receipt()
            with self.assertRaises(PermissionError): initialize('Riorganizza',root=tmp,session_id='NO-PROBE',admission_receipt=r,contract_text=CONTRACT)
            base=initialize('Riorganizza',root=tmp,session_id='SES-x',admission_receipt=r,probe_receipt=probe_receipt(r),contract_text=CONTRACT)
            self.assertTrue((base/'state.json').exists()); self.assertTrue((base/'artifacts'/'session-dashboard.html').exists()); self.assertTrue((base/'session.integrity.json').exists()); state=json.loads((base/'state.json').read_text()); self.assertEqual(state['request']['raw'],'Riorganizza'); self.assertEqual(state['phase'],'MODE_SELECTION_REQUIRED')
if __name__=='__main__': unittest.main()
