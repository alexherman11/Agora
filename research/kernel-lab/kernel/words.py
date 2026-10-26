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

from .kernel import Refused, FLOOR, MAY_WORDS


def _k(word, kind, takes, may, undo, help, **more):
    return {"word": word, "word_kind": kind, "takes": takes, "may": may, "undo": undo, "from": "kernel",
            "bound": word, "help": help, **more}


from hosts.web.layout import HELP as PANE_HELP, panes, arrange

KERNEL_ENTRIES = [
    _k('upload', 'do', 'name=<name> [in=<group>]', 'members', 'yes', once='at most 40 per day per person',
       help='upload: send bytes through POST /upload or agora.upload(file). Private file until attach. Size/type/hash are kernel facts; undo removes the file, retaining unreachable bytes.'),
    _k('attach', 'do', '<id> to=<id>', 'members', 'yes',
       help='attach <file> to=<thing>: the uploader shares a file with their visible parent. Look at both first. Permissions follow the parent, including later hiding. Undo restores the old attachment.'),
    _k('file-result', 'do', '<id> manifest=<hash>', 'members', 'yes',
       help='file-result <file> manifest=<hash>: only the granted files process publishes verified conversion blobs and richer things. Undo removes the conversion.'),
    _k('file-read', 'see', '<id> [page=<number>]', 'anyone', 'no',
       help='file-read <file or richer thing> [page=N]: read extracted pages, table columns/rows, calendar facts or conversion failure. Permissions follow the attachment. Page numbers start at 1.'),
    _k('dictionary-copy', 'do', '<id> word=<name> [in=<group>]', 'leaders', 'yes',
       help='dictionary-copy <kernel entry> word=<name> in=<group>: copy a kernel word into this group, with its own help, may and once. Leaders can word-set their local copy. Undo removes it.'),
    _k('group', 'do', '[<id>] [name=<name>] [open=yes|no] [in=<group>]', 'leaders', 'yes',
       help='group name=… [open=yes] in=<parent>: make a group led by you. group <group> name=… renames it; open=yes|no changes membership visibility. Only its leaders may change it; undo restores it.'),
    _k('clock', 'see', '', 'anyone', 'no', help='clock: the kernel UTC time as plain data; no changes.'),
    _k('forgotten', 'see', '', 'members', 'no', help='forgotten: visible moderation notices, with reason and leader, without hidden contents. undo the hiding receipt restores the thing.'),
    _k('components', 'see', '[for="purpose"]', 'anyone', 'no',
       help='components [for="a calendar of events"]: discover components grouped by category, with honest limits. help <component> reads its full typed card and example.'),
    _k('component', 'do', '<id>', 'stewards', 'yes',
       help='component <thing>: review the current inline JavaScript bytes for trusted in-page execution. Changed or unreviewed code starts in Worker quarantine. Repeated failures also quarantine a part; component-action <lens> path=<part> action=clear is steward-only. Component gestures retain viewer-narrowed widget grants.'),
    _k('look-view', 'see', '<window or lens>', 'anyone', 'no',
       help='look-view <window, widget or component lens> [plan=yes]: compact settings, parts, gestures, health and last painted observations; plan=yes adds full bindings/modules/tree. help personal-view explains just for me; help part-style explains validated styles.'),
    _k('component-health', 'do', '<lens> data=<JSON>', 'anyone', 'no',
       help='Painter instance reports its own bounded paint observations and failures. Reports are private to its viewer; they are observations, not verified pixels.'),
    _k('component-action', 'do', '<lens> path=<part> action=retry|previous|off|clear', 'anyone', 'yes',
       help='Recover one part: retry, undo its latest code/setting field change, or turn it off for me. clear removes quarantine and requires a steward. Concurrent edits refuse previous. No unrelated world fields change.'),
    _k('personal-view','do','<lens> [part.setting=value] [text=<arrangement>]','members','yes',
       help='Just for me: personal-view <lens> part.setting=value. Also part.format.setting=initials|relative-date|count and part.labels.setting=<JSON map>, or text=<personal arrangement>. Owned private preference; shared facts stay shared. undo removes it.'),
    _k('personal-style','do','<lens> target=<part> [color=...]','members','yes',
       help='Just for me: personal-style <lens> target=card padding="4px 8px". Private owned validated style; undo removes it. help part-style lists allowed values.'),
    _k('language', 'do', '<code>', 'members', 'yes',
       help='language <code>: choose your language (for example es). Help uses that label and help text '
            'on each entry when supplied, with the original as fallback. Your agent uses your language too.'),
    _k('word-set', 'do', '<id> [help=<text>] [aliases=<names>] [may=<who>] [undo=yes|no|external]', 'maker or leaders', 'yes',
       help='word-set <entry> help=… aliases="…" may=… undo=yes|no|external: stewards edit place words; leaders edit their group copies. '
            'Also takes takes=, once=, sealed=yes|no, status=live|old|hidden, label.<lang>= and help.<lang>=. '
            'Translations label this same entry. Look first. Implementation cannot be edited.'),
    _k('word-rename', 'do', '<id> to=<name>', 'stewards', 'yes',
       help='word-rename <entry> to=<name>: a steward changes a name, keeping stored lines bound to its id. '
            'Look first. Dotted names belong to the implementing module.'),
    _k('history', 'see', '<id>', 'anyone', 'no',
       help='history <thing>: its record trail, oldest first: record, at (UTC), by, word and changed facts. '
            'Only facts you may see are returned; sealed acts never identify their author. '
            'A lens repeats these same rows with of history:$task.id as event.'),
    _k('rule', 'do', 'on=<word> [kind=<kind>] do=<line> [name=<text>]', 'members', 'yes',
       help='rule on=<word> [kind=<target kind>] do="<line>" [name=<text>]: '
            'make a rule, binding its words now. It runs as its maker when that word happens on that kind. '
            '$target and $by are supplied at firing time. off=yes stops it. '
            'make kind=rule on=<word> of_kind=<kind> do="…" says the same.'),
    *[_k(w, "see" if w == "panes" else "do", "[<words>]", "members", "no" if w == "panes" else "yes", help=h)
      for w, h in PANE_HELP.items()],
    _k("kit", "do", "<id> [name=<text>]", "leaders", "yes",
       help="kit <group> [name=<text>]: gather its verb notes, dictionary entries, lenses, styles, rules and kind "
            "declarations as one definition-only thing. Referenced module words travel too, without code or grants. "
            "Data never travels. Replace references to live data with arguments before sharing. "
            "look <kit> shows its portable bundle; post <words> about=<kit> shares it normally."),
    _k("take", "do", "[<id>] [bundle=<JSON>] [in=<group>]", "leaders", "yes",
       help="take <kit> in=<group>, or take bundle=<quoted JSON> in=<group>: place new definitions here in one act. "
            "Carry the bundle from look <kit> to another world's door. Each copy remembers its source world and thing. "
            "References inside the kit are remapped; data references and name collisions refuse the whole take. "
            "Module entries remain unbound until this world grants and runs that module. Origin is attribution, "
            "not authenticated authorship. Review shared definitions: rules run with your own rights."),
    _k("rename", "do", "<id> [word=<name>] [aliases=<names>] [in=<group>]", "leaders", "yes",
       help="rename <entry> word=<name> aliases=\"<names>\" in=<group>: change this group's dictionary names. "
            "Look first. The bound name still answers. Copies in other communities are independent."),
    _k("module", "do", "<name> run=<JSON> grants=<words>", "stewards", "yes",
       help="module <name> run=<quoted JSON argv> grants=\"<words>\": explicitly install and grant a local module. "
            "Only stewards may run code. Kits carry neither this command nor its grants. off <module> stops it."),
    _k("grant", "do", "<id> words=<words> [only=<narrowing>]", "stewards", "yes",
       help="grant <module or widget> words=\"<words>\" [only=kind:<kind>]: give something already installed one "
            "more grant, as its own act. only=\"thing:<id>;fields:hat,coat\" limits set and undo to those facts. "
            "holds and look show it; undo or off takes it back."),
    _k("counts", "see", "<id>", "anyone", "no",
       help="counts <board>: anonymous totals of active uses of its count_word, grouped by count_bucket. "
            "A thing explicitly publishes to a board with count_in=<board> count_bucket=<label>; only things "
            "made by the board's maker count. Buckets are the board's public buckets= list. Counts expose "
            "neither target ids nor people, including when the target itself is hidden."),
    _k("test", "see", "[<id>] expr=<boolean> [value=<text>]", "anyone", "no",
       help="test [<thing>] expr=\"<boolean>\" [value=<text>]: answer yes or no, without changing anything. "
            "Expressions use literals, and/or/not, ==/!=, field('name') on the target, used('word', target) "
            "for YOUR active use (your agents count too), and digest(value), a SHA256 of trimmed casefolded text. "
            "No Python code runs. A see verb may contain one test; make sees_when=word:<see verb> narrows its "
            "normal visibility. allows.<word>=word:<see verb> also narrows admission of that word on the thing; "
            "its value is the line's answer=. refusal=<text> supplies a kind refusal. Policies bind entry ids, "
            "fail closed, and cannot call modules. They may inspect their own target's non-sealed facts."),
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
    _k("widget", "do", "<id> grants=<words> [surface=window|top|bottom|overlay] [only=kind:...]", "stewards", "yes",
       help="widget <thing> grants=\"...\" surface=window|top|bottom|overlay: activate in-page code with ordinary grants. "
            "Copying code grants no power. off <widget> stops it; undo restores its activation."),
    _k("describe", "do", "<id> text=<text>", "anyone", "yes",
       help="describe <widget> text=...: a running widget describes its own display for look; no other facts change."),
    _k("status", "see", "<module>", "anyone", "no",
       help="status <module>: what a running module says it is doing."),
    _k("rows", "see", "[<kind>] [k=<v> ...]", "anyone", "no", aliases="find",
       help="rows <kind> [field=value …]: the things of a kind you may see, as rows with their revs, in their `order`, "
            "then as made: rows item meeting=sb40, rows window, rows any.\nfind kind=<kind> … says the same."),
    _k("verb", "do", "<word> steps=<lines> help=<text> [may=<who>] [kind_of=do|see] [in=<group>]", "leaders", "yes",
       help="verb <word> steps=\"<lines>\" help=\"<what it does>\": a new word made of other words, a verb note. Its "
            "steps run as whoever says it, so it never adds power, and a do verb's steps are one act, which one undo "
            "takes back. $1 $2 … and $* are what follows the word.\n"
            "e.g. verb stop steps=\"off $1\" help=\"stop <module>: the same as off\". Leaders make words for their "
            "groups; undo takes the word back. Named values use $answer (quoted as data); "
            "once= and sealed= have the same meaning as on dictionary entries."),
    _k("holds", "see", "", "anyone", "no",
       help="holds: what each running module holds now (an overlay, a stream), and since when."),
    _k("make", "do","kind=<kind> [in=<group>] [k=<v> ...]", "members", "yes",
       help="make kind=<kind> [in=<group>] [name=… title=… text=…]: make a lasting thing of any kind: a lens, a button, "
            "a sign-up slot.\nIts other k=v are its first facts. In a group it is seen by the group."),
    _k("set", "do", "<id> k=<v> ...", "maker or leaders", "yes",
       help="set <thing> k=v …: change facts on a thing you made (leaders: any in their group). k= with nothing "
            "after it takes a fact away. Grants may narrow writes with only=\"thing:<id>;fields:hat,coat\"; "
            "the same scope checks every fact restored by undo."),
    _k("forget", "do", "<id>", "maker or leaders", "yes",
       help="forget <thing>: take a thing out of every view. It is never erased: undo brings it back."),
    _k("claim", "do", "<id> [phone=<v>]", "members", "yes", once="per person per target",
       help="claim <thing> [phone=…]: take a seat on it: a public-comment slot, a carpool seat.\n"
            "A thing says how many seats it has and when sign-up closes. A phone is seen only by you and the leaders. "
            "undo gives the seat back."),
    _k("vote", "do", "<id> <option>", "members", "yes", sealed="yes", once="per person per target", fence="adds",
       help="vote <poll> <option>: one vote each, sealed: the counts are shown, not who voted how.\n"
            "undo takes your vote back, so you can vote again."),
    _k("role", "do", "<id> leader|member|none in=<group>", "leaders", "yes",
       help="role <person> leader|member|none in=<group>: who leads a group and who belongs to it. Leaders appoint."),
]

