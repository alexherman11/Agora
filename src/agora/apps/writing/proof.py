"""The Writing center, used the way Alex would, in a hidden copy of his desktop world (nothing shows on the screen).

    python proof.py [--out evidence]
Copies the live world (read once), installs the Writing center with install.py through the door, opens the window in
a headless browser signed in as Alex, and walks: home, a plan, a [[link]], back, a comment on selected words, sending a
passage and a whole document to JEFF (the house is off: no model is called), a plan's call, a new document written in
place with a [[ link picked, Ctrl+E source, an edit that moves a comment's words, find, a task box, a resolve.
Each step prints PASS/FAIL; pictures land in the out folder. Exit status 1 if any step failed.
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
from sandbox_here import Sandbox  # noqa: E402
from install import install, claude_door  # noqa: E402
from look import open_writing, errors  # noqa: E402


class Walk:
    def __init__(self, page, door, out):
        self.p, self.door, self.out, self.results = page, door, Path(out), []

    def js(self, x):
        return self.p.js(x)

    def until(self, x, s=10):
        self.p.until(x, s)

    def settle(self, ms=350):
        self.js(f'new Promise(r=>setTimeout(r,{ms}))')

    def click(self, sel, button='left', rx=.5, ry=.5):
        pt = self.p.point(sel, rx, ry)
        c = self.p.c
        c.call('Input.dispatchMouseEvent', type='mouseMoved', **pt)
        c.call('Input.dispatchMouseEvent', type='mousePressed', button=button, clickCount=1, **pt)
        c.call('Input.dispatchMouseEvent', type='mouseReleased', button=button, clickCount=1, **pt)

    def key(self, key, code=None, vk=None, mods=0, text=None):
        c = self.p.c
        extra = dict(key=key, code=code or key, windowsVirtualKeyCode=vk or 0, modifiers=mods)
        c.call('Input.dispatchKeyEvent', type='rawKeyDown' if not text else 'keyDown', **extra, **({'text': text} if text else {}))
        c.call('Input.dispatchKeyEvent', type='keyUp', **extra)

    def type(self, text):
        self.p.c.call('Input.insertText', text=text)

    def select_words(self, block_sel, words):
        """Select `words` inside the first block matching block_sel, as a person dragging over them would."""
        return self.js('(()=>{const b=[...document.querySelectorAll(' + json.dumps(block_sel) + ')].find(n=>n.textContent.includes(' + json.dumps(words) + '));'
                       'if(!b)return false;const w=document.createTreeWalker(b,NodeFilter.SHOW_TEXT);let t;while((t=w.nextNode())){const i=t.data.indexOf(' + json.dumps(words) + ');'
                       'if(i>=0){const r=document.createRange();r.setStart(t,i);r.setEnd(t,i+' + str(len(words)) + ');const s=getSelection();s.removeAllRanges();s.addRange(r);'
                       't.parentElement.setAttribute("data-proof-sel","1");return true}}return false})()')

    def step(self, name, fn, shot=None):
        t0 = time.time()
        try:
            detail = fn()
            ok = detail is not False
        except Exception as e:
            ok, detail = False, (str(e).splitlines() or [repr(e)])[0][:300] + '\n' + traceback.format_exc(limit=2)[-600:]
        if shot:
            self.p.shot(str(self.out / shot))
        self.results.append((name, ok))
        print(('PASS ' if ok else 'FAIL ') + name + f' ({time.time() - t0:.1f}s)' + ('' if detail in (None, True) else ' · ' + str(detail)[:400]), flush=True)
        return ok


def run(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with Sandbox('claude-writing') as s:
        door = claude_door(s.url)
        t0 = time.time()
        ids = install(door)
        print('installed in', round(time.time() - t0, 1), 's:', json.dumps(ids), flush=True)
        alex = claude_door(s.url)
        page = open_writing(s.url, 'alex', 1440, 900)
        w = Walk(page, door, out)
        # the guide is made once; a copy of a world that already has it returns no id for it
        guide = ids.get('Writing in Agora') or door.rows('document', source='src/agora/apps/writing/install.py#guide')[0]['id']
        clutter, moving = ids['Shedding clutter'], ids['Moving into the desktop']

        def home():
            w.until('document.querySelector(".wr-hello")?.textContent.includes("Alex")')
            got = w.js('({hello:document.querySelector(".wr-hello").textContent,sub:document.querySelector(".wr-sub").textContent,'
                       'cards:[...document.querySelectorAll(".wr-card .wr-row-title")].map(n=>n.textContent),'
                       'shelves:[...document.querySelectorAll(".wr-shelf-toggle")].map(n=>n.textContent)})')
            assert 'Shedding clutter' in got['cards'], got
            assert any(x.startswith('›Plans') for x in got['shelves']) and any('Waiting' in x for x in got['shelves']), got
            return got
        w.step('home: hello, the waiting plan as a card, Plans with Waiting and Answered', home, 'proof-01-home.png')

        def open_plan():
            w.click('.wr-card')
            w.until('document.querySelector(".wr-title")?.value==="Shedding clutter"')
            w.settle(500)
            got = w.js('({plan:document.querySelector(".wr-plan")?.innerText,tables:document.querySelectorAll(".wr-md table").length,'
                       'h2:document.querySelectorAll(".wr-md h2").length,link:[...document.querySelectorAll(".wr-md a.wr-link")].map(a=>a.textContent+"→"+a.dataset.doc),'
                       'chip:document.querySelector(".wr-chip.wr-claude")?.textContent,current:document.querySelector(".wr-row[aria-current=true] .wr-row-title")?.textContent})')
            assert 'Waiting for you' in got['plan'] and got['tables'] >= 3 and got['chip'] == 'Draft by Claude', got
            assert any(x.endswith('→' + moving) for x in got['link']), got
            return got
        w.step('a plan opens: drawn Markdown with its tables, its call, Claude\'s draft, [[MOVING-IN]] resolved', open_plan, 'proof-02-plan.png')

        def follow():
            w.click('.wr-md a.wr-link[data-doc="' + moving + '"]')
            w.until('document.querySelector(".wr-title")?.value==="Moving into the desktop"')
            got = w.js('({plan:document.querySelector(".wr-plan").innerText,back:!![...document.querySelectorAll(".wr-top button")].find(b=>b.textContent.includes("Back")),'
                       'linked:document.querySelector(".wr-below")?.innerText||""})')
            assert 'Answered' in got['plan'] and 'T1' in got['plan'] and got['back'], got
            return got
        w.step('[[link]] opens Moving into the desktop: Answered, T1 still open, Back shown', follow, 'proof-03-linked.png')

        def back():
            w.until('document.querySelector(".wr-below")?.textContent.includes("Shedding clutter")', 8)
            w.click('.wr-top button[aria-label^="Back"]')
            w.until('document.querySelector(".wr-title")?.value==="Shedding clutter"')
        w.step('"Linked from" lists Shedding clutter; Back returns to it', back)

        quote = 'Clutter is not old things.'

        def comment():
            assert w.select_words('.wr-md li', quote)
            w.click('[data-proof-sel]', button='right', rx=.1)
            w.until('!!document.querySelector(".wr-menu")')
            menu = w.js('document.querySelector(".wr-menu").innerText')
            w.p.shot(str(out / 'proof-04-menu.png'))
            w.js('[...document.querySelectorAll(".wr-menu>button")].find(b=>b.textContent.startsWith("Comment")).click()')
            w.until('!!document.querySelector(".wr-pop textarea")')
            w.type('Is "clutter" the right word? It sounds like mess, not machine noise.')
            w.p.shot(str(out / 'proof-05-composer.png'))
            w.key('Enter', 'Enter', 13, text='\r')
            w.until('!!document.querySelector(".wr-c")', 10)
            w.settle(400)
            rows = door.rows('comment', about=clutter)
            assert rows and rows[0]['quote'] == quote and rows[0].get('heading') == 'The short version', rows
            got = w.js('({mark:document.querySelector("mark.wr-mark")?.textContent,card:document.querySelector(".wr-c")?.innerText})')
            assert got['mark'] == quote and 'under § The short version' in got['card'], got
            return {'menu': menu.replace('\n', ' | '), **got}
        w.step('select words, right-click, Comment: a comment thing, its words marked, "under § The short version"', comment, 'proof-06-comment.png')

        def to_jeff():
            assert w.select_words('.wr-md li', 'Shedding has three dials')
            w.click('[data-proof-sel]', button='right', rx=.05)
            w.until('!!document.querySelector(".wr-menu")')
            w.js('[...document.querySelectorAll(".wr-menu>button")].find(b=>b.textContent.startsWith("Send to JEFF")).click()')
            w.until('!!document.querySelector(".wr-pop textarea")')
            w.type('Which dial would you turn first?')
            w.key('Enter', 'Enter', 13, text='\r')
            w.until('!document.querySelector(".wr-pop")', 10)
            said = [r for r in alex.rows('said', about=clutter)]
            assert said and 'Which dial' in said[-1]['text'] and '> Shedding has three dials' in said[-1]['text'] and '[[' + clutter in said[-1]['text'], said
            convo = alex.rows('chat', name='Conversation')[0]['id']
            assert said[-1]['chat'] == convo, said[-1]
            return said[-1]['text']
        w.step('select words, right-click, Send to JEFF: a said line in the Conversation, quoted, about= the document', to_jeff)

        def whole_to_jeff():
            w.js('[...document.querySelectorAll(".wr-actions button")].find(b=>b.textContent.includes("Send to JEFF")).click()')
            w.until('!!document.querySelector(".wr-pop textarea")')
            w.type('Read this before we talk tonight.')
            w.p.shot(str(out / 'proof-07-send-doc.png'))
            w.key('Enter', 'Enter', 13, text='\r')
            w.until('!document.querySelector(".wr-pop")', 10)
            said = alex.rows('said', about=clutter)
            assert len(said) == 2 and said[-1]['text'].endswith('— about [[' + clutter + '|Shedding clutter]]'), said
            w.until('document.querySelector(".wr-below")?.textContent.includes("Sent to JEFF · 2")', 8)
        w.step('Send to JEFF on the whole document; "Sent to JEFF · 2" under it', whole_to_jeff)

        def verdict():
            w.js('[...document.querySelectorAll(".wr-plan-calls button")].find(b=>b.textContent==="Not yet, I have questions").click()')
            w.until('document.querySelector(".wr-plan")?.innerText.includes("You said: Not yet")', 10)
            d = door.rows('document', source='research/clutter-lab/README.md')[0]
            assert d['plan'] == 'answered' and d['verdict'] == 'questions', d
            w.p.shot(str(out / 'proof-08-verdict.png'))
            w.js('[...document.querySelectorAll(".wr-plan-calls button")].find(b=>b.textContent==="Back to waiting").click()')
            w.until('document.querySelector(".wr-plan")?.innerText.includes("Waiting for you")', 10)
            d = door.rows('document', source='research/clutter-lab/README.md')[0]
            assert d['plan'] == 'waiting' and 'verdict' not in d, d
        w.step('a plan\'s call: "Not yet, I have questions" answers it; "Back to waiting" undoes the state', verdict)

        def new_doc():
            w.click('.wr-top .wr-primary')        # a real press: typing goes where a person's would
            w.until('document.querySelector(".wr-title")?.value==="Untitled"', 10)
            w.until('document.activeElement?.classList.contains("wr-title")', 5)
            w.type('Saturday market list')
            w.key('Enter', 'Enter', 13, text='\r')
            w.until('[...document.querySelectorAll(".wr-row-title")].some(n=>n.textContent==="Saturday market list")', 10)
            w.click('.wr-md .wr-placeholder')
            w.until('document.activeElement?.classList.contains("wr-editor")', 5)
            w.type('## Things to bring\n\n- [ ] a **folding table**\n- [ ] the plans, see [[Shed')
            w.until('!document.querySelector(".wr-pick").hidden && document.querySelector(".wr-pick button")?.textContent.includes("Shedding clutter")', 5)
            w.p.shot(str(out / 'proof-09-link-picker.png'))
            w.key('Enter', 'Enter', 13, text='\r')
            w.type('\n- [x] *sun hat*')
            w.key('Escape', 'Escape', 27)
            w.until('!!document.querySelector(".wr-md h2") && !document.querySelector(".wr-editor")', 10)
            d = [x for x in door.rows('document') if x.get('title') == 'Saturday market list'][0]
            assert '[[' + clutter + '|Shedding clutter]]' in d['text'] and d['collection'] == 'notes', d
            got = w.js('({h2:document.querySelector(".wr-md h2").textContent,tasks:document.querySelectorAll(".wr-md li.wr-task").length,'
                       'link:document.querySelector(".wr-md a.wr-link")?.textContent,strong:document.querySelector(".wr-md strong")?.textContent})')
            assert got == {'h2': 'Things to bring', 'tasks': 3, 'link': 'Shedding clutter', 'strong': 'folding table'}, got
            return got
        w.step('New document: name it, press the page, write Markdown, [[ picks Shedding clutter, Esc keeps it, drawn', new_doc, 'proof-10-new-doc.png')

        def tick():
            w.click('.wr-md li.wr-task input')
            w.until('document.querySelector(".wr-md li.wr-task")?.classList.contains("wr-ticked")', 10)
            d = [x for x in door.rows('document') if x.get('title') == 'Saturday market list'][0]
            assert '- [x] a **folding table**' in d['text'], d['text']
        w.step('a task box ticks the line in the text', tick)

        def source():
            w.js('document.querySelector(".wr-md").focus()')
            w.key('e', 'KeyE', 69, mods=2)
            w.until('!!document.querySelector(".wr-source")', 5)
            v = w.js('document.querySelector(".wr-source").value')
            assert v.startswith('## Things to bring'), v
            w.js('(()=>{const t=document.querySelector(".wr-source");t.focus();t.setSelectionRange(t.value.length,t.value.length)})()')
            w.type('\n\n> Market opens at **8**.')
            w.p.shot(str(out / 'proof-11-source.png'))
            w.key('e', 'KeyE', 69, mods=2)
            w.until('!document.querySelector(".wr-source") && !!document.querySelector(".wr-md blockquote")', 10)
            d = [x for x in door.rows('document') if x.get('title') == 'Saturday market list'][0]
            assert d['text'].endswith('> Market opens at **8**.'), d['text']
        w.step('Ctrl+E shows the source; writing there and Ctrl+E again keeps it and draws it', source)

        def edit_moves_comment():
            w.js('[...document.querySelectorAll(".wr-row")].find(r=>r.textContent.includes("Shedding clutter")).click()')
            w.until('document.querySelector(".wr-title")?.value==="Shedding clutter"', 10)
            w.until('!!document.querySelector("mark.wr-mark")', 8)
            w.click('mark.wr-mark', rx=.9)          # a comment's mark lights its card; it does not start editing
            w.until('document.querySelector(".wr-c")?.classList.contains("wr-hot")', 5)
            assert not w.js('!!document.querySelector(".wr-editor")')
            w.js('document.querySelector("mark.wr-mark").closest(".wr-block").setAttribute("data-proof-edit","1")')
            w.click('[data-proof-edit] li:first-child', rx=.98)
            w.until('document.activeElement?.classList.contains("wr-editor")', 5)
            v = w.js('document.querySelector(".wr-editor").value')
            assert '**Clutter is not old things.**' in v, v[:200]
            w.js('(()=>{const t=document.querySelector(".wr-editor");t.value=t.value.replace("**Clutter is not old things.**","**Clutter is not merely old things.**");t.dispatchEvent(new Event("input"))})()')
            w.js('document.querySelector(".wr-title").focus()')
            w.until('!document.querySelector(".wr-editor")', 10)
            w.until('document.querySelector(".wr-c-st")?.textContent.startsWith("changed")', 10)
            d = door.rows('document', source='research/clutter-lab/README.md')[0]
            assert 'Clutter is not merely old things.' in d['text']
            return w.js('document.querySelector(".wr-c-st").textContent')
        w.step('press a part, change the commented words, leave: saved, the comment says its words changed', edit_moves_comment, 'proof-12-changed.png')

        def resolve():
            w.js('[...document.querySelectorAll(".wr-c-acts button")].find(b=>b.textContent.includes("Resolve")).click()')
            w.until('document.querySelector(".wr-more")?.textContent.includes("1 resolved")', 10)
            c = door.rows('comment', about=clutter)[0]
            assert c['resolved'] == 'yes', c
        w.step('Resolve folds the comment under "Show 1 resolved"', resolve)

        def find():
            w.click('.wr-find input')
            w.type('dial')
            w.until('document.querySelectorAll(".wr-results .wr-row").length>0', 5)
            got = w.js('[...document.querySelectorAll(".wr-results .wr-row-title")].map(n=>n.textContent)')
            assert 'Shedding clutter' in got, got
            w.p.shot(str(out / 'proof-13-find.png'))
            w.key('Escape', 'Escape', 27)
            w.until('!document.querySelector(".wr-results")', 5)
            return got
        w.step('Find a document: "dial" finds Shedding clutter by its text; Esc brings the collections back', find)

        def guide_doc():
            w.js('[...document.querySelectorAll(".wr-row")].find(r=>r.textContent.includes("Writing in Agora")).click()')
            w.until('document.querySelector(".wr-title")?.value==="Writing in Agora"', 10)
            w.settle(400)
            got = w.js('({link:document.querySelector(".wr-md a.wr-link")?.dataset.doc,table:document.querySelectorAll(".wr-md tbody tr").length,ticked:document.querySelectorAll(".wr-md li.wr-ticked").length})')
            assert got['link'] == moving and got['table'] == 7 and got['ticked'] == 3, got
            return got
        w.step('the guide: [[Moving into the desktop]] by title, its keys table, its ticked list', guide_doc, 'proof-14-guide.png')

        def home_again():
            w.js('[...document.querySelectorAll(".wr-top button")].find(b=>b.textContent==="Home").click()')
            w.until('!!document.querySelector(".wr-hello")', 5)
            got = w.js('[...document.querySelectorAll(".wr-list .wr-row-title")].map(n=>n.textContent)')
            assert got[0] in ('Shedding clutter', 'Saturday market list'), got
            return got
        w.step('Home lists recently changed, newest first', home_again, 'proof-15-home-after.png')

        def dark_and_light():
            look = alex.say('theme.current')['text'].splitlines()[0]
            return look
        w.step('the window wears the world\'s theme (the copy wears Alex\'s)', dark_and_light)

        errs = errors(page)
        w.step('no script errors in the window', lambda: (not errs) or (_ for _ in ()).throw(AssertionError(json.dumps(errs)[:1500])))
        page.close()
        failed = [n for n, ok in w.results if not ok]
        print(f'{len(w.results) - len(failed)} of {len(w.results)} steps pass', flush=True)
        return not failed


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(HERE / 'evidence'))
    a = ap.parse_args()
    sys.exit(0 if run(a.out) else 1)
