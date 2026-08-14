import tempfile,unittest
from juriscribe.convergence import ConvergenceMonitor,completion_gate
from juriscribe.mining import deep_mine,mine_style,compare_style
from juriscribe.orchestrator import ingest_and_mine,register_semantic_mining,apply_setup,freeze_dods
from juriscribe.session import Workspace
from juriscribe.setup import propose_setup,accept_setup,parameter_dods
from juriscribe.sources import SourceRecord,ClaimRecord,validate_claim,assess_dominance
SAMPLE="""CAPITOLO I - Legalità e tecnica\n\nAnzitutto, il problema non consiste nel contrapporre decisione umana e tecnica. Tuttavia, l'opacità non coincide sempre con illegittimità.\n\nNe consegue che la motivazione deve rendere intelligibile il percorso, salvo limiti proporzionati. Pertanto, la conoscibilità costituisce una condizione del controllo."""
def ret():
    u=[{'id':'U1','kind':'DEFINITION','text':'D','source_id':'SRC1','source_locator':'P1','chapter':'I','material':True},{'id':'U2','kind':'RULE','text':'R','source_id':'SRC1','source_locator':'P2','chapter':'I','material':True},{'id':'U3','kind':'CLAIM','text':'C','source_id':'SRC1','source_locator':'P2','chapter':'I','material':True}]; r=[{'source':'U1','predicate':'DEFINES','target':'U2'},{'source':'U2','predicate':'SUPPORTS','target':'U3'}]; return u,r
class RuntimeV2RegressionTests(unittest.TestCase):
    def test_deep_mining_extracts_style(self):
        result=deep_mine(SAMPLE,source_id='SRC-1',chapter='I'); self.assertGreater(result['surface']['word_count'],30); self.assertIn('tuttavia',result['style']['dominant_connectors'])
    def test_setup_requires_reticulum_and_stays_minimal(self):
        mining=deep_mine(SAMPLE,source_id='SRC1'); u,r=ret(); from juriscribe.reticulum import validate_reticulum; rr=validate_reticulum(u,r,source_ids={'SRC1'}).record(); proposal=propose_setup(mining,{'raw':'Scrivi capitolo II'},reticulum=rr); self.assertEqual(proposal['simple_options'],['ACCETTA CONSIGLIATI','MODIFICA']); self.assertEqual(len(proposal['parameters']),4)
    def test_parameters_become_blocking_dods(self):
        mining=deep_mine(SAMPLE,source_id='SRC1'); u,r=ret(); from juriscribe.reticulum import validate_reticulum; proposal=propose_setup(mining,{'raw':'Scrivi capitolo II'},reticulum=validate_reticulum(u,r,source_ids={'SRC1'}).record()); accepted=accept_setup(proposal,{'length_words':[1800,2200]}); dods=parameter_dods(accepted); self.assertTrue(all(d['blocking'] for d in dods))
    def test_completion_legacy_gate_still_requires_dod_and_10000(self):
        d=[{'id':'D','status':'DONE','blocking':True}]; self.assertFalse(completion_gate(d,{'dod_no_novelty_streak':9999},[])['eligible']); self.assertTrue(completion_gate(d,{'dod_no_novelty_streak':10000},[])['eligible'])
    def test_strong_inference_contract_preserved(self):
        source=SourceRecord('S1','Norma','u','primary_law',direct_read=True).record(); premise=ClaimRecord('C1','Premessa','direct','scope',support_source_ids=('S1',),status='SUPPORTED').record(); inf=ClaimRecord('C2','Inferenza','strong_inference','scope',premise_claim_ids=('C1',),inference_bridge='ponte',falsifier='fonte contraria',status='INFERRED').record(); self.assertTrue(validate_claim(inf,[source],[premise,inf])[0])
    def test_dominance_never_from_single_source(self):
        source=SourceRecord('S1','Commento','u','leading_treatise',court_or_author='A',direct_read=True).record(); self.assertEqual(assess_dominance('tesi',[source])['status'],'DOMINANCE_NOT_ESTABLISHED')
    def test_style_compare_is_auditable(self):
        c=compare_style(mine_style(SAMPLE).record(),SAMPLE); self.assertEqual(c['mean_relative_deviation'],0.0); self.assertTrue(c['register_match'])
    def test_lifecycle_now_requires_reticulum_before_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Workspace(tmp,'SES').initialize('Scrivi II'); ingest_and_mine(s,SAMPLE,source_id='SRC1',chapter='I'); self.assertEqual(s.phase,'SEMANTIC_MINING_REQUIRED'); u,r=ret(); register_semantic_mining(s,u,r); self.assertEqual(s.phase,'USER_SETUP_REQUIRED'); apply_setup(s); freeze_dods(s,[{'id':'DOD-CONTENT','kind':'CONTENT'}]); self.assertEqual(s.generation_contract['status'],'READY')
if __name__=='__main__': unittest.main()
