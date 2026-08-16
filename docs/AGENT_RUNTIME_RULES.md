# Juriscribe agent runtime rules v0.9.5 — post-bootstrap

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

## Bootstrap hardening e fast path
L'accettazione umana resta separata e non inferibile. Dopo un messaggio umano esattamente `I ACCEPT`, l'host può velocizzare il primo avvio usando la fast path canonica `bootstrap-after-acceptance`, che esegue nello stesso turno `probe -> probe receipt -> initialize`, purché le tre transizioni restino distinte e auditabili e `initialize` non esegua mai un probe implicito. La modalità resta una decisione umana separata dopo initialize.

Le receipt hanno nonce; una probe receipt è single-use per inizializzare una sessione. Le capability sigillate dal probe non possono essere mutate o ampliate durante initialize. Gli ID sessione automatici sono non deterministici e un workspace già occupato non viene mai sovrascritto.

## CONTINUATION
Preserva continuation frontier/coverage, coerenza inter-capitolo e non duplicazione.

## GREENFIELD
Non inventare seed o continuità. Il concept genera scope e research questions ma non vale come autorità.

## REVIEW
In `REPORT_ONLY`, finding aperti nel target sono output, non blocker del runtime. In `REPORT_AND_REVISED_TEXT`, le modifiche devono essere causalmente legate ai finding e il testo finale deve essere riesaminato.

## Editoriale
Applica `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2` con adattamento a genere, destinatari e house style. Non trasformare metriche in regole universali.

## Artefatti semantici v0.9.4+
I quattro dossier comuni devono essere costruiti dalla proiezione canonica `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`:

- `evidence_dossier`: proposizione, funzione giuridica, evidenze/premesse, pinpoint, qualificazioni/contrasti, disposizione e collocazione;
- `source_register`: carattere dell'autorità, autore/organo, giurisdizione/tempo, funzione, uso effettivo, evidenza circostanziata, riserve/controautorità e bibliografia;
- `inference_register`: conclusione, premesse testuali, ponte, falsificatore, autorità/evidenze, qualificazioni/obiezioni/contrasti e disposizione;
- `transformation_ledger`: finding, ragioni degli interventi, rigenerazioni, preservazione/perdita/novità, compressione, azioni editoriali e consequence probes.

Non duplicare questa logica in renderer diversi: usa `juriscribe.editorial_artifacts.build_editorial_artifact_views` come fonte semantica comune. Non aggiungere contenuti interpretativi che non siano già materializzati nello stato auditato.

## Dashboard inferenziale — vincolo non negoziabile
`session-dashboard.html` deve essere il dossier inferenziale integrato, non una console tecnica. Il `<body>` deve contenere **ogni informazione giuridico-umanistico-editoriale** presente nelle quattro proiezioni canoniche, oltre a mandato, modalità, genere, destinatari e principi editoriali applicati.

Dalla v0.9.5 la presentazione usa `JURISCRIBE_EDITORIAL_WORKBENCH_V1`:
- masthead editoriale con mandato e cornice;
- mappa dei quattro registri ottenuta soltanto da conteggi derivati;
- indice interno e landmark nominati;
- record semantici espandibili, aperti di default;
- ricerca locale sul testo già presente nel DOM;
- controlli espandi/contrai e profilo di stampa;
- layout responsive e focus visibile;
- HTML autosufficiente, senza CSS, font, analytics o JavaScript remoti.

La ricerca e gli strumenti di lettura non devono generare, trasformare o riassumere nuovo contenuto giuridico. Il browser presenta la proiezione: non diventa un secondo motore inferenziale.

Nel corpo della dashboard non mostrare:
- hash o digest;
- `session.integrity.json`;
- path di filesystem;
- capability host;
- readback/media type;
- log, receipt, stderr, traceback/stack trace;
- conteggi di record interni o altri dettagli di implementazione.

Il solo `juriscribe-state-digest` invisibile nel `<head>` resta consentito perché necessario al gate di freshness consolidato. Non renderlo visibile al lettore.

## Superficie AI artifact-first — vincolo non negoziabile
La complessità deve restare nel runtime, nei DOCX e nella dashboard, **non nella conversazione con l'utente**. Regola sintetica: **non narrare** il processo interno; materializzalo.

Dopo modalità, materiali e setup minimo:
- prosegui autonomamente senza narrare mining, reticolo, ricerca, fonti, review, rigenerazioni, saturazione, simulazioni, compressione, provenance o gate;
- non chiedere conferme meccaniche; interrompi solo per una decisione umana materialmente bloccante e realmente non inferibile;
- ogni messaggio ordinario post-bootstrap deve essere breve, normalmente entro **1–3 righe**;
- usa la chat soltanto per esito sintetico, prossimo passo essenziale o decisione umana necessaria;
- non riversare in chat report, finding completi, liste estese di fonti/evidenze, ledger, receipt, provenance raw, JSON macchina, log, stderr, traceback/stack trace o dettagli diagnostici;
- in caso di errore tecnico, mostra soltanto un messaggio redatto e non sensibile; conserva il dettaglio nel ledger interno e **non trasformare la dashboard in un contenitore tecnico**;
- una superficie machine-readable/verbosa richiede doppio opt-in tecnico: `JURISCRIBE_VERBOSE_JSON=1` e flag `--technical-output`.

## Delivery e materializzazione
Alla chiusura:
- scrivi in chat soltanto 1–3 righe con esito e rinvio agli allegati;
- allega tutti i documenti finali user-facing in **DOCX** realmente materializzati;
- allega sempre `session-dashboard.html` come dashboard HTML corrente;
- non allegare `state.json`, `session.integrity.json`, receipt, validation JSON, JSONL ledger, provenance raw o altri record macchina salvo richiesta tecnica esplicita;
- non sostituire un DOCX richiesto con Markdown, TXT, JSON o testo incollato in chat;
- un suffisso `.docx` non basta: il file deve esistere, non essere vuoto, essere un pacchetto OOXML/WordprocessingML riconoscibile ed essere rileggibile entro limiti di decompressione/size sicuri;
- i deliverable finali devono essere materializzati **dentro** `<workspace>/artifacts`; path esterni e symlink non soddisfano il gate;
- la dashboard deve restare state-bound tramite metadata invisibile; una dashboard stale non soddisfa il gate;
- i quattro dossier v0.9.4+ devono essere materializzati dalla proiezione corrente e, se sigillati, non possono essere stale rispetto al quadro inferenziale;
- se `DOCX_WRITE` o `DOCX_READBACK` non sono `AVAILABLE`, non dichiarare `COMPLETE`.

La persistenza di `state.json` e `session.integrity.json` usa replace atomico e ogni `load()` sostanziale valida l'integrità prima di restituire lo stato. Il manifest di consegna canonico resta costruito da `juriscribe.delivery.build_delivery_manifest`; il semantic-drift gate è `juriscribe.semantic_delivery.semantic_dossier_gate`.

Vedi `docs/DASHBOARD_WORKBENCH_V9_5.md`, `docs/EDITORIAL_ARTIFACTS_V9_4.md`, `docs/FINAL_DELIVERY_V9_4.md`, `docs/AUDIT_MAIN_V9_4.md` e `docs/RUNTIME_HARDENING_V9_3.md`.
