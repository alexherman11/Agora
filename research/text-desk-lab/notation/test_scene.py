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


def test_a_pulsing_role_is_printed():
    # a1140: the painter moves a role whose words include pulse; the print must say what the eye sees moving
    text = ("token ink = #111111\nrole waiting : text down, ink, pulse   # waits on Alex\n"
            "role pulsed : ink, pulse down\nrole chip : ink\n")
    orig = scene.style_source
    scene.style_source = lambda desk, name: {"text": text} if name == "pixel" else None
    try:
        assert scene.pulsing_roles(None, "pixel") == {"waiting"}      # `pulse down` is not the word pulse
        assert scene.pulsing_roles(None, None) == set()               # no calm note, no seed under this stub
    finally:
        scene.style_source = orig
    sc = {"role": "chip", "kids": [{"role": "waiting", "kids": []}]}
    scene.mark_pulse(sc, {"waiting"})
    assert not sc.get("pulse") and sc["kids"][0]["pulse"]
    scene.emit(sc["kids"][0])
    assert "pulse" not in sc["kids"][0]["paint"]                       # printer-side only: the role class carries it


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
    src, tmp = deskd.SESSIONS / "frontier-jeff-probe.pickle", deskd.SESSIONS / "_test_probe.pickle"
    shutil.copy(src, tmp)          # a Session saves on exit; the committed scratch session must not change from a test
    try:
        with deskd.Session("_test_probe", "jeff") as desk:
            sc, _ = scene.scene_for(desk, "beds-lens")
    finally:
        tmp.unlink(missing_ok=True)
    m = sc["members"]
    assert m["of"] == "kind:note" and m["n"] == len(m["ids"]) == len(sc["kids"]) and isinstance(m["at"], int)


def _scratch(name):
    import shutil, deskd           # anchored like deskd's own sessions, so the test runs from any directory
    src, tmp = deskd.SESSIONS / "frontier-jeff-probe.pickle", deskd.SESSIONS / f"{name}.pickle"
    shutil.copy(src, tmp)
    return tmp


def test_a_frame_may_not_shadow_one_above_and_count_is_defined_inside_instances():
    import deskd, lens_ir
    tmp = _scratch("_test_scope")
    try:
        with deskd.Session("_test_scope", "jeff") as desk:
            shadow = chr(10).join(["x : column, of kind:note as a, each y", "y : column, of kind:note as a, each z", 'z : text "$a.title"'])
            try:
                lens_ir.evaluate(desk, shadow)
                raise AssertionError("shadowing admitted")
            except scene.LensRefusal as e:
                assert "would shadow the frame `as a`" in str(e)
            counted = chr(10).join(["root : column, of kind:note, each d", 'd : text "$count things here"'])
            sc = lens_ir.evaluate(desk, counted)
            assert [k["text"] for k in sc["kids"]] == ["2 things here", "2 things here"]
    finally:
        tmp.unlink(missing_ok=True)

