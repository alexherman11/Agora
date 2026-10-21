"""apply: the app dev workspace's phone preview and its sample app into a world (worker-a6431, 20 Oct; commission a6431).

    python research/window-lab/app-dev/apply.py try [--for alex,worker-a6431]   into frontier-try (a copy), in process
    python research/window-lab/app-dev/apply.py lines <file.desk>                each line into the copy, refusals stopping nothing
    python research/window-lab/app-dev/apply.py check                        what it would do live; sends nothing
    python research/window-lab/app-dev/apply.py door [--for alex]               live, through the door (not run by a6431:
                                                                                 the commission was sandbox only)
What it writes, each skipped when it already stands as written:
  1. home-style gains the preview's roles (app-preview.style-roles), one line each, appended or replaced (LAMPLIT's rule)
  2. harbour-style (the sample app's own look), then the lenses harbour-app, app-preview, app-preview-small
  3. in Home base, the surface App studio: Devices (iPhone 15, Small Android, iPad: role=app-device, sizes and insets,
     an icon as text), the preview's three tool icons (role=apicon), Harbour places (twelve role=harbour-place notes)
  4. for each person named by --for: their Harbour view (role=harbour-view) and their phone preview (role=app-preview
     app=harbour-app device=iPhone 15 turn=portrait safe=on inspect=off)
It places no panel: the workspaces verb (a6427) puts app-preview in the middle of the app dev layout.
"""
import json
import pathlib
import re
import sys
import urllib.request
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = pathlib.Path(__file__).resolve().parent
NOTATION = HERE.parents[1] / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))
sys.path.insert(0, str(HERE))
import data  # noqa: E402

ROOM, ME = "f5204", "worker-a6431"


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


class Try:
    def __init__(self):
        import explore
        self.explore, self.path = explore, NOTATION / "sessions" / "frontier-try.pickle"
        self.d = explore.load_desk(self.path)
        self.d.world.me = ME

    def do(self, line):
        r = self.d.dispatch("desk", {"line": line, "reply": "put"})
        return r.get("text") or "ERR " + str(r.get("error"))

    def save(self):
        self.explore.save_desk(self.path, self.d)


class Live:
    writes = True

    def do(self, line):
        body = json.dumps({"session": "frontier", "as": ME, "line": line, "whole": True}).encode()
        req = urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, headers={"Content-Type": "application/json"})
        out = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return out.get("text") or "ERR " + str(out.get("error"))

    def save(self):
        pass


class Check(Live):
    """Reads go to the door; writes are printed, never sent."""
    def do(self, line):
        if line.startswith("do "):
            print("  would send:", line[:150])
            return "ok (not sent) → created a0"
        return super().do(line)


def body(text):
    return text.split("\n---\n", 1)[1].rsplit("\n---", 1)[0] if "\n---\n" in text else ""


def created(out):
    m = re.search(r"→ created ([afs]\d+)", out)
    return m.group(1) if m else None


def find_one(w, sel):
    m = re.search(r"^\s+([afs]\d+) (?:note|surface)", w.do(f"find {sel}"), re.M)
    return m.group(1) if m else None


