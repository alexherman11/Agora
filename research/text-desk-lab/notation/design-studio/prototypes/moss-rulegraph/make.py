"""Moss: build graph.json for the rule graph from a real desk session.

Usage (from the notation folder):
    python design-studio/prototypes/moss-rulegraph/make.py proto-moss

It reads the desk's OWN PRINTED TEXT (`rules`, `scripts`) plus `--dump` for surface titles,
and writes graph.json next to this file. Nothing is invented: every node carries the exact
line the desk printed, and every command shown on the page is one that runs as printed.

Note for the report: `--dump` contains subjects, nodes and links only. Rules and scripts are
NOT in it. The automation layer of a desk is invisible to any renderer that reads the dump;
the only way to see it is the text the desk prints. That is itself a finding.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def desk(session, commands):
    p = subprocess.run([sys.executable, "explore.py", session, "--as", "moss"],
                       input="\n".join(commands), capture_output=True, text=True, cwd=LAB)
    return p.stdout


def dump(session):
    p = subprocess.run([sys.executable, "explore.py", session, "--dump"],
                       capture_output=True, text=True, cwd=LAB)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"subjects": {}, "nodes": {}}


# ---- parsing the desk's printed lines -------------------------------------------------

RULE_WHEN = re.compile(r"^(r\d+) when (.+?) do (.+?)\s*\(fired (\d+)x\)\s*$")
RULE_ON = re.compile(r"^(r\d+) on (\S+)(?: by=(\S+))? do (.+?)\s*\(fired (\d+)x\)\s*$")
SCRIPT = re.compile(r"^(?:script )?(\S+) = (.+)$")


def parse_rules(text):
    rules = []
    for line in text.splitlines():
        line = line.strip()
        m = RULE_WHEN.match(line)
        if m:
            rules.append({"id": m.group(1), "gate_kind": "when", "gate": m.group(2),
                          "act": m.group(3).strip(), "fired": int(m.group(4)), "line": line})
            continue
        m = RULE_ON.match(line)
        if m:
            gate = m.group(2) + (f" by={m.group(3)}" if m.group(3) else "")
            rules.append({"id": m.group(1), "gate_kind": "on", "gate": gate,
                          "act": m.group(4).strip(), "fired": int(m.group(5)), "line": line})
    return rules


def parse_scripts(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(">") or line.startswith("no scripts"):
            continue
        m = SCRIPT.match(line)
        if m and " " not in m.group(1):
            out[m.group(1)] = m.group(2)
    return out


# ---- static analysis: what an action produces, what a gate requires --------------------

def effects_of(act, scripts, seen=()):
    """Facts an action makes true (or unmakes). Conservative: only what the verb plainly does."""
    made, unmade = [], []
    argv = act.split()
    if not argv:
        return made, unmade
    verb = argv[0]
    if verb == "run":
        name = argv[1] if len(argv) > 1 else ""
        if name in scripts and name not in seen:
            for step in scripts[name].split(";"):
                step = step.strip()
                step = re.sub(r"^do\s+", "", step)
                m, u = effects_of(step, scripts, seen + (name,))
                made += m
                unmade += u
        return made, unmade
    kv = dict(re.findall(r"(\w+)=(\S+)", act))
    if verb == "tag":
        for t in (kv.get("add") or "").split(","):
            if t:
                made.append(("tag", t))
        for t in (kv.get("remove") or "").split(","):
            if t:
                unmade.append(("tag", t))
    elif verb in ("move", "place", "group", "gather"):
        for k in ("into", "to"):
            if kv.get(k):
                made.append(("in", kv[k]))
    elif verb == "prop":
        for k, v in kv.items():
            made.append(("prop", f"{k}={v}"))
    elif verb == "create":
        if kv.get("kind"):
            made.append(("kind", kv["kind"]))
        for t in (kv.get("tags") or "").split(","):
            if t:
                made.append(("tag", t))
    elif verb == "due":
        made.append(("due", kv.get("to", "?")))
    return made, unmade


def requires_of(gate, gate_kind):
    """Positive facts a gate needs. Negated terms are returned separately."""
    if gate_kind == "on":
        return [], []
    pos, neg = [], []
    for term in gate.split(","):
        term = term.strip()
        negated = term.startswith("-")
        t = term[1:] if negated else term
        got = None
        if t.startswith("tag:"):
            got = ("tag", t[4:])
        elif t.startswith("in:"):
            got = ("in", t[3:])
        elif t.startswith("kind:"):
            got = ("kind", t[5:])
        elif t.startswith("prop:"):
            got = ("prop", t[5:])
        elif t.startswith("due"):
            got = ("due", t)
        if got:
            (neg if negated else pos).append(got)
    return pos, neg


def same_place(a, b, titles):
    """in:Today matches into=Today or into=f03 when f03 is titled Today."""
    if a == b:
        return True
    return titles.get(a, a).lower() == titles.get(b, b).lower()


def build(session):
    rtext = desk(session, ["rules"])
    stext = desk(session, ["scripts"])
    rules = parse_rules(rtext)
    scripts = parse_scripts(stext)
    d = dump(session)
    titles = {}
    for nid, n in (d.get("nodes") or {}).items():
        t = n.get("title")
        if n.get("type") == "surface" and t:
            titles[nid] = t
            titles[t] = nid
    surfaces = {v for k, v in titles.items() if k.startswith("f")}

    edges, findings = [], []
    for a in rules:
        made, unmade = effects_of(a["act"], scripts)
        for b in rules:
            if b["gate_kind"] == "on":
                verb = b["gate"].split()[0]
                if a["act"].split()[0] == verb:
                    edges.append({"from": a["id"], "to": b["id"], "kind": "makes",
                                  "why": f"{a['id']} does {verb}, which is the event {b['id']} watches"})
                continue
            pos, _ = requires_of(b["gate"], b["gate_kind"])
            for f in made:
                for need in pos:
                    if f[0] == need[0] and (same_place(f[1], need[1], titles) if f[0] == "in" else f[1] == need[1]):
                        edges.append({"from": a["id"], "to": b["id"], "kind": "makes",
                                      "why": f"{a['id']} makes {f[0]}:{f[1]}, which {b['id']} waits for"})
            for f in unmade:
                for need in pos:
                    if f[0] == need[0] and f[1] == need[1]:
                        edges.append({"from": a["id"], "to": b["id"], "kind": "unmakes",
                                      "why": f"{a['id']} removes {f[0]}:{f[1]}, which {b['id']} waits for"})

    # ---- findings the text cannot tell you --------------------------------------------
    incoming = {r["id"]: [e for e in edges if e["to"] == r["id"]] for r in rules}
    for r in rules:
        # dangling target
        for k, v in re.findall(r"(into|to)=(\S+)", r["act"]):
            if v.startswith("$"):
                continue
            if v not in titles and v not in surfaces:
                findings.append({"rule": r["id"], "grade": "broken",
                                 "text": f"target {v!r} does not exist on this desk; the rule fails only when it fires"})
        # frozen date
        m = re.search(r"due[<>](\d{4}-\d{2}-\d{2})", r["gate"])
        if m:
            findings.append({"rule": r["id"], "grade": "frozen",
                             "text": f"the date {m.group(1)} is fixed. `due<$today` is substituted when the rule is "
                                     f"WRITTEN; `due<today` stays live. The two look alike and behave oppositely."})
        # dead rule
        if r["fired"] == 0 and not incoming[r["id"]] and r["gate_kind"] == "when":
            findings.append({"rule": r["id"], "grade": "unreached",
                             "text": "never fired, and no other rule makes what it waits for. Only a person or a "
                                     "script outside these rules can reach it."})
        # missing recurrence
        if any(e["kind"] == "unmakes" for e in edges if e["from"] == r["id"]):
            tgt = [e["to"] for e in edges if e["from"] == r["id"] and e["kind"] == "unmakes"]
            findings.append({"rule": r["id"], "grade": "one-shot",
                             "text": f"undoes what {', '.join(tgt)} waits for. This looks like a cycle and is not one: "
                                     f"a `when` rule fires at most ONCE per thing, ever. The loop guard and "
                                     f"recurrence are the same knob."})

    # cycles over 'makes' edges
    adj = {}
    for e in edges:
        if e["kind"] == "makes":
            adj.setdefault(e["from"], []).append(e["to"])
    cycles, stack, onstack = [], [], set()

    def walk(n):
        stack.append(n)
        onstack.add(n)
        for m in adj.get(n, []):
            if m in onstack:
                cycles.append(stack[stack.index(m):] + [m])
            elif m not in seen_nodes:
                walk(m)
        stack.pop()
        onstack.discard(n)

    seen_nodes = set()
    for r in rules:
        if r["id"] not in seen_nodes:
            walk(r["id"])
        seen_nodes.add(r["id"])

    return {"session": session, "rules": rules, "scripts": scripts, "edges": edges,
            "findings": findings, "cycles": cycles,
            "raw": {"rules": rtext.strip(), "scripts": stext.strip()}}


if __name__ == "__main__":
    session = sys.argv[1] if len(sys.argv) > 1 else "proto-moss"
    g = build(session)
    with open(os.path.join(HERE, "graph.json"), "w", encoding="utf-8") as f:
        json.dump(g, f, indent=1)
    print(f"{len(g['rules'])} rules, {len(g['scripts'])} scripts, {len(g['edges'])} edges, "
          f"{len(g['findings'])} findings, {len(g['cycles'])} cycle(s) -> graph.json")
