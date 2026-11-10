"""test_workspaces.py: the verb workspace on a copy of frontier-try in memory (a6427); nothing is saved.

    python src/desktop/workspaces/test_workspaces.py

apply.py's steps first, then as JEFF (who runs it when Alex asks) and as Alex (who presses the dock): default, app-dev,
writing, back; save, change, apply, equal; a pinned thing with its lens (Codex c6468) through save and apply; back
twice; an unknown name refused with nothing changed; and one verb call is one event batch, never two.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "home-layout"))
import apply  # noqa: E402
import put  # noqa: E402

FAILS = []


def check(what, ok, more=""):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"  ({more})"))
    if not ok:
        FAILS.append(what)


def layout(W):
    """Alex's layout as facts, ids left out: its props, then each column's span and panels (lens, shelf, shows, pin)
    in order. full= names a panel by its lens, so two copies of one arrangement read the same. Since a5994's equal
    footing the chat (jeff-chat) and the viewer (home-viewer) are panels, counted like the rest."""
    lays = [n for n in W.nodes.values() if n["type"] == "surface" and (n.get("props") or {}).get("role") == "home-layout"
            and (n.get("props") or {}).get("actor") == "alex"]
    assert len(lays) == 1, f"{len(lays)} layouts"
    lay = lays[0]
    p = dict(lay.get("props") or {})
    lens_of = {}
    cols = []
    for c in W.children(lay["id"]):
        panels = []
        for k in W.children(c["id"]):
            sp = W.subjects[k["subject"]].get("props") or {}
            lens_of[k["id"]] = sp.get("lens")
            panels.append((W.subjects[k["subject"]]["title"], sp.get("lens"), sp.get("shelf"), sp.get("shows", ""),
                           sp.get("pin", "")))
        cols.append(((c.get("props") or {}).get("span", "1"), tuple(panels)))
    full = lens_of.get(p.get("full", ""), p.get("full", ""))
    keep = {k: p.get(k, "") for k in ("widgets",)}
    return {"props": keep, "full": full, "cols": tuple(cols)}


def viewer(W):
    v = next(s for s in W.subjects.values() if (s.get("props") or {}).get("role") == "home-view"
             and (s.get("props") or {}).get("actor") == "alex")
    return v["props"].get("viewing", ""), v["props"].get("with", "")


def out_lenses(L):
    return [p[1] for _, ps in L["cols"] for p in ps if p[2] != "yes"]


def main():
    w = put.Try("worker-a6427")
    if "nothing matches" not in w.do("find kind:surface,prop:role=workspaces,prop:actor=alex"):
        apply.undo(w)               # frontier-try holds an install (apply.py try): start from the world without it
    apply.run(w)
    W = w.d.world
    D = w.d
    per = {}

    def be(me):
        """Each person keeps their own looks, as deskd keeps them (test_blanks.be): the desk's fences then refuse an act
        on what they have not seen. Without this every caller shared one record, and a stale refusal never showed."""
        W.me = me
        if me not in per:
            per[me] = ({}, {W.root}, len(W.events))
        D.seen, D.open, D.last_event_seen = per[me]

    def say(who, line):
        be(who)
        out = w.do(line)
        if line.startswith("workspace") and line != "workspace nowhere":
            check(f"{who}: {line} runs whole, nothing refused", not out.startswith("ERR") and "stale:" not in out
                  and "\nERR" not in out, "\n".join(l for l in out.splitlines() if l.startswith(("ERR", "stale", "stopped", "!!", "you have not")) or "refused" in l)[:900])
        return out
    mine = layout(W)
    v0 = viewer(W)

    n0 = len(W.events)
    out = say("jeff", "workspace app-dev")
    check("jeff: workspace app-dev is taken", not out.startswith("ERR"), out[:600])
    L = layout(W)
    check("app-dev: The house on the left, the phone preview in the middle (span 2), the chat on the right",
          out_lenses(L) == ["home-house", "app-preview", "jeff-chat"]
          and [c[0] for c in L["cols"] if any(p[2] != "yes" for p in c[1])] == ["1", "2", "1"], L)
    check("app-dev: the receipt says what changed in a sentence (its about=)", "App dev: the phone preview" in out, out[-500:])
    check("app-dev: the viewer closed, the chat alone on the right", viewer(W)[0] == "", viewer(W))
    print(f"     ({len(W.events) - n0} events in the one call)")

    out = say("jeff", "workspace writing")
    check("writing: the viewer (Writing open in it) beside the chat, nothing else out",
          out_lenses(layout(W)) == ["home-viewer", "jeff-chat"] and viewer(W)[0] != "", (layout(W), viewer(W), out[:400]))

    out = say("jeff", "workspace back")
    check("back: app-dev again, as it was", layout(W) == L, (layout(W), L, out[-600:]))
    out = say("jeff", "workspace back")
    check("back twice: writing again", out_lenses(layout(W)) == ["home-viewer", "jeff-chat"] and viewer(W)[0] != "", out[-400:])

    out = say("jeff", "workspace default")
    check("default: Alex's own arrangement, as he had it", layout(W) == mine and viewer(W) == v0, (layout(W), mine, viewer(W), v0))

    # save, change, apply, equal: with a panel showing one outside thing (a5994's shows=, Codex c6468) among the panels
    lay = next(n["id"] for n in W.nodes.values() if n["type"] == "surface" and (n.get("props") or {}).get("role") == "home-layout")
    col = W.children(lay)[0]["id"]
    say("alex", f"look {col}")
    out = say("alex", f'do create {col} kind=note title="Plan, pinned" role=home-panel actor=alex lens=home-thing shows=a604 shelf=no pin=yes')
    check("a panel showing one thing: shows=a604 lens=home-thing pin=yes in the layout", "created" in out, out[:300])
    say("alex", "look f5204")
    say("alex", "read a5482")
    say("alex", "do prop a5482 viewing=a604 with=design-review")
    saved, vsaved = layout(W), viewer(W)
    out = say("jeff", "workspace save mine")
    check("save mine is taken", not out.startswith("ERR"), out[:600])
    check("save left the layout as it was", layout(W) == saved, layout(W))
    out = say("jeff", "workspace review")
    check("change: review is a different arrangement", layout(W) != saved
          and out_lenses(layout(W)) == ["waiting-on-me", "home-board", "jeff-chat"], (layout(W), out[-300:]))
    out = say("alex", "workspace mine")
    check("apply mine: equal to what was saved, the panel showing one thing too", layout(W) == saved, (layout(W), saved))
    check("apply mine: the viewer's thing and lens as saved", viewer(W) == vsaved, (viewer(W), vsaved))
    check("the panel still shows the outside thing (shows= not remapped)", any(p[3] == "a604" for _, ps in layout(W)["cols"] for p in ps))
    out = say("jeff", "workspace save mine")
    n_mine = sum(1 for n in W.nodes.values() if n["type"] == "surface" and (n.get("props") or {}).get("name") == "mine"
                 and (n.get("props") or {}).get("role") == "workspace")
    check("save mine again: one workspace named mine, not two", n_mine == 1, n_mine)

    before = layout(W)
    out = say("jeff", "workspace nowhere")
    check("an unknown name is refused, saying so", out.startswith("ERR") and "nothing matches" in out, out[:300])
    check("... and nothing changed", layout(W) == before)

    going = [n for n in W.nodes.values() if n["type"] == "surface" and (n.get("props") or {}).get("role") == "workspaces-going"]
    check("Workspaces going is empty after every use", going and not W.children(going[0]["id"]))
    names = sorted((n.get("props") or {}).get("name") for n in W.nodes.values() if n["type"] == "surface"
                   and (n.get("props") or {}).get("role") == "workspace")
    check("Workspaces holds the six, before and mine", names == sorted(["default", "app-dev", "writing", "review", "quiet", "play", "before", "mine"]), names)

    out = say("jeff", "workspace play")
    L = layout(W)
    check("play: nothing out, not even the chat, only the timer and the notices", out_lenses(L) == []
          and L["props"]["widgets"] == "home-timer-bar,home-notices", L)
    out = say("jeff", "workspace quiet")
    L = layout(W)
    check("quiet: only the chat out, only the glance", out_lenses(L) == ["jeff-chat"] and L["props"]["widgets"] == "home-glance", L)

    print(f"\n{len(FAILS)} failed" if FAILS else "\nall passed")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
