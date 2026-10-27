"""proof_house: JEFF in a hidden copy of Alex's desktop, run by the house against a scripted model. Never a live model,
never a window on Alex's screen (sandbox.py: port 8830, every module headless).

    python proof_house.py [--port 8830] [--out evidence/house-proof.json]

What it checks, each as ran:
  1. the house words answer at once (house.who)
  2. want=awake warms his process; Alex's line in the Conversation wakes him; his words come back into it, as JEFF
  3. the model was offered exactly the three door tools (see, do, lines) and no others
  4. one lines call: a refused line refuses only itself, the rest ran (his line in Shop talk exists)
  5. a line in Shop talk without @jeff does not wake him; with @jeff it does
  6. with the house off, a line to him waits; on house again, he is told it (the durable cursor)
  7. Alex's line -> JEFF's first words, in ms (the scripted model answers at once, so this is the house's own cost)
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESK = HERE.parents[2] / "window-lab" / "kernel-desktop"
PY = HERE.parents[3] / ".venv" / "Scripts" / "python.exe"
NAME = "house-proof"
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


class Proof:
    def __init__(self, port):
        self.port, self.checks = port, []
        self.world = DESK / "state" / f"world-{NAME}"

    def check(self, name, ok, detail=""):
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("ok   " if ok else "FAIL ") + name + (f" · {detail}" if detail else ""), flush=True)

    def token(self, signer):
        s = json.loads((self.world / "keep" / "sessions.json").read_text(encoding="utf-8"))
        return next(t for t, v in s.items() if v.get("signer") == signer)

    def line(self, line, who="alex", route=None):
        route = route or ("/see" if line.split()[0] in ("look", "rows", "chat", "house.who", "status") else "/do")
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{route}", json.dumps({"line": line}).encode(),
                                     {"Content-Type": "application/json", "Authorization": "Bearer " + self.token(who)})
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=20) as r:
            return json.load(r)

    def lines_of(self, chat):
        return self.line(f"chat {chat} limit=50")["rows"]

    def until(self, test, s=40):
        end = time.time() + s
        while time.time() < end:
            v = test()
            if v:
                return v
            time.sleep(0.05)
        return test()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8830)
    ap.add_argument("--fake-port", type=int, default=8841)
    ap.add_argument("--out", default=str(HERE / "evidence" / "house-proof.json"))
    a = ap.parse_args(argv)
    p = Proof(a.port)
    log = HERE / "evidence" / "fake-model-log.jsonl"
    log.parent.mkdir(exist_ok=True)
    log.unlink(missing_ok=True)
    procs = []
    try:
        procs.append(subprocess.Popen([str(PY), str(HERE / "fake_model.py"), str(a.fake_port), str(log)],
                                      stdout=subprocess.DEVNULL, creationflags=NO_WINDOW))
        subprocess.run([str(PY), str(DESK / "sandbox.py"), "fresh", "--name", NAME], check=True,
                       stdout=subprocess.DEVNULL, creationflags=NO_WINDOW)
        env = dict(os.environ, HOUSE_FAKE_MODEL=f"http://127.0.0.1:{a.fake_port}")
        procs.append(subprocess.Popen([str(PY), str(DESK / "sandbox.py"), "run", "--name", NAME, "--port", str(a.port)],
                                      env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      creationflags=NO_WINDOW))

        def up():
            try:
                return "runs 1 agent" in p.line("house.who").get("text", "")
            except Exception:                       # noqa: BLE001
                return False
        p.check("the sandbox and the house came up", p.until(up, 60))
        rows = p.line("rows house-agent")["rows"]
        agent, jeff = rows[0]["id"], rows[0]["person"]
        convo = next(r["id"] for r in p.line("rows chat")["rows"] if r.get("name") == "Conversation")
        shop = next(r["id"] for r in p.line("rows chat")["rows"] if r.get("name") == "Shop talk")
        t = time.time()
        who = p.line("house.who")
        p.check("house.who answers at once", time.time() - t < 1.0 and "JEFF" in who["text"],
                f"{(time.time() - t) * 1000:.0f} ms: {who['text'].splitlines()[-1].strip()}")

        p.line(f"look {agent}")
        p.line(f"set {agent} want=awake")
        p.check("want=awake warms his process (no turn)",
                p.until(lambda: "idle" in p.line("house.who")["text"], 30), p.line("house.who")["text"].splitlines()[-1].strip())

        t0 = time.time()
        said = p.line(f"say {convo} hello JEFF RUN: look {convo} | rows chat | frobnicate now | say {shop} hi from JEFF")
        p.check("Alex's line in the Conversation speaks to JEFF", "to JEFF" in said["text"], said["text"])

        mine = int(said["made"][0][2:])                   # the copy keeps the live Conversation: only lines after ours

        def jeff_said():
            return [r for r in p.lines_of(convo) if r["by"] == "JEFF" and int(r["id"][2:]) > mine]
        first = p.until(jeff_said)
        ms = int((time.time() - t0) * 1000)
        p.check("JEFF's words come back into the Conversation, as JEFF", first and first[0]["text"] == "On it.",
                f"{ms} ms to first words (scripted model); {first[0]['text'] if first else 'nothing'}")
        done = p.until(lambda: jeff_said()[1:] and jeff_said())
        p.check("his turn ends with his words on the result", done and done[1]["text"].startswith("Done:"),
                done[1]["text"][:160] if done else "")
        shop_lines = p.lines_of(shop)
        p.check("one lines call: a refused line refuses only itself; the line after it ran",
                any(r["by"] == "JEFF" and "hi from JEFF" in r["text"] and int(r["id"][2:]) > mine for r in shop_lines),
                "frobnicate refused, say in Shop talk ran")
        reqs = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
        offered = sorted(set(sum((r["tools"] for r in reqs if r["tools"]), [])))
        door = [t for t in offered if t.startswith("mcp__")]
        other = [t for t in offered if not t.startswith("mcp__") and t != "DeferredToolPlaceholder"]
        p.check("the model was offered the three door tools (see, do, lines) and no built-in tool",
                door == ["mcp__agora__do", "mcp__agora__lines", "mcp__agora__see"] and not other, ", ".join(offered))
        result = next((r["result"] for r in reqs if '"ran": 4' in (r.get("result") or "")), "") or ""
        p.check("the tool result says the refusal and the rest", '"refused": 1' in result and '"ran": 4' in result,
                result[:200])
        p.check("his charter is his system prompt", any("standing rules" in (r.get("system") or "") or
                                                         "charter" in (r.get("system") or "") for r in reqs))
        receipt = p.until(lambda: "refused" in (jeff_said()[0].get("acts") or "") and jeff_said()[0]["acts"])
        p.check("his tool calls are small receipts under the line before them",
                receipt and "rows chat" in receipt and "(1 refused)" in receipt, str(receipt)[:200])

        team = (p.line("rows group name=team")["rows"] or [{}])[0].get("id")
        shop_row = next(r for r in p.line("rows chat")["rows"] if r["id"] == shop)
        p.check("Shop talk is the team's, an open group the place sees", team and team in shop_row.get("groups", []))
        p.line(f"look {team}", who="jeff")
        led = p.line(f"group {team} open=yes", who="jeff", route="/do")
        # whether he is also a steward is the world's to say (Alex made him one, 27 Oct, f62c84eb6); the proof copies it
        steward = p.line("off guy", who="jeff").get("ok")
        if steward:
            p.line("undo", who="jeff")
        p.check("JEFF leads the team (a leader's word works for him)", led.get("ok"),
                led.get("text", "")[:120] + (" · in this world he is also a steward" if steward else
                                             " · Alex is the only steward here"))

        before = [r["id"] for c in (convo, shop) for r in p.lines_of(c)]
        p.line(f"look {jeff}")
        p.line(f"house.wake {jeff} RUN: rows chat", route="/do")
        acts = p.until(lambda: "Done:" in json.dumps(p.line(f"house.activity {jeff}")["rows"]), 30)
        after = [r["id"] for c in (convo, shop) for r in p.lines_of(c)]
        p.check("woken by no chat (house.wake), his words and acts go to his activity record, no chat",
                acts and before == after, p.line(f"house.activity {jeff}")["text"].splitlines()[-1][:160])

        p.line(f"say {shop} morning all, nothing for anyone")
        time.sleep(2)
        reqs = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
        p.check("a plain line in Shop talk wakes no one", not any("morning all" in (r.get("user") or "") for r in reqs),
                f"{len(reqs)} model requests, none carrying it")
        t1 = time.time()
        p.line(f"say {shop} @jeff a word, please")
        heard = p.until(lambda: [r for r in p.lines_of(shop) if r["by"] == "JEFF" and r["text"] == "Heard you."
                                 and int(r["id"][2:]) > mine])
        warm = int((time.time() - t1) * 1000)
        p.check("@jeff in Shop talk wakes him; he answers there", heard, f"{warm} ms to his words, warm")

        p.line("off house")
        p.until(lambda: "not running" in p.line("look house")["text"], 15)
        p.line(f"say {convo} are you there? (said while the house was off)")
        p.line("on house")
        got = p.until(lambda: jeff_said()[2:], 60)
        p.check("a line said while the house was off reaches him when it is on again (the cursor)", got,
                got[0]["text"] if got else "")
        sent = (p.world / "modules" / "house" / "jeff" / "transcript.jsonl").read_text(encoding="utf-8")
        p.check("he was told it as missed", "while the house was away" in sent)
        p.check("first words, Alex's line to JEFF's line, scripted model (the house's and Claude's own cost)", True,
                f"cold (process started moments before): {ms} ms; warm: {warm} ms")
    finally:
        subprocess.run([str(PY), str(DESK / "sandbox.py"), "stop", "--name", NAME], stdout=subprocess.DEVNULL,
                       creationflags=NO_WINDOW)
        for pr in procs:
            pr.kill()
    ok = all(c["ok"] for c in p.checks)
    Path(a.out).write_text(json.dumps({"at": time.strftime("%Y-%m-%d %H:%M"), "complete": ok, "checks": p.checks},
                                      indent=1), encoding="utf-8")
    print("all checks ok" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