def run(w, who):
    said, bad = [], 0

    def act(line):
        nonlocal bad
        out = w.do(line)
        if re.search(r"^(ERR|!! refused|.*does not compile)", out, re.M) or "refused" in out.split("\n", 1)[0]:
            bad += 1
            print(f"!! {line[:140]}\n   {out.strip()[:500]}")
        return out

    w.do(f"look {ROOM}")
    # 1. home-style's roles
    sid = find_one(w, f"title:home-style,in:{ROOM}")
    if not sid:
        print("ERR no home-style in Home base")
        return 1
    style = body(w.do(f"read {sid} :3"))
    have = {m.group(1): l.rstrip() for l in style.splitlines() for m in [re.match(r"role (\S+) :", l)] if m}
    n_add = n_rep = 0
    for l in (HERE / "app-preview.style-roles").read_text(encoding="utf-8").splitlines():
        m = re.match(r"role (\S+) :", l)
        if not m or have.get(m.group(1)) == l.rstrip():
            continue
        w.do(f"read {sid} :3")
        if m.group(1) in have:
            act(f"do replace {sid} old={q(have[m.group(1)])} new={q(l.rstrip())}"); n_rep += 1
        else:
            act(f"do append {sid} line={q(l.rstrip())}"); n_add += 1
    said.append(f"home-style: {n_add} roles appended, {n_rep} replaced")

    # 2. the sample app's style, then the lenses
    def note(title, text, extra):
        nid = find_one(w, f"title:{title},in:{ROOM}")
        if nid:
            if body(w.do(f"read {nid} :3")).strip() == text.strip():
                return f"{title}: as written"
            act(f"do rewrite {nid} text={q(text)}")
            return f"{title}: rewritten"
        w.do(f"look {ROOM}")
        act(f"do create {ROOM} kind=note title={q(title)} {extra} text={q(text)}")
        return f"{title}: made"
    said.append(note("harbour-style", (HERE / "harbour.style").read_text(encoding="utf-8").rstrip("\n"), "tags=style"))
    for name, style_name in (("harbour-app", "harbour-style"), ("app-preview", "home-style"), ("app-preview-small", "home-style")):
        said.append(note(name, (HERE / f"{name}.lens").read_text(encoding="utf-8").rstrip("\n"), f"tags=lens style={style_name}"))

    # 3. App studio and what it holds
    def surface(title, role, inside, layout):          # found by role: a title with spaces is no selection term
        sid_ = find_one(w, f"kind:surface,prop:role={role}")
        if sid_:
            return sid_
        w.do(f"look {inside}")
        sid_ = created(act(f"do create {inside} kind=surface title={q(title)} layout={layout}"))
        w.do(f"look {sid_}")
        act(f"do prop {sid_} role={role}")
        return sid_
    studio = surface("App studio", "app-studio", ROOM, "column")
    devices = surface("Devices", "app-devices", studio, "row")
    places = surface("Harbour places", "harbour-places", studio, "column")

    def thing(inside, title, props, text, sel):
        tid = find_one(w, sel)
        if tid:
            return tid
        w.do(f"look {inside}")
        p = " ".join(f"{k}={q(v)}" for k, v in props.items())
        return created(act(f"do create {inside} kind=note title={q(title)} {p}" + (f" text={q(text)}" if text else "")))
    ids = {}
    for title, props, svg in data.DEVICES:
        ids[title] = thing(devices, title, dict(role="app-device", **props), svg, f"prop:role=app-device,prop:order={props['order']}")
    for title, icon, svg in data.ICONS:
        thing(studio, title, dict(role="apicon", icon=icon), svg, f"prop:role=apicon,prop:icon={icon}")
    for i, (title, area, hours, rating, text) in enumerate(data.PLACES, 1):
        thing(places, title, dict(role="harbour-place", order=i, area=area, hours=hours, rating=rating), text,
              f"prop:role=harbour-place,prop:order={i}")
    said.append(f"App studio {studio}: {len(data.DEVICES)} devices, {len(data.ICONS)} icons, {len(data.PLACES)} places")

    # 4. each person's records
    for p in who:
        thing(studio, f"{p}'s Harbour view", dict(role="harbour-view", actor=p), "", f"prop:role=harbour-view,prop:actor={p}")
        thing(studio, f"{p}'s phone preview", dict(role="app-preview", actor=p, app="harbour-app", device=ids["iPhone 15"],
                                                   turn="portrait", safe="on", inspect="off"), "",
              f"prop:role=app-preview,prop:actor={p}")
    said.append("records for " + ", ".join(who))
    w.save()
    print("\n".join(said))
    print(f"{bad} refused")
    return 1 if bad else 0


def lines_try(path):
    """Each line of a .desk file into the COPY on its own, so one refusal (a prop already so) stops nothing else."""
    w = Try()
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            print(f"> {line[:100]}\n  {w.do(line).strip().splitlines()[0][:160]}")
    w.save()
    return 0


def main(a):
    if a[:1] == ["lines"] and len(a) > 1:
        return lines_try(a[1])
    if not a or a[0] not in ("try", "check", "door"):
        print(__doc__)
        return 2
    who = a[a.index("--for") + 1].split(",") if "--for" in a else ["alex"]
    w = {"try": Try, "check": Check, "door": Live}[a[0]]()
    return run(w, who)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
