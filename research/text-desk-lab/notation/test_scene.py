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


def test_a_part_is_judged_under_its_lens_style():
    # F18 (command center): a lens with its own style names roles the default style lacks; its parts must still hash
    src = "root : column, role page, of tag:day, each card\ncard : column, role card, carry\nbin : column, role page, on drop card do prop $carried status=done"
    roles = {"page", "card"}
    h = scene.defpart_hash(src, "bin", roles, "pixel")
    assert h and h == scene.defpart_hash(src + "\nfoot : text bye", "bin", roles, "pixel")
    try:
        scene.defpart_hash(src, "bin")
        assert False, "the default roles should refuse `page`"
    except scene.LensRefusal:
        pass


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


def test_fold_open_and_float():
    """Alex, 29 Sep: `fold ... open` starts unfolded, `fold ... float` is a menu drawn over the page; both print and emit."""
    src = chr(10).join(["ws : column", '  talk : column, fold "LOUNGE" open, share 2', '    t : text "a"',
                        '  log : column, fold "the world" float', '    ev : text "b"'])
    refused('x : column, fold "a" opne', "[open] [float]")
    refused("x : column, fold open open", "[open] [float]")
    import deskd, lens_ir
    tmp = _scratch("_test_fold")
    try:
        with deskd.Session("_test_fold", "jeff") as desk:
            sc = lens_ir.evaluate(desk, src)
            scene.emit(sc)
            talk, log = scene.painter_view(sc)["kids"]
            assert talk["paint"]["fold"] == {"folded": False, "label": "LOUNGE"} and talk["paint"]["share"] == 2
            assert log["paint"]["fold"] == {"folded": True, "label": "the world", "float": True}
            text = scene.to_text(sc, "ws", "jeff", 0)
            assert 'unfolded "LOUNGE"' in text and 'folded "the world" float' in text, text
    finally:
        tmp.unlink(missing_ok=True)


def test_peek_stays_while_folded():
    """a1032 (Alex, 30 Sep: 'see what they are working on at a glance'): `peek` marks a child the painter keeps showing
    while its parent is folded; it prints, emits on frames and text alike, and an absent part does not peek."""
    src = chr(10).join(["ws : column", '  tile : column, fold "pike"', '    now : column, peek', '      t : text "a"',
                        '    said : text "b", peek', '    gone : text "c", peek, only when $said = x', '    rest : text "d"'])
    root, parts = scene.parse(src)
    assert parts["ws"]["kids"][0]["kids"][0]["peek"] and not parts["ws"]["kids"][0]["kids"][3]["peek"]
    import deskd, lens_ir
    tmp = _scratch("_test_peek")
    try:
        with deskd.Session("_test_peek", "jeff") as desk:
            sc = lens_ir.evaluate(desk, src)
            scene.emit(sc)
            now, said, gone, rest = scene.painter_view(sc)["kids"][0]["kids"]
            assert now["paint"]["peek"] and said["paint"]["peek"], (now["paint"], said["paint"])
            assert "peek" not in gone["paint"] and "peek" not in rest["paint"], (gone["paint"], rest["paint"])
            assert scene.to_text(sc, "ws", "jeff", 0).count("peek") == 2
    finally:
        tmp.unlink(missing_ok=True)


def test_menu_entries_and_a_filled_fold_label():
    """Alex, 29 Sep: `on menu "<label>" do ...` entries, a fold label filled like text, and `handle <role>`."""
    src = chr(10).join(["ws : column", '  card : column, on menu "delete" do remove a1, on menu "start" do prop a1 status=doing',
                        '    more : column, fold "$title" handle meta', '      t : text "x"'])
    refused('x : column, on menu delete do remove a1', "on menu")
    refused('x : column, fold "a" handle', "handle <role>")
    root, parts = scene.parse(src)
    card = parts["ws"]["kids"][0]
    assert [(a["on"], a.get("label")) for a in card["on"]] == [("menu", "delete"), ("menu", "start")]
    assert card["kids"][0]["fold_handle"] == "meta"
    import deskd, lens_ir
    tmp = _scratch("_test_menu")
    try:
        with deskd.Session("_test_menu", "jeff") as desk:
            sc = lens_ir.evaluate(desk, src.replace("ws : column", "ws : column, the f01"))
            scene.emit(sc)
            card = scene.painter_view(sc)["kids"][0]
            assert [(a["on"], a["label"]) for a in card["acts"]] == [("menu", "delete"), ("menu", "start")] and card.get("fence") is not None
            fold = card["kids"][0]["paint"]["fold"]
            assert fold["handle"] == "meta" and "$" not in fold["label"] and fold["label"], fold
            text = scene.to_text(sc, "ws", "jeff", 0)
            assert '· menu "delete": do remove a1' in text and "handle meta" in text, text
    finally:
        tmp.unlink(missing_ok=True)