# aspects no line may write with make or set: what the kernel itself keeps, or derives
RESERVED_KINDS = {"person", "agent", "module", "grant", "word", "invite", "world", "place", "group", "kit", "web-layout", "paint-report"}
RESERVED_KINDS.add('file')
RESERVED = {"kind", "made_by", "for", "pinned", "forgotten", "sees", "lives", "from", "bound", "origin", "bundle",
            "made", "changed", "made_at", "changed_at", "steps_bound", "do_bound", "on_entry", "reviewed_code"}
SEES_SAID = {"me", "leaders", "group", "place"}      # what `make … sees=` may say (section 7: it may narrow)
from .blobs import PROTECTED
RESERVED.update(PROTECTED | {'pin_until', 'forget_reason'})
RESERVED_PREFIX = ("in:", "like:", "member:", "answer:", "sees.", "vote:", "claim:", "contact:")

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
    if not m or k.state.get(m, "kind") not in ("module", "widget"):
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
        if kind in ("module", "widget") and (kind == 'module' or a.get('code')):
            grants = [g for g in k.things("grant") if k.state.get(g, "to") == t]
            live = [k.state.get(g, "words") for g in grants if not k.state.get(g, "revoked")]
            words = [k.state.get(e, "word") for e in k.entries() if k.state.get(e, "from") == f"module:{a.get('name')}"]
            on = "on" if a.get("on") else "off"
            run = "running" if k.modules and k.modules.running(t) else "not running"
            if kind == 'widget':
                run = 'running' if any(h['by']==t for h in k.leases.values()) else 'not mounted'
            description = a.get('description', '') if kind == 'widget' else ''
            return {"text": f"{a.get('name')} ({t}), a {kind}: {on}, {run}; {description}; publishes {a.get('publishes')}; "
                            f"grants: {', '.join(live) or 'none'}; words: {', '.join(words) or 'none'}",
                    "rows": [{"id": t, "kind": kind, "name": a.get("name"), "on": bool(a.get("on")),
                              "description": description, "grants": live, "words": words}]}
        if kind in ("person", "agent"):
            answers = {x[7:]: v for x, v in a.items() if x.startswith("answer:")}
            text = f"{k.name(t)} ({t}), {'an agent' if kind == 'agent' else 'a person'}"
            if answers:
                text += " · answers: " + ", ".join(f"{q}={v}" for q, v in answers.items())
            return {"text": text, "rows": [{"id": t, "kind": kind, "name": k.name(t), "answers": answers}]}
        if kind == "word":
            return {"text": f"{a.get('word')} ({t}), a {a.get('word_kind')} word: {a.get('help', '').splitlines()[0]}",
                    "rows": [dict(a, id=t)]}
        facts = [f"{x}={v}" for x, v in a.items() if x not in ("kind", "made_by", "for") and
                 not x.startswith(("in:", "member:", "claim:", "contact:"))]
        who = k.name(a.get("made_by")) if a.get("made_by") else None
        return {"text": f"{a.get('title') or k.name(t)} ({t}), a{'n' if str(kind)[:1] in 'aeiou' else ''} {kind}"
                        + (f" by {who}" if who else "") + ("\n  " + "\n  ".join(facts) if facts else ""),
                "rows": [dict(a, id=t)]}
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
    from .dictionary import localized
    if st.words:
        w = st.words.split()[0].lower()
        e = k.find_entry(w, group)
        if e is None:
            if w=='part-style':
                return dict(text='make kind=part-style lens=<lens> target=component.part[fact=value] color=... background=... radius=... padding=... gap=... glow=... lines=1..9 emphasis=normal|bold. Colour tokens or #rgb/#rgba/#rrggbb/#rrggbbaa. Spacing uses 1..4 measures (gap 1..2), including CSS shorthand padding. target=tokens defines colour/spacing and motion-<name> JSON tokens. Invalid writes refuse. personal-style applies just for me.')
            card = component_card(k, actor, w)
            if card: return card
            if w in FLOOR_HELP:
                return {"text": f"{FLOOR_HELP[w]}\n(this word's entry is missing; the kernel answers from its own floor)"}
            raise Refused(f"nothing answers to '{w}' here; help lists the words you may use")
        if k.shown(actor.person, e) is None:
            raise k.no_such(e)
        a = localized(k, actor.person, k.entry(e))
        k.mark(actor, e, k.shown(actor.person, e))
        facts = [f"{a['word']} ({e}), a {a.get('word_kind')} word", f"takes: {a.get('takes') or 'nothing'}",
                 f"who may: {a.get('may')}"]
        for key in ("once", "sealed", "undo"):
            if a.get(key):
                facts.append(f"{key}: {a[key]}")
        facts.append(f"from: {a.get('from')}" + (f" ({a['bound']})" if a.get("bound") and a.get("bound") != a["word"] else ""))
        if a.get("from", "").startswith("module:"):
            mid = k.module_named(a["from"][7:])
            if not mid or not k.state.get(mid, "on") or not k.modules or not k.modules.running(mid):
                facts.append("unbound: this community must grant and run the module")
        return {"text": a.get("help", "") + "\n" + " · ".join(facts), "rows": [dict(a)]}
    mine, others = [], []
    for e in sorted(k.entries(), key=lambda e: k.state.get(e, "word")):
        if k.shown(actor.person, e) is None:
            continue
        a = localized(k, actor.person, k.entry(e))
        line = f"  {a['word']} ({a.get('word_kind')}): {a.get('help', '').splitlines()[0]}"
        (mine if k.may(actor, a, None, group) else others).append((line, a))
    text = ["words you may use here:"] + [l for l, _ in mine]
    if others:
        text.append("not yours here: " + ", ".join(f"{a['word']} ({a.get('may')})" for _, a in others))
    return {"text": "\n".join(text), "rows": [{"word": a["word"], "kind": a.get("word_kind"), "yours": True} for _, a in mine]
            + [{"word": a["word"], "kind": a.get("word_kind"), "yours": False} for _, a in others]}


