# Module-author review of shape-reads.md draft 1, by a review agent for Claude, 28 Oct 2026.

> Seat: someone who writes and keeps the processes that offer words (the House builders, the map, the board, importers).
> Everything here is on paper. No source was edited, nothing ran against any world, and no session pickles, `keep/` files or exported logs were read.
> - **read**: a primary source, with file:line. Paths are under `research/` unless they start with `kernel/` (that means `research/kernel-lab/kernel/`).
> - **imagined**: a sketch or a thought experiment. Every code block below is imagined.

## 0. Verdict in five lines
1. **The core idea is right for do-words with one target.** If the check and the read are one function, `board.calendar` stops crashing and the map can place a board event. The calendar is the cleanest win (§2.3).
2. **The `thing` payload as drafted puts three kinds of value in one flat dict:** canonical values, raw facts and provenance. A Python author who writes `thing.get('who')` treats *unread* as *absent*. That brings back the exact House bug the draft is meant to fix: the owner check is skipped (§2.1, §5.1).
3. **`set … through=` has no customer among the three real modules.** In the House it would turn a note write into a lane move, which is trial finding 5 again (§2.1, §4).
4. **Reads that matter most to a module are not covered:**
   - values that mean the same thing in different words (`closed`, `Done`, `submitted`);
   - the kernel's own words, which read raw facts: `claim` reads `seats`, and the painter derives `seats_left`;
   - readings that come back from a module's see word (`board.feed`).

   So RSVP on a redeveloped board still gives one seat (§4), and a due-soon module still needs a hand-written table of every vocabulary (§3.2).
5. **A module author has no test harness for a shape,** and never sees the calls the kernel refused before asking the module (§5.4).

---

## 1. What the draft gives a module author (read, with the code it changes)
- **The call today carries only the line:** `{"target", "words", "kv"}` (`kernel/kernel.py:1589-1590`, `kernel/modules.py:239-240`). Every module does its own `look`.
- **Three different readers hold the same thing:**
  - the kernel's check reads `shown()` raw (`kernel/kinds.py:298-311`);
  - `rows` reads it *filled*, adding `start` from `starts` plus an `as` note (`kernel/words.py:865-871`);
  - `look` reads it raw, except a post, which comes back as a summary of `id, kind, text, by, likes, pinned, rev, in` (`kernel/words.py:248-251, 275-276`).
- **The draft adds four things:**
  - typed needs (`start:time`);
  - optional `reads=`;
  - `through=` on `look`/`rows`/`set`;
  - `thing` in the call.

  For a module author the first two are declarations in the offer, the third is a new argument to learn, and the fourth is a new field to trust.

---

## 2. Three real readers, rewritten against the draft

### 2.1 The House builder (`kernel-lab/modules/house/builders.py`)

**What it reads today (read):**

| Where | What it reads | Through |
|---|---|---|
| `start` (182-226) | `title`, `who`, `builder`, `build_run`, and `held()`'s six aspects | `self.h.m.see('look …', use=…)` in-call (188) |
| `build` (244-257), `prepare` (259-272), `retry` (370), `tell` (382), `assert_owned` (447-453), `update` (161) | the same, re-read for hours after the call | `Door.look` through the requester's *agent session* (61-65, 132) |
| `hear` (402-417) | `chat`, `made_by`, `text` of a said line | the module's own `see` (405) |
| `prompt` (419-445) | `text`, `acceptance` | the task row passed in |
| `held` (40-43) | `lane`, `paused`, `cancelled`, `permission_required`, `approval_required`, `status` | raw |

- The owner check compares `who` to the caller's **name**, at builders.py:200-202 and again at manager.py:64.
- `state['basis']` keeps the raw `title`/`text`/`acceptance`/`who` in `state.json` on disk (214, 394). `assert_owned` compares it every time (452).
- `house.manage` hands its own `msg` to `start`: `dispatch` → `getattr(builders, OPS[action])(dict(msg, _managed=True))` (manager.py:84-85).

**The shape it should declare (imagined):**
```python
# house.py OFFER, replacing TASK_NEEDS = "kind=taskboard-task|task" (house.py:58-59, 749-759)
BUILD_SHAPE = dict(
    acts_on="task",                      # a steward-declared kind: needs="title|name|summary kind=taskboard-task|task|issue|gh-issue"
    needs="title|name|summary:text",
    reads="text|body|description:text acceptance|criteria:text who|assignee:person "
          "lane|status|state:text paused|held:yes cancelled:yes")
# house.build, house.tell, house.retry, house.review, house.land all say BUILD_SHAPE.
# house.manage says the same shape: it delegates to start() with its own msg, so `thing` arrives read through house.manage.
```

**The code (imagined):**
```python
def start(self, msg):
    t = msg.get('thing')                       # read through house.build as the caller narrowed to the House
    if not t:                                  # absent when the target is not visible; the kernel already refused a misfit
        return {'refused': 'choose a visible task card'}
    v, rd = t['values'], t['reading']          # envelope of §5.1; with the draft's flat dict, see the trap below
    if 'who' in rd['unread']:                  # "Alex" when two visible people are called Alex
        return {'refused': f"can't tell who owns this task ({rd['raw']['who']!r}); set who= to a person"}
    owner = v.get('who')                       # now a person id, not a name
    if owner and owner not in (msg['caller']['person'], self.h.jeff_id):
        return {'refused': 'task has another owner; ask that owner to release it first'}
    if held(v, t['facts']):
        return {'refused': 'task is held, finished, or already has a builder'}
    ...
    state = dict(..., title=v['title'], task_owner=owner or '', shape_rev=rd['shape_rev'],
                 basis={k: v.get(k, '') for k in ('title', 'text', 'acceptance', 'who')})

class Door:
    def look(self, target, through='house.build'):
        rows = self.call('/see', f'look {target} through={through}').get('rows') or []
        ...

def assert_owned(self, state):
    t = self.session(state['requester']).look(state['task'])
    if t['facts'].get('build_run') != state['run'] or held(t['values'], t['facts']):
        raise RuntimeError('task claim changed or is held; stop this operation')
    if t['reading']['shape_rev'] != state.get('shape_rev'):
        self.event(state, 'reread', 'house.build reads tasks differently now; basis re-taken')   # not a stop
        state['basis'] = {...}; state['shape_rev'] = t['reading']['shape_rev']
    elif any(t['values'].get(k, '') != b for k, b in state['basis'].items()):
        raise RuntimeError('task instructions or owner changed; review the correction before continuing')

def held(v, facts):
    # value meaning is NOT given by the draft (friction 2): the House hard-codes every vocabulary's "closed"
    lane = str(v.get('lane', '')).casefold()
    return lane in ('done', 'closed') or v.get('paused') == 'yes' or v.get('cancelled') == 'yes' or \
        any(str(facts.get(k, '')).casefold() in HELD for k in ('permission_required', 'approval_required'))

# bookkeeping writes stay RAW: builder, build, build_run, build_phase are the House's own facts
door.call('/do', f'set {task} builder={q(name)} build=asked build_run={q(run)}', saw={task: rev})
```