def test_fold_group():
    """Alex, 30 Sep: `fold ... group <name>`, an accordion: the group reaches the painter and both printers say it."""
    src = chr(10).join(["ws : column", '  a : column, fold "chat" open group talk', '    t : text "x"',
                        '  b : column, fold "turns" group talk', '    u : text "y"'])
    refused('x : column, fold "a" group', "group <name>")
    root, parts = scene.parse(src)
    assert [k["fold_group"] for k in parts["ws"]["kids"]] == ["talk", "talk"]
    import deskd, lens_ir
    tmp = _scratch("_test_group")
    try:
        with deskd.Session("_test_group", "jeff") as desk:
            sc = lens_ir.evaluate(desk, src)
            scene.emit(sc)
            kids = scene.painter_view(sc)["kids"]
            assert [k["paint"]["fold"].get("group") for k in kids] == ["talk", "talk"], kids
            assert scene.to_text(sc, "ws", "jeff", 0).count("group talk") == 2
    finally:
        tmp.unlink(missing_ok=True)


def test_value_test_has():
    """`has` and `!has`: the words contain the value, ignoring case; a value with a $name in it is filled."""
    m = scene._VALUE_TEST.fullmatch("$said has @$me")
    assert m and m.groups() == ("$said", "has", "@$me")
    assert scene._VALUE_TEST.fullmatch("$said !has @alex").group(2) == "!has"
    assert scene._compare("ok @Alex, look", "has", "@alex") and scene._compare("ok", "!has", "@alex")
    assert not scene._compare("ok", "has", "@alex") and scene._compare("5", ">", "3")


def test_replace_changes_one_exact_passage():
    """Alex, 29 Sep: one line of a note, changed without resending the note. Fenced as rewrite is."""
    import explore, re
    d = explore.fresh()
    slots = {}

    def do(line, who):
        slots[d.world.me] = (d.seen, d.open, d.last_event_seen)
        d.seen, d.open, d.last_event_seen = slots.get(who) or ({}, {d.world.root}, len(d.world.events))
        d.world.me = who
        r = d.dispatch("desk", {"line": line})
        return r.get("text") or ("ERR " + str(r.get("error")))

    do("look", "juniper")
    made = do(f'do create {d.world.root} kind=note title=lens text="a : column\\n  b : text \\"x\\", role meta\\n  c : text \\"y\\", role meta"', "juniper")
    nid = re.search(r"\b(a\d+)\b", made.split("created", 1)[-1]).group(1)
    assert "not looked" in do(f'do replace {nid} old="role meta" new="role tag"', "pike")
    do(f"read {nid}", "pike")
    assert "appears 2 times" in do(f'do replace {nid} old="role meta" new="role tag"', "pike")
    assert "appears 0 times" in do(f'do replace {nid} old="role nope" new="role tag"', "pike")
    assert do(f'do replace {nid} old="\\"y\\", role meta" new="\\"y\\", role tag"', "pike").startswith("ok replace")
    text = d.world.subjects[d.world.nodes[nid]["subject"]]["text"]
    assert text == 'a : column\n  b : text "x", role meta\n  c : text "y", role tag', text
    do(f"read {nid}", "juniper")
    do(f'do replace {nid} old="text \\"x\\"" new="text \\"z\\""', "pike")
    assert "stale" in do(f'do replace {nid} old="a : column" new="a : row"', "juniper")


