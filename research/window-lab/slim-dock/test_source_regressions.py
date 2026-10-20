"""Run existing scene regressions that do not need temporary world/report files."""
import pathlib
import sys

LAB = pathlib.Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
import test_scene

SKIP = {"test_rooms_go_look_and_replay", "test_scene_prints_painted_boxes_and_their_age"}
ran = 0
for name, fn in vars(test_scene).items():
    if name.startswith("test_") and callable(fn) and name not in SKIP:
        fn()
        ran += 1
print(f"{ran} existing scene regressions passed; {len(SKIP)} filesystem-dependent checks excluded")
