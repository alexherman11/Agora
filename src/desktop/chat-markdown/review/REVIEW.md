# Markdown chat body: guarded acceptance (a7629)

21 October 2026, worker-a7629 (builder-2, taking over builder-1's c7669 start). For JEFF: recommend the scoped body
apply of a7610, with one known table defect and one pre-existing repaint stall named below.

## What was reviewed

- Source at HEAD 82c133e (main, fast-forwarded). a7557's markdown.js, media.js, textedit.js and slice1/ are byte-identical
  to its landing 3e3c67c; lens.js has later edits (tiling dividers, partitions, a7544 float placement), none in the
  Markdown paths.
- sha256 at the run: lens.js A49A71D1…5FDC30, markdown.js AA791099…72D38, media.js 167AB005…B1ADA, textedit.js
  A6F912EE…554E3, stage.py 2C706F28…78ABAB, patches.md 830B0565…AFCF8D (full values in each run's
  report.json, `facts.sources`).
- The copy's lenses before apply: jeff-chat a5210 BCCDC49C…CDCF0F3F, conversation a5086 1D9B8E57…72C8BC6.
- a7610's passages = slice1/stage.py PATCHES.

## How (ran)

`python src/desktop/chat-markdown/review/accept.py [--small] [--only …] [--no-apply]`: a disposable copy
(hud_playtest.Copy, its own door), hidden-desktop Edge (Window(False)) with the guard. Both OLD passages preflighted
(each found exactly once) before either write, applied by `do replace`, read back equal to stage.prepare(), reversed
NEW→OLD at the end and read back equal to the original text. Fixtures go to a disposable chat in the copy (with=alex);
no line or comment reached the copy's Conversation. Copy events are caught in the page and cancelled (system clipboard
untouched); the host bridge is a recording stand-in; window.open is recorded, never called; the film is muted.

Runs (shots and report.json/report.md under `C:/Projects/Agora4/src/desktop/demos/chat-markdown-review/`):

| run | size, DPR | result |
|---|---|---|
| 2026-10-21-162602-2560x1440 | 2560x1440 CSS, DPR 1.5 | 14 pass, fallback fail (see stall) |
| 2026-10-21-162903-2560x1440 | same, `--only fallback` | pass |
| 2026-10-21-162931-1280x800 | 1280x800 CSS, DPR 1.5 | 14 pass, fallback fail (same stall) |
| 2026-10-21-163216-1280x800 | reply-hud, reply-conversation, fallback | all pass |
| 2026-10-21-163359-1280x800 | keyboard … draft journeys, fallback | all pass |
| 2026-10-21-163500 / 163852-1280x800 | formats, full-hud, widths, then fallback | fallback fail, reproduced |
| 2026-10-21-164049-1280x800-baseline | same order, passages NOT applied | fallback fail too: pre-existing |

Every guard: `(0, 'alex: untouched by the sandbox …')`.

## Per journey (both sizes unless said)

- formats-jeff-chat, formats-conversation: pass. h1 1, h2 1, bullets/tasks 4, numbered 2, nested 1, quote, rule; task
  boxes aria-disabled true; named link (md-wl) and explicit link focusable; javascript: link inert; one picture, one
  film, Pop out present; no script kept or run.
- full-hud: pass at 2560x1440 and 1280x800; no page scroll; chat document contained.
- widths 320/420/600 (both lenses): pass by measurement (doc and table widget scrollWidth = clientWidth, code wraps).
  **But see the table defect: the widget never scrolls, it squeezes.**
- keyboard-link: pass. Tab reaches the named link, Enter opens it with `view` (home-view shows a5202), no About added.
- selection-copy: pass. A pointer drag across words and the named link selected 62 chars, Ctrl+C gave the same words
  (caught); a drag inside the link's words did not follow it.
- inert-task: pass. A real click on a sent task box adds no event.
- media: pass. The film plays (t 0.1 → 1.6 s, muted); Pop out asks the host (stand-in) for a media-player window.
- draft-update (HUD and jeff-chat): pass. Same textarea, words, caret 13 of 19, focus and the removable About chip
  through an incoming Markdown message, which is shown.
- reply-hud, reply-conversation: pass. Answer aims the draft at the disposable chat before Enter; Reply here appends
  there.
- fallback: pass when run fresh. Malformed Markdown draws readable; an injected renderer failure shows the plain-text
  fallback with the film beside it and a working composer; no xss.
- apply-undo: pass every run.

## Findings

1. **Table squeezes instead of scrolling (source, a7557 owner).** Looked at 01-formats-jeff-chat.png (2560 run): a
   table with one wide cell wraps the wide column and crushes the narrow one to a letter per line ("N a m e",
   "fix tu re"). The widget has overflow-x auto but its table is never wider than it, so the "contained overflow"
   promise holds only by making the table unreadable. Likely fix: cells get a minimum width (e.g. `min-width` on
   th/td, or `white-space: nowrap` on short headings) so the table can grow and the widget scrolls. Not a reason to
   withhold the body apply in my view (imagined: today's `marks` body has no table at all, so nothing readable is lost),
   but JEFF may prefer to fix it first.
2. **Pre-existing repaint stall after many page loads (not this change).** After formats + full-hud + widths (9 page
   loads of pages holding the film) a new jeff-chat page paints nothing new: its 1.5 s scene polls and a fresh
   `/api/scene` fetch from the page wait >5 s, while the same URL from Python answers in 0.15–0.22 s, and the page's
   film sits at networkState LOADING, readyState 0. Same on the unpatched lenses (baseline run). Imagined cause: the
   browser's per-host connection pool held by stalled media loads; `refresh()` chains on the previous fetch with no
   timeout, so one stuck fetch freezes every later repaint. Matters little for the HUD (one long-lived page), may matter
   for a browser tab revisited many times. For the painter/media owner; not verified beyond these runs.

## Not checked

Real pywebview host (stand-in only), the system clipboard, a real Pop out window, Alex's live HUD, screen readers. The
table defect was found by eye after the harness passed it; the widths journey measures containment, not readability.