def test_rooms_go_look_and_replay():
    """a678, rooms step 1: where you are is a world fact (a go event), a bare look narrates your room, undo leaves
    walking alone, the !! line folds it, and a worktree merge replays it."""
    import explore, pickle, re, rooms, tempfile, pathlib, worktree
    d = explore.fresh()
    slots = {}

    def do(line, who):
        slots[d.world.me] = (d.seen, d.open, d.last_event_seen)
        d.seen, d.open, d.last_event_seen = slots.get(who) or ({}, {d.world.root}, len(d.world.events))
        d.world.me = who
        r = d.dispatch("desk", {"line": line})
        return r.get("text") or ("ERR " + str(r.get("error")))

    def made(out):
        return re.search(r"created ([af]\d+)", out).group(1)

    root = d.world.root
    assert do("look", "jeff").startswith(f"{root} surface"), "no rooms yet: a bare look is the tree"
    assert "no rooms" in do("go lounge", "jeff")
    home = made(do(f"do create {root} kind=surface title=Home", "jeff"))
    lounge = made(do(f"do create {home} kind=surface title=Lounge", "jeff"))
    corner = made(do(f"do create {root} kind=surface title=\"Juniper's corner\"", "jeff"))
    desc = made(do(f'do create {lounge} kind=note title=Couches text="Low couches around a table."', "jeff"))
    talk = made(do(f"do create {lounge} kind=chat title=\"Lounge talk\"", "jeff"))
    letter = made(do(f'do create {lounge} kind=note title="A letter" text="Dear all"', "jeff"))
    for line in ("one", "two", "three", "four"):
        do(f'do append {talk} line="{line}"', "jeff")
    do(f"do prop {home} role=room", "jeff")
    do(f"do prop {lounge} role=room describe={desc} talk={talk}", "jeff")
    do(f"do prop {corner} role=resident actor=juniper", "jeff")

    assert do("look", "juniper").startswith(f"You are in Juniper's corner ({corner}), your own corner."), "a resident starts in their corner"
    assert do("look", "pike").startswith(f"You are in Home ({home})."), "no corner: Home"
    out = do("go lounge", "juniper")
    ev = re.match(r"ok (e\d+):", out).group(1)
    body = out.split("\n", 1)[1]
    head, clock, body = body.split("\n", 2)
    assert clock.startswith("No clock is set here; the house's time is "), clock      # a948 (3): every narration is dated
    body = head + "\n" + body
    assert body.startswith(f"You are in Lounge ({lounge}).\nLow couches around a table.\nNo one else is here.\nAt hand:\n  {letter} note \"A letter\"\n"), body
    assert "Couches" not in body and "  Jeff: two\n  Jeff: three\n  Jeff: four\n" in body, body
    assert not re.search(r"\b(px|cramped|offscreen|spills?)\b", body) and len(body.split()) < 250
    assert "Here with you: Juniper." in do("go Lounge", "pike")
    # the fence: a listed title is not a read; the talk lines let you speak
    assert "not looked" in do(f'do rewrite {letter} text="gone"', "pike")
    assert do(f'do append {talk} line="hi"', "pike").startswith("ok")
    # undo leaves walking alone, and says why; history lists it
    assert "is a go" in do(f"undo {ev}", "juniper")
    assert "nothing of yours to undo" in do("undo", "juniper")
    assert f"{ev} go juniper to={lounge}" in do("history", "juniper")
    # the !! line folds walking: one line per actor, their latest room
    do("look", "pike")
    for place in ("home", "lounge", "home"):
        do(f"go {place} :1", "juniper")
    head = do("look", "pike").split("\n", 1)[0]
    assert head.count("juniper went to") == 1 and "juniper went to Home" in head, head
    assert "is not a room" in do(f"go {root}", "juniper")
    # Alex is not placed: no go, and his look is the tree
    assert "not placed" in do("go lounge", "alex") and do("look", "alex").startswith(f"{root} surface")
    # replay: a go made in a worktree comes back with the merge
    old = worktree.SESSIONS
    worktree.SESSIONS = pathlib.Path(tempfile.mkdtemp())
    try:
        text, _ = worktree.handle("worktree fork walk", "base", d, "juniper")
        assert text.startswith("ok"), text
        path = worktree.SESSIONS / "base@walk.pickle"
        f = pickle.loads(path.read_bytes())
        f.world.me, f.seen, f.open, f.last_event_seen = "juniper", {}, {f.world.root}, len(f.world.events)
        before, n0 = worktree.ids_of(f), len(f.world.events)
        f.dispatch("desk", {"line": "go lounge"})
        worktree.record(f, "go lounge", "juniper", before, n0)
        assert rooms.room_of(f.world, "juniper") == lounge
        path.write_bytes(pickle.dumps(f))
        assert rooms.room_of(d.world, "juniper") == home
        do(f"look {lounge}", "jeff")
        assert do(f'do rename {lounge} title="The Lounge"', "jeff").startswith("ok")                 # the base touched the room meanwhile
        text, merged = worktree.handle("worktree merge walk", "base", d, "jeff")
        assert text.startswith("ok merged"), text
        assert rooms.room_of(merged.world, "juniper") == lounge and rooms.room_of(merged.world, "pike") == lounge
    finally:
        worktree.SESSIONS = old


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


