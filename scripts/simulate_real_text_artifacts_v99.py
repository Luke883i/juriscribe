from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import io
import json
import random
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from juriscribe.admission import issue_receipt
from juriscribe.artifact_atlas import artifact_dashboard_coverage_gate, build_artifact_atlas
from juriscribe.artifact_governance import _govern_materialized_narrative, artifact_generation_governance_gate
from juriscribe.dashboard_persistence import persist_dashboard_generation, verify_persistent_dashboard
from juriscribe.delivery import delivery_gate, verify_materialized_artifact
from juriscribe.dossier_materialization import render_dossier_text
from juriscribe.generation_configuration import generation_conformance
from juriscribe.modes import MODES, REVIEW, mode_spec, required_artifact_roles
from juriscribe.orchestrator import apply_setup, freeze_dods, ingest_and_mine, record_artifact, register_semantic_mining, seal_draft
from juriscribe.pipeline_v9 import initialize, main as runtime_main, perform_probe
from juriscribe.semantic_delivery import semantic_dossier_gate
from juriscribe.session import Workspace
from juriscribe.sources import SourceRecord

CONTRACT = (ROOT / "ISENECA_ACCESS_CONTRACT.md").read_text(encoding="utf-8")
FIXTURE = ROOT / "fixtures" / "real_legal_texts_v99.json"
WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
LENGTH_CLASSES = {
    "SHORT": (80, 180),
    "MEDIUM": (220, 450),
    "LONG": (520, 900),
    "XL": (900, 1700),
}
DOSSIER_ROLES = ("evidence_dossier", "source_register", "inference_register", "transformation_ledger")
STOP = {
    "anche", "che", "con", "come", "dalla", "dalle", "dello", "della", "delle", "degli", "dei", "del", "di", "e", "ed", "gli",
    "il", "in", "la", "le", "lo", "nei", "nel", "nella", "nelle", "non", "o", "per", "piu", "più", "sul", "sulla", "tra", "un", "una",
    "uno", "the", "and", "for", "from", "into", "that", "this", "with", "without", "within", "which",
}


def _words(text: str) -> list[str]:
    return WORD_RE.findall(str(text or ""))


def _receipt(index: int):
    return issue_receipt(
        CONTRACT,
        phrase="I ACCEPT",
        actor_type="human",
        evidence_type="explicit_user_message",
        user_message="I ACCEPT",
        accepted_at="2026-08-17T06:00:00+00:00",
        receipt_nonce=f"{index + 1:032x}"[-32:],
    )


