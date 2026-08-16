# Juriscribe v0.9.3 — runtime hardening e fast bootstrap

## Mandato chiarito
Il mandato operativo è: correggere i finding P0/P1/P2 senza ridurre gli invarianti scientifico-editoriali consolidati, rendere il primo avvio in chat più rapido solo quando admission e probe restano fail-closed, e dimostrare il risultato con test negativi, baseline storiche e CI completa.

Non rientrano nello scope: ridurre M+10.000, eliminare mining/reticolo/review/provenance, trasformare i gate in euristiche, rendere implicita l'accettazione o la modalità, oppure spostare la complessità in chat.

## DoD Px

### P0 — integrità immediata
- session ID automatici non deterministici;
- workspace esistente mai sovrascritto;
- capability dopo probe immutabili e non ampliabili;
- direct push su `main` rilevato dalla CI come governance violation;
- configurazione server-side di branch protection dichiarata obbligatoria, senza fingere che la PR possa abilitarla da sola.

### P1 — consistenza e confini
- receipt nonce-bound e probe receipt single-use;
- automa bootstrap coerente fino a `MODE_SELECTION_REQUIRED` / `ACTIVE_WORK`;
- `load()` fail-closed sull'integrità;
- state/integrity scritti con atomic replace;
- dashboard legata anche a phase/interaction/completion/integrity/runtime;
- artefatti confinati a `<workspace>/artifacts`, no escape/symlink.

### P2 — superficie e supply chain
- messaggi d'eccezione completi solo nel ledger INTERNAL, non nella dashboard/chat;
- output JSON macchina con doppio opt-in;
- DOCX readback bounded contro ZIP/resource exhaustion, macro/encryption/path traversal;
- GitHub Actions pin a commit SHA immutabile.

## Fast bootstrap sicuro
La sequenza logica non cambia:

```text
TERMS_PRESENTED
-> human I ACCEPT
-> PROBE_REQUIRED / probe
-> PROBED / sealed receipt
-> INITIALIZING / initialize
-> MODE_SELECTION_REQUIRED
-> human mode
-> ACTIVE_WORK
```

L'ottimizzazione riguarda i round-trip, non i gate. Dopo `I ACCEPT`, `bootstrap-after-acceptance` può eseguire probe e initialize nello stesso turno dell'assistente, producendo e verificando comunque receipt distinte. La modalità non viene applicata automaticamente.

Percorso chat consigliato:

```text
1. host: acceptance notice / termini
2. human: I ACCEPT
3. host: probe + initialize, poi mostra CONTINUATION | GREENFIELD | REVIEW | ALTRO
4. human: seleziona modalità
5. host: lavoro autonomo artifact-first
```

Il runtime mantiene anche i comandi separati `accept`, `probe`, `initialize` per audit, test e host che preferiscono il percorso esplicito.

## Prestazioni
`persist_session()` centralizza render dashboard, binding e save. Il facade non rigenera più la dashboard dopo che il runtime l'ha già aggiornata. L'initialize costruisce lo stato in memoria e materializza una sola generazione coerente invece di salvare/rileggere/rerenderizzare ripetutamente.

## Governance GitHub
Una PR può pinning Actions e introdurre un controllo che, su push a `main`, verifica che il commit sia associato a una PR. Non può tuttavia rendere `main` server-side protected senza un'API amministrativa disponibile. DoD operativa del repository: abilitare in GitHub Settings una ruleset/branch protection che richieda PR e i check `runtime-tests (3.10)`, `runtime-tests (3.12)`, `simulation-and-saturation`, oltre a vietare force-push/delete. Il runtime non dichiara falsamente di aver applicato questa impostazione.
