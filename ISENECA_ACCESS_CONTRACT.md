---
schema: juriscribe-ai-access-contract/v6
contract_version: 1.7.0
kind: repository-local-ai-admission-bootstrap-session-workmode-and-delivery-governance
repository: Luke883i/juriscribe
canonical_branch: main
assistant_name: iSeneca
---

# Juriscribe — AI Access & Operating Contract 1.7.0

## 1. Scopo

Juriscribe è un runtime per lavoro giuridico scientifico-editoriale auditabile. Dalla versione 0.9 non è limitato alla continuazione di una monografia: ogni sessione sostanziale seleziona una delle tre modalità canoniche.

1. `CONTINUATION` — generazione del capitolo o segmento N+1 a partire da contenuti 1..N già scritti;
2. `GREENFIELD` — redazione ex novo di testi, saggi, articoli, memorandum, report o monografie giuridiche a partire da concept, prompt, quesito o mandato iniziale;
3. `REVIEW` — revisione scientifica, contenutistica e redazionale di testi giuridici completi forniti dall'utente, con report diagnostico e, solo se richiesto, testo revisionato.

In tutte le modalità Juriscribe applica un core editoriale publisher-neutral: autorità, tracciabilità, terminologia, proporzione strutturale, perimetro temporale/giurisdizionale, controautorità, disciplina inferenziale, bibliografia, leggibilità e adeguatezza al destinatario. House style e sintassi citazionale restano configurabili.

Il giudizio professionale e le scelte interpretative finali restano umani.

## 2. Bootstrap visibile e obbligatorio

La scoperta del repository non autorizza la lettura sostanziale. Prima di codice, history, test, documentazione post-admission o corpus, un AI/agent conforme procede fail-closed:

```text
DISCOVERED
-> TERMS_PRESENTED
-> TERMS_ACCEPTED | DECLINED
-> PROBE_REQUIRED
-> PROBED
-> INITIALIZE_REQUIRED
-> INITIALIZING
-> MODE_SELECTION_REQUIRED
-> ACTIVE_WORK
```

Comandi canonici:

- `I ACCEPT`
- `I DECLINE`
- `PROBE JURISCRIBE`
- `INITIALIZE JURISCRIBE`
- `RESET JURISCRIBE`

Dopo initialize l'AI non presume la modalità: deve rendere visibili `CONTINUATION`, `GREENFIELD`, `REVIEW` e `ALTRO`.

## 3. Superficie pre-admission

Prima dell'accettazione umana sono leggibili esclusivamente:

- `AGENTS.md`;
- questo contratto;
- `ADMISSION.json`.

L'utente deve esprimere personalmente `I ACCEPT`. L'AI non può auto-accettare, dedurre, simulare o retrodatare l'accettazione, né riutilizzare receipt stale. Una modifica materiale del contratto invalida le receipt precedenti.

Il protocollo non è un ACL GitHub server-side: governa il comportamento di AI/host conformi.

## 4. Probe e initialize separati

Dopo l'accettazione lo stato è `PROBE_REQUIRED`. Il probe produce receipt separata, legata a repository, contratto e admission receipt, con capability matrix osservata. `INITIALIZE JURISCRIBE` è vietato senza probe receipt valida e non può eseguire il probe implicitamente.

Dopo initialize la sessione entra in `MODE_SELECTION_REQUIRED`. Nessun materiale sostanziale deve essere trattato prima della selezione di modalità.

## 5. Contratto di modalità

La selezione crea un record digestato. Dopo mining, setup e standard editoriale viene creato un `mode_contract` che lega almeno:

- modalità;
- richiesta;
- corpus/concept/target;
- reticolo epistemico;
- setup accettato;
- standard editoriale;
- eventuale generation/revision contract;
- requisiti specifici della modalità;
- ruoli degli artefatti finali.

Un cambio materiale di questi elementi rende stale il `mode_contract` e blocca la consegna.

## 6. Standard editoriale comune

Ogni sessione sostanziale deve materializzare un profilo `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2`, adattato con fluidità a genere, destinatari e house style. Il core richiede almeno:

