# Extraction evidence and remaining acceptance

Baseline: `0a6b9d273d3d6ecb27abe9cb872bce4c6a39273f`, the incoming main
revision the house merged into this worktree. There are 36 steps:
the branch's original 34 plus `equal`, between `fill` and `widen`, and
`workspace`, between `reply` and `drag` (order 1750).
The existing relative order and every timing budget stay the same.
The house's two conflict blocks in hud_playtest.py were resolved with plain
file edits, keeping the discovered-step runner. The incoming workspace
callback and its two constants moved verbatim into workspace.py; hashes
verify those constants as well as the callback body. No Git merge was
run by the builder.

Ran in the Codex sandbox:

- `test_playtest_steps.py`: **Ran 14 tests; OK**. AST comparisons preserve
  original step bodies, inline assertions and shared helpers. All callbacks
  bind and resolve their globals. The old factories read from the baseline
  commit and the extracted runner give identical registration/results on
  identical stand-ins, including the first-paint result and five selection
  modes. The tests also cover success, assertion failure, dependency skip,
  the scroll compatibility adapter, new-file discovery, order ties,
  duplicate ids and missing exports. The workspace callback also checks
  success and a failure to restore the same panels using stand-ins.
- The merge test makes two sibling commits in a disposable **bare fixture
  repository**, each adding its own step file. `git merge-tree --write-tree`
  succeeds; the resulting tree has both files and the unchanged runner,
  and discovery loads both. This touches no project index, checkout,
  branch or ORIG_HEAD; it is not a merge of the project branches.
- `test_hud_scroll.py`: **Ran 5 tests; OK**. Existing stand-in verdict
  checks; these do not prove browser scrolling.
- `hud_playtest.py --list`: discovers steps without opening a browser.
- `git diff --check`: passed (only Git's CRLF normalization warnings).

Not run here: the real browser playtest before/after, screenshots, real
press timings, wheel behavior or a demo recording. The commission explicitly
excludes a real browser in this Codex sandbox. No project merge was run.

Browser-capable acceptance:

1. Use the same house-provided copied-world snapshot, painter, staging,
   dimensions, scale, assumptions and world-half files for baseline and
   extracted runner. Keep Alex's screen untouched.
2. Run `hud_playtest.py --report none` for baseline revision above and the
   landed extraction. Save each report.json/report.md and its shots.
3. Compare the ordered ids, names, budgets, outcome and skip/missing reasons
   for the same 36 steps. Investigate any new failure; measured milliseconds
   can vary, but the numerical budgets and timing method must match.
4. Check `--only scroll`, `--only open,writing`, and `--list`; confirm
   unselected rows remain "not played" and the wheel alias selects seven.
5. Report the copied world's printed event and artifact paths, explicitly
   separating browser results from the stand-in checks above.

For branches still adding inline callbacks: follow README.md and submit
one `playtest_steps/<unique_name>.py`, rather than restoring the runner's
deleted callback block or order list. Both `equal` and `workspace` have
already been migrated, including the workspace addition from incoming main.
