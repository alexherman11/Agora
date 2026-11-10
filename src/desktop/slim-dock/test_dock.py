"""In-memory desk integration: no sessions, browser, host or live world."""
import pathlib
import json
import re
import sys
import unittest
import uuid

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "text-desk" / "notation"))
import explore
import lens_ir
import names
import scene
import style
import partition_data
import world_patch
import partition_hook


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


class DockTests(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.w = self.d.world
        self.w.me = "alex"
        self.root = self.w.root
        self.runline("look")
        self.home = self.make(self.root, 'kind=surface title="Home base"')
        self.dock = self.make(self.home, 'kind=surface title=Dock')
        self.runline(f"do prop {self.dock} role=dock actor=alex")
        self.layout = self.make(self.home, 'kind=surface title=Layout')
        self.runline(f"do prop {self.layout} role=home-layout actor=alex")
        self.viewer = self.make(self.home, 'kind=note title=Viewer role=home-view actor=alex viewing="" with=""')
        self.doc = self.make(self.home, 'kind=note title="A real proposal" text="Keep this."')
        # Current public verbs, installed in the fixture before their callers.
        self.make(self.home, 'kind=note title=view tags=verb on=house text=' + q(
            'do prop prop:role=home-view,prop:actor=$me viewing=a5080 when count(prop:role=home-view,prop:actor=$me,prop:viewing) = 0\n'
            'do prop prop:role=home-view,prop:actor=$me back=$(max($viewing of prop:role=home-view,prop:actor=$me)) viewing=$1 find="" with="" when count(prop:role=home-view,prop:actor=$me,prop:viewing=$1) = 0\n'
            'do prop prop:role=home-panel,prop:actor=$me,prop:lens=home-viewer shelf=no when count(prop:role=home-panel,prop:actor=$me,prop:lens=home-viewer,prop:shelf=yes) > 0'))
        self.make(self.home, 'kind=note title=unview tags=verb on=house text=' + q(
            'do prop $1 back="$1.viewing" viewing="" with="" when ($1.viewing or "") != ""'))
        for path in HERE.glob("*.verb"):
            self.make(self.home, f'kind=note title={path.stem} tags=verb on=house text={q(path.read_text(encoding="utf-8"))}')

    def runline(self, line):
        r = self.d.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        text = r.get("text") or ""
        self.assertFalse(r.get("error") or re.search(r"(^|\n)(ERR|!! refused)", text), f"{line}\n{r}")
        return text

    def make(self, parent, body):
        self.runline(f"look {parent}")
        out = self.runline(f"do create {parent} {body}")
        return re.search(r"created ([af]\d+)", out)[1]

    def props(self, item):
        n = self.w.nodes[item]
        return (self.w.subjects[n["subject"]] if n.get("subject") else n).get("props", {})

    def pins(self):
        return self.w.children(self.dock)

    def pin(self, item):
        self.runline(f"look {item}")
        self.runline(f"look {self.dock}")
        self.runline(f"dock-pin {item} {self.dock}")

    def open(self, pin):
        self.runline(f"read {pin}")
        self.runline(f"look {self.layout} :3")
        self.runline(f"read {self.viewer}")
        self.runline(f"dock-open {pin} {self.layout} {self.viewer}")

    def test_document_duplicate_and_surface(self):
        self.pin(self.doc)
        self.pin(self.doc)
        self.assertEqual(1, len(self.pins()))
        self.assertEqual(self.w.nodes[self.doc]["subject"], self.props(self.pins()[0]["id"])["opens"])
        self.pin(self.home)
        self.assertEqual(2, len(self.pins()))
        view = self.make(self.home, 'kind=view title="Actual query" query=kind:note')
        self.pin(view)
        self.pin(view)
        self.assertEqual(3, len(self.pins()))
        self.open(self.pins()[-1]["id"])
        self.assertEqual(view, self.props(self.viewer)["viewing"])

    def test_panel_descriptor_restores_new_workspace_and_keeps_policy(self):
        panel = self.make(self.layout, 'kind=note title=Player role=home-panel actor=alex lens=player shows="" chrome=none sizing=content filled=player-full pin=yes shelf=yes')
        self.pin(panel)
        self.pin(panel)
        self.assertEqual(1, len(self.pins()))
        pin = self.pins()[0]["id"]
        self.assertNotIn(panel, str(self.props(pin)))
        self.open(pin)
        self.assertEqual("no", self.props(panel)["shelf"])
        # The prior workspace retains its own panel; a new current layout
        # must receive a new appearance, never reopen the old one.
        self.runline(f"do prop {self.layout} role=workspace")
        self.layout = self.make(self.home, 'kind=surface title=Next')
        self.runline(f"do prop {self.layout} role=home-layout actor=alex")
        self.runline(f'do prop {self.layout} tree={q(json.dumps({"v": 1, "root": None}))}')
        self.open(pin)
        current = self.w.children(self.layout)
        self.assertEqual(1, len(current))
        self.assertNotEqual(panel, current[0]["id"])
        p = self.props(current[0]["id"])
        self.assertEqual(("none", "content", "player-full", "yes"), tuple(p[k] for k in ("chrome", "sizing", "filled", "pin")))
        self.open(pin)
        self.assertEqual(1, len(self.w.children(self.layout)))

    def test_lens_and_existing_window_definition(self):
        lens = self.make(self.home, 'kind=note title=calendar tags=lens window=calendar text="root : text hello"')
        self.pin(lens)
        self.assertEqual("calendar", self.props(self.pins()[0]["id"])["lens"])
        app = self.make(self.home, 'kind=note title=Writer window=writing opens=chat')
        self.pin(app)
        self.pin(app)
        self.assertEqual(2, len(self.pins()))
        self.assertEqual("writing", self.props(self.pins()[1]["id"])["window"])
        native_definition = self.make(self.home, 'kind=note title=Notebook window=notes')
        self.pin(native_definition)
        p = self.props(self.pins()[-1]["id"])
        self.assertEqual("notes", p["window"])
        self.assertEqual("", p["opens"])

    def test_reorder_and_removal_is_undoable(self):
        self.pin(self.doc)
        self.pin(self.home)
        a, b = [n["id"] for n in self.pins()]
        self.runline(f"read {a}")
        self.runline(f"read {b}")
        self.runline(f"dock-place {b} {a} {self.dock}")
        self.assertEqual([b, a], [n["id"] for n in self.pins()])
        self.runline(f"dock-place-after {b} {a} {self.dock}")
        self.assertEqual([a, b], [n["id"] for n in self.pins()])
        self.runline(f"do prop {a} dock_removed=yes")
        event = self.w.events[-1]["id"]
        self.runline(f"undo {event}")
        self.assertNotEqual("yes", self.props(a).get("dock_removed"))
        self.assertEqual([a, b], [n["id"] for n in self.pins()])
        self.runline(f"do prop {a} dock_removed=yes")
        self.pin(self.doc)
        self.assertEqual("no", self.props(a)["dock_removed"])
        self.assertEqual(2, len(self.pins()))
        self.assertEqual([a, b], [n["id"] for n in self.pins()])
        other = self.make(self.home, 'kind=note title="External app" opens=chat window=writing')
        self.runline(f"read {a}")
        # Part names can coincide in different lenses: an external `app`
        # dropped over an existing icon pins; it must not silently disappear.
        self.runline(f"dock-place-after {other} {a} {self.dock}")
        self.assertEqual(3, len(self.pins()))

    def test_identity_fields_and_generic_drop_compile(self):
        self.assertEqual(self.w.nodes[self.doc]["subject"], names.part_of(self.w, self.doc, "id"))
        self.assertEqual(self.doc, names.part_of(self.w, self.doc, "item"))
        self.assertEqual("note", names.part_of(self.w, self.doc, "kind"))
        src = 'root : column\n  on drop any do prop $carried pinned=yes'
        _, parts = scene.parse(src)
        self.assertEqual("any", parts["root"]["on"][0]["part"])
        sc = lens_ir.evaluate(self.d, src)
        self.assertEqual("any", sc["acts"][0]["part"])
        with self.assertRaises(scene.LensRefusal):
            scene.parse("root : column\n  on drop missing do prop $carried pinned=yes")

    def test_staged_lens_compiles_and_emits_quiet_icons(self):
        src = (HERE / "home-dock.lens").read_text(encoding="utf-8")
        st = "token text = ui 16/1.4\n" + (HERE / "style.style").read_text(encoding="utf-8")
        look = style.looks(st)
        self.assertFalse(look["unread"])
        self.make(self.home, 'kind=note title=dock-style tags=style text=' + q(st))
        lens = self.make(self.home, 'kind=note title=slim-dock tags=lens style=dock-style text=' + q(src))
        self.pin(self.doc)
        result, _ = scene.scene_for(self.d, "slim-dock")
        def nodes(n):
            yield n
            for k in n.get("kids", []):
                yield from nodes(k)
        painted = list(nodes(result))
        apps = [n for n in painted if n["part"] == "app"]
        self.assertEqual(1, len(apps))
        self.assertEqual("A real proposal", apps[0]["paint"]["tip"][0])
        self.assertTrue(any(a["on"] == "carry" for a in apps[0]["acts"]))
        self.assertFalse(any(n.get("text") == "Dock this" for n in painted))
        self.assertTrue(any(a.get("part") == "any" for n in painted for a in n.get("acts", [])))
        self.assertEqual("sd.item", apps[0]["role"])
        self.runline(f"do prop {self.viewer} viewing={self.doc}")
        result, _ = scene.scene_for(self.d, "slim-dock")
        active = [n for n in nodes(result) if n["part"] == "app"]
        self.assertEqual("sd.item.open", active[0]["role"])

    def test_nested_tab_activation_preserves_literal_keys_and_policy(self):
        a = self.make(self.layout, 'kind=note title=First role=home-panel lens=first shelf=no')
        b = self.make(self.layout, 'kind=note title=Second role=home-panel lens=second shelf=yes sizing=content chrome=none')
        tree = {"v": 1, "literal": {a: b}, "root": {"axis": "tabs", "active": {"$ref": a},
                "kids": [{"id": {"$ref": a}}, {"id": {"$ref": b}, "size": "content"}]}}
        self.runline(f"do prop {self.layout} tree={q(json.dumps(tree))} full={a}")
        self.pin(b)
        self.open(self.pins()[0]["id"])
        actual = json.loads(self.props(self.layout)["tree"])
        self.assertEqual({"$ref": b}, actual["root"]["active"])
        self.assertEqual(tree["literal"], actual["literal"])
        self.assertEqual("content", actual["root"]["kids"][1]["size"])
        self.assertEqual("", self.props(self.layout)["full"])
        self.assertEqual("no", self.props(b)["shelf"])
        for bad in ('{', '{"v":2,"root":null}', '{"v":true,"root":null}', '{"v":1}',
                    '{"v":1,"root":{"id":"a1"}}'):
            with self.assertRaises((ValueError, TypeError)):
                partition_data.activate(bad, b)

    def test_host_menu_and_guard_admission(self):
        _, parts = scene.parse('root : text hi\n  on menu "Window" when true host window notes\n  on click when false host hide')
        self.assertEqual(["host window notes", "host hide"], [a["line"] for a in parts["root"]["on"]])
        for src in ('root : text hi\n  on click host window notes', 'root : text hi\n  media\n  on pop host window notes'):
            self.assertEqual("host window notes", scene.parse(src)[1]["root"]["on"][0]["line"])

    def test_column_layout_new_panel_and_document_open_keep_draft(self):
        column = self.make(self.layout, 'kind=surface title=column layout=column')
        lens = self.make(self.home, 'kind=note title=plans tags=lens text="root : text hi"')
        self.pin(lens)
        pin = self.pins()[0]["id"]
        self.open(pin)
        self.assertEqual("plans", self.props(self.w.children(column)[0]["id"])["lens"])
        self.open(pin)
        self.assertEqual(1, len(self.w.children(column)))
        draft = self.make(self.home, 'kind=note title=Draft role=draft text="Unsent words" about="Explicit conversation"')
        before = dict(self.props(draft))
        self.pin(self.doc)
        self.open(self.pins()[1]["id"])
        self.open(self.pins()[1]["id"])
        self.assertEqual(self.w.nodes[self.doc]["subject"], self.props(self.viewer)["viewing"])
        self.assertEqual(before, self.props(draft))
        self.assertEqual("Unsent words", self.w.subjects[self.w.nodes[draft]["subject"]]["text"])

    def test_malformed_tree_does_not_partly_restore_panel(self):
        panel = self.make(self.layout, 'kind=note title=Player role=home-panel lens=player shelf=yes')
        self.pin(panel)
        self.runline(f'do prop {self.layout} tree={q(json.dumps({"v": 9, "root": None}))} full={panel}')
        before = dict(self.props(self.layout)), dict(self.props(panel))
        self.open(self.pins()[0]["id"])
        self.assertEqual(before, (self.props(self.layout), self.props(panel)))

    def test_staging_and_source_hook_preflight_are_pure(self):
        texts = {ident: old for ident, old, _ in world_patch.passages()}
        world_patch.preflight(texts)
        changed = dict(texts)
        changed["a5486"] = "someone changed the passage"
        with self.assertRaises(ValueError):
            world_patch.preflight(changed)
        self.assertEqual(texts["a5486"], world_patch.VIEWER_OLD)
        source = "\n".join(old for old, _ in partition_hook.HUNKS)
        patched = partition_hook.patched(source)
        self.assertIn("external.release()", patched)
        self.assertIn("active.next = null", patched)
        with self.assertRaises(ValueError):
            partition_hook.patched(source.replace("const target = P.hit", "const target = changed"))
        self.assertNotIn("external.release()", source)


if __name__ == "__main__":
    unittest.main()
