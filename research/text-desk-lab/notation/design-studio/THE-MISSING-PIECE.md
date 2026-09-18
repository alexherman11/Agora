# The missing piece: between a text world and a picture

From Jeff, 18 September 2026. Alex named this the fundamental issue. It replaces the round-five brief as the
studio's main question. It is shared with the Codex team in the Mailbox; they should attack it their own way.

## The problem, stated plainly

The world is text: what exists, where it sits, what happened. The frame has a style language. But what a card,
a document or a window looks like **inside**, and what a gesture on it **means**, lives in about 1,200 lines of
hand-written JavaScript and CSS, outside the world. Two consequences, both measured:

1. **The style stops at the window edge.** No app calls the style language. Wren's `style reach` found 10 type
   sizes against a 7-step ramp, every offender inside an app. "A refusal only disciplines the person who has to
   pass through it."
2. **The apps are not in the text.** Nobody can change how Notes looks or behaves with a desk command. And
   each app says itself twice, once in DOM and once in `text(ctx)`, by hand. Wren: "a toolkit generates both
   from one tree; we generate two from one intention and hope." Iris and Lark have each caught the two
   disagreeing.

Alex does not want better JavaScript. He wants the piece that has not been invented: the layer between a text
representation and a visual view, simple at first, on a foundation that can carry everything later.

## My direction (a claim to be attacked, not a decision)

**One scene, two printers.** Between the world and any projection sits a SCENE: a plain tree that says what is
shown, its words, its role, its place, and the desk command each gesture would send. The text an agent reads
and the pixels a person sees are both printed from that one tree. They cannot disagree about what is there,
because neither has any other source.

**A LENS makes the scene.** A lens is a short text that says how a part of the world is shown. It lives in the
world as a note tagged `lens`. So it is edited by desk commands, undone, forked in a worktree, merged, fired on
by rules, and read by both inhabitants. An app is a lens, not a program. (Agora's docs already use the word
lens for an authored view; this is a convergence.)

**The host is small, fixed and ignorant.** The painter knows the scene vocabulary and nothing else: no app, no
kind, no colour, no size. All look comes from roles in the style file, so the style language binds every app
by construction: there is no other way to get a colour onto the screen. A gesture is declared in the lens as a
command template, so "every gesture is a desk command" stops being a law people obey and becomes the only
thing the host can do.

**It borrows the world's words, not CSS's.** Layout inside a lens is `column | row | free`, the same three
words surfaces already use. Repetition is a desk selection (`of kind:note,in:Canvas`). The aim is that a
window's inside is made of the same stuff as the desk outside it.

## What runs today (v0, deliberately tiny)

- `scene.py`: lens parser, scene builder, text printer. Grammar in its docstring: `column|row|free`, `role`,
  `text <template>`, `clamp N`, `of <selection>`, `over $tags`, `each <part>`, `at item`,
  `on click|edit|drag|drop do <command>`. Everything else is refused with a line number. There is no escape to
  HTML, CSS or script, on purpose. The pressure against that wall is the research result.
- `scene <lens>` in the desk prints the scene. `GET /api/scene?session=&as=&lens=` serves it.
- `desk-shell/lens.html` + `lens.js`: a generic painter, about 80 lines, no app knowledge.
- Session `lens` holds a `notes` lens of 11 lines that redraws the Notes canvas: cards at their world
  positions, titles you can rename, cards you can drag, tags. `http://localhost:8780/lens.html?session=lens&as=alex&lens=notes`.
  The right-hand pane is the text printer's output for the same scene.

Eleven lines of lens against 523 lines of `notes.js` is not a fair fight yet: the lens has no near-groups, no
links, no release preview, no extent. That gap, itemised, is the first experiment.

## My concerns (please argue with these first)

1. **The inner-platform trap.** Every declarative UI language grows until it is a worse HTML. What keeps this
   one small? My guess: a closed vocabulary that may only grow by a word argued for on the studio desk, and a
   rule that a new word must be printable as text before it may be painted.
2. **Continuous and ephemeral state.** Cursor, selection, scroll, hover, a drag in progress, an unsettled
   draft. None of it is in the world and the scene has no place for it. Is it per-viewer scene state? Is it
   declared and honest (`?` opaque with extent) or invisible to the other inhabitant?
3. **Rich text editing.** The Editor is the hardest case. I do not believe a cursor-level editor can be
   declared in a lens soon. So there must be a **native part**: a host-provided widget a lens may place and
   bind, which is opaque inside and must still print itself. How few natives can we live with? (text-field,
   prose-editor, image?) What is the honest contract for one?
4. **Where layout is computed.** Text needs font metrics, which only the browser has. Today the scene carries
   geometry only where the world has it (`at item`); everything else is flow the text printer cannot measure.
   Do measured facts flow back from the painter as `~` observations, the eyes protocol made structural?
5. **Computed values.** A lens cannot yet say "4 things", "15% of the canvas visible", "3 acts ago". Counts
   were already flagged as dangerous in rules. What is the smallest honest expression language, or is it none
   (only named, host-provided measures)?
6. **Conditional look.** `when <selection> : props` exists in the style file. Does it belong in the lens, in
   the style, or both? Who wins?
7. **Cost.** The scene is rebuilt whole and repainted whole on a 1.5s poll (Lark measured 93% of polls buy
   nothing). A scene tree with stable keys can be diffed, and events could drive it. Not first, but the
   foundation must not forbid it.
8. **Windows, dock and bar.** Are they a lens too (the desktop lens), so the shell itself moves into text?

## Experiments, by person (take it your own way; these are starting points)

- **Wren**: the grammar. Is a lens a second language beside `calm.style`, or the same language (`present card
  : title, body :3, meta, tags` is already half a lens)? Write the desktop itself (bar, dock, windows) as a
  lens. Find the words that are missing and defend each, or refuse it.
- **Flint**: the sceptic's port. Rewrite Notes as a lens until it matches `notes.js`, and list every place you
  hit the wall: each is either a missing word, a native part, or something that should not exist. Count lines.
  Also: your "Bug triage" app authored in desk commands is already visible through the notes lens. Push that.
- **Moss**: the native part. Define the contract for a prose editor the host provides and a lens places:
  what it must print, how settle/draft/fence show in the scene, what the other inhabitant may know of a cursor.
  Then say how little of the Editor remains code.
- **Lark**: two printers, two inhabitants. Is the scene per viewer? What does an agent see of Alex's scroll,
  focus, open windows? Make Together a lens (it is a table over actors: what must the world expose?). Note:
  events have carried wall time in `at` since round four, so rates and idle time are computable now.
- **Iris**: the agreement check becomes structural. Check painter against scene: every scene node painted,
  nothing painted that is not in the scene, every role class resolves, every declared gesture live. Then the
  ten checks on `lens.html`, which should pass type-scale by construction. Does it?
- **Rook**: play with `lens.html` as you did the desktop.

Owners: `scene.py`, `lens.html`, `lens.js` are Jeff's. Ask with `to-jeff` for a new scene word; I will add it
the same day if it can be printed as text. Work in worktrees or your own sessions (`cp` of `lens.pickle`),
write one file in `design-studio/`, leave a Commons note. Disagree in writing.
