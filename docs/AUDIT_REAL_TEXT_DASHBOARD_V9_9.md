# Audit v0.9.9 — fine-tuning con 100 sessioni su testi giuridici reali

## Scopo

Questa release risponde a una domanda più severa rispetto alla sola persistenza introdotta in v0.9.8: la dashboard persistente è davvero alimentata dalle informazioni prodotte durante una sessione sostanziale e gli artefatti materializzati sono realmente coerenti con la proiezione epistemica che dichiarano di rappresentare?

La verifica è costruita come DoD falsificabile. Non basta che l'HTML esista, che un digest sia fresco o che un DOCX sia un pacchetto OOXML valido. Il contenuto pubblico deve essere materializzato nel file destinato all'utente e deve rimanere allineato allo stato canonico.

## Audit causale dello stato v0.9.8

La v0.9.8 ha corretto il difetto principale della dashboard effimera: `session-dashboard.html` è persistente, viene rigenerata dopo le mutazioni runtime, è pubblicata con sostituzione atomica, viene riletta dal filesystem dopo il salvataggio dello stato e possiede un ledger monotono di generazione.

L'audit v0.9.9 ha però individuato due opportunità di hardening.

1. I quattro dossier canonici (`evidence_dossier`, `source_register`, `inference_register`, `transformation_ledger`) erano vincolati al digest della proiezione semantica nello stato, ma il runtime non dimostrava che **il testo effettivamente contenuto nel DOCX** materializzasse quella proiezione. Un DOCX formalmente valido ma semanticamente incompleto poteva quindi superare il controllo di formato e portare metadata riferiti alla proiezione corretta.
2. Il verifier della dashboard provava la presenza di ogni foglia dell'atlante, ma non esplicitava due controlli indipendenti utili contro futuri drift: testimoni semantici ricavati direttamente dalla sessione reale e parità dei ruoli materiali pubblici registrati rispetto all'atlante.

La v0.9.9 chiude entrambi i punti senza riscrivere mining, reticolo, review, provenance, anti-plagio, saturation o fixed point storici.

## DoD globale

La release è accettabile solo se tutte le condizioni seguenti sono vere contemporaneamente.

1. Esistono esattamente **100 sessioni E2E di fine-tuning**.
2. Gli input delle 100 sessioni sono composti esclusivamente da estratti giuridici congelati dopo verifica su fonti istituzionali ufficiali; il test CI non dipende dalla rete.
3. Le 100 sessioni sono suddivise in quattro classi di lunghezza: 25 SHORT, 25 MEDIUM, 25 LONG, 25 XL.
4. I tre modi Juriscribe sono esercitati ciclicamente.
5. Ogni pacchetto testuale delle 100 sessioni è univoco.
6. Ogni sessione attraversa inizializzazione, scelta della modalità, mining reale, semantic mining, configurazione, congelamento DoD, sealing del target/candidato e materializzazione degli artefatti.
7. Il test di artifact admission isola esplicitamente il prerequisito della final review; non dichiara che le 100 sessioni raggiungano l'intero completion fixed point. La convergenza complessiva resta coperta dalle suite storiche.
8. Ogni artefatto richiesto dal modo è un file reale sotto la directory `artifacts/` e passa verifica di formato, confinamento e readback.
9. Ogni nuovo dossier canonico DOCX materializza integralmente le foglie della stessa proiezione canonica utilizzata dalla dashboard.
10. Ogni artefatto narrativo primario sottoposto a generation governance possiede prova PASS di configurazione e anti-plagio; dove applicabile è legato al sealed candidate.
11. Venti scenari avversi inseriscono una sequenza copiata dalla fonte reale e devono essere bloccati dall'anti-plagio.
12. Dieci scenari avversi tentano di registrare un dossier DOCX semanticamente incompleto e devono essere bloccati.
13. La dashboard finale contiene un testimone semantico derivato dal testo reale e la summary pubblica di ogni artefatto registrato.
14. La dashboard non espone path assoluti, fingerprint, shingle/hash o altri campi tecnici riservati.
15. Il ledger della dashboard è strettamente monotono e termina sulla generazione descritta dallo state persistito.
16. Tutte le regressioni storiche e tutti i fixed point precedenti rimangono verdi senza aggiornare i receipt di validazione.

