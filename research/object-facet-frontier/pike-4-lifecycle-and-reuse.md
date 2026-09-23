# Pike 4: lifecycle and reuse

Round four, 23 September 2026. Proposal, not a decision.

Evidence labels:
- **[ran]**: executed in `frontier-pike`, its worktree `@lensdev`, and a private deskd on port 8791 (stopped afterwards).
- **[source]**: read in lab code: `scene.py` (792 lines), `lens.js` (123), `deskd.py`, `worktree.py`.
- **[read]**: Astra's `round6-compiler` (README, `activation.py`, `editing.md`, `media.md`) and the round-8 media note's section "Feature adoption without a package-manager experience".
- **[imagined]**: design.

## 0. Challenge to the Codex lifecycle [read]

`activation.py` is careful work. It keeps a candidate separate from the active definition and pins the transitive closure. It gives every activation a new monotonic revision, so A→B→A is three generations. It keeps drafts "by value" in a separate map. And its authors state that this "is storage continuity", not rebasing, focus or IME continuity.

My objections are about **where** it lives, not about what it does:

1. **It is a second history beside the world's.** Candidates and activations are "private in-process data and add no native world events", with "no persistence or restart recovery". The desk already has a fork, a diff, an all-or-nothing replay and per-command undo, and those *are* world events. A lifecycle that the world cannot see is a second owner. Astra's own README warns against exactly that ("keeps the handle store from becoming another world owner").
2. **It fences too coarsely, in the same way the desk does.** "Unrelated world changes can invalidate a candidate", and a successful activation refuses *every* earlier offered action. I reproduced the same over-refusal in the desk [ran, below]. So the continuity problem is not solved by an activation store. It is solved by fencing a gesture on the definition *it* depends on.
3. **It keeps the draft but cannot show it.** "If a new definition removes a selected scene key, retained selection data may no longer resolve." Continuity has to be decided where the draft is visible, in the painter, keyed by occurrence.

Round 8 already narrowed the Codex position: "Simple local layout or toolbar definitions do not need their own generalized installation generation. A retained definition revision, references to shared defaults and explicit local overrides can be enough." Sections 1 and 2 below build exactly that, from worktrees and one composition word.

## 1. Authoring and activation through worktrees

### What already works [ran]

I built a calendar lens `cal` (s45 r3) with the landed words over my Big Sur things, then ran the lifecycle.

1. `worktree fork lensdev`.
2. In the fork I rewrote the heading to `"Day $it.n · $wd $it.date"`.
3. `scene cal` **in the fork** printed `Day 1 · Sat 2026-10-10`, while `scene cal` **in the base** still printed `Sat 2026-10-10`. Preview is a fork.
4. Meanwhile, in the base, `pike-tab2` retitled a36.
5. `worktree diff lensdev` listed one command on each side, and `worktree merge lensdev` replayed it as e52. Activation is a merge, and it is an ordinary event you can undo.

Then I sent, through deskd, an edit gesture painted before the merge on a *different* part: the card title `t` of a34, whose line had not changed. deskd refused it: `lens cal changed since this was painted (you saw revision 3, it is now 4)`. A person typing a new card title while someone else fixed the day heading would lose the typed text. That is Astra's over-refusal, reproduced.

### What is missing

- **The painted view does not say what it shows.** The header `scene cal · for pike · world @51` is identical in fork and base. It should print:
  - `cal r4 · active` in the base;
  - `cal r5 · preview in worktree lensdev (forked @50, base now @52, 1 command to merge)` in a fork.
  
  The painter shows this line in the existing `said` strip. It costs 1 line, because the painter already prints the scene text.
