"""Read official copied Session; stage Rowan's exact menu/consumer on a deep copy.

No process/browser helpers, writes to sessions or live sends.
Fixture setup dispatches only create/read in the disposable in-memory copy.
Only artifacts under this script's directory are written.
"""
import copy
import json
from pathlib import Path
import sys
import re
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "text-desk" / "notation"))
import deskd
import lens_ir
import scene
from selection_snapshot import capture
from world import Refusal


def walk(n):
    yield n
    for kid in n.get("kids", []):
        yield from walk(kid)


with deskd.Session("frontier-try", "alex", read=True) as live:
    d = copy.deepcopy(live)
w = d.world
before = len(w.events)
subject = w.subjects[w.nodes["a5210"]["subject"]]
original = subject["text"]
start = original.index("    let wview =")
endline = '    let held = "" otherwise'
end = original.index(endline, start) + len(endline)
src = original[:start] + '    let held = ""' + original[end:]
start = src.index("    commenting : column")
end = src.index("    to : row", start)
src = src[:start] + src[end:]
quoted = ('      on edit quoted when ($draft.topic or "") = "" and ($draft.reply_to or "") = "" '
          'and ($draft.reply_thread or "") = "" do append $quote_destination line="$value" '
          'about="$quote_item" quote="$quote_text" words_before="$quote_before" '
          'words_after="$quote_after" captures="$draft.context" context_from="$draft"')
assert src.count("      commit explicit") == 1
src = src.replace("      commit explicit", "      commit explicit\n" + quoted)
old_plain = [a for a in original.splitlines() if a.startswith("      on edit when")]
assert [a for a in src.splitlines() if a.startswith("      on edit when")] == old_plain
subject["text"] = src  # in-memory copy ONLY; no session save/dispatch
home = next(s for s in w.subjects.values() if s.get("title") == "home-base" and "lens" in s.get("tags", []))
draft = w.subjects[w.nodes["a5082"]["subject"]]["props"]
# Mutate only this deep-copied draft's ordinary props, never the live draft.
report = {"world_event": w.events[-1]["id"], "events_before": before, "cases": []}
for name, props, count, quoted_count in [
    ("ordinary", {}, 1, 1),
    ("topic", {"topic": "a6079"}, 3, 0),
    ("reply elsewhere", {"reply_to": "m1", "reply_in": "a6079"}, 3, 0),
    ("thread", {"reply_thread": "c1", "reply_in": "a6079"}, 3, 0),
    ("ambiguous reply and thread", {"reply_to": "m1", "reply_in": "a6079", "reply_thread": "c1"}, None, None),
]:
    for key in ("topic", "reply_to", "reply_thread", "reply_in"):
        draft[key] = props.get(key, "")
    lens_ir._REUSE.clear()
    d._lens_good = {}
    try:
        root = lens_ir.compile_lens(d, home, (), [0], [])
    except scene.LensRefusal as error:
        assert count is None, (name, str(error))
        assert "exactly one offered plain" in str(error), str(error)
        report["cases"].append({"name": name, "refusal": str(error)})
        continue
    if count is None:
        refusals = [n for n in walk(root) if "exactly one offered plain" in str({k: v for k, v in n.items() if k != "kids"})]
        assert refusals and not any(a["on"] == "edit" for n in refusals for a in n.get("acts", [])), refusals
        report["cases"].append({"name": name, "refusal": "paired composer guard ambiguity; nested lens withheld"})
        continue
    composers = [n for n in walk(root) if any(a["on"] == "edit-quoted" for a in n.get("acts", []))
                 or (n["key"].endswith("/dock/say") and any(a["on"] == "edit" for a in n.get("acts", [])))]
    assert len(composers) == 1, (name, [n["key"] for n in composers])
    n = composers[0]
    plain = [a for a in n["acts"] if a["on"] == "edit"]
    qs = [a for a in n["acts"] if a["on"] == "edit-quoted"]
    assert len(plain) == 1 and len(qs) == quoted_count, (name, n["acts"])
    assert len(scene.split_batch(plain[0]["line"])) == count, (name, plain)
    report["cases"].append({"name": name, "key": n["key"], "actions": n["acts"],
                            "nodes": len(list(walk(root)))})
