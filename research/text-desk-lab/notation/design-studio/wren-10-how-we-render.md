# How we render, and where it is weaker than CSS

Wren, round five. Alex asked plainly: *how are we rendering, and what are the current limits?*
This is the pipeline as it truly is, step by step, with the place each step is weaker than a normal
toolkit named at the step rather than at the end.

Everything here is running at **http://localhost:8780/?session=desktop&as=wren**.

---

## 1. The pipeline, seven steps, world text to pixels

```
 (1) the world          deskd holds one world. Its whole state is desk commands.
       |                `python explore.py desktop --as wren` and the browser are the same world.
       v
 (2) snapshot           GET /api/snapshot -> {subjects, nodes, links, clock, worktree, events_total}
       |                core.js polls every 1.5s; every change anyone makes arrives here.
       v
 (3) the shell decides  shell.js asks: which appearances are on `<actor> screen`? Those are the
       |                open windows. Their x,y,w,h ARE the window geometry. Nothing else is.
       v
 (4) app draws          each app's open(host, ctx) builds DOM. The shell never draws app content.
       |                the app also implements text(ctx): the same window, in words.
       v
 (5) the style resolves style/style.js parses style/calm.style at runtime:
       |                tokens -> :root custom properties (--t-paper, --t-size-0 ..)
       |                roles  -> one class each (.r-card, .r-title ..)
       |                when <selection> clauses -> which role a thing takes
       v
 (6) the browser lays   flex/grid from shell.css (arrangement only: no colour, size, family or
       |                spacing lives there), then paint.
       v
 (7) the eye / the text Iris measures the pixels. `desktop as text` prints the same screen in words
                        and names what it does not carry.
```

Two properties this has that a normal toolkit does not. **Step 3 is reversible**: drag a window and
the shell sends `do move a25 to=424,96`, which appears in the *said* panel and is undoable, and the
other inhabitant's bar says `wren has 3 open`. And **step 5 is data**: the whole look is one text
file the running page re-parses on demand, and a style that does not parse is never installed, so
the last working desktop survives by construction.

## 2. Where each step is weaker than CSS or a normal toolkit

**(2) snapshot.** 1.5s polling, whole-world each time. A normal toolkit has a change notification
with a payload; we have a poll and a diff. Typing latency inside an app is fine because the app owns
its DOM, but *anything the world must confirm* costs up to 1.5 seconds. There is no partial update.

**(3) geometry.** Windows are honest, and the honesty is the cost: **every drag is a server
round-trip**. A native window manager moves at 120Hz with no I/O. We move at mouse-up, and the
intermediate positions are deliberately not recorded. That is the right trade — but it means
snapping, magnetism, live tiling and anything that reacts *during* a drag would each need a local
prediction layer we do not have.

**(4) apps.** Nothing in the substrate constrains an app's DOM. An app can write any CSS it likes in
its own `<style>` tag, and today three of them do. See §4 — this is the largest hole.

**(5) style.** The list is long enough to be its own section; see §3.

**(6) layout.** *The notation says nothing about arrangement at all.* Every flex, grid, position and
overflow rule in the desktop is hand-written CSS in `shell.css`. `calm.style` can say that a card
has a border, a radius, a padding and a type size; it cannot say that cards stack in a column with a
gap, that a rail is 240px and fixed, that a window body scrolls while its titlebar does not. This is
the single biggest gap between this language and CSS, and I do not think it should be closed by
adding flexbox to the notation — that road ends at CSS with extra steps.

**(7) the text face.** `text(ctx)` is written by hand per app, so it can disagree with the screen.
Iris found exactly that in round four: Lark's *Screen vs text* section existed on screen and not in
its own text. A toolkit generates its accessibility tree from the same tree it paints; we generate
two things from one intention and hope.

## 3. What the style language cannot say today

Measured against the desktop that is running, not against theory.

| it cannot say | what happens instead | could it? |
|---|---|---|
| **arrangement** — flex, grid, column, scroll, fixed rail widths | hand-written `shell.css` | yes, and I think it should not |
| **a texture** — the hatched band every honesty mark now uses | hand-written `shell.css`, colours from tokens | **yes, and this is the one I would add next** |
| **state** — hover, focus, pressed, drag-over | not expressed at all; nothing on this desktop has a hover state | yes: `role tool:hot`, blocked only by the selection colon, which the spaced ` : ` already solved |
| **motion** — a window settling, a panel opening, anything easing | nothing moves; every change is instant | partly. duration is a token; an easing curve is a texture-shaped problem |
| **density** — comfortable/compact as one switch | only by editing `gap`, which moves every space equally and is a blunt instrument | yes, and cheaply: density is a second multiplier on the spacing scale, exactly as `ramp` is on type |
| **type scale inside an app** | it *can*, via `--t-size-0..3`, but nothing makes an app use it | see §4 |
| **a second theme that is genuinely different** | see §5 | see §5 |
| **data colour** — a ramp, a heat map, nine series | still the hole named in round one | still unsolved |

Two smaller ones found by building: there is no way to say **"this colour means one thing"** (Flint
ran out of `accent` because honesty marks and ordinary affordances were both reaching for it — fixed
this round by adding a `mark` token, but the language cannot *enforce* that `mark` is only for
marks); and there is no way to say a length **relative to a parent** (`width 46em` works, `width
half` does not).

## 4. How far the one style actually reaches: a number

New this round, in the bar: **style reach** and **snap to ramp**.

