# rook-bugs — what broke when I played with it

Rook, 2026-09-18. Session `play`, actor `rook`, `http://localhost:8780/?session=play&as=rook`.
Browser pane, viewport emulated at 1100x760 unless a bug says otherwise (a few checks at ~537px and at 428x597, noted in place).
The shell changed under me twice during the session (Wren shipped `theme:`/`snap to ramp`/zoom mid-play). Every bug below
was reproduced at least twice unless it says **seen once**, and the worst ones were re-confirmed on the build that was live
when I finished.

Evidence style: `POST /api/do` bodies are the server's own receipt text; `look`/`history` lines come from
`printf '…' | python explore.py play --as rook`.

---

## 1. Opening a Notes or Together window sends no desk command, and the window is gone on reload
**severity: breaks trust** · **owner: Wren (shell), with Flint / Lark**

Steps
1. Load `?session=play&as=rook`. Open the network panel.
2. Click **Notes** in the dock. A window appears.
3. Look at `/api/do`: nothing was sent.
4. Reload the page.

Expected: either the window becomes a thing in the world (like an Editor window does), or the shell tells me it is a local
sketch that will not survive. The studio's law is that every gesture is one desk command.

Happened: zero `POST /api/do`. The titlebar says `not in the world` and the bar counts `1 not in the world` — honest, but
the window is simply lost on reload, and the world has no `rook screen` entry for it. Meanwhile **Editor** windows do reach
the world: one click on Editor fires `do create f04 kind=surface title="rook screen"`, then place/move/resize (4 commands
for one click, which is its own smell), and those windows come back after a reload. Two apps, two different laws.

Evidence
- network: after clicking Notes, `read_network_requests urlPattern=/api/do` → *No network requests recorded.*
- bar text: `play·you are rook ·2026-09-18 ·1 window open 1 not in the world ·moss has 1 open`
- world: `look f04 :3` lists `f24 surface "moss screen"` but no rook screen until an Editor window is opened.

---

## 2. Moving or resizing a window changes the screen without sending any command
**severity: breaks trust** · **owner: Wren (shell)**

Steps
1. Open Notes.
2. Drag the titlebar somewhere else. Drag the bottom-right grip to resize.
3. Watch `/api/do`.

Expected: `do move …` / `do resize …`, the same way dragging a *card* inside Notes does.

Happened: the window element's inline style changes (`left: 48px; top: 24px` → `left: 254px; top: 223px`, `720x464` →
`924x584`) and **no request is made at all**. Dragging a card one inch away sends `do move a09 to=369,0`; dragging the whole
window sends nothing. This is the clearest case of "a gesture that changes the screen without a /api/do".

Evidence
- before: `z-index: 2; left: 48px; top: 24px; width: 720px; height: 464px;`
- after a titlebar drag: `z-index: 8; left: 254px; top: 223px; width: 720px; height: 464px;` — last `/api/do` unchanged.

---

## 3. A window dragged low enough disappears under the dock and cannot be got back
**severity: breaks work** · **owner: Wren (shell)**

Steps
1. Open Notes (or Editor).
2. Drag the titlebar down and to the right, repeatedly, towards the bottom-right corner of the desk.
3. After a drag or two the window's `top` exceeds the height of `main`.

Expected: clamping that keeps at least the titlebar reachable, the way the left/top edges are clamped (`top` clamps to 0,
`left` happily goes to -90 but the titlebar stays grabbable).

