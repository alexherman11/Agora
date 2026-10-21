"""read_profiles (a6153): the scene builds a deskd profiled (DESKD_PROFILE_SCENES=<dir>), summed, and where they went.

    python research/window-lab/press-speed/read_profiles.py <dir> [--top 40] [--sort tottime|cumulative] [--skip 1]

--skip N leaves out the first N builds (the cold one). Prints each build's total and the top functions over the rest.
"""
import pstats
import sys
from pathlib import Path


def main(argv):
    d = Path(argv[0])
    opt = lambda k, v: argv[argv.index(k) + 1] if k in argv else v      # noqa: E731
    files = sorted(d.glob("scene-*.prof"))[int(opt("--skip", "1")):]
    if not files:
        return print("no profiles")
    st = None
    for f in files:
        one = pstats.Stats(str(f))
        print(f"{f.name}: {one.total_tt * 1000:.0f} ms (profiled)")
        st = one if st is None else st.add(str(f))
    print(f"{len(files)} builds")
    st.sort_stats(opt("--sort", "cumulative")).print_stats(int(opt("--top", "40")))


if __name__ == "__main__":
    main(sys.argv[1:])