def test_one_word_per_line():
    """Alex, 5 Oct (out of the comma lists): a part line says what the part is and how it looks; every other word is its
    own line under it, among its child parts. The comma list is still read; to_lines prints the one form; both parse
    to the same tree, and a refusal names the word's own line."""
    lines = chr(10).join([
        "card : column, role card",
        '  let size = "big" when $beds > 5',
        '  let size = "small" when $beds <= 5',
        '  let size = "unsized" otherwise',
        "  of kind:note",
        "  each t",
        "  on click do check $item",
        '  h : text "Things"',
        "    only when $beds > 2",
        't : text "$title"',
        "l : column",
        "  of kind:task",
        "  by priority rank",
        "  each t"])
    commas = chr(10).join([
        'card : column, let size = "big" when $beds > 5, let size = "small" when $beds <= 5, let size = "unsized" otherwise, of kind:note, each t, on click do check $item, role card',
        '  h : text "Things", only when $beds > 2',
        't : text "$title"',
        "l : column, of kind:task, by priority, rank, each t"])

    def norm(node):
        return {**{k: v for k, v in node.items() if k not in ("line", "kids", "src", "words")}, "kids": [norm(k) for k in node["kids"]]}
    a, b = scene.parse(lines), scene.parse(commas)
    assert a[0] == b[0] == "card" and {k: norm(v) for k, v in a[1].items()} == {k: norm(v) for k, v in b[1].items()}
    assert a[1]["card"]["kids"][0]["line"] == 8 and a[1]["card"]["kids"][0]["only"] == "$beds > 2" and a[1]["l"]["by"] == ["priority", "rank"]
    assert a[1]["l"]["src"] == b[1]["l"]["src"] == "l : column, of kind:task, by priority rank, each t"
    assert scene.to_lines(commas) == lines and scene.to_lines(lines) == lines
    refused("of kind:note" + chr(10) + "root : column", "line 1: 'of kind:note' is a word with no part above it")
    refused("root : column" + chr(10) + "  of kind:note" + chr(10) + "  eachh t", "line 3: a lens cannot say 'eachh t'")
    refused("root : column" + chr(10) + "  t : text a" + chr(10) + "  of kind:note" + chr(10) + "  each t" + chr(10) + "    role nosuch", "line 5: no role 'nosuch'")
    refused("root : column" + chr(10) + "  of kind:note", "line 1: `of`/`over` repeats something")      # a part's checks wait for all its lines
    _, parts = scene.parse('root : column' + chr(10) + '  the a01' + chr(10) + '  t : text "a"' + chr(10) + '    hint "say : it"')
    assert "say : it" in str(parts["root"]["kids"][0]["hint"]) and parts["root"]["the"] == "a01"


def test_only_when_takes_a_value_test_and_prints_it():
    import deskd, lens_ir
    tmp = _scratch("_test_guard")
    try:
        with deskd.Session("_test_guard", "jeff") as desk:
            src = chr(10).join(["root : column, of kind:note, each c", 'c : text "$title", only when $beds > 5'])
            sc = lens_ir.evaluate(desk, src)
            shown = [k for k in sc["kids"] if not k.get("absent")]
            absent = [k for k in sc["kids"] if k.get("absent")]
            assert len(shown) == 1 and shown[0]["test"] == "$beds > 5 ($beds=6)"
            assert len(absent) == 1 and absent[0]["why"] == "can't tell: no beds ($beds=none)"
            src = chr(10).join(["root : column, of kind:note, each c", 'c : text "$title", only when $beds = 7'])
            sc = lens_ir.evaluate(desk, src)
            assert [k.get("why") for k in sc["kids"]] == ["$beds = 7 is false ($beds=6)", "can't tell: no beds ($beds=none)"]
            text = scene.to_text(sc, "t", "jeff", 0)
            assert "(absent: $beds = 7 is false ($beds=6))" in text and "(absent: can't tell: no beds ($beds=none))" in text
            # 5 Oct: the older spelling with a bare word is read as the expression with the word quoted, the one way
            _, parts = scene.parse("root : column, of kind:note, each c\nc : text a, only when $status=done, role mark when $kind = note")
            assert parts["c"]["only"] == '$status = "done"' and parts["c"]["role_when"] == [("mark", '$kind = "note"')]
            try:
                scene.resolve(*scene.parse('root : column, of kind:note, each c\nc : text a, only when $kind = "note" and $beds > big'))
                raise AssertionError("a bare word that names no let was admitted")
            except scene.LensRefusal as e:
                assert "`big` in `only when" in str(e), e
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
    import deskd, lens_ir
    tmp = _scratch("_test_carry")
    try:
        with deskd.Session("_test_carry", "jeff") as desk:
            sc = lens_ir.evaluate(desk, chr(10).join(["root : column, of kind:note, each c, on drop c do move $carried into=f01", 'c : text "$title", carry']))
            assert sc["acts"] == [{"on": "drop", "line": "do move $carried into=f01", "part": "c"}] and sc.get("defpart") and sc["reads"] == []
            assert sc["kids"][0]["acts"] == [{"on": "carry"}] and sc["kids"][0]["rev"] is not None
            text = scene.to_text(sc, "t", "jeff", 0)
            assert "· drop c: do move $carried into=f01" in text and "· carry" in text
            try:
                lens_ir.evaluate(desk, "root : column, carry")
                raise AssertionError("carry on the root admitted")
            except scene.LensRefusal as e:
                assert "needs a world thing" in str(e)
    finally:
        tmp.unlink(missing_ok=True)


