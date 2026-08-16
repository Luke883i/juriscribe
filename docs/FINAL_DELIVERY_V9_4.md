# Final delivery contract v0.9.4

Questa specifica integra e supersede, per le sessioni v0.9.4+, `FINAL_DELIVERY_V9_2.md`. Tutti gli invarianti di materializzazione, confinamento, readback, freshness e artifact-first di v0.9.2/v0.9.3 restano applicabili.

## 1. Artefatti user-facing

I documenti finali restano DOCX realmente materializzati. I ruoli comuni sono:

- `evidence_dossier.docx`;
- `source_register.docx`;
- `inference_register.docx`;
- `transformation_ledger.docx`;
- `session-dashboard.html`.

I ruoli specifici di modalità restano invariati.

## 2. Contenuto giuridico-editoriale canonico

I quattro dossier comuni devono essere materializzati dalla proiezione `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1` definita in `juriscribe.editorial_artifacts`.

La proiezione non sostituisce provenance, reticolo o claim ledger: li traduce in una superficie professionale leggibile. Non puo introdurre nuove tesi o fonti che non esistano nello stato auditato.

## 3. Dashboard come dossier inferenziale integrato

La dashboard non e una console di stato e non e una pagina di diagnostica. Il suo corpo presenta:

1. mandato e cornice editoriale umana;
2. Evidence dossier integrale;
3. Source register integrale;
4. Inference register integrale;
5. Transformation ledger integrale.

Il corpo non deve esporre hash, digest, path, capability, integrity manifest, readback, raw record count, log o traceback.

Per conservare il gate di freshness gia consolidato, il documento HTML mantiene nel `<head>` il metadata non visibile `juriscribe-state-digest`. Questo dato e parte del protocollo di verifica, non del resoconto mostrato al lettore.

## 4. Semantic parity

La dashboard deve contenere ogni elemento intermedio giuridico-umanistico-editoriale presente nelle quattro viste canoniche. Un renderer che sintetizza o omette campi materializzati non soddisfa il contratto v0.9.4.

## 5. Semantic freshness

I quattro dossier registrati da v0.9.4 vengono associati alla proiezione semantica corrente. Se claim, fonti, inferenze, review, trasformazioni o final review cambiano dopo la registrazione in modo tale da modificare la vista del dossier, il dossier viene considerato stale al completion gate.

Questo controllo e aggiuntivo rispetto a:

- esistenza fisica;
- confinamento in `<workspace>/artifacts`;
- no symlink;
- DOCX/OOXML valido e bounded readback;
- readback PASS;
- dashboard state freshness.

## 6. Record interni

Restano interni: `state.json`, `session.integrity.json`, admission/probe receipts, raw provenance, validation JSON, JSONL ledger, hash manifest, stderr, traceback e analoghi record macchina.

Nessuna informazione tecnica viene spostata nella dashboard per compensare la loro esclusione dalla consegna.

## 7. Chat

La chat resta una superficie breve di controllo: normalmente 1–3 righe. Il maggiore dettaglio introdotto da v0.9.4 appartiene ai DOCX e alla dashboard e non autorizza una maggiore verbosità conversazionale.

## 8. Compatibilità

- access contract: resta 1.7.0;
- tri-mode: invariato;
- standard editoriale: `JURISCRIBE_LEGAL_EDITORIAL_CORE_V2` invariato;
- provenance/final review: invariati;
- M+10.000 e fixed-point: invariati;
- DOCX/materialization security: invariata;
- dashboard freshness tecnica: preservata come metadata invisibile.
