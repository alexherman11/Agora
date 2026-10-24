"""The kernel's own words: their dictionary entries (written into the world at genesis) and what each does.

An entry is world data, in the dictionary story's format (research/community-app/DICTIONARY-ENTRY.md): renaming,
aliasing, rewriting help or narrowing who may happens to the entry, not here. Only the implementation is code, named by
`from` and `bound` (`from: kernel, bound: look`). `takes` is in the format's usage notation (`<id>`, `[<id>]`,
`k=<v>`). The entry's kind is kept as `word_kind`, since `kind` is the thing's own kind (`word`), as frontier keeps it
as `word=`. Each function gets (kernel, actor, step, entry, tx, group) and returns {text, rows}; a do word writes facts
into `tx` and the kernel writes the record.
"""
import re
import time

from .kernel import Refused, FLOOR


def _k(word, kind, takes, may, undo, help, **more):
    return {"word": word, "word_kind": kind, "takes": takes, "may": may, "undo": undo, "from": "kernel",
            "bound": word, "help": help, **more}


KERNEL_ENTRIES = [
    _k("look", "see", "[<id>]", "anyone", "no", aliases="l",
       help="look: the feed, pinned posts first, then the newest.\nlook <thing>: one thing, as you may see it."),
    _k("help", "see", "[<word>]", "anyone", "no", aliases="?",
       help="help: the words you may use here.\nhelp <word>: what it does, what it takes and who may use it."),
    _k("post", "do", "<words> [in=<group>]", "members", "yes", once="at most 5 per day per person",
       help="post <words> [in=<group>]: share something in the feed, or in a group's feed.\n"
            "The feed is a slower lane: a few posts a day each. Fast talk belongs in a group's chat."),
    _k("like", "do", "<id>", "anyone", "yes", sealed="yes", once="per person per target", fence="adds",
       help="like <post>: add your weight to a post. Once each.\n"
            "Likes are sealed: the count is shown, not who liked. undo takes yours back."),
    _k("pin", "do", "<id>", "leaders", "yes",
       help="pin <post>: keep a post at the top of the feed, for what matters more than the rest.\n"
            "Leaders pin in their own groups. undo takes a pin back."),
    _k("undo", "do", "[r<n>]", "anyone", "no",
       help="undo: take back your latest act.  undo r<n>: take back that act.\n"
            "You may undo your own acts; leaders, the acts in their groups; stewards, any."),
    _k("off", "do", "<module>", "stewards", "yes",
       help="off <module>: stop a module and take back every grant it holds, in one act. undo turns it on again."),
    _k("status", "see", "<module>", "anyone", "no",
       help="status <module>: what a running module says it is doing."),
    _k("holds", "see", "", "anyone", "no",
       help="holds: what each running module holds now (an overlay, a stream), and since when."),
    _k("make", "do","kind=<kind> [in=<group>] [k=<v> ...]", "members", "yes",
       help="make kind=<kind> [in=<group>] [name=… title=… text=…]: make a lasting thing of any kind: a lens, a button, "
            "a sign-up slot.\nIts other k=v are its first facts. In a group it is seen by the group."),
    _k("set", "do", "<id> k=<v> ...", "maker or leaders", "yes",
       help="set <thing> k=v …: change facts on a thing you made (leaders: any in their group). k= with nothing "
            "after it takes a fact away."),
    _k("forget", "do", "<id>", "maker or leaders", "yes",
       help="forget <thing>: take a thing out of every view. It is never erased: undo brings it back."),
]

# aspects no line may write with make or set: what the kernel itself keeps, or derives
RESERVED_KINDS = {"person", "agent", "module", "grant", "word", "invite", "world", "place", "group"}
RESERVED = {"kind", "made_by", "for", "pinned", "forgotten", "sees", "lives", "from", "bound"}
RESERVED_PREFIX = ("in:", "like:", "member:", "answer:", "sees.", "vote:", "claim:")