`style reach` lists every element on the desktop whose type size is not a step of the ramp, and who
drew it — the honesty mark for the style itself. `snap to ramp` then forces every one of them to its
nearest step. The difference between the two is the measurement:

```
the ramp, from calm.style: -3=10px -2=11px -1=13px 0=15px +1=17px +2=20px +3=23px

ramp off:   10 distinct sizes on the desktop — 10.5 11 11.5 12 12.5 13 13.5 14 15 23
ramp on:     5 distinct sizes — 10 11 13 15 23, every one a step
            27 elements forced, all of them inside apps, none in the shell
```

**That gap — ten scales versus five — is the exact distance between a style that is available and a
style that is binding.** The shell has been on the ramp since round four. The apps are not, because
nothing makes them be: an app writes `font-size: 11.5px` in its own `<style>` tag and the style
language has no opinion, no refusal and no knowledge.

Snapping is a demonstration, not a fix. It overrides authored intent with `!important` and it cannot
tell a heading from a caption, so it makes the desktop *consistent* and slightly *wrong*. The real
fix is one of three, and I would take the third:

1. **Convention** — ask nicely. Tried; it produced this measurement.
2. **Force** — the shell snaps everything, always. Consistent, and it steals a decision the app
   owner is better placed to make.
3. **Refusal with a name.** The style installs a `#one-style` sheet; app sizes could be *required*
   to come from `var(--t-size-N)`, and the reach report becomes a check that fails the build. The
   refusal already exists for `calm.style` itself — `"text at 0.94" is not a step` — and it has
   never once fired in anger, because the only person who writes that file is me. **A refusal only
   disciplines the person who has to pass through it.** That is the finding of this round.

## 5. A second theme that is genuinely different — and its ceiling

My rule since round one: *a theme may redefine tokens, never roles.* I tested it this round by
writing a theme that is not "dark":

```
theme print of calm
  token paper  = #F3EFE7      token ink    = #221E17
  token card   = #FBF8F2      token accent = #6B4A2F
  token sheet  = #FFFFFF      token mark   = #7A2E2E
  token text   = serif 17/1.62
  token ramp   = 1.26
  token gap    = 10
```

It works, and further than I expected: the whole desktop becomes a warm serif surface at a wider
type ramp (8/11/13/17/21/27/34 instead of 10/11/13/15/17/20/23) on a 10px spacing step. Family,
size, rhythm, spacing and palette all move together from nine lines.

**The ceiling is shape.** `print` cannot remove the border from a card, round a corner differently,
drop the window's shadow, or make the dock a side rail — because all of those live in roles, and a
theme may not touch roles. And "genuinely different" in real design usually *means* shape: a poster
theme and a document theme differ in what has an edge, not in what colour the edge is.

So the honest statement of my own rule after testing it: **a theme can change everything about how
the desktop sounds and nothing about how it is built.** I still think that is right for a shared
desktop — two inhabitants should never see different structures — but I no longer claim it covers
what people mean by a theme. A third thing is missing between "theme" and "fork the style": a way to
say *this role, differently, under this name*, scoped and declared. I have not designed it.

## 6. What I fixed this round, from other people's findings

- **The boot guard** (Lark, `a474`). The shell now boots without the style: the dock builds, apps
  register and open, and a hatched band at the top says *"style is not loaded: everything below is
  unstyled"*. Testable on purpose with `?style=off`. A missing part subtracts itself and says so.
- **`said` over the bar** (Iris, pass 3; it had grown 470→516px). It is `position: fixed` between
  the bar and the dock and can cover neither, by construction rather than by choosing numbers.
- **The bar's buttons kept a light background in dark** (Iris, pass 9). `#bar button` never had
  `background: transparent`; three pale chips floated on a dark bar. One line.
- **`grid-8`.** Bar, dock and titlebar heights are now declared in gap multiples instead of coming
  from content, and the window cascade is on the grid (32/24, not 34/30). Iris: *every failure is in
  thirds* — 718.67, 44.17, 72.83. Those are 2/3 of a pixel, which is a **1.5× device pixel ratio**
  snapping CSS pixels, not a layout bug in my file. I can put my own boxes on the grid; I cannot make
  a 1.5× screen stop rounding. Iris, if that check is meant to pass it should measure in device
  pixels, or exempt anything whose remainder is a multiple of 1/3.
- **The as-text panel truncating in silence at 640px** (Flint, `a515`, relaying Iris). It wraps now,
  and if it ever still clips it appends a hatched footer saying how many pixels and of how many
  characters. The one surface whose whole job is completeness may not fail quietly.
- **`mark` and `sheet` tokens** (Flint `a455`, Moss `a511`). `mark` is a fourth ink for honesty
  marks only, so they stop wearing the accent that also means "link" and "filter chip". `sheet` is
  the paper *inside* a window, so a page can look like a page. Both are in every theme.
- **Worktree in the bar**: if the snapshot carries a worktree, the bar says so on a hatched band —
  *you are not in the base world* is exactly the kind of thing a desktop must not whisper.

## 7. What I would do next, in order

1. **Texture in the notation.** The best construction anyone has made in five rounds is a hatched
   band, and the style language cannot say one. Everything hatched on this desktop is hand-written.
2. **States.** Nothing on this desktop has a hover state, which on a real desktop is not minimalism,
   it is a missing affordance.
3. **Make the ramp binding, by refusal rather than by force** (§4.3).
4. **Density as a second multiplier**, so "compact" is one word rather than a re-tuned `gap`.
5. Then, and only then, arrangement — and I would still rather find that it belongs to the world's
   `row`/`column`/`free` than to the style file.
