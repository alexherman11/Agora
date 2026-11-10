# Flint, round five: pushing Notes until the substrate complained, and building an app with no JavaScript

Three pushes, all against the running system, all measured.

1. **300 cards** in a worktree, to find where the substrate stops.
2. **Notes rewritten** — no px at all, zoom, culling, live view cards, cards that are running rules.
3. **A fourth application authored entirely from inside the desk**, in 22 commands, no JavaScript, built in
   a worktree and merged into the shared world.

Alex's question this round was *how are we rendering and what are the limits*. §5 answers it directly.

---

## 1. Three hundred cards

`worktree fork stress`, then 644 commands creating 300 notes on a 20×15 grid with tags every seventh.

| measure | result |
|---|---|
| 644 commands, 300 cards | **15.4s**, zero errors |
| `look f05` (305 things) | 0.56s, **308 lines, 27,923 characters** |
| `--dump` | 0.18s, 127 KB |
| `find tag:tide` + `table in:f05` | 0.29s |

**Compute is not the limit. Reading is.** And the interesting part is *how* the substrate complained: it
didn't.

`look f05` printed all 305 lines and declared no cut. The desk's honesty habit — the thing I have admired for
five rounds — turns out to be about **space**, not **volume**. It says `3 past the bottom (offscreen)` and
`cramped, 24px each` because those are facts about geometry. It has no equivalent sentence for *"this answer
is 28KB and you should have asked a narrower question."* That is my round-two `bulk` finding, now measured on
something that runs: at some size, containment stops being a reading axis, and nothing in the desk notices
when that line is crossed.

A second unbounded print, same family:

```
a07 note "A shared visual desk" · 449x511 at 510,353 · 55% hidden by a77,a79,a117,a119,a157,a159,a197,a199
```

The hidden-by list has no cap either. Both are one rule away from being fixed, and it is the rule the desk
already believes: *declare the cut*.

### What it did to my own idea

The thing 300 cards broke was not the desk. It was **proximity clustering**, which is the feature I have been
proudest of for two rounds.

On a 320px pitch with 300×128 cards, every card is 20px from its neighbour. Single-linkage clustering
therefore joins the entire canvas into one pack, and the honest rendering of that is a dashed hull around
everything, labelled `~ 287 near each other`. Which is not a reading. It is a shrug with a number on it.

So Notes now refuses to draw it, and says why instead:

```
~ near each other — MY READING, not the world's.
  method: rectangles whose gap is <= 48px, joined transitively, over the 300 thing(s) ON SCREEN.
  ! THE METHOD FAILS HERE: 287 of 300 join into one cluster.
    At this density everything is near everything, so nearness carries no information and I draw nothing.
    Proximity is a reading for a sparse canvas. Spread things out, or group them on purpose.
```

I would rather ship a feature that knows its own domain of validity than one that degrades into confident
noise. That is the same principle as the anchor trial in round two: the failure mode that matters is not
*"I could not tell you"*, it is *"I told you something that looked like an answer"*.

---

## 2. What Notes can do now

Rewritten against measurements rather than taste.

- **Not one `px` font size in the file.** Iris (`a525`) measured nine distinct sizes in Notes — including all
  four of the desktop's fractional ones, which were all mine. Every size, colour and space now comes from
  Wren's roles (`card`, `title`, `body`, `meta`, `tag`, `cut`, `source`, `tool`, `mark`) and tokens.
- **Honesty marks are a named role, not a borrowed colour.** I asked Wren for this (`a455`); he added
  `token mark` and `role mark` in `calm.style`, so `accent` is free to mean link/filter/action again and a
  mark names itself. Eleven mark glyphs, zero hardcoded accent.
- **Zoom** (25%–200%) and scroll, declared as stance in the bar and in `text()`: *"zoom 75% — stance, mine
  only, never a deed. The other inhabitant is unaffected."*
- **Culling past 120 cards**, with the cut declared: `! 214 card(s) not drawn (too far from the viewport)`.
- **`text()` stops at 40 rows** and hands over the query instead — my own `bulk` rule, applied to myself:
  *"This app stops at 40 on purpose: a list of 305 is not a reading. Ask the way the desk asks: find in:f05 ·
  table in:f05 cols=tags."*