FLOOR_HELP = {e["word"]: e["help"] for e in KERNEL_ENTRIES if e["word"] in FLOOR}


def _today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def _post_line(k, reader, t, a):
    by = k.name(a.get("made_by"))
    bits = [f"{t} · {by}: {a.get('text', '')}", f"{a.get('likes', 0)} like" + ("" if a.get("likes") == 1 else "s")]
    if a.get("pinned"):
        bits.append(f"pinned by {k.name(a['pinned'])}")
    groups = [g for g in k.groups_of(t) if g != k.place]
    if groups:
        bits.append("in " + ", ".join(k.name(g) for g in groups))
    return " · ".join(bits)


def _post_row(k, t, a):
    return {"id": t, "kind": "post", "text": a.get("text", ""), "by": k.name(a.get("made_by")),
            "likes": a.get("likes", 0), "pinned": bool(a.get("pinned")), "rev": k.state.rev.get(t, 0),
            "in": [g for g in k.groups_of(t)]}


def _module_of(k, st):
    m = st.target or (k.module_named(st.words.split()[0]) if st.words else None)
    if not m or k.state.get(m, "kind") != "module":
        raise Refused(f"no module called {st.target or st.words or '(nothing)'} here")
    return m


def look(k, actor, st, entry, tx, group, saw=None):
    if not st.target and st.words:
        m = k.module_named(st.words.split()[0])
        if m:
            st.target = m
        else:
            raise k.no_such(st.words.split()[0])
    if st.target:
        t = st.target
        a = k.shown(actor.person, t)
        if a is None:
            raise k.no_such(t)
        k.mark(actor, t, a)
        kind = a.get("kind")
        if kind == "post":
            return {"text": _post_line(k, actor.person, t, a), "rows": [_post_row(k, t, a)]}
        if kind == "module":
            grants = [g for g in k.things("grant") if k.state.get(g, "to") == t]
            live = [k.state.get(g, "words") for g in grants if not k.state.get(g, "revoked")]
            words = [k.state.get(e, "word") for e in k.entries() if k.state.get(e, "from") == f"module:{a.get('name')}"]
            on = "on" if a.get("on") else "off"
            run = "running" if k.modules and k.modules.running(t) else "not running"
            return {"text": f"{a.get('name')} ({t}), a module: {on}, {run}; publishes {a.get('publishes')}; "
                            f"grants: {', '.join(live) or 'none'}; words: {', '.join(words) or 'none'}",
                    "rows": [{"id": t, "kind": "module", "name": a.get("name"), "on": bool(a.get("on")),
                              "grants": live, "words": words}]}
        if kind in ("person", "agent"):
            answers = {x[7:]: v for x, v in a.items() if x.startswith("answer:")}
            text = f"{k.name(t)} ({t}), {'an agent' if kind == 'agent' else 'a person'}"
            if answers:
                text += " · answers: " + ", ".join(f"{q}={v}" for q, v in answers.items())
            return {"text": text, "rows": [{"id": t, "kind": kind, "name": k.name(t), "answers": answers}]}
        if kind == "word":
            return {"text": f"{a.get('word')} ({t}), a {a.get('word_kind')} word: {a.get('help', '').splitlines()[0]}",
                    "rows": [dict(a, id=t)]}
        return {"text": f"{k.name(t)} ({t}), a {kind}", "rows": [dict(a, id=t)]}
    posts = []
    for t in k.things("post"):
        a = k.shown(actor.person, t)
        if a is not None:
            posts.append((t, a))
    pin_seq = lambda t: k.state.last_seq(t, "pinned")
    pinned = sorted([p for p in posts if p[1].get("pinned")], key=lambda p: -pin_seq(p[0]))
    rest = sorted([p for p in posts if not p[1].get("pinned")], key=lambda p: -k.state.history[(p[0], "kind")][0][0])
    lines = [f"{k.name(k.place)}: the feed, {len(posts)} post" + ("" if len(posts) == 1 else "s")]
    for t, a in pinned + rest:
        k.mark(actor, t, a)
        lines.append("  " + _post_line(k, actor.person, t, a))
    if not posts:
        lines.append("  nothing yet: post <words> shares something")
    return {"text": "\n".join(lines), "rows": [_post_row(k, t, a) for t, a in pinned + rest]}


