"""dictionary (a13316): one entry for every word, as world notes. The format is research/community-app/DICTIONARY-ENTRY.md.

An entry is a note. Its title is the word and its aliases (examine|x|ex); its text is the help, up to the first
translation section (`## es`); its props say the rest: word= (do, see, hear or hold: the entry's kind, since kind is
the thing's own), takes=, may=, undo=, from= (kernel, verb, module:<name>) and bound= (the implementation's name).
Entries for kernel and module words live in the Dictionary, the Help binder (role=help, helpnotes.py), at any depth; a
note there without word= is help (a topic, a noun), not an entry. A verb note (tagged verb) is its own entry, where it
lives, with defaults for what it leaves out.

The code here only reads entries and says whether their implementation answers. Everything an entry says is world
data: renaming (retitle), aliasing (a word after |), rewriting help (replace), translating (a section) and who may (a
prop) are edits to a note. `alias` lets the desk answer an entry's words for the code's own word; the code's own word
always answers too. Who may is recorded and never checked here: that is the kernel's (Powers).

A binder with no word= on any note is plain help, as before a13316, and check() says nothing about entries there.
"""
import re

KINDS = ("do", "see", "hear", "hold")
UNDO = ("yes", "no", "external")       # the kernel's (a13310 SHAPE.md Appendix B); a see word says none
STATUS = ("live", "old", "hidden")
LANG = re.compile(r"^##\s+([a-z]{2,3}(?:-[A-Za-z]{2,4})?)\s*$")
RULE_WORDS = {"on", "when"}          # the words a rule note's line begins with (help rules): the kernel's hear words
WITNESSED = {"home-base": "host"}    # a module that publishes its words as witnessed rows, and the rows' name


def _props(s):
    return s.get("props") or {}


def _is_verb(s):
    return s.get("kind") == "note" and "verb" in (s.get("tags") or [])


def split(text):
    """-> (help, {lang: text}): the text up to the first `## <lang>` line, and each translation section after it."""
    help_, langs, cur = [], {}, None
    for line in str(text or "").splitlines():
        m = LANG.match(line.strip())
        if m:
            cur = m.group(1)
            langs[cur] = []
            continue
        (langs[cur] if cur else help_).append(line)
    return "\n".join(help_).rstrip(), {k: "\n".join(v).strip() for k, v in langs.items()}


def doc_of(text):
    """A verb note's # lines, without their marks: what it says of itself."""
    return "\n".join(l.lstrip("#").strip() for l in str(text or "").splitlines() if l.strip().startswith("#"))


def _verb_takes(text, doc=""):
    """What a verb note takes: the placeholders its first # line names after its word (`lend <tool> <name>: ...`),
    else its blanks ($1 $2 $*)."""
    import verbs
    first = next((l for l in doc.splitlines() if l.strip()), "")
    m = re.match(r"\S+\s+((?:[<\[][^:]*?))\s*:", first)
    if m:
        return m.group(1).strip()
    steps = " ".join(verbs._steps(text))
    nums = sorted({int(n) for n in re.findall(r"\$(\d)", steps)})
    out = [f"${n}" for n in range(1, (nums[-1] if nums else 0) + 1)]
    if "$*" in steps:
        out.append("$*")
    return " ".join(out)


class Entry:
    """One word's entry, read from its note. `aid` is where it appears (its first appearance for a verb note)."""

    def __init__(self, w, s, aid, verb=False):
        import helpnotes
        p = _props(s)
        self.s, self.aid, self.sid, self.verb = s, aid, s["id"], verb
        self.words = helpnotes.words_of(s["title"]) if not verb else __import__("verbs")._names(s["title"])
        self.word = self.words[0] if self.words else ""
        self.aliases = self.words[1:]
        self.kind = p.get("word") or ("do" if verb else "")
        self.help, self.langs = split(s.get("text"))
        if verb:      # a verb note's help is its # lines; a `## es` line starts a translation, also of # lines
            self.help, self.langs = doc_of(self.help), {k: doc_of(v) for k, v in self.langs.items()}
        self.takes = p.get("takes", _verb_takes(s.get("text") or "", self.help) if verb else "")
        carried = verb and __import__("verbs").where(w, s)[0] == "actor"
        self.may = p.get("may") or (f"{__import__('verbs').where(w, s)[1]} (who carries it)" if carried else "anyone")
        self.undo = p.get("undo") or ("yes" if verb and self.kind not in ("see", "hear") else "")
        self.frm = p.get("from") or ("verb" if verb else "")
        self.bound = p.get("bound") or (self.sid if verb else self.word)
        self.status = p.get("status") or "live"          # recorded; the old desk neither hides nor retires a word
        self.once, self.sealed = p.get("once") or "", p.get("sealed") or ""      # recorded only: the kernel's

    def module(self):
        return self.frm.split(":", 1)[1] if self.frm.startswith("module:") else None


