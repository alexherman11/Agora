"""a10486: Send waits for a capture still arriving, in the guarded headless browser, on a copy (never Alex's screen,
captures folder or Conversation).

    python test_wait_send.py <draft> <signal> [world]

<draft> is a test draft (role=conversation-draft actor=worker-a10486) and <signal> a note with a `go` prop, both made
in the copy beforehand; the chat lenses must carry wait_patches.py's hunks there. screen.py serves a copy of the
copy and drives jeff-chat as the person would; this process plays the control screen: when a step sets the signal's
`go`, a thread runs capture.py's own Pending (the mark at the drag's end) and deliver, with a fake capture made in
the copy's session that arrives late (or never). Shots are screen-wait-*.png at the worktree root (ignored by git).
"""
import argparse
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

import capture as C

sys.path.insert(0, str(C.NOTATION))
import screen  # noqa: E402

WHO = "worker-a10486"
log = []


def say(*a):
    log.append(f"{time.strftime('%H:%M:%S')}.{int(time.time() * 1000) % 1000:03d} " + " ".join(map(str, a)))


def fake(session):
    return C.captures.make(session, WHO, {"rect": [0, 0, 40, 20], "native": "none", "refs": [], "image_size": None,
                                          "image_text": "a fake capture (a10486 test)"})


def player(port_box, session, draft, signal, done):
    while not port_box:
        time.sleep(0.1)
    args = argparse.Namespace(world=session, who=WHO, door=f"http://127.0.0.1:{port_box[0]}", draft=draft)
    for _ in range(300):
        try:
            if C._do(args, f"examine {signal}")[0]:
                break
        except Exception:
            pass
        time.sleep(0.2)
    seen = "none"
    while not done.is_set():
        try:
            ok, t = C._do(args, f"examine {signal}")
        except Exception as e:
            say("signal not read:", e)
            time.sleep(0.5)
            continue
        go = (re.search(r"\bgo=(\w+)", t) or [None, seen])[1] if ok else seen
        if go != seen:
            seen = go
            say("signal", go)
            if go in ("before", "chip"):     # the m10467 case: the capture lands while the words are being written
                p = C.Pending(args).start(); p.marked.wait(15); say("marked", p.token)
                time.sleep(0.3); cid = fake(session); say("made", cid, "delivered", C.deliver(cid, args, p)[0])
            elif go == "late":             # still being read when Send is pressed
                p = C.Pending(args).start(); p.marked.wait(15); say("marked", p.token)
                time.sleep(4.0); cid = fake(session); say("made", cid, "delivered", C.deliver(cid, args, p)[0])
            elif go == "two":
                p1 = C.Pending(args).start(); p2 = C.Pending(args).start(); p1.marked.wait(15); p2.marked.wait(15)
                say("marked", p1.token, p2.token)
                time.sleep(3.2); c1 = fake(session); say("made", c1, "delivered", C.deliver(c1, args, p1)[0])
                time.sleep(1.5); c2 = fake(session); say("made", c2, "delivered", C.deliver(c2, args, p2)[0])
            elif go == "never":
                p = C.Pending(args).start(); p.marked.wait(15); say("marked", p.token, "(never delivered)")
            elif go == "check":
                say("draft now:", " ".join(C._do(args, f"examine {draft}")[1].split())[:400])
                say("lines:", C._do(args, "read a5080 tail=8")[1][-700:])
                say("rows:", C._do(args, f"rows lines:a5080 by={WHO}")[1][-3000:])
        time.sleep(0.15)


def main():
    raise SystemExit(
        "Retained pre-takeover recipe is NOT acceptance-ready: it uses a copied Conversation "
        "and lacks --visible Guard admission. Replace its consumer with an isolated fixture "
        "feed and an admitted job-owned hidden lane before any browser launch."
    )
    draft, signal = sys.argv[1], sys.argv[2]
    world = sys.argv[3] if len(sys.argv) > 3 else "frontier-try"
    session = f"{world}-screen-{os.getpid()}"          # screen.py names its copy by its process: this one
    port_box, done = [], threading.Event()
    real = screen.free_port
    def free_port():                                  # the first asked for is the door's; Chrome's comes after
        p = real()
        if not port_box:
            port_box.append(p)
        return p
    screen.free_port = free_port
    say_ = f"chat/{draft}/dock/say"
    go = lambda v: ["desk", f"do prop {signal} go={v}"]
    dock = ["facts", f"chat/{draft}/dock", "2"]
    here = Path(__file__).resolve().parent
    shown, landed, sent = (["js", "@" + str(here / f)] for f in ("wait_shown.js", "wait_landed.js", "wait_sent.js"))
    # the page is waited on, not the clock: a mark reached the copy's page 1.5-2.5 s after its signal (ran), so each
    # drag's mark is seen painted before Send is pressed; a late capture lands ~1.5-2.5 s after Send
    steps = [
        # 1. the capture lands while the words are being written (Alex's m10467): Send carries it
        "click", say_, "type", "lets improve it:", *go("before"), *landed, "shot", "screen-wait-1-landed.png",
        "key", "Enter", *sent, "shot", "screen-wait-2-sent.png", "events", "2",
        # 2. still being read when Send is pressed: Send waits, then line and capture go together
        "click", say_, "type", "lets improve it:", *go("late"), *shown, "shot", "screen-wait-3-attaching.png",
        "key", "Enter", "wait", "300", "shot", "screen-wait-4-waiting.png", *sent, "shot", "screen-wait-5-joined.png", "events", "2",
        # 3. nothing pending: Send is instant
        "click", say_, "type", "nothing pending", "key", "Enter", *sent, "shot", "screen-wait-6-instant.png", "events", "1",
        # 4. two captures, then Send
        "click", say_, "type", "these two", *go("two"), *shown, "key", "Enter", "wait", "300", "shot", "screen-wait-7-two-waiting.png",
        *sent, "shot", "screen-wait-7-two.png", "events", "2",
        # 5. a capture that never arrives: nothing is sent, the words stay; then × stops the wait
        "click", say_, "type", "kept words", *go("never"), *shown, "key", "Enter", *sent,
        "shot", "screen-wait-8-never.png", *dock, "events", "1",
        "click", f"chat/{draft}/dock/coming/stop", "wait", "1500", "shot", "screen-wait-9-stopped.png", *dock,
        # 6. a chip that landed can still be removed (cap-5: the fifth this run makes)
        *go("chip"), *landed, *dock,
        "click", f"chat/{draft}/dock/attachments/cap-5/remove", "wait", "2500", *dock,
        *go("check"), "wait", "5000",
    ]
    t = threading.Thread(target=player, args=(port_box, session, draft, signal, done), daemon=True)
    t.start()
    sys.argv = ["screen.py", world, "--as", WHO, "--lens", "jeff-chat", "--size", "520x900", *steps]
    try:
        rc = screen.main()
    finally:
        done.set()
        t.join(10)
        print("\n--- the control screen's side")
        print("\n".join(log))
        made = C.captures.ROOT / session            # the fake captures this run made, in the copy's own session
        if made.exists() and made.name.startswith(f"{world}-screen-"):
            shutil.rmtree(made)
    return rc


if __name__ == "__main__":
    sys.exit(main() or 0)
