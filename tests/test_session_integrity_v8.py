import json,tempfile,unittest
from juriscribe.node_header import write_node_header
from juriscribe.session import Workspace
from juriscribe.session_integrity import CANONICAL_FILENAME
class SessionIntegrityMigrationTests(unittest.TestCase):
    def test_workspace_writes_only_canonical_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws=Workspace(tmp,'SES'); state=ws.initialize('Genera il capitolo successivo'); self.assertEqual(ws.integrity_path.name,CANONICAL_FILENAME); self.assertTrue(ws.integrity_path.exists()); self.assertFalse(ws.node_path.exists()); self.assertTrue(ws.validate_integrity(state)[0])
    def test_canonical_manifest_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws=Workspace(tmp,'SES'); state=ws.initialize('Genera'); payload=json.loads(ws.integrity_path.read_text(encoding='utf-8')); payload['bindings']['phase']='COMPLETE'; ws.integrity_path.write_text(json.dumps(payload),encoding='utf-8'); ok,errors=ws.validate_integrity(state); self.assertFalse(ok); self.assertTrue(any('bindings.phase mismatch' in error for error in errors),errors)
    def test_legacy_projection_is_optional_after_contract_1_6(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws=Workspace(tmp,'SES'); state=ws.initialize('Genera'); self.assertFalse(ws.node_path.exists()); self.assertTrue(ws.validate_integrity(state)[0]); ws.node_path.write_text('tampered legacy file',encoding='utf-8'); self.assertTrue(ws.validate_integrity(state)[0])
    def test_valid_legacy_workspace_migrates_one_way_to_canonical_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws=Workspace(tmp,'SES'); state=ws.initialize('Genera'); data=state.to_dict(); write_node_header(data,ws.node_path); ws.integrity_path.unlink(); loaded=ws.load(); self.assertTrue(ws.integrity_path.exists()); self.assertTrue(ws.validate_integrity(loaded)[0])
    def test_manifest_contains_no_raw_corpus_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws=Workspace(tmp,'SES'); state=ws.initialize('richiesta-segreta'); state.corpus.append({'source_id':'S1','raw':'testo-giuridico-segreto'}); ws.save(state); text=ws.integrity_path.read_text(encoding='utf-8'); self.assertNotIn('richiesta-segreta',text); self.assertNotIn('testo-giuridico-segreto',text)
if __name__=='__main__': unittest.main()
