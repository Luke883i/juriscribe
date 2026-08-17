# Universal Artifact Autopilot v0.10.0

## Obiettivo

Juriscribe non affida più al browser o all'assistente AI la responsabilità di ricordare quali artefatti finali creare. Dopo la selezione della modalità, il runtime congela modalità, artefatto primario e set standard; alla fase di consegna materializza i documenti canonici, costruisce un inventario materiale+epistemico e autorizza soltanto una release atomica compliant.

## Invariante principale

Per una nuova sessione v0.10.0 valida:

- `CONTINUATION` produce automaticamente `final_chapter`, `evidence_dossier`, `source_register`, `inference_register`, `transformation_ledger` e dashboard persistente;
- `GREENFIELD` produce automaticamente `final_legal_text` e i quattro dossier canonici, oltre alla dashboard;
- `REVIEW` produce automaticamente `review_report`, `review_findings_register`, i quattro dossier canonici e, se configurato, `revised_legal_text`, oltre alla dashboard;
- tutti i documenti finali sono DOCX OOXML materializzati dal runtime;
- la dashboard HTML è una superficie sintetica e persistente, non un canale di download documentale;
- il manifest di delivery espone i DOCX con placement `SESSION_CHAT_TAIL` soltanto se l'intero inventario contrattuale è PASS;
- l'assistente e il browser non decidono quali artefatti esistono e non possono ridurre il set standard tramite linguaggio naturale.

## Linguaggio naturale e anti-deragliamento

Il profilo `JURISCRIBE_NATURAL_LANGUAGE_PIPELINE_LOCK_V1` nasce al momento della selezione della modalità. Congela:

1. modalità;
2. artefatto primario;
3. set degli artefatti standard;
4. digest della mode selection.

Le successive locuzioni dell'utente possono essere interpretate come vincoli, decisioni, query di stato, nuove richieste o richieste ambigue, ma non possono implicitamente:

- cambiare modalità;
- sostituire l'artefatto primario;
- sopprimere gli artefatti standard;
- sostituire DOCX con HTML/PDF/testo chat;
- saltare mining, reticolo, review, provenance, final review o gate.

Una richiesta di cambio lavoro o modalità viene classificata come `NEW_SESSION_REQUIRED`. Un'istruzione ambigua resta bloccante finché non viene risolta. L'input libero resta consentito: ciò che viene vietato è il suo uso come bypass non tracciato del contratto.

## Tracciabilità del nuovo capitolo

Per `CONTINUATION`, `final_chapter` porta un receipt `juriscribe-final-artifact-inference-trace/v1` che collega:

```text
richiesta iniziale
→ interpretazioni materiali del linguaggio naturale
→ unità epistemiche materiali
→ claim materiali
→ continuation plan
→ generation contract
→ candidate digest finale
→ final_chapter.docx
```

La dashboard mostra la versione pubblica e sintetica di questa catena; fingerprint, digest tecnici e testo candidato sigillato restano esclusi dalla superficie umana.

## Materializzazione automatica

`juriscribe.artifact_autopilot.materialize_standard_artifacts` usa un writer OOXML stdlib-only, percorsi confinati nel workspace e registrazione attraverso i gate già esistenti. I quattro dossier sono generati dalla loro proiezione semantica canonica; i testi narrativi provengono dal candidate finale sigillato; report e finding register provengono dallo stato di review.

La materializzazione avviene soltanto quando `final_review.status == PASS` e `DOCX_WRITE`/`DOCX_READBACK` sono `AVAILABLE`. Se i prerequisiti non esistono, Juriscribe resta non pronto: non degrada in HTML, Markdown o testo incollato in chat.

## Inventario meccanico della consegna

`JURISCRIBE_MECHANICAL_DELIVERY_COMPLIANCE_V1` collega ogni artefatto finale ai prerequisiti che ne giustificano la consegna: mode contract, standard editoriale, mining atomico, reticolo epistemico, claim/evidence register, source intelligence, inference structure, generation contract, continuation, review, quality/anti-plagio, simulazioni, compression, provenance, final review, pipeline lock e autopilot.

La release è atomica. Se un nodo bloccante manca, `attachments=[]` e i candidate DOCX vengono riportati come `withheld_attachments`. Non esiste consegna parziale dichiarata valida.

La specifica dettagliata è in `docs/MECHANICAL_DELIVERY_COMPLIANCE_V10.md`.

## Dashboard e coda chat

La dashboard non contiene link `.docx` né anchor `download`. Riepiloga contenuti, stato, materializzazione runtime-owned, contratto conversazionale, inventario di delivery e tracciabilità inferenziale. I documenti finali sono descritti dal delivery manifest come attachment DOCX con placement `SESSION_CHAT_TAIL`.

La capacità dell'host di trasformare il manifest in allegati UI è una dipendenza di integrazione esplicita. Juriscribe garantisce il proprio boundary e non formula una falsa pretesa di controllo su un host esterno che ignori il contratto.

## Saturazione

La release esegue:

- 100 edge case primari tutti Safari-targeted;
- CONTINUATION, GREENFIELD e REVIEW;
- host assistant eterogenei;
- 10 famiglie di locuzioni naturali, incluse richieste di cambiare lavoro, saltare pipeline, sopprimere dossier, cambiare formato e istruzioni ambigue;
- verifica che il set DOCX standard sia sempre runtime-owned;
- verifica del reticolo materiale+epistemico prima della release;
- verifica che la dashboard resti summary-only e senza link documentali;
- M+100 scenari ulteriori su Safari, Chromium, Firefox, Edge, mobile/webview e host assistant diversi;
- criterio di arresto: zero nuove categorie dopo M.

Le regressioni storiche 400k, M+1000, 10k, 30k e fixed-point restano obbligatorie.
