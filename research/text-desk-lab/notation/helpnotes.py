"""helpnotes (a1595): help lives in the world, as notes; the code keeps a floor, and a check keeps the notes true.

Where help lives: a surface with prop role=help (the Help binder, in the Handbook), and every note inside it, at any
depth. A note's title is its word, with other words after | (examine|x|ex); its text is what help prints, verbatim.
`help` alone reads the note titled manual. A note tagged topic is listed among the topics when help doesn't know a word.
A note whose word is no command, no built-in verb and no topic (a noun: ids, chat ...) yields to a verb made in the
world with that word, as the nouns always did. Changing help is changing a note: replace, no commit, no restart.

The floor: a command, a built-in verb or the manual whose note is missing or empty still answers, from the code
(DeskKnife.USAGE beside the dispatcher; the verb registry's doc, args and example), and says the note is missing.

check(desk) -> [problem lines], each naming the note (id, title, who made it, who last changed it) and the code
(file:line). health.py prints them; an edit to a help note prints its own in the receipt, to whoever made the edit.
It checks: every command, built-in verb and the manual has a note; each argument the code declares (k=, :N, an option
word) is named in its note; no `do <verb> ... k=` or `<command> ... k=` a note shows uses a key the code doesn't know,
nor does a verb note's args: line; every `help <word>` a note names answers; the lens note names every lens word and
the selections note every selection term (the a1308 words check, pointed at the notes).
"""
import inspect
import re

ROLE = "help"
MANUAL = "manual"
TOPIC = "topic"
KEY = re.compile(r"(?<![\w<$.:-])([a-z_]+)=")
DEPTH = re.compile(r"(?<![\w])(:\d)(?![\w])")
HELP_WORD = re.compile(r"(?:^|[\s(;:·`'\"])help ([a-z][a-z-]+)(?=$|[\s).;,:`'\"])")
PROSE = {"is", "or", "with", "for", "lists", "may", "the", "a", "an", "to", "you", "take", "shape", "themselves", "users",
         "topics", "explains", "knows", "answers", "says", "can", "will", "and", "it", "them", "us", "out", "each"}
FALLBACK = "no command, verb or topic"


def _num(i):
    m = re.search(r"\d+", str(i))
    return int(m.group()) if m else 0


def binder(w):
    """-> the Help binder's id (the first surface with prop role=help), or None."""
    hits = [n["id"] for n in w.nodes.values() if n["type"] == "surface" and (n.get("props") or {}).get("role") == ROLE]
    return min(hits, key=_num) if hits else None


def words_of(title):
    return [x.strip().lower() for x in str(title or "").split("|") if x.strip()]


def entries(w):
    """-> [(words, subject, appearance id)] for every note in the Help binder, in the binder's order, at any depth."""
    fid = binder(w)
    out, stack = [], [fid] if fid else []
    while stack:
        for k in w.children(stack.pop(0)):
            if k["type"] == "surface":
                stack.append(k["id"])
            elif k.get("subject") in w.subjects:
                s = w.subjects[k["subject"]]
                out.append((words_of(s["title"]), s, k["id"]))
    return out


def lookup(w):
    """-> {word: (subject, appearance id)}; the first note to name a word has it."""
    out = {}
    for words, s, aid in entries(w):
        for x in words:
            out.setdefault(x, (s, aid))
    return out


def text(w, word):
    """-> the note's text for a word, or None when there is no note or it says nothing."""
    hit = lookup(w).get(word.lower())
    if not hit or not str(hit[0].get("text") or "").strip():
        return None
    return hit[0]["text"]


def topics(w):
    """The first word of each note tagged topic: what help lists as topics."""
    return [words[0] for words, s, _ in entries(w) if words and TOPIC in (s.get("tags") or [])]


def missing(word):
    return (f"  (help {word}: no note says this yet, so this answer is the floor, from the code. Help lives in notes "
            f"in the Help binder, a surface with prop role=help; a note titled {word} there is what help {word} prints)")


# ---- what the code says each word takes ----------------------------------------------------------------------------

def commands():
    import house
    import verbs
    return set(verbs.DESK_WORDS) | set(house.COMMANDS) | {"rest"}


def usage_args(usage):
    """The arguments a usage line names: k= keys, :N depths, and option words (bare lower-case words, not <placeholders>
    and not the command itself). -> (keys, depths, options)."""
    head, _, rest = usage.partition(" ")
    keys = set(KEY.findall(rest))
    depths = set(DEPTH.findall(rest))
    bare = re.sub(r"<[^>]*>", " ", rest)
    bare = re.sub(r"[a-z_]+=\S*", " ", bare)
    options = {t for t in re.split(r"[\s\[\]|/,.]+", bare) if re.fullmatch(r"[a-z][a-z-]+", t)}
    return keys, depths, options - {head}


