"""Comment composition, reply identity and source-bound image presentation."""

import hashlib

import image_comments
import lens_ir
import roomworld
import scene


def test_explicit_commit_survives_compilation():
    desk, _ = roomworld.build()
    src = 'root : text "", hint "reply", commit explicit, on edit do comment a1 line="$value"'
    sc = lens_ir.evaluate(desk, src)
    scene.emit(sc)
    assert scene.painter_view(sc)["paint"]["commit"] == "explicit"
    try:
        scene.parse("root : column, commit explicit")
    except scene.LensRefusal as e:
        assert "text" in str(e)
    else:
        raise AssertionError("frame admitted a text-only commit policy")


def test_replies_are_separate_stable_rows_even_for_one_author():
    desk, rooms = roomworld.build()
    aid = rooms.NOTE
    subject = desk.world.subjects[desk.world.nodes[aid]["subject"]]
    subject["comments"] = [
        dict(
            id="c1",
            by="alex",
            text="Question",
            resolved=False,
            replies=[
                dict(by="alex", text="First\nwith a second line"),
                dict(by="alex", text="Another message"),
            ],
        )
    ]
    src = f"""root : column, of comments:{aid} as c, each comment
comment : column
  thread : column, of replies:$item, each reply
reply : text "$by: $text", only when $thread = $c.cid"""
    sc = lens_ir.evaluate(desk, src)
    leaves = [n for n in scene._walk(sc) if n.get("part") == "reply"]
    assert [n["text"] for n in leaves] == [
        "alex: First\nwith a second line",
        "alex: Another message",
    ]
    keys = [n["key"] for n in leaves]
    assert len(set(keys)) == 2
    subject["comments"][0]["replies"].append(dict(by="rowan", text="Third"))
    assert [n["key"] for n in scene._walk(lens_ir.evaluate(desk, src)) if n.get("part") == "reply"][
        :2
    ] == keys


def test_regions_only_overlay_the_original_current_picture():
    desk, rooms = roomworld.build()
    aid = rooms.NOTE
    subject = desk.world.subjects[desk.world.nodes[aid]["subject"]]
    subject["text"] = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    subject["comments"] = [
        dict(
            id="c1",
            by="alex",
            text="Here",
            resolved=False,
            image=dict(
                source_hash=hashlib.sha256(subject["text"].encode()).hexdigest(),
                rect=[0.1, 0.2, 0.3, 0.4],
                data_url="saved crop",
            ),
        )
    ]
    src = f'root : text "$text", the {aid}, picture'
    sc = lens_ir.evaluate(desk, src)
    scene.emit(sc)
    assert scene.painter_view(sc)["paint"]["regions"][0]["current"]
    subject["text"] += " "
    sc = lens_ir.evaluate(desk, src)
    scene.emit(sc)
    assert not scene.painter_view(sc)["paint"]["regions"][0]["current"]
    crop = lens_ir.evaluate(desk, f'root : text "saved crop", the {aid}, picture')
    assert not crop.get("image_regions")
    subject["comments"][0]["resolved"] = True
    assert image_comments.regions(subject) == []
