# Runtime v0.9 tri-mode

La v0.9 generalizza il kernel dopo la fase continuation-only v0.1–v0.8.

Nuovi first-class state: `mode`, `mode_selection`, `mode_contract`, `editorial_standard`.

Il completion gate è mode-aware. Non esegue continuation coverage in greenfield/review; non impone simulation/compression a una review diagnostica; non confonde finding aperti con fallimento della review.

`session.integrity.json` lega modalità e standard editoriale. `node.h` non è più prodotto né richiesto ed è soltanto una sorgente di migrazione per workspace storici.

## Patch di delivery

- v0.9.1 ha ripristinato DOCX, dashboard obbligatoria, esclusione dei record macchina e chat finale breve;
- v0.9.2 verifica la materializzazione reale OOXML, lega la dashboard allo stato corrente e rende artifact-first/autonomia silenziosa un vincolo dell'intera superficie post-bootstrap e del contratto 1.7.0.

Le patch non introducono una quarta modalità e non alterano il significato scientifico delle tre modalità canoniche.
