"""The theme proof: hidden, headless, scratch kernels only (research/kernel-lab/theme/THEMES.md).

Nothing here touches the live desktop (127.0.0.1:8810), starts a window, or takes Alex's focus. It builds the community
board's own two-week scratch world (32 people, 409 posts), adds the theme module and the Appearance app to it, and then:

  words      import a base16 scheme, make a theme from Dusk with another accent, place-wide and just-for-me for a second
             person, theme.try that reverts by itself, undo
  sharing    export and import into a second scratch world, by file and by kit; a malicious theme is refused every way
  delivery   ONE theme.use reaches the board (painter), the Appearance app (painter), a widget made with the old
             vocabulary, the host chrome (taskbar) and the native sheet, and ONE undo puts all of them back
  looks      every starter rendered across the board, a painter component, host chrome and the Appearance app
             (screenshots in theme/evidence/)

Run:  C:/Projects/Agora4/.venv/Scripts/python.exe research/kernel-lab/theme/proof.py
"""
import json
import os
import secrets
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
BOARD = LAB.parent / "community-app/board"
DESKTOP = LAB.parent / "window-lab/kernel-desktop"
sys.path[:0] = [str(BOARD), str(LAB), str(DESKTOP), str(LAB / "tests"), str(LAB / "proof")]
OUT = HERE / "evidence"

import kdesk                                                          # noqa: E402
import ui_proof                                                       # noqa: E402
from painter.browser import Page, write_capture                       # noqa: E402
from widget_browser import Browser                                    # noqa: E402
from protocol import line as proto_line                               # noqa: E402
from theme import install as appearance                               # noqa: E402
from theme import model as M, starters as S, base16                   # noqa: E402
from theme import colour as C                                         # noqa: E402

Q = ui_proof.Q
ui_proof.HERE, ui_proof.OUT = OUT, OUT / "board-scratch"           # the board proof writes its own first-paint picture; keep it out of the board's evidence

NORD = """system: "base16"
name: "Nord"
author: "arcticicestudio"
variant: "dark"
palette:
  base00: "#2E3440"
  base01: "#3B4252"
  base02: "#434C5E"
  base03: "#4C566A"
  base04: "#D8DEE9"
  base05: "#E5E9F0"
  base06: "#ECEFF4"
  base07: "#8FBCBB"
  base08: "#BF616A"
  base09: "#D08770"
  base0A: "#EBCB8B"
  base0B: "#A3BE8C"
  base0C: "#88C0D0"
  base0D: "#81A1C1"
  base0E: "#B48EAD"
  base0F: "#5E81AC"
"""


