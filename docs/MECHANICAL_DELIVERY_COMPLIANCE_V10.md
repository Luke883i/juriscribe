# Juriscribe v0.10.0 — Inventario meccanico e release atomica degli artefatti

## Scopo

La consegna all'utente non è un effetto collaterale del browser o dell'assistente AI. È una fase governata dal runtime Juriscribe. Prima che un DOCX possa entrare nella coda della sessione-chat, il runtime costruisce un inventario meccanico che verifica due insiemi contemporaneamente:

1. gli artefatti materiali finali previsti dalla modalità;
2. le logiche e gli artefatti epistemici intermedi da cui quei documenti devono derivare.

La regola è **all-or-nothing**: se un solo prerequisito bloccante applicabile non è conforme, tutti i DOCX finali restano `withheld` e il manifest chat non rilascia attachment parziali.

## Inventario degli artefatti materiali

La funzione canonica `required_artifact_roles(mode, setup)` resta la sorgente del set standard.

### CONTINUATION

- `final_chapter.docx` — nuovo capitolo;
- `evidence_dossier.docx`;
- `source_register.docx`;
- `inference_register.docx`;
- `transformation_ledger.docx`;
- `session-dashboard.html` — sola superficie sintetica, mai attachment.

### GREENFIELD

- `final_legal_text.docx`;
- `evidence_dossier.docx`;
- `source_register.docx`;
- `inference_register.docx`;
- `transformation_ledger.docx`;
- `session-dashboard.html`.

### REVIEW

- `review_report.docx`;
- `review_findings_register.docx`;
- `evidence_dossier.docx`;
- `source_register.docx`;
- `inference_register.docx`;
- `transformation_ledger.docx`;
- `revised_legal_text.docx` quando il setup richiede `REPORT_AND_REVISED_TEXT`;
- `session-dashboard.html`.

Tutti i documenti sono runtime-owned per le nuove sessioni v0.10.0. Il browser non decide se crearli; l'assistente non deve ricordarsi di registrarli manualmente.

## Inventario delle logiche e degli artefatti epistemici

Il profilo `JURISCRIBE_MECHANICAL_DELIVERY_COMPLIANCE_V1` inventaria almeno i seguenti nodi.

| Nodo | Funzione contrattuale | Blocking |
|---|---|---:|
| `mode_contract` | congela modalità, output primario e requisiti | sì |
| `editorial_standard` | standard giuridico-editoriale applicabile | sì |
| `atomic_mining` | unità epistemiche atomiche | sì |
| `epistemic_reticulum` | reticolo epistemico e dipendenze semantiche | sì |
| `claim_ledger` | proposizioni materiali | sì |
| `artifact_evidence` | evidence register: claim, fonte, locator, artefatto | sì quando esistono claim |
| `source_register_logic` | fonti e source intelligence | sì |
| `bibliography` | bibliografia, se disponibile/necessaria | no, salvo gate storici più severi |
| `inference_structure` | premesse, ponti inferenziali, conclusioni, falsificatori | sì quando esistono claim |
| `generation_contract` | reticolo + setup + candidato | sì per testi narrativi |
| `generation_configuration` | abstract, key concepts, length | sì quando attiva la governance v0.9.7+ |
| `continuation_plan` | frontiera argomentativa | sì in CONTINUATION |
| `continuation_coverage` | copertura del piano | sì in CONTINUATION |
| `scientific_editorial_review` | finding, review, saturazione | sì |
| `quality_audit` | qualità del candidato corrente | sì |
| `anti_plagiarism` | prova scoped contro overlap proibito | sì quando applicabile |
| `simulations` | edge case e stress test | sì in generazione |
| `compression` | compressione finale lossless | sì in generazione |
| `provenance` | derivazione e trasformazioni | sì |
| `final_severe_review` | ultimo gate circostanziato | sì |
| `natural_language_pipeline` | anti-deragliamento conversazionale | sì per sessioni v0.10.0 |
| `standard_artifact_autopilot` | materializzazione esatta del set standard | sì per sessioni v0.10.0 |

