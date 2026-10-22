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

    # a5834: --draft auto finds the person's own draft as jeff-chat does (role=conversation-draft actor=<who>)
    who = "capture-test-a5834"
    ok, t = do(f'do create f571 kind=note title="capture auto test draft" role=conversation-draft actor={who}')
    m = re.search(r"created (a\d+)", t)
    auto = argparse.Namespace(world=world, who=who, door=None, draft="auto", do=do)
    found = C.own_draft(auto)
    okA, _ = C.deliver("cap-201", auto)
    _, t2 = do(f"examine {m.group(1)}") if m else (False, "")
    print("auto:", found, "| draft", m and m.group(1), "|", "context=cap-201" in t2)
    if not (m and found == m.group(1) and okA and "context=cap-201" in t2):
        fails.append(f"--draft auto should find {m and m.group(1)} and attach there, found {found}")
    if m:
        do(f"do remove {m.group(1)}")
    nobody = argparse.Namespace(world=world, who="nobody-has-this-draft", door=None, draft="auto", do=do)
    okN, saidN = C.deliver("cap-202", nobody)
    if okN or "no chat draft" not in saidN:
        fails.append(f"with no draft, auto should keep the capture and say so: {saidN}")
    fails += pending_cases(do, world)
    print("FAIL\n  " + "\n  ".join(fails) if fails else "ok")
    return 1 if fails else 0


def pending_cases(do, world):
    """a10486: the drag's end marks the draft (pending=<token>) before the capture is read; the capture replaces its
    token in one prop, on the draft that was open when the drag ended; a failed capture takes its token off."""
    fails = []
    who = "capture-test-a10486"

    def draft_of(title):
        ok, t = do(f'do create f571 kind=note title="{title}" role=conversation-draft actor={who}')
        m = re.search(r"created (a\d+)", t)
        return m and m.group(1)

    def held(d):
        _, t = do(f"examine {d}")
        return C._field(t, "context", r"cap-\d+"), C._field(t, "pending", r"wait-\d+-\d+")

    a = draft_of("pending test draft")
    args = argparse.Namespace(world=world, who=who, door=None, draft="auto", do=do)
    p1 = C.Pending(args).start()
    p1.marked.wait(60)
    now = held(a)
    print("marked at the drag's end:", now)
    if now != ([], [p1.token]):
        fails.append(f"the drag's end should mark the draft pending, before the capture: {now}")
    p2 = C.Pending(args).start()                    # a second drag while the first is still being read
    p2.marked.wait(60)
    ok2, _ = C.deliver("cap-302", args, p2)         # the second finishes first
    mid = held(a)
    ok1, _ = C.deliver("cap-301", args, p1)
    both = held(a)
    print("two, finished out of order:", mid, "->", both)
    if not (ok1 and ok2 and mid == (["cap-302"], [p1.token]) and both == (["cap-302", "cap-301"], [])):
        fails.append(f"two captures should each replace their own token: {mid} -> {both}")
    p3 = C.Pending(args).start()
    p3.marked.wait(60)
    p3.drop()                                       # explicit cancellation, not a processing failure
    if held(a) != (["cap-302", "cap-301"], []):
        fails.append(f"explicit cancellation should take its token off and leave the rest: {held(a)}")
    # the drag ended on draft a; a newer draft b becomes the person's before the capture is read: it still goes to a
    p4 = C.Pending(args).start()
    p4.marked.wait(60)
    do(f"do prop {a} role=old-draft")
    b = draft_of("the next draft")
    ok4, _ = C.deliver("cap-304", args, p4)
    print("the drag's draft:", held(a), "| the next:", held(b))
    if not (ok4 and held(a) == (["cap-302", "cap-301", "cap-304"], []) and held(b) == ([], [])):
        fails.append(f"a capture should go to the draft open when its drag ended: {held(a)} / {held(b)}")
    # A stopped control screen leaves the token; only an explicit cancellation clears it.
    p5 = C.Pending(args).start()
    p5.marked.wait(60)
    C.clear_pending(args)
    if held(b)[1]:
        fails.append(f"explicit cancellation should clear the token: {held(b)}")
    for d in (a, b):
        if d:
            do(f"do remove {d}")
    return fails


if __name__ == "__main__":
    sys.exit(main())