def verb_spec(desk, name, known=False):
    """-> (keys, open, where) for a built-in verb: the keys its args declare (known=True: and the ones the knife desk
    adds, DeskKnife.KNIFE_ARGS, which its topics explain), whether it takes any key (a prop), and the code's file:line.
    None for a word that is not one."""
    import knife
    import moo
    if name in knife.PAIR_DOC:
        args = knife.PAIR_DOC[name][0]
        return set(KEY.findall(args)), False, f"knife.py PAIR_DOC[{name!r}]"
    v = moo.REGISTRY.get(name)
    if not v:
        return None
    keys = set(KEY.findall(v.args or "")) | (set(desk.KNIFE_ARGS.get(name, ())) if known else set())
    open_ = "any other key" in (v.args or "") or "k=v" in (v.args or "")
    try:
        f = inspect.getsourcefile(v.run).replace("\\", "/").rsplit("/", 1)[-1]
        where = f"{f}:{inspect.getsourcelines(v.run)[1]}"      # a decorated function's first line is its @verb
    except (OSError, TypeError):
        where = "moo.REGISTRY"
    return keys, open_, where


def usage_where(desk, cmd):
    return f"desk_knife.py USAGE[{cmd!r}]"


def floor(desk, word):
    """-> the floor's answer for a command, a built-in verb or the manual: what the code alone can say."""
    import knife
    import moo
    if word == MANUAL:
        return "commands:\n" + "\n".join("  " + u for _, u in sorted(desk.USAGE.items())) + "\n" + missing(MANUAL)
    cmd = desk.COMMAND_ALIAS.get(word, word)
    if cmd in desk.USAGE:
        return desk.USAGE[cmd] + "\n" + missing(word)
    if word in knife.PAIR_DOC:
        args, doc = knife.PAIR_DOC[word]
        return f"{word}  (pair verb; level 2)\n  {doc}\n  args: {args}\n" + missing(word)
    v = moo.REGISTRY.get(word)
    if v:
        return (f"{v.name}  (on: {', '.join(v.kinds)}; level {v.level})\n  {v.doc}\n"
                + (f"  args: {v.args}\n" if v.args else "") + f"  e.g. {v.example}\n" + missing(word))
    return None


# ---- the check -------------------------------------------------------------------------------------------------------

def _targetish():
    import knife
    terms = "|".join(re.escape(t) for t in knife.TERMS)
    return re.compile(rf'^(?:[<$?"]|[afsecl]\d+$|-?(?:{terms})|-?(?:due|age)[<>]|hidden\b)')


def _segments(text_, word):
    """Each place a note shows `word` used as a command (`do move a12 into=f02`, `table kind:x cols=a`): -> [keys].
    After the word, a target may come first (after do <verb>, any word, as titles are targets; after a command, only
    an id, a <placeholder>, a $blank, a quoted title or a selection); then k=v words, <placeholders>, [options] and ids
    are read until the first word of prose."""
    from desk_knife import is_target_word
    out = []
    lenient = word.startswith("do ")
    TARGETISH = _targetish()
    for m in re.finditer(rf"(?<![\w$<.:/|=-]){re.escape(word)} ", text_):
        toks = re.findall(r'[^\s"]*"(?:[^"\\]|\\.)*"\S*|\S+', text_[m.end():m.end() + 400])
        keys, first = [], True
        for t in toks:
            core = t.strip("[]")
            if "=" in core and not core.startswith(("?", "-", "$")) and re.match(r"^[a-z_]+=", core) and not is_target_word(core):
                keys.append(core.split("=", 1)[0])
                first = False
                continue
            if first and core and (TARGETISH.match(core) or (lenient and re.match(r"^[\w$]", core))):
                first = False
                continue
            first = False
            if core.startswith(("<", "$", ":", "#")) or re.fullmatch(r"[afsecl]\d+", core) or core in ("...", "|"):
                continue
            break
        if keys:
            out.append(keys)
    return out


