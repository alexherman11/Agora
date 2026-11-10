# Containers, and kinds that match too much

> **Framing notes, by Claude, 28 Oct 2026.** Frictions 4 and 6 in `trials/FRICTION.md`. Not yet designs.
> - **Why only notes:** both turn on two decisions that are Alex's:
>   - whether spellings and kind membership are declared by producers (shape-reads §6);
>   - the graph and trails work, which he asked to hold (27–28 Oct).
>
>   A full design here would pre-empt both.
> - **Labels:** **read**, **ran**, **imagined**.

## Friction 6: structural matching over-reaches (ran, three trials)
**What happened:**
- `meeting extends=event needs=place` made **all 300 board events meetings by shape** (`rows meeting` returned 733 things).
- A task card's `when`, a card timestamp, put task cards on the calendar (32 real cards).
- A window's `at=2301,582`, a screen position, was "placed" on the map (5 windows).

**Why:**
- Alex's rule for kinds is "has the same plus more sits inside". Structure is a good test for *shape* (can this word read it?).
- It's a poor test for *meaning*: is this a meeting? Is this `when` a time something happens? Is this `at` a place?

**What each candidate fix covers (imagined):**

| Fix | Covers | Doesn't cover |
|---|---|---|
| **Typed needs** (shape-reads draft 2) | a screen position isn't a latitude, once `point` exists (2301 is out of range) | `at=45,60`; a card's `when` (it *is* a time) |
| **Markers** (`happening=yes`; exists today) | anything, if someone marks it | needs someone to mark; `event` refused a marker as narrowing in the trial (fixed now: opening a closed kind is widening) |
| **Producer-declared membership** (`issue implements task`, shape-reads §6) | meaning, declared by the vocabulary's owner once | loose notes with no kind of their own |
| **Child kinds nominal by default** | `meeting` contains only meetings (own kind, marked, or declared), while `event` stays structural | changes Alex's "has the same plus more" for children |

**My lean (imagined):**
- **Parents stay structural,** for lists and reach: "anything with a title and a start is an event" is useful, and lists are lenient.
- **Children** (kinds that `extends=`) **are membership by declaration or marker.** A child is almost always a *meaning* ("a meeting"), not a shape.
- **Typed needs** stop the screen-point class.
- **Producer declarations** give the honest path for apps.

This changes something Alex decided, so it's his call. It's raised together with shape-reads §6.

**Built, 28 Oct, late (Alex: "Children by declaration"):**
- a kind that `extends=` another holds its own kind, kinds extending it, and things marked `is.<kind>=yes` (`mark <thing> <kind>`);
- parents stay structural.

Code: `kinds.py` `fits`, `mark`. Test: `test_shapes.py` `test_a_child_kind_holds_only_what_is_declared_one`. Producer declarations ("issue implements task") move into [[kinds-intelligence]], Alex's wider direction.

## Friction 4: containers and members (ran, chats trial)
**What happened:**
- `say` and `chat` check `kind=chat` exactly (`chat.py:61`), so a Twitch channel or a chat window is refused.
- A verb can't follow a link: `say $chat …` came out empty (`kernel.py`, verb steps).
- A lens can't say "conversations I'm in": `prop:with=dk2` is exact, and `with` is a list.
- "Latest N" can't be said: `limit` takes the oldest.

**What it touches:**
- **Container words** (`say <chat>`) accept containers of another app. That's producer membership again (a `twitch-channel` implements `chat`, with its messages' `channel` spelling `chat`), or `say` declaring `acts_on=chat` once chat is open.
- **Following a link in a line** (`$1.chat`). That's the line language reaching through a thing to another: the graph work, held.
- **Membership predicates in lenses** ("I'm in `with`", "newest first, N"). Those are painter words, and could go ahead on their own:
  - a `has:with=me` predicate for list facts;
  - `limit` with `newest`.

**Proposal for now (imagined):** split out the two painter words (list membership, newest-N). They don't depend on the held work. Leave container reach and link-following with the graph work and the producer-membership decision.

### Correction and proposal (28 Oct, late)
**"Latest N can't be said" was wrong (read).** The desk's lens language has it already:
- `clamp last N` keeps the newest N of a repeat;
- `by -made` puts newest first.

The live JEFF chat lens uses `of tag:said,prop:chat=$CONVO` with `clamp last 120` (`desktop/kernel-desktop/lenses/jeff-chat.lens`). The trial agent didn't find it, so this is a help gap: `help lens` should show it where `limit` is looked for.

**List membership is real, and it's a language change (imagined), so it goes to Alex with the other language proposals.**
- **Today (read):** `knife.compares` matches "any of the listed people" only for person keys (`owner`, `asked_by`, `person`: `persons.matches`, split at commas). A chat's `with` isn't a person key, and the kernel stores it as space-separated ids. So `prop:with=$me` compares the whole string.
- **Options:**
  1. **`with` becomes a person key, and person values also split at spaces.** It's narrow, and it reuses what `owner=alex,sable` already does.
  2. **A general list operator** (`with~$me`). It's new syntax, and each aspect would need to say its separator.
  3. **Membership from the aspect's type.** Once shape-reads has types, a `people` type (a list of ids) makes `=` mean "holds". That's the principled one, and it waits on shape-reads v1.
- **Lean:** 1 now, as the stopgap the language already has a shape for; 3 when types land.
- **What would change my mind:** if other list-valued aspects (tags, `to`) want the same soon, 2 or 3 should come first.

## What would change my mind
- **If producer membership (§6) is a no,** friction 6 falls back to markers plus typed needs. Then it needs a "mark everything of kind X as Y" word, so marking isn't one thing at a time.
- **If the graph work resumes,** friction 4's link-following belongs there, with trails.
