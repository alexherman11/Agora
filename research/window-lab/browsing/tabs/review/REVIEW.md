# Viewer tabs: guarded acceptance of 3cc2796 + staged a7439/a7441 (a7544, for a7319)

worker-a7544 (builder-2), 20 Oct 2026. This is acceptance only. The reviewed source was not changed and nothing was applied live.

## Verdict

**Do not apply the staged bytes as they stand.** Three defects would meet Alex on first use. Each has a small world-level fix (one also needs a source change), so they belong in the patch before JEFF applies it:

1. The Tabs menu has no background.
2. The board and notices bypass the tabs, so Back goes to the wrong page.
3. Tab notes appear in search beside the real pages.

The core works in the real hidden Edge at 2560x1440 (CSS, DPR 1.5): migration, per-tab Back/Forward/branch/lens, reading position, the menus, keyboard, refusals, unview and resume, and the draft. Web, device and file browsing are still unavailable, which is correct.

## What was reviewed (ran)

- **Source:** main c429747 (contains 3cc2796). `test_viewer_tabs.py`: 10 tests OK.
- **SHA-256:**

  | file | hash |
  |---|---|
  | tab_history.py | 69C55E1C… |
  | viewer_tabs.py | 95AB13AF… |
  | viewer.js | F899DD0E… |
  | lens.js | 168395CB… |
  | textedit.js | 745F6C83… |
  | moo.py | 2BDB5D40… |
  | desk_moo.py | 6CBCBD18… |
  | scene.py | 35A89CEC… |
  | lens_ir.py | 48D08EAA… |
  | patches.json | D716135D… |
  | originals.json | DB379801… |

  The full hashes are in each report.json (`python tabs_world.py hashes`).
- **Live drift, read-only:** e15029, and again at e15082.
  - The live texts of a5486, a6194, a6782 and a6790 equal originals.json, and every hunk stands exactly once (stage.prepare OK).
  - The prepared texts equal home-viewer.lens, view.verb and open-found.verb.
  - Live SHA-256:

    | note | hash |
    |---|---|
    | a5486 | 6DECE146… |
    | a6194 | 2318BB58… |
    | a6782 | F9F89373… |
    | a6790 | 85DD5060… |
- **Copy:** hud_playtest's disposable copy of frontier-try (15257 events at start).
  - Staged by `tabs_world.apply_copy`: preflight, then one `do replace` per hunk, then `do browse <viewer> action=init` as alex.
  - Fixtures were synthetic: two 160-paragraph notes, 30 notes with long titles, and one page to delete.
- **Browser:** the guarded hidden Edge, driven by Windows messages.
  - 2560x1440 and 1280x800 CSS at DPR 1.5.
  - Page errors [] in both runs.
  - Guard on every run: "alex: untouched by the sandbox".

## Journeys

Reports are under `research/window-lab/demos/tabs-review/` (main checkout):
- 2560: `2026-10-20-214707-2560x1440`
- 1280: `2026-10-20-215024-1280x800`
- the candidate fix: `…215359-2560x1440-candidate-menu-role` and `…215536-1280x800-candidate-menu-role`

