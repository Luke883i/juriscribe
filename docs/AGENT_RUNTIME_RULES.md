# Juriscribe agent runtime rules v0.10.0 — post-bootstrap

Dopo bootstrap e initialize, chiedi/seleziona una modalità prima di lavorare sui materiali: `CONTINUATION`, `GREENFIELD`, `REVIEW`, lasciando sempre `ALTRO`.

## Invarianti comuni
- mode contract e standard editoriale first-class;
- mining atomico + reticolo prima delle conclusioni sostanziali;
- setup minimo e adattato al genere;
- claim/fonti circostanziati, evidence register e inferenze forti registrate;
- review scientifica, contenutistica e redazionale evidence-based;
- provenance e final severe review;
- M+10.000 vs DoD dove previsto;
- artifact set mode-specific con readback;
- nessuna esposizione di chain-of-thought latente.

## Bootstrap hardening e fast path
L'accettazione umana resta separata e non inferibile. Dopo un messaggio umano esattamente `I ACCEPT`, l'host può usare `bootstrap-after-acceptance`, purché `probe -> probe receipt -> initialize` restino transizioni distinte e auditabili. La probe receipt è `single-use`; le capability sigillate non possono essere ampliate durante initialize. Gli ID sessione automatici sono non deterministici e un workspace occupato non viene sovrascritto.

## Pipeline lock v0.10.0 — vincolo non negoziabile
Subito dopo `select_mode`, usa `JURISCRIBE_NATURAL_LANGUAGE_PIPELINE_LOCK_V1` per congelare:
- modalità;
- artefatto primario;
- set degli artefatti standard;
- mode-selection binding.

L'input libero resta consentito, ma una locuzione naturale **non** autorizza implicitamente a:
- cambiare modalità;
- cambiare artefatto primario;
- saltare mining, reticolo, review, provenance, final review o gate;
- sopprimere evidence/source/inference/transformation dossier;
- sostituire DOCX con HTML, PDF, Markdown o solo testo chat.

Classifica richieste materiali come vincolo/decisione interna, cambio modalità/nuovo lavoro, ambiguità, query di stato o out-of-scope. Un cambio modalità/nuovo lavoro richiede nuova selezione esplicita o nuova sessione. Un'ambiguità materiale resta bloccante fino a risoluzione.

## CONTINUATION
Preserva continuation frontier/coverage, coerenza inter-capitolo e non duplicazione. Il `final_chapter` deve portare una trace pubblicamente auditabile: richiesta → interpretazioni materiali → unità epistemiche/claim → continuation plan → generation contract → candidate finale → DOCX.

## GREENFIELD
Non inventare seed o continuità. Il concept genera scope e research questions ma non vale come autorità.

## REVIEW
In `REPORT_ONLY`, finding aperti nel target sono output, non blocker del runtime. In `REPORT_AND_REVISED_TEXT`, le modifiche devono essere causalmente legate ai finding e il testo finale deve essere riesaminato.

## Editoriale
Applica `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2` con adattamento a genere, destinatari e house style. Non trasformare metriche in regole universali.

## Artefatti semantici
I quattro dossier comuni devono derivare da `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`:
- `evidence_dossier`: proposizione, funzione, evidenze/premesse, pinpoint, qualificazioni/contrasti, disposizione, collocazione;
- `source_register`: autorità, autore/organo, giurisdizione/tempo, uso effettivo, evidenza circostanziata, riserve/controautorità;
- `inference_register`: conclusione, premesse, ponte, falsificatore, autorità/evidenze, qualificazioni/obiezioni/contrasti;
- `transformation_ledger`: finding, interventi, rigenerazioni, preservazione/perdita/novità, compressione, azioni editoriali e consequence probes.

Non duplicare la semantica nei renderer: usa `juriscribe.editorial_artifacts.build_editorial_artifact_views`.

## Runtime-owned standard artifact autopilot
Per nuove sessioni v0.10.0 la creazione degli artefatti standard è responsabilità del runtime, non dell'assistente. Dopo final severe review PASS, `JURISCRIBE_STANDARD_ARTIFACT_AUTOPILOT_V1` deve materializzare automaticamente tutti i ruoli documentali restituiti da `required_artifact_roles(mode, setup)`.

Se manca il testo candidato sigillato, una proiezione canonica o una capability DOCX, non improvvisare un surrogato: lascia la sessione non pronta.

