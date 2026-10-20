"""probe.py: run desk lines against frontier-try IN MEMORY and print the answers; nothing is saved (a6427).

    python research/window-lab/workspaces/probe.py <lines file> [--as who]

One line a request, as the door reads them. `!as <who>` on its own line changes who speaks from there on.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "home-layout"))
import put  # noqa: E402


def main():
    args = sys.argv[1:]
    who = args[args.index("--as") + 1] if "--as" in args else "worker-a6427"
    w = put.Try(who)
    for line in pathlib.Path(args[0]).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("!as "):
            w.d.world.me = line[4:].strip()
            continue
        print("> " + line)
        print(w.do(line))
        print()


if __name__ == "__main__":
    main()
