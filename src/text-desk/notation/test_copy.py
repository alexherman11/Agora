# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_copy (a6427): the desk word copy, and $* inside a verb's expression.

    python test_copy.py

A fresh world in memory (explore.fresh): a surface tree of columns, notes and a view, copied; the copy has the same
shape, order, titles, texts, tags and props, a prop naming a part inside points at the part's copy, one naming
something outside stays, $new is the copy itself, a chat inside is refused with nothing made, a copy cannot go inside
what it copies, and each step undoes. Then a verb that reads words-after($*, "save") gets the words after it.
"""
import os
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import explore  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1200]}"))
    if not ok:
        fails.append(name)


D = explore.fresh()
D._session = "copy-inmemory"
W = D.world
W.me = "pike"
ROOT = W.root


def reply(*lines):
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append(r.get("text") or ("ERR " + str(r.get("error"))))
    return out


def made(text):
    return re.search(r"created ([af]\d+)", text).group(1)


def shape(fid):
    """A surface tree as facts with no ids: (title, layout, props) and its children in order; a note as (kind, title,
    text, tags, props), a prop naming a part inside replaced by that part's path."""
    paths = {}

    def walk(n, path):
        paths[n["id"]] = path
        if n["type"] == "appearance":
            paths[n["subject"]] = path
        for i, k in enumerate(W.children(n["id"]) if n["type"] == "surface" else []):
            walk(k, path + (i,))
    walk(W.nodes[fid], ())

    def facts(n):
        if n["type"] == "surface":
            props = {k: paths.get(v, v) for k, v in (n.get("props") or {}).items()}
            return ("surface", n["title"], n.get("layout"), n.get("query"), props, tuple(facts(k) for k in W.children(n["id"])))
        s = W.subjects[n["subject"]]
        props = {k: paths.get(v, v) for k, v in (s.get("props") or {}).items()}
        return (s["kind"], s["title"], s["text"], tuple(s["tags"]), props)
    return facts(W.nodes[fid])


out = reply(f"look {ROOT}", f"do create {ROOT} kind=surface title=Layout layout=row")
lay = made(out[-1])
col1 = made(reply(f"look {lay}", f"do create {lay} kind=surface title=left layout=column")[-1])
col2 = made(reply(f"look {lay}", f"do create {lay} kind=surface title=middle layout=column")[-1])
a = made(reply(f"look {col1}", f'do create {col1} kind=note title="The board" text="lanes" tags=panel lens=home-board shelf=no')[-1])
b = made(reply(f"look {col1}", f"do create {col1} kind=task title=Card status=open")[-1])
outside = made(reply(f"look {ROOT}", f"do create {ROOT} kind=note title=Elsewhere")[-1])
c = made(reply(f"look {col2}", f"do create {col2} kind=note title=Pinned lens=doc-page thing={outside}")[-1])
v = made(reply(f"look {col2}", f"do create {col2} kind=view title=Tasks query=kind:task")[-1])
reply(f"look {lay} :3", f"do prop {lay} role=home-layout full={a}", f"do prop {col2} span=2")
holder = made(reply(f"look {ROOT}", f"do create {ROOT} kind=surface title=Kept layout=column")[-1])

n0 = len(W.events)
out = reply(f"look {lay} :3", f"look {holder}", f"do copy {lay} into={holder} title=Saved", "look $new")
cp = re.search(r"\$new = ([af]\d+)", out[-1])
check("copy is taken", out[2].startswith("ok copy"), out[2])
check("$new is the copy itself, not its last part", cp and W.nodes.get(cp.group(1), {}).get("parent") == holder
      and W.nodes[cp.group(1)]["title"] == "Saved", out[-1])
cp = cp.group(1) if cp else None
mine, theirs = shape(lay), shape(cp) if cp else None
check("the copy has the same shape, order, words, tags and props (title apart)",
      theirs and mine[0] == theirs[0] and mine[2:] == theirs[2:], (mine, theirs))
check("full= inside the copy names the board's copy, not the board",
      cp and (W.nodes[cp].get("props") or {}).get("full") not in (a, None)
      and W.nodes[(W.nodes[cp]["props"]["full"])]["parent"] != col1, W.nodes.get(cp))
pinned = [W.subjects[k["subject"]] for col in W.children(cp) for k in W.children(col["id"])
          if k["type"] == "appearance" and W.subjects[k["subject"]]["title"] == "Pinned"]
check("thing= naming something outside the copy stays as it was", pinned and pinned[0]["props"]["thing"] == outside, pinned)
check("the original is untouched", shape(lay) == mine)
evs = W.events[n0:]
check("one event per part and per thing with props", len([e for e in evs if e["verb"] == "create"]) == 7
      and len([e for e in evs if e["verb"] == "prop"]) == 5, [(e["verb"], e["target"]) for e in evs])

for e in reversed([e for e in W.events[n0:] if not e.get("undone") and e["verb"] != "undo"]):
    W.undo(e["id"])
check("undone step by step, nothing of the copy is left", not W.children(holder), W.children(holder))

chat = made(reply(f"look {col2}", f"do create {col2} kind=chat title=Talk")[-1])
before = len(W.nodes)
out = reply(f"look {lay} :3", f"do copy {lay} into={holder}")
check("a chat inside is refused, and nothing is made", out[-1].startswith("ERR") and "chat" in out[-1] and len(W.nodes) == before, out[-1])
reply(f"look {chat}", f"do remove {chat}")
out = reply(f"look {lay} :3", f"do copy {lay} into={col1}")
check("a copy cannot go inside what it copies", out[-1].startswith("ERR") and "inside" in out[-1], out[-1])

# stored, the line must say \"save\": a k=v value's own quotes are taken off when the line is read, the escaped ones stay
STORED = 'do prop ' + outside + r' kept=$(words-after($*, \"save\"))'
out = reply(f"look {ROOT}", f'do create {ROOT} kind=note title=keepas tags=verb text="{STORED.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"')
check("the verb stores the line as written", W.subjects[W.nodes[made(out[-1])]["subject"]]["text"] == STORED,
      W.subjects[W.nodes[made(out[-1])]["subject"]]["text"])
out = reply(f"look {outside}", "keepas save my-thing")
check("$* reads in an expression: words-after($*, \"save\") is the words after it",
      (W.subjects[W.nodes[outside]["subject"]].get("props") or {}).get("kept") == "my-thing", out)

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