def binder_entries(w):
    """-> [Entry] for each note in the Dictionary (the Help binder) whose word= is set, in the binder's order."""
    import helpnotes
    return [Entry(w, s, aid) for words, s, aid in helpnotes.entries(w) if _props(s).get("word")]


def verb_entries(w):
    import verbs
    return [Entry(w, s, w.appearances_of(s["id"])[0], verb=True) for s in verbs.all_verbs(w)]


def all_entries(desk):
    return binder_entries(desk.world) + verb_entries(desk.world)


def entry_of(desk, sid):
    """-> the Entry a subject is, or None: a binder note with word=, or a verb note."""
    w = desk.world
    s = w.subjects.get(sid)
    if not s:
        return None
    if _is_verb(s) and w.appearances_of(sid):
        return Entry(w, s, w.appearances_of(sid)[0], verb=True)
    import helpnotes
    if _props(s).get("word") and helpnotes.in_binder(w, sid):
        aid = next(a for a in w.appearances_of(sid))
        return Entry(w, s, aid)
    return None


def on(w):
    """Is there a dictionary here: does any note in the binder say word=?"""
    return bool(binder_entries(w))


# ---- does anything answer -------------------------------------------------------------------------------------------

def code_words(desk):
    """The words the desk's code answers to itself: its commands and their aliases, its built-in verbs and their
    synonyms, the promise verbs and the rule words."""
    import helpnotes
    import promises
    return (set(helpnotes.commands()) | set(desk.COMMAND_ALIAS) | set(desk._builtin_verbs())
            | set(promises.VERBS) | set(promises.HOUSE_VERBS) | RULE_WORDS)


def module_rows(desk, name, session=None):
    """-> the rows a module publishes now ([] when it publishes none), or None when the module is not running."""
    src = WITNESSED.get(name)
    if not src:
        return None
    import witnessed
    session = session or getattr(desk, "_session", "") or ""
    doc = witnessed.read(session, src) if session else None
    return None if doc is None else [r for r in doc.get("rows") or [] if isinstance(r, dict)]


def status(desk, e, session=None):
    """-> (bound?, words): whether something answers to the entry's bound= name now, and how, or why not."""
    w = desk.world
    if e.verb:
        return True, "a verb note, its own lines"
    if e.frm == "kernel":
        if e.bound in code_words(desk):
            return True, f"the kernel's {e.bound}"
        return False, f"nothing in the desk's code answers to {e.bound}"
    if e.frm == "verb":
        s = w.subjects.get(w.nodes.get(e.bound, {}).get("subject") or e.bound)
        if s and _is_verb(s):
            return True, f"the verb note {e.bound}"
        return False, f"{e.bound} is no verb note now"
    mod = e.module()
    if mod:
        rows = module_rows(desk, mod, session)
        if rows is None:
            return False, (f"the {mod} is not running, so nothing answers to {e.bound} now (it publishes its words as "
                           f"rows witnessed:{WITNESSED[mod]} while it runs)" if mod in WITNESSED
                           else f"no module named {mod} publishes words here")
        if any(str(r.get("name")) == e.bound for r in rows):
            return True, f"the {mod}'s {e.bound}"
        return False, f"the {mod} runs and publishes no {e.bound} (rows witnessed:{WITNESSED[mod]})"
    return False, "it says no from= (kernel, verb or module:<name>), so nothing is bound to it"


UNDO_SAID = {"yes": "undo takes it back", "no": "undo does not take it back",
             "external": "undo can't take it back (it acts outside the world)"}


def header(desk, e):
    """One line: the entry's kind, what it takes, undo, who may, where it comes from, and whether it is bound."""
    ok, how = status(desk, e)
    frm = {"kernel": "from the kernel", "verb": "from a verb note"}.get(e.frm) or (
        f"from the module {e.module()}" if e.module() else "from nowhere said")
    bits = [e.kind or "kind not said (word=)", f"takes {e.takes}" if e.takes else "takes nothing",
            UNDO_SAID.get(e.undo, f"undo={e.undo}" if e.undo else
                          "nothing to undo (a reading)" if e.kind == "see" else
                          "nothing to undo (a happening; what a rule does on it is undone as its own act)"
                          if e.kind == "hear" else "undo not said"), f"who may: {e.may}", frm]
    bits[1:1] = [x for x in (f"once: {e.once}" if e.once else "", "sealed" if e.sealed == "yes" else "",
                             f"status: {e.status}" if e.status != "live" else "") if x]
    head = " · ".join(bits)
    return head + (f", bound to {e.bound if not e.verb else 'its own lines'}" if ok else f": UNBOUND, {how}")


