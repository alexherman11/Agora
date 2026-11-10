"""Build the trial world: Alex's real board (58 cards) + a second team's Tracker app (kind=issue) + a GitHub adapter
(kind=gh-issue), with Alex's real backlog converted into both vocabularies and generated volume. Writes the world to
scratchpad/trial-tasks/w-built (a copy of the desktop log plus these acts). Every act goes through k.run as a real line.

Phase A only: the new apps install exactly as a team would, with closed kinds and words without shapes. Shapes and
widening are the experiments (trial.py), each on its own copy of this world."""
import json
import random
import time
from collections import Counter

from common import open_world, steward, say, short, Actor

random.seed(28)
k, dt = open_world("w-built")
alex = steward(k)
print(f"opened copy in {dt:.2f}s; things={len(k.state.things)}")


def q(v):
    s = str(v or "").replace('"', "'").replace("\\", "/").replace("\n", " ").replace(";", ",")
    return '"' + s[:400] + '"'


def must(line, actor=alex):
    out = say(k, actor, line)
    if not out.get("ok"):
        raise SystemExit(f"FAILED: {line[:200]}\n{short(out, 600)}")
    return out


# ---------------------------------------------------------------- install the Tracker app (a second team's words)
TRACKER = [
    'make kind=kind name=issue help="Tracker issue: name, status open|in_progress|closed, assignee, due, project, labels, estimate, parent"',
    'make kind=kind name=project help="Tracker project"',
    'make kind=project name=Agora key=AG',
    'make kind=project name=Seabright key=SB',
    'make kind=project name=Desktop key=DT',
    'verb issue.add takes="name=<text> [project=<name>] [assignee=<name>] [due=<date>] [labels=<words>] [estimate=<n>] [parent=<id>] [description=<text>]" '
    'steps="make kind=issue name=$name status=open project=$project assignee=$assignee due=$due labels=$labels estimate=$estimate parent=$parent description=$description" '
    'help="issue.add name=\\"Fix login\\" project=Agora: open a new issue."',
    'verb issue.close takes="<id>" steps="set $1 status=closed" help="issue.close <issue>: close an issue."',
    'verb issue.reopen takes="<id>" steps="set $1 status=open" help="issue.reopen <issue>: open it again."',
    'verb issue.move takes="<id> to=<status>" steps="set $1 status=$to" help="issue.move <issue> to=open|in_progress|closed."',
    'verb issue.assign takes="<id> who=<name>" steps="set $1 assignee=$who" help="issue.assign <issue> who=<name>."',
    'verb issue.estimate takes="<id> points=<n>" steps="set $1 estimate=$points" help="issue.estimate <issue> points=<n>."',
]
GITHUB = [
    'make kind=kind name=gh-issue help="GitHub issue (adapter): number, title, state open|closed, body, html_url, user, assignee, labels"',
    'verb gh.close takes="<id>" steps="set $1 state=closed" help="gh.close <gh-issue>: close it here (the adapter syncs to GitHub)."',
    'verb gh.reopen takes="<id>" steps="set $1 state=open" help="gh.reopen <gh-issue>: reopen it."',
    'verb gh.assign takes="<id> who=<login>" steps="set $1 assignee=$who" help="gh.assign <gh-issue> who=<login>."',
]
for line in TRACKER + GITHUB:
    out = must(line)
    print(short(out, 160))

# ---------------------------------------------------------------- Alex's real backlog, converted
cards = [t for t in k.things("taskboard-task") if not k.state.get(t, "forgotten")]
LANE_TO_STATUS = {"Backlog": "open", "Now": "in_progress", "Done": "closed"}
PEOPLE = ["Alex", "JEFF", "Sable", "Pike", "claude", "Codex", "Bea", "Mo"]
LOGINS = ["alexherman11", "jeff-bot", "sable-r", "pike-r", "octocat", "bea-dev", "mo-k"]
LABELS = ["kernel", "desktop", "lens", "house", "seabright", "bug", "design", "perf", "docs", "infra"]
conv = {"issue": [], "gh": []}
t0 = time.perf_counter()
for i, c in enumerate(cards):
    a = k.state.things[c]
    proj = random.choice(["Agora", "Desktop", "Seabright"])
    out = must(f'make kind=issue name={q(a.get("title"))} status={LANE_TO_STATUS[a.get("lane")]} '
               f'assignee={q(a.get("who") or "")} due={q(a.get("when") or "")} project={proj} '
               f'labels={q(" ".join(random.sample(LABELS, 2)))} estimate={random.choice([1, 2, 3, 5, 8])} '
               f'description={q(a.get("text") or "")} converted_from={c}')
    conv["issue"].append(out["made"][0])
    state = "closed" if a.get("lane") == "Done" else "open"
    out = must(f'make kind=gh-issue number={100 + i} title={q(a.get("title"))} state={state} body={q(a.get("text") or "")} '
               f'html_url="https://github.com/alex/agora/issues/{100 + i}" user={random.choice(LOGINS)} '
               f'assignee={random.choice(LOGINS + [""])} labels={q(random.choice(LABELS))} converted_from={c}')
    conv["gh"].append(out["made"][0])
