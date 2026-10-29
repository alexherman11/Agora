"""Show it on the map: three calendars, three vocabularies (trial, 28 Oct 2026).

Runs on a scratch copy of the live desktop log (never the live world). Loads 50 spots, 300 Seabright board events,
300 imported iCal-ish feed items and 100 of Alex's meetings, then asks, by doing what a steward, an importer and Alex
would do: does one calendar lens show all three, can they go on the map, can board.rsvp / board.calendar reach them,
where do aspect names collide, and how fast is it. The board and map modules are not running here; their real Python
(board.py `call`, map.py `placed`/`point_of`/`w_show`/`w_near`) is driven in-process with its kernel reads answered by
this kernel as the caller, the network cut off (tiles and Nominatim stubbed and counted).

usage: python trial.py <scratch dir>   (copies base/log/0001.jsonl into <scratch>/run-<n>)"""
import importlib
import json
import re
import shutil
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("C:/Projects/Agora4/research")
sys.path.insert(0, str(ROOT / "kernel-lab"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kernel.kernel import Kernel, Actor  # noqa: E402
import data as D  # noqa: E402

SCRATCH = Path(sys.argv[1])
n = 1
while (SCRATCH / f"run-{n}").exists():
    n += 1
WORLD = SCRATCH / f"run-{n}"
(WORLD / "log").mkdir(parents=True)
shutil.copy(SCRATCH / "base" / "log" / "0001.jsonl", WORLD / "log" / "0001.jsonl")

R = {"world": str(WORLD)}
T = {}                                   # timings, ms
t0 = time.perf_counter()
k = Kernel(WORLD)
T["open copied world"] = round((time.perf_counter() - t0) * 1000)
ALEX = Actor("dk2", "dk2", "person")
SABLE = Actor("dk1148", "dk1148", "person")       # a member, not a steward: plays the feed importer
assert k.is_steward("dk2") and not k.is_steward("dk1148")


def q(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def say(actor, line, ok=None, show=True):
    out = k.run(actor, line)
    if show:
        print(f"  [{'ok' if out.get('ok') else 'NO'}] {line[:150]}\n      -> {str(out.get('text'))[:400]}".replace(
            "\n", "\n         "))
    if ok is not None and out.get("ok") != ok:
        print(f"  !! expected ok={ok}")
    return out


def made(out):
    return (out.get("made") or [None])[0]


def timeit(name, fn, reps=5):
    xs = []
    out = None
    for _ in range(reps):
        a = time.perf_counter()
        out = fn()
        xs.append((time.perf_counter() - a) * 1000)
    T[name] = f"median {statistics.median(xs):.1f} ms (min {min(xs):.1f}, max {max(xs):.1f}, n={reps})"
    print(f"  TIME {name}: {T[name]}")
    return out


def section(title):
    print("\n" + "=" * 100 + "\n" + title + "\n" + "=" * 100)


# ====================================================================================================== load
section("LOAD: 50 spots, 300 board events, 300 feed items, 100 meetings")
import random  # noqa: E402
rng = random.Random(28102026)
spot_ids, spot_names = ["dk1026"], ["A spot"]
a = time.perf_counter()
for name, lat, lon in D.SPOTS:
    t = made(say(ALEX, f"make kind=spot map=Seabright name={q(name)} lat={lat} lon={lon}", show=False))
    spot_ids.append(t)
    spot_names.append(name)
for g in D.GENERIC:
    lat, lon = 36.9672 + rng.uniform(-0.01, 0.01), -122.0088 + rng.uniform(-0.015, 0.015)
    t = made(say(ALEX, f"make kind=spot map=Seabright name={q(g)} lat={lat:.5f} lon={lon:.5f}", show=False))
    spot_ids.append(t)
    spot_names.append(g)
SPOTS = spot_ids[1:]
print(f"  {len(SPOTS)} spots made")

board, feed, meet = [], [], []
fails = Counter()
for kv in D.board_events(rng, 300, SPOTS, [n for n in spot_names[1:]]):
    # the board module answers with line('post', text=…, **kv) in Meetings & events. post (and make kind=post) allow
    # 5 a day per person (ran: 295 of 300 refused), so the kernel's clock moves a day every 5 posts, as 300 posts
    # over weeks would arrive
    from datetime import timedelta
    day0 = datetime(2026, 9, 1, tzinfo=timezone.utc) + timedelta(days=len(board) // 5)
    k.clock = lambda d=day0: d
    line = "post " + " ".join(f"{x}={q(v)}" for x, v in kv.items()) + " in=dk309"
    out = say(ALEX, line, show=False)
    k.clock = None
    if out["ok"]:
        board.append(made(out))
    else:
        fails["board: " + out["text"][:80]] += 1
for kv in D.feed_items(rng, 300):
    # the importer is Sable, a member, as a feed importer would be (or a module installed for her)
    out = say(SABLE, "make kind=vevent " + " ".join(f"{x}={q(v)}" for x, v in kv.items()), show=False)
    if out["ok"]:
        feed.append(made(out))
    else:
        fails["feed: " + out["text"][:80]] += 1
for kv in D.meetings(rng, 100, SPOTS, [n for n in spot_names[1:]]):
    out = say(ALEX, "make kind=meeting sees=me " + " ".join(f"{x}={q(v)}" for x, v in kv.items()), show=False)
    if out["ok"]:
        meet.append(made(out))
    else:
        fails["meeting: " + out["text"][:80]] += 1
load_ms = (time.perf_counter() - a) * 1000
T["load 750 makes/posts"] = f"{load_ms:.0f} ms total, {load_ms / 750:.1f} ms each"
print(f"  board {len(board)}, feed {len(feed)}, meetings {len(meet)}; failures {dict(fails)}")
print(f"  TIME load: {T['load 750 makes/posts']}")
R["loaded"] = dict(spots=len(SPOTS), board=len(board), feed=len(feed), meetings=len(meet), failures=dict(fails))
SRC = {}
for t in board:
    SRC[t] = "board"
for t in feed:
    SRC[t] = "feed"
for t in meet:
    SRC[t] = "meeting"
for t in k.things("taskboard-task"):
    SRC[t] = "taskboard-task"


def by_source(rows):
    c = Counter(SRC.get(r["id"], k.state.get(r["id"], "kind")) for r in rows)
    return dict(c)


def rows_of(actor, line):
    out = k.run(actor, line)
    return out.get("rows", []) if out.get("ok") else []


# ====================================================================================================== Q1
section("Q1. ONE calendar lens over all three sources")
from painter.arrangement import compile_view  # noqa: E402

print("-- S0: the world as it is. The board's own post-kind declaration dk333 is named event (fields/required, no needs)")
R["q1_s0_rows_event"] = by_source(rows_of(ALEX, "rows event"))
print("  rows event ->", R["q1_s0_rows_event"])
# Alex's calendar: a component lens over tag:event, by start
lens = made(say(ALEX, 'make kind=lens name=all-events painter=components text="root : column, of tag:event as e, by '
                      'start, each row\nrow : text \\"EV|$e.title|$e.start|$e.end|$e.kind\\""'))


LENS_TOTAL = {}


def lens_rows(actor=ALEX, lid=None):
    """The rows a lens draws, in its order: (title, start, end, kind), from the compiled tree."""
    view = compile_view(k, actor, lid or lens)
    out = []

    def walk(node):
        if node.get("collection"):
            LENS_TOTAL[lid or lens] = node["collection"]
        txt = str((node.get("settings") or {}).get("text") or "")
        if txt.startswith("EV|"):
            out.append(tuple((txt.split("|") + ["", "", "", ""])[1:5]))
        for c in node.get("children") or []:
            walk(c)
    for r in view.get("rows") or []:
        if isinstance(r, dict) and r.get("tree"):
            walk(r["tree"])
    return out


R["q1_s0_lens"] = len(lens_rows())
print("  lens of tag:event draws", R["q1_s0_lens"], "rows")
print("  map layer Events (dk866) shows:", k.state.get("dk866", "shows"), "-> board events on it today:",
      sum(1 for r in rows_of(ALEX, "rows event") if SRC.get(r["id"]) == "board"))

print("-- S1: the steward opens the board's own declaration (dk333) with needs")
R["q1_s1_open_dk333"] = say(ALEX, 'set dk333 needs="title start"')["text"]
print("-- S1b: ... or makes a second declaration named event beside it")
out = say(ALEX, 'make kind=kind name=event needs="title start"')
EV = made(out)
R["q1_s1b_second_decl"] = out["text"]
R["q1_s1b_rows_event"] = by_source(rows_of(ALEX, "rows event"))
print("  rows event ->", R["q1_s1b_rows_event"])
untitled = sum(1 for t in board if not k.state.get(t, "title"))
print(f"  board events with no title (the board allows it: text is the post): {untitled}")

print("-- S2: widen event to every source's spelling")
out = say(ALEX, f'set {EV} needs="title|summary|name start|dtstart|when"')
R["q1_s2_widen"] = out["text"]
rows = rows_of(ALEX, "rows event")
R["q1_s2_rows_event"] = by_source(rows)
print("  rows event ->", R["q1_s2_rows_event"])
fp = [r for r in rows if SRC.get(r["id"]) not in ("board", "feed", "meeting")]
R["q1_s2_false_positives"] = Counter(r.get("kind") for r in fp)
print("  things that are now events but are no calendar's:", dict(R["q1_s2_false_positives"]))
for r in fp[:3]:
    print("     e.g.", r["id"], r.get("kind"), "|", str(r.get("title"))[:50], "| start =", r.get("start"), "|", r.get("as"))

print("-- S2b: include untitled board posts: title|summary|name|text")
out = say(ALEX, f'set {EV} needs="title|summary|name|text start|dtstart|when"')
rows = rows_of(ALEX, "rows event")
R["q1_s2b_rows_event"] = by_source(rows)
print("  rows event ->", R["q1_s2b_rows_event"])

print("-- S3: keep tasks out with a marker: needs kind|post_kind=event|vevent|meeting")
R["q1_s3_narrow"] = say(ALEX, f'set {EV} needs="title|summary|name|text start|dtstart|when kind|post_kind=event|vevent|meeting"')["text"]
print("-- S3b: a new kind, happening, with the marker (the narrower meaning gets a new name)")
HAP = made(say(ALEX, 'make kind=kind name=happening needs="title|summary|name|text start|dtstart|when '
                     'kind|post_kind=event|vevent|meeting"'))
R["q1_s3b_rows_happening"] = by_source(rows_of(ALEX, "rows happening"))
print("  rows happening ->", R["q1_s3b_rows_happening"])
lens2 = made(say(ALEX, 'make kind=lens name=happenings painter=components text="root : column, of tag:happening as e, '
                       'by start, limit 100, each row\nrow : text \\"EV|$e.title|$e.start|$e.end|$e.kind\\""'))
drawn = lens_rows(lid=lens2)
R["q1_lens_happenings_drawn"] = [len(drawn), LENS_TOTAL.get(lens2)]
print("  lens of tag:happening (limit 100) draws", len(drawn), "collection", LENS_TOTAL.get(lens2))
drawn_all = lens_rows(lid=lens)
R["q1_lens_event_drawn"] = [len(drawn_all), LENS_TOTAL.get(lens)]
print("  lens of tag:event (no limit said) draws", len(drawn_all), "collection", LENS_TOTAL.get(lens))
print("  first rows it draws:", drawn_all[:4])
# every page, to see the whole order a person paging the calendar meets
pages = []
for off in range(0, 800, 100):
    lp = made(say(ALEX, f'make kind=lens name=all-events-{off} painter=components text="root : column, of tag:happening '
                        f'as e, by start, offset {off}, limit 100, each row\nrow : text \\"EV|$e.title|$e.start|$e.end|$e.kind\\""',
                  show=False))
    got = lens_rows(lid=lp)
    pages += got
    say(ALEX, f"forget {lp}", show=False)
    if len(got) < 100:
        break
print("  paged through", len(pages), "rows of tag:happening")
drawn_all = pages


def when_of(s):
    """What a person means by each start spelling, as UTC (None when it can't be read)."""
    s = str(s).strip()
    for f in ("%Y%m%dT%H%M%SZ",):
        try:
            return datetime.strptime(s, f).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if re.fullmatch(r"\d{8}", s):
        return datetime.strptime(s, "%Y%m%d").replace(tzinfo=timezone.utc)
    if re.fullmatch(r"\d{8}T\d{6}", s):                 # floating local (TZID LA): call it -08:00
        return datetime.strptime(s, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc) + __import__("datetime").timedelta(hours=8)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", s):
        return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) + __import__("datetime").timedelta(hours=8)
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


starts = [s for _, s, _, _ in drawn_all]
parsed = [when_of(s) for s in starts]
unreadable = sum(1 for p in parsed if p is None)
inv = sum(1 for x, y in zip(parsed, parsed[1:]) if x and y and y < x)
fmt = Counter("iso-Z" if re.search(r"T\d\d:\d\dZ$", s) else "iso-offset" if re.search(r"[+-]\d\d:\d\d$", s) else
              "date" if re.fullmatch(r"\d{4}-\d\d-\d\d", s) else "ical-utc" if s.endswith("Z") else
              "ical-date" if re.fullmatch(r"\d{8}", s) else "ical-floating" if re.fullmatch(r"\d{8}T\d{6}", s) else
              "local-no-zone" if re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d", s) else "words" for s in starts)
order_runs = []
for s in starts:
    f = "iso" if re.match(r"\d{4}-", s) else "ical" if re.match(r"\d{8}", s) else "words"
    if not order_runs or order_runs[-1][0] != f:
        order_runs.append([f, 0])
    order_runs[-1][1] += 1
R["q1_sort"] = dict(formats=dict(fmt), unreadable=unreadable, adjacent_inversions=inv, runs=order_runs,
                    first=starts[:2], last=starts[-3:])
print("  start formats in one calendar:", dict(fmt))
print(f"  sorted by start as text: {inv} adjacent pairs out of chronological order; runs {order_runs}; "
      f"unreadable as a time: {unreadable}")
ends_missing = Counter()
for t, s, e, kd in drawn_all:
    pass
feed_with_dtend = sum(1 for t in feed if k.state.get(t, "dtend"))
lens_feed_end = sum(1 for t, s, e, kd in drawn_all if kd == "vevent" and e)
R["q1_end"] = dict(feed_with_dtend=feed_with_dtend, feed_rows_showing_end=lens_feed_end)
print(f"  feed items with dtend: {feed_with_dtend}; feed rows the lens shows an end for: {lens_feed_end}")
print("-- S4: the end, an optional aspect with two spellings: end|dtend")
R["q1_s4_end"] = say(ALEX, f'set {EV} needs="title|summary|name|text start|dtstart|when end|dtend"')["text"]
print("-- S5: who may declare: Sable (the importer) tries")
R["q1_s5_sable_kind"] = say(SABLE, 'make kind=kind name=vevent-shape needs="summary dtstart"')["text"]
R["q1_s5_sable_extends"] = say(SABLE, 'make kind=kind name=feed-event extends=event')["text"]
R["q1_s5_sable_widen"] = say(SABLE, f'set {EV} needs="title|summary|name|text|label start|dtstart|when"')["text"]
print("-- S6: Sable's view of the calendar (Alex's meetings are sees=me)")
R["q1_s6_sable_rows"] = by_source(rows_of(SABLE, "rows event"))
print("  Sable: rows event ->", R["q1_s6_sable_rows"])
print("-- S7: a second declaration narrows a kind the widen-only rule protects")
out = say(ALEX, 'make kind=kind name=event needs="title start seats"')
EV2 = made(out)
R["q1_s7_second_narrow"] = out["text"]
R["q1_s7_rows_event_after"] = by_source(rows_of(ALEX, "rows event"))
print("  rows event after a later declaration ->", R["q1_s7_rows_event_after"])
if EV2:
    say(ALEX, f"forget {EV2}")
    print("  (forgot it again) rows event ->", by_source(rows_of(ALEX, "rows event")))

print("-- S8: extends: Alex's meetings as events by lineage")
out = say(ALEX, 'make kind=kind name=meeting extends=event')
MK = made(out)
nowhen = made(say(ALEX, 'make kind=meeting sees=me name="Think about the garage" status=tentative'))
SRC[nowhen] = "meeting"
r = [x for x in rows_of(ALEX, "rows event") if x["id"] == nowhen]
R["q1_s8_meeting_without_when_is_event"] = bool(r) and r[0].get("as")
print("  a meeting with no when is in rows event:", R["q1_s8_meeting_without_when_is_event"])
say(ALEX, 'verb cal.go acts_on=event steps="set $1 going=yes" help="cal.go <event>: going"')
R["q1_s8_word_on_it"] = say(ALEX, f"cal.go {nowhen}")["text"]
R["q1_s8_kinds"] = say(ALEX, f"kinds {nowhen}")["text"]
R["q1_s8_rows_meeting"] = by_source(rows_of(ALEX, "rows meeting"))
print("  rows meeting after `meeting extends=event` ->", R["q1_s8_rows_meeting"])
R["q1_s8_kinds_board"] = say(ALEX, f"kinds {board[0]}")["text"]

# ====================================================================================================== Q2
section("Q2. On the map: what map.py reads, driven for real (network cut off)")
sys.path.insert(0, str(ROOT / "kernel-lab" / "modules" / "map"))
M = importlib.import_module("map")
geo_asked = []


def no_geocode(text, near=None, limit=5):
    geo_asked.append(text)
    return []


def no_area(*a, **kw):
    raise OSError("offline trial: no tiles")


M.geocode = no_geocode
M.area = no_area


class KCall(M.Call):
    """map.py's Call, its reads answered by this kernel as the caller (as the module's `see` would be)."""

    def __init__(self, actor):
        self.use, self.person, self.saw, self.looked, self.ground, self.actor = "trial", actor.person, {}, {}, None, actor

    def see(self, line):
        out = k.run(self.actor, line)
        if not out.get("ok"):
            raise ValueError(out.get("text"))
        return out.get("rows", []), out.get("text", "")


def why_not(row):
    if row.get("lat") and row.get("lon"):
        return "lat/lon"
    for key in ("at", "place"):
        v = row.get(key)
        if v:
            return f"{key}=id" if re.fullmatch(r"[a-z]{2,4}\d+", str(v)) else f"{key}=text"
    if row.get("location"):
        return "location text"
    if row.get("where"):
        return "where (map never reads it)"
    if row.get("geo"):
        return "geo (map never reads it)"
    return "nothing placeable"


def map_layer(actor, shows):
    call = KCall(actor)
    m = M.the_map(call)
    gf = M.ground_getter(call, m)
    found, _ = call.see(shows)
    del geo_asked[:]
    a = time.perf_counter()
    items = M.placed(call, gf, found)
    ms = (time.perf_counter() - a) * 1000
    got = {i["id"] for i in items}
    placed_by, unplaced_by = Counter(), Counter()
    for r in found:
        src = SRC.get(r["id"], r.get("kind"))
        (placed_by if r["id"] in got else unplaced_by)[(src, why_not(r))] += 1
    return dict(rows=len(found), placed=len(items), geocode_tried=len(geo_asked), ms=round(ms),
                placed_by={f"{a}/{b}": c for (a, b), c in sorted(placed_by.items())},
                unplaced_by={f"{a}/{b}": c for (a, b), c in sorted(unplaced_by.items())})


print("-- the Events layer (shows=rows event), as Alex")
R["q2_events_layer"] = map_layer(ALEX, k.state.get("dk866", "shows"))
print(json.dumps(R["q2_events_layer"], indent=1))
print("-- a located kind: spellings of the map's own words, so `rows located` hands the map at=")
LOC = made(say(ALEX, 'make kind=kind name=located needs="at|place|where"'))
R["q2_rows_located"] = by_source(rows_of(ALEX, "rows located"))
print("  rows located ->", R["q2_rows_located"])
R["q2_located_layer"] = map_layer(ALEX, "rows located")
print(json.dumps(R["q2_located_layer"], indent=1))
print("-- ... and with location too (at|place|where|location): free text read as at=")
say(ALEX, f'set {LOC} needs="at|place|where|location"')
R["q2_located2_layer"] = map_layer(ALEX, "rows located")
print(json.dumps(R["q2_located2_layer"], indent=1))
print("-- a lat|geo spelling for iCal GEO (lat;lon in one value)")
GK = made(say(ALEX, 'make kind=kind name=geofix needs="lat|geo lon|geo"'))
R["q2_geo_layer"] = map_layer(ALEX, "rows geofix")
print(json.dumps({x: R["q2_geo_layer"][x] for x in ("rows", "placed", "unplaced_by")}, indent=1))

print("-- map.show / map.near on each source (the module's own words, reading raw things)")
call = KCall(ALEX)
samples = {"board place=id": next(t for t in board if re.fullmatch(r"dk\d+", str(k.state.get(t, "place") or ""))),
           "board location text": next(t for t in board if k.state.get(t, "location") == "Seabright Beach"),
           "board place=name": next(t for t in board if k.state.get(t, "place") and not re.fullmatch(r"dk\d+", k.state.get(t, "place"))),
           "feed geo+location": next(t for t in feed if k.state.get(t, "geo")),
           "meeting where=spot": next(t for t in meet if re.fullmatch(r"dk\d+", str(k.state.get(t, "where") or ""))),
           "meeting where=Zoom": next(t for t in meet if k.state.get(t, "where") == "Zoom")}
R["q2_show"] = {}
for label, t in samples.items():
    del geo_asked[:]
    try:
        o = M.w_show(KCall(ALEX), {"target": t, "words": "", "kv": {}})
        res = "ok: " + o["text"]
    except ValueError as exc:
        res = "refused: " + str(exc)
    R["q2_show"][label] = dict(thing=t, result=res, sent_to_nominatim=list(geo_asked))
    print(f"  map.show {t} ({label}): {res[:110]} | nominatim asked: {geo_asked}")
print("-- controls: map.show a spot by id; map.near 0,0 (windows say at=x,y on the screen)")
o = M.w_show(KCall(ALEX), {"target": SPOTS[0], "words": "", "kv": {}})
R["q2_show_spot_control"] = o["text"]
print("  map.show", SPOTS[0], "->", o["text"])
o = M.w_near(KCall(ALEX), {"target": "0,0", "words": "", "kv": {"within": "5000"}})
R["q2_near_null_island"] = o["text"]
print("  map.near 0,0 within=5000 ->", o["text"].replace(chr(10), " | ")[:300])
print("  look <board event> rows:", k.run(ALEX, f"look {samples['board place=id']}")["rows"])
print("-- map.show by a private meeting's NAME (what leaves the machine?)")
dentist = next(t for t in meet if k.state.get(t, "name") == "Review lease with the landlord") if any(
    k.state.get(t, "name") == "Review lease with the landlord" for t in meet) else meet[0]
nm = k.state.get(dentist, "name")
del geo_asked[:]
try:
    o = M.w_show(KCall(ALEX), {"target": "", "words": nm, "kv": {}})
    res = "ok: " + o["text"]
except ValueError as exc:
    res = "refused: " + str(exc)
R["q2_show_private_name"] = dict(name=nm, result=res, sent_to_nominatim=list(geo_asked),
                                 where=k.state.get(dentist, "where"))
print(f"  map.show {nm!r} -> {res[:120]} | nominatim asked: {geo_asked}")
print("-- map.near a spot, kind=event")
sb = SPOTS[0]
o = M.w_near(KCall(ALEX), {"target": sb, "words": "", "kv": {"kind": "event", "within": "400"}})
R["q2_near"] = o["text"].splitlines()[0]
print("  map.near Seabright Beach kind=event within=400 ->", R["q2_near"])
o = M.w_near(KCall(ALEX), {"target": sb, "words": "", "kv": {"kind": "located", "within": "400"}})
R["q2_near_located"] = o["text"].splitlines()[0]
print("  map.near Seabright Beach kind=located within=400 ->", R["q2_near_located"])

# ====================================================================================================== Q3
section("Q3. board.rsvp and board.calendar on feed items and meetings")
print("  in the copied world board.rsvp says needs =", repr(k.state.get("dk297", "needs")),
      "/ board.calendar needs =", repr(k.state.get("dk303", "needs")), "(the module has not re-offered since)")
R["q3_entry_needs_before_offer"] = [k.state.get("dk297", "needs"), k.state.get("dk303", "needs")]
sys.path.insert(0, str(ROOT / "community-app" / "board"))
B = importlib.import_module("board")
spec = [dict(word="board." + nm_, kind=kd, takes=tk, may="members", undo="yes" if kd == "do" else "no", help=h,
             **({"needs": B.NEEDS[nm_]} if nm_ in B.NEEDS else {})) for nm_, kd, tk, h in B.SPECS]
said = k.on_offer(k.module_named("board"), spec)
print("  re-offer:", [s for s in said if "rsvp" in s or "calendar" in s])
R["q3_entry_needs_after_offer"] = [k.state.get("dk297", "needs"), k.state.get("dk303", "needs")]
be = next(t for t in board if k.state.get(t, "title"))
fe = next(t for t in feed if k.state.get(t, "status") == "CONFIRMED")
fe_cancel = next(t for t in feed if k.state.get(t, "status") == "CANCELLED")
me = next(t for t in meet if k.state.get(t, "when", "").startswith("2026"))
R["q3"] = {}
for lbl, t in (("board event", be), ("feed item", fe), ("meeting", me)):
    R["q3"][f"rsvp {lbl}"] = say(ALEX, f"board.rsvp {t}")["text"]
    R["q3"][f"calendar {lbl}"] = say(ALEX, f"board.calendar {t}")["text"]

# the board's real code, its kernel reads answered as the caller
B.hello.update(place="dk1")


def board_call(actor, word, target, **kv):
    def read(use, text):
        out = k.run(actor, text)
        if not out.get("ok"):
            raise ValueError(out.get("text"))
        return out.get("rows", [])
    B.read = read
    try:
        return B.call(dict(use="u", word="board." + word, args=dict(target=target, kv=kv), caller=dict(person=actor.person)))
    except Exception as exc:
        return dict(refused=f"{type(exc).__name__}: {exc}")


print("-- a steward widens board.rsvp to the feed and to meetings (one line, no reload)")
R["q3_word_set_unlooked"] = say(ALEX, 'word-set board.rsvp needs="kind|post_kind=event|vevent|meeting"')["text"]
say(ALEX, "look dk297")
R["q3_widen_rsvp"] = say(ALEX, 'word-set board.rsvp needs="kind|post_kind=event|vevent|meeting"')["text"]
for lbl, t in (("feed item", fe), ("cancelled feed item", fe_cancel), ("meeting", me)):
    R["q3"][f"rsvp {lbl} after widening"] = say(ALEX, f"board.rsvp {t}")["text"]
    ans = board_call(ALEX, "rsvp", t)
    R["q3"][f"board.py rsvp {lbl}"] = ans
    print(f"     board.py answers: {json.dumps(ans)[:300]}")
    for line in ans.get("lines", []):
        say(ALEX, line)                        # admitted as Alex (the module would act for him)
print("-- a second person RSVPs the same feed item (no seats: claim counts 1)")
ans = board_call(SABLE, "rsvp", fe)
R["q3"]["board.py rsvp feed item, Sable"] = ans
for line in ans.get("lines", []):
    R["q3"]["Sable claim"] = say(SABLE, line)["text"]
    break
print("-- Sable RSVPs Alex's private meeting by id")
R["q3"]["Sable rsvp private meeting"] = say(SABLE, f"board.rsvp {me}")["text"]
print("-- board.calendar widened by spelling: start|dtstart|when")
say(ALEX, "look dk303")
R["q3_widen_cal"] = say(ALEX, 'word-set board.calendar needs="kind|post_kind=event|vevent|meeting start|dtstart|when"')["text"]
cal_samples = (("board event", be), ("board event, date only", next(t for t in board if len(k.state.get(t, "start")) == 10)),
               ("feed item", fe), ("feed item, VALUE=DATE", next(t for t in feed if len(k.state.get(t, "dtstart")) == 8)),
               ("feed item, floating+TZID", next(t for t in feed if k.state.get(t, "tzid"))),
               ("meeting", me), ("meeting, local no zone", next(t for t in meet if re.fullmatch(r"\S+ \d\d:\d\d", k.state.get(t, "when") or ""))),
               ("meeting, words", next(t for t in meet if not (k.state.get(t, "when") or "2").startswith("2"))))
for lbl, t in cal_samples:
    R["q3"][f"calendar {lbl} after widening"] = say(ALEX, f"board.calendar {t}")["text"]
    ans = board_call(ALEX, "calendar", t)
    R["q3"][f"board.py calendar {lbl}"] = {x: (str(v)[:300]) for x, v in ans.items() if x != "rows"}
    raw = {x: k.state.get(t, x) for x in ("start", "dtstart", "tzid", "when") if k.state.get(t, x)}
    dt = re.findall(r"DTSTART[^\r]*", str(ans.get("text") or ""))
    R["q3"][f"board.py calendar {lbl}"]["raw"] = raw
    print(f"     raw {raw} -> board.py: {(ans.get('refused') or dt)!r}")
print("-- the safer move: the word says acts_on=event (the kind a steward keeps), and the module re-offers")
say(ALEX, "look dk303")
R["q3_acts_on"] = say(ALEX, 'word-set board.calendar acts_on=event needs="kind|post_kind=event|vevent|meeting"')["text"]
said = k.on_offer(k.module_named("board"), spec)
R["q3_reoffer_after_acts_on"] = [s for s in said if "calendar" in s]
print("  re-offer:", R["q3_reoffer_after_acts_on"], "| entry now acts_on =", k.state.get("dk303", "acts_on"),
      "needs =", k.state.get("dk303", "needs"))

# ====================================================================================================== Q4
section("Q4. Collisions and set's spelling refusal")
task = next(t for t in k.things("taskboard-task") if k.state.get(t, "when") and k.state.get(t, "title")
            and not k.state.get(t, "forgotten"))
R["q4"] = {}
R["q4"]["set task start (a task is an event now, by title+when)"] = say(ALEX, f"set {task} start=2026-11-30T09:00Z")["text"]
R["q4"]["set feed start (a lens editing $e.start)"] = say(ALEX, f"set {fe} start=2026-11-05T19:00Z")["text"]
R["q4"]["set feed dtstart as told"] = say(ALEX, f"set {fe} dtstart=2026-11-05T19:00Z")["text"]
R["q4"]["set meeting title"] = say(ALEX, f"set {me} title=\"Lunch moved\"")["text"]
R["q4"]["set board event end (optional, no spelling)"] = say(ALEX, f"set {be} end=2026-11-05T21:00Z")["text"]
R["q4"]["set feed end (it says dtend)"] = say(ALEX, f"set {fe} end=2026-11-05T21:00Z")["text"]
R["q4"]["sable sets start on her own feed item"] = say(SABLE, f"set {feed[5]} start=2026-11-06T10:00Z")["text"]
# status: three vocabularies under one name
st = Counter()
for t in board + feed + meet:
    v = k.state.get(t, "status")
    if v:
        st[(SRC[t], v)] += 1
R["q4_status"] = {f"{a}:{b}": c for (a, b), c in sorted(st.items())}
print("  status values by source:", R["q4_status"])
cancelled_rows = rows_of(ALEX, "rows happening status=cancelled")
R["q4_rows_status_cancelled"] = by_source(cancelled_rows)
print("  rows happening status=cancelled ->", R["q4_rows_status_cancelled"], "(feed says CANCELLED)")
where_kinds = Counter(a.get("kind") for t, a in k.state.things.items() if a.get("where") and SRC.get(t) != "meeting")
R["q4_where_elsewhere"] = dict(where_kinds)
print("  other things that say where=:", dict(where_kinds))
ex = next((a for t, a in k.state.things.items() if a.get("where") and SRC.get(t) != "meeting"), {})
print("     e.g.", {x: str(v)[:60] for x, v in ex.items() if x in ("kind", "where", "title", "name")})
R["q4_located_false"] = {k2: v for k2, v in by_source(rows_of(ALEX, "rows located")).items()}
print("  rows located ->", R["q4_located_false"])
print("-- dates vs datetimes under start")
dates = sum(1 for t in board if re.fullmatch(r"\d{4}-\d\d-\d\d", k.state.get(t, "start") or ""))
R["q4_date_only_board"] = dates
print(f"  board events whose start is a date: {dates}; meetings whose when is words: "
      f"{sum(1 for t in meet if not re.match(r'20', k.state.get(t, 'when') or '20'))}")

# ====================================================================================================== Q5
section("Q5. Timings at this scale")
R["things"] = len(k.state.things)
print("  things in world:", R["things"], "records:", len(k.log.records))
timeit("rows event (fitted, widened)", lambda: k.run(ALEX, "rows event"))
timeit("rows happening (fitted, marker)", lambda: k.run(ALEX, "rows happening"))
timeit("rows event exact=yes", lambda: k.run(ALEX, "rows event exact=yes"))
timeit("rows vevent (closed kind)", lambda: k.run(ALEX, "rows vevent"))
timeit("lens compile of tag:event (all)", lambda: compile_view(k, ALEX, lens), reps=3)
timeit("lens compile of tag:happening limit 100", lambda: compile_view(k, ALEX, lens2), reps=3)
timeit("actions <board event>", lambda: k.run(ALEX, f"actions {be}"))
timeit("actions <meeting>", lambda: k.run(ALEX, f"actions {me}"))
timeit("kinds <feed item>", lambda: k.run(ALEX, f"kinds {fe}"))
say(ALEX, 'verb meeting.done needs="kind=meeting" steps="set $1 status=done" help="meeting.done <meeting>: done"')
say(ALEX, 'verb vevent.done needs="kind=vevent" steps="set $1 attended=yes" help="vevent.done <vevent>: went"')
say(ALEX, 'verb post.done needs="kind|post_kind=event" steps="set $1 attended=yes" help="post.done <event>: went"')
R["q5_done_family"] = [k.state.get(e, "word") for e in k.entries() if str(k.state.get(e, "word")).endswith(".done")]
print("  done family:", R["q5_done_family"])
R["q5_done_meeting"] = say(ALEX, f"done {me}")["text"]
R["q5_done_feed"] = say(ALEX, f"done {fe}")["text"]
R["q5_done_board"] = say(ALEX, f"done {be}")["text"]
R["q5_done_task"] = say(ALEX, f"done {task}")["text"]
R["q5_done_by_name"] = say(ALEX, 'done "Dentist"')["text"]
R["q5_rsvp_by_name"] = say(ALEX, 'board.rsvp "Beach cleanup"')["text"]
timeit("plain word: done <meeting id> (refused or run, each re-said)", lambda: k.run(ALEX, f"done {meet[7]}"))
timeit("plain word: done \"Dentist\" (by name)", lambda: k.run(ALEX, 'done "Dentist"'))
timeit("named lookup board.rsvp \"Potluck\"", lambda: k.run(ALEX, 'board.rsvp "Potluck"'))
timeit("set with spelling check (feed dtstart)", lambda: k.run(ALEX, f"set {feed[9]} dtstart=20261109T190000Z"))


def churn():
    for i in range(10):
        k.run(ALEX, f"set {board[i]} seats={20 + i % 2}")
        k.run(ALEX, "rows event")


timeit("10 x (set + rows event): cache cleared by each write", churn, reps=2)
call = KCall(ALEX)
timeit("map placed() over rows located (no tiles, no Nominatim)", lambda: map_layer(ALEX, "rows located"), reps=3)
a = time.perf_counter()
Kernel(WORLD)
T["reopen world (replay)"] = f"{(time.perf_counter() - a) * 1000:.0f} ms, {len(k.log.records)} records"
print("  TIME reopen:", T["reopen world (replay)"])

R["timings"] = T
(SCRATCH / f"results-{n}.json").write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
print("\nresults ->", SCRATCH / f"results-{n}.json")
