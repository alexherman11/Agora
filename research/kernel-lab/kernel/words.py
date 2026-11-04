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
    _k("task.signal", "do", "<id> mode=<waiting|notify|reporter> event=<landed|done>",
       "members", "yes",
       help="task.signal <card> mode=waiting|notify|reporter event=landed|done: "
            "write deduplicated addressed card notes for world rules; undo removes them. "
            "No execution or completion permission is granted."),
    *[_k("task." + action, "do", "<id> " + takes, "members", "yes", help=help_,
         bound="task-" + action, aliases="task-" + action)
      for action, takes, help_ in [
          ("next", 'next_action=<text> acceptance=<text>', "task.next <task>: retain the next action and acceptance."),
          ("revise", 'goal=<text> acceptance=<text> request_ref=<ref> next_action=<text>', "task.revise <task>: reconcile intent with the current request."),
          ("review", 'basis=<token> next_action=<text>', "task.review <task>: designated reviewer acknowledges the current result; clears review_at."),
          ("verify", 'basis=<token> evidence=<id>', "task.verify <task>: designated reviewer attests acceptance against current visible evidence."),
          ("followup", 'review_at=<ISO-datetime>', "task.followup <task>: retain an explicit review deadline with timezone; never starts a timer.")]],
    _k('upload', 'do', 'name=<name> [in=<group>] [digest=<sha256>]', 'members', 'yes', once='at most 40 per day per person',
       help='upload: send bytes through POST /upload or agora.upload(file). Private file until attach. Size/type/hash are kernel facts; undo removes the file, retaining unreachable bytes. A module hands its caller a file it made with digest=<sha256> of bytes it put in the world\'s blob store.'),
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
       help="look-view <window, widget or component lens> [plan=yes]: compact settings, parts, gestures and this screen's paint health (kept on the screen, never in the world); plan=yes adds full bindings/modules/tree. help personal-view explains just for me; help part-style explains validated styles."),
    _k('component-health', 'do', '<lens> data=<JSON>', 'anyone', 'no',
       help='Painter instance reports its own failures and recovery. Kept on this screen (the kernel process memory, per viewer), never recorded: no painted text, no styles, no log line. A restart forgets it.'),
    _k('component-action', 'do', '<lens> path=<part> action=retry|previous|off|clear', 'anyone', 'yes',
       help='Recover one part: retry (also turns it back on for you), undo its latest code/setting field change (previous, recorded), or turn it off for you (off: a private view-preference <part>.enabled=no; undo takes it back). clear removes quarantine and requires a steward. Concurrent edits refuse previous. Quarantine and health stay on the screen.'),
    _k('paint-clear', 'do', '', 'stewards', 'yes',
       help='paint-clear: forget every old paint-report thing (screen state the painter used to keep in the world) in one act, one record. Paint health is kept on the screen now. undo brings them back.'),
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
    _k('history', 'see', '[<id>]', 'anyone', 'no',
       help='history [<thing>]: a thing\'s record trail, oldest first: record, at (UTC), by, word and changed facts; '
            'alone, your own latest acts (recent shows everyone\'s). '
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
            "only=\"kind:document-folder,document-entry;library:<id>\" limits make/set to inherited metadata "
            "in one visible library: named folders/entries only, name/parent changes only, no cross-library moves. "
            "On files.browse/folder/store/rename/move, only=\"library:<id>\" checks the complete outer "
            "selection and limits the provider's per-call rows readings to that library. "
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
    _k("say", "do", "<id> <words> [reply_to=<id>] [about=<id>]", "members", "yes",
       help="say <chat> <words>: a line in a chat (rows chat lists them). @name calls that person; in a closed chat "
            "(made with with=\"Alex, JEFF\") a line with no @name speaks to everyone else in it. reply_to=<said line> "
            "answers one. Only the chat's people may say in a closed chat. undo takes your line back."),
    _k("chat.receive", "do", "<id> text=<text> speaker=<name> external_id=<id>", "anyone", "yes",
       help="chat.receive <chat> text=... speaker=... external_id=...: import one external line; only the "
            "read-only chat's designated source module may use this. Duplicate ids do nothing; no local @name wakes."),
    _k("chat", "see", "<id> [limit=<n>] [since=<id>]", "anyone", "no",
       help="chat <chat> [limit=20] [since=<said line>]: its latest lines, oldest first, as you may see them. "
            "make kind=chat name=<name> makes an open chat; with=\"<names>\" makes one only those people see."),
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
            "then as made: rows item meeting=sb40, rows window, rows any.\nfind kind=<kind> … says the same; "
            "find <words>, when the first word is no kind, searches as search does."),
    _k("search", "see", "<words> [limit=<n>] [kind=<kind>]", "anyone", "no",
       help="search <words> [limit=12] [kind=<kind>]: the things of every kind you may see whose name, title or text "
            "holds all the words, title matches first, then open work (Now first) above done, each with its kind "
            "and a snippet. A name in the words is only words: search beach finds the beach board, the channels "
            "its view shows, its button, map and cards. find <words> says the same; board.search q=… searches posts and pages."),
    _k("verb", "do", "<word> steps=<lines> help=<text> [may=<who>] [kind_of=do|see] [acts_on=<kind>] [needs=<needs>] "
                     "[in=<group>]", "leaders", "yes",
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
    _k("who", "see", "", "anyone", "no",
       help="who: the people here (and who leads), the agents and whom they act for, and the modules, on or off."),
    _k("recent", "see", "[by=<name|me>] [kind=<kind>] [since=r<n>] [limit=<n>]", "anyone", "no",
       help="recent [by=<name|me>] [kind=<kind>] [since=r<n>] [limit=<n>]: the latest acts you can see, newest first: "
            "record, time, who, which word, on what. Never facts, never a sealed act's author."),
    _k("refusals", "see", "[by=<name|me>] [limit=<n>] [errors] [all]", "anyone", "no",
       help="refusals [by=<name|me>] [limit=<n>] [errors] [all]: the latest refused lines and errors, newest first: "
            "when, who (and whom a module or widget acted for), the line, and why. From any button, word, module, "
            "rule or agent; a module that died and a page's failure (failed) land here too. The same refusal again "
            "is counted (×N), not repeated. A steward sees everyone's; anyone else their own. errors leaves out "
            "plain refusals. Kept beside the world, never in it: a refusal writes nothing."),
    _k("failed", "do", "why=<text> [line=<text>] [where=<page>]", "anyone", "no",
       help="failed why=\"…\" [line=\"…\"] [where=dock]: say that something failed outside any line (a frame "
            "stopped, a native call threw, a bar fell back), so it lands in refusals. Writes nothing in the world."),
    _k("kinds", "see", "[<words>]", "anyone", "no",
       help="kinds: every kind of thing you can see, with how many. kinds <thing>: every kind it is, nearest first, "
            "each with why (its own kind, what that extends, and every kind whose needs it has). A kind may say what "
            "its things need: make kind=kind name=event needs=\"title start|starts\" (start|starts: either spelling; "
            "game=yes: a marker someone sets) and extend others: name=meeting extends=event needs=place. A kind with "
            "needs is declared by leaders and only widens. rows <kind> lists one kind; actions <thing> says what acts on it."),
    _k("mark", "do", "<id> <kind>", "maker or leaders", "yes",
       help="mark <thing> <kind>: set a kind's markers (a game needs run and game=yes: mark sets game=yes) on a thing "
            "that has the kind's other needs, or say what it lacks. It is a set: undo takes it back."),
    _k("alike", "see", "<kind>", "anyone", "no",
       help="alike <kind>: the kinds here made of the same parts, closest first: what they share, what only they have, "
            "and which extends which. Read it before naming a kind, so the same thing isn't made twice: if it's the "
            "same, aliases= on the one that's here names it; if it has notably more, extends= it."),
    _k("aspects", "see", "[loose]", "anyone", "no",
       help="aspects [loose]: every aspect on things you can see, as a part of which kind (likes is an upvote, start a "
            "time) or loose, with how many things say it. Many things sharing a loose aspect is a kind nobody has named. "
            "A kind gives its parts kinds: needs=\"start:time likes:upvote\"; a value kind ends in one: name=upvote "
            "value=number (the kernel's are text number time yes-no link person thing)."),
    _k("actions", "see", "<id>", "anyone", "no",
       help="actions <thing>: what you can do with it: every word whose shape it has (what the word's code reads, from "
            "acts_on=<kind> and needs=), grouped by kind, most specific first; then the lenses that show it."),
    _k("turn", "do", "<id> [r<n>|<id>|done] [work=<id>]", "anyone", "no",
       help="turn <agent> r<n> [work=<card>]: what an agent's acts are answering now (the line that woke it) and the "
            "card it works on, so every act it makes says because=… and work=… in the log. turn <agent> done ends it. "
            "A house says it when it wakes an agent; you may say it for your own agents. Kept in memory, never written "
            "as a fact."),
    _k("on", "do", "<module>", "stewards", "yes",
       help="on <module>: turn a module back on, with the grants its off took back. undo turns it off again."),
    _k("press", "see", "<id>", "anyone", "no",
       help="press <button>: run its does= line as you, exactly as a click would (press Feed, press dk41). What the "
            "line does is its own act, with its own receipt and undo."),
    _k("role", "do", "<id> leader|member|none in=<group>", "leaders", "yes",
       help="role <person> leader|member|none in=<group>: who leads a group and who belongs to it. Leaders appoint."),
]