assert len(w.events) == before
report["events_after"] = len(w.events)
(HERE / "PAIRED-COPY.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
start = src.index('    say : text ""')
end = src.index("    footer : row", start)
(HERE / "PAIRED-WORLD-EXAMPLE.txt").write_text(src[start:end], encoding="utf-8")
print(f"5 copied mounted guard cases passed; {report['world_event']}; events {before}->{len(w.events)}; no dispatch")

# Rowan's exact direct-note body menu and H2 removal, alongside the paired
# consumer above. Keep all edits in the same deep copy, never save it.
doc = w.subjects[w.nodes["a6079"]["subject"]]
doc_original = doc["text"]
# a11877, 22 Oct: the world is selection-only now. Pike's e24847-e24851 removed
# doc-page's body and paragraph on-select lines (the 21 Oct fixture replaced
# them), so the menu is staged beside the body's own edit line instead, and
# no on-select may remain anywhere in the lens.
assert not [x for x in doc_original.splitlines() if re.match(r"\s*on select\b", x)]
anchor = '              on edit do read $d.item; do rewrite $d.item text="$value"'
target_key = report["cases"][0]["key"]
menu_hunk = ('              let destination_title = join($title of $d.talk) when talk != ""\n'
             '              let destination_title = "" otherwise\n'
             '              let destination_id = join($id of $d.talk) when talk != ""\n'
             '              let destination_id = "" otherwise\n'
             f'              on menu "Comment" prepare {target_key} context=$d.id destination=$(destination_id)')
assert doc_original.count(anchor + "\n") == 1
doc["text"] = doc_original.replace(anchor + "\n", anchor + "\n" + menu_hunk + "\n")
assert [x for x in doc_original.splitlines() if "on edit" in x] == [
    x for x in doc["text"].splitlines() if "on edit" in x]

def fixture(args):
    result = d.dispatch("desk", {"line": 'do create f3402 ' + args, "whole": True})
    assert not result.get("error"), result
    assert not re.search(r"(^|\n)ERR", result.get("text", "")), result
    return re.search(r"created ([af]\d+)", result["text"])[1]

d.dispatch("desk", {"line": "look f3402", "whole": True})
talk = fixture('kind=chat title="Copy captured Talk" with="alex,jeff"')
other_talk = fixture('kind=chat title="Copy other Talk" with="alex,jeff"')
source_note = fixture('kind=note title="Copy source" role=doc talk=' + talk + ' text="same same **bold** end"')
other_note = fixture('kind=note title="Copy navigation" role=doc talk=' + other_talk + ' text="other words"')
fixture_at = len(w.events)
for key in ("topic", "reply_to", "reply_thread", "reply_in"):
    draft[key] = ""
draft["to"] = "rowan"  # Must not reroute prepared quote.
draft["context"] = "cap-999998 cap-999999"  # Private capture rows mocked below.
def compile_doc(item):
    lens_ir._REUSE.clear()
    d._lens_good = {}
    return lens_ir.compile_lens(d, doc, (), [0], [], on=item)

root = compile_doc(source_note)
menu_nodes = [n for n in walk(root) if any(a.get("label") == "Comment" for a in n.get("acts", []))]
assert len(menu_nodes) == 1, [(n["key"], n.get("acts")) for n in menu_nodes]
node = menu_nodes[0]
menu = next(a for a in node["acts"] if a.get("label") == "Comment")
doc_sid = w.nodes[source_note]["subject"]
talk_sid = w.nodes[talk]["subject"]
bindings = {r[0]: r[1] for r in node["reads"]}
assert doc_sid in bindings and talk_sid in bindings, (doc_sid, talk_sid, node["reads"])
assert node["source"]["item"] == doc_sid, node["source"]
scene.emit(root)
origin = scene.painter_view(node)
exact_context = re.search(r"\bcontext=(\S+)", menu["line"])[1]
exact_destination = re.search(r"\bdestination=(\S+)", menu["line"])[1]
assert exact_context == doc_sid and exact_destination == talk_sid
assert all(isinstance(bindings[x], int) for x in (exact_context, exact_destination))
packet = {**node["source"], "start": 5, "end": 9, "quote": "same",
          "context": {"item": {"item": doc_sid, "rev": bindings[doc_sid]},
                      "destination": {"item": talk_sid, "rev": bindings[talk_sid]}}}
snapshot = capture(d, packet)
with patch.object(lens_ir, "may_read", side_effect=lambda desk, item: "private" if item == talk_sid else None):
    try:
        capture(d, packet)
    except Refusal as error:
        unreadable = str(error)
    else:
        raise AssertionError("unreadable captured Talk accepted")
saved_rev = w.subjects[talk_sid]["rev"]
saved_app_rev = w.nodes[talk]["rev"]
w.subjects[talk_sid]["rev"] += 1
w.nodes[talk]["rev"] += 1
try:
    capture(d, packet)
except Refusal as error:
    stale_talk = str(error)
else:
    raise AssertionError("stale Talk accepted")
finally:
    w.subjects[talk_sid]["rev"] = saved_rev
    w.nodes[talk]["rev"] = saved_app_rev
saved_source_rev = w.subjects[doc_sid]["rev"]
w.subjects[doc_sid]["rev"] += 1
try:
    capture(d, packet)
except Refusal as error:
    stale_source = str(error)
else:
    raise AssertionError("stale source accepted")
finally:
    w.subjects[doc_sid]["rev"] = saved_source_rev

original_rows = scene._rows_of
def rows(desk, source, session=None):
    if scene.source_head(source) == "captures":
        ids = source.split()[1:]
        return [{"cid": cid, "label": "Mock attachment", "summary": "No private store access",
                 "remaining": " ".join(i for i in ids if i != cid), "thumb": ""} for cid in ids]
    return original_rows(desk, source, session)

def mounted_composer():
    lens_ir._REUSE.clear()
    d._lens_good = {}
    with patch.object(scene, "_rows_of", side_effect=rows):
        mounted = lens_ir.compile_lens(d, home, (), [0], [])
    scene.emit(mounted)
    found = [n for n in walk(mounted) if n["key"] == target_key and
             any(a["on"] == "edit" for a in n.get("acts", []))]
    assert len(found) == 1, [n["key"] for n in walk(mounted) if n["key"].endswith("/dock/say")]
    return scene.painter_view(found[0])

consumer = mounted_composer()
assert 'captures="cap-999998 cap-999999"' in next(a["line"] for a in consumer["acts"] if a["on"] == "edit-quoted")
viewer = next(s["props"] for s in w.subjects.values()
              if s.get("props", {}).get("role") == "home-view" and s["props"].get("actor") == "alex")
viewer["viewing"] = other_note
draft["to"] = "pike"
navigated_consumer = mounted_composer()
assert next(a["line"] for a in consumer["acts"] if a["on"] == "edit-quoted") == next(
    a["line"] for a in navigated_consumer["acts"] if a["on"] == "edit-quoted")
assert draft["context"] == "cap-999998 cap-999999"
assert capture(d, packet) == snapshot
assert len(w.events) == fixture_at
# Native append in a separate disposable copy, only to the fixture Talk.
# No captures/private-store access, real Conversation or session save.
delivery = copy.deepcopy(d)
delivery.dispatch("desk", {"line": "read " + talk_sid, "whole": True})
delivery_before = len(delivery.world.events)
native_route = delivery.dispatch("desk", {
    "line": 'do append ' + talk_sid + ' line="Copy canonical route"', "whole": True})
assert not native_route.get("error") and not re.search(r"(^|\n)ERR", native_route.get("text", "")), native_route
assert len(delivery.world.events) > delivery_before, native_route
native_route_read = delivery.dispatch("desk", {"line": "read " + talk_sid, "whole": True})
assert "Copy canonical route" in native_route_read["text"], native_route_read
paired_menu = {
    "world_event": report["world_event"], "baseline_events": before,
    "fixture_events": fixture_at, "events_after_assertions": len(w.events),
    "exact_menu_hunk": menu_hunk, "origin": origin,
    "consumer": consumer, "navigated_consumer": navigated_consumer,
    "snapshot_for_isolated_consumer_test": snapshot,
    "fixture": {"source": source_note, "source_subject": doc_sid, "talk": talk,
                "talk_subject": talk_sid, "other_source": other_note, "other_talk": other_talk,
                "capture_ids": draft["context"]},
    "acceptance": "PASS canonical source/Talk menu fence, native disposable Talk route, compiled consumer/navigation",
    "unreadable_talk_refusal": unreadable, "stale_talk_refusal": stale_talk,
    "stale_source_refusal": stale_source,
    "native_canonical_append": {"destination": talk_sid, "receipt": native_route,
                                "events_before": delivery_before,
                                "events_after": len(delivery.world.events)},
    "limits": ["Consumer DOM/transport integration is tested separately using this exact artifact",
               "Capture rows are mocks; private capture delivery/detach unproven",
               "Native append only to disposable fixture Talk; no live sends or browser"],
}
(HERE / "PAIRED-MENU-COPY.json").write_text(json.dumps(paired_menu, indent=2) + "\n", encoding="utf-8")
print(f"Paired canonical menu/consumer copy passed: source/Talk integer fences, unreadable/stale refusals, "
      f"navigation/captures compiled, native canonical fixture Talk append; {report['world_event']}; "
      f"copy fixture setup {before}->{fixture_at}; assertion events {fixture_at}->{len(w.events)}; no live sends")