def test_role_when_follows_state():
    """a1105: `role <name> when <selection | value test>`; the first that holds wins, else the plain role, and the
    scene prints the role it chose and why. Both evaluators agree."""
    refused("root : column, role card, role card.plain when", "role <name> when")
    refused("root : column, role card, role nosuch when prop:x=1", "no role 'nosuch'")
    try:
        scene.resolve(*scene.parse('root : column, of kind:task, each c\nc : text "a", role card when $nobody.x = 1'))
        raise AssertionError("a role's test read a frame no part names")
    except scene.LensRefusal as e:
        assert "no part above" in str(e), e
    _, parts = scene.parse("root : column, role card, role mark when prop:aim=open, role sheet when $n > 2")
    assert parts["root"]["role"] == "card" and parts["root"]["role_when"] == [("mark", "prop:aim=open"), ("sheet", "$n > 2")]
    import deskd, lens_ir
    tmp = _scratch("_test_rolewhen")
    try:
        with deskd.Session("_test_rolewhen", "jeff") as desk:
            desk.repl("look")
            desk.repl("do create f01 kind=task title=Plain")
            desk.repl("do create f01 kind=task title=Aim aim=open")
            desk.repl("do create f01 kind=task title=Both aim=open weight=9")
            src = chr(10).join(["root : column, of kind:task, each c",
                                'c : text "$title", role card, role mark when prop:aim=open,prop:weight=9, role sheet when prop:aim=open, role said when $weight > 3'])
            for sc in (lens_ir.evaluate(desk, src),):
                got = {k["text"]: (k["role"], k.get("since")) for k in sc["kids"]}
                assert got == {"Plain": ("card", None), "Aim": ("sheet", "prop:aim=open"), "Both": ("mark", "prop:aim=open,prop:weight=9")}, got
                scene.emit(sc)
                assert [k["paint"].get("role") for k in sc["kids"]] == ["card", "sheet", "mark"]
                text = scene.to_text(sc, "t", "jeff", 0)
                assert '"Aim" [sheet, since prop:aim=open]' in text and '"Plain" [card]' in text, text
            sc = lens_ir.evaluate(desk, src.replace("role mark when prop:aim=open,prop:weight=9, role sheet when prop:aim=open, ", ""))
            got = {k["text"]: (k["role"], k.get("since")) for k in sc["kids"]}
            assert got == {"Plain": ("card", None), "Aim": ("card", None), "Both": ("said", "$weight > 3 ($weight=9)")}, got
            sc = lens_ir.evaluate(desk, "root : column, role mark when kind:task,title:Nothing-here")
            assert sc["role"] is None and "since" not in sc          # no plain role, nothing holds: no role
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
    """`has` and `!has`: the words contain the value, ignoring case; a value with a $name in it is filled. Since 5 Oct
    there is one path, the expression evaluator; scene._one_test reads the older spelling as the expression."""
    import expr as X
    assert scene._one_test("$said has @$me", 1) == "$said has @$me"
    assert scene._one_test("$said !has @alex", 1) == "$said !has @alex"
    assert scene._one_test("$status=done", 1) == '$status = "done"' and scene._one_test("$beds>5", 1) == "$beds > 5"
    assert scene._one_test("kind:task,prop:x=1", 1) == "kind:task,prop:x=1"

    def env(**vals):
        return {"get": lambda n: vals.get(n.lstrip("$")), "select": lambda q: [], "field": lambda i, f: None, "reads": []}
    assert X.run("$said has @$me", env(said="ok @Alex, look", me="alex"))[0].v is True
    assert X.run("$said !has @alex", env(said="ok"))[0].v is True
    assert X.run("$said has @alex", env(said="ok"))[0].v is False
    assert X.run("$n > 3", env(n="5"))[0].v is True


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


