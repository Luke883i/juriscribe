# Runtime v0.6 — development frontier e coverage gate

## Perché

Il benchmark cieco su Santi Romano ha mostrato un risultato utile: Juriscribe può cogliere il nucleo teorico di una continuazione senza necessariamente sviluppare con la stessa densità **tutte le modalità** che un autore umano usa per dimostrarlo (casi, controargomenti, distinzioni, applicazioni). Pretendere la previsione esatta della sequenza dell'autore sarebbe un obiettivo fragile e poco generalizzabile.

v0.6 introduce quindi un controllo diverso: non “indovina l'indice”, ma verifica che il capitolo sviluppi in profondità sufficiente il **frontier epistemico** che i capitoli precedenti rendono disponibile.

## Development frontier

Dopo `freeze-dods`, il runtime deriva un `continuation.plan` dal generation contract e dal reticolo. Ogni obbligo contiene:

- unità epistemiche collegate;
- modalità (`ARGUMENT`, `COUNTERARGUMENT`, `CASE_FAMILY`, `DISTINCTION`, ecc.);
- priorità (`CORE`, `SUPPORTING`, `OPTIONAL`);
- orizzonte (`NOW`, `LATER`, `OPTIONAL`);
- profondità minima;
- rationale auditabile.

Le alternative di sviluppo sono non vincolanti e `sequence_is_binding` deve essere `false`.

## Coverage gate

Sul candidato sigillato il runtime registra per ogni obbligo stato, profondità, locator ed evidenze. Il gate fallisce quando, tra l'altro:

- un obbligo core `NOW` non è sviluppato alla profondità minima;
- la copertura ponderata complessiva resta sotto la soglia del piano;
- una famiglia di casi/applicazioni richiesta dal reticolo non riceve sviluppo concreto;
- un tema `LATER/OPTIONAL` viene sviluppato in profondità mentre restano core irrisolti;
- nuovo materiale sostanziale non è legato a un obbligo e a una fonte/inferenza auditata;
- plan o coverage sono stale rispetto a generation contract o candidato.

Il nuovo materiale **legato e verificato** resta ammesso: un capitolo N+1 deve poter produrre conoscenza nuova.

## Benchmark ex post

`benchmark_gap_report()` confronta facet reali e sintetiche dopo il reveal. Registra:

- weighted coverage;
- core mancanti;
- facet presenti ma sottosviluppate;
- surplus plausibile;
- copertura per categoria.

`sequence_scoring` è sempre `DISABLED`.

## Compatibilità

La funzione bassa `completion_gate()` mantiene `continuation_required=False` per i fixture storici. L'orchestratore v0.6 chiama invece il gate con `continuation_required=True`: una sessione reale Juriscribe non può completare senza continuation coverage `PASS` sul candidato finale.
