"""The universal conversation (a6638; Alex, 20 Oct: 'I need to be able to have a conversation about it when I pull it
up ... I should be able to make comments and they go right into this chat. Going forward this chat is the universal
chat. If I'm commenting on a document in the middle, those comments can get routed to the right person, but I talk
here.'). The world half, kept as files so it can be read, tried on a copy and applied after the source half lands
(scene.py: a line in a Talk is about its document, a reply about what it answers; house.py: a called agent hears what
a line points at).

    python research/window-lab/universal-chat/apply.py lines <out.desk>    the lines (explore.py <world> --as <you> < out.desk)
    python research/window-lab/universal-chat/apply.py undo <out.desk>     lines that put every passage back
    python research/window-lab/universal-chat/apply.py check [--world frontier] [--port 8794]
                                       every old= passage against the world's text now (each must stand once); sends nothing
    python research/window-lab/universal-chat/apply.py door [--as <name>] [--world frontier] [--port 8794]
                                       check, then all of it through the door, line by line, stopping at a refusal;
                                       first it saves the live text of every note it changes under saved/<stamp>/
    python research/window-lab/universal-chat/apply.py restore <saved dir> [--as <name>]   puts those texts back

What it changes, all world data anyone may change again:
  - jeff-chat (the Conversation in the home base): the feed shows everything said to or by Alex (a 'Just JEFF' tab
    keeps the old one); 'About <name>' at its top while something is open in the middle, and a line typed then goes to
    JEFF with about=<it>; a line about something shows the words it quotes, 'about <name>' and, on Alex's own lines,
    who it was sent to and where it is kept; Answer on a line from a Talk or a comment answers there; while words are
    held in a document (Alex's writer note view=conversation), the composer is the comment box: the comment is stored
    once, in the document's Talk, to its author, else its owner, else JEFF;
  - doc-page: a third view 'talk in the Conversation' that hides its own Talk pane and comment box and says where to
    write; a new Talk calls the author, else the owner, else JEFF;
  - home-style: the roles those parts paint with;
  - the Writing room's verb review (a4033) gains a second form, `review <thing> for <who> with "<one line>"`: it
    writes brief= for= sent_by= and tags the thing ready-for-review (review <document> alone does what it did);
  - Alex's writer note (role=writer actor=alex): view=conversation."""
import json
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent

JEFF_CHAT = "a5210"
DOC_PAGE = '"doc-page"'
STYLE = "a5206"
CONV = "a5080"

