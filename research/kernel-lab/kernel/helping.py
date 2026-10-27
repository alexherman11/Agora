"""Help that teaches (epic: a terminal that teaches itself, Alex 26 Oct 2026).

`help` alone shows a short first screen: how a line works and the words most worth knowing, not every word.
`help <anything>` helps with that thing: a word (help window.open), a topic (help windows), a module (help theme),
a kind of thing (help taskboard-task), one thing (help dk74), or, failing those, the words whose names or help
mention it. It never ends at "nothing answers".

The pages are world data. A topic is an ordinary thing, `make kind=topic name=windows aliases=window
words="window.* wm.*" text="…"`, so fixing a page is `set <topic> text=…` from Lines, and fixing a word's help is
`word-set <word> help=…`. Each answer ends with the line that fixes it, for whoever may.
`help all` is the old full listing (one line per word, each word once).
"""
import difflib
import fnmatch
import re

START = ("Lines: type a line, the world answers. A line is a word, then what it acts on, then settings:\n"
         "  window.open feed to=left      word, then a thing, then key=value\n"
         "  set dk74 at=40,40             a thing is named by its id (dk74); ids show in every answer\n"
         "  post \"hello there\"            quote text that has spaces\n"
         "Every act gets a receipt [r812]; undo takes back your latest act (undo r812 takes back that one).")
USEFUL = ("look", "help", "rows", "window.list", "window.open", "make", "set", "forget", "undo", "history", "post",
          "theme.use", "task-add", "verb", "rule")


# ---------------------------------------------------------------------------------------------------- small pieces
def _variants(w):
    w = w.casefold().strip()
    out = [w]
    if w.endswith("ies"):
        out.append(w[:-3] + "y")
    if w.endswith("es"):
        out.append(w[:-2])
    if w.endswith("s"):
        out.append(w[:-1])
    return out


def _split_help(word, text):
    """'window.open <lens> [to=..]: open a window. More…' -> ('window.open <lens> [to=..]', 'open a window')."""
    first = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    usage, desc = "", first
    cut, quoted = None, False
    for i, ch in enumerate(first[:160]):
        if ch == '"':
            quoted = not quoted
        elif ch == ":" and not quoted and first[i + 1:i + 2] in (" ", ""):
            cut = i
            break
    if cut is not None and (first[:cut].split() or [""])[0].casefold() in (word.casefold(),
                                                                         word.replace("-", ".").casefold()):
        usage, desc = first[:cut], first[cut + 1:].strip()
    desc = re.split(r"(?<!e\.g\.)(?<!i\.e\.)(?<=[.!?])\s", desc, maxsplit=1)[0].rstrip(".")
    if len(desc) > 72:
        desc = desc[:70].rsplit(" ", 1)[0] + "…"
    return usage, desc


def _dropped(k):
    """Module words whose running module no longer offers them (kernel.dropped), as {word: entry}."""
    return {k.state.get(e, "word"): e for e in k.entries() if hasattr(k, "dropped") and k.dropped(e)}


def _visible_entries(k, actor, group):
    """Each word once: the entry nearest the line's group, if the reader may see it. Words a running module no
    longer offers are left out (help check names them)."""
    from .dictionary import localized
    out = {}
    for e in k.entries():
        if k.shown(actor.person, e) is None or (hasattr(k, "dropped") and k.dropped(e)):
            continue
        a = localized(k, actor.person, k.entry(e))
        w = a.get("word")
        if not w or w in out:
            continue
        try:
            nearest = k.find_entry(w, group)
        except Exception:
            nearest = e
        if nearest not in (None, e):
            a = localized(k, actor.person, k.entry(nearest))
        out[w] = a
    return out


def _line(k, actor, a, group, width=18):
    _, desc = _split_help(a["word"], a.get("help", ""))
    mark = "" if k.may(actor, a, None, group) else f"  ({a.get('may')} only)"
    return f"  {a['word']:<{width}} {desc}{mark}"


def _listing(k, actor, entries, group):
    width = min(22, max([len(a["word"]) for a in entries] + [8]) + 1)
    return [_line(k, actor, a, group, width) for a in entries]


def _matching(pool, patterns):
    """In the order the patterns are written (a topic lists its most useful words first), each word once."""
    out = {}
    for p in [p.casefold() for p in str(patterns or "").split() if p]:
        for w, a in sorted(pool.items()):
            if w not in out and fnmatch.fnmatchcase(w.casefold(), p):
                out[w] = a
    return list(out.values())