def post(k, actor, st, entry, tx, group, saw=None):
    text = str(st.kv.get('text') or st.words).strip()
    if not text:
        raise Refused("post needs words: post <words> [in=<group>]")
    kv = {a: v for a, v in st.kv.items() if a not in ('text', 'in', 'as', 'about', 'within', 'sees')}
    sees = st.kv.get('sees')
    if sees is not None and sees not in SEES_SAID:
        raise Refused('sees says me, leaders, group or place')
    if sees == 'place' and group != k.place and not k.state.get(group, 'open'):
        raise Refused('a closed group cannot publish to the whole place')
    _writable(k, kv)
    p = tx.mint()
    tx.set(p, "kind", "post")
    tx.set(p, "text", text)
    for a, v in kv.items():
        if v != '':
            tx.set(p, a, v)
    _within(k, actor, st, tx, p)
    tx.set(p, "made_by", actor.id)
    if actor.id != actor.person:
        tx.set(p, "for", actor.person)
    tx.set(p, f"in:{group}", len(k.log.records) + 1)
    if group != k.place and not k.state.get(group, "open"):
        tx.set(p, "sees", f"group:{group}")
    if sees == 'me':
        tx.set(p, 'sees', 'person:' + actor.person)
    elif sees == 'leaders':
        tx.set(p, 'sees', 'leaders')
    _about(k, actor, st, tx, p)
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
    if st.kv.get('until'):
        from .world_words import utc
        utc(st.kv['until'])
        tx.set(t, 'pin_until', st.kv['until'])
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
    for target in {f[0] for f in facts}:
        k.reaches(actor, 'undo', k.state.get(target, 'kind'), target=target,
                  fields=[f[1] for f in facts if f[0] == target])
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
    if k.state.get(m, 'kind') == 'widget':
        return {'text': f"{name}: {'on' if k.state.get(m, 'on') else 'off'} · " + str(k.state.get(m, 'description') or 'no description yet')}
    if not k.modules or not k.modules.running(m):
        return {"text": f"{name} is not running ({'on' if k.state.get(m, 'on') else 'off'})"}
    said = k.modules.status(m)
    return {"text": f"{name}: {said}" if said else f"{name} did not say what it is doing within 2 s"}


