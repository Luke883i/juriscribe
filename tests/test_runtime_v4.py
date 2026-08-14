import json,tempfile,unittest
from pathlib import Path
from juriscribe.admission import issue_receipt,validate_receipt,contract_digest
from juriscribe.benchmark import BenchmarkChapter,BlindBenchmarkEnvelope,canonical_digest
from juriscribe.convergence import ConvergenceMonitor,completion_gate
from juriscribe.dashboard import render_session_dashboard
from juriscribe.epistemic import EpistemicUnit,Relation,contradiction_pairs
from juriscribe.generation import REQUIRED_EDGE_FAMILIES,audit_compression,validate_simulation_receipt
from juriscribe.mining import deep_mine
from juriscribe.orchestrator import ingest_and_mine,register_semantic_mining,apply_setup,freeze_dods
from juriscribe.pipeline import initialize
from juriscribe.quality import compare_editorial_style,analyze_reference_apparatus,audit_chapter
from juriscribe.reticulum import validate_reticulum,build_generation_contract,generation_contract_valid
from juriscribe.session import Workspace
from juriscribe.setup import propose_setup
from juriscribe.sources import SourceRecord,ClaimRecord,validate_claim,validate_inference_graph,assess_dominance

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=(ROOT/'ISENECA_ACCESS_CONTRACT.md').read_text(encoding='utf-8')
SAMPLE="""CAPITOLO 1\n\nAnzitutto, il problema richiede una ricostruzione ordinata. Tuttavia, la regola deve essere qualificata nel suo contesto.\n\nNe consegue che la conclusione dipende dalla premessa, salvo i limiti esplicitati. Pertanto il capitolo prepara il tema successivo."""

def receipt(): return issue_receipt(CONTRACT,phrase='I ACCEPT',actor_type='human',evidence_type='explicit_user_message',user_message='I ACCEPT',accepted_at='2026-01-01T00:00:00+00:00')
def ret_fixture():
    units=[
      {'id':'U1','kind':'DEFINITION','text':'Definizione','source_id':'S1','source_locator':'P1','chapter':'1','material':True,'tags':['preserve']},
      {'id':'U2','kind':'RULE','text':'Regola','source_id':'S1','source_locator':'P2','chapter':'1','material':True,'tags':['preserve']},
      {'id':'U3','kind':'OPEN_ISSUE','text':'Questione','source_id':'S2','source_locator':'P1','chapter':'2','material':False,'tags':['develop']},
      {'id':'U4','kind':'CLAIM','text':'Tesi intermedia','source_id':'S2','source_locator':'P2','chapter':'2','material':True,'tags':[]},]
    rel=[{'source':'U1','predicate':'DEFINES','target':'U2','rationale':'r'},{'source':'U2','predicate':'ANTICIPATES','target':'U3','rationale':'r'},{'source':'U3','predicate':'DEVELOPS','target':'U4','rationale':'r'}]
    return units,rel

class AdmissionTests(unittest.TestCase):
    def test_exact_human_acceptance_issues_receipt(self):
        r=receipt(); ok,errors=validate_receipt(r,CONTRACT); self.assertTrue(ok,errors); self.assertEqual(r['contract_sha256'],contract_digest(CONTRACT))
    def test_ai_cannot_be_receipt_actor(self):
        with self.assertRaises(PermissionError): issue_receipt(CONTRACT,phrase='I ACCEPT',actor_type='ai',evidence_type='explicit_user_message',user_message='I ACCEPT')
    def test_non_exact_phrase_rejected(self):
        with self.assertRaises(PermissionError): issue_receipt(CONTRACT,phrase='accept',actor_type='human',evidence_type='explicit_user_message',user_message='accept')
    def test_stale_receipt_rejected(self):
        r=receipt(); r['contract_sha256']='0'*64; self.assertFalse(validate_receipt(r,CONTRACT)[0])
    def test_initialize_fails_closed_without_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError): initialize('Scrivi capitolo',root=tmp,session_id='SES',contract_text=CONTRACT)
    def test_initialize_accepts_valid_receipt_and_host_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=initialize('Scrivi capitolo',root=tmp,session_id='SES',contract_text=CONTRACT,admission_receipt=receipt(),host_capabilities={'WEB_RESEARCH':'AVAILABLE'})
            state=json.loads((base/'state.json').read_text(encoding='utf-8')); self.assertEqual(state['admission']['status'],'ACCEPTED'); self.assertEqual(state['runtime']['capabilities']['WEB_RESEARCH'],'AVAILABLE')

