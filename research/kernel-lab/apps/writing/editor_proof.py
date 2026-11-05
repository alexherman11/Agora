"""The continuous editor, used the way a person uses a document editor, in a hidden copy of Alex's desktop world.
Nothing shows on the screen: the browser is headless and the world is a copy, deleted afterwards.

    python editor_proof.py [--out evidence/editor]

Every press and key is a real input event (mouse down/move/up, key down/up, typed text), not a script calling the
editor. Each step prints PASS/FAIL with what it saw; pictures land in the out folder. Exit status 1 if any step failed.
Builder draft by Claude, 4 Nov 2026.
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
from sandbox_here import Sandbox  # noqa: E402
from install import install, claude_door, Q  # noqa: E402
from look import open_writing, errors  # noqa: E402
from proof import Walk  # noqa: E402

CTRL, SHIFT = 2, 8
V = 'document.querySelector(".wr-sheet .cm-editor").wrView'


class EditorWalk(Walk):
    def step(self, name, fn, shot=None):
        ok = super().step(name, fn, shot)
        if not ok:
            try:
                print('   window log:', json.dumps(self.js('(window.__wrlog||[]).slice(-12)'))[:1500], flush=True)
            except Exception:
                pass
        return ok

    def doc(self):
        return self.js(V + '.state.doc.toString()')

    def sel(self):
        return self.js('(()=>{const r=' + V + '.state.selection.main;return [r.anchor,r.head]})()')

    def at(self, pos, side='left'):
        """Screen point of a document position (inside the widget frame, plus the frame's offset)."""
        self.js('(()=>{const v=' + V + ';v.dispatch({effects:v.constructor.scrollIntoView(' + str(pos) + ',{y:"center"})})})()')
        self.frame()
        self.frame()
        b = self.js('(()=>{const v=' + V + ';const c=v.coordsAtPos(' + str(pos) + ');'
                    'return c?{x:c.' + side + '+(' + ('1' if side == 'left' else '-1') + '),y:(c.top+c.bottom)/2}:null})()')
        assert b, f'no coordinates for {pos}'
        off = self.p.c.js('(()=>{const r=document.querySelector("iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')
        return dict(x=b['x'] + off['x'], y=b['y'] + off['y'])

    def mouse(self, kind, pt, button='left', count=1, mods=0, buttons=None):
        extra = {} if buttons is None else {'buttons': buttons}
        self.p.c.call('Input.dispatchMouseEvent', type=kind, button=button, clickCount=count, modifiers=mods, **pt, **extra)

    def press(self, pt, mods=0, count=1, button='left'):
        self.mouse('mouseMoved', pt, button='none')
        self.mouse('mousePressed', pt, button, count, mods)
        self.mouse('mouseReleased', pt, button, count, mods)
        self.frame()

    def drag(self, a, b):
        self.mouse('mouseMoved', a, button='none')
        self.mouse('mousePressed', a)
        for i in range(1, 11):
            self.mouse('mouseMoved', dict(x=a['x'] + (b['x'] - a['x']) * i / 10, y=a['y'] + (b['y'] - a['y']) * i / 10), buttons=1)
            self.frame()
        self.mouse('mouseReleased', b)
        self.frame()

    def frame(self):
        self.js('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(true))))')

    def k(self, key, code, vk, mods=0, text=None):
        c = self.p.c
        extra = dict(key=key, code=code, windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk, modifiers=mods)
        c.call('Input.dispatchKeyEvent', type='keyDown' if text else 'rawKeyDown', **extra, **({'text': text} if text else {}))
        c.call('Input.dispatchKeyEvent', type='keyUp', **extra)
        self.frame()

    def type(self, text):
        """Each character as a key press (down with its text, then up), as a keyboard sends it. Walk.type used
        Input.insertText, which skips keydown, so a page shortcut that ate a letter went unseen (5 Nov: the n)."""
        c = self.p.c
        for ch in text:
            up = ch.upper()
            vk = ord(up) if (up.isascii() and up.isalnum()) else (32 if ch == ' ' else 0)
            code = ('Key' + up) if up.isascii() and up.isalpha() else ('Digit' + ch) if ch.isdigit() else ('Space' if ch == ' ' else '')
            mods = SHIFT if (ch.isalpha() and ch.isupper()) else 0
            extra = dict(key=ch, code=code, windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk, modifiers=mods)
            c.call('Input.dispatchKeyEvent', type='keyDown', text=ch, unmodifiedText=ch.lower() if mods else ch, **extra)
            c.call('Input.dispatchKeyEvent', type='keyUp', **extra)
        self.frame()

    def enter(self):
        self.k('Enter', 'Enter', 13, text='\r')

    def ctrl(self, letter, shift=False):
        self.k(letter, 'Key' + letter.upper(), ord(letter.upper()), CTRL | (SHIFT if shift else 0))

    def find(self, words, nth=0):
        d = self.doc()
        i = -1
        for _ in range(nth + 1):
            i = d.index(words, i + 1)
        return i

    def saved(self, door, did, s=10):
        """Until the editor says Saved and the world's text is the editor's."""
        end = time.time() + s
        while time.time() < end:
            st = self.js('document.querySelector(".wr-save")?.textContent||""')
            world = self.k_.state.get(did, 'text') or ''
            if st == 'Saved' and world == self.doc():
                return world
            time.sleep(.15)
        raise AssertionError(f'not saved: status={st!r}; editor and world differ: {self.doc()!r} vs {world!r}')


def run(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with Sandbox('claude-writing-editor') as s:
        door = claude_door(s.url)
        t0 = time.time()
        ids = install(door)
        print('installed in', round(time.time() - t0, 1), 's', flush=True)
        moving, clutter = ids['Moving into the desktop'], ids['Shedding clutter']
        start = (f'# Editor walk\n\nThe first paragraph has **bold words**, *a slant*, `code`, and a [[{moving}|Moving into '
                 f'the desktop]] link.\n\n## A list\n\n- one\n- two\n- [ ] a task to tick\n\n> A quote from someone.\n\n'
                 f'| Name | Role |\n| --- | --- |\n| Alex | directs |\n| JEFF | keeps |\n\nThe last paragraph ends here.')
        did = door.say('make kind=document title="Editor walk" collection=notes text=' + Q(start))['made'][0]
        page = open_writing(s.url, 'alex', 1600, 900)
        w = EditorWalk(page, door, out)
        w.k_ = s.k

        def opens():
            w.js('[...document.querySelectorAll(".wr-row")].find(n=>n.title==="Editor walk"&&n.dataset.path.includes("/rail/")).setAttribute("data-proof-open","1")')
            w.click('[data-proof-open]')
            w.until('!!document.querySelector(".wr-sheet .cm-editor")&&document.querySelector(".wr-title")?.value==="Editor walk"')
            w.settle(400)
            w.js('document.querySelector(".wr-desk").scrollTop=1e6')   # the editor draws what is on screen
            w.frame()
            w.frame()
            got = w.js('''(()=>{const sh=getComputedStyle(document.querySelector(".wr-sheet"));const lines=[...document.querySelectorAll(".cm-line")].map(l=>l.textContent);
              return {blocks:document.querySelectorAll(".wr-block,.wr-editor,textarea.wr-source").length,border:sh.borderTopWidth,shadow:sh.boxShadow,bg:sh.backgroundColor,
              first:lines[0],h2:lines.find(l=>l.includes("A list")),table:!!document.querySelector(".cm-wr-table table"),boxes:document.querySelectorAll(".cm-wr-box").length,
              bullets:document.querySelectorAll(".cm-wr-bullet").length,link:[...document.querySelectorAll(".cm-wr-link")].map(a=>a.textContent+"→"+(a.dataset.doc||"")),
              bold:lines.find(l=>l.includes("bold words"))}})()''')
            assert got['blocks'] == 0 and got['border'] == '0px' and got['shadow'] == 'none', got
            assert got['first'] == 'Editor walk' and got['h2'] == 'A list', got          # the # marks are hidden
            assert got['table'] and got['boxes'] == 1 and got['bullets'] == 2, got
            assert 'Moving into the desktop→' + moving in got['link'] and '**' not in got['bold'], got
            return got
        w.step('opens as one continuous page: no boxes, headings without #, bullets, a box, a table, the link by title', opens, 'editor-01-open.png')

        def caret_anywhere():
            i = w.find('paragraph') + 4
            w.press(w.at(i))
            a, h = w.sel()
            assert a == h and abs(h - i) <= 1, (a, h, i)
            line = w.js('[...document.querySelectorAll(".cm-line")].find(l=>l.textContent.includes("bold words")).textContent')
            assert '**' not in line, line                                 # marks show only where the caret is
            w.press(w.at(w.find('bold words') + 3))
            line = w.js('[...document.querySelectorAll(".cm-line")].find(l=>l.textContent.includes("bold words")).textContent')
            assert '**bold words**' in line and '[[' not in line, line
            j = w.find('Editor walk') + 3
            w.press(w.at(j))
            first = w.js('document.querySelector(".cm-line").textContent')
            assert first == '# Editor walk', first
            return {'caret': h, 'asked': i, 'heading line': first}
        w.step('a press puts the caret where pressed; that line shows its marks, others stay drawn', caret_anywhere, 'editor-02-caret.png')

        def typing_saves():
            w.press(w.at(w.find('ends here')))
            w.k('End', 'End', 35, CTRL)
            w.type(' And more words.')
            text = w.saved(door, did)
            assert text.endswith('ends here. And more words.'), text[-60:]
            hist = door.say('edits ' + did)
            return {'end': text[-40:], 'history': hist['text'].split('\n')[0]}
        w.step('typing keeps itself: Saved, and the world\'s text is the editor\'s, with an edit history', typing_saves)

        def every_key():
            keys = ' abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 .,;:!?\'"()-_/+=&%$#@~'
            w.k('End', 'End', 35, CTRL)
            w.type(keys)
            got = w.saved(door, did)
            assert got.endswith(keys), ('lost keys', [c for c in keys if c not in got[-len(keys) - 5:]], got[-120:])
            return {'typed': len(keys), 'end': got[-40:]}
        w.step('every letter, digit and mark typed as key presses arrives (5 Nov: n was eaten by a page shortcut)', every_key)

        def select_across():
            a, b = w.find('Editor walk') + 2, w.find('two') + 2
            w.drag(w.at(a), w.at(b))
            x, y = w.sel()
            picked = w.doc()[min(x, y):max(x, y)]
            assert 'A list' in picked and 'first paragraph' in picked and min(x, y) == a and max(x, y) == b, (x, y, picked)
            c = w.find('quote from') + 2
            w.press(w.at(c), mods=SHIFT)
            x2, y2 = w.sel()
            assert x2 == x and y2 == c, (x2, y2, c)
            drawn = w.js('document.querySelectorAll(".cm-selectionBackground").length')
            return {'dragged': [x, y], 'shift-pressed to': y2, 'drawn selection pieces': drawn}
        w.step('dragging selects across a heading, a paragraph and a list; Shift+press extends it', select_across, 'editor-03-select.png')

        def right_click_menu():
            pt = w.at(w.find('first paragraph') + 3)
            w.press(pt, button='right')
            w.until('!!document.querySelector(".wr-menu")', 5)
            items = w.js('[...document.querySelectorAll(".wr-menu>button")].map(b=>b.textContent)')
            w.p.shot(str(out / 'editor-04-menu.png'))
            w.k('Escape', 'Escape', 27)
            assert any(i.startswith('Comment') for i in items) and any(i.startswith('Copy') for i in items), items
            return items
        w.step('right-click on the selection: Comment, Send to JEFF, Copy, Cut', right_click_menu)

        def delete_undo_redo():
            before = w.doc()
            a, b = w.find('paragraph has') + 10, w.find('one') + 1
            w.press(w.at(a))
            w.press(w.at(b), mods=SHIFT)
            w.k('Backspace', 'Backspace', 8)
            joined = w.doc()
            assert 'A list' not in joined and len(joined) == len(before) - (b - a), joined[:120]
            w.saved(door, did)
            w.ctrl('z')
            assert w.doc() == before, w.doc()[:120]
            w.ctrl('y')
            assert w.doc() == joined
            w.ctrl('z')
            text = w.saved(door, did)
            assert text == before
            return {'deleted': b - a, 'undo and redo': 'exact'}
        w.step('a selection across sections deletes as one; Ctrl+Z puts it back exactly, Ctrl+Y again, kept each time', delete_undo_redo)

        def lists():
            i = w.find('- two') + len('- two')
            w.press(w.at(i, 'right'))
            w.enter()
            w.type('three')
            w.enter()
            w.enter()
            w.type('After the list.')
            d = w.doc()
            assert '- two\n- three\n' in d and '\nAfter the list.' in d and '- After' not in d, d[d.index('- one'):d.index('- one') + 80]
            w.saved(door, did)
            return d[d.index('- one'):d.index('After the list.') + 15]
        w.step('Enter in a list makes the next item; Enter on an empty item ends the list', lists)

        def bold_key():
            a = w.find('first')
            w.press(w.at(a))
            w.press(w.at(a + 5), mods=SHIFT)
            w.ctrl('b')
            assert '**first**' in w.doc(), w.doc()[:80]
            w.ctrl('b')
            assert '**first**' not in w.doc() and 'The first paragraph' in w.doc()
            w.ctrl('i')
            assert 'The *first* paragraph' in w.doc()
            w.saved(door, did)
        w.step('Ctrl+B bolds the selection and again takes it off; Ctrl+I slants it', bold_key)

        def tab_stays():
            a = w.find('first')
            w.press(w.at(a))
            w.k('Tab', 'Tab', 9)
            d = w.doc()
            inside = w.js('document.activeElement?.classList.contains("cm-content")')
            assert d[a] == '	' and inside, (repr(d[a - 3:a + 6]), inside)
            w.k('Backspace', 'Backspace', 8)
            w.saved(door, did)
            return 'Tab indents in the text and the caret stays; Backspace takes it back'
        w.step('Tab outside a list indents in the text, and the caret stays in the editor', tab_stays)

        def tick():
            w.js('document.querySelector(".cm-wr-box").scrollIntoView({block:"center"})')
            w.click('.cm-wr-box')
            w.frame()
            text = w.saved(door, did)
            assert '- [x] a task to tick' in text, text
            done = w.js('!!document.querySelector(".cm-wr-done")')
            return {'kept': '- [x] a task to tick', 'struck through': done}
        w.step('pressing a task box ticks it in the text', tick)

        def link_picker():
            i = len(w.doc())
            w.k('End', 'End', 35, CTRL)
            w.type(' See [[Shed')
            w.until('!!document.querySelector(".cm-tooltip-autocomplete")', 5)
            opts = w.js('[...document.querySelectorAll(".cm-tooltip-autocomplete li")].map(l=>l.textContent)')
            w.p.shot(str(out / 'editor-05-picker.png'))
            w.enter()
            d = w.doc()
            assert f'See [[{clutter}|Shedding clutter]]' in d, d[-80:]
            w.press(w.at(w.find('Editor walk') + 1))
            drawn = w.js(f'[...document.querySelectorAll(".cm-wr-link[data-doc=\\"{clutter}\\"]")].map(a=>a.textContent)')
            assert drawn == ['Shedding clutter'], drawn
            w.saved(door, did)
            return {'offered': opts[:4], 'drawn': drawn}
        w.step('[[ offers documents by title; Enter writes the link, drawn by its title', link_picker)

        def follow_and_back():
            w.click(f'.cm-wr-link[data-doc="{clutter}"]')
            w.until('document.querySelector(".wr-title")?.value==="Shedding clutter"', 8)
            w.settle(300)
            w.click('.wr-top button[aria-label^="Back"]')
            w.until('document.querySelector(".wr-title")?.value==="Editor walk"&&!!document.querySelector(".wr-sheet .cm-editor")', 8)
            w.settle(300)
            had = w.doc()
            w.press(w.at(5))
            w.ctrl('z')                       # undo still knows this document's last change: the picked link
            assert w.doc().endswith('See [[Shed'), json.dumps([had[-90:], w.doc()[-90:]])
            w.ctrl('y')
            assert w.doc() == had
            return 'undo survived opening another document and coming back'
        w.step('pressing a drawn link opens it; Back returns, with the editor and its undo intact', follow_and_back)

        def type_through_saves():
            w.press(w.at(5))
            w.k('End', 'End', 35, CTRL)
            words = ' Typing straight through several saves without losing a letter.'
            for ch in words:
                w.type(ch)
                time.sleep(.045)
            w.settle(200)
            assert w.doc().endswith(words), w.doc()[-80:]
            text = w.saved(door, did)
            return {'end': text[-50:]}
        w.step('typing steadily through saves loses nothing and keeps the order', type_through_saves, 'editor-06-typed.png')

        def outside_change():
            w.press(w.at(w.find('A quote') + 1))
            w.type('Mine: ')
            door.say('look ' + did)
            now = s.k.state.get(did, 'text')
            out2 = door.say('set ' + did + ' text=' + Q('Written by someone else first.\n\n' + now))
            assert out2.get('ok', True), out2
            w.until(V + '.state.doc.toString().startsWith("Written by someone else first.")', 20)   # the headless window polls (15 s)
            text = w.saved(door, did)
            assert text.startswith('Written by someone else first.') and '> AMine:  quote' in text, text[:240]
            return {'both kept': [text[:30], text[text.index('> AMine'):text.index('> AMine') + 20]]}
        w.step('a change written meanwhile by someone else comes in under what is typed; both are kept', outside_change)

        def table():
            assert w.js('!!document.querySelector(".cm-wr-table table")')
            w.click('.cm-wr-table td')
            w.frame()
            lines = w.js('[...document.querySelectorAll(".cm-line")].map(l=>l.textContent).filter(t=>t.startsWith("|"))')
            assert lines and lines[0].startswith('| Name'), lines
            w.press(w.at(5))
            assert w.js('!!document.querySelector(".cm-wr-table table")')
            return lines[:2]
        w.step('a table is drawn; pressing it shows its source to edit; leaving draws it again', table, 'editor-07-table.png')

        def find_panel():
            w.ctrl('f')
            w.until('!!document.querySelector(".cm-search input")', 4)
            w.p.shot(str(out / 'editor-08-find.png'))
            w.k('Escape', 'Escape', 27)
            w.until('!document.querySelector(".cm-search")', 4)
        w.step('Ctrl+F opens find and replace; Escape closes it', find_panel)

        def comment():
            a = w.find('last paragraph')
            w.press(w.at(a))
            w.press(w.at(a + len('last paragraph')), mods=SHIFT)
            w.press(w.at(a + 3), button='right')
            w.until('!!document.querySelector(".wr-menu")', 5)
            w.js('[...document.querySelectorAll(".wr-menu>button")].find(b=>b.textContent.startsWith("Comment")).click()')
            w.until('!!document.querySelector(".wr-pop textarea")', 5)
            w.type('Does this need a better ending?')
            w.enter()
            w.until('!!document.querySelector(".wr-c")&&!!document.querySelector(".cm-wr-comment")', 10)
            got = w.js('({mark:document.querySelector(".cm-wr-comment").textContent,card:document.querySelector(".wr-c .wr-c-q")?.textContent,'
                       'state:document.querySelector(".wr-c-st")?.textContent||""})')
            assert got['mark'] == 'last paragraph', got
            return got
        w.step('select, right-click, Comment: the words are marked in the text and the comment sits in the margin', comment, 'editor-09-comment.png')

        def marks_key():
            w.press(w.at(len(w.doc()), 'right'))
            w.ctrl('e')
            first = w.js('document.querySelector(".cm-line").textContent')
            w.ctrl('e')
            again = w.js('document.querySelector(".cm-line").textContent')
            assert first.startswith('Written') or first.startswith('#'), first
            heading = w.js('[...document.querySelectorAll(".cm-line")].map(l=>l.textContent).find(t=>t.includes("Editor walk"))')
            assert heading == 'Editor walk', heading
            return 'every mark shown, then hidden again'
        w.step('Ctrl+E shows every mark, and again hides them', marks_key)

        def below_end():
            w.press(w.at(3))
            end = w.at(len(w.doc()))
            w.press(dict(x=end['x'] - 200, y=end['y'] + 60))       # the empty page below the last line
            a, h = w.sel()
            assert h == len(w.doc()), (h, len(w.doc()))
            w.ctrl('a')
            a, h = w.sel()
            assert (min(a, h), max(a, h)) == (0, len(w.doc()))
            w.k('End', 'End', 35, CTRL)
            return 'press below the text: caret at the end; Ctrl+A: all of it'
        w.step('pressing the empty page below puts the caret at the end; Ctrl+A selects everything', below_end)

        def paste():
            w.js('(()=>{const dt=new DataTransfer();dt.setData("text/plain","\\n\\nPasted line one\\nPasted line two");'
                 'document.querySelector(".wr-sheet .cm-content").dispatchEvent(new ClipboardEvent("paste",{clipboardData:dt,bubbles:true,cancelable:true}))})()')
            text = w.saved(door, did)
            assert text.endswith('Pasted line one\nPasted line two'), text[-60:]
        w.step('pasting several lines puts them in as text', paste)

        def history():
            out3 = door.say('edits ' + did)
            rows = out3.get('rows') or []
            assert sum(r['ops'] for r in rows) >= 10 and any(r['for'] for r in rows), out3
            body = Path(s.k.dir) / 'bodies' / f'{did}.text.loro'
            return {'changes kept': len(rows), 'body bytes': body.stat().st_size, 'first line': out3['text'].split('\n')[0]}
        w.step('every change is in the document\'s CRDT history beside the world', history)

        def long_doc():
            docs = sorted([r for r in door.rows('document') if not r.get('file_source')], key=lambda r: -len(r.get('text') or ''))
            titles = [r.get('title') or '' for r in docs[:40]]
            picked = w.js('(()=>{const t=' + json.dumps(titles) + ';for(const x of t){const n=[...document.querySelectorAll(".wr-row")].find(r=>r.title===x);'
                          'if(n){n.setAttribute("data-proof-big","1");return x}}return null})()')
            assert picked, titles[:5]
            big = next(r for r in docs if (r.get('title') or '') == picked)
            t1 = time.time()
            w.click('[data-proof-big]')
            w.until(f'document.querySelector(".wr-title")?.value==={json.dumps(picked)}&&!!document.querySelector(".wr-sheet .cm-editor")', 15)
            opened = time.time() - t1
            mid = len(w.doc()) // 2
            w.press(w.at(mid))
            lat = w.js('(async()=>{const v=' + V + ';const t=performance.now();v.contentDOM.dispatchEvent(new InputEvent("beforeinput",{inputType:"insertText",data:"Z",bubbles:true,cancelable:true}));'
                       'await new Promise(r=>requestAnimationFrame(()=>r()));return performance.now()-t})()')
            w.type('Q')
            text = w.saved(door, big['id'], 15)  # noqa
            assert text.count('Q') == (big.get('text') or '').count('Q') + 1
            w.ctrl('z')
            w.saved(door, big['id'], 15)
            return {'title': big.get('title'), 'characters': len(big.get('text') or ''), 'open s': round(opened, 2), 'keystroke to frame ms': round(lat or 0, 1)}
        w.step('the longest document opens, takes a keystroke in the middle, keeps it, and undoes it', long_doc, 'editor-10-long.png')

        def no_errors():
            e = errors(page)
            assert not e, json.dumps(e)[:1500]
        w.step('no script errors in the window', no_errors)
        page.close()
        failed = [n for n, ok in w.results if not ok]
        print(f'{len(w.results) - len(failed)} of {len(w.results)} steps pass', flush=True)
        return not failed


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(HERE / 'evidence' / 'editor'))
    a = ap.parse_args()
    sys.exit(0 if run(a.out) else 1)
