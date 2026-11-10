# health: room test
"""Real desk commands and repaints on a fresh in-memory world; never Alex's chat."""
import copy
import json
import pickle
import re
import unittest
import uuid
from pathlib import Path

import explore
import scene
import viewer_tabs
from tab_history import Browser

HERE = Path(__file__).resolve().parent


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


class TabsTests(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d._session = "fixture"
        self.w = self.d.world
        self.w.me = "alex"
        self.root = self.w.root
        self.line("look")
        self.home = self.make(self.root, 'kind=surface title=Home')
        self.a = self.make(self.home, 'kind=note title=First text="First long page"')
        self.b = self.make(self.home, 'kind=note title=Second text="Second page"')
        self.c = self.make(self.home, 'kind=note title=Third text="Third page"')
        self.page = self.make(self.home, 'kind=note title=reader tags=lens text="page : text $text"')
        self.v = self.make(self.home, f'kind=note title=Viewer role=home-view actor=alex viewing={self.a} with=reader pins="{self.b}"')
        self.draft = self.make(self.home, 'kind=note title="Fixture draft" role=draft text="Unsent words" to=jeff context=deliberate reply_to=m1 quote="Selected words"')
        self.before = copy.deepcopy(self.w.subjects[self.w.nodes[self.draft]["subject"]])

    def line(self, line, ok=True):
        r = self.d.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        text = r.get("text", "")
        failed = bool(r.get("error") or re.search(r"(^|\n)(ERR|!!)", text))
        self.assertEqual(failed, not ok, f"{line}\n{r}")
        return text

    def make(self, parent, body):
        self.line(f"look {parent}")
        return re.search(r"created ([af]\d+)", self.line(f"do create {parent} {body}"))[1]

    def props(self):
        return viewer_tabs.props(self.w, self.v)

    def act(self, action, more="", ok=True):
        self.line(f"read {self.v}")
        return self.line(f"do browse {self.v} action={action} {more}", ok=ok)

    def state(self):
        return Browser.restore(json.loads(self.props()["tabs_state"]))

    def unchanged_draft(self):
        self.assertEqual(self.before, self.w.subjects[self.w.nodes[self.draft]["subject"]])

    def test_migrate_history_branch_reload_and_lens(self):
        self.act("init")
        self.assertEqual(self.a, self.props()["viewing"])
        self.assertEqual("reader", self.props()["with"])
        state = self.props()["tabs_state"]
        self.act("init")
        self.assertEqual(state, self.props()["tabs_state"])
        self.act("open", f"target={self.b}")
        self.act("open", f"target={self.c}")
        self.act("back")
        self.assertEqual(self.b, self.props()["viewing"])
        self.act("forward")
        self.assertEqual(self.c, self.props()["viewing"])
        self.act("back")
        self.act("open", f"target={self.a}")
        self.assertEqual("no", self.props()["can_forward"])
        self.act("forward", ok=False)
        self.act("position", "scroll=233 zoom=1.25")
        self.act("reload")
        b = self.state()
        t = b.tabs[b.active]
        self.assertEqual(3, len(t.entries))
        self.assertEqual({"scroll": 233, "zoom": 1.25}, t.entries[t.index].view)
        self.act("lens", "lens=reader")
        self.assertEqual("reader", self.props()["with"])
        self.act("back")
        self.assertEqual("", self.props()["with"])
        self.assertEqual(self.b, self.props()["pins"])
        self.unchanged_draft()

    def test_tabs_selection_close_and_persistence(self):
        self.act("init")
        first = self.props()["active_tab"]
        self.act("new", f"target=agora://fixture/item/{self.b}")
        second = self.props()["active_tab"]
        self.assertNotEqual(first, second)
        self.act("select", f"tab={first}")
        self.assertEqual(self.a, self.props()["viewing"])
        self.act("select", f"tab={second}")
        self.assertEqual(self.b, self.props()["viewing"])
        # A new dispatcher/model object has no browser singleton or hidden layout.
        restored = Browser.restore(json.loads(self.props()["tabs_state"]))
        self.assertEqual(second, restored.active)
        # Serialize this synthetic desk only, in memory; no session file access.
        self.d = pickle.loads(pickle.dumps(self.d))
        self.w = self.d.world
        self.act("select", f"tab={first}")
        self.assertEqual(self.a, self.props()["viewing"])
        self.act("select", f"tab={second}")
        self.act("close", f"tab={second}")
        self.assertEqual(first, self.props()["active_tab"])
        self.act("select", f"tab={second}", ok=False)
        self.act("close")
        self.assertEqual("", self.props()["viewing"])
        self.assertEqual("1", self.props()["tab_count"])
        self.unchanged_draft()

    def test_refusals_leave_all_world_state_unchanged(self):
        self.act("init")
        for target in ["https://example.test/", "local://selection/fake", "file:///C:/private",
                       "javascript:alert(1)", f"agora://elsewhere/item/{self.b}",
                       f"agora://fixture/item/{self.b}#unsupported", "agora://fixture/item/a999999",
                       f"agora://fixture/item/{self.b}?lens=missing"]:
            before = (copy.deepcopy(self.w.nodes), copy.deepcopy(self.w.subjects), len(self.w.events))
            self.act("open", f"target={q(target)}", ok=False)
            self.assertEqual(before, (self.w.nodes, self.w.subjects, len(self.w.events)))
        self.unchanged_draft()

    def test_projection_tampering_has_no_navigation_authority(self):
        self.act("init")
        note = next(i for i in self.w.nodes if viewer_tabs.props(self.w, i).get("role") == "viewer-tab")
        self.line(f"read {note}")
        self.line(f'do prop {note} active=no label="Forged target"')
        self.act("reload")
        self.assertEqual(self.a, self.props()["viewing"])
        self.assertEqual("First", viewer_tabs.props(self.w, note)["label"])
        self.unchanged_draft()

    def chrome(self, viewer=None):
        return {i for i in self.w.nodes
                if viewer_tabs.props(self.w, i).get("viewer") == (viewer or self.v)
                and viewer_tabs.props(self.w, i).get("role") == "viewer-tab"}

    def test_projection_titles_and_legacy_placement_reconcile(self):
        self.act("init")
        note = next(iter(self.chrome()))
        # Emulate the old landed layout (a direct Home child).
        self.line(f"read {note}")
        self.line(f"do move {note} into={self.home}")
        self.act("open", f"target={self.b}")
        self.assertEqual("Second", self.w.subjects[self.w.nodes[note]["subject"]]["title"])
        self.assertEqual("Second", viewer_tabs.props(self.w, note)["label"])
        parent = self.w.nodes[note]["parent"]
        self.assertEqual("viewer-tabs", viewer_tabs.props(self.w, parent)["role"])
        self.assertEqual(self.v, viewer_tabs.props(self.w, parent)["viewer"])
        self.act("back")
        self.assertEqual("First", self.w.subjects[self.w.nodes[note]["subject"]]["title"])
        self.unchanged_draft()

    def test_projection_slots_bounded_over_close_reopen_and_restore(self):
        self.act("init")
        first = self.props()["active_tab"]
        self.act("new", f"target={self.b}")
        expected_nodes, expected_subjects = len(self.w.nodes), len(self.w.subjects)
        for _ in range(25):
            self.act("close")
            self.act("init")
            self.act("reload")
            self.act("new", f"target={self.c}")
        self.assertEqual(expected_nodes, len(self.w.nodes))
        self.assertEqual(expected_subjects, len(self.w.subjects))
        self.assertEqual(2, len(self.chrome()))
        self.d = pickle.loads(pickle.dumps(self.d))
        self.w = self.d.world
        self.act("select", f"tab={first}")
        self.act("close")
        self.act("close")
        self.assertEqual(expected_nodes, len(self.w.nodes))
        closed = [i for i in self.chrome() if viewer_tabs.props(self.w, i)["closed"] == "yes"]
        self.assertEqual(1, len(closed))
        self.assertEqual("Closed tab", self.w.subjects[self.w.nodes[closed[0]]["subject"]]["title"])
        self.assertEqual("", viewer_tabs.props(self.w, closed[0])["label"])
        self.unchanged_draft()

    def test_projection_actor_isolation_and_forgery_refusal(self):
        self.act("init")
        other = self.make(self.home, f"kind=note title=Other role=home-view actor=other viewing={self.b}")
        self.w.me = "other"
        self.d.dispatch("desk", {"line": "look", "whole": True, "reply": uuid.uuid4().hex})
        self.line(f"read {other}")
        self.line(f"do browse {other} action=init")
        other_before = copy.deepcopy([(i, self.w.nodes[i],
                                       self.w.subjects[self.w.nodes[i]["subject"]])
                                      for i in self.chrome(other)])
        self.w.me = "alex"
        self.d.dispatch("desk", {"line": "look", "whole": True, "reply": uuid.uuid4().hex})
        self.act("new", f"target={self.c}")
        self.assertEqual(other_before, [(i, self.w.nodes[i], self.w.subjects[self.w.nodes[i]["subject"]])
                                        for i in self.chrome(other)])
        # A claimed role/viewer from another actor grants no reconciliation authority.
        self.make(self.home, f"kind=note title=Foreign role=viewer-tab viewer={self.v} actor=other tab=forged")
        before = copy.deepcopy((self.w.nodes, self.w.subjects, self.w.events))
        self.act("reload", ok=False)
        self.assertEqual(before, (self.w.nodes, self.w.subjects, self.w.events))

    def test_search_excludes_chrome_only_when_explicitly_requested(self):
        import knife
        self.act("init")
        self.act("new", f"target={self.a}")
        plain = knife.parse_selection(self.w, "title:First")[0]
        self.assertIn(self.a, plain)
        self.assertTrue(self.chrome() & set(plain))
        exclusion = ",-prop:role=viewer-tab,-prop:role=viewer-tabs"
        # Native selectors remain general: exclusion belongs to the staged
        # search lens, not a global note-hiding rule.
        for query in ("title:First", "?First"):
            selected = knife.parse_selection(self.w, query + exclusion)[0]
            self.assertIn(self.a, selected)
            self.assertFalse(self.chrome() & set(selected))
        self.assertIn(self.b, knife.parse_selection(self.w, "title:Second" + exclusion)[0])

    def test_search_staged_hunks_roundtrip_and_repaint(self):
        stage = HERE.parents[1] / "desktop/browsing/tabs"
        original = (HERE.parents[1] / "desktop/home-search/home-search.lens").read_text(encoding="utf-8")
        text = original
        hunks = json.loads((stage / "search-exclusions.json").read_text(encoding="utf-8"))["a6788"]
        for hunk in hunks:
            self.assertEqual(1, text.count(hunk["old"]))
            text = text.replace(hunk["old"], hunk["new"])
        restored = text
        for hunk in reversed(hunks):
            self.assertEqual(1, restored.count(hunk["new"]))
            restored = restored.replace(hunk["new"], hunk["old"])
        self.assertEqual(original, restored)
        for path in (stage / "view.verb", stage / "open-found.verb"):
            self.make(self.home, f"kind=note title={path.stem} tags=verb on=house text=" +
                      q(path.read_text(encoding="utf-8")))
        self.make(self.home, "kind=note title=Layout role=home-layout actor=alex")
        base_style = (HERE / "desk-shell/style/calm.style").read_text(encoding="utf-8")
        roles = sorted(set(re.findall(r"^\s+role ([\w.]+)", text, re.M)))
        self.make(self.home, "kind=note title=search-style tags=style text=" +
                  q(base_style + "\n" + "\n".join("role " + r + " : ink" for r in roles)))
        self.make(self.home, "kind=note title=home-search tags=lens style=search-style text=" + q(text))
        self.act("init")
        self.act("new", f"target={self.a}")
        self.line(f"read {self.v}")
        self.line(f'do prop {self.v} find=First')
        painted, _ = scene.scene_for(self.d, "home-search")
        self.assertNotIn("refused", str(painted).lower())
        def commands(value):
            if isinstance(value, dict):
                if value.get("on") == "click":
                    yield value.get("line", "")
                for x in value.values():
                    yield from commands(x)
            elif isinstance(value, list):
                for x in value:
                    yield from commands(x)
        opened = [line for line in commands(painted) if "open-found" in line]
        self.assertTrue(any(f"open-found {self.a} " in line for line in opened))
        self.assertFalse(any(f"open-found {i} " in line for i in self.chrome() for line in opened))
        self.unchanged_draft()

    def test_reusing_projection_slot_is_fully_undoable(self):
        self.act("init")
        self.act("new", f"target={self.b}")
        self.act("close")
        before = copy.deepcopy({i: (viewer_tabs.props(self.w, i),
                                   self.w.subjects[self.w.nodes[i]["subject"]]["title"],
                                   self.w.nodes[i]["parent"]) for i in self.chrome() | {self.v}})
        offset = len(self.w.events)
        self.act("new", f"target={self.c}")
        events = [e["id"] for e in self.w.events[offset:]]
        self.assertEqual(2, len(self.chrome()))
        for event in reversed(events):
            self.w.undo(event)
        after = {i: (viewer_tabs.props(self.w, i),
                     self.w.subjects[self.w.nodes[i]["subject"]]["title"],
                     self.w.nodes[i]["parent"]) for i in self.chrome() | {self.v}}
        self.assertEqual(before, after)
        self.unchanged_draft()

    def test_selection_composition_tracks_all_events_and_noops(self):
        self.act("init")
        self.line(f"read {self.v}")
        state = self.props()["tabs_state"]
        # Selection composition must carry all native events for undo, not just
        # the final viewer prop. Its no-op receipt must not contain a None event.
        self.line("do browse prop:role=home-view,prop:actor=alex action=init")
        self.assertEqual(state, self.props()["tabs_state"])
        self.line(f"do browse prop:role=home-view,prop:actor=alex action=new target={self.b}")
        via = [e for e in self.w.events if e.get("via", "").startswith("browse prop:")]
        self.assertTrue(any(e["verb"] == "create" for e in via))
        self.assertTrue(any(e["verb"] == "prop" and e["target"] == self.v for e in via))
        # Undo every event in the native receipt: no orphan chrome or active tab.
        for e in reversed(via):
            self.w.undo(e["id"])
        self.assertEqual(state, self.props()["tabs_state"])
        self.unchanged_draft()

    def test_remember_scope_participates_in_reuse_fingerprint(self):
        import lens_ir
        # A scope can be the ONLY reference to a frame field. Cached repeated
        # parts must still change when a tab changes its reading identity.
        node = {"emit": {"remember": "$v.reading_key", "role_when": []},
                "bind": None, "place": None, "guard": None, "lets": [], "acts": [], "kids": []}
        self.assertIn(("v", "reading_key"), lens_ir._static(node, {}, {})[1])

    def test_staged_hunks_roundtrip_and_refuse_overlapping_drift(self):
        import importlib.util
        path = HERE.parents[1] / "desktop/browsing/tabs/stage.py"
        spec = importlib.util.spec_from_file_location("tabs_stage", path)
        stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        original = json.loads((stage.HERE / "originals.json").read_text(encoding="utf-8"))
        plan = stage.patches()
        changed = stage.prepare(original, plan)
        for item, file in stage.FILES.items():
            self.assertEqual((stage.HERE / file).read_text(encoding="utf-8").rstrip("\n"), changed[item])
        self.assertEqual(original, stage.prepare(changed, plan, reverse=True))
        outside = {k: "# unrelated edit\n" + v for k, v in original.items()}
        self.assertTrue(stage.prepare(outside, plan)["a5486"].startswith("# unrelated edit\n"))
        drift = dict(original)
        drift["a5486"] = drift["a5486"].replace('back : text "Back"', 'back : text "Changed"')
        with self.assertRaises(ValueError):
            stage.prepare(drift, plan)
        self.assertEqual(original["a6194"], drift["a6194"])

    def test_corrupt_snapshot_and_forged_web_entry_refuse_without_writes(self):
        self.act("init")
        state = json.loads(self.props()["tabs_state"])
        state["tabs"][0]["entries"][0]["target"] = {"kind": "web", "address": "https://example.test/"}
        for raw in ("{bad json", json.dumps(state)):
            self.line(f"read {self.v}")
            self.line(f"do prop {self.v} tabs_state={q(raw)}")
            n = len(self.w.events)
            self.act("select", ok=False)
            self.assertEqual(n, len(self.w.events))

    def test_deleted_target_and_other_actor_refuse(self):
        self.act("init")
        self.act("open", f"target={self.b}")
        # Remove the old appearance from this fixture without granting new reads.
        del self.w.nodes[self.a]
        before = self.props()["tabs_state"]
        self.act("back", ok=False)
        self.assertEqual(before, self.props()["tabs_state"])
        self.w.me = "someone-else"
        self.act("new", ok=False)

    def test_staged_world_repaint_and_routes(self):
        stage = HERE.parents[1] / "desktop" / "browsing" / "tabs"
        for path in [stage / "view.verb", stage / "open-found.verb"]:
            self.make(self.home, f"kind=note title={path.stem} tags=verb on=house text={q(path.read_text(encoding='utf-8'))}")
        original = json.loads((stage / "originals.json").read_text(encoding="utf-8"))
        self.make(self.home, 'kind=note title=unview tags=verb on=house text=' + q(original["a6790"]))
        panel = self.make(self.home, 'kind=note title="Viewer panel" role=home-panel actor=alex lens=home-viewer shelf=no')
        chat = self.make(self.home, 'kind=note title="Fixture chat panel" role=home-panel actor=alex lens=jeff-chat shelf=yes')
        base_style = (HERE / "desk-shell/style/calm.style").read_text(encoding="utf-8")
        extra = "\n".join("role " + r + " : ink" for r in
                          ("viewer", "pins", "chip", "chip.on", "hint", "viewhead", "find", "shown", "prose"))
        self.make(self.home, "kind=note title=fixture-style tags=style text=" + q(base_style + "\n" + extra))
        self.make(self.home, "kind=note title=home-viewer tags=lens style=fixture-style text=" +
                  q((stage / "home-viewer.lens").read_text(encoding="utf-8")))
        for title, body in [("home-note", 'note : text "$text"'),
                            ("home-chat", 'chat : text "$text"'), ("home-surface", 'surface : text "$title"')]:
            self.make(self.home, f"kind=note title={title} tags=lens text={q(body)}")
        self.act("init")
        painted, _ = scene.scene_for(self.d, "home-viewer")
        self.assertNotIn("refused", str(painted).lower())
        self.assertIn("First", str(painted))
        def walk(value):
            if isinstance(value, dict):
                yield value
                for x in value.values():
                    yield from walk(x)
            elif isinstance(value, list):
                for x in value:
                    yield from walk(x)
        self.assertTrue(any(n.get("remember") == self.props()["reading_key"] for n in walk(painted)))
        self.line(f"view agora://fixture/item/{self.b}")
        self.assertEqual(self.b, self.props()["viewing"])
        self.line(f"open-found {self.c} {self.v} {self.home}")
        self.assertEqual(self.c, self.props()["viewing"])
        self.assertEqual(1, len(self.state().tabs))
        painted, _ = scene.scene_for(self.d, "home-viewer")
        back = next(a["line"] for a in walk(painted) if a.get("on") == "click"
                    and "action=back" in a.get("line", ""))
        self.line(back)
        self.assertEqual(self.b, self.props()["viewing"])
        self.act("new", f"target={self.a}")
        painted, _ = scene.scene_for(self.d, "home-viewer")
        self.assertIn("First", str(painted))
        self.assertIn("Second", str(painted))
        state = self.props()["tabs_state"]
        self.line(f"unview {self.v}")
        self.assertEqual("", self.props()["viewing"])
        self.assertEqual("yes", viewer_tabs.props(self.w, panel)["shelf"])
        self.assertEqual("no", viewer_tabs.props(self.w, chat)["shelf"])
        self.assertEqual(state, self.props()["tabs_state"])
        self.line(f"view {self.a}")
        self.assertEqual("no", viewer_tabs.props(self.w, panel)["shelf"])
        self.assertEqual(2, len(self.state().tabs))
        self.unchanged_draft()


if __name__ == "__main__":
    unittest.main()
