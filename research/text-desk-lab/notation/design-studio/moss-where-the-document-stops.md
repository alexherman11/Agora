# Moss 7: where a text-defined document stops

Round five. I pushed the Editor toward the Google-Docs feel Alex asked for, then pushed until things
broke, and measured rather than argued. Everything below is a number from the running system on
2026-09-18, or a transcript. Session `desktop`, worktrees `desktop@moss5` and `desktop@rw`.

---

## 1. The headline: reading scales, writing does not

I generated a 4,061-word document (12 sections, 24,602 characters) and put it in a worktree.

**Reading it costs almost nothing.** Measured output, in characters:

| command | output |
|---|---|
| `look Shared :2` | 490 |
| `read a35` (the section list with word counts) | 818 |
| `examine a35` | 1,660 |
| `read a35 #3` (one section) | 2,023 |
| the Editor's own `text()` on the 4,061-word doc | **1,254** |

The three reading axes are effectively logarithmic in document size. That is the single best property
this substrate has, and it is not an accident — `look`/`read`/`examine` were designed for a reader
with a budget. A text-only inhabitant can hold a 4,000-word document in view for about a kilobyte.

**Writing it costs everything.** Same document, one word changed:

```
create:                     24,816-character command line
receipt for that create:    ~25,000 characters (the whole text echoed back)
one-word rewrite:           50,795 characters of output for one word
worktree diff of that edit: 50,307 characters
```

The Editor now prints this on the page, measured, in the margin of whatever you have open:

> `!` a settle rewrites the WHOLE document. One typo here sends 24,618 characters and the receipt
> echoes them back, so one word costs about 49.2k either way. The desk has no section-scoped rewrite
> yet; filed to-jeff.

So: **1.2 KB to read a document, 49 KB to change one word in it.** That asymmetry is where a
text-defined document stops, and it has one cause — the only verb that edits prose replaces all of it.

### Two consequences that are not obvious

**The receipt is the bigger half of the problem, not the command.** A command carrying the whole
document is at least *necessary* under `rewrite`. Echoing it back is not. The desk's own rule is that
a receipt says what changed and where things now are; at 4,000 words it says *everything*, which is
the same as saying nothing. A receipt should summarise a large value — `text=<4,061 words, 12
sections, +3w −1w>` — and leave the detail to `why`. That is a one-line change with a large effect on
what it costs an agent to live here.

**`rewrite <id> #<section>` is not a nicety; it is what makes worktrees usable for documents** (§3).

---

## 2. What I built into the Editor this round

All of it in `desk-shell/apps/editor.js`, my file, every change through `Desk.do`.

- **One type scale.** Iris measured seven sizes in my editor (11/12/13/14/15/16/26) and `11.5px`
  invented three times across the desktop. It is now four, all whole pixels: **12 / 14 / 16 / 26**,
  verified from the live DOM. Honesty marks moved off `--quiet` to a `--mark` token (falling back to
  `--ink` until Wren defines it), because the studio's recurring defect is drawing the warning quieter
  than the thing it warns about.
- **Elapsed time is now measured, not guessed.** Events carry `at` (wall time) since my round-four
  request landed, so the editor prints `=alex: edit here, 14s ago (the desk's own wall time on the
  event)` instead of last round's `~…(seen by this page)`. The `~` fallback is still there, for an
  event with no `at`, and still says which it is.
- **Rich formatting, as a rendering and never as state.** A `read as a page` toggle renders the four
  inline characters the studio agreed (`*strong*`, `/slant/`, `` `mono` ``), `- ` bullets, and the
  desk's own `- [ ]` checklists. Verified live: 1 strong, 1 em, 1 code, 4 list items from one
  paragraph. **The page view is not editable**, and `text()` says so:
  `= view: rendered page (*strong* /slant/ `mono` and - bullets drawn; not editable — the text below
  is the document)`. That boundary is my answer to "rich text": *formatting is a rendering of the
  text, so the moment you want to type, you are back in the text.* Nothing is stored twice, so
  nothing can disagree.
- **Selection and cursor are now facts a blind reader gets.** `= caret §1 What this is char 412,
  selection 412-431 "before the tide turned"`. Measured inside the section, so it survives the
  document growing above it.
- **Linked things, and what cannot be done with them.** If a document has links to other subjects the
  margin lists them and says: `? 3 linked subject(s), 2 of them images — the desk can link a document
  to a thing but cannot place it IN the text, so none of these has a position on the page.`

### The bug I want on the record

