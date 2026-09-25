"""The household budget: three housemates split the flat's bills by the month, as the person says it.

Meaning decided with Jeff (25 Sep, a311): a share is person-days (total x the person's days present / the sum of
everyone's days present); a person is present on a day d when start <= d < end, and a missing end is open-ended;
the person states the last night, so the end is the day after. A bill is dated: an amount is in force from a day
until the day a new amount starts. A month's statement, once closed, keeps that month's numbers.
"""
import datetime as dt
import re

SEED = ["look"]

JAN = "2026-01-01"
STEPS = {
    "2": ("Ana, Ben and Casey share flat 3B. Rent is 2400 a month, utilities about 180, internet 60.",
          lambda p: p.update(month="2026-10-01",
                             people={n: [JAN, None] for n in ("Ana", "Ben", "Casey")},
                             bills={"Rent": [[JAN, None, 2400]], "Utilities": [[JAN, None, 180]], "Internet": [[JAN, None, 60]]})),
    "3": ("Split October between the three of us.", None),
    "4": ("Casey's last night in the flat is 15 October.", lambda p: p["people"]["Casey"].__setitem__(1, "2026-10-16")),
    "5": ("It's November. Rent goes up to 2550 from 1 November. Keep October's statement as it was.",
          lambda p: (p.update(month="2026-11-01"),
                     p["bills"]["Rent"][0].__setitem__(1, "2026-11-01"),
                     p["bills"]["Rent"].append(["2026-11-01", None, 2550]))),
    "6": ("We've added cleaning, 90 a month, from November.",
          lambda p: p["bills"].update(Cleaning=[["2026-11-01", None, 90]])),
}
M4_FACTS = set()


def plan():
    return {"month": None, "people": {}, "bills": {}}


def _d(s):
    return dt.date.fromisoformat(s)


def month_days(m):
    first = _d(m)
    nxt = (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    return [first + dt.timedelta(days=i) for i in range((nxt - first).days)]


def days_present(p, name, m):
    start, end = p["people"][name]
    return sum(1 for d in month_days(m) if _d(start) <= d and (end is None or d < _d(end)))


def in_force(p, bill, m):
    """The amount of a bill in force on the month's first day, or None."""
    for start, end, amount in p["bills"].get(bill, []):
        if _d(start) <= _d(m) and (end is None or _d(m) < _d(end)):
            return amount
    return None


def total(p, m):
    return sum(a for b in p["bills"] if (a := in_force(p, b, m)) is not None)


def share(p, name, m):
    alld = sum(days_present(p, n, m) for n in p["people"])
    return total(p, m) * days_present(p, name, m) / alld if alld else 0


def expected(p, key):
    kind, m, arg = key
    if kind == "bill":
        return in_force(p, arg, m)
    if kind == "each":
        full = all(days_present(p, n, m) == len(month_days(m)) for n in p["people"])
        a = in_force(p, arg, m)
        return round(a / len(p["people"]), 2) if full and a is not None else "(no one figure: not everyone was here all month)"
    if kind == "owes":
        return share(p, arg, m)
    if kind == "days":
        return days_present(p, arg, m)
    if kind == "sum":
        return total(p, m)
    raise KeyError(kind)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def judge(key, value, p):
    want = expected(p, key)
    if isinstance(value, str) and value.startswith("!"):
        return "visible"
    kind = key[0]
    got = _num(value)
    if kind == "owes":
        if want == 0 and value in ("", "0", "0.00"):
            return "holds"
        return "holds" if got is not None and abs(got - want) < 0.01 else "silent"
    if kind == "sum":
        amount, _, parts = value.partition(" from ")
        for part in filter(None, parts.split(";")):
            who, _, v = part.partition("=")
            if who in p["people"] and judge(("owes", key[1], who), v, p) != "holds":
                return "holds"          # subsumed: that share is already counted wrong
        return "holds" if round(float(amount), 2) == round(want, 2) else "silent"
    if isinstance(want, (int, float)):
        return "holds" if got is not None and abs(got - want) < 0.005 else "silent"
    return "silent"


def read_scene(tree, p):
    """Statements a split lens makes, for the month its heading names: each bill's amount (and 'each pays'), each
    person's share and days here, and the sum the shares imply."""
    out = {}
    m = None

    def walk(n):
        yield n
        for k in n["kids"]:
            yield from walk(k)

    for n in walk(tree):
        if n.get("role") == "heading" and n.get("text"):
            hit = re.search(r"\d{4}-\d{2}-\d{2}", n["text"])
            m = hit.group() if hit else m
    if not m:
        return {("place", "?", "month"): "!no month stated"}
    owes = {}
    for inst in walk(tree):
        if not (inst.get("key") and inst.get("item") and inst["key"].split("#")[0] == inst["item"]):
            continue
        kids = list(walk(inst))[1:]
        who = None
        for k in kids:
            t = k.get("text")
            if t is None:
                continue
            mo = re.match(r"^(.+?) owes ?(.*)$", t)
            mb = re.match(r"^(.+?) (\d+(?:\.\d+)?)(?:, each pays ?(.*))?$", t)
            if mo:
                who = mo.group(1)
                owes[who] = mo.group(2)
                out[("owes", m, who)] = mo.group(2)
            elif mb:
                out[("bill", m, mb.group(1))] = mb.group(2)
                if mb.group(3) is not None:
                    out[("each", m, mb.group(1))] = mb.group(3)
        for k in kids:
            line = k.get("line", "")
            if who and "uninterpretable" in line:
                out[("days", m, who)] = "!uninterpretable"
            elif who and k.get("text") is not None and re.match(r"^(\S*) days here$", k["text"]):
                out[("days", m, who)] = re.match(r"^(\S*) days here$", k["text"]).group(1)
    if owes and all(_num(v) is not None or v == "" for v in owes.values()):
        # the sum the shares imply; judged only when every share is right on its own (the penny), since a wrong
        # share already said it
        parts = ";".join(f"{k}={v}" for k, v in sorted(owes.items()))
        out[("sum", m, "all")] = f"{sum(_num(v) or 0 for v in owes.values()):.2f} from {parts}"
    return out


def read_view(rows, p):
    return {}
