"""tabs_review.py (a7544): acceptance of the landed Agora viewer tabs (3cc2796) with JEFF's staged world half
(a7439/a7441, patches.json), in the guarded hidden Edge window on hud_playtest's DISPOSABLE copy of a world. Never the
live world, never Alex's screen, no Conversation send, no web, file or account data.

    python research/window-lab/browsing/tabs/review/tabs_review.py [--small] [--probe] [--only a,b]

The copy is staged by world.apply_copy: every old passage read from the copy and preflighted (stage.prepare) before
the first `do replace`, then `do browse <alex's viewer> action=init` as alex. Input is Windows messages to the sandbox
window. Each journey records ran/pass/fail/blocked with facts and shots under
research/window-lab/demos/tabs-review/<time>-<size>/ (report.json, report.md).
"""
import argparse
import asyncio
import datetime
import json
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
import hud_playtest as pt  # noqa: E402
import tabs_world as W  # noqa: E402

DEMOS = Path(r"C:/Projects/Agora4/research/window-lab/demos/tabs-review")
ME = "worker-a7544"

HELP = r"""(() => { if (window.__tr) return 'kept';
  const vis = e => !!e && e.isConnected && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden' && !e.closest('[hidden]');
  const R = e => { const b = e.getBoundingClientRect(); return [Math.round(b.left*10)/10, Math.round(b.top*10)/10, Math.round(b.width*10)/10, Math.round(b.height*10)/10]; };
  const viewer = () => [...document.querySelectorAll('#paint [data-key]')].filter(e => /(^|\/)lens:home-viewer(\/|$)/.test(e.dataset.key) && vis(e)).sort((a, b) => a.dataset.key.length - b.dataset.key.length)[0] || null;
  const leaf = (words, scope) => [...(scope || document).querySelectorAll('[data-key]')].filter(vis).find(e => !e.querySelector('[data-key]') && e.textContent.trim() === words) || null;
  const leaves = (words, scope) => [...(scope || document).querySelectorAll('[data-key]')].filter(vis).filter(e => !e.querySelector('[data-key]') && e.textContent.trim() === words);
  const hit = e => { if (!e) return null; const b = e.getBoundingClientRect(), x = b.left + b.width / 2, y = b.top + b.height / 2, at = document.elementFromPoint(x, y);
    return { x, y, ok: !!at && (e === at || e.contains(at) || at.contains(e)), at: at ? at.tagName + '.' + String(at.className).split(' ')[0] + ' ' + ((at.closest('[data-key]') || {}).dataset || {}).key : 'nothing' }; };
  const page = () => { const se = document.scrollingElement; return { vis: document.visibilityState, iw: innerWidth, ih: innerHeight, dpr: devicePixelRatio, sw: se.scrollWidth, sh: se.scrollHeight, sx: se.scrollLeft, sy: se.scrollTop }; };
  const bar = () => { const v = viewer(); if (!v) return null; return [...v.querySelectorAll('[data-key]')].filter(vis).filter(e => !e.querySelector('[data-key]') && /\/bar\//.test(e.dataset.key)).map(e => e.textContent.trim()).filter(Boolean); };
  const heading = () => { const v = viewer(); const h = v && [...v.querySelectorAll('[data-key]')].filter(vis).find(e => /\/head\/title$/.test(e.dataset.key)); return h ? h.textContent.trim() : null; };
  const scrollers = () => { const v = viewer(); return v ? [...v.querySelectorAll('[data-scroll]')].filter(vis).filter(e => e.dataset.scroll !== 'none' && e.scrollHeight > e.clientHeight + 4).map(e => ({ key: e.dataset.key, top: Math.round(e.scrollTop), sh: e.scrollHeight, ch: e.clientHeight, scope: (e.closest('[data-remember]') || {dataset: {}}).dataset.remember || '' })) : []; };
  const menu = () => { const m = document.getElementById('menu-pop'); return m && vis(m) ? [...m.querySelectorAll('button')].map(b => b.textContent) : null; };
  const floats = () => [...document.querySelectorAll('.l-float')].map(f => ({ key: f.dataset.key, folded: f.dataset.folded || '', r: R(f), open: [...f.children].filter(c => c.tagName !== 'BUTTON').some(vis) }));
  const reading = () => Object.keys(localStorage).filter(k => k.startsWith('lens-reading:')).map(k => [k, (JSON.parse(localStorage.getItem(k) || '[]')).length]);
  window.__tr = { vis, R, viewer, leaf, leaves, hit, page, bar, heading, scrollers, menu, floats, reading };
  return 'installed'; })()"""

# a reviewer's candidate world fixes (old, new) in home-viewer, applied only with --candidate, never part of the staged bytes
CANDIDATES = {"menu-role": ("      menu : column\n        measure 40ch\n", "      menu : column\n        role searchdrop\n        measure 40ch\n")}

