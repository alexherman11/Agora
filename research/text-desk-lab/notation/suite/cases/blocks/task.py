"""A short document edited the way people edit documents: blocks against one text (juniper-8's open question).

The codex team's Studio makes each paragraph its own subject; Sable's hunks keep one text with addressable parts.
The person's test: split a paragraph, move one, join two, two people editing different paragraphs at once, a
comment that stays with its paragraph when the paragraph moves, and a search that finds the paragraph. Facts are
about what the document says, in order, and where a comment and a search land.
"""
SEED = ["look"]

RENT = "Rent is split by the nights each of us sleeps here. Utilities and internet the same way."
RENT1 = "Rent is split by the nights each of us sleeps here."
UTIL = "Utilities and internet the same way."
GUESTS = "Guests staying more than three nights pay a share of utilities."
GUESTS4 = "Guests staying more than four nights pay a share of utilities."
CLEAN = "Cleaning is hired from November, 90 a month."
CLEAN95 = "Cleaning is hired from November, 95 a month."

STEPS = {
    "write": ("Our house rules: rent, guests, cleaning.", lambda p: p["paras"].extend([RENT, GUESTS, CLEAN])),
    "split": ("Put utilities in a paragraph of their own, after rent.",
              lambda p: p.update(paras=[RENT1, UTIL, GUESTS, CLEAN])),
    "move": ("Cleaning goes before guests.", lambda p: p.update(paras=[RENT1, UTIL, CLEAN, GUESTS])),
    "join": ("Actually, put utilities back into the rent paragraph.", lambda p: p.update(paras=[RENT, CLEAN, GUESTS])),
    "together": ("Ben changes guests to four nights while I change cleaning to 95; we both read the same version.",
                 lambda p: p.update(paras=[RENT, CLEAN95, GUESTS4])),
    "comment": ("I ask 'is 95 agreed?' on the cleaning paragraph, then move cleaning to the end.",
                lambda p: p.update(paras=[RENT, GUESTS4, CLEAN95])),
    "find": ("Where do we say something about guests?", None),
}
M4_FACTS = set()


def plan():
    return {"paras": []}


def read_scene(tree, p):
    """The document as the lens prints it: every body text in print order, a one-text body split into its lines."""
    paras = []

    def walk(n):
        for k in n["kids"]:
            if k.get("role") == "body" and k.get("text") is not None:
                paras.extend(x.strip() for x in k["text"].split(" / ") if x.strip())
            walk(k)
    walk(tree)
    return {("order",): tuple(paras)}


def read_view(rows, p):
    return {}


def judge(key, value, p):
    return "holds" if value == tuple(p["paras"]) else "silent"


def probe(name, run):
    w = run.desk.world
    if name == "comment-stays":
        for s in w.subjects.values():
            if any("95 agreed" in c["text"] for c in s.get("comments") or []):
                if CLEAN95 in s["text"] and GUESTS4 not in s["text"]:
                    return "holds", ""
                return "n/e", "the comment is on the whole document; it cannot say which paragraph it is about"
        return "silent", "the comment is gone"
    if name == "search-finds-paragraph":
        out, _ = run.line("find ?guests")
        ids = [l.split()[0] for l in out.splitlines() if l.strip()[:1] == "a" and ('note "' in l or 'doc "' in l)]
        for i in ids:
            s = w.subjects[w.nodes[i]["subject"]] if i in w.nodes else None
            if s and s["text"].strip() == GUESTS4:
                return "holds", ""
        return "n/e", "the search finds the whole document; a paragraph is not a thing a search can name"
    raise KeyError(name)
