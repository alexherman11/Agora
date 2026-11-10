"""Guarded acceptance of the Markdown chat body (a7629, for a7557's landed source and a7610's staged passages).

Everything runs on a disposable copy of a world, in a real Edge window on a hidden desktop (hud_playtest's Copy and
Window, guarded). The staged passages are applied to the copy's own jeff-chat and conversation lenses, preflighted
first and reversed at the end. Fixture lines go to a disposable chat made in the copy (with=alex): both lenses show
`sayings involving:alex`, so nothing is appended to the Conversation, even the copy's. Replies are sent only after the
copy's draft says they go to the disposable chat.

Not done, by design: no account or media service calls, no reading of the system clipboard (a copy event is caught in
the page and cancelled, so the system clipboard is untouched), no host window (the HUD's host bridge is a recording
stand-in in the page, named as such), no external link opened, nothing on Alex's screen.

    python src/desktop/chat-markdown/review/accept.py [--small] [--world frontier-try]
"""
import argparse
import asyncio
import datetime
import hashlib
import json
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
WINDOW = HERE.parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(WINDOW))
sys.path.insert(0, str(HERE.parent / "slice1"))
import hud_playtest as H  # noqa: E402
import stage  # noqa: E402

DEMOS = Path(r"C:/Projects/Agora4/src/desktop/demos/chat-markdown-review")
WHO = "worker-a7629"
FILM = "src/desktop/demos/a5820/writing-demo.mp4"
PICTURE = "src/desktop/demos/chat-markdown-review/fixture-picture.png"     # made by fixture_picture(): plain shapes, no one's content
SOURCES = ["src/text-desk/notation/desk-shell/lens.js", "src/text-desk/notation/desk-shell/markdown.js",
           "src/text-desk/notation/desk-shell/media.js", "src/text-desk/notation/desk-shell/textedit.js",
           "src/desktop/chat-markdown/slice1/stage.py", "src/desktop/chat-markdown/slice1/patches.md"]

FIXTURE = "\n".join([
    "# Review heading one",
    "## Second heading",
    "Plain **bold**, *italic*, `inline code`, a named thing a5202 and an [explicit link](https://example.test/) and a [bad link](javascript:alert(1)).",
    "- parent item",
    "  - child item",
    "- [ ] open task",
    "- [x] done task",
    "1. first",
    "2. second",
    "> A quoted line",
    "---",
    "```text",
    "very-long-code-" * 60,
    "```",
    "| Name | Value |",
    "| --- | --- |",
    "| fixture | " + "wide cell " * 60 + "|",
    f"![fixture picture]({PICTURE})",
    f"The film: {FILM}",
    "<script>window.__xss = 1</script> <img src=x onerror=\"window.__xss=2\">",
])
MALFORMED = "\n".join(["```", "unclosed fence", "| a | b", "|--", "**unclosed bold", "[x](javascript:alert(2))", "MALFORMED-MARK"])

# what each message body looks like in the page: its document, links, boxes, media, widths
MEASURE = r"""(() => { const out = [];
  for (const d of document.querySelectorAll('.md-doc.md-read, [data-md-failed="1"]')) {
    const part = d.closest('[data-key]'), r = d.getBoundingClientRect();
    const widget = [...d.querySelectorAll('.md-widget')].map(w => ({ cls: w.className, sw: w.scrollWidth, cw: w.clientWidth, ox: getComputedStyle(w).overflowX }));
    const code = [...d.querySelectorAll('.md-code')].map(c => ({ sw: c.scrollWidth, cw: c.clientWidth, ws: getComputedStyle(c).whiteSpace }));
    const host = part ? part : d;
    out.push({ key: part ? part.dataset.key.split('/').slice(-3).join('/') : '', failed: d.dataset.mdFailed === '1' || !!d.closest('[data-md-failed="1"]'),
      text: (d.innerText || '').slice(0, 60), rect: [r.left, r.top, r.width, r.height].map(v => Math.round(v * 10) / 10),
      sw: d.scrollWidth, cw: d.clientWidth, partSw: host.scrollWidth, partCw: host.clientWidth,
      h1: d.querySelectorAll('.md-h1').length, h2: d.querySelectorAll('.md-h2').length, li: d.querySelectorAll('.md-li').length,
      num: d.querySelectorAll('.md-num').length, nested: [...d.querySelectorAll('.md-li')].filter(l => +(l.style.getPropertyValue('--ind') || 0) > 0).length,
      quote: d.querySelectorAll('.md-quote, .md-bq').length, hr: d.querySelectorAll('.md-hr').length,
      checks: [...d.querySelectorAll('.md-check')].map(c => c.getAttribute('aria-disabled')),
      links: [...d.querySelectorAll('[role=link]')].map(l => [l.className.split(' ')[0], (l.innerText || '').slice(0, 30), l.tabIndex, l.dataset.href || '']),
      inertLinks: [...d.querySelectorAll('a.md-a')].filter(a => a.getAttribute('role') !== 'link').map(a => a.dataset.href || ''),
      imgs: [...host.querySelectorAll('img')].map(i => i.getAttribute('src')), videos: [...host.querySelectorAll('video')].map(v => v.getAttribute('src') || (v.querySelector('source') || {}).src),
      pops: [...host.querySelectorAll('button')].filter(b => /pop out/i.test(b.textContent)).length,
      widget, code, scripts: host.querySelectorAll('script').length });
  }
  return { docs: out, page: [document.scrollingElement.scrollWidth, document.scrollingElement.scrollHeight, innerWidth, innerHeight, devicePixelRatio, document.visibilityState],
           xss: window.__xss || 0 }; })()"""

