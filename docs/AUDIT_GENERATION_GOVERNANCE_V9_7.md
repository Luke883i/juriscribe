# Audit severo v0.9.7 — configurazione, originalità, saturazione e completezza dashboard

## Mandato atomizzato

Questa release deriva dai prompt dell'utente e li trasforma in obblighi falsificabili. Nessun requisito è trattato come semplice preferenza di stile.

1. Prima della generazione l'AI deve proporre **abstract, concetti chiave e lunghezza**, oltre ai parametri editoriali esistenti.
2. La configurazione accettata deve vincolare meccanicamente ciò che può essere sigillato e consegnato.
3. Juriscribe non deve plagiare; deve rilevare overlap verbatim/near-verbatim non attribuiti e poter **dimostrare** l'esito entro un perimetro dichiarato.
4. Il controllo anti-plagio deve essere ripetuto sul **materializzato**, non soltanto sul draft in memoria.
5. Prima della consegna deve esistere una logica esplicita di **saturazione e ri-controllo ciclico** fino a fixed point, con nuovo ciclo se emerge novità materiale.
6. La dashboard deve essere espressiva, gradevole, colorata, scientificamente/editorialmente densa e completa rispetto a ogni artefatto materiale ed epistemico previsto o prodotto.
7. Ogni artefatto deve avere una **sintesi compressa** e una **descrizione completa/drill-down**, oltre al richiamo al file quando esiste.
8. Le informazioni degli artefatti devono essere realmente **proiettate e materializzate nell'HTML**, non solo dichiarate nel modello.
9. Devono essere eseguiti test, simulazioni edge multi-seed e regressioni storiche.
10. Prima della release va riesaminato lo storico per opportunità di hardening, semplificazione, pulizia e chiarimento senza indebolire i gate esistenti.

## Finding dell'audit pre-implementazione

### A1 — configurazione non sufficientemente vincolante

Il setup storico possedeva la lunghezza per i writing mode, ma abstract e concetti chiave non erano contratti meccanici. Il quality audit non poteva quindi dimostrare che il prodotto corrispondesse alla configurazione anticipata all'utente.

**Correzione:** `JURISCRIBE_GENERATION_CONFIGURATION_V1`, con conformance gate su lunghezza, concetti chiave e copertura dell'abstract.

### A2 — anti-duplicazione non equivaleva ad anti-plagio

Il controllo storico di duplicazione fra capitoli non era una prova di originalità rispetto alle fonti o al corpus testuale disponibile.

**Correzione:** fingerprint deterministici, exact n-gram, near-verbatim shingle similarity, autorizzazione/attribuzione esplicita, receipt scoped e fail-closed per corpus incompleto.

### A3 — rischio di falsa dimostrazione

Una dichiarazione del tipo “nessun plagio” sarebbe epistemicamente falsa se estesa a testi non accessibili al runtime.

**Correzione:** `global_uniqueness_claim=false`; la prova vale sul corpus runtime-visible registrato. Perimetro incompleto = FAIL.

### A4 — claim paraphrase scambiabile per testo della fonte

Le proposizioni circostanziate sono semantica del claim ledger, non necessariamente verbatim source text. Usarle come corpus anti-plagio produrrebbe falsi positivi.

**Correzione:** solo `verbatim`, `quote`, `source_text`, corpus ingerito o reference fingerprint esplicitamente registrato possono alimentare il confronto testuale.

### A5 — draft pulito / artefatto diverso

Un controllo solo sul candidato in memoria non dimostra che il DOCX consegnato contenga lo stesso testo.

**Correzione:** bounded readback del DOCX, estrazione WordprocessingML, nuova verifica configurazione + anti-plagio sul file e binding del fingerprint al candidato sigillato quando applicabile.

### A6 — singolo PASS non è saturazione

Un gate finale eseguito una sola volta non dimostra stabilità rispetto all'ordine dei controlli o a novità tardive.

**Correzione:** almeno tre cicli con ordine variato, fixed point, all-gates-green e assenza di nuovi finding nei re-check successivi.

### A7 — dashboard paritaria ai dossier ma non necessariamente a ogni artefatto

Le release precedenti garantivano parità dei quattro dossier e tracciabilità `artifact_evidence`, ma non una descrizione completa/compatta di **ogni** artefatto previsto/prodotto.

**Correzione:** `JURISCRIBE_ARTIFACT_ATLAS_V1`, separando artefatti materiali e artefatti epistemici e rendendo il loro contenuto pubblico richiamabile nella dashboard.

### A8 — complessità di layering

Lo storico v0.9.x usa boundary additivi per preservare compatibilità. Questo è utile ma può produrre responsabilità sovrapposte.

**Hardening:**
- projector core separato dalla proiezione pubblica scrubbed;
- final delivery boundary unico per la saturazione v0.9.7;
- anti-plagio con API stabile ma implementazione ripulita;
- compatibilità legacy esplicita: i nuovi gate non invalidano retroattivamente sessioni prive del nuovo profilo;
- nessuna modifica ai fixed-point storici o ai receipt baseline.

## DoD globale

