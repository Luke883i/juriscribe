# Juriscribe

Juriscribe è un **runtime per lavoro giuridico scientifico-editoriale auditabile**. Opera in tre modalità canoniche e usa una superficie **artifact-first**: la complessità resta nei documenti e nella dashboard, non nella conversazione.

| Modalità | Quando usarla | Output principale |
|---|---|---|
| `CONTINUATION` | hai capitoli/segmenti precedenti e vuoi scrivere N+1 | `final_chapter` |
| `GREENFIELD` | parti da concept, prompt, quesito o mandato e vuoi un nuovo testo/monografia | `final_legal_text` |
| `REVIEW` | hai un testo completo e vuoi revisione scientifica, contenutistica e redazionale | `review_report` (+ eventuale `revised_legal_text`) |

In tutte le modalità Juriscribe usa mining epistemico, reticolo, fonti circostanziate, inferenze esplicite, review, saturazione, provenance e una baseline editoriale comune adattata al genere: struttura proporzionata, terminologia, autorità e controautorità, citazioni, bibliografia, perimetro temporale/giurisdizionale, registro, leggibilità e audience fit.

## Esperienza del giurista

Dopo il bootstrap l'esperienza ordinaria deve restare semplice:

1. scegli `CONTINUATION`, `GREENFIELD` o `REVIEW`;
2. fornisci i materiali;
3. ricevi soltanto il setup minimo realmente necessario;
4. accetti o modifichi i parametri;
5. **attendi gli artefatti finali**, salvo una decisione umana materialmente bloccante che Juriscribe non possa inferire in modo sicuro.

Juriscribe non deve trasformare la chat in un diario di lavorazione. Mining, ricerca, reticolo, review, rigenerazioni, simulazioni, saturazione, compressione e provenance appartengono al runtime e agli artefatti. La dashboard appartiene al giurista: dalla v0.9.4 non è più una superficie di telemetria, ma il dossier inferenziale integrato della sessione.

## Avvio in una sessione AI

Fornisci `https://github.com/Luke883i/juriscribe` oppure un bundle locale e usa questo prompt:

```text
Usa il repository/bundle Juriscribe che ti ho fornito come runtime della sessione.

Prima di lavorare sui miei materiali:
1. individua la superficie di admission/bootstrap dichiarata dal repository;
2. mostrami i termini correnti e non accettarli per mio conto;
3. se scrivo esattamente `I ACCEPT`, usa la fast path canonica dopo l'accettazione oppure conserva i passaggi separati di probe/initialize;
4. non inizializzare senza probe receipt valida;
5. dopo initialize non presumere il tipo di lavoro: fammi scegliere fra `CONTINUATION`, `GREENFIELD`, `REVIEW` e `ALTRO`;
6. considera il lavoro sostanziale autorizzato solo dopo la selezione della modalità.

Dopo la selezione della modalità:
- mantieni separati runtime, istruzioni, corpus dell'utente e fonti esterne;
- materializza un mode contract e uno standard editoriale adatto al genere e al destinatario;
- esegui mining atomico, reticolo e source/inference discipline prima delle conclusioni sostanziali;
- non trasformare concept, testo da revisionare o capitoli precedenti in autorità giuridiche auto-validanti;
- applica gli standard redazionali tipici in modo fluido, non meccanico;
- lavora autonomamente e NON narrare in chat i passaggi intermedi di mining, ricerca, review, rigenerazione, saturazione, simulazione, compressione, provenance o gate;
- non chiedere conferme meccaniche: interrompimi soltanto per una decisione materialmente bloccante che non sia inferibile in modo sicuro;
- non esporre chain-of-thought; evidenze, locator, inferenze registrate, finding e decisioni auditabili devono stare negli artefatti;
- non riversare in chat report, liste estese di fonti/evidenze, ledger, receipt, provenance raw, JSON, log, stderr o traceback;
- senza DOCX_WRITE e DOCX_READBACK reali non dichiarare COMPLETE;
- prima della consegna esegui provenance, final severe review, readback e completion gate specifico della modalità;
- alla fine scrivi in chat soltanto 1–3 righe e rimanda ai documenti allegati e alla dashboard;
- allega i documenti finali in DOCX realmente materializzati e sempre `session-dashboard.html` aggiornata;
- non allegare log, receipt, `state.json`, `session.integrity.json`, provenance raw o validation JSON salvo mia richiesta tecnica esplicita.
```

## CONTINUATION

Dopo `CONTINUATION`, carica i capitoli `1..N`, bibliografia e vincoli editoriali. Juriscribe costruisce il continuation frontier e genera N+1 solo dopo reticolo, setup e contratti.

## GREENFIELD

Dopo `GREENFIELD`, fornisci il concept o mandato. Juriscribe lo scompone in problemi, claim e questioni di ricerca; **il concept orienta, non prova**. Il setup chiarisce tipo di documento, pubblico, lunghezza, postura e livello di ricerca.

## REVIEW

Dopo `REVIEW`, carica il testo completo. Il default è `REPORT_ONLY`: una review può essere completa anche se conclude che il testo ha blocker o major finding. Se vuoi anche una riscrittura scegli `REPORT_AND_REVISED_TEXT`; in quel caso il testo revisionato deve essere riesaminato.

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

Le metriche editoriali sono segnali di audit, non regole universali.

