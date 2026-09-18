"""Definition-only authoring through unchanged Desk commands in memory.
No sessions, sockets, subprocesses or host files are written. --record writes only fixtures/ evidence.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1] / "text-desk-lab" / "notation"
FIXTURES = HERE / "fixtures"
HOST_FILES = ["scene.py", "desk-shell/lens.js", "desk-shell/lens.html", "desk-shell/style/style.js",
              "desk-shell/style/calm.style", "explore.py", "desk_knife.py", "desk_moo.py", "desk.py", "world.py", "moo.py"]
def hashes():
    return {name: hashlib.sha256((ENGINE / name).read_bytes()).hexdigest() for name in HOST_FILES}
before = hashes()
sys.path.insert(0, str(ENGINE))
from explore import fresh
import scene

desk = fresh()
desk.world.me = "editing"
commands, checks, observations = [], [], {}
def command(line):
    result = desk.dispatch("desk", {"line": line})
    commands.append({"line": line, "result": result})
    assert not result.get("error"), (line, result)
    assert not result.get("text", "").startswith("ERR"), (line, result)
    return result.get("text", "")
def quote(value):
    return json.dumps(value, ensure_ascii=False)
def create(title, text, tags):
    prior = set(desk.world.subjects)
    command("look f01")
    command(f"do create f01 kind=note title={quote(title)} tags={tags} text={quote(text)}")
    added = set(desk.world.subjects) - prior
    assert len(added) == 1
    sid = added.pop()
    aid = next(n["id"] for n in desk.world.nodes.values() if n.get("subject") == sid)
    return sid, aid
def walk(n):
    yield n
    for child in n["kids"]:
        yield from walk(child)
def scene_now():
    return scene.scene_for(desk, "Observations")
def rewrite_lens(src):
    command(f"read {lens_aid}")
    command(f"do rewrite {lens_aid} text={quote(src)}")
    return "e" + str(len(desk.world.events))
def check(label, ok):
    assert ok, label
    checks.append(label)
def content():
    return {sid: copy.deepcopy(s) for sid, s in desk.world.subjects.items() if "essay" in s.get("tags", [])}

first_sid, first_aid = create("Light on the stairs", "A bright square crosses the steps.\nIt moves while the room stays still.", "essay,light")
second_sid, second_aid = create("The garden after rain", "Leaves hold small lenses of water.\nThe wall is warm again.", "essay,garden")
sources = {name: (FIXTURES / (name + ".lens")).read_text(encoding="utf-8") for name in ("spatial", "editorial", "index")}
lens_sid, lens_aid = create("Observations", sources["spatial"], "lens")
original = content()
spatial, spatial_text = scene_now()
check("native-created lens builds spatial cards with target-bound drag", any(n["box"] and any(a["on"] == "drag" for a in n["acts"]) for n in walk(spatial)))

editorial_event = rewrite_lens(sources["editorial"])
editorial, editorial_text = scene_now()
check("native rewrite changes hierarchy and role without material mutation", editorial["part"] == "reading" and editorial["role"] == "sheet" and content() == original)
check("definition removes placement and drag while adding body rewrite", not any(n["box"] for n in walk(editorial)) and not any(a["on"] == "drag" for n in walk(editorial) for a in n["acts"]) and any(a["on"] == "edit" and a["line"].startswith("do rewrite ") for n in walk(editorial) for a in n["acts"]))
for name, sc in (("spatial", spatial), ("editorial", editorial)):
    check(name + " retains both occurrence identities", {n["item"] for n in walk(sc) if n["item"]} == {first_aid, second_aid})
command("undo " + editorial_event)
restored, _ = scene_now()
check("native undo restores lens scene and retains material", restored == spatial and content() == original)

rewrite_lens(sources["index"])
index, index_text = scene_now()
check("definition-only index hides body and removes all mutations", not any(n["part"] == "body" for n in walk(index)) and all(a["on"] == "click" and a["line"].startswith("read ") for n in walk(index) for a in n["acts"]) and content() == original)
rewrite_lens(sources["editorial"])
current, _ = scene_now()
body = next(n for n in walk(current) if n["part"] == "body" and n["item"] == first_aid)
edit = next(a for a in body["acts"] if a["on"] == "edit")
replacement = "The beam has reached the landing."
command("read " + first_aid)
bare_line = edit["line"].removeprefix("do ").replace("$value", replacement)
bare_result = desk.dispatch("desk", {"line": bare_line})
commands.append({"line": bare_line, "result": bare_result, "expected_refusal": True})
check("counterexample: bare rewrite advertised by naive lens refuses as unknown command", "unknown command" in bare_result.get("error", ""))
observations["command_prefix"] = "Mutation gestures need on edit do do rewrite: the first do belongs to lens syntax; the second to Desk command syntax. Read needs only on click do read."
command(edit["line"].replace("$value", replacement))
check("advertised command executed natively updates shared subject", desk.world.subjects[first_sid]["text"] == replacement)
changed_editorial, _ = scene_now()
changed_spatial = scene.build(desk, sources["spatial"])
check("same edited material appears through both definitions", all(any(n["text"] == replacement and n["item"] == first_aid for n in walk(sc)) for sc in (changed_editorial, changed_spatial)))
third_sid, third_aid = create("Windfall", "One apple waits beside the gate.", "essay,fruit")
dynamic, _ = scene_now()
check("existing selection includes new subject without definition or host change", any(n["item"] == third_aid and n["text"] == "Windfall" for n in walk(dynamic)))

invalid = "reading : column, raw-css display:grid"
rewrite_lens(invalid)
assert desk.world.subjects[lens_sid]["text"] == invalid
try:
    scene_now()
except scene.LensRefusal as refusal:
    observations["invalid_lens"] = str(refusal)
else:
    raise AssertionError("invalid lens unexpectedly rendered")
check("counterexample: ordinary rewrite stores invalid lens; scene refuses without last-good", True)
rewrite_lens("reading : column, role nonexistent-role, text Still accepted")
unknown, _ = scene_now()
check("counterexample: unknown style role is accepted by scene", unknown["role"] == "nonexistent-role")
observations["unknown_role"] = "scene accepts nonexistent-role; no such role exists in calm.style. This test does not claim browser appearance."
rewrite_lens(sources["editorial"])
after = hashes()
check("all eleven host/style source hashes unchanged", before == after)
result = {"checks": checks, "passed": len(checks), "host_before": before, "host_after": after,
          "host_edits": 0, "host_escape_paths_used": 0, "recording": "in-memory native command harness; no browser or model trial",
          "observations": observations, "commands": commands}
if "--record" in sys.argv:
    for name, sc, text in (("spatial", spatial, spatial_text), ("editorial", editorial, editorial_text), ("index", index, index_text)):
        (FIXTURES / (name + ".scene.json")).write_text(json.dumps(sc, ensure_ascii=False, indent=2), encoding="utf-8")
        (FIXTURES / (name + ".scene.txt")).write_text(text, encoding="utf-8")
    (FIXTURES / "authoring-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"passed": len(checks), "checks": checks, "host_sources_unchanged": before == after}, indent=2))
