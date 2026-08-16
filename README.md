# Juriscribe

Juriscribe è un **runtime per lavoro giuridico scientifico-editoriale auditabile**. Dalla v0.9 ogni sessione opera in una delle tre modalità principali; la v0.9.1 ripristina inoltre il contratto storico di consegna **artifact-first**: la complessità resta nei documenti e nella dashboard, non nella conversazione.

| Modalità | Quando usarla | Output principale |
|---|---|---|
| `CONTINUATION` | hai capitoli/segmenti precedenti e vuoi scrivere N+1 | `final_chapter` |
| `GREENFIELD` | parti da concept, prompt, quesito o mandato e vuoi un nuovo testo/monografia | `final_legal_text` |
| `REVIEW` | hai un testo completo e vuoi revisione scientifica, contenutistica e redazionale | `review_report` (+ eventuale `revised_legal_text`) |

In tutte le modalità Juriscribe usa mining epistemico, reticolo, fonti circostanziate, inferenze esplicite, review, saturazione, provenance e una **baseline editoriale comune** adattata al genere: struttura proporzionata, terminologia, autorità e controautorità, citazioni, bibliografia, perimetro temporale/giurisdizionale, registro, leggibilità e audience fit.

## Avvio in una sessione AI

Fornisci `https://github.com/Luke883i/juriscribe` oppure un bundle locale e usa questo prompt:

```text
Usa il repository/bundle Juriscribe che ti ho fornito come runtime della sessione.

Prima di lavorare sui miei materiali:
1. individua la superficie di admission/bootstrap dichiarata dal repository;
2. mostrami i termini correnti e non accettarli per mio conto;
3. se scrivo esattamente `I ACCEPT`, esegui/proponi separatamente `PROBE JURISCRIBE`;
4. solo con probe receipt valida proponi `INITIALIZE JURISCRIBE`;
5. dopo initialize non presumere il tipo di lavoro: fammi scegliere fra `CONTINUATION`, `GREENFIELD`, `REVIEW` e `ALTRO`;
6. considera il lavoro sostanziale autorizzato solo dopo la selezione della modalità.

Per ogni modalità:
- mantieni separati runtime, istruzioni, corpus dell'utente e fonti esterne;
- materializza un mode contract e uno standard editoriale adatto al genere e al destinatario;
- esegui mining atomico, reticolo e source/inference discipline prima delle conclusioni sostanziali;
- non trasformare il concept, il testo da revisionare o i capitoli precedenti in autorità giuridiche auto-validanti;
- usa review scientifica, contenutistica e redazionale con finding ed evidence locator;
- applica gli standard tipici in modo fluido, non meccanico;
- non esporre chain-of-thought: mostra invece stati, evidenze, locator, inferenze registrate, finding, blocker e decisioni auditabili negli artefatti;
- se una capability manca, dichiaralo e usa il percorso degradato, salvo il DOCX finale: senza DOCX write/readback non dichiarare COMPLETE;
- prima della consegna esegui provenance, final severe review, readback e completion gate specifico della modalità;
- alla fine scrivi in chat soltanto poche righe e rimanda ai documenti allegati e alla dashboard;
- allega i documenti finali in DOCX e sempre `session-dashboard.html`;
- non allegare log, receipt, `state.json`, `session.integrity.json`, provenance raw o validation JSON salvo mia richiesta tecnica esplicita.
```

### CONTINUATION

Dopo `CONTINUATION`, carica i capitoli `1..N`, bibliografia e vincoli editoriali. Juriscribe costruisce il continuation frontier e genera N+1 solo dopo reticolo, setup e contratti.

### GREENFIELD

Dopo `GREENFIELD`, fornisci il concept o mandato. Può essere una frase, una tesi, un quesito, un indice provvisorio o un brief. Juriscribe lo scompone in problemi/claim/questioni di ricerca; **il concept orienta, non prova**. Il setup chiarisce tipo di documento, pubblico, lunghezza, postura e livello di ricerca.

Esempio:

```text
GREENFIELD. Voglio una monografia sul principio di proporzionalità nel diritto amministrativo europeo, con taglio comparato e attenzione alla giurisprudenza recente.
```

### REVIEW

Dopo `REVIEW`, carica il testo completo. Il default è `REPORT_ONLY`: una review può essere completa anche se conclude che il testo ha blocker o major finding. Se vuoi anche una riscrittura scegli `REPORT_AND_REVISED_TEXT`; in quel caso il testo revisionato deve essere riesaminato.