## Pipeline comune

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
→ LEGAL-HUMANISTIC ARTIFACT PROJECTION
→ REAL DOCX MATERIALIZATION + READBACK
→ CURRENT INFERENTIAL HTML DASHBOARD
→ DELIVERY MANIFEST
→ COMPLETE
```

`CONTINUATION` conserva continuation frontier/coverage. `GREENFIELD` non inventa una continuità inesistente. `REVIEW` non richiede che il testo sorgente diventi “PASS” per poter consegnare un report diagnostico.

## Artefatti giuridico-umanistico-editoriali v0.9.4

I quattro dossier comuni non sono più soltanto ruoli di consegna: condividono la proiezione canonica `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`.

### Evidence dossier

Ricostruisce **proposizione → funzione giuridica → fonte/premessa → pinpoint → qualificazioni/contrasti → disposizione → collocazione finale**. Deve consentire a un revisore di capire perché una proposizione è sostenibile nella forma in cui appare.

### Source register

Non è una bibliografia duplicata. Rende visibili carattere dell'autorità, autore/organo, giurisdizione e tempo, ruolo nel ragionamento, claim sostenuti, evidenza circostanziata e controautorità/riserve.

### Inference register

Separa il dato attestato dal passaggio interpretativo. Per ogni inferenza materiale rende leggibili conclusione, premesse testuali, ponte, falsificatore, autorità/evidenze, qualificazioni, obiezioni, contrasti e disposizione finale.

### Transformation ledger

Racconta la storia causale del testo: finding, interventi, rigenerazioni, contenuti preservati/persi/introdotti, compressione lossless, azioni editoriali e consequence probes della final severe review.

La specifica completa è `docs/EDITORIAL_ARTIFACTS_V9_4.md`.

## Contratto di consegna v0.9.4

La chat post-bootstrap è una **superficie di controllo**, non una superficie di report. Normalmente contiene solo richieste umane non inferibili, un next step essenziale o il rinvio finale agli allegati. Il limite ordinario è 1–3 righe.

Tutti i documenti user-facing devono essere **DOCX reali**:

- `final_chapter` / `final_legal_text` / `review_report` / eventuale `revised_legal_text`;
- `evidence_dossier`;
- `source_register`;
- `inference_register`;
- `transformation_ledger`;
- `review_findings_register` quando applicabile.

Non basta che il path finisca in `.docx`: il file deve esistere, non essere vuoto, risultare un pacchetto OOXML/WordprocessingML leggibile e avere digest/size verificati al gate.

`session_dashboard` è sempre HTML ed è allegata come `session-dashboard.html`. Il suo **corpo contiene soltanto il resoconto giuridico-umanistico-editoriale**: mandato, cornice editoriale e l'intero contenuto dei quattro dossier. Non mostra digest, integrity, path, capability, readback, log o traceback.

Il metadata invisibile `juriscribe-state-digest` resta nel `<head>` per conservare il controllo di freshness: una dashboard stale continua a non valere come dashboard finale.

I quattro dossier registrati dalla v0.9.4 sono inoltre sigillati rispetto alla propria proiezione semantica. Se il quadro inferenziale cambia, devono essere rimaterializzati prima del completion gate.

I record macchina (`state.json`, `session.integrity.json`, receipt, provenance raw, validation JSON, JSONL ledger, traceback) restano interni e non devono essere allegati nella consegna ordinaria.

Se `DOCX_WRITE` o `DOCX_READBACK` non sono `AVAILABLE`, Juriscribe resta non pronto: non degrada a Markdown/JSON né compensa incollando il contenuto in chat.

Specifica corrente: `docs/FINAL_DELIVERY_V9_4.md`. La precedente `FINAL_DELIVERY_V9_2.md` resta come documento storico degli invarianti di materializzazione introdotti in quella release.

## Dashboard

`session-dashboard.html` è il **dossier inferenziale giuridico-umanistico-editoriale** della sessione. La regola è di parità, non di sommario:

```text
Dashboard = cornice umana
          + Evidence dossier
          + Source register
          + Inference register
          + Transformation ledger
```

La dashboard non è una console tecnica. Il runtime conserva i controlli tecnici nei record interni e nei metadata invisibili necessari ai gate.

## Integrità

Il record canonico è `.juriscribe/<session>/session.integrity.json`. `node.h` è ritirato: viene letto solo per migrare vecchi workspace. L'integrity manifest resta interno e non appartiene al pacchetto ordinario di allegati.

## Audit e non-regressione

`docs/AUDIT_MAIN_V9_4.md` documenta il nuovo audit di `main`, i pattern consolidati, gli anti-pattern corretti e la DoD. La strategia è additiva: la proiezione semantica si colloca sopra i record esistenti e non modifica reticolo, provenance, review receipts, simulation receipts o fixed-point.

## Validazione e CI

La CI conserva le baseline storiche: 400k v5, M+1000, continuation v6, mutazioni v7, reflection v8, tri-mode v9 e tutti i fixed-point. I regression test v0.9.4 aggiungono parità dossier/dashboard, assenza di telemetria dal corpo HTML e semantic-drift detection.

## Versioni

- runtime: `0.9.4`
- access contract: `1.7.0`
- manifest: `juriscribe-manifest/v9`

Documentazione corrente: `docs/MODES_V9.md`, `docs/EDITORIAL_STANDARD_V9.md`, `docs/RUNTIME_V9_TRI_MODE.md`, `docs/EDITORIAL_ARTIFACTS_V9_4.md`, `docs/FINAL_DELIVERY_V9_4.md`, `docs/AUDIT_MAIN_V9_4.md`, `docs/HISTORIOGRAPHIC_AUDIT_V9_2.md`, `docs/RUNTIME_HARDENING_V9_3.md`, `docs/AGENT_RUNTIME_RULES.md`, `docs/SESSION_MODEL.md`.
