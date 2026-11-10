"""One guarded copy lane. Stops on any pre-page-ready refusal; never retries/falls back.

Clipboard operations are intercepted BEFORE the test document loads. No live
Conversation actions, real clipboard, host restart or source/world override.
"""
import asyncio
import datetime
import json
import os
from pathlib import Path
import re
import sys
import traceback
import urllib.request
import urllib.parse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import hud_playtest as pt
from journeys import CLIP

ME = "worker-a8420"
MENU = "Remove review request (shared list)"

def refused(text):
    return bool(re.search(r"(^|\n)(ERR\b|!! (?!since your last look:))", text))


def replacements(which):
    if which == "a5548":
        return [('review : column\n  role nbneed',
                 'review : column\n  on menu "' + MENU + '" do tag $c remove=ready-for-review\n  role nbneed')]
    result = []
    for query in ("tag:ready-for-review,-prop:review=later", "tag:ready-for-review,prop:review=later",
                  "prop:design=waiting,-prop:review=later", "prop:design=waiting,prop:review=later"):
        old = f"    of {query} as w\n    each item"
        removable = "yes" if query.startswith("tag:") else "no"
        result.append((old, f'    let removable = "{removable}"\n' + old))
    result.append(("item : column\n  role wait", 'item : column\n  on menu "' + MENU +
                   '" when removable = "yes" do tag $w remove=ready-for-review\n  role wait'))
    return result