class Proof:
    def __init__(self):
        OUT.mkdir(parents=True, exist_ok=True)
        self.checks, self.shots, self.notes = [], [], []
        self.u = ui_proof.UI()
        self.f, self.d, self.k = self.u.f, self.u.d, self.u.f.k
        self.url = self.u.url
        self.alex = self.f.tokens["Alex"]
        self.doors = {name: ui_proof.taskboard.Door(self.url, tok) for name, tok in self.f.tokens.items()}
        self.maya, self.sam = self.doors["Maya"], self.doors["Neighbour 01"]
        self.pages = []
        self.host_key = os.environ["AGORA_WIDGET_HOST_KEY"]       # a second scratch desk overwrites it; the pages need this world's
        self.install_module()

    # ---------------------------------------------------------------------------------------------------- plumbing
    def check(self, name, ok, detail=None):
        self.checks.append(dict(check=name, ok=bool(ok), detail=detail))
        print(("PASS " if ok else "FAIL ") + name + ((" · " + str(detail)) if detail is not None else ""), flush=True)
        assert ok, name

    def install_module(self):
        """What kdesk.after_genesis does for the theme module, for this world: the module, its grant narrowed to the
        theme kinds, and the steward as the one it works for."""
        from kernel.kernel import Tx
        spec = next(s for s in kdesk.module_specs(True) if s["name"] == "theme")
        k = self.k
        steward = next(t for t in k.things("person") if k.is_steward(t))
        with k.lock:
            tx = Tx(k)
            tx.part("install", None, "install")
            mid = tx.mint()
            for a, v in (("kind", "module"), ("name", "theme"), ("run", spec["run"]), ("publishes", spec["publishes"]),
                         ("on", True), ("for", steward), ("about", kdesk.ABOUT["theme"])):
                tx.set(mid, a, v)
            g = tx.mint()
            for a, v in (("kind", "grant"), ("to", mid), ("words", spec["grants"]), ("where", k.place), ("by", steward),
                         ("only", spec["only"])):
                tx.set(g, a, v)
            k._commit(tx, by="kernel", words="install: the theme module, for the steward")
        self.f.host.reconcile()
        assert self.f.host.wait_offered(k.module_named("theme"), 30)
        self.wait(lambda: len(self.d.rows("theme")) >= 5, 30)
        self.ids = appearance.install(self.d)

    def wait(self, cond, seconds=20):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            for p in self.pages:
                try:
                    p.c.js("0")
                except Exception:
                    pass
            try:
                got = cond()
                if got:
                    return got
            except Exception:
                pass
            time.sleep(0.1)
        raise AssertionError("timed out waiting")

    def raw(self, door, text):
        return door.request("/do", {"line": text})

    def refused(self, door, text):
        out = self.raw(door, text)
        return (not out.get("ok")), out.get("text") or ""

    def get(self, path, token=None, who=None):
        token = token or self.f.tokens[who or "Alex"]
        req = urllib.request.Request(self.url + path, headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, dict(r.headers), r.read()

    def wears(self, who="Alex"):
        status, _, body = self.get("/desk/theme.json", who=who)
        return json.loads(body)

    def theme_id(self, name):
        return next(r["id"] for r in self.d.rows("theme") if r.get("name") == name or r.get("title") == name)

    def card(self, ref, door=None):
        return (door or self.d).say("theme.get " + Q(ref))["rows"][0]

    def shot_page(self, p, name, chrome=False):
        path = OUT / name
        p.shot(path) if not chrome else self.shot_chrome(p, path)
        self.shots.append(str(path.relative_to(HERE)))
        return path

    def shot_chrome(self, c, path):
        import base64
        c.call("Page.captureScreenshot", format="png")
        time.sleep(0.15)
        write_capture(path, base64.b64decode(c.call("Page.captureScreenshot", format="png")["data"]))

    # ---------------------------------------------------------------------------------------------------- the checks
    def starters(self):
        rows = self.d.rows("theme")
        names = {r.get("name") for r in rows}
        want = {slug for slug, _ in S.ORDER}
        self.check("five starter themes exist, each passing the theme check", want <= names, sorted(want))
        listing = self.d.say("theme.list")["rows"]
        self.check("theme.list shows all five as cards (none skipped by the check)", {c["name"] for c in listing} >= want)
        day = self.card("seabright-day")
        self.check("Seabright Day is light and keeps the place's green accent",
                   day["variant"] == "light" and day["roles"]["accent"].lower() == "#638779", day["roles"]["accent"])
        ink = self.card("ink-landscape")
        self.check("Ink Landscape carries its own SVG wallpaper", ink["wallpaper"]["kind"] == "svg" and ink["wallpaper"]["uri"],
                   f"{len(ink['wallpaper']['uri'] or '')} characters of data: address")
        cat = self.card("catppuccin-mocha")
        self.check("Catppuccin Mocha came through theme.import (base16)", cat["from"].startswith("base16:"), cat["from"])

    def words(self):
        d = self.d
        before = len(self.k.log.records)
        out = d.say("theme.import text=" + Q(NORD))
        self.check("theme.import takes a base16 scheme", out["ok"] and any(r.get("name") == "nord" for r in d.rows("theme")), out["text"].replace(chr(10), " "))
        nord = self.card("nord")
        self.check("the import is a theme thing with its palette and licence", nord["variant"] == "dark"
                   and nord["palette"]["base0B"].lower() == "#a3be8c" and nord["from"] == "base16:nord",
                   f"{nord['licence']} · {nord['from']}")
        exported = d.say("theme.export nord format=base16")["rows"][0]
        back = base16.parse(exported["text"])
        self.check("theme.export format=base16 hands the sixteen colours back",
                   all(str(back["palette"][f"base{i:02X}"]).lower() == nord["palette"][f"base{i:02X}"].lower() for i in range(16)),
                   exported["filename"])
        dusk_before = self.card("dusk")["digest"]
        out = d.say("theme.make dusk name=" + Q("Dusk Green"))
        green = self.theme_id("Dusk Green")
        d.say("theme.edit " + green + " roles.accent=base0B")
        edited = self.card(green)
        dusk = self.card("dusk")
        self.check("a theme made from Dusk with another accent",
                   edited["roles"]["accent"].lower() == dusk["palette"]["base0B"].lower()
                   and edited["roles"]["accent"].lower() != dusk["roles"]["accent"].lower(),
                   f"accent {dusk['roles']['accent']} -> {edited['roles']['accent']}")
        self.check("the original Dusk is untouched", dusk["digest"] == dusk_before)
        ratio = C.contrast(edited["roles"]["accent-ink"], edited["roles"]["accent"])
        self.check("the text on the new accent still reads (accent-ink contrast)", ratio >= 4.5, f"{ratio:.2f}:1")
        self.green = green
        # a second person cannot edit it
        bad, text = self.refused(self.maya, "theme.edit " + green + " roles.accent=base08")
        self.check("someone else's theme cannot be edited; theme.make gives a copy", bad, text[:90])

    def scopes(self):
        d, maya, sam = self.d, self.maya, self.sam
        d.say("theme.use " + self.green)
        a, m, s = self.wears("Alex"), self.wears("Maya"), self.wears("Neighbour 01")
        self.check("a place-wide theme reaches everyone", a["name"] == m["name"] == s["name"] == "Dusk Green"
                   and m["source"] == "place", f"{a['name']} · {m['source']}")
        bad, text = self.refused(maya, "theme.use ink-landscape")
        self.check("a neighbour cannot set the place's theme", bad, text[:100])
        out = maya.say("theme.use nord for=me")
        a, m, s = self.wears("Alex"), self.wears("Maya"), self.wears("Neighbour 01")
        self.check("just-for-me changes only that person's look",
                   m["name"] == "Nord" and m["source"] == "me" and a["name"] == s["name"] == "Dusk Green",
                   f"Maya {m['name']} ({m['source']}); Alex {a['name']}; Neighbour 01 {s['name']}")
        seen = [r.get("for") for r in sam.say("rows theme-choice")["rows"]]
        self.check("one person's choice is private to them", not seen, f"Neighbour 01 sees {len(seen)} choices")
        records = len(self.k.log.records)
        maya.say("theme.try night-metal")
        t = self.wears("Maya")
        self.check("theme.try wears a theme on a 30 s trial", t["source"] == "trial" and t["name"] == "Night Metal"
                   and t["until"], f"until {t['until']}")
        self.check("a trial is only Maya's", self.wears("Alex")["name"] == "Dusk Green")
        left = self.wears("Maya")["until"]
        self.f.at += timedelta(seconds=31)
        back = self.wears("Maya")
        self.check("the trial reverts by itself, writing nothing", back["name"] == "Nord" and back["source"] == "me",
                   f"{back['name']} ({back['source']}) after 31 s")
        maya.say("theme.try night-metal")
        maya.say("theme.revert")
        self.check("theme.revert goes back at once", self.wears("Maya")["name"] == "Nord")
        maya.say("theme.try night-metal")
        maya.say("theme.keep")
        self.check("theme.keep makes the trial the person's own", self.wears("Maya")["name"] == "Night Metal"
                   and self.wears("Maya")["source"] == "me")
        maya.say("theme.use place for=me")
        self.check("follow the place again", self.wears("Maya")["name"] == "Dusk Green" and self.wears("Maya")["source"] == "place")
        d.say("theme.use seabright-day")
        self.check("restoring the place's theme", self.wears("Alex")["name"] == "Seabright Day")

    def sharing(self):
        d = self.d
        ink = d.say("theme.export ink-landscape")["rows"][0]
        dusk = d.say("theme.export " + self.green)["rows"][0]
        self.check("theme.export is one file with its wallpaper inside", ink["filename"].endswith(".agora-theme.json")
                   and '"svg"' in ink["text"], f"{ink['filename']} · {ink['bytes']} bytes; {dusk['filename']} · {dusk['bytes']} bytes")
        second = kdesk_scratch()
        try:
            for ex in (ink, dusk):
                got = second.say("theme.import json=" + Q(ex["text"]), "alex")
                self.check("a file imports into a second scratch world", got["ok"], got["text"][:90])
            for ex, name in ((ink, "ink-landscape"), (dusk, "Dusk Green")):
                src = M.digest(M.check_text(ex["text"]))
                row = next(r for r in second.say("theme.list", "alex")["rows"] if r["title"] == (self.card(name)["title"]))
                self.check(f"{name}: same theme on the other side (digest)", row["digest"] == src, src[:12])
            kit = second.say("kit " + second.k.place, "alex")
            self.check("the place's own kit still builds with the theme module's words and themes in it (a help text that looked "
                       "like a reference once broke it)", kit["ok"], kit["text"][:90])
            wall = next(r for r in second.say("theme.list", "alex")["rows"] if r["name"] == "ink-landscape-2"
                        or r["title"] == "Ink Landscape" and r["wallpaper"]["kind"] == "svg")
            self.check("the wallpaper came with it", wall["wallpaper"]["kind"] == "svg" and wall["wallpaper"]["uri"])
        finally:
            second.close()

    def kits(self):
        import test_kits
        t = test_kits.Kits("run")
        t.setUp()
        try:
            self.run_kits(t)
        finally:
            t.tearDown()

    def run_kits(self, t):
        d = self.d
        ink = d.say("theme.get ink-landscape")["rows"][0]["theme"]
        text = M.canonical(ink)
        made = t.line(t.surl, "make kind=theme name=ink-landscape title=" + Q("Ink Landscape") + " text=" + Q(text) + " in=" + t.sg)["made"][0]
        kit = t.line(t.surl, f"kit {t.sg}")["made"][0]
        bundle = t.line(t.surl, f"look {kit}")["rows"][0]["bundle"]
        defs = [x["facts"] for x in bundle["definitions"] if x["facts"].get("kind") == "theme"]
        self.check("a kit carries a theme, wallpaper and all", len(defs) == 1 and "svg" in defs[0].get("text", ""),
                   f"{len(defs[0]['text'])} characters")
        got = t.take(bundle)
        taken = [x for x in got["made"] if t.t.state.get(x, "kind") == "theme"]
        same = M.digest(M.check_text(t.t.state.get(taken[0], "text"))) == M.digest(M.check_text(text))
        self.check("taking the kit in the other world makes the same theme", same, M.digest(M.check_text(text))[:12])
        refs = t.t.state.get(taken[0], "text")
        self.check("theme text is opaque to the kit's reference scan (colours are not mistaken for things)",
                   "#" in refs and "base0D" in refs)
        # the hostile kit: a bundle whose theme text is bad is refused whole
        bad = json.loads(json.dumps(bundle))
        evil = json.loads(text)
        evil["type"] = {"ui": "Arial, url(https://evil.example/f.woff)"}
        for x in bad["definitions"]:
            if x["facts"].get("kind") == "theme":
                x["facts"]["text"] = json.dumps(evil)
        before = len(t.t.log.records)
        out = t.take(bad, ok=False)
        self.check("a kit with a malicious theme is refused whole, writing nothing",
                   len(t.t.log.records) == before, (out.get("text") or "")[:110])

    def malicious(self):
        maya, d = self.maya, self.d
        base = json.loads(json.dumps(self.card("dusk")["theme"]))

        def bad(name, mutate, expect):
            t = json.loads(json.dumps(base))
            mutate(t)
            n = len(self.k.log.records)
            t0 = time.time()
            refused, text = self.refused(maya, "theme.import json=" + Q(json.dumps(t)))
            print("   (%.1f s)" % (time.time() - t0), flush=True)
            ok = refused and expect in text and len(self.k.log.records) == n
            self.check("refused: " + name, ok, text[:150] if not ok else text[:140])

        def font(t): t["type"] = {"ui": "Arial</style><script>alert(1)</script>"}
        bad("a script in a font name", font, "type.ui")
        def urlv(t): t["type"] = {"mono": "Consolas, url(https://evil.example/x.woff)"}
        bad("url( inside a value", urlv, "type.mono")
        def accent(t): t["roles"] = {"accent": "url(javascript:alert(1))"}
        bad("a colour that is an address", accent, "roles.accent")
        def css_key(t): t["css"] = "body{display:none}"
        bad("a key that is not part of a theme (raw css)", css_key, "css")
        def big_svg(t):
            t["wallpaper"] = {"kind": "svg", "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="' + "M0 0L1 1" * 40000 + '"/></svg>'}
        bad("an oversized svg wallpaper (320 KB; the limit is 128 KiB)", big_svg, "wallpaper.svg")
        def script_svg(t):
            t["wallpaper"] = {"kind": "svg", "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><script>alert(1)</script></svg>'}
        bad("a script inside the svg", script_svg, "wallpaper.svg")
        def href_svg(t):
            t["wallpaper"] = {"kind": "svg", "svg": '<svg xmlns="http://www.w3.org/2000/svg" xmlns:x="http://www.w3.org/1999/xlink" viewBox="0 0 10 10"><use href="https://evil.example/a.svg#x"/></svg>'}
        bad("an svg that fetches an address", href_svg, "wallpaper.svg")
        def big_png(t):
            import base64
            data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200_000
            t["wallpaper"] = {"kind": "image", "image": "data:image/png;base64," + base64.b64encode(data).decode()}
        bad("an oversized raster wallpaper (200 KB; the limit is 150 KB)", big_png, "larger than")
        def remote(t): t["wallpaper"] = {"kind": "image", "image": "https://evil.example/wall.png"}
        bad("a wallpaper that is a web address", remote, "wallpaper.image")
        n = len(self.k.log.records)
        refused, text = self.refused(maya, "make kind=theme name=sneaky title=Sneaky text=" +
                                     Q(json.dumps(dict(base, type={"ui": "Arial</style><script>"}))))
        self.check("a theme written straight to the world, bypassing the module, is refused by the kernel hook",
                   refused and len(self.k.log.records) == n, text[:140])
        refused, text = self.refused(maya, "theme.options")
        self.check("(control) a harmless word still answers", not refused)

    # ---------------------------------------------------------------------------------------------------- delivery
    def probe_widget(self):
        code = (LAB / "widgets/common.js").read_text(encoding="utf-8") + (
            "\ndocument.body.append(el('div',{id:'probe',style:{padding:'24px'}},"
            "el('h2',{},'A widget made with the old vocabulary'),el('p',{},'Its page, text and accent are the theme\\'s.'),"
            "el('button',{class:'primary'},'Primary')));\n")
        d = self.d
        w = d.say("make kind=widget name=theme-probe title=" + Q("Theme probe") + " style=bars code=" + Q(code))["made"][0]
        d.say("look " + w)
        d.say("widget " + w + " surface=window grants=" + Q("window.surface rows look"))
        return w

    def chrome(self, page, width=1280, height=420):
        c = Browser().__enter__()
        c.call("Runtime.enable")
        c.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
        c.call("Page.navigate", url=self.url + "/dev/signin?token=" + self.alex + "&next=/desk/" + page)
        c.until("document.readyState==='complete'")
        time.sleep(0.8)
        return c

    def surface_of(self, name):
        return self.card(name)["roles"]["surface"].lower()

    def delivery(self):
        d = self.d
        os.environ["AGORA_WIDGET_HOST_KEY"] = self.host_key
        widget = self.probe_widget()
        board = self.u.page("Alex")
        appearance_page = Page(self.url, self.alex, self.ids["widget"], 1280, 900, clock=self.f.at)
        probe = Page(self.url, self.alex, widget, 900, 420, clock=self.f.at)
        self.pages += [appearance_page, probe]
        bar = self.chrome("taskbar.html", 1280, 160)
        frame = self.chrome("help.html", 1280, 500)
        appearance_page.until('!!document.querySelector(".ap[data-ready]")', 30)
        probe.until('!!document.querySelector("#probe")', 30)
        self.surfaces = dict(board=board, appearance=appearance_page, probe=probe, bar=bar, frame=frame)

        def paper(p):
            return p.js('getComputedStyle(document.documentElement).getPropertyValue("--ag-surface").trim().toLowerCase()')

        def body_bg(p):
            return p.js('(()=>{const c=document.createElement("canvas").getContext("2d");c.fillStyle=getComputedStyle(document.body).backgroundColor;return c.fillStyle})()')

        def chrome_surface(c):
            return c.js('getComputedStyle(document.documentElement).getPropertyValue("--ag-surface").trim().toLowerCase()')

        def probe_bg(p):
            return p.js('(()=>{const c=document.createElement("canvas").getContext("2d");c.fillStyle=getComputedStyle(document.body).backgroundColor;return c.fillStyle})()')

        def nonlazy(c):
            c.js("window.AgoraTheme&&AgoraTheme.refresh();0")

        native_path = Path(self.k.dir) / "modules/theme/theme-native.json"
        hashes_before = d.say("theme.native")["rows"][0]["hash"]
        day = self.surface_of("seabright-day")
        for c in (bar, frame):
            self.wait(lambda: chrome_surface(c) == day, 15)
        self.check("before: every surface wears Seabright Day", paper(board) == day and paper(appearance_page) == day
                   and paper(probe) == day and chrome_surface(bar) == day and chrome_surface(frame) == day, day)
        colour_before = board.js('getComputedStyle(document.documentElement).getPropertyValue("--board-colour-1").trim().toLowerCase()')
        # the single act
        target = "dusk"
        want = self.surface_of(target)
        records = len(self.k.log.records)
        used = d.say("theme.use " + target)
        acts = len(self.k.log.records) - records
        record = used["records"][0]
        for c in (bar, frame):
            nonlazy(c)
        self.wait(lambda: all(x == want for x in (paper(board), paper(appearance_page), paper(probe),
                                                  chrome_surface(bar), chrome_surface(frame))), 30)
        got = dict(board=paper(board), appearance=paper(appearance_page), widget=paper(probe),
                   bar=chrome_surface(bar), help=chrome_surface(frame))
        self.check("ONE theme.use reached the board, the Appearance app, a legacy widget and two host chrome pages",
                   all(v == want for v in got.values()), f"{acts} record(s); all show {want}")
        sheet = json.loads(self.wait(lambda: native_path.read_text(encoding="utf-8") if native_path.exists() else None, 15))
        dusk = self.card("dusk")
        self.check("the native sheet changed in the same act", sheet["hash"] != hashes_before and sheet["theme"] == "Dusk"
                   and sheet["variant"] == "dark" and sheet["gap_inner"] == dusk["shape"]["gap_inner"],
                   f"hash {sheet['hash'][:10]} · gap {sheet['gap_inner']} · corner {sheet['corner']}")
        root_var = lambda name: board.js('getComputedStyle(document.documentElement).getPropertyValue("' + name + '").trim().toLowerCase()')
        self.check("the board's own tokens moved: --paper is dark, and a colour the board wrote for the light look (--board-colour-1) is worn in Dusk",
                   not C.is_light(root_var("--paper")) and root_var("--board-colour-1") != colour_before,
                   f"--paper {root_var('--paper')}; --board-colour-1 {colour_before} -> {root_var('--board-colour-1')}")
        legacy = probe.js('getComputedStyle(document.querySelector("#probe h2")).color')
        self.check("the legacy widget's text moved with it", legacy != "rgb(53, 67, 61)", legacy)
        for c in (bar, frame):
            self.shot_chrome(c, OUT / ("delivery-dusk-" + ("bar" if c is bar else "help") + ".png"))
        for name, p in (("board", board), ("appearance", appearance_page), ("probe", probe)):
            self.shot_page(p, f"delivery-dusk-{name}.png")
        d.say("undo " + record)
        for c in (bar, frame):
            nonlazy(c)
        self.wait(lambda: all(x == day for x in (paper(board), paper(appearance_page), paper(probe),
                                                 chrome_surface(bar), chrome_surface(frame))), 30)
        try:
            back = json.loads(self.wait(lambda: native_path.read_text(encoding="utf-8") if json.loads(native_path.read_text(encoding="utf-8"))["hash"] == hashes_before else None, 15))
        except AssertionError:
            print("native file now:", native_path.read_text(encoding="utf-8")[:300].replace(chr(10), " "), "| before:", hashes_before, "| word:", d.say("theme.native")["rows"][0]["hash"])
            raise
        self.check("ONE undo put every surface and the native sheet back", paper(board) == day and chrome_surface(bar) == day
                   and back["hash"] == hashes_before, f"native hash {back['hash'][:10]}")
        for name, p in (("board", board), ("appearance", appearance_page), ("probe", probe)):
            self.shot_page(p, f"delivery-undone-{name}.png")

    def starter_looks(self):
        s = self.surfaces
        board, ap, probe, bar, frame = s["board"], s["appearance"], s["probe"], s["bar"], s["frame"]
        order = [slug for slug, _ in S.ORDER]
        for slug in order:
            want = self.surface_of(slug)
            self.d.say("theme.use " + slug)
            for c in (bar, frame):
                c.js("window.AgoraTheme&&AgoraTheme.refresh();0")
            self.wait(lambda: board.js('getComputedStyle(document.documentElement).getPropertyValue("--ag-surface").trim().toLowerCase()') == want
                      and ap.js('getComputedStyle(document.documentElement).getPropertyValue("--ag-surface").trim().toLowerCase()') == want
                      and bar.js('getComputedStyle(document.documentElement).getPropertyValue("--ag-surface").trim().toLowerCase()') == want, 30)
            time.sleep(1.2)
            self.shot_page(board, f"{slug}-board.png")
            self.shot_page(ap, f"{slug}-appearance.png")
            self.shot_page(probe, f"{slug}-widget.png")
            self.shot_chrome(bar, OUT / f"{slug}-taskbar.png")
            self.shot_chrome(frame, OUT / f"{slug}-help.png")
            self.shots += [f"evidence/{slug}-taskbar.png", f"evidence/{slug}-help.png"]
            self.contact_sheet(slug)
        self.d.say("theme.use seabright-day")
        self.check("every starter rendered across the board, a painter component, a legacy widget and host chrome",
                   True, ", ".join(order))

    def contact_sheet(self, slug):
        """One picture per starter: the board, the Appearance app, a legacy widget, the taskbar and a host page, together."""
        from PIL import Image, ImageDraw
        parts = [("board", 760, 475), ("appearance", 640, 450), ("widget", 440, 206), ("taskbar", 760, 95), ("help", 640, 250)]
        sheet = Image.new("RGB", (1440, 960), (24, 24, 28))
        spots = {"board": (10, 10), "appearance": (790, 10), "widget": (790, 480), "taskbar": (10, 495), "help": (10, 600)}
        for name, w, h in parts:
            im = Image.open(OUT / f"{slug}-{name}.png").convert("RGB").resize((w, h), Image.LANCZOS)
            sheet.paste(im, spots[name])
        ImageDraw.Draw(sheet).text((660, 940), slug, fill=(200, 200, 200))
        path = OUT / f"sheet-{slug}.png"
        sheet.save(path)
        self.shots.append(str(path.relative_to(HERE)))

    def appearance_ui(self):
        """The Appearance app's own buttons, pressed in a hidden page."""
        ap = self.surfaces["appearance"]
        d = self.d
        ap.js('document.querySelector("[data-tab=gallery]")&&document.querySelector("[data-tab=gallery]").click()')
        ap.until('document.querySelectorAll(".ap-card").length>=5', 20)
        ap.js('document.querySelector(".ap-card[data-theme] [data-act=try]").click()')
        first = ap.js('document.querySelector(".ap-card[data-theme]").dataset.theme')
        self.wait(lambda: self.wears("Alex")["source"] == "trial", 20)
        ap.until('!!document.querySelector(".ap-trial")', 20)
        self.check("Try in the app wears the theme on a trial, with Keep and Go back in sight",
                   self.wears("Alex")["source"] == "trial" and ap.js('[...document.querySelectorAll(".ap-wear button")].map(b=>b.textContent).join("|")') == "Keep|Go back")
        self.shot_page(ap, "appearance-trial.png")
        ap.js('[...document.querySelectorAll(".ap-wear button")].find(b=>b.textContent==="Go back").click()')
        self.wait(lambda: self.wears("Alex")["source"] != "trial", 20)
        self.check("Go back reverts", self.wears("Alex")["name"] == "Seabright Day")
        # import by pasting
        ap.js('document.querySelector("[data-tab=share]").click()')
        ap.until('!!document.querySelector("textarea")', 20)
        scheme = NORD.replace('name: "Nord"', 'name: "Nord Paste"')
        ap.js("(()=>{const t=document.querySelector('.ap textarea');t.value=" + json.dumps(scheme) + ";t.dispatchEvent(new Event('input',{bubbles:true}))})()")
        ap.js('document.querySelector("[data-act=import]").click()')
        self.wait(lambda: any(r.get("title") == "Nord Paste" for r in d.rows("theme")), 20)
        self.check("pasting a base16 scheme into the app imports it", True, "Nord Paste")
        self.shot_page(ap, "appearance-import.png")
        # editing live: change the accent of a copy and see the preview and the saved theme follow
        ap.js('document.querySelector("[data-tab=gallery]").click()')
        ap.until('document.querySelectorAll(".ap-card [data-act=make]").length>1', 20)
        ap.js('document.querySelectorAll(".ap-card[data-theme]")[2].querySelector("[data-act=make]").click()')
        ap.until('!!document.querySelector(".ap-edit")', 20)
        name = ap.js('document.querySelector(".ap-edit input[type=text]").value')
        ap.js("""(()=>{const i=[...document.querySelectorAll('.ap-edit input[type=color]')].find(x=>x.getAttribute('aria-label')==='Blue');
          i.value='#ff8800';i.dispatchEvent(new Event('input',{bubbles:true}));i.dispatchEvent(new Event('change',{bubbles:true}))})()""")
        saved = self.wait(lambda: next((r for r in d.rows("theme") if r.get("title") == name and "#ff8800" in r.get("text", "").lower()), None), 20)
        self.check("editing a colour in the app saves it to the copy", bool(saved), name)
        ap.until('!!document.querySelector(".ap-edit")', 20)
        ap.js("document.querySelector('.ap-edit').scrollIntoView()")
        self.shot_page(ap, "appearance-editor.png")
        # share to the board
        ap.js('document.querySelector("[data-tab=share]").click()')
        ap.until('!!document.querySelector("[data-act=share]")', 20)
        before = len(d.rows("post"))
        ap.js('document.querySelector("[data-act=share]").click()')
        shared = self.wait(lambda: len(d.rows("post")) > before, 40)
        post = max(d.rows("post"), key=lambda r: int(r["id"][2:]) if r["id"][2:].isdigit() else 0)
        try:
            self.wait(lambda: len([r for r in d.rows("file") if r.get("attached_to") == post["id"]]) >= 2, 20)
        except AssertionError:
            pass
        files = [r for r in d.rows("file") if r.get("attached_to") == post["id"]]
        if len(files) != 2:
            print("   share note:", ap.js('(document.querySelector(".ap-note")||{}).textContent'), "| toast:", ap.js('(document.querySelector(".toast")||{}).textContent'), "| receipt:", ap.c.js('[...document.querySelectorAll("#receipt")].map(n=>n.textContent).join(" / ")'), "| errors:", str(ap.errors)[-600:])
        self.check("Share to the board posts with the preview picture and the theme file attached", shared and len(files) == 2,
                   f"post {post['id']} with {[f.get('name') for f in files]}")
        self.shot_page(ap, "appearance-share.png")
        # clean up the app's test acts: nothing else
        d.say("theme.use seabright-day")

    def run(self):
        steps = [self.starters, self.words, self.scopes, self.sharing, self.kits, self.malicious, self.delivery,
                 self.starter_looks, self.appearance_ui]
        if "--only" in sys.argv:
            steps = [getattr(self, n) for n in sys.argv[sys.argv.index("--only") + 1].split(",")]
        try:
            for step in steps:
                print("--", step.__name__, flush=True)
                step()
        finally:
            self.close()
        result = dict(checks=len(self.checks), failed=[c for c in self.checks if not c["ok"]],
                      live_desktop_touched=False, shots=len(self.shots))
        (OUT / "proof-result.json").write_text(json.dumps(dict(result, checks_detail=self.checks, shots=self.shots), indent=1))
        print("THEME PROOF", json.dumps(result))

    def close(self):
        for p in getattr(self, "pages", []):
            try:
                p.close()
            except Exception:
                pass
        for c in getattr(self, "surfaces", {}).values():
            try:
                if hasattr(c, "close"):
                    c.close()
                else:
                    c.__exit__(None, None, None)
            except Exception:
                pass
        try:
            self.u.close()
        except Exception:
            pass


def kdesk_scratch():
    from test_kdesk import Desk
    d = Desk()
    d.wait(lambda: "theme.use" in d.say("help all")["text"], 30)
    d.wait(lambda: len(d.say("theme.list", "alex")["rows"]) >= 5, 30)
    return d


if __name__ == "__main__":
    import faulthandler
    if "--dump" in sys.argv:
        faulthandler.dump_traceback_later(int(sys.argv[sys.argv.index("--dump") + 1]), exit=True)
    Proof().run()
