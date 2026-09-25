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
    w = W(); w.events = [{"id": "e1", "target": "s1", "verb": "retitle", "args": {"title": "B"}}]
    assert deskd.touched_aspects(w, "s1", 1, 2, ["title"])
    assert not deskd.touched_aspects(w, "s1", 1, 2, ["prop:beds"])
    w.events.append({"id": "e2", "target": "a1", "changed": ["s1"], "verb": "prop", "args": {"beds": "3"}})
    assert deskd.touched_aspects(w, "s1", 1, 3, ["prop:beds"])
    assert not deskd.touched_aspects(w, "s1", 2, 3, ["title"])
    # Pike S5: the clicked appearance and its subject are judged together, on the aspects read
    w.events.append({"id": "e3", "target": "a1", "changed": ["s1"], "verb": "prop", "args": {"place": "x"}})
    assert not deskd.touched_aspects(w, {"a1", "s1"}, 3, 4, ["title", "prop:beds"])
    assert deskd.touched_aspects(w, {"a1", "s1"}, 3, 4, ["prop:place"])
    # Sable's baseline (3): an undo of a retitle is a touch of the title
    w.events = [{"id": "e1", "target": "s1", "verb": "retitle", "args": {"title": "B"}},
                {"id": "e2", "target": "e1", "verb": "undo", "args": {}}]
    assert deskd.touched_aspects(w, "s1", 2, 3, ["title"])
    assert not deskd.touched_aspects(w, "s1", 2, 3, ["prop:beds"])


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


def _scratch(name):
    import shutil, pathlib
    src, tmp = pathlib.Path("sessions/frontier-jeff-probe.pickle"), pathlib.Path(f"sessions/{name}.pickle")
    shutil.copy(src, tmp)
    return tmp


def test_a_frame_may_not_shadow_one_above_and_count_is_defined_inside_instances():
    import deskd
    tmp = _scratch("_test_scope")
    try:
        with deskd.Session("_test_scope", "jeff") as desk:
            shadow = chr(10).join(["x : column, of kind:note as a, each y", "y : column, of kind:note as a, each z", 'z : text "$a.title"'])
            try:
                scene.build(desk, shadow)
                raise AssertionError("shadowing admitted")
            except scene.LensRefusal as e:
                assert "would shadow the frame `as a`" in str(e)
            counted = chr(10).join(["root : column, of kind:note, each d", 'd : text "$count things here"'])
            sc = scene.build(desk, counted)
            assert [k["text"] for k in sc["kids"]] == ["2 things here", "2 things here"]
    finally:
        tmp.unlink(missing_ok=True)

def test_only_when_takes_a_value_test_and_prints_it():
    import deskd
    tmp = _scratch("_test_guard")
    try:
        with deskd.Session("_test_guard", "jeff") as desk:
            src = chr(10).join(["root : column, of kind:note, each c", 'c : text "$title", only when $beds > 5'])
            sc = scene.build(desk, src)
            shown = [k for k in sc["kids"] if not k.get("absent")]
            absent = [k for k in sc["kids"] if k.get("absent")]
            assert len(shown) == 1 and shown[0]["test"] == "$beds is 6 > 5"
            assert len(absent) == 1 and absent[0]["why"] == "no beds"
            src = chr(10).join(["root : column, of kind:note, each c", 'c : text "$title", only when $beds = 7'])
            sc = scene.build(desk, src)
            assert [k.get("why") for k in sc["kids"]] == ["$beds is 6, not = 7", "no beds"]
            text = scene.to_text(sc, "t", "jeff", 0)
            assert "(absent: $beds is 6, not = 7)" in text and "(absent: no beds)" in text
    finally:
        tmp.unlink(missing_ok=True)


def test_carry_and_drop_shape():
    refused("root : column, of kind:note, each c\nc : text a, carry, on drag do move $item x=$x", "cannot both `carry` and `on drag`")
    refused("root : column, on drop c do move $carried into=$item", "no part named 'c' says `carry`")
    refused("root : column, of kind:note, each c\nc : text a, carry, on drop c do prop $carried x=1; do prop $carried y=2", "one proposal")
    _, parts = scene.parse("root : column, of kind:note, each c, on drop c do move $carried into=$item\nc : text a, carry")
    assert parts["root"]["on"] == [{"on": "drop", "line": "do move $carried into=$item", "part": "c"}] and parts["c"]["carry"]
    import deskd
    tmp = _scratch("_test_carry")
    try:
        with deskd.Session("_test_carry", "jeff") as desk:
            sc = scene.build(desk, chr(10).join(["root : column, of kind:note, each c, on drop c do move $carried into=f01", 'c : text "$title", carry']))
            assert sc["acts"] == [{"on": "drop", "line": "do move $carried into=f01", "part": "c"}] and sc.get("defpart") and sc["reads"] == []
            assert sc["kids"][0]["acts"] == [{"on": "carry"}] and sc["kids"][0]["rev"] is not None
            text = scene.to_text(sc, "t", "jeff", 0)
            assert "· drop c: do move $carried into=f01" in text and "· carry" in text
            try:
                scene.build(desk, "root : column, carry")
                raise AssertionError("carry on the root admitted")
            except scene.LensRefusal as e:
                assert "needs a world thing" in str(e)
    finally:
        tmp.unlink(missing_ok=True)


def test_resolve_judges_frames_before_evaluation():
    src = chr(10).join(["root : column, of tag:trip as trip, each day", "day : text \"$trip.start\"", "loose : text \"$nobody.start\""])
    root, parts = scene.parse(src)
    scene.resolve(root, parts)                       # `loose` is not reachable from the root: not judged
    src2 = chr(10).join(["root : column, of tag:trip as trip, each day", "day : column, each z", "z : text \"$nobody.start\""])
    root, parts = scene.parse(src2)
    try:
        scene.resolve(root, parts)
        raise AssertionError("an unknown frame was admitted")
    except scene.LensRefusal as e:
        assert "$nobody.start: no part above this one is named `as nobody`" in str(e) and "frames in scope: it, trip" in str(e)
    root, parts = scene.parse(chr(10).join(["root : column, of tag:t as a, each c, derive d = weekday $today", "c : text \"$d $a.title $beds $me\""]))
    scopes = scene.resolve(root, parts)
    sc = scopes[id(parts["c"])]
    assert [scene.classify(x, sc) for x in ("d", "a", "beds", "me", "title", "it")] == ["let", "frame", "prop", "host", "field", "frame"]


def test_emission_gives_the_painter_its_contract():
    import deskd, json
    tmp = _scratch("_test_emit")
    try:
        with deskd.Session("_test_emit", "jeff") as desk:
            sc, _ = scene.scene_for(desk, "beds-lens")
    finally:
        tmp.unlink(missing_ok=True)
    assert sc["paint"] == {"kind": "frame", "flow": "column"}
    card = sc["kids"][0]
    assert card["paint"]["kind"] == "text" and card["paint"]["text"].endswith("beds")
    assert set(card["fence"]) >= {"item", "rev", "reads", "defpart"} and card["acts"][0]["on"] == "click"
    pv = scene.painter_view(sc)
    assert set(pv) == {"key", "paint", "acts", "kids", "part"} and set(pv["kids"][0]) == {"key", "paint", "acts", "kids", "fence", "part"}
    assert "reads" not in json.dumps({k: v for k, v in pv["kids"][0].items() if k != "fence"})


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
