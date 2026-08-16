# Final delivery contract v0.9.2

Questa specifica supersede `FINAL_DELIVERY_V9_1.md`. PR10 ha ripristinato DOCX, dashboard e separazione fra deliverable e record macchina; l'audit successivo ha mostrato che quei vincoli erano ancora prevalentemente **dichiarativi**. v0.9.2 li rende materiali, state-bound e applicabili all'intera superficie post-bootstrap.

## 1. Artifact-first per tutta la sessione
Dopo il bootstrap la chat è una superficie di controllo, non una superficie di report. La complessità resta nel runtime, nei DOCX e nella dashboard.

L'assistente non deve narrare progressivamente mining, ricerca, reticolo, review, rigenerazioni, simulazioni, saturazione, compressione, provenance o gate. Dopo modalità, materiali e setup minimo prosegue autonomamente e interrompe l'utente solo per una scelta materialmente bloccante e realmente non inferibile.

La superficie ordinaria post-bootstrap è breve, normalmente **1–3 righe**. Sono ammessi: esito sintetico, next action essenziale, oppure una decisione umana necessaria. Report, finding completi, registri, liste estese di fonti/evidenze e diagnostica appartengono agli artefatti.

## 2. DOCX significa DOCX materializzato
Tutti i documenti finali user-facing devono essere DOCX: `final_chapter`, `final_legal_text`, `review_report`, `revised_legal_text` quando richiesto, `evidence_dossier`, `source_register`, `inference_register`, `transformation_ledger`, `review_findings_register` quando applicabile.

Il gate non accetta più il solo suffisso `.docx`. Il file deve esistere, non essere vuoto, essere un pacchetto ZIP OOXML valido, contenere almeno `[Content_Types].xml`, `_rels/.rels`, `word/document.xml`, avere WordprocessingML/testo rileggibile ed essere legato nel manifest a size e SHA-256 effettivi.

Un JSON/TXT/Markdown rinominato `.docx`, un path inesistente o un record `readback=PASS` autodichiarato non soddisfano il gate.

## 3. Dashboard corrente, non soltanto presente
`session_dashboard` resta obbligatoria e deve essere `session-dashboard.html`. Il renderer incorpora un `juriscribe-state-digest` deterministico dello stato sostanziale della sessione.

Al delivery gate la dashboard viene riletta e il digest incorporato viene confrontato con quello dello stato corrente. Se corpus, claim, review, fonti, contratti, artefatti o altri elementi sostanziali cambiano, una dashboard precedente diventa stale e non può chiudere la sessione. Il fascicolo umano mostra nel corpo principale soltanto i deliverable user-facing; i record interni sono esclusi dalla tabella e compaiono al massimo come conteggio sintetico nella sezione tecnica collassata.

## 4. Record interni e diagnostica
Restano interni, salvo richiesta tecnica esplicita: `state.json`, `session.integrity.json`, provenance raw, validation/simulation receipts raw, JSONL ledger, probe/admission receipts, traceback/stack trace, stderr, hash manifest e altri record macchina.

In caso di errore tecnico, la superficie pubblica restituisce soltanto un messaggio breve; traceback e dettaglio vengono scritti nel ledger interno e il blocker viene reso visibile nella dashboard.

## 5. Capability fail-closed
`COMPLETE` richiede `DOCX_WRITE = AVAILABLE` e `DOCX_READBACK = AVAILABLE` quando sono richiesti documenti. Non esiste fallback equivalente a Markdown, TXT, JSON o contenuto incollato in chat.

## 6. Manifest di consegna v2
`juriscribe-final-delivery/v2` contiene esclusivamente gli allegati user-facing richiesti e registra ruolo, path, formato/media type, readback, dimensione e SHA-256. Attesta `materialization_verified = true`, `dashboard_bound_to_current_state = true` e policy `BRIEF_ARTIFACT_FIRST_ALL_POST_BOOTSTRAP` soltanto quando i gate passano.

## 7. Eccezione tecnica esplicita
`JURISCRIBE_VERBOSE_JSON=1` e richieste tecniche esplicite possono esporre superfici machine-readable per debugging/audit. Questa eccezione non sostituisce i deliverable ordinari e non autorizza il runtime a diventare verboso per default.