# --- jeff-chat ---------------------------------------------------------------------------------------------------
TABS_OLD = '''    tabs : row
      role tabs
      mine : text "JEFF"
        role tab
        role tab.on when $draft.view != "all"
        on click do prop $draft view=jeff
      all : text "Everything"
        role tab
        role tab.on when $draft.view = "all"
        on click do prop $draft view=all
'''
TABS_NEW = '''    tabs : row
      role tabs
      all : text "All"
        role tab
        role tab.on when ($draft.view or "") != "jeff-only"
        on click when ($draft.view or "") = "jeff-only" do prop $draft view=all
      mine : text "Just JEFF"
        role tab
        role tab.on when ($draft.view or "") = "jeff-only"
        on click when ($draft.view or "") != "jeff-only" do prop $draft view=jeff-only
  about : column
    of prop:role=home-view,prop:actor=$me as v
    each abouting
'''
FEED_OLD = '''    role feed
    only when $draft.view != "all"
    of sayings in:a5080 as s
'''
FEED_NEW = '''    role feed
    only when ($draft.view or "") = "jeff-only"
    of sayings in:a5080 as s
'''
ALL_OLD = '''    role feed
    only when $draft.view = "all"
    of sayings involving:alex as s
'''
ALL_NEW = '''    role feed
    only when ($draft.view or "") != "jeff-only"
    of sayings involving:alex as s
'''
DOCK_OLD = '''  dock : column
    role dock
    answering : row
      role answering
      only when ($draft.reply_to or "") != ""
      q : text "Answering: $draft.quote"
        role meta
        clamp 1
        share 1
      x : text "×"
        role tool
        on click do prop $draft reply_to="" quote=""
    to : row
      role to
'''
DOCK_NEW = '''  dock : column
    role dock
    let vopen = (max($viewing of prop:role=home-view,prop:actor=$me) or "")
    let about = vopen when vopen != "" and vopen != "a5080" and vopen != ($draft.unabout or "")
    let about = "" otherwise
    let wview = (max($view of prop:role=writer,prop:actor=$me) or "")
    let qin = (max($quote_in of prop:role=writer,prop:actor=$me) or "")
    let qwords = (max($quote of prop:role=writer,prop:actor=$me) or "")
    let wopen = (max($open of prop:role=writer,prop:actor=$me) or "")
    let held = qwords when wview = "conversation" and qin != "" and qwords != "" and (qin = vopen or qin = wopen)
    let held = "" otherwise
    let elsewhere = "yes" when ($draft.reply_to or "") != "" and ($draft.reply_in or "") != "" and $draft.reply_in != "a5080"
    let elsewhere = "no" otherwise
    answering : row
      role answering
      only when ($draft.reply_to or "") != "" or ($draft.reply_thread or "") != ""
      q : text "Answering: $draft.quote"
        role meta
        clamp 1
        share 1
      in : text "in $draft.reply_in"
        role meta
        clamp 1
        only when elsewhere = "yes" or ($draft.reply_thread or "") != ""
      x : text "×"
        role tool
        on click do prop $draft reply_to="" quote="" reply_in="" reply_thread="" reply_kind=""
    commenting : column
      role commenting
      only when held != ""
      the prop:role=writer,prop:actor=$me as w
      on : column
        the $w.quote_in as d
        let talk = ($d.talk or "")
        let isnote = "yes" when $d.kind = "note"
        let isnote = "no" otherwise
        let pointing = ($w.quoting or $d.item)
        let ptext = join($text of $w.quoting) when isnote = "no"
        let ptext = "" otherwise
        let around = $d.text when isnote = "yes"
        let around = ptext otherwise
        let wbefore = (words-before(around, held) or "")
        let wafter = (words-after(around, held) or "")
        let wheading = (section-of($d.text, held) or "") when isnote = "yes"
        let wheading = "" otherwise
        let route = $d.author when ($d.author or "") != "" and $d.author != $me
        let route = $d.owner when ($d.owner or "") != "" and $d.owner != $me
        let route = "jeff" otherwise
        let rules = "A conversation about this document between Alex and its author; anyone may be called in with @name. Keep each message short: one point. If you took his point, change the document and say so in one line with mark=folded. Ask only what you need from him, with mark=ask. To point at a passage: do append <this chat> line=<your words> about=<the document or its paragraph> quote=<its words>."
        what : row
          role answering
          k : text "Comment on"
            role meta
          q : text "“$(held)”"
            role meta
            clamp 2
            share 1
          x : text "×"
            role tool
            on click do read $w; do prop $w quote="" quoting="" quote_in=""
        where : row
          role tagline
          in : text "in $d.item"
            role meta
            clamp 1
          new : text "· goes to $(route), kept in its Talk"
            role receipt
            only when talk = ""
          old : text "· goes to the people of its Talk"
            role receipt
            only when talk != ""
        say : text ""
          role input
          hint "Your comment on these words…"
          lines 1..12
          commit explicit
          on edit when talk != "" do append $d.talk line="$value" about=$(pointing) quote="$(held)" words_before="$(wbefore)" words_after="$(wafter)" heading="$(wheading)"; read $w; do prop $w quote="" quoting="" quote_in=""
          on edit when talk = "" do look f3402; do create f3402 kind=chat title="Talk: $d.title" talk_of=$d.item with="$me,$(route)" describe="$(rules)"; read $d.item; do prop $d.item talk=$new; do append $new line="$value" about=$(pointing) quote="$(held)" words_before="$(wbefore)" words_after="$(wafter)" heading="$(wheading)"; read $w; do prop $w quote="" quoting="" quote_in=""
    to : row
      role to
      only when held = "" and elsewhere = "no" and ($draft.reply_thread or "") = ""
'''
ATTACH_OLD = '''    attachments : column
      of captures $draft.context
      each attachment
    say : text ""
      role input
      hint "Write to JEFF, or anyone above…"
      lines 1..12
      commit explicit
      on edit do append a5080 line="$value" default_to="$draft.to" captures="$draft.context" context_from="$draft" reply_to="$draft.reply_to"
    help : text "Enter sends · Shift+Enter for a new line · @name to send to someone else · Ctrl+Alt drag to show JEFF something"
      role hint
'''
ATTACH_NEW = '''    attachments : column
      only when held = ""
      of captures $draft.context
      each attachment
    say : text ""
      role input
      only when held = ""
      hint "Write to JEFF, or anyone above…"
      lines 1..12
      commit explicit
      on edit when elsewhere = "no" and ($draft.reply_thread or "") = "" do append a5080 line="$value" default_to="$draft.to" captures="$draft.context" context_from="$draft" reply_to="$draft.reply_to" about="$(about)"
      on edit when elsewhere = "yes" do append $draft.reply_in line="$value" reply_to="$draft.reply_to"; read $draft; do prop $draft reply_to="" quote="" reply_in="" reply_kind=""
      on edit when ($draft.reply_thread or "") != "" do comment $draft.reply_in id=$draft.reply_thread line="$value"; read $draft; do prop $draft reply_thread="" quote="" reply_in="" reply_kind=""
    help : text "Enter sends · Shift+Enter for a new line · @name to send to someone else · Ctrl+Alt drag to show JEFF something"
      role hint
      only when held = ""
    helpc : text "Enter sends your comment to the document's Talk · it shows here, with who it went to · × goes back to talking to JEFF"
      role hint
      only when held != ""
'''
QUOTE_OLD = '''    role bubble.jeff when $s.name = "jeff"
    body : text "$s.said"
'''
QUOTE_NEW = '''    role bubble.jeff when $s.name = "jeff"
    quoted : text "“$s.quote”"
      role chatquote
      clamp 3
      only when ($s.quote or "") != ""
    body : text "$s.said"
'''
ACTS_OLD = '''  acts : row
    role acts
    answer : text "Answer"
      role tool
      on click do prop $draft reply_to=$s.line quote="$s.said"
'''
ACTS_NEW = '''  tagline : row
    role tagline
    only when ($s.about or "") != "" or ($s.name = "alex" and $s.item != "a5080")
    k : text "about"
      role meta
      only when ($s.about or "") != ""
    what : text "$s.about"
      role aboutname
      clamp 1
      only when ($s.about or "") != ""
    sent : text "sent to $s.to"
      role receipt
      only when $s.name = "alex" and ($s.to or "") != ""
    nobody : text "sent to no one: say @name to call someone"
      role receipt
      only when $s.name = "alex" and ($s.to or "") = ""
  acts : row
    role acts
    answer : text "Answer"
      role tool
      on click when $s.what = "line" do prop $draft reply_to=$s.line quote="$s.said" reply_in=$s.item reply_kind=line reply_thread=""
      on click when $s.what != "line" do prop $draft reply_thread=$s.thread quote="$s.said" reply_in=$s.item reply_kind=$s.what reply_to=""
'''
ABOUTING = '''abouting : column
  let open = $v.viewing when ($v.viewing or "") != "" and $v.viewing != "a5080"
  let open = "" otherwise
  on : row
    role abouthead
    only when open != "" and open != ($draft.unabout or "")
    k : text "About"
      role aboutkey
    what : text "$v.viewing"
      role aboutname
      clamp 1
      share 1
    note : text "what you write goes with it"
      role meta
    x : text "×"
      role tool
      tip "Not about it" "Your lines stop carrying what is open in the middle, until you open something else"
      on click when ($draft.unabout or "") != $v.viewing do prop $draft unabout=$v.viewing
  off : row
    role tagline
    only when open != "" and open = ($draft.unabout or "")
    k : text "Not about what is open"
      role meta
      share 1
    back : text "About it again"
      role tool
      on click when ($draft.unabout or "") != "" do prop $draft unabout=""
'''

