"""Admission tests for scene.py. Most of these began as defects reproduced by the Astra team's foundations audit
(research/shared-visual-desk/round5-bridge/foundations.md). Run: python test_scene.py"""

import scene


def refused(src, needle):
    try:
        scene.parse(src)
    except scene.LensRefusal as e:
        assert needle in str(e), f"refused, but for another reason: {e}"
        return True
    raise AssertionError(f"admitted, expected a refusal mentioning {needle!r}:\n{src}")


def test_literal_text_keeps_commas_and_hashes():
    _, parts = scene.parse('root : column\n  a : text "Hello, world # not a comment", role body')
    assert parts["root"]["kids"][0]["text"] == "Hello, world # not a comment"
    assert parts["root"]["kids"][0]["role"] == "body"


def test_backslash_n_in_a_lens_is_data():
    _, parts = scene.parse('root : column\n  a : text "C:\\new\\temp"')
    assert parts["root"]["kids"][0]["text"] == "C:\\new\\temp"


def test_refusals():
    refused("root : column, each root", "may not recurse")
    refused("root : column, of kind:note, each a\na : column, of kind:note, each root", "may not recurse")
    refused("root : column\nroot : row", "already defined")
    refused("root : column\n  a : text x\n  a : text y", "already has a child")
    refused("root : column, role no-such-role", "no role")
    refused("root : column, on drop do link $item to=$other", "on <click|edit|drag>")
    refused("root : column, width 300", "cannot say")
    # $me is not refused any more: a name outside NAMES is a prop of the thing, printed (no me) when it lacks it (Juniper, Pike)
    _, parts = scene.parse("root : column\n  a : text $me")
    assert parts["root"]["kids"][0]["props"] == ["me"]
    refused("root : column, of kind:note", "say what with `each")
    # Pike's binding words (round two of the object/facet frontier)
    refused("root : column, the tag:trip, each x\nx : text a", "names exactly one thing")
    refused("root : column, the tag:trip as title", "shadow a built-in")
    refused("root : column, as trip", "needs `the`, `of` or `over`")
    refused("root : column, derive d = plus $a $b", "no interpretation")
    refused("root : column, derive d = day-n $a", "takes 2 input(s)")
    refused("root : column, capture start=1", "no `the`")
    _, parts = scene.parse("root : column, the tag:trip as trip\n  h : derive d = day-n $trip.start 2, text $d")
    assert parts["root"]["as"] == "trip" and parts["root"]["kids"][0]["derive"] == [("d", "day-n", ["$trip.start", "2"])]


def test_a_gesture_may_not_run_a_script():
    # build step 1c (Juniper A4): the scene must be able to say what a click will do
    refused("root : column, text hi, on click do run tidy $item", "may not run a script")
    _, parts = scene.parse("root : column, text hi, on click do prop $item done=1")
    assert parts["root"]["on"] == [{"on": "click", "line": "do prop $item done=1"}]


def test_a_painted_gesture_that_could_fire_a_rule_is_refused():
    import deskd
    class D: pass
    d = D(); d.rules = []
    assert deskd.rules_blocking(d, "do prop a05 week=1") is None
    assert "runs the script tidy" in deskd.rules_blocking(d, "run tidy a05")
    d.rules = [{"id": "r1", "on": "tag", "sel": "on tag"}]
    assert deskd.rules_blocking(d, "do prop a05 week=1") is None
    assert "rule r1 fires on every tag" in deskd.rules_blocking(d, "do tag a05 add=done")
    d.rules = [{"id": "r2", "sel": "kind:task,due<2026-09-19"}]
    assert "rule r2 (when kind:task,due<2026-09-19)" in deskd.rules_blocking(d, "do move a05 into=f02")


def test_a_part_keeps_its_identity_when_the_lens_changes_elsewhere():
    # Pike a308: fence per part, not per lens
    src = "root : column, of tag:day as day, each card\ncard : text \"$title $beds\", on click do prop $item beds=1\nfoot : text bye"
    h = scene.defpart_hash(src, "root/card")
    assert h and h == scene.defpart_hash(src.replace("text bye", "text goodbye"), "root/card")
    assert h != scene.defpart_hash(src.replace("of tag:day", "of tag:night"), "root/card")
    assert h != scene.defpart_hash(src.replace("beds=1", "beds=2"), "root/card")
    assert scene.defpart_hash(src, "root/nowhere") is None
    assert scene._aspect_of_field("title") == "title" and scene._aspect_of_field("beds") == "prop:beds"
    assert scene._aspect_of_field("id") is None and scene._aspect_of_field("x") is None


def test_a_read_is_judged_by_aspect():
    import deskd
    class W: pass
    w = W(); w.events = [{"target": "s1", "verb": "retitle", "args": {"title": "B"}}]
    assert deskd.touched_aspects(w, "s1", 1, 2, ["title"])
    assert not deskd.touched_aspects(w, "s1", 1, 2, ["prop:beds"])
    w.events.append({"target": "a1", "changed": ["s1"], "verb": "prop", "args": {"beds": "3"}})
    assert deskd.touched_aspects(w, "s1", 1, 3, ["prop:beds"])
    assert not deskd.touched_aspects(w, "s1", 2, 3, ["title"])
    # Pike S5: the clicked appearance and its subject are judged together, on the aspects read
    w.events.append({"target": "a1", "changed": ["s1"], "verb": "prop", "args": {"place": "x"}})
    assert not deskd.touched_aspects(w, {"a1", "s1"}, 3, 4, ["title", "prop:beds"])
    assert deskd.touched_aspects(w, {"a1", "s1"}, 3, 4, ["prop:place"])


def test_a_repeat_records_its_membership_read():
    import deskd, shutil, pathlib
    src, tmp = pathlib.Path("sessions/frontier-jeff-probe.pickle"), pathlib.Path("sessions/_test_probe.pickle")
    shutil.copy(src, tmp)          # a Session saves on exit; the committed scratch session must not change from a test
    try:
        with deskd.Session("_test_probe", "jeff") as desk:
            sc, _ = scene.scene_for(desk, "beds-lens")
    finally:
        tmp.unlink(missing_ok=True)
    m = sc["members"]
    assert m["of"] == "kind:note" and m["n"] == len(m["ids"]) == len(sc["kids"]) and isinstance(m["at"], int)


def test_a_batch_applies_whole_or_not_at_all():
    import deskd, shutil, pathlib
    src, tmp = pathlib.Path("sessions/frontier-jeff-probe.pickle"), pathlib.Path("sessions/_test_batch.pickle")
    shutil.copy(src, tmp)
    try:
        with deskd.Session("_test_batch", "jeff") as desk:
            n0 = len(desk.world.events)
            desk.batch = True
            r = desk.dispatch("desk", {"line": "look; do prop a03 beds=7; do prop a999 x=1"})
            assert "rolled back" in r["text"] and r["batch_error"]
            assert len(desk.world.events) == n0, "the refused batch left events behind"
            sj = desk.world.subjects[desk.world.nodes["a03"]["subject"]]
            assert (sj.get("props") or {}).get("beds") != "7", "the rolled-back prop write survived"
            r = desk.dispatch("desk", {"line": "look; do prop a03 beds=7"})
            assert len(desk.world.events) == n0 + 1 and not r["batch_error"]
    finally:
        tmp.unlink(missing_ok=True)


def test_command_values_keep_their_quotes():
    assert scene._cmd_value('She said "yes"') == 'She said \\"yes\\"'
    assert scene._cmd_value("C:\\temp") == "C:\\\\temp"


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            n += 1
            print("ok", name)
    print(f"{n} passed")