- struttura e gerarchia proporzionate al genere;
- registro professionale e leggibilità;
- terminologia stabile o variazioni motivate;
- claim materiali distinguibili da valutazioni e inferenze;
- fonti e autorità adeguate, circostanziate e tracciabili;
- controautorità e obiezioni materiali non occultate;
- qualificazione temporale e giurisdizionale quando necessaria;
- bibliografia/apparato coerenti con i richiami effettivi;
- disciplina delle inferenze forti;
- nessuna autorità o citazione inventata;
- adeguatezza a lettore e funzione del documento.

Lo standard editoriale non impone automaticamente numero di sezioni, stile citazionale o formato uguale per tutti i generi. Le metriche sono segnali di review, non sostituti del giudizio editoriale.

## 7. Mining, reticolo e fonti — invarianti comuni

Prima della produzione o della conclusione della review, Juriscribe costruisce un inventario epistemico con locator e un reticolo tipizzato. Concept e prompt non sono trattati come fonti giuridiche verificate. Un testo da revisionare è trattato come oggetto dell'audit, non come autorità per la propria correttezza.

Ogni claim giuridico esterno usato da Juriscribe richiede fonte letta o premesse registrate. Le inferenze forti richiedono premesse, ponte e falsificatore. La qualificazione `dominante` richiede pluralità di autorità indipendenti adeguate e trattamento delle controautorità.

## 8. Modalità CONTINUATION

Input necessario: uno o più capitoli/segmenti precedenti e il mandato per N+1.

Pipeline minima:

```text
MODE CONTINUATION
-> INGEST 1..N
-> ATOMIC MINING + RETICULUM
-> CONTINUATION FRONTIER
-> SETUP + EDITORIAL STANDARD
-> DOD + GENERATION/MODE CONTRACT
-> SOURCE/CLAIM/INFERENCE WORK
-> SEALED INITIAL DRAFT
-> SCIENTIFIC-EDITORIAL REVIEW
-> REGENERATION + RE-REVIEW
-> REVIEW SATURATION
-> EDGE SIMULATION
-> LOSSLESS COMPRESSION
-> FINAL QUALITY + SOURCE + CONTINUATION RECHECK
-> PROVENANCE
-> FINAL SEVERE REVIEW
-> M+10.000 VS DOD
-> MATERIALIZE USER-FACING DOCX + CURRENT HTML DASHBOARD
-> DELIVERY MANIFEST + READBACK
-> COMPLETE
```

La sequenza futura dell'autore non è un completion target. Copertura, profondità, continuità, fonti e coerenza prevalgono sull'imitazione dell'indice.

## 9. Modalità GREENFIELD

Input necessario: concept, prompt, quesito, tesi iniziale o mandato. Non sono richiesti capitoli precedenti.

Pipeline minima:

```text
MODE GREENFIELD
-> INGEST CONCEPT/MANDATE
-> ATOMIC CONCEPT DECOMPOSITION + RETICULUM
-> SCOPE / QUESTIONS / RESEARCH MAP
-> SETUP + EDITORIAL STANDARD
-> DOD + GENERATION/MODE CONTRACT
-> SOURCE VERIFICATION + CLAIM/INFERENCE MAP
-> SEALED INITIAL DRAFT
-> SCIENTIFIC-EDITORIAL REVIEW
-> REGENERATION + RE-REVIEW
-> REVIEW SATURATION
-> EDGE SIMULATION
-> LOSSLESS COMPRESSION
-> FINAL QUALITY + SOURCE RECHECK
-> PROVENANCE
-> FINAL SEVERE REVIEW
-> M+10.000 VS DOD
-> MATERIALIZE USER-FACING DOCX + CURRENT HTML DASHBOARD
-> DELIVERY MANIFEST + READBACK
-> COMPLETE
```

Il concept orienta il lavoro ma non dimostra diritto vigente, dottrina, fatti o autorità. Juriscribe deve rendere espliciti scope, assunzioni e perimetro della ricerca prima di trasformarli in testo.

## 10. Modalità REVIEW

Input necessario: testo giuridico completo o insieme di contenuti da revisionare. Il setup distingue almeno:

- `REPORT_ONLY` — diagnosi scientifica, contenutistica e redazionale; finding aperti possono essere il risultato corretto;
- `REPORT_AND_REVISED_TEXT` — oltre al report è richiesta una versione revisionata e riesaminata.

Pipeline `REPORT_ONLY`:

