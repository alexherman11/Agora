# checks/results.md — the eyes' fixed script, run pass by pass

Owner: Iris. The script is `checks/checks.js`; this file is what it printed.

Run it from the page:

```js
const m = await import('/checks/checks.js');
await m.withText();          // switch every window's "as text" panel on first
m.md(7)                      // the markdown block for pass 7
```

**Every row is `=` measured or `?` opaque.** The script never emits `~`; a `~` in this file is
mine, written by hand, and says so. Every pass carries the page title, the href, the viewport
and the wall-clock time, because the page changes under me — three times on 2026-09-18 my tab
was carrying a *different person's* session when a measurement ran, and the stamp is the only
reason I noticed.

**A `?` is not a pass.** After pass 2 the script refuses to score anything content-shaped until
the page has at least six text leaves and a dock. See "What the instrument got wrong" below.

## The ten checks, and why each one

| check | asks | fails when |
|---|---|---|
| `type-scale` | how many distinct type sizes, are any fractional | more than 5 steps, or a size that is not a whole pixel |
| `contrast-min` | the worst text contrast on screen, against its real painted background | anything below 4.5:1 (3:1 for large text) |
| `honesty-loudness` | is every `= ~ ? !` at least as loud as what it qualifies | a mark quieter (contrast x size) than the loudest text in its own line |
| `grid-8` | are dock, bar, stage and windows on the 8px grid | any x/y/width/height off the grid by more than 0.75px |
| `clipped-unsaid` | is anything cut off without admitting it | overflow, line-clamp or ellipsis with no nearby text that says so |
| `first-landing` | what the eye lands on | never fails; prints a ranking by sqrt(area) x contrast x weight x chroma |
| `console-errors` | script errors since the previous pass | any error, unhandled rejection or `console.error` |
| `as-text-agreement` | does each window's "as text" say what the screen shows | a window shows words its `text()` does not contain |
| `dock-clearance` | windows over the dock, targets too small | any overlap, or a dock target under 24px |
| `named-controls` | can a text inhabitant name every control | a button, link or input with no accessible name |

`honesty-loudness` is the check this studio earned. Last round the same defect appeared
independently on all four prototypes: everyone invented a way for the screen to admit what it
does not know, and everyone then drew it quieter than the thing it was warning about — a stale
marker at 1.13:1 contrast, an absence chip whose dashed border measured 1.25:1 against its own
fill. It is now measured on every pass.

---

## Pass 1 — 14:02 — the plain skeleton, before the restyle

`http://localhost:8780/?session=desktop&as=iris` — 1280x720 light — 65 nodes — **5 pass / 3 fail / 2 open**

| check | | result | detail |
|---|---|---|---|
| `type-scale` | FAIL | = 6 sizes: 11/12/13/14/20/24 | more than 5 steps |
| `contrast-min` | PASS | = min 5.15:1, 0 below AA | |
| `honesty-loudness` | ? | ? no honesty marks found on this screen | extent: the whole screen |
| `grid-8` | FAIL | = 1/10 on the 8px grid | window x=60 y=60.67; titlebar 718.67x34.67 |
| `clipped-unsaid` | FAIL | = 1 clipped without saying so | DIV 503x453 in 503x302 |
| `first-landing` | ? | = "f01 surface \"desk\" row · 1280x" > "Welcome" > "Notes" | proxy ranking |
| `console-errors` | PASS | = 0 since last pass | |
| `as-text-agreement` | FAIL | = 1 of 3 windows shows words its text does not say | Editor: "welcome" |
| `dock-clearance` | PASS | = 0 windows over the dock, 0 targets under 24px | |
| `named-controls` | PASS | = 4/4 controls carry a name | |

`~` Mine, by hand: three stub windows cascaded down the stage, all the same weight, a two-thirds
empty stage above a dock of four small glyphs. It reads as a skeleton and is honest about being
one. The Outline window — a monospace dump of `f01 surface "desk" row` — is by a wide margin the
loudest thing on the screen, which is the debug-view failure mode arriving on day one.

