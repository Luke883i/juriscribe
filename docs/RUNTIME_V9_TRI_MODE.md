# Runtime v0.9 tri-mode

La v0.9 generalizza il kernel dopo la fase continuation-only v0.1–v0.8.

Nuovi first-class state: `mode`, `mode_selection`, `mode_contract`, `editorial_standard`.

Il completion gate è mode-aware. Non esegue continuation coverage in greenfield/review; non impone simulation/compression a una review diagnostica; non confonde finding aperti con fallimento della review.

`session.integrity.json` lega modalità e standard editoriale. `node.h` non è più prodotto né richiesto ed è soltanto una sorgente di migrazione per workspace storici.