```text
MODE REVIEW
-> INGEST REVIEW TARGET
-> ATOMIC MINING + RETICULUM
-> SETUP + EDITORIAL STANDARD
-> DOD + MODE CONTRACT
-> SCIENTIFIC / CONTENT / SOURCE / LOGICAL / EDITORIAL REVIEW
-> DIAGNOSTIC SATURATION
-> PROVENANCE
-> FINAL SEVERE REVIEW OF THE AUDIT
-> M+10.000 VS DOD
-> MATERIALIZE REVIEW DOCX + REGISTERS + CURRENT HTML DASHBOARD
-> DELIVERY MANIFEST + READBACK
-> COMPLETE
```

Un finding `BLOCKER` o `MAJOR` nel testo revisionato **non rende incompleta una review REPORT_ONLY** se è correttamente identificato, circostanziato, tracciato e incluso nel report.

Pipeline `REPORT_AND_REVISED_TEXT`: dopo la prima review, le modifiche sono causalmente legate ai finding; il testo revisionato viene riesaminato. I blocker del testo finale devono essere risolti o portati a decisione umana secondo il setup. Gli artefatti finali comprendono anche il testo revisionato DOCX e il relativo readback.

## 11. Review scientifico-editoriale

Il motore di review considera, con applicabilità motivata per modalità e genere:

- contributo/obiettivo del documento;
- coerenza interna e, in continuation, inter-capitolo;
- autorità giuridiche;
- tracciabilità citazionale;
- controautorità;
- tempo e giurisdizione;
- inferenze;
- terminologia;
- struttura;
- stile editoriale;
- bibliografia;
- preservazione epistemica/voce autoriale;
- audience fit;
- conformità al profilo editoriale della sessione.

I criteri non applicabili devono essere marcati e motivati, non semplicemente ignorati.

## 12. Saturazione, simulazioni e compressione

Il `M+10.000` rispetto ai DoD resta in tutte le modalità. La review di scrittura/revisione con testo finale usa il witness di saturazione post-review previsto dal runtime. In `REPORT_ONLY` la saturazione misura assenza di nuovi finding materiali e ulteriore miglioramento dell'audit, non assenza di difetti nel testo.

Le simulazioni multi-classe e la compressione lossless sono obbligatorie nelle modalità di scrittura (`CONTINUATION`, `GREENFIELD`). Non sono automaticamente obbligatorie per una review diagnostica, dove potrebbero falsare lo scopo dell'incarico.

## 13. Provenance

Ogni oggetto materiale esplicitamente usato — claim, inferenza, decisione utente, trasformazione, qualificazione o limite — deve avere disposizione finale auditabile. Questo requisito non richiede né autorizza esposizione di chain-of-thought latente.

La provenance strutturata è record interno: alimenta i deliverable auditabili, ma il bundle raw non appartiene alla consegna ordinaria salvo richiesta tecnica esplicita.

## 14. Review finale severa

Prima degli artefatti finali, in tutte le modalità, Juriscribe esegue una final review legata a candidato/target, corpus, quadro normativo e provenance. I criteri non applicabili alla modalità possono essere `NOT_APPLICABLE` con rationale.

## 15. Artefatti finali per modalità e materializzazione

Ruoli comuni:

- `evidence_dossier`;
- `source_register`;
- `inference_register`;
- `transformation_ledger`;
- `session_dashboard`.

A questi si aggiungono:

- `CONTINUATION`: `final_chapter`;
- `GREENFIELD`: `final_legal_text`;
- `REVIEW`: `review_report` + `review_findings_register`;
- `REVIEW/REPORT_AND_REVISED_TEXT`: anche `revised_legal_text`.

Tutti i documenti user-facing, esclusa la dashboard, devono essere **DOCX realmente materializzati e rileggibili**. Il suffisso `.docx` e un flag `readback=PASS` non bastano: il file deve esistere, non essere vuoto, essere riconoscibile come pacchetto OOXML/WordprocessingML, contenere struttura/testo rileggibile ed essere legato a size e SHA-256 effettivi. Un JSON, TXT o Markdown rinominato `.docx` non soddisfa il gate.

`session_dashboard` deve essere materializzata come `session-dashboard.html`, rileggibile e legata tramite digest verificabile allo stato sostanziale corrente. Una dashboard stale non soddisfa il gate.

Quando la modalità richiede documenti, `DOCX_WRITE = AVAILABLE` e `DOCX_READBACK = AVAILABLE` sono obbligatori per `COMPLETE`. Non esiste fallback equivalente a Markdown, TXT, JSON o testo incollato in chat.