| journey | 2560x1440 | 1280x800 |
|---|---|---|
| migrate: once, idempotent; pins/find/layout/draft unchanged; survives a reload | pass | pass |
| pins open in the active tab; Back, Forward, Back×2; a search after Back drops Forward; no new column (6=6) | pass | pass |
| New tab is blank; search opens in it; the Tabs menu names both; selecting tab 1 keeps its Back | pass | pass |
| reading position: A 600 px, B 1500 px, through tab switches and a browser reload | pass | blocked: at 1280 the viewer panel leaves no room for the page (pre-existing cramped HUD) |
| Open with a lens: an entry in that tab only; Back returns to the page's own look | pass | pass |
| "Open in new tab" from the pin menu and from the title menu | pass | pass |
| keyboard: Tab into the list, Down, Enter selects that tab | pass (Down on the handle does nothing; see 7) | pass |
| refused targets: https, http://127.0.0.1, file:///, local://, javascript:, another world, a missing id, an unknown title, `view https://…` | pass: each refused, viewer line unchanged | pass |
| bypass route: the board's "Read it in the middle" | **fail** (defect 2) | **fail** |
| 34 tabs with long titles: menu inside the page, 1 line per row, the HUD does not scroll, last row selectable | pass functionally; **unreadable** (defect 1) | **fail**: the menu runs off the page bottom (defect 4) |
| search lists each page once | **fail** (defect 3) | not shown (the search typing went elsewhere at this size) |
| Close the active tab moves to its neighbour; closing all leaves one blank tab | pass | **fail**: the Close is off the page (defect 4) |
| × shelves the Viewer, keeping the tabs; a search result brings it back on the same tab with its Back | pass | pass |
| unsent draft: words, range 7–11 and draft note unchanged after every journey; nothing sent | pass (the range is lost only by browser reloads, as before) | blocked: composer cut off at 1280 (pre-existing, as a7466 found) |

## Defects (reproduced)

1. **The Tabs menu float is transparent** (2560 shot `19-overflow-menu.png` in the 213723 run).
   - Its rows paint over the Chat panel's messages and cannot be read.
   - The `menu : column` has no role, unlike the search dropdown (`role searchdrop`).
   - **Candidate, ran (not the staged bytes):** add `role searchdrop` under `menu : column` in hunk 3. At 2560 the menu becomes a white, bounded, scrolling list ([1841, 164, 398x1008], scrollHeight 1063).
2. **Routes that write `viewing=` directly bypass the tabs.**
   - The live Home base has 20 such lines in 7 lenses:
     - home-board: 8
     - home-notices: 2
     - waiting-on-me: 2
     - home-surface: 2
     - home-work: 2
     - home-house: 2
     - home-usage: 2
   - `routes.py` lists them.
   - **Browser:** "Read it in the middle" on a board card set viewing a7641 → f4358, but tabs_state stayed on A, with the same label and reading key. Back then tried the tab's previous entry, a removed page, and was refused, so the viewer stayed on the card's page.
   - **Door** (`repro.py bypass`): from The lowdown, the card's line set Board; Back then went to f4358, skipping The lowdown.
   - HANDOFF already says these routes are not covered. Alex's board and notices are his main ways in, so this blocks.
   - **Fix (world):** route each line through `do view $c`, or `do browse … action=open target=$c lens=home-feed` where the line sets with=.
3. **Tab notes appear in search, and they are never cleaned up.**
   - Searching "Synthetic tab 07" listed the tab note a7725 beside the page a7659.
   - A tab note keeps the title of the page it was created with, even after the tab moves on. The repro's a7552 is still titled "A window's own values" while its tab shows The lowdown.
   - Every tab ever opened stays as a note in Home base: 34 closed notes after one run.
   - **Fix:** the source should give the notes a neutral title, or update the title. A world mitigation in home-search: `-prop:role=viewer-tab` on both of its `of` lines.
4. **1280 only: the Tabs list leaves the page.**
   - The menu is [876, 410, 398x560] on an 800 px page. That holds even with the candidate role, because the float opens below its handle at y≈410.
   - The last rows and their Close cannot be reached, even by scrolling the list.
   - The cause is the painter's `placeFloat`, which does not bound the float to the space left. That is a source fix, separate from this patch.
5. **Apply order.**
   - Applying the hunks in patches.json order leaves home-viewer not compiling between hunks 3 and 4: "line 57: each tab: no part of that name is defined".
   - The order 1, 2, 4, 3, 5, 6 compiles at every step (ran, `repro.py order`).
   - Alternatively, use one fenced `read` + `do rewrite` with the prepared text.
6. **Minor: the refusal reason is hidden.**
   - Back to a removed page is refused correctly ("That Agora item is unavailable", by door).
   - The status line shows only "refused: !! since your last look: … remove …".
   - The Back chip stays, and the entries before the removed one cannot be reached.
7. **Minor:** Down on the Tabs handle does not enter the list (the handle is not one of the `arrows` stops). Tab does.
8. **Minor:** migration drops the old one-step Back. The live viewer is closed (viewing= back=a6866), so the first tab starts blank and back=a6866 goes.