# aspects no line may write with make or set: what the kernel itself keeps, or derives
RESERVED_KINDS = {"person", "agent", "module", "grant", "word", "invite", "world", "place", "group", "kit", "web-layout", "paint-report", "said"}
RESERVED_KINDS.add('file')
RESERVED = {"kind", "made_by", "for", "pinned", "forgotten", "sees", "lives", "from", "bound", "origin", "bundle",
            "made", "changed", "made_at", "changed_at", "steps_bound", "do_bound", "on_entry", "reviewed_code"}
SEES_SAID = {"me", "leaders", "group", "place"}      # what `make … sees=` may say (section 7: it may narrow)
from .blobs import PROTECTED
RESERVED.update(PROTECTED | {'pin_until', 'forget_reason'})
RESERVED.add('via_actor')
RESERVED.update({'outside', 'outside_not'})      # the kernel's answer to a module, never a fact (review, Low)
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
    if not st.target and not st.words:
        # `status` alone (28 Oct, seen in the desktop's refusals: "no module called (nothing) here")
        raise Refused(f"{st.word} <module>: say which module, like {st.word} house (rows module lists them)")
    if not m or k.state.get(m, "kind") not in ("module", "widget"):
        raise Refused(f"no module called {st.target or st.words} here (rows module lists them)")
    return m


