# Pike 2: binding words

Round two, 23 September 2026. This is a proposal for Jeff to implement in round three. It is not a decision. Labels: **[ran]** executed in `frontier-pike`. **[read]** primary text fetched raw and grepped (Peritext, Automerge docs, the automerge-rs `cursor.rs` source). **[recall]** not re-read this round. **[imagined]** design or thought experiment. I read Sable 1, Juniper 1, and Juniper's Talk notes a29 and a31.

## 0. What already landed while I wrote [ran]

Jeff's working tree already does three things:

- It reads a thing's own props. `text "$title at $place"` prints `· read place=Kirk Creek`, and a missing prop prints `(no tripday)`.
- It binds to ids one by one. `of s03,a36` resolved subject s03 to its appearance a25.
- It prints an empty repeat as `(empty)`.

It also crashes in one case. `of` with a removed appearance (a04) or a nonexistent subject (s99) raises `KeyError` in `scene.py` `_ctx_for`, at the line `n = w.nodes[nid]`, instead of printing `gone`. And `do create` refused every argument form ("unexpected words after the target") during the same window, while `knife.py` was mid-edit. Both are reported in Talk. I did not work around either.

The words below build on what landed. Each one must obey the growth rules in THE-MISSING-PIECE:

- it can be said in the desk's own language;
- it contains no `if` and no arithmetic;
- the text printer shows at least what the painter paints;
- it is paid for against the painter's 150-line budget (118 used).

Most of these words cost the painter nothing, because they resolve at compile time. The binding lives in the scene, not in the pixels.

## 1. The words

### W1. `of <ids>`: name things one by one (landed in part)

```
pins : column, of s31,a36, each item
```

- **Prints:** one line per id, with a state. `live` is the default and is not printed. `unplaced`: the subject exists and has no appearance. `gone`: never existed, or deleted. A subject with k appearances yields k occurrences.
- **Keys:** `pins/s31@a33`, and `pins/s31` when unplaced. The same thing twice in one repeat gets `#2`. Keys never use list positions.
- **Painter:** `gone` paints nothing and is printed. `unplaced` paints the subject's words with no box, and turns off gestures that need an appearance (`drag`, `at item`). The text prints `· drag: off (unplaced)`.
- **Fence:** unchanged. The item rev still applies, and the subject rev is added (see F1).
- **Refuses:** nothing at compile time. A missing id is a state, not an error. The KeyError above is the bug to fix.

### W2. `the <selection>`: exactly one

```
trip : column, the tag:trip as trip
```

- **Prints:** `the tag:trip → s31 (a32)`, or `the tag:trip (empty)`, or `the tag:trip (ambiguous: a32, a50)`. The ambiguous case lists every candidate and picks none.
- **Painter:** children paint only in the `live` state. In the empty and ambiguous states the part shows its state line, in role `cut`.
- **Fence:** a gesture under `the` also carries the resolution: which subject it chose, plus the selection's membership at paint time. If membership has since changed to two or to zero, the gesture is refused.
- **Desk:** the same word works as a target. `do prop the tag:trip start=…` refuses unless exactly one thing matches. This subsumes `one=1`.
- **Refuses:** `the` together with `each`, since `the` is not a repeat.

### W3. `as <name>` and `$name.field`: name a frame

```
trip : column, the tag:trip as trip
  head : role heading, text "$trip.title from $trip.start"
```

- **Prints:** `· read trip s31 title=Big Sur trip, start=2026-10-10`. The printer states the source subject of every dotted read.
- **Painter:** nothing new. Words arrive already filled.
- **Refuses:** a name that shadows a built-in (`as title`); `$x.field` where no ancestor is named `x`; `as` on a part that has no `of` or `the`.

Today a nested `of` *replaces* the context: I ran `of links:$item,tag:trip` and lost the item's own fields inside it. `as` keeps outer frames reachable. That is all following a relationship needs.

### W4. `$prop` and `$name.prop`: read a prop (landed for own props)

- **Prints:** `· read place=Kirk Creek`; `(no place)` when the thing has no such prop. `(no start on trip s31)` for a dotted read.
- **Painter:** paints nothing in place of the missing value, and the part keeps a `missing` marker for the agreement check. Cost: 0 lines.
- **Schema:** the scene prints every prop it read, so the implicit schema Embark describes (the map "looks for objects with a 'location' property") becomes a listable fact. I propose `reads <prop>` as a desk command that lists the lenses reading that prop. Schema is then discovered from use instead of declared.

### W5. `parts:<id>` and `part-of:<id>`: typed, directed relation terms (a desk-level word)

```
items : column, of parts:$trip.item, each item
```

Today `links:<id>` is untyped and undirected (`knife.py`, line 147). It would also return `refers` and `blocks` links. These two terms follow only `part-of`, in one direction. Because they are selection terms, `find parts:a32` works in the terminal first. They do not refuse anything new.

### W6. `derive <name> = <interpretation> <inputs>`: named interpretations, not arithmetic

```
h : role heading, derive date = day-n $trip.start $tripday, text "$date"
```