def post(copy, route, body):
    req = urllib.request.Request(copy.base + route, json.dumps(
        {"session": copy.session, "as": ME, **body}).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def copy_review_acceptance(copy, fx):
    def view(name):
        url = copy.base + "/api/scene?" + urllib.parse.urlencode(
            {"session": copy.session, "as": "alex", "lens": name, "view": "painter"})
        with urllib.request.urlopen(url, timeout=20) as r:
            reply = json.load(r)
        if "scene" not in reply:
            raise AssertionError(reply)
        return reply

    def walk(node):
        yield node
        for child in node.get("kids", []):
            yield from walk(child)

    def action(reply, item):
        matches = [(n, a) for n in walk(reply["scene"])
                   for a in n.get("acts", []) if a.get("label") == MENU and item in n["key"]]
        assert len(matches) == 1, (item, [n["key"] for n, _ in matches])
        return matches[0]

    def press(reply, item):
        node, act = action(reply, item)
        return post(copy, "/api/do", {"as": "alex", "line": act["line"], "observed":
                    {**node["fence"], "at": reply["events_total"], "def": reply["scene"].get("def")}})

    result = {}
    for name in ("waiting-on-me", "home-board"):
        reply = view(name)
        action(reply, fx["tagged"])
        action(reply, fx["dual"])
        assert not [(n, a) for n in walk(reply["scene"]) for a in n.get("acts", [])
                    if a.get("label") == MENU and fx["design"] in n["key"]]
        copy.do(f"read {fx['tagged']}", ME)
        copy.do(f"do tag {fx['tagged']} remove=ready-for-review", ME)
        before = copy.at()
        stale = press(reply, fx["tagged"])
        assert stale.get("error") and copy.at() == before, stale
        copy.do(f"read {fx['tagged']}", ME)
        copy.do(f"do tag {fx['tagged']} add=ready-for-review", ME)
        reply = view(name)
        removed = press(reply, fx["dual"])
        assert not removed.get("error"), removed
        # It is still selected by design; removal never deletes the source.
        assert fx["dual"] in copy.do("find prop:design=waiting", ME)
        assert fx["dual"] not in copy.do("find tag:ready-for-review", ME)
        events = removed.get("events", [])
        event = events[-1].get("id") if events and isinstance(events[-1], dict) else events[-1] if events else None
        if not event:
            event = re.search(r"\[(e\d+)\]", removed.get("text", ""))[1]
        restored = copy.do(f"undo {event}", ME)
        assert not refused(restored), restored
        assert fx["dual"] in copy.do("find tag:ready-for-review", ME)
        result[name] = {"tag_menu": True, "design_only_menu": False, "dual_remains_design": True,
                        "stale_refused": True, "undo_restores_tag": True, "underlying_delete": False}
    return result


def setup(copy):
    def do(line):
        out = copy.do(line, ME)
        if refused(out):
            raise AssertionError(out)
        return out

    def make(parent, args):
        do(f"look {parent}")
        return re.search(r"created ([af]\d+)", do(f"do create {parent} {args}"))[1]

    do("look")
    room = make("f149", 'kind=surface title="Explicit menu fixtures"')
    source = make(room, 'kind=note title="Passage fixture" text="same 😀 same **bold** end" about=kept attachment=kept')
    tagged = make(room, 'kind=note title="Tagged fixture" tags=ready-for-review')
    design = make(room, 'kind=surface title="Design fixture"')
    dual = make(room, 'kind=note title="Dual fixture"')
    for target in (design, dual):
        do(f"look {target}")
        do(f"do prop {target} design=waiting")
    do(f"do tag {dual} add=ready-for-review")
    src = f'''selection : column
  plain : text $text
    on select do prop $item accidental=yes
    on menu "Comment" prepare selection/say
  marked : text $text
    markdown
    on select do prop $item accidental=yes
    on menu "Comment" prepare selection/say
    on edit do rewrite $item text="$value"
  say : text ""
    hint "Fixture draft"
    commit explicit
    on edit do prop $item draft="$value" quote="$quote_text" source=$quote_item start=$quote_start end=$quote_end
'''
    make(room, f'kind=note title=explicit-menu-fixture tags=lens text={pt.q(src)}')
    baseline = json.loads((HERE / "world-menu-fixtures.json").read_text(encoding="utf-8"))
    staged = {}
    for ident, text in baseline.items():
        changed = text
        for old, new in replacements(ident):
            if changed.count(old) != 1:
                raise AssertionError(f"{ident}: expected unique exact Rowan hunk {old!r}")
            changed = changed.replace(old, new)
            do(f"read {ident} :3")
            do(f"do replace {ident} old={pt.q(old)} new={pt.q(new)}")
        staged[ident] = changed
    # Real full-lens compilation in the disposable world, not just the small probe.
    full = {name: copy.do(f"scene {name} ok", "alex") for name in ("home-board", "waiting-on-me")}
    for name, text in full.items():
        if refused(text) or "does not compile" in text:
            raise AssertionError(f"{name}: {text}")
    return {"source": source, "tagged": tagged, "design": design, "dual": dual,
            "full_lenses": full, "staged_lenses": staged}


async def journey(win, copy, fx):
    facts = {}
    async def js(expr):
        return await win.js(expr)

    async def key(name, code):
        await win.p.call("Input.dispatchKeyEvent", type="keyDown", key=name, code=name, windowsVirtualKeyCode=code)
        await win.p.call("Input.dispatchKeyEvent", type="keyUp", key=name, code=name, windowsVirtualKeyCode=code)

    async def select(part, start, end, mouse=False):
        rect = await js(f"""(() => {{
          const el=document.querySelector('[data-key="selection/{part}"]');
          const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT), ns=[]; let n,t='';
          while(n=w.nextNode()){{ns.push([n,t.length]); t+=n.data;}}
          const at=p=>{{let i=ns.length-1;while(i>0&&ns[i][1]>p)i--;return [ns[i][0],p-ns[i][1]];}};
          const r=document.createRange();r.setStart(...at({start}));r.setEnd(...at({end}));
          getSelection().removeAllRanges();getSelection().addRange(r);
          const b=r.getBoundingClientRect();return [b.left,b.top,b.width,b.height,String(r)];
        }})()""")
        if mouse:
            await win.drag(rect[0] + .2, rect[1] + rect[3] / 2,
                           rect[0] + rect[2] - .2, rect[1] + rect[3] / 2, steps=8, devtools=True)
        return rect

    async def menu(rect=None):
        if rect:
            await win.click(rect[0] + rect[2] / 2, rect[1] + rect[3] / 2, right=True)
        else:
            await key("ContextMenu", 0x5D)
        await asyncio.sleep(.15)
        return await js("[...document.querySelectorAll('#menu-pop button')].map(b=>b.textContent)")

    async def choose(label):
        xy = await js(f"""(() => {{const b=[...document.querySelectorAll('#menu-pop button')].find(b=>b.textContent==={json.dumps(label)});
          if(!b)throw Error('missing entry');const r=b.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2];}})()""")
        await win.click(*xy)
        await asyncio.sleep(.3)

    await js("""(() => {const t=document.querySelector('.explicit-composer textarea');t.focus();t.value='Existing draft';
      t.dispatchEvent(new InputEvent('input',{bubbles:true}));window.__requests=[];
      const f=window.fetch;window.fetch=(url,o)=>{__requests.push([String(url),o?.body]);return f(url,o);};})()""")
    before = copy.at()
    rect = await select("plain", 8, 12, mouse=True)
    await asyncio.sleep(.2)
    assert copy.at() == before, "highlight mutated the copy"
    assert "Comment" in await menu(rect)
    assert copy.at() == before, "opening menu mutated the copy"
    await key("Escape", 27)
    assert await js("String(getSelection())") == "same"
    assert "Comment" in await menu()
    await choose("Comment")
    assert copy.at() == before, "preparation mutated the copy"
    assert await js("document.querySelector('.explicit-composer textarea').value") == "Existing draft"
    assert await js("!!document.querySelector('.explicit-composer a[href*=\"on=\"]')")
    packets = await js("__requests.filter(r=>r[0]==='/api/selection').map(r=>JSON.parse(r[1]).selection)")
    assert packets and (packets[-1]["start"], packets[-1]["end"], packets[-1]["quote"]) == (8, 12, "same")
    assert not await js("__requests.some(r=>r[0]==='/api/do')"), "selection/preparation sent a command"
    facts["highlight_keyboard_prepare"] = {"events_before": before, "events_after": copy.at(), "packet": packets[-1]}
    # Another quote refuses instead of replacing the first or existing words.
    await select("plain", 0, 4)
    await menu()
    await choose("Comment")
    assert await js("document.querySelector('.explicit-composer a').textContent.includes('same')")
    await js("[...document.querySelectorAll('.explicit-composer button')].find(b=>b.textContent==='Remove quote').click()")
    # Source edit while the selection/menu is held. No click on Send anywhere.
    rect = await select("plain", 8, 12)
    await menu(rect)
    copy.do(f"read {fx['source']}", ME)
    copy.do(f'do rewrite {fx["source"]} text="Source edited while menu is open"', ME)
    await choose("Comment")
    assert await js("document.querySelector('.explicit-composer a').parentElement.hidden")
    facts["stale_prepare_refused"] = True
    # Clipboard is a recorder. Cut/undo use TextEdit's actual handlers; no system clipboard.
    copy.do(f"read {fx['source']}", ME)
    copy.do(f'do rewrite {fx["source"]} text="same 😀 same **bold** end"', ME)
    await asyncio.sleep(1.5)
    await select("marked", 0, 4)
    await menu()
    labels = await js("[...document.querySelectorAll('#menu-pop button')].map(b=>b.textContent)")
    facts["markdown_menu"] = labels
    assert "Copy" in labels
    await choose("Copy")
    assert await js("__clip.length") > 0
    assert await js("__clip.every(x=>['copy','cut','writeText'].includes(x[0]))")
    # Record the same exact staged full-lens menu branches in this browser lane.
    for name in ("waiting-on-me", "home-board"):
        await win.p.call("Page.navigate", url=copy.url(lens=name, who="alex"))
        await asyncio.sleep(1.5)
        facts[name] = await js("""[...document.querySelectorAll('[data-menu]')].map(e=>e._n).filter(n=>
          n.acts.some(a=>a.label==='Remove review request (shared list)')).map(n=>({key:n.key,acts:n.acts,fence:n.fence}))""")
    return facts


async def main():
    # Keep scratch and reports within this worktree. Never override another checkout.
    scratch = HERE / "scratch"
    scratch.mkdir(exist_ok=True)
    os.environ["AGORA_TMP"] = str(scratch)
    out = HERE / "results" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    report = {"status": "blocked", "page_ready": False, "guard": None}
    copy = win = None
    try:
        pt.SIZE = (2560, 1440)
        copy = pt.Copy("frontier-try")
        fx = setup(copy)
        report["full_lenses"] = fx["full_lenses"]
        report["copy_review_acceptance"] = copy_review_acceptance(copy, fx)
        win = pt.Window(False)
        await win.open(copy.url(lens="explicit-menu-fixture", who=ME) + "&on=" + fx["source"])
        # Clipboard interception precedes the document used for every journey.
        await win.p.call("Page.addScriptToEvaluateOnNewDocument", source=CLIP)
        await win.p.call("Page.navigate", url=copy.url(lens="explicit-menu-fixture", who=ME) + "&on=" + fx["source"])
        async def ready():
            while not await win.js("document.readyState==='complete' && !!document.querySelector('.explicit-composer')"):
                await asyncio.sleep(.1)
        await asyncio.wait_for(ready(), timeout=20)
        report["page_ready"] = True
        report["facts"] = await journey(win, copy, fx)
        shot = out / "explicit-menu.png"
        await win.shot(shot)
        report["shot"] = str(shot)
        report["status"] = "partial"
        report["limits"] = "2560 only; markdown Cut/undo, 1280, full review stale/undo and native clipboard remain unverified"
    except Exception as e:
        report["error"] = f"{type(e).__name__}: {e}"
        report["trace"] = traceback.format_exc()
    finally:
        if win:
            try:
                report["guard"] = await win.close()
            except Exception as e:
                report["cleanup_error"] = str(e)
        if copy:
            copy.close()
        (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        print("report:", out / "report.json")
    return 0 if report["page_ready"] else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
