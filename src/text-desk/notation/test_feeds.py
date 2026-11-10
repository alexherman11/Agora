"""a5988: feeds, what a watched agent is doing as rows a lens follows. Checks redaction (a secret-looking string never
reaches a row), the reader on Claude, Codex and resident records, the tail (only new bytes, capped), and the writer
(a feed exists only while something watches it, and reads in a lens as witnessed:feed-<actor>).

    python test_feeds.py
"""
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import feeds  # noqa: E402

fails = 0


def check(what, good, said=""):
    global fails
    fails += not good
    print(f"{'ok  ' if good else 'FAIL'} {what}" + ("" if good else f": {said}"))


# 1. secrets are redacted: every one of these must lose its secret part
SECRETS = {
    "sk-ant-api03-Zx8kQ2mN7pL4vR9tY1wE6uI3oP0aS5dF": "sk-ant-api03",
    "export OPENAI_API_KEY=sk-proj-AbCdEf1234567890GhIjKlMn": "AbCdEf1234567890",
    "git remote add o https://x:ghp_R4nd0mT0k3nV4lu3H3r3abcdEF12@github.com/a/b": "ghp_R4nd0m",
    "token: github_pat_11ABCDEFG0123456789_abcdefghijklmnop": "github_pat_11",
    "aws AKIAIOSFODNN7EXAMPLE in a log": "AKIAIOSFODNN7EXAMPLE",
    "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U":
        "dozjgNryP4J3",
    "curl -H 'Authorization: Basic dXNlcjpodW50ZXIy' https://example.com": "dXNlcjpodW50ZXIy",
    'config = {"password": "hunter2", "user": "alex"}': "hunter2",
    "DB_PASSWORD=correct-horse-battery": "correct-horse-battery",
    "my password is Tr0ub4dor&3 today": "Tr0ub4dor",
    "client_secret=7f3a9c0b2e8d4f6a1b5c": "7f3a9c0b2e8d4f6a1b5c",
    "postgres://admin:s3cr3tP4ss@db.local:5432/x": "s3cr3tP4ss",
    "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA1234\n-----END RSA PRIVATE KEY-----": "MIIEpAIBAAKCAQEA",
    "the key is Q2hhcmxpZTEyMzQ1Njc4OTBhYmNkZWZnaGlqa2xtbm9w and more": "Q2hhcmxpZTEyMzQ1Njc4",
    "slack xoxb-123456789012-abcdefghijkl": "xoxb-1234",
    "AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY": "AIzaSyD",
    "hex key 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08": "9f86d081884c7d659a2f",
}
for raw, secret in SECRETS.items():
    got = feeds.redact(raw)
    check(f"1. redacted: {raw[:46]!r}", secret not in got and "[redacted" in got, got)

# 2. what is not a secret stays readable (over-redaction is allowed, but these must survive)
PLAIN = [
    "python src/text-desk/notation/test_scene.py",
    "C:/Projects/Agora4/.worktrees/a5988/src/text-desk/notation/feeds.py",
    "git commit -m 'a5988: feeds' (d1a1ce5)",
    "commit 3f786850e387550fdab836ed7e6dc881de23001b",          # a 40-character sha1
    "author: alex, asked_by=jeff, max_tokens=4000, thinking_tokens: 12",
    "the token budget is fine; a password prompt was on screen",
    "do comment a5988 line=\"done\" mark=ask",
    "C:/Users/Alex/AppData/Local/Temp/claude/C--Projects-Agora4--worktrees-a5820/tasks/x.txt",
    "Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe",
    "session 3b241101-e2bb-4255-8caf-4136c566a962 resumed",
]
for raw in PLAIN:
    got = feeds.redact(raw)
    check(f"2. kept: {raw[:50]!r}", got == raw, got)

