# `node.h` — proiezione legacy di compatibilità

`node.h` **non indica Node.js e non è un refuso per `node.s`**. Il nome fu introdotto nella linea v0.5 come metafora di un “header” di integrità e il file usa effettivamente direttive `#define` in stile C.

Da runtime v0.8 il record canonico è [`session.integrity.json`](SESSION_INTEGRITY_MANIFEST.md). `node.h` viene ancora generato perché il contratto di accesso 1.5.0 lo nomina esplicitamente e perché possono esistere workspace/integrations legacy.

Status: **DEPRECATED_COMPATIBILITY**.

La proiezione contiene soltanto metadata e digest, mai testo del corpus. Il gate verifica sia il manifest JSON canonico sia `node.h`; la rimozione definitiva del legacy file richiederà una futura revisione del contratto.

Per la ricostruzione storica della decisione vedi [`HISTORIOGRAPHIC_AUDIT_V8.md`](HISTORIOGRAPHIC_AUDIT_V8.md).
