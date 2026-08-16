# `node.h` — retired in v0.9

`node.h` fu introdotto in v0.5 come proiezione C-style dei digest di sessione. Non indicava Node.js né `node.s`.

PR8 lo aveva mantenuto come compatibility projection perché il contratto 1.5.0 lo richiedeva ancora. Il contratto 1.6.0 rimuove quel requisito: nuove sessioni non lo generano e il completion gate non lo verifica.

Resta soltanto una migrazione one-way: se un vecchio workspace non possiede `session.integrity.json` ma possiede un `node.h` valido rispetto a `state.json`, il runtime può sintetizzare il manifest canonico.