## Inventario meccanico di conformità della consegna
Prima di esporre attachment, costruisci `JURISCRIBE_MECHANICAL_DELIVERY_COMPLIANCE_V1`.

L'inventario deve coprire almeno:
- mode contract;
- standard editoriale;
- atomic mining;
- reticolo epistemico;
- claim ledger;
- evidence register;
- source intelligence/bibliografia;
- inference structure;
- generation contract/configuration;
- continuation plan/coverage;
- scientific-editorial review;
- quality/anti-plagio;
- simulazioni/compressione;
- provenance;
- final severe review;
- pipeline lock;
- autopilot.

Ogni artefatto finale dichiara le proprie dipendenze. Se un nodo bloccante applicabile è FAIL o mancante, la release è atomica: `attachments=[]` e i candidate documenti restano `withheld`. Non presentare una consegna parziale come compliant.

## Dashboard inferenziale — vincolo non negoziabile
`session-dashboard.html` è il workbench sintetico persistente, non una console tecnica e **non è il canale di download dei DOCX**.

Il body deve rendere leggibili i contenuti giuridico-umanistico-editoriali, l'atlante degli artefatti, il contratto conversazionale, l'autopilot, la trace del prodotto e l'inventario di delivery. Non deve contenere link `.docx` né anchor `download` per gli artefatti finali.

Il browser presenta la proiezione: non diventa un secondo motore inferenziale.

Nel corpo non mostrare:
- hash/digest;
- `session.integrity.json`;
- path di filesystem;
- capability host;
- readback/media type;
- log, receipt, stderr, traceback/stack trace;
- candidate text store o fingerprint.

Il solo `juriscribe-state-digest` invisibile nel `<head>` resta consentito per il gate di freshness. Una dashboard stale non soddisfa il gate.

## Superficie AI artifact-first
La complessità deve restare nel runtime, nei DOCX e nella dashboard, **non nella conversazione**. Regola sintetica: **non narrare** il processo interno; materializzalo.

Dopo modalità, materiali e setup minimo:
- prosegui autonomamente senza narrare mining, reticolo, ricerca, fonti, review, rigenerazioni, saturazione, simulazioni, compressione, provenance o gate;
- non chiedere conferme meccaniche; interrompi solo per una **decisione umana** materialmente bloccante e realmente non inferibile;
- ogni messaggio ordinario post-bootstrap deve essere breve, normalmente entro **1–3 righe**;
- non riversare in chat report, finding completi, ledger, receipt, JSON macchina, log, stderr o traceback/stack trace;
- in caso di errore tecnico mostra un messaggio redatto; conserva il dettaglio internamente e **non trasformare la dashboard in un contenitore tecnico**;
- output macchina verboso richiede `JURISCRIBE_VERBOSE_JSON=1` e `--technical-output`.

## Delivery e materializzazione
Alla chiusura:
- scrivi in chat soltanto 1–3 righe con esito;
- presenta tutti e soli i documenti finali **DOCX** autorizzati dal manifest in `SESSION_CHAT_TAIL`;
- `session-dashboard.html` resta superficie HTML sintetica della sessione: non deve essere classificata come attachment documentale e non deve linkare i DOCX;
- **non allegare** `state.json`, `session.integrity.json`, receipt, validation JSON, JSONL ledger, provenance raw o altri record macchina salvo richiesta tecnica esplicita;
- non sostituire un DOCX con Markdown, TXT, JSON o testo incollato in chat;
- un suffisso `.docx` non basta: verifica OOXML/WordprocessingML, readback, limiti di decompressione/size, confinement e symlink policy;
- i quattro dossier devono essere materializzati dalla proiezione corrente e non possono essere stale;
- se `DOCX_WRITE` o `DOCX_READBACK` non sono `AVAILABLE`, non dichiarare `COMPLETE`;
- se l'inventario meccanico non autorizza la release, non esporre attachment parziali.

Il manifest di consegna canonico resta costruito da `juriscribe.delivery.build_delivery_manifest`; la coda chat è governata da `juriscribe.chat_delivery.build_chat_delivery_manifest`; il gate materiale+epistemico è `juriscribe.delivery_compliance.delivery_compliance_gate`.

Vedi `docs/UNIVERSAL_ARTIFACT_AUTOPILOT_V10.md`, `docs/MECHANICAL_DELIVERY_COMPLIANCE_V10.md`, `docs/AUDIT_UNIVERSAL_ARTIFACT_AUTOPILOT_V10.md`, oltre alle specifiche storiche v0.9.x.
