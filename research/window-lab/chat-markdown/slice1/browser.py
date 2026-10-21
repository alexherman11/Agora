"""Disposable isolated feed, guarded hidden desktop only. Never posts to Conversation.

Run from the worktree root with the pinned interpreter. Uses the established
Copy/Window lifecycle; no live apply, account/media calls or host verbs.
"""
import asyncio
import json
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
WINDOW = HERE.parents[1]
sys.path.insert(0, str(WINDOW))
import hud_playtest as H


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("$", "\\$") + '"'


async def main():
    copy, win = None, None
    try:
        copy = H.Copy("frontier-try")

        def do(line):
            r = copy.do(line, who="worker-a7557")
            if isinstance(r, str):
                r = {"text": r}
            if r.get("error") or re.search(r"(^|\n)(ERR|refused:)", r.get("text") or ""):
                raise RuntimeError(str(r))
            return r

        do("look")
        # A fresh room, feed and renderer: no original Conversation lens/feed modified.
        made = do('do create f149 kind=surface title="Markdown disposable fixtures"')
        root = re.search(r"created (f\d+)", made["text"]).group(1)
        do("look " + root)
        note = do(f'do create {root} kind=note title="Markdown fixture message" role=md-fixture text=' + q(
            "# A readable message\n**Bold**, *italic*, `inline`.\n- parent\n  - child\n- [ ] sent task\n"
            "> Quote\n---\n```text\n" + "very-long-code-" * 100 + "\n```\n"
            "| Name | Value |\n| --- | --- |\n| fixture | " + "wide cell " * 100 + " |\n"
            "[Explicit external link](https://example.test/)\n<script>untrusted()</script>"))
        nid = re.search(r"created (a\d+)", note["text"]).group(1)
        chat = do(f'do create {root} kind=chat title="Disposable replies" with="worker-a7557"')
        cid = re.search(r"created (a\d+)", chat["text"]).group(1)
        do("read " + cid)
        style = 'token ink = #23312D\nrole page : ink'
        do(f'do create {root} kind=note title="md-slice-style" tags=style text={q(style)}')
        lens = (f'fixture : column\n  share 1\n  role page\n'
                f'  feed : column\n    share 1\n    scroll scroll\n    of in:{root},prop:role=md-fixture as m\n    each message\n'
                f'  composer : text ""\n    hint "Unsent fixture draft"\n    lines 2..6\n    commit explicit\n'
                f'    on edit do append {cid} line="$value"\n'
                f'message : column\n  body : text "$m.text"\n    markdown\n    media\n')
        do(f'do create {root} kind=note title="md-slice-fixture" tags=lens style=md-slice-style text={q(lens)}')
        win = H.Window(False)
        await win.open(copy.url("md-slice-fixture", "worker-a7557"))
        # If startup fails, nothing below is reported as run or passed.
        await asyncio.sleep(1)
        geometry = await win.js("[innerWidth,innerHeight,devicePixelRatio,document.visibilityState]")
        print("actual page:", geometry, flush=True)
        assert geometry[-1] == "visible", geometry
        await win.js("""(() => { const b=document.querySelector('textarea'); b.focus();
          b.value='Unsent fixture words'; b.dispatchEvent(new Event('input',{bubbles:true}));
          b.setSelectionRange(6,6); window.__fixtureBox=b;
          return true; })()""")
        do(f'do create {root} kind=note title="Incoming update" role=md-fixture text="## Incoming update"')
        await asyncio.sleep(2)
        print("draft/caret and incoming:", await win.js("""(() => { const b=document.querySelector('textarea');
          if(b!==window.__fixtureBox || b.value!=='Unsent fixture words' || b.selectionStart!==6 ||
             document.activeElement!==b || !document.body.textContent.includes('Incoming update')) throw Error('draft/update continuity');
          return {words:b.value,caret:b.selectionStart}; })()"""), flush=True)
        for width in (320, 420, 600):
            print("width check:", await win.js("""(() => { const w=WIDTH;
              document.getElementById('paint').style.width=w+'px';
              return new Promise((resolve,reject)=>requestAnimationFrame(()=> {
                const d=document.querySelector('.md-doc'), r=d.getBoundingClientRect();
                if(d.scrollWidth>d.clientWidth+1) return reject(Error('message overflows at '+w));
                resolve({requested:w,documentWidth:r.width,scrollWidth:d.scrollWidth,clientWidth:d.clientWidth,
                  wholePageScroll:document.scrollingElement.scrollWidth>innerWidth});
              })); })()""".replace("WIDTH", str(width))), flush=True)
        # The browser-capable reviewer must additionally drive trusted mouse/key
        # input, original Reply, native fixture media playback/Pop out, malformed
        # renderer injection and apply/undo; this subset is not full acceptance.
        out = HERE / ("screen-md-slice-" + time.strftime("%H%M%S") + ".png")
        await win.shot(out)
        print("shot:", out, flush=True)
    finally:
        if win:
            print("guard/cleanup:", await win.close(), flush=True)
        if copy:
            copy.close()


if __name__ == "__main__":
    asyncio.run(main())
