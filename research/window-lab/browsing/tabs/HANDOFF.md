# Agora viewer tabs: staged, not activated

For Alex: Back and Forward follow each tab's own trail. “Tabs” lists named pages;
New tab, Close and “Open in new tab” keep related pages together. Opening a page
does not choose a chat topic. Web and device pages remain unavailable here.

## Checkpoint and source boundary

Architecture checkpoint was posted on the commission before integration.
`tab_history.py` is the existing typed reducer, moved into notation; its original
window-lab import path remains a compatibility wrapper. `viewer_tabs.py` adapts
it to ordinary in-memory world commands. Native `browse` accepts only the
current actor's home-view record and current-world Agora targets. It never loads
another world, fetches a URL, opens a local file, imports a profile, or calls host
tools. World editing remains subject to the existing permissions; this is not a
new account or security boundary.

The viewer's version-1 JSON `tabs_state` is authoritative: tabs, active key,
per-tab entries, cursor and reducer view data. `viewing`, `with`, `back`,
`location`, `page_name`, `active_tab`, `tab_count`, `can_back`, `can_forward`,
`reading_key` and `reload_seq` are compatible projections. Pins stay as they are.
Named sibling notes (`role=viewer-tab`, `viewer=…`, `tab=…`, `label=…`,
`active=yes/no`, `order=…`, `closed=yes/no`) supply the lens menu. Editing a
projection cannot navigate; the next controller action repairs it.

URLs are canonical `agora://current/item/<appearance>?lens=<name>`. An explicit
URL naming the dispatcher world is accepted and normalized to `current`; other
worlds, unsupported sections, missing/ambiguous targets and invalid lenses
refuse before mutations. `agora://current/lens/<name>` resolves a unique lens
appearance. This deliberately retains the underlying reader's permissions.
HTTP(S)/local/file/javascript targets do not render in tabs. The existing
explicit external-open click for HTTP(S) remains external; no automatic fallback.

`browse` actions: init, open target=…, new [target=…], select tab=…, close
[tab=…], back, forward, reload, lens lens=…, position scroll=… zoom=….
Reload re-evaluates the current world page without pushing history; there is no
network refresh. Going Back then opening a different page truncates Forward.
Closing the final tab leaves one blank tab. Bounds: 100 tabs, 1000 entries per
tab, 1 MiB snapshot. Deleted history targets refuse visibly without losing the
current page. This is per-tab navigation, not a global visited-history log.

Generic `remember "<scope>"` on a frame gives its scrolling descendants a
scope-relative reading identity. The painter stores at most 2000 numeric
positions in `lens-reading:<world>:<person>:<lens>`, separate from drafts.
Positions survive tab changes and browser reloads in that browser only; they
are not a cross-device world sync. Reducer position/zoom round-trip, but no zoom
UI or continuous world position writes are wired. Browser localStorage remains
ordinary viewer continuity, not private/protected storage.

## JEFF apply plan (only after source landing and review)

No script in this folder applies live changes. `stage.py` is an offline planner.
`patches.json` is its exact old/new passages. `originals.json` captures the read
texts; unview is preserved unchanged. Files `home-viewer.lens`, `view.verb`,
`open-found.verb` are staged resulting text, not instructions to overwrite live
text wholesale.

1. Re-read live home-viewer, view, open-found and unview. Save ALL current texts
   and the full viewer props before the first write. Compare each old passage
   in patches.json exactly once. If anything overlaps, stop and rebase the hunk;
   preserve unrelated changes. `stage.prepare(saved_texts, patches)` preflights
   all hunks before returning any replacements; it has no live I/O.
2. Save a list of existing viewer-tab projection notes for that viewer. Ensure
   exactly one home-view for the actor; do not migrate any other actor.
3. In the same reviewed deployment, use the normal read/check-then-door path to
   replace these scoped passages only. Source must already support `browse`
   and `remember`. Keep tiling, dock, search lens, chat routes and styles intact.
   The search result route deliberately now opens the selected tab rather than
   creating an extra tiling column. The open-found three-argument contract stays.
4. As the viewer's actor, read the viewer, then `do browse <viewer> action=init`.
   It migrates existing viewing/with into the first tab exactly once. No props
   on a draft, chat, pin or layout are migrated. Empty/Conversation sentinel
   starts blank. JEFF's identity cannot silently mutate Alex's viewer through
   browse; use only the house's existing deliberately authorized actor path.
5. Run the acceptance journeys below on a copy before applying Alex's state.
   Never send a test message or use the real Conversation for acceptance.

Unview remains the existing “shelve viewer / show chat” operation. It clears the
legacy visible projection but retains the saved tabs. The next deliberate view
resumes the controller and opens the chosen page. It never infers chat About.
Navigation from custom world verbs that still write viewing/with directly must
be reviewed and routed through browse before claiming all entry points covered.
The scoped patch covers root name/deep links via view, pins, search, open-with,
and dock routes that already use view; it doesn't rewrite other owners' routes.

## Reversal

Re-read and save texts again. Preflight all *new* passages, then replace new by
old only (stage.prepare(..., reverse=True)); unrelated edits survive, overlapping
drift refuses. Restore the saved pre-migration viewer props, including their
presence/absence, using ordinary world events. Do not replace the whole current
props map: preserve later unrelated pin/find changes deliberately. Mark only
this deployment's newly created projection notes closed=yes, active=no (do not
delete others' notes). Retain the snapshot as a backup until JEFF accepts
reversal. If necessary undo the recorded init/create/prop events after checking
later edits; never blindly undo a whole shared event range. Remove world usage
of browse/remember before considering a source rollback. No host restart here.

## Acceptance and evidence

RAN: real in-memory desk dispatch and repaint fixtures cover first migration,
idempotence, two tabs, select/close/final blank, serialization, Back/Forward,
branching, lens history, reload/view data, pins unchanged, search/view/deep
links, actual emitted Back action, shelf/resume and unchanged synthetic draft
and explicit context. Negative targets/corrupt snapshots/projections are
exercised. Selector composition retains every native event for undo and no
None event for a no-op. Offline hunks round-trip, preserve outside edits and
refuse overlap. Fake DOM uses the actual Viewer and TextEdit modules to check
per-tab reading continuity, persisted positions, independent draft storage,
the Agora link listener and intentional HTTP external-open.

NOT RUN here: visual, real keyboard, browser composer, narrow viewport or
whole-HUD overflow acceptance. A guarded hidden-desktop screen.py availability
check failed before rendering: first document.readyState Runtime.evaluate in
sandbox_window.open_edge reset the websocket (WinError 10054 /
ConnectionClosedError). No screenshot/facts were produced, no fallback to
Alex's screen, no live state apply or restart. Existing browser keyboard/focus
semantics are reused, not a claim that new browser shortcuts were implemented.

Browser-capable follow-up: at 2560x1440 CSS / scale 1.5 and a smaller 900x700
viewport, open two synthetic long notes, scroll each differently, select/back/
forward/reload and reopen the page; inspect restored positions, named menu,
keyboard activation and no whole-HUD scroll. Keep an unsent synthetic composer
draft and explicit reply/selection context through every repaint; verify no
About is attached by navigation. Check pin/new-tab menu, root deep links, search,
dock shelf/resume, stale/deleted page refusal, 30 long tab names and overflow
menu, deliberate external-open only. Use fake/local fixture content, not
remote accounts, disk files, or the real Conversation.
