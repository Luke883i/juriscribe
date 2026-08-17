# Juriscribe

Juriscribe è un **runtime per lavoro giuridico scientifico-editoriale auditabile**. Opera in tre modalità canoniche e usa una superficie **artifact-first**: il ragionamento verificabile, le fonti, il reticolo e le revisioni restano nello stato/negli artefatti; la chat resta breve.

| Modalità | Quando usarla | Output principale |
|---|---|---|
| `CONTINUATION` | hai capitoli/segmenti precedenti e vuoi scrivere N+1 | `final_chapter.docx` |
| `GREENFIELD` | parti da concept, quesito o mandato | `final_legal_text.docx` |
| `REVIEW` | vuoi revisione scientifica, contenutistica e redazionale | `review_report.docx` (+ eventuale `revised_legal_text.docx`) |

In tutte le modalità Juriscribe usa mining epistemico, reticolo, fonti circostanziate, inferenze esplicite, review, saturazione, provenance e lo standard `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2`.

## Esperienza del giurista

Dopo il bootstrap l'esperienza ordinaria è:

1. scegli `CONTINUATION`, `GREENFIELD` o `REVIEW`;
2. fornisci i materiali;
3. ricevi il setup minimo necessario;
4. accetti o modifichi abstract, concetti chiave, lunghezza e altri parametri applicabili;
5. **attendi gli artefatti finali**, salvo una decisione umana materialmente bloccante non inferibile in modo sicuro.

Juriscribe non trasforma la chat in un diario di lavorazione. Mining, ricerca, reticolo, review, rigenerazioni, simulazioni, saturazione, compressione e provenance appartengono al runtime e agli artefatti.

## Avvio in una sessione AI

Fornisci `https://github.com/Luke883i/juriscribe` oppure un bundle locale e usa questo prompt:

```text
Usa il repository/bundle Juriscribe come runtime della sessione.

Prima di lavorare sui miei materiali:
1. individua admission/bootstrap dichiarati dal repository;
2. mostrami i termini correnti e non accettarli per mio conto;
3. se scrivo esattamente `I ACCEPT`, conserva probe e initialize come receipt distinti;
4. non inizializzare senza probe receipt valida;
5. dopo initialize fammi scegliere fra CONTINUATION, GREENFIELD, REVIEW e ALTRO;
6. considera autorizzato il lavoro sostanziale solo dopo la selezione della modalità.

Dopo la selezione:
- considera la modalità, l'artefatto primario e il set standard come vincoli di runtime;
- interpreta il linguaggio naturale come modifica interna solo quando compatibile con il mode contract;
- non consentire a locuzioni informali di cambiare modalità, saltare la pipeline, sopprimere dossier o sostituire DOCX con HTML/testo chat;
- esegui mining atomico, reticolo, source/evidence/inference discipline, review, provenance e final severe review;
- lavora autonomamente e NON narrare in chat mining, ricerca, review, rigenerazione, saturazione, simulazione, compressione, provenance o gate;
- non esporre chain-of-thought;
- senza DOCX_WRITE e DOCX_READBACK reali non dichiarare COMPLETE;
- materializza automaticamente tutti gli artefatti standard previsti dalla modalità;
- prima della consegna costruisci l'inventario materiale+epistemico e applica release atomica;
- alla fine scrivi in chat soltanto 1–3 righe;
- presenta in coda alla sessione-chat tutti e soli i documenti finali DOCX autorizzati dal manifest;
- usa session-dashboard.html come workbench sintetico persistente: non deve linkare i DOCX né contenere anchor download;
- non allegare log, receipt, state.json, session.integrity.json, provenance raw o validation JSON salvo richiesta tecnica esplicita.
```

## Pipeline comune v0.10.0

```text
BOOTSTRAP + PROBE + INITIALIZE
→ MODE SELECTION
→ NATURAL-LANGUAGE PIPELINE LOCK
→ INGEST
→ ATOMIC MINING
→ EPISTEMIC RETICULUM
→ MODE-AWARE SETUP
→ EDITORIAL STANDARD
→ DOD + MODE CONTRACT
→ SOURCES / CLAIMS / EVIDENCE / INFERENCES
→ MODE-SPECIFIC WORKFLOW
→ REVIEW / SATURATION
→ SIMULATIONS / COMPRESSION (quando applicabili)
→ PROVENANCE
→ FINAL SEVERE REVIEW
→ RUNTIME-OWNED STANDARD ARTIFACT AUTOPILOT
→ REAL DOCX MATERIALIZATION + READBACK
→ MATERIAL + EPISTEMIC DELIVERY INVENTORY
→ CURRENT SYNTHETIC HTML DASHBOARD
→ ATOMIC CHAT-TAIL DELIVERY MANIFEST
→ COMPLETE
```

`CONTINUATION` conserva continuation frontier/coverage. `GREENFIELD` non inventa una continuità inesistente. `REVIEW` usa `REPORT_ONLY` come default; con `REPORT_AND_REVISED_TEXT` materializza anche il testo revisionato e lo governa come artefatto narrativo.

## Artefatti standard

### Artefatti comuni DOCX

- `evidence_dossier.docx`
- `source_register.docx`
- `inference_register.docx`
- `transformation_ledger.docx`

### Artefatti specifici

- CONTINUATION: `final_chapter.docx`
- GREENFIELD: `final_legal_text.docx`
- REVIEW: `review_report.docx`, `review_findings_register.docx`, eventuale `revised_legal_text.docx`

### Dashboard

`session-dashboard.html` è il workbench sintetico persistente. **Non è un attachment DOCX e non è il canale di download dei documenti.** Riepiloga contenuto, funzione e stato degli artefatti e delle logiche epistemiche; i DOCX sono destinati alla coda della sessione-chat.

