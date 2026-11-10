"""Authored opt-in reaches the painter; absent options preserve the old spec."""
import scene
import explore
import lens_ir


def test_partition_magnetic_is_explicit_and_roundtrips():
    base = "root : column\n  partition tree min 240 140 gap 16 focus full"
    _, parts = scene.parse(base)
    assert parts["root"]["partition"] == dict(
        prop="tree", minimum=[240, 140], gap=16, focus_prop="full")
    root, parts = scene.parse(base + " magnetic")
    assert parts["root"]["partition"]["magnetic"] is True
    assert scene.emit(parts[root])["paint"]["partition"]["magnetic"] is True


def test_partition_magnetic_refuses_ambiguous_values():
    for suffix in ("magnetic off", "magnetic true", "magnetic magnetic", "magnetic focus full"):
        try:
            scene.parse("root : column\n  partition tree min 240 140 gap 16 " + suffix)
        except scene.LensRefusal:
            pass
        else:
            raise AssertionError(suffix)


def test_partition_magnetic_evaluation_preserves_fences_and_zero_events():
    desk = explore.fresh()
    root = desk.world.root
    src = f"root : column, the {root} as lay\n  partition tree min 240 140 gap 16 focus full"
    before = len(desk.world.events)
    old = scene.painter_view(scene.emit(lens_ir.evaluate(desk, src)))
    new = scene.painter_view(scene.emit(lens_ir.evaluate(desk, src + " magnetic")))
    assert new["paint"]["partition"].pop("magnetic") is True
    # Different authored definitions must keep distinct stale-action fences.
    old_hash = old["fence"]["defpart"].pop("hash")
    new_hash = new["fence"]["defpart"].pop("hash")
    assert old_hash != new_hash
    assert new == old
    assert len(desk.world.events) == before