# --- doc-page ----------------------------------------------------------------------------------------------------
DP_WITH_OLD = '''  let withwho = $d.author when ($d.author or "") != "" and $d.author != $me
  let withwho = "" otherwise
'''
DP_WITH_NEW = '''  let withwho = $d.author when ($d.author or "") != "" and $d.author != $me
  let withwho = $d.owner when ($d.owner or "") != "" and $d.owner != $me
  let withwho = "jeff" otherwise
'''
DP_TABS_OLD = '''    v1 : text "talk beside"
      role viewtab
      role viewtab.on when ($w.view or "") != "margins"
      on click when ($w.view or "") = "margins" do read $w; do prop $w view=talk
    v2 : text "margin notes only"
      role viewtab
      role viewtab.on when ($w.view or "") = "margins"
      on click when ($w.view or "") != "margins" do read $w; do prop $w view=margins
'''
DP_TABS_NEW = '''    v1 : text "talk beside"
      role viewtab
      role viewtab.on when ($w.view or "") != "margins" and ($w.view or "") != "conversation"
      on click when ($w.view or "") = "margins" or ($w.view or "") = "conversation" do read $w; do prop $w view=talk
    v2 : text "margin notes only"
      role viewtab
      role viewtab.on when ($w.view or "") = "margins"
      on click when ($w.view or "") != "margins" do read $w; do prop $w view=margins
    v3 : text "talk in the Conversation"
      role viewtab
      role viewtab.on when ($w.view or "") = "conversation"
      on click when ($w.view or "") != "conversation" do read $w; do prop $w view=conversation
'''
DP_PENDING_OLD = '''      pending : column
        role pending
        only when held != ""
'''
DP_PENDING_NEW = '''      elsewhere : text "Write your comment on “$(held)” in the Conversation: it is kept in this document's Talk, and goes to $(withwho)."
        role pending
        clamp 3
        only when held != "" and ($w.view or "") = "conversation"
      pending : column
        role pending
        only when held != "" and ($w.view or "") != "conversation"
'''
DP_TALK_OLD = '''      role talkpane
      only when ($w.view or "") != "margins"
'''
DP_TALK_NEW = '''      role talkpane
      only when ($w.view or "") != "margins" and ($w.view or "") != "conversation"
'''

