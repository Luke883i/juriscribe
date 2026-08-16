# Juriscribe v0.9.7 — Generation Governance

## Scopo

La v0.9.7 introduce un confine meccanico fra intenzione editoriale, generazione, controllo dell'originalità e consegna. La configurazione non è un prompt informale: è un contratto accettato dall'utente che deve restare verificabile nel candidato e negli artefatti narrativi materializzati.

## 1. Configurazione prima della generazione

Dopo il mining atomico e la validazione del reticolo, Juriscribe propone almeno:

- **abstract di generazione**: anticipa funzione, tesi/perimetro e dorsale epistemica del prodotto;
- **concetti chiave**: termini/contenuti che devono risultare coperti nel candidato;
- **lunghezza**: range di parole ammesso;
- i parametri editoriali già previsti: genere, destinatari, stile citazionale, profondità di ricerca e posture mode-specific.

L'utente può accettare i consigliati o modificarli. L'accettazione produce `JURISCRIBE_GENERATION_CONFIGURATION_V1`. Il contratto di generazione incorpora la configurazione e viene ridigerito; il mode contract viene poi riallineato allo stesso stato.

## 2. Vincolo meccanico

Un nuovo draft governato non può essere sigillato se:

- è fuori dal range di lunghezza accettato;
- non copre i concetti chiave accettati;
- non raggiunge la soglia minima di copertura lessicale dell'abstract accettato.

Il controllo viene ripetuto sul file DOCX materializzato. Per i testi narrativi finali, quando esiste un candidato sigillato, il fingerprint normalizzato del DOCX deve corrispondere al candidato. Non è quindi sufficiente auditare un draft e poi consegnare byte che contengano un testo sostanzialmente diverso.

## 3. Anti-plagio

Policy: `JURISCRIBE_ANTI_PLAGIARISM_V1`.

Juriscribe costruisce fingerprint deterministici del corpus testuale realmente disponibile al runtime e blocca:

- sequenze verbatim non attribuite;
- overlap near-verbatim sopra la soglia di policy;
- perimetri di confronto incompleti quando una fonte usata dal lavoro non dispone di testo/fingerprint registrato.

Una proposizione parafrasata nel claim ledger **non è trattata come testo della fonte**. Per fonti esterne il runtime deve ricevere testo sorgente o fingerprint registrabile. Questo evita sia falsi positivi sia false prove.

Il riuso testuale è consentito solo se esplicitamente autorizzato e associato a una **collocazione di attribuzione** (`attribution_locator`). Il receipt conserva la prova dell'autorizzazione senza dover esporre in dashboard i fingerprint interni.

### Perimetro della dimostrazione

Juriscribe può dimostrare: **nessun overlap vietato è stato rilevato nel corpus di confronto runtime-visible registrato**. Non dichiara unicità globale rispetto a testi non accessibili o non registrati (`global_uniqueness_claim = false`). Un corpus incompleto fa fallire il gate invece di produrre una rassicurazione non dimostrabile.

## 4. Saturazione e ri-controllo ciclico

Prima della consegna viene materializzato `JURISCRIBE_PREDELIVERY_SATURATION_V1`.

Il ciclo riesamina almeno:

- conformità alla configurazione;
- anti-plagio;
- quality audit;
- chiusura claim/fonti;
- provenance;
- review finale severa;
- freschezza dei dossier;
- tracciabilità delle evidenze;
- materializzazione/readback;
- governance dei testi narrativi materializzati;
- completezza della dashboard rispetto agli artefatti.

Il controllo è rieseguito con ordine variato per almeno tre cicli. La consegna richiede:

1. tutti i gate verdi;
2. stesso stato semantico/fixed point;
3. nessun nuovo finding nei ri-controlli successivi.

Una mutazione successiva invalida la saturazione e richiede nuovo audit.

## 5. Dashboard e artefatti

La dashboard v0.9.7 contiene un **Atlante completo degli artefatti**.

Per ogni artefatto materiale previsto/prodotto e per ogni artefatto epistemico attivo mostra:

- funzione;
- stato;
- sintesi compressa;
- descrizione pubblica completa/drill-down;
- richiamo alla sezione correlata;
- richiamo al file materializzato quando appropriato.

L'atlante comprende anche gli artefatti storici già previsti: Evidence dossier, Source register, Inference register, Transformation ledger, final chapter/final legal text, review report, findings register, revised text, provenance, review, simulazioni, compressione, DoD, limiti e tracciabilità.

Sono esclusi dal body umano: path assoluti, digest, capability, readback tecnico, fingerprint n-gram/shingle e strutture INTERNAL. L'esclusione non riduce il controllo: tali dati restano disponibili ai gate interni.

## 6. Compatibilità storica

La v0.9.7 è additiva rispetto a admission contract 1.7.0. Le sessioni pregresse prive del profilo v0.9.7 restano migrabili: i nuovi gate si attivano sui nuovi setup/configurazioni governati e sui nuovi artefatti materializzati, senza invalidare retroattivamente lo storico solo per assenza dei nuovi record.
