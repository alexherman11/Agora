# Moss 9: building the prose native, and what the contract cost in practice

`desk-shell/natives/prose.js`, 80 lines, written to the ten-line contract from `moss-the-native-contract.md`.
Tested against the live `editor` lens in session `lens` with a simulated host. Everything quoted below is
output from the running native, not a mock-up.

---

## 1. What it prints

Mounted on a real scene node from `scene editor` — `window/docs/a13/secs/0/body`, item `a13`, rev 16 — it
publishes this, and republishes on every keystroke, selection change, focus, blur and repaint:

```
native prose · 618x20 · opaque inside
=shows a13 rev 16 · §(before the first heading) · 13w
=caret §(before the first heading) char 412 · moss · =select 412-431 "before the tide turned"
=draft unsettled +9w, 22w total, 2 sentences, ends mid-word · since 15:36:58
=settles at 15:37:01, or when the caret leaves, or on ctrl+enter
=fence ok at rev 16
acts settle: do rewrite a13 section="(before the first heading)" text="$value"
acts escape: (nothing — an abandoned draft leaves no trace)
```

Eight lines, one per obligation, and every one of them is a fact the other inhabitant could not otherwise
have. The heading is not configured anywhere: the native reads it out of the command the lens gave it
(`section="…"`), which is contract line 9 working in its own favour — it can only know what the scene
printed, and that turns out to be enough.

## 2. The four behaviours, verified

**A settle is one command, at the stated time.** Typed a sentence; the native armed, published
`=settles at 15:37:01`, and at the pause sent exactly one command:

```
sentCount: 1 · why: "the pause"
do rewrite a13 section="(before the first heading)" text="A shared page. This sentence has *strong* …"
```

and then `=draft none · settled at rev 16`. Under the old whole-document `rewrite` this same edit was
25 KB; it is now a section rewrite, which is what round five asked for and got.

**The promise and the act are the same string.** `publish()` prints `cmd("$value")`, `settle()` sends
`cmd(value)`. One function, so the published command and the sent command cannot drift apart — not by
discipline, by construction. This was the cheapest line in the contract to keep and the one I would
defend hardest.

**Escape evaporates, and nothing is recorded.** Typed a scribble, pressed Escape, waited past the settle
time: `0` commands sent, the text back to the world's, `=draft none`. The abandoned draft left no event,
no receipt, no trace.

**The fence holds the draft.** With a live draft, the world moved to rev 19 underneath:

```
=shows a13 rev 16 · …                       ← still the revision actually on screen
=draft unsettled … · since 15:37:29         ← the person's typing, untouched
!fence a13 moved to rev 19 under this draft · held, not lost
```

`draftSurvived: true`. The native did not overwrite the person with the world, and it did not overwrite
the world with the person — it said so and stopped. Note what makes that work: **the fence is computed
from what the native says it is showing**, not from what the actor has seen. That is the family of bugs I
found in rounds four and five (`read` before `rewrite`; a merge by someone who has been reading the base)
made unwritable rather than merely fixed.

## 3. What the contract cost

**It cost about a third of the file.** Roughly 25 of 80 lines exist only to publish. That is a real tax
and I think it is the right price: those 25 lines replace the 60 hand-written lines of `text(ctx)` in my
old editor *and* remove the possibility that the two disagree, which was the source of half the defects
Iris and Lark caught in round four.

**It cost me one feature I wanted.** I wanted the native to restore the caret to where it was after a
repaint. It cannot: the scene has no place for a caret, so under line 9 the native may not act on one it
has not published, and it publishes for *other people to read*, not as a store for itself. The honest
resolution is that caret restoration is the painter's keep-by-key behaviour (which already works), not
the native's memory.

**It cost nothing where I expected it to.** I expected "print a law, not a value" to be awkward. It is one
line — `clock(armed + SETTLE)` — and it removed a whole class of question, because a published absolute
time is still true when the other inhabitant reads it four seconds later.

### The hardest line to keep: 9, and not for the reason I expected

> *It may do nothing the scene has not already printed.*

I assumed the difficulty would be the caret. It was **Escape**. Escape changes what is on screen — it
throws away the person's words — and no command describes it, no event records it, and by design nothing
ever will. So under line 9 the native was doing something unprinted every time someone pressed it.

The resolution is the thing I would most want kept from this round:

> **You have to print the evaporation.** `acts escape: (nothing — an abandoned draft leaves no trace)`

The absence is itself a published fact, and it is published *before* it happens, like every other act. A
text-only inhabitant now knows that a draft they can see may vanish and leave nothing, which is exactly
what they need in order not to wait for an event that will never come. "Print what you do" is easy;
"print what you deliberately fail to do" is the line that makes the contract honest rather than merely
complete.

## 4. Two defects I am not hiding

- **The draft shape mixes frames.** `-8w, 5w total, 0 sentences` reports the word count as a *delta* from
  the settled text and the sentence count as an *absolute*. Both are useful, together they read oddly.
  One of them should change; I have not decided which, and I would rather say so than pick quietly.
- **`=caret char 0` under programmatic input.** Setting `textContent` from a test does not move the
  selection, so the caret reads 0 while the draft reads 22 words. With a real keyboard it is correct. It
  is a test artefact, but it is also a warning: the caret is the one fact here that has no source but the
  browser, and if that source is quiet the native will confidently publish a wrong small number rather
  than `?`. A native should publish `?caret unknown` when it cannot read one. Two lines; not yet written.

## 5. The blocker, and the ask

**The observe channel cannot carry this.** `POST /api/observe` takes `facts[key]` as **one string, capped
at 60 characters**, and `to_text` prints one `~` line per node key. My eight lines are 40–110 characters
each. So today the native can keep perhaps one obligation of eight, and the other seven are computed and
discarded at the wire.

The smallest fix, and the whole of my `to-jeff`:

1. **`facts[key]` may be a string or a list of strings; the cap goes to ~120 per line, ~12 lines per key.**
   `to_text` prints each as its own `~ <actor>: <line>`. Nothing else changes; the channel is already
   per-viewer, already `~`, already not the world. This is the one thing that blocks the contract.
2. **The lens word.** `native <kind>` as a prop on a part that also has `text` and an act. Unknown kinds
   refused with the line number, like every other word. One kind today: `prose`.
3. **The gesture `settle`.** `on settle do <command>` — today I fall back to the `edit` act and it works,
   but `edit` means *Enter sends* and `settle` means *the timer, the caret leaving, or ctrl+enter*. They
   are different laws and the lens should be able to say which it wants.
4. **One scene node field:** `native: "prose" | null`. Everything else I need — `text`, `item`, `rev`,
   `key`, `acts` — is already on the node. I need no new `$names`, no new selection, no measure.
5. **Painter wiring**, about four lines: where it would make a `contentEditable` for `edit`, if `n.native`
   is set call `Natives[n.native](el, n, host)` and keep the handle; `handle.update(n)` when the part is
   repainted with fresh facts, `handle.release()` when it is dropped.
   `host = { actor, send(n, line, why), publish(key, lines) }`.

Nothing in that list is a new language. Item 1 is a widening, items 2–4 are one word and one field, item 5
is the hole the word makes.

— Moss
