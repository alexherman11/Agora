"""World half of a6646. Check exact current passages; generate or apply on a copy.

Live application is through Desk MCP after source landing and painter checks.
No localhost route, no automatic live rewrite. All roles have their own style.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
NOTATION = HERE.parents[1] / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))
from plan_usage import q

GLANCE_OLD = '''    plain : text "$(you) $(youword) · $(busy) at work"
      role lgword
      only when count(prop:role=home-layout,prop:actor=$me) = 0'''
GLANCE_NEW = GLANCE_OLD + '''
    usage : column
      lens plan-usage-glance'''
BOARD_OLD = '''    since : text "$(day-or-time($changed.commission, $today))"
      role nbwhen
      only when ($changed.commission or "") != ""'''
BOARD_NEW = '''    usage : text "$c.usage_state"
      role nbstage
      only when ($c.usage_state or "") != ""
''' + BOARD_OLD


def lines(w):
    def one(title):
        hits = [s for s in w.subjects.values() if s["title"] == title and w.appearances_of(s["id"])]
        if len(hits) != 1:
            raise ValueError(f"{title}: expected exactly one placed note")
        return hits[0]
    out = []
    room = next((n["id"] for n in w.nodes.values() if n["type"] == "surface" and n.get("title") == "Home base"), w.root)
    for name, file, tags, props in [
        ("plan-usage-style", "plan-usage.style", "style", ""),
        ("home-usage", "home-usage.lens", "lens,widget", "style=plan-usage-style slot=bar order=4 size=s"),
        ("plan-usage-reader", "plan-usage-reader.lens", "lens", "style=plan-usage-style"),
        ("plan-usage-glance", "plan-usage-glance.lens", "lens", "style=plan-usage-style")]:
        hits = [s for s in w.subjects.values() if s["title"] == name and w.appearances_of(s["id"])]
        text = (HERE / file).read_text(encoding="utf-8").rstrip()
        if hits:
            if len(hits) != 1 or hits[0]["text"].strip() != text:
                raise ValueError(f"{name}: already exists with different words; read before changing")
        else:
            out += [f"look {room} :1", f"do create {room} kind=note title={q(name)} tags={tags} {props} text={q(text)}"]
    for name, old, new in (("home-glance", GLANCE_OLD, GLANCE_NEW), ("home-board", BOARD_OLD, BOARD_NEW)):
        note = one(name)
        # Both indentation conventions exist in the world. These are two exact
        # passages, not a whitespace-insensitive rewrite of the surrounding lens.
        half = lambda text: "\n".join(" " * ((len(line) - len(line.lstrip())) // 2) + line.lstrip()
                                     for line in text.splitlines())
        if old not in note["text"] and half(old) in note["text"]:
            old, new = half(old), half(new)
        if new in note["text"]:
            continue
        if note["text"].count(old) != 1:
            raise ValueError(f"{name}: exact old passage moved; re-read before replacing")
        target = w.appearances_of(note["id"])[0]
        out += [f"read {target}", f"do replace {target} old={q(old)} new={q(new)}"]
    settings = [s for s in w.subjects.values() if s["title"] == "The house"
                and (s.get("props") or {}).get("model") and w.appearances_of(s["id"])]
    if len(settings) != 1:
        raise ValueError("Expected one model-bearing house settings note")
    target = w.appearances_of(settings[0]["id"])[0]
    role = (settings[0].get("props") or {}).get("role", "")
    if role not in ("", "house-settings"):
        raise ValueError("House settings role changed; read before changing")
    if not role:
        out += [f"read {target}", f"do prop {target} role=house-settings"]
    return out


if __name__ == "__main__":
    import argparse
    import export_docs
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world")
    parser.add_argument("out")
    args = parser.parse_args()
    doc = export_docs.load(args.world)
    Path(args.out).write_text("\n".join(lines(doc.world)) + "\n", encoding="utf-8")
    print("Wrote checked Desk lines to " + args.out + "; nothing applied.")