def _can_edit_thing(k, actor, t):
    a = k.state.things.get(t, {})
    return a.get("made_by") in (actor.id, actor.person) or k.is_steward(actor.person) or any(
        k.is_leader(actor.person, g) for g in k.groups_of(t))


def _can_edit_entry(k, actor, a):
    scope = a.get("lives")
    return k.is_steward(actor.person) or bool(scope and k.is_leader(actor.person, scope))


def _ask_hint(k, t):
    try:
        return f"unclear? ask {t} text=\"what confused you\"" if k.find_entry("ask") else ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------------------------------- the pages
def topics(k, actor):
    out = []
    for t in k.things("topic"):
        a = k.shown(actor.person, t)
        if a is not None and a.get("name"):
            out.append((t, a))
    return sorted(out, key=lambda ta: (str(ta[1].get("order", "50")).zfill(3), ta[1].get("name")))


def topic_named(k, actor, w):
    for v in _variants(w):
        for t, a in topics(k, actor):
            names = {str(a.get("name", "")).casefold(), *str(a.get("aliases", "")).casefold().split()}
            if v in names:
                return t, a
    return None


def _topic_page(k, actor, group, t, a, pool):
    k.mark(actor, t, a)
    text = str(a.get("text", "")).replace("\\n", "\n")       # a topic's text may say \n for a new line
    lines = [f"{a.get('title') or a.get('name')}: {text}" if text else str(a.get('title') or a.get('name'))]
    pats = str(a.get("words") or "").split()
    named = _matching(pool, " ".join(p for p in pats if "*" not in p))
    more = [x for x in _matching(pool, " ".join(p for p in pats if "*" in p)) if x not in named]
    found = named + more
    lines += _listing(k, actor, named, group)
    if more:
        lines.append("  more: " + ", ".join(x["word"] for x in more))
    tail = ["help <word> says more"]
    if _can_edit_thing(k, actor, t):
        tail.append(f"fix this page: set {t} text=\"…\" words=\"…\"")
    elif _ask_hint(k, t):
        tail.append(_ask_hint(k, t))
    lines.append(" · ".join(tail))
    return {"text": "\n".join(lines), "rows": [dict(a, id=t, rev=k.state.rev.get(t, 0))] +
            [{"word": x["word"], "kind": x.get("word_kind")} for x in found]}


def _module_page(k, actor, group, m, pool):
    name = k.state.get(m, "name")
    found = _matching(pool, f"{name}.*")
    if not found:
        return None
    about = k.state.get(m, "about") or f"the {name} module's words"
    on = "" if k.state.get(m, "on") else f" (off: nothing answers until a steward turns {name} on)"
    lines = [f"{name}: {about}{on}"] + _listing(k, actor, found, group)
    tail = ["help <word> says more"]
    if k.is_steward(actor.person):
        tail.append(f"make this a page: make kind=topic name={name} words=\"{name}.*\" text=\"…\"")
    lines.append(" · ".join(tail))
    return {"text": "\n".join(lines), "rows": [{"word": x["word"], "kind": x.get("word_kind")} for x in found]}


def _mentions(pool, term):
    """Entries whose name or help mentions term, best first."""
    term = term.casefold()
    rx = re.compile(r"(?<![a-z0-9])" + re.escape(term) + r"(s|es)?(?![a-z0-9])")
    scored = []
    for w, a in pool.items():
        name = w.casefold()
        score = (6 if name == term else 4 if term in re.split(r"[.\-]", name) else 2 if term in name else 0)
        score += min(3, len(rx.findall(str(a.get("help", "")).casefold())))
        score += 1 if rx.search(str(a.get("takes", "")).casefold()) else 0
        if score:
            scored.append((-score, w, a))
    return [a for _, _, a in sorted(scored)]


def _kind_page(k, actor, group, kind, pool):
    seen = [t for t in k.things(kind) if k.shown(actor.person, t) is not None]
    if not seen:
        return None
    found = _mentions(pool, kind)[:10]
    lines = [f"{kind}: {len(seen)} you can see. rows {kind} lists them with ids; look <id> shows one."]
    if found:
        lines.append(f"words that mention {kind}:")
        lines += _listing(k, actor, found, group)
    lines.append("any thing: look <id> · set <id> key=value · forget <id> · history <id>")
    return {"text": "\n".join(lines), "rows": [{"word": x["word"], "kind": x.get("word_kind")} for x in found]}


