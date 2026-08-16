# Artefatti giuridico-umanistico-editoriali — v0.9.4

Questa specifica definisce il contenuto semantico comune di `evidence_dossier`, `source_register`, `inference_register`, `transformation_ledger` e della dashboard che li ricompone.

## Principio

Gli artefatti non sono log del runtime. Sono strumenti di lettura professionale destinati a giuristi, autori, curatori scientifici e redazioni. Devono mostrare **che cosa e stato sostenuto, su quale base, attraverso quale inferenza, con quali limiti e come il testo e stato trasformato**.

Il runtime non ricostruisce ne pubblica chain-of-thought latente. La proiezione usa soltanto oggetti gia materializzati: unità epistemiche, relazioni, claim, source evidence, provenance, finding, rigenerazioni, compressione, editorial actions e final review.

La fonte canonica e `juriscribe.editorial_artifacts.build_editorial_artifact_views`.

## Evidence dossier

Funzione: rendere visibile l'architettura probatoria del testo.

Per ogni proposizione materiale, quando disponibile, espone:

- riferimento auditabile;
- proposizione;
- funzione giuridica (regola, definizione, qualificazione, inferenza, conclusione, proposta interpretativa...);
- ambito e stato epistemico;
- fonti ed evidenze circostanziate, con autorita, tempo, giurisdizione, pinpoint e proposizione attestata;
- premesse;
- ponte inferenziale e condizione di confutazione quando pertinenti;
- relazioni di supporto, qualificazione, dipendenza o contrasto;
- ragione probatoria/editoriale;
- disposizione finale;
- collocazione nel testo.

Il dossier deve consentire la domanda editoriale essenziale: **"perche questa proposizione puo stare qui, in questa forma?"**

## Source register

Funzione: rappresentare la geografia delle autorita, non un elenco bibliografico indifferenziato.

Per ogni fonte espone, quando disponibile:

- identita e riferimento;
- carattere dell'autorita: normativa, giurisprudenziale, istituzionale, dottrinale, corpus autoriale o altro;
- autore/organo;
- giurisdizione e collocazione temporale;
- ruolo nel lavoro;
- claim effettivamente sostenuti;
- pinpoint e proposizioni effettivamente lette;
- eventuale funzione di controautorita o riserva;
- stato della lettura/verifica;
- voce bibliografica e collegamento.

La gerarchia non e un automatismo decisorio: il carattere dell'autorita informa il giudizio, non lo sostituisce.

## Inference register

Funzione: distinguere il diritto attestato dal diritto inferito o proposto.

Per ogni inferenza materiale espone:

- conclusione inferenziale;
- premesse, con il loro contenuto e stato;
- ponte che giustifica il passaggio;
- condizione che falsificherebbe o indebolirebbe il passaggio;
- autorita/evidenze utilizzate;
- qualificazioni, obiezioni e contrasti del reticolo;
- ragione dell'inferenza;
- disposizione finale e collocazione.

Una inferenza priva di ponte o falsificatore non viene resa piu autorevole dalla presentazione: resta una lacuna da trattare secondo i gate gia esistenti.

## Transformation ledger

Funzione: raccontare la storia editoriale del testo come sequenza causale di decisioni, non come changelog tecnico.

Espone, quando materializzati:

- finding e criterio scientifico-editoriale che li ha generati;
- problema, gravita, intervento proposto e collocazione;
- rigenerazioni e finding affrontati;
- contenuti preservati, persi o introdotti;
- eventuali degradazioni;
- compressione finale e preservazione lossless;
- provenance delle trasformazioni materiali;
- azioni editoriali motivate;
- final severe review e consequence probes.

Il ledger risponde alla domanda: **"come e perche il testo e diventato quello consegnato, e che cosa e stato preservato nel percorso?"**

## Dashboard

`session-dashboard.html` e la vista integrata dei quattro artefatti. Il suo `<body>` deve riprodurre integralmente le informazioni giuridico-umanistico-editoriali delle quattro proiezioni e puo aggiungere soltanto una cornice umana: mandato, modalita, genere, destinatari e principi editoriali applicati.

Non sono contenuto della dashboard:

- digest e hash;
- `session.integrity.json`;
- path di filesystem;
- capability host;
- readback e media type;
- raw receipt, log, stderr o traceback;
- conteggi di record interni;
- altri dettagli di implementazione.

Il `<head>` conserva il solo metadata invisibile `juriscribe-state-digest` richiesto dal controllo di freshness. Esso non e una informazione presentata al lettore.

## Parita semantica

La dashboard non deve riassumere perdendo dettagli. La regola di parita e:

```text
Dashboard = cornice umana
          + Evidence dossier
          + Source register
          + Inference register
          + Transformation ledger
```

La stessa funzione canonica alimenta sia i DOCX sia la dashboard. Una correzione del significato deve quindi essere effettuata nel projector, non duplicata nei renderer.

## Freshness dei dossier

Dal runtime 0.9.4, quando uno dei quattro dossier viene registrato attraverso il facade pubblico, il record riceve:

- `semantic_profile = JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`;
- `semantic_projection_digest` della vista canonica al momento della materializzazione.

Se successivamente cambia una informazione che modifica quella vista, il completion gate considera stale il dossier sigillato e richiede la sua rimaterializzazione. I dossier storici privi del seal restano compatibili come input di migrazione.

## Rendering DOCX

Il projector definisce **contenuto e ordine semantico**, non un layout proprietario. L'host continua a materializzare DOCX reali e a sottoporli ai gate OOXML/readback v0.9.2/v0.9.3. Titoli, tabelle e stile tipografico possono seguire house style e genere, ma non devono omettere i campi materializzati dalla proiezione.