print(f"converted {len(cards)} cards x2 in {time.perf_counter() - t0:.2f}s")

# ---------------------------------------------------------------- generated volume
VERBS = ["Fix", "Add", "Remove", "Refactor", "Document", "Speed up", "Test", "Design", "Port", "Investigate"]
NOUNS = ["login", "bar", "dock", "lens compile", "rows reading", "theme picker", "map layer", "chat replies", "House landing",
         "kind declarations", "spellings", "board drag", "summary model", "upload size", "invite codes", "calendar", "RSVP",
         "search", "notifications", "profile page", "window focus", "pomodoro ring", "taskbar", "undo", "history trail"]
WHERE = ["on the desktop", "in Seabright", "for residents", "in the kernel", "on mobile", "for agents", "in the painter", ""]


def gen_title():
    return " ".join(x for x in [random.choice(VERBS), random.choice(NOUNS), random.choice(WHERE)] if x)


timings = []
made = Counter()
issues = list(conv["issue"])
batch_t = time.perf_counter()
for n in range(2000):
    r = random.random()
    if n < 300:                      # Alex's board keeps growing too
        lane = random.choice(["Backlog", "Backlog", "Now", "Done", "Done"])
        line = (f'make kind=taskboard-task title={q(gen_title())} lane={lane} who={random.choice(PEOPLE)} '
                f'priority={random.randint(1, 4)} colour=paper note_colour=paper note_style=normal seats=1 text={q("Generated " + str(n))}')
        kind = "taskboard-task"
    elif n < 1300:
        parent = random.choice(issues) if (issues and r < 0.25) else ""
        line = (f'make kind=issue name={q(gen_title())} status={random.choice(["open", "open", "in_progress", "closed"])} '
                f'assignee={random.choice(PEOPLE + [""])} due=2026-11-{random.randint(1, 30):02d} '
                f'project={random.choice(["Agora", "Desktop", "Seabright"])} labels={q(" ".join(random.sample(LABELS, random.randint(0, 3))))} '
                f'estimate={random.choice([1, 2, 3, 5, 8, ""])} parent={parent} description={q("Generated issue " + str(n))}')
        kind = "issue"
    else:
        num = 1000 + n
        line = (f'make kind=gh-issue number={num} title={q(gen_title())} state={random.choice(["open", "open", "closed"])} '
                f'body={q("Imported " + str(n))} html_url="https://github.com/alex/agora/issues/{num}" '
                f'user={random.choice(LOGINS)} assignee={random.choice(LOGINS + [""])} labels={q(random.choice(LABELS))}')
        kind = "gh-issue"
    t = time.perf_counter()
    out = must(line)
    timings.append((len(k.state.things), time.perf_counter() - t))
    made[kind] += 1
    if kind == "issue":
        issues.append(out["made"][0])
    if n % 250 == 249:
        recent = [x[1] for x in timings[-250:]]
        print(f"  {n + 1} made; things={len(k.state.things)}; mean make {sum(recent) / len(recent) * 1000:.1f} ms")
print("generated", dict(made), f"in {time.perf_counter() - batch_t:.1f}s")
counts = Counter(a.get("kind") for a in k.state.things.values() if not a.get("forgotten"))
print("now:", {x: counts[x] for x in ("taskboard-task", "issue", "gh-issue", "project")},
      "things", len(k.state.things), "records", len(k.log.records))
json.dump(conv, open(k.dir / "conv.json", "w"))
print("member actor: Sable", k.state.get("dk1148", "kind"), k.is_member("dk1148", k.place) if hasattr(k, "is_member") else "?")
