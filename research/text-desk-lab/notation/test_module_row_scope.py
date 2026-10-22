"""A newly registered source cannot steal an ordinary world property's reads."""

import re
from unittest.mock import patch

import explore
import lens_ir
import scene


def fixture():
    desk = explore.fresh()
    desk._session = "module-row-scope-memory"
    desk.dispatch("desk", dict(line="look " + desk.world.root))
    receipt = desk.dispatch(
        "desk",
        dict(line=f"do create {desk.world.root} kind=task title=Suite status=doing measurement=2"),
    )
    item = re.search(r"created (a\d+)", receipt["text"])[1]
    desk.dispatch("desk", dict(line="read " + item))
    changed = desk.dispatch("desk", dict(line=f"do prop {item} measurement=7"))["text"]
    event = re.search(r"\[(e\d+)\]", changed)[1]
    return desk, item, event


def test_source_registration_does_not_erase_world_freshness_or_own_gesture_fence():
    desk, item, event = fixture()
    with patch.object(scene, "SOURCE_FIELDS", (*scene.SOURCE_FIELDS, "measurement")):
        source = (
            "root : column, of kind:task, each t\n"
            't : text "$measurement / $changed.measurement", on click do check $item'
        )
        result = lens_ir.evaluate(desk, source)["kids"][0]
        assert result["text"].startswith("7 / " + event + " prop"), result["text"]
        assert any("prop:measurement" in r[2] for r in result["reads"])
        position, words = lens_ir.Accessor(desk).when_key(item, "changed.measurement")
        assert position is not None and not words.startswith("none")


def test_named_world_frame_keeps_property_fence_when_source_exports_same_word():
    desk, item, _ = fixture()
    with patch.object(scene, "SOURCE_FIELDS", (*scene.SOURCE_FIELDS, "measurement")):
        source = (
            f"root : column, the {item} as card\n"
            '  t : text "$card.measurement", on click do check $card.item'
        )
        result = lens_ir.evaluate(desk, source)["kids"][0]
        assert result["text"] == "7"
        assert any("prop:measurement" in r[2] for r in result["reads"])


def test_derived_row_fields_do_not_fabricate_world_property_reads():
    desk, item, _ = fixture()
    subject = desk.world.subject_of(item)

    def rows(*args):
        return [dict(item=item, id=subject, measurement=99)]

    with (
        patch.dict(scene.SOURCES, module_scope=("module_scope", ("item", "id", "measurement"))),
        patch.dict(scene.SOURCE_FILES, module_scope=dict(arg="none", open=False, rows=rows)),
        patch.object(scene, "SOURCE_FIELDS", (*scene.SOURCE_FIELDS, "measurement")),
    ):
        source = (
            "root : column, of module_scope as row, each t\n"
            't : text "$measurement / $row.measurement", on click do check $row.item'
        )
        result = lens_ir.evaluate(desk, source)["kids"][0]
        assert result["text"] == "99 / 99"
        assert not any("prop:measurement" in r[2] for r in result["reads"])


def test_aggregate_member_reads_remain_world_reads_with_colliding_source_vocabulary():
    desk, _, _ = fixture()
    with patch.object(scene, "SOURCE_FIELDS", (*scene.SOURCE_FIELDS, "measurement")):
        source = (
            "root : column\n"
            "  let total = sum($measurement of kind:task)\n"
            '  t : text "$total", on click do create f01 kind=note title="$total"'
        )
        result = lens_ir.evaluate(desk, source)["kids"][0]
        assert result["text"] == "7"
        assert any("prop:measurement" in r[2] for r in result["reads"])