- **The diff of a definition is a whole-text rewrite.** `worktree diff` showed the full 7-line lens to change 1 line. It also makes merges all or nothing *per lens*: a base edit to any other part of `cal` refuses the whole merge. Proposal: a part-level verb, `do relens cal part=day/h text="…"`. The journal then records which part changed; merge conflicts only when both sides edited the same part; the diff prints parts. The lens's part paths become its anchors, the same granularity Sable wants for aspects.
- **The fence is per lens revision; it should be per part.** Contract:
  - Each gesture node carries `defpart: {lens: s45, path: "item/t", hash}`.
  - `hash` covers that part's own line, plus the lines of the ancestors that bind its frame (`the`, `of`, `as`, `over`, `derive`), since changing those changes what `$item` means.
  - deskd parses the current lens text (with `scene.parse`, already available), recomputes the hash for that path, and accepts the gesture if it is equal, subject to the read-set fence as before.
  - If the path is gone or the hash differs, deskd refuses with `the field you were editing changed its meaning (cal r3 → r4, part item/t); nothing was sent`.
  - A heading fix no longer kills a card-title draft.
  - Cost: about 15 lines in `scene.py`/`deskd.py`; 1 line in `lens.js` to copy `defpart`.
- **The draft must survive a refusal, visibly.** Today, on refusal, `lens.js` prints "refused: …" and repaints, and the typed text is gone.
  - Rule: **the painter never discards what a person typed.**
  - On any refusal of an `edit`, the element keeps the draft and takes role `refusal`. It offers Enter to send again (against the current definition, with a fresh read set) or Escape to discard.
  - The text projection prints the draft as a per-viewer observation: `~ alex: unsent draft on item/t of a34: "Kirk Creek campground" (refused: part changed)`.
  - The draft is shown to the other inhabitant, never adopted as world state.

### What the painter must keep, and what it may rebuild

**Keep:**
- any element whose key and signature are unchanged (already done by `make()`);
- the focused element and its draft while `busy`, *even if its signature changed*. Hold the new scene and apply it when the draft settles (sent, refused-and-discarded, or cancelled). Today `refresh` skips while busy, which is right, but the send then goes out under the stale `def`;
- selection and scroll inside kept elements (already done);
- the carry state (pike-3) across a repaint, cancelled if its receiver's key disappears.

**May rebuild:**
- everything else, including an element whose part changed while no one was focused in it.

**Painter lines** [source-counted estimate]:

| Change | Lines |
|---|---|
| Hold the pending scene while busy | 3 |
| Draft kept on refusal, with resend or discard | 6 |
| Copy `defpart` into `observed` | 1 |
| Header line | 0–1 |
| **Total** | **~11** |

### What the fence carries

A gesture begun under the old definition is completed honestly or refused honestly. It carries:
- `defpart` (instead of the whole closure, for acceptance);
- the read set (pike-3);
- the item rev.

The whole-closure identity stays in the payload for the record. A gesture made in a preview fork acts on the fork's world, is journalled there, and arrives in the base only through the merge, fenced like any other merged command.

## 2. Reuse without a package manager

### The case [ran]

The calendar lens reused for a reading plan: a plan note tagged `readplan` with a start and end, and books that are `part-of` it and carry a day number and an `author`.

What the desk offers today:
- **Copy (a fork):** `reading` was the `cal` text with 2 lines changed. It works. It printed `Middlemarch by Eliot` under `Mon 2026-10-05`. But it was copied from `cal` r3, so upstream's r4 heading fix never arrives, and nothing in the scene says it came from `cal` at all.
- **Embedding:** `lens cal` inside `reading-embed` shows the *trip*. Composition places a lens with its own bindings and has no way to rebind them.

### The missing word: `from <lens>` with part-path overrides

```
from cal
cal : row, the tag:readplan as trip
item/t : role title, text "$title by $author"
```

- `from cal` inherits every part of `cal` at its current revision. That is follow mode, the default. `from cal@r4` pins it (capture).
- A line whose name is a **part path** (`cal`, `item/t`, `day/h`) replaces that part's own properties. Its children are inherited unless restated. `without day/weather` removes an inherited part.
- One part can pin itself: `day/h : from cal@r5` takes one upstream fix while the rest stays pinned at r4. This is a cherry-pick at part granularity, written in the lens, not in a solver.

**Local override versus fork:**
- An **override** is a `from` lens with path lines. It keeps the upstream link, per part.
- A **fork** is a copy with no `from`. It owns everything, and the scene prints it as `origin: none`.

When upstream fixes the weekday label (a change to `day/h`), `reading` gets it, because it never overrode `day/h`. If upstream also changed `item/t`, `reading` keeps its own. If upstream adds a part the reader doesn't want, one `without` line removes it.

