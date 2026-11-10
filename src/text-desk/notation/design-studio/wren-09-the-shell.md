# The shell, and what one style costs when four people draw

Wren, round four. I own `core.js`, `index.html`, `shell.js`, `shell.css` and `style/*` in
`desk-shell/`. Open it at **http://localhost:8780/?session=desktop&as=wren**.

## 1. An open window is a fact in the world

The question shell.js left open. My answer, built rather than argued:

> A window showing a thing is an **appearance of that thing on a per-actor free surface called
> `<actor> screen`**, carrying the window's x, y, w, h.

No new server feature was needed; the desk already had the concept. Opening the Welcome doc runs

```
do place s12 into=f24      do move a25 to=48,24      do resize a25 to=720x460
```

— all three visible in the *said* panel, all undoable, all replayable. Dragging a window is
`do move`. Closing is `do remove`, so a window closed by mistake comes back with `undo`. A reload
rebuilds your desktop from the world, not from a cookie. And my top bar now truthfully says
**`moss has 1 open`** — the first time in four rounds that one of us has perceived another through
the world rather than through a file.

What is *not* in the world, named as omissions in "desktop as text" rather than left silent: which
window is in front, scroll position, and whether a window is showing its text face. Per-eye and
per-moment.

The cost I am unsure about: opening a window is now an event, so a busy morning fills history with
window management. If that is noise, the fix is a quieter event, not a private window.

## 2. The style language, made real for four people

`style/calm.style` is the one style; `style/style.js` parses it at runtime with every round-three
fix in it — the spaced ` : ` separator (the desk's selections use colons), `on <colour>` for
background and a bare colour for foreground, `present` for which parts are drawn, and the stepped
type ramp with its refusal.

`shell.css` now contains **no colour, no font size, no font family and no spacing value**. That is
Iris's round-three catch made structural: she measured four sizes on a page whose ramp had three,
and the fourth came from the page's own stylesheet. What is left in `shell.css` is arrangement —
grid, flex, position, overflow — which the notation admits it cannot say.

For app owners there are two ways to use it and no third:
`Desk.style.role("card")` → `r-card`, and every token as a custom property, `--t-paper` *and*
`--paper`, with aliases for the names the apps were already written against.

**A refused style is never installed, so the last working desktop survives by construction.** Type
`on #eeeeee` into the style panel and press apply: the refusal prints with two runnable escapes and
the desktop keeps drawing. That is the answer I gave the Astra team in round two, now running.

### The bug that proves the point

`token paper = #FBFAF7      # the desktop itself` — the trailing comment was swallowed into the
value, `paper` stopped being a colour, and the whole desktop drew with no background *and said
nothing about it*. A comment marker is now `#` at line start or ` # ` with a space on each side,
because `#` also begins every colour. Two rounds of example text never contained a trailing comment.

## 3. Honesty marks are a property of the surface, not a character

Iris, across four prototypes: *"each of you invented a way for the screen to admit what it does not
know, and each of you then drew it quieter than the thing it is warning about."* Mine was the
worst of the four — a desk showing 26% of itself with nothing but a scrollbar.

So in the shell an omission is now a **hatched band**, not a glyph: `1 not in the world` and
`3 off the stage` sit on a 45° hatch in the warn token, and the stage itself grows a hatched border
when a window is off it.

**Declared notation gap:** `calm.style` cannot say a texture. The colours in that rule are tokens;
the 45° repeat is arrangement I had to write in `shell.css`. The best honesty mark anyone made
today is a texture, and my style language has no word for one. That is the next thing I would add,
and I do not yet know how to add it without opening the door to gradients in general.

## 4. What one style costs when four people draw

I measured the running desktop: **eleven distinct font sizes**, 10.5px to 23px, including 13.33 and
12.5. My own chrome is four (23/15/13/11, and the 11 is an app's). The one style exists, is
installed, and is available — and three apps still write their own px, because they were written
before it landed. Posted as `to-flint`, `to-moss`, `to-lark` with the exact role names.

This is the round's real finding and it is about people, not parsers: **a shared style is not
enforced by existing; it is enforced by being the only thing that works.** My refusals stop *me*
writing a hex in `calm.style`. Nothing stops an app owner writing one in their own file. The next
version of this should make the desktop *report* which surfaces are off the ramp — an honesty mark
for the style itself, on the same principle as everything above.

## 5. Asked and answered

Asked of Jeff (`to-jeff`): `do place` should name the appearance it created; an **appearance**
should be able to carry props, so a window can say which app it is rather than being guessed on
reload; and `do remove` of your own appearance should not hit the seen fence, for the same reason
`create` and `comment` no longer do.

Asked of the app owners: take sizes from the ramp, take colours from tokens, and ask me for a role
rather than inventing a colour.

Received: nothing tagged `to-wren` yet. I have added the aliases the apps were already using so
that nobody's work broke when the placeholder tokens were replaced.
