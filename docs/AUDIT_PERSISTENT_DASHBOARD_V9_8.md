# Audit severo v0.9.8 — dashboard persistente di sessione ed E2E reale

## Problema osservato

La dashboard poteva risultare formalmente corretta nei test e tuttavia apparire vuota nell'uso reale perché le prove storiche verificavano soprattutto renderer e proiezioni su fixture sintetiche o file temporanei. Mancava una prova end-to-end che attraversasse una sessione Juriscribe reale, riaprisse state e HTML dal filesystem e dimostrasse l'aggiornamento iterazione dopo iterazione.

## Mandato atomizzato

1. Ogni sessione possiede un solo `artifacts/session-dashboard.html` persistente.
2. Ogni mutazione runtime sostanziale deve generare una nuova revisione della dashboard prima di considerare la mutazione persistita.
3. L'HTML non deve essere scritto in-place: il render deve avvenire su file temporaneo, essere verificato e sostituito atomico.
4. Il nuovo HTML deve essere legato allo state corrente tramite il digest storico e deve materializzare le informazioni pubbliche dell'atlante degli artefatti.
5. Dopo il salvataggio dello state, il runtime deve ricaricare state e dashboard dal filesystem e rieseguire il controllo.
6. Ogni revisione deve essere registrata in un ledger monotono interno con trigger, generazione e fingerprint del file.
7. Un failure di rendering deve preservare la dashboard precedente e non avanzare la generazione persistita.
8. Le sessioni legacy prive del nuovo record devono migrare automaticamente alla prima persistenza successiva.
9. L'E2E deve usare il runtime reale e attraversare CONTINUATION, GREENFIELD e REVIEW.
10. La CI deve conservare dashboard E2E reali come artifact ispezionabile, oltre a mantenere tutte le regressioni storiche.

## Finding causali

### F1 — test sintetico != sessione reale

`test_generation_governance_v9_7.py` costruiva uno state manuale e rendeva HTML in `TemporaryDirectory`. Dimostrava che il renderer sapesse proiettare contenuto già presente, non che il runtime alimentasse e persistesse progressivamente la dashboard.

### F2 — simulazione dashboard campionata

La simulazione v0.9.6 rendeva solo un campione delle 10.000 iterazioni e sempre su file temporaneo. La simulazione v0.9.7 non attraversava il renderer dashboard.

### F3 — write diretto del file finale

Il vecchio `persist_session()` chiamava direttamente il renderer sul path finale. Un'interruzione durante la scrittura poteva lasciare un file parziale o vuoto. Mancava un commit atomico dell'HTML.

### F4 — assenza di prova iterativa persistente

Non esisteva un contatore monotono di generazione né un ledger che permettesse di dimostrare che initialize, select-mode, mine, semantic-mining, accept-setup e le altre mutazioni avessero ciascuna prodotto una dashboard nuova.

### F5 — assenza di reload E2E

La verifica storica avveniva prevalentemente sullo state in memoria. Mancava la prova che state salvato, integrity manifest e HTML riaperti dal filesystem fossero coerenti dopo il commit.

## Architettura introdotta

`JURISCRIBE_PERSISTENT_SESSION_DASHBOARD_V1` aggiunge un boundary di persistenza senza cambiare mining, reticolo, claim ledger, review, provenance, anti-plagio o saturazione.

La transazione per ogni mutazione è:

1. garantire il record stabile `session_dashboard` nello state;
2. incrementare la generazione candidata;
3. renderizzare su file HTML temporaneo nella directory artifacts;
4. verificare digest e materializzazione dei leaf pubblici dell'atlante;
5. conservare una copia di rollback della dashboard precedente;
6. `os.replace` del candidato sul path canonico;
7. rieseguire la verifica materiale storica dell'artefatto;
8. salvare `state.json` + `session.integrity.json`;
9. ricaricare lo state dal disco;
10. verificare nuovamente la dashboard contro lo state ricaricato;
11. appendere la generazione al ledger interno `ledger/dashboard-generations.jsonl`.

Se un passaggio fallisce prima del commit completo, la dashboard precedente viene ripristinata o il nuovo file viene rimosso se si trattava della prima generazione.

## DoD globale

La release è completa soltanto se tutte le condizioni seguenti sono vere.

### G1 — persistenza reale

- `session-dashboard.html` esiste dentro la directory artifacts della sessione;
- il path resta stabile fra le iterazioni;
- la generazione aumenta monotonicamente dopo ogni mutazione runtime persistita;
- il trigger dell'ultima generazione corrisponde al comando che ha prodotto la mutazione.

### G2 — coerenza state/HTML

- il meta digest della dashboard corrisponde allo state corrente;
- state viene ricaricato dal filesystem dopo il salvataggio;
- la dashboard viene riverificata sullo state ricaricato;
- state e integrity manifest continuano a usare il fail-closed storico.

### G3 — materializzazione informativa

- il mandato compare nel body;
- ogni leaf pubblico della vista dell'atlante effettivamente renderizzata deve essere reperibile nell'HTML;
- `missing_public_leaf_count` deve essere zero;
- un record epistemico aggiunto durante una iterazione deve comparire nella generazione successiva;
- la dashboard non può essere considerata PASS se il body è assente o vuoto.

### G4 — atomicità e rollback

- il renderer scrive su temp, non sul file finale;
- la pubblicazione usa `os.replace`;
- un errore di render non altera il dashboard precedente;
- un errore non incrementa la generazione presente nello state persistito.

### G5 — E2E reale tri-mode

Per ciascuna modalità CONTINUATION, GREENFIELD e REVIEW l'E2E deve attraversare realmente:

`initialize → select-mode → mine → semantic-mining → accept-setup`

e, dopo ogni passaggio, riaprire lo state con `Workspace.load()`, verificare `session-dashboard.html`, controllare il numero di generazione e trovare nell'HTML i marker epistemici introdotti dal runtime.

### G6 — regressioni

- Python 3.10 e 3.12 compilano;
- tutti gli unittest storici passano;
- i checker v0.9.6 e v0.9.7 restano validi in modo future-additive;
- il nuovo checker v0.9.8 passa;
- l'E2E tri-mode passa;
- 400k, M+1000, 10k continuation, 10k v7, v8, 30k tri-mode, 10k dashboard evidence, 10k generation governance e tutti i fixed-point storici restano verdi;
- nessun receipt di validazione storico viene aggiornato per assorbire regressioni.

## DoD locale

### `dashboard_persistence.py`

PASS se implementa render temporaneo, verifica informativa, replace atomico, rollback, salvataggio, reload e ledger monotono. FAIL se un HTML privo di leaf pubblici può essere committato.

### `pipeline_v9.py`

PASS se initialize, select-mode, dashboard esplicita e ogni comando mutante finale passano un trigger a `persist_session`. FAIL se una mutazione può essere salvata senza nuova dashboard.

### `session.py`

PASS se espone un record backward-compatible `dashboard_persistence` con generazione e stato. Le sessioni storiche senza il campo devono continuare a caricarsi usando il default della dataclass.

### E2E

PASS solo se usa admission/probe/initialize reali, CLI runtime reale e filesystem reale. Fixture sintetiche del renderer non contano come E2E.

### CI

PASS se esegue checker + E2E e conserva le tre dashboard risultanti come artifact CI, continuando a eseguire integralmente la suite storica.

## Criterio finale

La DoD non è soddisfatta da una dashboard ben formata costruita da una fixture. È soddisfatta solo quando una sessione reale produce lo stesso file persistente, lo aggiorna a ogni iterazione, ne conserva una prova monotona e la CI riapre e verifica state e HTML dal filesystem in tutte le modalità supportate.