def help_(k, actor, st, entry, tx, group, saw=None):
    if st.words:
        w = st.words.split()[0].lower()
        e = k.find_entry(w, group)
        if e is None:
            if w in FLOOR_HELP:
                return {"text": f"{FLOOR_HELP[w]}\n(this word's entry is missing; the kernel answers from its own floor)"}
            raise Refused(f"nothing answers to '{w}' here; help lists the words you may use")
        a = k.entry(e)
        facts = [f"{a['word']} ({e}), a {a.get('word_kind')} word", f"takes: {a.get('takes') or 'nothing'}",
                 f"who may: {a.get('may')}"]
        for key in ("once", "sealed", "undo"):
            if a.get(key):
                facts.append(f"{key}: {a[key]}")
        facts.append(f"from: {a.get('from')}" + (f" ({a['bound']})" if a.get("bound") and a.get("bound") != a["word"] else ""))
        return {"text": a.get("help", "") + "\n" + " · ".join(facts), "rows": [dict(a)]}
    mine, others = [], []
    for e in sorted(k.entries(), key=lambda e: k.state.get(e, "word")):
        a = k.entry(e)
        line = f"  {a['word']} ({a.get('word_kind')}): {a.get('help', '').splitlines()[0]}"
        (mine if k.may(actor, a, None, group) else others).append((line, a))
    text = ["words you may use here:"] + [l for l, _ in mine]
    if others:
        text.append("not yours here: " + ", ".join(f"{a['word']} ({a.get('may')})" for _, a in others))
    return {"text": "\n".join(text), "rows": [{"word": a["word"], "kind": a.get("word_kind"), "yours": True} for _, a in mine]
            + [{"word": a["word"], "kind": a.get("word_kind"), "yours": False} for _, a in others]}


def post(k, actor, st, entry, tx, group, saw=None):
    text = st.words.strip()
    if not text:
        raise Refused("post needs words: post <words> [in=<group>]")
    m = re.match(r"at most (\d+) per day per person", entry.get("once") or "")
    if m:
        n = int(m.group(1))
        undone = k.undone()
        today = [r for r in k.log.records if r.get("entry") == entry["id"] and r["seq"] not in undone
                 and actor.person in (r.get("by"), r.get("for")) and r["at"][:10] == _today()]
        if len(today) >= n:
            raise Refused(f"you have posted {n} times today, the most the feed takes from one person in a day; "
                          f"the feed is a slower lane, and talk in a group has no limit")
    p = tx.mint()
    tx.set(p, "kind", "post")
    tx.set(p, "text", text)
    tx.set(p, "made_by", actor.id)
    if actor.id != actor.person:
        tx.set(p, "for", actor.person)
    tx.set(p, f"in:{group}", len(k.log.records) + 1)
    if group != k.place:
        tx.set(p, "sees", f"group:{group}")
    where = "" if group == k.place else f" in {k.name(group)} (seen by its members)"
    return {"text": f"ok post {p} [r?]{where}"}


def like(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, "kind") != "post":
        raise Refused(f"{t} is not a post; only posts take likes")
    seal = k.seal(actor.person, entry["id"], t)          # by the entry's id, so renaming `like` changes no seal
    if tx.get(t, f"like:{seal}"):
        raise Refused(f"you already like {t}; once each. undo takes yours back")
    tx.set(t, f"like:{seal}", True)
    n = sum(1 for a in k.state.things[t] if a.startswith("like:")) + 1
    return {"text": f"ok like {t} [r?] · {n} like{'' if n == 1 else 's'}; who liked it is sealed"}