def _run_cli(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return runtime_main(argv)


def _load_fixture() -> list[dict]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = payload.get("records") or []
    if len(records) < 10:
        raise AssertionError("real legal fixture is unexpectedly small")
    for record in records:
        if not str(record.get("source_url") or "").startswith("https://"):
            raise AssertionError(f"official source URL missing for {record.get('id')}")
        if len(_words(record.get("text") or "")) < 15:
            raise AssertionError(f"real legal fixture excerpt too small for {record.get('id')}")
    return records


def _compose_real_text(records: list[dict], length_class: str, seed: int, seen: set[str]) -> tuple[str, list[dict]]:
    lower, upper = LENGTH_CLASSES[length_class]
    attempt = 0
    while attempt < 200:
        rng = random.Random(seed + attempt * 100003)
        order = list(records)
        rng.shuffle(order)
        selected: list[dict] = []
        chunks: list[str] = []
        cursor = 0
        while len(_words("\n\n".join(chunks))) < lower:
            record = order[cursor % len(order)]
            selected.append(record)
            chunks.append(f"{record['instrument']} — {record['locator']}\n{record['text']}")
            cursor += 1
        text = "\n\n".join(chunks)
        count = len(_words(text))
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if lower <= count <= upper and digest not in seen:
            seen.add(digest)
            return text, selected
        attempt += 1
    raise AssertionError(f"unable to construct unique {length_class} real-text scenario within {lower}-{upper} words")


def _sentences(text: str) -> list[str]:
    cleaned = [" ".join(item.split()) for item in SENTENCE_RE.split(text) if len(_words(item)) >= 6]
    if len(cleaned) < 3:
        paragraphs = [" ".join(item.split()) for item in text.split("\n\n") if len(_words(item)) >= 6]
        cleaned.extend(item for item in paragraphs if item not in cleaned)
    if len(cleaned) < 3:
        raise AssertionError("real legal packet did not yield three substantive semantic units")
    return cleaned


def _semantic_payload(text: str, source_id: str, scenario_id: str) -> tuple[list[dict], list[dict], str]:
    sentences = _sentences(text)
    kinds = ("DEFINITION", "RULE", "CLAIM")
    units = []
    for index, kind in enumerate(kinds, 1):
        units.append({
            "id": f"{scenario_id}-U{index}",
            "kind": kind,
            "text": sentences[index - 1],
            "source_id": source_id,
            "source_locator": f"real-text-sentence-{index}",
            "chapter": scenario_id,
            "material": True,
            "status": "VERIFIED",
        })
    relations = [
        {"source": units[0]["id"], "predicate": "DEFINES", "target": units[1]["id"], "rationale": "real-text semantic setup"},
        {"source": units[1]["id"], "predicate": "SUPPORTS", "target": units[2]["id"], "rationale": "real-text semantic setup"},
    ]
    return units, relations, units[1]["text"]


def _configuration(state) -> dict:
    return (state.generation_contract or {}).get("generation_configuration") or (state.setup or {}).get("generation_configuration") or {}


def _clean_candidate(configuration: dict, scenario_id: str, mode: str) -> str:
    terms: set[str] = set()
    abstract = str(configuration.get("abstract") or "")
    for token in _words(abstract):
        folded = token.casefold()
        if len(folded) >= 3 and folded not in STOP and not folded.isdigit():
            terms.add(token)
    for concept in configuration.get("key_concepts") or []:
        for token in _words(str(concept)):
            folded = token.casefold()
            if len(folded) >= 3 and folded not in STOP and not folded.isdigit():
                terms.add(token)
    ordered = sorted(terms, key=lambda item: item.casefold())
    lexical = ", ".join(ordered)
    paragraphs = [
        f"L'elaborato {scenario_id} sviluppa un'analisi giuridica autonoma in modalità {mode}. Il lessico necessario viene ricomposto in ordine sistematico e non riproduce la sequenza delle fonti: {lexical}.",
        "L'argomentazione distingue il dato normativo dalla sua elaborazione interpretativa. Ogni passaggio è formulato come proposizione controllabile, collegata alla funzione della fonte e sottoposta a verifica di coerenza. Il ragionamento evita equivalenze automatiche e rende esplicite le condizioni che possono limitare la conclusione.",
        "Sul piano metodologico, la ricostruzione coordina legalità, tutela effettiva, imparzialità, motivazione e controllo. I concetti vengono messi in relazione senza trasformare il testo della fonte in testo dell'autore. Le conseguenze sono esposte con linguaggio originale e con un nesso riconoscibile tra premessa, qualificazione e risultato.",
        "La conclusione conserva il perimetro del mandato e rimane verificabile rispetto al reticolo epistemico. La sintesi finale non aggiunge autorità inesistenti, non nasconde riserve e mantiene distinta la prova testuale dalla scelta editoriale. In questo modo la struttura resta leggibile per il giurista e compatibile con una successiva revisione severa.",
    ]
    text = "\n\n".join(paragraphs)
    lower, upper = [int(value) for value in configuration.get("length_words", [180, 260])]
    filler = " La verifica ulteriore confronta fonti, premesse, qualificazioni e conseguenze in modo trasparente, senza duplicazioni testuali e senza scorciatoie inferenziali."
    while len(_words(text)) < max(lower, 190):
        text += filler
    words = _words(text)
    if len(words) > upper:
        # Preserve the lexical paragraph and trim only repeated filler from the tail.
        tokens = text.split()
        text = " ".join(tokens[:upper])
    check = generation_conformance(text, configuration)
    if check.get("status") != "PASS":
        raise AssertionError(f"clean candidate does not satisfy accepted generation configuration: {check}")
    return text


def _write_docx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    paragraphs = [item.strip() for item in str(text).splitlines() if item.strip()] or [str(text)]
    body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{xml_escape(item)}</w:t></w:r></w:p>" for item in paragraphs)
    document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + "</w:body></w:document>"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        package.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
        package.writestr("word/document.xml", document)


def _checkpoint(ws: Workspace, marker: str | None = None) -> dict:
    state = ws.load()
    path = ws.artifact_dir / "session-dashboard.html"
    ok, errors, report = verify_persistent_dashboard(state, path)
    if not ok:
        raise AssertionError(f"persistent dashboard verification failed: {errors}")
    page = path.read_text(encoding="utf-8")
    if marker and html.escape(" ".join(marker.split()), quote=True) not in page:
        raise AssertionError(f"real semantic marker is missing from dashboard: {marker}")
    return {
        "generation": int((state.dashboard_persistence or {}).get("generation", 0) or 0),
        "bytes": path.stat().st_size,
        "public_leaf_count": int(report.get("public_leaf_count", 0) or 0),
        "semantic_witness_count": int(report.get("semantic_witness_count", 0) or 0),
        "registered_public_material_roles": int(report.get("registered_public_material_roles", 0) or 0),
    }


def _persist(ws: Workspace, state, trigger: str, marker: str | None = None):
    persist_dashboard_generation(ws, state, trigger=trigger)
    return ws.load(), _checkpoint(ws, marker)


def _narrative_role(mode: str, setup: dict) -> str:
    return str(mode_spec(mode, setup).get("primary_artifact_role") or "")


def exercise_scenario(root: Path, records: list[dict], index: int, length_class: str, source_text: str, selected: list[dict]) -> dict:
    mode = MODES[index % len(MODES)]
    scenario_id = f"REAL-{index + 1:03d}-{length_class}-{mode}"
    receipt = _receipt(index)
    probe = perform_probe(
        admission_receipt=receipt,
        contract_text=CONTRACT,
        host_capabilities={"DOCX_WRITE": "AVAILABLE", "DOCX_READBACK": "AVAILABLE"},
        host="real-text-dashboard-v99",
        probed_at="2026-08-17T06:00:01+00:00",
    )
    session_id = f"SES-real-{index + 1:03d}"
    base = initialize(
        f"Verifica E2E con fonti giuridiche ufficiali {scenario_id}",
        root=str(root),
        session_id=session_id,
        admission_receipt=receipt,
        probe_receipt=probe,
        contract_text=CONTRACT,
    )
    ws = Workspace(root, session_id)
    checkpoints = [_checkpoint(ws)]
    if _run_cli(["select-mode", str(base), "--mode", mode]) != 0:
        raise AssertionError(f"select-mode failed for {scenario_id}")
    checkpoints.append(_checkpoint(ws))

    source_id = f"SRC-REAL-{index + 1:03d}"
    authorities = sorted({str(item.get("authority")) for item in selected})
    instruments = sorted({str(item.get("instrument")) for item in selected})
    source_record = SourceRecord(
        source_id,
        "Pacchetto ufficiale: " + "; ".join(instruments[:4]),
        str(selected[0].get("source_url")),
        "primary_law",
        jurisdiction="Italia / Unione europea / CEDU",
        court_or_author="; ".join(authorities[:4]),
        verified_at="2026-08-17",
        direct_read=True,
        primary=True,
        notes="Estratti ufficiali congelati: " + ", ".join(str(item.get("id")) for item in selected),
        bibliography_entry="; ".join(f"{item.get('instrument')} {item.get('locator')}" for item in selected[:6]),
        role=mode_spec(mode, {}).get("input_role", "external_source"),
    ).record()
    state = ws.load()
    ingest_and_mine(state, source_text, source_id=source_id, chapter=scenario_id, source_record=source_record)
    state, checkpoint = _persist(ws, state, "mine")
    checkpoints.append(checkpoint)

    units, relations, semantic_marker = _semantic_payload(source_text, source_id, scenario_id)
    register_semantic_mining(state, units, relations)
    if state.reticulum.get("status") != "PASS":
        raise AssertionError(f"reticulum failed for {scenario_id}: {state.reticulum}")
    state, checkpoint = _persist(ws, state, "semantic-mining", semantic_marker)
    checkpoints.append(checkpoint)

    apply_setup(state, {"length_words": [180, 260]})
    state, checkpoint = _persist(ws, state, "accept-setup", semantic_marker)
    checkpoints.append(checkpoint)
    freeze_dods(state)
    state, checkpoint = _persist(ws, state, "freeze-dods", semantic_marker)
    checkpoints.append(checkpoint)
    configuration = _configuration(state)
    if configuration.get("status") != "READY":
        raise AssertionError(f"generation configuration not READY for {scenario_id}: {configuration}")
    generated = _clean_candidate(configuration, scenario_id, mode)

    if mode == REVIEW:
        seal_draft(state, source_text, stage="REVIEW_SOURCE")
    else:
        seal_draft(state, generated, stage="INITIAL")
    state, checkpoint = _persist(ws, state, "seal-draft", semantic_marker)
    checkpoints.append(checkpoint)

    primary_role = _narrative_role(mode, state.setup)
    negative_plagiarism_checked = False
    if index % 5 == 0:
        copied = " ".join(_words(source_text)[:24]) + " " + generated
        copied_words = copied.split()
        copied = " ".join(copied_words[:250])
        bad_path = ws.artifact_dir / f"negative-copy-{index + 1:03d}.docx"
        _write_docx(bad_path, copied)
        proof = _govern_materialized_narrative(state, {"role": primary_role, "path": str(bad_path), "readback": "PASS"})
        bad_path.unlink(missing_ok=True)
        plagiarism = proof.get("plagiarism") or {}
        if plagiarism.get("status") != "FAIL" or int(plagiarism.get("prohibited_findings", 0) or 0) < 1:
            raise AssertionError(f"copied-source adversarial probe was not blocked for {scenario_id}: {proof}")
        negative_plagiarism_checked = True

    negative_dossier_checked = False
    if index % 10 == 0:
        bad_dossier = ws.artifact_dir / f"negative-dossier-{index + 1:03d}.docx"
        _write_docx(bad_dossier, f"Dossier volutamente incompleto {scenario_id}")
        try:
            record_artifact(state, {"id": f"bad-{scenario_id}", "role": "evidence_dossier", "summary": "negative dossier probe", "path": str(bad_dossier), "readback": "PASS"})
        except ValueError as exc:
            if "semantic materialization" not in str(exc):
                raise
            negative_dossier_checked = True
        else:
            raise AssertionError(f"incomplete canonical dossier was accepted for {scenario_id}")
        finally:
            bad_dossier.unlink(missing_ok=True)

    required = required_artifact_roles(mode, state.setup)
    artifact_summaries: list[str] = []
    for role in sorted(required - {"session_dashboard"}):
        path = ws.artifact_dir / f"{role}.docx"
        summary = f"{scenario_id} — artefatto conforme {role}"
        if role in DOSSIER_ROLES:
            text = render_dossier_text(state, role)
        elif role == primary_role:
            text = generated
        elif role == "review_findings_register":
            text = f"Registro rilievi {scenario_id}. La simulazione verifica materializzazione, copertura semantica, originalità e persistenza senza formulare conclusioni giuridiche ulteriori."
        else:
            text = generated
        _write_docx(path, text)
        record_artifact(state, {"id": f"{scenario_id}-{role}", "role": role, "summary": summary, "path": str(path), "readback": "PASS"})
        artifact_summaries.append(summary)
        state, checkpoint = _persist(ws, state, f"record-artifact:{role}", semantic_marker)
        checkpoints.append(checkpoint)

    delivery_ok, delivery_errors = delivery_gate(state)
    if not delivery_ok:
        raise AssertionError(f"delivery materialization failed for {scenario_id}: {delivery_errors}")
    semantic_ok, semantic_errors = semantic_dossier_gate(state)
    if not semantic_ok:
        raise AssertionError(f"canonical dossier semantic gate failed for {scenario_id}: {semantic_errors}")
    narrative_ok, narrative_errors = artifact_generation_governance_gate(state)
    if not narrative_ok:
        raise AssertionError(f"narrative artifact governance failed for {scenario_id}: {narrative_errors}")
    atlas = build_artifact_atlas(state)
    atlas_ok, atlas_errors = artifact_dashboard_coverage_gate(state, atlas)
    if not atlas_ok:
        raise AssertionError(f"artifact atlas coverage failed for {scenario_id}: {atlas_errors}")

    dashboard = ws.artifact_dir / "session-dashboard.html"
    dashboard_ok, dashboard_errors, dashboard_report = verify_persistent_dashboard(state, dashboard)
    if not dashboard_ok:
        raise AssertionError(f"dashboard final verification failed for {scenario_id}: {dashboard_errors}")
    page = dashboard.read_text(encoding="utf-8")
    body = page.split("<body>", 1)[1].split("</body>", 1)[0]
    if html.escape(" ".join(semantic_marker.split()), quote=True) not in body:
        raise AssertionError(f"real semantic evidence is absent from final dashboard for {scenario_id}")
    for summary in artifact_summaries:
        if html.escape(summary, quote=True) not in body:
            raise AssertionError(f"artifact registration summary absent from dashboard for {scenario_id}: {summary}")
    for forbidden in [str(ws.base.resolve()), "exact_ngram_hashes", "shingle_hashes", "candidate_fingerprint_digest", "resolved_path"]:
        if forbidden in body:
            raise AssertionError(f"technical/internal information leaked into dashboard for {scenario_id}: {forbidden}")

    by_role = {str(item.get("role") or ""): item for item in state.artifacts if item.get("role")}
    for role in required:
        record = by_role.get(role)
        if not record:
            raise AssertionError(f"required artifact absent after materialization for {scenario_id}: {role}")
        ok, errors, _ = verify_materialized_artifact(state, record)
        if not ok:
            raise AssertionError(f"materialized artifact verification failed for {scenario_id}/{role}: {errors}")
        if role in DOSSIER_ROLES and (record.get("semantic_materialization") or {}).get("status") != "PASS":
            raise AssertionError(f"dossier semantic materialization proof missing for {scenario_id}/{role}")
        if role == primary_role and (record.get("artifact_generation_governance") or {}).get("status") != "PASS":
            raise AssertionError(f"primary narrative generation-governance proof missing for {scenario_id}/{role}")

    ledger_path = ws.ledger_dir / "dashboard-generations.jsonl"
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    generations = [int(row.get("generation", 0)) for row in rows]
    expected = list(range(1, len(rows) + 1))
    if generations != expected or generations[-1] != int(state.dashboard_persistence.get("generation", 0)):
        raise AssertionError(f"dashboard ledger is not monotonic for {scenario_id}: {generations}")

    return {
        "scenario_id": scenario_id,
        "status": "PASS",
        "mode": mode,
        "length_class": length_class,
        "input_word_count": len(_words(source_text)),
        "real_source_ids": [item.get("id") for item in selected],
        "official_source_urls": sorted({item.get("source_url") for item in selected}),
        "semantic_marker": semantic_marker,
        "required_artifact_roles": sorted(required),
        "materialized_artifacts": len(required),
        "dashboard_generation": int(state.dashboard_persistence.get("generation", 0)),
        "dashboard_bytes": dashboard.stat().st_size,
        "dashboard_public_leaf_count": int(dashboard_report.get("public_leaf_count", 0) or 0),
        "dashboard_semantic_witness_count": int(dashboard_report.get("semantic_witness_count", 0) or 0),
        "anti_plagiarism_negative_probe": negative_plagiarism_checked,
        "incomplete_dossier_negative_probe": negative_dossier_checked,
        "checkpoints": checkpoints,
    }


def run(cases: int = 100, out_root: str | None = None) -> dict:
    if cases != 100:
        raise ValueError("the real-text fine-tuning suite is intentionally fixed at exactly 100 scenarios")
    records = _load_fixture()
    temporary = None
    if out_root:
        root = Path(out_root).resolve()
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)
    else:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
    seen: set[str] = set()
    scenarios = []
    try:
        classes = list(LENGTH_CLASSES)
        for index in range(cases):
            length_class = classes[index // 25]
            source_text, selected = _compose_real_text(records, length_class, 990001 + index * 7919, seen)
            scenarios.append(exercise_scenario(root, records, index, length_class, source_text, selected))
        class_counts = Counter(item["length_class"] for item in scenarios)
        mode_counts = Counter(item["mode"] for item in scenarios)
        if class_counts != Counter({name: 25 for name in LENGTH_CLASSES}):
            raise AssertionError(f"length-class distribution mismatch: {class_counts}")
        if len({item["scenario_id"] for item in scenarios}) != 100:
            raise AssertionError("scenario identifiers are not unique")
        if sum(1 for item in scenarios if item["anti_plagiarism_negative_probe"]) != 20:
            raise AssertionError("expected exactly 20 copied-source adversarial probes")
        if sum(1 for item in scenarios if item["incomplete_dossier_negative_probe"]) != 10:
            raise AssertionError("expected exactly 10 incomplete-dossier adversarial probes")
        return {
            "schema": "juriscribe-real-text-artifact-dashboard-finetuning/v1",
            "profile": "JURISCRIBE_REAL_TEXT_FINETUNING_V1",
            "status": "PASS",
            "cases": 100,
            "unique_input_packets": len(seen),
            "official_fixture_records": len(records),
            "length_classes": dict(class_counts),
            "modes": dict(mode_counts),
            "anti_plagiarism_negative_probes": 20,
            "incomplete_dossier_negative_probes": 10,
            "invariants": [
                "all source packets consist exclusively of frozen official legal-text excerpts",
                "every required material artifact exists and passes bounded materialization verification",
                "new canonical dossier DOCX files contain every leaf of the canonical semantic projection",
                "primary narrative artifacts satisfy generation configuration and anti-plagiarism governance",
                "copied-source adversarial candidates are blocked",
                "incomplete canonical dossier adversarial files are blocked",
                "the persistent dashboard contains real semantic witnesses and every registered artifact summary",
                "the dashboard generation ledger advances monotonically throughout each real session",
            ],
            "scenarios": scenarios,
        }
    finally:
        if temporary is not None:
            temporary.cleanup()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=100)
    parser.add_argument("--out-root")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    result = run(args.cases, args.out_root)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
