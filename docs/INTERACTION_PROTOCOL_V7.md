# Interaction protocol v0.7

Le risposte operative di Juriscribe usano card deterministicamente strutturate, non menu chiusi.

Ogni card contiene:

- fase corrente;
- headline e sintesi;
- scelte standard;
- flag `blocking`;
- `free_input_allowed=true`;
- scelta `ALTRO` sempre disponibile;
- digest del payload.

Profili standard:

- terms → `I ACCEPT`, `I DECLINE`, `ALTRO`;
- probe → `PROBE JURISCRIBE`, `ALTRO`;
- initialize → `INITIALIZE JURISCRIBE`, `ALTRO`;
- active → `CARICA CAPITOLI`, `STATO SESSIONE`, `ALTRO`;
- setup → `ACCETTA CONSIGLIATI`, `MODIFICA`, `ALTRO`;
- complete → `APRI ARTEFATTI`, `RICHIEDI MODIFICHE`, `NUOVO CAPITOLO`, `ALTRO`.

L'host può aggiungere opzioni pertinenti senza rimuovere il percorso libero. Le card espongono stato e opzioni, non ragionamento interno.
