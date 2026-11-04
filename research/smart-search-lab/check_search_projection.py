"""Synthetic regression: actual Kernel.shown/search, no Kernel init/log/files."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/kernel-lab"))
from kernel.kernel import Actor, Kernel
from kernel.store import State
from kernel import lines as L, words as W


def world(*things):
    # Bypass the persistent constructor entirely, never create keep/seal/accounts.
    k = object.__new__(Kernel)
    k.tag, k.place = "sx", "sx1"
    k.state = State()
    k.state.things = {"sx1": {"kind": "place"}, "sx2": {"kind": "person"},
                      "sx3": {"kind": "person"}, **dict(things)}
    k.state.rev = {t: 0 for t in k.state.things}
    k.log = SimpleNamespace(records=[])
    k.kinds = SimpleNamespace(decl=lambda *a: False, is_open=lambda *a: False)
    k.name = Mock(wraps=k.name)
    return k


def search(k, query="needle", person="sx3", alias=False):
    actor = Actor(person, person, "person")
    step = L.parse(("find " if alias else "search ") + query)
    return (W.rows if alias else W.search)(k, actor, step, {}, None, k.place)


class SearchProjection(unittest.TestCase):
    def test_hidden_name_never_falls_back_to_raw_name(self):
        k = world(("sx4", dict(kind="note", name="PRIVATE_NAME_SENTINEL",
                             text="public needle body", **{"sees.name": "person:sx2"})))
        guest = search(k)
        self.assertEqual(guest["rows"][0]["name"], "Untitled result")
        self.assertNotIn("PRIVATE_NAME_SENTINEL", json.dumps(guest))
        k.name.assert_not_called()
        self.assertEqual(search(k, person="sx2")["rows"][0]["name"], "PRIVATE_NAME_SENTINEL")

    def test_all_searchable_private_fields_excluded_from_matching_and_snippets(self):
        fields = set(W.SEARCH_TITLE + W.SEARCH_TEXT)
        facts = {"kind": "note", "text": "needle public evidence"}
        for field in fields - {"text"}:
            facts[field] = "PRIVATE_FIELD_SENTINEL"
            facts["sees." + field] = "person:sx2"
        k = world(("sx4", facts))
        result = search(k)
        self.assertEqual(result["rows"][0]["name"], "Untitled result")
        self.assertIn("needle public evidence", result["rows"][0]["snippet"])
        self.assertNotIn("PRIVATE_FIELD_SENTINEL", json.dumps(result))
        self.assertFalse(search(k, "PRIVATE_FIELD_SENTINEL")["rows"])
        private_text = dict(kind="note", title="needle", text="PRIVATE_TEXT_SENTINEL",
                            **{"sees.text": "person:sx2"})
        result = search(world(("sx4", private_text)))
        self.assertEqual(result["rows"][0]["snippet"], "")
        self.assertNotIn("PRIVATE_TEXT_SENTINEL", json.dumps(result))

    def test_visible_label_precedence_and_neutral_fallback(self):
        for field in ("title", "label", "name", "word"):
            k = world(("sx4", dict(kind="note", text="needle", **{field: "Visible label"})))
            self.assertEqual(search(k)["rows"][0]["name"], "Visible label")
            k.name.assert_not_called()
        k = world(("sx4", dict(kind="note", title="", name="", text="needle")))
        self.assertEqual(search(k)["rows"][0]["name"], "Untitled result")

    def test_secondary_view_snippet_cannot_include_private_view_name(self):
        k = world(
            ("sx4", dict(kind="lens", name="PRIVATE_VIEW_SENTINEL",
                         text='reading:"rows board-channel"', **{"sees.name": "person:sx2"})),
            ("sx5", dict(kind="board-channel", title="Public child")),
        )
        result = search(k, "lens")
        child = next(r for r in result["rows"] if r["id"] == "sx5")
        self.assertEqual(child["snippet"], "shown in Untitled result")
        self.assertNotIn("PRIVATE_VIEW_SENTINEL", json.dumps(result))
        k.name.assert_not_called()

    def test_private_view_text_cannot_drive_related_expansion(self):
        k = world(
            ("sx4", dict(kind="lens", title="needle view",
                         text='reading:"rows board-channel"', **{"sees.text": "person:sx2"})),
            ("sx5", dict(kind="board-channel", title="Unrelated child")),
        )
        self.assertEqual([r["id"] for r in search(k)["rows"]], ["sx4"])

    def test_related_match_requires_visible_kind_and_label(self):
        k = world(
            ("sx4", dict(kind="lens", title="needle view", text='reading:"rows board-channel"')),
            ("sx5", dict(kind="board-channel", title="Hidden classification",
                         **{"sees.kind": "person:sx2"})),
            ("sx6", dict(kind="board-channel", name="PRIVATE_CHILD_SENTINEL",
                         **{"sees.name": "person:sx2"})),
            ("sx7", dict(kind="board-channel", title="Public child")),
        )
        result = search(k)
        self.assertEqual({r["id"] for r in result["rows"]}, {"sx4", "sx7"})
        self.assertNotIn("PRIVATE_CHILD_SENTINEL", json.dumps(result))

    def test_find_dispatch_uses_same_projected_labels(self):
        k = world(("sx4", dict(kind="note", name="PRIVATE_ALIAS_SENTINEL", text="needle",
                             **{"sees.name": "person:sx2"})))
        result = search(k, alias=True)
        self.assertEqual(result["rows"][0]["name"], "Untitled result")
        self.assertNotIn("PRIVATE_ALIAS_SENTINEL", json.dumps(result))
        k.name.assert_not_called()

    def test_revoked_forgotten_or_parent_private_records_absent(self):
        k = world(
            ("sx4", dict(kind="note", title="needle", sees="person:sx2")),
            ("sx5", dict(kind="note", title="needle", forgotten=True)),
            ("sx6", dict(kind="document", title="Parent", sees="person:sx2")),
            ("sx7", dict(kind="note", title="needle", visibility_of="sx6")),
            ("sx8", dict(kind="note", title="needle visible")),
        )
        self.assertEqual([r["id"] for r in search(k)["rows"]], ["sx8"])
        k.state.things["sx8"]["sees"] = "person:sx2"
        self.assertFalse(search(k)["rows"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
