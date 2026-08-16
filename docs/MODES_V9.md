# Juriscribe v0.9 — three work modes

`CONTINUATION`, `GREENFIELD` e `REVIEW` sono modalità semantiche, non etichette UI. Il `mode_contract` decide input, gate e artefatti obbligatori.

## CONTINUATION
Richiede seed precedente, generation contract e continuation frontier/coverage. Output primario: `final_chapter`.

## GREENFIELD
Richiede concept/mandato, non capitoli precedenti. Concept e prompt sono materiale di progetto, non fonti giuridiche. Output primario: `final_legal_text`.

## REVIEW
Richiede un `review_target`. `REPORT_ONLY` consegna un audit completo anche se il target contiene blocker. `REPORT_AND_REVISED_TEXT` richiede una revisione causalmente legata ai finding e una nuova review sul testo modificato.

## Invarianti comuni
Reticolo, mode-aware setup, standard editoriale, DoD, fonti/inferenze, provenance, final severe review, M+10.000 e readback restano trasversali.