def describe(k, actor, st, entry, tx, group, saw=None):
    if actor.kind != 'module' or actor.module != st.target or k.state.get(st.target, 'kind') != 'widget':
        raise Refused('a widget may describe only itself')
    text = str(st.kv.get('text', ''))[:2000]
    if text != k.state.get(st.target, 'description'):
        tx.set(st.target, 'description', text)
    return {'text': 'ok describe [r?]'}


def _writable(k, kv):
    for key in kv:
        if key in RESERVED or key.startswith(RESERVED_PREFIX) or not re.match(r"^[a-z_][a-z0-9_.-]*$", key):
            raise Refused(f"{key} is not a fact a line may write; the kernel keeps it")


def _conditions(k, kv, group):
    for key, value in list(kv.items()):
        if (key == "sees_when" or key.startswith("allows.")) and value:
            kv[key] = k.bind_policy(value, group)


def make(k, actor, st, entry, tx, group, saw=None):
    kv = dict(st.kv)
    kind = kv.pop("kind", "")
    kv.pop("in", None)
    kv.pop("about", None)                               # checked and set by _about
    kv.pop("as", None)                                  # a handle for later steps of the same line, not a fact
    kv.pop('within', None)
    sees = kv.pop("sees", None)
    if not re.match(r"^[a-z][a-z0-9_-]{0,31}$", kind or ""):
        raise Refused("make needs kind=<a plain word>: make kind=button name=Feed")
    if kind in RESERVED_KINDS:
        raise Refused(f"a {kind} is made by the kernel, not by make")
    if kind == 'post':
        # Keep make kind=post compatible, while applying the same scoped post
        # policy and rate limit. Its post part counts inside this make act.
        eid = k.find_entry('post', group)
        e = k.entry(eid)
        if not k.may(actor, e, None, group):
            raise k.refusal_for(e, group)
        said = k.once(actor, e, None, tx)
        if said:
            raise Refused(said)
        from .lines import Step
        tx.part(e['word'], None, st.text)
        tx.parts[-1]['entry'] = eid
        return post(k, actor, Step(st.text, e['word'], None,
            {a: v for a, v in st.kv.items() if a != 'kind'}, st.words), e, tx, group, saw)
    if kind == 'file-settings' and not k.is_steward(actor.person):
        raise Refused('file-settings belongs to stewards')
    k.reaches(actor, "make", kind)
    if sees is not None and sees not in SEES_SAID:
        raise Refused("sees= says me, leaders, group or place: who besides the kernel may see it")
    _writable(k, kv)
    _conditions(k, kv, group)
    from painter.handles import validate_write
    validate_write(k, actor, kind, kv, tx)
    if kind == 'rule':
        from .dictionary import bind
        eid = k.find_entry(kv.get('on', ''), group)
        if not eid:
            raise Refused('a rule needs on=<published word>')
        kv['on_entry'] = eid
        kv['do_bound'] = bind(k, kv.get('do', ''), group)
    t = tx.mint()
    tx.set(t, "kind", kind)
    _within(k, actor, st, tx, t)
    for key, v in kv.items():
        if v != "":
            tx.set(t, key, v)
    if st.words and "text" not in kv:
        tx.set(t, "text", st.words)
    _about(k, actor, st, tx, t)
    tx.set(t, "made_by", actor.id)
    if actor.id != actor.person:
        tx.set(t, "for", actor.person)
    tx.set(t, f"in:{group}", len(k.log.records) + 1)
    public = group == k.place or k.state.get(group, "open")         # an open group's work is seen by all
    if sees == "me":
        who = k.state.get(actor.module, "for") if actor.kind == "module" and actor.caller is None else actor.person
        if not who or k.state.get(who, "kind") != "person":
            raise Refused("sees=me needs a person: a module says it only when it is installed for one")
        tx.set(t, "sees", f"person:{who}")
    elif sees == "leaders":
        tx.set(t, "sees", "leaders")
    elif sees == "place" and not public:
        raise Refused(f"{k.name(group)} is not open, so what is made in it is seen by its members, not the place")
    elif not public:
        tx.set(t, "sees", f"group:{group}")
    return {"text": f"ok make {t} [r?] · a{'n' if kind[0] in 'aeiou' else ''} {kind}" + (f" in {k.name(group)}" if group != k.place else "")}