CHAT_TA ="[...document.querySelectorAll('textarea')].find(e => __tr.vis(e) && e.closest('[data-key*=\"lens:jeff-chat\"]'))"


def props_of(line):
    """key=value pairs of a find/examine line (values without spaces; page_name and label may be cut, used only as hints)."""
    # everything after the title (a page name may itself hold ' · ', as "Claude · 5 hours" does: a7544 ran it)
    return dict(re.findall(r"(\w+)=(\S*)", line.split(" · ", 1)[1] if " · " in line else line))


class Review:
    def __init__(self, win, copy, out, size):
        self.w, self.copy, self.out, self.size = win, copy, out, size
        self.rows, self.shots = [], 0
        self.vid = None
        self.trail = []          # (journey, the chat draft after it)

    # ---- page --------------------------------------------------------------------------------------------------------
    async def js(self, src):
        await self.w.js(HELP)
        return await self.w.js(src)

    async def shot(self, name):
        self.shots += 1
        p = self.out / f"{self.shots:02d}-{name}.png"
        await self.w.shot(p)
        return p.name

    async def wait_for(self, src, secs=4.0):
        for _ in range(int(secs / 0.1)):
            try:
                if await self.js(src):
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.1)
        return False

    async def press(self, src, right=False, what=""):
        """Press the element src finds (a JS expression), at its centre, as a hand: -> the hit facts."""
        h = await self.js(f"(() => {{ const e = {src}; if (!e) return null; e.scrollIntoView({{block: 'nearest', inline: 'nearest'}}); return __tr.hit(e); }})()")
        if not h:
            raise LookupError(f"nothing to press: {what or src}")
        await self.w.click(h["x"], h["y"], right)
        await asyncio.sleep(0.9)
        return h

    async def choose(self, label):
        r = await self.js(f"(() => {{ const b = [...document.querySelectorAll('#menu-pop button')].find(b => b.textContent === {json.dumps(label)}); if (!b) return null; return __tr.hit(b); }})()")
        if not r:
            raise LookupError(f"no open menu entry {label!r}; menu: {await self.js('__tr.menu()')}")
        await self.w.click(r["x"], r["y"])
        await asyncio.sleep(1.0)

    async def reload(self):
        await self.w.p.call("Page.reload")
        await self.wait_for("!!__tr.viewer()", 20)
        await asyncio.sleep(1.2)
        await self.w.js("document.getElementById('hud-frost')?.remove()")

    # ---- world (the copy) --------------------------------------------------------------------------------------------
    def do(self, line, who=ME):
        return self.copy.do(line, who)

    def viewer(self):
        line = W.viewer_line(lambda l: self.do(l))[0]
        return props_of(line)

    def tabs(self):
        # table always puts id and title (words) first: the four asked columns are the last four words
        out = self.do(f"table prop:role=viewer-tab,prop:viewer={self.vid} cols=tab,active,closed,order")
        rows = []
        for l in out.splitlines():
            f = l.split()
            if len(f) >= 5 and re.fullmatch(r"a\d+", f[0]) and re.fullmatch(r"tab-\d+", f[-4]):
                rows.append(dict(zip(("id", "tab", "active", "closed", "order"), [f[0], *f[-4:]])))
        return sorted(rows, key=lambda r: int(r["order"]) if r["order"].isdigit() else 0)

    def raw(self):
        """the viewer's whole line, and its tabs_state as printed (unquoted, so cut nowhere but by the next prop)"""
        line = W.viewer_line(lambda l: self.do(l))[0]
        m = re.search(r"tabs_state=(.*?) active_tab=", line)
        return line, (m.group(1) if m else "")

    def open_tabs(self):
        return [t for t in self.tabs() if t.get("closed") == "no"]

    def lines(self, sel):
        return [l.strip() for l in self.do(f"find {sel}").splitlines() if re.match(r"\s+[af]\d+ (note|surface|chat) ", l)]

    def record(self, jid, name, outcome, note, facts=None, shots=()):
        row = {"id": jid, "journey": name, "outcome": outcome, "note": note, "facts": facts or {}, "shots": list(shots)}
        self.rows.append(row)
        print(f"  {outcome:<8} {jid:<14} {note[:260]}", flush=True)
        return row


