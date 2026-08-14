import json,tempfile,unittest
from pathlib import Path
from juriscribe.admission import issue_receipt
from juriscribe.convergence import ConvergenceMonitor
from juriscribe.dashboard import render_session_dashboard
from juriscribe.epistemic import EpistemicUnit,Relation,contradiction_pairs
from juriscribe.pipeline import initialize
ROOT=Path(__file__).resolve().parents[1]; CONTRACT=(ROOT/'ISENECA_ACCESS_CONTRACT.md').read_text(encoding='utf-8')
def receipt(): return issue_receipt(CONTRACT,phrase='I ACCEPT',actor_type='human',evidence_type='explicit_user_message',user_message='I ACCEPT',accepted_at='2026-01-01T00:00:00+00:00')
class KernelTests(unittest.TestCase):
    def test_semantic_saturation_requires_1000_clean_probes(self):
        m=ConvergenceMonitor()
        for _ in range(999): self.assertFalse(m.semantic_probe(False,False))
        self.assertTrue(m.semantic_probe(False,False)); self.assertFalse(m.semantic_probe(True,False))
    def test_epistemic_unit_validation(self): self.assertEqual(EpistemicUnit('EU-1','CLAIM','Una proposizione','SRC-1').record()['kind'],'CLAIM')
    def test_contradiction_deduplicated(self): self.assertEqual(contradiction_pairs([Relation('A','CONTRADICTS','B').record(),Relation('B','CONTRADICTS','A').record()]),[('A','B')])
    def test_dashboard_is_session_specific(self):
        state={'session_id':'SES-test','phase':'VALIDATING','request':{'raw':'Scrivi il capitolo 3','summary':'Scrivi il capitolo 3'},'admission':{'status':'ACCEPTED'},'reticulum':{},'generation_contract':{},'epistemic_units':[],'relations':[],'sources':[{'title':'Capitolo 1'}],'setup':{},'dod':[],'claim_ledger':[],'artifact_evidence':[],'quality':{},'metrics':{},'simulations':{},'compression':{},'completion':{},'artifacts':[],'contradictions':[],'source_intelligence':{},'benchmark':{},'limits':[]}
        with tempfile.TemporaryDirectory() as tmp:
            text=render_session_dashboard(state,Path(tmp)/'dash.html').read_text(encoding='utf-8'); self.assertIn('Scrivi il capitolo 3',text); self.assertIn('Mappa epistemica',text)
    def test_initialize_requires_admission_and_materializes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError): initialize('Riorganizza',root=tmp,session_id='BAD',contract_text=CONTRACT)
            base=initialize('Riorganizza',root=tmp,session_id='SES-x',admission_receipt=receipt(),contract_text=CONTRACT); self.assertTrue((base/'state.json').exists()); self.assertTrue((base/'artifacts'/'session-dashboard.html').exists()); self.assertEqual(json.loads((base/'state.json').read_text())['request']['raw'],'Riorganizza')
if __name__=='__main__': unittest.main()
