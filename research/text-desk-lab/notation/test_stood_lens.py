# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_stood_lens (a5949; Sable's a4270, 'a lens stood on a thing'; Pike's anchors, c5957).

    python test_stood_lens.py

Imagined use: Alex reads a design in the home base's viewer, opens it 'with' another lens by typing its name, comments
on words in it, and the author then rewrites the passage. Builds its own small world (roomworld.py).
  1. a lens stood on a thing starts on it: `scene <lens> on <id>`, and a lens it places starts there too;
  2. stands_on= refuses what a lens cannot stand on, in words; an address that names no thing is refused;
  3. a lens named from data (`lens $v.with`) that is missing or contains itself is one line, and its placer is drawn;
     a lens named in the text still refuses its placer, as before;
  4. a comment's anchor: has ignores how white space falls; section-of, words-before, words-after find the words
     exactly and say none when they are gone.
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1200]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
ME = "juniper"
HOME = R.HOME


def say(*lines, me=ME):
    W.me = me
    token, out = uuid.uuid4().hex, ""
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out += (r.get("text") or "") + (r.get("error") or "") + "\n"
    return out


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


import expr as X   # noqa: E402
import lens_ir     # noqa: E402
import scene       # noqa: E402

DOC = "## Why\nTwo people can never\ntype in one paragraph.\n## How\nOne text per document."
made = say(f"look {HOME}", f"do create {HOME} kind=note title=Plan role=doc text={q(DOC)}")
doc = made.split("→ created ")[1].split()[0]
page = 'page : column\n  t : text "page of $title"\n  inner : column\n    lens pagebits\n'
bits = 'b : text "bits of $title ($item)"\n'
viewer = ('v : column\n  of ' + doc + ' as d\n  each one\none : column\n  named : column\n    lens $d.with\n'
          '  self : column\n    lens $d.title\n  after : text "still drawn"\n')
say(f"look {HOME}", f"do create {HOME} kind=note title=page tags=lens text={q(page)}",
    f"do create {HOME} kind=note title=pagebits tags=lens stands_on=prop:role=doc text={q(bits)}",
    f"do create {HOME} kind=note title=Plan2view tags=lens text={q(viewer)}")

# 1. stood on a thing
out = say(f"scene page on {doc}")
check("scene <lens> on <id>: the lens starts on that thing", "page of Plan" in out, out)
check("a lens it places starts on the same thing", f"bits of Plan ({doc})" in out, out)
sc, _ = lens_ir.scene_for(D, "page", on=doc)
check("the scene's def says what it stands on (on=)", sc["def"].get("on") == doc, sc["def"])

# 2. stands_on and an address not believed
out = say(f"scene page on {R.HOME}")
check("stands_on= refuses a thing it does not stand on, in words, and the placer is drawn",
      "stands on prop:role=doc" in out and "is not one" in out and "page of" in out, out)
sc, text = lens_ir.scene_for(D, "page", on="a999999")
check("on= naming no thing is refused in words, in the one place a scene is built (may_read)",
      "no thing has that id" in text and "page of" not in text, text)

# 3. named from data
out = say(f"scene Plan2view")
check("a data-named lens that is missing is one line, and the rest is drawn",
      "cannot be drawn here" in out and "still drawn" in out, out)
check("a data-named lens that contains itself is one line too (the viewer opened on itself)",
      out.count("cannot be drawn here") == 2, out)
say(f"look {HOME}", f"do create {HOME} kind=note title=selfish tags=lens text={q('s : column' + chr(10) + '  lens selfish' + chr(10))}")
out = say("scene selfish")
check("a lens named in its own text still refuses (an author's mistake, not data)", "contains itself" in out, out)

# 4. anchors
T = X.Value("text", DOC)


def call(name, words):
    return X.call(name, [T, X.Value("text", words)])


check("has ignores how white space falls: words quoted across a line break are found",
      X._cmp("has", T, X.Value("text", "never type in one")).v is True)
check("section-of: the heading over the words", call("section-of", "never type").v == "Why")
check("section-of: words under a later heading", call("section-of", "One text").v == "How")
check("words-before / words-after: the words either side, exactly",
      call("words-before", "never type").v == "## Why Two people can" and call("words-after", "never type").v == "in one paragraph. ## How One")
check("gone words are none, with the reason, never a guess",
      call("section-of", "two people can never").is_none() and call("words-before", "Three people").is_none())

if fails:
    print(f"{len(fails)} failed")
    sys.exit(1)
print("all passed")