def look(k, actor, st, entry, tx, group, saw=None):
    if not st.target and st.words:
        m = k.module_named(st.words.split()[0])
        if m:
            st.target = m
        else:
            raise Refused(k.needs_a_thing(actor, st, entry, st.text))    # look Lines: say which id
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
                    "rows": [dict(a, id=t, rev=k.state.rev.get(t,0))]}
        facts = [f"{x}={v}" for x, v in a.items() if x not in ("kind", "made_by", "for") and
                 not x.startswith(("in:", "member:", "claim:", "contact:"))]
        also = [f"{kd} ({why})" for kd, why in k.kinds.kinds_of(a, (k.groups_of(t) or [k.place])[0])[1:]]
        who = k.name(a.get("made_by")) if a.get("made_by") else None
        return {"text": f"{a.get('title') or k.name(t)} ({t}), a{'n' if str(kind)[:1] in 'aeiou' else ''} {kind}"
                        + (f" by {who}" if who else "") + (f"; also {', '.join(also[:4])}" if also else "")
                        + ("\n  " + "\n  ".join(facts) if facts else ""),
                "rows": [dict(a, id=t, rev=k.state.rev.get(t,0))]}
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
    """help, help <anything>, help all: kernel/helping.py (a short first screen; never a dead end)."""
    from . import helping
    if st.words:
        w = st.words.split()[0].lower()
        try:
            e = k.find_entry(w, group)
        except Refused:
            e = None
        if e is None:
            if w=='part-style':
                return dict(text='make kind=part-style lens=<lens> target=component.part[fact=value] color=... background=... radius=... padding=... gap=... glow=... lines=1..9 emphasis=normal|bold. Colour tokens or #rgb/#rgba/#rrggbb/#rrggbbaa. Spacing uses 1..4 measures (gap 1..2), including CSS shorthand padding. target=tokens defines colour/spacing and motion-<name> JSON tokens. Invalid writes refuse. personal-style applies just for me.')
            card = component_card(k, actor, w)
            if card: return card
        elif k.shown(actor.person, e) is None:
            raise k.no_such(e)
    out = helping.answer(k, actor, st.words, group)
    if out is not None:
        return out
    w = st.words.split()[0].lower()
    if w in FLOOR_HELP:
        return {"text": f"{FLOOR_HELP[w]}\n(this word's entry is missing; the kernel answers from its own floor)"}
    raise Refused(f"nothing here mentions '{w}'; " + helping.suggest(k, actor, w, group))


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
    _agent_origin(actor, tx, p)
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


STEERING = {'on', 'on_entry', 'do', 'do_bound', 'of_kind', 'by'}


def _rule_by(v):
    """A rule's by=: maker (its maker, their agents and its group's leaders; the default) or anyone."""
    v = str(v).strip().lower()
    if v not in ('maker', 'anyone'):
        raise Refused("a rule's by= is maker (you, your agents and your group's leaders: the default) or anyone "
                      "(everyone's acts, said on purpose)")
    return v


def rule_maker(k, actor, t):
    """Whether this actor is the rule's maker, or acts for the maker's person (Alex steers a rule his agent made)."""
    maker = k.state.get(t, 'made_by')
    person = k.state.get(maker, 'for') if k.state.get(maker, 'kind') == 'agent' else maker
    return maker in (actor.id, actor.person) or (person is not None and person == actor.person)