## DoD locali

### Dossier canonici

`JURISCRIBE_DOSSIER_SEMANTIC_MATERIALIZATION_V1` introduce una prova contenutistica distinta dal digest di freschezza. Il verifier estrae il testo reale da `word/document.xml` entro i limiti di readback già previsti, deriva tutte le foglie scalari della proiezione canonica e fallisce se anche una foglia pubblica manca dal DOCX. La registrazione di un nuovo dossier v0.9.9 è quindi fail-closed.

La compatibilità è deliberata: i dossier registrati da sessioni legacy prima di v0.9.9 non vengono invalidati retroattivamente. Il marker `semantic_materialization_profile` rende invece obbligatoria la prova per ogni nuova registrazione effettuata dal nuovo runtime.

### Dashboard

La verifica persistente conserva la parità completa dell'atlante e aggiunge:

- testimoni semantici da mandato, modalità, unità epistemiche, claim, titoli delle fonti, configurazione e summary degli artefatti;
- confronto fra ruoli materiali pubblici registrati e ruoli materiali presenti nell'atlante;
- materializzazione della summary registrata di ciascun artefatto nell'atlante pubblico;
- esposizione pubblica scrubbed delle prove di generation governance e semantic materialization, senza digest, path, hash o readback.

La pubblicazione resta atomica: un failure preserva la generazione precedente.

### Testi reali

`fixtures/real_legal_texts_v99.json` congela estratti verificati di Costituzione italiana, Carta dei diritti fondamentali dell'Unione europea, CEDU e GDPR, con autorità, strumento, locator e URL istituzionale. Il fixture non è una banca dati giuridica e non viene usato per produrre conclusioni sostanziali; serve esclusivamente come input legale reale, riproducibile e non sintetico per la prova E2E.

La costruzione dei 100 pacchetti usa shuffle deterministico e soglie di parole. La distribuzione è:

- SHORT: 80–180 parole, 25 casi;
- MEDIUM: 220–450 parole, 25 casi;
- LONG: 520–900 parole, 25 casi;
- XL: 900–1700 parole, 25 casi.

## Anti-plagio

Il test positivo non copia il testo sorgente: i termini necessari alla configurazione vengono ricomposti in un ordine autonomo e dentro prosa nuova. Ogni quinto scenario aggiunge invece almeno 24 parole consecutive del pacchetto reale a un candidato di prova. Il controllo deve produrre `FAIL` e almeno un finding proibito. La prova resta correttamente scoped al corpus registrato e non pretende unicità globale.

## Materializzazione degli artefatti

Per ciascuna sessione il test crea file DOCX reali per i ruoli richiesti dal modo. I dossier sono costruiti dalla proiezione canonica; i documenti narrativi usano il candidato generato; il registro rilievi REVIEW è un artefatto descrittivo del test. Ogni file viene poi verificato dal runtime e la dashboard viene rigenerata dopo ciascuna registrazione.

La summary di registrazione diventa parte della descrizione pubblica dell'artefatto nell'atlante. Questo permette di dimostrare che non esiste soltanto una card astratta per il ruolo, ma che la dashboard ha ricevuto le informazioni dell'istanza materiale realmente registrata.

## Non regressione e convergenza

Il fine-tuning non modifica i receipt storici e non riduce i target precedenti. La CI deve continuare a eseguire compile e unittest su Python 3.10 e 3.12, i checker di contratto precedenti, il real-text checker v0.9.9, le 100 sessioni reali, 400k five-class, M+1000, 10k continuation, 10k mutation, historiography, 30k tri-mode, 10k dashboard evidence, 10k generation governance e tutti i fixed point storici.

La release converge soltanto quando il medesimo head della PR supera l'intera matrice. Un failure della nuova suite non viene risolto riducendo le asserzioni: deve produrre un controesempio e una correzione causale.

## Criterio di fine-tuning

Il fine-tuning di questa release non è addestramento statistico del modello. È raffinamento del runtime e dei suoi invarianti mediante controesempi reali e verifiche meccaniche. La situazione desiderata per `main` è quindi: dashboard persistente, alimentazione semantica dimostrabile, dossier materialmente completi, artifact registration visibile, anti-plagio avverso verificato e compatibilità con tutto lo storico.