# 3. the reader: a Claude worker's stream
r = feeds.Reader()
ev = lambda d: {"at": 1760000000.0, "kind": "event", "data": d}     # noqa: E731
rows = []
for rec in [
    {"at": 1760000000.0, "kind": "start", "data": {"pid": 42}},
    {"at": 1760000001.0, "kind": "sent", "data": "Your commission (a1), asked by jeff: build it"},
    ev({"type": "system", "subtype": "init", "session_id": "s"}),
    ev({"type": "assistant", "thinking_duration_ms": 3200, "message": {"content": [{"type": "thinking", "thinking": "", "signature": "x"}]}}),
    ev({"type": "assistant", "message": {"content": [{"type": "text", "text": "I'll read the code first."}]}}),
    ev({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "C:/Projects/Agora4/.worktrees/a1/research/x.py"}}]}}),
    ev({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": "line one\nline two"}]}]}}),
    ev({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t2", "name": "Read", "input": {"file_path": "C:/x/.env"}}]}}),
    ev({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t2", "content": "API_KEY=abc"}]}}),
    ev({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t3", "name": "Edit", "input": {"file_path": "C:/Projects/Agora4/.worktrees/a1/research/x.py", "old_string": "a", "new_string": "b"}}]}}),
    ev({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t4", "name": "Bash", "input": {"command": "git commit -m 'a1: x'"}}]}}),
    ev({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t4", "is_error": True, "content": "nothing to commit"}]}}),
    ev({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t5", "name": "mcp__desk__desk", "input": {"line": "do comment a1 line=\"which way?\" mark=ask"}}]}}),
    ev({"type": "system", "subtype": "permission_denied", "tool_name": "Bash", "decision_reason": "not allowed"}),
    ev({"type": "rate_limit_event"}),
    ev({"type": "result", "is_error": False, "num_turns": 7}),
    {"at": 1760000009.0, "kind": "exit", "data": {"code": 1}},
]:
    rows += r.rows(rec)
kinds = [k for k, _ in rows]
check("3. a Claude worker's records read as start, heard, thought, said, read, result, ..., end, error "
      "(a permission refusal once, as its tool's result)",
      kinds == ["start", "heard", "thought", "said", "read", "result", "read", "result", "edit", "commit", "error",
                "ask", "end", "error"], kinds)
text = dict(enumerate(t for _, t in rows))
check("3. a thought with no words says how long and that its words are not kept", text[2] == "thought for 3 s (the words are not kept)", text[2])
check("3. paths are the repository's, not the worktree's", text[4] == "Read research/x.py" and text[8] == "Edit research/x.py", (text[4], text[8]))
check("3. a result of a call that touched .env is withheld whole", "abc" not in text[7] and ".env" in text[7], text[7])
check("3. a Read's result is how many lines, not the file", text[5] == "Read: 2 lines", text[5])
r3 = feeds.Reader()
r3.rows(ev({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "d", "name": "mcp__desk__desk", "input": {"line": "look a1"}}]}}))
got = r3.rows(ev({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "d", "content": [{"type": "text", "text":
      "> look a1\n!! since your last look: 3 changes by jeff\n   jeff: 3 edit in Board\na1 task \"x\" · open"}]}]}}))
check("3. a desk reply drops its echo and its 'since your last look' news", got == [("result", 'desk: a1 task "x" · open')], got)

# 4. a resident's reply: its > lines are acts, the rest is what it said
rows = feeds.Reader().rows(ev({"type": "assistant", "message": {"content": [
    {"type": "text", "text": "Looking at the board.\n> look Board :3\n> do comment a9 line=\"ok\""}]}}))
check("4. a resident's reply: said, then each > line as a desk act or comment",
      [k for k, _ in rows] == ["said", "desk", "comment"] and rows[1][1] == "look Board :3", rows)

# 5. Codex: items, and its last assistant event (which repeats its messages) is not said twice
r = feeds.Reader()
rows = []
for d in [{"type": "codex_event", "method": "item/agentMessage/delta", "data": {}},
          {"type": "codex_event", "method": "item/completed", "data": {"item": {"type": "reasoning", "summary": [], "content": []}}},
          {"type": "codex_event", "method": "item/completed", "data": {"item": {"type": "agentMessage", "text": "Checking."}}},
          {"type": "codex_event", "method": "item/completed", "data": {"item": {"type": "commandExecution", "command": "git status", "exitCode": 0, "aggregatedOutput": "clean"}}},
          {"type": "codex_event", "method": "item/completed", "data": {"item": {"type": "fileChange", "changes": [{"path": "C:/Projects/Agora4/.worktrees/a2/x.py"}]}}},
          {"type": "assistant", "message": {"content": [{"type": "text", "text": "Checking."}]}},
          {"type": "result", "is_error": True, "subtype": "failed", "result": "boom"}]:
    rows += r.rows(ev(d))
check("5. Codex items: thought, said, run, result, edit, error; the closing assistant event is not said again",
      [k for k, _ in rows] == ["thought", "said", "run", "result", "edit", "error"], rows)

# 6. the tail: only new bytes, whole lines, capped at CAP, a half-written line waits
tmp = Path(tempfile.mkdtemp(prefix="feeds-"))
try:
    t = tmp / "transcript.jsonl"
    line = lambda i: json.dumps(ev({"type": "assistant", "message": {"content": [{"type": "text", "text": f"step {i}"}]}})) + "\n"   # noqa: E731
    t.write_text("".join(line(i) for i in range(3)), encoding="utf-8")
    f = feeds.Feed(t)
    check("6. a first read takes what is there", f.read() == 3 and [x["text"] for x in f.rows] == ["step 0", "step 1", "step 2"])
    with t.open("a", encoding="utf-8") as h:
        h.write(line(3) + line(4)[:20])
    check("6. the next read takes only the new whole line", f.read() == 1 and f.rows[-1]["text"] == "step 3" and f.n == 4)
    with t.open("a", encoding="utf-8") as h:
        h.write(line(4)[20:])
    check("6. the half line is taken once it is whole", f.read() == 1 and f.rows[-1]["text"] == "step 4")
    with t.open("a", encoding="utf-8") as h:
        h.write("".join(line(i) for i in range(5, 5 + feeds.CAP + 50)))
    f.read()
    check("6. a feed keeps the last CAP rows, numbered as they came", len(f.rows) == feeds.CAP and f.rows[-1]["n"] == feeds.CAP + 55
          and f.rows[0]["n"] == 56, (len(f.rows), f.rows[0]["n"], f.rows[-1]["n"]))
    with t.open("a", encoding="utf-8") as h:
        h.write(json.dumps(ev({"type": "assistant", "message": {"content": [{"type": "text", "text": "key sk-ant-api03-Zx8kQ2mN7pL4vR9tY1wE6uI3oP0aS5dF"}]}})) + "\n")
    f.read()
    check("6. a secret in the stream is redacted in the row", "Zx8kQ2" not in f.rows[-1]["text"] and "[redacted" in f.rows[-1]["text"], f.rows[-1])
    big = tmp / "big.jsonl"
    big.write_text("x" * 100 + "\n" + "".join(line(i) for i in range(feeds.SEED // len(line(0)) + 100)), encoding="utf-8")
    g = feeds.Feed(big)
    g.read()
    check("6. a long transcript is read from its tail (SEED bytes), starting at a whole line",
          g.offset == big.stat().st_size and 0 < g.n <= feeds.SEED // len(line(0)) + 1 and g.rows[-1]["text"].startswith("step"), g.n)

    # 7. the writer: a feed is written only while something watches it, and a lens reads it
    import witnessed
    world = f"feedtest{int(time.time())}"
    state = tmp / "state"
    (state / "worker-a1").mkdir(parents=True)
    shutil.copy(t, state / "worker-a1" / "transcript.jsonl")

    class W:
        """A world with a viewer note standing `lens` on `viewing`, a card a1 its worker works on, a note a2 with no
        agent, and a resident's corner f3 (surfaces carry their props on the node)."""
        def __init__(self, viewing=None, lens="home-feed"):
            self.subjects = {"s1": {"title": "Alex's viewer", "props": {"role": "home-view", "viewing": viewing or "", "with": lens}},
                             "s2": {"title": "The card", "props": {"commission": "working", "worker": "worker-a1"}},
                             "s3": {"title": "A plain note"}}
            self.nodes = {"a1": {"subject": "s2"}, "a2": {"subject": "s3"},
                          "f3": {"subject": "s4", "title": "Pike's corner", "props": {"role": "resident", "actor": "pike"}}}
    corners = {"f3": W().nodes["f3"]}
    feeds.GAP = 0
    fd = feeds.Feeds(world, state)
    fd.step(W(None), corners)
    check("7. nobody watching: no feed file", witnessed.read(world, "feed-a1") is None)
    fd.step(W("a1", lens="doc-page"), corners)
    check("7. a viewer showing the card with another lens is not watching", witnessed.read(world, "feed-a1") is None)
    fd.step(W("a1"), corners, {"worker-a1": "working"})
    doc = witnessed.read(world, "feed-a1")
    head = (doc or {"rows": [{}]})["rows"][0]
    check("7. home-feed stood on a card: its worker's feed is written as feed-<card>, a head row first",
          doc is not None and head.get("kind") == "head" and head.get("who") == "worker-a1" and head.get("card") == "a1"
          and head.get("title") == "The card" and head.get("state") == "working" and head.get("last") == fd.feeds["a1"].n
          and len(doc["rows"]) == feeds.CAP + 1, head)
    st = witnessed.stamp(world)
    fd.step(W("a1"), corners, {"worker-a1": "working"})
    check("7. nothing new: the file is not rewritten (no repaint for every painter)", witnessed.stamp(world) == st)
    with (state / "worker-a1" / "transcript.jsonl").open("a", encoding="utf-8") as h:
        h.write(line("new"))
    time.sleep(0.02)
    fd.step(W("a1"), corners, {"worker-a1": "working"})
    doc = witnessed.read(world, "feed-a1")
    check("7. a new event is written at the next pass", doc["rows"][-1]["text"] == "step new" and witnessed.stamp(world) != st)
    feeds.GAP = 60
    st = witnessed.stamp(world)
    with (state / "worker-a1" / "transcript.jsonl").open("a", encoding="utf-8") as h:
        h.write(line("later"))
    fd.step(W("a1"), corners, {"worker-a1": "working"})
    check("7. within GAP of the last write, new lines wait (a feed repaints at most every GAP s)", witnessed.stamp(world) == st)
    feeds.GAP = 0
    fd.step(W("a1"), corners, {"worker-a1": "working"})
    check("7. ... and come at the next write", witnessed.read(world, "feed-a1")["rows"][-1]["text"] == "step later")
    fd.step(W("f3"), corners)
    check("7. the viewer moves on: the card's feed is removed; a resident's corner gives the resident's (none kept here)",
          witnessed.read(world, "feed-a1") is None and
          witnessed.read(world, "feed-f3")["rows"][0]["who"] == "pike" and
          witnessed.read(world, "feed-f3")["rows"][0]["state"] == "not kept by this house")
    fd.step(W("a2"), corners)
    check("7. a thing with no agent says so", witnessed.read(world, "feed-a2")["rows"][0]["state"] == "no agent on it")
    fd.step(W(None), corners)
    check("7. unwatched again: no feed files left", witnessed.stamp(world) == ())

    # 8. a lens reads it through the witnessed source, as a painter would
    fd.step(W("a1"), corners, {"worker-a1": "waiting"})
    import scene
    rows = scene.rows(type("D", (), {"_session": world, "world": None})(), "witnessed:feed-a1 kind=head")
    check("8. witnessed:feed-<id> kind=head is the head row, fields as written",
          len(rows) == 1 and rows[0].get("state") == "waiting" and rows[0].get("card") == "a1", rows)
    fd.step(W(None), corners)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
    import witnessed
    d = witnessed._dir(world) if "world" in dir() else None
    if d is not None and d.parent.exists():
        shutil.rmtree(d.parent, ignore_errors=True)

print(f"\n{'all ok' if not fails else f'{fails} FAILED'}")
sys.exit(1 if fails else 0)
