"""a6265: usage, how full each agent's context is and how much of Alex's limit is used, as witnessed:usage rows.

Checks the reader on made-up Claude and Codex transcripts (the shapes the house logs: assistant usage, result
modelUsage, rate_limit_event, thread/tokenUsage/updated), that a number with no source is LEFT OUT (never guessed, never
0), the writer (written only when changed), and the At work row lens (research/window-lab/at-work): an agent whose
context cannot be read shows no bar and no per cent, one that can shows its number.

    python test_usage.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import usage       # noqa: E402
import witnessed   # noqa: E402

FAILED = []


def check(what, ok):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        FAILED.append(what)


def ev(at, data, kind="event"):
    return {"at": at, "kind": kind, "data": data}


def write(path, recs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


def claude_msg(at, inp, cc, cr, model="claude-test-1", parent=None):
    d = {"type": "assistant", "message": {"model": model, "usage": {"input_tokens": inp, "cache_creation_input_tokens": cc,
                                                                     "cache_read_input_tokens": cr, "output_tokens": 9}}}
    if parent:
        d["parent_tool_use_id"] = parent
    return ev(at, d)


def init(at, sid, model="claude-test-1"):
    return ev(at, {"type": "system", "subtype": "init", "session_id": sid, "model": model})


def result(at, window, model="claude-test-1"):
    return ev(at, {"type": "result", "is_error": False, "modelUsage": {model: {"contextWindow": window}}})


def limit(at, five, five_at, week, week_at):
    return ev(at, {"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
        "five_hour": {"utilization": five, "resetsAt": five_at}, "seven_day": {"utilization": week, "resetsAt": week_at}}}})


def main():
    now = time.time()
    world = f"_test_usage_{os.getpid()}"
    base = HERE / "house-state" / world
    shutil.rmtree(base, ignore_errors=True)
    try:
        # 1. the house as house.json says: residents jeff (f1, resting) and sable (f2, working), workers on cards a1..a4
        st = {"pid": os.getpid(), "beat": now, "world": world,
              "residents": {"f1": {"actor": "jeff", "doing": "resting"}, "f2": {"actor": "sable", "doing": "working"},
                            "f3": {"actor": "gone", "doing": "stopped"}},
              "workers": {"a1": {"actor": "worker-a1", "doing": "working"}, "a2": {"actor": "worker-a2", "doing": "working"},
                          "a3": {"actor": "worker-a3", "doing": "waiting"}, "a4": {"actor": "worker-a4", "doing": "working"}}}
        base.mkdir(parents=True)
        (base / "house.json").write_text(json.dumps(st), encoding="utf-8")
        # jeff: ended a turn (own window 10000), context 100+200+700 = 1000; a sub-agent's bigger message is not his
        write(base / "f1" / "transcript.jsonl", [init(now - 600, "s1"), claude_msg(now - 590, 100, 200, 700),
                                                 claude_msg(now - 585, 5, 0, 9000, parent="toolu_1"),
                                                 result(now - 580, 10000),
                                                 limit(now - 580, 0.42, now + 3600, 0.13, now - 10)])
        # sable: working, same model, never ended a turn; quiet for 20 minutes
        write(base / "f2" / "transcript.jsonl", [ev(now - 1300, {"t": "x"}, "sent"), init(now - 1250, "s2"),
                                                 claude_msg(now - 1200, 1, 2, 3997)])
        # worker-a1: a model no one in this house has ended a turn with: its window is unknown
        write(base / "worker-a1" / "transcript.jsonl", [init(now - 60, "s3", "claude-other"),
                                                        claude_msg(now - 50, 1, 1, 998, "claude-other")])
        # worker-a2: Codex, context 2584 of 25840 (10%), then its process starts again (a new thread): unknown
        tok = {"type": "codex_event", "method": "thread/tokenUsage/updated",
               "data": {"threadId": "t1", "tokenUsage": {"last": {"totalTokens": 2584}, "modelContextWindow": 25840}}}
        write(base / "worker-a2" / "transcript.jsonl", [ev(now - 100, tok)])
        # worker-a3: a fresh session after a reading: the old one's fullness says nothing
        write(base / "worker-a3" / "transcript.jsonl", [init(now - 90, "s4"), claude_msg(now - 80, 1, 1, 4998),
                                                        init(now - 70, "s5")])
        # worker-a4: no transcript at all yet; held by the limit until an hour from now
        (base / "worker-a4").mkdir()
        (base / "worker-a4" / "state.json").write_text(json.dumps({"retry_at": now + 3600}), encoding="utf-8")

        u = usage.Usage(world, base)
        rows = u.rows(now)
        by = {r.get("corner"): r for r in rows if r["kind"] == "agent"}
        lim = rows[0]
        check("1. one limit row first, then one row per resident and live worker (a stopped one is left out)",
              lim["kind"] == "limit" and sorted(by) == ["a1", "a2", "a3", "a4", "f1", "f2"])
        check("1. jeff: 1000 of his own 10000 is 10%, from his own result; the sub-agent's message is passed over",
              by["f1"].get("ctx") == 10 and by["f1"].get("ctxpct") == "10%" and by["f1"].get("window_from") == "own"
              and by["f1"].get("tokens") == 1000)
        check("1. sable: the same model's window from jeff's result (window_from=house): 4000 is 40%",
              by["f2"].get("ctx") == 40 and by["f2"].get("window_from") == "house")
        check("1. sable has been silent 20 minutes while working: quiet=20m; since is when her turn was sent",
              by["f2"].get("quiet") == "20m" and by["f2"].get("since") == usage.clock(now - 1300, now, day=True))
        check("2. UNKNOWN: a model with no window in this house has no ctx, no ctxpct, no tokens (not 0, not a guess)",
              not {"ctx", "ctxpct", "tokens", "window"} & set(by["a1"]) and by["a1"].get("model") == "claude-other")
        check("1. codex: last.totalTokens of modelContextWindow, 10%", by["a2"].get("ctx") == 10 and by["a2"]["provider"] == "codex")
        check("2. UNKNOWN: a fresh session after a reading has no ctx", "ctx" not in by["a3"])
        check("2. UNKNOWN: no transcript yet: no provider, model or ctx; held by the limit until its retry",
              not {"ctx", "provider", "model"} & set(by["a4"]) and by["a4"].get("held") == usage.clock(now + 3600, now))
        check("1. the limit: five-hour 42% with its reset", lim.get("five") == 42 and lim.get("five_resets") == usage.clock(now + 3600, now))
        check("2. UNKNOWN: a week whose reset time has passed is left out (its use since is unknown, not 13%)",
              "week" not in lim and "week_resets" not in lim)
        check("2. UNKNOWN: no reading at all: a limit row with no numbers", usage.limit_row(None, now) == {"kind": "limit", "provider": "claude"})
        write(base / "worker-a2" / "transcript.jsonl", [ev(now - 6, {}, "start"), init(now - 5, "t1", "gpt-test")])
        check("1. Codex starts again and resumes its thread (init names it): the reading stands",
              {r.get("corner"): r for r in u.rows(now)}["a2"].get("ctx") == 10)
        write(base / "worker-a2" / "transcript.jsonl", [ev(now - 4, {}, "start"), init(now - 3, "t2", "gpt-test")])
        check("2. UNKNOWN: Codex starts on another thread: the old thread's context is dropped",
              "ctx" not in {r.get("corner"): r for r in u.rows(now)}["a2"])
        check("1. quiet words are coarse: 9 min none, 12 min 10m, 50 min 45m, 150 min 2h", [usage.quiet_word(m) for m in (9, 12, 50, 150)] == ["", "10m", "45m", "2h"])

        # 3. the writer: written as witnessed:usage, not rewritten when nothing changed
        u2 = usage.Usage(world, base)
        u2.step(force=True)
        doc = witnessed.read(world, "usage")
        check("3. written: witnessed:usage holds the rows", doc is not None and doc["rows"][0]["kind"] == "limit")
        stamp = witnessed.stamp(world)
        time.sleep(0.05)
        u2.step(force=True)
        check("3. nothing changed: the file is not rewritten (no repaint for every painter)", witnessed.stamp(world) == stamp)
        check("3. within GAP of the last pass, nothing is read or written", u2.step() is None)
        import scene
        got = scene.rows(type("D", (), {"_session": world, "world": None})(), "witnessed:usage kind=agent corner=a1")
        check("3. a lens reads it: witnessed:usage kind=agent corner=a1 is worker-a1's row, with no ctx field",
              len(got) == 1 and got[0]["actor"] == "worker-a1" and not (got[0].get("ctx") or got[0].get("ctxpct")))

        # 4. the row lens on a world: unknown shows nothing, known shows its number
        lens_check(now)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print(f"\n{'FAILED: ' + str(len(FAILED)) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


def lens_check(now):
    lab = HERE.parents[1] / "window-lab" / "at-work"
    sys.path.insert(0, str(lab))
    import put
    world = f"_test_usage_lens_{os.getpid()}"
    me = "worker-test"

    def desk(lines):
        r = subprocess.run([sys.executable, str(HERE / "explore.py"), world, "--as", me, "--whole"],
                           input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=HERE)
        return r.stdout + r.stderr

    try:
        style = put.style_text()
        room = (re.findall(r"\b(f\d+)\b", desk(["look"])) or ["f1"])[0]
        out = desk([f"look {room}", f"do create {room} kind=note title=direction-living tags=style text={put.q(style)}",
                    f"do create {room} kind=note title=house-at-work-row tags=lens style=direction-living "
                    f"text={put.q((lab / 'house-at-work-row.lens').read_text(encoding='utf-8'))}",
                    f"do create {room} kind=note title=viewer role=home-view actor={me}",
                    f'do create {room} kind=task title="Mend the kettle" commission=working worker=worker-k asked_by=jeff'])
        ids = re.findall(r"→ created (a\d+)", out)
        check("4. a world with the style, the row lens, a viewer note and a card (no refusal)",
              len(ids) == 4 and "does not compile" not in out and "ERR" not in out)
        if len(ids) < 4:
            print("\n".join(l[:300] for l in out.splitlines() if l.startswith(("ERR", "ok", "~", "stopped"))))
            return
        card = ids[3]
        row = {"kind": "agent", "corner": card, "actor": "worker-k", "doing": "working", "provider": "claude",
               "model": "claude-other", "since": "09:30"}
        witnessed.write(world, "usage", [{"kind": "limit", "provider": "claude"}, row], by="test")
        seen = desk([f"look {card}", f"scene house-at-work-row on {card}"])
        check("4. UNKNOWN: the line says what and the status, and draws no bar and no per cent",
              "Mend the kettle" in seen and "working" in seen and "%" not in seen and "<svg" not in seen)
        witnessed.write(world, "usage", [{"kind": "limit", "provider": "claude"},
                                         {**row, "ctx": 62, "ctxpct": "62%", "tokens": 620, "window": 1000,
                                          "ctxwords": "620 of 1k tokens"}], by="test")
        seen = desk([f"look {card}", f"scene house-at-work-row on {card}"])
        check("4. known: the line shows 62% and its bar", "62%" in seen and "width='62'" in seen)
    finally:
        witnessed.clear(world, "usage")
        shutil.rmtree(HERE / "house-state" / world, ignore_errors=True)
        for p in (HERE / "sessions").glob(f"{world}*"):
            p.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