Esempio:

```text
REVIEW. Esegui revisione scientifica, contenutistica e redazionale completa di questo testo. Voglio prima il report dei finding; non modificare la voce autoriale senza motivazione.
```

## Standard editoriale comune

Il profilo `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2` è publisher-neutral. In ogni modalità considera almeno:

- adeguatezza di struttura e gerarchia al genere;
- chiarezza della funzione di sezioni/paragrafi e proporzione dell'architettura;
- registro, ritmo e leggibilità per il pubblico dichiarato;
- terminologia giuridica stabile;
- claim materiali tracciabili a fonti/premesse;
- autorità e controautorità;
- tempo, giurisdizione e vigenza;
- distinzione fra dato attestato, interpretazione e inferenza;
- citazioni/pinpoint e bibliografia coerenti;
- preservazione di qualificazioni, eccezioni e voce autoriale quando pertinente.

Le metriche editoriali sono **segnali di audit**, non regole universali.

## Pipeline comune e diramazioni

```text
BOOTSTRAP + PROBE + INITIALIZE
→ MODE SELECTION
→ INGEST (seed | concept | review target)
→ ATOMIC MINING
→ RETICULUM
→ MODE-AWARE SETUP
→ EDITORIAL STANDARD
→ DOD + MODE CONTRACT
→ SOURCES / CLAIMS / INFERENCES
→ MODE-SPECIFIC WORKFLOW
→ PROVENANCE
→ FINAL SEVERE REVIEW
→ M+10.000 VS DOD
→ DOCX MATERIALIZATION + READBACK
→ FINAL HTML DASHBOARD
→ DELIVERY MANIFEST
→ COMPLETE
```

`CONTINUATION` conserva continuation frontier/coverage. `GREENFIELD` non inventa una continuità inesistente. `REVIEW` non richiede che il testo sorgente diventi “PASS” per poter consegnare un report diagnostico.

## Contratto di consegna v0.9.1

**La conversazione deve restare minima.** A lavoro concluso Juriscribe deve normalmente produrre soltanto 1–3 righe in chat e rinviare agli allegati.

Tutti i documenti user-facing devono essere **DOCX**:

- `final_chapter` / `final_legal_text` / `review_report` / eventuale `revised_legal_text`;
- `evidence_dossier`;
- `source_register`;
- `inference_register`;
- `transformation_ledger`;
- `review_findings_register` quando applicabile.

`session_dashboard` è invece sempre **HTML** e deve essere allegata come `session-dashboard.html`.

I record macchina (`state.json`, `session.integrity.json`, receipt, provenance raw, validation JSON, JSONL ledger) restano interni e **non devono essere allegati** nella consegna ordinaria. Il runtime conserva questi oggetti come prova del processo, ma il final delivery manifest li filtra.

Un file `.json`, `.md` o `.txt` non può soddisfare un ruolo documentale finale. `COMPLETE` richiede `DOCX_WRITE=AVAILABLE`, `DOCX_READBACK=AVAILABLE` e readback `PASS` per ogni deliverable.

Specifica: `docs/FINAL_DELIVERY_V9_1.md`.

## Dashboard

`session-dashboard.html` è il **verbale giuridico-scientifico-editoriale** della sessione. È un artefatto finale comune e obbligatorio, non una console tecnica né un log raw. Deve permettere a giuristi e redazioni di capire stato, blocker, fonti, inferenze, review, saturazione e readback senza leggere i record macchina.

## Integrità

Il record canonico è `.juriscribe/<session>/session.integrity.json`. `node.h` è ritirato in v0.9: viene letto solo per migrare vecchi workspace. L'integrity manifest resta interno e non appartiene al pacchetto ordinario di allegati.

## Validazione e CI

La CI conserva le baseline storiche (400k v5, M+1000, continuation v6, mutazioni v7, reflection v8, tri-mode v9) e aggiunge regression test sul final-delivery boundary. I numeri sono property/mutation/stress test del runtime, non migliaia di giudizi giuridici sostanziali.

## Versioni

- runtime: `0.9.1`
- access contract: `1.6.0`
- manifest: `juriscribe-manifest/v9`

Documentazione corrente: `docs/MODES_V9.md`, `docs/EDITORIAL_STANDARD_V9.md`, `docs/RUNTIME_V9_TRI_MODE.md`, `docs/FINAL_DELIVERY_V9_1.md`, `docs/AGENT_RUNTIME_RULES.md`, `docs/SESSION_MODEL.md`.