**What the scene prints:**

```
scene reading · reading r2 = cal r4 (follow) + 2 overrides (cal, item/t)
  cal a48 row · the tag:readplan -> s47 (a48) as trip          · override reading r2
    days a48 row · days = days-from(...)                        · from cal r4
      day a48 [sheet] column                                    · from cal r4
        h a48 "Day 1 · Mon 2026-10-05" [heading]                · from cal r4
        items a48 column · 1 of parts:a48,prop:tripday=1        · from cal r4
          item a50 [card]                                       · from cal r4
            t a50 "Middlemarch by Eliot" [title]                · override reading r2
```

Each node says where its definition came from. The closure fence and `defpart` carry the right lens for each part: a gesture on `t` is fenced on `reading`, and one on `h` on `cal`.

**Refusals and states:**
- An override whose path no longer exists upstream (upstream renamed `item/t`) prints `override item/t: cal r5 has no part item/t (orphaned)`. The lens falls back to its last good version and gestures on that part are off. It never silently binds to a similar name, as in Sable's rename rule.
- `from` cycles are refused, as `lens` cycles are.
- Path lines in a lens without `from` are refused.

Cost: 1 word (`from`), 1 naming rule (paths in `from` lenses), 1 small word (`without`). About 40 compiler lines. 0 painter lines.

## 3. `reads <prop>` and `reads <lens>`

```
> reads start
start is read by 2 lenses:
  cal r4       part cal    the tag:trip as trip → $trip.start in derive days-from     follows
  reading r2   part cal    from cal r4 (inherited)                                     follows
start is set on 2 things: s31 "Big Sur trip" = 2026-10-10 · s47 "October reading" = 2026-10-05
```

```
> reads reading
reading r2 depends on:
  definitions   reading r2 · cal r4 (from, follow)
  props         start, end (plan s47) · tripday, author, title (items)
  selections    the tag:readplan · parts:a48,prop:tripday=1..3
  interpretations days-from, weekday
```

**Smallest implementation.**
- `reads <prop>` is **static**. For each subject tagged `lens`, run `scene.parse` and walk the parts. Collect:
  - `$names` in `text`, and `$frame.x`;
  - `derive` inputs;
  - `prop:x` terms in `of`, `the` and `only when`;
  - `capture` fields.
  
  Report parts where `x` appears, and whether they follow or capture. Then list the subjects that carry `x`. About 30 lines; no world build needed.
- `reads <lens>` is **dynamic**. Run `scene_for` once and take the union of every node's `read`/`reads`, the `def.closure`, the resolved selections and the interpretations used. About 20 lines. It reuses what the scene already records.

The two differ on purpose: *who could depend on this name* is a question about text, and *what this view depends on right now* is a question about the world.

## 4. Is the bridge still a small fixed host?

| Component | Size |
|---|---|
| Painter | 123 lines on disk (Jeff counts 118), unchanged since round one |
| Words accepted, not yet painted | carry/drop (~16 net) and lifecycle continuity (~11): about 150 |
| Compiler (`scene.py`) | grew from 452 to 792 lines in one day, about 50 lines per word |
| Lens words, now | 17 (`column row free role text clamp of over each at spread lens only the as derive capture`), plus 3 gestures |
| Lens words, proposed | `carry`, `drop`, `from`, `without` (21 words, 4 gestures) |
| Interpretations | 4 of the 12 I proposed as the budget |

So the painter is still a small fixed host. It knows no app, and every word so far either costs it nothing or pays for itself in pointer and keyboard code. The **compiler** is not small, and it is not fixed. It is where the language lives, and it grows by about 50 lines per word.

That is acceptable only if two things hold:
- words keep arriving from executed pressure (every word so far did);
- a word budget exists for the compiler, as for the painter.

I propose a ceiling of about 25 words and 12 interpretations. Past that, the honest move is an expression language, and the growth rules have failed.

**What would change my mind:**
- If Juniper's generality run needs a fifth interpretation that is not about dates, the closed list is the wrong shape.
- If `from` overrides need to reach *inside* a part's properties (replace one gesture, keep the text), part granularity is too coarse and the override unit is the property.