def check(desk, only=None):
    """-> [problem lines]. only=<subject id>: the problems of that one note (an edit's receipt)."""
    import knife
    import scene
    w = desk.world
    fid = binder(w)
    if not fid:
        return ["no Help binder (a surface with prop role=help): every help answer is the floor"]
    found = entries(w)
    table = lookup(w)
    rec = desk._house_record([aid for _, _, aid in found])
    probs = []

    def ref(s, aid):
        r = rec.get(aid) or {}
        by = f"made by {r.get('made_by') or '?'}"
        if r.get("edited_by") and r.get("edited_by") != r.get("made_by"):
            by += f", last changed by {r['edited_by']}"
        return f"help note {aid} \"{s['title']}\" ({by})"

    def say(s, line):
        if only is None or s["id"] == only:
            probs.append(line)

    cmds = commands()
    verbs_ = desk._help_verbs()
    if only is None:
        for word in sorted(cmds | set(verbs_) | {MANUAL}):
            if word not in table:
                where = usage_where(desk, desk.COMMAND_ALIAS.get(word, word)) if word in cmds else \
                    "the manual" if word == MANUAL else (verb_spec(desk, word) or (0, 0, "?"))[2]
                probs.append(f"no help note for {word}: help {word} answers from the floor ({where})")
    seen = {}
    for words, s, aid in found:
        for x in words:
            if x in seen and seen[x][0]["id"] != s["id"]:
                say(s, f"{ref(s, aid)}: names {x}, which {ref(*seen[x])} already answers; help {x} reads that one")
            seen.setdefault(x, (s, aid))
    for words, s, aid in found:
        if only is not None and s["id"] != only:
            continue
        body = s.get("text") or ""
        if not body.strip():
            say(s, f"{ref(s, aid)}: says nothing, so help {words[0] if words else '?'} answers from the floor")
            continue
        for x in words:
            if table.get(x, (None,))[0] is not s:
                continue
            cmd = desk.COMMAND_ALIAS.get(x, x)
            if x in cmds and cmd in desk.USAGE:
                keys, depths, options = usage_args(desk.USAGE[cmd])
                for k in sorted(keys):
                    if not re.search(rf"(?<![\w-]){k}=", body):
                        say(s, f"{ref(s, aid)}: does not name {k}=, which {cmd} takes ({usage_where(desk, cmd)})")
                for d in sorted(depths | options):
                    if not re.search(rf"(?<![\w-]){re.escape(d)}(?![\w-])", body):
                        say(s, f"{ref(s, aid)}: does not name {d}, which {cmd} takes ({usage_where(desk, cmd)})")
            if x in verbs_:
                keys, _open, where = verb_spec(desk, x)
                for k in sorted(keys):
                    if not re.search(rf"(?<![\w-]){k}=", body):
                        say(s, f"{ref(s, aid)}: does not name {k}=, which {x} takes ({where})")
                known = verb_spec(desk, x, known=True)[0]
                for line in body.splitlines():
                    if line.strip().startswith("args:"):
                        for k in KEY.findall(line):
                            if k not in known:
                                say(s, f"{ref(s, aid)}: its args: line names {k}=, which {x} does not take ({where})")
        if "lens" in words:
            for word in scene.WORDS:
                if not re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", body):
                    say(s, f"{ref(s, aid)}: does not name the lens word {word} (scene.py WORDS)")
        for name, cols in (("views", desk.HOUSE_COLS), ("table", desk.HOUSE_COLS + desk.TABLE_COLS)):
            if name in words:      # a column is an argument too (cols=made_by): the code's columns, each named
                for col in cols:
                    if not re.search(rf"(?<![\w-]){col}(?![\w-])", body):
                        say(s, f"{ref(s, aid)}: does not name the column {col} (desk_knife.py HOUSE_COLS, TABLE_COLS)")
        if "selections" in words:
            for term in knife.TERMS:
                if term not in body:
                    say(s, f"{ref(s, aid)}: does not name the selection term {term} (knife.py TERMS)")
        # what the note shows being typed must be what the code would take
        for m in re.finditer(r"(?<![\w$<.:/|=-])do ([a-z]+) ", body):
            spec = verb_spec(desk, m.group(1), known=True)
            if not spec or spec[1]:
                continue
            for keys in _segments(body[m.start():], f"do {m.group(1)}")[:1]:
                for k in keys:
                    if k not in spec[0]:
                        say(s, f"{ref(s, aid)}: shows do {m.group(1)} ... {k}=, which {m.group(1)} does not take ({spec[2]})")
        for cmd, usage in desk.USAGE.items():
            if cmd == "do":
                continue
            known = usage_args(usage)[0]
            for keys in _segments(body, cmd):
                for k in keys:
                    if k not in known:
                        say(s, f"{ref(s, aid)}: shows {cmd} ... {k}=, which {cmd} does not take ({usage_where(desk, cmd)})")
        # a note titled with words help can't be asked (Where help lives) is about the binder, not an answer: its prose
        # says 'help prints' and 'help alone', so only answers are held to the words they name
        for word in dict.fromkeys(HELP_WORD.findall(body)) if all(" " not in x for x in words) else ():
            if word in PROSE or word in words:
                continue
            if word in table or word in cmds or word in verbs_:
                continue
            ans = desk.cmd_help(word)
            if FALLBACK in ans:
                say(s, f"{ref(s, aid)}: says help {word}, which help doesn't know")
    return list(dict.fromkeys(probs))


def receipt(desk, sid):
    """The ~ line an edit to a help note adds to its receipt: which help it is now, and its problems."""
    w = desk.world
    s = w.subjects.get(sid)
    if not s:
        return None
    words = words_of(s["title"])
    probs = check(desk, only=sid)
    head = (f"~ help note: help {words[0]} reads this now" if words and text(w, words[0]) is not None and
            lookup(w)[words[0]][0] is s else f"~ help note: help {words[0] if words else '?'} does not read this note")
    return head + ("" if not probs else f"; {len(probs)} problem(s):" + "".join(f"\n  ! {p}" for p in probs[:8]))


def in_binder(w, sid):
    fid = binder(w)
    return bool(fid) and any(w._is_inside(a, fid) for a in w.appearances_of(sid))