def pin(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, "kind") != "post":
        raise Refused(f"{t} is not a post; only posts are pinned")
    k.fence(actor, t, ["pinned"], saw)
    if tx.get(t, "pinned"):
        return {"text": f"{t} is already pinned (by {k.name(tx.get(t, 'pinned'))}); nothing changed"}
    tx.set(t, "pinned", actor.person)
    return {"text": f"ok pin {t} [r?] · it stays at the top of the feed"}


def _whose(k, rec):
    if rec.get("by") == "sealed":
        return "someone's"
    return f"{k.name(rec.get('for') or rec.get('by'))}'s"


def _own(k, actor, rec):
    """Whether a record is this actor's own act: by them, by their agent, or sealed with their seal."""
    p = actor.person
    if rec.get("by") in (actor.id, p) or rec.get("for") == p:
        return True
    if rec.get("by") == "sealed":
        target = rec["parts"][0].get("target") if rec.get("parts") else None
        return rec.get("seal") == k.seal(p, rec.get("entry"), target)
    return False


def _may_undo(k, actor, rec):
    p = actor.person
    if _own(k, actor, rec):
        return True
    if k.is_steward(p):
        return True
    touched = {f[0] for part in rec.get("parts", []) for f in part["facts"]}
    return any(k.is_leader(p, g) for t in touched for g in k.groups_of(t))


def undo(k, actor, st, entry, tx, group, saw=None):
    undone = k.undone()
    if st.target:
        seq = int(st.target[1:])
        if not 0 < seq <= len(k.log.records):
            raise Refused(f"no act r{seq} in this world's log")
        rec = k.log.records[seq - 1]
    else:
        rec = next((r for r in reversed(k.log.records) if r.get("entry") and not r.get("undoes")
                    and r["seq"] not in undone and _own(k, actor, r)), None)
        if rec is None:
            raise Refused("you have nothing to undo")
    seq = rec["seq"]
    if not rec.get("entry"):
        raise Refused(f"r{seq} is not an act of a word ({rec.get('words')}); it cannot be undone")
    if rec.get("undoes"):
        raise Refused(f"r{seq} is itself an undo; there is no redo")
    if rec.get("external"):
        raise Refused(f"r{seq} touched the outside world ({rec.get('words')}); undo cannot take that back")
    if seq in undone:
        raise Refused(f"r{seq} is already undone")
    if k.state.get(rec["entry"], "undo") in ("no", "external"):
        raise Refused(f"r{seq} was {k.state.get(rec['entry'], 'word')}, which cannot be undone")
    if not _may_undo(k, actor, rec):
        raise Refused(f"r{seq} is {_whose(k, rec)}; you may undo your own acts, leaders the acts in their groups, "
                      f"stewards any")
    facts = [f for part in rec["parts"] for f in part["facts"]]
    made = {f[0] for f in facts if f[1] == "kind" and f[2] == "0"}
    for f in facts:
        t, a = f[0], f[1]
        v = f[3] if len(f) > 3 else None
        now = k.state.things.get(t, {}).get(a)
        if (now is None) != (v is None) or (now is not None and k.state.last_seq(t, a) != seq):
            raise Refused(f"r{seq} cannot be undone: {t} {a.split(':')[0]} changed since (r{k.state.last_seq(t, a)})")
    for t in made:
        later = [s for (tt, _), hist in k.state.history.items() if tt == t for s, _ in hist if s > seq]
        if later:
            raise Refused(f"r{seq} cannot be undone: {t} has changed since (r{max(later)}); undo that first")
    for f in reversed(facts):
        tx.set(f[0], f[1], k.state.before(f[0], f[1], seq))
    tx.extra["undoes"] = seq
    if rec.get("by") == "sealed":
        tx.extra["sealed_as"] = rec.get("seal")
    return {"text": f"ok undo r{seq} [r?] · put back {len(facts)} fact{'' if len(facts) == 1 else 's'}"}