# --- home-style --------------------------------------------------------------------------------------------------
STYLE_OLD = "role attachthumb : corner gap /2, width gap x14\n"
STYLE_NEW = STYLE_OLD + (HERE / "roles.style").read_text(encoding="utf-8")

# the Writing room's verb review (a4033) gains a second form, by guards on $2, so the one word does both
VERB = "a4033"
VERB_OLD = ("# review <document>: make it the design you are reviewing (kept on your own review desk as reviewing=, so each "
            "person has their own)\ndo prop prop:role=reviewer,prop:actor=$me reviewing=$1")
VERB_NEW = (HERE / "review.verb").read_text(encoding="utf-8").rstrip("\n")

REPLACES = [
    (JEFF_CHAT, TABS_OLD, TABS_NEW), (JEFF_CHAT, FEED_OLD, FEED_NEW), (JEFF_CHAT, ALL_OLD, ALL_NEW),
    (JEFF_CHAT, DOCK_OLD, DOCK_NEW), (JEFF_CHAT, ATTACH_OLD, ATTACH_NEW), (JEFF_CHAT, QUOTE_OLD, QUOTE_NEW),
    (JEFF_CHAT, ACTS_OLD, ACTS_NEW),
    (DOC_PAGE, DP_WITH_OLD, DP_WITH_NEW), (DOC_PAGE, DP_TABS_OLD, DP_TABS_NEW), (DOC_PAGE, DP_PENDING_OLD, DP_PENDING_NEW),
    (DOC_PAGE, DP_TALK_OLD, DP_TALK_NEW), (VERB, VERB_OLD, VERB_NEW),
]
# the instance part a new passage names goes at the end of jeff-chat (after its last line, attachment's Remove)
TAIL_OLD = '''    on click do prop $draft context="$remaining"
'''


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def lines():
    out = [f"read {STYLE} :3", f"do replace {STYLE} old={q(STYLE_OLD)} new={q(STYLE_NEW)}"]
    for note in (JEFF_CHAT, DOC_PAGE, VERB):
        out.append(f"read {note} :3")
        if note == JEFF_CHAT:
            # the instance first, so every passage after it compiles against a part that exists
            out.append(f"do replace {note} old={q(TAIL_OLD)} new={q(TAIL_OLD + ABOUTING)}")
        out += [f"do replace {note} old={q(o)} new={q(n)}" for n_, o, n in REPLACES if n_ == note]
    out += ['do prop prop:role=writer,prop:actor=alex view=conversation']
    return out


