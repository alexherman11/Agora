"""Loose ends the main trial raised: a second declaration bypasses widen-only; a member's shaped word steals done on
Alex's own cards; a world-level lane mapping (lane things carry the other apps' values); what actions/kinds say."""
import time
from collections import Counter

from trial import open_built, run, decl, ids, pick, board_counts, lens_text, set_text, H, shape_words
from painter.arrangement import compile_view

H("E1. Widen-only is enforced on set, not on a second make")
k, alex, sable, conv, dt = open_built("t-extra1")
shape_words(k, alex)
run(k, alex, 'make kind=kind name=issue needs="name"', "steward: second declaration, wide")
run(k, alex, f'set {decl(k, "issue")} needs="name status project"', "steward narrows by set")
run(k, alex, 'make kind=kind name=issue needs="name status project"', "steward narrows by a third make")
print("   issue shape now:", [n.text() for n in (k.kinds.shape("issue") or [])])
print("   declarations of issue:", [(t, k.state.get(t, "needs"), k.name(k.state.get(t, "made_by"))) for t in k.things("kind")
                                    if k.state.get(t, "name") == "issue"])
bare = [t for t in ids(k, "issue") if not k.state.get(t, "project")]
print(f"   issues without project now refused by every issue.* word: {len(bare)} (of {len(ids(k, 'issue'))})")

H("E2. Before Alex shapes task.*, a member's shaped word wins done on Alex's own cards")
k, alex, sable, conv, dt = open_built("t-extra2")
run(k, sable, 'verb tidy.done needs="title lane" steps="set $1 who=Sable" help="tidy.done <card>: take it."', "Sable (member)")
c = Counter(pick(k, alex, f"done {t}")[1] for t in ids(k, "taskboard-task"))
print("   done <card id> over all cards:", dict(c))
k.run(alex, "look dk95", mode="see")
run(k, alex, "done dk95", "Alex types done on his own card")
print("   dk95 now:", {x: k.state.get("dk95", x) for x in ("lane", "who")})

H("E3. A world-level lane mapping: lane things carry the other apps' values")
k, alex, sable, conv, dt = open_built("t-extra3")
run(k, alex, 'make kind=kind name=task needs="title|name lane|status|state"', "steward")
for lane, st, gs in (("dk79", "open", "open"), ("dk80", "in_progress", ""), ("dk81", "closed", "closed")):
    k.run(alex, f"look {lane}", mode="see")
    run(k, alex, f"set {lane} issue_status={st}" + (f" gh_state={gs}" if gs else ""), "steward", n=100)
text = lens_text(k, "dk262").replace(
    "  cards : column, of tag:taskboard-task, prop:lane=$lane.name as task, by priority, each task-view",
    "  cards : column, of tag:taskboard-task, prop:lane=$lane.name as task, by priority, each task-view\n"
    "  issues : column, of tag:task, prop:kind=issue, prop:status=$lane.issue_status as task, each task-view\n"
    "  pulls : column, of tag:task, prop:kind=gh-issue, prop:state=$lane.gh_state as task, each task-view")
k.run(alex, "look dk262", mode="see")
set_text(k, alex, "dk262", text, "steward")
t = time.perf_counter()
v = compile_view(k, alex, "dk262")
print(f"   board: {dict(board_counts(v))} ({(time.perf_counter() - t) * 1000:.0f} ms)")
print("   view text:", v["text"])
i = conv["issue"][4]
run(k, alex, f"look {i}", "steward", n=30, mode="see")
print("   the drop gesture on an issue card says task-move $carried to=Done; as typed by Alex:")
run(k, alex, f"task-move {i} to=Done", "steward")
print("   a lens could say the plain word instead (move $carried to=$lane.name):")
print("   move <issue> to=Done ->", pick(k, alex, f"move {i} to=Done"))
run(k, alex, f"move {i} to=Done", "steward")
print("   the issue now says status =", k.state.get(i, "status"), "(the Tracker knows open|in_progress|closed)")

H("E4. What actions and kinds say for a gh-issue with every app shaped and the shared kinds declared")
k, alex, sable, conv, dt = open_built("t-extra4")
shape_words(k, alex)
for line in ('make kind=kind name=task needs="title|name lane|status|state"', 'make kind=kind name=assigned needs="assignee|who"',
             'verb gh.done needs="kind=gh-issue" steps="set $1 state=closed" help="gh.done <gh-issue>: close it."'):
    run(k, alex, line, "steward", n=80)
g = conv["gh"][3]
print(k.run(alex, f"kinds {g}", mode="see")["text"])
print(k.run(alex, f"actions {g}", mode="see")["text"])
print(k.run(alex, "actions dk91", mode="see")["text"])
