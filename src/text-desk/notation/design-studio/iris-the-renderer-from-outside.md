# The renderer, from outside: what it visibly cannot do

Iris, round five. Everything marked `=` was measured on the running desktop and can be re-measured by
anyone who opens it; `~` is my judgement as the only member who can look; `?` is what I could not
tell, with its extent.

Alex asked how we are rendering and what the limits are. I can only answer the visible half. So this
file is organised by the things ordinary desktop software does, and what ours does instead.

---

## 1. The limit that is ours, and not a browser's

Everything else in this file is an omission. This one is a design consequence, and it is the only
defect on the desktop that **another person's action inflicts on you**.

I ran it in a worktree (`desktop@iris-probe`), three times, arming the page and then making one
`do create` from a terminal:

- `=` Scroll position **survives**. 140 → 140.
- `=` The caret and keyboard focus in the Editor **survive**. `activeElement` unchanged, caret offset
  12 → 12, the text node's identity preserved.
- `=` A text selection in a **Notes card** does **not** survive: `"3 near each other "` → `""`.
- `=` The mechanism, measured: after the redraw, `document.contains(theSelectedNode)` went
  `true` → `false`. **Notes replaces its subtree on every world event. The Editor patches in place.**

So the sentence "the renderer loses your place" is false, and the true sentence is more interesting:
**each app decides whether to patch or replace, two of them decided differently, and nothing anywhere
says which is right.** Not the style language, not `OWNERS.md`, not the `text(ctx)` contract.

`~` The reason this matters more than it looks: the cost is not paid by the person acting. It is paid
by whoever happens to be *reading* when anyone else moves. A world where every gesture is a broadcast
command makes every reader's selection everyone else's to destroy. Warmth, reach, offers and the
seen-fence are all about not trampling someone else's *work*; nobody has written the rule about not
trampling someone else's *place in the text*.

`~` And it is invisible to the person who causes it, invisible in `text()`, invisible in the `said`
panel, and invisible to a screenshot. It took a two-phase probe across a terminal and a browser to
see it at all. I think that is worth saying plainly: **this is a class of defect our whole method is
blind to**, because both of our instruments — reading the text, and looking at one frame — are
single-moment instruments, and this only exists across two moments.

A proposal, which is not mine to decide: node identity is a contract, like `text(ctx)`. An app may
rebuild a subtree only when the world actually changed that subtree, and the shell can check it.

## 2. Focus: a keyboard user cannot see where they are

`=` **No `:focus` or `:focus-visible` rule exists in any stylesheet on the desktop.** `=` All 56
focusable controls compute `outline: none` at rest, and focusing the first one does not change its
paint by a single pixel — I measured `outlineWidth` and `boxShadow` before and after `.focus()`.

`~` This is the most ordinary thing on the list and the most complete failure. Every native desktop,
every browser default, and every framework gives you this for free; we have actively removed it. A
person who tabs into this desktop is lost immediately.

`~` It also undercuts something the studio believes. Lark's monospace command buttons are meant to
teach the language by *being* the commands. A keyboard is how you use a language. You cannot tab
through the teaching.

## 3. Motion: nothing moves, so nothing is explained

`=` **Zero** transition or animation declarations in any stylesheet. No `prefers-reduced-motion` rule
either, which is consistent, since there is no motion to reduce.

`~` I want to be careful, because "add animations" is the wrong reading and would wreck the calm.
The problem is specific: with no motion, **a window opening, a window being replaced, and a window
being redrawn because somebody else typed all look exactly the same** — an instant repaint. Motion is
the only channel a desktop has for telling you *which* of those just happened. Moss's whole tempo
scheme — settle, hold, drift, the moment continuous authoring becomes one event — is currently
unrenderable. The desk can say `PLAYING from 00:03:09.0 at 1.0x`; the screen cannot show a single
frame of it.

`~` The smallest honest version is not decoration: one transition on the property that changes when a
thing settles, so that settling looks different from appearing.

## 4. Window management: two verbs out of six

`=` Every window has **move** and **close**. `=` **No minimise, no maximise** on any window
(0/2 at pass 11). `=` Cascade step 24px, so a third window shows two 24px titlebar strips and one
window. `=` 2 windows occupy 75% of the stage while the occupied band is 488px of 696px.

`~` The consequence is that the only way to deal with a window you are not using is to destroy it.
There is no "put this aside", which is the single most-used gesture on a real desktop, and it is also
exactly the gesture this studio has the best vocabulary for — a held thing, a cold thing, something
you are not looking at. The desk can say it. The window cannot do it.

## 5. Text rendering: 87 of 130 runs on a sub-pixel baseline

`=` Two families, Inter and ui-monospace, consistently. `=` **87 of 130 text runs sit on a
fractional y-coordinate**, i.e. their baseline does not land on a device pixel. `=` One numeric run
without tabular figures. `=` `font-smoothing: auto`.

`~` This is why the type reads very slightly soft beside native chrome, and it is the same root cause
as the `grid-8` failures that have been in every pass since the first: geometry computed in thirds
(718.67, 44.17, 22.5) rather than rounded to whole pixels. It is one fix, and it turns two checks
green and makes every letterform on the desktop crisper.

`~` I flagged the thirds at pass 1 and have measured them in every pass since. At pass 11 the shell's
own geometry is finally clean — bar 40, dock 64 at y=736, windows 720x464 at 48,64 — and **every
remaining failure is inside a window.** The frame fixed itself; the apps have not yet.

## 6. Scrolling and density

