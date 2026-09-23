# Selection before implementation — 2026-09-16

Source: Alex's supplied 639-line placement/inspection transcript, read in full.
This is a selection from that work, not a new architecture proposal.

## Assessment

- Supported in the earlier example-world trials: content/occurrence separation,
  pure planning, atomic placement, compensation preserving later content, and
  the need to distinguish committed state from rendered observations.
- Promising and underexplored: reuse of the **installed** board action and Notes
  renderer, two windows sharing one arrangement with independent cameras, shared
  gesture mechanics, and bounded structured inspection derived from real state.
- Overstated: "parity for free"; appearance objects automatically solving layout
  ownership; shared rectangles implying shared semantics; a successful layout
  proving a reusable application framework. These implications are unsupported.
- Uncertain: the common descriptor for custom nested regions; general reference
  grants/transfers; maintained-layout ownership across applications; how much
  adapter code is actually small. Do not invent these contracts during this slice.

## Selected experiment and fixed scope

The transcript explicitly recommends independent occurrence IDs and adapting the
existing board layout action. Inspection of the current installed packages found:

- `studio.boards` source revision 2 / installation revision 2. Its `layout` already
  addresses embedded `item.id`, and schema already separates `id` from `note_id`.
- Its `add_note` prohibits duplicate subjects. Its `remove_note` removes by subject.
- `agora.notes` source revision 10 / installation revision 7. Its renderer and
  drafts are keyed by `note_id`, collapsing independent occurrences.
- `agora.shell` source revision 44 / installation revision 39 already forwards
  the existing board actions with current installation revision and subject scope.

Implement only the documented distinction using these existing paths:

1. Optional explicit `occurrence_id` in add/remove; omitted add keeps old deduplication.
2. Old records retain their IDs. No universal appearance objects or data migration.
3. Ambiguous subject-only removal refuses; explicit removal affects one occurrence.
4. Notes keys cards/drafts/placement reconciliation by occurrence ID, while content
   reads/edits continue to target the shared note. Existing IDs preserve old drafts.
5. The existing Add existing control can explicitly add another appearance.

Baseline scope is an **installed-package slice with synthetic board data**, not
a clone of Alex's complete active world. All installed package sources/builds and
schemas are pinned from a coherent read-only snapshot. The two arms share that
inventory; only board action code/schema and Notes occurrence handling differ.
Do not claim preservation of the person's full active arrangement or runtime.

Observed installation prerequisite: the installed Notes manifest declares an older
`text.annotations` schema than the captured world. The latter adds an optional
`tracking` property. The first candidate install correctly refused. The next
candidate reuses the captured current schema in its manifest, after asserting
that removing that one optional property exactly reproduces the old declaration.
No stored schema, annotation data, or native compatibility check is changed.
This compatibility alignment is an additional explicit candidate delta.

Acceptance: baseline duplicate refusal; candidate duplicate rendered separately;
move one occurrence through the existing action and keyboard path; shared text;
independent arrangement; two windows on one arrangement with independent camera;
single-occurrence removal; stale batch refusal without partial writes; replay.
Use real guest execution and browser observations, and a bounded actual JEFF
capability trial. Retain exact sources and results. Do not deploy to the live world.

## Stop boundary

If this requires a new reference-access system, nested-surface protocol, shared
dependency resolver, or storage/authority model, stop implementation and prepare
a concrete question for Alex's ideation agent. Do not broaden this slice to build
structured inspect, a generic transfer framework, or a new layout engine.
