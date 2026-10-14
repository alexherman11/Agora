"""Delivery of a capture to a chat draft (a5062; Codex m5109), on a copy of the world, never Alex's own draft.

    python test_deliver.py [world]          (default frontier-try: the copy the house gives a worker)

Makes a note shaped like Alex's draft (role=conversation-draft, context empty) in the copy, as alex, and checks that
capture.deliver puts ids on it the agreed way: 'do prop <draft> context=<ids>', joined in order, never twice, at most
eight; a ninth is refused and left off. Each desk line goes through explore.py, as a person's would.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

import capture as C

EXPLORE = C.NOTATION / "explore.py"


def desk(world, who):
    def do(line):
        p = subprocess.run([sys.executable, str(EXPLORE), world, "--as", who], input=line + "\n", capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env={**__import__("os").environ, "DESKD": "off"})
        t = p.stdout + p.stderr
        return not re.search(r"(^|\n)ERR\b", t), t
    return do


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
    do = desk(world, "alex")
    fails = []
    ok, t = do('do create f571 kind=note title="capture delivery test draft" role=conversation-draft actor=alex')
    m = re.search(r"created (a\d+)", t)
    if not (ok and m):
        print("could not make a test draft:", t[-600:])
        return 1
    draft = m.group(1)
    print("test draft", draft, "in", world)
    args = argparse.Namespace(world=world, who="alex", door=None, draft=draft, do=do)

    def context():
        _, t = do(f"examine {draft}")
        mm = re.search(r"\bcontext=(.*)", t)
        return re.findall(r"cap-\d+", re.split(r"\s[\w-]+=|\s·", mm.group(1))[0]) if mm else []

    ok1, _ = C.deliver("cap-101", args)
    ok2, _ = C.deliver("cap-102", args)
    now = context()
    print("after two:", now)
    if not (ok1 and ok2 and now == ["cap-101", "cap-102"]):
        fails.append(f"two captures should be joined in order, got {now}")
    C.deliver("cap-101", args)
    if context() != ["cap-101", "cap-102"]:
        fails.append(f"a capture already there should not be added again: {context()}")
    for n in range(103, 109):
        C.deliver(f"cap-{n}", args)
    eight = context()
    ok9, said = C.deliver("cap-109", args)
    print("after eight and a ninth:", context(), "| the ninth:", said)
    if len(eight) != 8 or ok9 or context() != eight:
        fails.append(f"a ninth should be refused and left off: {context()}")
    do(f"do remove {draft}")
    print("FAIL\n  " + "\n  ".join(fails) if fails else "ok")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
