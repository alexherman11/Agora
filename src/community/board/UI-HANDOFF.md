# Seabright interface handoff

Polish follow-up for Claude: [POLISH-HANDOFF.md](POLISH-HANDOFF.md) records the
current source, 104-check UI proof, final screenshots and new handles. Its live
adoption remains pending because the active desktop cannot be restarted under
the hidden-only constraint. The original handoff below is preserved as history.

Builder draft, 26 October 2026. Claude owns review, polish and commit. No git
commands were run by this builder, and `lens.js` was not edited.

## Kernel and painter additions first

**Read / implemented:** three small kernel changes in `kernel/words.py`:
ordinary `look` rows include `rev`; reserved `via_actor` retains authenticated
agent provenance through module wrappers; `vote` accepts an option in its
declared case, with a unique case-insensitive fallback. No new kernel word.
The corresponding missing world capabilities are recorded in painter
[ROUGH-SPOTS.md](../../agora/painter/ROUGH-SPOTS.md).

**Read / implemented:** admitted reading collections, reading watchers,
construction pagination, structured JSON settings, personal opening view
defaults, UI label maps, numeric/font theme tokens, local selections/drafts,
authored structured form fields and child settings. `look-view` remains a
compact structural reading; `plan=yes` exposes the full projection. Module
readings run outside the kernel lock as the viewer's widget principal.

**Read / implemented:** trusted file transport and downloads. The parent first
checks `file-read` with that viewer's widget grants, then fetches the exact
same-origin `/files/<thing>` route with its own cookie, no-store and no
redirects. Only a Blob crosses into the component. Generation disposal revokes
object URLs. The component receives no route, session, token or network API.
`connect-src 'none'` is unchanged; images retain `data: blob:`; media changes
from none to **exactly `blob:`**. Native downloads use a one-use, expiring
registration from the exact trusted top page for its Blob URL. Global native
downloads remain disabled. The native save dialog is reached only by an
explicit download action; the hidden proof substitutes a scratch destination.

The parent now queues bounded bridge bursts instead of silently losing calls,
paces component calls below the existing rate cap, and can hide technical
receipts for this board. `P.submit` supplies validated local pointer/keyboard
actions within the existing no-forms sandbox. Selection survives reconstruction
only while its complete source text is unchanged. Stale stopped attachments
retain text with a reopen explanation instead of a revoked preview URL.

## Arrangement and components

**Read / implemented:** [board.lens](board.lens) arranges catalogue `column`,
`markdown` and sortable `table`, with catalogue avatar/primitive controls.
New general catalogue components are `poll`, `slots`, `file` and `field-list`.
They live in `src/agora/components/` and have discoverable schema,
parts, settings, gestures, examples and limitations. `slots.label` identifies
independent volunteer slots. File content is a structured reading binding;
feed cards use cleaned thumbnails, threads use cleaned full content.

Eleven board components provide the shell, navigation, toolbar, catch-up,
reading entry, paged feed, post, thread, hide notice, search/queue and composer.
World declarations supply kinds, fields/order, field labels/types, channels,
orderings, kind accent tokens, roles and UI strings. Personal view/style handles
apply the same changes for one viewer. [UI-HANDLES.md](UI-HANDLES.md) is installed
as a world guide. Theme colours, measures, radii and type are world tokens.

The interface supplies the requested feed/orderings, explicit Mark seen,
post-kind states, two reply levels, exact post/page quotes, answer/decision,
upvotes, personal actions, why-here/history, leader hide/undo/report queue,
adaptive composer/upload/attach, file readers, search filters and identities.
Board readings now exclude unrelated surfaces' posts; badges expose only the
visible leadership scope needed by allowed controls. Calendar filenames use
human event titles. Calendar export remains a download, with no calendar page,
map, notifications or cross-surface routing.

## Proof

**Ran:** pinned Python, hidden scratch worlds and hidden Chromium only. The
native file proof uses never-shown WebView2. Nothing in these proofs installs
or opens the live board.

- `UI-REVIEW-FINAL.txt`: **BOARD UI: 86/86 checks passed; hidden=True; screenshots=53**.
- The seed runs the original board proof over **32 people (30 neighbours,
  2 leaders), 409 posts, 82 replies, 14 days** and its actual upload fixtures.
- Pointer/keyboard actions are confirmed through world readings: post,
  reply, selected quotation, upvote, RSVP, last slot, vote, photo/PDF upload
  and attachment, leader hide/undo, Mark seen. A second person's existing
  page receives a post without reloading. Imported ICS RSVP/download and
  Blob audio metadata are also exercised.