class EpistemicReticulumTests(unittest.TestCase):
    def test_epistemic_primitive_and_contradiction_dedup(self):
        self.assertEqual(EpistemicUnit('E','CLAIM','x','S').record()['kind'],'CLAIM'); rel=[Relation('A','CONTRADICTS','B').record(),Relation('B','CONTRADICTS','A').record()]; self.assertEqual(contradiction_pairs(rel),[('A','B')])
    def test_deep_mine_requires_semantic_atomization(self):
        self.assertEqual(deep_mine(SAMPLE,source_id='S1')['mining_status'],'SEMANTIC_ATOMIZATION_REQUIRED')
    def test_valid_reticulum_is_deterministic(self):
        u,r=ret_fixture(); a=validate_reticulum(u,r,source_ids={'S1','S2'}); b=validate_reticulum(list(reversed(u)),list(reversed(r)),source_ids={'S1','S2'}); self.assertEqual(a.status,'PASS'); self.assertEqual(a.digest,b.digest)
    def test_material_locator_is_mandatory(self):
        u,r=ret_fixture(); u[0]['source_locator']=''; self.assertEqual(validate_reticulum(u,r,source_ids={'S1','S2'}).status,'FAIL')
    def test_bad_relation_endpoint_is_rejected(self):
        u,r=ret_fixture(); r.append({'source':'U1','predicate':'SUPPORTS','target':'NOPE'}); self.assertEqual(validate_reticulum(u,r,source_ids={'S1','S2'}).status,'FAIL')
    def test_setup_forbidden_before_reticulum(self):
        with self.assertRaises(ValueError): propose_setup(deep_mine(SAMPLE,source_id='S1'),{'raw':'capitolo 2'})
    def test_orchestrator_requires_semantic_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Workspace(tmp,'SES').initialize('Scrivi capitolo II',admission={'status':'ACCEPTED'}); ingest_and_mine(s,SAMPLE,source_id='S1',chapter='1'); self.assertEqual(s.phase,'SEMANTIC_MINING_REQUIRED')
    def test_reticulum_unlocks_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Workspace(tmp,'SES').initialize('Scrivi capitolo III',admission={'status':'ACCEPTED'}); ingest_and_mine(s,SAMPLE,source_id='S1',chapter='1'); ingest_and_mine(s,SAMPLE,source_id='S2',chapter='2'); u,r=ret_fixture(); report=register_semantic_mining(s,u,r); self.assertEqual(report['status'],'PASS'); self.assertEqual(s.phase,'USER_SETUP_REQUIRED')
    def test_generation_contract_stale_on_setup_change(self):
        u,r=ret_fixture(); ret=validate_reticulum(u,r,source_ids={'S1','S2'}).record(); setup={'status':'ACCEPTED','accepted':{'length_words':[1000,1200]}}; gen=build_generation_contract(ret,setup,u,r); changed={'status':'ACCEPTED','accepted':{'length_words':[2000,2200]}}; self.assertFalse(generation_contract_valid(gen,ret,changed)[0])
    def test_freeze_materializes_generation_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Workspace(tmp,'SES').initialize('Scrivi capitolo III',admission={'status':'ACCEPTED'}); ingest_and_mine(s,SAMPLE,source_id='S1',chapter='1'); ingest_and_mine(s,SAMPLE,source_id='S2',chapter='2'); u,r=ret_fixture(); register_semantic_mining(s,u,r); apply_setup(s); freeze_dods(s,[{'id':'D-CONTENT','kind':'CONTENT'}]); self.assertEqual(s.generation_contract['status'],'READY')

class SourceInferenceTests(unittest.TestCase):
    def test_strict_claim_requires_pinpoint(self):
        s=SourceRecord('S','Norma','u','primary_law',direct_read=True).record(); c=ClaimRecord('C','Regola','direct','scope',support_source_ids=('S',),status='SUPPORTED').record(); self.assertFalse(validate_claim(c,[s],[c],strict=True)[0])
    def test_strict_claim_accepts_circumstantiated_source(self):
        s=SourceRecord('S','Norma','u','primary_law',direct_read=True).record(); c=ClaimRecord('C','Regola','direct','scope',support_source_ids=('S',),status='SUPPORTED',source_evidence=({'source_id':'S','pinpoint':'art. 1','proposition':'regola applicabile'},)).record(); self.assertTrue(validate_claim(c,[s],[c],strict=True)[0])
    def test_strong_inference_needs_falsifier(self):
        p={'id':'P','status':'SUPPORTED'}; c={'id':'I','claim_type':'strong_inference','material':True,'premise_claim_ids':['P'],'inference_bridge':'ponte','falsifier':'','support_source_ids':[]}; self.assertFalse(validate_claim(c,[],[p,c],strict=True)[0])
    def test_inference_cycle_rejected(self):
        a={'id':'A','claim_type':'strong_inference','premise_claim_ids':['B']}; b={'id':'B','claim_type':'strong_inference','premise_claim_ids':['A']}; self.assertFalse(validate_inference_graph([a,b])[0])
    def test_dominance_not_from_one_treatise(self):
        s=SourceRecord('S','Trattato','u','leading_treatise',court_or_author='A',direct_read=True).record(); self.assertEqual(assess_dominance('tesi',[s],kind='doctrine')['status'],'DOMINANCE_NOT_ESTABLISHED')