## Round 2 (builder-1, 20–21 Oct): repaired source, JEFF's composed payload, the float fix

worker-a7544 (builder-1), after the source repair 319b57d (a7319) and JEFF's c7704, e15996 and e16026. Nothing was applied live.

### Verdict

**JEFF may apply the menu, search, notice and the eleven `do view` route hunks of a7761 with a7439/a7693, once this branch's `placeFloat` lands.** Six route clauses must change first (corrected 21 Oct: this line said four, wrongly; a live read found 2 + 2 + 2):

- a5544 home-work: 2 clauses
- a6352 home-house: 2 clauses
- a6771 home-usage: 2 clauses (one passage, used twice)

Each of these clauses ends in `do prop …home-viewer shelf=no when count(…) > 0`. A trailing `when` on a lens click line is refused ("unexpected words after the target: 'when > 0'"). The browse open before it stands, but the Viewer stays shelved. Unguarded, `shelf=no` is refused as a no-op whenever the Viewer is already out. The guard has to live in a verb: for example, `view` taking an optional lens, as in `do view $u lens=plan-usage-reader`. That is JEFF's hunk to write (c7846).

### What was reviewed (ran)

- **Source:** branch worker/a7544 on main 4d7f671 (contains 319b57d).
  - `test_viewer_tabs.py`: 16 tests OK.
  - `test_scene.py`: 58 passed.
- **SHA-256:**

  | file | hash |
  |---|---|
  | viewer_tabs.py | F5F4DA5F… |
  | tab_history.py | 69C55E1C… |
  | lens.js (with placeFloat) | FD918FB9… |
  | viewer.js | F899DD0E… |
  | textedit.js | A6F912EE… |
  | search-exclusions.json | 8E315231… |
  | patches.json | D716135D… |
  | originals.json | DB379801… |

  The full hashes are in each report.json.
- **Staging on the copy:**
  1. `tabs_world.apply_copy`: a7439's six hunks, then init.
  2. `compose_jeff`: a7693's six search hunks (stage.prepare: every one once).
  3. a7761's menu (`role searchdrop`, `by order`) and 20 route clauses, each counted at its exact expected times before anything is written, then read back equal.
  4. Every lens compiled.
  - The intermediate "home-viewer does not compile" line comes from the known hunk order (defect 5 above); the end state compiles.
- **Browser:** the guarded hidden Edge, CSS 2560x1440 and 1280x800 at DPR 1.5.
  - Page errors [] at both sizes.
  - Guard on every run: "alex: untouched by the sandbox".
