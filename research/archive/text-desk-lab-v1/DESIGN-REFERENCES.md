# Design reference received 2026-09-16

Read in full: Alex's attachment
`C:\Users\Alex\.codex\attachments\f32f27ff-8e61-4759-acf4-96562c82caa8\pasted-text.txt`.
Treat it as design input, not a statement that all cited Agora mechanisms exist.
Its descriptions of external systems have not been independently researched here.

## Hypotheses to carry into the experiment

- Start navigation with recognizable visual containment. Follow content identity,
  semantic relationships and history through explicit pivots; do not silently make
  those different relationships indistinguishable children of one tree.
- Give folded nodes short summaries; expand locally while preserving parent and
  sibling context. Test attention allocation, not just larger dumps with more fields.
- Explore stable session-local handles. A handle must not silently retarget after
  sorting, deletion, pagination or refresh. Selection context must be explicit.
- Put applicable verbs close to the selected thing, grounded in the same operation
  registry used for execution. Share implementations, not merely snippets to copy.
- Compare spatial relations with coordinates-on-demand. Preserve exact geometry
  when verification or a precise request needs it.
- Explore an editable outline as a separate write-interface hypothesis, after
  defining omitted, folded, hidden, removed and deleted states unambiguously.

## Reservations to preserve

1. A structured scene is not the same thing as the observed screen. Viewport,
   clipping, occlusion, renderer measurements and transient state need explicit
   provenance/freshness. Persisted events alone do not necessarily capture them.
2. A navigable outline does not require all placement to be a tree. Containment
   can form the outline while freeform spatial relations remain inspectable.
   Constraining layouts is a product choice to test, not an established necessity.
3. One text diff hunk is not necessarily one user decision. A multi-line edit can
   need one atomic operation and undo; a one-line move can have domain consequences.
4. A uniform address syntax does not imply uniform authority, applicability or
   semantics. Moving a task into Done differs from moving a note 40 pixels.
5. Human and model usability should be tested separately. Neither implies the
   other automatically, and no screen-reader-user test has been performed.

## Evidence available when this reference arrived

The context variation had already been implemented and launched. Its results are
not attributed retroactively to this reference:

| Task | Outline | Context | State checks |
|---|---|---|---|
| Meeting | 29 calls, 44.11 s | 13 calls, 28.08 s | Both 10/10 |
| Clarified proposal | 18 calls, 41.17 s | 17 calls, 40.28 s | Both 10/10 |

One run per cell: these observations motivate further trials, not a stable speedup
claim. Short handles, persistent focus, folding budgets and editable-outline writes
have not yet been tested. The context release trial and transfer/repetition tests
also remain outstanding. No live Agora integration or common renderer was built.
