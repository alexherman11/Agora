# Comment margin review — blocked before rendering

21 October 2026 · worker-a8030 · commission a8030

**Not accepted.** JEFF's candidate remains a world-only proposal. No live lens,
style, document, comment or writer state was changed. No product source changed.

## Ran

From this worktree:

```powershell
& C:/Projects/Agora4/.venv/Scripts/python.exe src/desktop/comment-margin-review/review.py
```

The driver made its own disposable copy using the existing playtest helper.
Preflight found both exact margin blocks once:

- Copy: `frontier-try-playtest-86136`
- World event total: **17238**
- Lens: `a6079` (`doc-page`)
- Original lens SHA256:
  `74cdb629ed55b362503d838f878d175cf4175cb9eb4ad070c0f530b46015b00e`

Requested viewport: 2560×1440, scale 1.5. Actual CSS viewport and DPR were
**not measured** because the browser failed before the first page evaluation.

The command exited 1, printing:

```text
guard over a start that failed (no page was tested, so this is not an acceptance verdict): alex: untouched by the sandbox (foreground, focus, cursor and input desktop polled every 20 ms: no sandbox window became his foreground, none showed on his desktop, the input desktop stayed Default, the cursor never moved without real input)
edge started on the sandbox desktop but failed at document.readyState: ConnectionClosedError: no close frame received or sent; edge pid 88136 running, its DevTools port no longer answered (URLError); this sandbox was closed (a cleanup, not a tested page)
```

The helper closed its sandbox and the driver closed its owned copy. No candidate
replacement command ran. There are no before/after screenshots or measured
paragraph positions. No 1280×800 retry was attempted: the failure preceded page
testing, and JEFF explicitly accepted this blocker and prohibited an identical
retry (card c8103).

## Read

- JEFF's candidate note `a8028`; current `doc-page` lens `a6079` and `review`
  style `a4200`.
- Prior margin work `a4687` and `doc-editor` lens `a3417`.
- Existing painter `lens.js`: its afloat layout measures group height, packs
  groups by horizontal column in DOM order, and translates later groups past
  preceding groups with an 8px gap. This supports the proposed mechanism in
  principle; it does not prove this candidate renders correctly.
- Existing `viewer.js` `recoverLayout`: it can preserve uniquely matched draft
  fields across wrapper key changes using stable item/key suffixes and fences.
  It refuses ambiguous/pending recovery and asks for review after recovery.
  Thus wrapper changes do not establish draft loss. Caret, pending writes,
  ambiguous fields and actual reply continuity remain unverified.

## Exact staged payload and reversal

`patches.json` contains both full OLD/NEW pairs and their exact inverses. Keep
the margin's existing `share 1` and `role aside`; add one `notes : column` with
`role beside`, enclosing both Talk and legacy-comment branches. No style or
document edit is proposed.

Before application, re-read the current lens and require each OLD passage to
occur exactly once. If it differs, stop and review the new passage. Reversal is
each corresponding NEW → OLD replacement, with the same fresh preflight.
These are **unaccepted candidate hunks**, not an instruction to apply live.

`review.py` stages a copy-only initial before/after capture. Its browser steps
and measurement selectors remain unvalidated; it is not the complete
interaction acceptance suite.

## Remaining acceptance gate

A demonstrated browser-capable guarded runtime must render a fresh current-world
copy at both requested sizes. It must:

- Capture before/after paragraph positions around the reported gap and show
  main-text spacing independent of note height.
- Show all adjacent Talk and legacy notes without overlap or loss, including
  scrolling to the final note.
- Exercise expand/reply/resolve on disposable fixtures only, plus keyboard,
  selection/caret, unsent reply and composer continuity through repaint.
- Check Markdown documents and narrow-layout behavior.
- Record actual viewport/DPR, Guard result, screenshots and measured positions.

No compilation, source inspection or successful preflight closes that gate.
No account action, Conversation send, Alex-screen input/capture, restart,
installation or live world apply occurred in this review.