SINKS = r"""(() => { if (window.__sinks) return true; window.__sinks = 1;
  // a copy is caught and cancelled: what would have been copied is kept, the system clipboard is not touched
  window.__copied = []; document.addEventListener('copy', e => { window.__copied.push(String(getSelection())); e.preventDefault(); }, true);
  // the HUD's host bridge, as a recording stand-in (pywebview is not in this browser): no native window is opened
  window.__host = []; window.pywebview = { api: { host: async (verb, rest) => { window.__host.push([verb, rest]); return 'ok (review stand-in)'; } } };
  window.__opened = []; const wo = window.open; window.open = (...a) => { window.__opened.push(String(a[0])); return null; };
  return true; })()"""


def fixture_picture():
    from PIL import Image, ImageDraw
    p = DEMOS / "fixture-picture.png"
    if not p.exists():
        im = Image.new("RGB", (480, 270), (238, 242, 236))
        d = ImageDraw.Draw(im)
        d.rectangle((24, 24, 220, 246), fill=(15, 107, 87))
        d.ellipse((260, 60, 420, 220), fill=(184, 92, 0))
        im.save(p)
    return p


def sha(p):
    return hashlib.sha256((REPO / p).read_bytes()).hexdigest().upper()


def body(said):
    """The text of a note as `read` prints it: between its first two --- lines."""
    lines = said.split("\n")
    marks = [i for i, l in enumerate(lines) if l == "---"]
    return "\n".join(lines[marks[0] + 1:marks[-1]]) if len(marks) >= 2 else None