def _entry_page(k, actor, e):
    from .dictionary import localized
    a = localized(k, actor.person, k.entry(e))
    k.mark(actor, e, k.shown(actor.person, e))
    facts = [f"{a['word']} ({e}), a {a.get('word_kind')} word", f"takes: {a.get('takes') or 'nothing'}",
             f"who may: {a.get('may')}"]
    if a.get("aliases"):
        facts.insert(1, "also said: " + ", ".join(str(a["aliases"]).split()))
    for key in ("once", "sealed", "undo"):
        if a.get(key):
            facts.append(f"{key}: {a[key]}")
    facts.append(f"from: {a.get('from')}" + (f" ({a['bound']})" if a.get("bound") and a.get("bound") != a["word"] else ""))
    if a.get("from", "").startswith("module:"):
        mid = k.module_named(a["from"][7:])
        if not mid or not k.state.get(mid, "on") or not k.modules or not k.modules.running(mid):
            facts.append("unbound: this community must grant and run the module")
    text = a.get("help", "") + "\n" + " · ".join(facts)
    if _can_edit_entry(k, actor, a):
        text += f"\nfix this help: word-set {a['word']} help=\"…\""
    elif _ask_hint(k, e):
        text += "\n" + _ask_hint(k, e)
    return {"text": text, "rows": [dict(a)]}


def _search_page(k, actor, group, w, pool):
    found = _mentions(pool, w)[:8]
    for v in _variants(w)[1:]:
        if not found:
            found = _mentions(pool, v)[:8]
    if not found:
        return None
    lines = [f"no word called {w}; these mention it:"] + _listing(k, actor, found, group)
    lines.append("help <word> says more · help shows how lines work")
    return {"text": "\n".join(lines), "rows": [{"word": x["word"], "kind": x.get("word_kind")} for x in found]}


def suggest(k, actor, w, group, pool=None):
    """What to type instead of an unknown word: a help page that exists, or the nearest names."""
    pool = pool if pool is not None else _visible_entries(k, actor, group)
    if topic_named(k, actor, w) or any(k.module_named(v) for v in _variants(w)) or any(
            k.things(v) for v in _variants(w)):
        return f"help {w} shows the words for it"
    names = list(pool) + [x for a in pool.values() for x in str(a.get("aliases", "")).split()]
    near = difflib.get_close_matches(w.casefold(), names, n=3, cutoff=0.6)
    tails = [n for n in names if n.split(".")[-1] == w.casefold()]
    near = list(dict.fromkeys(tails + near))[:3]
    if near:
        return "did you mean " + " or ".join(near) + "?"
    return f"help {w} searches the words; help shows how lines work"


def check_page(k, actor, group, pool):
    """help check: help that would mislead, with the line that fixes each. A reading; nothing changes."""
    names = set(pool) | {x for a in pool.values() for x in str(a.get("aliases", "")).split()}
    problems, long = [], []
    for w, a in sorted(pool.items()):
        text = str(a.get("help", "")).strip()
        first = text.splitlines()[0] if text else ""
        said = []
        head = (first.split() or [""])[0].rstrip(":")
        if head and head != w and re.fullmatch(r"[a-z][a-z0-9]*[.-][a-z0-9.-]+", head) and head not in names:
            said.append(f"its example says {head}, but the word is {w}")
        elif not first.casefold().startswith(w.casefold()):
            said.append("no usage line: start with the word and what it takes")
        ghosts = sorted({m for m in re.findall(r"(?<![\w./<-])([a-z]+[.-][a-z][a-z0-9-]*)(?= |$)", text)
                         if m not in names and m.split(".")[0] in {n.split(".")[0] for n in names if "." in n}
                         and m != head})
        if ghosts:
            said.append("mentions " + ", ".join(ghosts[:3]) + ", which nothing answers to")
        if len(first) > 220:
            long.append(w)
        if said:
            problems.append((w, said))
    lines = [f"help check: {len(problems)} of {len(pool)} words have help that may mislead"]
    for w, said in problems[:30]:
        lines.append(f"  {w}: " + "; ".join(said))
    if len(problems) > 30:
        lines.append(f"  … and {len(problems) - 30} more (rows hold them all)")
    if long:
        lines.append(f"long first lines (over 220 characters), worth trimming: " + ", ".join(long))
    gone = sorted(_dropped(k))
    if gone:
        lines.append("no longer offered by their running module (left out of help): " + ", ".join(gone)
                     + f". Retire one: word-set {gone[0]} status=hidden")
    lines.append("fix one: help <word>, then word-set <word> help=\"<word> <what it takes>: what it does.\"")
    return {"text": "\n".join(lines), "rows": [{"word": w, "problems": said} for w, said in problems]}


