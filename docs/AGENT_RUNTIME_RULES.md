# Juriscribe agent runtime rules v0.4 — post-admission

Queste regole si applicano solo dopo receipt valida.

## Missione

Generare un capitolo giuridico N+1 partendo da capitoli precedenti, non produrre testo giuridico decontestualizzato.

## Invarianti

- niente setup prima di reticolo epistemico validato;
- niente generation contract prima di setup accettato e DoD congelati;
- niente completamento senza generation contract legato al reticolo corrente;
- ogni claim materiale esterno deve essere circostanziato;
- inferenze forti con premesse, ponte e falsificatore, senza cicli;
- confronto obbligatorio con capitoli precedenti per continuità, sviluppo e non duplicazione;
- bibliografia del corpus registrata se disponibile;
- simulazione edge-case e saturazione prima della chiusura;
- compressione finale lossless con inventario epistemico preservato;
- dashboard leggibile da giuristi e redazioni, non da soli ingegneri;
- nessuna esposizione di chain-of-thought.

## UX

Dopo il mining/reticolo, mostra solo una configurazione raccomandata con due scelte: `ACCETTA CONSIGLIATI` o `MODIFICA`. Dopo l'accettazione l'utente non deve essere trascinato nella meccanica interna salvo decisione interpretativa realmente non delegabile.
