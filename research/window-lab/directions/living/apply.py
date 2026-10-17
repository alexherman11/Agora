"""apply: LAMPLIT, the HUD sprint's lane 3 (a6057), put into a world: the look and the living parts, nothing else.
OWNER: worker-a6057, 17 Oct (round 3). Lanes 1 (board) and 2 (desk) have their own apply; the desk lane (a5994)
assembles the three in one pass.

    python research/window-lab/directions/living/apply.py check [--world try|live] [--chat]
        read only: what it would change, every passage it would replace found as it expects, the style it would write,
        and lint (below). Prints the plan; writes nothing anywhere.
    python research/window-lab/directions/living/apply.py lint [--world try|live]
        the style it would write, against THE RULE (lamplit.overrides, top): roles using a colour outside the rule,
        tokens outside it, and any role a lens in the Home base room uses that the style lacks (that one is an error).
    python research/window-lab/directions/living/apply.py lines <out.desk> [--world try|live] [--chat]
        the desk lines, for explore.py or hud_playtest.py --apply (made against that world: they say rewrite where a
        note of that title exists there, create where it does not)
    python research/window-lab/directions/living/apply.py undo-lines <out.desk> [--world live]
        the lines that would put that world back as it is now after an apply: a baseline for a copy that has LAMPLIT
        (hud_playtest.py --apply <out.desk> plays today's HUD on it, to compare)
    python research/window-lab/directions/living/apply.py try [--chat]       into frontier-try (a copy), via explore.py
    python research/window-lab/directions/living/apply.py door [--as <who>] [--chat]
        into the LIVE world through the keeper's door, one command a request, stopping at the first refusal. Before any
        write it saves, under saved/<when>/ beside this file: every text it replaces (home-style, home-notices, and
        jeff-chat with --chat), the props and tags it changes, and undo.desk, the lines that put them back.
    python research/window-lab/directions/living/apply.py undo <saved dir> [--as <who>]     undo.desk through the door

What it does, in order (a style's roles before the lenses that use them, so nothing is ever uncompiled):
  1. home-style (a5206) is rewritten as ONE flat style: the live text as read at that moment, then a5988's wf* roles
     it lacks (home-feed/feed.style), then lamplit.overrides; each name stands where it first stood with the words of
     its last definition, so it is a superset of what it replaces. Lane 1's marked nb* block is kept as it stands
     (this lane never writes nb* roles). Run twice, it gives the same text.
ORDER, when the three lanes go live together (agreed on the table a6049): lane 2's tiling and a5988's feed half first,
then lane 1's board apply, then this one (it reads home-style as they left it). This lane needs lane 2's tiling for a
glance number to fill the room (full=) and a5988's home-feed lens for a press in The house to show a feed.
  2. lenses, each a note in Home base (f5204), style=home-style: home-glance (widget, order 1), home-timer-bar (widget,
     order 3), home-timer, home-house, home-house-small; home-notices (a5530's widget) is rewritten with this lane's.
  3. widgets: home-clock, home-now and home-pomodoro lose their `widget` tag (the glance holds the time; Now and the
     timer are in The house, and the timer comes up in the bar whenever The house is not showing).
  4. Alex's At work panel (lens=home-work) shows home-house, lesser=home-house-small, and is called The house.
  5. glance tags on Alex's panels: glance-you on Waiting on you (lens=waiting-on-me), glance-work on The house,
     glance-board on The board (lens=home-board, or lane 1's direction-board-inbox). Lane 1's apply moves glance-you to
     The board when its inbox replaces Waiting on you.
  6. only with --chat: jeff-chat's typing row names only the one being written to (not this lane's lens; JEFF's word).
"""
import datetime
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
WL = HERE.parents[1]
LAB = WL.parent / "text-desk-lab" / "notation"
ROOM = "f5204"
DOOR = "http://127.0.0.1:8794/api/do"
# a5988's feed roles where home-style lacks them (lane 1's nb* roles are NOT borrowed: lane 1's own apply writes them
# as one marked block, agreed on the table a6049, c6262, so two copies never stand)
BORROWED = [WL / "home-feed" / "feed.style"]
# (title, tags, props): the lenses this lane puts in Home base
LENSES = [("home-timer", "lens", ""),
          ("home-timer-bar", "lens,widget", "slot=bar order=3 size=s"),
          ("home-glance", "lens,widget", "slot=bar order=1 size=m"),
          ("home-house-small", "lens", ""),
          ("home-house", "lens", ""),
          ("home-notices", "lens,widget", "slot=bar order=4 size=m")]