def undo():
    out = []
    for note in (VERB, DOC_PAGE, JEFF_CHAT):
        out.append(f"read {note} :3")
        out += [f"do replace {note} old={q(n)} new={q(o)}" for n_, o, n in reversed(REPLACES) if n_ == note]
        if note == JEFF_CHAT:
            out.append(f"do replace {note} old={q(TAIL_OLD + ABOUTING)} new={q(TAIL_OLD)}")
    out += [f"read {STYLE} :3", f"do replace {STYLE} old={q(STYLE_NEW)} new={q(STYLE_OLD)}",
            "do prop prop:role=writer,prop:actor=alex view=margins"]
    return out


def door(line, who, port, world):
    body = json.dumps({"session": world, "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def body(said):
    """The text of a note from `read <id> :3` as the door prints it: between the first --- line and the next."""
    ls = said.splitlines()
    i = ls.index("---")
    j = ls.index("---", i + 1)
    return "\n".join(ls[i + 1:j]) + "\n"


def check(who, port, world, read=None):
    """Every old= passage against the note's text now: each must stand there exactly once. -> how many do not."""
    read = read or (lambda note: body(door(f"read {note} :3", who, port, world)))
    texts = {n: read(n) for n in (JEFF_CHAT, DOC_PAGE, STYLE, VERB)}
    bad = 0
    for note, old in [(STYLE, STYLE_OLD), (JEFF_CHAT, TAIL_OLD)] + [(n, o) for n, o, _ in REPLACES]:
        k = texts[note].count(old)
        print(f"{note}: old= stands {k} time(s): {old.strip().splitlines()[0][:70]!r}")
        bad += k != 1
    return bad


def restore(saved, who, port, world):
    """One step back: every saved note text rewritten as it was (whatever was edited since in those notes goes too:
    read them first), and Alex's writer view as it was."""
    for f in sorted(saved.glob("*.txt")):
        note = f.stem if f.stem.startswith("a") else f'"{f.stem}"'
        door(f"read {note} :3", who, port, world)
        said = door(f"do rewrite {note} text={q(f.read_text(encoding='utf-8').rstrip(chr(10)))}", who, port, world)
        print(f"{note}: {said.splitlines()[0][:160] if said else '(no answer)'}")
    w = json.loads((saved / "writer.json").read_text(encoding="utf-8"))
    if w.get("id"):
        door(f"read {w['id']}", who, port, world)
        print(door(f"do prop {w['id']} view={w['view'] or 'margins'}", who, port, world).splitlines()[0])
    return 0


def main(argv):
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    if not argv or argv[0] not in ("lines", "undo", "check", "door", "restore"):
        print(__doc__)
        return 0
    if argv[0] in ("lines", "undo"):
        out = lines() if argv[0] == "lines" else undo()
        pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"wrote {len(out)} lines to {argv[1]}")
        return 0
    who, port, world = opt("--as", "worker-a6638"), opt("--port", "8794"), opt("--world", "frontier")
    if argv[0] == "restore":
        return restore(pathlib.Path(argv[1]), who, port, world)
    if check(who, port, world):
        print("stopped: a passage does not stand once; nothing was sent")
        return 1
    if argv[0] == "check":
        return 0
    # before the first write: the live text of every note it changes, and Alex's writer view, under saved/<stamp>/
    import time
    saved = HERE / "saved" / time.strftime("%Y%m%d-%H%M%S")
    saved.mkdir(parents=True)
    for note in (STYLE, JEFF_CHAT, DOC_PAGE, VERB):
        (saved / f"{note.strip(chr(34))}.txt").write_text(body(door(f"read {note} :3", who, port, world)), encoding="utf-8")
    w = door("find prop:role=writer,prop:actor=alex", who, port, world)
    wid = next((x.split()[0] for x in w.splitlines() if x.strip().startswith("a") and "role=writer" in x), "")
    wview = next((x.split("view=")[1].split()[0] for x in w.splitlines() if "role=writer" in x and "view=" in x), "")
    (saved / "writer.json").write_text(json.dumps({"id": wid, "view": wview}), encoding="utf-8")
    print(f"saved: {saved} (restore: python research/window-lab/universal-chat/apply.py restore {saved.relative_to(HERE.parents[2]).as_posix()})")
    for line in lines():
        said = door(line, who, port, world)
        print(said[:300])
        bad = [x for x in said.splitlines() if x.startswith(("ERR", "MISS")) or x.startswith("~ ! lens")]
        if bad:
            print("stopped: the line above was refused or left a lens not compiling:", bad[:2])
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
