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


def test_binds_on_chain_are_reads():
    """sable-8 amended: a gesture's fence includes the binds above it. `the` carries the membership read (q, S); an
    instance carries the aspects its selection's terms name. Soundness instrument: 21 unsound of 900 before, 0 after."""
    import deskd, lens_ir
    assert lens_ir.term_aspects("kind:task,prop:owner=juniper,-prop:status=done,due<today,tag:x,in:f01") == ({"prop:owner", "prop:status", "due", "tags"}, {"place"})
    tmp = _scratch("_test_binds")
    try:
        with deskd.Session("_test_binds", "jeff") as desk:
            desk.repl("look"); desk.repl("do create f01 kind=note title=Charter text=one")
            desk.repl("do create f01 kind=task title=Chore owner=jeff")
            src = chr(10).join(["root : column, the kind:note,title:Charter, as ch", "  open : text \"$ch.title\", on click do prop $item open=1",
                                "  chores : column, of kind:task,prop:owner=jeff, each c", "c : text \"$title\", on click do check $item"])
            sc = lens_ir.evaluate(desk, src)
            gest = sc["kids"][0]
            sel = [e for e in gest["reads"] if e[0] == "select"]
            assert sel and sel[0][1] == "kind:note,title:Charter" and len(sel[0][2]) == 1, gest["reads"]
            chore = sc["kids"][1]["kids"][0]
            assert any(e[0] != "select" and "prop:owner" in e[2] for e in chore["reads"]), chore["reads"]
            assert deskd.same_answer(desk, sel[0][1], sel[0][2])[0]
            desk.repl("do create f01 kind=note title=Charter text=two")
            same, now = deskd.same_answer(desk, sel[0][1], sel[0][2])
            assert not same and len(now) == 2
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


def test_a_print_reads_what_it_printed_whole():
    """jeff-2: the seen index is per aspect. A look that printed a title and a word count has not read the text; a
    rewrite after it is refused as blind; a read of the whole text admits it; a person's own write of an aspect counts."""
    import deskd
    tmp = _scratch("_test_reads")
    try:
        with deskd.Session("_test_reads", "jeff") as desk:
            desk.repl("look")
            out = desk.repl('do create f01 kind=note title=Bills text="Rent split by days here."')
            nid = out.split("created ")[1].split()[0]
            desk.repl("do prop " + nid + " owe=5")                          # own write: prop:owe is seen
            desk.repl("do prop " + nid + " owe=6")
            desk.world.me = "sable"
            desk.repl("look")
            try:
                desk.repl("do rewrite " + nid + ' text="Rent by nights."')
                raise AssertionError("a rewrite after a look that printed no text was admitted")
            except Exception as e:
                assert "have not seen " + nid + "'s text" in str(e), str(e)
            desk.repl("read " + nid)
            assert desk.repl("do rewrite " + nid + ' text="Rent by nights."').startswith("ok")
            desk.world.me = "jeff"
            assert desk.repl("do prop " + nid + " owe=7").startswith("ok")     # the outline line showed the prop
    finally:
        tmp.unlink(missing_ok=True)


def test_clamped_repeat_compares_the_shown_prefix():
    """sable-10: a clamped repeat records the shown prefix; the fence compares only that, as a set."""
    import deskd, lens_ir
    tmp = _scratch("_test_clamp")
    try:
        with deskd.Session("_test_clamp", "jeff") as desk:
            desk.repl("look")
            for t in ("One", "Two", "Three"):
                desk.repl("do create f01 kind=task title=" + t)
            sc = lens_ir.evaluate(desk, chr(10).join(["root : column, of kind:task, clamp 2, each t", 't : text "$title", on click do check $item']))
            sel = [e for e in sc["kids"][0]["reads"] if e[0] == "select"][0]
            assert len(sel[2]) == 2 and sel[3] == 2
            assert deskd.same_answer(desk, sel[1], sel[2], sel[3])[0]
            desk.repl("do create f01 kind=task title=Four")
            assert deskd.same_answer(desk, sel[1], sel[2], sel[3])[0]         # beyond the clamp: not shown, not read
            desk.repl("do remove " + sel[2][0])
            assert not deskd.same_answer(desk, sel[1], sel[2], sel[3])[0]
    finally:
        tmp.unlink(missing_ok=True)


