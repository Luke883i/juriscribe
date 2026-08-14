# Runtime v0.3.0 — scientific audit hardening

## Perché questa versione esiste

Il test reale Capitolo 1 → Capitolo 2 ha mostrato che Juriscribe sa costruire un seguito giuridicamente plausibile e ben strutturato, ma il primo audit v3 era a sua volta fragile. Questa versione corregge **anche l'audit**, non soltanto il generatore.

## Correzione del Capitolo 2 audit

Il precedente report indicava scarsa visibilità delle fonti. La verifica diretta del testo dimostra invece:

- corpo sostanziale: 7.528 parole, dentro il DoD 7.000–9.000;
- apparato: 13 fonti dichiarate;
- tutte le 13 fonti sono richiamate nel corpo, con 19 callout complessivi;
- quindi `source apparatus visibility = PASS`.

Il falso positivo nasceva da euristiche che cercavano URL/marker nel corpo e non riconoscevano il sistema note→appendice. Inoltre il calcolo del ritmo stilistico includeva l'appendice di fonti: le sue frasi corte abbassavano artificialmente la lunghezza media della frase.

Il rischio reale è diverso: il Capitolo 2 ha **24 heading su 7.528 parole** (3,188/1000) contro **10 su 8.291** (1,206/1000) nel Capitolo 1. Il ritmo medio del corpo (20,68 parole) resta entro il 25% del riferimento (25,43), ma la segmentazione è molto più fitta. È un caso di possibile over-sectioning AI e va sottoposto a review editoriale.

## Evidenza: tre livelli

1. source verification;
2. reader-visible source apparatus;
3. claim-level traceability: claim → source/premise → pinpoint → artifact locator.

Il Capitolo 2 prova il livello 2. Il livello 3 non può essere ricostruito integralmente dal solo DOCX perché il claim ledger originario non è incorporato con locator puntuali. Il runtime v0.3 aggiunge `artifact_evidence` proprio per evitare questa perdita.

## Benchmark monografico

Lawrence Rosen, *Open Source Licensing: Software Freedom and Intellectual Property Law*, resta una **leading specialist reference** adatta al dominio, ma non viene proclamata “dominante assoluta” senza un corpus bibliometrico adeguato. Il benchmark storico ch.5→ch.6 ha mostrato una buona previsione della transizione verso GPL/reciprocity ma ha mancato scelte autoriali specifiche (“The Preamble to the GPL”, “At No Charge”) e ha aggiunto sezioni moderne non presenti nell'originale.

Il precedente benchmark, però, non forniva prova robusta dell'assenza di leakage: l'N+1 era codificato nel runtime fixture. v0.3 rimuove il caso Rosen dal codice e introduce un protocollo generico con commitment SHA-256 esterno, sealing della generazione e reveal ex post.

## Hardening introdotto

- quality audit che separa body e apparatus;
- style-distance multidimensionale e gate anti-over-sectioning;
- artifact evidence ledger per claim-level traceability;
- benchmark generico con external commitment, senza answer hard-coded;
- completion gate integrato con quality/source/benchmark/readback;
- dashboard ridisegnata come verbale giuridico-scientifico-editoriale;
- simulator v3 che applica mutazioni reali e verifica il rifiuto dei gate;
- reflection v3 su 3.456 firme di scenario con ulteriori 1.000 no-novelty;
- script di validazione eseguibili direttamente dal repository senza `PYTHONPATH` esterno.

## Limiti residui

- nessun runtime può provare che un modello preaddestrato non abbia mai visto una monografia; il commitment protegge il protocollo di sessione, non il training;
- il quality gate usa proxy testuali e non sostituisce la valutazione scientifica di un giurista;
- la dominanza dottrinale/giurisprudenziale richiede campionamento e criteri di autorità adeguati al dominio;
- la semantica avanzata resta responsabilità dell'host AI, ma deve essere materializzata in record auditabili;
- DOCX/PDF rendering e web access restano capability dell'host e non della stdlib del kernel.