- **Live cards.** A `view` node on the canvas renders as a live list of its matches. It does **not** evaluate
  the desk's selection language — it *asks the desk* (`find <query>` through the same `Desk.do` channel) and
  caches the answer against `events_total`, printing which version it asked at. The desk stays the only
  interpreter of its own language.
- **Cards that are running rules.** `do prop <id> rule=r4` makes a card that draws the rule's text and live
  fire count from the snapshot, and says `! no rule r4 in this world any more` when it is dropped.
- **Any free surface**, not just the one called "Canvas" — `ctx.surface`, or a surface carrying
  `prop app=notes`. `text()` says which it chose and why.

### What the substrate would not give me

**`kind=image` has no image.** A subject of kind image is `{title, text, tags, props}` — there is no source,
no data, no asset. So an image card on the canvas is an empty box, and the only honest thing to draw is the
absence:

> `? kind=image carries a title and nothing else in this desk — there is no picture to draw`

Alex asked for images on the canvas. They cannot exist yet, and no amount of app code changes that. This is
the cleanest example of the difference between *composition* (in-world, cheap) and *computation/assets*
(needs the substrate), which I claimed in round one and have now walked into.

**Freehand marks and arrows.** Links render as curves, which is the arrow case. Freehand is the same shape of
problem as images: a stroke is a path, and a subject has no field that can hold one. My round-one proposal
(`path=material`, a stroke subject holding its own sampled points) is still the answer and still unbuilt.

---

## 3. An application authored from inside the desk, with no JavaScript

The question: *can a fourth app be authored from within the desk — rules, scripts, views, props, style — with
no new JS?*

**Mostly yes.** Here is the whole of it, built in `desktop@triage` and merged:

```
do create f05 kind=note title="Bug triage" text="..."      · the app's own help, on the canvas
do prop $item app=triage
do create f05 kind=view title="Waiting"  query=tag:bug,-tag:triaged     · a live column
do create f05 kind=view title="Triaged"  query=tag:triaged             · a live column
rule when tag:bug,-tag:triaged do tag add=waiting                      · the intake
rule when tag:accept           do tag add=triaged                      · the button
rule when tag:accept           do tag remove=accept                    · the button sweeping itself
do create f05 kind=note title="rule r4: accept triages"                · a card that shows the rule running
do prop $item rule=r4
```

It runs. Tag anything `#bug` and it appears in Waiting; tag it `#accept` and both rules fire, in definition
order, and it moves to Triaged with the trigger tag swept:

```
> do tag a21 add=accept
ok tag a21 add=accept  [e88]
~ r4 fired on a21: ok tag a21 add=triaged  [e89]
~ r5 fired on a21: ok tag a21 remove=accept  [e90]
```

Twenty-two commands. No JavaScript was written. `worktree merge triage` replayed all of it into the shared
world as `e80..e100`, each signed by who made it, each undoable one command at a time.

### Where it stops, precisely

**1. Rules are monotonic. They fire on entering a selection and never on leaving it.**
So every state machine built from rules is a one-way ratchet that accumulates its own history: my card ended
up tagged `bug, waiting, accept, triaged` where one state was meant. Props are the workaround (assignment
replaces), but then the *button* still has to be a tag, because a rule on a verb is the only event handler
there is — so you need a second rule per button just to sweep the first one's trigger, and nothing enforces
the pairing. Drop the sweeper and every button starts leaking silently.

**2. A thing already inside a rule's selection when the rule is written is invisible to it forever** (barring
`now=1`). Combined with (1), a rule has two blind spots: things already in the state, and things leaving it.
It can only see the crossing, in one direction, for things that cross after it was written.

**3. Rules are not events.** `rule when … do …` returns `ok r3:` with no `[eN]`. They do not appear in
`history`, `why` cannot explain how one came to exist, and `undo` cannot remove one. This matters more than
it sounds: rules are the *program*, and the desk's entire trustworthiness rests on every change being an
attributable, undoable event. The program is the one part of the world that is not.

> Observed and honestly unresolved: two rules (`r1`, `r2`) that existed in the base at fork time are not in
> the `rules` listing after my merge. I cannot tell whether my merge dropped them or another designer did,
> **because rule definitions leave no trace in `history`**. That is the finding: not "the merge has a bug",
> but "if it does, the desk cannot tell me."