- **Reports** (in `research/window-lab/demos/tabs-review/`):
  - 2560: `2026-10-21-093250-2560x1440-jeff-fixes` (every journey passed; routes stopped on one 502 from the copy's door, so its 2560 result is from `2026-10-20-231140-2560x1440-jeff-fixes`)
  - a run on 20 Oct at 23:3x lost its DevTools connection after `show` and hung with no guard verdict. Its Edge window or copy door may have been left running; I could not list processes to check.
  - 1280: `2026-10-20-231524-1280x800-jeff-fixes`
- **Door repros:** `repro.py notice` and `repro.py usage`.

### Journeys

| journey | 2560 | 1280 |
|---|---|---|
| migrate (the copy's Viewer is now out on Board): tab-1 on f155, second init "Already", heading kept over reload | pass | pass |
| pins, Back, Forward, Back×2, a search drops Forward, 6=6 columns | pass | pass |
| new tab, menu rows, select restores Back | pass | pass |
| reading position A 600 / B 1500 through switches and reload | pass | blocked: the viewer has no room at 1280 (as before) |
| lens entry, open in new tab, keyboard, refused targets | pass | pass |
| board "Read it in the middle" (now `do view`): the tab's own history, Back to the page before | **pass** (was defect 2) | **pass** |
| rerouted entries pressed in the browser | notices: removed, same tab, Back right; **usage: the Viewer stayed shelved** | notices pass; usage not pressable at this size |
| 34 tabs: menu opaque, inside the page, scrolls, last row selectable | **pass**: [1205, 164, 398x1008] | **pass** (was defect 4): [560, 4, 398x383] above its handle |
| order: closed slots reused, notes do not grow, menu rows = tabs by numeric order | pass | pass |
| floats: as-is, a real window resize, and the CSS page of 125% zoom (each side / 1.25, a real resize); keys reach the last row inside the box; Escape closes it and keeps the Viewer | pass (2560x1295, 2049x1152) | pass (1280x720, 1025x641) |
| search lists a page once (tab notes excluded) | **pass** (was defect 3) | pass |
| close moves to the neighbour; all closed leaves one blank tab | pass | **pass** (was defect 4) |
| unview and resume | pass | pass |
| draft words, range and About unchanged; nothing sent | pass | blocked: composer covered at 1280 (as before) |

Shot looked at: `22-overflow-menu.png` (1280). The menu is white, above the Tabs handle, inside the page, with its scrollbar.

### Door results (ran, copy)

- **Notice** `do view a5723; do remove a5733` after a shelve: the Viewer comes out on the item in the same tab, the notice is gone ("not in the world now"), and Back returns to Board.
- **Usage** `do browse … lens=plan-usage-reader; do prop … shelf=no when count(…) > 0`:
  - the open stands, with the right lens and Back;
  - the second command is refused (above).
  - With the guard removed: it works while the Viewer is shelved. With the Viewer out, it is refused "already has shelf=no; nothing to change; earlier steps undone", although the state read afterwards still shows the open.

### The float fix (source, approved by JEFF e15996)

- `desk-shell/lens.js` `placeFloat`: a lifted float opens below its line, or above it when it does not fit below and above has more room. It is no taller than the room on that side; the rest scrolls inside it (`overflow: auto` from lens.html). It is placed again on every settle (repaint, scroll, resize).
- Ordinary floats keep their place: the notices list and the search drop measured unchanged.
- No world sizing could say this: 70vh ignores where the handle sits.
- Recorded:
  - Rough spots a7781.
  - The Handbook's lens section a243 (e16166).

### Also found

- At 1280x496 the HUD gives the viewer tile no room at all. At 1280x720 the dock covers the viewer's Tabs handle. Both are the HUD's layout, not the float.
- The landing gate's test_landing_queue case 14 passed here every time (20 of 20 cases). This branch changes no queue code, so treat it as a room transient (c7755).

## Round 3 (builder-1, 21 Oct): JEFF's a7937 view-with-lens, copy only (c7956)

`python research/window-lab/browsing/tabs/review/repro.py helper` (ran) on a copy of frontier-try at e17553. It applies a7439/a7693/a7761, adds a7937's verb to f5204, and routes the six lens clauses through `do view-with-lens $x <lens>`. All nine rows passed:

1. Shelved Viewer: opens with the lens and comes out (shelf=no).
2. Already visible, another target: the guard is skipped, no refusal.
3. Same target and lens again: no new entry, no event.
4. Same target, another lens: gets its own entry, and Back returns to the first lens.
5. Another actor (pike): "nothing matches prop:role=home-view,prop:actor=pike", and alex's viewer is untouched. This is weak, because pike has no viewer on the copy.
6. `"home-feed; do remove a5082"` as the lens: refused as "Invalid lens; earlier steps undone", and a5082 stays.
7. Unknown lens: "That lens is unavailable; earlier steps undone", and the viewer is unchanged.
8. Stale press: "refused: a6866 changed since this was painted … nothing was done."
9. The draft a5082 and its About are unchanged.

Not checked: how this looks in a painted browser (no screen run, per e17636); a second actor that does have a viewer. Side note: after (4), the legacy `back=` field equals the current target, because both entries are a6868.

## Not run

- Clicking an agora:// link inside markdown (the textedit hook).
- The deliberate external open of an http link.
- Pressing Reload with the mouse (Reload ran by door only).
- `position`/`zoom` from the browser.
- Real touch.
- Any live apply.
