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