class QualityGenerationTests(unittest.TestCase):
    def test_semantic_saturation_still_requires_1000(self):
        m=ConvergenceMonitor(); [m.semantic_probe(False) for _ in range(999)]; self.assertFalse(m.semantic_saturated); m.semantic_probe(False); self.assertTrue(m.semantic_saturated)
    def test_simulation_requires_edge_family_coverage(self):
        r={'cases':10,'seeds':[1],'families':sorted(REQUIRED_EDGE_FAMILIES),'failures':0,'escapes':0,'status':'PASS'}; self.assertTrue(validate_simulation_receipt(r)[0]); r['families']=r['families'][:-1]; self.assertFalse(validate_simulation_receipt(r)[0])
    def test_compression_rejects_semantic_loss(self):
        r=audit_compression(before_words=1000,after_words=800,required_unit_ids=['A','B'],preserved_unit_ids=['A']); self.assertEqual(r['status'],'FAIL')
    def test_compression_rejects_new_material(self):
        r=audit_compression(before_words=1000,after_words=800,required_unit_ids=['A'],preserved_unit_ids=['A'],added_material_unit_ids=['NEW']); self.assertEqual(r['status'],'FAIL')
    def test_source_appendix_excluded_from_style(self):
        candidate=SAMPLE+'\nBibliografia\n1. Fonte breve.'; self.assertLess(compare_editorial_style(SAMPLE,candidate)['deltas']['avg_sentence_words'],.05)
    def test_reference_apparatus_visible(self):
        text='CAPITOLO 2\n2.1 A\nRegola. 1\nBibliografia\n1. Fonte.'; self.assertEqual(analyze_reference_apparatus(text)['status'],'PASS')
    def test_completion_requires_reticulum_simulation_compression_when_generating(self):
        u,r=ret_fixture(); ret=validate_reticulum(u,r,source_ids={'S1','S2'}).record(); setup={'status':'ACCEPTED','accepted':{'length_words':[1,10]}}; gen=build_generation_contract(ret,setup,u,r); sim={'cases':100,'seeds':[1],'families':sorted(REQUIRED_EDGE_FAMILIES),'failures':0,'escapes':0,'status':'PASS'}; comp=audit_compression(before_words=10,after_words=9,required_unit_ids=['U1'],preserved_unit_ids=['U1']); base=completion_gate([{'id':'D','status':'DONE','blocking':True}],{'dod_no_novelty_streak':10000},[],quality={'status':'PASS'},source_coverage='PASS',artifacts=[{'required':True,'readback':'PASS'}],generation_required=True,reticulum=ret,generation_contract=gen,simulation=sim,compression=comp,setup=setup,admission={'status':'ACCEPTED'}); self.assertFalse(base['eligible']); self.assertIn('scientific-editorial review', base['reason']); self.assertFalse(completion_gate([{'id':'D','status':'DONE','blocking':True}],{'dod_no_novelty_streak':10000},[],quality={'status':'PASS'},source_coverage='PASS',generation_required=True,reticulum=ret,generation_contract=gen,simulation={},compression=comp,setup=setup,admission={'status':'ACCEPTED'})['eligible'])

class DashboardTests(unittest.TestCase):
    def test_dashboard_is_for_jurists_and_editorial_board(self):
        state={'session_id':'SES','phase':'VALIDATING','request':{'summary':'Capitolo III','raw':'Genera Capitolo III'},'admission':{'status':'ACCEPTED'},'reticulum':{'status':'PASS','node_count':3,'relation_count':2,'material_locator_coverage':1.0,'connected_material_coverage':1.0,'cross_chapter_relations':1},'generation_contract':{'status':'READY'},'epistemic_units':[{'id':'U1','kind':'RULE','text':'Regola','chapter':'1','source_locator':'P1','status':'SUPPORTED'}],'relations':[],'sources':[],'setup':{'accepted':{'length_words':[1000,1200]}},'dod':[],'claim_ledger':[],'artifact_evidence':[],'quality':{},'metrics':{},'simulations':{},'compression':{},'completion':{'eligible':False,'reason':'simulation receipt missing'},'artifacts':[],'contradictions':[],'source_intelligence':{},'benchmark':{},'limits':[]}
        with tempfile.TemporaryDirectory() as tmp:
            p=render_session_dashboard(state,Path(tmp)/'d.html'); text=p.read_text(encoding='utf-8'); self.assertIn('NON PRONTO',text); self.assertIn('Mappa scientifica',text); self.assertIn('Review scientifico-editoriale',text); self.assertIn('Simulazioni, saturazione e compressione',text); self.assertNotIn('chain-of-thought</strong>',text)

class BlindBenchmarkTests(unittest.TestCase):
    def test_commitment_protocol(self):
        actual=BenchmarkChapter('A','Actual','N+1',['Alpha','Beta']); commit=canonical_digest(actual.record()); generated=BenchmarkChapter('G','Generated','N+1',['Alpha','Beta']); e=BlindBenchmarkEnvelope.seal_generation(monograph='M',author='A',domain='law',prior_context=[{'n':1}],hidden_reference_commitment=commit,generated=generated); self.assertEqual(e.reveal(actual)['score']['blind_integrity'],'PASS')

if __name__=='__main__': unittest.main()
