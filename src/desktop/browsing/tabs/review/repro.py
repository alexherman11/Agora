"""repro.py (a7544): defect reproductions on a staged DISPOSABLE copy, through its door only (no browser). Prints every
answer whole. Never the live world.

    python src/desktop/browsing/tabs/review/repro.py [deleted|bypass|order]
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
    got = {k: "" for k in keep}
    got.update({k: v for k, v in re.findall(r"(\w+)=(\S*)", line) if k in keep})
    return got


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


def batch(copy, who, line, observed=None):
    """a press's batch as the painter sends it: not whole, so ; splits it into commands (observed: the fence it was
    painted at, as the painter sends it)"""
    import json
    import urllib.request
    body = json.dumps({"session": copy.session, "as": who, "line": line, **({"observed": observed} if observed else {})}).encode()
    req = urllib.request.Request(f"{copy.base}/api/do", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    said = (("ERR " + out["error"] + "\n") if out.get("error") else "") + (out.get("text") or "")
    print(f"--- {who} (batch)> {line[:200]}\n{said.rstrip()}\n")
    return said


def notice(copy, vid):
    """a7761's notice press (do view <about>; do remove <notice>) after a shelve, then Back: is the notice removed, and
    where does Back go?"""
    out = copy.do("find prop:role=notice,prop:to=alex", ME)
    ids = re.findall(r"^\s+(a\d+) note ", out, re.M)
    print(f"notices to alex: {len(ids)}")
    n = ids[0]
    about = re.search(r"about=(\w+)", show(copy, ME, f"examine {n}")).group(1)
    show(copy, "alex", "do view a5202")
    show(copy, "alex", "do view f155")
    print("viewer:", viewer(copy))
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do unview {vid}")
    print("viewer after unview:", viewer(copy))
    show(copy, "alex", f"look {n}")
    batch(copy, "alex", f"do view {about}; do remove {n}")
    print("viewer after the press:", viewer(copy))
    print("notice after:", copy.do(f"examine {n}", ME).strip().splitlines()[:2])
    print("notices to alex now:", len(re.findall(r"^\s+(a\d+) note ", copy.do("find prop:role=notice,prop:to=alex", ME), re.M)))
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do browse {vid} action=back")
    print("viewer after Back (want f155):", viewer(copy))


def usage(copy, vid):
    """a7761's usage press (browse open target=<usage note> lens=plan-usage-reader; unshelve) after a shelve: what
    happens to the tabs?"""
    show(copy, "alex", "do view a5202")
    show(copy, "alex", "do view f155")
    print("viewer:", viewer(copy))
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do unview {vid}")
    print("viewer after unview:", viewer(copy))
    u = re.search(r"^\s+(a\d+) note ", copy.do("find prop:role=plan-usage", ME), re.M)
    target = u.group(1) if u else "a6866"
    show(copy, ME, f"examine {target}")
    show(copy, "alex", f"read {vid}")
    batch(copy, "alex", f"do browse {vid} action=open target={target} lens=plan-usage-reader; " + W.UNSHELF.replace("$me", "alex"))
    print("viewer after the press:", viewer(copy))
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do browse {vid} action=back")
    print("viewer after Back (want f155):", viewer(copy))
    plain = "do prop prop:role=home-panel,prop:actor=alex,prop:lens=home-viewer shelf=no"
    print("== the unshelve without its guard, the Viewer shelved:")
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do unview {vid}")
    show(copy, "alex", f"read {vid}")
    batch(copy, "alex", f"do browse {vid} action=open target={target} lens=plan-usage-reader; {plain}")
    print("panel:", copy.do("find prop:role=home-panel,prop:actor=alex,prop:lens=home-viewer", ME).strip().splitlines()[-2:])
    print("== the same, the Viewer already out:")
    show(copy, "alex", f"read {vid}")
    batch(copy, "alex", f"do browse {vid} action=open target=a5202 lens=home-feed; {plain}")
    print("viewer:", viewer(copy))


def helper(copy, vid):
    """c7956: JEFF's a7937 view-with-lens, on the copy with a7439/a7693/a7761 (its six lens routes through the verb):
    shelved and already-visible Viewer, same and different target and lens, Back, another actor, the draft, a stale
    press, and two things a world verb must refuse (a command in an argument, an unknown lens). -> rows"""
    rows = []

    def row(name, ok, said):
        rows.append((name, "PASS" if ok else "FAIL", said))
        print(f"== {'PASS' if ok else 'FAIL'} {name}: {said}\n", flush=True)

    panel = lambda: re.search(r"shelf=(\w+)", copy.do("find prop:role=home-panel,prop:actor=alex,prop:lens=home-viewer", ME)).group(1)  # noqa: E731
    draft = lambda: [l for l in copy.do("find prop:role=conversation-draft,prop:actor=alex", ME).splitlines() if " note " in l]  # noqa: E731
    d0 = draft()
    a, b = "a6866", "a6868"                       # two usage windows, as the usage lens opens them
    show(copy, "alex", "do view a5202")
    show(copy, "alex", "do view f155")
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do unview {vid}")
    v0 = viewer(copy)
    said = batch(copy, "alex", f"do view-with-lens {a} plan-usage-reader")
    v1 = viewer(copy)
    row("1 shelved Viewer: opens with the lens and comes out", v1["viewing"] == a and v1["with"] == "plan-usage-reader" and panel() == "no"
        and "ERR" not in said, f"{v0['viewing']!r} shelved -> {v1['viewing']} with {v1['with']}, shelf={panel()}")
    said = batch(copy, "alex", f"do view-with-lens {b} plan-usage-reader")
    v2 = viewer(copy)
    row("2 already visible, another target: no refusal, the guard skips", v2["viewing"] == b and "ERR" not in said and "refused" not in said.lower(),
        f"-> {v2['viewing']} with {v2['with']}, shelf={panel()}; receipt mentions skipped: {'skipped' in said}")
    said = batch(copy, "alex", f"do view-with-lens {b} plan-usage-reader")
    v3 = viewer(copy)
    row("3 same target, same lens again: nothing new, nothing refused", v3["viewing"] == b and "ERR" not in said,
        f"tab entries {v2.get('page_name')} -> {v3.get('page_name')}; can_back {v3['can_back']}; said: {said.strip().splitlines()[-1][:120] if said.strip() else ''}")
    said = batch(copy, "alex", f"do view-with-lens {b} home-feed")
    v4 = viewer(copy)
    show(copy, "alex", f"read {vid}")
    show(copy, "alex", f"do browse {vid} action=back")
    v5 = viewer(copy)
    row("4 same target, another lens: its own entry; Back gives the first lens", v4["with"] == "home-feed" and v5["viewing"] == b and v5["with"] == "plan-usage-reader",
        f"with {v4['with']}; after Back {v5['viewing']} with {v5['with']}")
    s0 = copy.do(f"find prop:role=home-view,prop:actor=alex", ME)
    said = batch(copy, "pike", f"do view-with-lens {a} home-feed")
    s1 = copy.do(f"find prop:role=home-view,prop:actor=alex", ME)
    row("5 another actor: acts on its own viewer, never alex's", s0 == s1, f"pike said: {said.strip().splitlines()[-1][:140] if said.strip() else ''}")
    said = batch(copy, "alex", f'do view-with-lens {a} "home-feed; do remove a5082"')
    alive = "not in the world" not in copy.do("examine a5082", ME)
    row("6 a command in an argument: never run", alive, f"a5082 still here: {alive}; said: {said.strip().splitlines()[-1][:140] if said.strip() else ''}")
    v6 = viewer(copy)
    said = batch(copy, "alex", f"do view-with-lens {a} no-such-lens")
    v7 = viewer(copy)
    row("7 an unknown lens: refused, the viewer as it was", "ERR" in said and v7 == v6, f"said: {said.strip().splitlines()[0][:160] if said.strip() else ''}")
    show(copy, ME, f"look {a}")
    show(copy, ME, f'do prop {a} usage_label="changed after it was painted"')
    v8 = viewer(copy)
    said = batch(copy, "alex", f"do view-with-lens {a} plan-usage-reader", observed={"item": a, "rev": 0})
    v9 = viewer(copy)
    row("8 a stale press (its row changed since it was painted): refused, nothing changed", "refused" in said.lower() and v9 == v8,
        f"said: {said.strip().splitlines()[0][:180] if said.strip() else ''}")
    row("9 the draft and its About: unchanged", draft() == d0, f"{d0} -> {draft()}")
    print("SUMMARY: " + "; ".join(f"{n.split(':')[0]} {r}" for n, r, _ in rows))
    return rows


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "deleted"
    copy = pt.Copy("frontier-try")
    try:
        if what == "order":
            return order(copy)
        log, _, _, vid = W.apply_copy(lambda who, line: copy.do(line, who))
        print("\n".join(log[-6:]))
        if what in ("notice", "usage"):
            print("\n".join(W.compose_jeff(lambda line: copy.do(line, ME))[-3:]))
        if what == "helper":
            body = W.helper_body(lambda line: copy.do(line, ME))
            print("a7937's verb, as composed:\n" + body)
            print("\n".join(W.compose_jeff(lambda line: copy.do(line, ME), helper=body)))
        {"deleted": deleted, "bypass": bypass, "notice": notice, "usage": usage, "helper": helper}[what](copy, vid)
    finally:
        copy.close()


if __name__ == "__main__":
    main()