def set_(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, 'kind') == 'file-settings' and not k.is_steward(actor.person):
        raise Refused('file-settings belongs to stewards')
    k.reaches(actor, "set", k.state.get(t, "kind"), target=t, fields=st.kv)
    if k.state.get(t, "kind") in RESERVED_KINDS:
        raise Refused(f"{t} is a {k.state.get(t, 'kind')}; set changes only things made with make")
    if not st.kv:
        raise Refused("set needs k=v: set <thing> label=Feed")
    _writable(k, st.kv)
    _conditions(k, st.kv, group)
    from painter.handles import validate_write
    previous=dict(k.state.things.get(t,{}))
    previous.update({a:v for (thing,a),v in tx.over.items() if thing==t})
    candidate={**previous,**st.kv}
    candidate={a:v for a,v in candidate.items() if v!=''}
    validate_write(k,actor,k.state.get(t,'kind'),candidate,tx)
    if k.state.get(t, 'kind') == 'rule':
        from .dictionary import bind
        values = dict(st.kv)
        if 'on' in values:
            eid = k.find_entry(values['on'], group)
            if not eid:
                raise Refused('a rule needs on=<published word>')
            values['on_entry'] = eid
        if 'do' in values:
            values['do_bound'] = bind(k, values['do'], group)
        st.kv = values
    k.fence(actor, t, list(st.kv), saw)
    for key, v in st.kv.items():
        if v != "":
            tx.set(t, key, v)
        else:
            tx.set(t, key)                      # k= with nothing after it: the fact goes
    return {"text": f"ok set {t} [r?] · " + ", ".join(f"{a}={v}" if v else f"{a} taken away" for a, v in st.kv.items())}


