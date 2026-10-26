# Seabright polish — builder draft for Claude

26 October 2026. No git commands or lens.js edits. No board window opened.
This records the implementation and its evidence for coordinator review.

## Additions first

- Kernel `shown`: reader-only `you_liked` and `your_vote`; sealed keys remain
  absent. No new kernel word.
- Painter: compact relative/calendar date formats, letters-only initials,
  `api.format(setting,value,fallback)`, viewer metadata on every part,
  `P.parseDateEntry`, `P.selectionAction`, and successful local selection before
  repaint through `api.fire(...,{select:{...}})`. Catalogue date tile (with its
  own reusable skin) and enhanced poll/slots/file/field-list handles. Document
  `pageTarget`/`pageRequest` address already-open readers; `owner` prevents late
  description controls moving the footer. See UI-HANDLES.md and ARRANGEMENT.md.
- General widget title fix in the native provider and trusted page/slot titles.
- Board module: RSVP status changes retain one claim; document page hits carry
  their owning thread/file; decisions retain their leader.
- Kernel enumeration and displayed rows take shallow snapshots across concurrent
  module updates. Reaction lookup avoids resolving empty reaction collections.
- Board shell `extras=feed` retains healthy column layout beside an extra failed
  sibling; `alongside` is available. Summary state follows channel/seen context.
- Proof driver: services both hidden browsers, checks unchanged frame timeOrigin,
  handles Chromium's alternate detached-session wording. Painter replay compares
  both snapshots under the writer lock. Capture writes publish atomically; the
  driver waits for attachment loading and position before capture. No assertions
  were weakened.
- Every source seam is recorded in painter/ROUGH-SPOTS.md.

## Requested changes

1. Slim Seabright/search/compose bar; banner, logo and sidebar blurb removed.
2. General human widget titles, without Widget prefix.
3. Conditional reading pane, minimum 520px/45%; below 1100px it replaces feed.
4. One vertical scroll per column; document and thread descendants do not scroll.
5. Channel unread counts; separated Saved and scoped leader queue with count.
   Both destinations are also in a separate group in the compact phone picker;
   returning to a channel leaves the bookmark filter.
6. One-line identity, role, channel and relative stamp; accented icon kind chip.
7. Letters-only initials through format, including Neighbour 02 → N.
8. Compact cards, bold supplied titles, three-line excerpts, replies/activity footer.
   Desktop catch-up previews share a compact row so the feed stays prominent.
9. One Reply; quote only on selection plus More fallback; zero count omitted;
   own upvote is labelled and pressed. History uses human activity/text.
   Explicit quoting consumes its selection. A hidden phone thread retains the
   reason and Undo inside its reading pane, without a reply form.
10. Photo filename hidden, bounded rounded image, full-size cleaned Blob viewer;
    description editing is behind a disclosure and available only to its poster.
11. General date tile, local time range/place, attendance/counts, RSVP toggle,
    quiet calendar action; countdown only in the near-future window.
12. Open polls have large buttons; after vote/close, bars, percentages/counts and
    reader-only choice mark. Option spelling is preserved.
13. General slot meter and remaining/total, primary claim; no action when full/closed.
14. Amber Needs an answer / green Answered; marked answer body/preview.
15. Decision banner first in its thread, leader/date, Decided preview in feed.
16. Pinned marker, subtle announcement band and optional until date.
17. Document icon/title/page count/text preview; comfortable page reader and picker.
18. Catch-up grouped by thread with one icon per category, count/since heading,
    rows that open threads, Mark all seen. Preview count is a setting.
19. Summarise only when service is up and selected model installed; separate heading.
20. Phone catch-up starts as one expandable line.
21. Kind choice first, friendly tiles from world declarations, including new kinds.
22. Only that kind's fields, human labels, advanced fields in More options;
    current channel is the default.
23. Drop zone, previews and remove controls; native file input is hidden.
24. Local friendly typed dates plus native picker, with visible interpretation.
    Parser deliberately accepts a small English grammar and ISO local date/time.
25. Search title/snippet/highlight, channel/type/person/date; named page hits open
    their thread and addressed initial page.
26. Live filter chips, date presets and a labelled custom date picker; no Apply.
27. Compact phone top row, visible first post, small order control, full-screen
    thread/back, floating compose with a reserved bottom strip. Saved and the
    admitted leader queue are reachable through that same compact picker.
28. Relative dates use format handles; generic dates also have date format handles.
29. Sentence case labels and human history; no implementation metadata in cards.
30. Darkened semantic text tokens; explicit WCAG AA ratio assertions over catch-up,
    action and muted text. Full slots omit the disabled action.