def test_what_you_made_you_have_seen():
    """a1190: a create's maker has seen all it wrote (title, text, tags, props), so a rewrite of their own text= needs
    no read; someone who only looked at it is still fenced. A 30 Sep change (create touches only its parent's
    contents) had marked the new thing seen for contents alone, and the maker's next rewrite was refused."""
    import explore, re
    d = explore.fresh()
    slots = {}

    def do(line, who):
        slots[d.world.me] = (d.seen, d.open, d.last_event_seen)
        d.seen, d.open, d.last_event_seen = slots.get(who) or ({}, {d.world.root}, len(d.world.events))
        d.world.me = who
        r = d.dispatch("desk", {"line": line})
        return r.get("text") or ("ERR " + str(r.get("error")))

    root = d.world.root
    do("look", "juniper")
    nid = re.search(r"created (a\d+)", do(f"do create {root} kind=note title=tidy tags=verb text=x", "juniper")).group(1)
    do(f"look {nid} :1", "juniper")
    # a1156: a verb's lines are stored text, bound when saved, so the new text is a step something answers (look)
    assert do(f"do rewrite {nid} text=look", "juniper").startswith("ok"), "the maker rewrites the text they typed"
    do(f"look {nid} :1", "pike")
    assert "have not seen" in do(f"do rewrite {nid} text=z", "pike"), "a look is not a read for anyone else"
    assert do(f"do prop {root} mood=calm", "juniper").startswith("ok"), "a create still leaves its parent's props unstaled"


def test_a_desktop_snapshot_is_not_a_look():
    """a2872: the Desktop asks /api/snapshot at every change anyone makes, and its outline marked every line's title
    and props seen for the asker. Alex, who had looked once, then retitled over pike's newer title without being refused
    (ran on a copy, e5105). Painting someone's screen must never count as their reading it."""
    import explore, deskd, re
    d = explore.fresh()
    slots = {}

    def do(line, who):
        slots[d.world.me] = (d.seen, d.open, d.last_event_seen)
        d.seen, d.open, d.last_event_seen = slots.get(who) or ({}, {d.world.root}, len(d.world.events))
        d.world.me = who
        r = d.dispatch("desk", {"line": line})
        return r.get("text") or ("ERR " + str(r.get("error")))

    do("look", "juniper")
    nid = re.search(r"created (a\d+)", do(f"do create {d.world.root} kind=note title=first text=x", "juniper")).group(1)
    do(f"look {nid}", "alex")                              # alex has looked once, at the old title
    do(f"look {nid}", "pike")
    assert do(f"do retitle {nid} title=second", "pike").startswith("ok")
    slots[d.world.me] = (d.seen, d.open, d.last_event_seen)
    d.seen, d.open, d.last_event_seen = slots["alex"]
    d.world.me = "alex"
    idx = dict(getattr(d, "_seen_idx", None) or {})
    deskd.snapshot_for(d)                                  # the Desktop repaints for alex
    assert dict(getattr(d, "_seen_idx", None) or {}) == idx, "a snapshot wrote what alex has seen"
    out = do(f"do retitle {nid} title=blind", "alex")
    assert "stale" in out, out


