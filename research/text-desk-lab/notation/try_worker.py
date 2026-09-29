"""try_worker: one real commission, run by a real worker, in a throwaway checkout, then cleaned up.

    python try_worker.py --title "..." --text "..." [--minutes 30] [--answer "..."] [--keep] [--name tag]

It makes a git worktree of HEAD (.worktrees/trial-<tag>, branch trial/<tag>) with a copy of the live world as
`try-<tag>`, lets every resident rest, writes the commission there as Alex, and runs that checkout's house. The worker
works in its own worktree off the trial branch, and the house lands into the trial branch, never into main. When the
worker waits on the commissioner, --answer is posted as Alex's reply (once each time it waits; default: "your call").

The report goes to research/command-center/trials/worker-<tag>.md: the thread on the commission, what the worker said,
the tools it used, and what landed on the trial branch (git log and diff stat). Afterwards, unless --keep, the trial
checkout and the worker's conversation are removed; the branch trial/<tag> is kept so what landed can be reviewed or
merged. This spends real model calls.
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PY = sys.executable
REPORTS = REPO / "research" / "command-center" / "trials"
PROJECTS = Path.home() / ".claude" / "projects"


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv[:-1] else default


def git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def main():
    tag = arg("--name") or time.strftime("%m%d-%H%M%S")
    title, text = arg("--title"), arg("--text", "")
    minutes = float(arg("--minutes", "30"))
    answer = arg("--answer", "Your call: keep it small, and say in your done note what you chose and why.")
    if not title:
        sys.exit("--title is required")
    tree, branch, world = REPO / ".worktrees" / f"trial-{tag}", f"trial/{tag}", f"try-{tag}"
    r = git("worktree", "add", str(tree), "-b", branch, "HEAD")
    if r.returncode:
        sys.exit(r.stderr)
    lab = tree / HERE.relative_to(REPO)
    shutil.copyfile(HERE / "sessions" / "frontier.pickle", lab / "sessions" / f"{world}.pickle")
    base = git("rev-parse", "HEAD", cwd=tree).stdout.strip()

    def desk(line, who="alex"):
        p = subprocess.run([PY, "explore.py", world, "--as", who], cwd=lab, input=line + "\n", capture_output=True,
                           text=True, env={**__import__("os").environ, "DESKD": "off"}, timeout=120)
        return p.stdout + p.stderr

    corners = re.findall(r"(f\d+) surface [^\n]*role=resident", desk("find prop:role=resident"))
    for c in corners:
        desk(f"look {c} :1; do prop {c} want=rest")
    out = desk(f"do create Frontier kind=task title={json.dumps(title)} commission=asked status=open text={json.dumps(text)}")
    m = re.search(r"→ created (a\d+)", out)
    if not m:
        sys.exit("could not write the commission:\n" + out)
    cid = m.group(1)
    print(f"trial {tag}: commission {cid} in {world}, checkout {tree}, branch {branch}", flush=True)
    house = subprocess.Popen([PY, "house.py", world], cwd=lab, stdout=open(lab / "house-test.log", "w", encoding="utf-8"),
                             stderr=subprocess.STDOUT, env={**__import__("os").environ, "DESKD": "off"})
    start, state, answered, ending = time.time(), "asked", 0, "?"
    try:
        while True:
            time.sleep(10)
            look = desk(f"look {cid} :1", "claude")
            m2 = re.search(r"commission=(\w+)", look)
            now_state = m2.group(1) if m2 else "?"
            if now_state != state:
                print(f"  {time.strftime('%H:%M:%S')} commission: {state} -> {now_state}", flush=True)
                state = now_state
            if state in ("landed", "reverted", "failed", "cancelled"):
                ending = state
                break
            if state == "waiting" and answered < 5:
                desk(f"read {cid}; do comment {cid} line={json.dumps(answer)}")
                answered += 1
                print(f"  alex answers: {answer}", flush=True)
                time.sleep(20)
            if house.poll() is not None:
                ending = f"the house exited ({house.returncode})"
                break
            if time.time() - start > minutes * 60:
                ending = f"time limit ({minutes:g} min, state {state})"
                break
    except KeyboardInterrupt:
        ending = "interrupted"
    finally:
        house.terminate()
        try:
            house.wait(timeout=30)
        except subprocess.TimeoutExpired:
            house.kill()
    thread = desk(f"examine {cid}", "claude")
    log = git("log", "--format=%h %s", f"{base}..{branch}", cwd=tree).stdout.strip()
    stat = git("diff", "--stat", f"{base}..{branch}", cwd=tree).stdout.strip()
    report = write_report(tag, cid, title, text, ending, thread, log, stat, lab / "house-state" / world / f"worker-{cid}")
    print(f"ended: {ending}\nreport: {report}\nlanded on {branch}:\n{log or '(nothing)'}", flush=True)
    if "--keep" not in sys.argv:
        for p in PROJECTS.glob("*"):
            if p.is_dir() and f"worktrees-trial-{tag}" in p.name:
                shutil.rmtree(p, ignore_errors=True)
        for b in git("branch", "--list", f"worker/*").stdout.split():
            if b.startswith("worker/") and git("merge-base", "--is-ancestor", b, branch).returncode == 0:
                git("branch", "-D", b)
        git("worktree", "remove", "--force", str(tree))
        git("worktree", "prune")
        print(f"removed the trial checkout; branch {branch} kept for review", flush=True)


def write_report(tag, cid, title, text, ending, thread, log, stat, wdir):
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = [f"# Worker trial {tag}", "",
           f"Commission {cid}, asked by alex in a copy of frontier, run by a real worker in a throwaway checkout. Ended: {ending}.",
           "", "## The commission", "", f"**{title}**", "", text, "", "## The thread (examine)", "", "```text", thread.strip(), "```", "",
           "## What landed on the trial branch", "", "```text", log or "(nothing)", "", stat, "```", "", "## The worker", ""]
    tools = {}
    tpath = wdir / "transcript.jsonl"
    if tpath.exists():
        for line in tpath.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            d = e["data"]
            at = time.strftime("%H:%M:%S", time.localtime(e["at"]))
            if e["kind"] == "sent":
                out += [f"**house → worker** {at}", "", "```text", d.strip()[:3000], "```", ""]
            elif e["kind"] == "event" and d.get("type") == "assistant":
                for c in d.get("message", {}).get("content", []):
                    if c.get("type") == "text" and c["text"].strip():
                        out += [f"**worker** {at}", "", "```text", c["text"].strip()[:3000], "```", ""]
                    elif c.get("type") == "tool_use":
                        tools[c.get("name")] = tools.get(c.get("name"), 0) + 1
            elif e["kind"] == "event" and d.get("type") == "result":
                out += [f"*turn ended {at}: {d.get('subtype')}{' (error)' if d.get('is_error') else ''}, "
                        f"{d.get('num_turns')} steps, ${d.get('total_cost_usd', 0):.2f} so far*", ""]
            elif e["kind"] in ("start", "exit", "failed", "restart", "unsent"):
                out += [f"*{e['kind']} {at}: {json.dumps(d)[:240]}*", ""]
    out += ["## Tools the worker used", ""] + [f"- {k}: {v}" for k, v in sorted(tools.items(), key=lambda x: -x[1])]
    path = REPORTS / f"worker-{tag}.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    main()
