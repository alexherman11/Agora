"""Guarded review entry point. Stages only hud_playtest's disposable copy.

No live endpoint, host restart, account action or Conversation send. The existing
runner owns the copy, hidden desktop, guard, screenshots and cleanup.
"""
import argparse
import asyncio
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hud_playtest as pt
import navigation_stage as stage
import world
sys.path.insert(0, str(HERE.parent / "slim-dock"))
import world_patch as dock_stage


def prepare_navigation(snapshot):
    """Checked commands from the copy's public JSON snapshot, never a pickle."""
    w = world.World()
    w.nodes, w.subjects = snapshot["nodes"], snapshot["subjects"]
    props = lambda n: (n.get("props") if n["type"] == "surface" else
                       w.subjects[n["subject"]].get("props")) or {}
    layouts = [n for n in w.nodes.values()
               if props(n).get("role") == "home-layout" and props(n).get("actor") == "alex"]
    lenses = [n for n in w.nodes.values() if n.get("subject") in w.subjects
              and w.subjects[n["subject"]].get("title") == "home-tiling"
              and "lens" in w.subjects[n["subject"]].get("tags", [])]
    if len(layouts) != 1 or len(lenses) != 1:
        raise ValueError("STOP: copy needs exactly one Alex layout and home-tiling lens")
    lay, lens = layouts[0], lenses[0]
    old = w.subjects[lens["subject"]]["text"]
    hunks = stage.patches(old)  # preflight all passages before any mutation
    p = props(lay)
    manifest = [{"span": props(c).get("span", 1), "panels": [
        {"id": n["id"], "height_share": props(n).get("height_share", 1),
         "sizing": props(n).get("sizing", "")}
        for n in w.children(c["id"]) if props(n).get("role") == "home-panel"]}
        for c in w.children(lay["id"]) if c["type"] == "surface"]
    tree = p.get("tree") or json.dumps(stage.migration(manifest))
    declaration = list(dict.fromkeys(
        [s.strip() for s in p.get("copy_json", "").split(",") if s.strip()] + ["tree"]))
    commands = [f"look {lay['id']}",
                f"do prop {lay['id']} tree={pt.q(tree)} copy_json={pt.q(','.join(declaration))}"]
    for old_text, new_text in hunks:
        commands += [f"read {lens['id']}",
                     f"do replace {lens['id']} old={pt.q(old_text)} new={pt.q(new_text)}"]
    return commands


def prepare_dock(snapshot):
    """Plan the landed dock world half, preserving exact already-applied text.

    All targets and verb definitions are checked before returning commands.
    No guessing at a moved passage, rewriting newer verbs or duplicate creates.
    """
    nodes, subjects = snapshot["nodes"], snapshot["subjects"]
    commands = []
    for ident, old, new in dock_stage.passages():
        node = nodes.get(ident, {})
        subject = subjects.get(node.get("subject"), {})
        text = subject.get("text")
        if not isinstance(text, str):
            raise ValueError("STOP: dock target missing from copy: " + ident)
        # Some replacements extend the old passage. Count only occurrences
        # outside the exact new passage when detecting an already-applied half.
        if text.count(new) == 1 and text.replace(new, "", 1).count(old) == 0:
            continue
        if text.count(old) != 1 or new in text or (
                ident == "a5206" and "# a7223 slim dock begin" in text):
            raise ValueError("STOP: dock passage moved/partly applied: " + ident)
        commands += [f"read {ident}",
                     f"do replace {ident} old={pt.q(old)} new={pt.q(new)}"]
    if "f5189" not in nodes:
        raise ValueError("STOP: dock verb surface missing from copy")
    verbs = []
    for path in sorted(dock_stage.HERE.glob("*.verb")):
        expected = path.read_text(encoding="utf-8").rstrip()
        matches = [s for s in subjects.values()
                   if s.get("title") == path.stem and "verb" in s.get("tags", [])
                   and s.get("props", {}).get("on") == "f5189"]
        if matches:
            if len(matches) != 1 or matches[0].get("text", "").rstrip() != expected:
                raise ValueError("STOP: dock verb changed/ambiguous: " + path.stem)
            continue
        verbs += ["look f5189", "do create f5189 kind=note title=" + pt.q(path.stem)
                  + " tags=verb on=f5189 text=" + pt.q(expected)]
    return verbs + commands


def prepare(snapshot):
    # Both pure planners must complete before the first copy write.
    navigation = prepare_navigation(snapshot)
    dock = prepare_dock(snapshot)
    return dock + navigation


def stage_copy(copy):
    if "-playtest-" not in copy.session:
        raise ValueError("STOP: only a disposable playtest session is allowed")
    query = urllib.parse.urlencode({"session": copy.session, "as": "hud-playtest"})
    with urllib.request.urlopen(copy.base + "/api/snapshot?" + query, timeout=60) as response:
        commands = prepare(json.load(response))
    for command in commands:
        said = copy.do(command, "hud-playtest")
        if ("ERR" in said or "refused" in said[:200]) and "already has that;" not in said:
            raise RuntimeError("STOP: staging refused in disposable copy: " + said[:400])
    print("staged combined navigation + slim dock on disposable copy only: " + copy.session, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--world", default="frontier-try")
    ap.add_argument("--small", action="store_true", help="1280x800 window request; retain native scale")
    a = ap.parse_args()
    base = pt.Copy

    class ReviewCopy(base):
        def __init__(self, name):
            super().__init__(name)
            try:
                stage_copy(self)
            except BaseException:
                self.close()
                raise

    pt.Copy = ReviewCopy
    if a.small:
        pt.SIZE = (1280, 800)
    args = SimpleNamespace(world=a.world, headless=False, apply=[], apply_as="hud-playtest",
                           breaks=[], only=["open", "partition_navigation"],
                           assume=["a7045", "a7223"], report="none", by="hud-playtest")
    return asyncio.run(pt.amain(args))


if __name__ == "__main__":
    sys.exit(main())
