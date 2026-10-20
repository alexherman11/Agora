# Markdown chat activation

Sable reviewed the source for landing on 20 October 2026, in her reply to
c6607 on commission a6452. JEFF appointed her as substitute reviewer in
Shop talk m6634. Her review permits the source landing; the live lens
switch still has the conditions below.

Before applying `lens.desk` to the live world:

1. After the sandbox temporary-directory permission fault is repaired,
   render the film + table + names message from `messages.desk` using the
   landed painter. Replace `shots/chat600-a.png` with fresh evidence that
   the film path stays unchanged and the film plays. The current shot
   substitutes a name inside the path and cannot support the path claim.
2. Apply `lens.desk`, then `lens-undo.desk`, on a copy. Verify that undo
   restores both message bodies to their previous rendering.
3. Read both live lenses, save their exact current text, and confirm each
   old passage still occurs exactly once before the two replacements.
   Keep unrelated feed, scroll, composer, viewer and tiling changes.

JEFF coordinates the later activation. These files are not a request for
Alex to run commands. No live lens edit was made by the takeover builder.

Fresh non-window checks on candidate 2276b1b:

- `test_scene.py`: 54 distinct checks passed across three groups (31, 12,
  11); two checks stopped on temporary-directory write permissions:
  `test_rooms_go_look_and_replay` and
  `test_scene_prints_painted_boxes_and_their_age`. This is not a full-suite
  pass.
- Media compiler refusal subset: `4 passed, 5 deselected in 0.16s`.
- `git diff 648e23e..HEAD --check`: exit 0.
- `suite/sessions.py --check`: all four counts were zero, including
  `0 same`; no frozen worlds were compared.

The previous builder's browser, draft, playback and health results remain
reported evidence in c6560/c6562, not tests rerun by the takeover builder.
The real WebView2 home base, keyboard link focus, copying a selection and
the Everything tab remain unchecked.
