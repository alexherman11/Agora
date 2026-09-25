"""The trip: Embark's case, as the person says it, and the facts that must hold after each step.

Nothing here knows a representation. A solution (R.sol, H2.sol, ...) says which lines state the person's
decisions and which outputs to read; this file says what those outputs must say. Readers turn an output into
statements; judge() compares each statement with the plan.
"""
import datetime as dt
import re

SEED = [
    "look",
    'do create f01 kind=doc title="Big Sur trip" text="Thinking Sat-Sun Oct 10-11, maybe the weekend after. Want McWay Falls, '
    'a hike, one night near the coast (Kirk Creek if a site is free, else Cambria). Sam can only do Sunday."',
]

# the person's words, step by step, and what each changes in the plan
STEPS = {
    "2": ("Saturday 10 to Sunday 11 October. Day 1: McWay Falls, a night on the coast. Day 2: the Ewoldsen hike, "
          "lunch with Sam at Nepenthe, the Bixby Bridge stop.",
          lambda p: p.update(start="2026-10-10", items={"McWay Falls": 1, "Night on the coast": 1, "Ewoldsen hike": 2,
                                                          "Lunch with Sam at Nepenthe": 2, "Bixby Bridge stop": 2})),
    "3": ("Give me an itinerary and a calendar of the two days.", None),
    "4": ("Kirk Creek is full on the 10th: move the whole trip a week, to the 17th.", lambda p: p.update(start="2026-10-17")),
    "5": ("Add Pfeiffer Beach on Saturday.", lambda p: p["items"].update({"Pfeiffer Beach": 1})),
    "6a": ("The hike might not happen: trail status unknown.", lambda p: p["open"].add("Ewoldsen hike")),
    "6b": ("The trail is open again.", lambda p: p["open"].discard("Ewoldsen hike")),
    "7": ("Note on the hike: check the trail report on Friday.", None),
    "8": ("For the night: Kirk Creek campsite, or the Cambria motel.", None),
    "9": ("A site opened up on the 10th: move it back.", lambda p: p.update(start="2026-10-10")),
    "10": ("I don't need the calendars any more; keep why I moved it.", None),
    "11": ("I have the trip open in two tabs and edit the hike in both.", None),
}
M4_FACTS = {"b-kept"}          # a fact whose failure means someone's accepted edit was lost or landed on the wrong thing
M1_STEPS = {"2", "3", "4", "5", "6a", "6b", "7", "8", "9", "10"}   # the recorded runs counted writes for steps 2-10; step 11 was reported apart


def plan():
    return {"start": None, "items": {}, "open": set()}


def day(p, k):
    return (dt.date.fromisoformat(p["start"]) + dt.timedelta(days=k - 1)).isoformat()


def expected(p, key):
    kind, arg = key
    if kind == "date":
        return day(p, p["items"][arg]) if arg in p["items"] else "(not in the plan)"
    if kind == "head":
        return day(p, arg)
    if kind == "members":
        return frozenset(t for t, d in p["items"].items() if d == arg) or "0-of"
    if kind == "day-of":
        return p["items"].get(arg, "(not in the plan)")
    if kind == "open":
        return arg in p["open"]
    if kind == "listed":
        return arg in p["items"]
    if kind == "group":
        return None                      # a part that is not a day has no right value
    raise KeyError(kind)


MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def date_in(text):
    """The date a piece of text states, or None. ISO dates, or 'Sat Oct 17' (the year is the trip's)."""
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\b", text)
    if m:
        return dt.date(2026, MONTHS[m.group(1)], int(m.group(2))).isoformat()
    return None


def read_scene(tree, p):
    """Statements a calendar or itinerary scene makes. A group is a node with a heading child (a day); an instance is
    a repeat member keyed by its thing. Values: a string or set as printed, '0-of' for a repeat that printed 0 of,
    '!<why>' for a visible marker."""
    out = {}
    titles = set(p["items"])

    def instances(n):
        for k in n["kids"]:
            if k.get("key") and k.get("item") and k["key"].split("#")[0] == k["item"]:
                yield k
            else:
                yield from instances(k)

    def texts(n):
        for k in n["kids"]:
            yield k
            yield from texts(k)

    def title_of(inst):
        seen = [k["text"] for k in texts(inst) if k.get("text")]
        for t in seen:
            if t in titles:
                return t
        return next((t for t in seen if not date_in(t) and not t.lower().startswith("open")), "?")

    def line_title(line):
        """A document line '- Ewoldsen hike, morning (? trail status)' names the item it starts with."""
        body = line[2:]
        return next((t for t in titles if body.startswith(t)), body.split(",")[0].strip())

    def visit(n, group_no):
        for k in n["kids"]:
            if any(c.get("role") == "heading" for c in k["kids"]):
                head = next(c for c in k["kids"] if c.get("role") == "heading")
                if (head.get("text") or "").startswith("("):
                    # the printer's own word for a part that is not a day, e.g. '(before the first heading)'
                    out[("group", head["text"])] = "!" + head["text"]
                    continue
                group_no[0] += 1
                g = group_no[0]
                if head.get("absent"):
                    out[("head", g)] = "!" + head["absent"]
                elif head.get("text") and date_in(head["text"]):
                    out[("head", g)] = date_in(head["text"])
                ms = [title_of(i) for i in instances(k)]
                body = [c for c in k["kids"] if c.get("role") == "body" and c.get("text")]
                for b in body:            # a section lens: the day's items are the section's '- ' lines
                    for line in b["text"].split(" / "):
                        if line.startswith("- "):
                            t = line_title(line)
                            ms.append(t)
                            out[("open", t)] = "(?" in line
                for t in ms:
                    placed.setdefault(t, g)
                if not ms and any(c.get("zero") for c in texts(k)):
                    out[("members", g)] = "0-of"
            else:
                visit(k, group_no)

    # A calendar says, per item, which day it is on; an empty day says 'nothing on this day'. An item on no day is
    # wrong on its own only when no day printed 0 of (the empty day already said it).
    placed = {}
    visit(tree, [0])
    if placed or any(k[0] == "members" for k in out):
        for t, g in placed.items():
            out[("day-of", t)] = g
        if not any(k[0] == "members" for k in out):
            for t in titles - set(placed):
                out[("day-of", t)] = "missing"
    for inst in instances(tree):
        t = title_of(inst)
        out[("listed", t)] = True
        for k in texts(inst):
            if k.get("absent") and "uncertain" in k["absent"]:
                out[("open", t)] = False
            elif k.get("text") and k["text"].lower().startswith("open"):
                out[("open", t)] = True
            elif k.get("text") and date_in(k["text"]) and k.get("role") != "heading":
                out[("date", t)] = date_in(k["text"])
    for t in titles:
        if any(k[0] == "listed" for k in out) and ("listed", t) not in out:
            out[("listed", t)] = False
    return out


def read_view(rows, p):
    """Statements a table view makes: each row's day and open question."""
    out = {}
    for r in rows:
        t = r.get("title", "?")
        out[("listed", t)] = True
        if "day" in r:
            out[("date", t)] = r["day"] or "!no day"
        if "uncertain" in r:
            out[("open", t)] = bool(r["uncertain"])
    for t in p["items"]:
        if ("listed", t) not in out:
            out[("listed", t)] = False
    return out


def judge(key, value, p):
    """-> 'holds' | 'silent' | 'silent 0-of' | 'visible'"""
    want = expected(p, key)
    if value == want:
        return "holds"
    if isinstance(value, str) and value.startswith("!"):
        return "visible"
    if value == "0-of":
        return "silent 0-of"
    return "silent"
