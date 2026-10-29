"""P5 (imagined vocabulary, real data). If the desktop world had nouns that nest, adjectives computed from aspects,
and aspects that say what they point at, what would `kinds <thing>` and `near <thing>` read like? Prints only names,
kinds and counts; no contents."""
import collections, re
from world import load, fam, INFRA, PATH
live, recs = load(PATH)
# nouns: declared, by a yes (here: my proposal, for the dry run)
IS = {"taskboard-task": ["task"], "house-agent": ["agent"], "map-layer": ["layer"], "pane": ["window"],
      "said": ["remark"], "post": ["remark"], "taskboard-event": ["remark"], "ask-request": ["remark", "request"],
      "board-catch-up": ["remark"], "note": ["page"], "guide": ["page"], "topic": ["page"], "soul": ["page"],
      "charter": ["page"], "style": ["look"], "theme": ["look"], "part-style": ["look"], "lens": ["view"],
      "view-preference": ["preference"], "theme-choice": ["preference"], "document": ["file"],
      **{k: ["settings"] for k in ("wm-settings", "theme-settings", "model-settings", "board-settings", "file-settings",
                                   "shell-settings", "taskboard-settings")},
      "remark": ["writing-noun"], "page": ["writing-noun"], "settings": ["preference"]}
# belongs-to, read off the names that mean "for" (not is-a)
FOR = {"wm-settings": "the window manager", "theme-settings": "themes", "model-settings": "the model module",
       "board-settings": "the board", "file-settings": "files", "shell-settings": "the shell", "taskboard-settings": "the task board"}
# adjectives: computed from aspects
ADJ = {"writing": lambda a, kd: "text" in a and kd not in ("style", "theme", "lens", "part-style", "rule"),
       "titled": lambda a, kd: any(k in a for k in ("title", "name")),
       "coloured": lambda a, kd: any(k in a for k in ("colour", "color", "accent")),
       "chooses a model": lambda a, kd: "model" in a,
       "on a bar": lambda a, kd: "bar" in a, "in a chat": lambda a, kd: "chat" in a,
       "carried from the old desk": lambda a, kd: "carried_from" in a or str(a.get("source", "")).startswith("a1"),
       "timed": lambda a, kd: any(k in a for k in ("start", "when", "until", "closes"))}
# typed aspects: what a name-valued aspect points at
POINTS = {"lane": "taskboard-lane", "who": ("agent", "person"), "style": "style", "lens": "lens", "map": "map",
          "chat": "chat", "soul": "soul", "charter": "charter", "person": "person", "theme": "theme", "trial": "theme"}
def ladder(kd):
    out, todo = [], [kd]
    while todo:
        k = todo.pop(0)
        for p in IS.get(k, []):
            if p not in out: out.append(p); todo.append(p)
    return out
def label(t): a = live[t]; return str(a.get("title") or a.get("name") or a.get("label") or t)[:44]
def resolve(asp, v):
    want = POINTS.get(asp)
    if not want: return None
    want = (want,) if isinstance(want, str) else want
    if isinstance(v, str) and re.fullmatch(r"dk\d+", v): return v if v in live else None
    hits = [t for t, a in live.items() if a["kind"] in want and str(v).casefold() in
            {str(a.get(f, "")).casefold() for f in ("name", "title", "label", "signer")}]
    return hits[0] if len(hits) == 1 else None
def show(t):
    a = live[t]; kd = a["kind"]
    adj = [n for n, f in ADJ.items() if f(a, kd)]
    print(f"\nkinds {label(t)}  ({t})")
    print(f"  is: a {kd}" + "".join(f", so a {p}" for p in ladder(kd) if p != "writing-noun")
          + (f"; settings for {FOR[kd]}" if kd in FOR else ""))
    print(f"  has: {', '.join(adj) or '-'}")
    near = []
    for k, v in a.items():
        r = resolve(fam(k), v)
        if r and r != t: near.append(f"{fam(k)} → {label(r)} (a {live[r]['kind']})")
    print(f"  near: {'; '.join(near) or 'nothing it points at by name'}")
    sib = sum(1 for o in live.values() if o["kind"] == kd) - 1
    cousins = collections.Counter(o["kind"] for o in live.values() if o["kind"] != kd and ladder(kd) and
                                  set(ladder(o["kind"])) & set(ladder(kd)[:1]))
    print(f"  others like it: {sib} more {kd}" + (f"; through '{ladder(kd)[0]}': " + ", ".join(f"{n} {k}" for k, n in cousins.most_common(5)) if cousins else ""))
pick = {}
for t, a in sorted(live.items(), key=lambda x: int(x[0][2:]) if x[0][2:].isdigit() else 0):
    pick.setdefault(a["kind"], t)
for kd in ("taskboard-task", "house-agent", "wm-settings", "ask-request", "document", "map-layer", "said"):
    if kd in pick: show(pick[kd])
# how many content things gain at least one noun above their own kind, or one adjective
content = [t for t, a in live.items() if a["kind"] not in INFRA and t != "world"]
up = sum(1 for t in content if ladder(live[t]["kind"]))
adj = sum(1 for t in content if any(f(live[t], live[t]["kind"]) for n, f in ADJ.items() if n not in ("titled",)))
print(f"\ncontent things {len(content)}: {up} gain an outer noun under this vocabulary, {adj} gain an adjective other than 'titled'")