def test_day_or_time():
    f = scene.INTERPS["day-or-time"][1]
    assert f(["e4 prop · 2026-09-25 21:40", "2026-09-25"]) == ("21:40", None)
    assert f(["2026-09-21 09:00", "2026-09-25"]) == ("Mon 21", None)
    assert f(["2026-09-01", "2026-09-25"]) == ("2026-09-01", None)
    assert f(["soon", "2026-09-25"])[0] is None


def test_code_runs_are_automatic_and_plain_opts_out():
    t = "Because the card changed:\n```\nif seen != now: refuse()\n```\nsee `fence` above"
    rs = scene.runs_of(t)
    assert [r.get("role") for r in rs] == [None, "code", None, "code", None] and rs[1]["block"] and rs[3]["text"] == "fence"
    assert scene.runs_of("no code here") is None
    n = {"text": t, "acts": [], "kids": []}
    scene.emit(n)
    assert n["paint"]["runs"] == rs and n["paint"]["text"] == t
    scene.emit({"text": t, "plain": True, "acts": [], "kids": []})
    m = {"text": t, "plain": True, "acts": [], "kids": []}
    scene.emit(m)
    assert "runs" not in m["paint"]


def test_count_word_and_true_size():
    """a1101: `count <selection>` is a size without drawing; $count on a repeat is its size before the clamp."""
    import deskd, lens_ir
    refused("root : column, of kind:note, count kind:note, each c\nc : text a", "a repeat already has $count")
    tmp = _scratch("_test_count")
    try:
        with deskd.Session("_test_count", "jeff") as desk:
            src = chr(10).join(["root : column",
                                '  line : text "$count notes", role meta, count kind:note, only when $count > 1',
                                '  none : text "$count gone", count tag:no-such-tag, only when $count > 0',
                                '  list : column, of kind:note, clamp 1, each c, text "$n of $count"',
                                '    foot : text "all $count"',
                                'c : text "$title ($count)"'])
            sc = lens_ir.evaluate(desk, src)
            line, none, lst = sc["kids"]
            assert line["text"] == "2 notes" and line["counted"] == ("kind:note", 2), line
            assert none.get("absent") and none["why"] == "$count is 0, not > 0", none
            assert lst["text"] == "1 of 2", lst["text"]
            assert lst["kids"][0]["text"].endswith("(2)") and lst["kids"][-1]["text"] == "all 2", [k["text"] for k in lst["kids"]]
            assert "· count 2 of kind:note" in scene.to_text(sc, "t", "jeff", 0)
    finally:
        tmp.unlink(missing_ok=True)


