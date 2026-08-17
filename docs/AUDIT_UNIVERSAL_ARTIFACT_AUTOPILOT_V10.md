# Audit severo v0.10.0 — universal artifact autopilot, anti-deragliamento e delivery compliance

## Prompt atomizzato

I requisiti sono trasformati in condizioni falsificabili:

1. nessun browser deve determinare se gli artefatti standard esistono;
2. nessun assistente deve poter omettere un artefatto standard senza far fallire il completion gate;
3. gli artefatti documentali standard devono essere DOCX reali;
4. la dashboard HTML deve restare sintetica e non linkare i DOCX;
5. i DOCX devono essere destinati alla coda della sessione-chat tramite manifest `SESSION_CHAT_TAIL`;
6. il linguaggio naturale non deve poter cambiare implicitamente modalità, artefatto primario, set standard, formato finale o pipeline;
7. una richiesta di nuovo lavoro/cambio modalità deve essere isolata come nuova sessione o nuova selezione esplicita;
8. un'istruzione ambigua deve bloccare la mutazione materiale fino a risoluzione;
9. il nuovo capitolo in CONTINUATION deve avere una trace verificabile dalla richiesta alle premesse epistemiche fino al candidate finale e al DOCX;
10. la trace pubblica deve essere sintetizzata nella dashboard senza esporre chain-of-thought, fingerprint o testo candidato interno;
11. la consegna deve essere preceduta da inventario di artefatti materiali e logiche intermedie: reticolo epistemico, claim/evidence, source intelligence, inference structure, review, provenance e altri gate applicabili;
12. se un nodo bloccante manca, tutti gli attachment devono essere withheld: nessuna release parziale;
13. 100 edge case Safari devono attraversare le tre modalità e host assistant diversi;
14. M+100 deve produrre zero nuove categorie;
15. tutte le regressioni storiche devono restare verdi.

## Finding strutturali

### F1 — Gate reattivo, non costruttivo

Il runtime storico conosceva `required_artifact_roles()` e sapeva rifiutare ruoli mancanti, ma la materializzazione era command-driven. Un host poteva non invocare `record-artifact`, lasciando dashboard o stato senza set documentale completo.

### F2 — Linguaggio naturale senza pipeline lock

`interaction_card` consente correttamente input libero, ma mancava un contratto che distinguesse vincolo interno, cambio modalità, bypass della review o soppressione dei dossier. Un assistente esterno poteva interpretare una locuzione informale come autorizzazione a cambiare workflow.

### F3 — Esistenza del file non equivale a consegna conforme

Anche dopo l'autopilot, limitarsi a verificare `.docx`/MIME/readback non dimostra che il documento sia il prodotto del reticolo epistemico richiesto. La release deve dipendere dalla presenza e dalla coerenza delle logiche intermedie.

## Correzione causale

### A1 — Pipeline lock

`JURISCRIBE_NATURAL_LANGUAGE_PIPELINE_LOCK_V1` nasce su `select_mode`. Congela modalità, artefatto primario e set standard. `apply_setup` può aggiornare soltanto ruoli legittimamente dipendenti dal setup, senza cambiare modalità o primary role.

### A2 — Interpretation ledger

Le istruzioni naturali materialmente rilevanti sono tipizzate. `MODE_CHANGE_REQUEST`, `NEW_WORK_REQUEST`, bypass della pipeline, soppressione degli artefatti o cambio formato vengono bloccati. L'ambiguità resta aperta fino a risoluzione.

### A3 — Runtime-owned artifact autopilot

Quando la final severe review è PASS, il runtime genera i ruoli standard DOCX dalla sorgente canonica appropriata e li registra attraverso i gate preesistenti. L'assistente non deve ricordare il set degli output.

### A4 — Candidate text custody

Il testo candidato passato a `seal_draft` viene custodito nel solo stato interno `strategy.sealed_candidate_texts`, escluso dall'atlante pubblico. Ciò consente di rimaterializzare deterministicamente `final_chapter`, `final_legal_text` e `revised_legal_text`.

### A5 — Final chapter inference trace

`final_chapter` riceve una trace che lega request id, interpretazioni materiali, unità epistemiche, claim, continuation plan, generation contract e candidate digest. Il gate rifiuta trace stale o incoerenti.

