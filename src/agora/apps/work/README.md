# Work

> Builder update for dk1332, 28 October 2026. The current source supersedes the layout and proof described in the historical record below. It has not been installed live or visually accepted by Alex.

Work now shows one list of **current cards** from `house.active`: working cards held by a resident in Now, cards with a matching running/reviewing/landing worker, and blocked cards with their reason and resolver. The card's lane/status wins over old build reports. Done, verified, finished, queued, paused and released work hides. A retained worker must match the current run and builder; received, reviewed and landed phases alone do not keep a card visible.

Each card appears once, on one calm line. Names open bounded details. Missing blocker information is stated explicitly. Overflow uses Previous/Next pages sized to the window; the page and details do not scroll. Colours come from the viewer's theme tokens. Installation updates the app and its reading grant without changing JEFF's chat or deleting old styles.

**Verification:** `modules/house/test_work_overview.py` covers card transitions, stale runs, resident claims, blockers, names and unavailable readings. `proof.py` is the independent hidden desktop/browser proof for current rendering, details, disappearance, pagination and responsive sizing. The sandboxed worker did not run that proof or retry denied fixtures; see the worktree's BUILD-RESULT.md for exactly what ran.

**Activation:** the House must load the updated House module (new `house.active` reading) and run the Work installer before the live app can use it. No activation was performed by this worker.

**Rough spot:** the missing world word was a current-card work projection. `house.active` supplies it; Work no longer infers current work from the builder's last phase. The new `work-overview` and `work-line` components supply bounded pages and one-line named card details. General component `band` and `console` remain available to other lenses.

## Historical record — previous layout and checks

> Builder record by Claude, 27 Oct 2026. Alex: "Also bring forward a worker monitoring page as well that used to exist", and on the design page: "a coder terminal style interface where i can see worker progress (basically a really good overview of all the work being done), where i can click in and view more closely or chat with workers directly."

One window, `window.open work`, in the dock as **Work**. Brought forward from the old desk's home-work and home-board panels (`old-desk/`), in the component painter's style (`painter=components`, like the Task board).

- **Left, like the old home-board:** bands with a count on the header (the `band` component): AT WORK (one line per agent the house runs, `reading:"house.who"`, with Open), NEEDS YOU (`who=Alex`, not done), BUILDS (a card with `build=` and its `builder=`), IN MOTION (lane Now), LANDED (lane Done, folded, the last 12). One compact line per card. An empty band folds to one quiet line ("NEEDS YOU · nothing waits on you").
- **Colour says whose move it is**, as part-styles on the badges: amber Alex's, lilac a resident's (JEFF), mint an agent at work now, rose stuck, the rest a grey pill. Hex is the light look; the painter lifts it to whatever theme is worn (proof: dusk).
- **Right, a coder's terminal** (the `console` component): the open person's log from `house.log <person>`, monospaced, newest at the bottom: their chat's lines, the receipts of their acts under the line they belong to (`↳`), what they said outside any chat (marked `[outside any chat · what woke them]`), and what they are doing now. Under it a prompt: Enter says into their chat as Alex, or into Shop talk with @name for an agent with no chat of its own. JEFF is open from the start, so the right side is never empty.
- **Fills the window:** two columns, the log takes the height; only the log scrolls, never the page.
- **Live:** the house announces `house.doing` (never recorded) when what an agent is doing changes, so the page rereads.

**Builders appear by themselves:** every `house-agent` is a row of `house.who` (its `chat=` and `task=` facts say where to talk to it and what it builds), and `task.build` (MOVING-IN step 3) only needs to write `build=asked|building|landing|blocked|landed` and `builder=<name>` on its card.

Files: `work.lens` (the arrangement), `../../components/band.js` and `../../components/console.js` (reviewed by Alex's session on install), `install.py` (through the door, as Alex: lens, widget and grants, his `work-view`, JEFF's `chat=`, the dock), `proof.py` (hidden).

## Evidence

- **Ran** `proof.py` (27 Oct, polish pass): a fresh hidden desktop (`test_kdesk.Desk`), headless browser, scripted model: 15 of 15 checks (`evidence/work-proof.json`; pictures `work-overview.png`, `work-jeff-talked.png`, `work-dark.png`). Among them: bands with counts and quiet empty lines; the log in time order with one receipt under its line; monospaced; the log 825 of 929 px high; the page 929 of 929 px (no page scroll); the prompt said "from the Work page" into the Conversation as Alex, JEFF answered there, and the box emptied; dusk worn (a dark log, light words).
- **"The kernel is away" in the pictures** is the test browser's firewall (`widget_browser.py`) failing `/door/stream` with BlockedByClient; the proof checks that every stream request failed that way. **Ran, live:** `/door/stream` on 8810 answered 200 `text/event-stream` in 0.03 s. **Read:** the live window guard (`widget_guard.py`) lets a top page reach 127.0.0.1, so the live window gets its stream.
- **Ran, live (8810):** kdesk restarted (so the house offers `house.log`), installed; the band and console components reviewed at their current bytes; one live grant (with `house.log`), the first install's revoked; `house.log` gives JEFF's 36 lines; `dock_apps` ends with `work`. No window was opened on Alex's screen; the page has not been seen live.

## Rough spots

- A component widget without the `components` grant paints nothing, silently (it took a bisection to find). The missing word: **a refusal the painter shows** when its own words are not granted.
- The component painter paints only a page that is seen; headless proofs must bring their tab to the front.
- `pages/shell/shell.js`: one line, `work` in `AGORA_APPS`, plus `apps/work.svg`. The missing word: **an app's dock name and icon as world facts** (today the dock knows its apps in source).
- The test browser's firewall continues a paused request only while Python reads its events, so a proof that sleeps stalls the page (a "say" took 30-70 s until the wait loop read events). Not a word: a harness note (`page.c.js("0")` while waiting).
- The Task board's theme stylesheet styles bare class names for every component page (`.empty` is a dashed box, `.heading` a spaced flex row, `body` padded 38 px). `band` uses `band-empty`; Work avoids `role heading` on a name. The missing word: **page-wide styles scoped to their own lens**.
- `widget <id> grants=` adds a grant beside the old one instead of replacing it; install turns the widget off (which revokes its grants) before granting again. The missing word: **a regrant that replaces**.
