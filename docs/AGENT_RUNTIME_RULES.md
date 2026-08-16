# Juriscribe agent runtime rules v0.9.1 — post-bootstrap

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

## Delivery: vincolo non negoziabile
La complessità deve restare nel runtime e nella dashboard, **non nella conversazione con l'utente**.

Alla chiusura della lavorazione:
- scrivi in chat soltanto 1–3 righe brevi con l'esito e il rinvio agli allegati;
- non riversare in chat report, finding completi, ledger, receipt, provenance raw o log;
- allega tutti i documenti finali user-facing in **DOCX**;
- allega sempre `session-dashboard.html` come dashboard HTML;
- non allegare `state.json`, `session.integrity.json`, receipt, validation JSON, JSONL ledger o altri record macchina salvo richiesta tecnica esplicita;
- non sostituire un DOCX richiesto con Markdown, TXT o JSON;
- se `DOCX_WRITE` o `DOCX_READBACK` non sono `AVAILABLE`, non dichiarare `COMPLETE`.

Il manifest di consegna canonico è costruito da `juriscribe.delivery.build_delivery_manifest`. Vedi `docs/FINAL_DELIVERY_V9_1.md`.
