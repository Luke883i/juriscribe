# Juriscribe Dashboard Workbench v0.9.5

## Scopo

`session-dashboard.html` è la superficie di lettura giuridico-scientifico-editoriale della sessione. La v0.9.5 non modifica il contenuto dei quattro dossier canonici introdotti in v0.9.4: modifica **come quel contenuto viene letto, attraversato e stampato**.

Profilo di presentazione: `JURISCRIBE_EDITORIAL_WORKBENCH_V1`.

L'obiettivo non è imitare una dashboard amministrativa o una console tecnica. Il modello è quello di un **dossier di lavoro per giuristi, studiosi e redazioni**: denso, gerarchico, navigabile, stampabile e capace di rendere visibili fondamento probatorio, autorità, inferenze e trasformazioni senza perdere alcuna informazione semantica già materializzata.

## Invarianti scientifici

La dashboard continua a essere una proiezione, non una nuova fonte di verità. Il contenuto sostanziale deriva esclusivamente da `build_dashboard_inference_view`, che a sua volta aggrega:

1. `evidence_dossier`;
2. `source_register`;
3. `inference_register`;
4. `transformation_ledger`.

Il renderer può aggiungere soltanto **struttura di lettura derivata**: titoli, numerazione, conteggi dei record, indice, badge tipografici, ricerca locale, espansione/contrazione e regole di stampa. Non può aggiungere nuove conclusioni giuridiche, correggere il contenuto dei dossier o produrre inferenze autonome nel browser.

La parità semantica resta lossless: ogni stringa contenuta nelle quattro proiezioni deve essere presente nel body HTML.

## Architettura dell'informazione

### Masthead editoriale

La testata espone mandato, stato editoriale (`PRONTO` / `NON PRONTO`), modalità, genere giuridico e destinatari. È una cornice umana, non una superficie di diagnostica.

### Mappa editoriale

La prima sezione offre una lettura quantitativa minima dei quattro registri:

- proposizioni ed evidenze;
- fonti e autorità;
- inferenze esplicite;
- trasformazioni tracciate.

I numeri sono semplici conteggi delle proiezioni canoniche e non costituiscono scoring di qualità.

Quando disponibili, orientamento editoriale e principi applicati sono visualizzati come lenti di lettura. Non vengono generate nuove raccomandazioni nel renderer.

### Indice laterale

L'indice sticky consente accesso diretto a sintesi e quattro dossier. Ogni link punta a un landmark nominato della pagina. Su viewport ridotti l'indice rientra nel flusso e diventa una griglia/colonna responsive.

### Record semantici

Ogni elemento dei dossier è un `<details open>`:

- il summary rende subito leggibile proposizione/fonte/conclusione/problema principale;
- riferimento e badge fungono da orientamento rapido;
- il corpo conserva l'intero record canonico;
- oggetti annidati, evidenze circostanziate e premesse sono resi come blocchi secondari, non come JSON raw.

I badge sono una classificazione tipografica dei valori già presenti (`VERIFIED`, `INFERRED`, `MAJOR`, `ADDRESSED`, ecc.); non introducono stati nuovi.

## Strumenti di lettura

La pagina è autosufficiente e può essere aperta offline.

- **Cerca nel dossier** filtra i record mediante `textContent` già presente nel DOM.
- **Espandi** apre tutti i record.
- **Contrai** chiude tutti i record per scansione rapida.
- **Stampa** usa `window.print()` e un profilo CSS dedicato.
- `Escape` svuota la ricerca.

Nessun controllo effettua richieste di rete o modifica lo stato Juriscribe.

## Accessibilità e struttura HTML

La struttura segue HTML semantico e landmark nominati:

- skip link al contenuto principale;
- `<nav aria-label="Indice del dossier">`;
- `<main id="dashboard-content">`;
- sezioni con `aria-labelledby`;
- un solo `h1` e `h2` gerarchici per overview/dossier;
- focus visibile;
- `aria-live` per il numero di risultati della ricerca;
- il significato non dipende dal colore: badge e stato hanno sempre testo esplicito.

Queste scelte sono coerenti con la funzione editoriale: permettono di scorrere per titoli, saltare alle regioni e distinguere visivamente senza occultare il testo.

## Tipografia e grammatica visiva

La pagina usa soltanto font di sistema. Nessun font remoto, CSS esterno o libreria JavaScript è caricato.

La grammatica è volutamente ibrida:

- serif per mandato, titoli e testo giuridico;
- sans-serif di sistema per metadati editoriali, navigazione, label e badge;
- palette sobria blu/inchiostro con accenti vino/oro;
- superfici chiare e bordi discreti al posto di grafici decorativi;
- nested evidence evidenziata con una linea laterale, per conservare gerarchia senza trasformare il dossier in una tabella tecnica.

## Stampa

Il profilo `@media print`:

- elimina sidebar, controlli e ornamenti;
- forza fondo bianco e contrasto tipografico;
- conserva tutti i record, anche se l'utente li aveva contratti a schermo;
- evita per quanto possibile la rottura interna di record e sezioni;
- mantiene la dashboard utilizzabile come allegato editoriale stampato/PDF dal browser.

Il profilo di stampa non sostituisce i DOCX finali e non modifica il contratto di delivery.

## Zero-state

Una sessione appena inizializzata può non avere ancora modalità o materiale semantico. La dashboard non deve apparire rotta o vuota: mantiene masthead, cornice, indice, mappa con conteggi a zero e quattro empty-state espliciti. Non inventa evidenze o fonti per “riempire” la pagina.

Questo risolve il caso mostrato dal preview v0.9.4: una dashboard corretta ma visivamente assimilabile a HTML grezzo.

## Divieto di telemetria nel body

Restano esclusi dal body:

- digest/hash;
- `session.integrity.json`;
- path di filesystem;
- capability host;
- readback/media type;
- receipt, log, stderr e traceback;
- dettagli implementativi del runtime.

`juriscribe-state-digest` resta esclusivamente nel `<head>` come metadata invisibile, perché il freshness gate consolidato lo richiede.

## Autosufficienza

Il deliverable non contiene `<link>` a fogli di stile esterni né `<script src=...>`. CSS e JavaScript di lettura sono inline. Collegamenti a fonti giuridiche possono naturalmente comparire come normali link perché fanno parte del contenuto del Source register; non sono dipendenze del renderer.

## Definition of Done v0.9.5

La dashboard workbench è considerata completata soltanto se:

1. ogni leaf semantica dei quattro dossier resta presente nel body;
2. il body non reintroduce telemetria tecnica;
3. la dashboard vuota è strutturata e leggibile senza inventare contenuto;
4. indice, anchor e landmark hanno target coerenti;
5. la ricerca è locale e non modifica il contenuto sorgente;
6. tutti i record sono espandibili e aperti di default;
7. il profilo di stampa rende il contenuto completo;
8. user material è HTML-escaped;
9. nessuna dipendenza visuale o JavaScript è remota;
10. i test storici v0.3-v0.9.4, contract checker, simulazioni e fixed-point restano invariati e verdi.

## Non-regressione

La v0.9.5 non cambia:

- `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`;
- schema degli artefatti semantici;
- semantic seal dei dossier;
- dashboard state digest e freshness gate;
- DOCX write/readback e bounded OOXML validation;
- mining, reticolo, claim/source/inference discipline;
- tri-mode;
- provenance, final severe review, saturation o simulation receipts;
- access contract 1.7.0.

La release è quindi una evoluzione della **superficie editoriale**, non una riscrittura del runtime scientifico.