def _who(k, actor):
    me = k.name(actor.id) if actor.id in k.state.things else k.name(actor.person)
    if actor.id != actor.person:
        return f"You are {me}, acting with {k.name(actor.person)}'s rights, in {k.name(k.place)}."
    return f"You are {me}, in {k.name(k.place)}."


def start_page(k, actor, group, pool):
    hit = topic_named(k, actor, "start")
    if hit:
        page = _topic_page(k, actor, group, hit[0], hit[1], pool)
        body, _, tail = page["text"].rpartition("\n")
        page["text"] = "\n".join([_who(k, actor), body, "help <anything> helps with that: help windows · help theme · "
                                  "help window.open · help all", tail])
    else:
        found = [pool[w] for w in USEFUL if w in pool]
        lines = [_who(k, actor), START, "", "words worth knowing:"] + _listing(k, actor, found, group)
        lines.append("help <anything> helps with that: help windows · help theme · help window.open · help all")
        page = {"text": "\n".join(lines), "rows": []}
    names = [n for _, a in topics(k, actor) if (n := a.get("name")) and n != "start"]
    mods = [k.state.get(m, "name") for m in k.things("module") if k.shown(actor.person, m) is not None
            and _matching(pool, f"{k.state.get(m, 'name')}.*")]
    more = list(dict.fromkeys(names + [m for m in mods if not topic_named(k, actor, m)]))
    if more:
        page["text"] += "\ntopics: " + " · ".join(more)
    # rows stay the whole dictionary, as the Help window reads them
    page["rows"] = [{"word": w, "kind": a.get("word_kind"), "yours": bool(k.may(actor, a, None, group))}
                    for w, a in sorted(pool.items())]
    return page


def all_page(k, actor, group, pool):
    mine = [a for _, a in sorted(pool.items()) if k.may(actor, a, None, group)]
    others = [a for _, a in sorted(pool.items()) if not k.may(actor, a, None, group)]
    text = [f"all {len(pool)} words here, each once:"] + _listing(k, actor, mine, group)
    if others:
        text.append("not yours here: " + ", ".join(f"{a['word']} ({a.get('may')})" for a in others))
    return {"text": "\n".join(text), "rows": [{"word": a["word"], "kind": a.get("word_kind"), "yours": True} for a in mine]
            + [{"word": a["word"], "kind": a.get("word_kind"), "yours": False} for a in others]}


def answer(k, actor, words, group):
    """help [<anything>] -> {text, rows}."""
    from . import lines as L
    pool = _visible_entries(k, actor, group)
    w = (words or "").split()[0].casefold() if (words or "").strip() else ""
    if not w:
        return start_page(k, actor, group, pool)
    if w in ("all", "everything") or (w == "words" and not topic_named(k, actor, w)):
        return all_page(k, actor, group, pool)
    if w == "check":
        return check_page(k, actor, group, pool)
    try:
        e = k.find_entry(w, group)
    except Exception:
        e = None
    if e is not None and k.shown(actor.person, e) is not None:
        return _entry_page(k, actor, e)
    hit = topic_named(k, actor, w)
    if hit:
        return _topic_page(k, actor, group, hit[0], hit[1], pool)
    for v in _variants(w):
        m = k.module_named(v)
        if m and k.state.get(m, "kind") == "module":
            page = _module_page(k, actor, group, m, pool)
            if page:
                return page
    for v in _variants(w):
        page = _kind_page(k, actor, group, v, pool)
        if page:
            return page
    if L.ID.fullmatch(w):
        a = k.shown(actor.person, w)
        if a is not None:
            kind = a.get("kind")
            k.mark(actor, w, a)
            page = (topic_named(k, actor, kind) and _topic_page(k, actor, group, *topic_named(k, actor, kind), pool)) \
                or _kind_page(k, actor, group, kind, pool) or {"text": "", "rows": []}
            page["text"] = f"{w} is a{'n' if str(kind)[:1] in 'aeiou' else ''} {kind}: {k.name(w)}. look {w} shows its facts.\n" \
                + page["text"]
            return page
    return _search_page(k, actor, group, w, pool)