- Broken poll, throwing file and a new infinite-loop component each stop
  independently. Compose, upvote and another person's updates keep working.
- Private group post/file/thumbnail never enter an outsider's component page;
  both file transport variants refuse access. Owner content/thumbnail positive
  controls pass. Direct component networking remains blocked.
- `ui-native-files2.txt`: **NATIVE FILE: 9/9 checks passed; hidden=True**.
  This includes cleaned file decode, thumbnail, no component cookie,
  connect-none, opaque download refusal, actual native cleaned download and
  native calendar download, with global download settings unchanged.
- `UI-REVIEW-REGRESSIONS.txt`: all five required proof processes exit **0**:
  contract **11 of 11**, purpose **9 of 9**, isolation/handles **18 of 18**,
  painter **28 of 28**, widgets **23 of 23**.
- `UI-REVIEW-SUITE.txt`, combined agora, board contracts/transport and
  kernel-desktop suite: **148 passed, 47 subtests passed in 283.93s (0:04:43)**.
- Original real-model proof: `ui-board-final-proof.txt`, **62 checks**, one
  labelled `qwen3.5:9b` summary attempt completed. The final UI run uses the
  explicit offline-model response and verifies its private summary context;
  opening/polling a board never invokes a model.

**Ran, as printed in the final UI run:**

```json
{"cold_start_to_board_ms":2084.38,"feed_threads":331,"first_paint_upper_bound_ms":1342.87,"max_feed_cards":12,"pages_scrolled":28,"scroll_all_posts_ms":11818.97}
```

First paint is a verified board-raster **upper bound from navigation**, not an
exact browser FCP entry: this opaque-frame harness did not expose one. Cold
start additionally includes starting hidden Chromium. Scroll traverses all
28 pages/331 feed threads from the 409-post seed, with at most 12 feed cards.
The broad suite ran concurrently, so these are this machine/run's timings.

**Read / looked:** all **53 final PNGs** under [evidence/ui/](evidence/ui/)
were opened and visually inspected. The set covers each requested scene at
1440x900 and 390x844, plus the first verified paint. Corrections after review:
wait for actual photo decode, reserve image space, name independent slots,
start the CSV view at column headings, show the quoted reply in the quote
screenshot, and give phone search filters their own rows.

Earlier failed candidate runs remain in this folder. They exposed the bridge
backpressure issue, blocked native sandbox form submission, stale gesture
fences and quote reconstruction. One earlier painter replay snapshot raced;
`ui-painter-replay-recheck.txt` and the subsequent full proof both passed.
No failure evidence was removed.

## Live adoption

**Ran:** `gaming_gate.py` reported **Gaming gate: clear** before adoption. The
separate installer also checked games/full-screen foreground apps before every
restart and mutation, with no blocked step. It restarted the single canonical
kdesk process tree to adopt the source, then installed the world definitions,
catalogue/app components, lens, theme, guide, widget and dock entry.

`UI-LIVE-INSTALL.txt` and [live-install.json](evidence/ui/live-install.json)
record **6 channels, 5 orderings, 0 feed posts, 0 seeded posts, opened=false**.
The world's total kind count is 12 (including its pre-existing kinds).
All **26 existing task facts and their histories**, **8 window facts**, and
the existing **window provider off** state compare equal before/after.
Installed widget source exactly matches the repository-generated source;
the running kernel's `look` revision was verified. No board window was opened.
The provider remains off for Claude to resume/open after review; the dock
entry is installed as a world fact, not a claim that a visible dock was tested.

## Remaining boundaries

- PDF extracted-text pages, search, exact page quotes and original download
  work. Original page graphics are unavailable without an installed renderer;
  none was installed in this job.
- Physical phones, a screen reader, and a complete human Spanish translation
  have not been audited. The labels handle is available; it is not a claim that
  every domain value has been translated. The frozen fresh-agent tweak trial
  and Claude's polish review are still to follow.
- The board is deliberately unopened live; installation evidence cannot prove
  its first live paint. Hidden native file tests do not prove public hosting.
- The standing charter read was attempted first through the documented Desk
  entrypoint; the door acknowledgement was unavailable. The supplied AGENTS
  rules were followed. No pickle or exported transcript was inspected.
- No calendar page, map, notifications, digest or cross-surface gathering was
  built. These remain the stated separate design work.