**Simpler:**
- `start` loses its `look`.
- `title` reads on 1,058 issues, and `prompt` gets `body` and `description`.
- The shape is the honest list of what the code reads, so the kernel's check and the House agree.

**Harder, or wrong on the first try:**
- **(a) Unread looks like absent.** With the draft's flat `thing`, the natural line is `if thing.get('who') and thing['who'] != …`. An unreadable `who` simply isn't there under that name, so the owner check is **skipped**. That is the trial's 1,255 (tasks-rebuilt FINDINGS §4) reproduced, now behind a design that says it fixed them.
  - The draft's own table (§4, row 2) relies on the builder checking `unread`. Nothing makes it.
- **(b) Names become ids.** `who` turns from "Alex" into `dk2`.
  - builders.py:200-202, 249, 383 and manager.py:64, 99 all compare `who` to a **name** or to the stored `task_owner`. After adoption every build is refused ("task has another owner") until each is rewritten to compare ids.
  - `'JEFF'` becomes JEFF's agent id, which the House has to look up.
- **(c) Running builds stop after the upgrade.** `state.json` from before holds `basis.who = "Alex"`. The first `assert_owned` after the change reads `"dk2"` and raises "owner changed", so every running build blocks at its next turn boundary. A widening by a steward mid-build does the same: `title` appears from `name`, or the type of `who` changes.
  - A module needs to tell "the thing changed" from "the reading changed". Hence the `shape_rev` in the sketch, which the draft doesn't provide.
- **(d) Two readers.** `thing` is read as the caller narrowed to the House. The door re-reads as the requester's *agent*. `who:person` resolves "a name exactly one *visible* person has" (draft §3.2), so the two readers can disagree, and `assert_owned` raises a false alarm.
  - The draft doesn't say *as whom* `thing` is read.
- **(e) Delegation reads through the wrong word.** `house.manage` → `start` hands `start` a `thing` read through `house.manage`. `through` names it, but nobody checks.
- **(f) `set … through=` would be wrong here.**
  - `NOTE_FIELDS` includes `status` (manager.py:11). On a task card, `status` is a free-text note; on a Tracker issue, it is the lane.
  - With `lane|status|state` in the shape, `set dk94 status="waiting on review" through=house.manage` would write to `lane`: the card moves to a lane named after a note and disappears. That is tasks-rebuilt finding 5 exactly.
  - The House's writes are all its own bookkeeping, which must stay raw. **The House has no use for set-through.**

**What the draft doesn't give the House:**
- **`closed` vs `HELD`:** 507 closed-but-buildable things start a *paid Codex worker*. That is the costliest of the House's failures, and it's left for later (draft §4, row 3).
- **No `shape_rev` / reading version.**
- **No statement of which reader `thing` uses.**

**From the author's seat:** don't widen `house.build` past task cards until value meaning exists.

### 2.2 The map (`kernel-lab/modules/map/map.py`)