- **Prints:** `· date = day-n(trip s31 start 2026-10-10, tripday 2) = 2026-10-11`, with both inputs and their sources. If an input cannot be interpreted, the part prints `(uninterpretable: tripday='two')`. That is a state, not a crash.
- **Painter:** words arrive filled. Cost: 0 lines.
- **Desk:** `derive day-n 2026-10-10 2` and `derive day-n s31.start a36.tripday` print the same thing. That satisfies the sayable rule.
- **The list is closed and budgeted,** like roles in `calm.style`. It grows only by an argued word. It starts with four:
  - `day-n` (date, n → date of day n, where day 1 is the date itself);
  - `days-from` (start, end → a row per day with fields `n` and `date`, keyed by `n`);
  - `weekday`;
  - `week-of`.
  
  Each one is pure over printed inputs and total. There is no `+`, no `if` and no nesting of interpretations.
- **Refuses:** an unknown interpretation (listing the known ones), wrong arity, and a derive whose name shadows a prop or a built-in.

This is the answer to Juniper's "start plus N". The interpretation has a name and prints its inputs. It is the same kind of concession as `spread`: a relationship with a named coefficient, not an expression language.

### W7. `capture`: follow or capture as a visible mode

Following is the default. It is never written down, because every binding follows unless it is captured.

```
trip : column, the tag:trip as trip, capture start=2026-10-10
```

- **Prints:** `captured start=2026-10-10 from trip s31 (now 2026-10-17: differs)`, or `(same)` when it still matches. A literal written in a selection with no source (`due<2026-10-03`) prints `· literal 2026-10-03 (no source)`. It is legal, but it is labelled as what it is.
- **Painter:** paints the captured value. Captured parts take role `mark`, so a captured value looks different on screen. Cost: 1 line.
- **Desk:** `capture <lens> <frame>` rewrites the lens text, writing the current values with their sources. `follow <lens> <frame>` removes the capture. Both are ordinary events, undoable.
- **Fence:** captured values are left out of the read-set fence (F1) on purpose. A gesture that uses one prints `uses captured start`.
- **Refuses:** `capture` on a field the frame does not have.

This is "remember how you got there", with Embark's staleness watcher built in. The watcher becomes a comparison between the captured value and the live one, not a heuristic.

### Fences (not lens words; they are changes to what a gesture carries)

- **F1, the read-set fence.** A gesture carries `(subject, rev)` for every subject whose value filled its line or fed its derive inputs. That includes `$trip.start`, not only `$item`. deskd refuses if any of those changed. This is what would have caught Juniper's stale "move to Sun": the lens and the item were unchanged, but a value the line was built from had changed. Per-prop revisions would make this finer, and they are Sable's (referent, aspect) granularity. Subject revisions are enough to start.
- **F2, no self-exemption for painted gestures.** A painted frame is a view, not the actor's memory. deskd should judge the observed revs as sent, regardless of who made the intervening change. The terminal's `_touched_by_others` leniency can stay for typed commands.
- **F3, ambiguity is a state.** `lens <name>` with two lenses of that title, or `the` with two matches, prints `ambiguous` and refuses gestures. It never picks the first.

## 2. Worked example: Juniper's trip, relative variant [imagined text; W4, W5-by-hand and the item facts ran]

I seeded the world with `start=2026-10-10`, items carrying `tripday` and `place`, and `part-of` links to the trip.

```
cal : row
  trip : row, the tag:trip as trip
    days : row, derive days = days-from $trip.start $trip.end, over $days, each day
day : column, role sheet
  h : role heading, derive wd = weekday $it.date, text "$wd $it.date"
  items : column, of parts:$trip.item,prop:tripday=$it.n, each item
item : role card
  t : role title, text "$title at $place"
  later : role tool, text "move to next day", on click do prop $item tripday=$it.n
```

The `later` gesture shows two defects in my own draft. It needs *next*, and next is arithmetic. `$it` there is also the item's scope, not the day's. The honest version is per-column: `on drag` from one day to another column, where the drop target supplies `$it.n`. The desk has no drop gesture ("admitted and never painted"). So gesture targets between columns are the first thing this grammar cannot say, and I am recording that rather than hiding it.

Text projection after `do prop the tag:trip start=2026-10-17 end=2026-10-19`:

```
cal row
  trip s31 (a32) row · read trip s31 start=2026-10-17, end=2026-10-19
    days row · days = days-from(trip s31 start 2026-10-17, end 2026-10-19) = 3 rows
      day days/1 [sheet] column
        h "Sat 2026-10-17" [heading] · wd = weekday(2026-10-17) = Sat
        items column · 1 of parts:a32,prop:tripday=1
          item s33@a34 [card]
            t "Kirk Creek camp at Kirk Creek" [title] · read place=Kirk Creek
```

- Repairs after the date change: **0**. Literals in the lens: **0**.
- Day columns are keyed by `n`, not by date, so moving the trip keeps every column's elements and any draft inside them. Keying by date would rebuild all three.
- Juniper's missing calendar date is now visible, printed with its derivation.
- The captured variant, `capture start=2026-10-10`, prints `(now 2026-10-17: differs)` on the trip line. Nothing else is silently wrong.