def test_scene_for_one_part_and_ok():
    """a1101: scene <lens> <part path> prints only that part; scene <lens> ok is one line; the lens name may be quoted;
    a lens without style= says so; lens and style edits say their effect on the receipt."""
    import deskd
    tmp = _scratch("_test_part")
    try:
        with deskd.Session("_test_part", "jeff") as desk:
            say = lambda line: (lambda r: r.get("text") or r.get("error"))(desk.dispatch("desk", {"line": line}))   # noqa: E731
            say("look")
            src = "\\n".join(["root : column", "  side : column", '    h : text \\"PEOPLE\\"', "    list : column, of kind:note, each c",
                              '  other : text \\"elsewhere\\"', 'c : text \\"$title\\"'])
            made = say(f'do create f01 kind=note tags=lens title="two words" text="{src}"')
            assert "~ lens two words compiles: " in made and "no style=; using the default (calm)" in made, made
            out = say('scene "two words" side')
            assert "part side: 1 match" in out and "PEOPLE" in out and "elsewhere" not in out, out
            assert "= root/side" in out and "no style=; using the default (calm)" in out.splitlines()[0]
            assert " matches · " in say("scene two words list/c")      # each instance of c is a match
            assert len(say("scene two words ok").splitlines()) == 1
            assert "no part 'nope'" in say("scene two words nope")
            say("find two words")
            aid = [s for s in desk.world.subjects.values() if s["title"] == "two words"][0]
            app = desk.world.appearances_of(aid["id"])[0]
            say(f"read {app} :3")
            broke = say(f'do replace {app} old="text \\"elsewhere\\"" new="text \\"elsewhere\\", role no-such"')
            assert "~ ! lens two words does not compile: line 5: no role 'no-such'" in broke and "| two words line 5: other :" in broke, broke
            assert say("scene two words ok").startswith("lens two words does not compile")
            # a style note, and a lens under it
            say('do create f01 kind=note tags=style title=plainer text="token paper = #fff\\ntoken ink = #111\\nrole body : ink"')
            say(f"read {app} :3")
            say(f'do replace {app} old=", role no-such" new=", role body"')
            said = say(f"do prop {app} style=plainer")
            assert "~ lens two words compiles" in said and "style plainer" in said, said
            st = [s for s in desk.world.subjects.values() if s["title"] == "plainer"][0]
            sa = desk.world.appearances_of(st["id"])[0]
            say(f"read {sa} :3")
            out = say(f'do append {sa} line="role oops on paper"')
            assert "~ style plainer does not parse: line 4" in out and "lenses using it: two words; all compile" in out, out
            say(f"read {sa} :3")
            out = say(f'do replace {sa} old="role oops on paper" new="role card : on papr"')
            assert "~ style plainer parses" in out and "- new: role card `on papr` (line 4)" in out, out
            say(f"read {sa} :3")
            out = say(f'do replace {sa} old="role body : ink" new="role bodies : ink"')
            assert "now refusing: 1" in out and "no role 'body' in style plainer" in out, out
    finally:
        tmp.unlink(missing_ok=True)


STYLE_SAMPLES = [
    "token paper = #EEE\ntoken ink = #111\ntoken gap = 8\ntoken text = plex 14/1.5\ntoken line = ink at 70%\n"
    "role a : on paper, ink, text down 2, pad gap, pad top gap, corner 3, corner gap, lift 1, lift gap, edge line\n"
    "role b : on papr, inky, text.pixel, space below gap /2, between gap x2, width 30em, border left ink, text at 12\n"
    "role c : text medium, hide title, ink at 40%, glow",
    "role x : on #fff",
    "role x : pad 12px",
    "role x on paper",
    "present card : title",
    "theme dark of calm\n  role x : ink",
    "token a = #000\nsomething else",
    "# only a comment\ntoken paper = #fff  # trailing comment\nrole y : on paper",
]


def test_style_check_agrees_with_the_painter():
    """a1101: scene.style_check mirrors desk-shell/style/style.js; judged against node running the real file."""
    import json, pathlib, shutil, subprocess
    here = pathlib.Path(scene.__file__).resolve().parent
    samples = STYLE_SAMPLES + [(here / "desk-shell" / "style" / "calm.style").read_text(encoding="utf-8")]
    for src in samples:
        py = scene.style_check(src)
        if not shutil.which("node"):
            continue
        js = json.loads(subprocess.run(["node", str(here / "desk-shell" / "checks" / "style-read.js")], input=src,
                                       capture_output=True, text=True, encoding="utf-8", check=True).stdout)
        assert (py["refusal"] or "").split(":")[0] == (js["refusal"] or ""), (src, py["refusal"], js["refusal"])
        assert sorted([r, p] for r, p, _l, _w in py["unread"]) == sorted(js["unread"]), (src, py["unread"], js["unread"])
    bad = scene.style_check(STYLE_SAMPLES[0])["unread"]
    assert ("b", "on papr", 7,"names no token of the right kind") in bad


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            n += 1
            print("ok", name)
    print(f"{n} passed")