def test_edits_to_what_you_made_are_told():
    """a1471 (sketch2, c1439 c1450): when someone else changes a note or task you made, your next reply says so in a
    ~ line of its own (who, which line, the event, its undo), not in the !! counts. Your own edits, a chat line and
    a comment are not told so; ten quick edits by one person are one line; edits an hour apart are two."""
    import explore, re
    d = explore.fresh()
    slots = {}

    def do(line, who):
        slots[d.world.me] = (d.seen, d.open, d.last_event_seen)
        d.seen, d.open, d.last_event_seen = slots.get(who) or ({}, {d.world.root}, len(d.world.events))
        d.world.me = who
        r = d.dispatch("desk", {"line": line})
        return r.get("text") or ("ERR " + str(r.get("error")))

    def ev(out):
        return re.search(r"\b(e\d+)\b", out).group(1)

    def head(out):
        return [l for l in out.splitlines() if l.startswith(("!!", "~ "))]

    root = d.world.root
    do("look", "juniper")
    words = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india", "juliet"]
    steps = "\\n".join(words)
    part = re.search(r"created (a\d+)", do(f'do create {root} kind=note title="Sketch 2" text="{steps}"', "juniper")).group(1)
    talk = re.search(r"created (a\d+)", do(f"do create {root} kind=chat title=Talk", "juniper")).group(1)
    do("look", "pike")
    pikes = re.search(r"created (a\d+)", do(f"do create {root} kind=note title=Mine text=x", "pike")).group(1)
    do("look", "juniper")
    # one line replaced by someone else: the maker hears it, in its own line, and nothing is counted under !!
    do(f"read {part}", "pike")
    e1 = ev(do(f'do replace {part} old="hotel" new="HOTEL"', "pike"))
    got = head(do("look", "juniper"))
    assert got == [f'~ pike replaced line 8 of your {part} "Sketch 2" ({e1}; undo {e1})'], got
    # the editor is not the maker: they hear it as a change by someone, not as an edit to theirs
    do(f"read {part}", "juniper")
    do(f'do replace {part} old="bravo" new="BRAVO"', "juniper")
    got = head(do("look", "pike"))
    assert got and got[0].startswith("!!") and not any(l.startswith("~") for l in got), got
    # my own edits never show to me
    assert not head(do("look", "juniper")), "your own edit is not told back to you"
    # a chat line, a comment, an edit to someone else's note: nothing new for the maker in a ~ line
    do(f'do append {talk} line="hello"', "pike")
    do(f'do comment {part} line="nice"', "pike")
    do(f"read {pikes}", "pike")
    do(f'do replace {pikes} old="x" new="y"', "pike")
    got = head(do("look", "juniper"))
    assert got and got[0].startswith("!!") and not any(l.startswith("~") for l in got), got
    # an append and a retitle say what they did
    do(f"read {part}", "pike")
    e2 = ev(do(f'do append {part} line="kilo"', "pike"))
    got = head(do("look", "juniper"))
    assert got == [f'~ pike appended line 11 to your {part} "Sketch 2" ({e2}; undo {e2})'], got
    e3 = ev(do(f'do retitle {part} title="Sketch 2 · the test language"', "pike"))
    got = head(do("look", "juniper"))
    assert got == [f'~ pike retitled your {part} "Sketch 2 · the test language" (was "Sketch 2"; {e3}; undo {e3})'], got
    # ten quick edits fold into one line, with a count and the latest's undo
    ids = []
    for i in range(10):
        do(f"read {part}", "pike")
        old = words[i].upper() if i in (1, 7) else words[i]
        out = do(f'do replace {part} old="{old}" new="n{i + 1}."', "pike")
        assert out.startswith("ok"), out
        ids.append(ev(out))
    got = head(do("look", "juniper"))
    assert len(got) == 1 and got[0].startswith(f'~ pike edited your {part} "Sketch 2 · the test language" 10 times (replaced lines 1-10; '), got
    assert got[0].endswith(f"{ids[0]}..{ids[-1]}; undo {ids[-1]} takes back the latest)"), got
    assert do(f"undo {ids[-1]}", "juniper").startswith("ok"), "the maker can take back the latest"
    # an hour apart: two lines
    do(f"read {part}", "pike")
    a = ev(do(f'do replace {part} old="n1." new="t1"', "pike"))
    b = ev(do(f'do replace {part} old="n2." new="t2"', "pike"))
    for e in d.world.events:
        if e["id"] == a:
            e["at"] = "2026-10-01T08:00:00"
        if e["id"] == b:
            e["at"] = "2026-10-01T10:00:00"
    got = [l for l in head(do("look", "juniper")) if l.startswith("~")]
    assert len(got) == 2 and "line 1 " in got[0] and "line 2 " in got[1], got
    # a1595: help events (which shows this very line as its example) is a note in the world's Help binder now, and a
    # world built here has none; what help prints is the binder's to say, and health's to hold to the code


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