## 3. Where a derived value lives (answer to a31)

**Recommendation:** a derived value lives in the **binding**, owned by the view definition that derives it. It is recomputed at every scene and never stored on the item. It becomes an aspect of the item only through an explicit `capture` that writes it with provenance, as a prop and its source (`date=2026-10-11`, `date.from=day-n s31.start tripday @e52`). That is an ordinary, attributed, undoable event, and from then on it is data that no longer follows.

**Reasons:**

- Storing derivations on items recreates Juniper's two-variant problem: `day` and `tripday` both on the item, drifting apart.
- Sable's ownership rule assigns an aspect to the definition that writes it. A lens writes nothing, so its derivations cannot be aspects without inventing writers.
- The trip lens and a second lens (say a week view) can derive differently from the same sources without contending for one slot.

**Juniper's follow-up**, whether each view mints referents: no. Views key occurrences, `(part, subject@appearance, #k)`. They mint nothing durable. A part earns a referent only when something *outside the view* refers to it, for example a comment on a day. Then it becomes a thing, by an explicit `create`, and the lens binds to it.

## 4. Does a text CRDT give anchor mapping for free? [read]

What is free:

- **Anchors are element identities, not indexes.** Peritext inserts "after the existing character whose ID is 1@alice" and removes by `removedId`. An Automerge cursor "represents a relative position, 'before character X'". `cursor.rs` says a cursor identifies a position in "a Sequence (either Self::List or Self::Text)", so cursors also work over lists.
- **Concurrent edits elsewhere never move an anchor,** and overlapping comments coexist. Peritext: "multiple comments can be associated with a single character".
- **Comment boundaries follow editor convention:** a comment "does not grow" at its ends.
- **Deleted characters stay as tombstones,** so a mark's ops "are preserved".

What is not free:

1. **The editor must emit operations.** Automerge's `updateText` diffs whole values, and "if the text has changed a lot between calls … the diff will not merge well." The desk's whole-document `rewrite` is exactly that case: anchors would follow a diff's guess, not the edit. Free mapping needs an op-level editor binding, one per editor toolkit (a ProseMirror binding exists).
2. **Deleted ranges fail silently.** When the anchored character goes, the cursor shifts to "the next item that was visible at the time of cursor creation". A comment on fully deleted text collapses to a point, and nothing says so. The state "anchored text deleted" is tool code under every candidate.
3. **Moves are not moves.** Peritext: "cutting or pasting an entire paragraph, turn[s] into lots of single-character operations." New ids mean comments do not follow moved text. I found no move operation in the Automerge list docs [read]. Research on moves exists [recall: Kleppmann et al.], but I did not find it in the shipped API.
4. **Blocks are out of scope.** Peritext handles only inline formatting "within a single paragraph"; headings, lists and tables are left to "a future article".
5. **A grid gets the mapping only by design.** A cursor lives in one sequence. A cell rectangle needs a row-cursor range plus a column-cursor range. That works only if the grid's author made rows list elements *and* columns a list of ids, with cells keyed by column id. Sort must also be a view order: a sort done as delete-and-reinsert destroys every row anchor.
6. **Refs are experimental and may be positional.** Automerge Refs can path through indexes (`handle.ref("todos", 0, "done")`). The docs call the API "experimental" and do not say whether index 0 is pinned to an element. Until verified, treat indexed Refs as position keys.

**What this does to case (b).** C's advantage is real but narrower than "free":

- For E1 (prose) it is conditional on an op-emitting editor binding.
- For E2 (grid), Juniper's "1 small adapter" holds only if the grid was built with identified rows and columns and sort as view order. A grid built any other way needs a full adapter.
- The honesty states (deleted, moved, orphaned) cost the same tool code in every candidate.
- A can close most of the gap by storing a text aspect as a CRDT sequence, which is Juniper's own observation.

So the counts should read: C = 0 anchor code for E1 plus 1 editor binding; E2 ranges from 1 to "full" depending on representation; plus N lines of orphan and move reporting under every candidate.

## 5. What moved since round one

- Four of my round-one defects are now fixed or specified:
  - the closure fence;
  - ids in `of` (in progress, crash noted);
  - `(empty)`;
  - prop reads.
- My position is unchanged in substance, but now sharper:
  - **provenance** becomes three concrete things: `as` frames, printed reads, and `capture` with a source;
  - **derived values** belong to bindings, not to items;
  - the **fence** must cover the read set, not only definitions and the clicked item.
- The CRDT reading moves me toward Juniper on text and away from "free" on everything else.
- New gap: a **gesture whose target is another part** (drop on a column) cannot be expressed. Without it, relative edits like "move to the next day" fall back to arithmetic or to literals.

**What would change my mind:**

- Jeff implements W2–W7, and Juniper's script still needs a repair at step 4 or 9.
- The interpretation list passes 12 within a month of use. The budget would then be the wrong guard, and an expression language would be the honest answer.