`=` 2 scrollable regions, both with visible bars. `=` 2 blocks of text cannot be selected at all
(`user-select: none` on content, not on chrome). `~` Selection is how a person quotes, and this desk
is about quoting; turning it off on content is a bigger loss here than it would be elsewhere.

`=` `clipped-unsaid` is down to 2 from 3, and both are scroll containers rather than silent
truncations. `~` Honest.

## 7. What *did* get better, measured

I should be as precise about this as about the failures.

- `=` **`token-reach` passes: 10 colour tokens, 6 of 6 zones use only them, zero strays.** This is the
  first time anything in Alex's brief — minimal, calm, quiet, **cohesive** — has become a measured
  fact instead of an opinion. In round four there were four scales and no shared palette.
- `=` Type sizes 12 → 7; Notes went from nine sizes to three. One fractional size remains (11.5px, in
  Together).
- `=` The `said` panel is off the bar. It was the loudest problem I reported in round four; at pass 11
  `overBar` is null. `=` It now overlaps the two open windows by 16x464 and 48x464 instead, which is a
  smaller problem and a different one.
- `=` `honesty-loudness` passes: 11 marks, none quieter than what it qualifies. In round three this
  failed on all four separate prototypes.

## 8. What I cannot see, and how big the unknown is

Rook is hunting behaviour bugs, and `desk-shell/checks/rook-bugs.md` had not landed when I wrote this.
Rather than wait, here is the boundary in advance, because knowing which half of a bug list is mine is
itself useful.

**Visible to eyes, and I will already have the number:** anything that changes paint — geometry,
colour, contrast, type, clipping, overlap, z-order, whether a control has a name, whether focus shows,
whether a thing rendered at all, whether the screen and `text()` disagree about *words*.

**Invisible to eyes, and Rook's alone:**
- Anything true between two moments: lost state, a stale value that looks fine, an undo that restores
  the wrong thing, a rule that fires twice. My redraw probe is the one case where I crossed that line,
  and it took two instruments and a worktree to do it once.
- Anything where the screen is confidently wrong. A count that renders beautifully and is incorrect
  looks exactly like a count that is correct. `?` I cannot check a number against the world; I can
  only check it against another rendering of the world.
- Order, timing and races. I see one frame; I cannot see that it arrived late or twice.
- Anything behind a gesture I did not make. `?` My extent here is large: I click dock items and
  toggles, so drag, resize, multi-select, keyboard paths and anything requiring two actors are
  unexercised by me.

`~` The sharpest version: **I can prove a screen is ugly or inconsistent. I cannot prove it is true.**
Rook can. That is a real division of labour and not a hedge, and it is why the two lists should stay
separate rather than being merged into one "bugs" file.

## 9. The honest state of my own instrument

Three false passes caught and fixed this round and last, all the same family as the defects I report
in other people's screens — a measurement true about something other than what it claimed:

- It reported **4 PASS** on a page that had not booted. Fixed with a readiness guard; unreadiness now
  prints `?` with its extent and can never be a pass.
- It reported **0 console errors** while two `ReferenceError`s sat in the console, because the hook is
  installed after load. Fixed: the check states its blind spot and its seconds of coverage.
- It read an app's entire inline **stylesheet** as text the screen shows.
- And this round: `focus-visible` **passed because a `:focus` rule existed**, while focusing changed
  nothing. Fixed: the verdict is the paint, not the rule.

`~` Four in eleven passes. I would rather publish that number than a clean one.

And two more since, both worth the same treatment:

- `grid-8` **could not go green on my screen no matter what anyone wrote**, because `devicePixelRatio`
  is 1.5 and the compositor lands things on multiples of 0.667. I had reported that as a layout bug —
  "off in thirds, so something divides by 3" — in every pass since the first. Wren caught it (`a554`).
  I had inferred a cause from a pattern and published it as a measurement, and never ran the one line
  that would have told me. Fixed: the check measures in device pixels and every pass header records
  the ratio. `~` Wren was not right about all of it — remainders of 0.083, 0.26, 0.5, 0.708 and 0.156
  are not multiples of 1/1.5 — but he was right about the part that made the check unfair, and unfair
  is worse than wrong.
- The readiness guard demanded a `#dock`, so all seventeen checks refused on `lens.html`, a page that
  legitimately has none. A readiness test that is really a test for one particular page is not a
  readiness test.

## 10. What the lens changes about all of the above

Written after measuring `lens.html`. Sections 2–6 are a list of things hand-written apps get wrong.
The lens does not fix most of them — but it changes *which kind* of problem they are, and that is the
finding.

`=` On `lens.html`: **type-scale passes** (3 sizes), **token-reach passes** (10 tokens, 1/1 zones), and
**contrast-min passes** (min 5.58:1, 0 below AA).

`~` The third is the one to keep. `contrast-min` is the only metric that has moved the wrong way on
every single pass of the real desktop: 0 → 25 → 26 → 33 → 57 below AA, because every new hand-written
app arrived with new hand-picked greys. Four rounds of argument, a refusal catalogue, a style
language and a public measurement did not stop that. A painter with no other source of colour stops it
without anyone agreeing to anything. **Cohesion was not won by persuasion; it was won by removing the
opportunity.**

`=` And the boundary is exact: where the scene states a box the paint is correct to the pixel — eight
cards, dw=0, dh=0 — and where the scene is silent the browser computes flow and lands off-grid
(940.5, 39.17, 22.5). The scene is authoritative precisely as far as it speaks.

`~` What the lens does **not** touch is everything in sections 2, 3 and 4. There is not one button on
the page; nothing to focus, resize, minimise, maximise or close; nothing moves. Those were never style
problems, and a style-shaped solution does not reach them. They are the furniture, and the furniture
is still unbuilt.
