"""repro.py (a7544): defect reproductions on a staged DISPOSABLE copy, through its door only (no browser). Prints every
answer whole. Never the live world.

    python research/window-lab/browsing/tabs/review/repro.py [deleted|bypass|order]
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))
import hud_playtest as pt  # noqa: E402
import tabs_world as W  # noqa: E402

ME = "worker-a7544"


def show(copy, who, line):
    said = copy.do(line, who)
    print(f"--- {who}> {line[:200]}\n{said.rstrip()}\n")
    return said


def viewer(copy):
    line = W.viewer_line(lambda l: copy.do(l, ME))[0]
    keep = ("viewing", "with", "back", "active_tab", "tab_count", "can_back", "can_forward", "page_name")
    return {k: v for k, v in re.findall(r"(\w+)=(\S*)", line) if k in keep}


def deleted(copy, vid):
    """open a page, open another, remove the first, then Back (as the viewer's Back chip sends it)"""
    show(copy, ME, "look f5189")
    a = re.search(r"created (a\d+)", show(copy, ME, 'do create f5189 kind=note title="Doomed (synthetic)" text="x"')).group(1)
    b = re.search(r"created (a\d+)", show(copy, ME, 'do create f5189 kind=note title="Survivor (synthetic)" text="y"')).group(1)
    show(copy, "alex", f"do view {a}")
    show(copy, "alex", f"do view {b}")
    print("viewer:", viewer(copy))
    show(copy, ME, f"look {a}")
    show(copy, ME, f"do remove {a}")
    print("viewer after remove:", viewer(copy))
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do browse {vid} action=back")
    print("viewer after Back:", viewer(copy))
    show(copy, "alex", f"do browse {vid} action=reload")
    print("viewer after Reload:", viewer(copy))


def bypass(copy, vid):
    """the board card's own click line (home-board line 161), sent as alex, then the tabs' Back"""
    show(copy, "alex", "do view a5202")
    print("viewer:", viewer(copy))
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f'do prop {vid} viewing=f155 back="a5202" find=""')
    print("viewer after the card's line:", viewer(copy))
    print("tab notes:", copy.do(f"table prop:role=viewer-tab,prop:viewer={vid} cols=tab,active,closed", ME))
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do browse {vid} action=back")
    print("viewer after Back:", viewer(copy))
    print("find by a page's words:", copy.do('find title:lowdown', ME))


def order(copy):
    """home-viewer's six hunks with the 4th before the 3rd: does every step compile? (no init, nothing else)"""
    import json
    hs = json.loads((HERE.parent / "patches.json").read_text(encoding="utf-8"))["a5486"]
    copy.do("read a5486 :3", ME)
    for k in (0, 1, 3, 2, 4, 5):
        said = copy.do(f"do replace a5486 old={W.q(hs[k]['old'])} new={W.q(hs[k]['new'])}", ME)
        print(f"hunk {k + 1}: {said.strip().splitlines()[-1][:160]}")


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "deleted"
    copy = pt.Copy("frontier-try")
    try:
        if what == "order":
            return order(copy)
        log, _, _, vid = W.apply_copy(lambda who, line: copy.do(line, who))
        print("\n".join(log[-6:]))
        {"deleted": deleted, "bypass": bypass}[what](copy, vid)
    finally:
        copy.close()


if __name__ == "__main__":
    main()