UNWIDGET = ["home-clock", "home-now", "home-pomodoro"]
PANEL = "prop:role=home-panel,prop:actor=alex"
CHAT_OLD = "  working : row\n    role working\n    of house doing=working as h"
CHAT_NEW = "  working : row\n    role working\n    of house doing=working resident=$draft.to as h"
# THE RULE (lamplit.overrides): the colours a role may use
ALLOWED = {"warm", "jeff", "accent", "ink", "soft", "faint", "ghost", "night", "hush",
           "glass", "glassdeep", "wash", "raised", "raisedhi", "mine", "rim", "paper",
           "warmwash", "jeffwash", "jeffwash2", "accentwash"}


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


# ---- the two worlds ---------------------------------------------------------------------------------------------------
class Try:
    name = "frontier-try"

    def __init__(self, who="worker-a6057"):
        self.who = who

    def run(self, lines):
        r = subprocess.run([sys.executable, str(LAB / "explore.py"), "frontier-try", "--as", self.who, "--whole"],
                           input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=LAB)
        return r.stdout + r.stderr

    def do(self, line):
        return self.run([line])

    def reads(self, ids):
        """id -> its text, in one run of explore.py (each answer begins with its echoed '> read <id>')."""
        out, cur = {}, None
        for chunk in re.split(r"^> (read a\d+)\s*$", self.run([f"read {i}" for i in ids]), flags=re.M):
            m = re.match(r"^read (a\d+)$", chunk)
            if m:
                cur = m.group(1)
            elif cur:
                out[cur] = body_of(chunk)
                cur = None
        return out


