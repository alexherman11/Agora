# Press is an act

Builder evidence for dk2834, 5 November 2026.

Source: fix
Missing-word: none

**Read:** `help word.set` and `kernel/dictionary.py:word_set` allow dictionary
wording edits, but deliberately exclude implementation classification. This is
a bug in the general button dispatcher, so the repair belongs in the kernel.

**Read, before the fix:** `kernel/words.py` classified `press` as `see`.
`Kernel._run` called `pressed_line` before `step`, substituting a button's
`does=` line and executing it, not merely returning it. The normal `step`
guard still rejected an ordinary write reached this way in see mode.
However, `do press Button`, a nested press, or a reading verb could reach
`kernel/readings.py:press`, which calls `k.run(actor, line)` with its default
do mode. That fallback could act from `/see`.

The fix classifies `press` as `do`, refuses see mode before button expansion,
and checks a resolved word's classification before resolving its target or
dispatching it. The refusal directs the caller to `/do`. Existing dictionaries
upgrade on kernel construction: every kernel-bound `press` still marked `see`,
including renamed entries and group copies, becomes `do`; its existing help
is retained with the mode explanation appended. A second startup adds nothing.
The ordinary `/do` expansion is unchanged: the button's line owns the receipt
and undo.

**Ran:** `tests/test_press_modes.py` verifies actual authenticated `/see` and
`/do` on isolated loopback fixtures: classification/help, refusal with unchanged
world snapshot and act-log length, missing buttons, reading buttons, nested
buttons, explicit `do press`, reading verbs, matching click-line receipts and
undo, MCP Lines routing, and one-time migration including aliases/group copies.
Refusal diagnostics beside the world remain enabled.

The MCP `route_of` and the desktop Lines page already route `press` to `/do`.
The MCP path is exercised through its real `Door.batch`; the page routing was
read in `kernel-desktop/pages/lines.html`. No live button was pressed and no
desktop window was opened.

## Other see words: bounded source audit

**Read:** live `rows word word_kind=see` returned 79 entries, including `press`
and four hidden, unbound legacy entries. The following inventory covers every
entry returned. This is a source-path review, not execution of these commands
and not a proof against arbitrary future module code.

| Entries | Paths reviewed and finding |
| --- | --- |
| `look`, `help`, `status`, `find`, `holds`, `rows`, `counts`, `test`, `history`, `panes`, `components`, `look-view`, `file.read`, `clock`, `forgotten`, `who`, `recent`, `kinds`, `chat`, `refusals`, `actions`, `alike`, `aspects`, `search`, `edits` | Kernel handler inventory and delegated reading paths (`words`, `readings`, `world_words`, `predicates`, `kinds`, `chat`, `blobs`, `bodies`, `refusals`, painter arrangement and web layout). No additional handler like `press` found. Observation marks/caches are in memory. `status` sends a module status query. `look-view` can reread `forgotten` with explicit see mode. |
| `around`, `nearby`, `preview`, `words` | Hidden legacy kernel entries, absent from current `KERNEL` dispatch. |
| `window.list`, `window.desktop` | `kd_window.WindowHost._call` branches: filtered rows/native window enumeration and icon extraction; no activation. |
| `media.now`, `system.now`, `twitch.now` | `kd_media.call`, `kd_system.call`, adapter `call`: current readings. Background polling/socket activity belongs to the running modules, not these calls. |
| `board.queue`, `board.feed`, `board.catch-up`, `board.why-here`, `board.search`, `board.calendar`, `board.badges`, `board.events`, `board.asks` | `community-app/board/board.py:call`: filtered readings and generated calendar data; no returned write lines in these branches. |
| `new`, `top-this-week`, `needs-answers`, `happening-soon`, `catch-up` | Live verb definitions delegate to the board readings above. `Kernel.verb_note` runs reading-verb steps with see mode. |
| `theme.list`, `theme.get`, `theme.current`, `theme.export`, `theme.preview`, `theme.options`, `theme.native`, `theme.css` | `theme/theme_module.py` corresponding `w_*` handlers return data/CSS, including preview/export; no file export or theme application in these handlers. |
| `wm.windows`, `wm.policy`, `wm.sizes` | `agora-wm/wm_module.py:call`: current readings; no window action requests in these branches. |
| `house.who`, `house.activity`, `house.log`, `house.active`, `house.board` | `modules/house/house.py` dispatch and projection helpers: read current agent/worker/card state. |
| `files.browse` | `community-app/board/documents.py:call`: visible document/folder/link rows. |
| `house.snap` | Starts hidden capture work, writes a PNG and wakes the requester; details below. |
| `model.ask`, `model.status`, `model.preview`, `model.search` | Quota writes and/or inference; details below. |
| `map.tile`, `map.find`, `map.where`, `map.near`, `map.place`, `map.path`, `map.layers`, `map.cache` | Network/cache effects and explicit cache deletion; details below. |

Findings outside this patch, for Pike to assign:

- **`map.cache trim=<GB>`:** `modules/map/map.py:w_cache` calls
  `Tiles.trim` in `tiles.py`, which uses `os.remove` on cached tile files.
  This is an explicit destructive action currently offered as a reading.
- **`house.snap <thing>`:** `modules/house/house.py:House.snap` creates the
  output directory, starts a background thread, calls the hidden capture
  implementation and wakes the requesting agent when finished. `house.snap last`
  only returns status. Capture is useful, but it is not a passive read.
- **Model readings:** `modules/model/model.py:plan` calls `limit` before
  branching, including for `model.status`. `limit` persists `usage.json`.
  `model.ask` runs inference; `model.preview` charges its own attempt and calls
  the summarization plan, which can run inference and charges that attempt too.
  `model.search mode=semantic` charges quota and can call inference.
  `generate` sends `/api/generate` to the local model server with a keep-alive;
  lexical/check search paths do not perform that inference.
- **Map reading network/cache effects:** `map.tile` calls `Tiles.chunk`.
  `map.find`, `map.where`, `map.near`, `map.place`, `map.path`, and `map.layers`
  can reach live ground tiles through `area`, ground lookup or building lookup;
  name lookup can reach `geocode`. `tiles.py` downloads and writes disk caches;
  `geocode` sends a search and caches results in memory. `map.layers` also
  evaluates its allowed saved reading through `Call.see`, retaining see mode.
  These effects differ from explicit world mutation but disprove a literal
  promise that every see word writes/sends nothing.

**Read:** `Kernel.module_word` does not admit returned world-write lines from a
see module word. It cannot reverse a module's own file/network/process effects,
which occur before its answer. No module classification or behavior above was
changed in this task.

## Validation

**Ran, pinned Python:** 40 passed for press modes, Lines, help topics and
dictionary behavior; 46 passed, 5 subtests passed for skeleton HTTP, text words
and painter integration. These fixtures use isolated worlds and no visible UI.
See the worktree's `BUILD-RESULT.md` for exact commands and the initial fixture
corrections. Activation and a read-only live `help press` check remain for the
House landing.
