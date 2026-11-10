# press-speed (a6153): where a HUD press's time goes, and the tools that say so

A press on the home base that goes through the world is: the act (POST /api/do), then the build of the scene after it
(GET /api/scene), then the trip back and the paint. Numbers below are **ran** on frontier-try copies (e11917-e12015),
16 Oct, as alex, unless marked.

## The scoreboard (hud_playtest.py --report none, a real Edge window in the sandbox)

| press | before (main c3d9b01, no log) | after (this branch) |
|---|---|---|
| lowdown (first press of a session) | 574 | 638 |
| board | 714 | 239 |
| later | 741 | 283 |
| writing | 824 | 337 |
| comment | 863 | 540 |
| send | 709 | 302 |
| drag | 739 | 349 |
| restore | 704 | 313 |
| widen | 733 | 283 |
| dock | 733 | 318 |
| median | 733 | 313 |

Every press says it was heard on the next frame (first change 1-4 ms: a6010's `data-sending`).

## Causes found, and what was done

1. **The playtest's copy had no log** (the live world has one): each act pickled the whole world twice, ~200-250 ms.
   The copy is logged now (PLAYTEST_NOLOG=1 plays the old way). Not a live cost: a measuring error.
2. **Kept instances lived in 24 stores**, one per placed lens per place; with the board out the home base places more,
   so each build pushed out what the next needed (kept 4, made 260). lens_ir.REUSE_STORES = 400.
3. **Every part made escaped its whole context for its gestures** (~620k escapes in 8 builds); now only parts with one.
4. **A part holding a `by`/`run` repeat was never kept**: the sort keys were read around the accessor. They are read
   through it now (Accessor.props), so the holder is kept while they read the same.
5. **The painter was sent the scene text** it never shows with inspect=0 (~400 KB, ~25 ms): `&text=0`.
6. **The body was encoded twice** (sorted for its name, then to send): once now.
7. **`sayings for:<me> ... eid>...`** read every saying to keep one: cheap terms are asked first (scene.SAYING_EARLY),
   a chat dropped by them is skipped whole, and an id against an id is compared without typing (28-37 -> ~20 ms).
8. **The style was read ~26 times a build**: once per build (style_roles), and its pulsing roles once per text.
9. **The world's lock was a file tried every 50 ms**, even between two requests of one deskd: live, Alex's requests
   waited a median 58 ms, 90th percentile 288, most 1339, with the lock held <1% of the time (**read**, the live
   trace, the hour to 21:58). An in-process lock is taken first now (deskd._take/_give).
10. **hud.py rewrote 4 unchanged witnessed files every 2 s**, so every open lens rebuilt every 2 s (live trace 08:33:
    home-base every ~2 s, ~360 ms each, **read**). witnessed.write(changed_only=True); the pages are told only then.

## Not done (named, with what would)

- **First act of a deskd** (~260 ms more, once per process, so Alex's first press after every landing): store.begin
  flattens the world once, the first commit digests it, and the world is loaded. A warm-up at the lease would move it
  off the press (store.py is Snappy Desk's core: a proposal, not done here).
- **A build when everything is kept is still ~85-150 ms**: holders that place lenses are made again, every kept
  instance's questions are asked again, `sayings for:` (~20 ms) can't be kept (a6010: it follows a house rule with
  no event). Next would be keeping holders that place lenses, or pushing only what changed (scene deltas).
- **Optimistic paint** (the result before the desk agrees) is a design question for Alex: the painter cannot know a
  lens's result without the lens; the options are in a6153's done comment.
- **A press behind a page's build or the background save** still waits for it (~100-150 ms), now without the 50 ms
  steps.

## Tools

- `test_press_budget.py` - the regression test: fails when a press's act + build is over budget (230 ms server, the
  rest is the trip and paint), when a build keeps <80% of what it could, when text=0 sends text, or when a witnessed
  source is rewritten unchanged.
- `scene_cost.py` (a scene request's stages and bytes), `lens_cost.py` (a build by lens), `sayings_cost.py`,
  `sayings_ab.py`, `check_sayings_early.py` (the early terms change no row: 132 cases), `read_profiles.py` (with
  hud_playtest.py --profile-scenes DIR), `lock_share.py` (who holds a world's lock, from deskd's trace),
  `page_cost.js` (screen.py js @...: the trip and parse in the page).
- board-lab/bench_board.py gained `--stage`, `--wait`, `--why` (lens_ir._WHY: why instances were made), `--sel`,
  `--sort`, and asks text=0 as the painter does (`--text` for the old way).