Notable: the window geometry is off the grid in *thirds* (60.67, 34.67, 718.67). That is a
three-column or `calc(x/3)` layout landing on sub-pixels, not a rounding slip.

## Pass 2 — 14:05:41 — **the desktop is down**

`http://localhost:8780/?session=desktop&as=iris` — 1280x800 light — 18 nodes — **blank white page**

```
ReferenceError: Style is not defined
    at loadStyle (http://localhost:8780/shell.js:23:5)
    at Object.start (http://localhost:8780/core.js:103:26)
```

`=` `document.readyState` is `complete`; `<body>` contains only `<header id=bar>`, `<main id=stage>`,
`<aside id=said hidden>`, `<nav id=dock>` — all empty. `=` `index.html` loads `core.js`, `shell.js`,
`apps/notes.js`, `apps/editor.js`, `apps/third.js`, then calls `Desk.start()`. Nothing defines
`Style`. `=` Because `Desk.start()` throws, the dock is never built, so no app can be opened.

`~` Anyone still seeing a working desktop is on a tab loaded before this change. I had one stale
tab and one fresh tab open at the same moment, which is the only reason I could tell the
difference. Filed to Eyes as `a467`, tagged `to-wren`.

Every other check on this pass returns `?` "page not ready", by design.

## Pass 3 — 14:07 — the shell is back, and the apps have arrived

1280x800 light — 291 nodes — **3 pass / 5 fail / 2 open**

`type-scale` **FAIL** `=` 12 sizes: 10.5/11/11.5/12/12.5/13/13.5/14/15/16/23/26, four fractional.
`contrast-min` **FAIL** `=` min 1:1, 25 below AA; worst in the top bar, #7c7d7d on #fbfaf7 at 13px = 3.96:1.
`honesty-loudness` **FAIL** `=` 11 marks, 1 quieter than what it qualifies.
`grid-8` **FAIL** `=` 1/15; titlebars 718.67 x 44.17 at y=72.83 — off in *thirds*, so something divides by 3.
`clipped-unsaid` **FAIL** `=` 3: an app body 1100x795 into 703x399; 703x1497 into 703x415; a window 719x677 into 719x459.
`dock-clearance`, `named-controls` (48/48) **PASS**.

`~` Mine: the **`said` panel** is the loudest problem on the desktop. `=` 470x132 at (0,0), **overlapping
the top bar by exactly 470x48** — it covers the left third of the bar. `=` Not hidden, Inter, on pure
white #ffffff against the desk's #fbfaf7, showing raw command echo. `~` It reads as a debug console
taped over the chrome, and it is the first thing I see.

## Pass 4 — 14:09 — Flint's Notes, on request (blind)

`=` type-scale 4 sizes (11/13/15/23) in that session — Wren's ramp had landed.
`=` The text contract holds: 35 distinct words on screen, **one** absent from `text()` — "name", from
the control "name this group". An affordance, not content.
`=` Accent #3f5d73 used by exactly **9 elements, all 9 honesty-mark glyphs**, zero others. One colour,
one meaning, completely — the cleanest result measured in two rounds.
`=` The dashed cluster ring is now 1.333px at an effective #a2a2a2, **2.45:1** — up from the 1.25:1
that failed in round three. The dashes render.
`=` New defect found in passing: at a 640px viewport the **as-text panel is clipped on its right edge**
with no ellipsis and nothing saying so. The panel whose job is to be the honest reading is silently
truncated.

## Pass 5 — 14:10 — Lark's Together, on request (blind)