def undo(k, actor, st, entry, tx, group, saw=None):
    undone = k.undone()
    if st.target:
        seq = int(st.target[1:])
        if not 0 < seq <= len(k.log.records):
            raise Refused(f"no act r{seq} in this world's log")
        rec = k.log.records[seq - 1]
    else:
        # your latest act: not an undo, not what a rule did on its own (that goes back with the act that caused it)
        rec = next((r for r in reversed(k.log.records) if r.get("entry") and not r.get("undoes") and not r.get("rule")
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
    # the whole action (P3, Alex 27 Oct): what rules did because of it goes back with it, when that can go back
    caused = [r for r in k.log.records if r.get("caused_by") == seq and r["seq"] not in undone and not r.get("undoes")]
    left = [r for r in caused if r.get("external") or not _may_undo(k, actor, r)
            or k.state.get(r.get("entry"), "undo") in ("no", "external")]
    group_recs = sorted([r for r in caused if r not in left] + [rec], key=lambda r: -r["seq"])   # newest first
    seqs = {r["seq"] for r in group_recs}
    cur = {}                                  # (thing, aspect) -> (value, seq that set it), as the undo walks back

    def now(t, a):
        if (t, a) not in cur:
            cur[(t, a)] = (k.state.things.get(t, {}).get(a), k.state.last_seq(t, a))
        return cur[(t, a)]

    def prev_seq(t, a, s):
        return max([x for x, _ in k.state.history.get((t, a), []) if x < s] + [0])

    def settled(seqs_after):
        """Later writes that cancel out: acts since undone, and the undos that undid them."""
        return all(x in undone or x in seqs or k.log.records[x - 1].get("undoes") for x in seqs_after)

    writes = []
    left_off = set()
    for r in group_recs:
        facts = [f for part in r["parts"] for f in part["facts"]]
        for target in {f[0] for f in facts}:
            k.reaches(actor, 'undo', k.state.get(target, 'kind'), target=target,
                      fields=[f[1] for f in facts if f[0] == target],
                      group=(k.groups_of(target) or [k.place])[0])
        for f in reversed(facts):
            t, a = f[0], f[1]
            v = f[3] if len(f) > 3 else None
            value, last = now(t, a)
            later = [x for x, _ in k.state.history.get((t, a), []) if x > r["seq"]]
            same = (value is None) == (v is None) and (value is None or value == v)
            if not same or (last != r["seq"] and not settled(later)):
                raise Refused(f"r{seq} cannot be undone: {k.name(t)} {a.split(':')[0]} changed since (r{last})")
            back = k.state.before(t, a, r["seq"])
            cur[(t, a)] = (None if back is GONE else back, prev_seq(t, a, r["seq"]))
            writes.append((t, a, back))
            # a rule runs as its maker: someone else's undo may switch it off, never re-point it or switch it back on
            # (security review round 2: a steward's undo turned a member's rule back to an old `do`, as the member)
            if k.state.get(t, 'kind') == 'rule' and not rule_maker(k, actor, t) and (
                    a in STEERING or (a in ('off', 'forgotten') and (back is GONE or back in (None, ''))
                                      and not _own(k, actor, r))):
                left_off.add(t)       # undoing the maker's own forget is switching it on too (review M6)
        for t in {f[0] for f in facts if f[1] == "kind" and f[2] == "0"}:
            later = [s for (tt, _), hist in k.state.history.items() if tt == t for s, _ in hist
                     if s > r["seq"] and s not in seqs]
            if later and not settled(later):
                raise Refused(f"r{seq} cannot be undone: {k.name(t)} has changed since (r{max(later)}); undo that first")
    for t, a, back in writes:
        tx.set(t, a, back)
    for t in sorted(left_off):
        tx.set(t, 'off', 'yes')
    tx.extra["undoes"] = seq
    if len(group_recs) > 1:
        tx.extra["undoes_too"] = sorted(seqs - {seq})
    if rec.get("by") == "sealed":
        tx.extra["sealed_as"] = rec.get("seal")
    word = k.state.get(rec.get("entry"), "word") or "it"
    things = [t for p in rec["parts"] for t in [p.get("target")] if t] or \
             list(dict.fromkeys(f[0] for p in rec["parts"] for f in p["facts"]))
    what = ", ".join(str(k.state.get(t, "title") or k.state.get(t, "name") or k.state.get(t, "label") or t)
                     for t in things[:2])
    said = f"undid r{seq}: {word}" + (f" {what}" if what else "")
    if len(group_recs) > 1:
        n = len(group_recs) - 1
        said += f", and what {n} rule act{'' if n == 1 else 's'} did because of it"
    if left:
        said += f" (r{', r'.join(str(r['seq']) for r in left)} by rules cannot go back)"
    if left_off:
        said += (f"; {', '.join(sorted(left_off))} left switched off: a rule runs as its maker, so only they "
                 f"switch it back on")
    return {"text": f"{said} [r?]"}


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


def _agent_origin(actor, tx, target):
    """Keep verified agent attribution through reviewed module wrappers."""
    source=actor
    for _ in range(16):
        if source.kind=='agent':
            tx.set(target,'via_actor',source.id)
            return
        if source.caller is None:return
        source=source.caller


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
    write_values = dict(st.kv)
    if st.words and "text" not in write_values:
        write_values["text"] = st.words
    # Check before make's post compatibility path too: it must not bypass a
    # metadata-only grant by delegating to post.
    k.reaches(actor, "make", kind, fields=write_values, group=group)
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
    if sees is not None and sees not in SEES_SAID:
        raise Refused("sees= says me, leaders, group or place: who besides the kernel may see it")
    closed = None
    if kind == "chat" and kv.get("with"):
        from .chat import closed_sees
        closed = closed_sees(k, actor, kv)          # with="Alex, JEFF": only those people see it
    _writable(k, kv)
    _conditions(k, kv, group)
    if kind == "kind":
        k.kinds.validate_decl(actor, kv, group)         # needs and extends: readable, by leaders, no cycle (kinds.py)
    from painter.handles import validate_write
    validate_write(k, actor, kind, kv, tx)
    if kind == 'rule':
        from .dictionary import bind
        eid = k.find_entry(kv.get('on', ''), group)
        if not eid:
            raise Refused('a rule needs on=<published word>')
        kv['on_entry'] = eid
        kv['do_bound'] = bind(k, kv.get('do', ''), group)
        kv['by'] = _rule_by(kv.get('by') or 'maker')       # whose acts it hears (kernel._rule_hears)
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
    _agent_origin(actor, tx, t)
    if actor.id != actor.person:
        tx.set(t, "for", actor.person)
    tx.set(t, f"in:{group}", len(k.log.records) + 1)
    public = group == k.place or k.state.get(group, "open")         # an open group's work is seen by all
    if closed:
        tx.set(t, "sees", closed)
    elif sees == "me":
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
    return {"text": f"ok make {t} [r?] · a{'n' if kind[0] in 'aeiou' else ''} {kind}" + (f" in {k.name(group)}" if group != k.place else "")
                    + _make_notes(k, actor, kind, kv)
                    + (k.kinds.alike_note(actor, kv, group) if kind == "kind" else "")}


def _make_notes(k, actor, kind, kv):
    """What make does not recognise, said, never refused (P7, Alex 27 Oct): a kind nothing here shows or uses yet, and
    a setting the kind's other things never say, or say otherwise (bar=dock where buttons say bar=taskbar). Only for
    what a person or agent wrote: a module's own lines (window.open's make) are its business."""
    if actor.kind == "module":
        return ""
    others = [a for t, a in list(k.state.things.items()) if a.get("kind") == kind and not a.get("forgotten")
              and k.shown(actor.person, t) is not None]
    if not others:
        mentioned = any(kind in str(a.get(f, "")) for a in k.state.things.values()
                        if a.get("kind") in ("lens", "rule", "topic", "word") for f in ("text", "on", "of_kind", "do",
                                                                                        "words", "help", "takes"))
        return "" if mentioned else (f"\n~ {kind} is new here: no lens, rule or word mentions it yet, so it shows only "
                                     f"in look and rows (kinds lists the kinds there are)")
    notes = []
    for key, v in kv.items():
        if key in ("title", "name", "text", "label", "about") or v == "" or (
                kind == "kind" and key in ("needs", "extends", "value", "aliases", "has")):
            continue
        said = {str(a.get(key)) for a in others if a.get(key) not in (None, "")}
        if not said:
            notes.append(f"no other {kind} has {key}=")
        elif str(v) not in said and len(said) <= 4:
            notes.append(f"no other {kind} has {key}={v} (they say {' or '.join(sorted(said))})")
    return ("\n~ " + "; ".join(notes[:3]) + ": still made, as you said") if notes else ""


def set_(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, 'kind') == 'file-settings' and not k.is_steward(actor.person):
        raise Refused('file-settings belongs to stewards')
    k.reaches(actor, "set", k.state.get(t, "kind"), target=t, fields=st.kv, group=group)
    if k.state.get(t, "kind") == "said":
        from .chat import said_set
        said_set(k, actor, t, st.kv)                    # its speaker's acts only (chat.py)
    elif k.state.get(t, "kind") in RESERVED_KINDS:
        raise Refused(f"{t} is a {k.state.get(t, 'kind')}; set changes only things made with make")
    if not st.kv:
        raise Refused("set needs k=v: set <thing> label=Feed")
    # a thing that already spells this aspect another way, under a kind it fits: write what was said, and say so
    # (kinds.py). Not a refusal: spellings can be vocabularies (lane|status), and refusing blocked the House's
    # status=paused hold and advised a write that hid the card (trials 28 Oct); a silent rewrite would dodge grant
    # fields: and undo, and read a hidden aspect
    seen_as = k.shown(actor.person, t) or {}
    spelled = []
    for key, v in st.kv.items():
        if key in ("in", "as") or v == "":
            continue
        # a part with a kind (has="priority:number"): a value that isn't one is still set, and said (P7: said, never
        # refused), so a thing doesn't drift back into loose
        after_row = dict(seen_as, **{x: y for x, y in st.kv.items() if x not in ("in", "as")})
        pk, how = k.kinds.aspect_kind(after_row, key, (k.groups_of(t) or [k.place])[0])
        if pk is None and how and "isn't" in how and seen_as.get("kind") != "kind":
            spelled.append(f"\n~ {how}: still set, as you said")
        other = k.kinds.spelled_otherwise(seen_as, key, (k.groups_of(t) or [k.place])[0])
        if other:
            spelled.append(f"\n~ {seen_as.get('title') or k.name(t)} also says {other[0]}, which {'an' if other[1][:1] in 'aeiou' else 'a'} {other[1]} reads as "
                           f"{key}; set {t} {other[0]}= changes that one")
    if k.state.get(t, "kind") == "kind":
        k.kinds.validate_decl(actor, st.kv, (k.groups_of(t) or [k.place])[0], old=dict(k.state.things.get(t, {})), t=t)
    if all(str(k.state.get(t, a) if k.state.get(t, a) is not None else '') == str(v) for a, v in st.kv.items()):
        return {"text": f"{k.name(t)} already says {', '.join(f'{a}={v}' for a, v in st.kv.items())}; nothing changed"}
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
        # a rule runs as its maker, so what it does is the maker's to say: a leader may switch it off or forget it,
        # never re-point it (security review C1, 28 Oct: a steward set a member's rule to say into the member's DM, as
        # the member, and to publish the member's private upload)
        maker = k.state.get(t, 'made_by')
        steering = STEERING & set(st.kv)
        if steering and not rule_maker(k, actor, t):
            raise Refused(f"{t} is {k.name(maker)}'s rule and runs as them, so only they change what it does "
                          f"({', '.join(sorted(steering))}); set {t} off=yes switches it off, forget {t} removes it")
        if 'off' in st.kv and str(st.kv['off']) not in ('yes', 'True') and k.state.get(t, 'off') \
                and not rule_maker(k, actor, t):
            # switching off is moderation; switching on is acting as the maker (security review round 2)
            raise Refused(f"{t} is {k.name(maker)}'s rule and runs as them, so only they switch it back on; "
                          f"undo takes back your own off=yes")
        values = dict(st.kv)
        if 'by' in values:
            values['by'] = _rule_by(values['by'])     # by= with nothing is refused, never "everyone" (review, Low)
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
    return {"text": f"ok set {t} [r?] · " + ", ".join(f"{a}={v}" if v else f"{a} taken away" for a, v in st.kv.items())
                    + "".join(spelled)}


def forget(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    k.reaches(actor, "forget", k.state.get(t, "kind"), target=t, group=group)
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
    seats = int(a.get("seats", 1)) if str(a.get("seats", 1)).isdecimal() else 1
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
    choice = (st.words.split() or [""])[0]
    if choice not in options:
        matches=[option for option in options if option.casefold()==choice.casefold()]
        if len(matches)==1:choice=matches[0]
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
    if kind.startswith("nextsteps:"):
        from .next_steps import rows as next_rows, packet
        ref = kind.split(":", 1)[1]
        items = next_rows(k, actor, ref)
        return {"text": packet(items, ref), "rows": items}
    if (st.text.split() or [""])[0].lower() == "find" and "kind" not in st.kv and kind != "any" \
            and not (k.things(kind) or k.kinds.decl(kind, group) or k.kinds.is_open(kind, group)):
        return search(k, actor, st, entry, tx, group)      # find Seabright: no kind is called that, so words to search
    kv.pop("in", None)
    exact =str(kv.pop("exact", "")).casefold() in ("yes", "true")
    # a kind with a shape, or one another kind extends, also lists what has that shape (kinds.py), read under the
    # kind's names (start for a thing that says starts); exact=yes lists only things whose own kind is that word
    fitted = kind != "any" and not exact and k.kinds.is_open(kind, group)
    # a value kind lists what has one as a part: rows upvote lists everything with an upvote (kinds all the way down)
    by_part = kind != "any" and not exact and k.kinds.is_value(kind, group)
    fitted = fitted or by_part
    rows = []
    for t in (list(k.state.things) if kind == "any" or fitted else k.things(kind)):
        if t == "world":
            continue
        a = k.shown(actor.person, t)
        if a is None:
            continue
        why = k.kinds.fits(a, kind, group) if fitted else None
        if not why and by_part and a.get("kind") not in NOT_FITTED_KINDS:
            ps = k.kinds.parts_of(a, kind, (k.groups_of(t) or [group])[0])
            why = f"its {', '.join(ps)} {'is' if len(ps) == 1 else 'are'} {'an' if kind[:1] in 'aeiou' else 'a'} {kind}" if ps else None
        if fitted and not why:
            continue
        if fitted:
            a = k.kinds.filled(a, kind, group)
        if any(str(a.get(f, "")) != v for f, v in kv.items()):
            continue
        row = {x: v for x, v in a.items() if not x.startswith(("in:", "member:"))}
        if why and a.get("kind") != kind:
            row["as"] = why + (f"; {a['as']}" if a.get("as") else "")   # has title, start; a meeting, so an event
        row['groups'] = k.groups_of(t)
        if a.get("made_by"):
            row["by"] = k.name(a["made_by"])
        rows.append(dict(row, id=t, rev=k.state.rev.get(t, 0)))
    rows.sort(key=lambda r: (int(r["order"]) if str(r.get("order", "")).isdecimal() else 10 ** 9,
                             int(r["id"][len(k.tag):] or 0)))       # then in the order they were made
    for r in rows:
        k.mark(actor, r["id"], r)
    what = kind if kind != "any" else "thing"
    if not rows and kind != "any" and not kv and not k.things(kind) and not k.kinds.decl(kind, group):
        # rows refusals: nothing in the world is one, and "0 refusalses" read as an empty log (JEFF, 28 Oct)
        try:
            word = k.find_entry(kind, group)
        except Refused:
            word = None
        return {"text": f"nothing here is a {kind}" + (f"; {kind} is a word: say {kind}" if word else
                                                         "; kinds lists the kinds, rows any lists everything, "
                                                         f"search {st.words or kind} finds things by name or text"),
                "rows": []}
    text = "\n".join(f"  {r['id']} · {r.get('kind')} · "
                     f"{r.get('title') or r.get('name') or r.get('word') or r.get('label') or (r.get('text') or '')[:60]}"
                     + (f" ({r['as']})" if r.get("as") else "")
                     for r in rows)
    plural = what if len(rows) == 1 else what + ("es" if what.endswith(("s", "x", "ch", "sh")) else "s")
    if not rows and kv:
        # a filter compares a fact exactly; say so, rather than a bare 0 that reads like "there are none"
        return {"text": f"0 {plural}: none you can see has " + " and ".join(f"{f}={v}" for f, v in kv.items())
                        + f"; rows {kind} alone lists them all", "rows": rows}
    return {"text": f"{len(rows)} {plural}" + ("\n" + text if rows else ""), "rows": rows}


SEARCH_TITLE = ("title", "name", "label", "word")
SEARCH_TEXT = ("text", "help", "goal", "acceptance", "next_action", "description", "about", "summary", "body")
SEARCH_DONE = {"done", "closed", "cancelled", "canceled", "archived", "finished"}


def _open_rank(a):
    """0 for work in Now, 1 for anything not finished, 2 for done (its lane, status or state says so)."""
    said = {str(a.get(f, "")).casefold() for f in ("lane", "status", "state")}
    if said & SEARCH_DONE or str(a.get("done", "")).casefold() in ("yes", "true"):
        return 2
    return 0 if "now" in said else 1


def _snippet(text, terms, width=90):
    """The text around the first word searched for, on one line."""
    text = " ".join(str(text).split())
    low = text.casefold()
    at = min((low.find(w) for w in terms if w in low), default=0)
    start = max(0, at - width // 3)
    return ("…" if start else "") + text[start:start + width] + ("…" if start + width < len(text) else "")


def search(k, actor, st, entry, tx, group, saw=None):
    """search <words> [limit=] [kind=] (or find <words>): every thing the asker may see whose name, title or text
    holds all the words, any case; title matches first, then open work above done, then newest (dk1322, 28 Oct:
    'search Seabright' resolved Seabright as the map and refused). The words never resolve to a thing."""
    kv = dict(st.kv)
    query = " ".join(x for x in (kv.pop("q", ""), st.target or "", st.words) if x).strip()
    terms = query.casefold().replace('"', " ").split()
    if not terms:
        raise Refused("search needs words: search <words> [limit=12], e.g. search Seabright")
    try:
        limit = max(1, int(kv.pop("limit", 12)))
    except ValueError:
        raise Refused("limit= is a number: search <words> limit=20")
    want = str(kv.pop("kind", "")).casefold()
    phrase = " ".join(terms)

    def visible(t):
        a = k.shown(actor.person, t) if t != "world" else None
        if a is None or a.get("forgotten") or (a.get("kind") == "word" and a.get("status") == "hidden"):
            return None
        kind = str(a.get("kind") or "thing").casefold()
        return None if want and kind != want and not kind.endswith("-" + want) else a

    def called(t, a):
        return str(a.get("title") or a.get("label") or a.get("name") or a.get("word") or k.name(t))

    found, shows = {}, {}
    for t in list(k.state.things):
        a = visible(t)
        if a is None:
            continue
        # seabright-board-button reads as words too
        title = " ".join(str(a[f]) for f in SEARCH_TITLE if a.get(f)).casefold().replace("-", " ").replace("_", " ")
        body = " ".join(str(a[f]) for f in SEARCH_TEXT if a.get(f))
        low, kind = body.casefold(), str(a.get("kind", "")).replace("-", " ")      # Seabright map: the map
        if not all(w in title or w in low or w in kind for w in terms):
            continue
        rank = 0 if phrase in title else 1 if all(w in title or w in kind for w in terms) else 2 if any(
            w in title for w in terms) else 4
        found[t] = (rank, a, _snippet(body, terms) if body else "")
        if rank < 4 and a.get("kind") in ("lens", "widget"):
            # what a matching view shows is part of it: the Seabright board's lens reads rows board-channel, and its
            # channels' own titles never say Seabright (Announcements, Asks & offers)
            for kd in re.findall(r'reading:"rows ([a-z][a-z0-9-]*)', str(a.get("text", ""))):
                if kd != "kind":
                    shows.setdefault(kd, called(t, a))
    for kd, view in shows.items():
        for t in k.things(kd):
            a = visible(t)
            if t not in found and a is not None and (a.get("title") or a.get("name") or a.get("label")):
                found[t] = (3, a, f"shown in {view}")
    order = []
    for t, (rank, a, snip) in found.items():
        opened, num = _open_rank(a), t[len(k.tag):]
        order.append(((opened == 2, rank, opened, -int(num) if num.isdecimal() else 0), t, rank, a, snip))
    order.sort(key=lambda x: x[0])
    found = order
    rows = []
    for _, t, rank, a, snip in found[:limit]:
        row = {"id": t, "kind": str(a.get("kind") or "thing"), "name": called(t, a), "rev": k.state.rev.get(t, 0),
               "match": "title" if rank < 3 else "part" if rank == 3 else "text", "snippet": snip}
        row.update({f: a[f] for f in ("lane", "status") if a.get(f)})
        rows.append(row)
    if not rows:
        return {"text": f"nothing you can see has {query!r} in its name, title or text"
                        + (f" (of kind {want})" if want else "") + "; rows any lists everything", "rows": []}
    head = f"{len(found)} thing{'s' if len(found) != 1 else ''} with {query!r}" + (
        f" (the first {len(rows)}; limit={len(found)} shows all)" if len(found) > len(rows) else "")
    lines = [f"  {r['id']} · {r['kind']} · {r['name'][:70]}" + (f" [{r['lane']}]" if r.get("lane") else "")
             + (f" — {r['snippet']}" if r["snippet"] else "") for r in rows]
    return {"text": head + "\n" + "\n".join(lines), "rows": rows}


VERB_NAME = re.compile(r"^[a-z][a-z0-9-]{0,31}(\.[a-z][a-z0-9-]{0,31})?$")      # word or family.word


def verb(k, actor, st, entry, tx, group, saw=None):
    """verb <word> steps=… help=…: a verb note, its own entry (from=verb) living in the line's group."""
    kv = dict(st.kv)
    w = (st.words.split() or [""])[0].lower()
    if not VERB_NAME.match(w):
        raise Refused("verb needs a word: verb <word> steps=\"<lines>\" help=\"…\" (a family word is family.word)")
    if k.namespace_owner(w):
        raise Refused(f"{w.split('.')[0]}.* belongs to the {k.namespace_owner(w)} module; choose another family")
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
    # a verb that says its shape takes a thing first (rsvp.go <event>), so the check sees what it acts on
    takes = kv.get("takes") or ("<id> [<words>]" if kv.get("acts_on") or kv.get("needs") else "[<words>]")
    for a, v in [("kind", "word"), ("word", w), ("word_kind", wk), ("takes", takes),
                 ("help", help_), ("may", may), ("undo", "yes" if wk == "do" else "no"), ("from", "verb"),
                 ("bound", w), ("steps", steps), ("lives", group), ("made_by", actor.id)]:
        tx.set(e, a, v)
    for key in ("once", "sealed", "fence"):
        if kv.get(key):
            tx.set(e, key, kv[key])
    from .kinds import KIND_NAME
    if kv.get("acts_on"):
        tx.set(e, "acts_on", k.kinds.check_acts_on(kv["acts_on"], group))   # the kind its steps act on (kinds.py)
    if kv.get("needs"):
        tx.set(e, "needs", k.kinds.check_shape_text(kv["needs"]))
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
    if not st.target:
        from .readings import own_history
        return own_history(k, actor)
    rows = k.trail(actor.person, st.target)
    k.mark(actor, st.target, k.shown(actor.person, st.target))
    return {'text': '\n'.join(f"{r['record']} · {r['at']} · {r['by']} · {r['word']} · {r['changes']}" for r in rows),
            'rows': rows}


from .dictionary import word_set, word_rename, language
from .kits import kit, take, rename, module, grant
from .inpage import widget
from .blobs import upload, attach, file_result, file_read
from .world_words import dictionary_copy, group_word, clock, forgotten
from .readings import who, recent, kinds, on, press
from .refusals import refusals, failed
from .kinds import mark, words_for, alike_word, aspects_word, NOT_FITTED as NOT_FITTED_KINDS
from .bonds import turn                  # the graph's readings (around, nearby, preview) are held (28 Oct)
from .chat import say, receive as chat_receive, chat as chat_word, closed_sees
from .store import GONE
from .next_steps import change as task_change
from .card_signals import signal as card_signal
from painter.arrangement import component, look_view, components, component_card
from painter.health import component_health, component_action, personal_view, personal_style, paint_clear

KERNEL = {"kit": kit, "take": take, "rename": rename, "module": module, "grant": grant, "widget": widget, "describe": describe,
          "task.signal": card_signal,
          **{"task-" + action: task_change for action in ("next", "revise", "review", "verify", "followup")},
          'upload': upload, 'attach': attach, 'file-result': file_result, 'file-read': file_read,
          'dictionary-copy': dictionary_copy, 'group': group_word, 'clock': clock, 'forgotten': forgotten,
          'component': component, 'look-view': look_view, 'components': components,
          'component-health': component_health, 'component-action': component_action, 'paint-clear': paint_clear,
          'personal-view': personal_view, 'personal-style': personal_style,
          'word-set': word_set, 'word-rename': word_rename, 'history': history, 'rule': rule,
          'language': language,
          **{w: panes if w == "panes" else arrange for w in PANE_HELP},
          "counts": counts, "test": test, "look": look, "help": help_, "post": post, "like": like, "pin": pin, "undo": undo, "off": off,
          "status": status, "make": make, "set": set_, "forget": forget, "holds": holds, "claim": claim,
          "vote": vote, "role": role, "rows": rows, "find": rows, "search": search, "verb": verb,
          "who": who, "recent": recent, "kinds": kinds, "on": on, "press": press, "say": say, "chat": chat_word,
          "refusals": refusals, "failed": failed, "mark": mark, "actions": words_for, "turn": turn,
          "chat.receive": chat_receive, "alike": alike_word, "aspects": aspects_word}