`status()` wrote the status line with `el.textContent = …` on the bar that also held the new view
toggle — so every refresh silently deleted the control. It took two passes to see, because the
button was there, worked once, and then was gone with no error. The fix is a rule I would apply
everywhere: **never `textContent` a container that holds anything else.** Round four's lesson was
that convenience (`read` before `rewrite`) can disarm a safety mechanism; this is the same shape in
the DOM.

---

## 3. The worktree as a document draft: better, but not yet

Alex's question: is fork/diff/merge a better answer than settle-and-fence for long edits? I ran it.

**What works, and works well.** `worktree fork moss5` copies the world; you enter it as its own
session; the base keeps moving. A merge replays the commands signed by whoever made them, and it
renames ids on the way in — I created `a35` in the fork while Lark independently used `a35` in the
base, and the merge printed `ids renamed on the way in: s34→s38 a35→a39`. That is the right
behaviour and I did not expect it to be there.

**Three things break.**

**(a) The journal is commands, so a document draft is as heavy as the document.** `worktree diff
moss5` on my long document printed 50,307 characters — the same blow-up as §1, because the fork's
one command carries the whole text. A worktree is exactly the right *shape* for a long edit (work
apart, land once, all or nothing), and it cannot carry a long document until a settle can name a
section. **Fork/merge and settle/fence are not alternatives; they answer different questions.**
Settle asks *when does typing become an event*; the worktree asks *whose events land, and when*. A
long edit wants both, and the missing piece under both is the same verb.

**(b) The seen fence does not survive a merge, because "seen" belongs to the actor.** I appended to
`a13` in the base as `moss`, appended differently to `a13` in the fork as `moss`, and merged. The
diff correctly flagged it — `! e63 edit a13 by moss · ! = the worktree also names this thing; merge
will refuse there if someone else did it` — and then the merge applied anyway, because *I* had seen
`a13`'s current revision in the base. Both appends landed (they are additive, so the result is
benign) but the detector was not what stopped anything.

This is precisely the defect I found in round four one level down: `read <id>; do rewrite <id>`
disarms the fence because `read` refreshes what the actor has seen. **"Seen" is a property of the
actor, not of the command, so any path that refreshes seen-ness before a write — a helpful `read`, a
merge by the same person who has been reading the base — silently disables the conflict detector.**
I think the fix is that a replayed command should be judged against *the revision it was written
against*, carried in the journal, not against what its author happens to have seen now.

**(c) Merging an empty worktree closes it forever, silently.** I merged `desktop@rw` while it was
empty (0 commands). Afterwards I did real work in it — a whole-document rewrite — and:

```
> worktree diff rw
  nothing yet
> worktree merge rw
ERR worktree rw was already merged at event 67
```

The rewrite exists in `desktop@rw` and can never come back. The refusal is honest about *what*
happened and offers nothing: no re-fork, no "merge again from here", no pointer to the work. By the
house rule that every refusal offers a runnable next act, this one is incomplete — and it is the one
place in the system where a person can lose work and not be told.

---

## 4. What the document model cannot represent today

Plainly, in the order I would fix them.

1. **A change smaller than a document.** `rewrite` is all-or-nothing. Everything above follows.
2. **A position inside the text for anything that is not text.** An image, a table, an embedded
   subject, another document. The desk can *link* a doc to an image; it cannot say *where*. So a
   document is a string plus a set of unplaced neighbours, and the Editor says so rather than
   inventing a syntax.
3. **A comment that knows its passage.** Still every margin comment prints `? unanchored`. This is
   the oldest of my requests and the one that most changes how the page feels: a Google-Docs margin
   is *anchored*, and an unanchored margin is a mailing list beside a page.
4. **Two people in one document.** Two windows on one doc can still both settle, and the second wins.
   The fence protects me from the other inhabitant, not from my other window. The desk has no notion
   of *who is editing what right now* — only of who has seen what.
5. **Structure below the section.** Paragraphs have no identity. `##` sections are the smallest thing
   the desk can name, which is why `rewrite #section` is the right grain to ask for and also why it
   will not be enough forever: a 400-word section is still a large thing to resend for one word.
6. **A table.** Wren flagged this in round two and it is still true: a table is dense *and*
   structured, and the dense/sparse rule gives no guidance. I have nothing to add except that the
   Editor would render one and could not let you edit it.

## 5. What I would do next

`rewrite <id> #<section> text="…"` and a receipt that summarises large values. Those two, together,
turn every number in §1 from kilobytes into hundreds of bytes, make the worktree usable as a document
draft, and make undo mean "that paragraph" instead of "that document". Everything else I want —
anchors, positions, per-paragraph identity — is a larger argument. This one is arithmetic.

— Moss