L'inventario non espone chain-of-thought. Registra soltanto strutture epistemiche esplicite e verificabili già previste dal contratto Juriscribe.

## Dipendenze per artefatto

Ogni artefatto materiale ha un vettore di dipendenze. Per esempio, `final_chapter` richiede almeno:

```text
mode contract
→ editorial standard
→ atomic mining
→ epistemic reticulum
→ claim ledger
→ evidence register
→ source intelligence
→ inference structure
→ generation contract/configuration
→ continuation plan/coverage
→ scientific-editorial review
→ quality audit / anti-plagiarism
→ simulations
→ compression
→ provenance
→ final severe review
→ natural-language pipeline lock
→ standard artifact autopilot
→ final chapter inference trace
→ DOCX materialized/readback PASS
```

I quattro dossier canonici hanno dipendenze specializzate:

- **Evidence dossier**: claim ledger + artifact evidence + reticolo/inferenze + fonti;
- **Source register**: fonti + source intelligence + uso nei claim;
- **Inference register**: claim/inference structure + reticolo + evidenze;
- **Transformation ledger**: review, rigenerazioni, decisioni, compression e provenance.

## Controllo del file materializzato

Un documento non è eleggibile perché il nome termina in `.docx`. Il runtime riusa i controlli esistenti:

- workspace confinement;
- divieto di symlink deliverable;
- pacchetto OOXML valido;
- limiti di dimensione e decompressione;
- `word/document.xml` leggibile;
- readback `PASS`;
- SHA-256 del file;
- materializzazione semantica dei dossier;
- conformance/anti-plagiarism/binding del testo narrativo quando applicabili.

## Release atomica in coda chat

`build_chat_delivery_manifest()` costruisce prima i candidate attachment, poi consulta l'inventario di conformità.

Se `release_authorized=true`:

- tutti e soli i DOCX standard sono rilasciati;
- `placement=SESSION_CHAT_TAIL`;
- `content_disposition=attachment`;
- la dashboard resta esclusa dagli attachment.

Se `release_authorized=false`:

- `attachments=[]`;
- tutti i ruoli candidati sono elencati in `withheld_attachments`;
- gli errori indicano quali nodi materiali/epistemici impediscono la consegna;
- nessun rilascio parziale viene presentato come risultato valido.

## Dashboard

La dashboard HTML resta il workbench sintetico della sessione. Deve riepilogare:

- artefatti materiali e relativo stato;
- reticolo epistemico, evidence, source e inference registers;
- contratto conversazionale;
- autopilot;
- inventario meccanico di conformità della consegna;
- tracciabilità inferenziale del nuovo capitolo.

Non contiene link `.docx` né anchor `download`. I DOCX sono consegnati nella sessione-chat, non dall'HTML.

## Browser e assistenti

Il contratto è browser-agnostic e assistant-agnostic rispetto alla **logica di generazione e release**. Safari, Chrome, Firefox, Edge, webview o un assistente diverso non modificano il set standard né i gate.

Resta esplicito il limite di integrazione: Juriscribe può produrre un manifest conforme e fail-closed; non può obbligare un host esterno non cooperante a renderizzare graficamente gli attachment. Per questo `global_external_host_behavior_claim=false`.

## Criterio di conformità

La consegna è compliant solo quando:

1. l'inventario materiale coincide con `required_artifact_roles()`;
2. tutti i nodi epistemici bloccanti applicabili sono PASS;
3. ogni artefatto materiale è eleggibile;
4. l'autopilot ha creato esattamente il set standard;
5. `final_chapter` ha inference trace valida quando applicabile;
6. la dashboard è presente come superficie sintetica;
7. l'inventario autorizza la release atomica;
8. il manifest chat contiene esclusivamente i DOCX autorizzati.
