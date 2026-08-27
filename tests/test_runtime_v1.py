from __future__ import annotations
import copy, tempfile, unittest
from pathlib import Path

from juriscribe.chat_shell import render_chat_shell, validate_rendered_shell
from juriscribe.continuity import MATERIALIZATION_CONTINUE_PHRASE, MATERIALIZATION_PENDING, archive_material, checkpoint_id, project_iteration, validate_material_archive
from juriscribe.recovery import create_recovery_bundle_bytes, inspect_recovery_bundle
from juriscribe.runtime_router import route_owner

MODES=("CONTINUATION","GREENFIELD","REVIEW","COMPRESSION & CONSOLIDATION")

def state(mode="GREENFIELD"):
    s={"session_id":"SES-test","request":{"raw":"draft"},"phase":"ACTIVE_WORK","mode":mode,"admission":{"status":"ACCEPTED"},"interaction":{"card":{},"history":[]},"corpus":[],"sources":[],"reticulum":{"status":"PASS"},"setup":{"status":"ACCEPTED"},"mode_contract":{"status":"READY"},"generation_contract":{"status":"READY"},"dod":[{"id":"D"}],"drafts":[],"review":{"cycles":[]},"final_review":{},"provenance":{},"strategy":{},"artifacts":[],"completion":{"eligible":False},"runtime":{"host":"host-a","workspace_base":"/old"},"dashboard_persistence":{}}
    if mode=="COMPRESSION & CONSOLIDATION": s["strategy"]["consolidation"]={}
    return s

def finalize(s):
    if s["mode"]=="COMPRESSION & CONSOLIDATION": s["strategy"]["consolidation"].update({"peer_review_readiness":{"status":"PASS"},"provenance":{"status":"PASS"},"final_review":{"status":"PASS"}})
    else: s["provenance"]={"status":"PASS"}; s["final_review"]={"status":"PASS"}

class RuntimeV1Tests(unittest.TestCase):
    def test_exact_runtime_input_archive_and_checkpoint_transport_independence(self):
        s=state(); text="alpha β"; import hashlib
        digest=hashlib.sha256(text.encode()).hexdigest(); s["corpus"]=[{"source_id":"src","role":"concept_source","digest":digest}]
        archive_material(s,text,source_id="src",role="concept_source")
        ok,errors=validate_material_archive(s); self.assertTrue(ok,errors)
        cp=checkpoint_id(s); moved=copy.deepcopy(s); moved["runtime"]={"host":"host-b","workspace_base":"/new"}; moved["phase"]="VALIDATING"; moved["completion"]={"eligible":False}; moved["strategy"]["continuity"]["recovery_lineage"]=[{"source_checkpoint_id":cp}]
        self.assertEqual(cp,checkpoint_id(moved))
        moved["request"]["raw"]="changed"; self.assertNotEqual(cp,checkpoint_id(moved))

    def test_materialization_pending_is_cross_mode_and_exact_phrase_survives_shell(self):
        import juriscribe.continuity as c
        old=c._materialization_requirements; c._materialization_requirements=lambda _:[{"role":"expected","instance_key":"expected","required":True}]
        try:
            for mode in MODES:
                with self.subTest(mode=mode):
                    s=state(mode); finalize(s); p=project_iteration(s)
                    self.assertEqual(MATERIALIZATION_PENDING,p["where"]["status"]); self.assertEqual("MATERIALIZATION",p["next"]["stage"]); self.assertIn(MATERIALIZATION_CONTINUE_PHRASE,p["next"]["how"])
                    shell=render_chat_shell(s); ok,errors=validate_rendered_shell(shell); self.assertTrue(ok,errors); self.assertIn(MATERIALIZATION_CONTINUE_PHRASE,shell.splitlines()[1])
                    s["artifacts"]=[{"role":"expected","instance_key":"expected","path":"expected.docx","readback":"PASS"}]; self.assertNotEqual(MATERIALIZATION_PENDING,project_iteration(s)["where"]["status"])
        finally: c._materialization_requirements=old

    def test_recovery_bundle_roundtrip_is_readback_verified(self):
        s=state(); data=create_recovery_bundle_bytes(s); r=inspect_recovery_bundle(data); self.assertEqual("PASS",r["status"],r["errors"]); self.assertEqual(checkpoint_id(s),r["manifest"]["checkpoint_id"]); self.assertTrue(r["manifest"]["fresh_host_probe_required_on_resume"])

    def test_recovery_export_is_explicit_materialization_route(self):
        self.assertEqual("juriscribe.recovery.create_recovery_bundle",route_owner("create_recovery_bundle"))

if __name__=="__main__": unittest.main()