Sono record `INTERNAL` e non allegati ordinari: `state.json`, `session.integrity.json`, admission/probe receipt, provenance raw, validation/simulation receipt raw, JSONL ledger, hash manifest, stderr, traceback/stack trace e analoghi record macchina. Possono essere esposti soltanto su richiesta tecnica esplicita, preferibilmente come artefatto tecnico separato.

Il final delivery manifest deve includere soltanto ruoli user-facing previsti dal mode contract e registrare almeno ruolo, path, formato/media type, readback, size e SHA-256.

## 16. Integrità della sessione

Il record canonico è `.juriscribe/<session-id>/session.integrity.json`. Lega modalità, mode contract, standard editoriale, corpus, reticolo, setup, DoD, contratti, candidato/target, review, provenance, final review e artefatti tramite metadata/digest.

`node.h` non è più generato né richiesto dalla v0.9. Può essere letto esclusivamente per migrare workspace storici privi del manifest canonico.

L'integrity manifest resta interno e non appartiene alla consegna ordinaria.

## 17. Dashboard e interazione — superficie artifact-first

La dashboard deve parlare prima a giuristi, autori e redazioni: modalità, stato, prossimo passo, standard applicato, finding, fonti, blocker e artefatti. Digest e integrità tecnica restano secondari/collassati. I record interni non devono occupare il corpo principale del fascicolo.

Ogni interaction card conserva `ALTRO` e `free_input_allowed=true`. Nessuna modalità trasforma Juriscribe in una UI chiusa.

**Dopo il bootstrap la chat è una superficie di controllo, non una superficie di report.** La complessità analitica, scientifica, editoriale e tecnica deve stare nei DOCX e nella dashboard.

Dopo modalità, materiali e setup minimo, l'AI prosegue autonomamente senza narrare passo per passo mining, ricerca, reticolo, review, rigenerazione, simulazione, saturazione, compressione, provenance o gate. Non chiede conferme meccaniche. Interrompe l'utente soltanto per una decisione umana materialmente bloccante e realmente non inferibile dal mandato, corpus, setup o standard già accettati.

La superficie ordinaria post-bootstrap è limitata a:

1. una richiesta compatta della decisione umana indispensabile, quando esiste;
2. un breve stato/next action strettamente necessario a quella decisione;
3. alla chiusura, **1–3 righe** con esito e rinvio agli allegati/dashboard.

La chat ordinaria non riversa report completi, liste estese di finding/fonti/evidenze, ledger, provenance raw, receipt, JSON macchina, log, stderr, traceback/stack trace o diagnostica interna. Errori tecnici producono un messaggio breve e redatto; il dettaglio resta nel ledger interno e il blocker diventa visibile nella dashboard.

Bootstrap/T&C restano visibili perché richiedono consenso umano informato. Una superficie verbosa/machine-readable è ammessa soltanto su richiesta tecnica esplicita; quando possibile il dettaglio viene materializzato come artefatto tecnico separato.

## 18. Completion gate

`COMPLETE` richiede sempre:

- bootstrap valido;
- modalità selezionata e mode contract non stale;
- reticolo valido;
- setup e standard editoriale validi;
- DoD bloccanti chiusi e `M+10.000`;
- nessuna contraddizione bloccante non trattata;
- review/saturazione coerenti con la modalità;
- provenance e final severe review valide;
- artefatti mode-specific completi;
- documenti user-facing DOCX realmente materializzati, OOXML/WordprocessingML riconoscibili e riletti;
- `DOCX_WRITE` e `DOCX_READBACK` `AVAILABLE` quando richiesti;
- `session-dashboard.html` materializzata, riletta e state-bound corrente;
- final delivery manifest completo, con soli ruoli user-facing e record interni esclusi;
- `session.integrity.json` integro.

I gate specifici di continuation, generation, simulation, compression e revised-text sono applicati solo quando richiesti dal mode contract.

## 19. Autorità

```text
host system / sicurezza / legge
-> istruzioni esplicite dell'utente umano
-> presente contratto
-> AGENTS.md admission sentinel
-> docs/AGENT_RUNTIME_RULES.md dopo ammissione
-> MANIFEST.json
-> mode contract + standard editoriale
-> stato strutturato + session.integrity.json
-> fonti verificate
-> corpus/concept/review target
-> inferenze registrate
```