**What it reads today (read):**
- **`position` (208-256):** `lat`/`lon`; `at`/`place` as `lat,lon` text, as an id (recursing two levels, `depth < 2`, adding the hop's rev to `call.saw` at 225), or as a ground name; then `location` text, through the ground and then Nominatim (241-255).
- **`placed` (301-325)** copies a fixed `KEEP` list of raw names (55-57).
- **Word inputs:** `w_where`/`w_near`/`w_show` (422-454, 819-824) take a target that may be an id, a name or `lat,lon`, through `point_of` (259-287).
- **No shapes:** the map offers no `needs` (899).
- **Names never become targets:** the kernel resolves a name into a target only when `takes` starts with `<id>` (`kernel/kernel.py:679-683`). The map's takes is `<thing|name|lat,lon>`.

**The shape (imagined):**
```python
POINT_READS = "lat+lon|geo|where|at|place:point? location|venue|where:text title|name|summary:text"
#   `?` = lenient: present but unreadable is NOT a refusal; the map has its own fallback (ground names, geocoding)
#   No needs: the map must still answer for a name or lat,lon, where no thing is read at all.
for word in ("map.where", "map.near", "map.place", "map.show"):
    offer(word, reads=POINT_READS)
```

**The code (imagined):**
```python
def position(call, gf, t):                      # t: an enveloped reading (from `thing` or `rows … through=`)
    v, rd = t['values'], t['reading']
    if 'where' in v:
        la, lo = (float(x) for x in v['where'].split(','))   # canonical "lat,lon" is a STRING: parse it again
        for hop_id, hop_rev in rd['via'].get('where', []):  # at=dk55 read through the structure's point
            call.saw[hop_id] = hop_rev                       # the module can't fence a hop it never saw
        return la, lo, False
    text = rd['raw'].get('where') if 'where' in rd['unread'] else v.get('location')
    if not text:
        return None
    if rd.get('private') and not ground_only:             # FRICTION §7: a private title went to Nominatim
        return ground_lookup(gf, text)                     # local tiles only, never the outside service
    return ground_lookup(gf, text) or geocode_limited(call, text, gf)

def w_show(call, a, thing=None):
    if thing:                                    # only for `map.show dk94`
        p = position(call, ground_getter(call, the_map(call)), thing)
    else:                                        # `map.show "Beach cleanup"` / `map.show 36.96,-122.01`: no thing
        p = point_of(call, ...)                  # the old path stays
    ...

def w_layers(call, a):
    shows = layer['shows']
    if shows.startswith('rows '):
        found = call.see(shows + ' through=map.where')   # one kernel read: spellings + types for every row
    else:                                                # 'board.feed', 'map.near …': a module's rows can't be read through
        found = [legacy_envelope(r) for r in call.see(shows)]   # …so the raw position() stays as well
```

**Simpler:**
- `map.show dk94` on a board event works: `look <post>` no longer hides the facts behind a summary.
- `where`/`geo`/`lat;lon` read without hand parsing.
- `at=2301,582` (a window) is unread rather than placed.

**Harder:**
- **Two paths for good, maybe three:**
  - typed, from `thing` or `rows … through=`;
  - raw, for name and coordinate targets;
  - raw, for layers whose `shows` is a module word (`board.feed`, map.py:58, 716-721).

  The map gets *bigger*, not smaller.
- **The canonical `point` is a string.** Every consumer re-splits it, so a JSON pair would be friendlier.
- **Hops** go one level in the type (draft §3.2, Q3) and two in the map (map.py:217). The map will keep its own recursion for event → stall → structure. Unless the reading reports `via` ids and revs, the map can't fence what the kernel read for it. Today's `call.saw[other['id']]` at 225 has nothing to attach to.
- **Lenient reads:** the map needs present-but-unreadable `at="Seabright & Murray"` to fall through to its own lookup. So it wants reads that don't refuse. The House wants the opposite (§2.1a), which is why the sketch marks the map's reads lenient with `?`.

**What the draft doesn't give the map:**
- `through=` on the rows of a module's see word;
- `via` provenance for hops;
- a privacy hint before a value leaves the machine (FRICTION §7);
- names → targets for `<thing|name|…>` takes, so `thing` is absent for the two most common ways a person says `map.show`.

**From the author's seat:** also make `map.add`'s help stop teaching `start="Thu 6pm"` (map.py:852), which no `time` type will ever read. The draft has no write-time check that would catch it (§3.1).

### 2.3 The board (`community-app/board/board.py`)

**What it reads today (read):**
- **`rsvp` (193-209)** finds the thing three ways, `rows post` + `rows event` then `look` (196-197), and answers with `claim <target>` plus `make kind=board-rsvp` (208-209).
  - **It never reads `seats`.** The kernel's `claim` does, raw from state: `seats` (1 when absent) and `closes` as a *string* compare against `%Y-%m-%dT%H:%MZ` (`kernel/words.py:784-791`).
  - `seats_left`, the painter's "full" signal, is derived raw too (`kernel/kernel.py:477-478`, board.py:375-377).
- **`calendar` (217-245)** reads `start`, `end`, `title`, `location`. Its `stamp()` refuses floating times (13-19) and its `date()` assumes ISO (224-225): that is the eight-formats crash.
- **Feed `soon`** (359-361) sorts `p['start']` as strings.
- **`NEEDS`** = `{'rsvp': 'kind|post_kind=event', 'calendar': 'kind|post_kind=event start'}` (401).

**The shape (imagined):**
```python
SHAPES = {
  'rsvp':     dict(acts_on='event', reads='status:text'),
  'calendar': dict(acts_on='event', needs='start|begins|dtstart:time',
                   reads='end|ends|dtend:time title|summary|name:text location|venue|where:text'),
}
# event (dk333) opened by a steward: needs="title|summary|name start|begins|dtstart|when"
```

**The code (imagined):**
```python
if word == 'calendar':
    v = message['thing']['values']            # the kernel refused a fuzzy start before asking
    def ics(x):                               # canonical: 'YYYY-MM-DD' or an ISO instant
        return x.replace('-', '') if len(x) == 10 else stamp(x).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for key, name in (('DTSTART', 'start'), ('DTEND', 'end')):
        if v.get(name):
            lines.append(key + (';VALUE=DATE' if len(v[name]) == 10 else '') + ':' + ics(v[name]))
    ...                                       # SUMMARY/LOCATION from v['title'], v['location']

if word == 'rsvp':
    t = message['thing']                      # replaces the three-way search at 196-197
    if str(t['values'].get('status', '')).casefold() in ('cancelled', 'canceled'):   # hand value table again
        raise ValueError('that event is cancelled')
    return answer([line('claim', target), line('make', kind='board-rsvp', ...)], t)
```

**Simpler:**
- `calendar` becomes correct with almost no change. Its `len == 10` logic was right; only its input was wrong.
- `rsvp` and `calendar` lose the three-way search.
- The `post` path could share the kernel's `time` reader instead of its own `stamp()` (112-115). The draft gives no way to ask the kernel "does this value read as a time?" for a value that isn't on a thing yet, so the board keeps its own reader for validation. Two readers again.

**Harder or not covered:**
- **RSVP capacity lives in `claim`, a kernel word.** The draft's table says the feed-item seat bug is "module logic … `board.rsvp` must treat that as unlimited" (draft §4, row 9). **That's misattributed:** board.rsvp never reads seats. The one-seat default is `kernel/words.py:786`. Fixing it needs one of:
  - `claim` reading through a shape;
  - board.rsvp not calling `claim` when there are no seats, which loses claim's once/undo/seal.

  The draft's cost table (§5) lists no kernel word adopting reads.
- **Writes:** the board never `set`s the event. Like the House, **it has no customer for set-through**.

---

## 3. Two new modules, from scratch

### 3.1 An importer: Canvas assignments (with Google Calendar notes)
Alex is a Cal Poly student on Canvas (memory: user profile). Canvas's own field names are `name`, `due_at` (ISO UTC `…Z` or null), `points_possible`, `html_url`, `course_id`, `description` (HTML), and `submission.workflow_state` (`unsubmitted|submitted|graded`).

The module (imagined):
```python
# module installed `for` Alex (do/see on its own, outside calls: modules.py:10-17); token from its own .env, never the world
KIND = 'canvas-assignment'

def facts_of(a, course):
    f = {'canvas_id': a['id'], 'course_id': a['course_id'], 'course': course['name'], 'name': a['name'],
         'due_at': a.get('due_at'), 'points_possible': a.get('points_possible'), 'html_url': a['html_url'],
         'submission.workflow_state': (a.get('submission') or {}).get('workflow_state'),
         'description': html_to_text(a.get('description') or '')[:4000]}
    return {k: str(v) for k, v in f.items() if v not in (None, '')}       # 1st-try bug: `due_at=` REMOVES a fact

def sync():
    have = {r['canvas_id']: r for r in see('rows canvas-assignment exact=yes')}
    for course in canvas('/courses?enrollment_state=active'):
        for a in canvas(f"/courses/{course['id']}/assignments?include[]=submission"):
            f, old = facts_of(a, course), have.get(str(a['id']))
            if old is None:
                do(line('make', kind=KIND, sees='me', **f))
            else:
                changed = {k: v for k, v in f.items() if str(old.get(k, '')) != v}
                gone = {k: '' for k in old if k in FIELDS and k not in f}       # due date removed upstream
                if changed or gone:
                    do(line('set', old['id'], **changed, **gone), saw={old['id']: old['rev']})
```

**For Google Calendar, the same with two traps:**
- `start` is an *object*, `{dateTime, timeZone}` or `{date}`, so the importer must flatten it.
- Google's names are camelCase (`dateTime`, `htmlLink`, `iCalUID`). A line's key must match `^[a-z_][a-z0-9_.-]*=` (`kernel/lines.py:12`), and `make`/`set` refuse anything else (`kernel/words.py:563`). So `start.dateTime=…` isn't parsed as a key at all; it lands in `words`.
- **"In their own field names" is impossible for camelCase sources.** Every importer of a JSON API needs a renaming function, and the first one written will drop data silently.

**Where the design helps (imagined):**
- The importer keeps `name` and `due_at`. It doesn't need to know the board, the House or the due-soon module exists.
- Canvas `due_at` is ISO Z, so it reads as `time`. Google `start.date` stays a date, so all-day stays all-day.

**Where it hurts:**
- **Wiring is N×M.** Spellings live on the *consumer*: each word's `reads=` and each kind's `needs`. Every new importer means a steward edit to every consumer's shape (`due|due_at|…`). Only a steward or leader may declare a kind with needs (`kernel/kinds.py:372-375`), and a re-offer doesn't override a steward's `word-set` (SHAPE §17). The importer can't say "my `due_at` is a due" anywhere.
  - Twelve months in, `reads="due|due_at|deadline|dueDate|due_on|duedate|…"` is the new bespoke table.
  - **Proposal (imagined):** let a *producing* kind declare its mapping once, for example `make kind=kind name=canvas-assignment reads_as="due=due_at title=name done=submission.workflow_state:submitted|graded"`.
  - Then a consumer asks only for `due:time`, and the work is N+M, not N×M.
  - It still never adds power: grants and rules keep matching the thing's own kind (kinds.py:19).
  - Keep consumer-side spellings too, for words that must be exact.
- **No write-time check.** `make` doesn't say "`due_at` 'Friday' won't read as the `time` that `due.soon` reads". The importer learns only when a consumer refuses, and it never sees those refusals (§5.4).
  - `make` already appends notes about unusual values (`kernel/words.py:680-688`). A typed note in the same place is cheap.
  - **Or:** `make kind=X through=<kind>`, writing canonical forms.
- **Done-ness** (`submitted`, `graded`) is a value. The draft leaves value meaning for later; see §3.2.

**What I'd get wrong on the first try:**
- empty values (`due_at=` removes a fact);
- camelCase keys;
- HTML in `description`;
- forgetting `sees=me`, so Alex's grades become visible to the place;
- re-making on every sync because `rows … canvas_id=123` compares strings and I stored an int;
- trusting `due_at` as local time when it is UTC.

**Evidence on the draft's "importers normalize" counter-hypothesis (imagined):**
- An importer author *won't* normalize names: source names are what make idempotent sync and links back possible.
- *Formats* from APIs are mostly ISO already.
- The unreadable values in the trials came from people typing (`tomorrow after lunch`, `2026-11-23 15:00`) and from iCal's basic format.

So: spellings are needed at once; `time` matters mostly for hand-typed values and iCal; `person` and `point` matter least for importers. That suggests building in stages (§6).

### 3.2 "Due soon" across board events, task cards, Tracker issues and Canvas
The module (imagined):
```python
OFFER = [dict(word='due.soon', kind='see', takes='[within=3d]', help='due.soon [within=3d]: what is due or starts soon, yours first',
              reads='due|due_at|deadline|start|begins|dtstart:time title|name|summary:text '
                    'who|assignee|for:person? done:yes?')]
SOURCES = ('task', 'event', 'issue', 'canvas-assignment')   # NOT `rows any`: a task card's `when` is a card
                                                            # timestamp (map-calendars finding 7). World data later.

def soon(call, within):
    now, out = utc_now(), []
    zone = call.caller.get('zone')                     # NOT in the draft: whose "tonight"?
    for kind in SOURCES:
        for t in call.see(f'rows {kind} through=due.soon'):
            v, rd = t['values'], t['reading']
            if 'due' in rd['unread']:
                out.append(dict(id=t['id'], title=v.get('title'), problem=f"can't read {rd['raw']['due']!r} as a time"))
                continue
            if 'due' not in v or is_done(t):
                continue
            when = instant(v['due'], zone, end_of_day=(rd['from']['due'] != 'start'))  # a date: due = end of day,
            if now <= when <= now + within:                                            # starts = start of day
                out.append(dict(id=t['id'], title=v['title'], when=when,
                                verb='starts' if rd['from']['due'] in ('start', 'begins', 'dtstart') else 'due',
                                mine=v.get('who') == call.person))
    return sorted(out, key=lambda r: (not r['mine'], r['when']))       # sort INSTANTS, never the strings

def is_done(t):     # what the draft leaves to every module: one hand table per vocabulary
    f = t['facts']
    return (str(f.get('lane', '')).casefold() == 'done' or str(f.get('status', '')).casefold() in ('closed', 'done', 'cancelled')
            or str(f.get('state', '')).upper() == 'CLOSED' or f.get('submission.workflow_state') in ('submitted', 'graded'))
```

**Where the design helps:**
- One `rows … through=` per kind gives every due time in one form.
- `unread` gives a "can't read this date" line instead of a crash.
- Dates stay dates, so "due Friday" isn't treated as midnight.

**Where it hurts:**
1. **Value meaning is the whole job.** A reminder for a submitted assignment, a closed issue or a cancelled event is the failure Alex sees first. `is_done` is the per-vocabulary coupling shapes were meant to remove. A `done:yes` read only helps if *some* kind can say `submission.workflow_state=graded` means `done=yes`. That is the producer-side mapping of §3.1, extended to values.
   - **For a module author this is not "later":** a cross-vocabulary module can't be written correctly without it.
2. **Provenance must be machine-readable.** `start` (be there) and `due_at` (hand it in) are different deadlines. The module reads `reading.from.due` to pick its wording. The draft's `read: {who: "assignee 'Alex'"}` is a sentence, not data.
3. **Canonical times with offsets don't sort as strings.**
   - `2026-11-06T01:00-08:00` sorts before `2026-11-06T05:00Z` yet is later.
   - Python raises `TypeError` comparing a `date` with a `datetime`.

   That is the same class of failure as the board's `Invalid isoformat`, moved one step later. The kernel's typed sort (draft §3.3) fixes the kernel's sort, not the module's.
4. **No reader zone.** The draft's `timezone=` reads *floating values* in the zone of the thing's place. A reminder needs the *reader's* zone for "today" and for date-only dues. The call carries none.
5. **People.**
   - `who` is a name on task cards, `assignee` a name on Tracker, `user` a GitHub *login* on gh-issues, and `for` an id on Canvas things.
   - `person` reads names "exactly one visible person has": `alexh` never matches, and a second Alex flips every card from read to unread.
6. **Membership vs reach.** Does `rows task through=due.soon` *drop* things the word wouldn't reach, or list every task with `unread`? The draft doesn't say. Here I want them listed (to say "can't read"); for the House I'd want them dropped.

What I'd get wrong first: sorting strings; `date` vs `datetime`; reminding about submitted work; `rows any`; and a timer that wakes JEFF (memory: no timer wakes). The reading belongs on a lens Alex opens; a notification is a plain `happen`, not a wake.

---

## 4. The board redeveloped: `happening` with `begins`, `venue`, `capacity`
**Set-up (imagined):** someone ships `kind=happening` with `title`, `begins`, `venue`, `capacity`, `blurb`, `signups_close`, and their own `happening.rsvp`, which **decrements `capacity`** (it stores how many places are left).

**Reads:** these work under the draft if a steward opens `event` with `start|begins` and `location|venue` spellings.
- `board.calendar <happening>`: `begins` → `start`, canonical. Fixed.
- `map.show <happening>`: `venue` is text, so it is geocoded unless it names a structure id.
- `rows event` lists happenings, read as `start`.

**Writes** fail, and the shape layer can't fix them:

| Press | What runs (read) | What happens (imagined) |
|---|---|---|
| `board.rsvp <happening>` | `claim <id>` + `make board-rsvp` (board.py:208-209) | `claim` reads raw `seats`. It is absent, so 1 seat (words.py:786). The 1st RSVP says "0 seats left"; the 2nd is refused "taken". The happening still says `capacity=40`. |
| `signups_close` | `claim` compares raw `closes` (words.py:789) | never read; sign-up never closes |
| board feed "full" | `seats_left` from raw `seats` (kernel.py:477) | never full |
| `happening.rsvp` after board RSVPs | writes `capacity=39` | doesn't count `claim:` facts, so two seat models disagree |

**With the draft extended so `claim` reads `seats|capacity:number` (imagined):** the board counts claims against 40. But `capacity` here is *remaining*, not *total*.
- After one happening-RSVP (39) and one board claim, the board thinks 38 are left and the happening thinks 39.
- **`seats|capacity` is a spelling that lies.** Types can't say "total vs remaining", and `set capacity=… through=` can't either.
- This is a different *model*, not a different name.

**What works, and the draft should say so:**
- For a write with app semantics, route to the owner's word: plain `rsvp <happening>` dispatches to `happening.rsvp` (own kind's word first, SHAPE §17 "Plain words").
- The board's lens should press plain `rsvp $id`, not `board.rsvp $id`. That is FRICTION §2 option (a) for writing.
- Shapes are for reading.
- `set … through=` sits awkwardly in between:
  - safe only where spellings are pure synonyms (`title|name`, `end|dtend`);
  - wrong where they are vocabulary roles (`lane|status|state`) or models (`seats|capacity`);
  - the draft can't tell them apart.