def off(k, actor, st, entry, tx, group, saw=None):
    m = _module_of(k, st)
    if not k.state.get(m, "on"):
        return {"text": f"{k.name(m)} is already off"}
    tx.set(m, "on", False)
    n = 0
    for g in k.things("grant"):
        if k.state.get(g, "to") == m and not k.state.get(g, "revoked"):
            tx.set(g, "revoked", True)
            n += 1
    return {"text": f"ok off {k.state.get(m, 'name')} [r?] · {n} grant{'' if n == 1 else 's'} taken back, its process "
                    f"stopped; undo turns it on again"}


def status(k, actor, st, entry, tx, group, saw=None):
    m = _module_of(k, st)
    name = k.state.get(m, "name")
    if not k.modules or not k.modules.running(m):
        return {"text": f"{name} is not running ({'on' if k.state.get(m, 'on') else 'off'})"}
    said = k.modules.status(m)
    return {"text": f"{name}: {said}" if said else f"{name} did not say what it is doing within 2 s"}


def _writable(k, kv):
    for key in kv:
        if key in RESERVED or key.startswith(RESERVED_PREFIX) or not re.match(r"^[a-z_][a-z0-9_.-]*$", key):
            raise Refused(f"{key} is not a fact a line may write; the kernel keeps it")


def make(k, actor, st, entry, tx, group, saw=None):
    kv = dict(st.kv)
    kind = kv.pop("kind", "")
    kv.pop("in", None)
    if not re.match(r"^[a-z][a-z0-9_-]{0,31}$", kind or ""):
        raise Refused("make needs kind=<a plain word>: make kind=button name=Feed")
    if kind in RESERVED_KINDS:
        raise Refused(f"a {kind} is made by the kernel, not by make")
    _writable(k, kv)
    t = tx.mint()
    tx.set(t, "kind", kind)
    for key, v in kv.items():
        if v != "":
            tx.set(t, key, v)
    if st.words and "text" not in kv:
        tx.set(t, "text", st.words)
    tx.set(t, "made_by", actor.id)
    if actor.id != actor.person:
        tx.set(t, "for", actor.person)
    tx.set(t, f"in:{group}", len(k.log.records) + 1)
    if group != k.place:
        tx.set(t, "sees", f"group:{group}")
    return {"text": f"ok make {t} [r?] · a {kind}" + (f" in {k.name(group)}" if group != k.place else "")}


def set_(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, "kind") in RESERVED_KINDS:
        raise Refused(f"{t} is a {k.state.get(t, 'kind')}; set changes only things made with make")
    if not st.kv:
        raise Refused("set needs k=v: set <thing> label=Feed")
    _writable(k, st.kv)
    k.fence(actor, t, list(st.kv), saw)
    for key, v in st.kv.items():
        if v != "":
            tx.set(t, key, v)
        else:
            tx.set(t, key)                      # k= with nothing after it: the fact goes
    return {"text": f"ok set {t} [r?] · " + ", ".join(f"{a}={v}" if v else f"{a} taken away" for a, v in st.kv.items())}


def forget(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, "kind") in RESERVED_KINDS:
        raise Refused(f"{t} is a {k.state.get(t, 'kind')}, which forget does not take")
    tx.set(t, "forgotten", actor.person)
    return {"text": f"ok forget {t} [r?] · out of every view; undo brings it back"}


def holds(k, actor, st, entry, tx, group, saw=None):
    rows = [dict(h, by=k.name(h["by"])) for h in k.leases.values()]
    text = "\n".join(f"  {r['by']} holds {r['word']} ({r['lease']}) since {r['since']}" for r in rows)
    return {"text": ("holds:\n" + text) if rows else "nothing is held", "rows": rows}


KERNEL = {"look": look, "help": help_, "post": post, "like": like, "pin": pin, "undo": undo, "off": off,
          "status": status, "make": make, "set": set_, "forget": forget, "holds": holds}
