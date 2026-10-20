# Wheel acceptance handoff (a6549, 20 Oct)

**UNVERIFIED in a real browser.** JEFF applied the live lens fix himself:
home-tiling panel/body receive bounded `share 1` and `scroll scroll`;
the chat feeds use `scroll end`. The old `tiling-fix.desk` is historical,
commented out and must not be applied.

Source ready under JEFF's e12889 instruction:

- `agora_tmp.py`: unique directories made with UUID + `os.makedirs`,
  inheriting their parent's ACL. `AGORA_TMP` is restricted to this worktree;
  default `research/window-lab/.tmp-agora`. Children inherit TMP/TEMP/TMPDIR.
- `screen.py` and `sandbox_window.py`: shared temp allocation and real wheel
  input. The wheel locator does not call `scrollIntoView`.
- `hud_playtest.py --only scroll`: seven reported cases from `hud_scroll.py`,
  using long fixtures in the copied world and actual HUD lenses. Notes,
  Writing, HUD chat, Conversation, At-work feed, board Landed and proposal
  reader; reader skips until a6460 lands (or its source/world half is supplied).
  Each proof requires a received wheel event, a changing panel scroll position
  and matching content rectangle movement, with the page still at zero.
  Missing bounds, clipping, repainting during measurement and lost input fail.
  Before/after shots are saved by the ordinary runner. Failed steps now cause
  a nonzero exit status.

Run in a browser-capable sandbox, from the checkout root:

```
python research/window-lab/hud_playtest.py --only scroll --report none
```

Use the refreshed house copy; `--world` can select another copied world.
For reader work before landing, use the existing `--assume a6460 --apply ...`
workflow. These checks create content only inside the runner's private copy,
including stand-in witnessed feed rows. They do not send to the shared chat.
The board's Landed fold is opened during setup; the following movement proof
uses only wheel input. The board intentionally displays only five landed rows,
so stand-in queued rows make the preceding band long enough to require scrolling.

Ran here, using the pinned interpreter:

- `test_agora_tmp.py`: `temp: child write, parent read, painter copytree,
  inherited TMP/TEMP, Python temp, override: ok`.
- `test_hud_scroll.py`: `Ran 5 tests`, `OK`. These use stand-in measurements,
  including clipping, page movement, missing wheel and scrollbar-only movement.
  They verify the verdict logic, **not browser behavior**.
- `hud_playtest.py --list`: lists seven scroll checks as UNVERIFIED.
- Python syntax parsing and `git diff --check` pass.

Earlier actual Edge attempt reached DevTools but its first
`Runtime.evaluate(document.readyState)` reset the websocket with WinError 10054 /
ConnectionClosedError. A subsequent HTTP version request was refused (10061).
Adding `--remote-allow-origins=*` did not help and is not retained. The clients
explicitly send no Origin header. Pipe transport was considered, not implemented.
The owned sandbox was closed. No readyState value, painter facts, shots,
recording, guard acceptance or wheel movement was obtained. Full health was not
rerun: it includes browser checks that this environment cannot complete.

`chain.js` and `clipped.js` are preserved diagnostic drafts, not acceptance
evidence. The next worker must run the real checks, inspect every before/after
shot, then update the card and remove the pending-landing qualifier in the
Handbook's Running it paragraph once the source actually lands.