class Review:
    def __init__(self, size, world, apply=True):
        self.size, self.world, self.rows, self.apply = size, world, [], apply
        self.out = DEMOS / f"{datetime.datetime.now():%Y-%m-%d-%H%M%S}-{size[0]}x{size[1]}{'' if apply else '-baseline'}"
        self.out.mkdir(parents=True, exist_ok=True)
        self.shots = 0
        fixture_picture()

    def record(self, jid, outcome, note, facts=None, shots=()):
        self.rows.append({"id": jid, "outcome": outcome, "note": note, "facts": facts or {}, "shots": list(shots)})
        print(f"  {outcome:8} {jid:22} {note[:220]}", flush=True)

    async def shot(self, name):
        self.shots += 1
        p = self.out / f"{self.shots:02d}-{name}.png"
        await self.win.shot(p)
        return p.name

    def do(self, line, who=WHO, ok=True):
        said = self.copy.do(line, who)
        if ok and re.search(r"(^|\n)(ERR|refused:)", said or ""):
            raise RuntimeError(f"{line[:80]!r} -> {said[:300]}")
        return said

    async def page(self, lens, who="alex", width=None):
        await self.win.p.call("Page.navigate", url=self.copy.url(lens, who))
        for _ in range(100):
            await asyncio.sleep(0.2)
            if await self.win.js("!!document.querySelector('#paint [data-key]')"):
                break
        await asyncio.sleep(1.5)
        await self.win.js("document.getElementById('hud-frost')?.remove()")
        await self.win.js(SINKS)
        if width:
            await self.win.js(f"(() => {{ const p = document.getElementById('paint'); p.style.width = '{width}px'; p.style.maxWidth = '{width}px'; return true; }})()")
            await asyncio.sleep(0.8)

    async def composer(self, hint):
        """A composer by its hint, pressed only where a press really lands on it: -> (x, y) or a reason it is not pressable."""
        return await self.win.js(f"""(() => {{ const t = [...document.querySelectorAll('textarea')].find(t => (t.placeholder || '').startsWith({json.dumps(hint)}) && t.getClientRects().length);
          if (!t) return 'no such composer drawn'; t.scrollIntoView({{block: 'nearest'}}); const r = t.getBoundingClientRect(), x = r.left + 20, y = r.top + Math.min(r.height / 2, 12);
          const at = document.elementFromPoint(x, y); if (at !== t && !t.contains(at)) return 'a press at its centre lands on ' + (at ? at.tagName + '.' + at.className : 'nothing') + ' at ' + [Math.round(x), Math.round(y)];
          return [x, y]; }})()""")

    async def focus_is(self, hint):
        return await self.win.js(f"(() => {{ const a = document.activeElement; return !!a && a.tagName === 'TEXTAREA' && (a.placeholder || '').startsWith({json.dumps(hint)}); }})()")

    def append(self, words):
        """A fixture line from the worker: read the chat first, so the line is never held for lines others added."""
        self.do(f"read {self.chat}")
        return self.do(f"do append {self.chat} line={H.q(words)} to=alex")

    # ---- setup on the copy --------------------------------------------------------------------------------------
    def setup(self):
        self.copy = H.Copy(self.world)
        self.facts = {"world": self.world, "copy_session": self.copy.session, "copy_events_at_start": self.copy.at(),
                      "sources": {p: sha(p) for p in SOURCES}, "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()}
        texts = {}
        for item in stage.PATCHES:
            said = self.do(f"read {item}", "jeff")
            texts[item] = body(said)
            if texts[item] is None:
                raise RuntimeError(f"could not read {item}'s text: {said[:200]}")
        self.before = texts
        self.facts["lens_before"] = {i: hashlib.sha256(t.encode()).hexdigest().upper() for i, t in texts.items()}
        stage.prepare(texts)                        # preflight: both OLD passages exactly once, before either write
        self.facts["preflight"] = {stage.PATCHES[i]["name"]: texts[i].count(stage.PATCHES[i]["old"]) for i in texts}
        self.facts["applied"] = self.apply
        for item, h in (stage.PATCHES.items() if self.apply else []):
            self.do(f"look {item}", "jeff")
            said = self.do(f"do replace {item} old={H.q(h['old'])} new={H.q(h['new'])}", "jeff")
            self.facts.setdefault("apply", {})[h["name"]] = said.splitlines()[0][:160]
        after = {i: body(self.do(f"read {i}", "jeff")) for i in stage.PATCHES}
        want = stage.prepare(texts) if self.apply else texts
        self.facts["applied_exact"] = {stage.PATCHES[i]["name"]: after[i] == want[i] for i in after}
        if not all(self.facts["applied_exact"].values()):
            raise RuntimeError(f"applied text differs from the staged result: {self.facts['applied_exact']}")
        # the disposable feed, and the fixture message in it
        self.do("look f5189")
        made = self.do('do create f5189 kind=chat title="Markdown review fixtures (disposable copy only)" with="alex,worker-a7629"')
        self.chat = re.search(r"created (a\d+)", made).group(1)
        self.do(f"read {self.chat}")
        self.do(f"do append {self.chat} line={H.q(FIXTURE)} to=alex")
        self.facts["chat"] = self.chat
        self.facts["conversation_history_before"] = self.conversation_events()

    def conversation_events(self):
        """The events `history a5080` lists (its own lines that start with an event id; never the 'since your last look' header)."""
        return [l.strip() for l in self.do("history a5080", "jeff").splitlines() if re.match(r"e\d+ ", l.strip())]

    def undo(self):
        now = {i: body(self.do(f"read {i}", "jeff")) for i in stage.PATCHES}
        if self.apply:
            stage.prepare(now, reverse=True)
        for item, h in (stage.PATCHES.items() if self.apply else []):
            self.do(f"look {item}", "jeff")
            self.do(f"do replace {item} old={H.q(h['new'])} new={H.q(h['old'])}", "jeff")
        back = {i: body(self.do(f"read {i}", "jeff")) for i in stage.PATCHES}
        same = {stage.PATCHES[i]["name"]: back[i] == self.before[i] for i in back}
        new = [l for l in self.conversation_events() if l not in self.facts["conversation_history_before"]]
        sends = [l for l in new if re.search(r"\b(append|comment|reply) a5080\b|\bline=", l)]
        ok = all(same.values()) and not sends
        self.record("apply-undo", "pass" if ok else "fail",
                    f"preflight counts {self.facts['preflight']}; applied exactly as staged {self.facts['applied_exact']}; reversed to the original text {same}; "
                    f"lines or comments added to the copy's Conversation: {sends or 'none'}; other events naming it (not sends): {[l[:110] for l in new if l not in sends]}",
                    {"apply": self.facts.get("apply"), "conversation_new": new})

    # ---- the journeys -------------------------------------------------------------------------------------------
    async def formats(self, lens):
        await self.page(lens)
        m = await self.win.js(MEASURE)
        docs = [d for d in m["docs"] if "Review heading one" in d["text"]]
        if not docs:
            self.record(f"formats-{lens}", "fail", f"the fixture message did not draw as a read Markdown document ({len(m['docs'])} docs)", m, [await self.shot(f"formats-{lens}")])
            return None
        d, bad = docs[0], []
        if d["failed"]: bad.append("drawn as the plain-text fallback")
        if d["h1"] < 1 or d["h2"] < 1: bad.append(f"headings h1 {d['h1']} h2 {d['h2']}")
        if d["li"] < 4 or d["num"] < 2 or d["nested"] < 1: bad.append(f"list items: bullets/tasks {d['li']}, numbered {d['num']}, nested {d['nested']}")
        if not d["checks"] or any(c != "true" for c in d["checks"]): bad.append(f"task boxes {d['checks']}")
        if not any(w["ox"] in ("auto", "scroll") for w in d["widget"]): bad.append(f"table widget overflow {d['widget']}")
        if d["code"] and any(c["ws"] not in ("pre-wrap", "break-spaces") for c in d["code"]): bad.append(f"code white-space {d['code']}")
        if len([i for i in d["imgs"] if i and "fixture-picture" in i]) != 1: bad.append(f"picture drawn {d['imgs']}")
        if len([v for v in d["videos"] if v and "writing-demo" in v]) != 1: bad.append(f"film drawn {d['videos']}")
        if d["pops"] < 1: bad.append("no Pop out")
        if d["scripts"] or m["xss"]: bad.append(f"script ran or kept: scripts {d['scripts']} xss {m['xss']}")
        if any("javascript" in l[3] for l in d["links"]): bad.append("the javascript: link is a live link")
        self.record(f"formats-{lens}", "pass" if not bad else "fail",
                    (f"problems: {bad}; " if bad else "") + f"h1 {d['h1']} h2 {d['h2']} bullets/tasks {d['li']} numbered {d['num']} nested {d['nested']} quote {d['quote']} rule {d['hr']} task boxes aria-disabled {d['checks']}; "
                    f"links {[l[:3] for l in d['links']]}; inert {d['inertLinks']}; pictures {len(d['imgs'])}, films {len(d['videos'])}, Pop out {d['pops']}; table widgets {d['widget']}",
                    {"doc": d, "page": m["page"]}, [await self.shot(f"formats-{lens}")])
        return d

    async def widths(self, lens):
        rows = []
        for w in (320, 420, 600):
            await self.page(lens, width=w)
            m = await self.win.js(MEASURE)
            docs = [d for d in m["docs"] if "Review heading one" in d["text"]]
            if not docs:
                rows.append({"width": w, "problem": "no fixture document"})
                continue
            d = docs[0]
            rows.append({"width": w, "doc": [d["rect"][2], d["sw"], d["cw"]], "part": [d["partSw"], d["partCw"]], "widgets": [(x["sw"], x["cw"], x["ox"]) for x in d["widget"]],
                         "code": [(c["sw"], c["cw"]) for c in d["code"]], "page": m["page"][:4],
                         "problem": ("document overflows" if d["sw"] > d["cw"] + 1 else "") + ("; part overflows" if d["partSw"] > d["partCw"] + 1 else "")
                         + ("; whole page scrolls sideways" if m["page"][0] > m["page"][2] + 1 else "") + ("; code does not wrap" if any(c["sw"] > c["cw"] + 1 for c in d["code"]) else "")})
            rows[-1]["shot"] = await self.shot(f"width-{lens}-{w}")
        bad = [r for r in rows if r.get("problem")]
        self.record(f"widths-{lens}", "pass" if not bad else "fail",
                    "; ".join(f"{r['width']}px: doc {r.get('doc')} widgets {r.get('widgets')} {r.get('problem') or 'contained'}" for r in rows), {"rows": rows}, [r.get("shot") for r in rows if r.get("shot")])

    async def hud(self):
        await self.page("home-base")
        m = await self.win.js(MEASURE)
        docs = [d for d in m["docs"] if "Review heading one" in d["text"]]
        page = m["page"]
        bad = []
        if page[0] > page[2] + 1 or page[1] > page[3] + 1: bad.append(f"the home base page scrolls {page[:4]}")
        if not docs: bad.append("the fixture is not drawn in the HUD chat")
        for d in docs:
            if d["sw"] > d["cw"] + 1 or d["partSw"] > d["partCw"] + 1: bad.append(f"{d['key']} overflows {d['sw']}>{d['cw']}")
        self.facts["viewport"] = page[2:6]
        self.record("full-hud", "pass" if not bad else "fail", (f"problems: {bad}; " if bad else "") +
                    f"page {page[2]}x{page[3]} CSS at DPR {page[4]}, {page[5]}; chat document {docs[0]['rect'] if docs else None} widgets {docs[0]['widget'] if docs else None}",
                    {"docs": docs, "page": page}, [await self.shot("full-hud")])

    async def keyboard_link(self):
        """Tab reaches the named link with real keys, Enter opens it with `view`, and no chat About is attached."""
        await self.page("jeff-chat")
        before = self.do("read a5082", "alex")
        # put the focus just before the fixture document, then Tab with posted keys until a link has it
        await self.win.js("(() => { const d = [...document.querySelectorAll('.md-doc.md-read')].find(d => d.innerText.includes('Review heading one')); d.scrollIntoView({block:'center'}); "
                          "const s = document.createElement('span'); s.tabIndex = 0; s.id = '__start'; d.before(s); s.focus(); return true; })()")
        seen = None
        for i in range(12):
            await self.win.key("Tab")
            await asyncio.sleep(0.15)
            seen = await self.win.js("(() => { const a = document.activeElement; return a ? [a.getAttribute('role'), a.className.split(' ')[0], (a.innerText || '').slice(0, 40), a.dataset.href || ''] : null; })()")
            if seen and seen[0] == "link" and "md-wl" in seen[1]:
                break
        if not seen or seen[0] != "link":
            self.record("keyboard-link", "fail", f"Tab never reached a named link; last focus {seen}", {}, [await self.shot("keyboard-link")])
            return
        await self.win.key("Enter")
        await asyncio.sleep(1.5)
        view = self.do("find prop:role=home-view,prop:actor=alex", "alex")
        after = self.do("read a5082", "alex")
        topic_before = re.search(r"topic=(\S*)", before), re.search(r"topic=(\S*)", after)
        opened = "a5202" in view
        same_topic = (topic_before[0].group(1) if topic_before[0] else "") == (topic_before[1].group(1) if topic_before[1] else "")
        self.record("keyboard-link", "pass" if opened and same_topic else "fail",
                    f"focus by Tab: {seen}; Enter -> home-view {'shows a5202' if opened else 'did not change to a5202'}; draft topic before/after "
                    f"{[t.group(1) if t else '' for t in topic_before]} (no About attached: {same_topic}); external opens {await self.win.js('window.__opened')}",
                    {"view": view[:400]}, [await self.shot("keyboard-link")])

    async def selection_copy(self):
        """A pointer drag selects words across a link (DevTools input, Chromium's own path), does not follow it; Ctrl+C copies them (caught, cancelled)."""
        await self.page("jeff-chat")
        view0 = self.do("find prop:role=home-view,prop:actor=alex", "alex")
        # from the word 'Plain' to past the named link, in the same line: a range's own rectangles (text beside bold words has no leaf of its own)
        pts = await self.win.js("""(() => { const d = [...document.querySelectorAll('.md-doc.md-read')].find(d => d.innerText.includes('Review heading one')); if (!d) return null;
          const l = [...d.querySelectorAll('[role=link]')].find(l => l.className.includes('md-wl')); if (!l) return null;
          l.scrollIntoView({block: 'center'});
          const w = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode()) && !n.data.includes('Plain')); if (!n) return null;
          const r = document.createRange(), i = n.data.indexOf('Plain'); r.setStart(n, i); r.setEnd(n, i + 1); const a = r.getBoundingClientRect(), b = l.getBoundingClientRect();
          return [[a.left + 1, a.top + a.height / 2], [b.right + 30, b.top + b.height / 2]]; })()""")
        a, b = pts if pts else (None, None)
        if not a or not b:
            self.record("selection-copy", "blocked", f"no words or link to select across ({a}, {b})", {}, [await self.shot("selection")])
            return
        await self.win.drag(a[0], a[1], b[0], b[1], devtools=True)
        await asyncio.sleep(0.3)
        sel = await self.win.js("String(getSelection())")
        await self.win.p.call("Input.dispatchKeyEvent", type="keyDown", key="c", code="KeyC", windowsVirtualKeyCode=67, modifiers=2, commands=["copy"])
        await self.win.p.call("Input.dispatchKeyEvent", type="keyUp", key="c", code="KeyC", windowsVirtualKeyCode=67, modifiers=2)
        await asyncio.sleep(0.3)
        copied = await self.win.js("window.__copied")
        shot1 = await self.shot("selection")
        # a drag inside the link's own words: its press and release are both on the link, so a click lands on it with words selected
        lk = await self.win.js("(() => { const d = [...document.querySelectorAll('.md-doc.md-read')].find(d => d.innerText.includes('Review heading one')); const l = d && [...d.querySelectorAll('[role=link]')].find(l => l.className.includes('md-wl')); if (!l) return null; const r = l.getBoundingClientRect(); return [r.left + 2, r.right - 2, r.top + r.height / 2]; })()")
        await self.win.drag(lk[0], lk[2], lk[1], lk[2], devtools=True)
        await asyncio.sleep(0.3)
        sel_link = await self.win.js("String(getSelection())")
        await asyncio.sleep(1.2)
        view1 = self.do("find prop:role=home-view,prop:actor=alex", "alex")
        followed = view0 != view1
        ok = len(sel) > 10 and bool(copied) and copied[-1] == sel and len(sel_link) > 0 and not followed
        self.record("selection-copy", "pass" if ok else "fail",
                    f"drag across words and the named link selected {len(sel)} chars {sel[:60]!r}; Ctrl+C copied {[c[:60] for c in copied or []]} (caught and cancelled: system clipboard untouched); "
                    f"a drag inside the link's words selected {sel_link!r} and the link was {'FOLLOWED' if followed else 'not followed'}", {"selected": sel, "copied": copied, "in_link": sel_link},
                    [shot1, await self.shot("selection-in-link")])

    async def inert_task(self):
        await self.page("jeff-chat")
        hist0 = self.do(f"history {self.chat}")
        box = await self.win.js("(() => { const c = [...document.querySelectorAll('.md-doc.md-read .md-check')][0]; if (!c) return null; c.scrollIntoView({block:'center'}); const r = c.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, c.getAttribute('aria-disabled'), c.className]; })()")
        if not box:
            self.record("inert-task", "fail", "no task box drawn", {}, [await self.shot("inert-task")])
            return
        await self.win.click(box[0], box[1])
        await asyncio.sleep(1.2)
        hist1 = self.do(f"history {self.chat}")
        after = await self.win.js("(() => { const c = [...document.querySelectorAll('.md-doc.md-read .md-check')][0]; return c ? c.className : null; })()")
        ev = lambda h: [l.strip() for l in h.splitlines() if re.match(r"e\d+ ", l.strip())]
        new = [l for l in ev(hist1) if l not in ev(hist0)]
        ok = not new and box[2] == "true" and after == box[3]
        self.record("inert-task", "pass" if ok else "fail", f"aria-disabled {box[2]}; a real click: new events on the message's chat {new}; box {box[3]} -> {after}", {}, [await self.shot("inert-task")])

    async def media(self):
        await self.page("jeff-chat")
        film = await self.win.js("""(async () => { const v = [...document.querySelectorAll('video')].find(v => (v.currentSrc || v.src || '').includes('writing-demo')); if (!v) return null;
          v.muted = true; v.scrollIntoView({block:'center'}); if (v.readyState < 1) await new Promise(r => { v.addEventListener('loadedmetadata', r, {once:true}); setTimeout(r, 6000); });
          const t0 = v.currentTime; try { await v.play(); } catch (e) { return {error: String(e), ready: v.readyState}; }
          await new Promise(r => setTimeout(r, 1500)); const t1 = v.currentTime; v.pause();
          return {src: v.currentSrc, duration: v.duration, ready: v.readyState, t0, t1, muted: v.muted}; })()""")
        pop = await self.win.js("(() => { const b = [...document.querySelectorAll('.md-doc.md-read ~ * button, [data-key] button')].find(b => /pop out/i.test(b.textContent) && b.closest('[data-key]') && b.closest('[data-key]').innerText.includes('Review heading one')); if (!b) return null; b.scrollIntoView({block:'center'}); const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, b.className, b.previousElementSibling ? b.previousElementSibling.tagName : '']; })()")
        host, player = None, None
        if pop:
            await self.win.click(pop[0], pop[1])
            await asyncio.sleep(1.5)
            host = await self.win.js("window.__host")
            player = self.do("find prop:role=media-player,prop:actor=alex", "alex")
        bad = []
        if not film or film.get("error") or not (film.get("t1", 0) > film.get("t0", 0)): bad.append(f"film did not play {film}")
        if not pop: bad.append("no Pop out on the fixture")
        elif not host or not any(h[0] == "window" and "media-player" in h[1] for h in host): bad.append(f"Pop out asked the host {host}")
        self.record("media", "pass" if not bad else "fail", (f"problems: {bad}; " if bad else "") +
                    f"film {film}; Pop out {pop[2:] if pop else None} -> host (recording stand-in) {host}; media-player note: {(player or '')[:160]!r}",
                    {"film": film, "host": host, "player": player}, [await self.shot("media")])

    async def draft_through_update(self, lens="home-base"):
        """Unsent words, a caret not at the end and an explicit removable context survive an incoming message and a repaint."""
        jid = "draft-update" if lens == "home-base" else f"draft-update-{lens}"
        await self.page(lens)
        return await self._draft(jid)

    async def _draft(self, jid):
        self.do("look a5082", "alex")
        self.do("do prop a5082 topic=a5202 reply_to= quote= reply_in= reply_thread=", "alex")
        await asyncio.sleep(1.5)
        box = await self.composer("Write to JEFF")
        if isinstance(box, str):
            self.record(jid,"blocked", f"the HUD's JEFF composer is not pressable: {box}", {}, [await self.shot("draft-update")])
            self.do("look a5082", "alex"); self.do("do prop a5082 topic=", "alex")
            return
        await self.win.click(box[0], box[1])
        await asyncio.sleep(0.3)
        if not await self.focus_is("Write to JEFF"):
            self.record(jid,"blocked", "a press on the composer did not focus it; nothing typed", {}, [await self.shot("draft-update")])
            self.do("look a5082", "alex"); self.do("do prop a5082 topic=", "alex")
            return
        await self.win.type("unsent review words")
        for _ in range(6):
            await self.win.key("ArrowLeft")
        await asyncio.sleep(0.3)
        await self.win.js("(() => { window.__box = document.activeElement; return true; })()")
        chip = ("[...document.querySelectorAll('[data-key$=\"/chip/label\"], [data-key$=\"/chip\"]')].filter(e => e.getClientRects().length).map(e => (e.innerText || '').replace(/\\s+/g, ' ').slice(0, 60))")
        st0 = await self.win.js(f"(() => {{ const t = document.activeElement; return [t.tagName, t.value, t.selectionStart, t.selectionEnd, {chip}]; }})()")
        d0 = self.do("read a5082", "alex").splitlines()[1][:200]
        self.append("## Incoming update\n- arrives while you type")
        await asyncio.sleep(3.0)
        st1 = await self.win.js(f"(() => {{ const t = document.activeElement; return [t.tagName, t.value, t.selectionStart, t.selectionEnd, {chip}, t === window.__box, document.body.innerText.includes('arrives while you type')]; }})()")
        d1 = self.do("read a5082", "alex").splitlines()[1][:200]
        ok = st1[1] == st0[1] and st1[2] == st0[2] and st1[5] and st1[4] == st0[4] and bool(st0[4]) and st1[6] and st0[2] < len(st0[1] or "")
        self.record(jid,"pass" if ok else "fail", f"before {st0}; after an incoming Markdown message {st1} (same element, words, caret, focus, context chip text, message shown); "
                    f"draft note before {d0!r}, after {d1!r}", {"before": st0, "after": st1, "draft": [d0, d1]}, [await self.shot("draft-update")])
        # leave the draft as it was: no topic, nothing unsent sent
        await self.win.js("(() => { const t = window.__box; if (t) { t.value = ''; t.dispatchEvent(new Event('input', {bubbles:true})); t.blur(); } return true; })()")
        self.do("look a5082", "alex")
        self.do("do prop a5082 topic=", "alex")

    async def reply_jeff_chat(self):
        """Answer on the fixture in the HUD chat: the reply goes to the disposable chat (its original place), checked before Enter."""
        await self.page("home-base")
        ans = await self.win.js("(() => { const d = [...document.querySelectorAll('.md-doc.md-read')].find(d => d.innerText.includes('Review heading one')); if (!d) return null; "
                                "let b = d.closest('[data-key]'); while (b && !b.querySelector('[data-key$=\"/answer\"]')) b = b.parentElement; const a = b && b.querySelector('[data-key$=\"/answer\"]'); if (!a) return null; a.scrollIntoView({block:'center'}); const r = a.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        if not ans:
            self.record("reply-hud", "blocked", "no Answer on the fixture", {}, [await self.shot("reply-hud")])
            return
        await self.win.click(ans[0], ans[1])
        await asyncio.sleep(1.5)
        draft = self.do("read a5082", "alex")
        where = re.search(r"reply_in=(\S+)", draft)
        if not where or where.group(1) != self.chat:
            self.record("reply-hud", "fail", f"Answer did not aim at the disposable chat: {draft[:200]!r}; nothing sent", {}, [await self.shot("reply-hud")])
            return
        box = await self.composer("Write to JEFF")
        if isinstance(box, str):
            self.record("reply-hud", "blocked", f"Answer aimed the draft at {where.group(1)} (the disposable chat), but the HUD's composer is not pressable: {box}; nothing sent",
                        {}, [await self.shot("reply-hud")])
            self.do("look a5082", "alex"); self.do("do prop a5082 reply_to= quote= reply_in= reply_thread= reply_kind=", "alex")
            return
        await self.win.click(box[0], box[1])
        await asyncio.sleep(0.3)
        if not await self.focus_is("Write to JEFF"):
            self.record("reply-hud", "blocked", "a press on the composer did not focus it; nothing typed", {}, [await self.shot("reply-hud")])
            return
        await self.win.type("review reply in place")
        await self.win.key("Enter")
        await asyncio.sleep(2.0)
        lines = self.do(f"rows lines:{self.chat}")
        ok = "review reply in place" in lines
        self.record("reply-hud", "pass" if ok else "fail", f"draft aimed at {where.group(1)} (the disposable chat) before Enter; the reply {'is' if ok else 'is not'} a line there", {"rows": lines[-600:]}, [await self.shot("reply-hud")])

    async def reply_conversation(self):
        await self.page("conversation")
        fold = await self.win.js("(() => { const d = [...document.querySelectorAll('.md-doc.md-read')].find(d => d.innerText.includes('Review heading one')); if (!d) return null; let m = d.closest('[data-key]'); "
                                 "while (m && !m.querySelector('[data-key$=\"/answer\"]')) m = m.parentElement; const f = m && m.querySelector('[data-key$=\"/answer\"]'); if (!f) return null; f.scrollIntoView({block:'center'}); const h = f.querySelector('.l-fold-handle, [data-fold], summary') || f; const r = h.getBoundingClientRect(); return [r.left + 20, r.top + 10]; })()")
        if not fold:
            self.record("reply-conversation", "blocked", "no Reply here on the fixture", {}, [await self.shot("reply-conversation")])
            return
        await self.win.click(fold[0], fold[1])
        await asyncio.sleep(1.0)
        box = await self.win.js("(() => { const t = [...document.querySelectorAll('textarea')].find(t => (t.placeholder || '').startsWith('Reply in this conversation') && t.getClientRects().length); if (!t) return null; t.scrollIntoView({block:'center'}); const r = t.getBoundingClientRect(); return [r.left + 20, r.top + r.height / 2]; })()")
        if not box:
            self.record("reply-conversation", "fail", "Reply here opened no composer", {}, [await self.shot("reply-conversation")])
            return
        await self.win.click(box[0], box[1])
        await asyncio.sleep(0.3)
        if not await self.focus_is("Reply in this conversation"):
            self.record("reply-conversation", "blocked", "a press on Reply here's composer did not focus it; nothing typed", {}, [await self.shot("reply-conversation")])
            return
        await self.win.type("conversation reply in place")
        await self.win.key("Enter")
        await asyncio.sleep(2.0)
        lines = self.do(f"rows lines:{self.chat}")
        ok = "conversation reply in place" in lines
        self.record("reply-conversation", "pass" if ok else "fail", f"Reply here (appends to the line's own chat, the disposable one) {'arrived' if ok else 'did not arrive'}", {"rows": lines[-600:]}, [await self.shot("reply-conversation")])

    async def fallback(self):
        """Malformed Markdown, and a drawing made to fail in the page, keep readable words, the media and a working composer."""
        await self.page("jeff-chat")
        await self.win.js("(() => { const M = window.Markdown, d = M.draw; M.draw = function (root, src, ...a) { if (String(src).includes('FAILME')) throw new Error('injected review failure'); return d.call(this, root, src, ...a); }; return true; })()")
        # a plain line first: does this page paint new lines at all right now (Markdown or not)?
        self.append("plain probe line PLAINPROBE")
        t0, plain = time.time(), None
        for _ in range(40):
            await asyncio.sleep(0.25)
            if await self.win.js("document.body.innerText.includes('PLAINPROBE')"):
                plain = round(time.time() - t0, 2)
                break
        self.facts["plain_probe_painted_after_s"] = plain
        said = [self.append(MALFORMED), self.append("FAILME words stay readable " + FILM)]
        self.facts["fallback_appends"] = [s.splitlines()[:3] for s in said]
        live = False
        for _ in range(40):
            await asyncio.sleep(0.25)
            if await self.win.js("document.body.innerText.includes('MALFORMED-MARK') && document.body.innerText.includes('FAILME')"):
                live = True
                break
        self.facts["fallback_painted_live"] = live
        if not live:
            # recorded as a finding, then looked at again on a fresh page with the same injected failure
            self.facts["fallback_missed_page"] = await self.win.js("({events: (window.__pt && window.__pt.errors) || [], visible: document.visibilityState, text: document.body.innerText.slice(-200)})")
            # why: the page's scene fetches (a refresh waits on the one before it), and does a fresh one answer at all?
            self.facts["fallback_missed_fetches"] = await self.win.js(r"""(async () => {
              const now = performance.now(), scenes = performance.getEntriesByType('resource').filter(e => /\/api\/scene|\/door\/stream/.test(e.name));
              const recent = scenes.slice(-6).map(e => [e.name.split('?')[0], Math.round(e.startTime), Math.round(e.responseEnd), Math.round(e.duration)]);
              const ctl = new AbortController(), t0 = performance.now(); setTimeout(() => ctl.abort(), 5000);
              let fresh; try { const r = await fetch(location.origin + '/api/scene?session=' + new URLSearchParams(location.search).get('session') + '&as=alex&lens=jeff-chat&view=painter&text=0', {signal: ctl.signal}); fresh = [r.status, Math.round(performance.now() - t0)]; } catch (e) { fresh = [String(e), Math.round(performance.now() - t0)]; }
              return {now: Math.round(now), scene_entries: scenes.length, recent, fresh}; })()""")
            # the same scene asked from outside the browser: is it the server or the page that waits?
            import urllib.request
            t0 = time.time()
            try:
                u = f"{self.copy.base}/api/scene?session={self.copy.session}&as=alex&lens=jeff-chat&view=painter&text=0"
                with urllib.request.urlopen(u, timeout=8) as f:
                    self.facts["fallback_missed_server"] = [f.status, round(time.time() - t0, 2)]
            except Exception as e:
                self.facts["fallback_missed_server"] = [repr(e)[:120], round(time.time() - t0, 2)]
            self.facts["fallback_missed_media"] = await self.win.js("[...document.querySelectorAll('video, img')].filter(m => /\\/media\\//.test(m.currentSrc || m.src || '')).map(m => [m.tagName, (m.currentSrc || m.src).split('/').pop(), m.readyState, m.networkState, m.preload || ''])")
            missed = await self.shot("fallback-not-painted")
            await self.page("jeff-chat")
            await self.win.js("(() => { const M = window.Markdown, d = M.draw; M.draw = function (root, src, ...a) { if (String(src).includes('FAILME')) throw new Error('injected review failure'); return d.call(this, root, src, ...a); }; return true; })()")
            self.facts["fallback_missed_shot"] = missed
            self.append("FAILME again, after a reload " + FILM)
            await asyncio.sleep(4.0)
        await asyncio.sleep(0.8)
        st = await self.win.js("""(() => {
          const mal = [...document.querySelectorAll('.md-doc, [data-md-failed]')].find(e => (e.innerText || e.textContent || '').includes('MALFORMED-MARK'));
          const fail = [...document.querySelectorAll('[data-md-failed="1"]')].find(e => e.textContent.includes('FAILME'));
          const host = fail && fail.closest('[data-key]');
          const film = host && host.parentElement && [...host.parentElement.querySelectorAll('video')].some(v => (v.currentSrc || v.src || '').includes('writing-demo'));
          const t = [...document.querySelectorAll('textarea')].find(t => (t.placeholder || '').startsWith('Write to JEFF'));
          return { errors: ((window.__pt && window.__pt.errors) || []).slice(-4), lastLines: [...document.querySelectorAll('[data-key*="/said"], [data-key*="/everything/"]')].slice(-3).map(e => (e.innerText || '').slice(0, 80)), malformed: mal ? (mal.dataset.mdFailed === '1' ? 'plain fallback: ' : 'drawn: ') + (mal.innerText || mal.textContent).slice(0, 120) : null, failedShown: fail ? fail.textContent.slice(0, 80) : null, filmBeside: !!film, composer: !!t, xss: window.__xss || 0 }; })()""")
        ok = live and st["malformed"] and "unclosed fence" in st["malformed"] and st["failedShown"] and st["composer"] and not st["xss"]
        self.record("fallback", "pass" if ok else "fail", f"a plain probe line painted after {self.facts['plain_probe_painted_after_s']} s; " + ("" if live else f"THE TWO NEW LINES DID NOT PAINT LIVE within 10 s (page then: {self.facts.get('fallback_missed_page')}; its scene fetches: {self.facts.get('fallback_missed_fetches')}; the same from outside the browser: {self.facts.get('fallback_missed_server')}; media: {self.facts.get('fallback_missed_media')}); after a reload: ")
                    + f"{st}; appends: {self.facts['fallback_appends']}", st, [s for s in (self.facts.get("fallback_missed_shot"), await self.shot("fallback")) if s])

    async def run(self, only=None):
        H.SIZE = self.size
        self.win, self.copy = H.Window(False), None
        guard = None
        try:
            self.setup()
            await self.win.open(self.copy.url("jeff-chat", "alex"))
            await asyncio.sleep(2)
            steps = [("formats-jeff-chat", lambda: self.formats("jeff-chat")), ("formats-conversation", lambda: self.formats("conversation")),
                     ("full-hud", self.hud), ("widths-jeff-chat", lambda: self.widths("jeff-chat")), ("widths-conversation", lambda: self.widths("conversation")),
                     ("keyboard-link", self.keyboard_link), ("selection-copy", self.selection_copy), ("inert-task", self.inert_task), ("media", self.media),
                     ("draft-update", self.draft_through_update), ("draft-update-jeff-chat", lambda: self.draft_through_update("jeff-chat")),("reply-hud", self.reply_jeff_chat), ("reply-conversation", self.reply_conversation), ("fallback", self.fallback)]
            for jid, fn in steps:
                if only and jid not in only:
                    continue
                try:
                    await fn()
                except Exception as e:
                    self.record(jid, "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-1500:]}, [await self.shot(jid + "-error")])
            self.undo()
        finally:
            guard = await self.win.close()
            if self.copy:
                self.copy.close()
        self.facts["guard"] = guard
        (self.out / "report.json").write_text(json.dumps({"facts": self.facts, "rows": self.rows}, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
        md = [f"# Markdown chat acceptance, {self.size[0]}x{self.size[1]}", "", f"guard: {guard}", f"viewport: {self.facts.get('viewport')}", "",
              "| journey | outcome | note | shots |", "|---|---|---|---|"]
        md += [f"| {r['id']} | {r['outcome']} | {r['note'].replace('|', '/')[:500]} | {', '.join(r['shots'])} |" for r in self.rows]
        (self.out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print("guard:", guard)
        print("report:", self.out / "report.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", action="store_true")
    ap.add_argument("--world", default="frontier-try")
    ap.add_argument("--only", type=lambda s: s.split(","), default=None)
    ap.add_argument("--no-apply", action="store_true", help="the same journeys on the copy's lenses as they are (a baseline: marks, not markdown)")
    a = ap.parse_args()
    asyncio.run(Review((1280, 800) if a.small else (2560, 1440), a.world, apply=not a.no_apply).run(a.only))