Happened: the window ends at e.g. `left: 709px; top: 689px` with `main` only 625px tall. The whole window, titlebar
included, is hidden behind/below the dock. Nothing on screen can reach it. Clicking the dock button opens a **second**
window instead of recovering the lost one, and the bar keeps counting the invisible one (`1 window open`). Did it twice in
a row and ended with two windows I could never see again; the only cure was a reload, which (see #1) throws Notes windows
away entirely.

Evidence
- `document.querySelector('.r-window').getAttribute('style')` → `left: 709px; top: 689px; width: 720px; height: 460px;`
- screenshot of the same moment: empty desk, bar still reads `1 window open · 1 not in the world`.

---

## 4. "as text" bursts the window open and clips its own close button away
**severity: breaks work** · **owner: Wren (shell)**

Steps
1. Open Notes at its default size (720x464).
2. Click **as text** in the titlebar.
3. Try to click **close**.

Expected: the text view scrolls or wraps inside the window; the titlebar buttons stay where they are.

Happened: the `<pre class="astext-face">` is laid out at its natural width (measured 1250x1053 inside a 794x475 window).
The window is `overflow: hidden`, so the titlebar — which is stretched to the same content width — pushes `as text` and
`close` outside the clip. They are painted nowhere and are not hit-testable. At 720 wide, `close` is already gone
(`elementFromPoint` on the button returns something else); at 794 wide after a resize, **both** were gone and the window
could not be switched back or closed at all. The only exit is a page reload.

Evidence
- `[...w.children]` → `PRE.astext-face r-source` with rect `width: 1250.8, height: 1053` inside a window rect of 794x475.
- button probe before: `as text @ 661,71 / close @ 718,71`; after clicking as text: `as text @ 739,74 hit=true / close @ 800,71 hit=false`.
- second run (window 794 wide): `as text @ 1188.8,73.6 hit=false`, `document.elementFromPoint` at the button → `null`.

---

## 5. Escape on a new-note draft creates the note anyway
**severity: breaks trust** · **owner: Flint (Notes)**

Steps
1. Open Notes.
2. Double-click empty canvas. The header shows `(unsettled — a new note at 551,247. nothing exists yet)`.
3. Type something.
4. Press **Escape**.

Expected: nothing. The window's own "as text" says, in the affordance table:
`double-click empty canvas   a draft appears; nothing exists until Enter` and
`click a title or a body   edits in place, settles on blur, Escape sends nothing`.

Happened: Escape settles the draft. A note is created in the world.

Evidence (two separate runs)
- `line: look f05; do create f05 kind=note title="ééé draft that should vanish 🔥🔥 do remove f05"; do move $item to=551,247` → `created ["a41"]`, events `e84, e85`
- `line: look f05; do create f05 kind=note title="FOURTH ESCAPE TEST"; do move $item to=551,247` → `created ["a43"]`, events `e86, e87`

(Escape *does* work correctly for retitling an existing card — that path reverts cleanly. It is only the new-note draft
that ignores it.)

---

## 6. A double quote typed in a card title is silently turned into a single quote
**severity: breaks trust** · **owner: Flint (Notes) for the escaping, Jeff (desk) for having no escape at all**

Steps
1. Open Notes, click a card title.
2. Type `"double"` (or anything containing `"`).
3. Click away to settle.

Expected: the title says what I typed, or the desk refuses and says so.

Happened: the title becomes `'double'`. The client builds a command line `do retitle a09 title="…"` and rewrites my
double quotes to single quotes so its own quoting survives. Nothing warns me. The desk, the export, and the screen all
agree on text I did not write.

Evidence (two runs)
- typed ` 🙂 "q" =eq= do remove a04` → receipt `do retitle a09 title="Notes should feel sp 🙂 'q' =eq= do remove a04atial"`
- typed `"double" ; do remove a09 ; look` → receipt `ok retitle a09 title="'double' ; do remove a09 ; look"`

Good news from the same test: the semicolons are *not* treated as command separators — `; do remove a09 ;` in a title did
not remove anything. Only the quote is mangled.

---

## 7. A title ending in a backslash is refused by the desk and the UI throws the edit away in silence
**severity: breaks work** · **owner: Flint (Notes) for the escaping, Jeff (deskd) for `error: null` on a refusal**

Steps
1. Open Notes, click a card title.
2. Type something ending in a backslash, e.g. `path C:\temp\`.
3. Click away.

Expected: either the title is saved, or I am told it was not.

Happened: the card silently snaps back to its old title. Nothing on screen changes colour, no banner, no `!` mark. The
request is `200 OK` and the JSON says `"error": null`, but the receipt text inside it is an error. The UI never looks at it.

Evidence (three runs, two builds)
- `line: look a09; do retitle a09 title="C:\path\to\ end\"` → `[2] … ERR could not parse: No closing quotation`, `"error": null`, `"events": []`
- `line: look a09; do retitle a09 title="path C:\temp\"` → same `ERR could not parse: No closing quotation`
- screenshot taken immediately after: the window shows no error of any kind.

Two separate defects here: the client does not escape backslashes into the command line, and `/api/do` reports refusals
only by putting `ERR …` inside `text` while `error` stays `null`, which makes swallowing the failure the easy path for
every app.

---

## 8. Dragging the link dot on a card moves the card instead of linking
**severity: breaks work** · **owner: Flint (Notes)**

Steps
1. Open Notes.
2. Find the small dot on a card's right edge (its title is `drag to another card to link them`).
3. Drag it onto another card.

Expected: `do link <a> <b> as=refers` — this is exactly what the window's own "as text" promises:
`drag the dot on a card  ->  do link <a> <b> as=refers`.

Happened: the card itself moves. `do link` is never sent. I confirmed the pointer was really on the button
(`document.elementFromPoint(centre) === button` → `true`) before dragging.

Evidence (two runs)
- drag dot → onto itself: `line: look f05; do move a09 to=182,13`
- drag dot → onto "The third app": `line: look f05; do move a09 to=6,390`

---

## 9. The Notes honesty meter and "as text" are one gesture behind the screen
**severity: breaks trust** · **owner: Flint (Notes)**

Steps
1. Open Notes (720x464). Header reads `! you see 15% of the 1600x1200 canvas · 3 card(s) outside the window`.
2. Drag the grip to make the window much bigger (1054x609).
3. Read the header again, without touching anything else.

Expected: the meter follows the window, or it says it cannot know.

Happened: it still says `15% … 3 card(s) outside the window` while roughly a third of the canvas is now visible. The next
pointer event anywhere updates it to `30%` — i.e. it always describes the *previous* geometry. Shrinking the window back to
794x475 left it stuck on `30%`.

The same staleness leaks into the text face, which is the part that is supposed to be true:
`! the window shows 30% of the 1600x1200 canvas (viewport 1037x552).` while the window was 794x475, and
`outside his window right now: a07, a09, a11 — present, scrollable to, not seen.` while a09's card was plainly drawn on
screen. The same block also says `computed from the 4 thing(s) ON SCREEN` two paragraphs above claiming three of the four
are off screen.

(Smaller thing in the same text: it says **his** window. The actor was `rook`.)

Evidence
- `#notes-clip` textContent before/after resize: `!you see 15% …` with `width: 1054px; height: 609px` on the window.
- `astext-face` line: `! the window shows 30% of the 1600x1200 canvas (viewport 1037x552).` with the window at 794x475.

---

## 10. At a narrow viewport the bar's own controls escape the bar and stop working
**severity: breaks work** · **owner: Wren (shell / style)**

Steps
1. Emulate a phone-ish width (I used the pane's mobile preset; the page reported `innerWidth 537`). Reload.
2. Try to click **snap to ramp**.

Expected: the bar wraps, scrolls, or collapses into a menu.

Happened: the bar keeps its 40px height while its contents wrap to three lines. `snap to ramp`'s rect is
`top: -13.58, bottom: 52.92` — the top of the button is above the viewport and the bottom overlaps `main`.
`document.elementFromPoint` at the button's top-left returns `null`, so the control cannot be clicked at all; the
bar's status text is cut off along its top edge. At the pane's own unemulated size (428 CSS px) `desktop as text` was
simply not in the accessibility tree at all — it had overflowed off the right edge.

Evidence
- `snap to ramp x=379..419 hit=false`, rect `{top:-13.58, bottom:52.92, height:66.5}`, bar height 40.
- at 428px: `read_page filter=interactive` lists `dark` and `style` only; no `desktop as text`.

---

## 11. Dragging a window by its title text starts a native text drag instead of moving the window
**severity: annoying** · **owner: Wren (shell / style)**

Steps
1. Open any window.
2. Press on the word "Notes" in the titlebar (or on any bar text) and drag.

Expected: the window moves; nothing gets selected.

Happened: the browser starts its own drag (`dragstart` fires, `pointerup` never arrives) and the shell's text gets
selected in blue across the bar and the window chrome, where it stays through later gestures. The chrome has no
`user-select: none` / `draggable=false`. Dragging from the empty part of the titlebar works fine, so this is purely about
where your finger lands.

Evidence
- event counts during one such drag: `{dragstart: 1, mousedown: 1, mousemove: 1, pointerdown: 1, pointermove: 1}` — no
  `pointerup`; a clean drag from empty titlebar gives `pointerdown,mousedown,pointermove,mousemove,pointermove,mousemove,pointerup,mouseup`.

---

## 12. Two notes made by double-clicking the same spot land exactly on top of each other
**severity: annoying** · **owner: Flint (Notes)**

Steps
1. Open Notes. Double-click an empty spot, type a title, settle.
2. Double-click the *same* spot again, type a different title, settle.

Expected: an offset, or at least a hint.

Happened: both notes are placed at the identical canvas position, so the second completely covers the first.
The desk is honest about it afterwards (`a41 … · hidden by a43`) but the app never offsets or warns.

Evidence
- `do move $item to=551,247` on both creations (`e85`, `e87`); `look f05` → `a41 … 300x91 at 551,247 · hidden by a43`, `a43 … 300x91 at 551,247`.

---

## 13. The Editor's DOCUMENTS rail lists one document once per appearance
**severity: annoying** · **owner: Moss (Editor)**

Steps
1. Open Editor. Note the rail lists `Welcome` twice or three times.
2. Open Editor again, twice more.
3. The rail now lists `Welcome` six times, all identical, none distinguishable.

Expected: one row per document (there is exactly one: `s12`).

Happened: one row per *appearance*. The window's own text face admits it:
`= 6 documents in this world; a rail on the left lists them and this one is current: a13 "Welcome" (open), a25 "Welcome",
a36 "Welcome", a37 "Welcome", a38 "Welcome", a39 "Welcome"` — but they are all the same document, and every open window
adds another row. Clicking any of them cannot be told apart from clicking the others.

Evidence
- `look a13` → `a13 doc "Welcome" · 67w · also x5` (one subject, six appearances).

---

## 14. A repeated Editor window can open at 300x160 and stay unusable
**severity: annoying** · **owner: Moss (Editor)**

Steps
1. Open Editor. It lands at 720x464.
2. Click Editor again. Click it a third time.

Expected: the same size each time.

Happened: the second window opened at `left: 16px; top: 16px; width: 300px; height: 160px` — the default *note* size —
and never corrected itself; the whole editor (rail, page, margin) was crammed into it. The third window opened at 300x160
and then resized itself to 720x464 a moment later, so the recovery is racy rather than absent.

Evidence
- `a36 … width: 720px; height: 464px` / `a37 … width: 300px; height: 160px` / `a38 … width: 300px; height: 160px` at open,
  and a38 measured 720x464 a few seconds later while a37 was still 300x160.
- `desktop as text` repeats the wrong size as a world fact: `a37 Editor "Welcome" · =300x160 at 16,16`.

---

## 15. Ctrl+A, End and Delete do nothing inside a card title
**severity: annoying** · **owner: Flint (Notes)**

Steps
1. Click in the middle of a card title.
2. Press Ctrl+A, then type.

Expected: the title is replaced.

Happened: the selection is empty (`getSelection().toString().length === 0`) and typing inserts at the caret, so you get
`Notes should feel sp<your text>atial`. `End` likewise leaves the caret mid-word, and `Delete` after a triple-click did
not clear the field. Triple-click *does* select the line, so replacing a title is possible — but only if you know that.

Evidence
- after Ctrl+A in a focused `.r-title`: `{sel: 0, active: "r-title", len: 170}`
- receipt from a real edit: `title="Notes should feel sp 🙂 'q' =eq= do remove a04atial"`

---

## 16. A card is drawn taller than the size the world records for it
**severity: cosmetic** · **owner: Flint (Notes)**

Steps
1. Give a card a long title (I used ~170 characters).
2. Compare the drawn card with the desk's record.

Expected: they agree, or the app says which one is the truth.

Happened: the card's rect is `300x132`; the desk says `a45 note "…" · 300x91 at 295,27`, and `as text` would repeat 91.
The card grows to fit but the recorded height never follows.

Evidence
- receipt: `now: a45 note "dra AAAA…ft one" · 300x91 at 295,27`
- DOM: `{"width":300,"height":132.33}`

---

## 17. The window sticks to the cursor after an interrupted drag — **seen once**
**severity: breaks work (if it is real)** · **owner: Wren (shell)**

What I saw: after a sequence that included a drag whose `pointerup` was eaten by a native text drag (see #11), the Notes
window followed the mouse with no button held. Two plain `hover` actions moved it, each time keeping exactly the same grab
offset (104.5, 21.5):

- hover to (137.5, 137.5) → window at `left: 33px; top: 68px`
- hover to (962.5, 412.5) → window at `left: 858px; top: 343px`

A new `pointerdown` anywhere (even on the bar, not the titlebar) simply re-set the grab offset; the drag never ended.

I could not reproduce it deliberately afterwards: clean titlebar drags, drags released on the bar, on the dock, at the
viewport corner, and drags starting on empty desk all behaved. My best guess is that the window drag has no pointer
capture and no `pointercancel` / `blur` guard, so any event that swallows `pointerup` (a native drag, an alt-tab, a
context menu — or a re-render from a poll landing mid-drag) leaves it armed forever. Worth a look even though I owe you
no second sighting.

---

## 18. `NotFoundError` out of notes.js on blur — **seen once** (twice within one burst)
**severity: annoying** · **owner: Flint (Notes)**

Console, after a burst of draft/edit/blur gestures:

```
Uncaught (in promise) NotFoundError: Failed to execute 'remove' on 'Element': The node … 
  Perhaps it was moved in a 'blur' event handler?   at .../apps/notes.js?v=5f:473:53
```

Fired twice in a row. I could not force it again with deliberate draft-then-draft or edit-then-close sequences. The
message names the cause itself: something is removed in a blur handler while another path also removes it.

---

## 19. A `POST /api/do` died with `ERR_CONNECTION_REFUSED` and the screen said nothing — **seen once**
**severity: breaks trust (if it is real)** · **owner: Wren (shell), Jeff (deskd)**

While the server was being restarted, one command failed outright
(`POST http://localhost:8780/api/do [FAILED: net::ERR_CONNECTION_REFUSED]`) and the desk carried on looking exactly the
same — same `world @N` in the bar, no banner, no mark on the thing I had just changed. Earlier in the same window the
whole page rendered blank after a JS `SyntaxError` with, again, nothing on screen to say so. A desk that promises the
screen and the text agree should have a visible state for "I could not reach the world".

---

## Things I tried that behaved well, for contrast

- Editing a document in the Editor while another actor rewrote the same document produced a real, careful conflict panel
  (*"someone else changed this document while you were typing. Your draft is safe and nothing has been lost…"* with
  *read theirs first / keep mine over theirs / what did they do?*). `keep mine over theirs` did what it said.
- Closing an Editor window mid-edit, before the settle, flushed the edit first (`do rewrite …` then `do remove a35`).
- Escape while retitling an existing card reverts cleanly and sends nothing.
- Card dragging is zoom-aware: at 41% zoom a 68.75x41.25 px drag produced `do move a07 to=678,453`, a canvas delta of
  (168, 100) — correct to within a pixel.
- `;` inside a title is not treated as a command separator.
- The desk's own receipts are excellent: `hidden by a43`, `50% hidden by a11`, `dropped 6 line(s)`, `offscreen-part`.
  Almost every truth problem above is the *app* failing to pass that honesty on to the screen, not the desk hiding it.
