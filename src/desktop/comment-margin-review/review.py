"""Copy-only margin wrapper preflight and guarded before/after capture.

No live endpoint, source overlay, writer-state change or Conversation sends.
Uses existing playtest Copy and screen.run for copy/Guard/browser ownership.
"""
import argparse
import asyncio
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hud_playtest as pt
import sandbox_window


OLD_WRITTEN = """          margin : column
            share 1
            role aside
            talked : column
              only when talk != ""
              list : column
                of lines:$d.talk about=$d.item as c
                each remark
            older : column
              of comments:$d.item as oc
              each oldremark"""
OLD_ENTRY = """  margin : column
    share 1
    role aside
    talked : column
      only when ($d.talk or "") != ""
      list : column
        of lines:$d.talk about=$p.item as c
        each premark
    older : column
      of comments:$p.item as oc
      each oldremark"""


def patches(text):
    out = []
    for old in (OLD_WRITTEN, OLD_ENTRY):
        if text.count(old) != 1:
            raise ValueError("STOP: expected margin block missing or ambiguous")
        lines = old.splitlines()
        indent = len(lines[2]) - len(lines[2].lstrip())
        new = "\n".join(lines[:3] + [
            " " * indent + "notes : column",
            " " * (indent + 2) + "role beside",
            *["  " + line for line in lines[3:]]])
        out.append({"old": old, "new": new})
    return out


MEASURE = r"""JSON.stringify((() => {
  const box = e => {const r=e.getBoundingClientRect();return {
    key:e.dataset.key,x:r.x,y:r.y,w:r.width,h:r.height,scroll:e.scrollTop,
    scrollHeight:e.scrollHeight,overflow:getComputedStyle(e).overflowY};};
  const all=[...document.querySelectorAll('#paint [data-key]')];
  return {viewport:[innerWidth,innerHeight,devicePixelRatio],
    visibility:document.visibilityState,
    paragraphs:all.filter(e=>e.dataset.key.endsWith('/words')&&e.getClientRects().length).map(box),
    margins:all.filter(e=>/(?:\/margin|\/notes)$/.test(e.dataset.key)&&e.getClientRects().length).map(box),
    floats:[...document.querySelectorAll('[data-role~="beside"]')].map(box),
    pageScroll:[scrollX,scrollY],
    status:document.getElementById('status')?.textContent};
})())"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--world", default="frontier-try")
    ap.add_argument("--size", default="2560x1440")
    args = ap.parse_args()
    # Never sweep another run's stale copies from this acceptance driver.
    pt.sweep = lambda: None
    copy = pt.Copy(args.world)
    try:
        if "-playtest-" not in copy.session:
            raise ValueError("STOP: not a disposable playtest copy")
        query = urllib.parse.urlencode({"session": copy.session, "as": "worker-a8030"})
        with urllib.request.urlopen(copy.base + "/api/snapshot?" + query, timeout=60) as r:
            snapshot = json.load(r)
        lenses = [(n["id"], snapshot["subjects"][n["subject"]])
                  for n in snapshot["nodes"].values()
                  if n.get("subject") in snapshot["subjects"]
                  and snapshot["subjects"][n["subject"]].get("title") == "doc-page"
                  and "lens" in snapshot["subjects"][n["subject"]].get("tags", [])]
        if len(lenses) != 1:
            raise ValueError("STOP: doc-page lens missing or ambiguous")
        ident, subject = lenses[0]
        hunks = patches(subject["text"])
        manifest = {"copy": copy.session, "event_total": copy.at(), "lens": ident,
                    "before_sha256": hashlib.sha256(subject["text"].encode()).hexdigest(),
                    "hunks": hunks, "reverse": [{"old": h["new"], "new": h["old"]} for h in hunks]}
        (HERE / "patches.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print("preflight: " + json.dumps({k: v for k, v in manifest.items()
                                        if k not in ("hunks", "reverse")}), flush=True)
        commands = []
        for h in hunks:
            commands += ["desk", "read " + ident, "desk",
                         f"do replace {ident} old={pt.q(h['old'])} new={pt.q(h['new'])}"]
        steps = ["js", MEASURE, "shot", str(HERE / ("screen-before-" + args.size + ".png")),
                 *commands, "wait", "2", "js", MEASURE,
                 "shot", str(HERE / ("screen-after-" + args.size + ".png"))]
        screen = pt.screen
        screen.VISIBLE, screen.SB, screen.SCALE = "sandbox", sandbox_window, 1.5
        url = copy.url("doc-page", "alex") + "&on=f4358"
        asyncio.run(screen.run(url, steps, tuple(map(int, args.size.split("x"))), [0]))
    finally:
        copy.close()


if __name__ == "__main__":
    main()
