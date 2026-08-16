# Final delivery contract v0.9.1

Questa specifica ripristina gli invarianti di consegna presenti nella storia di Juriscribe e persi nella generalizzazione tri-mode.

## 1. Artifact-first, chat-last

La conversazione non è il luogo in cui riversare report, ledger, receipt o log. La complessità resta nel runtime e nella dashboard.

Quando una lavorazione è `COMPLETE`, l'assistente deve limitare il messaggio finale a **1–3 righe brevi**: esito e rinvio agli allegati. Non deve duplicare nel messaggio il contenuto dei documenti, dei finding o del dossier.

Esempio conforme:

```text
Completato. Ho allegato i documenti finali e la dashboard di controllo.
```

## 2. Formato degli allegati

Tutti i documenti finali destinati all'utente devono essere **DOCX**:

- `final_chapter`;
- `final_legal_text`;
- `review_report`;
- `revised_legal_text`, quando richiesto;
- `evidence_dossier`;
- `source_register`;
- `inference_register`;
- `transformation_ledger`;
- `review_findings_register`, in modalità REVIEW.

L'unica eccezione è `session_dashboard`, che deve essere **HTML** (`session-dashboard.html`) perché è il fascicolo navigabile di stato e controllo.

Un file JSON/TXT/MD non può soddisfare uno di questi ruoli finali anche se porta `readback=PASS`.

## 3. Dashboard sempre allegata

`session_dashboard` è un ruolo finale comune alle tre modalità. Deve essere aggiornato alla sessione corrente, sottoposto a readback e incluso nel final delivery manifest. Non è un log tecnico: è il verbale leggibile per giuristi e redazioni.

## 4. Record interni mai allegati

Sono **interni** e non fanno parte del pacchetto consegnato, salvo richiesta espressa dell'utente per audit tecnico:

- `state.json`;
- `session.integrity.json`;
- provenance bundle raw;
- validation/simulation receipts raw;
- JSONL ledger;
- probe/admission receipts;
- hash manifest e altri record macchina.

Il runtime può conservarli e usarli nei gate, ma il delivery manifest deve escluderli.

## 5. Capability fail-closed

Poiché i documenti finali devono essere DOCX, `COMPLETE` richiede:

- `DOCX_WRITE = AVAILABLE`;
- `DOCX_READBACK = AVAILABLE`;
- readback `PASS` per ciascun documento finale;
- estensione `.docx` per ogni documento finale;
- estensione `.html` per la dashboard.

Se l'host non può materializzare e rileggere DOCX, Juriscribe non deve degradare la consegna a JSON/Markdown fingendo equivalenza: la sessione resta non pronta.

## 6. Separazione fra prova e consegna

Provenance, receipt, saturation e registri macchina **provano** il processo. I DOCX e la dashboard **comunicano** il risultato. Il final delivery boundary impedisce che i primi vengano confusi con i secondi.