def test_paint_words_print_and_emit():
    """pike-7 sections 6 and 9, lowered: grid tracks, gap, scroll, fold, measure, verbatim, lines, share, hint."""
    src = chr(10).join(["ws : grid 1 3 fit, gap 12", '  bar : column, fold, text "Projects"', "  chat : column, scroll end, measure 70ch",
                        '    say : text "", lines 1..8, hint "Message"', '  page : column, share 2', '    code : text "x = 1", verbatim'])
    root, parts = scene.parse(src)
    by = {k["name"]: k for k in scene._walk(parts["ws"])}
    assert by["ws"]["tracks"] == ["1fr", "3fr", "fit"] and by["bar"]["fold"] and by["say"]["lines"] == [1, 8]
    refused("x : column, gap 4, verbatim", "text word")
    refused("x : grid", "grid <tracks>")
    refused('x : text "a", gap 4', "frame word")
    import deskd, lens_ir
    tmp = _scratch("_test_paint")
    try:
        with deskd.Session("_test_paint", "jeff") as desk:
            sc = lens_ir.evaluate(desk, src)
            scene.emit(sc)
            pv = scene.painter_view(sc)
            assert pv["paint"]["tracks"] == ["1fr", "3fr", "fit"] and pv["paint"]["gap"] == 12
            bar, chat, page = pv["kids"]
            assert bar["paint"]["fold"] == {"folded": True, "label": "Projects"} and bar["acts"] == [{"on": "fold"}] and "fence" not in bar
            assert chat["paint"]["scroll"] == "end" and chat["paint"]["measure"] == "70ch"
            assert chat["kids"][0]["paint"]["lines"] == [1, 8] and chat["kids"][0]["paint"]["hint"] == "Message"
            assert page["paint"]["share"] == 2 and page["kids"][0]["paint"]["wrap"] == "verbatim"
            text = scene.to_text(sc, "ws", "jeff", 0)
            for w in ("grid 1fr 3fr fit", "gap 12", "folded", "scroll end", "measure 70ch", "lines 1..8", 'hint "Message"', "share 2", "verbatim"):
                assert w in text, w
            assert "· fold" not in text
    finally:
        tmp.unlink(missing_ok=True)


def test_freshness_words_are_host_reads():
    """Juniper: $touched is the last event on the thing, $changed.<field> the last that changed that aspect; a comment
    refreshes the first and not the second; undo is not a touch; neither enters the gesture fence."""
    import deskd, lens_ir
    tmp = _scratch("_test_touched")
    try:
        with deskd.Session("_test_touched", "jeff") as desk:
            desk.repl("look")
            nid = desk.repl("do create f01 kind=task title=Suite status=doing").split("created ")[1].split()[0]
            import re as _re
            done = _re.search(r"\[(e\d+)\]", desk.repl("do prop " + nid + " status=done")).group(1)
            cm = _re.search(r"\[(e\d+)\]", desk.repl("do comment " + nid + ' line="nice"')).group(1)
            src = chr(10).join(["root : column, of kind:task, each t", 't : text "$title $changed.status / $touched / $touched.by", on click do check $item'])
            sc = lens_ir.evaluate(desk, src)
            t = sc["kids"][0]
            assert t["text"].startswith("Suite " + done + " prop ·") and " comment ·" in t["text"] and t["text"].endswith("/ jeff"), t["text"]
            assert all(e[0] != done and not str(e[0]).startswith("e") for e in t["reads"]), t["reads"]
            assert not any(e[0] == "touched" and e[3] is None for e in sc["R"] if e[0] == "touched" and e[2] is None)
            desk.repl("undo " + cm)
            desk.repl("undo " + done)
            sc2 = lens_ir.evaluate(desk, src)
            assert "no changed.status" not in str(sc2) and done not in sc2["kids"][0]["text"], sc2["kids"][0]["text"]
    finally:
        tmp.unlink(missing_ok=True)


def test_time_and_date_interpretations():
    assert scene.INTERPS["time"][1](["e412 prop · 2026-09-25 21:40"]) == ("21:40", None)
    assert scene.INTERPS["date"][1](["e412 prop · 2026-09-25 21:40"]) == ("2026-09-25", None)
    assert scene.INTERPS["date"][1](["2026-10-10"]) == ("2026-10-10", None)
    assert scene.INTERPS["time"][1](["2026-10-10"])[0] is None and scene.INTERPS["time"][1](["soon"])[0] is None
