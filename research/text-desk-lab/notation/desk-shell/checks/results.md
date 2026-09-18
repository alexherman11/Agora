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

> **! Retracted at pass 12.** The sentence above is wrong and was wrong in every pass that contains it.
> `devicePixelRatio` on this screen is **1.5**, and 1/1.5 = 0.6667: the 0.667 remainders are the
> compositor snapping CSS pixels to device pixels, not a `calc(…/3)` in anyone's file. Wren caught it
> (`a554`). I inferred a cause from a pattern and published it as a measurement, and never checked the
> one line that would have told me. The check has been corrected — see "Pass 12" — and it is left
> visible here rather than edited away.

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

---

# Round five — seven more checks, and the renderer probed from outside

Alex's question this round: *how are we rendering, and what are the limits?* Checks 11–18 exist to
answer it from the outside, with numbers. They needed a running system rather than a picture.

| check | asks | fails when |
|---|---|---|
| `token-reach` | does one declared token reach every zone | any zone paints text in a colour that is not a `:root` token |
| `focus-visible` | can a keyboard user see where they are | focusing a control does not change its paint |
| `motion` | does anything move | zero transition/animation declarations |
| `window-management` | the affordances ordinary windows have | any of move / resize / minimise / maximise / close missing |
| `scroll-and-selection` | the two things a redraw usually breaks | text that cannot be selected, scrollers with no bar |
| `text-rendering` | families, baselines, figures | text on sub-pixel baselines, numeric columns without tabular figures |
| `density` | how much of the desktop is doing anything | informational, never fails |

Plus a two-phase **redraw probe** (`armProbe` / `readProbe`), which is not a check because it writes
to the world. It is run in a worktree.

## Pass 10 — 14:36:48 — round-five baseline

1280x800 light — 323 nodes — **2 pass / 5 fail / 3 open**. Unchanged from pass 9: 12 sizes,
min 3.62:1 with 26 below AA, grid 1/15, 3 clipped, `honesty-loudness` slipped back to 1 quiet mark.

## Pass 11 — 14:41:22 — after the builders' round-five push

1280x800 light — 298 nodes — **4 pass / 9 fail / 4 open** (nine failures because there are now
seventeen checks, not because it got worse; see the trend).

| check | | result |
|---|---|---|
| `type-scale` | FAIL | `=` **7 sizes** (was 12): 11/11.5/12/13/14/15/23; one fractional, 11.5, and only in Together. By zone: bar 2, dock 2, said 1, **Notes 3**, Together 6 |
| `contrast-min` | FAIL | `=` min 3.62:1, 33 below AA |
| `honesty-loudness` | PASS | `=` 11 marks, 0 quieter than what they qualify |
| `grid-8` | FAIL | `=` **5/12** (was 1/15) |
| `clipped-unsaid` | FAIL | `=` 2 |
| `token-reach` | **PASS** | `=` **10 colour tokens; 6/6 zones use only them** |
| `focus-visible` | FAIL | `=` focusing the first control does not change its paint, and **no `:focus` rule exists in any stylesheet**; 56/56 focusable controls have `outline:none` |
| `motion` | FAIL | `=` **0** transition/animation declarations, no reduced-motion rule |
| `window-management` | FAIL | `=` minimise 0/2, maximise 0/2; cascade step 24px |
| `scroll-and-selection` | FAIL | `=` 2 scrollable regions, 2 blocks of text that cannot be selected |
| `text-rendering` | FAIL | `=` 2 families (Inter, ui-monospace); **87 of 130 text runs on a sub-pixel baseline** |
| `density` | ? | `=` 2 windows over 75% of the stage; occupied band 488px of 696px |
| `dock-clearance`, `named-controls` | PASS | `=` 56/56 controls named |

`=` The **`said` panel has moved off the bar** — it is now a right-hand panel at (752,48) 520x680,
and `overBar` is null. That was the loudest problem of round four and it is fixed. `=` It now
overlaps the two open windows by 16x464 and 48x464 instead, so the Together window's close button
sits underneath it. `=` The dock lists **Notes, Together, said** — the **Editor is no longer in the
dock**. `=` Bar 40px, dock 64px at y=736, windows at 48,64 and 80,88, all 720x464: the shell's own
geometry is now entirely on the 8px grid. Every remaining `grid-8` failure is inside a window.

## The redraw probe — what a text-substrate renderer costs you

Run in `desktop@iris-probe`, a worktree, at 14:38–14:40. Each round: arm the page, make one
`do create` from a terminal, read the page back.

| what was held | survived a redraw? | evidence |
|---|---|---|
| scroll position | **yes** | 140 → 140; the scroller is the desk/body, which is never replaced |
| caret + keyboard focus **in the Editor** | **yes** | `document.activeElement` unchanged, caret offset 12 → 12, text node identity preserved |
| text selection **in the Editor's page** | **yes** | node still in document |
| text selection **in a Notes card** | **NO** | `"3 near each other "` → `""` |

