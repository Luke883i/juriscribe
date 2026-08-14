# Juriscribe

Juriscribe è un **agent repository** per progettare, scrivere, riorganizzare e verificare monografie giuridiche con il giurista in controllo. L'assistente operativo è **iSeneca**.

## Cosa fa

Juriscribe trasforma una richiesta e un corpus in uno stato di lavoro auditabile. Prima di scrivere esegue deep mining di contenuto, relazioni e stile; propone un setup minimo; converte i parametri accettati in Definition of Done (DoD) bloccanti; controlla claim, fonti, continuità editoriale e artefatti; termina solo quando il completion gate è soddisfatto.

Juriscribe **non è** un prompt monolitico, un archivio di testi, un motore di ricerca autonomo né una prova di correttezza giuridica. Il modello linguistico produce analisi e proposte; il runtime deve rendere osservabile che cosa è stato letto, verificato, inferito, materializzato e ancora non provato.

## Esperienza dell'utente

Dopo l'ammissione (`I ACCEPT` → `PROBE ISENECA` → `INITIALIZE ISENECA`), l'utente normalmente deve fare solo questo:

1. fornire richiesta e materiali;
2. scegliere `ACCETTA CONSIGLIATI` oppure `MODIFICA`;
3. ricevere il risultato quando i gate sono chiusi.

Il setup raccomandato contiene solo i parametri necessari: funzione del capitolo, lunghezza, profondità di ricerca e postura argomentativa. Ogni valore accettato diventa un DoD bloccante.

## Pipeline di un nuovo capitolo

```text
INGEST
→ DEEP_MINE + STYLE_FINGERPRINT
→ GLOBAL / LOCAL / RELATIONAL MODEL
→ PROPOSE_MINIMAL_SETUP
→ USER_ACCEPT_OR_MODIFY
→ PARAMETERS_TO_DOD + FREEZE_DOD
→ CLAIM_AND_RESEARCH_PLAN
→ SOURCE_VERIFICATION
→ DRAFT
→ STYLE / QUALITY / LOSSLESS AUDIT
→ CLAIM→SOURCE→PINPOINT→ARTIFACT TRACEABILITY
→ DOD_VALIDATION
→ M+10.000 NO-NOVELTY VS DOD
→ MATERIALIZE + READBACK
→ COMPLETE
```

## Tre livelli di evidenza da non confondere

1. **Fonte verificata**: la fonte è stata effettivamente letta e registrata.
2. **Apparato visibile**: il lettore dell'artefatto può ricostruire quali fonti sono richiamate.
3. **Tracciabilità scientifica**: ogni claim materiale è mappato a fonte/premessa, pinpoint e posizione nell'artefatto.

Un elenco bibliografico non sostituisce il terzo livello. Allo stesso modo, un claim presente nel ledger ma invisibile nel documento non è sufficiente per un elaborato scientifico.

## Continuità di stile

La continuità non significa imitazione meccanica. Juriscribe misura separatamente ritmo della frase, densità di sezionamento, punteggiatura argomentativa e connettori. L'apparato bibliografico viene escluso dalle metriche di prosa. Scostamenti strutturali importanti — per esempio l'**over-sectioning** tipico di una bozza AI — vengono resi espliciti prima di `COMPLETE`.

## Benchmark monografico cieco

Quando Juriscribe afferma di saper inferire un capitolo N+1 dai capitoli precedenti, può essere sottoposto a benchmark cieco. Il runtime non contiene fixture hard-coded di monografie. La reference N+1 deve essere custodita fuori dal contesto del generatore; prima della generazione il runtime riceve al massimo un **commitment SHA-256**. Il testo effettivo viene rivelato solo dopo che la generazione è stata sigillata.

Il benchmark misura capacità di extrapolazione strutturale, non verità giuridica. La presenza della reference nel training del modello non è tecnicamente escludibile dal solo runtime e va registrata come limite.

## Completion gate

`COMPLETE` richiede almeno:

- tutti i DoD bloccanti `DONE`;
- nessuna contraddizione bloccante aperta;
- `M+10.000` probe consecutivi senza novità materiale rispetto ai DoD;
- quality gate senza failure bloccanti;
- claim/source coverage conforme al setup;
- benchmark cieco integro quando il DoD richiede una capacità di extrapolazione monografica;
- readback degli artefatti richiesti.

## Dashboard

`session-dashboard.html` è un **verbale giuridico-scientifico-editoriale della sessione**. Mostra corpus letto, parametri e DoD, qualità, claim/fonti, tracciabilità, benchmark, limiti, capability host e readback. Non espone chain-of-thought.

## Validazione

```bash
python -m unittest discover -s tests -v
python scripts/audit_chapter2.py --chapter /path/to/candidate.txt --reference /path/to/reference.txt --length-min 7000 --length-max 9000 --json-out /tmp/audit.json
python scripts/simulate_v3.py --cases 100000 --json-out validation/simulation-v3.json
python scripts/reflect_v3.py --target 1000 --json-out validation/reflection-v3.json
```

La simulazione v3 applica mutazioni reali ai gate e verifica che vengano respinte; non conta semplicemente casi instradati come successi. La riflessione v3 ha saturazione `1..Q` seguita da `Q+1000` scenari senza nuova firma di rischio.

Vedi `AGENTS.md` e `docs/RUNTIME_V3_AUDIT_HARDENING.md`.