def fixtures(copy):
    """Synthetic pages in the copy only: two long notes, a doc, and 30 long-titled notes. -> {name: id}"""
    do = lambda line: copy.do(line, ME)  # noqa: E731

    def made_id(said):
        m = re.search(r"created ([afs]\d+)", said)
        if not m:
            raise RuntimeError("fixture refused: " + said[:600])
        return m.group(1)
    do("look f5189")
    said = do('do create f5189 kind=surface title="Tabs review fixtures (synthetic)" layout=column')
    sid = made_id(said)
    do(f"look {sid}")
    made = {"surface": sid}
    long = lambda tag: "\\n\\n".join(f"{tag} paragraph {k}: synthetic reading text for the tabs review, line after line so the page scrolls." for k in range(1, 161))  # noqa: E731
    for name, tag in (("Long note A (synthetic)", "Alpha"), ("Long note B (synthetic)", "Bravo")):
        said = do(f'do create {sid} kind=note title="{name}" text="{long(tag)}"')
        made[name] = made_id(said)
    said = do(f'do create {sid} kind=note title="Doomed page (synthetic)" text="this page is removed mid-review"')
    made["doomed"] = made_id(said)
    made["long"] = []
    for k in range(1, 31):
        t = f"Synthetic tab {k:02d}: a deliberately long page title that keeps going well past any chip width so it must be clamped"
        said = do(f'do create {sid} kind=note title="{t}" text="page {k}"')
        made["long"].append(made_id(said))
    return made


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="frontier-try")
    ap.add_argument("--small", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--only", type=lambda s: s.split(","), default=None)
    ap.add_argument("--candidate", choices=sorted(CANDIDATES), default=None)
    ap.add_argument("--jeff-fixes", action="store_true", help="c7704: compose search exclusions, menu look/order and the 20 routes on the copy")
    a = ap.parse_args()
    size = (1280, 800) if a.small else (2560, 1440)
    pt.SIZE = size
    out = DEMOS / (f"{datetime.datetime.now():%Y-%m-%d-%H%M%S}-{size[0]}x{size[1]}" + ("-jeff-fixes" if a.jeff_fixes else "")
                   + (f"-candidate-{a.candidate}" if a.candidate else ""))
    out.mkdir(parents=True, exist_ok=True)
    copy = pt.Copy(a.world)
    win, guard, R, errors, stagelog = None, None, None, None, []
    try:
        at0 = copy.at()
        base = {"viewer": W.viewer_line(lambda l: copy.do(l, ME)),
                "draft": [l.strip() for l in copy.do("find prop:role=conversation-draft,prop:actor=alex", ME).splitlines() if " note " in l],
                "layout": [l.strip() for l in copy.do("find prop:role=home-panel,prop:actor=alex", ME).splitlines() if " note " in l]}
        stagelog, saved, before, vid = W.apply_copy(lambda who, line: copy.do(line, who))
        if a.jeff_fixes:
            stagelog += ["JEFF's copy-review payload a7761 + search exclusions a7693, composed exactly on the copy (never live):"] + W.compose_jeff(lambda line: copy.do(line, ME))
        if a.candidate:
            # NOT the staged bytes: a reviewer's candidate world fix, applied after them so its effect can be seen
            old, new = CANDIDATES[a.candidate]
            copy.do("read a5486 :3", ME)
            said = copy.do(f"do replace a5486 old={W.q(old)} new={W.q(new)}", ME)
            stagelog.append(f"CANDIDATE {a.candidate} (not the staged bytes): {said.strip().splitlines()[-1][:160]}")
        made = fixtures(copy)
        win = pt.Window(False)
        await win.open(copy.url())
        R = Review(win, copy, out, size)
        R.vid, R.made, R.base, R.at0 = vid, made, base, at0
        R.stagelog = stagelog
        await R.wait_for("!!__tr.viewer()", 30)
        await asyncio.sleep(1.5)
        await win.js("document.getElementById('hud-frost')?.remove()")
        import steps
        for jid, fn in steps.ALL:
            if a.probe and jid != "probe":
                continue
            if a.only and jid not in a.only and jid != "probe":
                continue
            try:
                await fn(R)
                if getattr(R, "draft0", None):
                    R.trail.append((jid, await R.js(steps.DRAFT)))
            except Exception as e:
                R.record(jid, fn.__doc__ or jid, "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-1500:]},
                         [await R.shot(jid + "-error")])
        errors = await win.js("(window.__pt && window.__pt.errors) || []")
    finally:
        if win:
            guard = await win.close()
        copy.close()
    rows = R.rows if R else []
    rep = {"size": size, "copy_at_start": R.at0 if R else None, "guard": guard, "page_errors": errors, "stage": stagelog,
           "hashes": W.hashes(), "draft_trail": R.trail if R else [], "rows": rows}
    (out / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    md = [f"# Viewer tabs acceptance, {size[0]}x{size[1]}", "", f"guard: {guard[1] if guard else 'none'}", "",
          f"copy of {a.world}, {R.at0 if R else '?'} events at start", "", "stage:", *[f"- {s}" for s in stagelog], "",
          "| journey | outcome | note | shots |", "|---|---|---|---|"]
    md += [f"| {r['id']} | {r['outcome']} | {r['note'].replace('|', '/')[:500]} | {', '.join(r['shots'])} |" for r in rows]
    md += ["", f"Page errors: {errors}", "", "Chat draft after each journey (words, selection, About row):"]
    md += [f"- {j}: {d}" for j, d in (R.trail if R else [])]
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"guard: {guard[1] if guard else 'none'}")
    print(f"report: {out / 'report.md'}")
    return 1 if (guard and guard[0]) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