`=` Headings in order: Who is here · Needs you · Since you looked here · Warm · House rules ·
The text() contract · **Screen vs text**.
`=` Its self-check line, whole: `= every row of the model appears in both projections`.
`=` **Six of the seven headings appear in the as-text panel. "Screen vs text" does not.** Searched the
whole 2581-character panel for "screen vs", for "projection", and for the sentence: none occurs.
So the section that certifies the two views agree exists in exactly one of them, and its claim is
false about the row it is written in.
`~` The best construction on the desktop is also here: 5 rows carry a 135° hatched band the full width
of the row plus a 2.67px accent left border, with a paper-coloured plate behind the words. That is
"an honesty mark is a property of the surface, not a character in the text" actually built.

## Pass 6 — 14:11 — the twelve sizes, split by owner

`=` Same 12 sizes as pass 3. Split by zone, at 14:11:47:

| zone | sizes |
|---|---|
| shell — bar / dock / said (Wren) | 11/13 · 13/23 · 11/13 — **3 in total** |
| Notes (Flint) | 10.5/11/11.5/12/12.5/13/13.5/14/15 — **9, and all four half-pixels on the desktop** |
| Together (Lark) | 11/11.5/12/13/14/15 — **6** |
| Editor (Moss) | 11/12/13/14/15/16/26 — **7** |

`~` The headline is not "the shell has a bad scale". It is that **four scales exist** and the style
language is not reaching into the apps. 11.5px appears in three apps and nowhere in the shell — three
people independently invented the same off-ramp. The measurable form of "cohesive" is one ramp,
declared once, every app size drawn from it; this check goes green the moment that is true.

`=` `said` over bar has **grown**, 470x48 → 516x48.

The per-zone split is now part of `type-scale` on every future pass.

## Pass 7 — 14:12 — 3 pass / 4 fail / 3 open

`honesty-loudness` **PASS** — `=` 11 marks, 0 quieter than what they qualify. First green.
`type-scale`, `contrast-min` (min 3.62:1, 26 below AA), `grid-8` (1/15), `clipped-unsaid` (3) unchanged.
`=` Console, read separately: the two boot-time `ReferenceError: Style is not defined` are still
thrown, plus new `ERR_CONNECTION_REFUSED` and `TypeError: Failed to fetch` at `core.js poll` — the
server went away briefly mid-pass.

## Pass 8 — 14:13:30 — steady state, light

206 nodes — **3 pass / 4 fail / 3 open**. Unchanged from pass 7 except `clipped-unsaid` 3 → 2 and
`contrast-min` 26 → 27 below AA. `honesty-loudness` holds green.

## Pass 9 — 14:13:39 — dark

`=` Pressing **dark** in the bar: body background #131517, 317 nodes, structure unchanged.
`=` **Dark is measurably kinder than light: 3 text elements below AA, against 27 in light.**
`=` But all three failures are the same bug, and it is a real one: the bar's own buttons
(*light*, *style*, *desktop as text*) keep a **light** background — #898987 on **#f0f0f0** — while the
page around them is #131517. `~` On screen they read as three pale chips floating on a dark bar. The
theme reached the whole desktop except the controls that switch it.

## Trend across passes

| check | p1 14:02 | p3 14:07 | p6 14:11 | p7 14:12 |
|---|---|---|---|---|
| `type-scale` | 6 sizes | 12, 4 fractional | 12, 4 fractional | 12, 4 fractional |
| `contrast-min` | min 5.15, 0 fail | min 1:1, 25 fail | min 3.62, 26 fail | min 3.62, 26 fail |
| `honesty-loudness` | ? none present | 1 quiet | 1 quiet | **0 quiet — PASS** |
| `grid-8` | 1/10 | 1/15 | 1/15 | 1/15 |
| `clipped-unsaid` | 1 | 3 | 3 | 3 |
| `as-text-agreement` | 1 of 3 disagree | ? | ? | ? |
| `dock-clearance` | PASS | PASS | PASS | PASS |
| `named-controls` | 4/4 | 48/48 | 45/45 | 45/45 |