La release è completa soltanto se sono vere contemporaneamente tutte le condizioni seguenti.

### G1 — pre-generation configuration

- la configurazione viene proposta dopo reticolo valido e prima della scrittura;
- contiene abstract, concetti chiave e lunghezza;
- l'utente può accettare/modificare;
- l'accettazione genera un contratto deterministico;
- il candidato fuori configurazione non può essere sigillato.

### G2 — originalità dimostrabile

- overlap verbatim non attribuito = blocker;
- overlap near-verbatim oltre soglia = blocker;
- riuso autorizzato richiede attribuzione e locator;
- tutte le fonti materiali richieste devono avere testo/fingerprint nel corpus di confronto;
- il receipt è legato al candidato;
- nessuna pretesa di unicità globale;
- il controllo viene ripetuto sul DOCX narrativo materializzato.

### G3 — saturazione pre-consegna

- minimo tre cicli;
- ordine dei gate variato;
- tutti i gate verdi;
- fixed point stabile;
- nessun nuovo finding nei cicli successivi;
- una mutazione successiva invalida il receipt e richiede nuova saturazione.

### G4 — completezza dashboard

- ogni ruolo di artefatto materiale atteso dalla modalità compare nell'atlante;
- ogni artefatto umano effettivamente prodotto compare nell'atlante;
- ogni artefatto epistemico attivo materialmente rilevante compare nell'atlante;
- ogni record ha sintesi compressa, descrizione completa e richiamo dashboard;
- ogni artefatto materiale richiamabile espone link relativo quando sicuro;
- le informazioni pubbliche distintive vengono ritrovate nel body HTML finale;
- path, fingerprint, digest, capability, readback e INTERNAL restano fuori dal body;
- layout mantiene palette editoriale blu/vino/oro, gerarchia tipografica, responsive e print profile.

### G5 — non regressione

- Python 3.10 e 3.12 compilano;
- unit/lifecycle/review/continuation/multimode/finalization passano;
- contract checker storico passa;
- evidence traceability checker v0.9.6 passa;
- generation governance checker v0.9.7 passa;
- 400k v5, M+1000, 10k continuation, 10k v7, v8 no-novelty, 30k tri-mode e 10k dashboard evidence restano verdi;
- 10k nuovi scenari edge generation-governance multi-seed passano;
- tutti i fixed-point storici restano identici e nessuna baseline viene aggiornata.

## DoD locale per componente

### `generation_configuration.py`

PASS se proposta, contratto e conformance sono deterministici e falsificabili; FAIL su lunghezza, concetti o abstract insufficienti.

### `plagiarism.py`

PASS solo su corpus di confronto completo e senza overlap vietati; FAIL su scope incompleto, overlap o receipt stale. La prova è scoped.

### `artifact_governance.py`

PASS solo se il DOCX è leggibile entro i limiti storici, conforme alla configurazione, anti-plagio e — per i testi finali derivati da draft — legato al candidato sigillato.

### `saturation.py`

PASS solo a fixed point multi-cycle senza nuovi finding dopo il primo ciclo.

### `artifact_atlas.py` / dashboard

PASS se ogni artefatto attivo possiede descrizione completa + compressa e la dashboard materializza i leaf pubblici. I record tecnici sensibili devono essere assenti.

### `governance_delivery.py`

PASS solo se tutti i gate precedenti e storici convergono nello stesso release state.

## Simulazioni edge v0.9.7

La nuova simulazione usa 10.000 scenari con seed di scenario derivato univocamente da 20 seed base. Le famiglie includono:

- violazione della lunghezza;
- omissione di concetti chiave;
- overlap esatto;
- corpus anti-plagio incompleto;
- riuso attribuito consentito;
- saturazione con gate mutante/failing e controllo positivo.

Lo script fallisce anche se i seed effettivi non sono 10.000 distinti.

## Matrice di adempimento dei prompt

| Intenzione utente | Meccanismo | Prova |
|---|---|---|
| proposta prima della generazione | generation preview | unit + contract checker |
| abstract / concetti / lunghezza | configuration contract | conformance tests |
| vincolo meccanico | seal gate + materialized gate | negative tests |
| Juriscribe non plagia | anti-plagiarism policy | overlap tests |
| deve poterlo dimostrare | scoped receipt + manifest corpus | receipt tests/dashboard |
| saturazione e ri-controllo ciclico | predelivery saturation | fixed-point tests + 10k |
| dashboard completa ogni artefatto | artifact atlas | coverage gate |
| completa e compressa | dual-level cards | dashboard materialization test |
| gradevole e colorata | editorial workbench V3 | HTML/CSS regression assertions |
| test materializzazione informazioni | distinctive-leaf HTML test | unit integration |
| edge e no regressioni | new 10k + historical CI | workflow |
| hardening/semplificazione storico | core/public split, scoped proof, one final boundary | audit + checker |

## Criterio di release

La PR non è considerata completa sulla base di review manuale o di un singolo test. La DoD si considera raggiunta soltanto quando la CI completa è `success` sul medesimo head finale della PR, senza aggiornare i receipt fixed-point storici.