def forget(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    k.reaches(actor, "forget", k.state.get(t, "kind"))
    if k.state.get(t, "kind") in RESERVED_KINDS:
        raise Refused(f"{t} is a {k.state.get(t, 'kind')}, which forget does not take")
    tx.set(t, "forgotten", actor.person)
    if st.kv.get('reason'):
        tx.set(t, 'forget_reason', st.kv['reason'])
    return {"text": f"ok forget {t} [r?] · out of every view; undo brings it back"}


def _about(k, actor, st, tx, t):
    """`about=<id>`: what a post or a made thing is about (an agenda item, a staff report). It must be one the maker
    may see."""
    a = st.kv.get("about")
    if not a:
        return
    if k.shown(actor.person, a) is None:
        raise k.no_such(a)
    tx.set(t, "about", a)


def _within(k, actor, st, tx, t):
    parent = st.kv.get('within')
    if parent:
        if k.shown(actor.person, parent) is None:
            raise k.no_such(parent)
        tx.set(t, 'visibility_of', parent)


def claim(k, actor, st, entry, tx, group, saw=None):
    """claim <thing> [phone=…]: take one of its seats (a comment slot, a carpool seat). A thing says `seats` (1 when
    it says none) and may say `closes` (a UTC time, 2026-10-28T18:30Z); a contact given is seen only by the person
    and leaders."""
    t = st.target
    a = k.state.things.get(t, {})
    taken = [x for x in a if x.startswith("claim:")]
    seats = int(a.get("seats", 1)) if str(a.get("seats", 1)).isdigit() else 1
    if f"claim:{actor.person}" in a:
        raise Refused(f"you already hold a seat on {t}; undo gives it back")
    if a.get("closes") and k.now().strftime("%Y-%m-%dT%H:%MZ") >= str(a["closes"]):
        raise Refused(f"sign-up for {k.name(t) if a.get('title') else t} closed at {a['closes']}")
    if len(taken) >= seats:
        raise Refused(f"{t} is taken ({seats} seat{'' if seats == 1 else 's'}, all claimed); look shows what is open")
    tx.set(t, f"claim:{actor.person}", actor.id)
    contact = st.kv.get("phone") or st.kv.get("contact")
    if contact:
        tx.set(t, f"contact:{actor.person}", contact)
        tx.set(t, f"sees.contact:{actor.person}", f"person:{actor.person}|leaders")
    left = seats - len(taken) - 1
    return {"text": f"ok claim {t} [r?] · yours; {left} seat{'' if left == 1 else 's'} left"
                    + ("; your contact is seen only by you and the leaders" if contact else "")}


def vote(k, actor, st, entry, tx, group, saw=None):
    """vote <poll> <option>: sealed. The world knows you voted; readers see only the counts."""
    t = st.target
    options = str(k.state.get(t, "options") or "").split()
    choice = (st.words.split() or [""])[0].lower()
    if not options:
        raise Refused(f"{t} is not a poll; make kind=poll title=… options=\"yes no\" makes one")
    if choice not in options:
        raise Refused(f"vote {t} needs one of: {' '.join(options)}")
    from .world_words import utc
    if k.state.get(t, "closed") or (k.state.get(t, 'closes') and k.now() >= utc(k.state.get(t, 'closes'))):
        raise Refused(f"the poll {t} is closed")
    seal = k.seal(actor.person, entry["id"], t)
    tx.set(t, f"vote:{seal}", choice)
    return {"text": f"ok vote {t} [r?] · counted; how you voted is sealed"}


def role(k, actor, st, entry, tx, group, saw=None):
    """role <person> leader|member|none in=<group>: who leads or belongs to a group. Leaders appoint."""
    p = st.target
    what = (st.words.split() or [""])[0].lower()
    if k.state.get(p, "kind") != "person":
        raise Refused(f"{p} is not a person")
    if what not in ("leader", "member", "none"):
        raise Refused("role <person> leader|member|none in=<group>")
    g = st.kv.get("in") or k.place
    if what == "none":
        tx.set(g, f"member:{p}")                        # no value: the fact goes
    else:
        tx.set(g, f"member:{p}", what)
    return {"text": f"ok role {p} [r?] · {k.name(p)} is {'no longer in' if what == 'none' else 'a ' + what + ' of'} "
                    f"{k.name(g)}"}


def rows(k, actor, st, entry, tx, group, saw=None):
    """rows <kind|any> [field=value …] (or find kind=<kind> …): the things of a kind you may see, with their revs, so
    whoever reads them can act on what it read; in their `order` when they have one, then as made."""
    kv = dict(st.kv)
    kind = kv.pop("kind", None) or (st.words.split() or ["any"])[0].lower()
    kv.pop("in", None)
    rows = []
    for t in (list(k.state.things) if kind == "any" else k.things(kind)):
        if t == "world":
            continue
        a = k.shown(actor.person, t)
        if a is None or any(str(a.get(f, "")) != v for f, v in kv.items()):
            continue
        row = {x: v for x, v in a.items() if not x.startswith(("in:", "member:"))}
        row['groups'] = k.groups_of(t)
        if a.get("made_by"):
            row["by"] = k.name(a["made_by"])
        rows.append(dict(row, id=t, rev=k.state.rev.get(t, 0)))
    rows.sort(key=lambda r: (int(r["order"]) if str(r.get("order", "")).isdigit() else 10 ** 9,
                             int(r["id"][len(k.tag):] or 0)))       # then in the order they were made
    for r in rows:
        k.mark(actor, r["id"], r)
    what = kind if kind != "any" else "thing"
    text = "\n".join(f"  {r['id']} · {r.get('kind')} · "
                     f"{r.get('title') or r.get('name') or r.get('word') or (r.get('text') or '')[:60]}" for r in rows)
    return {"text": f"{len(rows)} {what}{'' if len(rows) == 1 else 's'}" + ("\n" + text if rows else ""),
            "rows": rows}


VERB_NAME = re.compile(r"^[a-z][a-z0-9-]{0,31}$")


def verb(k, actor, st, entry, tx, group, saw=None):
    """verb <word> steps=… help=…: a verb note, its own entry (from=verb) living in the line's group."""
    kv = dict(st.kv)
    w = (st.words.split() or [""])[0].lower()
    if not VERB_NAME.match(w):
        raise Refused("verb needs a plain word: verb <word> steps=\"<lines>\" help=\"…\" (dotted words belong to "
                      "modules)")
    if k.find_entry(w, group):
        raise Refused(f"{w} already answers here; choose another word, so no word is hidden behind it")
    steps, help_ = str(kv.get("steps") or ""), str(kv.get("help") or "").strip()
    if not steps.strip():
        raise Refused('a verb note needs steps="<lines>", the words it runs')
    if not help_:
        raise Refused('a word with no help is not published: add help="<what it does>"')
    wk = kv.get("kind_of", "do")
    if wk not in ("do", "see"):
        raise Refused("a verb note is a do or a see word: kind_of=do|see")
    may = kv.get("may", "anyone")
    if not all(t.strip() in MAY_WORDS for t in may.split(" or ")):
        raise Refused(f"may={may}: say anyone, members, leaders, stewards, maker or nobody, joined by or")
    e = tx.mint()
    from .dictionary import bind
    tx.set(e, 'steps_bound', bind(k, steps, group, w, e))
    for a, v in [("kind", "word"), ("word", w), ("word_kind", wk), ("takes", kv.get("takes", "[<words>]")),
                 ("help", help_), ("may", may), ("undo", "yes" if wk == "do" else "no"), ("from", "verb"),
                 ("bound", w), ("steps", steps), ("lives", group), ("made_by", actor.id)]:
        tx.set(e, a, v)
    for key in ("once", "sealed", "fence"):
        if kv.get(key):
            tx.set(e, key, kv[key])
    return {"text": f"ok verb {w} ({e}) [r?] · a new word in {k.name(group)}: {steps}"}


def test(k, actor, st, entry, tx, group, saw=None):
    from .predicates import evaluate
    context = getattr(k._local, "predicate", None)
    target, value, policy = context or (st.target, st.kv.get("value", ""), False)
    result = evaluate(k, actor.person, target, st.kv.get("expr", ""), value, policy)
    return {"text": "yes" if result else "no", "value": result, "rows": []}


def counts(k, actor, st, entry, tx, group, saw=None):
    board = k.shown(actor.person, st.target)
    buckets = str(board.get("buckets", "")).split()
    eid = k.find_entry(str(board.get("count_word", "")), (k.groups_of(st.target) or [k.place])[0])
    if not buckets or not eid or k.state.get(eid, "sealed") != "yes":
        raise Refused("a count board needs buckets= and count_word=<sealed word>")
    targets = {t: a.get("count_bucket") for t, a in k.state.things.items()
               if a.get("count_in") == st.target and a.get("made_by") == board.get("made_by")
               and not a.get("forgotten") and a.get("count_bucket") in buckets}
    totals = dict.fromkeys(buckets, 0)
    undone = k.undone()
    for r in k.log.records:
        if r["seq"] in undone or r.get("undoes") or not r.get("parts"):
            continue
        included = {p.get("target") for p in r["parts"] if p.get("entry") == eid}
        if r.get("entry") == eid:
            included.add(r["parts"][0].get("target"))
        for target in included:
            bucket = targets.get(target)
            if bucket in totals:
                totals[bucket] += 1
    return {"text": "sealed counts: " + " · ".join(f"{b}: {n}" for b, n in totals.items()),
            "rows": [{"bucket": b, "count": n} for b, n in totals.items()]}


def holds(k, actor, st, entry, tx, group, saw=None):
    rows = [dict(h, by=k.name(h["by"])) for h in k.leases.values()]
    text = "\n".join(f"  {r['by']} holds {r['word']} ({r['lease']}) since {r['since']}" for r in rows)
    return {"text": ("holds:\n" + text) if rows else "nothing is held", "rows": rows}


def rule(k, actor, st, entry, tx, group, saw=None):
    from .lines import Step
    kv = dict(st.kv)
    if 'kind' in kv:
        kv['of_kind'] = kv.pop('kind')
    kv['kind'] = 'rule'
    return make(k, actor, Step(st.text, 'make', None, kv, ''), entry, tx, group, saw)


def history(k, actor, st, entry, tx, group, saw=None):
    rows = k.trail(actor.person, st.target)
    k.mark(actor, st.target, k.shown(actor.person, st.target))
    return {'text': '\n'.join(f"{r['record']} · {r['at']} · {r['by']} · {r['word']} · {r['changes']}" for r in rows),
            'rows': rows}


from .dictionary import word_set, word_rename, language
from .kits import kit, take, rename, module, grant
from .inpage import widget
from .blobs import upload, attach, file_result, file_read
from .world_words import dictionary_copy, group_word, clock, forgotten
from painter.arrangement import component, look_view, components, component_card
from painter.health import component_health, component_action, personal_view, personal_style

KERNEL = {"kit": kit, "take": take, "rename": rename, "module": module, "grant": grant, "widget": widget, "describe": describe,
          'upload': upload, 'attach': attach, 'file-result': file_result, 'file-read': file_read,
          'dictionary-copy': dictionary_copy, 'group': group_word, 'clock': clock, 'forgotten': forgotten,
          'component': component, 'look-view': look_view, 'components': components,
          'component-health': component_health, 'component-action': component_action,
          'personal-view': personal_view, 'personal-style': personal_style,
          'word-set': word_set, 'word-rename': word_rename, 'history': history, 'rule': rule,
          'language': language,
          **{w: panes if w == "panes" else arrange for w in PANE_HELP},
          "counts": counts, "test": test, "look": look, "help": help_, "post": post, "like": like, "pin": pin, "undo": undo, "off": off,
          "status": status, "make": make, "set": set_, "forget": forget, "holds": holds, "claim": claim,
          "vote": vote, "role": role, "rows": rows, "find": rows, "verb": verb}