class Live:
    name = "frontier (live)"

    def __init__(self, who="worker-a6057"):
        self.who = who

    def do(self, line):
        body = json.dumps({"session": "frontier", "as": self.who, "line": line, "whole": True}).encode()
        req = urllib.request.Request(DOOR, body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as f:
            r = json.loads(f.read())
        return r.get("text") or r.get("error") or json.dumps(r)

    def run(self, lines):
        return "\n".join(self.do(l) for l in lines)

    def reads(self, ids):
        return {i: body_of(self.do(f"read {i}")) for i in ids}


def body_of(read_text):
    """The text of a `read` answer: between its first --- and the last ---."""
    if "---" not in read_text:
        return None
    return read_text.split("---", 1)[1].rsplit("---", 1)[0].strip("\n")


def room_notes(w):
    """title -> (id, the note's line) of every note in Home base."""
    out = {}
    for m in re.finditer(r'^\s+(a\d+) note "([^"]+)"(.*)$', w.do(f"look {ROOM} :2"), re.M):
        out[m.group(2)] = (m.group(1), m.group(3))
    return out


def read(w, ident):
    return body_of(w.do(f"read {ident}"))


# ---- the style --------------------------------------------------------------------------------------------------------
def key_of(line):
    m = re.match(r"^(token|role|font)\s+([\w.-]+)", line)
    return (m.group(1), m.group(2)) if m else None


def names(text, kind):
    return {k[1] for l in text.splitlines() if (k := key_of(l)) and k[0] == kind}


def flat_style(base):
    """base (the live home-style) + borrowed roles it lacks + the overrides; the last definition of each name kept."""
    over = (HERE / "lamplit.overrides").read_text(encoding="utf-8")
    # applied twice, the base already holds this lane's comment lines: keep them once (keyed lines collapse anyway)
    mine = {l for l in over.splitlines() if not key_of(l) and l.strip()}
    base = "\n".join(l for l in base.splitlines() if key_of(l) or not (l in mine or l.startswith("# from board-lab/")
                                                                       or l.startswith("# from home-feed/")))
    have = names(base, "role")
    lent = []
    for p in BORROWED:
        if p.exists():
            got = [l for l in p.read_text(encoding="utf-8").splitlines() if (k := key_of(l)) and k[0] == "role" and k[1] not in have]
            if got:
                lent += [f"# from {p.parent.name}/{p.name} (roles home-style did not have yet)"] + got
    lines = base.splitlines() + lent + over.splitlines()
    # each name stands where it first stood (fonts and tokens stay at the top, a role in its section), with the words of
    # its last definition: the same style a later-wins reading gives, written once
    last, first = {}, {}
    for i, l in enumerate(lines):
        if (k := key_of(l)):
            last[k] = l
            first.setdefault(k, i)
    return "\n".join(last[k] if (k := key_of(l)) else l for i, l in enumerate(lines)
                     if not (k := key_of(l)) or first[k] == i).rstrip("\n")


def lint(style, lens_texts):
    """-> (errors, notes): roles lenses use that the style lacks; roles and tokens outside the rule."""
    roles = names(style, "role")
    tokens = {k[1] for l in style.splitlines() if (k := key_of(l)) and k[0] == "token"}
    colour_tokens = {k[1] for l in style.splitlines() if (k := key_of(l)) and k[0] == "token"
                     and re.search(r"=\s*(#[0-9A-Fa-f]{3,8}|[\w.]+ at [\d.]+%?)\s*$", l)}
    errors, notes = [], []
    for title, text in sorted(lens_texts.items()):
        used = {m.group(1) for m in re.finditer(r"^\s+role\s+([\w.-]+)", text, re.M)}
        miss = sorted(used - roles)
        if miss:
            errors.append(f"lens {title} uses roles home-style would lack: {' '.join(miss)}")
    outside = {}
    for l in style.splitlines():
        k = key_of(l)
        if not k or k[0] != "role":
            continue
        props = l.split(":", 1)[1] if ":" in l else ""
        for p in props.split(","):
            for w in re.findall(r"[A-Za-z][\w.]*", p.strip()):
                if w in colour_tokens and w not in ALLOWED:
                    outside.setdefault(w, []).append(k[1])
    for t, rs in sorted(outside.items()):
        notes.append(f"colour {t} (outside the rule) is used by {len(rs)} role(s): {' '.join(sorted(set(rs))[:12])}")
    extra = sorted(colour_tokens - ALLOWED - set(outside))
    if extra:
        notes.append(f"colour tokens outside the rule, used by no role: {' '.join(extra)}")
    return errors, notes


# ---- the plan ---------------------------------------------------------------------------------------------------------
def lens_text(title):
    return (HERE / f"{title}.lens").read_text(encoding="utf-8").rstrip("\n")


def plan(w, chat=False):
    """-> (lines, saves, undo, report): what to send, what it replaces (to keep), and the lines that put it back."""
    notes = room_notes(w)
    report, lines, saves, undo = [], [], {}, []
    need = ["home-style"] + UNWIDGET + (["jeff-chat"] if chat else [])
    lost = [t for t in need if t not in notes]
    if lost:
        raise SystemExit(f"refused: no note titled {', '.join(lost)} in the Home base room of {w.name}")
    # 1. the style
    sid = notes["home-style"][0]
    base = read(w, sid)
    style = flat_style(base)
    saves["home-style.style"] = base
    lines += [f"read {sid}", f"do rewrite {sid} text={q(style)}"]
    undo += [f"read {sid}", f"do rewrite {sid} text={q(base)}"]
    report.append(f"home-style {sid}: {len(names(base, 'role'))} roles -> {len(names(style, 'role'))} "
                  f"({len(names(style, 'role') - names(base, 'role'))} new), {len(style.splitlines())} lines")
    # 2. the lenses
    lines.append(f"look {ROOM}")
    for title, tags, props in LENSES:
        text = lens_text(title)
        if title in notes:
            nid = notes[title][0]
            old = read(w, nid)
            saves[f"{title}.lens"] = old
            lines += [f"read {nid}", f"do rewrite {nid} text={q(text)}"]
            undo += [f"read {nid}", f"do rewrite {nid} text={q(old)}"]
            report.append(f"lens {title} {nid}: rewritten ({len(old.splitlines())} -> {len(text.splitlines())} lines)")
        else:
            lines.append(f"do create {ROOM} kind=note title={title} tags={tags} style=home-style {props} text={q(text)}".replace("  ", " "))
            undo += [f"read \"{title}\"", f"do remove \"{title}\""]
            report.append(f"lens {title}: new")
    # 3. widgets
    for title in UNWIDGET:
        nid, line = notes[title]
        head = next((l for l in w.do(f"read {nid}").splitlines() if f"appears at {nid}" in l), "")
        tags = re.search(r"· tags (\S+)", head)
        if tags and "widget" in tags.group(1).split(","):
            lines += [f"read {nid}", f"do tag {nid} remove=widget"]
            undo += [f"read {nid}", f"do tag {nid} add=widget"]
            report.append(f"widget {title} {nid}: tag widget off")
    # 4. the panel
    found = w.do(f"find {PANEL},prop:lens=home-work")
    m = re.search(r'^\s+(a\d+) note "([^"]+)" · (.*)$', found, re.M)
    if m:
        pid, ptitle, pline = m.group(1), m.group(2), m.group(3)
        lesser = re.search(r"\blesser=(\S*)", pline)
        saves["at-work-panel.txt"] = f"{pid} title={ptitle} {pline}"
        lines += [f"read {pid}", f"do prop {pid} lens=home-house lesser=home-house-small", f"read {pid}", f'do retitle {pid} title="The house"']
        undo += [f"read {pid}", f"do prop {pid} lens=home-work lesser={lesser.group(1) if lesser else ''}", f"read {pid}", f"do retitle {pid} title={q(ptitle)}"]
        report.append(f"panel {pid} '{ptitle}': lens home-work -> home-house, called The house")
    elif "home-house" in w.do(f"find {PANEL},prop:lens=home-house"):
        report.append("panel: The house is already Alex's (lens=home-house)")
    else:
        report.append("panel: Alex has no At work panel (lens=home-work); The house is not placed (make a panel note)")
    # 5. glance tags (agreed, a6049 c6262): lane 1's apply tags The board glance-you and glance-board; Waiting on you is
    # tagged glance-you here only while no panel answers 'you' yet, and the assembler takes it off when the board lands
    claimed = set(re.findall(r"^\s+(a\d+) note ", w.do(f"find {PANEL},tag:glance-you"), re.M))
    for lens, tag in (("waiting-on-me", "glance-you"), ("home-house", "glance-work"), ("home-work", "glance-work"),
                      ("home-board", "glance-board"), ("direction-board-inbox", "glance-board")):
        if tag == "glance-you" and claimed:
            report.append(f"glance-you: already answered by {' '.join(sorted(claimed))}; Waiting on you left untagged")
            continue
        f = w.do(f"find {PANEL},prop:lens={lens}")
        for pid in re.findall(r"^\s+(a\d+) note ", f, re.M):
            lines += [f"read {pid}", f"do tag {pid} add={tag}"]
            undo += [f"read {pid}", f"do tag {pid} remove={tag}"]
            report.append(f"panel {pid} (lens {lens}): tag {tag}")
    # 6. the chat's typing row
    if chat:
        cid = notes["jeff-chat"][0]
        old = read(w, cid)
        if CHAT_OLD not in old:
            report.append("jeff-chat: its typing row is not as expected (changed since 16 Oct?): left alone")
        else:
            saves["jeff-chat.lens"] = old
            lines += [f"read {cid}", f"do replace {cid} old={q(CHAT_OLD)} new={q(CHAT_NEW)}"]
            undo += [f"read {cid}", f"do replace {cid} old={q(CHAT_NEW)} new={q(CHAT_OLD)}"]
            report.append(f"jeff-chat {cid}: the typing row names only the one written to")
    # lint, against every lens in the room that wears home-style, as they would be after this
    texts = {t: lens_text(t) for t, _, _ in LENSES}
    worn = {nid: title for title, (nid, line) in notes.items() if title not in texts and "style=home-style" in line}
    for nid, t in w.reads(list(worn)).items():
        if t and re.search(r"^\S+ : ", t, re.M):
            texts[worn[nid]] = t
    errors, lnotes = lint(style, texts)
    return lines, saves, list(reversed_pairs(undo)), report, errors, lnotes, style


def reversed_pairs(undo):
    """undo lines come in look/read + act pairs (or triples for the panel); put them back last first."""
    groups, cur = [], []
    for l in undo:
        if (l.startswith("read ") or l.startswith("look ")) and cur:
            groups.append(cur)
            cur = []
        cur.append(l)
    if cur:
        groups.append(cur)
    for g in reversed(groups):
        yield from g


# ---- main -------------------------------------------------------------------------------------------------------------
def opt(a, k, d=None):
    return a[a.index(k) + 1] if k in a else d


def main(a):
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    who = opt(a, "--as", "worker-a6057")
    chat = "--chat" in a
    how = a[0]
    if how == "undo":
        d = pathlib.Path(a[1])
        w = Live(who)
        for l in (d / "undo.desk").read_text(encoding="utf-8").splitlines():
            said = w.do(l)
            print(said[:300])
            if said.startswith("ERR") or "refused" in said[:200]:
                print("stopped: the line above was refused")
                return 1
        return 0
    world = opt(a, "--world", "live" if how == "door" else "try")
    w = (Live if world == "live" else Try)(who)
    lines, saves, undo, report, errors, lnotes, style = plan(w, chat)
    print(f"LAMPLIT into {w.name}:")
    for r in report:
        print("  " + r)
    print(f"lint: {len(errors)} error(s)" + "".join("\n  ERROR " + e for e in errors))
    for n in lnotes:
        print("  note: " + n)
    if how in ("check", "lint"):
        (HERE / "home-style.lamplit").write_text(style + "\n", encoding="utf-8")
        print(f"the style it would write: {HERE / 'home-style.lamplit'} ({len(style.splitlines())} lines); nothing sent")
        return 1 if errors else 0
    if errors:
        print("refused: a lens would lose its roles (lint errors above); nothing sent")
        return 1
    if how == "lines":
        pathlib.Path(a[1]).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {len(lines)} lines to {a[1]}")
        return 0
    if how == "undo-lines":      # what would put this world back as it is now, once applied (a baseline for a copy)
        pathlib.Path(a[1]).write_text("\n".join(undo) + "\n", encoding="utf-8")
        print(f"wrote {len(undo)} undo lines to {a[1]}")
        return 0
    if how == "try":
        out = w.run(lines)
        bad = [l for l in out.splitlines() if re.match(r"^(ERR|.*refused|.*does not compile)", l)]
        print("\n".join(l[:300] for l in out.splitlines() if re.match(r"^(ok |ERR|.*refused|~ .*compil)", l)))
        return 1 if bad else 0
    if how == "door":
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        d = HERE / "saved" / stamp
        d.mkdir(parents=True, exist_ok=True)
        for name, text in saves.items():
            (d / name).write_text(text + "\n", encoding="utf-8")
        (d / "undo.desk").write_text("\n".join(undo) + "\n", encoding="utf-8")
        (d / "apply.desk").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"saved what it replaces, and undo.desk, in {d}")
        for l in lines:
            said = w.do(l)
            print(said[:300])
            if said.startswith("ERR") or "refused" in said[:200]:
                print(f"stopped: the line above was refused. To put back what was done: apply.py undo {d}")
                return 1
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