## Quattro dossier giuridico-umanistico-editoriali

I quattro dossier condividono la proiezione canonica `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`.

### Evidence dossier

Ricostruisce **proposizione → funzione giuridica → fonte/premessa → pinpoint → qualificazioni/contrasti → disposizione → collocazione finale**.

### Source register

Rende visibili autorità, autore/organo, giurisdizione e tempo, ruolo nel ragionamento, claim sostenuti, evidenza circostanziata e controautorità/riserve.

### Inference register

Separa il dato attestato dal passaggio interpretativo: conclusione, premesse, ponte inferenziale, falsificatore, autorità/evidenze, qualificazioni e obiezioni.

### Transformation ledger

Ricostruisce la storia causale del testo: finding, interventi, rigenerazioni, contenuti preservati/persi/introdotti, compressione lossless, azioni editoriali e consequence probes.

Specifiche storiche preservate: `docs/EDITORIAL_ARTIFACTS_V9_4.md`.

## Pipeline lock contro il deragliamento conversazionale

Da v0.10.0 `JURISCRIBE_NATURAL_LANGUAGE_PIPELINE_LOCK_V1` congela modalità, artefatto primario e set standard. Le istruzioni naturali vengono trattate come:

- vincoli o decisioni interne compatibili;
- query di stato;
- richiesta di nuovo lavoro/cambio modalità, da isolare;
- richiesta ambigua, da risolvere prima di modificare stato materiale.

Non è consentito cambiare implicitamente modalità, disabilitare artefatti standard, saltare review/provenance o cambiare il formato documentale finale.

## Materializzazione automatica degli artefatti

`JURISCRIBE_STANDARD_ARTIFACT_AUTOPILOT_V1` rende la generazione dei file responsabilità del runtime. Un assistente può dimenticare di invocare manualmente `record-artifact`, ma non può ottenere una sessione v0.10.0 completa con un set incompleto: il runtime materializza il set canonico oppure fallisce chiuso.

Per `final_chapter`, il DOCX porta una tracciabilità inferenziale verificabile che lega richiesta, decisioni naturali materiali, unità epistemiche, claim, continuation plan, generation contract e candidato finale.

## Inventario meccanico e release atomica

Prima della consegna `JURISCRIBE_MECHANICAL_DELIVERY_COMPLIANCE_V1` controlla:

- mode contract e standard editoriale;
- mining atomico e reticolo epistemico;
- claim ledger ed evidence register;
- fonti/source intelligence e inference structure;
- generation contract/configuration e anti-plagio quando applicabili;
- continuation plan/coverage;
- review, simulazioni, compressione;
- provenance e final severe review;
- pipeline lock e autopilot;
- validità materiale dei DOCX e prove semantiche dei dossier.

La release è **atomica**. Se un prerequisito bloccante manca, il manifest produce `attachments=[]` e classifica i candidate documenti come `withheld_attachments`. Non esiste una consegna parziale dichiarata valida.

Specifica: `docs/MECHANICAL_DELIVERY_COMPLIANCE_V10.md`.

## Contratto di consegna

Tutti i documenti user-facing devono essere **DOCX reali**. Non basta l'estensione: il file deve esistere, essere confinato nel workspace, essere un pacchetto OOXML/WordprocessingML leggibile, superare i limiti di sicurezza e avere readback `PASS`.

I DOCX autorizzati sono descritti dal manifest con:

- `delivery_class=ATTACH`
- `placement=SESSION_CHAT_TAIL`
- MIME Word OOXML
- `content_disposition=attachment`

`session-dashboard.html` resta `SURFACE`: non entra negli attachment e non contiene link `.docx` o anchor `download`.

I record macchina (`state.json`, `session.integrity.json`, receipt, provenance raw, validation JSON, JSONL ledger, traceback) restano interni.

Le specifiche storiche `docs/FINAL_DELIVERY_V9_2.md` e `docs/FINAL_DELIVERY_V9_4.md` restano documenti degli invarianti introdotti nelle release precedenti.

## Dashboard persistente

La dashboard è aggiornata a ogni mutazione di runtime, sostituita atomicamente e verificata dopo il reload. La V4 conserva la linea editoriale V2/V3 e aggiunge il riepilogo di:

- contratto conversazionale;
- autopilot artefatti standard;
- tracciabilità del prodotto;
- inventario meccanico della consegna.

Il metadata invisibile `juriscribe-state-digest` resta nel `<head>` per il controllo di freshness. Nel body non devono comparire path assoluti, digest tecnici, readback, capability, log o traceback.

## Integrità

Il record canonico è `.juriscribe/<session>/session.integrity.json`. `node.h` è solo input di migrazione per workspace storici.

## Validazione e CI

La CI v0.10.0 aggiunge:

- 100 edge case Safari di delivery DOCX + M+100 no-novelty;
- 100 scenari universali Safari su autopilot/pipeline lock/inventario + M+100 multi-browser/multi-assistant;
- test di release atomica per evidence, reticulum, source coverage, autopilot drift e dashboard mancante.

Restano obbligatorie senza modifica delle baseline: 400k v5, M+1000 architecture saturation, 10k continuation, 10k mutazioni v7, historiography M+100, 30k tri-mode, 10k dashboard evidence, 10k generation governance e tutti i fixed-point storici.

## Versioni

- runtime: `0.10.0`
- access contract: `1.7.0`
- manifest: `juriscribe-manifest/v9`

Documentazione v0.10.0: `docs/UNIVERSAL_ARTIFACT_AUTOPILOT_V10.md`, `docs/MECHANICAL_DELIVERY_COMPLIANCE_V10.md`, `docs/AUDIT_UNIVERSAL_ARTIFACT_AUTOPILOT_V10.md`.
