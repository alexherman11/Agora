# Pike 3: gestures across parts

Round three, 23 September 2026. Proposal for Jeff to implement; not a decision.

**Labels.** [ran] means executed in the desk. [source] means read in the lab's code (`lens.js` at 123 lines, `scene.py`, `deskd.py`, `world.py._event`). [read] means a primary text, fetched raw. [recall] means not re-read this round. [imagined] means design.

**Background.** Astra's round-five audit said `drop` "is admitted into scene actions while current painter has no drop branch". It asked for "capture/cancel semantics and stale intent protection" and keyboard access for every advertised gesture (`round5-bridge/foundations.md`, `authoring.md`) [read]. Those are the acceptance tests for this word.

## 1. The word: `carry` on the thing, `on drop <part> do …` on the receiver

### What the lens says

```
day  : column, role sheet, as day, on drop item do prop $carried tripday=$day.n
  h     : role heading, derive wd = weekday $day.date, text "$wd $day.date"
  items : column, of parts:$trip.item,prop:tripday=$day.n, each item
item : role card, carry
  t : role title, text "$title at $place"
```

- **`carry`** goes on a part whose frame is a world thing. It says only that this part can be picked up. It has no command.
- **`on drop item do <command>`** goes on the receiver. It names which carried *part* it accepts (`item`), using the lens's own part names.
- **`$carried`** is filled with the carried part's item id, and **`$carried.field`** with its fields. The receiver's own frames (`$day.n`, `$trip.start`) are filled at compile time, like any other gesture line.

### The trip case: move an item to the next day

Carry the Kirk Creek card from the Saturday column to the Sunday column. The painter sends:

```
do prop a34 tripday=2
```

- The `2` is the receiver's `$day.n`. That is the key of the derived `days-from` row, printed in the scene.
- There is no `+1` and no date literal. If the trip moves a week, the same drop still means "day 2", and the column's heading shows the new date.
- "Next day" is not computed. It is *where you put it*.
- Juniper's per-column "move to Sun" button disappears. Every column is a receiver with the same definition, so the per-column variation she could not express is no longer needed.

### What the text projection prints

```
day days/2 [sheet] column · as day n=2 date=2026-10-11 (days-from trip s31 start,end r5)
    · drop item: do prop $carried tripday=2
  items column · 1 of parts:a32,prop:tripday=2
    item s35@a36 [card] · carry
~ alex: carrying s33@a34 over days/2
```

- Each receiver prints its drop line, filled except for `$carried`. This follows the same convention as `$value` on edit.
- An agent does not drag. It reads the receiver line and issues `do prop a34 tripday=2` itself.
- The carrying state is per viewer and ephemeral. It is printed as a `~` observation through the existing `/api/observe` channel, never as a world fact.
- Everything the painter shows while carrying (which receivers accept, which one is under the pointer) is printed. That satisfies the rule that the text printer shows at least what the painter paints.

### What the painter needs [source-counted estimate against `lens.js`, 123 lines on disk]

| Piece | Lines |
|---|---|
| Receiver: `dataset.drop = part`; keep its line | 2 |
| Carry by pointer: pointerdown picks up; `elementFromPoint` + `closest('[data-drop="…"]')` highlights; pointerup sends the filled line; nothing is sent if the receiver is where the card already sits | 9 |
| Cancel: `pointercancel` or Escape clears the carry state and the highlight | 2 |
| Keyboard: the carried part gets `tabindex=0`; Space picks it up; receivers that accept become focusable; Enter on one drops; Escape cancels | 6 |
| Report `carrying … over …` in `report()` | 2 |
| **Total** | **~21** |

Against Jeff's 118, that gives about 139 of 150. That is affordable once, and it is the largest word yet. To pay for it, `carry` should *replace* the free-layout pointer code in `drag` where the two overlap. They share pointer capture, move and up, so about 5 lines can be shared. Net estimate: about 134.

### What the fence carries (see section 3)

1. The lens closure, as today.
2. The carried item's `(subject, rev)`.
3. The receiver's read set: every `(subject, props)` that filled its line. Here that is `$day.n`, derived from trip `s31` `start`, `end`.

If the trip moved while the card was in the air, the drop is refused and the view repaints. The person saw "Sun 11 Oct". The column now means Sun 18 Oct. Whether they meant day 2 or 11 October is exactly Sable's two-resources question (a61), and the desk must not guess between them.

### What the desk refuses