def test_marks_are_asked_for_and_stay_out_of_code():
    """Editor board a3486 (7 Oct): `marks` on a text part reads **strong**, *stressed* and [label](address) in its words.
    Without the word nothing changes; inside a code run a star is a star; a star beside a space is a star."""
    t = "a **bold** move, a *soft* one, [the log](https://x.y/z), `co*de*` and 2 * 3 * 4"
    assert [r.get("role") for r in scene.runs_of(t)] == [None, "code", None], scene.runs_of(t)
    rs = scene.runs_of(t, True)
    assert [(r["text"], r.get("mark") or r.get("role")) for r in rs if r.get("mark") or r.get("role")] == [
        ("bold", "strong"), ("soft", "stress"), ("the log", "link"), ("co*de*", "code")], rs
    assert rs[5]["href"] == "https://x.y/z" and rs[-1]["text"] == " and 2 * 3 * 4", rs
    assert "".join(r["text"] for r in scene.runs_of("x **a b** y", True)) == "x a b y"
    assert scene.runs_of("no marks here", True) is None
    n = {"text": t, "marks": True, "acts": [], "kids": []}
    scene.emit(n)
    assert n["paint"]["runs"] == rs and n["paint"]["marks"] is True and n["paint"]["text"] == t


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
            assert none.get("absent") and none["why"] == "$count > 0 is false ($count=0)", none
            assert lst["text"] == "1 of 2", lst["text"]
            assert lst["kids"][0]["text"].endswith("(2)") and lst["kids"][-1]["text"] == "all 2", [k["text"] for k in lst["kids"]]
            assert "· count 2 of kind:note" in scene.to_text(sc, "t", "jeff", 0)
            # Juniper, 7 Oct: a numbered item could not ask where it stands. $index is the place in the repeat, from 1,
            # in the instance and its kids; a clamp last keeps the true place; an expression can use it
            src = chr(10).join(["root : column", "  all : column, of kind:note, each c", "  end : column, of kind:note, clamp last 1, each c",
                                'c : column, text "$index of $count"', '  k : text "$index."', '  odd : text "odd", only when $index = 1'])
            sc = lens_ir.evaluate(desk, src)
            every, end = sc["kids"]
            assert [k["text"] for k in every["kids"]] == ["1 of 2", "2 of 2"], [k["text"] for k in every["kids"]]
            assert every["kids"][1]["kids"][0]["text"] == "2." and every["kids"][1]["kids"][1].get("absent"), every["kids"][1]["kids"]
            assert not every["kids"][0]["kids"][1].get("absent"), every["kids"][0]["kids"][1]
            assert [k["text"] for k in end["kids"] if k["part"] == "c"] == ["2 of 2"], [k["text"] for k in end["kids"]]
            # Juniper, the same hour: a let named above a nested repeat read none inside it; and a numbered item wants
            # its place in its own list. A let crosses into a repeat; `run <prop>` counts along like neighbours
            assert scene.run_places(["n", "n", None, "n", "b", "b", "b"]) == [1, 2, 1, 1, 1, 2, 3]
            w = desk.world
            for nid in [n["id"] for n in w.nodes.values() if n.get("subject")]:
                w.subjects[w.nodes[nid]["subject"]].setdefault("props", {})["block"] = "number"
            src = chr(10).join(["root : column", "  all : column, of kind:note, run block, each entry",
                                "entry : row", "  let place = $run", "  main : column, of $item, each para",
                                'para : text "$(place). of $index"'])
            sc = lens_ir.evaluate(desk, src)
            got = [e["kids"][0]["kids"][0]["text"] for e in sc["kids"][0]["kids"]]
            assert got == ["1. of 1", "2. of 1"], got
            assert "run block" in scene.to_text(sc, "t", "jeff", 0)
            refused("root : column, run block\n  c : text a", "counts along a repeat")
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