**Where no owner word exists (an iCal feed item with no seats):** `board.rsvp` should make `board-rsvp` without `claim`, or `claim` should treat a missing `seats` as unlimited only when asked. Either way it is a kernel-word decision the draft doesn't list.

---

## 5. Developer experience

### 5.1 Is `thing` the right surface? Yes, with an envelope
**What the draft's flat dict mixes (draft §3.1):**
- canonical values (`who: "dk2"`, which overwrites the raw `assignee`'s meaning but not its key);
- raw facts ("the thing's other facts, untouched");
- three reserved keys, `through`, `read` and `unread`. A rows-filled thing also carries `as` (`kernel/words.py:870-871`).

**Problems for an author:**
- **Collisions.** None of `read`, `unread`, `through` is a kernel-reserved fact (`kernel/words.py:561-564`). A Gmail adapter's `read=yes` (memory: adapters word) collides on the first email. A route can say `through`.
- **Overlays.** When a thing spells the shape's own name in another form (`start=20261106`), `thing['start']` is the canonical value. The raw survives only inside a provenance *sentence*. `thing['dtend']` is raw while `thing['end']` is canonical. Every `.get` needs the author to remember which.
- **Unread collapses to absent (§2.1a).** This is the important one.

**Proposal (imagined):**
```json
{"t": "call", "use": "…", "word": "board.calendar", "args": {"target": "dk901", "words": "", "kv": {}},
 "caller": {"id": "dk2", "person": "dk2", "name": "Alex", "zone": "America/Los_Angeles"},
 "thing": {
   "id": "dk901", "kind": "feed-item", "rev": 4,
   "values":  {"start": "2026-11-06", "end": "2026-11-07", "title": "Beach cleanup", "location": "Cowell Beach"},
   "reading": {"through": "board.calendar", "shape_rev": 12, "reader": "dk2 via board",
               "from": {"start": "dtstart", "end": "dtend", "title": "summary"},
               "raw":  {"start": "20261106", "end": "20261107"},
               "unread": {}, "via": {}, "private": false},
   "facts":   {"summary": "Beach cleanup", "dtstart": "20261106", "dtend": "20261107", "location": "Cowell Beach", "uid": "…"}}}
```
- `values` holds **only** the shape's names.
- `facts` holds exactly what `look` returns, posts included, not a summary.
- `reading` holds data, not prose. `unread` is a top-level sibling the author can't miss.
- `look … through=` and `rows … through=` return rows in the same envelope.
- **Always send `thing` when the target is a visible thing, shaped or not** (an empty shape → empty `values`). Then:
  - "when is `thing` present?" stops being a question;
  - `reads=` never needs to count as "having a shape". It matters because shaped words outrank unshaped ones in dispatch (`kernel/kinds.py:313-327`; chats finding 4). Adding optional reads to `map.show` must not change what plain `show` dispatches to.
- **Typed JSON for canonical values:** numbers as numbers, `yes` as booleans, a point as `[lat, lon]`, instants as UTC `…Z`. Keep the original offset in `raw` (or `values.<name>_zone`). Strings with mixed offsets are the §3.2 trap.

**The draft must also say three things:**
- **(a)** `thing` is read as the caller narrowed to the module, as `module_see` reads (`kernel/kernel.py:1677-1681`).
- **(b)** It counts as the caller's look, as `module_see`'s rows do (1684-1690).
- **(c)** Every hop in `via` joins the call's `saw`.

**The cache:** "per-(thing, rev, shape)" (draft §5) is the wrong key. A reading also depends on:
- the reader;
- the other people's names (`person`);
- the hopped thing's rev (`point`);
- the place's `timezone`;
- the kind declarations.

The kinds cache already clears on every record (`kernel/kinds.py:101-106`). Do the same.

### 5.2 Is `through=` discoverable?
- **Mostly not needed, if `thing` is always sent.** Only long-runners (the builder), list readers (map layers, due-soon) and second things on a line (`board.answer reply=`, `map.show map=`) need it.
- **Name it in four places:**
  - `help look` and `help rows`;
  - the protocol table in SHAPE §17;
  - the module docstring (`kernel/modules.py:1-26`);
  - `actions <thing>`, which could add a line such as "read as board.calendar: start ✓ (from dtstart), end ✓, location ✗ unread".
- **Ambiguity:** `through=task` may be a kind *or* a bare verb note (`task-done` style names are bare, SHAPE §17). Say which wins (word first), and echo it in `reading.through` as `word:x` or `kind:x`.
- **Missing:** `through` as a field of the protocol's `see` message (`{t: see, use, line, through}`). The kernel then re-reads every returned row that has an `id` through the shape. That covers module see words (`board.feed` as a map layer), which `look`/`rows` arguments can't.

### 5.3 Do `read`/`unread` help or clutter?
- **`unread` helps** and must be impossible to miss, so make it a sibling, not a key among facts.
- **`read`/`from` helps** where provenance changes meaning (due vs starts) and for debugging.
- **On `rows … through=` over 2,174 things, both are noise** in the text view. Keep them in `rows`' JSON. Print them in `look` text and `actions` only. Don't print them per row in `rows` text unless `explain=yes`.
- **Merge `rows`' existing `as` note** (`kernel/words.py:870-871`) into the same `reading`, so a row has one provenance, not two.

### 5.4 Refusals: a person vs a module author
**A person** needs one sentence:
- the thing by name;
- the value, if the person can see it;
- the line that fixes it.

For example: "board.calendar needs a start it can read as a time; Coffee (dk901) says 'tomorrow after lunch'. set dk901 start=2026-11-07T13:00 fixes it." The draft's wording (§3.3) is nearly this; add the fix line.

**An author never sees these refusals today.** The kernel refuses *before* the module is asked (`kernel/kinds.py:291-311`; SHAPE §17 "A module word is refused before its module is asked"). Every call the shape turned away is invisible to the person who could widen it.

**Proposal:** keep them in the module's refusal log, which `k.refusals.keep` already exists for (`kernel/modules.py:102, 132, 212`). Count them in `status <module>` and `look <module>`, for example: `board.calendar: 37 refused before asking this week: start unread 31 ('Nov 6' ×19, 'tomorrow after lunch' ×12), not an event 6`.

- **For a steward** add "word-set board.calendar reads=… widens it".
- **For a member** never add it.

### 5.5 What I'd want in `help` and a test harness
1. **`help <word>` prints its shape in plain words, with an example per type.** For example: "acts on an event · needs start (a time: 2026-11-06 or 2026-11-06T19:00-08:00) · reads end, title, location".
2. **A see word, `reads <thing> <word>` (or `look <id> through=<word> explain=yes`),** listing each need: the spelling found, the raw value, the typed value, and why it is unread.
3. **A see word for values not yet on a thing,** for example `read time "2026-11-23 15:00" in=<group>`. Then the board's `post` validation (board.py:112-115), importers and `map.add` share the one reader instead of three `stamp()`s.
4. **An importable pure function.**
   - `from kernel.kinds import read_through`, with a small context (people, zone, things for hops).
   - Modules unit-test their shape without a kernel.
   - Since modules may be in any language, (3) is the protocol answer and this is the Python convenience.
5. **A probe over a copied world.** It runs a word's shape over every thing and prints reach / read / unread counts and the top unread raw values. All three trial agents built this by hand (`trials/*/trial.py`); commit it once.
6. **Fixture worlds.** Keep the trial vocabularies (task cards, Tracker `issue`, `gh-issue`, iCal feed, `when`/`where` meetings, Twitch) as a small genesis, so a module change shows its reach table before it lands.

---

## 6. Recommended changes to the draft, in order
1. **Envelope the reading:** `thing = {id, kind, rev, values, reading{through, shape_rev, from, raw, unread, via, private}, facts}`.
   - Same envelope from `look`/`rows … through=`.
   - Typed JSON values, instants in UTC.
   - Always sent for a visible target.
   - Read as the caller narrowed to the module; counts as their look; hops join `saw`.
2. **Optional reads are strict when present, by default:** an optional read that is present but unreadable refuses, like a need.
   - A `?` marks a lenient read for words with their own fallback (the map).
   - This turns the silent-skip class (the 1,255) into refusals without the author remembering `unread`.
3. **Defer `set … through=`.** None of the House, map or board writes through a shape. It would reproduce the `status`→`lane` move.
   - For cross-app writes with app meaning, route to the owner's word (plain-word dispatch) and say so in the draft.
   - Revisit when a real module needs it, and only for needs marked as pure synonyms.
4. **Put the kernel's own readers in scope.**
   - `claim` (`seats`, `closes`), `vote`/`pin until` (`closes`, `pin_until`) and the derived `seats_left` read through the same function.
   - Correct §4, row 9: the one-seat default is `kernel/words.py:786`, not board logic.
5. **`through` at the protocol level** on `see` messages, so rows from module see words can be read too.
6. **Producer-side mapping:** a kind may say `reads_as="due=due_at title=name"`, and later values (`done=submission.workflow_state:submitted|graded`). This keeps wiring N+M.
   - Value meaning should be planned now, not later: the House's costliest failure and due-soon's correctness both depend on it.
7. **Write-time help for writers:**
   - typed notes on `make`/`set` when a value won't read as the type a kind's consumers read;
   - a `read <type> <value>` see word.
8. **Context in the call:** the caller's `zone`.
   - Also give the place a `timezone` at founding, so Alex's own `2026-11-23 15:00` meetings aren't unread on day one.
9. **Visibility for authors:** refusals before asking go to the module's log, are counted in `status`/`look <module>`, and `help <word>` prints its shape.
10. **Build in stages**, each with the trial rerun the draft promises (§7):
    - (a) spellings in `look`/`thing` plus `reads=` plus the envelope;
    - (b) `time` and `number`;
    - (c) `person` and `point` hops;
    - (d) value maps.

    Stage (a) alone fixes the map's 6/6, the House's titles and the calendar's missing ends.

**Answers to the draft's open questions, from this seat:**
- **Q1:** has/reads is right for lists, with recommendation 2 for optional reads.
- **Q2:** no automatic through=; go further and defer set-through.
- **Q3:** yes to the hop, with `via` and revs, and a stated depth (the map uses 2).
- **Q4:** too clever for authority. If kept, mark by-name readings in `reading.from`, so an owner check can refuse them.
- **Q5:** no customer; defer.
- **Q6:** types on the consumer's need, *plus* producer mappings.
- **Q7:** `through=` is fine. Resolve word vs kind.

## 7. What would change my mind
- **If the rerun shows authors don't fall into the unread-as-absent trap with the flat dict** (say, three fresh agents adopting it all check `unread`), the envelope is extra ceremony.
- **If a real module turns up that writes a shared aspect on foreign things** (a calendar that moves events, say) and dispatch to the owner's word can't serve it, set-through earns its place. Even then, only for synonym needs.
- **If importers end up normalizing names after all** (§3.1 says they won't), producer-side mapping isn't needed.
- **If the kernel's own words are to stay raw on purpose** (they are the floor, and apps should bring words), recommendation 4 becomes "say so, and move RSVP off `claim`".

## 8. Not verified
- **Nothing ran.** Every rewrite is on paper; no shape, payload or harness was tried. No kernel, module or world was started.
- **Python behaviour:** the `date`/`datetime` `TypeError` and the offset-sorting claim are from my knowledge of Python's `datetime` and string ordering, not run here.
- **API fields:** Canvas and Google Calendar field names are as I recall the public APIs, not checked against them.
- **Not checked:** whether `make` drops or refuses an empty value (I relied on SHAPE §17's `set` "`k=` alone takes a fact away"), and whether `module_own` gives a module installed `for` Alex `sees=me` as Alex.
- **Not read:** the other reviews in this folder (`shape-reads-house.md`, `-kernel-shape.md`, `-residents.md`), so overlaps with them are unchecked.

---

# Round 2: against draft 2 (same reviewer, 28 Oct 2026)

> Draft 2 is read in full (`shape-reads.md`, lines 1-191). It is still all on paper: nothing ran. Code blocks are **imagined**; file:line references are **read**.
> - **Since round 1 I also read:**
>   - the door hands `saw` straight to `run` (`kernel/door.py:266`);
>   - `fence` reads the per-aspect `{rev, aspects}` form (`kernel/kernel.py:829-836`);
>   - only module answers validate that form (`_module_saw`, `kernel/kernel.py:1644-1658`).
> - **Envelopes below** follow draft 2 §2: `values` / `reading` / `basis`, with no raw facts.

## R1. The House: `start` and `assert_owned`
```python
BUILD = dict(acts_on='task', needs='title|name|summary',
             reads='text|body|description acceptance|criteria who|assignee:id lane|status|state '
                   'paused cancelled permission_required approval_required builder build_run')  # bookkeeping as text reads

def start(self, msg):
    t = msg.get('thing')
    if t is None:                                    # not visible, OR no look grant: the module can't tell which
        return {'refused': 'choose a visible task card'}
    v = t['values']                                  # an unread `who` never gets here: strict-when-present refused it
    if v.get('who') and v['who'] not in (msg['caller']['person'], self.h.jeff_id):
        return {'refused': 'task has another owner; ask that owner to release it first'}
    if held(v) or claimed(v, prev): ...
    state = dict(..., title=v['title'], shape=t['reading']['shape_rev'],
                 based={k: v.get(k, '') for k in ('title', 'text', 'acceptance', 'who')})

def assert_owned(self, state):
    t = self.session(state['requester']).look(state['task'], through='word:house.build')   # the door, as the agent
    v, rd = t['values'], t['reading']
    if rd['unread']:                                 # look doesn't refuse; this line is the module's to remember
        raise RuntimeError('task now says ' + ', '.join(f"{k} {x!r}" for k, x in rd['unread'].items()) + '; held')
    if v.get('build_run') != state['run'] or held(v):
        raise RuntimeError('task claim changed or is held; stop this operation')
    if rd['shape_rev'] != state['shape']:
        state.update(shape=rd['shape_rev'], based=...)          # the reading changed, not the card: note it, go on
    elif any(v.get(k, '') != b for k, b in state['based'].items()):
        raise RuntimeError('task instructions or owner changed; review the correction before continuing')

# writes: plain set of the House's own facts, fenced on what was read
door.call('/do', f'set {task} build_phase={q(p)}', saw=t['basis'])
```

**Simpler:**
- **Owner check:** at admission, the unread-`who` trap is gone.
- **Fewer stale refusals:** `basis` is per-aspect, so the House's own `build_phase` writes and JEFF's unrelated edits no longer make the next write stale. Today that takes a four-try retry loop (`builders.py:160-173`).
- **No extra look:** declaring the bookkeeping aspects (`builder`, `build_run`, `paused`…) as text reads makes `thing` enough.

**Still hurts:**
- **The re-read path isn't strict.** Strict-when-present runs only at admission; `look … through=` never refuses. The builder re-reads for hours, and there `unread` still looks like absent unless the code checks `reading.unread` (the line marked above).
  - **Example:** a card that started with no owner gets `who=Sable` (a name) mid-build. `values.who` stays absent, `'' == ''`, and the owner check passes.
  - **Ask:** the reading says whether the word would admit it, for example `reading.refuses: {who: "…"}` (empty when it would). Or `look … through=<word> strict=yes`.
- **`thing` absent can mean two things:** not visible, or no grant. The module keeps its old `look` path forever, and its error can't say which.
- **`shape_rev` needs a definition.** It must be a digest of the *resolved* shape (word needs plus `acts_on` kind), not a rev. `ui_install.py:70-89` sets `accent`/`field_labels`/`compose_label` on kind things, and a rev would trip on those.

**Made worse:**
- **`who:id` with strict-when-present refuses every owned native card on day one.**
  - Alex's cards say `who=Alex` / `who=JEFF`. The House compares names at `builders.py:202, 249, 383`, `manager.py:64, 99` and `house.py:592`.
  - So `house.build` refuses "assignee 'Alex' isn't a person here" on the House's own board until every card, the task board's writer and the lenses move to ids.
  - Draft 2's cost (§7) lists "owner by id" in the House only.
  - **Ask:** add the migration (visible `set dkN who=<id>` acts, the task board writing ids, lenses showing `who_title`) as a stage-2 step *before* the House declares `who:id`.

## R2. The board: `calendar` and `rsvp`
```python
def ics(key, t):                                  # t: a typed time
    if 'date' in t:     return f"{key};VALUE=DATE:{t['date'].replace('-', '')}"
    if 'floating' in t: return f"{key}:{compact(t['floating'])}"     # no Z: iCal floating
    return f"{key}:{compact(t['instant'])}"                            # ends in Z

if word == 'calendar':
    v = message['thing']['values']
    lines += [ics('DTSTART', v['start'])] + ([ics('DTEND', v['end'])] if 'end' in v else [])
    ...                                                                # SUMMARY/LOCATION from v

if word == 'rsvp':
    t = message['thing']
    if str(t['values'].get('status', '')).casefold() in ('cancelled', 'canceled'):   # values: still hand-coded
        raise ValueError('that event is cancelled')
    group = scope(read(use, 'look ' + target)[0])          # EXTRA look: `groups` isn't an aspect, so not in `values`
    return dict(lines=[line('claim', target), line('make', kind='board-rsvp', ..., **{'in': group})],
                saw=t['basis'])
```

**`calendar` is the clearest win of the whole design:**
- the three time tags are exactly iCalendar's three forms;
- the code is shorter than today's and correct for the first time;
- no `stamp()`, no `len == 10` guess.

**`rsvp`:**
- `saw = basis` replaces hand-built revs.
- `claim` reading `seats:count?` fixes the feed item.

**Made worse: absent seats now means unlimited, and structural reach brings a redeveloped `happening capacity=40` to `board.rsvp`.**
- A happening fits `event` by `title start|begins`. Draft 2 rightly says `capacity` isn't a spelling of `seats`, so `claim` sees no seats.
- Draft 1 gave **1 seat**; draft 2 gives **unlimited**, so pressing `board.rsvp` on a happening **overbooks** it.
- Plain `rsvp` dispatching to `happening.rsvp` only helps if the board's lens presses plain `rsvp`.
- **Rule to write down:** a word whose *write* has app meaning reaches by its own kind or marker (`needs="kind|post_kind=event"`, as today at `board.py:401`); a word that only *reads* may reach by structure.

**Still open:** what `claim`'s `closes` means when it is a date or a floating time and there are no zones in v1. The kernel has to compare it with `now`, and no module sits in between to decide.

## R3. The map: `w_show`
```python
SHOW = dict(reads='lat:number? lon:number? at|place? location|venue|where? title|name|summary')

def w_show(call, a, thing=None):
    m, target = the_map(call, a['kv'].get('map')), a['target'] or a['words'].strip()
    t = thing or (None if latlon_text(target) else call.envelope(f'look {q(target)} through=word:map.show'))
    if t:                                        # ids AND names now (look through= also mends the post summary)
        call.saw.update(t['basis'])              # mixes with the map's int revs; _module_saw takes both
        lat, lon, label = position_from(call, ground_getter(call, m), t['values'])   # own hop for at=dkN, as today
    else:
        lat, lon, label = point_of(call, ground_getter(call, m), target)            # lat,lon or a ground name
    ...

# map.layers: see {line: shows, through: 'word:map.show'} gives envelopes even for board.feed
```
**Simpler than round 1 feared:**
- `see {through}` puts layers made from module readings on the same path, so the map has **two** paths (envelope, coordinates), not three;
- names go through `look "<name>" through=`;
- `number` gives floats.

**Still hurts:**
- the hop and its fence stay in the map, as draft 2 says;
- `at=2301,582` is still placed by `latlon_text` (no range check on `at`) until `point` exists;
- the Nominatim privacy leak (FRICTION §7) is untouched. A `reading.private` flag would let the map stay on local tiles for a private title.

**No extra look:** everything `w_show` reads is declarable.

## R4. Due soon
```python
OFFER = dict(word='due.soon', kind='see', takes='[within=3d]',
             reads='due|due_at|deadline|start|begins|dtstart:time? title|name|summary who|assignee|for:id? '
                   'lane|status|state submission.workflow_state')       # done-ness must be declared to be seen

def soon(call, within, zone):                    # zone: the module's own (system local on Alex's PC)
    for kind in SOURCES:
        for t in call.see(f'rows {kind} through=word:due.soon'):
            v, rd = t['values'], t['reading']
            if 'due' in rd['unread']: report(t, rd['unread']['due']); continue
            if 'due' not in v or is_done(v, rd['from']): continue          # hand table per vocabulary (friction 2)
            when = to_instant(v['due'], zone, end_of_day=rd['from']['due'] not in ('start', 'begins', 'dtstart'))
            ...

def to_instant(t, zone, end_of_day=False):       # every module that compares times writes this
    if 'instant' in t:  return utc(t['instant'])
    if 'floating' in t: return local(t['floating'], zone)
    return local_midnight(date.fromisoformat(t['date']) + (ONE_DAY if end_of_day else ZERO), zone)
```
**Simpler:**
- `from` is data, so "starts" and "due" can be told apart;
- instants compare without string traps;
- the `unread` report is free.

**Still hurts:**
- **Zones are the module's problem.** Dates and floating times can't be ordered against instants without one. A module on Alex's PC can use the system's local zone (`naive.astimezone()`, no tzdata needed; imagined, from my knowledge of CPython). One on the Seabright box serving several people can't.
- **"Is it done?"** is still a hand table, and the shape grows with every vocabulary's status name.
- **"Mine" fails on native cards** (`who=Alex` is unread) until the same migration as R1.

## R5. The two questions

**Typed time `{"date"} / {"floating"} / {"instant", "offset"}`: pleasant, with three asks.**
- **Why pleasant:**
  - It maps one-to-one onto iCalendar (R2).
  - A wrong assumption fails *loudly*: `t['instant']` on a date is a `KeyError`, where today's strings sorted wrong silently.
  - `if 'date' in t` / `match t: case {"date": d}` reads well.
- **The pain is the zone, not the tags:** see R4. The kernel's own `closes` has the same pain (R2).
- **Ask 1: fixed precision.** Always seconds: `floating` `YYYY-MM-DDTHH:MM:SS`, `instant` `YYYY-MM-DDTHH:MM:SSZ`, `offset` always present (`+00:00` for a `Z` input). Draft 2's own example has floating without seconds and instant with them, which is two branches in every `compact()`.
- **Ask 2: one helper beside the protocol files.** A ~20-line `agora_time.py` with `ics(t)`, `to_instant(t, zone, end_of_day)` and `sort_key(t, zone)`. All three time-reading sketches above wrote the same function. The `read <type> <value>` see word covers validation, not this.
- **Ask 3: say whether `rows … through=` sorts mixed forms,** and how without a zone (dates as their start in UTC? flagged in `guessed`?).

**Does dropping the raw facts force an extra `look` in the common case?** Mostly no. I accept the privacy reasons, and declaring what a word reads is the point. Case by case:

| Word | Extra look? | Why |
|---|---|---|
| `board.calendar` | no | everything is a shape name |
| `map.show` | no | lat/lon/at/place/location/title declarable |
| House `start` / `assert_owned` | no, **if** bookkeeping is declared as text reads | otherwise two reads per check, at two moments, with two bases |
| `board.rsvp` | **yes, every call** | `groups` (for `in=`, `board.py:37-38, 209`) is kernel-derived, not an aspect, so it can't be declared; the owner (`for`/`made_by`, `board.py:22-23`) likewise |
| due-soon | no | but its shape grows with every vocabulary's status names |

- **Ask:** the envelope carries the derived metadata `rows` already shows anyone who can see the thing: `groups`, plus `by`/`for`.
- **Ask:** make declaring a word's own bookkeeping cheap. Either `reads=` of plain text, with `help` listing those apart as "also reads (its own facts)", or a separate `keeps=`.

## R6. Round-2 asks, in order
1. **Fix the day-one breakage:** migrate `who` names to ids (visible acts, the task-board writer, lenses) before any word declares `who:id`. Put it in the stage-2 cost.
2. **Make re-reads as strict as admission:** `reading.refuses` (or `strict=yes`), so `look … through=` can't hide unread from a long-running reader.
3. **Write-meaning words reach by kind or marker, not structure.** Otherwise "absent seats = unlimited" overbooks a structurally-fitting `happening` through `board.rsvp`.
4. **Envelope carries `groups` and the owner.** Without them, `board.rsvp` needs a second look on every call.
5. **Time:** fixed precision, offset always present, a shared helper, and a stated meaning for date/floating `closes` in `claim`.
6. **Say why `thing` is absent** (`no look grant` vs not visible), so authors can drop the fallback path once granted.
7. **Define `shape_rev`** as a digest of the resolved shape.

**What would change my mind on 3:** if `board.rsvp` is never pressed on things the board doesn't own, because lenses always press plain `rsvp`. Then the rule is redundant, but it is cheap insurance.