No numbered item was intentionally deferred. The reach boundaries are the small
English date grammar, extracted PDF text rather than original PDF graphics,
fixed CSS responsive breakpoints (documented as such), admitted catch-up rows
bounded to 100, and no physical phone or screen-reader audit. No calendar, map,
notifications, or new model trial was added.

## Proof and visual review

**Ran**, final source: `POLISH-RELEASE.txt` prints:

```
BOARD UI: 104/104 checks passed; hidden=True; screenshots=53
BOARD UI SPEED {"cold_start_to_board_ms": 2172.02, "feed_threads": 331, "first_paint_upper_bound_ms": 1700.57, "max_feed_cards": 12, "pages_scrolled": 28, "scroll_all_posts_ms": 63285.86}
```

First paint is an upper bound from navigation to a verified board raster, not
browser FCP. Scroll traverses all 28 pages with at most twelve feed cards; this
is substantially slower than the original handoff's 11818.97 ms run. The driver
now services both browsers during waits; the full cause of the timing difference
has not been isolated. No performance improvement is claimed.

The final UI log includes a Pillow deprecation warning that PowerShell labels
`NativeCommandError` (the wrapper reports exit 1). The Python proof completed
and printed 104/104; `ui-proof.json` has all 104 checks true and 53 screenshots.
No assertion or Python traceback failed in that run.

**Ran**, regression evidence:

- `POLISH-HIDDEN-TESTS.txt`: `156 passed, 2 deselected, 63 subtests passed in 331.61s (0:05:31)`.
- `POLISH-NATIVE-RECHECK.txt`: the two gated native tests, `2 passed in 17.45s`.
- Earlier combined run, `POLISH-SUITE-VERIFIED.txt`: `158 passed, 63 subtests passed in 294.07s (0:04:54)`.
  These cover kernel-lab, board contracts/transport/polish, and kernel-desktop.
- After the final general component changes, `POLISH-FINAL-BOARD-TESTS.txt`:
  `18 passed in 10.44s`.
- `POLISH-FINAL-PROOFS.txt` and `regressions/`: all five subprocesses exit 0;
  contract 11/11, purpose 9/9, isolation 18/18, painter 28/28, widgets 23/23.
- `POLISH-FINAL-GENERAL.txt`: `POLISH ACTIONS: 7/7 checks passed; hidden=True`.
- `POLISH-HANDLE-TESTS.txt`: `7 passed in 7.45s`; `POLISH DATES: 12/12 checks passed; local=True; model=False`.

Candidate failures remain in POLISH-UI*.txt and related logs. They exposed
dialog-selection ordering, RSVP refresh timing, peer CDP servicing, concurrent
dictionary enumeration and async capture readiness; final checks retain their
assertions. The latest phone navigation change is covered by the 104-check UI
run. Broad Python and generic painter suites preceded that small board-only
navigation change.

Before images were preserved before any retake under evidence/ui/polish/.
Final screenshots retain the original 53 names under evidence/ui/; before/after
pairs cover feed, event, poll, compose and search at both widths.
`evidence/ui/polish/index.html` presents the ten pairs. All 53 final rasters were
opened and reviewed, including byte-identical rechecks after the final retake;
all ten preserved before images and three extra component/chooser images were
also opened. `visual-review.json` and `capture-manifest.json` bind the review to
the exact final PNG hashes.

## Live adoption: pending, no live mutation

**Ran**, gate: an earlier game blocked the requested five-minute polling; it
cleared at 23:10 UTC. A later full-screen app blocked 23:42 and 23:47 UTC polls;
the gate cleared at 23:52 UTC. Nothing was raised or activated while blocked.

The explicit installer attempt at 23:52 UTC stopped before any mutation or
restart: the live window provider had changed from off/eight window records to
on/nine records, including a Seabright board record. The board feed was still
empty and 26 existing tasks remained. A read-only projection at 23:53 UTC
confirmed that the running compiler lacks the new viewer/format contract.

Restarting that runtime would recreate active desktop windows, conflicting with
the user's hidden-only constraint. No kernel restart, board opening, seed post,
or definition/style/component mutation was performed. Do not call this installed
or live verified. `POLISH-LIVE-INSTALL.txt`, `POLISH-RUNTIME-INSPECT.txt` and
`evidence/ui/polish/live-pending.json` record the boundary. `polish_live.py --live`
is ready to adopt after the coordinator arranges a hidden runtime restart; it
refuses active window providers and nonempty boards and verifies preserved
tasks/history/windows/provider state after adoption.

The standing charter read was attempted first through the documented Desk
entrypoint and returned acknowledgement unavailable. Supplied AGENTS.md rules
were followed; no session pickle or exported transcript was inspected.