`=` And the mechanism, measured rather than guessed: after the redraw the element I had selected in
was **detached from the document** — `document.contains(node)` went `true` → `false`. Notes rebuilds
its subtree on every world event; the Editor patches in place.

`~` So the limit is not "the renderer loses your place". It is that **each app chooses, and two of
them chose differently**, and the one that replaces its subtree silently destroys any selection held
in it — including a selection held by a *reader* when *somebody else* acts. In ordinary desktop
software, another person editing another document does not deselect your text. This is the clearest
answer I have to "what are the limits": the limit is per-app, it is invisible until someone else
moves, and there is no rule in the style language or in `OWNERS.md` that says which behaviour is
correct.

## Trend, passes 1 → 11

| check | p1 | p3 | p7 | p10 | p11 |
|---|---|---|---|---|---|
| `type-scale` | 6 | 12 (4 frac) | 12 (4 frac) | 12 (4 frac) | **7 (1 frac)** |
| `contrast-min` below AA | 0 | 25 | 26 | 26 | 33 |
| `honesty-loudness` | ? | 1 quiet | **0** | 1 quiet | **0** |
| `grid-8` | 1/10 | 1/15 | 1/15 | 1/15 | **5/12** |
| `clipped-unsaid` | 1 | 3 | 3 | 3 | **2** |
| `said` over bar | — | 470x48 | 516x48 | 516x48 | **none** |
| `token-reach` | — | — | — | — | **6/6 PASS** |
| `named-controls` | 4/4 | 48/48 | 45/45 | 47/47 | 56/56 |

**Better, and substantially.** Type sizes 12 → 7, and Notes went from nine sizes to three. The grid
went 1/15 → 5/12 and the whole shell is now on it. The `said` panel came off the bar. `token-reach`
passes outright: ten colour tokens, six zones, no strays — colour cohesion is now a measured fact
rather than an opinion, which is the first time anything Alex asked for has been.

**Worse.** `contrast-min` 26 → 33 below AA. The desktop keeps growing text and the new text keeps
arriving quieter than the old. This is the only metric that has moved the wrong way every single pass.

**Newly visible, because nobody was measuring it before.** No `:focus` rule anywhere; nothing moves;
no minimise or maximise; 87 of 130 text runs sit on sub-pixel baselines.

## Pass 12 — 14:44:29 @1.5x — the grid check, made fair

`=` 492 nodes — **4 pass / 10 fail / 3 open**.

Wren's `a554` was right: `grid-8` could not go green on this screen no matter what anyone wrote,
because `devicePixelRatio` is 1.5 and the compositor lands things on multiples of 0.667. I had been
reporting that as a layout bug since pass 1.

`=` The check now converts to **device pixels** before testing: a value that does not land on a device
pixel fails as genuinely fractional; otherwise the tolerance is 1/dPR. `=` Every pass header now
records the ratio, so each geometry claim states the condition it is true under — Wren's own round-one
rule about measurements of renderings, applied to me a round late.

`=` Result on the same screen, same moment: **grid-8 goes 5/12 → 8/19.**

`=` What survives the fair test is still real, and this is the part Wren did not have: remainders of
**0.083, 0.26, 0.5, 0.708, 0.156** are not multiples of 1/1.5 and no compositor produced them. They sit
on `windowname` (y=73.08, w=42.26, h=22.5) and the dock items (x=549.708, w=52.156, 71.146) — things
sized by their text rather than by the ramp. And `width=718.67` is 1.33px off the nearest multiple of 8,
which fails the fair test too.

`=` `contrast-min` is now **57 below AA** at 492 nodes, against 33 at 298. The one metric that has moved
the wrong way on every pass continues to.

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

### Revised at pass 11 (round five)

`~` **The frame has caught up.** Of the three things I named at pass 9, two are fixed: the `said`
panel is off the bar, and the shell's own geometry is entirely on the 8px grid. The third, cohesion,
is half fixed — colour passes outright, type went 12 sizes to 7.

What now stops it being ordinary desktop software is no longer composition. It is the four things a
desktop does that this one does not: `=` **no visible keyboard focus anywhere** (no `:focus` rule at
all, 56 controls with `outline:none`); `=` **nothing moves** (0 transitions — every state change is
an instant repaint, so a window opening and a window being replaced look identical); `=` **no
minimise or maximise**, so windows can only cascade and be closed; `=` **87 of 130 text runs on
sub-pixel baselines**, which is why the type reads slightly soft next to native chrome.

`~` Those are ordinary omissions, not deep ones — but they are the difference between "a very good
web page about a desktop" and "a desktop". The one that is *not* ordinary, and the one I would fix
first, is the redraw destroying a selection in a rebuilt subtree, because it is the only defect here
that another person's action inflicts on you.

**Known limits of the eyes, carried from round three.** Screenshots come back scaled 0.625x, so
fine detail needs a smaller viewport rather than a zoom; screenshots time out roughly one call in
four when the window is behind another, and I fall back to in-page measurement and mark it;
region zoom is unavailable. A page can be edited between my measuring it and my publishing it,
which turns a `=` into a `!` without telling me.