def help_text(desk, sid, text):
    """help <word> for an entry: its header, its help (translations left out), and the languages it is also in."""
    e = entry_of(desk, sid)
    if e is None:
        return text
    body, langs = split(text)
    out = f"{' | '.join(e.words)}   ({header(desk, e)})\n{body}"
    if langs:
        out += "\n  also in: " + ", ".join(f"{k} (read {e.aid} #{k})" for k in langs)
    return out


def card(desk, sid):
    """examine's lines for an entry, or []."""
    e = entry_of(desk, sid)
    if e is None:
        return []
    out = [f"  a dictionary entry (a13316): {' | '.join(e.words)}: {header(desk, e)}"]
    if e.langs:
        out.append("  its help is also in: " + ", ".join(e.langs) + f" (read {e.aid} #<language>)")
    return out


# ---- saying a word ------------------------------------------------------------------------------------------------

def aliases(desk):
    """-> {word: code word} for every word of a kernel entry that the code does not answer to itself."""
    w = desk.world
    found = binder_entries(w)
    if not found:
        return {}
    own = code_words(desk)
    out = {}
    for e in found:
        if e.frm != "kernel" or e.bound not in own:
            continue
        for x in e.words:
            if x != e.bound and x not in own:
                out.setdefault(x, e.bound)
    return out


def alias(desk, word):
    """-> the code's word an entry's word stands for, or None. A word a verb note answers anywhere stays the verb's
    (a world verb is never taken quietly, a1156 (4)); check() names the clash."""
    to = aliases(desk).get(str(word or "").lower())
    if not to:
        return None
    import verbs
    if any(str(word).lower() in verbs._names(s["title"]) for s in verbs.all_verbs(desk.world)):
        return None
    return to


# ---- the check ------------------------------------------------------------------------------------------------------

def check(desk, only=None):
    """-> [problem lines] about entries (helpnotes.check adds them; health prints them). Nothing when there is no
    dictionary here. only=<subject id>: that entry's."""
    w = desk.world
    found = binder_entries(w)
    if not found:
        return []
    import helpnotes
    import verbs
    probs = []

    def say(e, line):
        if only is None or e.sid == only:
            probs.append(f"dictionary entry {e.aid} \"{e.s['title']}\": {line}")

    own = code_words(desk)
    import moo

    def means(x):      # a code word's own meaning: x is examine, drag is move
        return desk.COMMAND_ALIAS.get(x) or moo.SYNONYMS.get(x) or x
    verb_words = {x: s["id"] for s in verbs.all_verbs(w) for x in verbs._names(s["title"])}
    for e in found:
        if e.kind not in KINDS:
            say(e, f"word={e.kind} is not one of {', '.join(KINDS)}")
        if e.undo and e.undo not in UNDO:
            say(e, f"undo={e.undo} is not one of {', '.join(UNDO)}")
        if e.status not in STATUS:
            say(e, f"status={e.status} is not one of {', '.join(STATUS)}")
        if not e.help.strip():
            say(e, "has no help, so it is not published (a word with no help is not published)")
        if e.frm not in ("kernel", "verb") and not e.module():
            say(e, f"from={e.frm or '(none)'} is not kernel, verb or module:<name>")
        # an unbound entry is not a problem: an entry may be written before its code lands (help, examine and rows
        # dictionary say unbound); health must never fail on what a resident may rightly write
        for x in e.words:
            if x != e.bound and x in own and means(x) != e.bound:
                say(e, f"names {x}, which the code answers to itself as {means(x)}; {x} keeps meaning that")
            if x != e.bound and x in verb_words and e.frm == "kernel":
                say(e, f"names {x}, which the verb note {verb_words[x]} answers; {x} keeps meaning that verb")
    if only is None:
        have = {x for e in found if e.frm == "kernel" for x in e.words} | {e.bound for e in found if e.frm == "kernel"}
        cmds = helpnotes.commands() - set(desk.COMMAND_ALIAS)
        for word in sorted(cmds | set(desk._help_verbs())):
            if word not in have:
                probs.append(f"no dictionary entry for {word}: its help note says no word= (do, see, hear or hold), "
                             f"from=kernel and bound=")
        for mod, src in WITNESSED.items():
            rows = module_rows(desk, mod)
            names = {e.bound for e in found if e.module() == mod}
            for r in rows or []:
                if str(r.get("name")) not in names:
                    probs.append(f"the {mod} publishes {r.get('name')} (rows witnessed:{src}) and the dictionary has no "
                                 f"entry for it, so it has no help")
    return probs
