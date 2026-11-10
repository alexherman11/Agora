"""Guarded, throwaway-world review; no live mode and no arbitrary extra input.

screen.py owns copying/cleanup. Its --visible path uses a separate guarded
desktop. This entry point never starts hud.py, uses host verbs, or sends chat.
"""
import argparse
import pathlib
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "text-desk" / "notation"))
import screen
import world_patch


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world", default="frontier-try")
    p.add_argument("--small", action="store_true")
    a = p.parse_args()
    # A world name only, no path/live URL; screen creates its own copy.
    if not a.world.replace("-", "").replace("_", "").isalnum():
        p.error("world must be a local world name")
    steps = []
    for line in world_patch.commands():
        steps += ["desk", line]
    steps += ["facts", "home/dock", "5", "shot", str(HERE / ("screen-dock-small.png" if a.small else "screen-dock.png"))]
    sys.argv = ["screen.py", a.world, "--as", "alex", "--lens", "home-base",
                "--visible", "--size", "1280x800" if a.small else "2560x1440", *steps]
    screen.main()


if __name__ == "__main__":
    main()