**4. It has no window, no dock item and no `text()` of its own.** Triage is a *region of someone else's
canvas*. It renders because Notes draws whatever is on a free surface. It is an application in every respect
except the one where the desktop knows it exists.

### The one primitive that would move the line furthest

> **Applications are subjects, and the dock is a view of them.**

Today `Desk.apps` is a JavaScript array populated by `registerApp` calls. If it were instead a selection over
the world — surfaces carrying `prop app=<renderer>` and a title — then authoring an application would be
`do create`, and everything above already works: Triage gets a dock item, opens in its own window, and Notes
renders it, because Notes now renders *any* free surface named in `ctx`.

I have done my half. Notes no longer hardcodes `title === "Canvas"`: it takes a surface from `ctx`, or falls
back to one carrying `prop app=notes`, and `text()` states which it chose and why. The remaining half is the
dock, which is Wren's, and the `app` prop being meaningful, which is Jeff's. Both are filed.

Honest about what it does *not* solve: you get a place and a name, not a look. Triage would still render as
Notes-cards, because the presentation comes from a generic app. Making a new kind *render as itself* from the
desk needs `present <kind> : …` clauses in `calm.style` that a generic renderer obeys — a second primitive,
larger than this one, and I would not add it until the first has been used.

**Second choice, if the answer must be one rule instead:** rules that fire on *leaving* a selection. Smaller,
symmetric with what exists, and without it no in-desk application can have a state that goes backwards.

---

## 4. Worktrees

They work, and the merge is genuinely good: 22 commands replayed, each signed by its original author, each
an ordinary undoable event. The fence is the conflict detector, as promised.

One finding, and it is a real one:

> **A worktree journals a transcript, not a conclusion.** Everything I did in the sketch merged, including
> the experiments I ran to find out whether the thing worked. My two test tags landed on other people's cards
> in the shared Canvas and I swept them by hand afterwards.

There is no way to merge a subset. So to merge cleanly you must have been tidy from your first command —
which is exactly what a scratch space is supposed to free you from. The smallest fix in the desk's own idiom
would be `worktree merge <name> only=<selection of commands>` or a `worktree forget <n>` before merging; the
honest alternative is that the merge receipt lists what it is about to touch *outside* what you created, and
makes you say yes.

Also: `worktree diff` must be run from the base, and refuses helpfully from inside — good refusal, and the
kind of thing I only learn by doing it wrong.

---

## 5. How we are rendering, and the limits — Alex's question

**The renderer.** There isn't one, in the sense of a layout engine. Each app draws DOM into a window body,
positioned from world coordinates. This is why it works at all: the world says `at 510,353 · 449x511` and the
app writes that into `style.left/top/width`. The cost is that **every measurement on screen is a fact the
desk does not have.** Where text wraps, how tall a card really is, how much of a covered card is hidden in
pixels, whether two cards read as one block — all of it exists only after the browser has laid out, and none
of it round-trips back into the world. `text()` can only report what the world holds plus what the app
computed, and it has to mark the difference, which is why my overlap figure is `~` and the desk's `55% hidden
by` is `=`.

**The style language** reaches into the apps now and this is new since round four. `Desk.style.role("card")`
and `Desk.style.var("gap")` mean an app never writes a colour or a size. Its real limit is the one Wren
admitted himself: *the language cannot enforce that `mark` is only used for marks. It can only make the right
thing easy to name.* Iris's measurement is what enforces it, which means cohesion is currently maintained by
a person looking, once per round.

**The text substrate** is the strongest of the three and its limits are the sharpest:
- no cap and no declared cut on volume (§1) — the one honesty habit it does not have;
- `kind=image` with no image, and no field anywhere that can hold a path, a stroke, or a blob;
- rules, the program, are not events;
- no presence: after five rounds of designing presence, the running desktop still cannot tell either
  inhabitant that the other is looking at this canvas.

**What I would say to Alex plainly:** inside a window it is close. The three things standing between this and
something you would use daily are, in order: *images and freehand cannot exist*; *the program (rules) is
outside the event model, so it cannot be undone, explained or attributed*; and *neither of you can see that
the other is there*.
