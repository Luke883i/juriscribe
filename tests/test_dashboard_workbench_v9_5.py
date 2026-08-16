import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from juriscribe.dashboard_v9 import DASHBOARD_DESIGN_PROFILE, render_session_dashboard
from juriscribe.editorial_artifacts import DOSSIER_ROLES, build_dashboard_inference_view


class DashboardWorkbenchV95Tests(unittest.TestCase):
    def _state(self, *, rich=True):
        base = dict(
            request={"raw": "Analizza la proporzionalita", "summary": "Analisi della proporzionalita e dei suoi limiti"},
            mode="GREENFIELD" if rich else None,
            editorial_standard={
                "document_type": "LEGAL_MONOGRAPH",
                "audience": "giuristi, studiosi e redazioni giuridiche",
                "mode_adjustments": ["esplicitare scope e confini interpretativi"],
                "rules": {"stable_terminology": True, "authority_and_counterauthority": True},
            } if rich else {},
            setup={}, sources=[], bibliography={}, epistemic_units=[], relations=[], reticulum={}, generation_contract={}, continuation={}, drafts=[],
            review={}, final_review={}, provenance={}, contradictions=[], mining={}, style_profile={}, source_intelligence={}, claim_ledger=[], artifact_evidence=[],
            quality={}, benchmark={}, simulations={}, compression={}, limits=[], strategy={}, dod=[], editorial_actions=[], reflection={}, metrics={},
            phase="VALIDATING", interaction={}, completion={"eligible": False}, node_integrity={}, runtime={}, artifacts=[], mode_selection={}, mode_contract={}, corpus=[],
        )
        if not rich:
            base["request"]={"raw":"inizializza https://github.com/Luke883i/juriscribe","summary":"inizializza https://github.com/Luke883i/juriscribe"}
            return SimpleNamespace(**base)
        base.update(
            sources=[{
                "id":"S1","title":"Corte costituzionale, sentenza esemplificativa","source_type":"constitutional_court","jurisdiction":"Italia",
                "court_or_author":"Corte costituzionale","date":"2025-01-15","direct_read":True,"verified_at":"2026-08-16T12:00:00+00:00",
                "role":"autorita di controllo","notes":"Verificata nel suo perimetro decisorio","url":"https://example.invalid/source",
            }],
            epistemic_units=[
                {"id":"C1","kind":"RULE","text":"Il controllo richiede adeguatezza e necessita.","source_id":"S1","source_locator":"p. 12","status":"VERIFIED","material":True},
                {"id":"I1","kind":"INFERENCE","text":"La necessita richiede alternative meno restrittive.","source_id":"S1","source_locator":"p. 13","status":"INFERRED","material":True},
            ],
            relations=[{"source":"C1","predicate":"SUPPORTS","target":"I1","rationale":"La regola costituisce la premessa dell'inferenza."}],
            claim_ledger=[
                {"id":"C1","text":"Il controllo richiede adeguatezza e necessita.","claim_type":"legal_rule","scope":"proporzionalita","support_source_ids":["S1"],"status":"VERIFIED","material":True,"source_evidence":[{"source_id":"S1","pinpoint":"p. 12","proposition":"Adeguatezza e necessita sono passaggi distinti."}]},
                {"id":"I1","text":"La necessita richiede alternative meno restrittive.","claim_type":"strong_inference","scope":"necessita","support_source_ids":["S1"],"premise_claim_ids":["C1"],"inference_bridge":"Dalla necessita segue il confronto tra mezzi equivalenti.","falsifier":"Una regola speciale esclude il confronto.","status":"INFERRED","material":True},
            ],
            provenance={"entries":[
                {"id":"C1","kind":"CLAIM","proposition":"Il controllo richiede adeguatezza e necessita.","rationale":"Direttamente attestata.","disposition":"IN_FINAL","evidence_refs":["S1"],"artifact_locators":["§ 1.2"]},
                {"id":"I1","kind":"INFERENCE","proposition":"La necessita richiede alternative meno restrittive.","rationale":"Passaggio interpretativo esplicito.","disposition":"IN_FINAL","evidence_refs":["S1"],"premise_ids":["C1"],"inference_bridge":"Dalla necessita segue il confronto tra mezzi equivalenti.","falsifier":"Una regola speciale esclude il confronto.","artifact_locators":["§ 2.2"]},
                {"id":"T1","kind":"TRANSFORMATION","proposition":"Integrare la controautorita.","rationale":"Evitare una rappresentazione unilaterale.","disposition":"IN_FINAL","artifact_locators":["§ 2.3"]},
            ]},
            review={"cycles":[{"cycle":1,"findings":[{"id":"F1","criterion":"COUNTERAUTHORITY","severity":"MAJOR","message":"La controautorita deve essere discussa.","proposed_action":"Integrare l'obiezione.","epistemic_unit_ids":["I1"],"source_ids":["S1"],"artifact_locator":"§ 2.3","status":"ADDRESSED"}]}]},
            final_review={"consequence_probes":[{"id":"P1","proposition":"La tesi non e assoluta.","downstream_effect":"La conclusione resta qualificata.","evidence_ref":"I1","status":"PASS"}]},
        )
        return SimpleNamespace(**base)

    def _render(self, state):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"session-dashboard.html"
            render_session_dashboard(state,path)
            return path.read_text(encoding="utf-8")

    def _leaf_strings(self, value):
        if isinstance(value,dict):
            for item in value.values(): yield from self._leaf_strings(item)
        elif isinstance(value,(list,tuple)):
            for item in value: yield from self._leaf_strings(item)
        elif value not in (None,""):
            yield str(value).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#x27;")

    def test_workbench_is_rich_self_contained_and_navigable(self):
        html=self._render(self._state())
        body=html.split("<body>",1)[1].split("</body>",1)[0]
        self.assertEqual(DASHBOARD_DESIGN_PROFILE,"JURISCRIBE_EDITORIAL_WORKBENCH_V1")
        for token in ["Indice del dossier","Quadro del ragionamento materializzato","Cerca nel dossier","Espandi","Contrai","Stampa","Evidenze e merito","Standard redazionali applicati","Modalità:"]:
            self.assertIn(token,body)
        for anchor in ["overview","evidence-dossier","source-register","inference-register","transformation-ledger"]:
            self.assertIn(f'id="{anchor}"',body)
            self.assertIn(f'href="#{anchor}"',body)
        self.assertIn('@media print',html)
        self.assertIn('type="search"',body)
        self.assertIn('<details class="record" open>',body)
        self.assertNotIn('<link ',html.lower())
        self.assertNotRegex(html.lower(),r'<script[^>]+src=')

    def test_workbench_preserves_every_semantic_leaf(self):
        state=self._state(); aggregate=build_dashboard_inference_view(state); html=self._render(state); body=html.split("<body>",1)[1].split("</body>",1)[0]
        for role in DOSSIER_ROLES:
            for value in self._leaf_strings(aggregate[role]):
                self.assertIn(value,body,(role,value))

    def test_empty_initialized_dashboard_is_still_structured(self):
        html=self._render(self._state(rich=False)); body=html.split("<body>",1)[1].split("</body>",1)[0]
        self.assertIn("inizializza https://github.com/Luke883i/juriscribe",body)
        self.assertIn("Non selezionata",body)
        self.assertGreaterEqual(body.count("0 elementi"),4)
        self.assertGreaterEqual(body.count("Nessun elemento materializzato."),4)
        self.assertEqual(body.count('class="dossier"'),4)

    def test_workbench_does_not_reintroduce_technical_surface(self):
        state=self._state(); state.runtime={"workspace_base":"/secret/path","capabilities":{"DOCX_WRITE":"AVAILABLE"}}; state.node_integrity={"status":"PASS"}
        html=self._render(state); body=html.split("<body>",1)[1].split("</body>",1)[0]
        self.assertIn('name="juriscribe-state-digest"',html)
        for token in ["/secret/path","DOCX_WRITE","DOCX_READBACK","session.integrity.json","sha256","readback","workspace_base","Dashboard state digest"]:
            self.assertNotIn(token,body)

    def test_user_material_is_html_escaped(self):
        state=self._state(); state.request={"raw":"<script>alert(1)</script>","summary":"<script>alert(1)</script>"}
        html=self._render(state); body=html.split("<body>",1)[1].split("</body>",1)[0]
        self.assertNotIn("<script>alert(1)</script>",body)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;",body)

    def test_landmarks_and_heading_targets_are_consistent(self):
        html=self._render(self._state()); body=html.split("<body>",1)[1].split("</body>",1)[0]
        ids=set(re.findall(r'\bid="([^"]+)"',body))
        targets=set(re.findall(r'href="#([^"]+)"',body))
        self.assertTrue(targets.issubset(ids),(targets-ids))
        self.assertEqual(body.count("<h1>"),1)
        for anchor in ["overview","evidence-dossier","source-register","inference-register","transformation-ledger"]:
            self.assertIn(f'aria-labelledby="{anchor}-title"',body)
            self.assertIn(f'id="{anchor}-title"',body)


if __name__=="__main__": unittest.main()