def test_scene_prints_painted_boxes_and_their_age():
    """a1473: a painter's report carries each part's box and the lens frame it painted; scene prints the box on the
    part's line, marks 0 high, and after an edit says the sizes are of the old lens until a painter reports again."""
    import deskd
    tmp = _scratch("_test_boxes")
    try:
        with deskd.Session("_test_boxes", "jeff") as desk:
            say = lambda line: (lambda r: r.get("text") or r.get("error"))(desk.dispatch("desk", {"line": line}))   # noqa: E731
            say("look")
            say('do create f01 kind=note tags=lens title=boxy text="root : column\\n  a : text \\"seen\\"\\n  z : row"')
            assert "no painted sizes" in say("scene boxy root"), "with no report, the part print says there are no sizes"
            sc, _ = scene.scene_for(desk, "boxy")

            def paint(boxes, sc=sc):          # what deskd's /api/observe keeps for a painter that reported
                desk._views = {"alex": {"lens": "boxy", "at": len(desk.world.events), "time": "2026-10-01T09:00:00", "viewport": None,
                                        "facts": {}, "boxes": boxes, "painted": {"frame": sc["def"]["frame"], "style": "seed"}}}
            paint({"root": "900x40", "root/a": "900x40", "root/z": "900x0"})
            out = say("scene boxy root")
            assert "sizes are of the lens as it stands" in out and "~ alex: 900x40px" in out, out
            assert "z row ~ alex: 900x0px (0 high: nothing visible)" in out, out
            assert "painted sizes, oldest first: alex " in say("scene boxy ok") and "(current)" in say("scene boxy ok")
            aid = desk.world.appearances_of([s for s in desk.world.subjects.values() if s["title"] == "boxy"][0]["id"])[0]
            say(f"read {aid} :3")
            say(f'do replace {aid} old="z : row" new="z : row\\n  b : text \\"more\\""')
            out = say("scene boxy root")
            assert "painted before your edit at e" in out and "! no viewer has painted this lens since your edit" in out, out
            assert "~ alex before the edit: not in the paint" in out, "a part the old paint did not have says so"
            assert "(before your edit at e" in say("scene boxy ok")
            paint({"root": "900x60 scroll sh=300", "root/a": "hidden", "root/z": "0x10", "root/b": "900x20 clip sh=80 cut=2/5"},
                  scene.scene_for(desk, "boxy")[0])
            out = say("scene boxy root")
            assert "as it stands" in out and "scrolls: contents 300 high" in out and "not drawn (folded or hidden)" in out, out
            assert "0x10px (0 wide: nothing visible)" in out and "clipped: contents 80 high, 2 of 5 parts cut off" in out, out
    finally:
        tmp.unlink(missing_ok=True)