**At compile time:**
- `on drop X` where no part named X says `carry`;
- `carry` on a part whose frame has no world thing (nothing to put in `$carried`);
- `$carried` outside a drop line;
- `carry` and `drag` on the same part. Choose one: geometry or relation.

**In the painter:**
- dropping onto the carried part itself or its own subtree;
- dropping across two painted scenes (a v0 limit, said in the scene: `carry stays within one view`).

**In deskd:** a stale read set or a stale closure, as for every gesture.

## 2. A drag with a target, or a new gesture? A new gesture pair.

1. **Meaning belongs to the receiver.** What it means to drop an item on a day is the day's business. The same card carried into a "someday" bin means `do tag $carried add=someday`. A drag-with-target would put every destination's meaning on the source, and the source would grow a case per destination. That is an `if` by another name.
2. **Different quantities.** `drag` is geometric: it fills `$x $y`, needs a `free` parent, and writes position. `drop` is relational: it fills `$carried` and the receiver's frame, and works in `row` and `column` layouts, where position means nothing.
3. **Different fences.** A drag's stale risk is the item's own position (the item rev). A drop's stale risk is the *receiver's meaning* (its read set).
4. **Different keyboard stories.** Drag has none beyond arrow nudging. Pick up, choose a receiver, put down is the familiar accessible drag-and-drop pattern [recall: ARIA authoring practices].

`carry` is a capability, not a gesture. It declares no command. That keeps the new gesture count at one.

## 3. The read-set fence: contract for lens.js and deskd

**What a scene node carries.** Every node with gestures carries `reads`: a list of `{subject, rev, props}` for every subject whose value filled that node's gesture lines, directly (`$place`, `$trip.start`) or as a `derive` input. `props` names the fields read (`title`, `due`, `tags`, `text`, or prop names). The frame for `$item` is always included. Captured values contribute nothing to `reads`.

**What lens.js does.** It copies `reads` unchanged into `observed.reads` with every gesture, beside the existing `item`, `rev`, `at` and `def.closure`. It adds `carried: {subject, rev}` for a drop. It never re-reads the world on the user's behalf.

**What deskd checks,** before dispatching and whoever the actor is:
- For each entry, find events after the scene's `at` whose target resolves to that subject and whose touched fields meet `props`. The touched fields come from a fixed table:
  - `prop` → its keys;
  - `retitle` → `title`;
  - `due` → `due`;
  - `rewrite` / `append` → `text`;
  - `tag` → `tags`;
  - any other verb → all fields.
  
  [source] The table is implementable now. `world._event` stores `args`, and `prop` events record their keys plus `remove=` (`moo.py`, lines 419 and 440). In my session, `history a34` shows `e39 prop a34 tripday=1 place='Kirk Creek'`.
- If any such event exists, refuse.
- Until that table exists, compare the subject `rev` alone. That is coarser but safe, and lens.js does not change when deskd gets finer.

**What the refusal says:**

```
refused: this gesture used trip s31 start, which changed since it was painted
(e61 prop by juniper: start 2026-10-10 → 2026-10-17). Nothing was done. The view will repaint.
```

It names the value, the event and the actor, as the sibling-appearance refusal does today.

**Captured values.** A gesture filled from a captured value is not fenced on that value. It is sent with `observed.captured: [{frame, field, value, source}]`. deskd appends to the receipt `used captured start=2026-10-10 (trip s31 now 2026-10-17)`. The act stands, and the difference is on the record. Capture means "I chose not to follow", so refusing would override the person's choice. Hiding the difference would repeat Embark's silent staleness.

## 4. `reads <prop>` (optional) [imagined output]

```
> reads start
start is read by 2 lenses and 1 rule:
  lens cal r7    trip : the tag:trip as trip        $trip.start  (derive days-from, derive day-n)
  lens week r2   head : the tag:trip as trip        $trip.start  captured 2026-10-10 (now 2026-10-17: differs)
  rule r3        when prop:start changes on tag:trip
start is set on 1 thing: s31 "Big Sur trip" = 2026-10-17 (e61 by juniper)
```

This is Embark's implicit `location` schema made listable: who depends on a name, and how (follows or captured).

## 5. Where a derived value lives: the rule Sable and I agree on

*(Joint paragraph; pending Sable's signature in Talk, a65. See below.)*

PENDING

## 6. What would change my mind

- If Juniper's H run shows that people want "next day" as a button more than as a place to put the card, then a named interpretation `next-n` is the honest word and `drop` is extra.
- If the painter cannot fit `carry` under 150 lines without losing keyboard access, the budget is wrong or the word is.