**Better:** honesty marks went from one quiet mark to none — the only check that turned green, and it
is the one this studio invented. Flint's dashed boundary went 1.25:1 → 2.45:1 and now renders. Flint's
accent means exactly one thing across nine uses. The apps are real: an editor with an outline rail and
a margin, a canvas with loose positions, a presence window that audits itself.

**Worse:** type-scale 6 → 12 sizes, because three apps arrived each carrying its own ramp. Contrast
went from 0 failures to 26 — the desktop got more text, and the new text is quieter than the old.
`clipped-unsaid` 1 → 3. The `said` panel's overlap of the bar grew 470x48 → 516x48.

**Flat, and the most annoying:** `grid-8` has never been above 1/15. Every failure is in thirds
(718.67, 44.17, 72.83, 22.5) — one `calc(…/3)` or a 3-column division is generating every one of them.
It is a single fix in Wren's file that would turn a whole check green.

## What the instrument got wrong, and when

**Pass 2, first attempt.** The script reported **4 pass** against the blank page: `type-scale`
passed on *zero* font sizes, `contrast-min` passed on *no text*, `clipped-unsaid` passed on
nothing at all. That is precisely the defect I have spent two rounds reporting in other people's
screens — a claim that is true only because the thing it describes is absent. Fixed the same
minute: a readiness guard, and a `?` that states its extent. The broken run is left in this file
rather than deleted, because a checks file that only records the screen's failures and not the
instrument's is not an honest instrument.

**Pass 3.** `console-errors` reported **0** while two `ReferenceError`s sat in the console. The hook is
installed when this module is first imported, which is always *after* the page has loaded, so errors
thrown during boot are invisible to it. Fixed: the check now says "since this script was imported",
prints how many seconds of coverage that is, states the blind spot in its own detail, and returns `?`
rather than PASS on a clean run.

**Pass 5.** My screen-versus-text word diff reported an app's entire inline stylesheet as "text the
screen shows and `text()` does not". A `<style>` tag is a childless node full of text and every naive
"what is on screen" query picks it up. Fixed: `STYLE`, `SCRIPT`, `TEMPLATE`, `NOSCRIPT` and friends are
excluded from every leaf query.

Three instrument defects in nine passes, all of them the same family as the defects I report in the
apps: a measurement that was true about something other than what it claimed to be about.

## Does it read as calm, normal desktop software yet?

`~` Mine, by hand, at pass 9. **Nearly, in the windows. Not yet, in the shell.**

Inside a window it already does. The Editor is a page with an outline rail and a margin of comments,
and it looks like an editor; Notes is a canvas with cards at irregular positions, and it looks like a
canvas; Together is a quiet list of people and rules. One paper, hairline rules, no shadows, one
accent. If a screenshot were cropped to a single window I would believe it was shipped software.

The shell is what breaks it, and it is three specific things, all measurable:

1. `=` The **`said` panel sits at (0,0) and covers 516x48 of the top bar**, in a different typeface
   (Inter) on a different background (#ffffff against the desk's #fbfaf7), showing raw command echo.
   It is the first thing the eye lands on and it is a debug console taped over the chrome.
2. `=` Windows **cascade by 34px**, so three open windows show two 34px titlebar strips and one window.
   `=` Meanwhile 121px of stage sits empty below the lowest window. The desktop is crowded in one
   corner and blank everywhere else.
3. `=` **Four type scales and 27 AA failures.** Cohesion is the one thing Alex named that is currently
   false as a fact rather than as an opinion.

None of the three is deep. The apps are further along than the frame they sit in.

**Known limits of the eyes, carried from round three.** Screenshots come back scaled 0.625x, so
fine detail needs a smaller viewport rather than a zoom; screenshots time out roughly one call in
four when the window is behind another, and I fall back to in-page measurement and mark it;
region zoom is unavailable. A page can be edited between my measuring it and my publishing it,
which turns a `=` into a `!` without telling me.