STYLE_SAMPLES = [
    "token paper = #EEE\ntoken ink = #111\ntoken gap = 8\ntoken text = plex 14/1.5\ntoken line = ink at 70%\n"
    "role a : on paper, ink, text down 2, pad gap, pad top gap, corner 3, corner gap, lift 1, lift gap, edge line\n"
    "role b : on papr, inky, text.pixel, space below gap /2, between gap x2, width 30em, border left ink, text at 12\n"
    "role c : text medium, hide title, ink at 40%, glow, pulse, pulse down",
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
    import pathlib, health      # the same comparison health prints on its own line, with the world's styles too
    here = pathlib.Path(scene.__file__).resolve().parent
    srcs = [(f"sample {k + 1}", s) for k, s in enumerate(STYLE_SAMPLES)]
    srcs.append(("calm.style", (here / "desk-shell" / "style" / "calm.style").read_text(encoding="utf-8")))
    bad, note = health.style_mirror(srcs)
    assert not bad, bad
    if note:
        print("  (" + note + ")")
    bad = scene.style_check(STYLE_SAMPLES[0])["unread"]
    assert ("b", "on papr", 7,"names no token of the right kind") in bad


def test_let_if_and_arithmetic():
    """Alex, 5 Oct: if and arithmetic. `let` names a value from an expression; several lets of one name with `when` are
    an if; aggregates carry their reach; a missing value is none and a guard on it cannot tell; $( ) computes in words."""
    import deskd, lens_ir
    refused("root : column, let x = $a +", "expected a value")
    refused("root : column, let x = 1, let x = 2", "two answers")
    refused("root : column, let x = 1 when $a > 1, let x = 3 otherwise, let x = 4 otherwise", "two `otherwise`")
    refused("root : column, let title = 3", "that name is taken")
    refused("root : column, let n = 3", "that name is taken")
    tmp = _scratch("_test_let")
    try:
        with deskd.Session("_test_let", "jeff") as desk:            # the probe world: 'Probe' has beds=6, 'beds-lens' has none
            src = chr(10).join([
                "root : column, let total = sum($beds of kind:note), let num = count(kind:note), let avg = total / num",
                '  head : text "$num notes, $(total) beds, $(avg) each", only when total > 3',
                '  none : text "never", only when $nothing > 1',
                '  old : text "old path", only when $count > 0, count kind:note',
                "  list : column, of kind:note, each c",
                'c : row, let size = "big" when $beds > 5, let size = "small" when $beds <= 5, let size = "unsized" otherwise, let twice = $beds * 2',
                '  t : text "$title: $size ($(twice))"',
                '  big : text "a big one", only when size = "big"',
                '  both : text "x", let k = 1 when $beds > 1, let k = 2 when $beds > 2'])
            sc = lens_ir.evaluate(desk, src)
            d = {x["name"]: x for x in sc["derived"]}
            assert d["total"]["result"] == "6 · 1 of 2; 1 have none" and d["total"]["expr"] == "sum($beds of kind:note)", d["total"]
            assert d["num"]["result"] == "2" and d["avg"]["result"] == "3 · from 1 of 2", (d["num"], d["avg"])
            head, none, old, lst = sc["kids"]
            assert head["text"] == "2 notes, 6 (1 of 2) beds, 3 (from 1 of 2) each", head["text"]
            assert head["test"].startswith("total > 3 (") and head["computed"][0][0] == "total", head
            assert none["absent"] and none["why"] == "can't tell: no nothing ($nothing=none)", none
            assert old["text"] == "old path" and old["test"] == "$count > 0 ($count=2)", old            # the older spelling, the one print
            big, small = lst["kids"]
            assert big["kids"][0]["text"] == "Probe: big (12)" and not big["kids"][1].get("absent"), big["kids"]
            assert small["kids"][0]["text"] == "beds-lens: unsized (none)", small["kids"][0]
            assert small["kids"][1]["why"] == 'size = "big" is false (size=unsized)', small["kids"][1]
            sz = {x["name"]: x for x in small["derived"]}
            assert sz["size"]["expr"] == '"unsized" otherwise' and sz["twice"]["result"] == "none", sz
            both = {x["name"]: x for x in big["kids"][2]["derived"]}
            assert both["k"]["result"] == "1" and both["k"]["overlap"] == 2, both             # an overlap is taken first and said
            text = scene.to_text(sc, "t", "jeff", 0)
            assert "· total = 6 · 1 of 2; 1 have none (sum($beds of kind:note))" in text and "(overlap: 2 answers held; the first was taken)" in text, text
            assert "(absent: can't tell: no nothing ($nothing=none))" in text and '(absent: size = "big" is false (size=unsized))' in text, text
            # a guard that cannot tell is absence with the reason, never false
            sc2 = lens_ir.evaluate(desk, chr(10).join(["root : column, of kind:note, each c", 'c : text "$title", only when $beds * 2 > 5']))
            assert [k.get("why") for k in sc2["kids"]] == [None, "can't tell: no beds ($beds=none)"], [k.get("why") for k in sc2["kids"]]
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))      # the scratch sessions are named from the lab, wherever it is run from
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            n += 1
            print("ok", name)
    print(f"{n} passed")
