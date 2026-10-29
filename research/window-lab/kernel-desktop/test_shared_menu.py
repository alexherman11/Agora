"""The shared right-click menu (card dk1344, pages/menu.js), in a hidden browser over a trial world.

The view is made by this test, after the change, with no menu code of its own: a plain component lens listing tasks.
Right-clicking its parts must give a menu that fits: a Needs-you task gets Delete, another person's does not, any task
gets Look and its own words, selected words get Comment (quoted into the Conversation), an empty spot gets the window's
ask box; and a lens with the painter's old right_click=ask gets the same shared menu. No window appears on screen.
"""
import json
from pathlib import Path
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / "kernel-lab"
sys.path[:0] = [str(HERE), str(LAB)]
from test_kdesk import Desk
from painter.install import taskboard, upsert, activate, Q
from painter.browser import Page
import widget_browser

LENS = """root : column, gap 12px
  title : text "A view made after the menu"
  gap : text " "
  rows : column, gap 6px, of tag:taskboard-task as t, each line
line : row, gap 8px
  what : text "$t.title"
  who : text "$t.who"
"""


class SharedMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        widget_browser.Browser.also_allow = ("/see", "/do")   # the menu reads and acts as the viewer, as on the desktop
        (HERE / "state").mkdir(exist_ok=True)           # the hidden browser's disposable profile lives there
        cls.d = Desk()
        cls.door = taskboard.Door(cls.d.url, cls.d.entry.token("alex"))
        say = cls.door.say
        # the live world's ask verb (read from `help ask` on 8810, 29 Oct); a trial world starts without it
        say('verb ask steps=' + Q('make kind=ask-request about=$1 text=$text where=$where status=open')
            + ' help=' + Q('ask <thing> text= where=: ask for a change (stand-in for the live verb)'))
        cls.mine = say('make kind=taskboard-task title="Call the plumber" who=Alex lane=Now')["made"][0]
        cls.theirs = say('make kind=taskboard-task title="Draft the agenda" who=JEFF lane=Now')["made"][0]
        if not [c for c in cls.door.rows("chat") if c.get("name") == "Conversation"]:
            say('make kind=chat name=Conversation about="Alex and JEFF"')
        cls.chat = next(c["id"] for c in cls.door.rows("chat") if c.get("name") == "Conversation")
        name = "fresh-menu-view-%d" % int(time.time())
        cls.lens = upsert(cls.door, "lens", name, title="Fresh view", painter="components", text=LENS)
        cls.widget = activate(cls.door, name, "Fresh view")
        cls.p = Page(cls.d.url, cls.d.entry.token("alex"), cls.widget, width=1100, height=760)
        cls.p.until('document.body.innerText.includes("Call the plumber")', 30)
        # what each pressed entry's line got back; the hidden browser's requests move only while CDP is being read
        cls.p.c.js('window.__did=[];addEventListener("agora-menu-did",e=>window.__did.push(e.detail));0')

    @classmethod
    def tearDownClass(cls):
        cls.p.close(); cls.d.close()

    # ---- helpers: frame coordinates are made page coordinates; presses are real CDP mouse input
    def at_text(self, words, start=None, end=None):
        """The page point in the middle of `words` drawn in the frame (or of its [start:end] slice, selecting it)."""
        js = """(()=>{const w=%s,s=%s,e=%s;const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
          while(n=walk.nextNode())if(n.data===w)break;if(!n)return null;const r=document.createRange();
          r.setStart(n,s===null?0:s);r.setEnd(n,e===null?n.length:e);
          if(s!==null){const sel=getSelection();sel.removeAllRanges();sel.addRange(r)}
          const b=r.getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2}})()""" % (
            json.dumps(words), json.dumps(start), json.dumps(end))
        pt = self.p.js(js)
        self.assertTrue(pt, words)
        off = self.p.c.js('(()=>{const r=document.querySelector("iframe").getBoundingClientRect();return {x:r.x,y:r.y}})()')
        return dict(x=pt["x"] + off["x"], y=pt["y"] + off["y"])

    def press(self, pt, button="left"):
        for t in ("mousePressed", "mouseReleased"):
            self.p.c.call("Input.dispatchMouseEvent", type=t, button=button, clickCount=1, **pt)

    def menu(self, wait_for):
        self.p.c.until('(()=>{const m=document.querySelector(".ag-menu");return !!m&&!m.querySelector(".ag-wait")&&'
                       'm.innerText.includes(%s)})()' % json.dumps(wait_for), 15)
        return self.p.c.js('[...document.querySelectorAll(".ag-menu button")].map(b=>b.firstChild.textContent)')

    def press_item(self, label):
        pt = self.p.c.js('(()=>{const b=[...document.querySelectorAll(".ag-menu button")].find(b=>b.firstChild.textContent===%s);'
                         'const r=b.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()' % json.dumps(label))
        time.sleep(.35)                                   # a menu takes no click in its first 300 ms
        self.press(pt)

    def type_enter(self, words):
        if words:
            self.p.c.call("Input.insertText", text=words)
        for t in ("keyDown", "keyUp"):
            self.p.c.call("Input.dispatchKeyEvent", type=t, key="Enter", code="Enter", windowsVirtualKeyCode=13)

    def close_menu(self):
        self.p.c.call("Input.dispatchKeyEvent", type="keyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)
        self.p.c.until('!document.querySelector(".ag-menu")')

    # ---- the checks
    def test_1_a_task_gets_its_own_words_and_another_persons_has_no_delete(self):
        self.press(self.at_text("Draft the agenda"), "right")
        items = self.menu("Draft the agenda")
        self.assertIn("Look", items)
        self.assertNotIn("Delete", items)
        # its own words, from `actions`: every word offered needs nothing more than the task
        own = items[items.index("Look") + 1:]
        self.assertTrue([w for w in own if not w.startswith("Open in ")], items)
        self.assertTrue(self.p.c.js('!!document.querySelector(".ag-menu input[placeholder^=Ask]")'))
        self.close_menu()

    def test_2_selected_words_comment_into_the_conversation(self):
        self.press(self.at_text("Call the plumber", 9, 16), "right")       # "plumber"
        items = self.menu("plumber")
        self.assertEqual(["Comment", "Copy"], items[:2])
        self.press_item("Comment")
        self.p.c.until('document.activeElement&&document.activeElement.getAttribute("aria-label")==="Your comment on these words"')
        before = self.p.c.js('window.__did.length')
        self.type_enter("Which one?")
        self.p.c.until('window.__did.length>%d' % before, 15)
        self.assertTrue(self.p.c.js('window.__did[window.__did.length-1].ok'), self.p.c.js('window.__did[window.__did.length-1]'))
        said = self.d.wait(lambda: [r for r in self.door.rows("said") if "> plumber" in str(r.get("text", ""))], 10)
        text = said[-1]["text"]
        self.assertTrue(text.startswith("Which one?"), text)
        self.assertIn("[[%s|Call the plumber]]" % self.mine, text)
        self.assertEqual(self.mine, said[-1].get("about"))
        self.p.c.until('!document.querySelector(".ag-menu")')

    def test_3_an_empty_spot_asks_about_the_window(self):
        self.press(self.at_text("A view made after the menu"), "right")
        items = self.menu("This window")
        self.assertNotIn("Delete", items)
        self.p.c.until('document.activeElement&&document.activeElement.placeholder==="Ask for a change…"')
        before = self.p.c.js('window.__did.length')
        self.type_enter("Make the title bigger")
        self.p.c.until('window.__did.length>%d' % before, 15)
        self.assertTrue(self.p.c.js('window.__did[window.__did.length-1].ok'), self.p.c.js('window.__did[window.__did.length-1]'))
        asks = self.d.wait(lambda: [r for r in self.door.rows("ask-request") if r.get("text") == "Make the title bigger"], 10)
        self.assertEqual(self.widget, asks[-1].get("about"))

    def test_3b_the_windows_own_strip_has_the_menu_too(self):
        pt = self.p.c.js('(()=>{const r=document.querySelector(".strip .name").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()')
        self.press(pt, "right")
        self.menu("This window")
        self.p.c.until('document.activeElement&&document.activeElement.placeholder==="Ask for a change…"')
        before = self.p.c.js('window.__did.length')
        self.type_enter("Give the strip a clock")
        self.p.c.until('window.__did.length>%d' % before, 15)
        asks = self.d.wait(lambda: [r for r in self.door.rows("ask-request") if r.get("text") == "Give the strip a clock"], 10)
        self.assertEqual(self.widget, asks[-1].get("about"))

    def test_4_a_lens_with_the_old_ask_only_menu_gets_the_shared_one(self):
        self.door.say("look " + self.lens); self.door.say("set " + self.lens + " right_click=ask")
        time.sleep(1.5)
        self.press(self.at_text("Draft the agenda"), "right")
        self.assertIn("Look", self.menu("Draft the agenda"))
        self.assertFalse(self.p.js('!!document.querySelector(".ask-menu")'))
        self.close_menu()

    def test_6_a_view_that_draws_its_own_menu_keeps_it(self):
        self.p.js('document.querySelector("[data-fact-title=\\"Draft the agenda\\"]").addEventListener("contextmenu",e=>e.preventDefault());0')
        self.press(self.at_text("Draft the agenda"), "right")
        time.sleep(.8); self.p.c.js('0')
        self.assertFalse(self.p.c.js('!!document.querySelector(".ag-menu")'))

    def test_5_a_needs_you_task_gets_delete_and_delete_forgets_it(self):
        self.press(self.at_text("Call the plumber"), "right")
        items = self.menu("Call the plumber")
        self.assertIn("Delete", items)
        self.assertIn("Look", items)
        self.p.shot(HERE / "evidence" / "shared-menu-needs-you.png")
        before = self.p.c.js('window.__did.length')
        self.press_item("Delete")
        self.p.c.until('window.__did.length>%d' % before, 15)
        self.assertTrue(self.p.c.js('window.__did[window.__did.length-1].ok'), self.p.c.js('window.__did'))
        self.d.wait(lambda: not [r for r in self.door.rows("taskboard-task") if r["id"] == self.mine], 10)
        self.p.until('!document.body.innerText.includes("Call the plumber")', 15)
        self.assertFalse([e for e in self.p.errors if e.get("method") == "Runtime.exceptionThrown"], self.p.errors[-3:])


POSTS = """root : column, gap 10px
  title : text "Posts in a view made after the menu"
  feed : column, gap 8px, of tag:said as s, each post
post : column, gap 4px
  body : text "$s.text"
  answer : text "Answer"
    on click do set $s.item seen=yes
"""


class PostsButtonsAndWindows(SharedMenu):
    """Card dk1344 (dk1476): posts, a button inside a post, and the window's own words, in a second fresh view opened
    as a desktop window (win=), the way kd_window opens one. Reuses SharedMenu's helpers; none of its checks rerun."""
    @classmethod
    def setUpClass(cls):
        widget_browser.Browser.also_allow = ("/see", "/do")
        (HERE / "state").mkdir(exist_ok=True)
        cls.d = Desk()
        cls.door = taskboard.Door(cls.d.url, cls.d.entry.token("alex"))
        say = cls.door.say
        if not [c for c in cls.door.rows("chat") if c.get("name") == "Conversation"]:
            say('make kind=chat name=Conversation about="Alex and JEFF"')
        cls.chat = next(c["id"] for c in cls.door.rows("chat") if c.get("name") == "Conversation")
        say("say %s text=%s" % (cls.chat, Q("The kettle is broken again")))
        cls.post = cls.d.wait(lambda: [r for r in cls.door.rows("said") if r.get("text") == "The kettle is broken again"], 10)[-1]["id"]
        name = "fresh-posts-view-%d" % int(time.time())
        upsert(cls.door, "lens", name, title="Fresh posts", painter="components", text=POSTS)
        from painter.install import widget_source
        cls.widget = upsert(cls.door, "widget", name, title="Fresh posts", style="bars", component_lens=name, code=widget_source())
        say("look " + cls.widget)
        say("widget %s surface=window grants=%s only=kind:said" % (cls.widget, Q("window.surface rows look look-view history components help component-health component-action set hear:make hear:set hear:forget hear:undo hear:component hear:component-action")))
        assert cls.d.say("window.open " + name, "alex")["ok"]
        cls.win = cls.d.wait(lambda: [w for w in cls.d.windows() if w.get("shows") == name], 10)[0]["id"]
        cls.p = Page(cls.d.url, cls.d.entry.token("alex"), cls.widget + "&win=" + cls.win, width=1100, height=760)
        cls.p.until('document.body.innerText.includes("The kettle is broken again")', 30)
        cls.p.c.js('window.__did=[];addEventListener("agora-menu-did",e=>window.__did.push(e.detail));0')

    def test_7_a_button_inside_a_post_gives_the_posts_menu(self):
        self.press(self.at_text("Answer"), "right")
        items = self.menu("Look")
        self.assertEqual(self.post, self.p.c.js('document.querySelector(".ag-menu").dataset.thing'))
        self.assertNotIn("Comment", items)                            # nothing selected
        self.close_menu()

    def test_8_words_in_a_post_comment_into_the_conversation_with_a_link_back(self):
        self.press(self.at_text("The kettle is broken again", 4, 10), "right")   # "kettle"
        self.assertEqual(["Comment", "Copy"], self.menu("kettle")[:2])
        self.press_item("Comment")
        self.p.c.until('document.activeElement&&document.activeElement.getAttribute("aria-label")==="Your comment on these words"')
        before = self.p.c.js('window.__did.length')
        self.type_enter("")                                           # no words of your own: the quote alone
        self.p.c.until('window.__did.length>%d' % before, 15)
        said = self.d.wait(lambda: [r for r in self.door.rows("said") if str(r.get("text", "")).startswith("> kettle")], 10)
        self.assertIn("[[%s|" % self.post, said[-1]["text"])
        self.assertEqual(self.post, said[-1].get("about"))
        self.assertEqual(self.chat, said[-1].get("chat"))

    def test_9_an_empty_spot_gives_the_windows_own_words(self):
        self.press(self.at_text("Posts in a view made after the menu"), "right")
        items = self.menu("window")
        self.assertTrue([w for w in items if w.startswith("window.")], items)
        self.close_menu()

    # SharedMenu's checks belong to its own view; not rerun here
    test_1_a_task_gets_its_own_words_and_another_persons_has_no_delete = None
    test_2_selected_words_comment_into_the_conversation = None
    test_3_an_empty_spot_asks_about_the_window = None
    test_3b_the_windows_own_strip_has_the_menu_too = None
    test_4_a_lens_with_the_old_ask_only_menu_gets_the_shared_one = None
    test_5_a_needs_you_task_gets_delete_and_delete_forgets_it = None
    test_6_a_view_that_draws_its_own_menu_keeps_it = None


if __name__ == "__main__":
    unittest.main(verbosity=2)