### A6 — Inventario meccanico di conformità

`JURISCRIBE_MECHANICAL_DELIVERY_COMPLIANCE_V1` costruisce due inventari:

- **materiale**: tutti i ruoli previsti da `required_artifact_roles()`;
- **epistemico**: mode contract, standard editoriale, mining, reticolo, claim/evidence, fonti, inferenze, generation, continuation, review, quality/anti-plagio, simulazioni/compressione, provenance, final review, pipeline lock e autopilot.

Ogni artefatto materiale dichiara le proprie dipendenze. Un prerequisito bloccante FAIL rende `eligible_for_delivery=false`.

### A7 — Release atomica

`build_chat_delivery_manifest()` non espone parzialmente i candidate attachment. Se l'inventario non autorizza la release:

- `attachments=[]`;
- i ruoli sono in `withheld_attachments`;
- gli errori indicano il nodo contrattuale mancante.

### A8 — Dashboard summary-only

Il workbench mostra stato, funzione, materializzazione automatica, inventario e trace pubblica, ma non linka DOCX e non espone candidate store, digest tecnici o fingerprint.

## DoD globale

La release è accettabile solo se:

- G1: public orchestrator usa pipeline lock e runtime autopilot;
- G2: completion include lock gate, autopilot gate, final-chapter trace gate, mechanical delivery compliance e chat-tail DOCX gate;
- G3: 100/100 Safari edge passano;
- G4: M+100 produce zero nuove categorie;
- G5: ogni scenario produce esattamente il set standard DOCX della modalità senza chiamate manuali `record-artifact`;
- G6: dashboard materializzata contiene riepilogo sintetico ma zero link `.docx`/download anchor;
- G7: richieste naturali di cambio modalità, skip pipeline, soppressione artifact o cambio formato non mutano la pipeline attiva;
- G8: `final_chapter` CONTINUATION espone inference trace PASS;
- G9: inventario materiale ed epistemico è PASS prima della release;
- G10: qualsiasi failure di evidence/source/inference/reticulum/autopilot/dashboard produce release atomica withheld;
- G11: regressioni storiche e fixed-point restano verdi sullo stesso head;
- G12: nessuna baseline storica viene aggiornata per far passare la CI.

## DoD locali

### Contratto conversazionale
- lock digest stabile;
- mode e primary-role drift bloccati;
- set artefatti setup-aware ma mode-stable;
- record ambigui/bloccati richiedono risoluzione.

### Autopilot
- stdlib-only OOXML;
- write atomico;
- workspace confinement ereditato dai gate;
- final review obbligatoria;
- DOCX_WRITE e DOCX_READBACK obbligatori;
- tutti i ruoli standard eccetto la dashboard materializzati automaticamente.

### Delivery compliance
- inventario esplicito dei nodi epistemici;
- dependency vector per artefatto;
- dossier semantic materialization PASS;
- narrative governance PASS quando applicabile;
- exact autopilot role parity;
- atomic release e withheld set.

### Delivery UI
- only DOCX attachments;
- placement `SESSION_CHAT_TAIL`;
- dashboard non attachment;
- dashboard no DOCX links.

### Tracciabilità
- request id;
- interpretazioni materiali;
- epistemic unit ids;
- claim ids;
- generation contract;
- continuation status;
- candidate binding;
- visualizzazione pubblica scrubbed nell'atlante.

## Saturazione

Le 100 simulazioni primarie sono Safari-targeted. La famiglia comprende richieste naturali favorevoli e avverse. Segue M+100 su browser/assistant eterogenei; il criterio di arresto è `no_novelty_after_M=true`.

I fixed-point storici restano immutati: la nuova release è additiva e non usa aggiornamenti di baseline per nascondere regressioni.

## Limite epistemico esplicito

Juriscribe rende contrattuale il comportamento del proprio runtime e rifiuta `COMPLETE` quando il boundary non è rispettato. Non può costringere un'applicazione terza che ignori deliberatamente il runtime a mostrare un attachment nella propria UI. Per questo distingue `runtime-owned materialization` dalla capability di presentazione dell'host e mantiene `global_external_host_behavior_claim=false`.
