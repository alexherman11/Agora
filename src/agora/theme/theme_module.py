"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

theme: the theme words, a module (SHAPE section 11). One process, any number of themes, nothing kept of its own.

    theme.list [mine=yes]                  see   the themes you may see, with what each looks like and which one you wear
    theme.get <theme>                      see   one theme in full, and its derived values
    theme.current                          see   which theme you wear, and why (place | me | trial)
    theme.use <theme> [for=place]          do    yours (27 Oct: yours by default); for=place: the place's (stewards); `place` follows the place
    theme.try <theme> [seconds=30]         do    wear it for a while; it goes back by itself unless you keep it
    theme.keep / theme.revert              do    keep what you are trying / go back now
    theme.import [yaml=|json=|text=] [name=] [in=<group>]
                                           do    a base16/base24 scheme or an agora-theme.json, checked, as a theme of yours
    theme.export <theme> [format=agora|base16|css]
                                           see   a downloadable file (a row with filename and text)
    theme.make from=<theme> [name=]        do    your own copy, to edit
    theme.edit <theme> path=value ...      do    change your theme (palette.base0D=#c4a8ff shape.radius=large wallpaper=preset:dusk)
    theme.preview <theme> path=value ...   see   what an edit would look like; writes nothing
    theme.options [theme=<theme>]          see   the safe fonts, shapes and wallpapers the editor offers
    theme.native / theme.css               see   the native sheet and the CSS for you
    theme.starters                         do    (stewards) add the starter themes that are missing

Where the look is read from is not here: the kernel's door serves /theme.css and the others (theme/service.py) from the
same facts these words write, so a switch reaches every surface at once and `undo` puts it back. This module also keeps
<home>/theme-native.json for the window manager, and says `theme.changed` (delivered, not recorded) when the look changes.
Off switch: `off theme`. The look stays; only the words stop.
"""
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from theme import base16, service, starters  # noqa: E402
from theme import compile as K  # noqa: E402
from theme import model as M  # noqa: E402
from theme import wallpapers as W  # noqa: E402

TRY_SECONDS = 30
KINDS = ("theme", "theme-settings", "theme-choice")
OFFER = [
    {"word": "theme.list", "kind": "see", "takes": "[mine=yes]", "may": "anyone",
     "help": "theme.list: the themes you may see, each with its palette and shape and which one you wear now (place, "
             "just for you, or being tried). One theme is one palette and one shape language for every window."},
    {"word": "theme.get", "kind": "see", "takes": "<theme>", "may": "anyone",
     "help": "theme.get <theme>: one theme in full, with the derived values (roles, the extra palette slots, accent-ink, contrast)."},
    {"word": "theme.current", "kind": "see", "takes": "", "may": "anyone",
     "help": "theme.current: the theme you wear, and why: the place's, your own choice, or one you are trying."},
    {"word": "theme.use", "kind": "do", "takes": "<theme> [for=place]", "may": "anyone",
     "help": "theme.use <theme> [for=place]: wear a theme, just you (agents change it for the person they act for). "
             "for=place changes the place's theme for everyone (stewards). theme.use place follows the place again. "
             "undo puts it back."},
    {"word": "theme.try", "kind": "do", "takes": "<theme> [seconds=30]", "may": "anyone",
     "help": "theme.try <theme> [seconds=30]: wear a theme for a while, just yourself. It goes back by itself unless "
             "you say theme.keep."},
    {"word": "theme.keep", "kind": "do", "takes": "", "may": "anyone",
     "help": "theme.keep: keep the theme you are trying as your own choice."},
    {"word": "theme.revert", "kind": "do", "takes": "", "may": "anyone",
     "help": "theme.revert: stop trying a theme now and go back to what you wore."},
    {"word": "theme.import", "kind": "do", "takes": "[yaml=<text>] [json=<text>] [name=<title>] [in=<group>]", "may": "members",
     "help": "theme.import yaml=\"<scheme>\" | json=\"<agora-theme.json text>\" [name=…] [in=<group>]: make a theme "
             "from a tinted-theming scheme (base 16 or 24) or an exported agora theme. It is checked first: no scripts, "
             "no addresses, fonts by name only, assets inline and small. A refusal says why."},
    {"word": "theme.export", "kind": "see", "takes": "<theme> [format=agora|yaml|css]", "may": "anyone",
     "help": "theme.export <theme> [format=agora|yaml|css]: a file to save (a row with filename and text): "
             "agora-theme.json with its wallpaper inside, a tinted-theming scheme (yaml), or the compiled theme.css."},
    {"word": "theme.make", "kind": "do", "takes": "<theme> [name=<title>] [in=<group>]", "may": "members",
     "help": "theme.make <theme> [name=…]: your own copy of a theme to edit (also theme.make from=<theme>)."},
    {"word": "theme.edit", "kind": "do", "takes": "<theme> path=value ...", "may": "members",
     "help": "theme.edit <theme> palette.base0D=#c4a8ff shape.radius=large surface.bar_opacity=0.7 type.ui=\"Segoe UI\" "
             "wallpaper=preset:dusk: change a theme you made. Every value is checked; an empty value drops an override."},
    {"word": "theme.preview", "kind": "see", "takes": "<theme> path=value ...", "may": "anyone",
     "help": "theme.preview <theme> path=value ...: what theme.edit would give, as variables for a preview. Writes nothing."},
    {"word": "theme.changed", "kind": "hear", "takes": "", "may": "anyone",
     "help": "theme.changed: heard when the look changes (a theme used, tried, kept, reverted or edited, or a trial "
             "ending). A rule can act on it: rule on=theme.changed do=\"...\" (the wallpaper follows the theme this way)."},
    {"word": "theme.options", "kind": "see", "takes": "[theme=<theme>]", "may": "anyone",
     "help": "theme.options: the safe fonts, radii, shadows, motion curves and wallpaper presets an editor may offer."},
    {"word": "theme.native", "kind": "see", "takes": "", "may": "anyone",
     "help": "theme.native: the sheet the window manager reads (gaps, border width, corner, state colours, bar and dock "
             "sizes) for the theme you wear."},
    {"word": "theme.css", "kind": "see", "takes": "", "may": "anyone",
     "help": "theme.css: the --ag-* variables of the theme you wear, as CSS text."},
    {"word": "theme.starters", "kind": "do", "takes": "", "may": "stewards",
     "help": "theme.starters: add the starter themes this place is missing (Seabright Day, Dusk, Night Metal, Ink "
             "Landscape, Catppuccin Mocha). Never changes a theme that is already here."},
]


def q(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


class Refuse(Exception):
    pass


class Theme:
    def __init__(self):
        self.out_lock = threading.Lock()
        self.waiting = {}
        self.hello = {}
        self.after = {}                 # use -> announce when the kernel admits that answer
        self.pending_see = []           # (use, key) of readings made inside a call, to match the kernel's answers
        self.native_lock = threading.Lock()
        self.native_hash = None
        self.refresh_timer = None
        self.closed = threading.Event()

    # ------------------------------------------------------------------------------------------- protocol
    def send(self, msg):
        with self.out_lock:
            try:
                sys.stdout.write(json.dumps(msg) + "\n")
                sys.stdout.flush()
            except (OSError, ValueError):
                self.closed.set()

    def ask(self, key, msg, timeout=12):
        slot = [threading.Event(), None]
        self.waiting[key] = slot
        self.send(msg)
        slot[0].wait(timeout)
        self.waiting.pop(key, None)
        return slot[1] or {"refused": "the kernel did not answer", "rows": [], "text": ""}

    def see(self, line, use=None):
        """A reading: inside a call (use given) as the caller, else on the module's own grants."""
        if use:
            key = "see:" + uuid.uuid4().hex[:8]
            slot = [threading.Event(), None]
            self.waiting[key] = slot
            self.pending_see.append((use, key))
            self.send({"t": "see", "use": use, "line": line})
            slot[0].wait(12)
            self.waiting.pop(key, None)
            try:
                self.pending_see.remove((use, key))
            except ValueError:
                pass
            got = slot[1] or {"refused": "the kernel did not answer", "rows": []}
        else:
            i = uuid.uuid4().hex[:10]
            got = self.ask(i, {"t": "see", "id": i, "line": line})
        if got.get("refused"):
            raise Refuse(str(got["refused"]))
        return got.get("rows") or []

    def do_own(self, line, saw=None):
        i = uuid.uuid4().hex[:10]
        return self.ask(i, {"t": "do", "id": i, "line": line, **({"saw": saw} if saw else {})}, 20)

    def announce(self, text=""):
        self.send({"t": "happen", "word": "theme.changed", "target": None, "text": text})

    def handle(self, msg):
        t = msg.get("t")
        if t == "hello":
            self.hello = msg
            self.send({"t": "offer", "words": OFFER})
            threading.Thread(target=self.start, daemon=True).start()
        elif t in ("rows", "done"):
            slot = self.waiting.get(msg.get("id"))
            if not slot and msg.get("use"):
                key = next((k for u, k in self.pending_see if u == msg["use"]), None) if t == "rows" else None
                slot = self.waiting.get(key)
            if slot:
                slot[1] = msg
                slot[0].set()
            if t == "done" and msg.get("use") in self.after:
                what = self.after.pop(msg["use"])
                if msg.get("ok"):
                    self.announce(what)
                    self.schedule_refresh()
        elif t == "call":
            threading.Thread(target=self.answer, args=(msg,), daemon=True).start()
        elif t == "status?":
            self.send({"t": "status", "use": msg.get("use"), "doing": "themes: " + (self.native_hash or "starting")})
        elif t == "happen":
            self.schedule_refresh()
        elif t == "off":
            self.closed.set()
            os._exit(0)

    def answer(self, msg):
        try:
            out = self.call(msg)
        except Refuse as exc:
            out = {"refused": str(exc)}
        except M.ThemeError as exc:
            out = {"refused": "the theme was not accepted: " + "; ".join(f"{p}: {m}" for p, m in exc.errors[:6])
                              + (f" (+{len(exc.errors) - 6} more)" if len(exc.errors) > 6 else "")}
        except base16.SchemeError as exc:
            out = {"refused": "the scheme was not accepted: " + str(exc)}
        except Exception as exc:                    # a module's mistake is a refusal, never silence
            out = {"refused": f"{msg.get('word')} failed inside the theme module: {exc!r}"}
        if out.get("lines") and not out.get("refused"):
            self.after[msg["use"]] = out.pop("announce", "")
        else:
            out.pop("announce", None)
        self.send(dict(out, t="answer", use=msg["use"]))

    # ------------------------------------------------------------------------------------------- reading the world
    def now(self, use=None):
        try:
            return service.parse_time(self.see("clock", use)[0]["at"]) or datetime.now(timezone.utc)
        except (Refuse, IndexError, KeyError):
            return datetime.now(timezone.utc)

    def things(self, use=None):
        return {"themes": self.see("rows theme", use), "settings": self.see("rows theme-settings", use),
                "choices": self.see("rows theme-choice", use)}

    def steward(self, person):
        return person == self.hello.get("owner")

    def owner_made(self, row):
        """Made by the steward, or by this module acting for the steward (which leaves no `for`)."""
        return row.get("for") == self.hello.get("owner") or row.get("made_by") == self.hello.get("id")

    def pick(self, w, person, now):
        owner = self.hello.get("owner")
        settings = [{"id": s["id"], "active": s.get("active"), "steward": self.owner_made(s)} for s in w["settings"]]
        choices = [{"id": c["id"], "person": c.get("for"), "theme": c.get("theme"), "trial": c.get("trial"),
                    "trial_until": c.get("trial_until")} for c in w["choices"]]
        return service.pick(settings, choices, person, now)

    def find(self, w, ref):
        ref = (ref or "").strip()
        if not ref:
            raise Refuse("name a theme: theme.use dusk")
        rows = w["themes"]
        hit = next((r for r in rows if r["id"] == ref), None) or \
            next((r for r in rows if str(r.get("name", "")).lower() == ref.lower()), None) or \
            next((r for r in rows if str(r.get("title", "")).lower() == ref.lower()), None)
        if hit is None:
            raise Refuse(f"no theme {ref!r} that you can see; theme.list shows them")
        return hit

    # ------------------------------------------------------------------------------------------- a theme as rows
    def theme_of(self, row):
        return M.check_text(row.get("text"))

    def card(self, row, w, me, now, full=False):
        """What a gallery needs to draw one theme: its identity, its look and who wears it."""
        theme = self.theme_of(row)
        r = M.resolve(theme)
        picked, source, until = self.pick(w, me, now)
        place_id = next((s["active"] for s in reversed([x for x in w["settings"] if self.owner_made(x)])
                         if s.get("active")), None)
        mine = row.get("for") == me or (self.steward(me) and self.owner_made(row))
        m = r["meta"]
        uri = K.wallpaper_uri(r)
        out = {"kind": "theme", "id": row["id"], "rev": row.get("rev"), "name": row.get("name"),
               "title": m["name"], "author": m.get("author", ""), "licence": m["licence"], "variant": r["variant"],
               "tags": m.get("tags", []), "description": m.get("description", ""), "from": m.get("from", ""),
               "starter": row.get("starter") == "yes", "mine": mine, "digest": M.digest(theme),
               "can_place": self.steward(me),
               "place": row["id"] == place_id, "wearing": row["id"] == picked,
               "source": source if row["id"] == picked else "",
               "vars": K.scope(r), "palette": r["palette"], "roles": r["roles"], "shape": r["shape"],
               "type": r["type"], "surface": r["surface"], "windows": r["windows"],
               "wallpaper": {"kind": r["wallpaper"].get("kind", "none"), "fit": r["wallpaper"].get("fit", "cover"),
                             "dim": r["wallpaper"].get("dim", 0),
                             "background": K.wallpaper_css(r, None)[0] if r["wallpaper"].get("kind") == "gradient" else "none",
                             "uri": uri if uri and len(uri) <= 400_000 else None}}
        if full:
            out["theme"] = theme
        return out

    def preview_card(self, base_row, theme, w, me, now):
        r = M.resolve(theme)
        uri = K.wallpaper_uri(r)
        return {"kind": "theme-preview", "id": base_row["id"], "title": r["meta"]["name"], "variant": r["variant"],
                "vars": K.scope(r), "palette": r["palette"], "roles": r["roles"], "shape": r["shape"],
                "type": r["type"], "surface": r["surface"], "windows": r["windows"],
                "wallpaper": {"kind": r["wallpaper"].get("kind", "none"), "fit": r["wallpaper"].get("fit", "cover"),
                              "dim": r["wallpaper"].get("dim", 0),
                              "background": K.wallpaper_css(r, None)[0] if r["wallpaper"].get("kind") == "gradient" else "none",
                              "uri": uri if uri and len(uri) <= 400_000 else None},
                "digest": M.digest(theme)}

    # ------------------------------------------------------------------------------------------- the words
    def call(self, msg):
        word = msg["word"].split(".", 1)[1]
        a = msg.get("args") or {}
        kv = dict(a.get("kv") or {})
        arg = (a.get("target") or (a.get("words") or "")).strip()
        use = msg["use"]
        caller = msg.get("caller") or {}
        me = caller.get("person")
        handler = getattr(self, "w_" + word.replace("-", "_"), None)
        if not handler:
            raise Refuse(f"theme has no word {word}")
        return handler(use, me, caller, arg, kv)

    def w_list(self, use, me, caller, arg, kv):
        w = self.things(use)
        now = self.now(use)
        cards, skipped = [], 0
        for row in w["themes"]:
            try:
                cards.append(self.card(row, w, me, now))
            except M.ThemeError:
                skipped += 1
        if kv.get("mine") in ("yes", "true", "1"):
            cards = [c for c in cards if c["mine"]]
        order = [slug for slug, _ in starters.ORDER]
        cards.sort(key=lambda c: (0, order.index(c["name"])) if c["starter"] and c["name"] in order else (1, c["title"].lower()))
        lines = [f"{'*' if c['wearing'] else ' '} {c['id']} · {c['title']} · {c['variant']} · {c['author'] or 'unknown'}"
                 + (" · the place's" if c["place"] else "") for c in cards]
        if skipped:
            lines.append(f"({skipped} not shown: they do not pass the theme check)")
        return {"text": "\n".join(lines) or "no themes yet; a steward can say theme.starters", "rows": cards}

    def w_get(self, use, me, caller, arg, kv):
        w = self.things(use)
        row = self.find(w, arg or kv.get("theme"))
        c = self.card(row, w, me, self.now(use), full=True)
        _, warnings = M.validate(c["theme"])
        r = M.resolve(c["theme"])
        c["warnings"] = warnings
        c["contrast"] = {"ink_on_surface": round(__import__("theme.colour", fromlist=["x"]).contrast(
            r["roles"]["ink"], r["roles"]["surface"]), 2)}
        return {"text": f"{c['title']} · {c['variant']} · {c['id']}", "rows": [c]}

    def w_current(self, use, me, caller, arg, kv):
        w = self.things(use)
        now = self.now(use)
        tid, source, until = self.pick(w, me, now)
        name = next((r.get("title") or r.get("name") for r in w["themes"] if r["id"] == tid), "Seabright Day")
        left = max(0, int((until - now).total_seconds())) if until else None
        row = {"kind": "theme-current", "theme": tid, "name": name, "source": source,
               "until": until.isoformat() if until else None}
        return {"text": f"{name} ({source}" + (f", {left} s left" if left is not None else "") + ")", "rows": [row]}

    def choice_of(self, w, me):
        return next((c for c in w["choices"] if c.get("for") == me), None)

    def w_use(self, use, me, caller, arg, kv):
        w = self.things(use)
        personal = kv.get("for") not in ("place", "everyone")      # yours unless you say the place's (P6, 27 Oct)
        if arg.lower() in ("place", "default") and personal:
            ref, theme_id = None, "place"
        else:
            row = self.find(w, arg or kv.get("theme"))
            theme_id = row["id"]
            self.theme_of(row)                               # a theme that does not pass the check is never worn
        if personal:
            c = self.choice_of(w, me)
            if c:
                return {"lines": [f"set {c['id']} theme={theme_id} trial= trial_until="], "saw": {c["id"]: c["rev"]},
                        "text": f"you now wear {arg or theme_id} (just for you)", "announce": "me"}
            return {"lines": [f"make kind=theme-choice theme={theme_id} sees=me"], "saw": {},
                    "text": f"you now wear {arg or theme_id} (just for you)", "announce": "me"}
        if not self.steward(me):
            raise Refuse("only a steward sets the place's theme; theme.use <theme> changes it for you alone")
        owned = [s for s in w["settings"] if self.owner_made(s)]
        if owned:
            s = owned[-1]
            return {"lines": [f"set {s['id']} active={theme_id}"], "saw": {s["id"]: s["rev"]},
                    "text": f"the place now wears {arg or theme_id}", "announce": "place"}
        return {"lines": [f"make kind=theme-settings active={theme_id}"], "saw": {},
                "text": f"the place now wears {arg or theme_id}", "announce": "place"}

    def w_try(self, use, me, caller, arg, kv):
        w = self.things(use)
        row = self.find(w, arg or kv.get("theme"))
        self.theme_of(row)
        try:
            seconds = max(5, min(300, int(float(kv.get("seconds", TRY_SECONDS)))))
        except ValueError:
            raise Refuse("seconds is a number from 5 to 300") from None
        until = (self.now(use) + timedelta(seconds=seconds)).isoformat()
        c = self.choice_of(w, me)
        threading.Timer(seconds + 0.6, self.announce, args=("trial ended",)).start()
        threading.Timer(seconds + 0.8, self.schedule_refresh).start()
        if c:
            return {"lines": [f"set {c['id']} trial={row['id']} trial_until={until}"], "saw": {c["id"]: c["rev"]},
                    "text": f"trying {row.get('title') or row['id']} for {seconds} s; theme.keep keeps it", "announce": "trial"}
        return {"lines": [f"make kind=theme-choice theme=place trial={row['id']} trial_until={until} sees=me"], "saw": {},
                "text": f"trying {row.get('title') or row['id']} for {seconds} s; theme.keep keeps it", "announce": "trial"}

    def w_keep(self, use, me, caller, arg, kv):
        w = self.things(use)
        c = self.choice_of(w, me)
        now = self.now(use)
        until = service.parse_time(c.get("trial_until")) if c else None
        if not c or not c.get("trial") or not until or now >= until:
            raise Refuse("nothing is being tried right now; theme.try <theme> first")
        return {"lines": [f"set {c['id']} theme={c['trial']} trial= trial_until="], "saw": {c["id"]: c["rev"]},
                "text": "kept: this theme is now yours", "announce": "me"}

    def w_revert(self, use, me, caller, arg, kv):
        w = self.things(use)
        c = self.choice_of(w, me)
        if not c or not c.get("trial"):
            raise Refuse("nothing is being tried right now")
        return {"lines": [f"set {c['id']} trial= trial_until="], "saw": {c["id"]: c["rev"]},
                "text": "back to what you wore", "announce": "revert"}

    # ----- making themes
    def slug(self, w, title):
        base = base16.slugify(title)
        taken = {r.get("name") for r in w["themes"]}
        name, n = base, 2
        while name in taken:
            name, n = f"{base}-{n}", n + 1
        return name

    def make_line(self, w, theme, title=None, group=None, extra=""):
        clean = M.check(theme)
        name = self.slug(w, title or clean["meta"]["name"])
        return (f"make kind=theme name={q(name)} title={q(clean['meta']['name'])} text={q(M.canonical(clean))}"
                + (f" in={group}" if group else "") + extra), clean, name

    def w_import(self, use, me, caller, arg, kv):
        text = kv.get("yaml") or kv.get("json") or kv.get("text") or kv.get("base16") or ""
        if not text.strip():
            raise Refuse('theme.import yaml="<base16 scheme>" or json="<agora-theme.json>"')
        w = self.things(use)
        if text.lstrip().startswith("{"):
            try:
                obj = json.loads(text)
            except ValueError as exc:
                raise Refuse(f"that is not JSON: {exc}") from None
            if isinstance(obj, dict) and set(obj) == {"theme"} and isinstance(obj["theme"], dict):
                obj = obj["theme"]
            origin = "agora"
        else:
            obj = base16.to_theme(text, kv.get("name"))
            origin = "base16"
        if kv.get("name"):
            obj.setdefault("meta", {})["name"] = kv["name"]
        if not isinstance(obj, dict):
            raise Refuse("a theme is an object")
        if origin == "agora" and caller.get("name") and not (obj.get("meta") or {}).get("author"):
            obj.setdefault("meta", {})["author"] = caller["name"]
        line, clean, name = self.make_line(w, obj, group=kv.get("in"))
        warn = M.validate(clean)[1]
        return {"lines": [line], "saw": {}, "announce": "import",
                "text": f"imported {clean['meta']['name']} ({origin}) as {name}" + (" · " + "; ".join(warn) if warn else "")}

    def w_make(self, use, me, caller, arg, kv):
        w = self.things(use)
        row = self.find(w, arg or kv.get("from"))
        theme = json.loads(M.canonical(self.theme_of(row)))
        title = kv.get("name") or f"My {theme['meta']['name']}"
        theme["meta"]["name"] = title[:60]
        theme["meta"]["author"] = (caller.get("name") or theme["meta"].get("author") or "me")[:60]
        theme["meta"]["from"] = f"theme:{row.get('name') or row['id']}"[:80]
        theme["meta"].pop("description", None)
        line, clean, name = self.make_line(w, theme, group=kv.get("in"))
        return {"lines": [line], "saw": {}, "announce": "make",
                "text": f"made {clean['meta']['name']} ({name}) from {row.get('title') or row['id']}; theme.edit changes it"}

    def patched(self, w, arg, kv):
        row = self.find(w, arg or kv.get("theme"))
        patch = {k: v for k, v in kv.items() if k not in ("theme", "in")}
        for k in patch:
            if k != "wallpaper" and k.split(".")[0] not in M.TOP:
                raise Refuse(f"{k} is not a part of a theme (palette.base0D, shape.radius, surface.bar_opacity, ...)")
        theme = M.check(M.apply_patch(self.theme_of(row), patch))
        return row, theme

    def w_edit(self, use, me, caller, arg, kv):
        w = self.things(use)
        row, theme = self.patched(w, arg, kv)
        if not (row.get("for") == me or (self.steward(me) and self.owner_made(row))):
            raise Refuse("you can edit themes you made; theme.make <theme> gives you a copy")
        return {"lines": [f"set {row['id']} text={q(M.canonical(theme))} title={q(theme['meta']['name'])}"],
                "saw": {row["id"]: row["rev"]}, "announce": "edit",
                "text": f"{theme['meta']['name']} changed"}

    def w_preview(self, use, me, caller, arg, kv):
        w = self.things(use)
        row, theme = self.patched(w, arg, kv)
        card = self.preview_card(row, theme, w, me, self.now(use))
        warnings = M.validate(theme)[1]
        card["warnings"] = warnings
        return {"text": f"{theme['meta']['name']} (preview)", "rows": [card]}

    def w_export(self, use, me, caller, arg, kv):
        w = self.things(use)
        row = self.find(w, arg or kv.get("theme"))
        theme = self.theme_of(row)
        slug = row.get("name") or base16.slugify(theme["meta"]["name"])
        fmt = kv.get("format", "agora")
        if fmt in ("base16", "yaml"):
            text, filename, mime = base16.to_yaml(theme), f"{slug}.yaml", "text/yaml"
        elif fmt == "css":
            text, filename, mime = K.css(M.resolve(theme), None, M.digest(theme)), f"{slug}.theme.css", "text/css"
        elif fmt in ("agora", "json"):
            text, filename, mime = M.pretty(theme), f"{slug}.agora-theme.json", "application/json"
        else:
            raise Refuse("format is agora, yaml or css")
        if len(text) > M.MAX_TEXT:
            raise Refuse("that theme is too large to export")
        return {"text": f"{filename} · {len(text)} characters", "rows": [{"kind": "file-text", "filename": filename,
                                                                          "mime": mime, "text": text, "bytes": len(text.encode())}]}

    def w_options(self, use, me, caller, arg, kv):
        palette_theme = None
        if arg or kv.get("theme"):
            w = self.things(use)
            palette_theme = M.resolve(self.theme_of(self.find(w, arg or kv.get("theme"))))
        walls = []
        for name, wall in sorted(W.library().items()):
            base = {"name": name, "kind": wall["kind"]}
            if palette_theme is not None:
                r = dict(palette_theme, wallpaper=wall)
                base["background"] = K.wallpaper_css(r, None)[0] if wall["kind"] == "gradient" else "none"
                base["uri"] = K.wallpaper_uri(r)
            walls.append(base)
        row = {"kind": "theme-options", "fonts": M.FONT_STACKS, "radii": list(M.RADII), "shadows": list(M.SHADOWS),
               "eases": list(M.EASES), "blur": ["none", "soft"], "corners": ["square", "small", "round"],
               "icon_styles": ["native", "plate", "mono"], "licences": M.LICENCES, "wallpapers": walls,
               "limits": {k: list(v[:2]) for k, v in M.NUMBERS.items()}, "slots": M.SLOTS16}
        return {"text": "fonts, shapes, wallpapers", "rows": [row]}

    def w_native(self, use, me, caller, arg, kv):
        w = self.things(use)
        theme = self.theme_for(w, me, self.now(use))
        sheet = K.native(M.resolve(theme), M.digest(theme))
        return {"text": json.dumps(sheet), "rows": [dict(sheet, kind="theme-native")]}

    def w_css(self, use, me, caller, arg, kv):
        w = self.things(use)
        theme = self.theme_for(w, me, self.now(use))
        css = K.css(M.resolve(theme), None, M.digest(theme))
        return {"text": css, "rows": [{"kind": "theme-css", "text": css, "filename": "theme.css"}]}

    def theme_for(self, w, person, now):
        tid, source, until = self.pick(w, person, now)
        row = next((r for r in w["themes"] if r["id"] == tid), None)
        if row:
            try:
                return self.theme_of(row)
            except M.ThemeError:
                pass
        return service.builtin()

    def w_starters(self, use, me, caller, arg, kv):
        if not self.steward(me):
            raise Refuse("only a steward adds the starter themes")
        w = self.things(use)
        have = {r.get("name") for r in w["themes"]}
        lines, names = [], []
        for slug, theme in starters.all_starters():
            if slug in have:
                continue
            clean = M.check(theme)
            lines.append(f"make kind=theme name={q(slug)} title={q(clean['meta']['name'])} text={q(M.canonical(clean))} "
                         f"starter=yes as={slug.replace('-', '_')}")
            names.append(clean["meta"]["name"])
        if not lines:
            return {"text": "every starter theme is already here", "rows": []}
        if not [s for s in w["settings"] if self.owner_made(s)]:
            lines.append("make kind=theme-settings active=$seabright_day")
            if "seabright-day" in have:
                lines.pop()
        return {"lines": lines, "saw": {}, "announce": "starters", "text": "added " + ", ".join(names)}

    # ------------------------------------------------------------------------------------------- startup and the native sheet
    def start(self):
        try:
            if not self.hello.get("for"):
                return
            w = self.things()
            if not w["themes"]:
                lines = []
                for slug, theme in starters.all_starters():
                    clean = M.check(theme)
                    lines.append(f"make kind=theme name={q(slug)} title={q(clean['meta']['name'])} "
                                 f"text={q(M.canonical(clean))} starter=yes as={slug.replace('-', '_')}")
                if not w["settings"]:
                    lines.append("make kind=theme-settings active=$seabright_day")
                got = self.do_own("; ".join(lines))
                sys.stderr.write(f"theme: starters {'added' if got.get('ok') else 'refused: ' + str(got.get('refused'))}\n")
                sys.stderr.flush()
            self.refresh_native()
            threading.Thread(target=self.watch, daemon=True).start()
        except Exception as exc:                    # noqa: BLE001
            sys.stderr.write(f"theme: startup failed: {exc!r}\n")
            sys.stderr.flush()

    def watch(self):
        """The kernel does not always tell a module about an `undo` of its own act, so the native sheet also follows the
        two small kinds that decide what anyone wears (the place's setting, each person's choice) every few seconds.
        Reading them is cheap; a theme's own text is not read here (an edit is heard as `set`)."""
        last = None
        while not self.closed.wait(3):
            try:
                rows = self.see("rows theme-settings") + self.see("rows theme-choice")
            except Refuse:
                continue
            sig = json.dumps(sorted((r["id"], r.get("rev"), r.get("active"), r.get("theme"), r.get("trial")) for r in rows),
                             default=str)
            if last is not None and sig != last:
                self.schedule_refresh()
            last = sig

    def schedule_refresh(self):
        if self.refresh_timer:
            self.refresh_timer.cancel()
        self.refresh_timer = threading.Timer(0.4, self.refresh_native)
        self.refresh_timer.daemon = True
        self.refresh_timer.start()

    def refresh_native(self):
        """<home>/theme-native.json for the window manager, for the person this module is installed for."""
        home = self.hello.get("home")
        me = self.hello.get("for")
        if not home or not me:
            return
        with self.native_lock:
            try:
                w = self.things()
                theme = self.theme_for(w, me, self.now())
                sheet = K.native(M.resolve(theme), M.digest(theme))
                tid, source, until = self.pick(w, me, self.now())
                sheet["source"], sheet["until"] = source, until.isoformat() if until else None
            except (Refuse, M.ThemeError, KeyError) as exc:
                sys.stderr.write(f"theme: native sheet not refreshed: {exc}\n")
                sys.stderr.flush()
                return
            h = json.dumps(sheet, sort_keys=True)
            if h == self.native_hash:
                return
            Path(home).mkdir(parents=True, exist_ok=True)
            tmp = Path(home) / "theme-native.json.tmp"
            tmp.write_text(json.dumps(sheet, indent=1), encoding="utf-8")
            os.replace(tmp, Path(home) / "theme-native.json")
            changed = self.native_hash is not None
            self.native_hash = h
        if changed:
            self.announce("native sheet")

    def run(self):
        for line in sys.stdin:
            try:
                self.handle(json.loads(line))
            except json.JSONDecodeError:
                continue
            except Exception as exc:                # noqa: BLE001  one bad message never stops the reader
                sys.stderr.write(f"theme: {exc!r}\n")
                sys.stderr.flush()
        os._exit(0)


if __name__ == "__main__":
    Theme().run()
