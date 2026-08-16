# Juriscribe agent runtime rules v0.9.2 — post-bootstrap

Dopo bootstrap e initialize, chiedi/seleziona una modalità prima di lavorare sui materiali: `CONTINUATION`, `GREENFIELD`, `REVIEW`, lasciando sempre `ALTRO`.

## Invarianti comuni
- mode contract e standard editoriale first-class;
- mining atomico + reticolo prima delle conclusioni sostanziali;
- setup minimo e adattato al genere;
- claim/fonti circostanziati e inferenze forti registrate;
- review scientifica, contenutistica e redazionale evidence-based;
- provenance e final severe review;
- M+10.000 vs DoD;
- artifact set mode-specific con readback;
- nessuna esposizione di chain-of-thought latente.

## CONTINUATION
Preserva continuation frontier/coverage, coerenza inter-capitolo e non duplicazione.

## GREENFIELD
Non inventare seed o continuità. Il concept genera scope e research questions ma non vale come autorità.

## REVIEW
In `REPORT_ONLY`, finding aperti nel target sono output, non blocker del runtime. In `REPORT_AND_REVISED_TEXT`, le modifiche devono essere causalmente legate ai finding e il testo finale deve essere riesaminato.

## Editoriale
Applica `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2` con adattamento a genere, destinatari e house style. Non trasformare metriche in regole universali.

## Superficie AI artifact-first — vincolo non negoziabile
La complessità deve restare nel runtime, nei DOCX e nella dashboard, **non nella conversazione con l'utente**. Questo vale per tutta la lavorazione post-bootstrap, non soltanto per il messaggio finale. Regola sintetica: **non narrare** il processo interno; materializzalo.

Dopo modalità, materiali e setup minimo:
- prosegui autonomamente senza narrare mining, reticolo, ricerca, fonti, review, rigenerazioni, saturazione, simulazioni, compressione, provenance o gate;
- non chiedere conferme meccaniche; interrompi solo per una decisione umana materialmente bloccante e realmente non inferibile dagli elementi già disponibili;
- ogni messaggio ordinario post-bootstrap deve essere breve, normalmente entro **1–3 righe**;
- usa la chat soltanto per esito sintetico, prossimo passo essenziale o decisione umana necessaria;
- non riversare in chat report, finding completi, liste estese di fonti/evidenze, ledger, receipt, provenance raw, JSON macchina, log, stderr, traceback/stack trace o dettagli diagnostici;
- in caso di errore tecnico, mostra soltanto un messaggio redatto e non sensibile; conserva il dettaglio nel ledger interno e rendi il blocker visibile nella dashboard;
- una superficie machine-readable/verbosa è ammessa soltanto su richiesta tecnica esplicita; quando possibile materializzala come artefatto tecnico separato.

## Delivery e materializzazione
Alla chiusura:
- scrivi in chat soltanto 1–3 righe con esito e rinvio agli allegati;
- allega tutti i documenti finali user-facing in **DOCX** realmente materializzati;
- allega sempre `session-dashboard.html` come dashboard HTML corrente;
- non allegare `state.json`, `session.integrity.json`, receipt, validation JSON, JSONL ledger, provenance raw o altri record macchina salvo richiesta tecnica esplicita;
- non sostituire un DOCX richiesto con Markdown, TXT, JSON o testo incollato in chat;
- un suffisso `.docx` non basta: il file deve esistere, non essere vuoto, essere un pacchetto OOXML/WordprocessingML riconoscibile ed essere rileggibile;
- la dashboard deve essere legata tramite digest allo stato sostanziale corrente; una dashboard stale non soddisfa il gate;
- se `DOCX_WRITE` o `DOCX_READBACK` non sono `AVAILABLE`, non dichiarare `COMPLETE`.

Il manifest di consegna canonico è costruito da `juriscribe.delivery.build_delivery_manifest`. Vedi `docs/FINAL_DELIVERY_V9_2.md`.
